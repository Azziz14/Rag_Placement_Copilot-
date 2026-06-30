"""Service module for parsing job descriptions using PDF/DOCX extractors, Regex, SpaCy, and section heuristics.
"""

import os
import re
from typing import List, Dict, Any, Tuple
from app.services.resume_parser import extract_text, COMMON_SKILLS, COMMON_TECHNOLOGIES, nlp

# Section detection patterns for Job Descriptions
JD_SECTION_PATTERNS = {
    "responsibilities": re.compile(
        r"^\b(responsibilities|what you will do|key responsibilities|duties|roles and responsibilities|expectations|your role|tasks|responsibilities include)\b",
        re.IGNORECASE
    ),
    "requirements": re.compile(
        r"^\b(requirements|qualifications|what you need|what we are looking for|basic qualifications|skills required|experience required|criteria|about you)\b",
        re.IGNORECASE
    ),
    "preferred": re.compile(
        r"^\b(preferred qualifications|preferred skills|nice to have|plus|desired skills|preferred experience|bonus points)\b",
        re.IGNORECASE
    ),
    "about_company": re.compile(
        r"^\b(about us|about the company|who we are|our company|company overview|about)\b",
        re.IGNORECASE
    )
}


def _get_jd_sections(text: str) -> Dict[str, List[str]]:
    """Divide the JD text into sections based on keywords/headings."""
    lines = [line.strip() for line in text.split("\n")]
    sections: Dict[str, List[str]] = {
        "responsibilities": [],
        "requirements": [],
        "preferred": [],
        "about_company": [],
        "unknown": []
    }

    current_section = "unknown"
    for line in lines:
        if not line:
            continue

        found_header = False
        for sec_name, pattern in JD_SECTION_PATTERNS.items():
            if pattern.match(line) and len(line.split()) <= 5:
                current_section = sec_name
                found_header = True
                break

        if not found_header:
            sections[current_section].append(line)

    return sections


def extract_job_title(text: str) -> str:
    """Extract job title using patterns or top-line heuristics."""
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    if not lines:
        return ""

    # Look for explicit Title fields
    title_pattern = re.compile(r"^(?:job\s+)?title\s*:\s*(.+)$", re.IGNORECASE)
    role_pattern = re.compile(r"^(?:role|position)\s*:\s*(.+)$", re.IGNORECASE)
    for line in lines[:10]:
        t_match = title_pattern.match(line)
        if t_match:
            return t_match.group(1).strip()
        r_match = role_pattern.match(line)
        if r_match:
            return r_match.group(1).strip()

    # Fallback to the first line if it looks like a title
    for line in lines[:3]:
        if len(line.split()) <= 8 and not any(kw in line.lower() for kw in ["http", "@", "about", "company", "description"]):
            # Filter punctuation
            title = re.sub(r"[^\w\s\-\&\/\+\#\.]", "", line).strip()
            if title:
                return title

    return "Job Position"


def extract_company_name(text: str) -> str:
    """Extract company name using SpaCy NER or section patterns."""
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    if not lines:
        return ""

    # Look for explicit Company fields
    company_pattern = re.compile(r"^(?:company|employer|organization)(?:\s+name)?\s*:\s*(.+)$", re.IGNORECASE)
    for line in lines[:15]:
        c_match = company_pattern.match(line)
        if c_match:
            return c_match.group(1).strip()

    # Try SpaCy NER on the first 5 lines
    if nlp:
        first_chunk = "\n".join(lines[:6])
        doc = nlp(first_chunk)
        for ent in doc.ents:
            if ent.label_ in ["ORG"]:
                ent_text = ent.text.strip()
                # Exclude common noise or titles
                if not any(kw in ent_text.lower() for kw in ["job", "role", "description", "requirements", "resume"]):
                    return ent_text

    # Try checking about company section or looking at first line
    sections = _get_jd_sections(text)
    about_lines = sections["about_company"]
    if about_lines:
        for line in about_lines[:3]:
            # e.g., "At Google, we believe..."
            match = re.search(r"\b(?:at|with|join)\s+([A-Z][a-zA-Z0-9\s]+?)(?:\s+we\b|\b,)", line)
            if match:
                return match.group(1).strip()

    return ""


def extract_required_skills(text: str) -> List[str]:
    """Extract matching required skills from text or requirements section."""
    sections = _get_jd_sections(text)
    req_text = "\n".join(sections["requirements"] + sections["unknown"])
    req_text_lower = req_text.lower()

    matched = []
    for skill in COMMON_SKILLS:
        pattern = r"\b" + re.escape(skill) + r"\b"
        if re.search(pattern, req_text_lower):
            matched.append(skill)
    return matched


