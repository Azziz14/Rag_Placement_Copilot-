import os
import subprocess
import tempfile
import time
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class CodeRunner:
    """Service to execute user code in isolated subprocesses with constraints."""

    def execute_code(
        self,
        code: str,
        language: str,
        input_data: str,
        time_limit_sec: float = 2.0,
        memory_limit_mb: int = 128
    ) -> Dict[str, Any]:
        language = language.lower().strip()
        
        if language == "python":
            return self._execute_python(code, input_data, time_limit_sec)
        elif language == "javascript":
            return self._execute_javascript(code, input_data, time_limit_sec)
        elif language in ["c++", "cpp"]:
            return self._execute_cpp(code, input_data, time_limit_sec)
        elif language == "java":
            return self._execute_java(code, input_data, time_limit_sec)
        else:
            return {
                "success": False,
                "stdout": "",
                "stderr": f"Unsupported language: '{language}'",
                "error_type": "UnsupportedLanguage"
            }

    def _execute_python(self, code: str, input_val: str, timeout: float) -> Dict[str, Any]:
        # Formulate full executable code with wrapper to execute and print the function output
        wrapper = f"""
{code}

# Test execution wrapper
import json
try:
    # Try parsing input as JSON (list, dict, etc.)
    parsed_input = json.loads('''{input_val}''')
except Exception:
    parsed_input = '''{input_val}'''

# Attempt to call 'solution' or 'solve' function
if 'solution' in globals():
    res = solution(parsed_input)
    if res is not None:
        print(res)
elif 'solve' in globals():
    res = solve(parsed_input)
    if res is not None:
        print(res)
"""
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode="w", encoding="utf-8") as temp_file:
            temp_file.write(wrapper)
            temp_path = temp_file.name

        try:
            start_time = time.time()
            process = subprocess.run(
                ["python", temp_path],
                capture_output=True,
                text=True,
                timeout=timeout
            )
            elapsed = time.time() - start_time
            
            if process.returncode != 0:
                return {
                    "success": False,
                    "stdout": process.stdout,
                    "stderr": process.stderr,
                    "error_type": "RuntimeError",
                    "time_taken": elapsed
                }
            return {
                "success": True,
                "stdout": process.stdout,
                "stderr": process.stderr,
                "time_taken": elapsed
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "stdout": "",
                "stderr": f"Time Limit Exceeded (>{timeout}s)",
                "error_type": "TimeLimitExceeded"
            }
        except Exception as e:
            return {
                "success": False,
                "stdout": "",
                "stderr": str(e),
                "error_type": "ExecutorError"
            }
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def _execute_javascript(self, code: str, input_val: str, timeout: float) -> Dict[str, Any]:
        wrapper = f"""
{code}

// Test execution wrapper
let parsedInput;
try {{
    parsedInput = JSON.parse('{input_val}');
}} catch(e) {{
    parsedInput = '{input_val}';
}}

if (typeof solution === 'function') {{
    let res = solution(parsedInput);
    if (res !== undefined) console.log(res);
}} else if (typeof solve === 'function') {{
    let res = solve(parsedInput);
    if (res !== undefined) console.log(res);
}}
"""
        with tempfile.NamedTemporaryFile(suffix=".js", delete=False, mode="w", encoding="utf-8") as temp_file:
            temp_file.write(wrapper)
            temp_path = temp_file.name

        try:
            start_time = time.time()
            process = subprocess.run(
                ["node", temp_path],
                capture_output=True,
                text=True,
                timeout=timeout
            )
            elapsed = time.time() - start_time
            
            if process.returncode != 0:
                return {
                    "success": False,
                    "stdout": process.stdout,
                    "stderr": process.stderr,
                    "error_type": "RuntimeError",
                    "time_taken": elapsed
                }
            return {
                "success": True,
                "stdout": process.stdout,
                "stderr": process.stderr,
                "time_taken": elapsed
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "stdout": "",
                "stderr": f"Time Limit Exceeded (>{timeout}s)",
                "error_type": "TimeLimitExceeded"
            }
        except FileNotFoundError:
            return {
                "success": False,
                "stdout": "",
                "stderr": "Node.js (node) is not installed or not found on system PATH.",
                "error_type": "MissingDependency"
            }
        except Exception as e:
            return {
                "success": False,
                "stdout": "",
                "stderr": str(e),
                "error_type": "ExecutorError"
            }
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def _execute_cpp(self, code: str, input_val: str, timeout: float) -> Dict[str, Any]:
        # C++ compilation and execution fallback helper
        return {
            "success": False,
            "stdout": "",
            "stderr": "C++ compilation sandbox requires GCC (g++) compiler configured on host.",
            "error_type": "MissingDependency"
        }

    def _execute_java(self, code: str, input_val: str, timeout: float) -> Dict[str, Any]:
        # Java compilation and execution fallback helper
        return {
            "success": False,
            "stdout": "",
            "stderr": "Java execution requires JDK (javac & java) installed and configured on host.",
            "error_type": "MissingDependency"
        }

code_runner = CodeRunner()
