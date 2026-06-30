import re

def clean_output(output: str) -> str:
    """Standardizes string output by trimming spaces, trailing newlines, and carriage returns."""
    if not output:
        return ""
    # Normalize carriage returns and strip leading/trailing whitespace
    cleaned = output.replace("\r\n", "\n").replace("\r", "\n").strip()
    # Replace multiple spaces with a single space
    cleaned = re.sub(r"[ \t]+", " ", cleaned)
    # Remove empty lines
    lines = [line.strip() for line in cleaned.split("\n") if line.strip()]
    return "\n".join(lines)

def validate_expected_output(actual: str, expected: str) -> bool:
    """Checks if the actual output matches the expected output strictly."""
    return clean_output(actual) == clean_output(expected)
