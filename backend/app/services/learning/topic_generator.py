import json
import logging
import re
from typing import List, Dict, Any, Optional
from app.services.llm_service import llm_service
from app.services.learning.domain_engine import SUPPORTED_DOMAINS, is_valid_domain

logger = logging.getLogger(__name__)

class TopicGenerator:
    """Service to prioritize learning topics using LLM based on user goals and preferences."""

    def prioritize_topics(
        self,
        domain: str,
        level: str,
        target_role: str,
        target_company: str,
        weak_topics: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Dynamically generates and ranks important topics using the LLM."""
        domain = domain.lower()
        if not is_valid_domain(domain):
            raise ValueError(f"Unsupported CS domain: '{domain}'")

        standard_topics = SUPPORTED_DOMAINS[domain]
        weak_topics = weak_topics or []

        prompt = f"""
You are an expert computer science educator and career mentor.
Given a selected CS domain, a candidate's skill level, their placement goals, and their weak areas, rank and prioritize the most important topics they should learn.

Input Details:
- Selected Domain: {domain.upper()}
- Standard Topics Registry: {json.dumps(standard_topics)}
- User Skill Level: {level}
- Target Role: {target_role}
- Target Company Type: {target_company}
- User Weak Topics: {json.dumps(weak_topics)}

Task:
1. Select the most critical topics from the Standard Topics Registry that fit the User's Target Role and Target Company.
2. Order the list by importance.
3. For each selected topic, assign:
   - A priority_score (integer from 0 to 100, where higher means more urgent/critical for interviews).
   - A difficulty_level ("Easy", "Medium", or "Hard") adapted to their skill level '{level}'.
4. Prioritize topics marked in User Weak Topics if they are highly relevant to the role.

Return ONLY a valid JSON object matching the format below. Do not wrap in markdown or include ```json.

Output Format:
{{
  "important_topics": ["Topic A", "Topic B", "Topic C"],
  "priority_score": [95, 90, 85],
  "difficulty_level": ["Medium", "Hard", "Easy"]
}}
"""
        try:
            response = llm_service.generate_content(prompt, temperature=0.3, response_json=True)
            text = response.strip()

            if text.startswith("```"):
                lines = text.splitlines()
                if lines[0].startswith("```json") or lines[0].startswith("```"):
                    text = "\n".join(lines[1:-1])

            match_json = re.search(r"\{.*\}", text, re.DOTALL)
            if match_json:
                text = match_json.group(0)

            data = json.loads(text)
            
            # Simple validation
            for k in ["important_topics", "priority_score", "difficulty_level"]:
                if k not in data or not isinstance(data[k], list):
                    data[k] = []
            
            return data
        except Exception as e:
            logger.error(f"Topic prioritization failed: {str(e)}. Falling back to default ordering.")
            # Fallback heuristic prioritization
            return self._fallback_prioritization(domain, level, weak_topics)

    def _fallback_prioritization(self, domain: str, level: str, weak_topics: List[str]) -> Dict[str, Any]:
        """Provides a safe, rule-based default fallback if LLM call fails."""
        topics = SUPPORTED_DOMAINS[domain]
        important = []
        scores = []
        levels = []

        # Prioritize weak topics first
        for topic in topics:
            if topic in weak_topics:
                important.append(topic)
                scores.append(95)
                levels.append("Medium" if level.lower() == "beginner" else "Hard")

        for topic in topics:
            if topic not in important:
                important.append(topic)
                scores.append(75)
                levels.append("Easy" if level.lower() == "beginner" else "Medium")

        return {
            "important_topics": important,
            "priority_score": scores,
            "difficulty_level": levels
        }

topic_generator = TopicGenerator()
