#!/usr/bin/env python3
"""
Build search indexes for the RAG system

This script:
1. Loads news.csv
2. Creates OpenAI embeddings
3. Builds FAISS index for semantic search
4. Builds BM25 index for keyword search
5. Saves all indexes to disk

Usage:
    python build_indexes.py
"""

from app.services.data_processor import DataProcessor
from pathlib import Path


def main():
    base_dir = Path(__file__).parent
    data_path = base_dir / "data" / "news.csv"
    index_dir = base_dir / "indexes"

    print("\n" + "="*80)
    print("Building Search Indexes")
    print("="*80 + "\n")

    print(f"Data path: {data_path}")
    print(f"Index directory: {index_dir}\n")

    if not data_path.exists():
        print(f"Error: Data file not found at {data_path}")
        return

    processor = DataProcessor(str(data_path), str(index_dir))

    try:
        processor.build_all_indexes()
        print("\n" + "="*80)
        print("✓ Index building completed successfully!")
        print("="*80 + "\n")

    except Exception as e:
        print(f"\n✗ Error building indexes: {e}\n")
        raise


if __name__ == "__main__":
    main()
