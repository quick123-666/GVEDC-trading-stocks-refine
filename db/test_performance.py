import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 60)
print("GVEDC Performance Test")
print("=" * 60)

def test_performance():
    try:
        from src.retrieval import DualRecall
        from src.storage import VectorStore
        
        # Initialize components
        vector_store = VectorStore(".")
        recall = DualRecall(vector_store)
        
        queries = [
            "vector database optimization",
            "knowledge graph construction",
            "ChromaDB performance",
            "document encyclopedia",
            "AI models GPT BERT"
        ]
        
        print("\nTesting retrieval performance...")
        print("-" * 60)
        
        results = []
        
        for query in queries:
            query_results = {
                "query": query,
                "dual_time": 0,
                "vector_time": 0,
                "graph_time": 0
            }
            
            # Test dual recall
            start = time.time()
            dual_result = recall.dual_recall(query)
            query_results["dual_time"] = round((time.time() - start) * 1000)
            
            # Test vector only
            start = time.time()
            vector_result = recall.vector_only_recall(query)
            query_results["vector_time"] = round((time.time() - start) * 1000)
            
            # Test graph only
            start = time.time()
            graph_result = recall.graph_only_recall(query)
            query_results["graph_time"] = round((time.time() - start) * 1000)
            
            results.append(query_results)
            
            print(f"Query: {query[:30]}...")
            print(f"  Dual: {query_results['dual_time']}ms")
            print(f"  Vector: {query_results['vector_time']}ms")
            print(f"  Graph: {query_results['graph_time']}ms")
            print("-" * 60)
        
        # Calculate average times
        avg_dual = sum(r['dual_time'] for r in results) / len(results)
        avg_vector = sum(r['vector_time'] for r in results) / len(results)
        avg_graph = sum(r['graph_time'] for r in results) / len(results)
        
        print("\nPerformance Summary:")
        print("-" * 60)
        print(f"Average Dual Recall: {round(avg_dual)}ms")
        print(f"Average Vector Only: {round(avg_vector)}ms")
        print(f"Average Graph Only: {round(avg_graph)}ms")
        
        improvement = ((avg_vector - avg_dual) / avg_vector) * 100 if avg_vector > 0 else 0
        print(f"\nPerformance Improvement: {round(improvement)}% faster than vector only")
        
        # Write results to file
        with open("performance_test_results.txt", "w") as f:
            f.write("GVEDC Performance Test Results\n")
            f.write("=" * 50 + "\n")
            for r in results:
                f.write(f"Query: {r['query']}\n")
                f.write(f"  Dual: {r['dual_time']}ms\n")
                f.write(f"  Vector: {r['vector_time']}ms\n")
                f.write(f"  Graph: {r['graph_time']}ms\n")
                f.write("-" * 50 + "\n")
            f.write(f"Average Dual: {round(avg_dual)}ms\n")
            f.write(f"Average Vector: {round(avg_vector)}ms\n")
            f.write(f"Average Graph: {round(avg_graph)}ms\n")
            f.write(f"Improvement: {round(improvement)}%\n")
        
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        return False

def main():
    success = test_performance()
    print("\n" + "=" * 60)
    if success:
        print("Performance test completed successfully!")
    else:
        print("Performance test failed!")
    print("=" * 60)

if __name__ == "__main__":
    main()
