# Workflow Diagram and Steps

This document outlines the user and system workflows for InterviewPilot-AI.

## Application Flow

```mermaid
graph TD
    A[User] --> B[Upload Resume]
    B --> C[Upload JD]
    C --> D[Select Company]
    D --> E[RAG (Retrieval-Augmented Generation)]
    E --> F[Mock Interview]
    F --> G[Evaluation]
    G --> H[Dashboard]
```

### Flow Details
1. **User**: The entry point of the application.
2. **Upload Resume**: User uploads their professional resume (PDF/Docx).
3. **Upload JD**: User uploads the job description of the target role.
4. **Select Company**: User selects the target company (to customize interview style, values, and question bank).
5. **RAG (Retrieval-Augmented Generation)**: Contextualizing interview questions and resources by querying database datasets, resumes, and JD.
6. **Mock Interview**: The interactive mock interview simulation starts, utilizing the customized question set.
7. **Evaluation**: Comprehensive assessment and feedback generation on the user's responses.
8. **Dashboard**: Centralized performance metrics, history, and learning progress dashboard.
