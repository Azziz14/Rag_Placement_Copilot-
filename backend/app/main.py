"""Main entrypoint for the FastAPI application.

This module initializes the FastAPI application, sets up middleware (CORS),
includes API routers, and defines a basic health check endpoint.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import engine, Base
from app.api.v1 import api_router
from app.models import User, Resume, JobDescription, AnswerEvaluation, WeaknessAnalysis, ImprovementRoadmap, ProgressSnapshot, AdaptiveProfile, TailoredResume


# Create database tables
Base.metadata.create_all(bind=engine)

# Auto-migration for existing database to add 'questions' column if it doesn't exist
from sqlalchemy import text
try:
    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE interview_sessions ADD COLUMN questions VARCHAR;"))
except Exception:
    pass

# Auto-migration for answer_evaluations keyword matching columns
try:
    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE answer_evaluations ADD COLUMN key_phrases VARCHAR;"))
except Exception:
    pass

try:
    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE answer_evaluations ADD COLUMN matched_key_phrases VARCHAR;"))
except Exception:
    pass

try:
    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE answer_evaluations ADD COLUMN missing_key_phrases VARCHAR;"))
except Exception:
    pass

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Set up CORS middleware
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/", tags=["Health"])
async def root():
    """Root endpoint to check API information."""
    return {
        "message": f"Welcome to {settings.PROJECT_NAME}",
        "docs_url": "/docs",
        "redoc_url": "/redoc",
        "api_version": settings.API_V1_STR
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint to verify system status."""
    return {"status": "healthy"}
