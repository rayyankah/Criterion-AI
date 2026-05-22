"""
tools.py — MCP Tool definitions for Criterion AI.

Exposes three tools via the Model Context Protocol that Gemini can invoke:
  1. fetch_question     – retrieve past-paper questions by syllabus / topic
  2. evaluate_working   – auto-grade step-by-step mathematical working
  3. update_student_profile – persist pass/fail state for adaptive tracking
"""

from typing import Any
from mcp.server.fastmcp import FastMCP
from database import (
    get_questions_collection,
    get_student_profiles_collection,
)

# ---------------------------------------------------------------------------
# MCP Server instance (mounted into FastAPI in main.py)
# ---------------------------------------------------------------------------
mcp = FastMCP(
    name="criterion-ai-tools",
    instructions=(
        "You are Criterion AI, an expert O/A Level academic tutor. "
        "Use the tools below to fetch questions, grade student work, "
        "and track student progress adaptively."
    ),
)


# ═══════════════════════════════════════════════════════════════════════════
# Tool 1 — fetch_question
# ═══════════════════════════════════════════════════════════════════════════

@mcp.tool()
def fetch_question(
    subject: str,
    level: str,
    topic: str | None = None,
    year: int | None = None,
    session: str | None = None,
    difficulty: str | None = None,
) -> dict[str, Any]:
    """
    Fetch a past-paper question and its mark scheme from the question bank.

    Args:
        subject:    Subject name, e.g. "Mathematics", "Physics".
        level:      Examination level — "O" or "A".
        topic:      Optional topic filter, e.g. "Differentiation".
        year:       Optional year filter, e.g. 2023.
        session:    Optional session filter, e.g. "May/June".
        difficulty: Optional difficulty filter — "easy", "medium", "hard".

    Returns:
        A dict with the question text, mark scheme, and metadata.
    """
    collection = get_questions_collection()

    # Build dynamic query
    query: dict[str, Any] = {
        "subject": {"$regex": f"^{subject}$", "$options": "i"},
        "level": level.upper(),
    }
    if topic:
        query["topic"] = {"$regex": f"^{topic}$", "$options": "i"}
    if year:
        query["year"] = year
    if session:
        query["session"] = {"$regex": session, "$options": "i"}
    if difficulty:
        query["difficulty"] = difficulty.lower()

    # TODO: Replace with smarter sampling (weighted by weakness) once
    #       the adaptive engine is wired up.
    doc = collection.find_one(query)

    if doc is None:
        return {
            "status": "not_found",
            "message": (
                f"No question found for {subject} ({level}) "
                f"with the given filters."
            ),
        }

    # Serialise ObjectId for JSON transport
    doc["_id"] = str(doc["_id"])
    return {"status": "ok", "question": doc}


# ═══════════════════════════════════════════════════════════════════════════
# Tool 2 — evaluate_working
# ═══════════════════════════════════════════════════════════════════════════

@mcp.tool()
def evaluate_working(
    question_id: str,
    student_id: str,
    student_working: str,
) -> dict[str, Any]:
    """
    Auto-grade a student's step-by-step mathematical working against
    the stored mark scheme, assigning partial credit where appropriate.

    Args:
        question_id:     The _id of the question document being answered.
        student_id:      Unique identifier for the student.
        student_working: The student's full working/answer as a string
                         (may include LaTeX or plain text steps).

    Returns:
        A grading report with score, max marks, per-step feedback, and
        whether the attempt is considered a pass.
    """
    from bson import ObjectId

    questions = get_questions_collection()
    question = questions.find_one({"_id": ObjectId(question_id)})

    if question is None:
        return {"status": "error", "message": "Question not found."}

    mark_scheme: str = question.get("mark_scheme", "")
    total_marks: int = question.get("total_marks", 0)

    # ------------------------------------------------------------------
    # TODO: Implement the core grading algorithm.
    #
    # Approach outline:
    #   1. Parse `student_working` into discrete steps.
    #   2. Compare each step against the mark-scheme rubric using
    #      Gemini (or a custom heuristic for arithmetic checks).
    #   3. Award marks per step:
    #        M marks – method marks (correct approach)
    #        A marks – accuracy marks (correct numerical result)
    #        B marks – independent marks
    #   4. Sum awarded marks and determine pass/fail threshold
    #      (typically ≥ 50 % of total_marks).
    # ------------------------------------------------------------------

    # Placeholder response — replace with real grading logic
    awarded_marks = 0
    passed = awarded_marks >= (total_marks * 0.5)

    return {
        "status": "ok",
        "question_id": question_id,
        "student_id": student_id,
        "total_marks": total_marks,
        "awarded_marks": awarded_marks,
        "percentage": round((awarded_marks / total_marks * 100), 1) if total_marks else 0,
        "passed": passed,
        "step_feedback": [
            # Each entry will look like:
            # {"step": 1, "content": "...", "marks_awarded": 1, "max": 2, "note": "..."}
        ],
        "overall_feedback": "Grading logic not yet implemented.",
    }


