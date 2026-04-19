import chromadb

client = chromadb.PersistentClient(path=".")
collections = client.list_collections()

print("=" * 50)
print("GVEDC New Database Status")
print("=" * 50)
print(f"\nTotal collections: {len(collections)}\n")

total_docs = 0
for c in collections:
    col = client.get_collection(c.name)
    count = col.count()
    total_docs += count
    print(f"  {c.name}: {count} documents")

print(f"\nTotal documents: {total_docs}")
print("=" * 50)
