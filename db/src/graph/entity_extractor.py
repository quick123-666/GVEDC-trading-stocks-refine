import re
from typing import List, Dict, Any, Set

ENTITY_TYPES = ["PERSON", "ORG", "TECH", "CONCEPT", "LOCATION"]

ENTITY_PATTERNS = {
    "PERSON": [
        r'([A-Z][a-z]+ [A-Z][a-z]+)',
        r'([\u4e00-\u9fff]{2,4}(?:教授|博士|先生|女士|工程师))',
    ],
    "ORG": [
        r'([A-Z][a-z]+(?:Company|Corp|Inc|Ltd|University|Institute))',
        r'([\u4e00-\u9fff]{3,}(?:公司|大学|研究院|研究所|学院|医院|企业))',
    ],
    "TECH": [
        r'(?:技术|算法|系统|框架|库|数据库|语言|协议|标准)[\s:]*([\u4e00-\u9fffA-Za-z0-9]+)',
        r'([A-Z][a-z]+(?:DB|DB|AI|ML|DL|NLP|CV|KG))',
    ],
    "LOCATION": [
        r'([A-Z][a-z]+(?:City|Country|State|Province|County|District))',
        r'([\u4e00-\u9fff]{2,}(?:市|省|县|区|国家|洲))',
    ]
}

TECH_KEYWORDS = [
    "向量数据库", "图谱", "知识图谱", "机器学习", "深度学习", "神经网络",
    "人工智能", "自然语言处理", "计算机视觉", "推荐系统", "搜索引擎",
    "ChromaDB", "Neo4j", "SQLite", "PostgreSQL", "MongoDB",
    "Python", "Java", "JavaScript", "C++", "Go", "Rust",
    "TensorFlow", "PyTorch", "Keras", "Scikit-learn",
    "Transformer", "BERT", "GPT", "LLaMA",
    "HNSW", "FAISS", "Annoy", "ScaNN"
]

class EntityExtractor:
    def __init__(self):
        self.min_frequency = 2
        self.entity_types = ENTITY_TYPES

    def extract_entities(self, text: str) -> List[Dict[str, Any]]:
        entities = []
        seen_entities = {}

        for entity_type, patterns in ENTITY_PATTERNS.items():
            for pattern in patterns:
                matches = re.findall(pattern, text)
                for match in matches:
                    entity_text = match.strip() if isinstance(match, str) else match[0].strip() if isinstance(match, tuple) else str(match).strip()
                    if len(entity_text) > 1:
                        if entity_text in seen_entities:
                            seen_entities[entity_text]['count'] += 1
                        else:
                            seen_entities[entity_text] = {
                                'text': entity_text,
                                'type': entity_type,
                                'count': 1
                            }

        for keyword in TECH_KEYWORDS:
            if keyword.lower() in text.lower():
                if keyword in seen_entities:
                    seen_entities[keyword]['count'] += 1
                else:
                    seen_entities[keyword] = {
                        'text': keyword,
                        'type': 'TECH',
                        'count': 1
                    }

        return list(seen_entities.values())

    def extract_relations(self, text: str, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        relations = []
        entity_texts = [e['text'] for e in entities]

        for i, entity1 in enumerate(entity_texts):
            for j, entity2 in enumerate(entity_texts):
                if i != j:
                    co_occur = self._check_cooccurrence(text, entity1, entity2)
                    if co_occur:
                        distance = self._calculate_distance(text, entity1, entity2)
                        weight = self._calculate_weight(co_occur, distance)
                        if weight > 0.3:
                            relations.append({
                                'source': entity1,
                                'target': entity2,
                                'co_occurrence': co_occur,
                                'distance': distance,
                                'weight': weight,
                                'type': 'CO_OCCUR'
                            })

        return relations

    def _check_cooccurrence(self, text: str, entity1: str, entity2: str, window: int = 100) -> int:
        count = 0
        pos1 = text.find(entity1)
        while pos1 != -1:
            start = max(0, pos1 - window)
            end = min(len(text), pos1 + len(entity1) + window)
            window_text = text[start:end]
            if entity2 in window_text:
                count += 1
            pos1 = text.find(entity1, pos1 + 1)
        return count

    def _calculate_distance(self, text: str, entity1: str, entity2: str) -> float:
        pos1 = text.find(entity1)
        pos2 = text.find(entity2)
        if pos1 == -1 or pos2 == -1:
            return float('inf')
        return abs(pos2 - pos1) / len(text)

    def _calculate_weight(self, co_occurrence: int, distance: float) -> float:
        base_weight = 0.3
        freq_factor = min(co_occurrence / 10, 0.4)
        dist_factor = max(0, 0.3 * (1 - distance * 10))
        return min(base_weight + freq_factor + dist_factor, 1.0)

    def identify_communities(self, entities: List[Dict[str, Any]], relations: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        communities = {
            'tech_community': [],
            'person_community': [],
            'concept_community': [],
            'general_community': []
        }

        entity_map = {e['text']: e for e in entities}

        for relation in relations:
            if relation['weight'] > 0.5:
                source_type = entity_map.get(relation['source'], {}).get('type', 'CONCEPT')
                target_type = entity_map.get(relation['target'], {}).get('type', 'CONCEPT')

                if source_type == 'TECH' or target_type == 'TECH':
                    communities['tech_community'].extend([relation['source'], relation['target']])
                elif source_type == 'PERSON' or target_type == 'PERSON':
                    communities['person_community'].extend([relation['source'], relation['target']])
                elif source_type == 'CONCEPT' or target_type == 'CONCEPT':
                    communities['concept_community'].extend([relation['source'], relation['target']])

        for key in communities:
            communities[key] = list(set(communities[key]))

        return communities

    def identify_god_nodes(self, entities: List[Dict[str, Any]], relations: List[Dict[str, Any]], limit: int = 10) -> List[Dict[str, Any]]:
        if not entities:
            return []

        entity_scores = {}
        for entity in entities:
            entity_scores[entity['text']] = entity['count']

        for relation in relations:
            source = relation['source']
            target = relation['target']
            weight = relation['weight']
            if source in entity_scores:
                entity_scores[source] += weight * 2
            if target in entity_scores:
                entity_scores[target] += weight * 2

        for entity in entities:
            entity_scores[entity['text']] *= 0.6 + (0.4 if entity['type'] == 'TECH' else 0)

        sorted_entities = sorted(entity_scores.items(), key=lambda x: x[1], reverse=True)
        max_score = sorted_entities[0][1] if sorted_entities else 1

        god_nodes = []
        for text, score in sorted_entities[:limit]:
            god_nodes.append({
                'id': text,
                'score': round(score / max_score, 2) if max_score > 0 else 0
            })

        return god_nodes
