# Product Requirements Document (PRD)

## 1. Problem Statement
Job seekers, particularly new graduates and professionals pivoting to new roles, struggle to prepare effectively for company-specific interviews. Traditional interview prep resources are static, generic, and do not provide realistic simulation or personalized feedback. 

Candidates need a way to:
- Practice interviews that align precisely with their resume and a target Job Description (JD).
- Simulate the unique culture, style, and question trends of specific target companies.
- Receive immediate, constructive, and granular evaluation on their performance to bridge skill gaps.

---

## 2. Users
The primary user personas for InterviewPilot-AI include:
- **Active Job Seekers**: Candidates actively applying to specific roles who want to run highly realistic mock simulations before the actual interview.
- **Career Switchers**: Professionals transitioning into new domains (e.g., QA to Software Developer, Product Management) who need to practice framing their past experience for their new role.
- **Students & Fresh Graduates**: Entry-level applicants looking to build confidence and understand the typical interview flows for target companies.

---

## 3. Features
*For a detailed breakdown of features, see [FEATURES.md](file:///c:/Users/ashis/OneDrive/Desktop/InterviewPilot-AI/docs/FEATURES.md).*

- **User Authentication**: Secure onboarding and session tracking.
- **Resume & Job Description (JD) Parsing**: High-accuracy data extraction for tailored alignment.
- **Company-Specific RAG System**: Custom knowledge base indexing company-specific interview structures, tech stacks, and core values.
- **Dynamic Mock Interview Simulator**: Adaptive question generation based on user performance and context.
- **Detailed Evaluation Engine**: Automated scoring with breakdown of accuracy, communication, and key Improvement points.
- **Personalized Analytics Dashboard**: Progression tracking, skill-gap analysis, and recommendation system.

---

## 4. Goals
### Short-term Goals
- Launch a functional MVP supporting core text-based mock interviews.
- Integrate RAG to successfully inject resume, JD, and company profile context into mock sessions.
- Provide a clear, actionable grading rubric in the post-interview report.

### Long-term Goals
- Expand the simulator to support audio/video input (speech-to-text, facial expression analysis, tone analysis).
- Build a community question bank where users can anonymously share recent real-world interview questions.
- Offer direct integration with job boards to match well-performing candidates directly with recruiting companies.

---

## 5. Future Scope
- **AI Voice Agent**: Seamless real-time audio conversation mimicking a live video call or phone interview.
- **IDE Integration**: Built-in coding environment for technical/coding rounds within the mock simulator.
- **Offline Mode & Mobile App**: Mobile platforms for on-the-go interview prep.
- **Enterprise / B2B Portal**: Enable universities and recruitment agencies to license the platform to track student/candidate readiness.
