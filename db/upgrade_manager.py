#!/usr/bin/env python3
"""
GVEDC 决策优化迭代系统
整合所有升级组件：诊断 + 层级 + 多索引 + 检索Pipeline + 质量保障 + 适配器
"""

import sys
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


@dataclass
class RetrievalFeedback:
    """检索反馈"""
    query: str
    results: List[Dict]
    clicked_ids: List[str]
    satisfaction: float
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class DecisionOptimizer:
    """
    决策优化器
    实现决策优化迭代闭环：意图识别 → 策略选择 → 执行 → 反馈 → 优化
    """

    INTENT_WEIGHTS = {
        "academic_research": {"semantic": 0.6, "keyword": 0.3, "graph": 0.1},
        "technical_implementation": {"semantic": 0.4, "keyword": 0.4, "graph": 0.2},
        "industry_trend": {"semantic": 0.3, "keyword": 0.5, "graph": 0.2},
        "general": {"semantic": 0.4, "keyword": 0.4, "graph": 0.2}
    }

    def __init__(self, db_path: str = None):
        if db_path is None:
            self.db_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        else:
            self.db_path = db_path

        self.query_history = []
        self.quality_history = []
        self.strategy_adjustments = []

        self._import_components()

    def _import_components(self):
        """导入各组件"""
        try:
            from diagnose_db import DatabaseDiagnoser
            self.diagnoser = DatabaseDiagnoser(self.db_path)
        except Exception as e:
            print(f"  ⚠️ 诊断组件导入失败: {e}")
            self.diagnoser = None

        try:
            from activate_hierarchy import HierarchyActivator
            self.hierarchy_activator = HierarchyActivator(self.db_path)
        except Exception as e:
            print(f"  ⚠️ 层级组件导入失败: {e}")
            self.hierarchy_activator = None

        try:
            from multi_index_manager import MultiIndexManager, Reranker
            self.index_manager = MultiIndexManager(self.db_path)
            self.reranker = Reranker()
        except Exception as e:
            print(f"  ⚠️ 多索引组件导入失败: {e}")
            self.index_manager = None
            self.reranker = None

        try:
            from retrieval_pipeline import RetrievalPipeline, QueryProcessor
            self.pipeline = RetrievalPipeline(self.db_path)
            self.query_processor = QueryProcessor()
        except Exception as e:
            print(f"  ⚠️ 检索Pipeline导入失败: {e}")
            self.pipeline = None
            self.query_processor = None

        try:
            from quality_assurance import QualityAssurance
            self.qa = QualityAssurance(self.db_path)
        except Exception as e:
            print(f"  ⚠️ 质量保障组件导入失败: {e}")
            self.qa = None

        try:
            from adapter_for_old_db import OldDatabaseAdapter, LayeredStrategyBridge
            self.adapter = OldDatabaseAdapter(self.db_path)
            self.adapter.initialize()
            self.bridge = LayeredStrategyBridge(self.db_path)
        except Exception as e:
            print(f"  ⚠️ 适配器组件导入失败: {e}")
            self.adapter = None
            self.bridge = None

    def recognize_intent(self, query: str) -> str:
        """识别查询意图"""
        if self.query_processor:
            ctx = self.query_processor.process(query)
            return ctx.intent
        return "general"

    def select_strategy(self, intent: str) -> Dict[str, Any]:
        """选择策略"""
        weights = self.INTENT_WEIGHTS.get(intent, self.INTENT_WEIGHTS["general"])

        return {
            "intent": intent,
            "weights": weights,
            "layers": {
                "top": "图谱导航优先",
                "middle": "混合检索",
                "bottom": "完整双检索 + Rerank"
            },
            "params": self._optimize_params(intent, weights)
        }

    def _optimize_params(self, intent: str, weights: Dict[str, float]) -> Dict[str, Any]:
        """优化参数"""
        params = {
            "semantic_top_k": 50,
            "keyword_top_k": 30,
            "graph_top_k": 20,
            "use_rerank": True,
            "fusion_k": 60
        }

        if intent == "academic_research":
            params["semantic_top_k"] = 60
            params["use_rerank"] = True
        elif intent == "technical_implementation":
            params["keyword_top_k"] = 40
            params["use_rerank"] = True
        elif intent == "industry_trend":
            params["semantic_top_k"] = 40
            params["keyword_top_k"] = 40

        return params

    def execute_retrieval(self, query: str, strategy: Dict) -> Dict:
        """执行检索"""
        if self.pipeline:
            result = self.pipeline.retrieve(
                query,
                top_k=10,
                use_cache=True,
                use_rerank=strategy["params"].get("use_rerank", True)
            )
            return {
                "success": True,
                "results": result.results,
                "total": result.total,
                "time_ms": result.retrieval_time_ms,
                "metadata": result.metadata
            }

        if self.adapter and self.bridge:
            result = self.bridge.run_with_strategy(query)
            return result.get("result", {})

        return {"success": False, "error": "No retrieval component available"}

    def collect_feedback(self, feedback: RetrievalFeedback) -> float:
        """收集反馈"""
        quality_score = self._calculate_quality(feedback)

        self.query_history.append({
            "query": feedback.query,
            "timestamp": feedback.timestamp,
            "quality_score": quality_score
        })

        self.quality_history.append(quality_score)

        if len(self.quality_history) > 100:
            self.quality_history = self.quality_history[-100:]

        if quality_score < 0.5:
            self._trigger_strategy_adjustment(feedback)

        return quality_score

    def _calculate_quality(self, feedback: RetrievalFeedback) -> float:
        """计算质量得分"""
        if not feedback.results:
            return 0.0

        click_rate = len(feedback.clicked_ids) / len(feedback.results) if feedback.results else 0
        satisfaction = feedback.satisfaction / 5.0 if feedback.satisfaction else 0.5

        return click_rate * 0.4 + satisfaction * 0.6

    def _trigger_strategy_adjustment(self, feedback: RetrievalFeedback):
        """触发策略调整"""
        recent_quality = self.quality_history[-5:]

        if len(recent_quality) >= 3 and all(q < 0.5 for q in recent_quality):
            print(f"\n⚠️ 连续{len(recent_quality)}次质量低于0.5，触发策略重学习")

            adjustment = {
                "trigger": "low_quality",
                "queries": recent_quality,
                "action": "increase_rerank_weight"
            }

            self.strategy_adjustments.append(adjustment)

    def optimize_strategy(self, query: str) -> Dict[str, Any]:
        """优化策略"""
        recent_queries = [h["query"] for h in self.query_history[-10:]]

        similar_count = sum(1 for q in recent_queries if self._query_similarity(query, q) > 0.5)

        if similar_count > 5:
            recent_quality = [
                h["quality_score"]
                for h in self.query_history[-10:]
                if self._query_similarity(query, h["query"]) > 0.5
            ]
            avg_quality = sum(recent_quality) / len(recent_quality) if recent_quality else 0.5

            if avg_quality > 0.7:
                return {"action": "keep_current", "confidence": 0.9}
            elif avg_quality > 0.5:
                return {"action": "minor_adjustment", "confidence": 0.7}
            else:
                return {"action": "major_readjustment", "confidence": 0.5}

        return {"action": "use_default", "confidence": 0.6}

    def _query_similarity(self, q1: str, q2: str) -> float:
        """查询相似度"""
        words1 = set(q1.lower().split())
        words2 = set(q2.lower().split())

        if not words1 or not words2:
            return 0.0

        intersection = words1 & words2
        union = words1 | words2

        return len(intersection) / len(union)

    def get_optimization_report(self) -> Dict:
        """获取优化报告"""
        avg_quality = sum(self.quality_history) / len(self.quality_history) if self.quality_history else 0

        return {
            "total_queries": len(self.query_history),
            "avg_quality_score": avg_quality,
            "quality_trend": self.quality_history[-10:] if len(self.quality_history) >= 10 else self.quality_history,
            "strategy_adjustments": len(self.strategy_adjustments),
            "recommendations": self._generate_recommendations(avg_quality)
        }

    def _generate_recommendations(self, avg_quality: float) -> List[str]:
        """生成建议"""
        recommendations = []

        if avg_quality < 0.5:
            recommendations.append("整体质量偏低，建议增加Rerank强度")
            recommendations.append("考虑重新训练嵌入模型")
        elif avg_quality < 0.7:
            recommendations.append("质量一般，可以微调权重参数")
        else:
            recommendations.append("质量良好，保持当前策略")

        if len(self.query_history) > 50:
            recommendations.append("历史数据充足，可以进行深度学习优化")

        return recommendations


