"""Service module for generating personalized study roadmaps based on weakness analysis.
"""

import json
import logging
from datetime import datetime
from typing import List, Dict, Any
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.interview_session import InterviewSession
from app.models.resume_match import ResumeMatch
from app.models.weakness_analysis import WeaknessAnalysis
from app.models.improvement_roadmap import ImprovementRoadmap
from app.services.rag_service import rag_service
from app.services.llm_service import llm_service

logger = logging.getLogger(__name__)


class RoadmapService:
    """Service to handle generation, prioritization, and resource recommendations for roadmap."""

    def generate_roadmap(self, db: Session, user_id: str, session_id: str) -> Dict[str, Any]:
        """Orchestrates roadmap generation, saves to database, and returns the result."""
        # 1. Fetch session & verify ownership
        session = db.query(InterviewSession).filter(
            InterviewSession.id == session_id,
            InterviewSession.user_id == user_id
        ).first()
        if not session:
            raise ValueError("Interview session not found or unauthorized.")

        # 2. Check if roadmap already exists
        existing_roadmap = db.query(ImprovementRoadmap).filter(
            ImprovementRoadmap.session_id == session_id
        ).first()
        if existing_roadmap:
            return self._format_response(existing_roadmap)

        # 3. Fetch Weakness Analysis
        weakness_analysis = db.query(WeaknessAnalysis).filter(
            WeaknessAnalysis.session_id == session_id
        ).first()
        if not weakness_analysis:
            raise ValueError("Weakness analysis not found. Please run weakness analysis first.")

        # 4. Fetch Resume Match data
        match = db.query(ResumeMatch).filter(
            ResumeMatch.id == session.match_id,
            ResumeMatch.user_id == user_id
        ).first()
        if not match:
            raise ValueError("Associated Resume-JD Match analysis not found.")

        missing_skills = match.missing_skills or []
        improvement_areas = match.improvement_areas or []

        # 5. Fetch RAG Context
        missing_skill_context = []
        dsa_context = []
        try:
            rag_context = rag_service.retrieve_all_context(db, user_id, match.id)
            missing_skill_context = rag_context.get("missing_skill_context", [])
            dsa_context = rag_context.get("dsa_context", [])
        except Exception as e:
            logger.error(f"Error fetching RAG context: {str(e)}")

        # 6. Generate Plans
        roadmap_data = self._generate_roadmap_data(
            weakness_analysis, missing_skills, improvement_areas, missing_skill_context, dsa_context
        )

        # 7. Persist Roadmap
        db_roadmap = ImprovementRoadmap(
            session_id=session_id,
            technical_plan=roadmap_data["technical_plan"],
            dsa_plan=roadmap_data["dsa_plan"],
            behavioral_plan=roadmap_data["behavioral_plan"],
            resource_recommendations=roadmap_data["resource_recommendations"]
        )
        db.add(db_roadmap)
        db.commit()
        db.refresh(db_roadmap)

        return self._format_response(db_roadmap)

    def _generate_roadmap_data(
        self,
        weakness: WeaknessAnalysis,
        missing_skills: List[str],
        improvement_areas: List[str],
        missing_skill_context: List[Dict[str, Any]],
        dsa_context: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Routes roadmap generation to LLM or rule-based fallback."""
        if settings.GEMINI_API_KEY or settings.GROQ_API_KEY:
            try:
                return self._generate_with_llm(
                    weakness, missing_skills, improvement_areas, missing_skill_context, dsa_context
                )
            except Exception as e:
                logger.error(f"LLM Roadmap generation failed: {str(e)}. Falling back to local rules.")

        # Fallback Heuristics
        tech_plan = self.generate_technical_plan(
            weakness.technical_weaknesses or [], missing_skills, missing_skill_context
        )
        dsa_plan = self.generate_dsa_plan(
            weakness.dsa_weaknesses or [], dsa_context
        )
        behavioral_plan = self.generate_behavioral_plan(
            weakness.behavioral_weaknesses or [], improvement_areas
        )
        resources = self.recommend_resources(
            weakness.priority_areas or [], missing_skill_context, dsa_context
        )

        # Apply prioritization ordering
        prioritized = self.prioritize_study_plan(
            tech_plan, dsa_plan, behavioral_plan, weakness.priority_areas or []
        )

        return {
            "technical_plan": prioritized["technical_plan"],
            "dsa_plan": prioritized["dsa_plan"],
            "behavioral_plan": prioritized["behavioral_plan"],
            "resource_recommendations": resources
        }

    def _generate_with_llm(
        self,
        weakness: WeaknessAnalysis,
        missing_skills: List[str],
        improvement_areas: List[str],
        missing_skill_context: List[Dict[str, Any]],
        dsa_context: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generates the structured improvement roadmap using Gemini."""
        prompt = f"""
You are an expert career coach, senior software engineer, and technical educator.
Analyze the candidate's weakness profile, target job gaps, and retrieved context to construct a personalized preparation roadmap.

Candidate's Weakness Profile:
- Technical Weaknesses: {json.dumps(weakness.technical_weaknesses)}
- Behavioral Weaknesses: {json.dumps(weakness.behavioral_weaknesses)}
- DSA Weaknesses: {json.dumps(weakness.dsa_weaknesses)}
- Priority Areas: {json.dumps(weakness.priority_areas)}

Target Job Description Gaps:
- Missing Skills from Resume-JD Match: {json.dumps(missing_skills)}
- Resume Match Improvement Areas: {json.dumps(improvement_areas)}

Retrieved Study Guides & Context:
- Missing Skills Context: {json.dumps([c['content'] for c in missing_skill_context])}
- DSA Context: {json.dumps([c['content'] for c in dsa_context])}

Create three distinct learning plans:
1. technical_plan: Technical concepts, tools, framework gaps, architecture.
2. dsa_plan: Algorithmic limits, problem-solving, code optimization.
3. behavioral_plan: Communications delivery, leadership storytelling, STAR format.

Each plan must be a JSON array of goal objects. Each goal object must contain:
- timeframe: "short_term", "medium_term", or "long_term" (short_term = 1-3 days, medium_term = 1-2 weeks, long_term = 3+ weeks).
- goal: A detailed, clear action item.
- priority: "high", "medium", or "low".

Also recommend a list of learning resources (resource_recommendations). For each resource:
- title: Name of the tutorial topic/tool.
- type: "documentation", "article", "video", "practice_problem", or "course".
- url: A mock/placeholder link or a real reference.
- description: Why this is recommended and what it targets.
- priority: "high", "medium", or "low" based on weakness severity and JD importance.

Return ONLY a valid JSON object matching the format below. Do not wrap in markdown or include ```json.

Output Format:
{{
  "technical_plan": [
    {{
      "timeframe": "string",
      "goal": "string",
      "priority": "string"
    }}
  ],
  "dsa_plan": [
    {{
      "timeframe": "string",
      "goal": "string",
      "priority": "string"
    }}
  ],
  "behavioral_plan": [
    {{
      "timeframe": "string",
      "goal": "string",
      "priority": "string"
    }}
  ],
  "resource_recommendations": [
    {{
      "title": "string",
      "type": "string",
      "url": "string",
      "description": "string",
      "priority": "string"
    }}
  ]
}}
"""
        response_text = llm_service.generate_content(prompt, temperature=0.4, response_json=True)
        text = response_text.strip()

        if text.startswith("```"):
            lines = text.splitlines()
            if lines[0].startswith("```json") or lines[0].startswith("```"):
                text = "\n".join(lines[1:-1])

        data = json.loads(text)
        required_keys = ["technical_plan", "dsa_plan", "behavioral_plan", "resource_recommendations"]
        for key in required_keys:
            if key not in data:
                raise ValueError(f"Missing roadmap key: {key}")

        return data

    # Core Functions (Fallback & Heuristics)
    def generate_technical_plan(
        self, technical_weaknesses: List[str], missing_skills: List[str], missing_skill_context: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Generates a list of short, medium, and long-term technical prep goals."""
        plan = []

        # Utilize weaknesses
        for w in technical_weaknesses[:2]:
            plan.append({
                "timeframe": "short_term",
                "goal": f"Review core concepts of: {w}",
                "priority": "high"
            })
            plan.append({
                "timeframe": "medium_term",
                "goal": f"Build a miniature prototype or project implementing: {w}",
                "priority": "medium"
            })

        # Utilize missing skills
        for skill in missing_skills:
            if len([x for x in plan if x["timeframe"] == "short_term"]) < 3:
                plan.append({
                    "timeframe": "short_term",
                    "goal": f"Read official documentation for missing skill: '{skill}'",
                    "priority": "high"
                })
            if len([x for x in plan if x["timeframe"] == "medium_term"]) < 3:
                plan.append({
                    "timeframe": "medium_term",
                    "goal": f"Integrate '{skill}' into a sample GitHub repository or build an API endpoint with it",
                    "priority": "medium"
                })
            if len([x for x in plan if x["timeframe"] == "long_term"]) < 3:
                plan.append({
                    "timeframe": "long_term",
                    "goal": f"Deep dive into advanced design patterns, caching, scaling and concurrency limits for {skill}",
                    "priority": "low"
                })

        # Default fallbacks
        if not [x for x in plan if x["timeframe"] == "short_term"]:
            plan.append({
                "timeframe": "short_term",
                "goal": "Revise core technical language and system architecture fundamentals.",
                "priority": "high"
            })
        if not [x for x in plan if x["timeframe"] == "medium_term"]:
            plan.append({
                "timeframe": "medium_term",
                "goal": "Mock design a highly scalable microservice on paper or diagram tool.",
                "priority": "medium"
            })
        if not [x for x in plan if x["timeframe"] == "long_term"]:
            plan.append({
                "timeframe": "long_term",
                "goal": "Review production readiness guidelines, docker setups, and CI/CD pipelines.",
                "priority": "low"
            })

        return plan

    def generate_dsa_plan(self, dsa_weaknesses: List[str], dsa_context: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generates algorithmic prep goals."""
        plan = []

        for w in dsa_weaknesses[:2]:
            plan.append({
                "timeframe": "short_term",
                "goal": f"Analyze the time/space complexities and edge cases of: {w}",
                "priority": "high"
            })
            plan.append({
                "timeframe": "medium_term",
                "goal": f"Solve 5 practice problems specifically targeting the patterns: {w}",
                "priority": "medium"
            })

        # Default DSA plan
        if not [x for x in plan if x["timeframe"] == "short_term"]:
            plan.append({
                "timeframe": "short_term",
                "goal": "Review fundamental data structures: Arrays, HashMaps, Two-Pointers, and Sliding Window.",
                "priority": "high"
            })
        if not [x for x in plan if x["timeframe"] == "medium_term"]:
            plan.append({
                "timeframe": "medium_term",
                "goal": "Solve 10 medium-level problems on Tree/Graph traversal, Binary Search, and Recursion.",
                "priority": "medium"
            })
        if not [x for x in plan if x["timeframe"] == "long_term"]:
            plan.append({
                "timeframe": "long_term",
                "goal": "Practice advanced algorithm strategies like Dynamic Programming, backtracking, and heap optimization under timed settings.",
                "priority": "low"
            })

        return plan

    def generate_behavioral_plan(self, behavioral_weaknesses: List[str], improvement_areas: List[str]) -> List[Dict[str, Any]]:
        """Generates communication and soft-skills prep goals."""
        plan = []

        for w in behavioral_weaknesses[:2]:
            plan.append({
                "timeframe": "short_term",
                "goal": f"Draft answers for weakness area: '{w}' using the STAR structure",
                "priority": "high"
            })
            plan.append({
                "timeframe": "medium_term",
                "goal": f"Record yourself explaining your approach to '{w}' and check for clarity",
                "priority": "medium"
            })

        for area in improvement_areas[:2]:
            plan.append({
                "timeframe": "long_term",
                "goal": f"Build a narrative that demonstrates growth and conflict resolution regarding '{area}'",
                "priority": "low"
            })

        if not [x for x in plan if x["timeframe"] == "short_term"]:
            plan.append({
                "timeframe": "short_term",
                "goal": "Outline 3 professional stories from your resume highlighting leadership, ownership, and failure.",
                "priority": "high"
            })
        if not [x for x in plan if x["timeframe"] == "medium_term"]:
            plan.append({
                "timeframe": "medium_term",
                "goal": "Conduct a mock interview focusing specifically on STAR formatting (Situation, Task, Action, Result).",
                "priority": "medium"
            })
        if not [x for x in plan if x["timeframe"] == "long_term"]:
            plan.append({
                "timeframe": "long_term",
                "goal": "Refine pacing, remove verbal filler words, and practice active listening methods.",
                "priority": "low"
            })

        return plan

    def recommend_resources(
        self, priority_areas: List[str], missing_skill_context: List[Dict[str, Any]], dsa_context: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Recommends specific tutorials and links based on RAG indexing and priority areas."""
        recommendations = []

        # 1. RAG Skills guides
        for ctx in missing_skill_context[:3]:
            title = ctx.get("metadata", {}).get("title", "Technology Guide")
            recommendations.append({
                "title": f"Tutorial: {title}",
                "type": "documentation",
                "url": ctx.get("metadata", {}).get("source", "https://docs.microsoft.com"),
                "description": f"Learn foundational concepts. Content reference: {ctx.get('content')[:100]}...",
                "priority": "high"
            })

        # 2. DSA guides from RAG
        for ctx in dsa_context[:2]:
            recommendations.append({
                "title": f"DSA Pattern: {ctx.get('metadata', {}).get('pattern', 'Coding Challenge')}",
                "type": "practice_problem",
                "url": "https://leetcode.com",
                "description": f"Solve coding question. Ref: {ctx.get('content')[:100]}...",
                "priority": "high" if len(recommendations) < 2 else "medium"
            })

        # Add default general resources if list is empty
        if not recommendations:
            recommendations.append({
                "title": "System Design Primer",
                "type": "documentation",
                "url": "https://github.com/donnemartin/system-design-primer",
                "description": "Learn how to build large-scale distributed systems.",
                "priority": "medium"
            })
            recommendations.append({
                "title": "Tech Interview Handbook",
                "type": "article",
                "url": "https://techinterviewhandbook.org",
                "description": "Comprehensive guide to resume, behavioral, and technical prep.",
                "priority": "medium"
            })

        return recommendations

    def prioritize_study_plan(
        self, tech_plan: List[Dict[str, Any]], dsa_plan: List[Dict[str, Any]], behavioral_plan: List[Dict[str, Any]], priority_areas: List[str]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Customizes plan priorities based on identified high importance areas."""
        for priority in priority_areas:
            p_lower = priority.lower()
            # If priority contains keywords, flag match
            for plan in [tech_plan, dsa_plan, behavioral_plan]:
                for item in plan:
                    goal_lower = item["goal"].lower()
                    if any(word in goal_lower for word in p_lower.split() if len(word) > 2):
                        item["priority"] = "high"
                        if not item["goal"].startswith("★"):
                            item["goal"] = f"★ PRIORITY: {item['goal']}"

        return {
            "technical_plan": tech_plan,
            "dsa_plan": dsa_plan,
            "behavioral_plan": behavioral_plan
        }

    def _format_response(self, roadmap: ImprovementRoadmap) -> Dict[str, Any]:
        """Formats db model to schema response dict."""
        return {
            "id": roadmap.id,
            "session_id": roadmap.session_id,
            "technical_plan": roadmap.technical_plan or [],
            "dsa_plan": roadmap.dsa_plan or [],
            "behavioral_plan": roadmap.behavioral_plan or [],
            "resource_recommendations": roadmap.resource_recommendations or [],
            "created_at": roadmap.created_at
        }


# Global service instance
roadmap_service = RoadmapService()
