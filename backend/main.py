"""
main.py — FastAPI entry point & MCP server setup for Criterion AI.

Mounts:
  - MCP SSE transport at /mcp (for native MCP clients)
  - REST API at /api/* (for Agent Builder OpenAPI tools)
  - Smart Chat Orchestrator at /api/chat (replaces Gemini/Agent Builder)
"""

import os
import re
from contextlib import asynccontextmanager
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from database import ensure_indexes, get_student_profiles_collection, is_using_memory
from tools import mcp, fetch_question, evaluate_working, update_student_profile
from schemas import (
    FetchQuestionRequest,
    EvaluateWorkingRequest,
    UpdateProfileRequest,
)
from weakness_tracker import get_weakest_topics, get_recommended_difficulty

load_dotenv()

# ---------------------------------------------------------------------------
# Lifespan: runs on startup / shutdown
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan — setup DB indexes on boot."""
    ensure_indexes()
    mode = "in-memory" if is_using_memory() else "MongoDB Atlas"
    print(f"[OK] Criterion AI backend is live. (Database: {mode})")
    yield
    print("[OK] Criterion AI backend shutting down.")


# ---------------------------------------------------------------------------
# FastAPI application
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Criterion AI",
    description=(
        "Autonomous O/A Level academic agent — exposes MCP tools for "
        "question fetching, auto-grading, and adaptive weakness tracking."
    ),
    version="0.1.0",
    lifespan=lifespan,
)

# CORS — allow all origins during hackathon (tighten in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Mount MCP SSE transport at /mcp
# ---------------------------------------------------------------------------

mcp_app = mcp.streamable_http_app()
app.mount("/mcp", mcp_app)


# ---------------------------------------------------------------------------
# REST API Wrappers (for Agent Builder OpenAPI tools)
# ---------------------------------------------------------------------------

@app.post("/api/fetch-question")
async def api_fetch_question(req: FetchQuestionRequest):
    """REST wrapper around the MCP fetch_question tool."""
    result = fetch_question(
        subject=req.subject,
        level=req.level,
        topic=req.topic,
        year=req.year,
        session=req.session,
        difficulty=req.difficulty,
    )
    return result


@app.post("/api/evaluate-working")
async def api_evaluate_working(req: EvaluateWorkingRequest):
    """REST wrapper around the MCP evaluate_working tool."""
    result = evaluate_working(
        question_id=req.question_id,
        student_id=req.student_id,
        student_working=req.student_working,
    )
    return result


@app.post("/api/update-student-profile")
async def api_update_student_profile(req: UpdateProfileRequest):
    """REST wrapper around the MCP update_student_profile tool."""
    result = update_student_profile(
        student_id=req.student_id,
        subject=req.subject,
        topic=req.topic,
        question_id=req.question_id,
        score=req.score,
        max_score=req.max_score,
        passed=req.passed,
        feedback=req.feedback,
    )
    return result


@app.get("/api/weakest-topics/{student_id}/{subject}")
async def api_weakest_topics(student_id: str, subject: str, top_n: int = 3):
    """Get the student's weakest topics ranked by WTPS."""
    topics = get_weakest_topics(student_id, subject, top_n)
    return {"student_id": student_id, "subject": subject, "weakest_topics": topics}


@app.get("/api/student-profile/{student_id}")
async def api_student_profile(student_id: str):
    """Get a student's full profile."""
    profiles = get_student_profiles_collection()
    profile = profiles.find_one({"student_id": student_id})
    if profile is None:
        raise HTTPException(status_code=404, detail="Student not found")
    profile["_id"] = str(profile["_id"])
    return profile


# ---------------------------------------------------------------------------
# Smart Chat Orchestrator — /api/chat
# ---------------------------------------------------------------------------

# Per-student conversation state
_sessions: dict[str, dict[str, Any]] = {}

# Known subjects and topics for matching
KNOWN_SUBJECTS = {
    "math": "Mathematics",
    "maths": "Mathematics",
    "mathematics": "Mathematics",
    "physics": "Physics",
    "phys": "Physics",
    "chemistry": "Chemistry",
    "chem": "Chemistry",
    "biology": "Biology",
    "bio": "Biology",
}

KNOWN_TOPICS = [
    "quadratic equations", "differentiation", "integration",
    "simultaneous equations", "trigonometry", "algebra",
    "kinematics", "mechanics", "waves", "electricity",
    "organic chemistry", "atomic structure", "calculus",
    "probability", "statistics", "vectors", "matrices",
    "coordinate geometry", "functions", "logarithms",
    "sequences", "series", "permutations", "combinations",
]

