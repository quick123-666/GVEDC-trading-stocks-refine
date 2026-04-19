import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    print("[TEST] Testing imports...")
    try:
        from config import config
        print("[OK] config imported")
    except Exception as e:
        print(f"[FAIL] config import failed: {e}")
        return False

    try:
        from src.storage import VectorStore, GraphStore, FileStore
        print("[OK] storage imported")
    except Exception as e:
        print(f"[FAIL] storage import failed: {e}")
        return False

    try:
        from src.encyclopedia import EncyclopediaProcessor, DocumentReader
        print("[OK] encyclopedia imported")
    except Exception as e:
        print(f"[FAIL] encyclopedia import failed: {e}")
        return False

    try:
        from src.graph import GraphBuilder, EntityExtractor
        print("[OK] graph imported")
    except Exception as e:
        print(f"[FAIL] graph import failed: {e}")
        return False

    try:
        from src.retrieval import DualRecall, RecallPack
        print("[OK] retrieval imported")
    except Exception as e:
        print(f"[FAIL] retrieval import failed: {e}")
        return False

    return True

def test_vector_store():
    print("\n[TEST] Testing VectorStore...")
    try:
        from src.storage import VectorStore
        store = VectorStore("db")
        print(f"[OK] VectorStore initialized")
        print(f"  Collections: {store.list_collections()}")
        print(f"  Document count: {store.count('documents')}")
        return True
    except Exception as e:
        print(f"[FAIL] VectorStore test failed: {e}")
        return False

def test_graph_store():
    print("\n[TEST] Testing GraphStore...")
    try:
        from src.storage import GraphStore
        store = GraphStore("db/gvedc.db")
        print(f"[OK] GraphStore initialized")
        hierarchy = store.get_hierarchy()
        print(f"  Wings: {len(hierarchy.get('wings', []))}")
        return True
    except Exception as e:
        print(f"[FAIL] GraphStore test failed: {e}")
        return False

def test_encyclopedia():
    print("\n[TEST] Testing EncyclopediaProcessor...")
    try:
        from src.encyclopedia import EncyclopediaProcessor
        processor = EncyclopediaProcessor()
        print(f"[OK] EncyclopediaProcessor initialized")
        metadata = processor.extract_metadata("This is a test document content.", "test.txt")
        print(f"  Title: {metadata['title']}")
        print(f"  Keywords: {metadata['keywords'][:3] if metadata['keywords'] else 'none'}")
        return True
    except Exception as e:
        print(f"[FAIL] EncyclopediaProcessor test failed: {e}")
        return False

def test_dual_recall():
    print("\n[TEST] Testing DualRecall...")
    try:
        from src.retrieval import DualRecall
        recall = DualRecall()
        print(f"[OK] DualRecall initialized")
        print(f"  Dual recall mode: {recall.use_dual_recall}")
        print(f"  Default TopK: {recall.default_top_k}")
        return True
    except Exception as e:
        print(f"[FAIL] DualRecall test failed: {e}")
        return False

def main():
    print("=" * 60)
    print("GVEDC Project Test")
    print("=" * 60)

    all_passed = True
    all_passed = test_imports() and all_passed
    all_passed = test_vector_store() and all_passed
    all_passed = test_graph_store() and all_passed
    all_passed = test_encyclopedia() and all_passed
    all_passed = test_dual_recall() and all_passed

    print("\n" + "=" * 60)
    if all_passed:
        print("All tests passed!")
    else:
        print("Some tests failed!")
    print("=" * 60)

    return all_passed

if __name__ == "__main__":
    main()
