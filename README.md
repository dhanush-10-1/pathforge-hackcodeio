# PathForge — AI-Driven Adaptive Onboarding Engine

> Parse what you claim, prove what you actually know, and only then generate your path from scratch — not from a pre-authored menu.

Built for **HackCode.io 2026** — 48-Hour Hackathon

---

## 🎯 Problem

Current corporate onboarding uses static "one-size-fits-all" curricula. Experienced hires waste time on known concepts while beginners get overwhelmed.

## 💡 Our Solution — Two Gaps We Solve

| Gap | Problem | Our Fix |
|-----|---------|---------|
| **Gap 1** | Resume → path is a black box | Fine-tuned BERT NER extracts real skills from resume text |
| **Gap 2** | No skill verification | Diagnostic quiz verifies actual skill levels before generating path |

## ⚡ Adaptive Logic (100% Original)

1. **Gap Calculator** — `gap = required_level - verified_level`
2. **Priority Scorer** — `priority = gap_size × 0.6 + role_importance × 0.4`
3. **Path Sequencer** — Topological sort (Kahn's algorithm) on skill dependency graph

Every module includes a human-readable reason:
> "You scored 2/5 in FastAPI but Backend Engineer requires 4/5."

---

## 🏗️ Architecture

```
Frontend (Next.js) → Backend (FastAPI) → ML Service (FastAPI)
    :3000                :8000               :8001
        \
         \-> External Quiz Portal :8900
                           ↕
                    PostgreSQL :5432
```

### Project Structure
```
pathforge/
├── docker-compose.yml      # 4 services: frontend, backend, ml, postgres
├── .env.example            # Environment variables template
├── frontend/               # Next.js — Landing, Onboarding, Quiz, Pathway
├── backend/                # FastAPI — Auth, Resume, Quiz, Pathway APIs
├── ml/                     # FastAPI — BERT, SBERT, Quiz Gen, Adaptive Engine
└── data/                   # O*NET skills taxonomy + skill dependencies
```

---

## 🚀 Quick Start

### Docker Compose (Recommended)
```bash
cp .env.example .env
docker-compose up --build
```

Open [http://localhost:3000](http://localhost:3000)

### Manual Development

**ML Service:**
```bash
cd ml
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

**Backend:**
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

---

## 🧠 ML Models (Citations)

| Model | Purpose | Citation |
|-------|---------|----------|
| Fine-tuned `bert-base-uncased` | Skill NER from resume text | Devlin et al., 2018 — [BERT Paper](https://arxiv.org/abs/1810.04805) |
| `all-MiniLM-L6-v2` | Role → competency mapping | Reimers & Gurevych, 2019 — [Sentence-BERT](https://arxiv.org/abs/1908.10084) |
| TF-IDF Quiz Generator | Diagnostic MCQ generation | Rule-based on O*NET descriptions |

**Data Sources:**
- [O*NET Database](https://www.onetonline.org/) — Skills taxonomy
- [Kaggle Resume Dataset](https://www.kaggle.com/) — Training data for skill extraction

---

## 📡 API Endpoints

### ML Service (`:8001`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/ml/extract-skills` | Extract skills from resume text |
| POST | `/api/ml/map-role` | Map role to competency profile |
| GET | `/api/ml/roles` | List available roles |
| POST | `/api/ml/generate-quiz` | Generate diagnostic MCQ quiz |
| POST | `/api/ml/grade-quiz` | Grade quiz responses |
| POST | `/api/ml/generate-pathway` | Generate adaptive learning pathway |

### Backend (`:8000`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register` | Register new user |
| POST | `/api/auth/login` | Login |
| POST | `/api/resume/upload` | Upload resume (PDF/text) |
| POST | `/api/quiz/start` | Start diagnostic quiz |
| POST | `/api/quiz/submit` | Submit quiz answers |
| POST | `/api/quiz/external-submit` | Accept externally graded quiz results (quiz portal callback) |
| GET | `/api/quiz/{id}/results` | Get quiz results |
| POST | `/api/pathway/generate` | Generate learning pathway |
| GET | `/api/pathway/{id}` | Get saved pathway |

---

## 🛠️ Tech Stack

- **Frontend:** Next.js 14, React 18, TypeScript
- **Backend:** FastAPI, SQLAlchemy (async), PostgreSQL
- **ML Service:** FastAPI, scikit-learn, BERT (via transformers)
- **Database:** PostgreSQL (Supabase for production)
- **Containerization:** Docker + Docker Compose

---

## 🔗 External Quiz Flow

1. Candidate selects role first in onboarding.
2. Candidate uploads resume; skills + experience are extracted.
3. Backend creates an adaptive quiz session and frontend shows link to `http://localhost:8900`.
4. Quiz is conducted and graded on the external quiz portal.
5. Portal posts results to backend `/api/quiz/external-submit` with `QUIZ_CALLBACK_SECRET`.
6. Candidate returns to pathway page, and results are used for pathway generation.

---

## 👥 Team

Built with ❤️ for HackCode.io 2026