"""Pydantic models for request/response validation."""

from pydantic import BaseModel, Field
from typing import Optional


class FetchQuestionRequest(BaseModel):
    subject: str = Field(..., description="Subject name, e.g. Mathematics")
    level: str = Field(..., pattern="^[OA]$", description="O or A")
    topic: Optional[str] = None
    year: Optional[int] = None
    session: Optional[str] = None
    difficulty: Optional[str] = None


class EvaluateWorkingRequest(BaseModel):
    question_id: str = Field(..., description="MongoDB ObjectId as string")
    student_id: str = Field(..., description="Unique student identifier")
    student_working: str = Field(..., min_length=1, description="Student's working/answer")


class UpdateProfileRequest(BaseModel):
    student_id: str
    subject: str
    topic: str
    question_id: str
    score: int = Field(..., ge=0)
    max_score: int = Field(..., gt=0)
    passed: bool
    feedback: str = ""


class StepFeedback(BaseModel):
    step: int
    mark_type: str
    content: str
    marks_awarded: int
    marks_available: int
    correct: bool
    note: str


class GradingResult(BaseModel):
    status: str
    question_id: str
    student_id: str
    total_marks: int
    awarded_marks: int
    percentage: float
    passed: bool
    step_feedback: list[StepFeedback]
    overall_feedback: str
