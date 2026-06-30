# Changelog

All notable changes to InterviewPilot AI will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Planned
- WebSocket support for real-time interview feedback
- Voice-to-text answer input
- Multi-language support
- OAuth provider integrations (Google, GitHub)

---

## [1.0.0] - 2025-07-01

### Added
- **Resume Parser** — PDF and DOCX resume parsing with spaCy NLP skill extraction
- **JD Parser** — Job description ingestion and keyword extraction
- **Resume–JD Matcher** — Cosine similarity scoring with versioned match history
- **RAG Interview Engine** — ChromaDB vector store + Gemini LLM for contextual question generation
- **Mock Interview Sessions** — Timed sessions with per-question tracking
- **Answer Evaluation** — LLM-based scoring on relevance, depth, and keyword matching
- **Weakness Analysis** — Automated skill gap identification from session history
- **Improvement Roadmap** — Week-by-week personalized study plan generation
- **Progress Analytics** — Session performance trends and score tracking
- **Adaptive Profile** — Dynamic difficulty adjustment based on performance history
- **Resume Tailoring** — LLM-powered resume rewriting to target specific JDs
- **Learning Hub** — Domain-specific practice questions (coding, system design, behavioural)
- **Supabase Auth** — JWT-based authentication with refresh token support
- **FastAPI Backend** — Async REST API with auto-generated OpenAPI documentation
- **React Frontend** — Full SPA with protected routes and dashboard
- **Docker Support** — Dockerized backend for containerised deployment
- **Render Deployment** — `render.yaml` for one-click cloud deployment

---

[Unreleased]: https://github.com/Azziz14/Rag_Placement_Copilot-/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/Azziz14/Rag_Placement_Copilot-/releases/tag/v1.0.0
