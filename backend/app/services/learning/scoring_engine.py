import logging
import json
import re
from typing import Dict, Any, List
from app.services.code_runner.runner import code_runner
from app.services.code_runner.validators import validate_expected_output
from app.services.llm_service import llm_service

logger = logging.getLogger(__name__)

class ScoringEngine:
    """Evaluates theory and coding submissions strictly according to correctness rules."""

    def evaluate_submission(self, question_data: Dict[str, Any], submission: Dict[str, Any]) -> Dict[str, Any]:
        """Orchestrates submission grading based on whether it is coding or theory."""
        is_coding = question_data.get("is_coding", False)

        if is_coding:
            return self._evaluate_coding(question_data, submission)
        else:
            return self._evaluate_theory(question_data, submission)

    def _evaluate_coding(self, question_data: Dict[str, Any], submission: Dict[str, Any]) -> Dict[str, Any]:
        code = submission.get("code", "")
        language = submission.get("language", "python")
        test_cases = question_data.get("test_cases", [])

        if not test_cases:
            return {
                "score": 0.0,
                "status": "wrong",
                "feedback": "No test cases provided for this coding question.",
                "test_case_results": []
            }

        passed_count = 0
        results = []

        for index, tc in enumerate(test_cases):
            input_val = str(tc.get("input", ""))
            expected = str(tc.get("expected_output", ""))
            
            # Execute code using isolated code runner
            exec_res = code_runner.execute_code(code, language, input_val)
            actual_output = exec_res.get("stdout", "")
            stderr = exec_res.get("stderr", "")
            
            if exec_res.get("success", False):
                is_correct = validate_expected_output(actual_output, expected)
                if is_correct:
                    passed_count += 1
                    status = "passed"
                else:
                    status = "failed"
            else:
                is_correct = False
                status = "error"

            results.append({
                "test_case_index": index + 1,
                "input": input_val,
                "expected": expected,
                "actual": actual_output.strip() if actual_output else "",
                "stderr": stderr.strip() if stderr else "",
                "status": status
            })

        total = len(test_cases)
        # Rules: Correct = full score, Partial = partial score, Wrong = 0
        score = 0.0
        if passed_count == total:
            score = 100.0
            status_text = "correct"
            feedback = f"All {total} test cases passed successfully!"
        elif passed_count > 0:
            score = round((passed_count / total) * 100.0, 1)
            status_text = "partial"
            feedback = f"Passed {passed_count} of {total} test cases."
        else:
            score = 0.0
            status_text = "wrong"
            feedback = "All test cases failed or code execution crashed."

        return {
            "score": score,
            "status": status_text,
            "feedback": feedback,
            "test_case_results": results
        }

    def _evaluate_theory(self, question_data: Dict[str, Any], submission: Dict[str, Any]) -> Dict[str, Any]:
        q_type = question_data.get("type", "short_answer")
        user_answer = submission.get("answer", "")

        if q_type == "mcq":
            correct_index = int(question_data.get("correct_choice", 0))
            try:
                user_index = int(submission.get("choice_index", -1))
            except ValueError:
                user_index = -1

            if user_index == correct_index:
                return {
                    "score": 100.0,
                    "status": "correct",
                    "feedback": "Correct choice selected!"
                }
            else:
                return {
                    "score": 0.0,
                    "status": "wrong",
                    "feedback": f"Wrong choice. Expected index {correct_index}."
                }

        # For conceptual questions, evaluate correctness via LLM
        prompt = f"""
You are an expert technical grading assistant.
Grade the candidate's answer to the theory question based on the expected model answer.

Question Type: {q_type}
Question: {question_data.get("question")}
Expected Model Answer Guidance: {question_data.get("model_answer")}
Candidate's Answer: {user_answer}

Grading Rules:
- If the answer is completely correct and covers the core concepts: score = 100, status = "correct".
- If the answer is partially correct: score = 50, status = "partial".
- If the answer is wrong, irrelevant, empty, or misses the core concepts: score = 0, status = "wrong". Never give positive points for incorrect claims.

Return ONLY a valid JSON object matching the format below. Do not wrap in markdown or include ```json.

Output Format:
{{
  "score": 0.0,
  "status": "correct | partial | wrong",
  "feedback": "Detailed justification..."
}}
"""
        try:
            response = llm_service.generate_content(prompt, temperature=0.2, response_json=True)
            text = response.strip()
            if text.startswith("```"):
                lines = text.splitlines()
                if lines[0].startswith("```json") or lines[0].startswith("```"):
                    text = "\n".join(lines[1:-1])
            match_json = re.search(r"\{.*\}", text, re.DOTALL)
            if match_json:
                text = match_json.group(0)

            data = json.loads(text)
            
            # Strict verification of scoring bounds
            score = float(data.get("score", 0.0))
            if data.get("status") == "wrong":
                score = 0.0
            data["score"] = score
            return data
        except Exception as e:
            logger.error(f"Failed to grade theory question: {str(e)}")
            # Fallback grading
            if not user_answer or len(user_answer.strip()) < 5:
                return {"score": 0.0, "status": "wrong", "feedback": "Answer was empty or too short."}
            return {"score": 50.0, "status": "partial", "feedback": "Heuristic fallback evaluation."}

scoring_engine = ScoringEngine()
