import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 60)
print("Testing GVEDC Features")
print("=" * 60)

def test_encyclopedia():
    print("\n[1] Testing Encyclopedia Feature...")
    try:
        from src.encyclopedia import EncyclopediaProcessor
        enc = EncyclopediaProcessor()
        
        # Test metadata extraction
        content = "This is a test document about vector databases and knowledge graphs. ChromaDB is a vector database. GPT and BERT are AI models."
        metadata = enc.extract_metadata(content, "test_document.md")
        
        print("  [OK] EncyclopediaProcessor initialized")
        print(f"  [OK] Title: {metadata.get('title')}")
        print(f"  [OK] Keywords: {metadata.get('keywords', [])[:3]}")
        print(f"  [OK] Category: {metadata.get('category')}")
        print(f"  [OK] Abstract: {metadata.get('abstract', '')[:50]}...")
        
        return True
    except Exception as e:
        print(f"  [FAIL] {e}")
        return False

def test_dual_recall():
    print("\n[2] Testing Dual Recall Feature...")
    try:
        from src.retrieval import DualRecall, RecallPack
        from src.storage import VectorStore
        
        # Initialize components
        vector_store = VectorStore(".")
        recall = DualRecall(vector_store)
        rp = RecallPack()
        
        # Test dual recall
        query = "vector database optimization"
        result = recall.dual_recall(query, top_k=3)
        
        print("  [OK] DualRecall initialized")
        print(f"  [OK] Query: {result.get('query')}")
        print(f"  [OK] Expanded query: {result.get('expanded_query')}")
        print(f"  [OK] Graph result: {result.get('graph_result') is not None}")
        print(f"  [OK] Vector result: {result.get('vector_result') is not None}")
        
        # Test Recall Pack
        recall_pack = rp.format_recall_pack(query, result)
        print(f"  [OK] Recall Pack created: {recall_pack is not None}")
        
        return True
    except Exception as e:
        print(f"  [FAIL] {e}")
        return False

def main():
    results = []
    results.append(test_encyclopedia())
    results.append(test_dual_recall())
    
    print("\n" + "=" * 60)
    print("Test Results:")
    print("=" * 60)
    
    features = ["Encyclopedia Feature", "Dual Recall Feature"]
    for feature, result in zip(features, results):
        status = "PASS" if result else "FAIL"
        print(f"  {feature}: {status}")
    
    all_passed = all(results)
    print("\n" + "=" * 60)
    if all_passed:
        print("All features tested successfully!")
    else:
        print("Some features failed!")
    print("=" * 60)
    
    # Write results to file
    with open("feature_test_results.txt", "w") as f:
        f.write("GVEDC Feature Test Results\n")
        f.write("=" * 50 + "\n")
        for feature, result in zip(features, results):
            f.write(f"{feature}: {'PASS' if result else 'FAIL'}\n")
        f.write("=" * 50 + "\n")
        f.write(f"Overall: {'ALL PASS' if all_passed else 'SOME FAIL'}\n")

if __name__ == "__main__":
    main()
