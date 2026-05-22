"""
main.py — FastAPI entry point & MCP server setup for Criterion AI.

Mounts:
  - MCP SSE transport at /mcp (for native MCP clients)
  - REST API at /api/* (for Agent Builder OpenAPI tools)
"""

import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from database import ensure_indexes, get_student_profiles_collection
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
    print("🚀  Criterion AI backend is live.")
    yield
    print("👋  Criterion AI backend shutting down.")


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
    allow_credentials=True,
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
# Health / Root
# ---------------------------------------------------------------------------

@app.get("/")
async def root():
    return {
        "service": "Criterion AI",
        "version": "0.1.0",
        "status": "healthy",
        "mcp_endpoint": "/mcp",
    }


@app.get("/health")
async def health():
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Run with: uvicorn main:app --reload
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8000")),
        reload=True,
    )
