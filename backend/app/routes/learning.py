import json
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.api.v1.auth.security import get_current_user
from app.models.user import User
from app.services.learning.domain_engine import get_registered_domains, is_valid_domain, SUPPORTED_DOMAINS
from app.services.learning.topic_generator import topic_generator
from app.services.learning.question_generator import question_generator
from app.services.learning.scoring_engine import scoring_engine
from app.services.code_runner.runner import code_runner
from app.services.llm_service import llm_service
from app.core.cache import file_cache

router = APIRouter(prefix="/learning", tags=["CS Learning Platform"])

# Pydantic Schemas for requests/responses
class DomainRequest(BaseModel):
    domain: str

class DomainResponse(BaseModel):
    domain: str
    topics: List[str]

class StudyRequest(BaseModel):
    domain: str
    topic: Optional[str] = None

class TrendsRequest(BaseModel):
    domain: str

class TopicPrioritizationRequest(BaseModel):
    domain: str
    level: str  # e.g., "beginner", "intermediate", "advanced"
    target_role: str  # e.g., "Backend Engineer"
    target_company: str  # e.g., "FAANG", "Startup"
    weak_topics: Optional[List[str]] = None

class TopicPrioritizationResponse(BaseModel):
    important_topics: List[str]
    priority_score: List[int]
    difficulty_level: List[str]

class QuestionGenerationRequest(BaseModel):
    domain: str
    topic: str
    difficulty: str  # "easy", "medium", "hard"
    preferred_language: Optional[str] = "python"
    force_refresh: Optional[bool] = False

class SubmissionRequest(BaseModel):
    question_data: Dict[str, Any]
    submission_data: Dict[str, Any]  # for coding: {"code": "...", "language": "..."}, for theory: {"answer": "..."} or {"choice_index": 0}

class CodeExecutionRequest(BaseModel):
    code: str
    language: str
    input_data: str


@router.post("/domain", response_model=DomainResponse, status_code=status.HTTP_200_OK)
async def get_domain_topics(payload: DomainRequest, current_user: User = Depends(get_current_user)):
    """Retrieves standard topics list for a registered domain."""
    domain_lower = payload.domain.lower()
    if not is_valid_domain(domain_lower):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported CS domain: '{payload.domain}'"
        )
    return {
        "domain": domain_lower,
        "topics": SUPPORTED_DOMAINS[domain_lower]
    }


@router.post("/topics", response_model=TopicPrioritizationResponse, status_code=status.HTTP_200_OK)
async def prioritize_topics(payload: TopicPrioritizationRequest, current_user: User = Depends(get_current_user)):
    """Dynamically generates and ranks important topics using the LLM based on user preferences."""
    try:
        results = topic_generator.prioritize_topics(
            domain=payload.domain,
            level=payload.level,
            target_role=payload.target_role,
            target_company=payload.target_company,
            weak_topics=payload.weak_topics
        )
        return results
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to prioritize topics: {str(e)}"
        )


@router.post("/questions", response_model=Dict[str, Any], status_code=status.HTTP_200_OK)
async def generate_learning_question(payload: QuestionGenerationRequest, current_user: User = Depends(get_current_user)):
    """Generates a theory or coding question dynamically for a given topic."""
    try:
        results = question_generator.generate_question(
            domain=payload.domain,
            topic=payload.topic,
            difficulty=payload.difficulty,
            language=payload.preferred_language,
            force_refresh=payload.force_refresh
        )
        return results
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate question: {str(e)}"
        )


@router.post("/submit", response_model=Dict[str, Any], status_code=status.HTTP_200_OK)
async def submit_learning_answer(payload: SubmissionRequest, current_user: User = Depends(get_current_user)):
    """Submits a theory or coding solution and evaluates it."""
    try:
        results = scoring_engine.evaluate_submission(
            question_data=payload.question_data,
            submission=payload.submission_data
        )
        return results
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to grade submission: {str(e)}"
        )


@router.post("/code/execute", response_model=Dict[str, Any], status_code=status.HTTP_200_OK)
async def execute_raw_code(payload: CodeExecutionRequest, current_user: User = Depends(get_current_user)):
    """Executes raw user code directly against standard inputs."""
    try:
        results = code_runner.execute_code(
            code=payload.code,
            language=payload.language,
            input_data=payload.input_data
        )
        return results
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Code execution wrapper failed: {str(e)}"
        )


