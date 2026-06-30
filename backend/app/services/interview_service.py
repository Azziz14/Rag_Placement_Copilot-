"""Service module for managing mock interview workflows.
"""

import json
from datetime import datetime
from typing import List, Dict, Any, Tuple, Optional
from sqlalchemy.orm import Session

from app.models.resume_match import ResumeMatch
from app.models.interview_session import InterviewSession
from app.models.interview_answer import InterviewAnswer
from app.services.rag_service import rag_service
from app.services.question_service import question_service
from app.models.resume import Resume
from app.models.job_description import JobDescription


class InterviewService:
    """Service class executing the mock interview logic, maintaining question order, and persisting answers."""

    def _load_previous_questions(self, db: Session, user_id: str, match_id: str) -> List[str]:
        """Loads previously asked questions for this user and resume/JD pair."""
        current_match = db.query(ResumeMatch).filter(
            ResumeMatch.id == match_id,
            ResumeMatch.user_id == user_id
        ).first()
        related_match_ids = [match_id]
        if current_match:
            related_matches = db.query(ResumeMatch).filter(
                ResumeMatch.user_id == user_id,
                ResumeMatch.resume_id == current_match.resume_id,
                ResumeMatch.job_description_id == current_match.job_description_id
            ).all()
            related_match_ids = [match.id for match in related_matches]

        previous_sessions = db.query(InterviewSession).filter(
            InterviewSession.user_id == user_id,
            InterviewSession.match_id.in_(related_match_ids),
            InterviewSession.questions.isnot(None)
        ).order_by(InterviewSession.started_at.desc()).limit(10).all()

        previous_questions = []
        for session in previous_sessions:
            try:
                cached_questions = json.loads(session.questions or "[]")
                for item in cached_questions:
                    if isinstance(item, (list, tuple)) and item:
                        previous_questions.append(str(item[0]))
                    elif isinstance(item, str):
                        previous_questions.append(item)
            except Exception:
                continue
        return previous_questions

    def _fetch_ordered_questions(
        self,
        db: Session,
        user_id: str,
        match_id: str
    ) -> List[Tuple[str, str]]:
        """Coordinates RAG context retrieval and invokes the question generator to get an ordered list of questions.
        
        Returns:
            List of tuples: (question_text, category_name)
        """
        # Coerce match_id to string to query the database
        match_id_str = str(match_id)
        
        match = db.query(ResumeMatch).filter(
            ResumeMatch.id == match_id_str,
            ResumeMatch.user_id == user_id
        ).first()
        if not match:
            raise ValueError(f"Match record with ID {match_id_str} not found or unauthorized.")

        resume = db.query(Resume).filter(Resume.id == match.resume_id, Resume.user_id == user_id).first()
        jd = db.query(JobDescription).filter(JobDescription.id == match.job_description_id, JobDescription.user_id == user_id).first()

        if not resume or not jd:
            raise ValueError("Associated Resume or Job Description documents not found.")

        # Pull context from vector DB
        rag_context = rag_service.retrieve_all_context(
            db=db,
            user_id=user_id,
            match_id=match_id_str
        )

        # Generate categorized questions
        questions_dict = question_service.generate_questions(
            resume=resume,
            jd=jd,
            match=match,
            rag_context=rag_context,
            previous_questions=self._load_previous_questions(db, user_id, match_id_str)
        )

        # Build an ordered list to maintain a sequential flow:
        # Technical -> Project -> Behavioral -> DSA
        ordered_questions = []
        
        for q in questions_dict.get("technical_questions") or []:
            ordered_questions.append((q, "technical"))
        for q in questions_dict.get("project_questions") or []:
            ordered_questions.append((q, "project"))
        for q in questions_dict.get("behavioral_questions") or []:
            ordered_questions.append((q, "behavioral"))
        for q in questions_dict.get("dsa_questions") or []:
            ordered_questions.append((q, "dsa"))

        if not ordered_questions:
            raise ValueError("No interview questions could be generated from the given documents.")

        return ordered_questions

    def start_interview(self, db: Session, user_id: str, match_id: Any) -> Tuple[str, str]:
        """Core function: Start a new mock interview session and return the first question."""
        match_id_str = str(match_id)

        # Fetch questions and cache/store them (we pull them directly using document models)
        questions = self._fetch_ordered_questions(db, user_id, match_id_str)
        first_question, _ = questions[0]

        # Create session with cached questions
        session = InterviewSession(
            user_id=user_id,
            match_id=match_id_str,
            status="started",
            current_question_index=0,
            started_at=datetime.utcnow(),
            questions=json.dumps(questions)
        )
        db.add(session)
        db.commit()
        db.refresh(session)

        return session.id, first_question

    def get_next_question(self, db: Session, user_id: str, session_id: str) -> Tuple[Optional[str], str]:
        """Core function: Retrieve the next question or mark the interview as completed.
        
        Returns:
            Tuple: (next_question_text, status)
        """
        session = db.query(InterviewSession).filter(
            InterviewSession.id == session_id,
            InterviewSession.user_id == user_id
        ).first()
        if not session:
            raise ValueError("Interview session not found or unauthorized.")

        if session.status == "completed":
            return None, "completed"

        # Load cached questions from DB if available, otherwise fetch and cache
        try:
            if session.questions:
                questions = json.loads(session.questions)
            else:
                questions = self._fetch_ordered_questions(db, user_id, session.match_id)
                session.questions = json.dumps(questions)
                db.commit()
        except Exception as e:
            # If RAG fails midway, fallback gracefully
            raise ValueError(f"Failed to fetch questions for session: {str(e)}")

        index = session.current_question_index
        if index >= len(questions):
            # Mark session as completed
            session.status = "completed"
            session.ended_at = datetime.utcnow()
            db.commit()
            return None, "completed"

        next_question, _ = questions[index]
        return next_question, "started"

    def save_answer(self, db: Session, user_id: str, session_id: str, answer_text: str) -> Dict[str, Any]:
        """Core function: Saves the current answer, increments the current question index, and fetches the next question."""
        session = db.query(InterviewSession).filter(
            InterviewSession.id == session_id,
            InterviewSession.user_id == user_id
        ).first()
        if not session:
            raise ValueError("Interview session not found or unauthorized.")

        if session.status == "completed":
            raise ValueError("Cannot submit answers to a completed interview session.")

        # Resolve current question category and text using cached questions
        try:
            if session.questions:
                questions = json.loads(session.questions)
            else:
                questions = self._fetch_ordered_questions(db, user_id, session.match_id)
                session.questions = json.dumps(questions)
                db.commit()
        except Exception as e:
            raise ValueError(f"Failed to fetch questions for session: {str(e)}")

        index = session.current_question_index

        if index >= len(questions):
            session.status = "completed"
            session.ended_at = datetime.utcnow()
            db.commit()
            return {"is_finished": True, "next_question": None, "status": "completed"}

        current_question, category = questions[index]

        # Prevent empty submissions
        if not answer_text or not answer_text.strip():
            raise ValueError("Answer content cannot be empty.")

        # Save the answer
        db_answer = InterviewAnswer(
            session_id=session.id,
            question=current_question,
            answer=answer_text,
            category=category,
            created_at=datetime.utcnow()
        )
        db.add(db_answer)

        # Move to next index
        session.current_question_index = index + 1
        db.commit()

        # Check if we finished
        if session.current_question_index >= len(questions):
            session.status = "completed"
            session.ended_at = datetime.utcnow()
            db.commit()
            return {"is_finished": True, "next_question": None, "status": "completed"}

        next_question, _ = questions[session.current_question_index]
        return {"is_finished": False, "next_question": next_question, "status": "started"}

    def end_interview(self, db: Session, user_id: str, session_id: str) -> None:
        """Core function: Manually mark session completed and lock submissions."""
        session = db.query(InterviewSession).filter(
            InterviewSession.id == session_id,
            InterviewSession.user_id == user_id
        ).first()
        if not session:
            raise ValueError("Interview session not found or unauthorized.")

        if session.status != "completed":
            session.status = "completed"
            session.ended_at = datetime.utcnow()
            db.commit()
