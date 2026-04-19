#!/usr/bin/env python3
"""
GVEDC 检索增强Pipeline
Phase 4: 检索增强 - Query处理 + 多索引 + Rerank
"""

import sys
import os
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import chromadb
    HAS_CHROMADB = True
except ImportError:
    HAS_CHROMADB = False


@dataclass
class QueryContext:
    """查询上下文"""
    original_query: str
    expanded_query: str = ""
    intent: str = ""
    weights: Dict[str, float] = None
    entities: List[str] = None
    hints: List[str] = None

    def __post_init__(self):
        if self.weights is None:
            self.weights = {"semantic": 0.4, "keyword": 0.4, "graph": 0.2}
        if self.entities is None:
            self.entities = []
        if self.hints is None:
            self.hints = []


@dataclass
class RetrievalResult:
    """检索结果"""
    query: str
    results: List[Dict]
    total: int
    retrieval_time_ms: float
    mode: str
    metadata: Dict = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class QueryProcessor:
    """查询处理器"""

    INTENT_KEYWORDS = {
        "academic_research": ["论文", "研究", "学术", "paper", "research", "arxiv", "知识", "理论"],
        "technical_implementation": ["代码", "实现", "教程", "code", "tutorial", "如何", "怎么", "方法"],
        "industry_trend": ["趋势", "最新", "发展", "2026", "未来", "预测", "市场"],
        "general": []
    }

    def __init__(self):
        self.query_cache = {}

    def process(self, query: str) -> QueryContext:
        """处理查询"""
        intent = self._recognize_intent(query)
        expanded = self._expand_query(query, intent)
        entities = self._extract_entities(query)

        return QueryContext(
            original_query=query,
            expanded_query=expanded,
            intent=intent,
            entities=entities
        )

    def _recognize_intent(self, query: str) -> str:
        """识别查询意图"""
        scores = {}

        for intent, keywords in self.INTENT_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in query.lower())
            scores[intent] = score

        if max(scores.values()) > 0:
            return max(scores.items(), key=lambda x: x[1])[0]
        return "general"

    def _expand_query(self, query: str, intent: str) -> str:
        """扩展查询"""
        expansions = {
            "academic_research": ["学术", "研究", "论文", "分析"],
            "technical_implementation": ["技术", "实现", "方法", "步骤"],
            "industry_trend": ["行业", "趋势", "发展", "动态"],
            "general": []
        }

        expand_terms = expansions.get(intent, [])
        if expand_terms:
            return f"{query} {' '.join(expand_terms)}"
        return query

    def _extract_entities(self, query: str) -> List[str]:
        """提取实体"""
        entities = []

        words = query.split()
        for word in words:
            if len(word) > 2:
                entities.append(word)

        return entities


