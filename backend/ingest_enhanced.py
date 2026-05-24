#!/usr/bin/env python3
"""
Enhanced Data Ingestion Pipeline.
Loads from CSS notes, PMS notes, and Essay files, then enriches with GPT-4 O Mini.
"""

import os
import sys
import json
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.vector_store import VectorStore
from app.services.note_generator import NoteGenerator

class EnhancedIngestion:
    def __init__(self, vs, note_gen=None):
        self.vs = vs
        self.note_gen = note_gen
        
    def ingest_css_notes(self, file_path):
        """Ingest CSS study notes."""
        print(f"[Ingestion] Loading CSS notes from {file_path}...")
        
        if not os.path.exists(file_path):
            print(f"[Ingestion] File not found: {file_path}")
            return 0
        
        count = 0
        with open(file_path, 'r', encoding='utf-8') as f:
            documents, metadatas, ids = [], [], []
            
            for line_num, line in enumerate(f):
                if not line.strip():
                    continue
                    
                try:
                    data = json.loads(line)
                    
                    # Extract content
                    facts = data.get('facts', [])
                    text = (
                        f"Subject: {data.get('subject', '')}\n"
                        f"Topic: {data.get('topic', '')}\n"
                        f"Summary: {data.get('summary', '')}\n"
                        f"Facts: {', '.join(facts)}"
                    )
                    
                    metadata = {
                        "type": "css_note",
                        "subject": str(data.get('subject', '')),
                        "topic": str(data.get('topic', '')),
                        "exam": "CSS",
                        "source": "CSS Study Materials"
                    }
                    
                    documents.append(text)
                    metadatas.append(metadata)
                    ids.append(f"css_note_{count}")
                    count += 1
                    
                    if len(documents) >= 20:
                        embeddings = self.vs.model.encode(documents, show_progress_bar=False).tolist()
                        self.vs.collection.add(
                            ids=ids,
                            documents=documents,
                            embeddings=embeddings,
                            metadatas=metadatas
                        )
                        documents, metadatas, ids = [], [], []
                        
                except json.JSONDecodeError as e:
                    print(f"[Ingestion] Error parsing line {line_num}: {e}")
                    continue
            
            # Final batch
            if documents:
                embeddings = self.vs.model.encode(documents, show_progress_bar=False).tolist()
                self.vs.collection.add(
                    ids=ids,
                    documents=documents,
                    embeddings=embeddings,
                    metadatas=metadatas
                )
        
        print(f"[Ingestion] CSS notes: {count} items added")
        return count

    def ingest_pms_notes(self, file_path):
        """Ingest PMS study notes."""
        print(f"[Ingestion] Loading PMS notes from {file_path}...")
        
        if not os.path.exists(file_path):
            print(f"[Ingestion] File not found: {file_path}")
            return 0
        
        count = 0
        with open(file_path, 'r', encoding='utf-8') as f:
            documents, metadatas, ids = [], [], []
            
            for line_num, line in enumerate(f):
                if not line.strip():
                    continue
                    
                try:
                    data = json.loads(line)
                    
                    # Extract content
                    subtopics = data.get('subtopics', [])
                    key_points = data.get('key_points', [])
                    
                    text = (
                        f"Subject: {data.get('subject', '')}\n"
                        f"Topic: {data.get('topic', '')}\n"
                        f"Summary: {data.get('summary', '')}\n"
                        f"Key Points: {', '.join(key_points)}\n"
                        f"Subtopics: {', '.join(subtopics)}"
                    )
                    
                    metadata = {
                        "type": "pms_note",
                        "subject": str(data.get('subject', '')),
                        "topic": str(data.get('topic', '')),
                        "exam": "PMS",
                        "source": "PMS Study Materials"
                    }
                    
                    documents.append(text)
                    metadatas.append(metadata)
                    ids.append(f"pms_note_{count}")
                    count += 1
                    
                    if len(documents) >= 20:
                        embeddings = self.vs.model.encode(documents, show_progress_bar=False).tolist()
                        self.vs.collection.add(
                            ids=ids,
                            documents=documents,
                            embeddings=embeddings,
                            metadatas=metadatas
                        )
                        documents, metadatas, ids = [], [], []
                        
                except json.JSONDecodeError as e:
                    print(f"[Ingestion] Error parsing line {line_num}: {e}")
                    continue
            
            # Final batch
            if documents:
                embeddings = self.vs.model.encode(documents, show_progress_bar=False).tolist()
                self.vs.collection.add(
                    ids=ids,
                    documents=documents,
                    embeddings=embeddings,
                    metadatas=metadatas
                )
        
        print(f"[Ingestion] PMS notes: {count} items added")
        return count

    def ingest_essay_files(self, essay_dir):
        """Ingest English essay files from CSS_Banks."""
        print(f"[Ingestion] Loading essay files from {essay_dir}...")
        
        if not os.path.isdir(essay_dir):
            print(f"[Ingestion] Directory not found: {essay_dir}")
            return 0
        
        count = 0
        documents, metadatas, ids = [], [], []
        
        for file_path in Path(essay_dir).glob("*.txt"):
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    topic = file_path.stem  # Filename without .txt
                    
                    text = (
                        f"Subject: English Essay\n"
                        f"Topic: {topic}\n"
                        f"Content: {content[:1000]}..."  # Limit length
                    )
                    
                    metadata = {
                        "type": "essay",
                        "subject": "English Essay",
                        "topic": topic,
                        "exam": "CSS",
                        "source": "CSS Essay Bank"
                    }
                    
                    documents.append(text)
                    metadatas.append(metadata)
                    ids.append(f"essay_{count}")
                    count += 1
                    
                    if len(documents) >= 20:
                        embeddings = self.vs.model.encode(documents, show_progress_bar=False).tolist()
                        self.vs.collection.add(
                            ids=ids,
                            documents=documents,
                            embeddings=embeddings,
                            metadatas=metadatas
                        )
                        documents, metadatas, ids = [], [], []
                        
            except Exception as e:
                print(f"[Ingestion] Error processing {file_path}: {e}")
                continue
        
        # Final batch
        if documents:
            embeddings = self.vs.model.encode(documents, show_progress_bar=False).tolist()
            self.vs.collection.add(
                ids=ids,
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas
            )
        
        print(f"[Ingestion] Essay files: {count} items added")
        return count

    def ingest_pms_definition(self):
        """Add correct PMS definition to the system."""
        print("[Ingestion] Adding PMS definition...")
        
        pms_definition = {
            "text": (
                "Provincial Management Service (PMS) is a high-level competitive examination "
                "in Pakistan used to recruit Grade-17 bureaucratic officers at the provincial level. "
                "The exam includes a written test covering general and optional subjects, a psychological test, "
                "and an interview, designed to fill top provincial administration positions. "
                "PMS is considered one of Pakistan's most prestigious civil service exams."
            ),
            "metadata": {
                "type": "definition",
                "subject": "Government & Administration",
                "topic": "Provincial Management Service (PMS)",
                "exam": "PMS",
                "source": "PMS Exam Information"
            }
        }
        
        embeddings = self.vs.model.encode([pms_definition["text"]], show_progress_bar=False).tolist()
        self.vs.collection.add(
            ids=["pms_definition"],
            documents=[pms_definition["text"]],
            embeddings=embeddings,
            metadatas=[pms_definition["metadata"]]
        )
        
        print("[Ingestion] PMS definition added")


