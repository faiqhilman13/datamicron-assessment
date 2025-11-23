from openai import OpenAI
from typing import List, Dict, Tuple
import os
import math
from dotenv import load_dotenv

from .hybrid_search import HybridSearch
from .reranker import Reranker
from .llm_judge import LLMJudge
from .web_search import perform_web_search
from .rl_optimizer import RLOptimizer

load_dotenv()


def safe_string(value, default=''):
    """Convert value to string, handling nan/None values"""
    if value is None:
        return default
    if isinstance(value, float) and math.isnan(value):
        return default
    return str(value)


class RAGService:
    """Main RAG service combining hybrid search, reranking, and answer generation"""

    def __init__(self, index_dir: str):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = os.getenv("LLM_MODEL", "gpt-4-turbo-preview")

        # Check if reranker should be enabled (disabled by default for free tier deployments)
        self.enable_reranker = os.getenv("ENABLE_RERANKER", "false").lower() == "true"

        # Initialize components
        print("Initializing RAG service...")
        self.searcher = HybridSearch(index_dir)

        if self.enable_reranker:
            self.reranker = Reranker()
            print("✓ Reranker enabled")
        else:
            self.reranker = None
            print("⚠ Reranker disabled (to enable, set ENABLE_RERANKER=true)")

        self.judge = LLMJudge()
        self.rl_optimizer = RLOptimizer()  # Add RL optimizer
        print("✓ RAG service ready")

    def generate_answer(
        self,
        query: str,
        context_docs: List[Dict],
        web_results: List[Dict] = None
    ) -> str:
        """
        Generate answer using OpenAI with retrieved context

        Args:
            query: User query
            context_docs: Retrieved and reranked documents
            web_results: Optional web search results

        Returns:
            Generated answer with source citations
        """
        # Prepare context from internal documents
        context_parts = []

        if context_docs:
            context_parts.append("INTERNAL KNOWLEDGE BASE:\n")
            for i, doc in enumerate(context_docs, 1):
                context_parts.append(
                    f"[Source {i}] Title: {doc['title']}\n"
                    f"Author: {doc['author']}\n"
                    f"Content: {doc['summary']}\n"
                    f"Full Article: {doc['content'][:500]}...\n"
                )

        # Add web results if available
        if web_results:
            context_parts.append("\n\nWEB SEARCH RESULTS:\n")
            for i, result in enumerate(web_results, 1):
                context_parts.append(
                    f"[Web Source {i}] {result.get('title', 'N/A')}\n"
                    f"URL: {result.get('url', 'N/A')}\n"
                    f"Content: {result.get('text', 'N/A')[:500]}...\n"
                )

        context = "\n".join(context_parts)

        # Create prompt
        prompt = f"""You are a helpful AI assistant that answers questions about Malaysian news based on provided sources.

User Question: {query}

{context}

Instructions:
1. Answer the question based on the provided sources
2. ALWAYS cite your sources in your answer by mentioning the source name or author
3. If using internal knowledge base, mention the news source (e.g., "According to Kosmo Digital..." or "FMT Reporters reported that...")
4. If using web search results, mention "According to web sources..." and include the URL if relevant
5. If the sources don't contain enough information, say so clearly
6. Be concise but comprehensive
7. Support both English and Malay questions

Answer:"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful news assistant that provides accurate, well-cited answers."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=800
            )

            answer = response.choices[0].message.content
            return answer

        except Exception as e:
            print(f"Error generating answer: {e}")
            return f"I apologize, but I encountered an error while generating an answer: {str(e)}"

    def process_query(
        self,
        query: str,
        enable_web_search: bool = True
    ) -> Dict:
        """
        Process a query through the complete RAG pipeline

        Args:
            query: User query
            enable_web_search: Whether to enable web search fallback

        Returns:
            {
                "answer": str,
                "sources": List[Dict],
                "confidence": float,
                "judge_scores": Dict,
                "retrieval_method": str,
                "web_search_triggered": bool
            }
        """
        # Step 1: Hybrid Search
        print(f"\n[1/6] Performing hybrid search for: {query}")
        retrieved_docs = self.searcher.hybrid_search(query, top_k=20)

        # Step 2: Reranking (or skip if disabled)
        if self.enable_reranker and self.reranker:
            print("[2/6] Reranking results...")
            reranked_docs = self.reranker.rerank(query, retrieved_docs, top_k=5)
        else:
            print("[2/6] Reranking disabled, using top 5 from hybrid search...")
            reranked_docs = retrieved_docs[:5]
            # Add dummy rerank scores for compatibility
            for doc in reranked_docs:
                if 'rerank_score' not in doc:
                    doc['rerank_score'] = doc.get('score', 0.5)

        # Step 3: Judge retrieval adequacy
        print("[3/6] Evaluating retrieval quality...")
        retrieval_eval = self.judge.evaluate_retrieval_adequacy(query, reranked_docs)

        web_search_triggered = False
        web_results = None

        # Step 4: Web search if needed (using RL-optimized threshold)
        # Use RL optimizer to determine if web search should be triggered
        judge_score = retrieval_eval['confidence']
        # Calculate preliminary confidence (will be recalculated later with RL weights)
        prelim_confidence = judge_score / 10.0

        # Use RL-optimized decision making
        should_search = self.rl_optimizer.should_trigger_web_search(
            confidence=prelim_confidence,
            judge_score=judge_score
        )

        rl_threshold = self.rl_optimizer.config.get('web_search.confidence_threshold', 0.7)
        print(f"[RL] Web search decision: confidence={prelim_confidence:.2f}, threshold={rl_threshold:.2f}, trigger={should_search}")

        if enable_web_search and (retrieval_eval.get("needs_web_search", False) or should_search):
            print(f"\n[4/6] Internal knowledge insufficient (confidence: {retrieval_eval['confidence']}/10). Triggering web search...")
            web_results = perform_web_search(query, num_results=3)
            if web_results:
                print(f"  ✓ Retrieved {len(web_results)} web results")
                for i, result in enumerate(web_results, 1):
                    print(f"    {i}. {result['title'][:60]}...")
                web_search_triggered = True
            else:
                print(f"  ✗ Web search failed or returned no results")
        else:
            print(f"\n[4/6] Internal knowledge sufficient (confidence: {retrieval_eval['confidence']}/10). Skipping web search.")

        # Step 5: Generate answer
        print("\n[5/6] Generating answer...")
        print(f"  → Using {len(reranked_docs)} documents as context")
        answer = self.generate_answer(query, reranked_docs, web_results)
        print(f"    ✓ Generated answer ({len(answer)} chars)")
        print(f"    Preview: {answer[:150]}...")

        # Step 6: Evaluate answer quality
        print("\n[6/6] Evaluating answer quality...")

        # Prepare sources for response
        sources = []

        # Normalize rerank scores to 0-1 range
        if reranked_docs:
            rerank_scores = [doc.get('rerank_score', 0) for doc in reranked_docs]
            min_score = min(rerank_scores)
            max_score = max(rerank_scores)
            score_range = max_score - min_score if max_score != min_score else 1
            print(f"  → Normalizing {len(reranked_docs)} source relevance scores...")

        for doc in reranked_docs:
            # Normalize rerank_score to 0-1 range
            raw_score = float(doc.get('rerank_score', 0))
            if reranked_docs and score_range > 0:
                normalized_score = (raw_score - min_score) / score_range
            else:
                normalized_score = 0.5

            sources.append({
                "type": "internal",
                "title": safe_string(doc.get('title', '')),
                "author": safe_string(doc.get('author', '')),
                "url": safe_string(doc.get('url', '')),
                "relevance_score": max(0.0, min(1.0, normalized_score)),  # Clamp to 0-1
                "sentiment": safe_string(doc.get('sentiment', ''))
            })

        # Add web sources if any
        if web_results:
            for result in web_results:
                # Ensure relevance_score is never None
                score = result.get('score', 0.8)
                if score is None or (isinstance(score, float) and math.isnan(score)):
                    score = 0.8

                sources.append({
                    "type": "web",
                    "title": safe_string(result.get('title', '')),
                    "author": safe_string(result.get('author', None)),
                    "url": safe_string(result.get('url', '')),
                    "relevance_score": float(score),
                    "sentiment": safe_string(result.get('sentiment', None))
                })

        # Evaluate answer
        answer_eval = self.judge.evaluate_answer_quality(query, answer, sources)

        # Calculate overall confidence using RL-optimized weights
        weighted_overall_score = self.rl_optimizer.calculate_weighted_judge_score(answer_eval)
        confidence = self.rl_optimizer.calculate_weighted_confidence(
            retrieval_score=retrieval_eval['confidence'],
            answer_score=weighted_overall_score
        )

        print(f"[RL] Confidence calculation: retrieval={retrieval_eval['confidence']:.1f}, answer={weighted_overall_score:.1f}, final={confidence:.2f}")

        print(f"\n{'='*80}")
        print(f"✓ QUERY PROCESSING COMPLETE")
        print(f"{'='*80}")
        print(f"  Overall Confidence: {confidence:.2%} ({confidence*10:.1f}/10)")
        print(f"  Sources Used: {len(sources)}")
        print(f"  Web Search Triggered: {'Yes' if web_search_triggered else 'No'}")
        print(f"  Retrieval Method: hybrid_search_with_reranking")
        print(f"  Judge Scores: R={answer_eval.get('relevance', 0)}/10, F={answer_eval.get('factuality', 0)}/10, C={answer_eval.get('completeness', 0)}/10")
        print(f"{'='*80}\n")

        return {
            "answer": answer,
            "sources": sources,
            "confidence": confidence,
            "judge_scores": {
                "relevance": answer_eval.get('relevance', 5),
                "factuality": answer_eval.get('factuality', 5),
                "completeness": answer_eval.get('completeness', 5)
            },
            "retrieval_method": "hybrid_search_with_reranking",
            "web_search_triggered": web_search_triggered
        }


def test_rag():
    """Test RAG service"""
    from pathlib import Path

    base_dir = Path(__file__).parent.parent.parent
    index_dir = base_dir / "indexes"

    rag = RAGService(str(index_dir))

    # Test queries
    queries = [
        "What are some initiatives launched by MCMC?",
        "Adakah SSM terbabit dengan kes-kes mahkamah?"
    ]

    for query in queries:
        print(f"\n{'='*80}")
        print(f"QUERY: {query}")
        print(f"{'='*80}")

        result = rag.process_query(query, enable_web_search=True)

        print(f"\nANSWER:\n{result['answer']}")
        print(f"\nCONFIDENCE: {result['confidence']:.2f}")
        print(f"\nJUDGE SCORES:")
        for key, value in result['judge_scores'].items():
            print(f"  {key.capitalize()}: {value}/10")


if __name__ == "__main__":
    test_rag()
