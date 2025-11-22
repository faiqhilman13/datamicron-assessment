from sentence_transformers import CrossEncoder
from typing import List, Dict
import os
from dotenv import load_dotenv

load_dotenv()


class Reranker:
    """Rerank retrieved documents using cross-encoder model"""

    def __init__(self):
        self.model_name = os.getenv("RERANKER_MODEL", "cross-encoder/ms-marco-MiniLM-L-6-v2")
        self.top_k_rerank = int(os.getenv("TOP_K_RERANK", "5"))

        print(f"Loading reranker model: {self.model_name}")
        self.model = CrossEncoder(self.model_name)
        print("✓ Reranker model loaded")

    def rerank(self, query: str, documents: List[Dict], top_k: int = None) -> List[Dict]:
        """
        Rerank documents using cross-encoder

        Args:
            query: User query
            documents: List of retrieved documents
            top_k: Number of top documents to return after reranking

        Returns:
            Reranked list of documents with relevance scores
        """
        if top_k is None:
            top_k = self.top_k_rerank

        if not documents:
            return []

        print(f"  → Reranking {len(documents)} documents with cross-encoder...")

        # Prepare query-document pairs
        pairs = []
        for doc in documents:
            # Use title + summary for reranking (more concise than full content)
            doc_text = f"{doc['title']} {doc['summary']}"
            pairs.append([query, doc_text])

        # Get relevance scores from cross-encoder
        scores = self.model.predict(pairs)
        print(f"    ✓ Computed rerank scores (range: {scores.min():.3f} to {scores.max():.3f})")

        # Add reranking scores to documents
        for doc, score in zip(documents, scores):
            doc['rerank_score'] = float(score)

        # Sort by reranking score (descending)
        reranked_docs = sorted(documents, key=lambda x: x['rerank_score'], reverse=True)

        # Show top reranked results
        print(f"    Top {min(3, len(reranked_docs))} after reranking:")
        for i, doc in enumerate(reranked_docs[:3], 1):
            print(f"      {i}. [{doc['rerank_score']:.3f}] {doc['title'][:60]}...")

        # Return top-k
        return reranked_docs[:top_k]

    def rerank_with_threshold(
        self,
        query: str,
        documents: List[Dict],
        threshold: float = 0.0,
        top_k: int = None
    ) -> List[Dict]:
        """
        Rerank documents and filter by threshold

        Args:
            query: User query
            documents: List of retrieved documents
            threshold: Minimum rerank score to include
            top_k: Maximum number of documents to return

        Returns:
            Filtered and reranked documents
        """
        reranked = self.rerank(query, documents, top_k)

        # Filter by threshold
        filtered = [doc for doc in reranked if doc['rerank_score'] >= threshold]

        return filtered


def test_reranker():
    """Test reranker functionality"""
    from pathlib import Path
    from hybrid_search import HybridSearch

    base_dir = Path(__file__).parent.parent.parent
    index_dir = base_dir / "indexes"

    # Initialize services
    searcher = HybridSearch(str(index_dir))
    reranker = Reranker()

    # Test query
    query = "What are some initiatives launched by MCMC?"

    print(f"\nQuery: {query}")
    print(f"{'='*80}\n")

    # Get initial results from hybrid search
    results = searcher.hybrid_search(query, top_k=10)

    print("BEFORE RERANKING:")
    print("-" * 80)
    for i, doc in enumerate(results[:5], 1):
        print(f"{i}. {doc['title']}")
        print(f"   RRF Score: {doc['rrf_score']:.4f}\n")

    # Rerank
    reranked_results = reranker.rerank(query, results, top_k=5)

    print("\nAFTER RERANKING:")
    print("-" * 80)
    for i, doc in enumerate(reranked_results, 1):
        print(f"{i}. {doc['title']}")
        print(f"   RRF Score: {doc['rrf_score']:.4f}")
        print(f"   Rerank Score: {doc['rerank_score']:.4f}\n")


if __name__ == "__main__":
    test_reranker()
