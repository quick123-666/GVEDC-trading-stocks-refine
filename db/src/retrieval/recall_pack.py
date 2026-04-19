import time
from typing import Dict, List, Any, Optional

class RecallPack:
    def __init__(self):
        self.include_graph = True
        self.include_vector = True
        self.include_metadata = True
        self.max_vector_results = 8

    def format_recall_pack(
        self,
        query: str,
        dual_result: Dict[str, Any],
        mode: str = "graph_vector"
    ) -> Dict[str, Any]:
        recall_pack = {
            'query': query,
            'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ'),
            'mode': mode,
            'graph_section': None,
            'vector_section': None,
            'metadata': {
                'retrieval_mode': mode,
                'total_time_ms': dual_result.get('time_ms', 0),
                'confidence': 0.0
            }
        }

        if self.include_graph and dual_result.get('graph_result'):
            recall_pack['graph_section'] = self._format_graph_section(dual_result['graph_result'])

        if self.include_vector and dual_result.get('vector_result'):
            recall_pack['vector_section'] = self._format_vector_section(dual_result['vector_result'])

        if dual_result.get('graph_result') and dual_result.get('vector_result'):
            recall_pack['metadata']['confidence'] = 0.88
        elif dual_result.get('vector_result'):
            recall_pack['metadata']['confidence'] = 0.75

        return recall_pack

    def _format_graph_section(self, graph_result: Dict[str, Any]) -> Dict[str, Any]:
        if not graph_result.get('success'):
            return {'error': graph_result.get('error', 'Graph recall failed')}

        return {
            'matched_nodes': graph_result.get('matched_nodes', []),
            'god_nodes': graph_result.get('god_nodes', []),
            'total_hits': graph_result.get('total_hits', 0),
            'navigation': self._generate_navigation(graph_result)
        }

    def _format_vector_section(self, vector_result: Dict[str, Any]) -> Dict[str, Any]:
        if not vector_result.get('success'):
            return {'error': vector_result.get('error', 'Vector recall failed'), 'results': []}

        results = vector_result.get('results', [])
        limited_results = results[:self.max_vector_results]

        formatted_results = []
        for result in limited_results:
            formatted_results.append({
                'id': result.get('id'),
                'title': result.get('title'),
                'snippet': result.get('snippet', ''),
                'score': result.get('score', 0.0),
                'metadata': result.get('metadata', {}) if self.include_metadata else {}
            })

        return {
            'results': formatted_results,
            'total': len(formatted_results)
        }

    def _generate_navigation(self, graph_result: Dict[str, Any]) -> str:
        matched_nodes = graph_result.get('matched_nodes', [])
        god_nodes = graph_result.get('god_nodes', [])

        if matched_nodes:
            return f"Suggest exploring from: {', '.join(matched_nodes[:3])}"
        elif god_nodes:
            return f"Key nodes to explore: {', '.join(god_nodes[:3])}"
        else:
            return "No specific navigation path available"

    def to_markdown(self, recall_pack: Dict[str, Any]) -> str:
        lines = []
        lines.append("# Recall Pack")
        lines.append("")
        lines.append(f"**Query**: {recall_pack.get('query', 'N/A')}")
        lines.append(f"**Timestamp**: {recall_pack.get('timestamp', 'N/A')}")
        lines.append(f"**Mode**: {recall_pack.get('mode', 'N/A')}")
        lines.append("")

        if recall_pack.get('graph_section'):
            lines.append("## Graph Section")
            graph = recall_pack['graph_section']
            if 'error' in graph:
                lines.append(f"Error: {graph['error']}")
            else:
                lines.append(f"- Matched Nodes: {', '.join(graph.get('matched_nodes', []))}")
                lines.append(f"- God Nodes: {', '.join(graph.get('god_nodes', []))}")
                lines.append(f"- Navigation: {graph.get('navigation', 'N/A')}")
            lines.append("")

        if recall_pack.get('vector_section'):
            lines.append("## Vector Section")
            vector = recall_pack['vector_section']
            if 'error' in vector:
                lines.append(f"Error: {vector['error']}")
            else:
                lines.append(f"Total Results: {vector.get('total', 0)}")
                for i, result in enumerate(vector.get('results', []), 1):
                    lines.append(f"\n### {i}. {result.get('title', 'Untitled')}")
                    lines.append(f"- Score: {result.get('score', 0):.2f}")
                    lines.append(f"- Snippet: {result.get('snippet', '')[:100]}...")
            lines.append("")

        if recall_pack.get('metadata'):
            meta = recall_pack['metadata']
            lines.append("## Metadata")
            lines.append(f"- Retrieval Mode: {meta.get('retrieval_mode', 'N/A')}")
            lines.append(f"- Total Time: {meta.get('total_time_ms', 0)}ms")
            lines.append(f"- Confidence: {meta.get('confidence', 0):.2f}")

        return "\n".join(lines)

    def to_json_string(self, recall_pack: Dict[str, Any], indent: int = 2) -> str:
        import json
        return json.dumps(recall_pack, ensure_ascii=False, indent=indent)
