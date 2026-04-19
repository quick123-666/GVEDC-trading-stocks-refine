#!/usr/bin/env python3
"""
GVEDC 数据库诊断脚本
Phase 1: 诊断与数据盘点
"""

import sys
import os
import json
from datetime import datetime
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import chromadb
    HAS_CHROMADB = True
except ImportError:
    HAS_CHROMADB = False

try:
    import sqlite3
    HAS_SQLITE = True
except ImportError:
    HAS_SQLITE = False


class DatabaseDiagnoser:
    def __init__(self, db_path: str = None):
        if db_path is None:
            self.db_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        else:
            self.db_path = db_path

        self.vector_client = None
        self.graph_conn = None
        self.report = {
            "timestamp": datetime.now().isoformat(),
            "db_path": self.db_path,
            "collections": {},
            "graph_stats": {},
            "issues": [],
            "recommendations": []
        }

        self._connect()

    def _connect(self):
        if HAS_CHROMADB:
            try:
                self.vector_client = chromadb.PersistentClient(
                    path=self.db_path,
                    settings=chromadb.config.Settings(allow_reset=True)
                )
                print("✅ ChromaDB 连接成功")
            except Exception as e:
                print(f"❌ ChromaDB 连接失败: {e}")
                self.report["issues"].append(f"ChromaDB连接失败: {e}")

        if HAS_SQLITE:
            db_file = os.path.join(self.db_path, "gvedc.db")
            if os.path.exists(db_file):
                try:
                    self.graph_conn = sqlite3.connect(db_file)
                    print("✅ SQLite 连接成功")
                except Exception as e:
                    print(f"❌ SQLite 连接失败: {e}")
                    self.report["issues"].append(f"SQLite连接失败: {e}")

    def scan_collections(self):
        """扫描所有集合"""
        print("\n" + "=" * 60)
        print("📊 ChromaDB 集合扫描报告")
        print("=" * 60)

        if not self.vector_client:
            print("  ⚠️  无法连接ChromaDB")
            return

        collections = self.vector_client.list_collections()
        total_docs = 0

        for coll_obj in collections:
            coll_name = coll_obj.name if hasattr(coll_obj, 'name') else str(coll_obj)
            try:
                coll = self.vector_client.get_collection(coll_name)
                count = coll.count()
                total_docs += count

                metadata = coll.metadata or {}
                print(f"  📦 {coll_name}: {count:,} 文档")

                self.report["collections"][coll_name] = {
                    "count": count,
                    "metadata": metadata
                }
            except Exception as e:
                print(f"  ❌ {coll_name}: 读取失败 - {e}")
                self.report["issues"].append(f"集合{coll_name}读取失败: {e}")

        print(f"\n  总计: {total_docs:,} 文档")
        self.report["total_documents"] = total_docs

    def analyze_metadata_distribution(self):
        """分析元数据分布"""
        print("\n" + "=" * 60)
        print("📋 元数据分布分析")
        print("=" * 60)

        if not self.vector_client:
            return

        coll = self.vector_client.get_collection("documents")
        try:
            all_docs = coll.get()
        except:
            print("  ⚠️  无法获取documents集合")
            return

        kinds = {}
        categories = {}
        sources = {}
        type_distribution = {}

        for meta in all_docs.get('metadatas', []):
            kind = meta.get('kind', 'unknown')
            kinds[kind] = kinds.get(kind, 0) + 1

            category_list = meta.get('category', [])
            if isinstance(category_list, list):
                for cat in category_list:
                    categories[cat] = categories.get(cat, 0) + 1
            elif category_list:
                categories[category_list] = categories.get(category_list, 0) + 1

            source = meta.get('source', 'unknown')
            sources[source] = sources.get(source, 0) + 1

            doc_type = meta.get('type', 'unknown')
            type_distribution[doc_type] = type_distribution.get(doc_type, 0) + 1

        print("\n  📌 按类型分布 (kind):")
        for kind, count in sorted(kinds.items(), key=lambda x: -x[1])[:10]:
            pct = count / len(all_docs['metadatas']) * 100 if all_docs['metadatas'] else 0
            print(f"    {kind}: {count} ({pct:.1f}%)")

        print("\n  📌 按分类分布 (category, Top 10):")
        for cat, count in sorted(categories.items(), key=lambda x: -x[1])[:10]:
            pct = count / len(all_docs['metadatas']) * 100 if all_docs['metadatas'] else 0
            print(f"    {cat}: {count} ({pct:.1f}%)")

        print("\n  📌 按来源分布 (source):")
        for source, count in sorted(sources.items(), key=lambda x: -x[1])[:10]:
            print(f"    {source}: {count}")

        self.report["metadata_distribution"] = {
            "kinds": kinds,
            "categories": categories,
            "sources": sources,
            "types": type_distribution
        }

    def analyze_graph(self):
        """分析图谱数据"""
        print("\n" + "=" * 60)
        print("🕸️  图谱分析")
        print("=" * 60)

        if not self.graph_conn:
            db_file = os.path.join(self.db_path, "gvedc.db")
            if os.path.exists(db_file):
                self.graph_conn = sqlite3.connect(db_file)
            else:
                print("  ⚠️  图谱数据库不存在")
                return

        cursor = self.graph_conn.cursor()

        tables = ["entities", "relations", "nodes", "edges"]
        for table in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"  📊 {table}: {count} 条记录")
                self.report["graph_stats"][table] = count
            except:
                pass

        try:
            cursor.execute("SELECT COUNT(DISTINCT entity_type) FROM entities")
            entity_types = cursor.fetchone()[0]
            print(f"  🏷️  实体类型数: {entity_types}")
            self.report["graph_stats"]["entity_types"] = entity_types
        except:
            pass

        try:
            cursor.execute("SELECT COUNT(DISTINCT relation_type) FROM relations")
            relation_types = cursor.fetchone()[0]
            print(f"  🔗 关系类型数: {relation_types}")
            self.report["graph_stats"]["relation_types"] = relation_types
        except:
            pass

    def check_orphan_documents(self):
        """检查孤儿文档"""
        print("\n" + "=" * 60)
        print("🔍 孤儿文档检测")
        print("=" * 60)

        if not self.vector_client:
            return

        try:
            doc_coll = self.vector_client.get_collection("documents")
            graph_coll = self.vector_client.get_collection("graph_nodes")
        except Exception as e:
            print(f"  ⚠️  无法检查孤儿文档: {e}")
            return

        try:
            all_doc_ids = set(doc_coll.get()['ids'])
        except:
            all_doc_ids = set()

        try:
            all_node_ids = set(graph_coll.get()['ids'])
        except:
            all_node_ids = set()

        orphans = all_doc_ids - all_node_ids

        print(f"  总文档数: {len(all_doc_ids)}")
        print(f"  总节点数: {len(all_node_ids)}")
        print(f"  孤儿文档: {len(orphans)}")

        if orphans:
            print("\n  孤儿文档列表 (前10个):")
            for oid in list(orphans)[:10]:
                print(f"    - {oid}")

            self.report["issues"].append({
                "type": "orphan_documents",
                "count": len(orphans),
                "description": "存在未关联到图谱的文档"
            })

        self.report["orphan_count"] = len(orphans)

    def check_hierarchy_structure(self):
        """检查层级结构"""
        print("\n" + "=" * 60)
        print("🏗️  层级结构检查")
        print("=" * 60)

        if not self.vector_client:
            return

        try:
            coll = self.vector_client.get_collection("documents")
            all_docs = coll.get()
        except:
            print("  ⚠️  无法获取文档集合")
            return

        wings = {}
        rooms = {}
        halls = {}

        for meta in all_docs.get('metadatas', []):
            wing = meta.get('wing', 'no_wing')
            room = meta.get('room', 'no_room')
            hall = meta.get('hall', 'no_hall')

            wings[wing] = wings.get(wing, 0) + 1
            rooms[room] = rooms.get(room, 0) + 1
            halls[hall] = halls.get(hall, 0) + 1

        print(f"\n  Wing (大类): {len(wings)} 种")
        for wing, count in sorted(wings.items(), key=lambda x: -x[1])[:5]:
            print(f"    {wing}: {count}")

        print(f"\n  Room (中类): {len(rooms)} 种")
        for room, count in sorted(rooms.items(), key=lambda x: -x[1])[:5]:
            print(f"    {room}: {count}")

        print(f"\n  Hall (细类): {len(halls)} 种")
        for hall, count in sorted(halls.items(), key=lambda x: -x[1])[:5]:
            print(f"    {hall}: {count}")

        no_hierarchy = wings.get('no_wing', 0)
        if no_hierarchy > 0:
            pct = no_hierarchy / len(all_docs['metadatas']) * 100
            print(f"\n  ⚠️  无层级分类的文档: {no_hierarchy} ({pct:.1f}%)")
            self.report["issues"].append({
                "type": "missing_hierarchy",
                "count": no_hierarchy,
                "description": "大部分文档缺少Wings/Rooms/Halls层级分类"
            })

        self.report["hierarchy"] = {
            "wings": len(wings),
            "rooms": len(rooms),
            "halls": len(halls),
            "no_hierarchy_count": no_hierarchy
        }

    def generate_recommendations(self):
        """生成升级建议"""
        print("\n" + "=" * 60)
        print("💡 升级建议")
        print("=" * 60)

        recommendations = []

        total_docs = self.report.get("total_documents", 0)
        if total_docs < 100:
            recommendations.append("数据量较少，建议优先扩充知识库")
        elif total_docs > 10000:
            recommendations.append("数据量较大，建议启用多索引策略")

        orphan_count = self.report.get("orphan_count", 0)
        if orphan_count > 50:
            recommendations.append(f"存在{orphan_count}个孤儿文档，建议执行图谱关联")

        hierarchy = self.report.get("hierarchy", {})
        if hierarchy.get("no_hierarchy_count", 0) > 100:
            recommendations.append("建议激活Wings/Rooms/Halls层级结构")

        collections = self.report.get("collections", {})
        if "documents" not in collections:
            recommendations.append("缺少documents集合，需要初始化基础存储")
        if len(collections) < 4:
            recommendations.append("集合数量较少，建议增加多索引支持")

        if not recommendations:
            print("  ✅ 数据库状态良好，无需特殊处理")
        else:
            for i, rec in enumerate(recommendations, 1):
                print(f"  {i}. {rec}")

        self.report["recommendations"] = recommendations

    def save_report(self, output_path: str = None):
        """保存诊断报告"""
        if output_path is None:
            output_path = os.path.join(self.db_path, "diagnostic_report.json")

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(self.report, f, ensure_ascii=False, indent=2)

        print(f"\n📄 诊断报告已保存: {output_path}")

    def run_full_diagnosis(self):
        """运行完整诊断"""
        print("\n" + "=" * 60)
        print("🚀 GVEDC 数据库诊断工具 v1.0")
        print("=" * 60)
        print(f"数据库路径: {self.db_path}")
        print(f"诊断时间: {self.report['timestamp']}")

        self.scan_collections()
        self.analyze_metadata_distribution()
        self.analyze_graph()
        self.check_orphan_documents()
        self.check_hierarchy_structure()
        self.generate_recommendations()
        self.save_report()

        print("\n" + "=" * 60)
        print("✅ 诊断完成")
        print("=" * 60)

        return self.report


def main():
    import argparse

    parser = argparse.ArgumentParser(description="GVEDC 数据库诊断工具")
    parser.add_argument("--db-path", "-d", default=None, help="数据库路径")
    parser.add_argument("--output", "-o", default=None, help="报告输出路径")

    args = parser.parse_args()

    diagnoser = DatabaseDiagnoser(args.db_path)
    diagnoser.run_full_diagnosis()

    if args.output:
        diagnoser.save_report(args.output)


if __name__ == "__main__":
    main()
