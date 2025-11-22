import pandas as pd
import numpy as np
import pickle
import faiss
from pathlib import Path
from typing import List, Dict
from openai import OpenAI
from rank_bm25 import BM25Okapi
import os
from dotenv import load_dotenv

load_dotenv()


class DataProcessor:
    """Handles data loading, preprocessing, and index creation"""

    def __init__(self, data_path: str, index_dir: str):
        self.data_path = Path(data_path)
        self.index_dir = Path(index_dir)
        self.index_dir.mkdir(parents=True, exist_ok=True)

        self.df = None
        self.documents = []
        self.faiss_index = None
        self.bm25_index = None

        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.embedding_model = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

    def load_data(self) -> pd.DataFrame:
        """Load and preprocess news.csv"""
        print("Loading news data...")
        self.df = pd.read_csv(self.data_path)

        # Clean and prepare documents
        self.df['combined_text'] = (
            self.df['title'].fillna('') + ' ' +
            self.df['summary'].fillna('') + ' ' +
            self.df['article_content'].fillna('')
        )

        # Create document objects with metadata
        self.documents = []
        for idx, row in self.df.iterrows():
            self.documents.append({
                'id': idx,
                'title': row['title'],
                'content': row['article_content'],
                'summary': row['summary'],
                'author': row['author'],
                'sentiment': row['sentiment'],
                'timestamp': row['timestamp'],
                'combined_text': row['combined_text'],
                'url': row.get('url', '')
            })

        print(f"Loaded {len(self.documents)} documents")
        return self.df

    def create_embeddings(self, texts: List[str], batch_size: int = 100) -> np.ndarray:
        """Create embeddings using OpenAI API with batching"""
        print(f"Creating embeddings for {len(texts)} texts...")
        all_embeddings = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            print(f"Processing batch {i//batch_size + 1}/{(len(texts)-1)//batch_size + 1}")

            response = self.client.embeddings.create(
                input=batch,
                model=self.embedding_model
            )

            batch_embeddings = [item.embedding for item in response.data]
            all_embeddings.extend(batch_embeddings)

        return np.array(all_embeddings, dtype='float32')

    def build_faiss_index(self) -> faiss.Index:
        """Build FAISS index for semantic search"""
        print("Building FAISS index...")

        # Get combined texts for embedding
        texts = [doc['combined_text'] for doc in self.documents]

        # Create embeddings
        embeddings = self.create_embeddings(texts)

        # Build FAISS index
        dimension = embeddings.shape[1]
        self.faiss_index = faiss.IndexFlatIP(dimension)  # Inner product for cosine similarity

        # Normalize embeddings for cosine similarity
        faiss.normalize_L2(embeddings)
        self.faiss_index.add(embeddings)

        # Save index and embeddings
        faiss.write_index(self.faiss_index, str(self.index_dir / "faiss.index"))
        np.save(str(self.index_dir / "embeddings.npy"), embeddings)

        print(f"FAISS index created with {self.faiss_index.ntotal} vectors")
        return self.faiss_index

    def build_bm25_index(self) -> BM25Okapi:
        """Build BM25 index for keyword search"""
        print("Building BM25 index...")

        # Tokenize documents (simple word-based tokenization)
        tokenized_docs = [doc['combined_text'].lower().split() for doc in self.documents]

        # Build BM25 index
        self.bm25_index = BM25Okapi(tokenized_docs)

        # Save BM25 index
        with open(self.index_dir / "bm25.pkl", 'wb') as f:
            pickle.dump(self.bm25_index, f)

        print("BM25 index created")
        return self.bm25_index

    def save_documents(self):
        """Save processed documents"""
        with open(self.index_dir / "documents.pkl", 'wb') as f:
            pickle.dump(self.documents, f)
        print("Documents saved")

    def build_all_indexes(self):
        """Build all indexes (FAISS + BM25)"""
        self.load_data()
        self.build_faiss_index()
        self.build_bm25_index()
        self.save_documents()
        print("\n✓ All indexes built successfully!")


def main():
    """Build indexes from command line"""
    import sys

    base_dir = Path(__file__).parent.parent.parent
    data_path = base_dir / "data" / "news.csv"
    index_dir = base_dir / "indexes"

    processor = DataProcessor(str(data_path), str(index_dir))
    processor.build_all_indexes()


if __name__ == "__main__":
    main()
