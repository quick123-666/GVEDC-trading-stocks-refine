#!/usr/bin/env python3
"""
GVEDC 多索引管理系统
Phase 3: 多索引策略 - Semantic/Keyword/Graph 三路索引
"""

import sys
import os
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
import math

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import chromadb
    HAS_CHROMADB = True
except ImportError:
    HAS_CHROMADB = False


class MultiIndexManager:
    """多索引管理器"""

    def __init__(self, db_path: str = None):
        if db_path is None:
            self.db_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        else:
            self.db_path = db_path

        self.client = None
        if HAS_CHROMADB:
            self.client = chromadb.PersistentClient(
                path=self.db_path,
                settings=chromadb.config.Settings(allow_reset=True)
            )

        self.indexes = {}
        self.default_config = {
            "semantic": {
                "top_k": 50,
                "min_score": 0.5
            },
            "keyword": {
                "top_k": 30,
                "k1": 1.5,
                "b": 0.75
            },
            "graph": {
                "top_k": 20,
                "depth": 2
            }
        }

        self._init_indexes()

    def _init_indexes(self):
        """初始化索引集合"""
        if not self.client:
            return

        index_configs = {
            "index_semantic": {
                "index_type": "semantic",
                "description": "语义向量索引"
            },
            "index_keyword": {
                "index_type": "keyword",
                "description": "关键词BM25索引"
            },
            "index_graph": {
                "index_type": "graph",
                "description": "图谱关系索引"
            }
        }

        for name, config in index_configs.items():
            try:
                self.indexes[name] = self.client.get_or_create_collection(
                    name=name,
                    metadata=config
                )
                print(f"  ✅ {name} 索引就绪")
            except Exception as e:
                print(f"  ❌ {name} 创建失败: {e}")

    def add_document(self, doc_id: str, content: str, metadata: Dict,
                     embedding: Optional[List[float]] = None,
                     keywords: Optional[List[str]] = None,
                     entities: Optional[List[str]] = None):
        """添加文档到所有索引"""
        if not self.client:
            return

        try:
            if "index_semantic" in self.indexes and embedding:
                self.indexes["index_semantic"].add(
                    ids=[doc_id],
                    embeddings=[embedding],
                    documents=[content],
                    metadatas=[metadata]
                )

            if "index_keyword" in self.indexes:
                keyword_meta = {**metadata, "keywords": keywords or []}
                self.indexes["index_keyword"].add(
                    ids=[doc_id],
                    documents=[content],
                    metadatas=[keyword_meta]
                )

            if "index_graph" in self.indexes and entities:
                entity_meta = {**metadata, "entities": entities}
                self.indexes["index_graph"].add(
                    ids=[doc_id],
                    documents=[content],
                    metadatas=[entity_meta]
                )

        except Exception as e:
            print(f"  ⚠️  添加索引失败 {doc_id}: {e}")

    def search_semantic(self, query: str, embedding: List[float],
                        top_k: int = 50) -> List[Dict]:
        """语义向量检索"""
        if "index_semantic" not in self.indexes:
            return []

        try:
            results = self.indexes["index_semantic"].query(
                query_embeddings=[embedding],
                n_results=top_k
            )

            docs = []
            for i in range(len(results["ids"][0])):
                docs.append({
                    "id": results["ids"][0][i],
                    "content": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "distance": results["distances"][0][i],
                    "score": 1 - results["distances"][0][i]
                })
            return docs
        except:
            return []

    def search_keyword(self, query: str, top_k: int = 30) -> List[Dict]:
        """关键词BM25检索 (简化版)"""
        if "index_keyword" not in self.indexes:
            return []

        try:
            results = self.indexes["index_keyword"].query(
                query_texts=[query],
                n_results=top_k
            )

            docs = []
            for i in range(len(results["ids"][0])):
                meta = results["metadatas"][0][i]
                keywords = meta.get("keywords", [])

                score = self._calculate_bm25_score(query, keywords)

                docs.append({
                    "id": results["ids"][0][i],
                    "content": results["documents"][0][i],
                    "metadata": meta,
                    "score": score,
                    "match_type": "keyword"
                })

            docs.sort(key=lambda x: x["score"], reverse=True)
            return docs[:top_k]
        except:
            return []

    def _calculate_bm25_score(self, query: str, keywords: List[str]) -> float:
        """简化的BM25评分"""
        query_terms = query.lower().split()
        keyword_str = " ".join(keywords).lower()

        matches = sum(1 for term in query_terms if term in keyword_str)
        return matches / len(query_terms) if query_terms else 0

    def search_graph(self, query: str, entities: List[str],
                     depth: int = 2, top_k: int = 20) -> List[Dict]:
        """图谱检索"""
        if "index_graph" not in self.indexes:
            return []

        try:
            results = self.indexes["index_graph"].query(
                query_texts=[query],
                n_results=top_k * 2
            )

            docs = []
            for i in range(len(results["ids"][0])):
                meta = results["metadatas"][0][i]
                doc_entities = meta.get("entities", [])

                entity_overlap = len(set(entities) & set(doc_entities))
                score = entity_overlap / max(len(entities), 1)

                if score > 0:
                    docs.append({
                        "id": results["ids"][0][i],
                        "content": results["documents"][0][i],
                        "metadata": meta,
                        "score": score,
                        "match_type": "graph"
                    })

            docs.sort(key=lambda x: x["score"], reverse=True)
            return docs[:top_k]
        except:
            return []

    def hybrid_search(self, query: str,
                      embedding: Optional[List[float]] = None,
                      entities: Optional[List[str]] = None,
                      weights: Optional[Dict[str, float]] = None,
                      top_k: int = 10,
                      fusion_k: int = 60) -> List[Dict]:
        """
        混合检索 - 多索引融合

        Args:
            query: 查询文本
            embedding: 向量嵌入
            entities: 实体列表
            weights: 权重 {semantic, keyword, graph}
            top_k: 返回数量
            fusion_k: RRF融合参数
        """
        if weights is None:
            weights = {"semantic": 0.4, "keyword": 0.4, "graph": 0.2}

        results = {
            "semantic": [],
            "keyword": [],
            "graph": []
        }

        if embedding:
            results["semantic"] = self.search_semantic(
                query, embedding,
                top_k=top_k * 3
            )

        results["keyword"] = self.search_keyword(query, top_k=top_k * 3)

        if entities:
            results["graph"] = self.search_graph(
                query, entities,
                top_k=top_k * 2
            )

        fused_scores = self._reciprocal_rank_fusion(results, weights, fusion_k)

        final_results = []
        for doc_id, combined_score in fused_scores[:top_k]:
            for source in ["semantic", "keyword", "graph"]:
                for doc in results[source]:
                    if doc["id"] == doc_id:
                        doc["combined_score"] = combined_score
                        doc["sources"] = [s for s in ["semantic", "keyword", "graph"]
                                         if any(d["id"] == doc_id for d in results[s])]
                        final_results.append(doc)
                        break

        seen = set()
        unique_results = []
        for doc in final_results:
            if doc["id"] not in seen:
                seen.add(doc["id"])
                unique_results.append(doc)

        return unique_results[:top_k]

    def _reciprocal_rank_fusion(self, results: Dict[str, List[Dict]],
                                weights: Dict[str, float],
                                k: int = 60) -> List[Tuple[str, float]]:
        """倒数排名融合 (RRF)"""
        doc_scores = {}

        for source, docs in results.items():
            weight = weights.get(source, 1.0)
            for rank, doc in enumerate(docs):
                doc_id = doc["id"]
                rrf_score = weight * (1 / (k + rank + 1))
                doc_scores[doc_id] = doc_scores.get(doc_id, 0) + rrf_score

        sorted_docs = sorted(doc_scores.items(), key=lambda x: -x[1])
        return sorted_docs

    def get_index_stats(self) -> Dict:
        """获取索引统计"""
        stats = {
            "indexes": {},
            "total_documents": 0
        }

        for name, coll in self.indexes.items():
            try:
                count = coll.count()
                stats["indexes"][name] = count
                stats["total_documents"] += count
            except:
                stats["indexes"][name] = 0

        return stats