def extract_preferred_skills(text: str) -> List[str]:
    """Extract preferred/desired skills from preferred section or overall text."""
    sections = _get_jd_sections(text)
    pref_text = "\n".join(sections["preferred"])
    pref_text_lower = pref_text.lower()

    matched = []
    # If preferred section is empty, search in general text for preferred-related phrases
    if not pref_text:
        lines = text.split("\n")
        pref_lines = []
        for line in lines:
            if any(term in line.lower() for term in ["preferred", "plus", "nice to have", "desired", "highly value"]):
                pref_lines.append(line)
        pref_text_lower = "\n".join(pref_lines).lower()

    for skill in COMMON_SKILLS:
        pattern = r"\b" + re.escape(skill) + r"\b"
        if re.search(pattern, pref_text_lower):
            matched.append(skill)
    return matched


def extract_experience_required(text: str) -> str:
    """Extract experience required using regex patterns."""
    # Pattern to match years of experience: e.g. "3+ years", "5-7 years", "minimum of 2 years"
    exp_pattern = re.compile(
        r"(\b\d+\+?\s*(?:to|-)?\s*\d*\+?\s*years?(?:\s*of\s*(?:relevant\s*)?experience)?)\b",
        re.IGNORECASE
    )

    # Search requirements and general text
    sections = _get_jd_sections(text)
    search_corpus = "\n".join(sections["requirements"] + sections["unknown"])
    match = exp_pattern.search(search_corpus)
    if match:
        return match.group(1).strip()

    # Search entire text as fallback
    match = exp_pattern.search(text)
    if match:
        return match.group(1).strip()

    return "Not specified"


def _clean_bullet_points(lines: List[str]) -> List[str]:
    """Filter and clean lines to isolate actual bullet points / list items."""
    cleaned = []
    for line in lines:
        line_stripped = line.strip()
        if not line_stripped:
            continue
        # Check if line starts with bullet characters or numbers
        # e.g., -, *, •, 1., a)
        match = re.match(r"^[\-\*\•\d\.\w\)]+\s*(.+)$", line_stripped)
        if match:
            item = match.group(1).strip()
        else:
            item = line_stripped

        if len(item) > 10 and not any(header in item.lower() for header in JD_SECTION_PATTERNS.keys()):
            cleaned.append(item)
    return cleaned


def extract_responsibilities(text: str) -> List[str]:
    """Extract responsibilities using section heuristic and bullet cleaning."""
    sections = _get_jd_sections(text)
    resp_lines = sections["responsibilities"]
    if not resp_lines:
        # Fallback search for lines containing common responsibility verbs
        resp_lines = []
        for line in text.split("\n"):
            if any(term in line.lower() for term in ["responsible for", "own the", "manage", "collaborate with"]):
                resp_lines.append(line)
    return _clean_bullet_points(resp_lines)


def extract_qualifications(text: str) -> List[str]:
    """Extract qualifications/educational requirements."""
    sections = _get_jd_sections(text)
    req_lines = sections["requirements"]
    qual_lines = []
    # Focus on degree words, certifications or standard qualification terms
    degree_keywords = ["degree", "bachelor", "master", "phd", "b.s", "m.s", "computer science", "equivalent"]
    for line in req_lines:
        if any(keyword in line.lower() for keyword in degree_keywords):
            qual_lines.append(line)

    if not qual_lines:
        # Fallback: return general requirement bullet points
        return _clean_bullet_points(req_lines)[:10]

    return _clean_bullet_points(qual_lines)


def extract_technologies(text: str) -> List[str]:
    """Extract technologies matching predefined lists."""
    matched = []
    text_lower = text.lower()
    for tech in COMMON_TECHNOLOGIES:
        pattern = r"\b" + re.escape(tech) + r"\b"
        if re.search(pattern, text_lower):
            matched.append(tech)
    return matched


def parse_jd_text(text: str) -> Dict[str, Any]:
    """Orchestrates parsing of raw text into a structured job profile."""
    return {
        "job_title": extract_job_title(text),
        "company_name": extract_company_name(text),
        "required_skills": extract_required_skills(text),
        "preferred_skills": extract_preferred_skills(text),
        "experience_required": extract_experience_required(text),
        "responsibilities": extract_responsibilities(text),
        "qualifications": extract_qualifications(text),
        "technologies": extract_technologies(text)
    }