KNOWN_LEVELS = {"o level": "O", "a level": "A", "o-level": "O", "a-level": "A", "igcse": "O", "as": "A", "al": "A"}


class ChatRequest(BaseModel):
    message: str
    student_id: str = "demo_student"


class ChatResponse(BaseModel):
    reply: str
    data: dict[str, Any] | None = None
    action: str = "message"


def _detect_subject(msg: str) -> str | None:
    """Detect a subject name from the message."""
    msg_lower = msg.lower()
    for keyword, subject in KNOWN_SUBJECTS.items():
        if keyword in msg_lower:
            return subject
    return None


def _detect_topic(msg: str) -> str | None:
    """Detect a topic name from the message."""
    msg_lower = msg.lower()
    for topic in KNOWN_TOPICS:
        if topic in msg_lower:
            return topic.title()
    return None


def _detect_level(msg: str) -> str | None:
    """Detect exam level from the message."""
    msg_lower = msg.lower()
    for keyword, level in KNOWN_LEVELS.items():
        if keyword in msg_lower:
            return level
    # Default: check for O or A standalone
    if re.search(r'\bo\b', msg_lower):
        return "O"
    if re.search(r'\ba\b', msg_lower):
        return None  # 'a' is too common to match alone
    return None


def _detect_difficulty(msg: str) -> str | None:
    """Detect difficulty from the message."""
    msg_lower = msg.lower()
    for diff in ["easy", "medium", "hard"]:
        if diff in msg_lower:
            return diff
    return None


def _is_working_submission(msg: str) -> bool:
    """Check if the message looks like mathematical working (an answer submission)."""
    indicators = [
        r'=',               # equations
        r'x\s*=',           # x = something
        r'y\s*=',           # y = something
        r'\d+\s*[+\-*/]\s*\d+',  # arithmetic
        r'dy/dx',           # differentiation
        r'∫',              # integration symbol
        r'sqrt',            # square root
        r'v\s*=\s*u',       # kinematics
        r's\s*=\s*u',       # kinematics
        r'\d+\s*m/s',       # units
        r'factoris',        # factorisation
        r'\(\d+x',          # brackets with x
        r'answer',          # explicit answer keyword
        r'ans',             # short answer keyword
        r'^\s*\d+(\.\d+)?\s*$', # just a number
    ]
    for pattern in indicators:
        if re.search(pattern, msg, re.IGNORECASE):
            return True
    return False


def _wants_question(msg: str) -> bool:
    """Check if the user is asking for a question."""
    msg_lower = msg.lower()
    question_keywords = [
        "question", "give me", "ask me", "test me", "practice",
        "quiz", "try", "attempt", "solve", "problem", "exercise",
        "challenge", "start", "new question", "next question",
        "another question",
    ]
    return any(kw in msg_lower for kw in question_keywords)


def _wants_progress(msg: str) -> bool:
    """Check if the user is asking about progress or weaknesses."""
    msg_lower = msg.lower()
    progress_keywords = [
        "weakest", "weakness", "progress", "how am i",
        "performance", "improve", "strength", "mastery",
        "what should i study", "recommend", "suggestion",
        "dashboard", "stats", "statistics", "report",
        "how did i do", "my score", "my results",
    ]
    return any(kw in msg_lower for kw in progress_keywords)


def _format_question(question_data: dict) -> str:
    """Format a question nicely for chat display."""
    q = question_data
    lines = [
        f"📝 **{q.get('subject', '')} — {q.get('topic', '')}**",
        f"*{q.get('level', '')} Level | {q.get('paper', '')} | {q.get('year', '')} {q.get('session', '')}*",
        f"*Difficulty: {q.get('difficulty', 'medium')} | Marks: {q.get('total_marks', '?')}*",
        "",
        f"**Question {q.get('question_number', '')}:**",
        q.get("question_text", ""),
        "",
        "---",
        "💡 *Type your working/answer below and I'll grade it using the Cambridge mark scheme!*",
    ]
    return "\n".join(lines)


