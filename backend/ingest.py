#!/usr/bin/env python3
"""
Ingest CSS/PMS study materials into ChromaDB vector database.
This script loads:
- master_notes_rag.jsonl (CSS + PMS study notes)
- past_papers_extracted.jsonl (exam past papers)
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.vector_store import VectorStore

def ingest_all_data():
    """Ingest all study materials into ChromaDB."""
    
    # Initialize vector store
    vs = VectorStore(db_path=r"e:\css\chroma_db", reset=False)
    
    # Define file paths
    BASE_DIR = r"e:\css"
    notes_file = os.path.join(BASE_DIR, "master_notes_rag.jsonl")
    papers_file = os.path.join(BASE_DIR, "past_papers_extracted.jsonl")
    
    # Ingest study notes
    if os.path.exists(notes_file):
        print(f"[Ingestion] Loading notes from {notes_file}...")
        vs.add_jsonl(notes_file, doc_type="notes")
        print(f"[Ingestion] Notes ingestion complete.")
    else:
        print(f"[Ingestion] Notes file not found: {notes_file}")
    
    # Ingest past papers
    if os.path.exists(papers_file):
        print(f"[Ingestion] Loading past papers from {papers_file}...")
        vs.add_jsonl(papers_file, doc_type="past_paper")
        print(f"[Ingestion] Past papers ingestion complete.")
    else:
        print(f"[Ingestion] Papers file not found: {papers_file}")
    
    # Final stats
    final_count = vs.collection.count()
    print(f"\n✅ [Ingestion Complete] Total documents in ChromaDB: {final_count}")
    
    return final_count

if __name__ == "__main__":
    ingest_all_data()
