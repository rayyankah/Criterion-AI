"""
database.py — MongoDB connection with IN-MEMORY fallback for Criterion AI.

Establishes a singleton client and exposes collection handles for:
  • questions    – past-paper questions + mark schemes
  • student_profiles – per-student weakness / mastery state

If MongoDB is not available (no URI, connection error, etc.), seamlessly
falls back to a simple in-memory dict-based store so the app works with
ZERO external setup.
"""

import os
import re
import copy
import uuid
from typing import Any
from dotenv import load_dotenv

load_dotenv()

MONGODB_URI: str = os.getenv("MONGODB_URI", "")
DB_NAME: str = os.getenv("MONGODB_DB_NAME", "criterion_ai")

# ---------------------------------------------------------------------------
# In-Memory Store — drop-in replacement for pymongo Collection
# ---------------------------------------------------------------------------

class _UpdateResult:
    """Mimics pymongo UpdateResult."""
    def __init__(self, matched: int, modified: int, upserted_id=None):
        self.matched_count = matched
        self.modified_count = modified
        self.upserted_id = upserted_id


class _InsertManyResult:
    """Mimics pymongo InsertManyResult."""
    def __init__(self, ids: list):
        self.inserted_ids = ids


class InMemoryCollection:
    """
    A minimal in-memory collection that supports the subset of pymongo
    operations used by Criterion AI:
      find_one, find, insert_many, insert_one, update_one,
      delete_many, create_index, count_documents
    """

    def __init__(self, name: str):
        self.name = name
        self._docs: list[dict[str, Any]] = []

    # ── helpers ──

    def _generate_id(self) -> str:
        """Generate a unique string ID (replaces ObjectId)."""
        return uuid.uuid4().hex[:24]

    def _match(self, doc: dict, query: dict) -> bool:
        """Check if a document matches a MongoDB-style query."""
        for key, condition in query.items():
            # Handle dot-notation for nested fields
            value = self._get_nested(doc, key)

            if isinstance(condition, dict):
                # Operator queries
                for op, operand in condition.items():
                    if op == "$regex":
                        flags = 0
                        opts = condition.get("$options", "")
                        if "i" in opts:
                            flags = re.IGNORECASE
                        if value is None or not re.search(operand, str(value), flags):
                            return False
                    elif op == "$options":
                        continue  # handled by $regex
                    elif op == "$gte":
                        if value is None or value < operand:
                            return False
                    elif op == "$lte":
                        if value is None or value > operand:
                            return False
                    elif op == "$gt":
                        if value is None or value <= operand:
                            return False
                    elif op == "$lt":
                        if value is None or value >= operand:
                            return False
                    elif op == "$in":
                        if value not in operand:
                            return False
                    elif op == "$ne":
                        if value == operand:
                            return False
            else:
                if value != condition:
                    return False
        return True

    def _get_nested(self, doc: dict, key: str) -> Any:
        """Get a value from a nested dict using dot notation."""
        parts = key.split(".")
        current = doc
        for part in parts:
            if isinstance(current, dict):
                current = current.get(part)
            else:
                return None
        return current

    def _set_nested(self, doc: dict, key: str, value: Any):
        """Set a value in a nested dict using dot notation."""
        parts = key.split(".")
        current = doc
        for part in parts[:-1]:
            if part not in current or not isinstance(current[part], dict):
                current[part] = {}
            current = current[part]
        current[parts[-1]] = value

    def _inc_nested(self, doc: dict, key: str, amount):
        """Increment a nested value."""
        parts = key.split(".")
        current = doc
        for part in parts[:-1]:
            if part not in current or not isinstance(current[part], dict):
                current[part] = {}
            current = current[part]
        current[parts[-1]] = current.get(parts[-1], 0) + amount

    # ── public API ──

    def find_one(self, query: dict | None = None, *args, **kwargs) -> dict | None:
        query = query or {}
        for doc in self._docs:
            if self._match(doc, query):
                return copy.deepcopy(doc)
        return None

    def find(self, query: dict | None = None, *args, **kwargs) -> list[dict]:
        query = query or {}
        return [copy.deepcopy(d) for d in self._docs if self._match(d, query)]

    def insert_one(self, doc: dict) -> Any:
        doc = copy.deepcopy(doc)
        if "_id" not in doc:
            doc["_id"] = self._generate_id()
        self._docs.append(doc)
        return type("Result", (), {"inserted_id": doc["_id"]})()

    def insert_many(self, docs: list[dict]) -> _InsertManyResult:
        ids = []
        for doc in docs:
            doc = copy.deepcopy(doc)
            if "_id" not in doc:
                doc["_id"] = self._generate_id()
            self._docs.append(doc)
            ids.append(doc["_id"])
        return _InsertManyResult(ids)

    def update_one(self, query: dict, update: dict, upsert: bool = False) -> _UpdateResult:
        target = None
        for doc in self._docs:
            if self._match(doc, query):
                target = doc
                break

        if target is None and upsert:
            # Create a new document from $setOnInsert and query fields
            target = {}
            # Copy simple query fields
            for k, v in query.items():
                if not isinstance(v, dict):
                    target[k] = v
            if "_id" not in target:
                target["_id"] = self._generate_id()
            # Apply $setOnInsert
            for k, v in update.get("$setOnInsert", {}).items():
                self._set_nested(target, k, copy.deepcopy(v))
            self._docs.append(target)
            upserted_id = target["_id"]
        elif target is None:
            return _UpdateResult(0, 0)
        else:
            upserted_id = None

        # Apply $set
        for k, v in update.get("$set", {}).items():
            self._set_nested(target, k, copy.deepcopy(v))

        # Apply $inc
        for k, v in update.get("$inc", {}).items():
            self._inc_nested(target, k, v)

        # Apply $push
        for k, v in update.get("$push", {}).items():
            parts = k.split(".")
            current = target
            for part in parts[:-1]:
                if part not in current or not isinstance(current[part], dict):
                    current[part] = {}
                current = current[part]
            last = parts[-1]
            if last not in current or not isinstance(current[last], list):
                current[last] = []
            current[last].append(copy.deepcopy(v))

        # Apply $addToSet
        for k, v in update.get("$addToSet", {}).items():
            parts = k.split(".")
            current = target
            for part in parts[:-1]:
                current = current.setdefault(part, {})
            last = parts[-1]
            if last not in current or not isinstance(current[last], list):
                current[last] = []
            if v not in current[last]:
                current[last].append(copy.deepcopy(v))

        return _UpdateResult(1, 1, upserted_id)

    def delete_many(self, query: dict | None = None) -> Any:
        query = query or {}
        before = len(self._docs)
        self._docs = [d for d in self._docs if not self._match(d, query)]
        deleted = before - len(self._docs)
        return type("Result", (), {"deleted_count": deleted})()

    def count_documents(self, query: dict | None = None) -> int:
        query = query or {}
        return sum(1 for d in self._docs if self._match(d, query))

    def create_index(self, *args, **kwargs):
        """No-op for in-memory store."""
        pass


