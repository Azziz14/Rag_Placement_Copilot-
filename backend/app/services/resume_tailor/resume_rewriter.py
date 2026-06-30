"""Module to interface with LLM for rewriting resume content.
"""

import json
import logging
import re
from app.core.config import settings
from app.services.llm_service import llm_service

logger = logging.getLogger(__name__)

def rewrite_resume(prompt: str) -> dict:
    """Invokes LLM to rewrite the resume text based on the generated prompt.
    """
    if not settings.GEMINI_API_KEY and not settings.GROQ_API_KEY:
        logger.warning("LLM keys not configured. Returning empty tailoring stub.")
        return {}
        
    try:
        text = llm_service.generate_content(prompt, temperature=0.5, response_json=True)
        text = text.strip()
        
        # Clean markdown wrappers if any
        if text.startswith("```"):
            lines = text.splitlines()
            if lines[0].startswith("```json") or lines[0].startswith("```"):
                text = "\n".join(lines[1:-1])

        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            text = match.group(0)

        return json.loads(text)
    except Exception as e:
        logger.error(f"Failed to rewrite resume content: {str(e)}")
        raise
