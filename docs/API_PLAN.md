# API Integration Plan

This document details the backend API endpoints for InterviewPilot-AI, including request bodies, headers, and response formats.

---

## 1. POST `/upload-resume`
Uploads and parses a candidate's resume.

- **Content-Type**: `multipart/form-data`
- **Request Body**:
  - `resume`: File (PDF, DOCX)
- **Success Response**: `201 Created`
  ```json
  {
    "success": true,
    "message": "Resume uploaded and parsed successfully",
    "data": {
      "resume_id": "8f83038d-8a29-4a9f-b7e5-1a8c88bf92bb",
      "file_name": "John_Doe_CV.pdf",
      "structured_data": {
        "skills": ["JavaScript", "React", "Node.js", "PostgreSQL"],
        "experience_years": 4,
        "education": "B.S. in Computer Science"
      }
    }
  }
  ```

---

## 2. POST `/analyze-jd`
Parses job description text or uploads a JD file and returns structured analysis.

- **Content-Type**: `application/json`
- **Request Body**:
  ```json
  {
    "company_name": "Google",
    "job_title": "Software Engineer",
    "jd_text": "We are looking for a Software Engineer proficient in React and Node.js..."
  }
  ```
- **Success Response**: `200 OK`
  ```json
  {
    "success": true,
    "message": "Job description analyzed successfully",
    "data": {
      "job_id": "c138d9ee-204b-4a57-b08e-ee77e923e59b",
      "extracted_skills": ["React", "Node.js", "System Design"],
      "focus_areas": ["Frontend development", "Microservices architecture"]
    }
  }
  ```

---

## 3. POST `/generate-roadmap`
Generates a preparation roadmap using RAG to highlight gaps between resume and JD.

- **Content-Type**: `application/json`
- **Request Body**:
  ```json
  {
    "resume_id": "8f83038d-8a29-4a9f-b7e5-1a8c88bf92bb",
    "job_id": "c138d9ee-204b-4a57-b08e-ee77e923e59b"
  }
  ```
- **Success Response**: `200 OK`
  ```json
  {
    "success": true,
    "data": {
      "roadmap_id": "428bb841-f761-4171-89e4-c5a4b7ee92a1",
      "skills_gap": ["System Design"],
      "recommended_topics": [
        {
          "topic": "Microservices Design Patterns",
          "priority": "High",
          "resources": ["https://microservices.io"]
        }
      ]
    }
  }
  ```

---

## 4. POST `/start-interview`
Initiates a mock interview session.

- **Content-Type**: `application/json`
- **Request Body**:
  ```json
  {
    "resume_id": "8f83038d-8a29-4a9f-b7e5-1a8c88bf92bb",
    "job_id": "c138d9ee-204b-4a57-b08e-ee77e923e59b"
  }
  ```
- **Success Response**: `200 OK`
  ```json
  {
    "success": true,
    "data": {
      "interview_id": "e6abf776-6ee1-4545-9273-04bc7a0e1cb1",
      "first_question": "Hi John! Let's start with your experience in React. Can you describe a complex application you built and how you managed its state?"
    }
  }
  ```

---

## 5. POST `/submit-answer`
Submits a candidate's response to the current question and retrieves the follow-up question.

- **Content-Type**: `application/json`
- **Request Body**:
  ```json
  {
    "interview_id": "e6abf776-6ee1-4545-9273-04bc7a0e1cb1",
    "answer": "I built a dashboard using Redux Toolkit to sync real-time web socket data..."
  }
  ```
- **Success Response**: `200 OK`
  ```json
  {
    "success": true,
    "data": {
      "is_finished": false,
      "next_question": "Thanks for explaining. How did you optimize the re-rendering performance when handling high-frequency web socket updates in Redux?"
    }
  }
  ```

---

## 6. GET `/dashboard`
Retrieves aggregated statistics and history metrics for the current user.

- **Headers**:
  - `Authorization: Bearer <token>`
- **Success Response**: `200 OK`
  ```json
  {
    "success": true,
    "data": {
      "total_interviews": 12,
      "average_score": 82.5,
      "skill_mastery": [
        { "skill": "React", "score": 90 },
        { "skill": "System Design", "score": 65 }
      ],
      "recent_interviews": [
        {
          "interview_id": "e6abf776-6ee1-4545-9273-04bc7a0e1cb1",
          "company_name": "Google",
          "job_title": "Software Engineer",
          "score": 85.0,
          "completed_at": "2026-06-25T01:50:00Z"
        }
      ]
    }
  }
  ```
