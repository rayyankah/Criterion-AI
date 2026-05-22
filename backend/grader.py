"""
Auto-Grader Engine for Cambridge O/A Level mark scheme evaluation.

Algorithm:
  Phase 1: Normalize + fuzzy match student working against mark scheme
  Phase 2: LLM escalation for ambiguous cases (optional, uses Gemini)

Supports:
  - M (method), A (accuracy), B (independent) marks
  - Dependency chains (A marks depend on M marks)
  - Follow-through (FT) marking for internally consistent errors
  - Partial credit at every step
"""

import re
import math
from typing import Any


# ─── Text Normalization ──────────────────────────────────────────────────

def normalize_math_text(text: str) -> str:
    """
    Normalize a mathematical text string for comparison.
    Strips whitespace, lowercases, standardizes notation.
    """
    if not text:
        return ""

    s = text.lower().strip()

    # Remove all spaces
    s = re.sub(r'\s+', '', s)

    # Standardize common math symbols
    replacements = {
        '×': '*', '÷': '/', '−': '-', '–': '-',
        '²': '^2', '³': '^3', '√': 'sqrt',
        'π': 'pi', '∞': 'inf',
    }
    for old, new in replacements.items():
        s = s.replace(old, new)

    # Remove trailing zeros: "5.0" → "5", "3.50" → "3.5"
    s = re.sub(r'(\d+\.\d*?)0+(?=\D|$)', r'\1', s)
    s = re.sub(r'(\d+)\.(?=\D|$)', r'\1', s)

    return s


def extract_numerical_values(text: str) -> list[float]:
    """Extract all numerical values from text, including fractions."""
    values = []

    # Match fractions like 3/2
    for match in re.finditer(r'(-?\d+)\s*/\s*(\d+)', text):
        num, den = int(match.group(1)), int(match.group(2))
        if den != 0:
            values.append(num / den)

    # Match decimals and integers
    for match in re.finditer(r'-?\d+\.?\d*', text):
        try:
            values.append(float(match.group()))
        except ValueError:
            pass

    return values


def values_match(val1: float, val2: float, tolerance: float = 0.001) -> bool:
    """Check if two numerical values match within tolerance."""
    return abs(val1 - val2) < tolerance


# ─── Step Matching ────────────────────────────────────────────────────────

def match_step(
    student_text: str,
    step_schema: dict[str, Any],
) -> dict[str, Any]:
    """
    Compare student's working against a single mark scheme step.

    Returns:
        {
            "matched": bool,
            "confidence": float (0.0 to 1.0),
            "marks_awarded": int,
            "note": str,
            "match_type": "exact" | "keyword" | "numerical" | "none"
        }
    """
    normalized_student = normalize_math_text(student_text)
    marks_available = step_schema.get("marks", 1)
    mark_type = step_schema.get("mark_type", "B")

    # ── Check 1: Exact match against acceptable working/answers ──
    acceptable = (
        step_schema.get("acceptable_working", [])
        + step_schema.get("acceptable_answers", [])
    )
    for acceptable_text in acceptable:
        normalized_acceptable = normalize_math_text(acceptable_text)
        if normalized_acceptable in normalized_student:
            return {
                "matched": True,
                "confidence": 1.0,
                "marks_awarded": marks_available,
                "note": "Correct — matches mark scheme",
                "match_type": "exact",
            }

    # ── Check 2: Numerical value match ──
    student_values = extract_numerical_values(student_text)
    acceptable_values = []
    for a in acceptable:
        acceptable_values.extend(extract_numerical_values(a))

    numerical_matches = 0
    for sv in student_values:
        for av in acceptable_values:
            if values_match(sv, av):
                numerical_matches += 1
                break

    if acceptable_values and numerical_matches >= len(acceptable_values):
        return {
            "matched": True,
            "confidence": 0.85,
            "marks_awarded": marks_available,
            "note": "Correct numerical answer found in working",
            "match_type": "numerical",
        }

    # ── Check 3: Keyword partial match (for method marks) ──
    keywords = step_schema.get("keywords", [])
    keyword_hits = 0
    for kw in keywords:
        if normalize_math_text(kw) in normalized_student:
            keyword_hits += 1

    if keywords and keyword_hits >= len(keywords) * 0.5:
        if mark_type == "M":
            return {
                "matched": True,
                "confidence": 0.6,
                "marks_awarded": marks_available,
                "note": "Method identified — mark awarded for approach",
                "match_type": "keyword",
            }
        else:
            return {
                "matched": False,
                "confidence": 0.4,
                "marks_awarded": 0,
                "note": f"Method seen but final answer incorrect for {mark_type} mark",
                "match_type": "keyword",
            }

    # ── Check 4: Common errors ──
    common_errors = step_schema.get("common_errors", [])
    for err in common_errors:
        if normalize_math_text(err) in normalized_student:
            return {
                "matched": False,
                "confidence": 0.8,
                "marks_awarded": 0,
                "note": f"Common error detected: {err}",
                "match_type": "none",
            }

    # ── No match ──
    return {
        "matched": False,
        "confidence": 0.0,
        "marks_awarded": 0,
        "note": f"Working does not match expected {mark_type} mark criteria",
        "match_type": "none",
    }


