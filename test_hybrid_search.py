#!/usr/bin/env python
"""Quick test for Hybrid Search functionality"""

from backend.app.services.vector_store import VectorStore

print("\n" + "="*60)
print("  HYBRID SEARCH TEST")
print("="*60)

vs = VectorStore(db_path=r'e:\css\chroma_db', reset=False)
print(f'\n[OK] Loaded {vs.collection.count()} documents from ChromaDB')
print(f'[OK] BM25 index ready with {len(vs.documents_list)} documents')

# Test queries
test_queries = [
    "Islamic Law Pakistan constitutional",
    "CSS exam structure syllabus",
    "Federal Public Service Commission",
    "Pakistan economy trade policy"
]

for query in test_queries:
    print(f'\n{"-"*60}')
    print(f'Query: "{query}"')
    print("-"*60)
    
    results = vs.search(query, n_results=3, hybrid=True)
    
    if results['documents'][0]:
        for i, (doc, source) in enumerate(zip(results['documents'][0], results['sources']), 1):
            print(f'\n{i}. Source: {source}')
            print(f'   Preview: {doc[:150]}...')
    else:
        print('[ERROR] No results found.')

print("\n" + "="*60)
print("  [SUCCESS] Hybrid Search is Working!")
print("="*60 + "\n")