class Reranker:
    """结果重排序器 (简化版 - 实际生产应使用BGE-Reranker)"""

    def __init__(self):
        self.min_score_threshold = 0.3

    def rerank(self, query: str, documents: List[Dict],
               top_k: int = 10) -> List[Dict]:
        """
        重排序检索结果

        简化策略:
        1. 标题匹配优先
        2. 关键词重叠
        3. 语义相似度
        """
        query_terms = set(query.lower().split())

        scored_docs = []
        for doc in documents:
            score = 0.0
            metadata = doc.get("metadata", {})

            title = metadata.get("title", "").lower()
            if title:
                title_terms = set(title.split())
                title_overlap = len(query_terms & title_terms)
                score += title_overlap * 0.5

            keywords = metadata.get("keywords", [])
            if isinstance(keywords, list):
                keyword_set = set(" ".join(keywords).lower().split())
                keyword_overlap = len(query_terms & keyword_set)
                score += keyword_overlap * 0.3

            content = doc.get("content", "").lower()
            if content:
                content_terms = set(content.split())
                content_overlap = len(query_terms & content_terms)
                score += content_overlap * 0.1

            original_score = doc.get("score", 0.5)
            combined = original_score * 0.5 + score * 0.5

            doc["rerank_score"] = combined
            doc["rerank_components"] = {
                "title_match": title_overlap if title else 0,
                "keyword_match": keyword_overlap if keywords else 0
            }
            scored_docs.append(doc)

        scored_docs.sort(key=lambda x: x["rerank_score"], reverse=True)
        return scored_docs[:top_k]


def main():
    print("\n" + "=" * 60)
    print("🚀 GVEDC 多索引管理系统 v1.0")
    print("=" * 60)

    manager = MultiIndexManager()

    print("\n📊 索引状态:")
    stats = manager.get_index_stats()
    for name, count in stats["indexes"].items():
        print(f"  {name}: {count} 文档")

    print("\n✅ 多索引管理系统就绪")
    print("\n可用方法:")
    print("  - add_document(): 添加文档到多索引")
    print("  - search_semantic(): 语义检索")
    print("  - search_keyword(): 关键词检索")
    print("  - search_graph(): 图谱检索")
    print("  - hybrid_search(): 混合检索")
    print("  - Reranker.rerank(): 重排序")


if __name__ == "__main__":
    main()
