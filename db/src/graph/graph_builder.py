import json
import time
from typing import Dict, List, Any, Optional
from .entity_extractor import EntityExtractor

class GraphBuilder:
    def __init__(self, vector_store=None, graph_store=None):
        self.entity_extractor = EntityExtractor()
        self.vector_store = vector_store
        self.graph_store = graph_store

    def build_graph(self, documents: Optional[List[Dict]] = None) -> Dict[str, Any]:
        if documents is None and self.vector_store:
            docs = self.vector_store.search("", n_results=100, collection_name="documents")
            documents = [{'content': doc['content'], 'metadata': doc['metadata']} for doc in docs]

        all_entities = []
        all_relations = []
        all_communities = {}

        for doc in (documents or []):
            content = doc.get('content', '')
            entities = self.entity_extractor.extract_entities(content)
            relations = self.entity_extractor.extract_relations(content, entities)
            communities = self.entity_extractor.identify_communities(entities, relations)

            all_entities.extend(entities)
            all_relations.extend(relations)

            for key, value in communities.items():
                if key not in all_communities:
                    all_communities[key] = []
                all_communities[key].extend(value)

        for key in all_communities:
            all_communities[key] = list(set(all_communities[key]))

        unique_entities = []
        seen = set()
        for entity in all_entities:
            if entity['text'] not in seen:
                seen.add(entity['text'])
                unique_entities.append(entity)

        god_nodes = self.entity_extractor.identify_god_nodes(unique_entities, all_relations)

        graph_data = {
            'nodes': unique_entities,
            'edges': all_relations,
            'communities': all_communities,
            'god_nodes': god_nodes,
            'stats': {
                'total_nodes': len(unique_entities),
                'total_edges': len(all_relations),
                'total_communities': len(all_communities)
            },
            'generated_at': time.strftime('%Y-%m-%dT%H:%M:%SZ')
        }

        if self.vector_store:
            self._store_graph_to_vector(graph_data)

        return graph_data

    def _store_graph_to_vector(self, graph_data: Dict[str, Any]):
        if not self.vector_store:
            return

        for node in graph_data.get('nodes', []):
            self.vector_store.add_document(
                content=f"Node: {node['text']}",
                metadata={
                    'type': 'graph_node',
                    'node_type': node['type'],
                    'count': node['count'],
                    'community': node.get('community', '')
                },
                collection_name="graph_nodes"
            )

        for edge in graph_data.get('edges', []):
            self.vector_store.add_document(
                content=f"Edge: {edge['source']} -> {edge['target']}",
                metadata={
                    'type': 'graph_edge',
                    'source': edge['source'],
                    'target': edge['target'],
                    'weight': edge['weight'],
                    'relation_type': edge['type']
                },
                collection_name="graph_edges"
            )

    def get_graph_report(self, graph_data: Optional[Dict[str, Any]] = None) -> str:
        if graph_data is None:
            graph_data = self.build_graph()

        report = []
        report.append("# Graph Report")
        report.append(f"Generated: {graph_data.get('generated_at', 'N/A')}")
        report.append("")
        report.append("## Statistics")
        report.append(f"- Total Nodes: {graph_data['stats']['total_nodes']}")
        report.append(f"- Total Edges: {graph_data['stats']['total_edges']}")
        report.append(f"- Total Communities: {graph_data['stats']['total_communities']}")
        report.append("")

        report.append("## God Nodes")
        for node in graph_data.get('god_nodes', []):
            report.append(f"- {node['id']}: {node['score']}")
        report.append("")

        report.append("## Communities")
        for community_name, members in graph_data.get('communities', {}).items():
            if members:
                report.append(f"### {community_name}")
                for member in members[:10]:
                    report.append(f"- {member}")
                if len(members) > 10:
                    report.append(f"- ... and {len(members) - 10} more")
                report.append("")

        return "\n".join(report)

    def save_graph_json(self, graph_data: Dict[str, Any], output_path: str = "db/graph_output/graph.json"):
        import os
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(graph_data, f, ensure_ascii=False, indent=2)

    def load_graph_json(self, input_path: str = "db/graph_output/graph.json") -> Dict[str, Any]:
        import os
        if not os.path.exists(input_path):
            return None
        with open(input_path, 'r', encoding='utf-8') as f:
            return json.load(f)
