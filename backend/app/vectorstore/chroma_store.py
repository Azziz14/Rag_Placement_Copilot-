"""Vector store management module using ChromaDB.
"""

import os
import chromadb
from chromadb.utils import embedding_functions

# Define storage directory within the backend workspace
CHROMA_PERSIST_DIR = os.environ.get(
    "CHROMA_PERSIST_DIR",
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "chroma_db")
    )
)

# Initialize Client
client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)

# Use Chroma's default embedding function (ONNX-based local MiniLM-L6-v2)
default_ef = embedding_functions.DefaultEmbeddingFunction()


def get_or_create_collection(name: str):
    """Retrieves or creates a ChromaDB collection with the default embedding function."""
    return client.get_or_create_collection(name=name, embedding_function=default_ef)


def seed_database():
    """Seeds the database collections with mock data if they are empty."""
    # 1. Role Guides Collection
    role_guides = get_or_create_collection("role_guides")
    if role_guides.count() == 0:
        role_guides.add(
            ids=["rg_1", "rg_2", "rg_3"],
            documents=[
                "Software Engineer Guide: Focused on coding quality, algorithms, system design patterns like MVC, Microservices, REST APIs, and database consistency models.",
                "System Design Basics: Topics include load balancing, horizontal scalability, caching strategies (Redis/Memcached), message queues (Kafka/RabbitMQ), and database sharding.",
                "Frontend Engineer Guide: Focus on performance optimizations, semantic HTML, modern styling, React/Next.js architectures, state management, and accessibility standards."
            ],
            metadatas=[
                {"role": "Software Engineer", "topic": "General SE"},
                {"role": "Software Engineer", "topic": "System Design"},
                {"role": "Frontend Engineer", "topic": "UI/UX"}
            ]
        )

    # 2. Company Patterns Collection
    company_patterns = get_or_create_collection("company_patterns")
    if company_patterns.count() == 0:
        company_patterns.add(
            ids=["cp_1", "cp_2", "cp_3"],
            documents=[
                "Google Interview Patterns: Emphasis on solid understanding of algorithms, data structures (graphs, trees, dynamic programming), clean code, and complexity analysis (Big-O).",
                "Meta Product Architecture: Heavy focus on system design, end-to-end user flows, API interfaces, caching, scale estimation, and product engineering tradeoffs.",
                "Amazon Leadership Principles Guide: Emphasizes Customer Obsession, Ownership, Bias for Action, and Deliver Results. Behavioral answers must follow the STAR method (Situation, Task, Action, Result)."
            ],
            metadatas=[
                {"company": "Google", "pattern": "Algorithm Heavy"},
                {"company": "Meta", "pattern": "System Design Heavy"},
                {"company": "Amazon", "pattern": "Leadership Principles"}
            ]
        )

    # 3. DSA Questions Collection
    dsa_questions = get_or_create_collection("dsa_questions")
    if dsa_questions.count() == 0:
        dsa_questions.add(
            ids=["dsa_1", "dsa_2", "dsa_3"],
            documents=[
                "Two Sum: Find two numbers in an array that add up to a target value. Topics: Hash Map, Arrays, Two Pointer.",
                "Reverse Linked List: Reverse a singly linked list iteratively and recursively. Topics: Linked List, Pointers.",
                "Longest Common Subsequence: Find the length of the longest subsequence present in both strings. Topics: Dynamic Programming, Strings."
            ],
            metadatas=[
                {"difficulty": "Easy", "topic": "Arrays & HashMaps"},
                {"difficulty": "Easy", "topic": "Linked Lists"},
                {"difficulty": "Medium", "topic": "Dynamic Programming"}
            ]
        )

    # 4. Behavioral Questions Collection
    behavioral_questions = get_or_create_collection("behavioral_questions")
    if behavioral_questions.count() == 0:
        behavioral_questions.add(
            ids=["bq_1", "bq_2"],
            documents=[
                "Describe a conflict you had with a team member and how you resolved it. Key focus: communication, compromise, professional alignment.",
                "Tell me about a time you made a mistake or failed to meet a deadline. Key focus: learning from errors, accountability, problem remediation."
            ],
            metadatas=[
                {"category": "Conflict Resolution"},
                {"category": "Failure & Learning"}
            ]
        )

    # 5. Skills Index Collection
    skills_index = get_or_create_collection("skills_index")
    if skills_index.count() == 0:
        skills_index.add(
            ids=["sk_python", "sk_fastapi", "sk_docker", "sk_sql"],
            documents=[
                "Python Guide: Covers core object-oriented programming, data structures, list comprehensions, generators, asyncio, and standard library features.",
                "FastAPI Guide: Focuses on async endpoints, dependency injection, Pydantic data validation, automated docs generation, and middle-layer configurations.",
                "Docker Guide: Focuses on containerization, writing Dockerfiles, multi-stage builds, Docker Compose orchestration, and resource constraints.",
                "SQL Guide: Covers relational queries, joins, indexes, database normalization, transaction isolation levels, and aggregation query optimizations."
            ],
            metadatas=[
                {"skill": "Python"},
                {"skill": "FastAPI"},
                {"skill": "Docker"},
                {"skill": "SQL"}
            ]
        )


# Run seeding on module import
seed_database()
