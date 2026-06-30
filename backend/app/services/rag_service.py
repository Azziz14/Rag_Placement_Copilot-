"""Service module for managing RAG-based context retrieval from ChromaDB.
"""

from typing import List, Dict, Any
from sqlalchemy.orm import Session

from app.models.resume_match import ResumeMatch
from app.models.job_description import JobDescription
from app.vectorstore.chroma_store import get_or_create_collection


class RAGService:
    """Service to handle vector store queries and aggregate relevant context for question generation."""

    def build_query(self, match: ResumeMatch, jd: JobDescription) -> Dict[str, str]:
        """Builds search query strings from the match analysis and JD.
        
        Returns a dictionary of queries mapped by category.
        """
        # Formulate query strings using missing/required/strong skills and areas
        missing_skills_str = ", ".join(match.missing_skills or [])
        strong_areas_str = ", ".join(match.strong_areas or [])
        required_skills_str = ", ".join(jd.required_skills or [])
        
        return {
            "role_query": f"Guides for {jd.job_title} role with required skills ({required_skills_str}) and core responsibilities.",
            "company_query": f"{jd.company_name} interview process, patterns, values, and questions.",
            "missing_skills_query": f"Tutorials, explanations and guidelines for learning: {missing_skills_str}",
            "behavioral_query": f"Behavioral questions matching candidate strong areas ({strong_areas_str}), STAR method, conflict resolution, leadership.",
            "dsa_query": f"Common DSA data structures and algorithms questions relevant to {jd.job_title} role."
        }

    def retrieve_role_context(self, role: str, query: str) -> List[Dict[str, Any]]:
        """Retrieves guides and architectural patterns related to the target role."""
        collection = get_or_create_collection("role_guides")
        results = collection.query(
            query_texts=[query],
            n_results=3
        )
        return self._format_results(results)

    def retrieve_company_context(self, company: str, query: str) -> List[Dict[str, Any]]:
        """Retrieves company interview experiences and guidelines."""
        collection = get_or_create_collection("company_patterns")
        
        # Optionally filter by company name metadata if present
        where_filter = {}
        if company:
            where_filter = {"company": company}
            
        results = collection.query(
            query_texts=[query],
            n_results=3,
            where=where_filter if where_filter else None
        )
        return self._format_results(results)

    def retrieve_missing_skill_context(self, missing_skills: List[str]) -> List[Dict[str, Any]]:
        """Retrieves targeted guides/references for candidate's missing skills using a single batch query."""
        if not missing_skills:
            return []
            
        collection = get_or_create_collection("skills_index")
        query_texts = [f"Tutorial and guide for {skill}" for skill in missing_skills[:5]]
        
        results = collection.query(
            query_texts=query_texts,
            n_results=1
        )
        
        formatted = []
        if not results or "documents" not in results:
            return formatted
            
        docs_list = results.get("documents") or []
        metadatas_list = results.get("metadatas") or []
        ids_list = results.get("ids") or []
        distances_list = results.get("distances") or []
        
        for q_idx in range(len(docs_list)):
            q_docs = docs_list[q_idx]
            q_metadatas = metadatas_list[q_idx] if q_idx < len(metadatas_list) else []
            q_ids = ids_list[q_idx] if q_idx < len(ids_list) else []
            q_distances = distances_list[q_idx] if q_idx < len(distances_list) else []
            
            for i in range(len(q_docs)):
                formatted.append({
                    "id": q_ids[i] if i < len(q_ids) else f"miss_{q_idx}_{i}",
                    "content": q_docs[i],
                    "metadata": q_metadatas[i] if i < len(q_metadatas) else {},
                    "score": float(q_distances[i]) if i < len(q_distances) else 0.0
                })
                
        return formatted

    def retrieve_behavioral_context(self, query: str) -> List[Dict[str, Any]]:
        """Retrieves sample behavioral questions and alignment guides."""
        collection = get_or_create_collection("behavioral_questions")
        results = collection.query(
            query_texts=[query],
            n_results=3
        )
        return self._format_results(results)

    def retrieve_dsa_context(self, query: str) -> List[Dict[str, Any]]:
        """Retrieves coding questions and data structure explanations."""
        collection = get_or_create_collection("dsa_questions")
        results = collection.query(
            query_texts=[query],
            n_results=3
        )
        return self._format_results(results)

    def retrieve_all_context(
        self, db: Session, user_id: str, match_id: str
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Coordinates the full retrieval process based on match analysis."""
        # 1. Fetch match record
        match = db.query(ResumeMatch).filter(ResumeMatch.id == match_id, ResumeMatch.user_id == user_id).first()
        if not match:
            raise ValueError(f"Match analysis with ID {match_id} not found or unauthorized.")
            
        # 2. Fetch associated Job Description
        jd = db.query(JobDescription).filter(JobDescription.id == match.job_description_id, JobDescription.user_id == user_id).first()
        if not jd:
            raise ValueError(f"Job Description associated with match analysis was not found.")

        # 3. Build queries
        queries = self.build_query(match, jd)

        # 4. Fetch context arrays from collections in parallel
        import concurrent.futures
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            future_role = executor.submit(self.retrieve_role_context, jd.job_title, queries["role_query"])
            future_company = executor.submit(self.retrieve_company_context, jd.company_name, queries["company_query"])
            future_skills = executor.submit(self.retrieve_missing_skill_context, match.missing_skills or [])
            future_behavioral = executor.submit(self.retrieve_behavioral_context, queries["behavioral_query"])
            future_dsa = executor.submit(self.retrieve_dsa_context, queries["dsa_query"])
            
            role_ctx = future_role.result()
            company_ctx = future_company.result()
            skills_ctx = future_skills.result()
            behavioral_ctx = future_behavioral.result()
            dsa_ctx = future_dsa.result()

        return {
            "role_context": role_ctx,
            "company_context": company_ctx,
            "missing_skill_context": skills_ctx,
            "behavioral_context": behavioral_ctx,
            "dsa_context": dsa_ctx
        }

    def _format_results(self, raw_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Helper to format raw ChromaDB query responses into clean dictionaries."""
        formatted = []
        if not raw_results or "documents" not in raw_results:
            return formatted
            
        docs = raw_results.get("documents", [[]])[0]
        metadatas = raw_results.get("metadatas", [[]])[0]
        distances = raw_results.get("distances", [[]])[0] if "distances" in raw_results else []
        ids = raw_results.get("ids", [[]])[0]

        for i in range(len(docs)):
            formatted.append({
                "id": ids[i],
                "content": docs[i],
                "metadata": metadatas[i] if i < len(metadatas) else {},
                "score": float(distances[i]) if i < len(distances) else 0.0
            })
            
        return formatted


# Global service instance
rag_service = RAGService()
