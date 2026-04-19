import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("Testing GVEDC Features...")
print("-")

try:
    from src.encyclopedia import EncyclopediaProcessor
    print("1. Encyclopedia Feature:")
    enc = EncyclopediaProcessor()
    content = "This is a test document about vector databases and knowledge graphs."
    metadata = enc.extract_metadata(content, "test.md")
    print("   OK: Initialized")
    print("   Title: " + str(metadata.get('title')))
    print("   Keywords: " + str(metadata.get('keywords', [])[:3]))
    print("   Category: " + str(metadata.get('category')))
    print("   OK: Encyclopedia feature working")
except Exception as e:
    print("1. Encyclopedia Feature: FAILED - " + str(e))

try:
    from src.retrieval import DualRecall, RecallPack
    print("2. Dual Recall Feature:")
    recall = DualRecall()
    rp = RecallPack()
    result = recall.dual_recall("vector database")
    print("   OK: Initialized")
    print("   Query: " + str(result.get('query')))
    print("   Graph result: " + str(result.get('graph_result') is not None))
    print("   Vector result: " + str(result.get('vector_result') is not None))
    print("   OK: Dual recall feature working")
except Exception as e:
    print("2. Dual Recall Feature: FAILED - " + str(e))

print("-")
print("Test completed!")