class GVEDCUpgradeManager:
    """GVEDC 升级管理器 - 一键升级老数据库"""

    def __init__(self, db_path: str = None):
        if db_path is None:
            self.db_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        else:
            self.db_path = db_path

        self.decision_optimizer = DecisionOptimizer(db_path)

    def run_full_upgrade(self):
        """运行完整升级"""
        print("\n" + "=" * 70)
        print("🚀 GVEDC 老数据库全面升级系统 v1.0")
        print("=" * 70)
        print(f"数据库路径: {self.db_path}")
        print(f"升级时间: {datetime.now().isoformat()}")
        print("=" * 70)

        steps = [
            ("Phase 1: 诊断与数据盘点", self._run_diagnosis),
            ("Phase 2: 激活层级结构", self._activate_hierarchy),
            ("Phase 3: 初始化多索引", self._init_multi_index),
            ("Phase 4: 测试检索Pipeline", self._test_pipeline),
            ("Phase 5: 质量保障检查", self._run_quality_check),
            ("Phase 6: 决策优化迭代", self._init_decision_optimization)
        ]

        for step_name, step_func in steps:
            print(f"\n{'='*70}")
            print(f"📍 {step_name}")
            print(f"{'='*70}")
            try:
                step_func()
            except Exception as e:
                print(f"  ❌ 步骤失败: {e}")

        self._print_upgrade_summary()

    def _run_diagnosis(self):
        """运行诊断"""
        if self.decision_optimizer.diagnoser:
            self.decision_optimizer.diagnoser.scan_collections()
            self.decision_optimizer.diagnoser.analyze_metadata_distribution()
            self.decision_optimizer.diagnoser.check_orphan_documents()
        else:
            print("  ⚠️ 诊断组件不可用，跳过")

    def _activate_hierarchy(self):
        """激活层级"""
        if self.decision_optimizer.hierarchy_activator:
            self.decision_optimizer.hierarchy_activator.create_hierarchy_collections()
        else:
            print("  ⚠️ 层级组件不可用，跳过")

    def _init_multi_index(self):
        """初始化多索引"""
        if self.decision_optimizer.index_manager:
            self.decision_optimizer.index_manager._init_indexes()
            stats = self.decision_optimizer.index_manager.get_index_stats()
            print(f"  📊 索引统计: {stats}")
        else:
            print("  ⚠️ 多索引组件不可用，跳过")

    def _test_pipeline(self):
        """测试Pipeline"""
        if self.decision_optimizer.pipeline:
            test_query = "GVEDC 数据库升级测试"
            result = self.decision_optimizer.pipeline.retrieve(test_query)
            print(f"  ✅ Pipeline测试: {result.total} 结果, {result.retrieval_time_ms:.1f}ms")
        else:
            print("  ⚠️ Pipeline组件不可用，跳过")

    def _run_quality_check(self):
        """运行质量检查"""
        if self.decision_optimizer.qa:
            self.decision_optimizer.qa.run_quality_check()
        else:
            print("  ⚠️ 质量保障组件不可用，跳过")

    def _init_decision_optimization(self):
        """初始化决策优化"""
        print("  ✅ 决策优化迭代系统已就绪")
        print("  💡 可用方法:")
        print("     - recognize_intent(query): 识别查询意图")
        print("     - select_strategy(intent): 选择策略")
        print("     - execute_retrieval(query, strategy): 执行检索")
        print("     - collect_feedback(feedback): 收集反馈")
        print("     - optimize_strategy(query): 优化策略")

    def _print_upgrade_summary(self):
        """打印升级总结"""
        print("\n" + "=" * 70)
        print("📊 升级总结")
        print("=" * 70)

        report = self.decision_optimizer.get_optimization_report()

        print(f"\n  总查询数: {report['total_queries']}")
        print(f"  平均质量分: {report['avg_quality_score']:.2f}")
        print(f"  策略调整次数: {report['strategy_adjustments']}")

        print(f"\n  💡 建议:")
        for rec in report["recommendations"]:
            print(f"     - {rec}")

        print("\n" + "=" * 70)
        print("✅ GVEDC 老数据库全面升级完成!")
        print("=" * 70)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="GVEDC 老数据库升级工具")
    parser.add_argument("--db-path", "-d", default=None, help="数据库路径")
    parser.add_argument("--step", "-s", type=int, choices=[1, 2, 3, 4, 5, 6],
                       help="只运行指定步骤")

    args = parser.parse_args()

    manager = GVEDCUpgradeManager(args.db_path)

    if args.step:
        step_map = {
            1: manager._run_diagnosis,
            2: manager._activate_hierarchy,
            3: manager._init_multi_index,
            4: manager._test_pipeline,
            5: manager._run_quality_check,
            6: manager._init_decision_optimization
        }
        step_map[args.step]()
    else:
        manager.run_full_upgrade()


if __name__ == "__main__":
    main()