# ─── Full Grading Pipeline ───────────────────────────────────────────────

def grade_student_working(
    student_working: str,
    mark_scheme: dict[str, Any],
    total_marks: int,
) -> dict[str, Any]:
    """
    Grade a student's complete working against the full mark scheme.

    Handles:
    - Per-step matching with M/A/B marks
    - Dependency chains (A marks depend on M marks)
    - Follow-through (FT) marking
    - Partial credit aggregation

    Args:
        student_working: The student's full answer as a string.
        mark_scheme: The mark_scheme dict from the question document.
        total_marks: Maximum marks for the question.

    Returns:
        Dict with step_feedback list, total awarded marks, pass/fail, etc.
    """
    steps = mark_scheme.get("steps", [])
    if not steps:
        return {
            "awarded_marks": 0,
            "total_marks": total_marks,
            "percentage": 0.0,
            "passed": False,
            "step_feedback": [],
            "overall_feedback": "No mark scheme steps defined for this question.",
        }

    # Split student working into lines for per-step analysis
    student_lines = [
        line.strip() for line in student_working.strip().split('\n') if line.strip()
    ]

    # Combine all student working into one block for matching
    full_student_text = ' '.join(student_lines)

    step_results: list[dict[str, Any]] = []
    step_awarded: dict[int, bool] = {}

    for step in steps:
        step_num = step["step_number"]
        mark_type = step.get("mark_type", "B")
        marks_available = step.get("marks", 1)

        # ── Check dependency chain ──
        depends_on = step.get("depends_on", [])
        dependency_failed = False
        for dep in depends_on:
            if not step_awarded.get(dep, False):
                dependency_failed = True
                break

        # ── Match this step ──
        result = match_step(full_student_text, step)

        # ── Apply dependency rules ──
        if dependency_failed and result["matched"]:
            if mark_type == "A":
                if result["confidence"] >= 0.85:
                    result["note"] = (
                        "Follow-through mark awarded — working is "
                        "internally consistent despite earlier error"
                    )
                else:
                    result["marks_awarded"] = 0
                    result["matched"] = False
                    result["note"] = (
                        f"Cannot award {mark_type} mark — "
                        f"dependent step(s) {depends_on} not achieved"
                    )

        step_awarded[step_num] = result["matched"]

        step_results.append({
            "step": step_num,
            "mark_type": mark_type,
            "content": step.get("description", ""),
            "marks_awarded": result["marks_awarded"],
            "marks_available": marks_available,
            "correct": result["matched"],
            "note": result["note"],
        })

    # ── Aggregate ──
    total_awarded = sum(s["marks_awarded"] for s in step_results)
    percentage = round((total_awarded / total_marks * 100), 1) if total_marks > 0 else 0
    passed = total_awarded >= math.ceil(total_marks * 0.5)

    # ── Generate overall feedback ──
    if percentage == 100:
        overall = "Excellent work! Full marks awarded. Your working is clear and complete."
    elif percentage >= 75:
        overall = "Very good attempt. You demonstrated strong understanding with minor errors."
    elif percentage >= 50:
        overall = "Satisfactory attempt. You showed some correct methods but need to be more careful with accuracy."
    elif percentage >= 25:
        overall = "You showed some understanding but several key steps were incorrect or missing."
    else:
        overall = "This topic needs more practice. Review the mark scheme carefully and try similar questions."

    return {
        "awarded_marks": total_awarded,
        "total_marks": total_marks,
        "percentage": percentage,
        "passed": passed,
        "step_feedback": step_results,
        "overall_feedback": overall,
    }
