import json
import logging
import re
from typing import List, Dict, Any, Optional
from app.services.llm_service import llm_service
from app.core.cache import file_cache

logger = logging.getLogger(__name__)

CODING_DOMAINS = ["sql", "dsa"]
CODING_KEYWORDS = ["write", "implement", "query", "queries", "code", "program", "function", "algorithm", "array", "hashmap", "tree", "graph", "linked list", "join", "group by"]

class QuestionGenerator:
    """Service to generate both theory and coding questions dynamically based on domain and topic."""

    def is_coding_topic(self, domain: str, topic: str) -> bool:
        """Heuristically detects if a topic warrants a coding challenge."""
        domain_lower = domain.lower()
        topic_lower = topic.lower()

        if domain_lower in CODING_DOMAINS:
            return True
        
        return any(kw in topic_lower for kw in CODING_KEYWORDS)

    def generate_question(
        self,
        domain: str,
        topic: str,
        difficulty: str,
        language: str = "python",
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """Generates a structured question (either coding or theory)."""
        is_coding = self.is_coding_topic(domain, topic)
        language = language.lower()
        
        cache_key = f"question_{domain.lower()}_{topic.lower()}_{difficulty.lower()}_{language}"
        if not force_refresh:
            cached_data = file_cache.get(cache_key)
            if cached_data:
                return cached_data

        import random
        import uuid
        seed = f"{random.randint(1000, 999999)}-{uuid.uuid4().hex[:6]}"

        if is_coding:
            result = self._generate_coding_question(domain, topic, difficulty, language, seed)
        else:
            result = self._generate_theory_question(domain, topic, difficulty, seed)
            
        file_cache.set(cache_key, result)
        return result

    def _generate_coding_question(
        self,
        domain: str,
        topic: str,
        difficulty: str,
        language: str,
        seed: str
    ) -> Dict[str, Any]:
        prompt = f"""
You are a senior technical interviewer creating a coding challenge.
Generate a completely unique and original coding challenge for the domain '{domain}' on the topic '{topic}' with difficulty '{difficulty}'.
The user's preferred language is '{language}'.

== UNIQUE GENERATION DIRECTIVE (Seed: {seed}) ==
- You must create a completely fresh and distinct problem scenario, application context, constraints, and algorithmic requirements.
- Do not repeat standard template problems. Create a realistic, highly specific engineering scenario (e.g. log parsing, rate limiters, sensor telemetry, inventory reconciliation, network routing, etc.) that tests this topic.

== CRITICAL RULES FOR starter_code ==
- starter_code MUST contain ONLY the function signature(s) with an empty body (use 'pass' in Python, empty braces in JS/Java/C++).
- starter_code MUST NOT contain any logic, algorithm steps, hints, comments about the approach, or partial solutions.
- starter_code is what the user TYPES INTO to solve the problem — it must be completely blank inside.
- WRONG example: "def solve(nums):\\n    seen = set()\\n    for n in nums:\\n        ..." (this reveals the approach)
- CORRECT example: "def solve(nums):\\n    # Write your solution here\\n    pass"

Provide:
1. title: Title of the problem.
2. description: Clear challenge explanation, constraints, and examples.
3. starter_code: ONLY the empty function signature(s) with a single placeholder comment and pass/empty body. NO solution logic whatsoever.
4. test_cases: List of at least 3 test case objects. Each must have:
   - input: String representing the input arguments.
   - expected_output: String matching what the program should print to stdout.
5. model_solution: A complete, fully functional, optimized reference solution in '{language}'. This is separate from starter_code.
6. language: The programming language string.

Return ONLY a valid JSON object. Do not wrap in markdown or include ```json.

Output Format:
{{
  "is_coding": true,
  "title": "Problem Title",
  "description": "Problem description with examples and constraints...",
  "starter_code": "def solve(nums):\\n    # Write your solution here\\n    pass",
  "model_solution": "def solve(nums):\\n    # complete working solution here",
  "test_cases": [
    {{"input": "input_val", "expected_output": "expected_val"}}
  ],
  "language": "{language}"
}}
"""
        try:
            # Use higher token limit for coding questions (starter code + model solution + test cases)
            response = llm_service.generate_content(prompt, temperature=0.8, response_json=True, max_tokens=4096)
            text = response.strip()
            # Strip markdown code fences if present
            if text.startswith("```"):
                lines = text.splitlines()
                if lines[0].startswith("```json") or lines[0].startswith("```"):
                    text = "\n".join(lines[1:-1])
            # Extract JSON object from response
            match_json = re.search(r"\{.*\}", text, re.DOTALL)
            if match_json:
                text = match_json.group(0)

            data = json.loads(text)
            data["is_coding"] = True
            # Sanitize starter_code — strip any full solution that leaked in
            data["starter_code"] = self._sanitize_starter_code(
                data.get("starter_code", ""),
                data.get("model_solution", ""),
                topic,
                language
            )
            return data
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse failed for coding question: {str(e)}")
            return self._fallback_coding_question(topic, language)
        except Exception as e:
            logger.error(f"Failed to generate coding question: {str(e)}")
            return self._fallback_coding_question(topic, language)

    def _generate_theory_question(
        self,
        domain: str,
        topic: str,
        difficulty: str,
        seed: str
    ) -> Dict[str, Any]:
        prompt = f"""
You are an expert technical interviewer.
Generate a completely unique and original theory question for the domain '{domain}' on the topic '{topic}' with difficulty '{difficulty}'.

== UNIQUE GENERATION DIRECTIVE (Seed: {seed}) ==
- You must create a completely fresh and distinct question, scenario, or case-study. Do not ask generic 'What is X?' questions.
- Introduce a unique, realistic engineering scenario or architectural trade-off that tests this topic.

Randomly select one of the following question types:
- "mcq" (Multiple Choice Question)
- "short_answer" (Brief conceptual answer)
- "long_answer" (Detailed architectural or system explanation)
- "interview" (Typical verbal interview style)

Depending on the chosen type, construct the JSON response:
- If "mcq": Include 'question', 'choices' (list of 4 strings), and 'correct_choice' (integer index 0-3).
- If "short_answer" / "long_answer" / "interview": Include 'question', and 'model_answer' (rubric / expected points).

Return ONLY a valid JSON object matching the format below. Do not wrap in markdown or include ```json.

Output Format:
{{
  "is_coding": false,
  "type": "mcq | short_answer | long_answer | interview",
  "question": "Question text...",
  "choices": ["choice 0", "choice 1", "choice 2", "choice 3"],
  "correct_choice": 0,
  "model_answer": "Expected conceptual explanation..."
}}
"""
        try:
            response = llm_service.generate_content(prompt, temperature=0.6, response_json=True, max_tokens=2048)
            text = response.strip()
            # Strip markdown code fences if present
            if text.startswith("```"):
                lines = text.splitlines()
                if lines[0].startswith("```json") or lines[0].startswith("```"):
                    text = "\n".join(lines[1:-1])
            # Extract JSON object from response
            match_json = re.search(r"\{.*\}", text, re.DOTALL)
            if match_json:
                text = match_json.group(0)

            data = json.loads(text)
            data["is_coding"] = False
            return data
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse failed for theory question: {str(e)}")
            return self._fallback_theory_question(topic)
        except Exception as e:
            logger.error(f"Failed to generate theory question: {str(e)}")
            return self._fallback_theory_question(topic)

    def _sanitize_starter_code(
        self,
        starter_code: str,
        model_solution: str,
        topic: str,
        language: str
    ) -> str:
        """
        Ensures starter_code is a blank stub with no solution logic.
        If the LLM leaked the solution into starter_code, replace it with a safe empty stub.
        """
        if not starter_code:
            return self._blank_stub(language)

        # If starter_code looks identical (or nearly identical) to model_solution, it leaked
        stripped_starter = starter_code.strip()
        stripped_solution = model_solution.strip() if model_solution else ""
        if stripped_solution and stripped_starter == stripped_solution:
            logger.warning("starter_code matched model_solution exactly — replacing with blank stub.")
            return self._blank_stub(language)

        # Heuristic: if starter_code is suspiciously long relative to a simple stub,
        # and contains actual algorithmic tokens, it probably leaked solution logic.
        SOLUTION_TOKENS = [
            # Python
            "return ", "for ", "while ", "if ", "elif ", "sorted(", "set(", "dict(",
            "append(", ".add(", "enumerate(", "zip(", "range(",
            # JS / Java / C++
            "for(", "for (", "while(", "while (", "return ", "push(", "pop(",
            "new HashMap", "new HashSet", "ArrayList", "std::sort", "std::unordered",
        ]
        lines = stripped_starter.splitlines()
        # A legitimate stub should have at most a signature + 1-2 placeholder lines
        if len(lines) > 5:
            logic_line_count = sum(
                1 for line in lines
                if any(tok in line for tok in SOLUTION_TOKENS)
                and not line.strip().startswith("#")
                and not line.strip().startswith("//")
            )
            if logic_line_count >= 2:
                logger.warning(
                    "starter_code appears to contain solution logic (%d logic lines) — replacing with blank stub.",
                    logic_line_count
                )
                return self._blank_stub(language)

        return starter_code

    def _blank_stub(self, language: str) -> str:
        """Returns a minimal blank function stub for the given language."""
        stubs = {
            "python":     "def solve(args):\n    # Write your solution here\n    pass",
            "javascript": "function solve(args) {\n    // Write your solution here\n}",
            "java":       "public class Solution {\n    public static void solve() {\n        // Write your solution here\n    }\n}",
            "c++":        "#include <bits/stdc++.h>\nusing namespace std;\n\nvoid solve() {\n    // Write your solution here\n}",
        }
        return stubs.get(language.lower(), stubs["python"])

    def _fallback_coding_question(self, topic: str, language: str) -> Dict[str, Any]:
        """Safe fallback coding question if LLM fails."""
        python_starter = "def solve(arr):\n    # Write your solution here\n    pass"
        js_starter = "function solve(arr) {\n    // Write your solution here\n}"
        java_starter = "public class Solution {\n    public static int solve(int[] arr) {\n        // Write your solution here\n        return 0;\n    }\n}"
        cpp_starter = "#include <vector>\nusing namespace std;\n\nint solve(vector<int>& arr) {\n    // Write your solution here\n    return 0;\n}"

        starters = {
            "python": python_starter,
            "javascript": js_starter,
            "java": java_starter,
            "c++": cpp_starter
        }

        python_solution = "def solve(arr):\n    return sum(arr)"
        js_solution = "function solve(arr) {\n    return arr.reduce((a, b) => a + b, 0);\n}"
        java_solution = "public class Solution {\n    public static int solve(int[] arr) {\n        int sum = 0;\n        for(int x : arr) sum += x;\n        return sum;\n    }\n}"
        cpp_solution = "#include <vector>\n#include <numeric>\n\nint solve(std::vector<int>& arr) {\n    return std::accumulate(arr.begin(), arr.end(), 0);\n}"

        solutions = {
            "python": python_solution,
            "javascript": js_solution,
            "java": java_solution,
            "c++": cpp_solution
        }

        return {
            "is_coding": True,
            "title": f"Coding Practice: {topic}",
            "description": f"Write a function to solve a basic challenge relating to {topic}. For testing, implement a function returning the sum of array values.",
            "starter_code": starters.get(language, python_starter),
            "model_solution": solutions.get(language, python_solution),
            "test_cases": [
                {"input": "[1, 2, 3]", "expected_output": "6"},
                {"input": "[10, -5]", "expected_output": "5"}
            ],
            "language": language
        }

    def _fallback_theory_question(self, topic: str) -> Dict[str, Any]:
        """Safe fallback theory question if LLM fails."""
        return {
            "is_coding": False,
            "type": "short_answer",
            "question": f"Explain the core concept and purpose of {topic} in modern computer systems.",
            "model_answer": f"A standard explanation of {topic} focusing on its architectural definition, benefits, and common trade-offs."
        }

question_generator = QuestionGenerator()
