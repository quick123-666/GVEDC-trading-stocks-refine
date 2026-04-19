import chromadb

client = chromadb.PersistentClient(path=".")
collections = client.list_collections()

output = []
output.append("=" * 50)
output.append("GVEDC New Database Status")
output.append("=" * 50)
output.append("")
output.append(f"Total collections: {len(collections)}")
output.append("")

total_docs = 0
for c in collections:
    col = client.get_collection(c.name)
    count = col.count()
    total_docs += count
    output.append(f"  {c.name}: {count} documents")

output.append("")
output.append(f"Total documents: {total_docs}")
output.append("=" * 50)

with open("status_output.txt", "w") as f:
    f.write("\n".join(output))
