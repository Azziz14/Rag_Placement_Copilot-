"""API version 1 router definition.
"""

from fastapi import APIRouter
from app.api.v1.auth.routes import router as auth_router
from app.routes.resume import router as resume_router
from app.routes.jd import router as jd_router
from app.routes.matcher import router as matcher_router
from app.routes.rag import router as rag_router
from app.routes.questions import router as questions_router
from app.routes.interview import router as interview_router
from app.routes.evaluation import router as evaluation_router
from app.routes.weakness import router as weakness_router
from app.routes.roadmap import router as roadmap_router
from app.routes.progress import router as progress_router
from app.routes.adaptive import router as adaptive_router
from app.routes.tailor import router as tailor_router
from app.routes.learning import router as learning_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(resume_router)
api_router.include_router(jd_router)
api_router.include_router(matcher_router)
api_router.include_router(rag_router)
api_router.include_router(questions_router)
api_router.include_router(interview_router)
api_router.include_router(evaluation_router)
api_router.include_router(weakness_router)
api_router.include_router(roadmap_router)
api_router.include_router(progress_router)
api_router.include_router(adaptive_router)
api_router.include_router(tailor_router)
api_router.include_router(learning_router)



