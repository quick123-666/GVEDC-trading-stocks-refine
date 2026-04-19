import sys
import os
import time
import chromadb

def save_memory(args):
    if len(args) < 4:
        print("Usage: python save_memory.py <added_by> <content> <room>")
        return
    
    added_by = args[1]
    content = args[2]
    room = args[3]
    wing = args[4] if len(args) > 4 else 'memory'
    
    # Initialize ChromaDB client
    client = chromadb.PersistentClient(path=".")
    collection = client.get_or_create_collection(name="documents")
    
    # Generate document ID
    doc_id = f"memory-{int(time.time())}-{hash(content) % 100000}"
    
    # Create metadata
    metadata = {
        "id": doc_id,
        "kind": "memory",
        "title": f"Memory from {added_by}",
        "authors": [added_by],
        "date": time.strftime("%Y-%m-%d"),
        "type": "memory",
        "abstract": content[:100] + "..." if len(content) > 100 else content,
        "keywords": ["memory", room, wing],
        "category": ["Memory"],
        "source": "trae-context-retriever",
        "room": room,
        "wing": wing,
        "added_by": added_by
    }
    
    # Add to collection
    collection.add(
        documents=[content],
        metadatas=[metadata],
        ids=[doc_id]
    )
    
    print(f"Memory saved successfully with ID: {doc_id}")
    print(f"Room: {room}, Wing: {wing}")
    print(f"Content: {content[:50]}...")

if __name__ == "__main__":
    save_memory(sys.argv)
