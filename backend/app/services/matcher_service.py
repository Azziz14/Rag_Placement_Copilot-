"""Service module for matching parsed resumes with job descriptions.
"""

import re
from datetime import datetime
from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session

from app.models.resume import Resume
from app.models.job_description import JobDescription
from app.models.resume_match import ResumeMatch
from app.models.match_score_version import MatchScoreVersion
from app.services.jd_parser import parse_jd_text
from app.services.resume_parser import extract_skills, extract_technologies, extract_experience


class MatcherService:
    """Service to handle the Resume-JD matching logic, scoring, and persistence."""

    def _normalize_string(self, text: str) -> str:
        """Helper to normalize a string for better matching."""
        if not text:
            return ""
        # Remove special characters, multiple spaces, and convert to lowercase
        text = text.lower().strip()
        text = re.sub(r"[^\w\s\-\+\#]", " ", text)
        return " ".join(text.split())

    def match_skills(
        self, resume_skills: List[str], required_skills: List[str], preferred_skills: List[str]
    ) -> Tuple[List[str], List[str], List[str], List[str], float, float]:
        """Matches resume skills against required and preferred skills.
        
        Returns:
            matched_required: List of matched required skills
            missing_required: List of missing required skills
            matched_preferred: List of matched preferred skills
            missing_preferred: List of missing preferred skills
            required_score: Score for required skills (0-100)
            preferred_score: Score for preferred skills (0-100)
        """
        # Safe defaults
        resume_skills = resume_skills or []
        required_skills = required_skills or []
        preferred_skills = preferred_skills or []

        normalized_resume = [self._normalize_string(s) for s in resume_skills]

        # Function to check if a skill matches the resume skills (exact or substring)
        def is_match(skill: str) -> bool:
            norm_skill = self._normalize_string(skill)
            if not norm_skill:
                return False
            for rs in normalized_resume:
                # Direct match, or one is a substring of another
                if norm_skill == rs or norm_skill in rs or rs in norm_skill:
                    return True
            return False

        # Match Required Skills
        matched_required = []
        missing_required = []
        for req in required_skills:
            if is_match(req):
                matched_required.append(req)
            else:
                missing_required.append(req)

        # Match Preferred Skills
        matched_preferred = []
        missing_preferred = []
        for pref in preferred_skills:
            if is_match(pref):
                matched_preferred.append(pref)
            else:
                missing_preferred.append(pref)

        # Calculate scores
        required_score = 100.0
        if required_skills:
            required_score = (len(matched_required) / len(required_skills)) * 100.0

        preferred_score = 100.0
        if preferred_skills:
            preferred_score = (len(matched_preferred) / len(preferred_skills)) * 100.0

        return (
            matched_required,
            missing_required,
            matched_preferred,
            missing_preferred,
            required_score,
            preferred_score,
        )

    def match_technologies(
        self, resume_tech: List[str], jd_tech: List[str]
    ) -> Tuple[List[str], List[str], float]:
        """Matches resume technologies against job description technologies.
        
        Returns:
            matched_tech: List of matched technologies
            missing_tech: List of missing technologies
            tech_score: Score for technologies (0-100)
        """
        resume_tech = resume_tech or []
        jd_tech = jd_tech or []

        normalized_resume = [self._normalize_string(t) for t in resume_tech]

        def is_match(tech: str) -> bool:
            norm_tech = self._normalize_string(tech)
            if not norm_tech:
                return False
            for rt in normalized_resume:
                if norm_tech == rt or norm_tech in rt or rt in norm_tech:
                    return True
            return False

        matched_tech = []
        missing_tech = []
        for tech in jd_tech:
            if is_match(tech):
                matched_tech.append(tech)
            else:
                missing_tech.append(tech)

        tech_score = 100.0
        if jd_tech:
            tech_score = (len(matched_tech) / len(jd_tech)) * 100.0

        return matched_tech, missing_tech, tech_score

    def extract_years_from_text(self, text: str) -> float:
        """Heuristic to extract years of experience from a text snippet."""
        if not text:
            return 0.0
        
        # Look for patterns like "5+ years", "3 years", "2.5 yrs", "10 years"
        patterns = [
            r"(\d+(?:\.\d+)?)\s*(?:year|yr)s?",
            r"(\d+)\s*(?:[-–—]\s*(Present|\d+))?\s*(?:year|yr)s?"
        ]
        
        years_found = []
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    val = match[0]
                else:
                    val = match
                try:
                    years_found.append(float(val))
                except ValueError:
                    pass

        # Look for date ranges in experience, e.g., "2018 - 2021" or "2020 to Present"
        date_pattern = r"\b(19\d{2}|20\d{2})\s*(?:[-–—]|to)\s*(Present|19\d{2}|20\d{2})\b"
        date_matches = re.findall(date_pattern, text, re.IGNORECASE)
        for start, end in date_matches:
            try:
                start_year = int(start)
                if end.lower() == "present":
                    end_year = datetime.utcnow().year
                else:
                    end_year = int(end)
                duration = max(0, end_year - start_year)
                years_found.append(float(duration))
            except ValueError:
                pass

        # Return max or sensible sum
        # In a resume, experiences are listed sequentially. If we find date ranges, we can sum them up,
        # but to avoid double counting overlaps or templates, let's take a sensible approach.
        # If there are date ranges, sum them up. Otherwise, return the maximum number found.
        if date_matches:
            # Simple sum of non-overlapping is ideal, but let's sum durations of ranges as a heuristic
            range_sum = sum(max(0, int(end if end.lower() != "present" else datetime.utcnow().year) - int(start)) for start, end in date_matches)
            return float(range_sum)

        return max(years_found) if years_found else 0.0

    def compare_experience(
        self, resume_experience_list: List[Dict[str, Any]], jd_experience_required_str: str, resume_full_text: str = ""
    ) -> Tuple[float, float, float, str]:
        """Compares resume experience against job description experience requirements.
        
        Returns:
            required_years: Years of experience required by JD
            candidate_years: Years of experience candidate has
            score: Experience match score (0-100)
            message: Formatted comparison message
        """
        # 1. Parse JD required years
        jd_years = 0.0
        if jd_experience_required_str:
            # Look for number near "year" or "yr"
            match = re.search(r"(\d+(?:\.\d+)?)\s*(?:year|yr)", jd_experience_required_str, re.IGNORECASE)
            if match:
                jd_years = float(match.group(1))

        # 2. Parse candidate years from experience details or full text
        candidate_years = 0.0
        # Combine all raw_info from resume_experience_list
        exp_texts = []
        if resume_experience_list:
            for exp in resume_experience_list:
                if isinstance(exp, dict) and "raw_info" in exp:
                    exp_texts.append(exp["raw_info"])
                elif isinstance(exp, str):
                    exp_texts.append(exp)
        
        combined_exp_text = "\n".join(exp_texts)
        if not combined_exp_text and resume_full_text:
            combined_exp_text = resume_full_text

        candidate_years = self.extract_years_from_text(combined_exp_text)

        # 3. Calculate score
        if jd_years == 0.0:
            score = 100.0
            message = "No specific experience requirement specified."
        else:
            if candidate_years >= jd_years:
                score = 100.0
                message = f"Exceeds/meets required experience: {candidate_years:.1f} years of experience vs {jd_years:.1f} years required."
            else:
                score = (candidate_years / jd_years) * 100.0
                message = f"Experience gap: {candidate_years:.1f} years of experience vs {jd_years:.1f} years required."

        return jd_years, candidate_years, score, message

    def calculate_match_score(
        self, req_skills_score: float, pref_skills_score: float, tech_score: float, exp_score: float
    ) -> float:
        """Calculates the weighted total match score.
        
        Weights:
            - Required Skills: 40%
            - Preferred Skills: 20%
            - Technologies: 20%
            - Experience: 20%
        """
        total_score = (
            (req_skills_score * 0.40) +
            (pref_skills_score * 0.20) +
            (tech_score * 0.20) +
            (exp_score * 0.20)
        )
        return round(total_score, 1)

    def identify_gaps(
        self,
        matched_skills: List[str],
        missing_skills: List[str],
        matched_tech: List[str],
        missing_tech: List[str]
    ) -> Dict[str, List[str]]:
        """Identifies gaps in skills and technologies between candidate and job description."""
        return {
            "missing_skills": missing_skills,
            "missing_technologies": missing_tech
        }

    def generate_improvement_areas(
        self,
        gaps: Dict[str, List[str]],
        exp_score: float,
        exp_message: str
    ) -> List[str]:
        """Generates list of recommended improvement areas based on gaps and experience."""
        improvement_areas = []
        missing_skills = gaps.get("missing_skills") or []
        missing_tech = gaps.get("missing_technologies") or []

        if missing_skills:
            improvement_areas.append(f"Consider acquiring required/preferred skills: {', '.join(missing_skills[:5])}")
        if missing_tech:
            improvement_areas.append(f"Add projects or certifications for missing technologies: {', '.join(missing_tech[:5])}")
        if exp_score < 100.0:
            improvement_areas.append(f"Experience Gap: {exp_message}")

        if not improvement_areas:
            improvement_areas.append("Great alignment! No major gaps detected compared to this Job Description.")

        return improvement_areas

    def generate_feedback_areas(
        self,
        matched_req: List[str],
        missing_req: List[str],
        matched_pref: List[str],
        missing_pref: List[str],
        matched_tech: List[str],
        missing_tech: List[str],
        exp_message: str,
        exp_score: float
    ) -> Tuple[List[str], List[str]]:
        """Generates strong areas and improvement areas lists."""
        strong_areas = []

        # Strong areas
        if matched_req:
            strong_areas.append(f"Possesses key required skills: {', '.join(matched_req[:5])}")
        if matched_tech:
            strong_areas.append(f"Demonstrates alignment with technologies: {', '.join(matched_tech[:5])}")
        if matched_pref:
            strong_areas.append(f"Has preferred skills: {', '.join(matched_pref[:5])}")
        if exp_score >= 100.0:
            strong_areas.append(f"Experience: {exp_message}")

        gaps = self.identify_gaps(
            matched_skills=matched_req + matched_pref,
            missing_skills=missing_req + missing_pref,
            matched_tech=matched_tech,
            missing_tech=missing_tech
        )
        improvement_areas = self.generate_improvement_areas(gaps, exp_score, exp_message)

        # Fallback if empty
        if not strong_areas:
            strong_areas.append("Good start, matching basic keyword profiles.")

        return strong_areas, improvement_areas

    def perform_match_analysis(
        self, db: Session, user_id: str, resume_id: str, job_description_id: str, tailored_content: Dict[str, Any] = None
    ) -> ResumeMatch:
        """Retrieves models, runs calculations, persists match to DB, and returns model."""
        # 1. Fetch resume and JD
        resume = db.query(Resume).filter(Resume.id == resume_id, Resume.user_id == user_id).first()
        if not resume:
            raise ValueError(f"Resume with ID {resume_id} not found or unauthorized.")

        jd = db.query(JobDescription).filter(JobDescription.id == job_description_id, JobDescription.user_id == user_id).first()
        if not jd:
            raise ValueError(f"Job Description with ID {job_description_id} not found or unauthorized.")
        
        # Parse JD: check skills in full text + metadata
        full_jd_text = f"{jd.job_title or ''} {jd.raw_text}"
        parsed_jd = parse_jd_text(full_jd_text)
        
        # Use stored resume attributes
        resume_skills = resume.skills or []
        resume_technologies = resume.technologies or []
        resume_experience = resume.experience or []
        resume_text = resume.extracted_text or ""

        # 2. Extract and match skills
        (
            matched_req,
            missing_req,
            matched_pref,
            missing_pref,
            req_skills_score,
            pref_skills_score,
        ) = self.match_skills(resume_skills, parsed_jd.get("required_skills"), parsed_jd.get("preferred_skills"))

        # 3. Match technologies
        matched_tech, missing_tech, tech_score = self.match_technologies(
            resume_technologies, parsed_jd.get("technologies")
        )

        # 4. Compare experience
        _, _, exp_score, exp_message = self.compare_experience(
            resume_experience, parsed_jd.get("experience_required"), resume_text
        )

        # 5. Calculate weighted score
        final_score = self.calculate_match_score(
            req_skills_score, pref_skills_score, tech_score, exp_score
        )

        # 6. Generate strong & improvement areas
        strong_areas, improvement_areas = self.generate_feedback_areas(
            matched_req,
            missing_req,
            matched_pref,
            missing_pref,
            matched_tech,
            missing_tech,
            exp_message,
            exp_score
        )

        # Save to database
        db_match = ResumeMatch(
            user_id=user_id,
            resume_id=resume_id,
            job_description_id=job_description_id,
            match_score=final_score,
            matched_skills=matched_req + matched_pref,
            missing_skills=missing_req + missing_pref,
            matched_technologies=matched_tech,
            missing_technologies=missing_tech,
            strong_areas=strong_areas,
            improvement_areas=improvement_areas
        )
        db.add(db_match)
        
        # Save version history
        db_version = MatchScoreVersion(
            resume_id=resume_id,
            jd_id=job_description_id,
            score=final_score
        )
        db.add(db_version)
        
        db.commit()
        db.refresh(db_match)

        return db_match


# Global service instance
matcher_service = MatcherService()