def _format_grading(grading: dict) -> str:
    """Format grading results nicely for chat display."""
    score = grading.get("awarded_marks", 0)
    total = grading.get("total_marks", 0)
    pct = grading.get("percentage", 0)
    passed = grading.get("passed", False)

    # Emoji based on performance
    if pct == 100:
        emoji = "🌟"
    elif pct >= 75:
        emoji = "✅"
    elif pct >= 50:
        emoji = "📊"
    else:
        emoji = "📚"

    lines = [
        f"{emoji} **Score: {score}/{total} ({pct}%)**",
        f"**Result: {'✅ PASS' if passed else '❌ NEEDS MORE PRACTICE'}**",
        "",
    ]

    # Step-by-step feedback
    steps = grading.get("step_feedback", [])
    if steps:
        lines.append("**Step-by-step breakdown:**")
        for step in steps:
            mark = "✅" if step.get("correct") else "❌"
            lines.append(
                f"  {mark} Step {step['step']}) [{step['mark_type']}] "
                f"{step.get('content', '')} — "
                f"{step['marks_awarded']}/{step['marks_available']} "
                f"({step.get('note', '')})"
            )
        lines.append("")

    lines.append(f"**Feedback:** {grading.get('overall_feedback', '')}")
    lines.append("")
    lines.append("---")
    lines.append("💡 *Ask for another question or check your progress!*")

    return "\n".join(lines)


def _format_progress(student_id: str, subject: str, topics: list) -> str:
    """Format progress/weakness report."""
    if not topics:
        return (
            f"📊 No practice data yet for **{subject}**.\n\n"
            f"Start by asking me for a {subject} question! "
            f"For example: *\"Give me a {subject.lower()} question\"*"
        )

    lines = [
        f"📊 **Progress Report — {subject}**",
        f"*Student: {student_id}*",
        "",
        "| # | Topic | Priority | Mastery | Attempts | Avg Score |",
        "|---|-------|----------|---------|----------|-----------|",
    ]

    for i, t in enumerate(topics, 1):
        mastery_bar = "█" * int(t["mastery"] * 10) + "░" * (10 - int(t["mastery"] * 10))
        lines.append(
            f"| {i} | {t['topic']} | {t['wtps']:.2f} | "
            f"{mastery_bar} {t['mastery']:.0%} | "
            f"{t['attempts']} | {t.get('avg_score_pct', 0):.0%} |"
        )

    lines.append("")
    if topics:
        weakest = topics[0]["topic"]
        lines.append(
            f"🎯 **Recommendation:** Focus on **{weakest}** — "
            f"it has the highest priority score."
        )
        lines.append(
            f"\n💡 *Say \"Give me a {subject.lower()} {weakest.lower()} question\" to practice!*"
        )

    return "\n".join(lines)


