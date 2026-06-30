"""Service module for generating personalized interview questions using Gemini LLM or heuristics fallback.
"""

import json
import logging
import random
import re
import time
from typing import List, Dict, Any, Optional

from app.core.config import settings
from app.models.resume import Resume
from app.models.job_description import JobDescription
from app.models.resume_match import ResumeMatch
from app.services.llm_service import llm_service

logger = logging.getLogger(__name__)


class QuestionService:
    """Service to handle the logic of generating personalized interview questions."""



    def generate_questions(
        self,
        resume: Resume,
        jd: JobDescription,
        match: ResumeMatch,
        rag_context: Dict[str, Any],
        previous_questions: Optional[List[str]] = None
    ) -> Dict[str, List[str]]:
        """Coordinates the retrieval-augmented question generation using Gemini or a rule-based fallback."""
        previous_questions = previous_questions or []
        
        # Extract RAG contexts
        role_ctx = rag_context.get("role_context", [])
        company_ctx = rag_context.get("company_context", [])
        missing_skill_ctx = rag_context.get("missing_skill_context", [])
        behavioral_ctx = rag_context.get("behavioral_context", [])
        dsa_ctx = rag_context.get("dsa_context", [])

        # Try to generate using LLM if configured
        if settings.GEMINI_API_KEY or settings.GROQ_API_KEY:
            try:
                generated = self._generate_with_llm(
                    resume,
                    jd,
                    match,
                    role_ctx,
                    company_ctx,
                    missing_skill_ctx,
                    behavioral_ctx,
                    dsa_ctx,
                    previous_questions
                )
                important_topics = self._build_important_topics(jd, match)
                cleaned = self._remove_previous_questions(generated, previous_questions, important_topics)
                return self._ensure_minimum_questions(cleaned, jd, important_topics)
            except Exception as e:
                logger.error(f"Gemini LLM question generation failed: {str(e)}. Falling back to rule-based generation.")
        else:
            logger.warning("Gemini question generation is not configured. Falling back to rule-based generation.")

        # Fallback to local rule-based/heuristic generation
        generated = {
            "technical_questions": self.generate_technical_questions(resume, jd, match, role_ctx, missing_skill_ctx),
            "project_questions": self.generate_project_questions(resume, jd),
            "behavioral_questions": self.generate_behavioral_questions(jd, match, behavioral_ctx, company_ctx),
            "dsa_questions": self.generate_dsa_questions(jd, dsa_ctx)
        }
        important_topics = self._build_important_topics(jd, match)
        cleaned = self._remove_previous_questions(generated, previous_questions, important_topics)
        return self._ensure_minimum_questions(cleaned, jd, important_topics)

    def _build_important_topics(self, jd: JobDescription, match: ResumeMatch) -> List[str]:
        """Ranks topics that should be covered even if similar questions appeared before."""
        topics = []
        for values in [
            jd.required_skills or [],
            jd.technologies or [],
            match.missing_skills or [],
            match.missing_technologies or [],
            match.matched_skills or [],
            match.matched_technologies or [],
        ]:
            for value in values:
                if isinstance(value, str) and value.strip():
                    normalized = value.strip()
                    if normalized.lower() not in [item.lower() for item in topics]:
                        topics.append(normalized)
        return topics[:12]

    def _mentions_important_topic(self, question: str, important_topics: List[str]) -> bool:
        question_lower = question.lower()
        return any(topic.lower() in question_lower for topic in important_topics if len(topic.strip()) >= 2)

    def _is_exact_repeat(self, question: str, previous_questions: List[str]) -> bool:
        normalized = " ".join(question.lower().split())
        return any(normalized == " ".join(prev.lower().split()) for prev in previous_questions)

    def _is_similar_to_previous(self, question: str, previous_questions: List[str]) -> bool:
        normalized = " ".join(question.lower().split())
        for prev in previous_questions:
            prev_norm = " ".join(prev.lower().split())
            if normalized == prev_norm:
                return True
            question_terms = set(normalized.split())
            prev_terms = set(prev_norm.split())
            if len(question_terms) > 8 and len(prev_terms) > 8:
                overlap = len(question_terms.intersection(prev_terms)) / max(len(question_terms), 1)
                if overlap >= 0.82:
                    return True
        return False

    def _remove_previous_questions(
        self,
        categorized_questions: Dict[str, List[str]],
        previous_questions: List[str],
        important_topics: Optional[List[str]] = None
    ) -> Dict[str, List[str]]:
        if not previous_questions:
            return categorized_questions

        important_topics = important_topics or []
        cleaned = {}
        for category, questions in categorized_questions.items():
            cleaned[category] = []
            for question in questions:
                if self._is_exact_repeat(question, previous_questions):
                    continue
                is_repeat = self._is_similar_to_previous(question, previous_questions)
                covers_required_topic = self._mentions_important_topic(question, important_topics)
                if not is_repeat or covers_required_topic:
                    cleaned[category].append(question)
        return cleaned

    def _ensure_minimum_questions(
        self,
        categorized_questions: Dict[str, List[str]],
        jd: JobDescription,
        important_topics: Optional[List[str]] = None,
        minimum: int = 2
    ) -> Dict[str, List[str]]:
        job_title = jd.job_title or "Software Engineer"
        topics = important_topics or []
        primary_topic = topics[0] if topics else "the most important JD requirement"
        secondary_topic = topics[1] if len(topics) > 1 else "the production system"
        scenario_id = random.randint(1000, 9999)
        fallback_bank = {
            "technical_questions": [
                f"For this {job_title} JD, design a production feature where '{primary_topic}' is central. What APIs, data model, failure modes, and trade-offs would you discuss?",
                f"Scenario {scenario_id}: a service using '{secondary_topic}' is slow under peak traffic. How would you debug it and what would you change first?",
                f"Compare two implementation approaches for '{primary_topic}' in this role. Which would you choose and what risk would you watch?"
            ],
            "project_questions": [
                f"Pick a past project and map it directly to '{primary_topic}'. What evidence proves you can handle that JD requirement?",
                f"Tell me about a project where decisions around '{secondary_topic}' mattered. How did you validate the design?",
                f"If your strongest project had to support this {job_title} role, what would you add or change to better match the JD?"
            ],
            "behavioral_questions": [
                f"Tell me about a time you had to learn or deliver something like '{primary_topic}' quickly. How did you manage the risk?",
                "Describe a time you pushed back on scope because quality or reliability would suffer. What happened?",
                f"This JD needs ownership around '{secondary_topic}'. Tell me about a time you drove a technical decision end to end."
            ],
            "dsa_questions": [
                f"Design an algorithmic solution for ranking or filtering records related to '{primary_topic}'. Explain complexity and edge cases.",
                f"Given high-volume events from '{secondary_topic}', find the top K frequent failures in near real time. What data structure would you use?",
                "Given a stream of user actions, detect repeated patterns efficiently and explain the memory trade-off."
            ],
        }

        for category, fallback_questions in fallback_bank.items():
            existing = categorized_questions.setdefault(category, [])
            available = [question for question in fallback_questions if question not in existing]
            random.shuffle(available)
            while len(existing) < minimum and available:
                existing.append(available.pop())
        return categorized_questions

    def generate_technical_questions(
        self,
        resume: Resume,
        jd: JobDescription,
        match: ResumeMatch,
        role_ctx: List[Dict[str, Any]],
        missing_skill_ctx: List[Dict[str, Any]]
    ) -> List[str]:
        """Generates technical questions based on skills, role context, and missing skills."""
        questions = []
        matched_skills = list(match.matched_skills or [])
        missing_skills = list(match.missing_skills or [])
        required_skills = list(jd.required_skills or [])
        required_technologies = list(jd.technologies or [])
        job_title = jd.job_title or "Software Engineer"
        random.shuffle(matched_skills)
        random.shuffle(missing_skills)

        priority_skills = []
        for skill in required_skills + required_technologies + missing_skills + matched_skills:
            if skill and skill not in priority_skills:
                priority_skills.append(skill)

        # 1. Focus questions on the most important JD requirements first.
        for skill in priority_skills[:3]:
            is_missing = skill in missing_skills or skill in (match.missing_technologies or [])
            gap_phrase = "This appears to be a gap in your current profile" if is_missing else "Your resume appears to show related experience"
            questions.append(random.choice([
                f"The {job_title} JD emphasizes '{skill}'. {gap_phrase}; can you explain a practical project, architecture, or implementation where '{skill}' is central, and what trade-offs you would consider?",
                f"Imagine you join this {job_title} team and must deliver a feature using '{skill}' in week one. What assumptions would you clarify, what design would you propose, and how would you validate it?",
                f"Give me a concrete debugging scenario involving '{skill}'. What symptoms would you look for, what tools or logs would you inspect, and how would you prove the fix worked?",
                f"What is a common failure mode or misconception around '{skill}', and how would you avoid it in a production implementation for this JD?"
            ]))
        
        # 2. Ask deeper follow-ups on matched skills.
        for skill in matched_skills[:1]:
            questions.append(
                f"You have experience with '{skill}' listed on your resume. How do you approach caching, performance optimization, "
                f"or concurrency challenges when building production services using '{skill}'?"
            )

        # 3. Add role context standard questions
        if role_ctx:
            pattern_desc = random.choice(role_ctx)['content'][:120].strip()
            questions.append(
                random.choice([
                    f"Considering target {job_title} role standards and design patterns such as: '{pattern_desc}...', how would you architect a fault-tolerant system to align with these guidelines?",
                    f"Based on this {job_title} context: '{pattern_desc}...', what architecture would you choose for a high-traffic feature and what trade-offs would you call out?",
                    f"For a {job_title} role, how would you turn the guidance '{pattern_desc}...' into concrete API, data, and reliability decisions?"
                ])
            )
        else:
            questions.append(random.choice([
                f"In your previous roles as related to {job_title}, how do you evaluate architectural trade-offs between monolithic services and distributed microservices architectures?",
                f"For a {job_title} role, walk me through how you would decide between synchronous APIs, async queues, and scheduled jobs for a new workflow.",
                f"Describe how you would debug and improve latency in a production service for a {job_title} team."
            ]))

        random.shuffle(questions)
        return questions

    def generate_project_questions(
        self,
        resume: Resume,
        jd: JobDescription
    ) -> List[str]:
        """Generates questions probing into candidate's resume projects and technologies used."""
        questions = []
        projects = resume.projects or []

        if projects:
            selected_projects = projects[:]
            random.shuffle(selected_projects)
            for proj in selected_projects[:2]:
                proj_name = proj.get("name", "your recent project")
                techs = proj.get("technologies", [])
                tech_str = f" using {', '.join(techs)}" if techs else ""
                questions.extend(random.sample([
                    f"Explain the architecture and data flows of your project '{proj_name}'{tech_str}. What were the key bottlenecks and how did you resolve them?",
                    f"In '{proj_name}', if you had to scale the request throughput by 10x, what structural changes would you implement in your database or caching layer to handle the load?",
                    f"What was the most important technical decision in '{proj_name}', and what alternative did you reject?",
                    f"If you had to make '{proj_name}' more reliable for production users, what monitoring, testing, or rollback strategy would you add?"
                ], 2))
        else:
            # Fallback if no projects are listed
            questions.extend(random.sample([
                "Can you walk me through the system design of a challenging software project you built? Highlight the core technology choices and DB schema design.",
                "Describe a scenario where a production deployment or system migration failed in your past project. How did you perform root cause analysis and mitigate the issue?",
                "Tell me about a feature you built where the first implementation was not good enough. What did you change and why?",
                "Pick a past project and explain how you would redesign it today with what you know now."
            ], 2))

        random.shuffle(questions)
        return questions

    def generate_behavioral_questions(
        self,
        jd: JobDescription,
        match: ResumeMatch,
        behavioral_ctx: List[Dict[str, Any]],
        company_ctx: List[Dict[str, Any]]
    ) -> List[str]:
        """Generates behavioral questions tailored to company context and candidate strong/improvement areas."""
        questions = []
        strong_areas = match.strong_areas or []
        company_name = jd.company_name or "the company"

        # 1. Company values & interview context questions
        if company_ctx:
            value_info = random.choice(company_ctx)['content'][:120].strip()
            questions.append(
                f"At {company_name}, engineering teams emphasize values like '{value_info}...'. "
                f"Describe a situation in your career where you made a key decision that aligned with these principles."
            )
        else:
            questions.append(random.choice([
                f"Why are you looking to join the engineering team at {company_name}, and how do you foster high-performance engineering standards in a fast-paced environment?",
                f"What kind of engineering culture helps you do your best work, and how would you contribute to that at {company_name}?",
                f"Tell me about a time you raised the quality bar for a team without slowing delivery."
            ]))

        # 2. Behavioral STAR questions mapped to candidate's strong/improvement areas
        if behavioral_ctx:
            behavioral_desc = random.choice(behavioral_ctx)['content'][:120].strip()
            questions.append(
                f"Describe a time when you had to resolve conflict or manage tight deadlines under guidelines like: "
                f"'{behavioral_desc}...'. Explain the situation, task, action, and results (STAR method)."
            )
        else:
            questions.append(random.choice([
                "Tell me about a time you had to deliver a feature under high ambiguity with incomplete product requirements. How did you align the technical goals with business value?",
                "Describe a time you disagreed with a technical direction. How did you handle the discussion and what happened?",
                "Tell me about a mistake you made in a project and how you changed your process afterward."
            ]))

        # 3. Mapped to candidate strengths
        if strong_areas:
            questions.append(
                f"Since your profile demonstrates strengths in: '{strong_areas[0]}', tell me about a time "
                f"you leveraged this capability to onboard team members or improve the team's velocity."
            )

        random.shuffle(questions)
        return questions

    def generate_dsa_questions(
        self,
        jd: JobDescription,
        dsa_ctx: List[Dict[str, Any]]
    ) -> List[str]:
        """Generates DSA and algorithmic questions tailored to the role requirements."""
        questions = []
        job_title = jd.job_title or "Software Engineer"

        # 1. Extract context-specific questions
        if dsa_ctx:
            selected_context = dsa_ctx[:]
            random.shuffle(selected_context)
            for item in selected_context[:2]:
                questions.append(
                    f"Coding Challenge: {item['content'].strip()}"
                )
        else:
            # General fallback DSA questions based on common software engineer profiles
            questions.extend(random.sample([
                "Design and implement an efficient rate limiter (e.g. Token Bucket or Leaky Bucket algorithm). Explain the data structure selection and write clean mock code.",
                "Given an array of integers representing stock prices, find the maximum profit you can achieve by buying and selling once. Optimize the solution to run in O(N) time complexity and O(1) space.",
                "Given a stream of events, design a data structure to return the top K most frequent events efficiently.",
                "Given a grid with blocked cells, find the shortest path between two points and explain the time complexity.",
                "Design an LRU cache and explain how your implementation guarantees O(1) get and put operations."
            ], 2))

        # 2. Ensure role-relevance is explicitly appended
        questions.append(
            f"As a candidate for a {job_title} role, explain how you choose between a hash map, a trie, "
            f"and a balanced binary search tree when implementing fast prefixes lookups or lookup auto-completions."
        )

        random.shuffle(questions)
        return questions

    def _generate_with_llm(
        self,
        resume: Resume,
        jd: JobDescription,
        match: ResumeMatch,
        role_ctx: List[Dict[str, Any]],
        company_ctx: List[Dict[str, Any]],
        missing_skill_ctx: List[Dict[str, Any]],
        behavioral_ctx: List[Dict[str, Any]],
        dsa_ctx: List[Dict[str, Any]]
        ,
        previous_questions: Optional[List[str]] = None
    ) -> Dict[str, List[str]]:
        """Helper to invoke Gemini to generate structured categorized questions using JSON constraints."""
        
        # Prepare structured input summaries for LLM
        candidate_summary = {
            "skills": resume.skills or [],
            "experience_summary": [exp.get("raw_info", "")[:150] for exp in (resume.experience or [])[:2]],
            "projects": [{"name": p.get("name"), "technologies": p.get("technologies", [])} for p in (resume.projects or [])[:3]]
        }

        role_summary = {
            "job_title": jd.job_title,
            "company_name": jd.company_name,
            "required_skills": jd.required_skills or [],
            "preferred_skills": jd.preferred_skills or [],
            "technologies": jd.technologies or [],
            "responsibilities": jd.responsibilities or [],
            "qualifications": jd.qualifications or []
        }

        match_summary = {
            "matched_skills": match.matched_skills or [],
            "missing_skills": match.missing_skills or [],
            "matched_technologies": match.matched_technologies or [],
            "missing_technologies": match.missing_technologies or [],
            "strong_areas": match.strong_areas or [],
            "improvement_areas": match.improvement_areas or []
        }

        rag_summary = {
            "role_context": [c["content"] for c in role_ctx[:2]],
            "company_context": [c["content"] for c in company_ctx[:2]],
            "missing_skill_context": [c["content"] for c in missing_skill_ctx[:2]],
            "behavioral_context": [c["content"] for c in behavioral_ctx[:2]],
            "dsa_context": [c["content"] for c in dsa_ctx[:2]]
        }
        generation_seed = f"{int(time.time())}-{random.randint(1000, 9999)}"
        previous_questions = previous_questions or []
        important_topics = self._build_important_topics(jd, match)

        prompt = f"""
You are an expert technical interviewer. Generate personalized interview questions for a candidate applying to a role.

---
CANDIDATE INFO:
{json.dumps(candidate_summary, indent=2)}

ROLE INFO:
{json.dumps(role_summary, indent=2)}

MATCH ANALYSIS:
{json.dumps(match_summary, indent=2)}

RAG RETRIEVED GUIDELINES:
{json.dumps(rag_summary, indent=2)}

PREVIOUSLY ASKED QUESTIONS:
{json.dumps(previous_questions[-60:], indent=2)}

MANDATORY HIGH-IMPORTANCE TOPICS:
{json.dumps(important_topics, indent=2)}

GENERATION SEED:
{generation_seed}
---

Generate exactly 3 to 4 questions per category. Custom-tailor them using the provided candidate projects, skills, gaps, and company context:
1. "technical_questions": Prioritize mandatory high-importance topics from the JD, especially required skills, technologies, missing skills, and missing technologies. Ask the most job-critical technical questions first.
2. "project_questions": Target candidate's listed projects, technologies they used, and system engineering trade-offs.
3. "behavioral_questions": Align with company values, culture context, team dynamics, and STAR-style situational challenges.
4. "dsa_questions": Algorithmic or coding questions relevant to the role, required technologies, and likely interview level.

Coverage rules:
- Ask the most important and relevant questions based on the JD, required skills, technologies, responsibilities, and candidate skill gaps.
- Never repeat exact question wording from PREVIOUSLY ASKED QUESTIONS.
- It is acceptable to revisit a previous topic when it is mandatory for the JD or essential to evaluate the candidate, but ask a deeper follow-up, new scenario, debugging case, design case, or trade-off question.
- Avoid repeating low-priority generic questions.
- If a required JD skill appears in previous questions, ask a sharper follow-up or alternate scenario instead of skipping it.
- Every returned question should be useful for deciding whether the candidate fits this specific JD.
- Prefer interactive, senior interviewer style questions: ask the candidate to reason, clarify assumptions, debug, design, trade off, or improve an implementation.
- Avoid textbook definitions unless the JD explicitly requires fundamentals.

Return ONLY a valid JSON object matching the format below. Do not include markdown code block formatting or wrap in ```json.

Output Format:
{{
  "technical_questions": ["q1", "q2", "q3"],
  "project_questions": ["q1", "q2", "q3"],
  "behavioral_questions": ["q1", "q2", "q3"],
  "dsa_questions": ["q1", "q2", "q3"]
}}
"""

        # Identify configured providers
        configured_providers = []
        if settings.GEMINI_API_KEY: configured_providers.append("gemini")
        if settings.GROQ_API_KEY: configured_providers.append("groq")
        if settings.DEEPSEEK_API_KEY: configured_providers.append("deepseek")
        if settings.OPENROUTER_API_KEY: configured_providers.append("openrouter")
        if settings.MISTRAL_API_KEY: configured_providers.append("mistral")

        if not configured_providers:
            raise RuntimeError("No LLM providers are configured.")

        pools = {
            "technical_questions": [],
            "project_questions": [],
            "behavioral_questions": [],
            "dsa_questions": []
        }

        successful_count = 0
        for provider in configured_providers:
            if successful_count >= 3:
                break
            try:
                logger.info(f"Generating candidate questions with provider: {provider}")
                response_text = llm_service.generate_content(
                    prompt,
                    temperature=0.95,
                    max_tokens=4096,
                    response_json=True,
                    provider=provider
                )
                text = response_text.strip()
                if text.startswith("```"):
                    lines = text.splitlines()
                    if lines[0].startswith("```json") or lines[0].startswith("```"):
                        text = "\n".join(lines[1:-1])
                match_json = re.search(r"\{.*\}", text, re.DOTALL)
                if match_json:
                    text = match_json.group(0)
                
                data = json.loads(text)
                has_questions = False
                for key in pools.keys():
                    if key in data and isinstance(data[key], list) and len(data[key]) > 0:
                        pools[key].extend(data[key])
                        has_questions = True
                
                if has_questions:
                    successful_count += 1
            except Exception as exc:
                logger.warning(f"Failed to generate candidate questions with {provider}: {str(exc)}")

        # Deduplicate pools
        for key in pools.keys():
            pools[key] = list(set([q.strip() for q in pools[key] if isinstance(q, str) and q.strip()]))

        total_questions = sum(len(pools[k]) for k in pools.keys())
        if total_questions == 0:
            raise RuntimeError("No questions were generated from any LLM provider.")

        # Consolidation pass
        consolidation_prompt = f"""
You are a senior principal technical interviewer.
You are given a candidate profile, a target Job Description, and pools of candidate interview questions generated by different AI models.

Target Job Description:
{json.dumps(role_summary, indent=2)}

Candidate Profile:
{json.dumps(candidate_summary, indent=2)}

Match Analysis (Gaps):
{json.dumps(match_summary, indent=2)}

POOLS OF GENERATED QUESTIONS:
{json.dumps(pools, indent=2)}

Task:
Review all questions in the pools. For each category ("technical_questions", "project_questions", "behavioral_questions", "dsa_questions"), select or synthesize the best and most job-critical 3 to 4 questions.
- Prioritize questions that test mandatory job-critical skills or target the candidate's specific gaps.
- Avoid duplicate questions, textbook questions, or simple generic questions.
- Select questions that feel senior, interactive, and probe deep into design, trade-offs, and practical troubleshooting.

Return ONLY a valid JSON object matching the format below. Do not wrap in markdown or include ```json.

Output Format:
{{
  "technical_questions": ["q1", "q2", "q3"],
  "project_questions": ["q1", "q2", "q3"],
  "behavioral_questions": ["q1", "q2", "q3"],
  "dsa_questions": ["q1", "q2", "q3"]
}}
"""
        logger.info("Running final LLM consolidation pass to select the best questions")
        consolidated_response = llm_service.generate_content(
            consolidation_prompt,
            temperature=0.4,
            max_tokens=4096,
            response_json=True
        )
        consolidated_text = consolidated_response.strip()

        if consolidated_text.startswith("```"):
            lines = consolidated_text.splitlines()
            if lines[0].startswith("```json") or lines[0].startswith("```"):
                consolidated_text = "\n".join(lines[1:-1])

        match_json = re.search(r"\{.*\}", consolidated_text, re.DOTALL)
        if match_json:
            consolidated_text = match_json.group(0)

        final_data = json.loads(consolidated_text)
        for key in ["technical_questions", "project_questions", "behavioral_questions", "dsa_questions"]:
            if key not in final_data or not isinstance(final_data[key], list):
                final_data[key] = []
        return final_data


# Global service instance
question_service = QuestionService()
