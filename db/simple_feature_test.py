import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("Testing GVEDC Features...")
print("-" * 50)

try:
    from src.encyclopedia import EncyclopediaProcessor
    print("1. Encyclopedia Feature:")
    enc = EncyclopediaProcessor()
    content = "This is a test document about vector databases and knowledge graphs."
    metadata = enc.extract_metadata(content, "test.md")
    print("   ✓ Initialized")
    print(f"   ✓ Title: {metadata.get('title')}")
    print(f"   ✓ Keywords: {metadata.get('keywords', [])[:3]}")
except Exception as e:
    print(f"1. Encyclopedia Feature: FAILED - {e}")

try:
    from src.retrieval import DualRecall, RecallPack
    print("2. Dual Recall Feature:")
    recall = DualRecall()
    rp = RecallPack()
    result = recall.dual_recall("vector database")
    print("   ✓ Initialized")
    print(f"   ✓ Query: {result.get('query')}")
    print(f"   ✓ Graph result: {result.get('graph_result') is not None}")
    print(f"   ✓ Vector result: {result.get('vector_result') is not None}")
except Exception as e:
    print(f"2. Dual Recall Feature: FAILED - {e}")

print("-" * 50)
print("Test completed!")
