import chromadb
from chromadb.utils import embedding_functions

client = chromadb.PersistentClient(path=r"e:\css\chroma_db")
ef = embedding_functions.DefaultEmbeddingFunction()
collection = client.get_or_create_collection(name="exam_knowledge", embedding_function=ef)

print("Attempting to add one test document...")
collection.add(
    documents=["This is a test document about CSS preparation."],
    metadatas=[{"type": "test"}],
    ids=["test_1"]
)
print(f"Count: {collection.count()}")
