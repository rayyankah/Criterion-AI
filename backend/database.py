"""
database.py — MongoDB Atlas connection boilerplate for Criterion AI.

Establishes a singleton client and exposes collection handles for:
  • questions    – past-paper questions + mark schemes
  • student_profiles – per-student weakness / mastery state
"""

import os
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

load_dotenv()

MONGODB_URI: str = os.getenv("MONGODB_URI", "")
DB_NAME: str = os.getenv("MONGODB_DB_NAME", "criterion_ai")

if not MONGODB_URI:
    raise EnvironmentError(
        "MONGODB_URI is not set. Add it to your .env file."
    )

# ---------------------------------------------------------------------------
# Singleton client
# ---------------------------------------------------------------------------
_client: MongoClient | None = None


def get_client() -> MongoClient:
    """Return (and lazily create) a MongoClient singleton."""
    global _client
    if _client is None:
        _client = MongoClient(MONGODB_URI)
        # Verify the connection is alive
        try:
            _client.admin.command("ping")
            print("✅  Connected to MongoDB Atlas successfully.")
        except ConnectionFailure as exc:
            raise ConnectionFailure(
                f"Could not connect to MongoDB Atlas: {exc}"
            ) from exc
    return _client


def get_database():
    """Return the default Criterion AI database handle."""
    return get_client()[DB_NAME]


# ---------------------------------------------------------------------------
# Collection accessors
# ---------------------------------------------------------------------------

def get_questions_collection():
    """
    Collection: questions
    Schema (indicative):
    {
        "_id": ObjectId,
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
    return get_database()["questions"]


def get_student_profiles_collection():
    """
    Collection: student_profiles
    Schema (indicative):
    {
        "_id": ObjectId,
        "student_id": "uuid-string",
        "name": "Student Name",
        "level": "O" | "A",
        "subjects": ["Mathematics", "Physics"],
        "weakness_map": {
            "Mathematics": {
                "Differentiation": {"attempts": 5, "pass": 2, "fail": 3, "mastery": 0.40},
                "Integration":    {"attempts": 3, "pass": 3, "fail": 0, "mastery": 1.00},
            }
        },
        "exam_history": [
            {
                "timestamp": "ISO-8601",
                "subject": "Mathematics",
                "topic": "Differentiation",
                "question_id": "ObjectId-ref",
                "score": 4,
                "max_score": 6,
                "passed": false,
                "feedback": "..."
            }
        ],
        "created_at": "ISO-8601",
        "updated_at": "ISO-8601",
    }
    """
    return get_database()["student_profiles"]


# ---------------------------------------------------------------------------
# Index setup (call once on startup)
# ---------------------------------------------------------------------------

def ensure_indexes():
    """Create indexes for efficient queries."""
    questions = get_questions_collection()
    questions.create_index([("subject", 1), ("level", 1), ("topic", 1)])
    questions.create_index([("syllabus_code", 1), ("year", 1), ("session", 1)])

    profiles = get_student_profiles_collection()
    profiles.create_index("student_id", unique=True)

    print("✅  Database indexes ensured.")