# ═══════════════════════════════════════════════════════════════════════════
# Tool 3 — update_student_profile
# ═══════════════════════════════════════════════════════════════════════════

@mcp.tool()
def update_student_profile(
    student_id: str,
    subject: str,
    topic: str,
    question_id: str,
    score: int,
    max_score: int,
    passed: bool,
    feedback: str = "",
) -> dict[str, Any]:
    """
    Persist a student's attempt result and update their weakness map so
    that future exam generation can adapt to their strengths/weaknesses.

    Args:
        student_id:  Unique identifier for the student.
        subject:     Subject name, e.g. "Mathematics".
        topic:       Topic name, e.g. "Differentiation".
        question_id: The _id of the question that was attempted.
        score:       Marks the student was awarded.
        max_score:   Maximum marks for the question.
        passed:      Whether the attempt meets the pass threshold.
        feedback:    Optional textual feedback from the grader.

    Returns:
        Updated weakness-map entry and confirmation.
    """
    from datetime import datetime, timezone

    profiles = get_student_profiles_collection()
    now = datetime.now(timezone.utc).isoformat()

    # Upsert the student document
    result = profiles.update_one(
        {"student_id": student_id},
        {
            # Ensure base fields exist on first insert
            "$setOnInsert": {
                "student_id": student_id,
                "name": "",
                "level": "",
                "subjects": [],
                "weakness_map": {},
                "exam_history": [],
                "created_at": now,
            },
            "$set": {
                "updated_at": now,
            },
            # Append this attempt to the history log
            "$push": {
                "exam_history": {
                    "timestamp": now,
                    "subject": subject,
                    "topic": topic,
                    "question_id": question_id,
                    "score": score,
                    "max_score": max_score,
                    "passed": passed,
                    "feedback": feedback,
                }
            },
            # Increment counters in the weakness map
            "$inc": {
                f"weakness_map.{subject}.{topic}.attempts": 1,
                f"weakness_map.{subject}.{topic}.{'pass' if passed else 'fail'}": 1,
            },
        },
        upsert=True,
    )

    # ------------------------------------------------------------------
    # Recalculate mastery score for this topic
    # mastery = pass_count / attempts
    # ------------------------------------------------------------------
    profile = profiles.find_one({"student_id": student_id})
    topic_stats = (
        profile.get("weakness_map", {})
        .get(subject, {})
        .get(topic, {})
    )
    attempts = topic_stats.get("attempts", 0)
    passes = topic_stats.get("pass", 0)
    mastery = round(passes / attempts, 2) if attempts > 0 else 0.0

    profiles.update_one(
        {"student_id": student_id},
        {"$set": {f"weakness_map.{subject}.{topic}.mastery": mastery}},
    )

    return {
        "status": "ok",
        "student_id": student_id,
        "subject": subject,
        "topic": topic,
        "updated_stats": {
            "attempts": attempts,
            "pass": passes,
            "fail": topic_stats.get("fail", 0),
            "mastery": mastery,
        },
        "upserted": result.upserted_id is not None,
    }