class RetrievalPipeline:
    """检索Pipeline"""

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

        self.query_processor = QueryProcessor()
        self.cache = {}
        self.stats = {
            "total_queries": 0,
            "cache_hits": 0,
            "avg_time_ms": 0
        }

    def retrieve(self, query: str,
                top_k: int = 10,
                use_cache: bool = True,
                use_rerank: bool = True) -> RetrievalResult:
        """
        执行检索Pipeline

        Pipeline流程:
        1. Query处理 (意图识别 + 扩展)
        2. 多索引检索 (Semantic + Keyword + Graph)
        3. RRF融合
        4. Rerank重排序
        5. 结果返回
        """
        start_time = datetime.now()

        if use_cache and query in self.cache:
            self.stats["cache_hits"] += 1
            cached = self.cache[query]
            cached.metadata["cache_hit"] = True
            return cached

        ctx = self.query_processor.process(query)

        results = self._multi_index_search(ctx, top_k * 3)

        fused = self._rrf_fusion(results, ctx.weights)

        if use_rerank:
            fused = self._rerank(query, fused, top_k * 2)

        final_results = fused[:top_k]

        retrieval_time = (datetime.now() - start_time).total_seconds() * 1000

        result = RetrievalResult(
            query=query,
            results=final_results,
            total=len(final_results),
            retrieval_time_ms=retrieval_time,
            mode="enhanced_pipeline",
            metadata={
                "intent": ctx.intent,
                "expanded_query": ctx.expanded_query,
                "weights": ctx.weights,
                "cache_hit": False
            }
        )

        self.stats["total_queries"] += 1
        self._update_avg_time(retrieval_time)

        if use_cache:
            self.cache[query] = result

        return result

    def _multi_index_search(self, ctx: QueryContext, top_k: int) -> Dict[str, List[Dict]]:
        """多索引检索"""
        if not self.client:
            return {"semantic": [], "keyword": [], "graph": []}

        results = {"semantic": [], "keyword": [], "graph": []}

        try:
            semantic_coll = self.client.get_or_create_collection("documents")
            semantic_results = semantic_coll.query(
                query_texts=[ctx.expanded_query or ctx.original_query],
                n_results=top_k
            )

            for i in range(len(semantic_results["ids"][0])):
                results["semantic"].append({
                    "id": semantic_results["ids"][0][i],
                    "content": semantic_results["documents"][0][i],
                    "metadata": semantic_results["metadatas"][0][i],
                    "distance": semantic_results["distances"][0][i],
                    "score": 1 - semantic_results["distances"][0][i],
                    "source": "semantic"
                })
        except Exception as e:
            print(f"  ⚠️ 语义检索失败: {e}")

        try:
            keyword_coll = self.client.get_or_create_collection("index_keyword")
            keyword_results = keyword_coll.query(
                query_texts=[ctx.original_query],
                n_results=top_k
            )

            for i in range(len(keyword_results["ids"][0])):
                results["keyword"].append({
                    "id": keyword_results["ids"][0][i],
                    "content": keyword_results["documents"][0][i],
                    "metadata": keyword_results["metadatas"][0][i],
                    "score": 0.5,
                    "source": "keyword"
                })
        except:
            pass

        return results

    def _rrf_fusion(self, results: Dict[str, List[Dict]],
                   weights: Dict[str, float],
                   k: int = 60) -> List[Dict]:
        """RRF分数融合"""
        doc_scores = {}

        for source, docs in results.items():
            weight = weights.get(source, 1.0)
            for rank, doc in enumerate(docs):
                doc_id = doc["id"]
                rrf_score = weight * (1 / (k + rank + 1))
                doc_scores[doc_id] = doc_scores.get(doc_id, 0) + rrf_score

        sorted_ids = sorted(doc_scores.items(), key=lambda x: -x[1])

        fused = []
        for doc_id, score in sorted_ids:
            for source, docs in results.items():
                for doc in docs:
                    if doc["id"] == doc_id:
                        doc["combined_score"] = score
                        doc["sources"] = [s for s in results.keys() if any(d["id"] == doc_id for d in results[s])]
                        fused.append(doc)
                        break

        seen = set()
        unique = []
        for doc in fused:
            if doc["id"] not in seen:
                seen.add(doc["id"])
                unique.append(doc)

        return unique

    def _rerank(self, query: str, documents: List[Dict], top_k: int) -> List[Dict]:
        """重排序"""
        query_terms = set(query.lower().split())

        scored = []
        for doc in documents:
            score = 0.0
            meta = doc.get("metadata", {})

            title = (meta.get("title", "") or "").lower()
            if title:
                title_terms = set(title.split())
                score += len(query_terms & title_terms) * 0.5

            keywords = meta.get("keywords", [])
            if keywords:
                kw_str = " ".join(keywords).lower()
                kw_terms = set(kw_str.split())
                score += len(query_terms & kw_terms) * 0.3

            content = (doc.get("content", "") or "").lower()
            if content:
                content_terms = set(content.split())
                score += len(query_terms & content_terms) * 0.1

            original = doc.get("combined_score", doc.get("score", 0.5))
            doc["final_score"] = original * 0.4 + score * 0.6

            scored.append(doc)

        scored.sort(key=lambda x: x["final_score"], reverse=True)
        return scored[:top_k]

    def _update_avg_time(self, time_ms: float):
        """更新平均时间"""
        total = self.stats["total_queries"]
        current_avg = self.stats["avg_time_ms"]
        self.stats["avg_time_ms"] = (current_avg * (total - 1) + time_ms) / total

    def get_stats(self) -> Dict:
        """获取统计信息"""
        return {
            **self.stats,
            "cache_hit_rate": self.stats["cache_hits"] / max(self.stats["total_queries"], 1)
        }

    def clear_cache(self):
        """清空缓存"""
        self.cache = {}
        print("  ✅ 缓存已清空")


def demo():
    """演示检索Pipeline"""
    print("\n" + "=" * 60)
    print("🚀 GVEDC 检索增强Pipeline演示")
    print("=" * 60)

    pipeline = RetrievalPipeline()

    test_queries = [
        "如何使用Python实现机器学习",
        "2026年AI发展趋势",
        "论文检索的方法"
    ]

    for query in test_queries:
        print(f"\n查询: {query}")
        result = pipeline.retrieve(query)

        print(f"  意图: {result.metadata.get('intent', 'unknown')}")
        print(f"  扩展查询: {result.metadata.get('expanded_query', query)}")
        print(f"  结果数: {result.total}")
        print(f"  耗时: {result.retrieval_time_ms:.1f}ms")

        if result.results:
            print(f"  Top 3结果:")
            for i, r in enumerate(result.results[:3], 1):
                title = r.get("metadata", {}).get("title", "Untitled")
                score = r.get("final_score", r.get("score", 0))
                print(f"    {i}. {title} (score: {score:.3f})")

    print("\n📊 Pipeline统计:")
    stats = pipeline.get_stats()
    for k, v in stats.items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    demo()
