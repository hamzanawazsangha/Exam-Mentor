import sqlite3
import os
import chromadb
import sys

def check_db():
    print("--- SQLITE CHECK ---")
    db_path = r"e:\css - Copy\portal.db"
    if not os.path.exists(db_path):
        print(f"ERROR: {db_path} not found")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(mock_tests)")
    columns = [col[1] for col in cursor.fetchall()]
    print(f"Columns in mock_tests: {columns}")
    conn.close()

def check_chroma():
    print("\n--- CHROMA CHECK ---")
    db_path = r"e:\css - Copy\chroma_db_v2"
    if not os.path.exists(db_path):
        print(f"ERROR: {db_path} not found")
        return
    
    try:
        client = chromadb.PersistentClient(path=db_path)
        print(f"Chroma client connected to {db_path}")
        collections = client.list_collections()
        print(f"Collections: {[c.name for c in collections]}")
        for c in collections:
            print(f"Collection '{c.name}' count: {c.count()}")
    except Exception as e:
        print(f"CHROMA ERROR: {e}")

if __name__ == "__main__":
    check_db()
    check_chroma()
