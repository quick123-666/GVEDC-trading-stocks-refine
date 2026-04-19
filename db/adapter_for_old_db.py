#!/usr/bin/env python3
"""
GVEDC 原有插件适配器层
连接老数据库 + 分层策略系统 (GVEDC-trading-stocks-refine)
"""

import sys
import os
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import chromadb
    HAS_CHROMADB = True
except ImportError:
    HAS_CHROMADB = False


@dataclass
class StrategyContext:
    """策略上下文 - 来自 layered_strategy.py"""
    layer: str
    strategy: str
    params: Dict[str, Any]


@dataclass
class FeedbackData:
    """反馈数据"""
    query: str
    results: List[Dict]
    clicked_ids: List[str]
    satisfaction: float
    dwell_time: float


class OldDatabaseAdapter:
    """
    老数据库适配器
    让 GVEDC-trading-stocks-refine 的分层策略系统能够使用老数据库
    """

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

        self.collections = {}
        self.feedback_history = []
        self.strategy_history = []

    def initialize(self):
        """初始化适配器"""
        print("\n" + "=" * 60)
        print("🔌 GVEDC 老数据库适配器初始化")
        print("=" * 60)

        if not self.client:
            print("  ❌ ChromaDB 未连接")
            return False

        base_collections = ["documents", "graph_nodes", "graph_edges", "recalls"]
        for name in base_collections:
            try:
                self.collections[name] = self.client.get_or_create_collection(name)
                print(f"  ✅ {name} 集合就绪")
            except Exception as e:
                print(f"  ❌ {name} 初始化失败: {e}")

        print(f"  ✅ 适配器初始化完成")
        return True

    def get_collection(self, name: str):
        """获取集合"""
        if name not in self.collections:
            self.collections[name] = self.client.get_or_create_collection(name)
        return self.collections[name]

    def execute_with_strategy(self, query: str, strategy: StrategyContext) -> Dict:
        """
        执行带策略的检索

        Args:
            query: 查询文本
            strategy: 来自分层策略系统的策略上下文

        Returns:
            检索结果
        """
        print(f"\n📡 执行策略: {strategy.layer} - {strategy.strategy}")

        if strategy.layer == "top":
            return self._execute_top_strategy(query, strategy)
        elif strategy.layer == "middle":
            return self._execute_middle_strategy(query, strategy)
        else:
            return self._execute_bottom_strategy(query, strategy)

    def _execute_top_strategy(self, query: str, strategy: StrategyContext) -> Dict:
        """顶层策略 - 图谱导航优先"""
        print(f"  [顶层] 图谱导航检索")

        try:
            graph_coll = self.get_collection("graph_nodes")
            results = graph_coll.query(
                query_texts=[query],
                n_results=20
            )

            nodes = []
            for i in range(len(results["ids"][0])):
                nodes.append({
                    "id": results["ids"][0][i],
                    "content": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i]
                })

            return {
                "success": True,
                "mode": "top_graph",
                "results": nodes,
                "total": len(nodes)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _execute_middle_strategy(self, query: str, strategy: StrategyContext) -> Dict:
        """中间层策略 - 混合检索"""
        print(f"  [中间层] 混合检索: {strategy.strategy}")

        try:
            doc_coll = self.get_collection("documents")
            results = doc_coll.query(
                query_texts=[query],
                n_results=30
            )

            docs = []
            for i in range(len(results["ids"][0])):
                docs.append({
                    "id": results["ids"][0][i],
                    "content": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "score": 1 - results["distances"][0][i]
                })

            return {
                "success": True,
                "mode": "middle_hybrid",
                "results": docs,
                "total": len(docs)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _execute_bottom_strategy(self, query: str, strategy: StrategyContext) -> Dict:
        """细节层策略 - 完整双检索 + Rerank"""
        print(f"  [细节层] 完整双检索: {strategy.strategy}")

        try:
            doc_coll = self.get_collection("documents")
            results = doc_coll.query(
                query_texts=[query],
                n_results=50
            )

            docs = []
            for i in range(len(results["ids"][0])):
                docs.append({
                    "id": results["ids"][0][i],
                    "content": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "score": 1 - results["distances"][0][i]
                })

            docs = self._rerank_results(query, docs)

            return {
                "success": True,
                "mode": "bottom_full",
                "results": docs[:10],
                "total": len(docs)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _rerank_results(self, query: str, results: List[Dict]) -> List[Dict]:
        """重排序"""
        query_terms = set(query.lower().split())

        for doc in results:
            meta = doc.get("metadata", {})
            score = 0.0

            title = (meta.get("title", "") or "").lower()
            if title:
                score += len(query_terms & set(title.split())) * 0.5

            keywords = meta.get("keywords", [])
            if keywords:
                kw_str = " ".join(keywords).lower()
                score += len(query_terms & set(kw_str.split())) * 0.3

            doc["rerank_score"] = doc.get("score", 0.5) * 0.5 + score * 0.5

        results.sort(key=lambda x: x.get("rerank_score", 0), reverse=True)
        return results

    def collect_feedback(self, feedback: FeedbackData):
        """收集反馈供策略迭代"""
        print(f"\n📥 收集反馈: {feedback.query}")

        quality_score = self._calculate_quality_score(feedback)

        self.feedback_history.append({
            "query": feedback.query,
            "quality_score": quality_score,
            "timestamp": datetime.now().isoformat(),
            "result_count": len(feedback.results),
            "clicked_count": len(feedback.clicked_ids)
        })

        if len(self.feedback_history) > 100:
            self.feedback_history = self.feedback_history[-100:]

        self._store_feedback_in_db(feedback, quality_score)

        print(f"  质量得分: {quality_score:.2f}")

        if quality_score < 0.5:
            self._suggest_strategy_adjustment()

        return quality_score

    def _calculate_quality_score(self, feedback: FeedbackData) -> float:
        """计算质量得分"""
        if not feedback.results:
            return 0.0

        click_rate = len(feedback.clicked_ids) / len(feedback.results) if feedback.results else 0
        satisfaction = feedback.satisfaction / 5.0 if feedback.satisfaction else 0.5

        return click_rate * 0.4 + satisfaction * 0.6

    def _store_feedback_in_db(self, feedback: FeedbackData, quality_score: float):
        """存储反馈到数据库"""
        try:
            coll = self.get_collection("recalls")

            doc = {
                "query": feedback.query,
                "quality_score": quality_score,
                "clicked_ids": ",".join(feedback.clicked_ids) if feedback.clicked_ids else "",
                "satisfaction": feedback.satisfaction,
                "timestamp": datetime.now().isoformat()
            }

            coll.add(
                documents=[f"Query: {feedback.query}, Score: {quality_score}"],
                metadatas=[doc],
                ids=[f"feedback_{datetime.now().strftime('%Y%m%d_%H%M%S')}"]
            )
        except Exception as e:
            print(f"  ⚠️ 反馈存储失败: {e}")

    def _suggest_strategy_adjustment(self):
        """建议策略调整"""
        recent_scores = [f["quality_score"] for f in self.feedback_history[-5:]]
        avg_score = sum(recent_scores) / len(recent_scores) if recent_scores else 0.5

        print(f"\n💡 策略调整建议:")

        if avg_score < 0.3:
            print("  ⚠️ 质量持续较低，建议:")
            print("     1. 切换到更细粒度的检索策略")
            print("     2. 增加图谱导航权重")
            print("     3. 重新训练嵌入模型")
        elif avg_score < 0.5:
            print("  ⚡ 质量一般，建议:")
            print("     1. 启用Rerank重排序")
            print("     2. 调整语义/关键词权重")

    def get_strategy_recommendation(self, query: str) -> StrategyContext:
        """获取策略推荐"""
        recent_queries = [f["query"] for f in self.feedback_history[-10:]]

        similar_count = sum(1 for q in recent_queries if self._query_similarity(query, q) > 0.5)

        if similar_count > 5:
            avg_quality = sum(
                self.feedback_history[i]["quality_score"]
                for i, q in enumerate(recent_queries)
                if self._query_similarity(query, q) > 0.5
            ) / max(similar_count, 1)

            if avg_quality > 0.7:
                return StrategyContext(
                    layer="top",
                    strategy="图谱优先检索",
                    params={"graph_weight": 0.6, "semantic_weight": 0.2}
                )
            elif avg_quality > 0.5:
                return StrategyContext(
                    layer="middle",
                    strategy="混合检索",
                    params={"semantic_weight": 0.4, "keyword_weight": 0.4, "graph_weight": 0.2}
                )
            else:
                return StrategyContext(
                    layer="bottom",
                    strategy="完整双检索",
                    params={"top_k": 50, "use_rerank": True}
                )

        return StrategyContext(
            layer="middle",
            strategy="默认混合检索",
            params={"semantic_weight": 0.4, "keyword_weight": 0.4, "graph_weight": 0.2}
        )

    def _query_similarity(self, q1: str, q2: str) -> float:
        """查询相似度"""
        words1 = set(q1.lower().split())
        words2 = set(q2.lower().split())

        if not words1 or not words2:
            return 0.0

        intersection = words1 & words2
        union = words1 | words2

        return len(intersection) / len(union)

    def get_stats(self) -> Dict:
        """获取统计信息"""
        return {
            "total_collections": len(self.collections),
            "feedback_count": len(self.feedback_history),
            "avg_quality": sum(f["quality_score"] for f in self.feedback_history) / max(len(self.feedback_history), 1),
            "recent_quality": sum(f["quality_score"] for f in self.feedback_history[-5:]) / max(len(self.feedback_history[-5:]), 1)
        }


class LayeredStrategyBridge:
    """
    分层策略桥接器
    将 GVEDC-trading-stocks-refine 的 LayeredStrategySystem 连接到老数据库
    """

    def __init__(self, db_path: str = None):
        self.adapter = OldDatabaseAdapter(db_path)
        self.adapter.initialize()

    def run_with_strategy(self, query: str, error_context: Optional[Dict] = None) -> Dict:
        """
        运行带分层策略的检索

        Args:
            query: 查询文本
            error_context: 错误上下文 (用于问题诊断场景)

        Returns:
            检索结果 + 策略信息
        """
        print("\n" + "=" * 60)
        print(f"🔄 分层策略检索: {query}")
        print("=" * 60)

        strategy = self.adapter.get_strategy_recommendation(query)

        print(f"\n📋 策略决策:")
        print(f"  层级: {strategy.layer}")
        print(f"  策略: {strategy.strategy}")
        print(f"  参数: {strategy.params}")

        result = self.adapter.execute_with_strategy(query, strategy)

        return {
            "query": query,
            "strategy": {
                "layer": strategy.layer,
                "strategy": strategy.strategy,
                "params": strategy.params
            },
            "result": result
        }

    def run_with_feedback(self, feedback: FeedbackData) -> float:
        """
        运行并收集反馈

        Args:
            feedback: 用户反馈数据

        Returns:
            质量得分
        """
        return self.adapter.collect_feedback(feedback)


def demo():
    """演示适配器"""
    print("\n" + "=" * 60)
    print("🚀 GVEDC 老数据库适配器演示")
    print("=" * 60)

    bridge = LayeredStrategyBridge()

    test_queries = [
        "Python机器学习教程",
        "2026年AI发展趋势",
        "如何优化向量数据库"
    ]

    for query in test_queries:
        result = bridge.run_with_strategy(query)

        print(f"\n📊 结果:")
        print(f"  成功: {result['result'].get('success', False)}")
        print(f"  模式: {result['result'].get('mode', 'unknown')}")
        print(f"  结果数: {result['result'].get('total', 0)}")

    feedback = FeedbackData(
        query="Python机器学习教程",
        results=[{"id": "doc1"}, {"id": "doc2"}, {"id": "doc3"}],
        clicked_ids=["doc1", "doc2"],
        satisfaction=4.0,
        dwell_time=30.0
    )

    bridge.run_with_feedback(feedback)

    print("\n📈 统计信息:")
    stats = bridge.adapter.get_stats()
    for k, v in stats.items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    demo()