def ingest_all_data_enhanced():
    """Ingest all data using enhanced pipeline."""
    
    # Initialize vector store (don't reset - preserve existing data)
    vs = VectorStore(db_path=r"e:\css\chroma_db", reset=False)
    
    # Initialize note generator (optional - for enrichment)
    try:
        note_gen = NoteGenerator()
        print("[Ingestion] Note generator initialized")
    except Exception as e:
        print(f"[Ingestion] Note generator not available: {e}")
        note_gen = None
    
    # Initialize enhanced ingestion
    ingestion = EnhancedIngestion(vs, note_gen)
    
    # Define file paths
    BASE_DIR = r"e:\css"
    
    # Ingest from specified sources only
    total_count = 0
    
    # 1. Ingest CSS notes
    css_notes_file = os.path.join(BASE_DIR, "css_notes_rag.jsonl")
    total_count += ingestion.ingest_css_notes(css_notes_file)
    
    # 2. Ingest PMS notes
    pms_notes_file = os.path.join(BASE_DIR, "pms_notes_rag.jsonl")
    total_count += ingestion.ingest_pms_notes(pms_notes_file)
    
    # 3. Ingest Essay files
    essay_dir = os.path.join(BASE_DIR, "CSS_Banks", "english essay")
    total_count += ingestion.ingest_essay_files(essay_dir)
    
    # 4. Add PMS definition
    ingestion.ingest_pms_definition()
    
    # Rebuild BM25 index for hybrid search
    print("[Ingestion] Rebuilding BM25 index for hybrid search...")
    vs._rebuild_bm25_index()
    
    # Final statistics
    final_count = vs.collection.count()
    print(f"\n✅ [Ingestion Complete]")
    print(f"   Total new documents ingested: {total_count}")
    print(f"   Total documents in ChromaDB: {final_count}")
    print(f"   Sources: CSS Notes + PMS Notes + Essay Files")
    
    return final_count


if __name__ == "__main__":
    ingest_all_data_enhanced()
