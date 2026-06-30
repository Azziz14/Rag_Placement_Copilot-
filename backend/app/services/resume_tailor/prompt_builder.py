"""Module for building prompts to send to the Gemini LLM for resume tailoring.
"""

from typing import Dict, Any, List

def build_tailoring_prompt(
    original_resume: Dict[str, Any],
    jd_text: str,
    matcher_analysis: Dict[str, Any],
    preferences: Dict[str, Any]
) -> str:
    """Constructs the prompt for the Gemini LLM to rewrite and tailor the resume.
    """
    target_role = preferences.get("target_role", "")
    focus_areas = preferences.get("focus_areas") or []
    exclude_sections = preferences.get("exclude_sections") or []
    tone = preferences.get("tone", "professional")
    custom_instructions = preferences.get("custom_instructions", "")
    
    matched_skills = matcher_analysis.get("matched_skills") or []
    missing_skills = matcher_analysis.get("missing_skills") or []
    missing_tech = matcher_analysis.get("missing_technologies") or []
    
    prompt = f"""You are an expert resume tailoring assistant. Your goal is to optimize a candidate's resume for a specific Job Description (JD) and user preferences, ensuring maximum ATS compatibility and professional relevance while maintaining absolute honesty.

CRITICAL CONSTRAINTS:
1. Do NOT invent or hallucinate any fake skills, experience, projects, or certifications.
2. Do NOT add new companies, roles, or change the dates/years of employment.
3. If specific sections are in the exclude list, do not output them.
4. Improve ATS keyword relevance by aligning wording and phrasing to the JD using the matched/missing skills lists.
5. Respect user tailoring preferences (focus areas, tone, custom instructions).

INPUT DETAILS:

Target Role: {target_role}
Focus Areas: {", ".join(focus_areas)}
Tone: {tone}
Custom Instructions: {custom_instructions}
Excluded Sections: {", ".join(exclude_sections)}

Job Description:
\"\"\"
{jd_text}
\"\"\"

Matcher Analysis:
- Matched Skills/Tech: {", ".join(matched_skills)}
- Missing Skills: {", ".join(missing_skills)}
- Missing Technologies: {", ".join(missing_tech)}

Original Resume Content:
- Summary: {original_resume.get("summary") or "None"}
- Skills: {", ".join(original_resume.get("skills") or [])}
- Experience:
{_format_experience_or_projects(original_resume.get("experience"))}
- Projects:
{_format_experience_or_projects(original_resume.get("projects"))}
- Certifications: {", ".join(original_resume.get("certifications") or [])}
- Technologies: {", ".join(original_resume.get("technologies") or [])}

INSTRUCTIONS FOR GENERATION:
Rewrite the resume content to align with the JD. Output a JSON object with the following keys. Only include the sections that are not excluded.
- "summary": A tailored professional summary reflecting the target role and tone.
- "skills": The optimized list of skills (incorporating matched/missing skills only if the candidate has exposure or it can be inferred from experience/projects). Do not invent skills.
- "experience": List of experience entries with updated bullet points. Each bullet point should highlight impact, metrics, and JD-relevant keywords.
- "projects": List of project entries with updated descriptions/bullets focusing on relevant technologies.
- "certifications": The list of certifications.

Return ONLY a valid JSON object matching this structure:
{{
  "summary": "Tailored summary string",
  "skills": ["Skill1", "Skill2"],
  "experience": [
    {{
      "raw_info": "Updated experience block text with headers and bullets exactly as originally structured but with tailored text"
    }}
  ],
  "projects": [
    {{
      "raw_info": "Updated projects block text"
    }}
  ],
  "certifications": ["Cert1", "Cert2"]
}}
"""
    return prompt

def _format_experience_or_projects(items: Any) -> str:
    if not items:
        return "None"
    formatted = []
    for idx, item in enumerate(items):
        if isinstance(item, dict) and "raw_info" in item:
            formatted.append(f"Entry {idx + 1}:\n{item['raw_info']}")
        elif isinstance(item, str):
            formatted.append(f"Entry {idx + 1}:\n{item}")
    return "\n\n".join(formatted)
