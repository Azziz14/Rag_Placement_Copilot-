"""Service module for analyzing candidate weaknesses from mock interview evaluations.

Utilizes Gemini LLM to find pattern-based weaknesses and prioritize them,
with a robust local fallback rule-based aggregation service.
"""

import json
import logging
from typing import List, Dict, Any, Union
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.interview_session import InterviewSession
from app.models.resume_match import ResumeMatch
from app.models.answer_evaluation import AnswerEvaluation
from app.models.interview_answer import InterviewAnswer
from app.models.weakness_analysis import WeaknessAnalysis
from app.services.llm_service import llm_service

logger = logging.getLogger(__name__)


class WeaknessService:
    """Service to handle aggregated weakness analysis and prioritization."""

    def analyze_session_weaknesses(
        self, db: Session, user_id: str, session_id: str
    ) -> Dict[str, Any]:
        """Runs weakness analysis for a session, persists results, and returns the report."""
        # 1. Fetch session & verify ownership
        session = db.query(InterviewSession).filter(
            InterviewSession.id == session_id,
            InterviewSession.user_id == user_id
        ).first()
        if not session:
            raise ValueError("Interview session not found or unauthorized.")

        # 2. Check if weakness analysis already exists
        existing_analysis = db.query(WeaknessAnalysis).filter(
            WeaknessAnalysis.session_id == session_id
        ).first()
        if existing_analysis:
            return self._format_response(existing_analysis)

        # 3. Fetch evaluations & resume match data
        evaluations = db.query(AnswerEvaluation).filter(
            AnswerEvaluation.session_id == session_id
        ).all()
        if not evaluations:
            raise ValueError("No evaluations found for this session. Please evaluate answers first.")

        # Resolve match data
        match = db.query(ResumeMatch).filter(
            ResumeMatch.id == session.match_id,
            ResumeMatch.user_id == user_id
        ).first()

        missing_skills = match.missing_skills if match else []
        improvement_areas = match.improvement_areas if match else []

        # 4. Perform analysis
        analysis_data = self._perform_analysis(evaluations, missing_skills, improvement_areas)

        # 5. Persist analysis results
        db_analysis = WeaknessAnalysis(
            session_id=session_id,
            technical_weaknesses=analysis_data["technical_weaknesses"],
            behavioral_weaknesses=analysis_data["behavioral_weaknesses"],
            dsa_weaknesses=analysis_data["dsa_weaknesses"],
            communication_weaknesses=analysis_data["communication_weaknesses"],
            priority_areas=analysis_data["priority_areas"]
        )
        db.add(db_analysis)
        db.commit()
        db.refresh(db_analysis)

        return self._format_response(db_analysis)

    def _perform_analysis(
        self, evaluations: List[AnswerEvaluation], missing_skills: List[str], improvement_areas: List[str]
    ) -> Dict[str, Any]:
        """Routes analysis to Gemini LLM or falls back to local rules-based engine."""
        if settings.GEMINI_API_KEY or settings.GROQ_API_KEY:
            try:
                return self._analyze_with_llm(evaluations, missing_skills, improvement_areas)
            except Exception as e:
                logger.error(f"LLM weakness analysis failed: {str(e)}. Falling back to local rules.")

        # Heuristic fallback
        tech = self.aggregate_technical_weaknesses(evaluations, missing_skills)
        behavioral = self.aggregate_behavioral_weaknesses(evaluations, improvement_areas)
        dsa = self.aggregate_dsa_weaknesses(evaluations)
        comm = self.aggregate_communication_weaknesses(evaluations)
        priority = self.prioritize_weaknesses(tech, behavioral, dsa, comm, missing_skills, improvement_areas)

        return {
            "technical_weaknesses": tech,
            "behavioral_weaknesses": behavioral,
            "dsa_weaknesses": dsa,
            "communication_weaknesses": comm,
            "priority_areas": priority
        }

    def _analyze_with_llm(
        self, evaluations: List[AnswerEvaluation], missing_skills: List[str], improvement_areas: List[str]
    ) -> Dict[str, Any]:
        """Triggers Gemini LLM pattern analysis on all evaluations to extract consolidated weaknesses."""
        # Clean evaluations input for prompt tokens savings
        eval_summary = []
        for index, ev in enumerate(evaluations):
            eval_summary.append({
                "question_index": index + 1,
                "category": ev.answer.category if ev.answer else "unknown",
                "scores": {
                    "overall": ev.overall_score,
                    "relevance": ev.relevance_score,
                    "depth": ev.depth_score,
                    "clarity": ev.clarity_score,
                    "accuracy": ev.technical_accuracy_score,
                    "confidence": ev.confidence_score
                },
                "weaknesses": ev.weaknesses or [],
                "suggestions": ev.suggestions or []
            })

        prompt = f"""
You are a career development expert and senior technical interviewer.
Analyze the following mock interview session results to perform a detailed Weakness Analysis.

---
EVALUATIONS LIST:
{json.dumps(eval_summary, indent=2)}

RESUME-JD MATCHING GAPS:
- Missing Skills: {json.dumps(missing_skills)}
- Resume Match Improvement Areas: {json.dumps(improvement_areas)}
---

Identify recurring patterns, group them by category, and generate detailed lists:
1. technical_weaknesses: Focus on technical concepts, architecture, missing tools, or project gaps.
2. behavioral_weaknesses: Focus on communication values, conflict management, structural storytelling, or STAR alignment.
3. dsa_weaknesses: Algorithmic limits, runtime trade-offs, code optimization, or complexity understanding.
4. communication_weaknesses: Readability, sentence flow, speech fillers, clarity of explanations, or lack of confidence.

Finally, compile a list of priority_areas. Rank these areas by order of urgency based on:
- Lower scores in the mock interview
- High importance of the skills for the target job description (refer to Missing Skills and Matching Gaps)
- Frequency of occurrence of this weakness during the interview.

Return ONLY a valid JSON object matching the format below. Do not wrap in markdown or include ```json.

Output Format:
{{
  "technical_weaknesses": ["string"],
  "behavioral_weaknesses": ["string"],
  "dsa_weaknesses": ["string"],
  "communication_weaknesses": ["string"],
  "priority_areas": ["string"]
}}
"""
        response_text = llm_service.generate_content(prompt, temperature=0.3, response_json=True)
        text = response_text.strip()

        if text.startswith("```"):
            lines = text.splitlines()
            if lines[0].startswith("```json") or lines[0].startswith("```"):
                text = "\n".join(lines[1:-1])

        data = json.loads(text)
        required_keys = ["technical_weaknesses", "behavioral_weaknesses", "dsa_weaknesses", "communication_weaknesses", "priority_areas"]
        for key in required_keys:
            if key not in data:
                raise ValueError(f"Missing weakness analysis key: {key}")

        return data

    # Core Aggregation & Heuristics
    def aggregate_technical_weaknesses(
        self, evaluations: List[AnswerEvaluation], missing_skills: List[str]
    ) -> List[str]:
        """Aggregates technical weaknesses from evaluations and resume match gaps."""
        weaknesses = []
        for ev in evaluations:
            category = ev.answer.category if ev.answer else "unknown"
            if category in ["technical", "project"] and ev.technical_accuracy_score < 80:
                if ev.weaknesses:
                    weaknesses.extend(ev.weaknesses)

        # Merge missing skills gaps
        for skill in missing_skills[:3]:
            weaknesses.append(f"Demonstrated lack of experience or depth with critical JD skill: '{skill}'.")

        # Deduplicate and limit
        seen = set()
        deduped = [x for x in weaknesses if not (x in seen or seen.add(x))]
        return deduped[:5]

    def aggregate_behavioral_weaknesses(
        self, evaluations: List[AnswerEvaluation], improvement_areas: List[str]
    ) -> List[str]:
        """Aggregates behavioral and cultural alignment weaknesses."""
        weaknesses = []
        for ev in evaluations:
            category = ev.answer.category if ev.answer else "unknown"
            if category == "behavioral" and ev.relevance_score < 80:
                if ev.weaknesses:
                    weaknesses.extend(ev.weaknesses)

        for area in improvement_areas[:3]:
            weaknesses.append(f"Matching Gap identified: '{area}'.")

        seen = set()
        deduped = [x for x in weaknesses if not (x in seen or seen.add(x))]
        return deduped[:5]

    def aggregate_dsa_weaknesses(self, evaluations: List[AnswerEvaluation]) -> List[str]:
        """Aggregates algorithm and problem-solving weaknesses."""
        weaknesses = []
        for ev in evaluations:
            category = ev.answer.category if ev.answer else "unknown"
            if category == "dsa" and ev.technical_accuracy_score < 80:
                if ev.weaknesses:
                    weaknesses.extend(ev.weaknesses)

        seen = set()
        deduped = [x for x in weaknesses if not (x in seen or seen.add(x))]
        return deduped[:5]

    def aggregate_communication_weaknesses(self, evaluations: List[AnswerEvaluation]) -> List[str]:
        """Aggregates communication, speech filler, and explanation clarity weaknesses."""
        weaknesses = []
        low_clarity_count = 0
        low_confidence_count = 0

        for ev in evaluations:
            if ev.clarity_score < 75:
                low_clarity_count += 1
                if ev.weaknesses:
                    # Look for communication-relevant weaknesses
                    comm_weak = [w for w in ev.weaknesses if any(k in w.lower() for k in ["structure", "brief", "detail", "clear", "narrative"])]
                    weaknesses.extend(comm_weak)
            if ev.confidence_score < 75:
                low_confidence_count += 1
                if ev.weaknesses:
                    conf_weak = [w for w in ev.weaknesses if any(k in w.lower() for k in ["filler", "confidence", "hesita", "maybe", "sure"])]
                    weaknesses.extend(conf_weak)

        # Add generalized summaries if thresholds crossed
        if low_clarity_count >= 2:
            weaknesses.append("Recurring issue structuring technical answers cleanly; explanations tend to lack structured STAR framing.")
        if low_confidence_count >= 2:
            weaknesses.append("Frequent use of hesitation markers (e.g. 'um', 'like') or non-declarative endings during verbal delivery.")

        seen = set()
        deduped = [x for x in weaknesses if not (x in seen or seen.add(x))]
        return deduped[:5]

    def prioritize_weaknesses(
        self, tech: List[str], behavioral: List[str], dsa: List[str], comm: List[str],
        missing_skills: List[str], improvement_areas: List[str]
    ) -> List[str]:
        """Prioritizes areas of focus based on target relevance and category scoring weight."""
        priorities = []

        # 1. Target JD missing skills (highest priority for preparation)
        for skill in missing_skills[:2]:
            priorities.append(f"Bridge critical technology gap in target JD: '{skill}'")

        # 2. DSA/Technical weaknesses that impact core evaluation
        if dsa:
            priorities.append(f"Improve algorithmic and coding accuracy: {dsa[0]}")
        if tech:
            priorities.append(f"Reinforce system architecture knowledge: {tech[0]}")

        # 3. Behavioral and communication improvements
        if comm:
            priorities.append(f"Enhance communication delivery: {comm[0]}")
        if behavioral:
            priorities.append(f"Practice behavioral storytelling: {behavioral[0]}")

        # Ensure unique, up to 5 prioritized elements
        seen = set()
        deduped = [x for x in priorities if not (x in seen or seen.add(x))]
        return deduped[:5]

    def _format_response(self, analysis: WeaknessAnalysis) -> Dict[str, Any]:
        """Formats the db model into response json structure."""
        return {
            "id": analysis.id,
            "session_id": analysis.session_id,
            "technical_weaknesses": analysis.technical_weaknesses or [],
            "behavioral_weaknesses": analysis.behavioral_weaknesses or [],
            "dsa_weaknesses": analysis.dsa_weaknesses or [],
            "communication_weaknesses": analysis.communication_weaknesses or [],
            "priority_areas": analysis.priority_areas or [],
            "created_at": analysis.created_at
        }


# Global service instance
weakness_service = WeaknessService()
