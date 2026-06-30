"""Service module for evaluating candidate interview answers.

This service utilizes Gemini LLM to grade answers on multiple criteria,
with a robust fallback scoring system if LLM credentials are not available or fail.
"""

import json
import logging
import re
from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.interview_session import InterviewSession
from app.models.interview_answer import InterviewAnswer
from app.models.answer_evaluation import AnswerEvaluation
from app.models.resume_match import ResumeMatch
from app.models.job_description import JobDescription
from app.services.llm_service import llm_service

logger = logging.getLogger(__name__)


class EvaluationService:
    """Service to handle modular evaluation of mock interview answers."""



    def evaluate_session_answers(
        self, db: Session, user_id: str, session_id: str
    ) -> Dict[str, Any]:
        """Fetches all answers for a session, evaluates them, stores results, and returns them."""
        # 1. Fetch session & verify ownership
        session = db.query(InterviewSession).filter(
            InterviewSession.id == session_id,
            InterviewSession.user_id == user_id
        ).first()
        if not session:
            raise ValueError("Interview session not found or unauthorized.")

        # 2. Fetch all answers
        answers = db.query(InterviewAnswer).filter(
            InterviewAnswer.session_id == session_id
        ).order_by(InterviewAnswer.created_at.asc()).all()

        if not answers:
            raise ValueError("No answers found for this interview session. Cannot perform evaluation.")

        match = db.query(ResumeMatch).filter(ResumeMatch.id == session.match_id).first()
        jd = db.query(JobDescription).filter(JobDescription.id == match.job_description_id).first() if match else None
        evaluation_results = []

        # 3. Evaluate each answer
        for answer in answers:
            # Check if evaluation already exists to prevent duplicate scoring
            existing_eval = db.query(AnswerEvaluation).filter(
                AnswerEvaluation.session_id == session_id,
                AnswerEvaluation.answer_id == answer.id
            ).first()

            # Perform evaluation
            eval_data = self.evaluate_single_answer(answer.question, answer.answer, answer.category, jd, match)

            # Store result
            db_eval = existing_eval or AnswerEvaluation(session_id=session_id, answer_id=answer.id)
            db_eval.overall_score = eval_data["overall_score"]
            db_eval.relevance_score = eval_data["relevance_score"]
            db_eval.depth_score = eval_data["depth_score"]
            db_eval.clarity_score = eval_data["clarity_score"]
            db_eval.technical_accuracy_score = eval_data["technical_accuracy_score"]
            db_eval.confidence_score = eval_data["confidence_score"]
            db_eval.strengths = eval_data["strengths"]
            db_eval.weaknesses = eval_data["weaknesses"]
            db_eval.suggestions = eval_data["suggestions"]
            db_eval.key_phrases = eval_data.get("key_phrases", [])
            db_eval.matched_key_phrases = eval_data.get("matched_key_phrases", [])
            db_eval.missing_key_phrases = eval_data.get("missing_key_phrases", [])
            if not existing_eval:
                db.add(db_eval)
            db.flush()  # Populates db_eval.id and created_at without committing entire transaction yet

            evaluation_results.append(self._format_detail(answer, db_eval))

        db.commit()
        return {
            "session_id": session_id,
            "evaluations": evaluation_results
        }

    def evaluate_single_answer(
        self,
        question: str,
        answer: str,
        category: str,
        jd: JobDescription | None = None,
        match: ResumeMatch | None = None
    ) -> Dict[str, Any]:
        """Grades a single answer using Gemini LLM if configured, otherwise falls back to heuristics."""
        if settings.GEMINI_API_KEY or settings.GROQ_API_KEY:
            try:
                return self._evaluate_with_llm(question, answer, category, jd, match)
            except Exception as e:
                logger.error(f"Gemini evaluation failed: {str(e)}. Falling back to heuristics.")

        # Heuristic/rule-based scoring fallback
        relevance = self.evaluate_relevance(question, answer, category)
        depth = self.evaluate_depth(question, answer, category)
        clarity = self.evaluate_clarity(question, answer, category)
        accuracy = self.evaluate_technical_accuracy(question, answer, category)
        confidence = self.evaluate_confidence(question, answer, category)
        relevance, accuracy = self.apply_jd_fit_adjustment(relevance, accuracy, answer, jd, match)
        overall = self.calculate_overall_score(relevance, depth, clarity, accuracy, confidence)
        feedback = self.generate_feedback(question, answer, category, relevance, depth, clarity, accuracy, confidence)
        keywords_data = self._extract_heuristic_keywords(question, answer, category, jd)

        return {
            "relevance_score": relevance,
            "depth_score": depth,
            "clarity_score": clarity,
            "technical_accuracy_score": accuracy,
            "confidence_score": confidence,
            "overall_score": overall,
            "strengths": feedback["strengths"],
            "weaknesses": feedback["weaknesses"],
            "suggestions": feedback["suggestions"],
            "key_phrases": keywords_data["key_phrases"],
            "matched_key_phrases": keywords_data["matched_key_phrases"],
            "missing_key_phrases": keywords_data["missing_key_phrases"]
        }

    def _extract_heuristic_keywords(self, question: str, answer: str, category: str, jd: JobDescription | None = None) -> Dict[str, List[str]]:
        """Heuristically extracts 3-5 key phrases for a question and checks if they exist in the answer."""
        stop_words = {"the", "a", "an", "is", "are", "of", "to", "in", "for", "on", "with", "at", "by", "from", "how", "what", "why", "you", "your", "can", "describe", "explain", "would", "do", "does", "did", "have", "has", "had", "will", "shall", "should", "could", "would", "about", "using", "your", "experience", "with", "in", "project", "technical", "tell", "me", "about"}
        
        words = re.findall(r'\b[a-zA-Z]{3,15}\b', question.lower())
        filtered_words = [w for w in words if w not in stop_words]
        
        additional_keywords = []
        if jd:
            if jd.required_skills:
                additional_keywords.extend(jd.required_skills)
            if jd.technologies:
                additional_keywords.extend(jd.technologies)
        
        candidates = []
        for w in filtered_words:
            if w not in candidates:
                candidates.append(w)
        for w in additional_keywords:
            w_clean = w.lower().strip()
            if w_clean and w_clean not in candidates and w_clean in question.lower():
                candidates.insert(0, w_clean)
                
        if not candidates:
            if category == "technical":
                candidates = ["architecture", "scaling", "performance", "database"]
            elif category == "dsa":
                candidates = ["complexity", "algorithm", "optimization", "data structure"]
            elif category == "project":
                candidates = ["implementation", "challenges", "testing", "development"]
            else:
                candidates = ["communication", "problem solving", "collaboration", "leadership"]
                
        key_phrases = [c.title() if len(c) > 3 else c.upper() for c in candidates[:5]]
        
        answer_lower = answer.lower()
        matched = []
        missing = []
        for kp in key_phrases:
            if kp.lower() in answer_lower:
                matched.append(kp)
            else:
                missing.append(kp)
                
        return {
            "key_phrases": key_phrases,
            "matched_key_phrases": matched,
            "missing_key_phrases": missing
        }

    def apply_jd_fit_adjustment(
        self,
        relevance: int,
        accuracy: int,
        answer: str,
        jd: JobDescription | None,
        match: ResumeMatch | None
    ) -> Tuple[int, int]:
        """Adjusts fallback scores based on whether the answer addresses JD-critical topics."""
        topics = []
        if jd:
            topics.extend(jd.required_skills or [])
            topics.extend(jd.technologies or [])
        if match:
            topics.extend(match.missing_skills or [])
            topics.extend(match.missing_technologies or [])
            topics.extend(match.matched_skills or [])
            topics.extend(match.matched_technologies or [])

        normalized_topics = []
        for topic in topics:
            if isinstance(topic, str) and topic.strip() and topic.lower() not in [t.lower() for t in normalized_topics]:
                normalized_topics.append(topic.strip())

        if not normalized_topics:
            return relevance, accuracy

        answer_lower = answer.lower()
        hits = sum(1 for topic in normalized_topics[:12] if topic.lower() in answer_lower)
        if hits == 0:
            return max(0, relevance - 15), max(0, accuracy - 15)
        if hits >= 3:
            return min(100, relevance + 8), min(100, accuracy + 8)
        return min(100, relevance + 3), min(100, accuracy + 3)

    def _evaluate_with_llm(
        self,
        question: str,
        answer: str,
        category: str,
        jd: JobDescription | None = None,
        match: ResumeMatch | None = None
    ) -> Dict[str, Any]:
        """Calls Gemini API to generate structured evaluation and feedback."""
        jd_context = {
            "job_title": jd.job_title if jd else None,
            "company_name": jd.company_name if jd else None,
            "required_skills": jd.required_skills if jd else [],
            "preferred_skills": jd.preferred_skills if jd else [],
            "technologies": jd.technologies if jd else [],
            "responsibilities": jd.responsibilities if jd else [],
        }
        match_context = {
            "matched_skills": match.matched_skills if match else [],
            "missing_skills": match.missing_skills if match else [],
            "matched_technologies": match.matched_technologies if match else [],
            "missing_technologies": match.missing_technologies if match else [],
        }
        prompt = f"""
You are an expert technical interviewer and senior engineering evaluator.
Evaluate the candidate's answer to the interview question below against the target JD.

Question Category: {category}
Question: {question}
Candidate's Answer: {answer}
Target JD Context:
{json.dumps(jd_context, indent=2)}
Resume/JD Match Context:
{json.dumps(match_context, indent=2)}

Perform a deep analysis and evaluate the following metrics on a scale of 0 to 100:
1. relevance_score: How directly the answer addresses the exact question and JD requirement.
2. depth_score: Specificity, examples, trade-offs, constraints, edge cases, and implementation detail.
3. clarity_score: Coherent structure, concise explanation, and easy-to-follow reasoning.
4. technical_accuracy_score: Correctness for the relevant JD skills/technologies, architecture, algorithms, and terminology.
5. confidence_score: Directness, ownership, concrete language, and lack of vague filler.

Calculate an overall_score (weighted average: relevance=25%, depth=25%, clarity=15%, accuracy=25%, confidence=10%).

Also generate:
- strengths: A list of 2-3 specific positive things about the response, tied to the JD when possible.
- weaknesses: A list of 1-2 concrete gaps, missing details, incorrect claims, or shallow areas.
- suggestions: A list of 2-3 actionable improvements the candidate can apply in the next answer.
- key_phrases: A list of 3-5 critical keywords or key technical phrases/concepts (e.g., 'React Hooks', 'Dependency Array', 'B-Trees') expected in a correct/complete answer to this specific question.
- matched_key_phrases: A list of those keywords/key-phrases from key_phrases that the candidate actually mentioned or correctly addressed in their answer.
- missing_key_phrases: A list of those keywords/key-phrases from key_phrases that the candidate did NOT mention or address in their answer.

Scoring rules:
- Do not give high scores for vague answers.
- Penalize answers that do not mention the relevant JD skill, system behavior, trade-off, or example.
- Reward concrete examples, measurable impact, implementation detail, and accurate reasoning.
- If the answer is generic but fluent, clarity may be decent but relevance/depth/accuracy should be lower.

Return ONLY a valid JSON object matching the format below. Do not wrap in markdown or include ```json.

Output Format:
{{
  "relevance_score": 85,
  "depth_score": 75,
  "clarity_score": 90,
  "technical_accuracy_score": 80,
  "confidence_score": 85,
  "overall_score": 82,
  "strengths": ["string"],
  "weaknesses": ["string"],
  "suggestions": ["string"],
  "key_phrases": ["keyword1", "keyword2", "keyword3"],
  "matched_key_phrases": ["keyword1"],
  "missing_key_phrases": ["keyword2", "keyword3"]
}}
"""
        response_text = llm_service.generate_content(prompt, temperature=0.25, max_tokens=2048, response_json=True)
        text = response_text.strip()

        if text.startswith("```"):
            lines = text.splitlines()
            if lines[0].startswith("```json") or lines[0].startswith("```"):
                text = "\n".join(lines[1:-1])

        data = json.loads(text)
        
        # Ensure correct key typing
        required_keys = [
            "relevance_score", "depth_score", "clarity_score", 
            "technical_accuracy_score", "confidence_score", "overall_score",
            "strengths", "weaknesses", "suggestions",
            "key_phrases", "matched_key_phrases", "missing_key_phrases"
        ]
        for key in required_keys:
            if key not in data:
                # Provide fallback for missing keys
                if key in ["key_phrases", "matched_key_phrases", "missing_key_phrases"]:
                    data[key] = []
                else:
                    raise ValueError(f"Missing evaluation key: {key}")
            
        return data

    # Core Heuristic Functions
    def evaluate_relevance(self, question: str, answer: str, category: str) -> int:
        """Heuristically measures relevance of the answer to the question."""
        q_words = set(re.findall(r'\w+', question.lower()))
        # Filter out common stop words
        stop_words = {"the", "a", "an", "is", "are", "of", "to", "in", "for", "on", "with", "at", "by", "from", "how", "what", "why", "you", "your", "can", "describe", "explain"}
        keywords = q_words - stop_words

        if not keywords:
            return 70

        a_lower = answer.lower()
        matches = sum(1 for kw in keywords if kw in a_lower)
        
        # Calculate overlap percentage
        ratio = matches / len(keywords)
        score = int(45 + (ratio * 50))  # Range: 45 to 95
        return min(max(score, 0), 100)

    def evaluate_depth(self, question: str, answer: str, category: str) -> int:
        """Heuristically measures depth based on length and richness."""
        word_count = len(answer.split())
        
        if word_count < 15:
            score = 30
        elif word_count < 40:
            score = 55
        elif word_count < 80:
            score = 75
        elif word_count < 150:
            score = 88
        else:
            score = 95

        # DSA or Technical might require code blocks or technical keywords for depth
        if category in ["dsa", "technical"]:
            if any(code_kw in answer for code_kw in ["def ", "class ", "return", "function", "const", "let ", "import"]):
                score += 5

        return min(max(score, 0), 100)

    def evaluate_clarity(self, question: str, answer: str, category: str) -> int:
        """Heuristically measures clarity based on sentence structure and readability."""
        sentences = [s.strip() for s in re.split(r'[.!?]', answer) if s.strip()]
        if not sentences:
            return 30

        # Good formatting indicator: presence of uppercase letters, punctuation
        has_punctuation = answer.endswith(('.', '!', '?'))
        words = answer.split()
        avg_word_len = sum(len(w) for w in words) / len(words) if words else 0

        score = 75
        if has_punctuation:
            score += 10
        if 4 < avg_word_len < 7:  # reasonable word length distribution
            score += 5
        else:
            score -= 10

        # Penalize for lack of capitalisation
        if not answer[0].isupper() if answer else False:
            score -= 10

        return min(max(score, 0), 100)

    def evaluate_technical_accuracy(self, question: str, answer: str, category: str) -> int:
        """Heuristically measures technical accuracy based on tech terms matching."""
        tech_terms = [
            "database", "index", "cache", "concurrency", "scaling", "api", "query", "optimize", "runtime", "complexity", 
            "memory", "latency", "throughput", "http", "rest", "graphql", "sql", "nosql", "json", "python", "javascript", 
            "docker", "kubernetes", "microservices", "load balancer", "threading", "process", "lock", "queue", "stack", 
            "tree", "graph", "hash", "binary", "sorting", "search", "asynchronous", "await", "promise", "git"
        ]
        
        a_lower = answer.lower()
        matches = sum(1 for term in tech_terms if term in a_lower)

        if category in ["technical", "dsa"]:
            if matches == 0:
                score = 50
            elif matches <= 2:
                score = 70
            elif matches <= 5:
                score = 85
            else:
                score = 95
        else:
            # Behavioral or Project evaluation has slightly lower tech term weight
            score = 80 + min(matches * 3, 15)

        return min(max(score, 0), 100)

    def evaluate_confidence(self, question: str, answer: str, category: str) -> int:
        """Heuristically measures confidence based on speech fillers."""
        filler_words = ["um", "uh", "like", "maybe", "i think", "i guess", "probably", "sort of", "kind of", "not sure", "possibly"]
        a_lower = answer.lower()
        
        filler_count = sum(a_lower.count(filler) for filler in filler_words)

        score = 95 - (filler_count * 5)
        # Reward structures that indicate high confidence
        strong_phrases = ["specifically", "key decision", "resolved by", "architected", "implemented", "consequently"]
        rewards = sum(5 for phrase in strong_phrases if phrase in a_lower)
        score += rewards

        return min(max(score, 0), 100)

    def calculate_overall_score(
        self, relevance: int, depth: int, clarity: int, accuracy: int, confidence: int
    ) -> int:
        """Calculates a weighted average overall score."""
        weighted_score = (
            (relevance * 0.25) +
            (depth * 0.25) +
            (clarity * 0.15) +
            (accuracy * 0.25) +
            (confidence * 0.10)
        )
        return int(round(weighted_score))

    def generate_feedback(
        self, question: str, answer: str, category: str,
        relevance: int, depth: int, clarity: int, accuracy: int, confidence: int
    ) -> Dict[str, List[str]]:
        """Generates dynamic feedback points based on calculated scores."""
        strengths = []
        weaknesses = []
        suggestions = []

        # Category mapping
        cat_display = category.capitalize()

        # 1. Evaluate Relevance
        if relevance >= 80:
            strengths.append(f"Demonstrated good alignment with the question objectives under the {cat_display} category.")
        else:
            weaknesses.append("The response partially deviated from the specific question prompt.")
            suggestions.append("Ensure you address all parts of the question directly in your opening statements.")

        # 2. Evaluate Depth
        if depth >= 80:
            strengths.append("Provided a detailed explanation with structural depth and elaboration.")
        elif depth <= 60:
            weaknesses.append("The response was brief and lacked necessary supporting detail or context.")
            suggestions.append("Elaborate further by detailing key architecture decisions, constraints, or alternatives.")

        # 3. Evaluate Clarity
        if clarity >= 80:
            strengths.append("The answer is structured cleanly, making it easy to follow the technical narrative.")
        else:
            weaknesses.append("The response structure could be improved to make the system explanation more cohesive.")
            suggestions.append("Use the STAR format (Situation, Task, Action, Result) or structured paragraphs to present your thoughts.")

        # 4. Evaluate Technical Accuracy
        if accuracy >= 80:
            strengths.append("Accurately utilized relevant industry terminology and design concepts.")
        elif accuracy <= 60:
            weaknesses.append("Lacked reference to specific technical frameworks, protocols, or algorithmic parameters.")
            suggestions.append("Incorporate more technical vocabulary, system components, or specific design patterns.")

        # 5. Evaluate Confidence
        if confidence >= 80:
            strengths.append("Answered assertively without relying on hesitation terms or filler phrases.")
        else:
            weaknesses.append("Contained some filler words or uncertain language (e.g. 'maybe', 'not sure').")
            suggestions.append("Practice delivering answers with strong declarative statements to project authority.")

        # Ensure we always return at least some default suggestions/strengths if empty
        if not strengths:
            strengths.append("Communicated thoughts clearly on the subject matter.")
        if not weaknesses:
            weaknesses.append("No critical architectural gaps identified in the answer.")
        if not suggestions:
            suggestions.append("Keep refining the level of details and structural layouts of your answers.")

        return {
            "strengths": strengths[:3],
            "weaknesses": weaknesses[:2],
            "suggestions": suggestions[:3]
        }

    # Helper formatters
    def _format_detail(self, answer: InterviewAnswer, eval_record: AnswerEvaluation) -> Dict[str, Any]:
        """Formats a database model pair into the detailed response dictionary."""
        return {
            "id": eval_record.id,
            "session_id": eval_record.session_id,
            "answer_id": eval_record.answer_id,
            "question": answer.question,
            "answer": answer.answer,
            "category": answer.category,
            "overall_score": eval_record.overall_score,
            "relevance_score": eval_record.relevance_score,
            "depth_score": eval_record.depth_score,
            "clarity_score": eval_record.clarity_score,
            "technical_accuracy_score": eval_record.technical_accuracy_score,
            "confidence_score": eval_record.confidence_score,
            "strengths": eval_record.strengths or [],
            "weaknesses": eval_record.weaknesses or [],
            "suggestions": eval_record.suggestions or [],
            "key_phrases": eval_record.key_phrases or [],
            "matched_key_phrases": eval_record.matched_key_phrases or [],
            "missing_key_phrases": eval_record.missing_key_phrases or [],
            "created_at": eval_record.created_at
        }


# Global service instance
evaluation_service = EvaluationService()
