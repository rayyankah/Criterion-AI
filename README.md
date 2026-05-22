# 🎯 Criterion AI

> Autonomous O/A Level Academic Agent — Google Cloud Rapid Agent Hackathon

An intelligent tutoring system that fetches past-paper questions, auto-grades step-by-step mathematical working with partial credit, and adaptively tracks student weaknesses to generate personalised exams.

## Tech Stack

| Layer    | Technology                          |
| -------- | ----------------------------------- |
| Backend  | Python · FastAPI · MCP              |
| AI       | Gemini on Google Cloud              |
| Database | MongoDB Atlas                       |
| Frontend | React · Vite · TypeScript · Tailwind |

## Getting Started

### Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
uvicorn main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## MCP Tools

| Tool                     | Description                                      |
| ------------------------ | ------------------------------------------------ |
| `fetch_question`         | Retrieve past-paper questions by syllabus/topic  |
| `evaluate_working`       | Auto-grade student working with partial credit   |
| `update_student_profile` | Persist pass/fail state for adaptive tracking    |

## Team

Built for the **Google Cloud Rapid Agent Hackathon**.
