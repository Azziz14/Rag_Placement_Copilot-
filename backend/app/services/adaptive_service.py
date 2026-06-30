"""Service module for aggregating user performance and generating adaptive preparation profiles.
"""

import json
import logging
from datetime import datetime
from typing import List, Dict, Any
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.interview_session import InterviewSession
from app.models.answer_evaluation import AnswerEvaluation
from app.models.weakness_analysis import WeaknessAnalysis
from app.models.improvement_roadmap import ImprovementRoadmap
from app.models.progress_snapshot import ProgressSnapshot
from app.models.adaptive_profile import AdaptiveProfile
from app.models.resume_match import ResumeMatch
from app.services.llm_service import llm_service

logger = logging.getLogger(__name__)


class AdaptiveService:
    """Service to generate and persist adaptive preparation profiles for users."""

    def generate_adaptive_profile(self, db: Session, user_id: str, force_refresh: bool = False) -> Dict[str, Any]:
        """Aggregates user history, generates the adaptive preparation profile, saves it, and returns the result."""
        latest_match = db.query(ResumeMatch).filter(
            ResumeMatch.user_id == user_id
        ).order_by(ResumeMatch.created_at.desc()).first()

        # Check if there is an existing profile to reuse (caching)
        existing_profile = db.query(AdaptiveProfile).filter(
            AdaptiveProfile.user_id == user_id
        ).order_by(AdaptiveProfile.created_at.desc()).first()

        if existing_profile and not force_refresh:
            latest_session = db.query(InterviewSession).filter(
                InterviewSession.user_id == user_id
            ).order_by(InterviewSession.started_at.desc()).first()
            
            is_dirty = False
            if latest_session and (existing_profile.created_at < latest_session.started_at or (latest_session.ended_at and existing_profile.created_at < latest_session.ended_at)):
                is_dirty = True
            if latest_match and existing_profile.created_at < latest_match.created_at:
                is_dirty = True
                
            if not is_dirty:
                logger.info(f"Returning cached adaptive profile for user {user_id}")
                return self._format_response(existing_profile)

        # 1. Fetch historical data
        sessions = db.query(InterviewSession).filter(
            InterviewSession.user_id == user_id
        ).order_by(InterviewSession.started_at.asc()).all()

        if not sessions:
            # Return default baseline profile for new users
            baseline = self._create_baseline_profile(user_id, latest_match)
            profile = AdaptiveProfile(
                user_id=user_id,
                next_focus_areas=baseline["next_focus_areas"],
                difficulty_adjustments=baseline["difficulty_adjustments"],
                priority_questions=baseline["priority_questions"],
                recommended_interview_type=baseline["recommended_interview_type"]
            )
            db.add(profile)
            db.commit()
            db.refresh(profile)
            return self._format_response(profile)

        session_ids = [s.id for s in sessions]

        # Fetch progress snapshots, weakness analyses, answer evaluations, roadmaps
        snapshots = db.query(ProgressSnapshot).filter(
            ProgressSnapshot.user_id == user_id
        ).order_by(ProgressSnapshot.created_at.desc()).all()

        weaknesses = db.query(WeaknessAnalysis).filter(
            WeaknessAnalysis.session_id.in_(session_ids)
        ).order_by(WeaknessAnalysis.created_at.desc()).all()

        evaluations = db.query(AnswerEvaluation).filter(
            AnswerEvaluation.session_id.in_(session_ids)
        ).all()

        roadmaps = db.query(ImprovementRoadmap).filter(
            ImprovementRoadmap.session_id.in_(session_ids)
        ).order_by(ImprovementRoadmap.created_at.desc()).all()

        # 2. Perform adaptation logic (LLM with local fallback)
        profile_data = self._generate_profile_data(sessions, snapshots, weaknesses, evaluations, roadmaps, latest_match)

        # 3. Store adaptation profile
        profile = AdaptiveProfile(
            user_id=user_id,
            next_focus_areas=profile_data["next_focus_areas"],
            difficulty_adjustments=profile_data["difficulty_adjustments"],
            priority_questions=profile_data["priority_questions"],
            recommended_interview_type=profile_data["recommended_interview_type"]
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)

        return self._format_response(profile)

    def _generate_profile_data(
        self,
        sessions: List[InterviewSession],
        snapshots: List[ProgressSnapshot],
        weaknesses: List[WeaknessAnalysis],
        evaluations: List[AnswerEvaluation],
        roadmaps: List[ImprovementRoadmap],
        latest_match: Any = None
    ) -> Dict[str, Any]:
        """Routes adaptation profile generation to Gemini LLM or falls back to local rules-based engine."""
        if settings.GEMINI_API_KEY or settings.GROQ_API_KEY:
            try:
                return self._generate_with_llm(sessions, snapshots, weaknesses, evaluations, roadmaps, latest_match)
            except Exception as e:
                logger.error(f"LLM adaptive profile generation failed: {str(e)}. Falling back to local rules.")

        # Heuristic fallback
        focus_areas = self.generate_focus_areas(sessions, snapshots, weaknesses, roadmaps)
        
        # If fallback focus areas are empty or generic and latest_match is present, use latest_match gaps!
        if (not focus_areas or any("General Software Engineering" in f.get("area", "") for f in focus_areas)) and latest_match:
            missing = (latest_match.missing_skills or []) + (latest_match.missing_technologies or [])
            improvements = latest_match.improvement_areas or []
            focus_areas = []
            for skill in missing[:2]:
                focus_areas.append({
                    "area": f"Skill Gap: {skill}",
                    "priority": "High",
                    "reason": f"Identified as a critical missing competency in your target job match analysis."
                })
            for imp in improvements[:1]:
                focus_areas.append({
                    "area": f"Improvement: {imp}",
                    "priority": "Medium",
                    "reason": f"Identified as an area for professional optimization."
                })

        diff_adjustments = self.adjust_difficulty(sessions, evaluations, snapshots)
        priority_qs = self.prioritize_questions(sessions, weaknesses, evaluations)
        if not priority_qs and latest_match:
            missing = (latest_match.missing_skills or []) + (latest_match.missing_technologies or [])
            for skill in missing[:2]:
                priority_qs.append({
                    "category": "Technical",
                    "topic": skill,
                    "recommended_complexity": "Medium"
                })
        if not priority_qs:
            priority_qs = [
                {
                    "category": "Technical",
                    "topic": "Domain Architecture & Web APIs",
                    "recommended_complexity": "Medium"
                }
            ]

        interview_type = self.recommend_interview_type(sessions, weaknesses, evaluations)
        if interview_type == "Balanced Mock Interview" and latest_match and latest_match.missing_skills:
            interview_type = "Technical Focus"

        return {
            "next_focus_areas": focus_areas,
            "difficulty_adjustments": diff_adjustments,
            "priority_questions": priority_qs,
            "recommended_interview_type": interview_type
        }

    def _generate_with_llm(
        self,
        sessions: List[InterviewSession],
        snapshots: List[ProgressSnapshot],
        weaknesses: List[WeaknessAnalysis],
        evaluations: List[AnswerEvaluation],
        roadmaps: List[ImprovementRoadmap],
        latest_match: Any = None
    ) -> Dict[str, Any]:
        """Generates adaptive preparation profile using Gemini LLM."""
        # Convert inputs to simplified summaries for the LLM
        latest_snapshot = snapshots[0] if snapshots else None
        snapshot_summary = {
            "overall_progress_score": latest_snapshot.overall_progress if latest_snapshot else 70.0,
            "improved_areas": latest_snapshot.improved_areas if latest_snapshot else [],
            "persistent_weaknesses": latest_snapshot.persistent_weaknesses if latest_snapshot else [],
            "roadmap_completion": latest_snapshot.roadmap_completion if latest_snapshot else {}
        }

        recent_weaknesses = []
        for w in weaknesses[:3]:  # Top 3 recent analyses
            recent_weaknesses.append({
                "date": w.created_at.isoformat() if w.created_at else "",
                "technical": w.technical_weaknesses or [],
                "behavioral": w.behavioral_weaknesses or [],
                "dsa": w.dsa_weaknesses or [],
                "communication": w.communication_weaknesses or [],
                "priority_areas": w.priority_areas or []
            })

        recent_evals = []
        for ev in evaluations[-10:]:  # Last 10 answers
            recent_evals.append({
                "overall_score": ev.overall_score,
                "strengths": ev.strengths or [],
                "weaknesses": ev.weaknesses or [],
                "clarity": ev.clarity_score,
                "technical_accuracy": ev.technical_accuracy_score,
                "confidence": ev.confidence_score
            })

        # Build JD match gap context
        match_gap_context = ""
        if latest_match:
            missing_skills = latest_match.missing_skills or []
            missing_tech = latest_match.missing_technologies or []
            improvements = latest_match.improvement_areas or []
            match_score = latest_match.match_score or 0
            match_gap_context = f"""
- Job Description Match Score: {match_score:.0f}%
- Missing Skills vs Target JD: {json.dumps(missing_skills)}
- Missing Technologies vs Target JD: {json.dumps(missing_tech)}
- JD Improvement Areas: {json.dumps(improvements)}

IMPORTANT: The candidate's latest Job Description analysis shows specific skill and technology gaps (listed above). Prioritize these gaps heavily when generating focus areas and priority questions. If the candidate is missing specific skills or technologies, they should appear as HIGH priority focus areas and their matching practice questions.
"""

        prompt = f"""
You are the intelligence coordinator for InterviewPilot AI. Your goal is to analyze the candidate's historical interview sessions, weakness reports, answer evaluations, and progress snapshots to create a highly personalized, adaptive preparation profile.

Here is the candidate's historical progress data:
- Progress Snapshot Summary: {json.dumps(snapshot_summary, indent=2)}
- Recent Weakness Analyses (Chrono Desc): {json.dumps(recent_weaknesses, indent=2)}
- Recent Answer Evaluations (Chronological): {json.dumps(recent_evals, indent=2)}
{match_gap_context}

Adaptation Task Instructions:
1. **Next Focus Areas**: Identify the key topics/skills the candidate needs to work on next. Factor in persistent weaknesses, but filter out improved areas. Provide a priority (High, Medium, Low) and a clear reason.
2. **Difficulty Adjustments**: Provide difficulty adjustments (Beginner, Intermediate, Advanced) for "technical", "behavioral", and "dsa" sections as a list of dicts. If scores are consistently high (>85), increase difficulty; if low (<65), decrease difficulty; otherwise, maintain.
3. **Priority Questions**: Define specific question categories, topics, and recommended complexity levels (Low, Medium, High) to present in the next mock interview.
4. **Recommended Interview Type**: Suggest one of: "Technical Focus", "Behavioral Focus", "System Design", "DSA/Coding", or "Balanced Mock Interview".

Return ONLY a valid JSON object matching the format below. Do not wrap in markdown or include ```json.

Output Format:
{{
  "next_focus_areas": [
    {{
      "area": "string",
      "priority": "string",
      "reason": "string"
    }}
  ],
  "difficulty_adjustments": [
    {{
      "section": "string",
      "level": "string",
      "reason": "string"
    }}
  ],
  "priority_questions": [
    {{
      "category": "string",
      "topic": "string",
      "recommended_complexity": "string"
    }}
  ],
  "recommended_interview_type": "string"
}}
"""
        response_text = llm_service.generate_content(prompt, temperature=0.3, response_json=True)
        text = response_text.strip()

        if text.startswith("```"):
            lines = text.splitlines()
            if lines[0].startswith("```json") or lines[0].startswith("```"):
                text = "\n".join(lines[1:-1])

        data = json.loads(text)
        required_keys = ["next_focus_areas", "difficulty_adjustments", "priority_questions", "recommended_interview_type"]
        for key in required_keys:
            if key not in data:
                raise ValueError(f"Missing adaptive profile key: {key}")

        return data

    # Core Rule-Based Functions (Fallback)
    def generate_focus_areas(
        self,
        sessions: List[InterviewSession],
        snapshots: List[ProgressSnapshot],
        weaknesses: List[WeaknessAnalysis],
        roadmaps: List[ImprovementRoadmap]
    ) -> List[Dict[str, Any]]:
        """Identifies next focus areas based on persistent weaknesses and active gaps."""
        focus_areas = []
        latest_snapshot = snapshots[0] if snapshots else None

        # Fetch persistent weaknesses
        persistent = set()
        if latest_snapshot and latest_snapshot.persistent_weaknesses:
            for w in latest_snapshot.persistent_weaknesses:
                persistent.add(w.strip())

        # Check improved areas to avoid recommending them
        improved = set()
        if latest_snapshot and latest_snapshot.improved_areas:
            for w in latest_snapshot.improved_areas:
                improved.add(w.strip().lower())

        # Pull from latest weakness analysis priority areas
        latest_wa = weaknesses[0] if weaknesses else None
        wa_priorities = []
        if latest_wa and latest_wa.priority_areas:
            for area in latest_wa.priority_areas:
                val = area if isinstance(area, str) else area.get("name", "") if isinstance(area, dict) else ""
                if val:
                    wa_priorities.append(val.strip())

        # Populate high priority focus areas
        for p in persistent:
            if p.lower() not in improved:
                focus_areas.append({
                    "area": p,
                    "priority": "High",
                    "reason": "This area was flagged as a persistent weakness across multiple sessions."
                })

        # Add other priority areas
        for a in wa_priorities:
            if a.lower() not in improved and not any(f["area"].lower() == a.lower() for f in focus_areas):
                focus_areas.append({
                    "area": a,
                    "priority": "Medium",
                    "reason": "Flagged as a key improvement area in your latest session."
                })

        # Baseline fallback if nothing identified
        if not focus_areas:
            focus_areas.append({
                "area": "General Software Engineering Concepts",
                "priority": "Medium",
                "reason": "Complete more mock interviews to get personalized topic focus areas."
            })

        return focus_areas[:5]

    def adjust_difficulty(
        self,
        sessions: List[InterviewSession],
        evaluations: List[AnswerEvaluation],
        snapshots: List[ProgressSnapshot]
    ) -> List[Dict[str, Any]]:
        """Adjusts difficulty levels based on repeated low or high scores."""
        latest_snapshot = snapshots[0] if snapshots else None
        overall_progress = latest_snapshot.overall_progress if latest_snapshot else 75.0

        # Rule-based difficulty assignment based on progress metrics
        if overall_progress < 65.0:
            level = "Beginner"
            adjustment = "Lowering difficulty to help build confidence and reinforce fundamental concepts."
        elif overall_progress > 85.0:
            level = "Advanced"
            adjustment = "Increasing difficulty to challenge you with more complex scenarios and depth."
        else:
            level = "Intermediate"
            adjustment = "Maintaining current difficulty level to solidify core knowledge."

        return [
            {
                "section": "technical",
                "level": level,
                "reason": adjustment
            },
            {
                "section": "behavioral",
                "level": level,
                "reason": adjustment
            },
            {
                "section": "dsa",
                "level": level,
                "reason": adjustment
            }
        ]

    def prioritize_questions(
        self,
        sessions: List[InterviewSession],
        weaknesses: List[WeaknessAnalysis],
        evaluations: List[AnswerEvaluation]
    ) -> List[Dict[str, Any]]:
        """Determines target question categories and topics to prioritize next."""
        priority_qs = []
        latest_wa = weaknesses[0] if weaknesses else None

        # Look for categories with weaknesses
        has_tech = False
        has_dsa = False
        has_behavioral = False

        if latest_wa:
            if latest_wa.technical_weaknesses:
                has_tech = True
                for tw in latest_wa.technical_weaknesses[:2]:
                    val = tw if isinstance(tw, str) else tw.get("name", "") if isinstance(tw, dict) else ""
                    if val:
                        priority_qs.append({
                            "category": "Technical",
                            "topic": val,
                            "recommended_complexity": "Medium"
                        })
            if latest_wa.dsa_weaknesses:
                has_dsa = True
                for dw in latest_wa.dsa_weaknesses[:1]:
                    val = dw if isinstance(dw, str) else dw.get("name", "") if isinstance(dw, dict) else ""
                    if val:
                        priority_qs.append({
                            "category": "DSA",
                            "topic": val,
                            "recommended_complexity": "Medium"
                        })
            if latest_wa.behavioral_weaknesses:
                has_behavioral = True
                for bw in latest_wa.behavioral_weaknesses[:1]:
                    val = bw if isinstance(bw, str) else bw.get("name", "") if isinstance(bw, dict) else ""
                    if val:
                        priority_qs.append({
                            "category": "Behavioral",
                            "topic": val,
                            "recommended_complexity": "Medium"
                        })

        # Add general fallbacks if we don't have enough priorities
        if len(priority_qs) < 3:
            if not has_tech:
                priority_qs.append({
                    "category": "Technical",
                    "topic": "System Design and Scalability Principles",
                    "recommended_complexity": "Medium"
                })
            if not has_dsa:
                priority_qs.append({
                    "category": "DSA",
                    "topic": "Arrays, HashMaps, and Sorting Algorithms",
                    "recommended_complexity": "Medium"
                })
            if not has_behavioral:
                priority_qs.append({
                    "category": "Behavioral",
                    "topic": "STAR Method (Situation, Task, Action, Result) Delivery",
                    "recommended_complexity": "Medium"
                })

        return priority_qs[:4]

    def recommend_interview_type(
        self,
        sessions: List[InterviewSession],
        weaknesses: List[WeaknessAnalysis],
        evaluations: List[AnswerEvaluation]
    ) -> str:
        """Determines the recommended interview type based on weakness counts."""
        if not weaknesses:
            return "Balanced Mock Interview"

        latest_wa = weaknesses[0]

        tech_count = len(latest_wa.technical_weaknesses or [])
        behavioral_count = len(latest_wa.behavioral_weaknesses or [])
        dsa_count = len(latest_wa.dsa_weaknesses or [])

        counts = {
            "Technical Focus": tech_count,
            "Behavioral Focus": behavioral_count,
            "DSA/Coding Focus": dsa_count
        }

        # Find the category with maximum weaknesses
        max_type = max(counts, key=counts.get)

        if counts[max_type] == 0:
            return "Balanced Mock Interview"

        return max_type

    def _create_baseline_profile(self, user_id: str, latest_match: Any = None) -> Dict[str, Any]:
        """Creates a baseline configuration for a user, personalizing it to their resume mismatch analysis if available."""
        next_focus_areas = []
        priority_qs = []

        if latest_match:
            # Dynamically target the skills/technologies that are missing or require improvement
            missing = (latest_match.missing_skills or []) + (latest_match.missing_technologies or [])
            improvements = latest_match.improvement_areas or []

            # Populate up to 3 high-priority focus areas
            for skill in missing[:2]:
                next_focus_areas.append({
                    "area": f"Skill Gap: {skill}",
                    "priority": "High",
                    "reason": f"Identified as a critical missing competency in your target job match analysis."
                })
            for imp in improvements[:1]:
                next_focus_areas.append({
                    "area": f"Improvement: {imp}",
                    "priority": "Medium",
                    "reason": f"Identified as an area for professional optimization."
                })

            # Populate priority questions mapping to gaps
            for skill in missing[:2]:
                priority_qs.append({
                    "category": "Technical",
                    "topic": skill,
                    "recommended_complexity": "Medium"
                })

        # Fallback to defaults if no match analysis gaps exist
        if not next_focus_areas:
            next_focus_areas = [
                {
                    "area": "Core Domain Fundamentals",
                    "priority": "Medium",
                    "reason": "Initial baseline focus to assess core domain alignment."
                },
                {
                    "area": "Behavioral Competencies",
                    "priority": "Medium",
                    "reason": "Standard assessment of collaboration, conflict resolution, and soft skills."
                }
            ]
        if not priority_qs:
            priority_qs = [
                {
                    "category": "Technical",
                    "topic": "Domain Architecture & Web APIs",
                    "recommended_complexity": "Medium"
                },
                {
                    "category": "Behavioral",
                    "topic": "Conflict Resolution and Teamwork",
                    "recommended_complexity": "Medium"
                }
            ]

        return {
            "next_focus_areas": next_focus_areas,
            "difficulty_adjustments": [
                {
                    "section": "technical",
                    "level": "Intermediate",
                    "reason": "Starting at default intermediate level."
                },
                {
                    "section": "behavioral",
                    "level": "Intermediate",
                    "reason": "Starting at default intermediate level."
                },
                {
                    "section": "dsa",
                    "level": "Intermediate",
                    "reason": "Starting at default intermediate level."
                }
            ],
            "priority_questions": priority_qs,
            "recommended_interview_type": "Technical Focus" if (latest_match and latest_match.missing_skills) else "Balanced Mock Interview"
        }

    def _format_response(self, profile: AdaptiveProfile) -> Dict[str, Any]:
        """Formats the database model to match the output schema structure."""
        return {
            "id": profile.id,
            "user_id": profile.user_id,
            "next_focus_areas": profile.next_focus_areas or [],
            "difficulty_adjustments": profile.difficulty_adjustments or [],
            "priority_questions": profile.priority_questions or [],
            "recommended_interview_type": profile.recommended_interview_type,
            "created_at": profile.created_at
        }


# Global instance of service
adaptive_service = AdaptiveService()
