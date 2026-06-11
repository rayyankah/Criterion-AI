# 🎯 Criterion AI — Autonomous O/A Level Academic Agent

> **Google Cloud Rapid Agent Hackathon Submission**
> An AI-powered Cambridge O-Level and A-Level exam preparation agent that fetches real past-paper questions, auto-grades step-by-step mathematical working with partial credit, and adaptively tracks student weaknesses.

![Built with](https://img.shields.io/badge/Built%20with-Google%20Cloud-4285F4?logo=google-cloud&logoColor=white)
![Python](https://img.shields.io/badge/Backend-Python%20%7C%20FastAPI-009688?logo=fastapi)
![React](https://img.shields.io/badge/Frontend-React%20%7C%20Vite-61DAFB?logo=react)
![MongoDB](https://img.shields.io/badge/Database-MongoDB-47A248?logo=mongodb&logoColor=white)

---

## 🚀 What It Does

Criterion AI is an **autonomous exam preparation agent** that:

1. **📝 Fetches Past Paper Questions** — Retrieves real Cambridge O/A Level questions filtered by subject, topic, year, and difficulty from a structured question bank.

2. **✏️ Auto-Grades with Partial Credit** — Evaluates student step-by-step working against official mark schemes using Cambridge's M/A/B marking methodology (Method, Accuracy, and Independent marks), including dependency chains and follow-through marking.

3. **📊 Adaptive Weakness Tracking** — Uses our **Weighted Topic Priority Score (WTPS)** algorithm to identify a student's weakest topics and recommend what to practice next, creating a personalized study path.

---

## 🏗️ Architecture

```
┌─────────────────┐     ┌──────────────────────────┐     ┌───────────────┐
│   React + Vite  │────▶│  FastAPI + MCP Server     │────▶│   MongoDB     │
│   Chat Interface│◀────│  (Smart Orchestrator)     │◀────│   Atlas       │
└─────────────────┘     │                          │     └───────────────┘
                        │  Tools:                  │
                        │  ├─ fetch_question        │
                        │  ├─ evaluate_working      │
                        │  └─ update_student_profile │
                        │                          │
                        │  Algorithms:             │
                        │  ├─ Auto-Grader (M/A/B)  │
                        │  └─ WTPS Weakness Tracker │
                        └──────────────────────────┘
```

### Tech Stack
| Layer | Technology |
|-------|-----------|
| **Frontend** | React 19, TypeScript, Tailwind CSS v4, Vite 8 |
| **Backend** | Python, FastAPI, Model Context Protocol (MCP) |
| **Database** | MongoDB Atlas (with in-memory fallback) |
| **AI Protocol** | MCP (Streamable HTTP transport) |
| **Cloud** | Google Cloud (Vertex AI Agent Builder compatible) |

---

## ⚡ Quick Start (2 minutes)

### Prerequisites
- Python 3.10+
- Node.js 18+

### 1. Clone & Start Backend
```bash
cd criterion-ai/backend
python -m venv venv
# Windows:
.\venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt
python main.py
```
The backend starts on `http://localhost:8000` with **in-memory question bank** (no MongoDB setup needed for demo).

### 2. Start Frontend
```bash
cd criterion-ai/frontend
npm install
npm run dev
```
Open `http://localhost:5173` — you're ready to go!

---

## 🧠 Core Algorithms

### Auto-Grader Engine (`grader.py`)
A **two-phase grading pipeline** that mirrors Cambridge's official marking methodology:

- **Phase 1: String Normalization + Fuzzy Matching** — Normalizes mathematical notation (`²` → `^2`, `×` → `*`), extracts numerical values (including fractions), and matches against acceptable answers with configurable tolerance.
- **Dependency Chains** — A-marks (accuracy) depend on M-marks (method). If the method step fails, accuracy marks are denied unless follow-through (FT) marking applies.
- **Partial Credit** — Every step is graded independently. Students receive credit for correct methods even if the final answer is wrong.

### WTPS Algorithm (`weakness_tracker.py`)
**Weighted Topic Priority Score** — a scoring function that ranks topics by weakness:

```
WTPS(T) = 0.45 × failure_rate + 0.25 × recency_factor + 0.20 × attempt_penalty − 0.10 × streak_bonus
```

| Factor | Weight | Purpose |
|--------|--------|---------|
| Failure Rate | 0.45 | Topics with more failures are prioritized |
| Recency | 0.25 | Topics not practiced recently get higher scores |
| Attempt Penalty | 0.20 | Under-tested topics are flagged |
| Streak Bonus | -0.10 | Consecutive passes reduce priority |

---

## 📁 Project Structure

```
criterion-ai/
├── backend/
│   ├── main.py              # FastAPI entry + MCP mount + chat orchestrator
│   ├── tools.py             # 3 MCP tools (fetch, grade, update)
│   ├── database.py          # MongoDB + in-memory fallback
│   ├── grader.py            # Auto-grading engine (298 lines)
│   ├── weakness_tracker.py  # WTPS adaptive algorithm
│   ├── schemas.py           # Pydantic request validation
│   ├── seed_questions.py    # Sample Cambridge questions
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.tsx          # Chat interface + orchestration
│   │   ├── index.css        # Design system
│   │   └── main.tsx
│   ├── index.html
│   └── package.json
└── README.md
```

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/chat` | Smart orchestrator — handles all student interactions |
| `POST` | `/api/fetch-question` | Fetch a question by subject/topic/level |
| `POST` | `/api/evaluate-working` | Grade student working against mark scheme |
| `POST` | `/api/update-student-profile` | Save attempt and update weakness map |
| `GET` | `/api/weakest-topics/{id}/{subject}` | Get weakest topics ranked by WTPS |
| `GET` | `/api/student-profile/{id}` | Get full student profile |
| `GET` | `/health` | Health check |

---

## 🏆 Google Cloud Integration

Criterion AI is designed for **Vertex AI Agent Builder**:
- Backend exposes tools via **Model Context Protocol (MCP)** at `/mcp`
- OpenAPI 3.0 spec provided for Agent Builder tool registration
- REST wrappers at `/api/*` for Agent Builder OpenAPI tool integration
- Compatible with Dialogflow CX messenger widget embedding

---

## 👥 Team

| Name | Role |
|------|------|
| **Asef** | AI Orchestration (Vertex AI Agent Builder) |
| **Rayyan** | Backend & Algorithms (FastAPI, MCP, Grading Engine) |
| **Iztihad** | Frontend & Infrastructure (React, Deployment) |

---

## 📄 License

MIT — Built for the Google Cloud Rapid Agent Hackathon.