class InMemoryDB:
    """Mimics a pymongo Database object."""

    def __init__(self, name: str):
        self.name = name
        self._collections: dict[str, InMemoryCollection] = {}

    def __getitem__(self, name: str) -> InMemoryCollection:
        if name not in self._collections:
            self._collections[name] = InMemoryCollection(name)
        return self._collections[name]


# ---------------------------------------------------------------------------
# Connection logic with automatic fallback
# ---------------------------------------------------------------------------

_use_memory: bool = False
_memory_db: InMemoryDB | None = None
_seeded: bool = False

_client = None  # pymongo MongoClient, if available


def _try_mongo() -> bool:
    """Attempt to connect to MongoDB. Returns True on success."""
    global _client

    if not MONGODB_URI or "<" in MONGODB_URI:
        # URI is empty or still has placeholder values
        return False

    try:
        from pymongo import MongoClient
        from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

        _client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=3000)
        _client.admin.command("ping")
        print("[OK] Connected to MongoDB Atlas successfully.")
        return True
    except Exception as exc:
        print(f"[WARN] MongoDB unavailable ({type(exc).__name__}): {exc}")
        print("[INFO] Falling back to in-memory database.")
        return False


def _init():
    """Initialize the database connection (called lazily once)."""
    global _use_memory, _memory_db, _seeded

    if _memory_db is not None or _client is not None:
        return  # already initialized

    if _try_mongo():
        _use_memory = False
    else:
        _use_memory = True
        _memory_db = InMemoryDB(DB_NAME)


