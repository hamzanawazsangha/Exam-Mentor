from app.services.vector_store import VectorStore

vs = VectorStore(r"e:\css\chroma_db")
r = vs.search("CPEC Pakistan economy", n_results=2)

print("=== RAG SEARCH RESULT ===")
for i, (doc, meta) in enumerate(zip(r["documents"][0], r["metadatas"][0])):
    print(f"[{i+1}] type={meta.get('type')} subject={meta.get('subject', '')}")
    print(doc[:200])
    print()
print(f"=== TOTAL DOCS IN DB: {vs.collection.count()} ===")
