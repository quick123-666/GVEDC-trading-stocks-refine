import time
from typing import Dict, List, Any, Optional

DEFAULT_TOP_K = 8
DEFAULT_GRAPH_LIMIT = 50

class DualRecall:
    def __init__(self, vector_store=None, graph_store=None, graph_builder=None):
        self.vector_store = vector_store
        self.graph_store = graph_store
        self.graph_builder = graph_builder
        self.use_dual_recall = True
        self.default_top_k = DEFAULT_TOP_K

    def dual_recall(
        self,
        query: str,
        top_k: int = DEFAULT_TOP_K,
        graph_only: bool = False,
        no_graph: bool = False,
        use_hints: bool = True,
        use_parallel: bool = True
    ) -> Dict[str, Any]:
        start_time = time.time()
        results = {
            'query': query,
            'mode': 'dual',
            'graph_result': None,
            'vector_result': None,
            'expanded_query': query
        }

        if use_parallel and not graph_only and not no_graph:
            # 并行执行图谱和向量检索
            import concurrent.futures
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
                # 提交图谱检索任务
                graph_future = executor.submit(self.graph_recall, query)
                # 提交向量检索任务（使用原始查询）
                vector_future = executor.submit(self.vector_recall, query, top_k=top_k)
                
                # 等待结果
                graph_result = graph_future.result()
                vector_result = vector_future.result()
                
                results['graph_result'] = graph_result
                results['vector_result'] = vector_result
                
                # 如果启用了提示，使用图谱结果扩展查询并重新检索
                if use_hints and graph_result.get('success') and graph_result.get('hints'):
                    expanded_query = self._expand_query(query, graph_result['hints'])
                    results['expanded_query'] = expanded_query
                    # 使用扩展查询重新执行向量检索
                    results['vector_result'] = self.vector_recall(expanded_query, top_k=top_k)
        else:
            # 串行执行
            if not no_graph:
                graph_result = self.graph_recall(query)
                results['graph_result'] = graph_result

                if use_hints and graph_result.get('success') and graph_result.get('hints'):
                    expanded_query = self._expand_query(query, graph_result['hints'])
                    results['expanded_query'] = expanded_query
                else:
                    expanded_query = query

            if not graph_only:
                if no_graph:
                    expanded_query = query

                vector_result = self.vector_recall(expanded_query, top_k=top_k)
                results['vector_result'] = vector_result

        results['time_ms'] = round((time.time() - start_time) * 1000)
        results['parallel'] = use_parallel

        return results

    def graph_recall(self, query: str) -> Dict[str, Any]:
        if not self.vector_store:
            return {'success': False, 'error': 'Vector store not available'}

        try:
            graph_docs = self.vector_store.search(
                query=query,
                n_results=DEFAULT_GRAPH_LIMIT,
                collection_name="graph_nodes"
            )

            matched_nodes = []
            hints = []
            for doc in graph_docs:
                if doc.get('metadata', {}).get('type') == 'graph_node':
                    node_text = doc.get('content', '').replace('Node: ', '')
                    matched_nodes.append(node_text)
                    hints.append(node_text)

            god_nodes = [n['id'] for n in self.graph_builder.entity_extractor.identify_god_nodes([], [])] if self.graph_builder else []

            return {
                'success': True,
                'matched_nodes': matched_nodes[:10],
                'hints': hints[:5],
                'god_nodes': god_nodes,
                'total_hits': len(matched_nodes)
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def vector_recall(self, query: str, top_k: int = DEFAULT_TOP_K) -> Dict[str, Any]:
        if not self.vector_store:
            return {'success': False, 'error': 'Vector store not available'}

        try:
            docs = self.vector_store.search(
                query=query,
                n_results=top_k,
                collection_name="documents"
            )

            results = []
            for doc in docs:
                results.append({
                    'id': doc.get('id'),
                    'title': doc.get('metadata', {}).get('title', 'Untitled'),
                    'snippet': doc.get('content', '')[:200],
                    'score': 1 - (doc.get('distance', 0) or 0),
                    'metadata': doc.get('metadata', {})
                })

            return {
                'success': True,
                'results': results,
                'total': len(results)
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _expand_query(self, original_query: str, hints: List[str]) -> str:
        if not hints:
            return original_query

        hints_str = " ".join(hints[:3])
        return f"{original_query} {hints_str}"

    def graph_only_recall(self, query: str) -> Dict[str, Any]:
        return self.dual_recall(query, graph_only=True, no_graph=False)

    def vector_only_recall(self, query: str, top_k: int = DEFAULT_TOP_K) -> Dict[str, Any]:
        return self.dual_recall(query, graph_only=False, no_graph=True, top_k=top_k)

    def enable_dual_recall(self):
        self.use_dual_recall = True

    def disable_dual_recall(self):
        self.use_dual_recall = False