def _ensure_seeded():
    """Seed the in-memory database with questions on first access."""
    global _seeded
    if _seeded or not _use_memory:
        return
    _seeded = True

    try:
        from seed_questions import SEED_QUESTIONS
        collection = _memory_db["questions"]
        if collection.count_documents() == 0:
            result = collection.insert_many(SEED_QUESTIONS)
            print(f"[OK] Seeded {len(result.inserted_ids)} questions into in-memory store.")
    except Exception as e:
        print(f"[WARN] Could not seed in-memory DB: {e}")


# ---------------------------------------------------------------------------
# Public API — same interface as before
# ---------------------------------------------------------------------------

def get_client():
    """Return the MongoClient (or None if using in-memory)."""
    _init()
    return _client


def get_database():
    """Return the database handle."""
    _init()
    if _use_memory:
        return _memory_db
    return _client[DB_NAME]


def get_questions_collection():
    """
    Collection: questions
    Schema (indicative):
    {
        "_id": str (hex id),
        "subject": "Mathematics" | "Physics" | "Chemistry" | ...,
        "level": "O" | "A",
        "syllabus_code": "9709",
        "paper": "Paper 1",
        "year": 2023,
        "session": "May/June" | "Oct/Nov" | "Feb/Mar",
        "question_number": 3,
        "topic": "Differentiation",
        "question_text": "...",
        "mark_scheme": "...",
        "total_marks": 6,
        "difficulty": "medium",
    }
    """
    _init()
    _ensure_seeded()
    if _use_memory:
        return _memory_db["questions"]
    return _client[DB_NAME]["questions"]


def get_student_profiles_collection():
    """
    Collection: student_profiles
    Schema (indicative):
    {
        "_id": str,
        "student_id": "uuid-string",
        "name": "Student Name",
        "level": "O" | "A",
        "subjects": ["Mathematics", "Physics"],
        "weakness_map": {
            "Mathematics": {
                "Differentiation": {"attempts": 5, "pass": 2, "fail": 3, "mastery": 0.40},
            }
        },
        "exam_history": [...],
        "created_at": "ISO-8601",
        "updated_at": "ISO-8601",
    }
    """
    _init()
    if _use_memory:
        return _memory_db["student_profiles"]
    return _client[DB_NAME]["student_profiles"]


# ---------------------------------------------------------------------------
# Index setup (call once on startup)
# ---------------------------------------------------------------------------

def ensure_indexes():
    """Create indexes for efficient queries (no-op for in-memory)."""
    questions = get_questions_collection()
    questions.create_index([("subject", 1), ("level", 1), ("topic", 1)])
    questions.create_index([("syllabus_code", 1), ("year", 1), ("session", 1)])

    profiles = get_student_profiles_collection()
    profiles.create_index("student_id", unique=True)

    _init()
    mode = "in-memory" if _use_memory else "MongoDB Atlas"
    print(f"[OK] Database indexes ensured ({mode} mode).")


def is_using_memory() -> bool:
    """Check if the app is using in-memory storage."""
    _init()
    return _use_memory