@router.post("/explain")
async def explain_topic(payload: StudyRequest, current_user: User = Depends(get_current_user)):
    domain_key = payload.domain.lower()
    topic_key = payload.topic.lower() if payload.topic else "basics"
    cache_key = f"explain_{domain_key}_{topic_key}"
    
    cached_data = file_cache.get(cache_key)
    if cached_data:
        return cached_data

    target = payload.topic if payload.topic else payload.domain
    domain_names = {
        "dbms": "Database Management Systems",
        "sql": "SQL Querying",
        "cn": "Computer Networks",
        "os": "Operating Systems",
        "oops": "Object-Oriented Programming",
        "dsa": "Data Structures & Algorithms",
        "system_design": "System Design",
        "ml": "Machine Learning"
    }
    friendly_domain = domain_names.get(payload.domain.lower(), payload.domain)
    
    is_domain_basics = not payload.topic
    
    if is_domain_basics:
        prompt = (
            f"You are an expert computer science professor and technical interviewer.\n"
            f"Generate an extremely comprehensive, clear, and high-quality educational study guide for the core domain: '{friendly_domain}'.\n\n"
            f"Structure the explanation beautifully using Markdown headers and bold text:\n"
            f"### 1. Domain Overview\n"
            f"Define what '{friendly_domain}' is, its role in computer science, and its primary significance.\n\n"
            f"### 2. Core Pillars & Subtopics\n"
            f"Describe the essential subtopics of '{friendly_domain}' (such as key algorithms, architectural concepts, or methodologies) and why they are studied.\n\n"
            f"### 3. Real-world Importance\n"
            f"Why does this domain matter in professional software engineering? Provide concrete real-world system examples (e.g. scale, reliability).\n\n"
            f"### 4. Essential Career Skills\n"
            f"What kind of questions or problems regarding '{friendly_domain}' are candidates expected to solve in interviews?\n\n"
            f"### 5. Recommended Learning Path\n"
            f"Provide a brief bullet-pointed roadmap to master this domain from basics to advanced levels.\n\n"
            f"Ensure all content is highly accurate, educational, and engaging. Avoid generic placeholders."
        )
    else:
        prompt = (
            f"You are an expert computer science professor and technical interviewer.\n"
            f"Generate a highly specific, deep, and high-quality educational study guide focusing ONLY on the subtopic: '{target}' "
            f"within the computer science domain: '{friendly_domain}'.\n\n"
            f"IMPORTANT: The content MUST focus directly on the subtopic '{target}'. Do NOT write a generic overview of '{friendly_domain}'. "
            f"Ensure every section specifically describes, analyzes, and represents '{target}' and its implementation/architecture.\n\n"
            f"Structure the explanation beautifully using Markdown headers and bold text:\n"
            f"### 1. Conceptual Overview\n"
            f"Define '{target}' clearly and precisely, detailing its core mechanism, characteristics, and how it fits into '{friendly_domain}'.\n\n"
            f"### 2. Why It Matters & Real-world Use Case\n"
            f"Explain why '{target}' is critical in professional software engineering. Provide a real-world system scenario or concrete design example where '{target}' is leveraged.\n\n"
            f"### 3. Everyday Analogy\n"
            f"Illustrate '{target}' using a highly relatable, non-technical analogy.\n\n"
            f"### 4. Key Takeaways & Architecture Gotchas\n"
            f"Detail time/space complexity, common pitfalls/bugs, design trade-offs, and critical considerations when implementing or using '{target}'.\n\n"
            f"### 5. Practical Code/Syntax Representation\n"
            f"Provide a clean, readable code snippet or pseudo-code (in Python, SQL, or standard pseudo-code) showing a practical implementation or usage of '{target}'.\n\n"
            f"### 6. Standard Technical Interview Q&A\n"
            f"List 1-2 actual interview questions specifically testing knowledge of '{target}', along with clear, optimal answers.\n\n"
            f"Ensure all content is highly accurate, matching the subtopic '{target}' perfectly. Do not be generic."
        )
    try:
        content = llm_service.generate_content(prompt)
        result = {"explanation": content}
        file_cache.set(cache_key, result)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate study guide: {str(e)}"
        )


@router.post("/trends")
async def get_market_trends(payload: TrendsRequest, current_user: User = Depends(get_current_user)):
    domain_key = payload.domain.lower()
    cache_key = f"trends_{domain_key}"
    
    cached_data = file_cache.get(cache_key)
    if cached_data:
        return cached_data

    domain_names = {
        "dbms": "Database Management Systems",
        "sql": "SQL Querying",
        "cn": "Computer Networks",
        "os": "Operating Systems",
        "oops": "Object-Oriented Programming",
        "dsa": "Data Structures & Algorithms",
        "system_design": "System Design",
        "ml": "Machine Learning"
    }
    friendly_domain = domain_names.get(payload.domain.lower(), payload.domain)
    prompt = (
        f"Generate a JSON object containing a list of exactly 3 current (2024-2025) market trends, ecosystem updates, "
        f"or modern frameworks/methodologies specifically related to: '{friendly_domain}'. "
        f"Each trend MUST be directly relevant to '{friendly_domain}' and not a generic technology trend. "
        f"Format the output strictly as a JSON object with a single key 'trends' containing a list of objects. "
        f"Each object must have the keys: "
        f"- 'title': name of the trend (specific to {friendly_domain}) "
        f"- 'description': 2-3 sentences explaining the trend and why it matters in {friendly_domain} "
        f"- 'impact_level': string (e.g. 'High', 'Critical') "
        f"- 'is_trending': boolean true. "
        f"Do not return any conversational prefix or suffix; output only valid raw JSON."
    )
    try:
        content = llm_service.generate_content(prompt, response_json=True)
        # Attempt to parse json
        try:
            result = json.loads(content)
        except Exception:
            # Clean if markdown wrapped
            cleaned = content.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            result = json.loads(cleaned.strip())
        
        file_cache.set(cache_key, result)
        return result
    except Exception as e:
        # Fallback trends list if LLM failover fails
        fallback_result = {
            "trends": [
                {
                    "title": "Cloud-Native Infrastructure & Serverless Integration",
                    "description": "Orchestrating microservices using containerized functions, scaling dynamically to zero on demand.",
                    "impact_level": "Critical",
                    "is_trending": True
                },
                {
                    "title": "AI-Driven Copilot Code Optimizations",
                    "description": "Leveraging generative LLMs to autogenerate tests, perform lint checks, and improve system design blueprints.",
                    "impact_level": "High",
                    "is_trending": True
                },
                {
                    "title": "Real-time Streaming Analytics & Event-Driven Architecture",
                    "description": "Moving from batch processing to instant streaming pipelines (like Kafka, Redpanda) to process high volumes of data.",
                    "impact_level": "High",
                    "is_trending": True
                }
            ]
        }
        file_cache.set(cache_key, fallback_result)
        return fallback_result
