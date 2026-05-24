import chromadb
import json
import os
import shutil
from sentence_transformers import SentenceTransformer
from rank_bm25 import BM25Okapi
import pickle

# Singleton model — loaded once, shared across all VectorStore instances
_model = None

def _get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer('all-MiniLM-L6-v2')
    return _model


class VectorStore:
    def __init__(self, db_path="./chroma_db_v2", reset=False):
        """
        Args:
            db_path: Path to the ChromaDB persistent directory.
            reset:   If True, wipe and recreate the collection (only used during ingestion).
                     NEVER set to True in the Flask app — it destroys indexed data.
        """
        self.db_path = db_path
        self.client = chromadb.PersistentClient(path=db_path)
        self.model = _get_model()
        
        # BM25 index for keyword-based search
        self.bm25_index = None
        self.documents_list = []  # Keep track of documents for BM25
        self.document_ids = []  # Map BM25 results back to ChromaDB IDs
        self.bm25_cache_path = os.path.join(db_path, "bm25_index.pkl")

        if reset:
            try:
                self.client.delete_collection("exam_knowledge")
                print("[VectorStore] Collection reset.")
            except Exception:
                pass

        self.collection = self.client.get_or_create_collection(name="exam_knowledge")
        print(f"[VectorStore] Loaded collection with {self.collection.count()} documents.")
        
        # Load BM25 index from cache if available
        self._load_bm25_index()

    def _tokenize(self, text):
        """Simple tokenization: lowercase and split by whitespace."""
        return text.lower().split()

    def _load_bm25_index(self):
        """Load BM25 index from cache if it exists."""
        if os.path.exists(self.bm25_cache_path):
            try:
                with open(self.bm25_cache_path, 'rb') as f:
                    cache = pickle.load(f)
                    self.bm25_index = cache['bm25']
                    self.documents_list = cache['documents']
                    self.document_ids = cache['ids']
                    print(f"[VectorStore] Loaded BM25 index with {len(self.documents_list)} documents.")
            except Exception as e:
                print(f"[VectorStore] Failed to load BM25 cache: {e}. Will rebuild on next ingest.")

    def _save_bm25_index(self):
        """Save BM25 index to cache for faster startup."""
        try:
            os.makedirs(self.db_path, exist_ok=True)
            with open(self.bm25_cache_path, 'wb') as f:
                pickle.dump({
                    'bm25': self.bm25_index,
                    'documents': self.documents_list,
                    'ids': self.document_ids
                }, f)
            print(f"[VectorStore] Saved BM25 index to cache.")
        except Exception as e:
            print(f"[VectorStore] Failed to save BM25 cache: {e}")

    def _rebuild_bm25_index(self):
        """Rebuild BM25 index from ChromaDB documents."""
        print("[VectorStore] Rebuilding BM25 index...")
        self.documents_list = []
        self.document_ids = []
        
        # Fetch all documents from ChromaDB
        all_docs = self.collection.get()
        
        if all_docs and all_docs['documents']:
            for i, doc in enumerate(all_docs['documents']):
                tokenized = self._tokenize(doc)
                self.documents_list.append(tokenized)
                self.document_ids.append(all_docs['ids'][i])
            
            # Create BM25 index
            self.bm25_index = BM25Okapi(self.documents_list)
            self._save_bm25_index()
            print(f"[VectorStore] BM25 index rebuilt with {len(self.documents_list)} documents.")
        else:
            print("[VectorStore] No documents in collection, skipping BM25 rebuild.")

    def _get_embeddings(self, texts):
        return self.model.encode(texts, show_progress_bar=False).tolist()

    def add_jsonl(self, file_path, doc_type):
        """Ingest a JSONL file into ChromaDB. Only call from the ingestion script."""
        if not os.path.exists(file_path):
            print(f"[VectorStore] File not found: {file_path}")
            return

        with open(file_path, 'r', encoding='utf-8') as f:
            documents, metadatas, ids = [], [], []
            count = 0

            for line in f:
                if not line.strip():
                    continue
                data = json.loads(line)

                if doc_type == "notes":
                    facts = data.get('facts', [])
                    text = (
                        f"Subject: {data.get('subject', '')}\n"
                        f"Topic: {data.get('topic', '')}\n"
                        f"Summary: {data.get('summary', '')}\n"
                        f"Facts: {', '.join(facts)}"
                    )
                    metadata = {
                        "type": "note",
                        "subject": str(data.get('subject', '')),
                        "topic": str(data.get('topic', '')),
                        "exam": str(data.get('exam_type', '')),
                        "source": f"{data.get('subject', 'Unknown')} - {data.get('topic', 'General')}"
                    }
                else:  # past_paper
                    text = str(data.get('content', ''))
                    metadata = {
                        "type": "past_paper",
                        "source": str(data.get('source', 'Past Paper')),
                        "subject": "Past Paper",
                        "topic": "General"
                    }

                documents.append(text)
                metadatas.append(metadata)
                ids.append(f"{doc_type}_{count}_{os.path.basename(file_path)}")
                count += 1

                if len(documents) >= 10:
                    embeddings = self._get_embeddings(documents)
                    self.collection.add(
                        documents=documents, metadatas=metadatas,
                        ids=ids, embeddings=embeddings
                    )
                    documents, metadatas, ids = [], [], []
                    print(f"  Added {count} {doc_type} docs...")

            if documents:
                embeddings = self._get_embeddings(documents)
                self.collection.add(
                    documents=documents, metadatas=metadatas,
                    ids=ids, embeddings=embeddings
                )
                print(f"  Finalized {count} {doc_type} docs.")
        
        # Rebuild BM25 index after ingestion
        self._rebuild_bm25_index()

    def search(self, query, n_results=3, hybrid=True):
        """
        Search against the indexed knowledge base using hybrid search (BM25 + semantic).
        
        Args:
            query: Search query string
            n_results: Number of results to return
            hybrid: If True, use hybrid search (BM25 + semantic). If False, semantic only.
            
        Returns:
            Dictionary with documents, metadatas, and source attribution
        """
        if self.collection.count() == 0:
            return {"documents": [[]], "metadatas": [[]], "sources": []}
        
        if not hybrid or self.bm25_index is None:
            # Fallback to semantic search only
            return self._semantic_search(query, n_results)
        
        return self._hybrid_search(query, n_results)

    def _semantic_search(self, query, n_results):
        """Pure semantic search using embeddings."""
        query_embeddings = self._get_embeddings([query])
        results = self.collection.query(
            query_embeddings=query_embeddings,
            n_results=min(n_results, self.collection.count())
        )
        
        # Add source attribution
        sources = []
        if results.get('metadatas') and results['metadatas'][0]:
            sources = [meta.get('source', 'Unknown Source') for meta in results['metadatas'][0]]
        
        results['sources'] = sources
        return results

    def _hybrid_search(self, query, n_results):
        """Hybrid search combining BM25 (keyword) and semantic search."""
        # ──── BM25 Search (Keyword-based) ────
        tokenized_query = self._tokenize(query)
        bm25_scores = self.bm25_index.get_scores(tokenized_query)
        
        # Convert to list if numpy array
        if hasattr(bm25_scores, 'tolist'):
            bm25_scores = bm25_scores.tolist()
        
        # Get top results from BM25
        top_bm25_indices = sorted(
            range(len(bm25_scores)),
            key=lambda i: bm25_scores[i],
            reverse=True
        )[:n_results * 2]  # Get more to merge with semantic results
        
        # ──── Semantic Search (Embedding-based) ────
        query_embeddings = self._get_embeddings([query])
        semantic_results = self.collection.query(
            query_embeddings=query_embeddings,
            n_results=min(n_results * 2, self.collection.count())
        )
        
        # ──── Merge Results ────
        merged_results = {}  # doc_id -> (score, metadata, document)
        
        # Add BM25 results with normalized scores
        max_bm25_score = max(bm25_scores) if bm25_scores and len(bm25_scores) > 0 else 1
        for idx in top_bm25_indices:
            if idx < len(self.document_ids):
                doc_id = self.document_ids[idx]
                normalized_bm25 = bm25_scores[idx] / (max_bm25_score or 1)
                
                if doc_id not in merged_results:
                    merged_results[doc_id] = {'bm25': normalized_bm25, 'semantic': 0}
                else:
                    merged_results[doc_id]['bm25'] = normalized_bm25
        
        # Add semantic results with normalized distances
        if semantic_results.get('ids') and semantic_results['ids'][0]:
            for i, doc_id in enumerate(semantic_results['ids'][0]):
                # ChromaDB returns distances; lower is better. Convert to similarity.
                distance = semantic_results.get('distances', [[]])[0][i] if semantic_results.get('distances') else 0
                normalized_semantic = 1 / (1 + distance)  # Convert distance to similarity
                
                if doc_id not in merged_results:
                    merged_results[doc_id] = {'bm25': 0, 'semantic': normalized_semantic}
                else:
                    merged_results[doc_id]['semantic'] = normalized_semantic
        
        # Calculate combined score (weighted average: 50% BM25, 50% semantic)
        scored_results = []
        for doc_id, scores in merged_results.items():
            combined_score = 0.5 * scores['bm25'] + 0.5 * scores['semantic']
            scored_results.append((doc_id, combined_score))
        
        # Sort by combined score and get top n_results
        scored_results.sort(key=lambda x: x[1], reverse=True)
        top_docs = [doc_id for doc_id, _ in scored_results[:n_results]]
        
        # ──── Fetch full document details ────
        final_documents = []
        final_metadatas = []
        final_sources = []
        
        all_docs = self.collection.get()
        doc_id_to_content = {doc_id: (doc, meta) for doc_id, doc, meta in 
                            zip(all_docs['ids'], all_docs['documents'], all_docs['metadatas'])}
        
        for doc_id in top_docs:
            if doc_id in doc_id_to_content:
                doc_content, metadata = doc_id_to_content[doc_id]
                final_documents.append(doc_content)
                final_metadatas.append(metadata)
                final_sources.append(metadata.get('source', 'Unknown Source'))
        
        return {
            "documents": [final_documents] if final_documents else [[]],
            "metadatas": [final_metadatas] if final_metadatas else [[]],
            "sources": final_sources
        }


