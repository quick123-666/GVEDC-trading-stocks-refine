import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("Testing Dual Recall functionality...")

# Test 1: Check if modules can be imported
try:
    from src.retrieval import DualRecall
    from src.storage import VectorStore
    print("✓ Modules imported successfully")
except Exception as e:
    print(f"✗ Module import failed: {e}")
    sys.exit(1)

# Test 2: Check if vector store works
try:
    vector_store = VectorStore(".")
    collections = vector_store.list_collections()
    print(f"✓ Vector store initialized, {len(collections)} collections found")
except Exception as e:
    print(f"✗ Vector store failed: {e}")
    sys.exit(1)

# Test 3: Check if dual recall works
try:
    recall = DualRecall(vector_store)
    print("✓ DualRecall initialized")
    
    # Test a simple query
    result = recall.dual_recall("vector database")
    print("✓ Dual recall executed successfully")
    print(f"  Query: {result.get('query')}")
    print(f"  Time: {result.get('time_ms', 0)}ms")
    print(f"  Graph result: {result.get('graph_result') is not None}")
    print(f"  Vector result: {result.get('vector_result') is not None}")
    
    # Test vector only
    vector_result = recall.vector_only_recall("vector database")
    print("✓ Vector only recall executed")
    
    # Test graph only
    graph_result = recall.graph_only_recall("vector database")
    print("✓ Graph only recall executed")
    
    print("\n✓ All dual recall tests passed!")
    
except Exception as e:
    print(f"✗ Dual recall test failed: {e}")
    import traceback
    traceback.print_exc()
