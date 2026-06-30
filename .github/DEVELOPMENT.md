# Development Guide

Internal development principles and architecture decisions for contributors and maintainers.

## Development Principles

- **Build one module at a time** — Focus on single components sequentially. Never generate the whole project at once.
- **Wait after every module** — Allow review, testing, and alignment before proceeding.
- **Clean architecture** — Maintain clear separation of concerns across API, services, models, and schemas.
- **Modular backend** — Structured directory setup: `api/`, `core/`, `services/`, `models/`, `schemas/`, `vectorstore/`.
- **Component-driven frontend** — Reusable components with hooks and utilities.
- **Production-grade code only** — Clean, robust, well-typed, and secure. No shortcuts.

## Tech Decisions

| Concern | Choice | Rationale |
|---|---|---|
| Backend framework | FastAPI | Async-native, auto OpenAPI docs, excellent typing support |
| ORM | SQLAlchemy | Mature, supports migrations, DB-agnostic |
| Database (dev) | SQLite | Zero-config local development |
| Database (prod) | PostgreSQL | Battle-tested, ACID compliant, hosted on Supabase or Render |
| Vector store | ChromaDB | Lightweight, file-persistent, no external service needed in dev |
| LLM | Google Gemini 2.5 Flash | Fast inference, generous free tier, strong reasoning |
| Auth | Supabase | Hosted auth with JWT, social logins, RLS support |
| NLP | spaCy | Fast, production-ready, good English model coverage |
| Frontend | React 19 + Vite | Modern, fast HMR, small bundle |
| Routing | React Router v7 | Industry standard, nested routes support |

## Code Standards

### Python

- All functions and classes must have **docstrings**.
- Use **type hints** on all function signatures.
- Keep service functions focused — single responsibility.
- Use Pydantic schemas for all request/response validation.
- Never commit secrets or API keys.

### JavaScript / React

- Functional components with hooks only — no class components.
- Extract API calls into `services/api.js`.
- Keep pages thin — move logic to custom hooks or services.
- Use descriptive variable names.

## Local Development Workflow

```bash
# Start backend (from /backend)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Start frontend (from /frontend)
npm run dev
```

The backend auto-falls back to SQLite locally — no database setup required for development.

## Adding a New Feature

1. Define the **SQLAlchemy model** in `backend/app/models/`
2. Register the model in `backend/app/models/__init__.py`
3. Define **Pydantic schemas** in `backend/app/schemas/`
4. Implement **business logic** in `backend/app/services/`
5. Create **API routes** in `backend/app/routes/` or `backend/app/api/v1/`
6. Register routes in `backend/app/api/v1/__init__.py`
7. Build the **frontend page/component** in `frontend/src/pages/` or `frontend/src/components/`
8. Add the route to `frontend/src/App.jsx`