if __name__ == "__main__":
    # Run this script directly to (re)ingest all data.
    import time
    
    db_path = r"e:\css - Copy\chroma_db_v2"
    
    # Clean up old database
    if os.path.exists(db_path):
        try:
            shutil.rmtree(db_path)
            print(f"[Setup] Removed old database at {db_path}")
            time.sleep(1)  # Let file system settle
        except Exception as e:
            print(f"[Setup] Could not remove old database: {e}")
    
    # Create fresh database
    os.makedirs(db_path, exist_ok=True)
    vs = VectorStore(db_path=db_path, reset=False)

    print("\nIngesting master notes...")
    vs.add_jsonl(r"e:\css - Copy\master_notes_rag.jsonl", "notes")

    print("\nIngesting past papers...")
    vs.add_jsonl(r"e:\css - Copy\past_papers_extracted.jsonl", "past_paper")

    print(f"\n✅ Done. Total docs in DB: {vs.collection.count()}")
    print(f"✅ BM25 index contains: {len(vs.documents_list)} documents")
    
    # Quick test
    print("\n─── Testing Hybrid Search ───")
    test_query = "Islamic Sharia law Pakistan"
    results = vs.search(test_query, n_results=3, hybrid=True)
    if results['documents'][0]:
        print(f"\nResults for: '{test_query}'")
        for i, (doc, meta, source) in enumerate(zip(results['documents'][0], results['metadatas'][0], results['sources']), 1):
            print(f"\n{i}. Source: {source}")
            print(f"   Preview: {doc[:150]}...")
    else:
        print("No results found.")
