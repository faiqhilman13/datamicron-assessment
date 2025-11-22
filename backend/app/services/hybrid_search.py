import numpy as np
import faiss
import pickle
from pathlib import Path
from typing import List, Dict, Tuple
from openai import OpenAI
from rank_bm25 import BM25Okapi
import os
from dotenv import load_dotenv

load_dotenv()


class HybridSearch:
    """Hybrid search combining semantic (FAISS) and keyword (BM25) search"""

    def __init__(self, index_dir: str):
        self.index_dir = Path(index_dir)
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.embedding_model = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
        self.top_k = int(os.getenv("TOP_K_RETRIEVAL", "20"))

        self.faiss_index = None
        self.bm25_index = None
        self.documents = None
        self.embeddings = None

        self.load_indexes()

    def load_indexes(self):
        """Load pre-built indexes"""
        print("Loading indexes...")

        # Load FAISS index
        faiss_path = self.index_dir / "faiss.index"
        if faiss_path.exists():
            self.faiss_index = faiss.read_index(str(faiss_path))
            print(f"✓ FAISS index loaded ({self.faiss_index.ntotal} vectors)")
        else:
            raise FileNotFoundError(f"FAISS index not found at {faiss_path}")

        # Load embeddings
        embeddings_path = self.index_dir / "embeddings.npy"
        if embeddings_path.exists():
            self.embeddings = np.load(str(embeddings_path))
            print(f"✓ Embeddings loaded")

        # Load BM25 index
        bm25_path = self.index_dir / "bm25.pkl"
        if bm25_path.exists():
            with open(bm25_path, 'rb') as f:
                self.bm25_index = pickle.load(f)
            print(f"✓ BM25 index loaded")
        else:
            raise FileNotFoundError(f"BM25 index not found at {bm25_path}")

        # Load documents
        docs_path = self.index_dir / "documents.pkl"
        if docs_path.exists():
            with open(docs_path, 'rb') as f:
                self.documents = pickle.load(f)
            print(f"✓ Documents loaded ({len(self.documents)} docs)")
        else:
            raise FileNotFoundError(f"Documents not found at {docs_path}")

    def create_query_embedding(self, query: str) -> np.ndarray:
        """Create embedding for query"""
        response = self.client.embeddings.create(
            input=[query],
            model=self.embedding_model
        )
        embedding = np.array([response.data[0].embedding], dtype='float32')
        faiss.normalize_L2(embedding)
        return embedding

    def semantic_search(self, query: str, k: int = None) -> List[Tuple[int, float]]:
        """Perform semantic search using FAISS"""
        if k is None:
            k = self.top_k

        query_embedding = self.create_query_embedding(query)

        # Search FAISS index
        distances, indices = self.faiss_index.search(query_embedding, k)

        # Return list of (doc_id, score) tuples
        results = [(int(idx), float(score)) for idx, score in zip(indices[0], distances[0])]
        return results

    def keyword_search(self, query: str, k: int = None) -> List[Tuple[int, float]]:
        """Perform keyword search using BM25"""
        if k is None:
            k = self.top_k

        # Tokenize query
        tokenized_query = query.lower().split()

        # Get BM25 scores for all documents
        scores = self.bm25_index.get_scores(tokenized_query)

        # Get top-k results
        top_k_indices = np.argsort(scores)[::-1][:k]

        # Return list of (doc_id, score) tuples
        results = [(int(idx), float(scores[idx])) for idx in top_k_indices]
        return results

    def reciprocal_rank_fusion(
        self,
        semantic_results: List[Tuple[int, float]],
        keyword_results: List[Tuple[int, float]],
        k: int = 60
    ) -> List[Tuple[int, float]]:
        """
        Combine results using Reciprocal Rank Fusion (RRF)

        RRF formula: score(d) = sum(1 / (k + rank(d)))
        where k is a constant (typically 60) and rank(d) is the rank of document d
        """
        rrf_scores = {}

        # Add semantic search scores
        for rank, (doc_id, _) in enumerate(semantic_results, 1):
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0) + (1 / (k + rank))

        # Add keyword search scores
        for rank, (doc_id, _) in enumerate(keyword_results, 1):
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0) + (1 / (k + rank))

        # Sort by RRF score (descending)
        sorted_results = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)

        return sorted_results

    def hybrid_search(self, query: str, top_k: int = None) -> List[Dict]:
        """
        Perform hybrid search combining semantic and keyword search

        Returns:
            List of document dictionaries with metadata and scores
        """
        if top_k is None:
            top_k = self.top_k

        print(f"  → Performing semantic search (FAISS)...")
        semantic_results = self.semantic_search(query, k=top_k)
        print(f"    ✓ Found {len(semantic_results)} semantic matches")
        print(f"    Top 3 semantic: {[self.documents[doc_id]['title'][:50] + '...' for doc_id, _ in semantic_results[:3]]}")

        print(f"  → Performing keyword search (BM25)...")
        keyword_results = self.keyword_search(query, k=top_k)
        print(f"    ✓ Found {len(keyword_results)} keyword matches")
        print(f"    Top 3 keyword: {[self.documents[doc_id]['title'][:50] + '...' for doc_id, _ in keyword_results[:3]]}")

        # Combine using RRF
        print(f"  → Fusing results with Reciprocal Rank Fusion...")
        fused_results = self.reciprocal_rank_fusion(semantic_results, keyword_results)

        # Get top-k fused results
        top_results = fused_results[:top_k]

        # Retrieve full document information
        retrieved_docs = []
        for doc_id, rrf_score in top_results:
            doc = self.documents[doc_id].copy()
            doc['rrf_score'] = rrf_score
            doc['doc_id'] = doc_id
            retrieved_docs.append(doc)

        return retrieved_docs


def test_hybrid_search():
    """Test hybrid search functionality"""
    import sys
    from pathlib import Path

    base_dir = Path(__file__).parent.parent.parent
    index_dir = base_dir / "indexes"

    searcher = HybridSearch(str(index_dir))

    # Test queries
    queries = [
        "What are some initiatives launched by MCMC?",
        "Adakah SSM terbabit dengan kes-kes mahkamah?",
        "Malaysian economy 2025"
    ]

    for query in queries:
        print(f"\n{'='*80}")
        print(f"Query: {query}")
        print(f"{'='*80}")

        results = searcher.hybrid_search(query, top_k=5)

        for i, doc in enumerate(results, 1):
            print(f"\n{i}. {doc['title']}")
            print(f"   Author: {doc['author']}")
            print(f"   RRF Score: {doc['rrf_score']:.4f}")
            print(f"   Sentiment: {doc['sentiment']}")
            print(f"   Summary: {doc['summary'][:150]}...")


if __name__ == "__main__":
    test_hybrid_search()
