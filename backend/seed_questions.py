"""
Seed the MongoDB questions collection with sample Cambridge past paper
questions for demo purposes.

Run: python seed_questions.py
"""

from datetime import datetime, timezone
from database import get_questions_collection, ensure_indexes


SEED_QUESTIONS = [
    {
        "syllabus_code": "4024",
        "subject": "Mathematics",
        "level": "O",
        "paper": "Paper 1",
        "year": 2023,
        "session": "May/June",
        "question_number": 5,
        "topic": "Quadratic Equations",
        "subtopic": "Factorisation",
        "question_text": "Solve the equation 2x² - 5x + 3 = 0 by factorisation.",
        "question_image_url": None,
        "total_marks": 4,
        "difficulty": "medium",
        "mark_scheme": {
            "steps": [
                {
                    "step_number": 1,
                    "description": "Attempt to factorise into two brackets",
                    "mark_type": "M",
                    "marks": 1,
                    "acceptable_working": ["(2x - 3)(x - 1)", "(x - 1)(2x - 3)"],
                    "keywords": ["factorise", "brackets", "(2x", "(x"],
                    "common_errors": ["(2x + 3)(x + 1)", "(2x - 1)(x - 3)"],
                },
                {
                    "step_number": 2,
                    "description": "Set each factor equal to zero",
                    "mark_type": "M",
                    "marks": 1,
                    "acceptable_working": ["2x - 3 = 0", "x - 1 = 0"],
                    "keywords": ["= 0", "equals"],
                    "depends_on": [1],
                },
                {
                    "step_number": 3,
                    "description": "x = 3/2 or x = 1.5",
                    "mark_type": "A",
                    "marks": 1,
                    "acceptable_answers": ["3/2", "1.5"],
                    "depends_on": [1, 2],
                },
                {
                    "step_number": 4,
                    "description": "x = 1",
                    "mark_type": "A",
                    "marks": 1,
                    "acceptable_answers": ["1"],
                    "depends_on": [1, 2],
                },
            ],
            "final_answer": "x = 3/2 or x = 1",
            "alternative_methods": [
                "Quadratic formula: x = (5 ± sqrt(25-24))/4 = (5 ± 1)/4"
            ],
        },
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source": "Cambridge 4024/12/M/J/23",
    },
    {
        "syllabus_code": "4024",
        "subject": "Mathematics",
        "level": "O",
        "paper": "Paper 2",
        "year": 2022,
        "session": "Oct/Nov",
        "question_number": 3,
        "topic": "Differentiation",
        "subtopic": "Gradient of Tangent",
        "question_text": (
            "The equation of a curve is y = x³ - 6x² + 9x + 2. "
            "Find the gradient of the curve at the point where x = 2."
        ),
        "question_image_url": None,
        "total_marks": 3,
        "difficulty": "medium",
        "mark_scheme": {
            "steps": [
                {
                    "step_number": 1,
                    "description": "Differentiate y with respect to x",
                    "mark_type": "M",
                    "marks": 1,
                    "acceptable_working": [
                        "dy/dx = 3x^2 - 12x + 9",
                        "3x² - 12x + 9",
                        "dy/dx = 3x² - 12x + 9",
                    ],
                    "keywords": ["dy/dx", "differentiate", "3x^2", "3x²"],
                },
                {
                    "step_number": 2,
                    "description": "Substitute x = 2",
                    "mark_type": "M",
                    "marks": 1,
                    "acceptable_working": [
                        "3(4) - 12(2) + 9",
                        "12 - 24 + 9",
                        "3(2)^2 - 12(2) + 9",
                    ],
                    "keywords": ["x = 2", "substitute", "x=2"],
                    "depends_on": [1],
                },
                {
                    "step_number": 3,
                    "description": "Gradient = -3",
                    "mark_type": "A",
                    "marks": 1,
                    "acceptable_answers": ["-3"],
                    "depends_on": [1, 2],
                },
            ],
            "final_answer": "-3",
        },
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source": "Cambridge 4024/22/O/N/22",
    },
    {
        "syllabus_code": "4024",
        "subject": "Mathematics",
        "level": "O",
        "paper": "Paper 1",
        "year": 2023,
        "session": "May/June",
        "question_number": 12,
        "topic": "Simultaneous Equations",
        "subtopic": "Linear",
        "question_text": (
            "Solve the simultaneous equations:\n"
            "3x + 2y = 12\n"
            "x - y = 1"
        ),
        "question_image_url": None,
        "total_marks": 3,
        "difficulty": "easy",
        "mark_scheme": {
            "steps": [
                {
                    "step_number": 1,
                    "description": "Attempt to eliminate one variable",
                    "mark_type": "M",
                    "marks": 1,
                    "acceptable_working": [
                        "x = 1 + y",
                        "3(1 + y) + 2y = 12",
                        "2x - 2y = 2",
                        "5x = 14",
                    ],
                    "keywords": ["substitute", "eliminate", "rearrange"],
                },
                {
                    "step_number": 2,
                    "description": "x = 14/5 or x = 2.8",
                    "mark_type": "A",
                    "marks": 1,
                    "acceptable_answers": ["14/5", "2.8"],
                    "depends_on": [1],
                },
                {
                    "step_number": 3,
                    "description": "y = 9/5 or y = 1.8",
                    "mark_type": "A",
                    "marks": 1,
                    "acceptable_answers": ["9/5", "1.8"],
                    "depends_on": [1],
                },
            ],
            "final_answer": "x = 14/5, y = 9/5",
        },
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source": "Cambridge 4024/12/M/J/23",
    },
    {
        "syllabus_code": "9709",
        "subject": "Mathematics",
        "level": "A",
        "paper": "Paper 1",
        "year": 2023,
        "session": "May/June",
        "question_number": 4,
        "topic": "Integration",
        "subtopic": "Definite Integration",
        "question_text": "Evaluate the definite integral: ∫₁³ (2x + 1)² dx",
        "question_image_url": None,
        "total_marks": 5,
        "difficulty": "hard",
        "mark_scheme": {
            "steps": [
                {
                    "step_number": 1,
                    "description": "Expand (2x + 1)² = 4x² + 4x + 1",
                    "mark_type": "B",
                    "marks": 1,
                    "acceptable_working": ["4x^2 + 4x + 1", "4x² + 4x + 1"],
                    "keywords": ["expand", "4x^2", "4x²"],
                },
                {
                    "step_number": 2,
                    "description": "Integrate: (4/3)x³ + 2x² + x",
                    "mark_type": "M",
                    "marks": 2,
                    "acceptable_working": [
                        "(4/3)x^3 + 2x^2 + x",
                        "4x³/3 + 2x² + x",
                        "4/3 x³ + 2x² + x",
                    ],
                    "keywords": ["x^3", "x³", "integrate"],
                    "depends_on": [1],
                },
                {
                    "step_number": 3,
                    "description": "Apply limits and evaluate",
                    "mark_type": "M",
                    "marks": 1,
                    "acceptable_working": [
                        "(36 + 18 + 3) - (4/3 + 2 + 1)",
                        "57 - 4/3 - 3",
                        "57 - 13/3",
                    ],
                    "keywords": ["upper", "lower", "subtract", "limits"],
                    "depends_on": [2],
                },
                {
                    "step_number": 4,
                    "description": "Final answer: 158/3 or 52.67 or 52⅔",
                    "mark_type": "A",
                    "marks": 1,
                    "acceptable_answers": ["158/3", "52.67", "52.7", "52 2/3"],
                    "depends_on": [2, 3],
                },
            ],
            "final_answer": "158/3",
        },
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source": "Cambridge 9709/12/M/J/23",
    },
    {
        "syllabus_code": "5054",
        "subject": "Physics",
        "level": "O",
        "paper": "Paper 2",
        "year": 2022,
        "session": "May/June",
        "question_number": 6,
        "topic": "Kinematics",
        "subtopic": "Equations of Motion",
        "question_text": (
            "A car starts from rest and accelerates uniformly at 2 m/s² "
            "for 10 seconds. Calculate:\n"
            "(a) the final velocity\n"
            "(b) the distance travelled"
        ),
        "question_image_url": None,
        "total_marks": 4,
        "difficulty": "easy",
        "mark_scheme": {
            "steps": [
                {
                    "step_number": 1,
                    "description": "Use v = u + at for final velocity",
                    "mark_type": "M",
                    "marks": 1,
                    "acceptable_working": [
                        "v = 0 + 2(10)",
                        "v = u + at",
                        "v = 0 + 2 × 10",
                    ],
                    "keywords": ["v = u + at", "v=u+at"],
                },
                {
                    "step_number": 2,
                    "description": "v = 20 m/s",
                    "mark_type": "A",
                    "marks": 1,
                    "acceptable_answers": ["20"],
                    "depends_on": [1],
                },
                {
                    "step_number": 3,
                    "description": "Use s = ut + ½at² for distance",
                    "mark_type": "M",
                    "marks": 1,
                    "acceptable_working": [
                        "s = 0 + 0.5(2)(100)",
                        "s = ½ × 2 × 10²",
                        "s = ut + ½at²",
                    ],
                    "keywords": ["s = ut", "½at²", "0.5at^2"],
                },
                {
                    "step_number": 4,
                    "description": "s = 100 m",
                    "mark_type": "A",
                    "marks": 1,
                    "acceptable_answers": ["100"],
                    "depends_on": [3],
                },
            ],
            "final_answer": "v = 20 m/s, s = 100 m",
        },
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source": "Cambridge 5054/22/M/J/22",
    },
]


def seed():
    """Insert seed questions into MongoDB."""
    ensure_indexes()
    collection = get_questions_collection()

    # Clear existing seed data
    collection.delete_many({})

    result = collection.insert_many(SEED_QUESTIONS)
    print(f"[OK] Seeded {len(result.inserted_ids)} questions into the database.")
    for i, doc_id in enumerate(result.inserted_ids):
        q = SEED_QUESTIONS[i]
        print(f"   {doc_id} - {q['subject']} / {q['topic']} ({q['level']}-Level)")


if __name__ == "__main__":
    seed()
