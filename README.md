<div align="center">

<img src="frontend/public/favicon.svg" alt="InterviewPilot AI Logo" width="80" height="80" />

# InterviewPilot AI

**An AI-powered, RAG-driven interview preparation platform that adapts to your resume and target job.**

[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-19-61DAFB?style=flat-square&logo=react&logoColor=black)](https://reactjs.org/)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Vite](https://img.shields.io/badge/Vite-8.x-646CFF?style=flat-square&logo=vite&logoColor=white)](https://vitejs.dev/)
[![Supabase](https://img.shields.io/badge/Supabase-Auth-3ECF8E?style=flat-square&logo=supabase&logoColor=white)](https://supabase.com/)
[![Gemini](https://img.shields.io/badge/Gemini-2.5_Flash-4285F4?style=flat-square&logo=google&logoColor=white)](https://deepmind.google/technologies/gemini/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](LICENSE)

[Live Demo](#) · [API Docs](http://localhost:8000/docs) · [Report Bug](https://github.com/Azziz14/Rag_Placement_Copilot-/issues) · [Request Feature](https://github.com/Azziz14/Rag_Placement_Copilot-/issues)

</div>

---

## 📖 Table of Contents

- [About the Project](#about-the-project)
- [Key Features](#key-features)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Backend Setup](#backend-setup)
  - [Frontend Setup](#frontend-setup)
- [Environment Variables](#environment-variables)
- [Project Structure](#project-structure)
- [API Reference](#api-reference)
- [Deployment](#deployment)
- [Contributing](#contributing)
- [License](#license)

---

## About the Project

**InterviewPilot AI** transforms interview preparation by combining **Retrieval-Augmented Generation (RAG)** with adaptive learning. Upload your resume and a job description — the platform parses both, identifies skill gaps, generates tailored interview questions, evaluates your answers with an LLM, and produces a personalized improvement roadmap.

Unlike static mock-interview tools, InterviewPilot continuously adapts its question difficulty and topic focus based on your performance history.

---

## Key Features

| Feature | Description |
|---|---|
| 📄 **Resume Parsing** | Extracts skills, experience, and education from PDF/DOCX resumes |
| 🎯 **JD Matching** | Compares resume against job descriptions to compute match scores |
| 🧠 **RAG Interview Engine** | Generates contextual interview questions using vector search + Gemini LLM |
| 🎤 **Mock Interview Sessions** | Timed, interactive interview sessions with real-time answer evaluation |
| 📊 **Answer Evaluation** | Scores answers on relevance, depth, keyword matching, and communication |
| 📉 **Weakness Analysis** | Identifies skill gaps and knowledge blind spots automatically |
| 🗺️ **Improvement Roadmap** | Generates a week-by-week personalized study plan |
| 📈 **Progress Analytics** | Tracks performance trends across all sessions |
| 🔄 **Adaptive Profiling** | Adjusts question difficulty based on your evolving performance |
| ✏️ **Resume Tailoring** | Rewrites your resume sections to better match a target JD |
| 🏋️ **Learning Hub** | Domain-specific practice questions for coding, system design, and more |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Client (React + Vite)                   │
│   Dashboard · Interview · Match Analysis · Roadmap · Analytics  │
└─────────────────────────┬───────────────────────────────────────┘
                          │ REST API (JSON)
┌─────────────────────────▼───────────────────────────────────────┐
│                    FastAPI Backend (Python 3.11)                 │
│                                                                 │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────────────┐  │
│  │  Auth Layer │  │ API Routers  │  │   Business Services    │  │
│  │  (Supabase) │  │  /api/v1/... │  │  RAG · Eval · Roadmap  │  │
│  └─────────────┘  └──────────────┘  └────────────────────────┘  │
│                                                                 │
│  ┌──────────────────────┐  ┌──────────────────────────────────┐  │
│  │   Gemini LLM Layer   │  │         Vector Store             │  │
│  │  (google-generativeai│  │   (ChromaDB — local/persistent)  │  │
│  └──────────────────────┘  └──────────────────────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │             SQLite (dev) / PostgreSQL (prod)             │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Tech Stack

### Backend
- **[FastAPI](https://fastapi.tiangolo.com/)** — High-performance async REST API framework
- **[SQLAlchemy](https://www.sqlalchemy.org/)** — ORM with SQLite (dev) / PostgreSQL (prod)
- **[Google Gemini](https://deepmind.google/technologies/gemini/)** — LLM for question generation & evaluation
- **[ChromaDB](https://www.trychroma.com/)** — Persistent local vector store for RAG
- **[Supabase](https://supabase.com/)** — Authentication & JWT management
- **[spaCy](https://spacy.io/)** — NLP for resume/JD skill extraction
- **[PyMuPDF](https://pymupdf.readthedocs.io/) / [pdfplumber](https://github.com/jsvine/pdfplumber)** — PDF parsing
- **[python-docx](https://python-docx.readthedocs.io/)** — Word document support

### Frontend
- **[React 19](https://reactjs.org/)** + **[Vite 8](https://vitejs.dev/)** — Fast, modern UI
- **[React Router v7](https://reactrouter.com/)** — Client-side routing
- **[Lucide React](https://lucide.dev/)** — Icon library
- **[Axios](https://axios-http.com/)** — HTTP client

---

## Getting Started

### Prerequisites

- **Python 3.11+**
- **Node.js 20+** and **npm 10+**
- A **Supabase** project ([free tier](https://supabase.com/))
- A **Google Gemini API key** ([get one free](https://aistudio.google.com/app/apikey))

### Backend Setup

```bash
# 1. Clone the repository
git clone https://github.com/Azziz14/Rag_Placement_Copilot-.git
cd Rag_Placement_Copilot-

# 2. Create and activate a virtual environment
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

# 3. Install Python dependencies
pip install -r backend/requirements.txt

# 4. Download the required spaCy NLP model
python -m spacy download en_core_web_sm

# 5. Configure environment variables
cp backend/.env.example backend/.env
# Edit backend/.env with your credentials

# 6. Start the backend server
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be live at **http://localhost:8000**  
Interactive docs: **http://localhost:8000/docs**

### Frontend Setup

```bash
# From the project root
cd frontend

# Install dependencies
npm install

# Configure environment
cp .env.example .env   # if you have frontend env vars
# Edit .env with your Supabase URL and anon key

# Start the dev server
npm run dev
```

The frontend will be live at **http://localhost:5173**

---

## Environment Variables

Copy `backend/.env.example` to `backend/.env` and fill in your values:

| Variable | Description | Required |
|---|---|:---:|
| `PROJECT_NAME` | API display name | ✅ |
| `POSTGRES_SERVER` | PostgreSQL host | ✅ (prod) |
| `POSTGRES_USER` | PostgreSQL username | ✅ (prod) |
| `POSTGRES_PASSWORD` | PostgreSQL password | ✅ (prod) |
| `POSTGRES_DB` | PostgreSQL database name | ✅ (prod) |
| `SUPABASE_URL` | Your Supabase project URL | ✅ |
| `SUPABASE_KEY` | Supabase anon public key | ✅ |
| `SUPABASE_JWT_SECRET` | JWT secret for token verification | ✅ |
| `SUPABASE_SERVICE_ROLE_KEY` | Service role key (admin ops) | ✅ |
| `GEMINI_API_KEY` | Google Gemini API key | ✅ |
| `GEMINI_MODEL` | Gemini model version | ✅ |

> **Note:** In development, the backend automatically falls back to a local SQLite database (`interviewpilot.db`) if no PostgreSQL connection is available.

---

## Project Structure

```
InterviewPilot-AI/
├── .github/                    # GitHub configuration
│   ├── workflows/              # CI/CD pipelines
│   ├── ISSUE_TEMPLATE/         # Issue templates
│   └── PULL_REQUEST_TEMPLATE.md
│
├── backend/                    # FastAPI application
│   ├── app/
│   │   ├── api/v1/             # Versioned API routers
│   │   │   └── auth/           # Auth endpoints & JWT security
│   │   ├── core/               # Config, database, caching
│   │   ├── models/             # SQLAlchemy ORM models
│   │   ├── schemas/            # Pydantic request/response schemas
│   │   ├── services/           # Business logic layer
│   │   │   ├── learning/       # Adaptive learning engine
│   │   │   ├── resume_tailor/  # Resume rewriting service
│   │   │   └── code_runner/    # Code execution sandbox
│   │   ├── routes/             # Legacy route handlers
│   │   ├── vectorstore/        # ChromaDB integration
│   │   └── main.py             # Application entrypoint
│   ├── Dockerfile
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/                   # React + Vite application
│   ├── public/                 # Static assets
│   └── src/
│       ├── components/         # Reusable UI components
│       ├── context/            # React context providers
│       ├── pages/              # Route-level page components
│       └── services/           # API client & Supabase client
│
├── docs/                       # Project documentation
│   ├── API_PLAN.md
│   ├── DATABASE.md
│   ├── FEATURES.md
│   ├── PRD.md
│   └── WORKFLOW.md
│
├── architecture/               # Architecture diagrams & specs
├── datasets/                   # Training/seed datasets
├── prompts/                    # LLM prompt templates
├── render.yaml                 # Render.com deployment config
├── CHANGELOG.md
├── CONTRIBUTING.md
└── LICENSE
```

---

## API Reference

The full interactive API documentation is auto-generated by FastAPI:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI JSON**: `http://localhost:8000/api/v1/openapi.json`

Key endpoint groups:

| Prefix | Description |
|---|---|
| `POST /api/v1/resume/upload` | Upload and parse a resume |
| `POST /api/v1/jd/upload` | Upload a job description |
| `GET /api/v1/matcher/score` | Get resume–JD match score |
| `POST /api/v1/interview/start` | Start a new interview session |
| `POST /api/v1/evaluation/submit` | Submit and evaluate an answer |
| `GET /api/v1/weakness/analysis` | Get weakness analysis report |
| `GET /api/v1/roadmap/generate` | Generate improvement roadmap |
| `GET /api/v1/progress/analytics` | Fetch progress analytics |

---

## Deployment

The project includes a [`render.yaml`](render.yaml) for one-click deployment to **[Render](https://render.com/)**.

```bash
# The backend is Dockerized for easy deployment
docker build -t interviewpilot-backend ./backend
docker run -p 8000:8000 --env-file backend/.env interviewpilot-backend
```

For production, set `DATABASE_URL` to your PostgreSQL connection string and configure all environment variables on your host.

---

## Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) before submitting a pull request.

1. Fork the repository
2. Create your feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'feat: add amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

---

## License

Distributed under the **MIT License**. See [LICENSE](LICENSE) for more information.

---

<div align="center">

Made with ❤️ by [Azziz14](https://github.com/Azziz14)

</div>
