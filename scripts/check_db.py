import chromadb

client = chromadb.PersistentClient(path=r"e:\css\chroma_db")
collection = client.get_collection("exam_knowledge")
print(f"Total documents in collection: {collection.count()}")