@app.post("/api/chat", response_model=ChatResponse)
async def api_chat(req: ChatRequest):
    """
    Smart Chat Orchestrator — replaces Google Cloud Agent Builder / Gemini.

    Receives natural language messages and determines intent:
    - Asking for a question → fetch_question
    - Submitting working/answer → evaluate_working + update_student_profile
    - Asking about progress → get_weakest_topics
    - General chat → helpful contextual response
    """
    msg = req.message.strip()
    student_id = req.student_id

    # Get or create session
    if student_id not in _sessions:
        _sessions[student_id] = {
            "current_question": None,
            "current_question_id": None,
            "current_subject": None,
            "current_topic": None,
            "current_level": None,
            "history": [],
        }
    session = _sessions[student_id]

    # Detect intent
    subject = _detect_subject(msg) or session.get("current_subject")
    topic = _detect_topic(msg)
    level = _detect_level(msg) or session.get("current_level") or "O"
    difficulty = _detect_difficulty(msg)

    # ── INTENT 1: Asking for a question ──
    if _wants_question(msg):
        if not subject:
            return ChatResponse(
                reply=(
                    "📚 I'd love to give you a question! Which subject?\n\n"
                    "Available subjects:\n"
                    "• **Mathematics** (O Level & A Level)\n"
                    "• **Physics** (O Level)\n\n"
                    "Just say something like: *\"Give me a math question\"* or "
                    "*\"Physics kinematics question\"*"
                ),
                action="need_subject",
            )

        # Try to get recommended difficulty if student has history
        if not difficulty:
            if topic:
                difficulty = get_recommended_difficulty(student_id, subject, topic)

        result = fetch_question(
            subject=subject,
            level=level,
            topic=topic,
            difficulty=difficulty,
        )

        if result["status"] == "not_found":
            # Try without optional filters
            result = fetch_question(subject=subject, level=level)

        if result["status"] == "not_found":
            return ChatResponse(
                reply=(
                    f"😕 I couldn't find a question matching those filters.\n\n"
                    f"Try: *\"Give me a math question\"* or "
                    f"*\"Physics question\"*"
                ),
                action="not_found",
            )

        question = result["question"]
        # Update session
        session["current_question"] = question
        session["current_question_id"] = question["_id"]
        session["current_subject"] = question.get("subject")
        session["current_topic"] = question.get("topic")
        session["current_level"] = question.get("level")

        return ChatResponse(
            reply=_format_question(question),
            data={"question": question},
            action="question_fetched",
        )

    # ── INTENT 2: Submitting working / answer ──
    if _is_working_submission(msg) and session.get("current_question_id"):
        question_id = session["current_question_id"]
        current_question = session.get("current_question", {})

        # Grade the working
        grading = evaluate_working(
            question_id=question_id,
            student_id=student_id,
            student_working=msg,
        )

        if grading.get("status") == "error":
            return ChatResponse(
                reply=f"⚠️ {grading.get('message', 'Could not grade your working.')}",
                data=grading,
                action="error",
            )

        # Auto-update student profile
        profile_update = update_student_profile(
            student_id=student_id,
            subject=session.get("current_subject", ""),
            topic=session.get("current_topic", ""),
            question_id=question_id,
            score=grading["awarded_marks"],
            max_score=grading["total_marks"],
            passed=grading["passed"],
            feedback=grading["overall_feedback"],
        )

        # Clear current question from session
        session["current_question"] = None
        session["current_question_id"] = None

        return ChatResponse(
            reply=_format_grading(grading),
            data={
                "grading": grading,
                "profile_update": profile_update,
            },
            action="graded",
        )

    # ── INTENT 3: Progress / weakness query ──
    if _wants_progress(msg):
        target_subject = subject or "Mathematics"
        topics = get_weakest_topics(student_id, target_subject, top_n=5)

        return ChatResponse(
            reply=_format_progress(student_id, target_subject, topics),
            data={"weakest_topics": topics, "subject": target_subject},
            action="progress",
        )

    # ── INTENT 4: Greeting or general help ──
    msg_lower = msg.lower()
    greetings = ["hello", "hi", "hey", "salam", "good morning", "good evening", "good afternoon"]
    if any(g in msg_lower for g in greetings):
        return ChatResponse(
            reply=(
                "👋 **Hello! I'm Criterion AI**, your personal Cambridge O/A Level tutor.\n\n"
                "Here's what I can do:\n\n"
                "📝 **Practice Questions** — *\"Give me a math question\"*\n"
                "✍️ **Grade Your Work** — Just type your working after getting a question\n"
                "📊 **Track Progress** — *\"Show my progress in Mathematics\"*\n"
                "🎯 **Adaptive Learning** — I focus on your weakest topics!\n\n"
                "**Available subjects:** Mathematics (O/A Level), Physics (O Level)\n\n"
                "What would you like to practice today? 🚀"
            ),
            action="greeting",
        )

    # ── INTENT 5: If there's a current question but input doesn't look like math ──
    if session.get("current_question_id"):
        current_q = session.get("current_question", {})
        return ChatResponse(
            reply=(
                f"🤔 I'm not sure if that's your answer. You currently have an active question:\n\n"
                f"**{current_q.get('topic', 'Unknown')}** — "
                f"*{current_q.get('question_text', '')[:100]}...*\n\n"
                f"Please type your **mathematical working** to submit your answer, "
                f"or say *\"new question\"* to get a different one."
            ),
            action="clarify",
        )

    # ── Default helpful response ──
    return ChatResponse(
        reply=(
            "🤖 I'm **Criterion AI**, your Cambridge exam tutor!\n\n"
            "Try one of these:\n"
            "• *\"Give me a Mathematics question\"*\n"
            "• *\"Physics kinematics question\"*\n"
            "• *\"Show my progress\"*\n"
            "• *\"Give me an A Level integration question\"*\n\n"
            "I'll fetch real Cambridge past-paper questions and grade your "
            "working step-by-step using official mark schemes! 📚"
        ),
        action="help",
    )


# ---------------------------------------------------------------------------
# Health / Root
# ---------------------------------------------------------------------------

@app.get("/")
async def root():
    return {
        "service": "Criterion AI",
        "version": "0.1.0",
        "status": "healthy",
        "database": "in-memory" if is_using_memory() else "MongoDB Atlas",
        "mcp_endpoint": "/mcp",
        "chat_endpoint": "/api/chat",
        "docs": "/docs",
    }


@app.get("/health")
async def health():
    return {"status": "ok", "database": "in-memory" if is_using_memory() else "MongoDB Atlas"}


# ---------------------------------------------------------------------------
# Run with: python main.py
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8000")),
        reload=True,
    )
