"""
Adaptive Weakness Tracker for Criterion AI.

Uses the Weighted Topic Priority Score (WTPS) algorithm to determine
which topic a student should practice next based on their historical
performance data stored in MongoDB.
"""

from datetime import datetime, timezone
from typing import Any

from database import get_student_profiles_collection


# ─── Tunable weights ─────────────────────────────────────────────────────
W_FAILURE_RATE = 0.45
W_RECENCY = 0.25
W_ATTEMPT_PENALTY = 0.20
W_STREAK_BONUS = 0.10
RECENCY_DECAY_FACTOR = 0.1
ATTEMPT_DECAY_FACTOR = 0.2
STREAK_CAP = 5


def compute_wtps(topic_stats: dict[str, Any]) -> float:
    """
    Compute the Weighted Topic Priority Score for a single topic.

    Higher score = weaker topic = should be practiced next.

    Args:
        topic_stats: {
            "attempts": int,
            "pass": int,
            "fail": int,
            "mastery": float,
            "streak": int,
            "last_attempt": str (ISO-8601),
            "avg_score_pct": float
        }

    Returns:
        WTPS score between 0.0 and 1.0
    """
    attempts = topic_stats.get("attempts", 0)
    if attempts == 0:
        # Never attempted = high priority (we want to test this topic)
        return 0.85

    fails = topic_stats.get("fail", 0)
    streak = topic_stats.get("streak", 0)

    # ── Factor 1: Failure rate (higher = weaker) ──
    failure_rate = fails / attempts

    # ── Factor 2: Recency (higher = NOT practiced recently) ──
    last_attempt_str = topic_stats.get("last_attempt")
    if last_attempt_str:
        try:
            last_attempt_dt = datetime.fromisoformat(last_attempt_str)
            if last_attempt_dt.tzinfo is None:
                last_attempt_dt = last_attempt_dt.replace(tzinfo=timezone.utc)
            days_since = (datetime.now(timezone.utc) - last_attempt_dt).days
        except (ValueError, TypeError):
            days_since = 30
    else:
        days_since = 30

    recency_decay = 1.0 / (1.0 + days_since * RECENCY_DECAY_FACTOR)
    recency_factor = 1.0 - recency_decay

    # ── Factor 3: Attempt penalty (higher if fewer attempts = undertested) ──
    attempt_penalty = 1.0 / (1.0 + attempts * ATTEMPT_DECAY_FACTOR)

    # ── Factor 4: Streak bonus (higher streak = topic mastered recently) ──
    streak_bonus = min(streak / STREAK_CAP, 1.0)

    # ── Weighted sum ──
    wtps = (
        W_FAILURE_RATE * failure_rate
        + W_RECENCY * recency_factor
        + W_ATTEMPT_PENALTY * attempt_penalty
        - W_STREAK_BONUS * streak_bonus
    )

    return max(0.0, min(1.0, wtps))


def get_weakest_topics(
    student_id: str,
    subject: str,
    top_n: int = 3,
) -> list[dict[str, Any]]:
    """
    Return the top N weakest topics for a student in a given subject,
    ranked by WTPS (highest priority first).

    Args:
        student_id: The student's unique identifier.
        subject: The subject to analyze, e.g. "Mathematics".
        top_n: How many topics to return.

    Returns:
        List of dicts: [{"topic": str, "wtps": float, "mastery": float, ...}]
    """
    profiles = get_student_profiles_collection()
    profile = profiles.find_one({"student_id": student_id})

    if profile is None:
        return []

    weakness_map = profile.get("weakness_map", {})
    subject_map = weakness_map.get(subject, {})

    if not subject_map:
        return []

    scored_topics = []
    for topic_name, stats in subject_map.items():
        wtps = compute_wtps(stats)
        scored_topics.append({
            "topic": topic_name,
            "wtps": round(wtps, 4),
            "mastery": stats.get("mastery", 0.0),
            "attempts": stats.get("attempts", 0),
            "avg_score_pct": stats.get("avg_score_pct", 0.0),
            "streak": stats.get("streak", 0),
        })

    scored_topics.sort(key=lambda x: x["wtps"], reverse=True)
    return scored_topics[:top_n]


def get_recommended_difficulty(
    student_id: str,
    subject: str,
    topic: str,
) -> str:
    """
    Recommend a difficulty level based on the student's mastery.

    mastery < 0.3  → "easy"
    mastery 0.3–0.7 → "medium"
    mastery > 0.7  → "hard"
    """
    profiles = get_student_profiles_collection()
    profile = profiles.find_one({"student_id": student_id})

    if profile is None:
        return "medium"

    mastery = (
        profile.get("weakness_map", {})
        .get(subject, {})
        .get(topic, {})
        .get("mastery", 0.0)
    )

    if mastery < 0.3:
        return "easy"
    elif mastery < 0.7:
        return "medium"
    else:
        return "hard"
