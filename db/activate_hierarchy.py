#!/usr/bin/env python3
"""
GVEDC 层级结构激活系统
Phase 2: 层级结构激活 - Wings/Rooms/Halls 三层架构
"""

import sys
import os
from datetime import datetime
from typing import Dict, List, Optional, Any

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import chromadb
    HAS_CHROMADB = True
except ImportError:
    HAS_CHROMADB = False


class HierarchyActivator:
    """层级结构激活器"""

    WING_KEYWORDS = {
        "学术类": {
            "keywords": ["论文", "研究", "学术", "paper", "research", "arxiv", "学术研究", "知识", "学科"],
            "icon": "📚"
        },
        "代码类": {
            "keywords": ["代码", "项目", "Git", "code", "project", "编程", "开发", "程序", "实现"],
            "icon": "💻"
        },
        "交易类": {
            "keywords": ["股票", "交易", "量化", "trading", "stock", "投资", "金融", "市场", "炒股"],
            "icon": "📊"
        },
        "系统类": {
            "keywords": ["系统", "配置", "工具", "system", "config", "环境", "安装", "部署", "设置"],
            "icon": "🔧"
        }
    }

    ROOM_MAPPING = {
        "学术类": ["论文研究", "学术报告", "技术文档", "知识库"],
        "代码类": ["前端项目", "后端服务", "AI项目", "数据库", "DevOps"],
        "交易类": ["量化策略", "市场分析", "风险管理", "回测系统"],
        "系统类": ["数据库", "工具插件", "配置文档", "环境设置"]
    }

    def __init__(self, db_path: str = None):
        if db_path is None:
            self.db_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        else:
            self.db_path = db_path

        self.vector_store = None
        if HAS_CHROMADB:
            self.vector_store = chromadb.PersistentClient(
                path=self.db_path,
                settings=chromadb.config.Settings(allow_reset=True)
            )

        self.hierarchy_collections = {}
        self.stats = {
            "total_processed": 0,
            "wing_distribution": {},
            "room_distribution": {},
            "hall_distribution": {}
        }

    def create_hierarchy_collections(self):
        """创建层级集合结构"""
        print("\n" + "=" * 60)
        print("🏗️  创建层级集合结构")
        print("=" * 60)

        if not self.vector_store:
            print("  ❌ ChromaDB 未连接")
            return

        base_collections = ["documents", "graph_nodes", "graph_edges", "recalls"]

        for base_name in base_collections:
            try:
                coll = self.vector_store.get_or_create_collection(
                    name=base_name,
                    metadata={
                        "description": f"基础集合 - {base_name}",
                        "hierarchy_level": "base"
                    }
                )
                print(f"  ✅ {base_name} 集合就绪")
            except Exception as e:
                print(f"  ❌ {base_name} 创建失败: {e}")

        for wing, wing_data in self.WING_KEYWORDS.items():
            for room in self.ROOM_MAPPING.get(wing, []):
                wing_en = {"学术类": "academic", "代码类": "code", "交易类": "trading", "系统类": "system"}.get(wing, "other")
                room_en_map = {
                    "论文研究": "paper", "学术报告": "report", "技术文档": "tech", "知识库": "knowledge",
                    "前端项目": "frontend", "后端服务": "backend", "AI项目": "ai", "数据库": "db", "DevOps": "devops",
                    "量化策略": "quant", "市场分析": "market", "风险管理": "risk", "回测系统": "backtest",
                    "工具插件": "plugins", "配置文档": "config", "环境设置": "env"
                }
                room_en = room_en_map.get(room, room[:5])
                collection_name = f"docs_{wing_en}_{room_en}".replace(" ", "_")[:63]

                try:
                    coll = self.vector_store.get_or_create_collection(
                        name=collection_name,
                        metadata={
                            "wing": wing,
                            "room": room,
                            "icon": wing_data["icon"],
                            "hierarchy_level": "hierarchical"
                        }
                    )
                    self.hierarchy_collections[f"{wing}/{room}"] = collection_name
                    print(f"  ✅ {wing}/{room} -> {collection_name}")
                except Exception as e:
                    print(f"  ❌ {collection_name} 创建失败: {e}")

        self.vector_store.get_or_create_collection(
            name="cross_hierarchy_search",
            metadata={
                "type": "federated",
                "description": "跨层级联合检索"
            }
        )
        print("  ✅ cross_hierarchy_search 集合就绪")

        print(f"\n  📊 共创建 {len(self.hierarchy_collections)} 个层级集合")

    def classify_wing(self, content: str, metadata: Dict) -> str:
        """根据内容分类到Wing"""
        text = content + " " + json.dumps(metadata)

        scores = {}
        for wing, wing_data in self.WING_KEYWORDS.items():
            score = sum(1 for kw in wing_data["keywords"] if kw in text)
            scores[wing] = score

        if scores and max(scores.values()) > 0:
            return max(scores.items(), key=lambda x: x[1])[0]
        return "其他类"

    def classify_room(self, wing: str, content: str, metadata: Dict) -> str:
        """分类到Room"""
        text = content + " " + json.dumps(metadata)

        rooms = self.ROOM_MAPPING.get(wing, [])

        scores = {}
        for room in rooms:
            score = sum(1 for kw in room if kw in text)
            scores[room] = score

        if scores and max(scores.values()) > 0:
            return max(scores.items(), key=lambda x: x[1])[0]
        return rooms[0] if rooms else "默认房间"

    def classify_hall(self, content: str, metadata: Dict) -> str:
        """分类到Hall (项目级)"""
        source = metadata.get("source", "")
        if source and source != "unknown":
            return source

        title = metadata.get("title", "")
        if title:
            return title[:20]

        project = metadata.get("project", "")
        if project:
            return project

        return "默认大厅"

    def activate_hierarchy(self, dry_run: bool = False):
        """激活层级结构 - 为文档添加层级元数据"""
        print("\n" + "=" * 60)
        print("🔄 激活层级结构")
        print("=" * 60)

        if not self.vector_store:
            print("  ❌ ChromaDB 未连接")
            return

        if dry_run:
            print("  ⚠️  演练模式 - 不实际修改数据")

        try:
            base_coll = self.vector_store.get_or_create_collection("documents")
        except Exception as e:
            print(f"  ❌ 无法获取documents集合: {e}")
            return

        try:
            all_docs = base_coll.get()
        except Exception as e:
            print(f"  ❌ 无法获取文档: {e}")
            return

        total = len(all_docs.get("ids", []))
        print(f"  📊 待处理文档: {total}")

        if total == 0:
            print("  ⚠️  没有文档需要处理")
            return

        updated_count = 0
        import json

        for i, doc_id in enumerate(all_docs["ids"]):
            content = all_docs["documents"][i]
            metadata = all_docs["metadatas"][i]

            wing = self.classify_wing(content, metadata)
            room = self.classify_room(wing, content, metadata)
            hall = self.classify_hall(content, metadata)

            new_metadata = {
                **metadata,
                "wing": wing,
                "room": room,
                "hall": hall,
                "hierarchy_path": f"{wing}/{room}/{hall}",
                "hierarchy_activated": datetime.now().isoformat()
            }

            self.stats["total_processed"] += 1
            self.stats["wing_distribution"][wing] = self.stats["wing_distribution"].get(wing, 0) + 1
            self.stats["room_distribution"][room] = self.stats["room_distribution"].get(room, 0) + 1
            self.stats["hall_distribution"][hall] = self.stats["hall_distribution"].get(hall, 0) + 1

            if not dry_run:
                try:
                    base_coll.update(ids=[doc_id], metadatas=[new_metadata])
                    updated_count += 1
                except Exception as e:
                    print(f"  ⚠️  更新失败 {doc_id}: {e}")

            if (i + 1) % 100 == 0:
                print(f"  进度: {i + 1}/{total}")

        print(f"\n  ✅ 处理完成: {updated_count}/{total} 文档已更新")

        print("\n  📊 层级分布统计:")
        print("\n  Wing (大类):")
        for wing, count in sorted(self.stats["wing_distribution"].items(), key=lambda x: -x[1]):
            print(f"    {wing}: {count}")

        print("\n  Room (中类):")
        for room, count in sorted(self.stats["room_distribution"].items(), key=lambda x: -x[1])[:10]:
            print(f"    {room}: {count}")

        print("\n  Hall (细类):")
        for hall, count in sorted(self.stats["hall_distribution"].items(), key=lambda x: -x[1])[:10]:
            print(f"    {hall}: {count}")

    def migrate_to_hierarchical_collections(self):
        """将文档迁移到层级集合"""
        print("\n" + "=" * 60)
        print("📦 迁移文档到层级集合")
        print("=" * 60)

        if not self.vector_store:
            print("  ❌ ChromaDB 未连接")
            return

        try:
            base_coll = self.vector_store.get_or_create_collection("documents")
            all_docs = base_coll.get()
        except Exception as e:
            print(f"  ❌ 无法获取文档: {e}")
            return

        total = len(all_docs.get("ids", []))
        print(f"  📊 待迁移文档: {total}")

        migrated = 0
        for i, doc_id in enumerate(all_docs["ids"]):
            metadata = all_docs["metadatas"][i]

            wing = metadata.get("wing", "其他类")
            room = metadata.get("room", "默认房间")
            path_key = f"{wing}/{room}"

            target_collection = self.hierarchy_collections.get(path_key)
            if not target_collection:
                target_collection = f"docs_{wing}_{room}".replace(" ", "_")

            try:
                target_coll = self.vector_store.get_or_create_collection(
                    name=target_collection,
                    metadata={"wing": wing, "room": room}
                )

                target_coll.add(
                    documents=[all_docs["documents"][i]],
                    metadatas=[metadata],
                    ids=[doc_id]
                )
                migrated += 1

            except Exception as e:
                print(f"  ⚠️  迁移失败 {doc_id}: {e}")

            if (i + 1) % 100 == 0:
                print(f"  进度: {i + 1}/{total}")

        print(f"\n  ✅ 迁移完成: {migrated}/{total}")

    def get_hierarchy_stats(self) -> Dict:
        """获取层级统计"""
        stats = {
            "collections": len(self.hierarchy_collections),
            "distribution": {
                "wings": {},
                "rooms": {},
                "halls": {}
            }
        }

        if self.vector_store:
            for path_key, coll_name in self.hierarchy_collections.items():
                try:
                    coll = self.vector_store.get_collection(coll_name)
                    wing, room = path_key.split("/")
                    stats["distribution"]["wings"][wing] = stats["distribution"]["wings"].get(wing, 0) + coll.count()
                    stats["distribution"]["rooms"][room] = stats["distribution"]["rooms"].get(room, 0) + coll.count()
                except:
                    pass

        return stats


def main():
    import argparse

    parser = argparse.ArgumentParser(description="GVEDC 层级结构激活工具")
    parser.add_argument("--db-path", "-d", default=None, help="数据库路径")
    parser.add_argument("--dry-run", "-n", action="store_true", help="演练模式")
    parser.add_argument("--migrate", "-m", action="store_true", help="迁移到层级集合")

    args = parser.parse_args()

    activator = HierarchyActivator(args.db_path)

    print("\n" + "=" * 60)
    print("🚀 GVEDC 层级结构激活系统 v1.0")
    print("=" * 60)

    activator.create_hierarchy_collections()
    activator.activate_hierarchy(dry_run=args.dry_run)

    if args.migrate:
        activator.migrate_to_hierarchical_collections()

    print("\n" + "=" * 60)
    print("✅ 层级结构激活完成")
    print("=" * 60)


if __name__ == "__main__":
    import json
    main()
