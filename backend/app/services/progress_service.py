"""Service module for calculating user progress metrics and managing progress snapshots.
"""

import logging
from datetime import datetime
from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session

from app.models.interview_session import InterviewSession
from app.models.answer_evaluation import AnswerEvaluation
from app.models.weakness_analysis import WeaknessAnalysis
from app.models.improvement_roadmap import ImprovementRoadmap
from app.models.resume_match import ResumeMatch
from app.models.progress_snapshot import ProgressSnapshot
from app.models.job_description import JobDescription

logger = logging.getLogger(__name__)


class ProgressService:
    """Service class containing logic for dashboard calculations and snapshot persistence."""

    def _normalize_items(self, values: Any) -> List[str]:
        """Converts list-like fields into a clean list of strings."""
        if not values:
            return []

        cleaned = []
        for item in values:
            if isinstance(item, str) and item.strip():
                cleaned.append(item.strip())
            elif isinstance(item, dict):
                val = item.get("name") or item.get("title") or item.get("goal") or item.get("area")
                if isinstance(val, str) and val.strip():
                    cleaned.append(val.strip())
        return cleaned

    def _build_fallback_snapshot(self, db: Session, user_id: str) -> Dict[str, Any]:
        """Builds a dashboard snapshot from resume/JD data when no interview session exists."""
        latest_match = db.query(ResumeMatch).filter(
            ResumeMatch.user_id == user_id
        ).order_by(ResumeMatch.created_at.desc()).first()

        score = round(float(latest_match.match_score), 2) if latest_match and latest_match.match_score is not None else 0.0
        strong_areas = self._normalize_items((latest_match.strong_areas if latest_match else []) or (latest_match.matched_skills if latest_match else []))
        missing_areas = self._normalize_items((latest_match.improvement_areas if latest_match else []) or [])
        if not missing_areas and latest_match:
            missing_areas = self._normalize_items((latest_match.missing_skills or []) + (latest_match.missing_technologies or []))

        roadmap_completion = {"completed_goals": 0, "total_goals": 0, "completion_percentage": 0.0}
        if latest_match:
            total_goals = len(missing_areas) or len(strong_areas)
            roadmap_completion = {
                "completed_goals": len(strong_areas),
                "total_goals": total_goals,
                "completion_percentage": 0.0 if total_goals == 0 else round((len(strong_areas) / total_goals) * 100, 2)
            }

        snapshot = ProgressSnapshot(
            user_id=user_id,
            overall_progress=score,
            score_trend=[],
            improved_areas=strong_areas[:3],
            persistent_weaknesses=missing_areas[:5],
            roadmap_completion=roadmap_completion
        )
        db.add(snapshot)
        db.commit()
        db.refresh(snapshot)

        return {
            "id": snapshot.id,
            "user_id": snapshot.user_id,
            "overall_progress": snapshot.overall_progress,
            "score_trend": [],
            "improved_areas": snapshot.improved_areas or [],
            "persistent_weaknesses": snapshot.persistent_weaknesses or [],
            "roadmap_completion": snapshot.roadmap_completion or roadmap_completion,
            "created_at": snapshot.created_at
        }

    def calculate_overall_progress(self, trend: List[Dict[str, Any]]) -> float:
        """Calculates the overall progress based on the latest interview score.
        
        Returns 0.0 if there is no trend data available.
        """
        if not trend:
            return 0.0
        return trend[-1]["average_score"]

    def generate_score_trend(self, sessions: List[InterviewSession], evaluations: List[AnswerEvaluation]) -> List[Dict[str, Any]]:
        """Generates the chronological average score trend for each session."""
        trend = []
        for session in sessions:
            session_evals = [e for e in evaluations if e.session_id == session.id]
            if not session_evals:
                continue
            avg_score = sum(e.overall_score for e in session_evals) / len(session_evals)
            trend.append({
                "session_id": session.id,
                "date": session.started_at.isoformat(),
                "average_score": round(avg_score, 2)
            })
        return trend

    def identify_improved_areas(
        self,
        sessions: List[InterviewSession],
        evaluations: List[AnswerEvaluation],
        weaknesses: List[WeaknessAnalysis],
        resume_matches: List[ResumeMatch]
    ) -> List[str]:
        """Identifies areas of improvement by comparing past weaknesses with current ones."""
        if not sessions:
            return []

        # Extract latest weaknesses
        latest_weaknesses = set()
        if weaknesses:
            latest_wa = weaknesses[-1]
            for attr in ['technical_weaknesses', 'behavioral_weaknesses', 'dsa_weaknesses', 'communication_weaknesses']:
                items = getattr(latest_wa, attr) or []
                for item in items:
                    val = item if isinstance(item, str) else item.get("name", "") if isinstance(item, dict) else ""
                    if val:
                        latest_weaknesses.add(val.lower().strip())

        # Extract older weaknesses
        older_weaknesses = set()
        for wa in weaknesses[:-1]:
            for attr in ['technical_weaknesses', 'behavioral_weaknesses', 'dsa_weaknesses', 'communication_weaknesses']:
                items = getattr(wa, attr) or []
                for item in items:
                    val = item if isinstance(item, str) else item.get("name", "") if isinstance(item, dict) else ""
                    if val:
                        older_weaknesses.add(val.lower().strip())

        # Extract latest missing skills
        latest_missing = set()
        if resume_matches:
            latest_rm = resume_matches[-1]
            for s in (latest_rm.missing_skills or []):
                latest_missing.add(s.lower().strip())
            for t in (latest_rm.missing_technologies or []):
                latest_missing.add(t.lower().strip())

        # Extract older missing skills
        older_missing = set()
        for rm in resume_matches[:-1]:
            for s in (rm.missing_skills or []):
                older_missing.add(s.lower().strip())
            for t in (rm.missing_technologies or []):
                older_missing.add(t.lower().strip())

        # Improved areas: things that were weaknesses or missing in the past but are not anymore
        improved_weaknesses = older_weaknesses - latest_weaknesses
        improved_missing = older_missing - latest_missing
        improved_set = improved_weaknesses | improved_missing

        # Add strengths from the latest session if available as another dimension
        latest_strengths = set()
        latest_session_id = sessions[-1].id if sessions else None
        if latest_session_id:
            latest_evals = [e for e in evaluations if e.session_id == latest_session_id]
            for ev in latest_evals:
                for s in (ev.strengths or []):
                    latest_strengths.add(s.strip())

        improved_list = [item.title() for item in improved_set if item]
        
        # If no historical transition, use top strengths from the latest evaluation
        if not improved_list and latest_strengths:
            improved_list = list(latest_strengths)[:3]

        return improved_list

    def identify_persistent_weaknesses(
        self,
        sessions: List[InterviewSession],
        evaluations: List[AnswerEvaluation],
        weaknesses: List[WeaknessAnalysis]
    ) -> List[str]:
        """Identifies weaknesses that persist across multiple sessions."""
        if len(weaknesses) < 2:
            # If only one session exists, return its weaknesses as areas to work on
            if weaknesses:
                current_weaknesses = []
                latest_wa = weaknesses[-1]
                for attr in ['technical_weaknesses', 'behavioral_weaknesses', 'dsa_weaknesses', 'communication_weaknesses']:
                    items = getattr(latest_wa, attr) or []
                    for item in items:
                        val = item if isinstance(item, str) else item.get("name", "") if isinstance(item, dict) else ""
                        if val:
                            current_weaknesses.append(val)
                return current_weaknesses
            return []

        # Find weaknesses that appear in the latest session AND in past sessions
        latest_wa = weaknesses[-1]
        latest_set = set()
        latest_orig = {}
        for attr in ['technical_weaknesses', 'behavioral_weaknesses', 'dsa_weaknesses', 'communication_weaknesses']:
            items = getattr(latest_wa, attr) or []
            for item in items:
                val = item if isinstance(item, str) else item.get("name", "") if isinstance(item, dict) else ""
                if val:
                    key = val.lower().strip()
                    latest_set.add(key)
                    latest_orig[key] = val

        older_set = set()
        for wa in weaknesses[:-1]:
            for attr in ['technical_weaknesses', 'behavioral_weaknesses', 'dsa_weaknesses', 'communication_weaknesses']:
                items = getattr(wa, attr) or []
                for item in items:
                    val = item if isinstance(item, str) else item.get("name", "") if isinstance(item, dict) else ""
                    if val:
                        older_set.add(val.lower().strip())

        persistent = latest_set.intersection(older_set)
        return [latest_orig[p] for p in persistent if p in latest_orig]

    def calculate_roadmap_completion(
        self,
        sessions: List[InterviewSession],
        weaknesses: List[WeaknessAnalysis],
        roadmaps: List[ImprovementRoadmap]
    ) -> Dict[str, Any]:
        """Calculates roadmap completion statistics based on resolved weaknesses."""
        if not roadmaps:
            return {"completed_goals": 0, "total_goals": 0, "completion_percentage": 0.0}

        all_goals = []
        for rm in roadmaps:
            for plan_attr in ["technical_plan", "dsa_plan", "behavioral_plan"]:
                plan = getattr(rm, plan_attr) or []
                for item in plan:
                    if isinstance(item, dict) and "goal" in item:
                        all_goals.append(item["goal"])
                    elif isinstance(item, str):
                        all_goals.append(item)

        total_goals = len(all_goals)
        if total_goals == 0:
            return {"completed_goals": 0, "total_goals": 0, "completion_percentage": 0.0}

        # Identify latest weaknesses
        latest_weaknesses = set()
        if weaknesses:
            latest_wa = weaknesses[-1]
            for attr in ['technical_weaknesses', 'behavioral_weaknesses', 'dsa_weaknesses', 'communication_weaknesses']:
                items = getattr(latest_wa, attr) or []
                for item in items:
                    val = item if isinstance(item, str) else item.get("name", "") if isinstance(item, dict) else ""
                    if val:
                        latest_weaknesses.add(val.lower().strip())

        completed_goals = 0
        for goal in all_goals:
            goal_lower = goal.lower()
            # If the goal doesn't mention any current/latest weaknesses, consider it completed
            is_completed = True
            for w in latest_weaknesses:
                if w in goal_lower:
                    is_completed = False
                    break
            if is_completed:
                completed_goals += 1

        completion_percentage = round((completed_goals / total_goals) * 100, 2)
        return {
            "completed_goals": completed_goals,
            "total_goals": total_goals,
            "completion_percentage": completion_percentage
        }

    def get_or_create_dashboard_snapshot(self, db: Session, user_id: str) -> Dict[str, Any]:
        """Aggregates user history, computes metrics, saves and returns a progress snapshot."""
        # 1. Fetch historical data
        sessions = db.query(InterviewSession).filter(
            InterviewSession.user_id == user_id
        ).order_by(InterviewSession.started_at.asc()).all()

        if not sessions:
            return self._build_fallback_snapshot(db=db, user_id=user_id)

        session_ids = [s.id for s in sessions]

        evaluations = db.query(AnswerEvaluation).filter(
            AnswerEvaluation.session_id.in_(session_ids)
        ).all()

        weaknesses = db.query(WeaknessAnalysis).filter(
            WeaknessAnalysis.session_id.in_(session_ids)
        ).order_by(WeaknessAnalysis.created_at.asc()).all()

        roadmaps = db.query(ImprovementRoadmap).filter(
            ImprovementRoadmap.session_id.in_(session_ids)
        ).order_by(ImprovementRoadmap.created_at.asc()).all()

        resume_matches = db.query(ResumeMatch).filter(
            ResumeMatch.user_id == user_id
        ).order_by(ResumeMatch.created_at.asc()).all()

        # 2. Compute metrics
        score_trend = self.generate_score_trend(sessions, evaluations)
        overall_progress = self.calculate_overall_progress(score_trend)
        improved_areas = self.identify_improved_areas(sessions, evaluations, weaknesses, resume_matches)
        persistent_weaknesses = self.identify_persistent_weaknesses(sessions, evaluations, weaknesses)
        roadmap_completion = self.calculate_roadmap_completion(sessions, weaknesses, roadmaps)

        # 3. Create snapshot
        snapshot = ProgressSnapshot(
            user_id=user_id,
            overall_progress=overall_progress,
            score_trend=score_trend,
            improved_areas=improved_areas,
            persistent_weaknesses=persistent_weaknesses,
            roadmap_completion=roadmap_completion
        )
        db.add(snapshot)
        db.commit()
        db.refresh(snapshot)

        return {
            "id": snapshot.id,
            "user_id": snapshot.user_id,
            "overall_progress": snapshot.overall_progress,
            "score_trend": snapshot.score_trend or [],
            "improved_areas": snapshot.improved_areas or [],
            "persistent_weaknesses": snapshot.persistent_weaknesses or [],
            "roadmap_completion": snapshot.roadmap_completion or {
                "completed_goals": 0,
                "total_goals": 0,
                "completion_percentage": 0.0
            },
            "created_at": snapshot.created_at
        }

    def get_score_history(self, db: Session, user_id: str) -> Dict[str, Any]:
        """Returns historical JD match scores and interview session scores for a user."""
        matches = db.query(ResumeMatch).filter(
            ResumeMatch.user_id == user_id
        ).order_by(ResumeMatch.created_at.desc()).all()

        jd_ids = [match.job_description_id for match in matches]
        jds = db.query(JobDescription).filter(
            JobDescription.id.in_(jd_ids)
        ).all() if jd_ids else []
        jd_by_id = {jd.id: jd for jd in jds}

        jd_scores = []
        for match in matches:
            jd = jd_by_id.get(match.job_description_id)
            jd_scores.append({
                "match_id": match.id,
                "resume_id": match.resume_id,
                "job_description_id": match.job_description_id,
                "job_title": jd.job_title if jd else None,
                "company_name": jd.company_name if jd else None,
                "match_score": match.match_score,
                "matched_skills_count": len(match.matched_skills or []) + len(match.matched_technologies or []),
                "missing_skills_count": len(match.missing_skills or []) + len(match.missing_technologies or []),
                "created_at": match.created_at,
            })

        sessions = db.query(InterviewSession).filter(
            InterviewSession.user_id == user_id
        ).order_by(InterviewSession.started_at.desc()).all()

        session_ids = [session.id for session in sessions]
        evaluations = db.query(AnswerEvaluation).filter(
            AnswerEvaluation.session_id.in_(session_ids)
        ).all() if session_ids else []

        evals_by_session = {}
        for evaluation in evaluations:
            evals_by_session.setdefault(evaluation.session_id, []).append(evaluation)

        match_by_id = {match.id: match for match in matches}
        session_scores = []
        for session in sessions:
            session_evals = evals_by_session.get(session.id, [])
            average_score = 0.0
            if session_evals:
                average_score = round(sum(ev.overall_score for ev in session_evals) / len(session_evals), 2)

            match = match_by_id.get(session.match_id)
            jd = jd_by_id.get(match.job_description_id) if match else None
            session_scores.append({
                "session_id": session.id,
                "match_id": session.match_id,
                "job_title": jd.job_title if jd else None,
                "company_name": jd.company_name if jd else None,
                "status": session.status,
                "average_score": average_score,
                "evaluation_count": len(session_evals),
                "started_at": session.started_at,
                "ended_at": session.ended_at,
            })

        return {
            "jd_scores": jd_scores,
            "session_scores": session_scores,
        }


# Global instance of service
progress_service = ProgressService()
