# Database Schema Design

This document details the database tables and relationships for InterviewPilot-AI.

---

## 1. Table: `users`
Stores user profile and credentials information.

| Column Name | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `UUID` | `PRIMARY KEY, DEFAULT gen_random_uuid()` | Unique identifier for each user |
| `email` | `VARCHAR(255)` | `UNIQUE, NOT NULL` | User email address |
| `password_hash` | `VARCHAR(255)` | `NULLABLE` (OAuth users may not have one) | Password hashed with bcrypt/argon2 |
| `first_name` | `VARCHAR(100)` | `NOT NULL` | First name of the user |
| `last_name` | `VARCHAR(100)` | `NOT NULL` | Last name of the user |
| `created_at` | `TIMESTAMP` | `DEFAULT CURRENT_TIMESTAMP` | Time user registered |
| `updated_at` | `TIMESTAMP` | `DEFAULT CURRENT_TIMESTAMP` | Time profile was last updated |

---

## 2. Table: `resumes`
Stores uploaded resume details and parsed text.

| Column Name | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `UUID` | `PRIMARY KEY, DEFAULT gen_random_uuid()` | Unique identifier for each resume |
| `user_id` | `UUID` | `FOREIGN KEY REFERENCES users(id) ON DELETE CASCADE` | ID of the user who owns this resume |
| `file_name` | `VARCHAR(255)` | `NOT NULL` | Original filename |
| `file_url` | `VARCHAR(512)` | `NOT NULL` | Storage URL for the resume file |
| `parsed_content` | `TEXT` | `NOT NULL` | Raw parsed text content from PDF/Docx |
| `structured_data` | `JSONB` | `NULLABLE` | Extracted skills, experience, and education structured details |
| `created_at` | `TIMESTAMP` | `DEFAULT CURRENT_TIMESTAMP` | Time resume was uploaded |

---

## 3. Table: `jobs`
Stores job descriptions (JD) and target company information.

| Column Name | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `UUID` | `PRIMARY KEY, DEFAULT gen_random_uuid()` | Unique identifier for each JD record |
| `user_id` | `UUID` | `FOREIGN KEY REFERENCES users(id) ON DELETE CASCADE` | ID of the user preparing for this job |
| `company_name` | `VARCHAR(100)` | `NOT NULL` | Target company name |
| `job_title` | `VARCHAR(150)` | `NOT NULL` | Target job title |
| `jd_text` | `TEXT` | `NOT NULL` | Job description raw text |
| `structured_skills`| `JSONB` | `NULLABLE` | Extracted key skills and requirements |
| `created_at` | `TIMESTAMP` | `DEFAULT CURRENT_TIMESTAMP` | Time job was configured |

---

## 4. Table: `interviews`
Tracks mock interview sessions, questions, and evaluation outputs.

| Column Name | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `UUID` | `PRIMARY KEY, DEFAULT gen_random_uuid()` | Unique identifier for each interview session |
| `user_id` | `UUID` | `FOREIGN KEY REFERENCES users(id) ON DELETE CASCADE` | User taking the mock interview |
| `resume_id` | `UUID` | `FOREIGN KEY REFERENCES resumes(id) ON DELETE SET NULL` | Resume used in this interview |
| `job_id` | `UUID` | `FOREIGN KEY REFERENCES jobs(id) ON DELETE SET NULL` | Target JD used in this interview |
| `status` | `VARCHAR(50)` | `NOT NULL` (`in-progress`, `completed`, `failed`) | Session state |
| `history` | `JSONB` | `NOT NULL` | Chat history containing questions and responses |
| `overall_score` | `DECIMAL(5,2)` | `NULLABLE` | Final grade overall score (0 to 100) |
| `evaluation_report`| `JSONB` | `NULLABLE` | Strengths, weaknesses, and improvement details |
| `created_at` | `TIMESTAMP` | `DEFAULT CURRENT_TIMESTAMP` | Start time of the interview |
| `completed_at` | `TIMESTAMP` | `NULLABLE` | Completion time of the interview |

---

## 5. Table: `progress`
Maintains records of skill mastery, overall improvement, and cumulative stats.

| Column Name | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `UUID` | `PRIMARY KEY, DEFAULT gen_random_uuid()` | Unique identifier for the progress record |
| `user_id` | `UUID` | `FOREIGN KEY REFERENCES users(id) ON DELETE CASCADE` | User tracking their progress |
| `skill_name` | `VARCHAR(100)` | `NOT NULL` | Name of the skill (e.g., "React", "System Design") |
| `mastery_level` | `DECIMAL(5,2)` | `NOT NULL DEFAULT 0.00` | Current mastery level/score (0 to 100) |
| `interviews_count` | `INTEGER` | `NOT NULL DEFAULT 0` | Number of interviews taken mapping to this skill |
| `updated_at` | `TIMESTAMP` | `DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP` | Last time progress was updated |
