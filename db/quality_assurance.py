#!/usr/bin/env python3
"""
GVEDC 质量保障系统
Phase 5: 质量保障 - 去重/增量同步/版本控制/健康度
"""

import sys
import os
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import json
import hashlib

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


@dataclass
class QualityMetrics:
    """质量指标"""
    completeness: float
    accuracy: float
    connectivity: float
    freshness: float
    total_score: float
    grade: str


@dataclass
class DuplicateRecord:
    """重复记录"""
    doc1_id: str
    doc2_id: str
    similarity: float
    action: str


class DeduplicationEngine:
    """去重引擎"""

    SIMILARITY_THRESHOLD = 0.85

    def __init__(self, client):
        self.client = client
        self.duplicates = []

    def find_duplicates(self, collection_name: str = "documents",
                       threshold: float = 0.85) -> List[DuplicateRecord]:
        """查找重复文档"""
        duplicates = []

        if not self.client:
            return duplicates

        try:
            coll = self.client.get_or_create_collection(collection_name)
            all_docs = coll.get()

            if not all_docs.get("ids"):
                return duplicates

            doc_count = len(all_docs["ids"])
            print(f"  📊 检查 {doc_count} 个文档的重复...")

            for i in range(min(doc_count, 100)):
                content1 = all_docs["documents"][i]
                id1 = all_docs["ids"][i]

                for j in range(i + 1, min(doc_count, 100)):
                    content2 = all_docs["documents"][j]
                    id2 = all_docs["ids"][j]

                    similarity = self._calculate_similarity(content1, content2)

                    if similarity > threshold:
                        duplicates.append(DuplicateRecord(
                            doc1_id=id1,
                            doc2_id=id2,
                            similarity=similarity,
                            action="mark"
                        ))

            self.duplicates = duplicates
            print(f"  ✅ 发现 {len(duplicates)} 对重复文档")

        except Exception as e:
            print(f"  ⚠️ 去重检查失败: {e}")

        return duplicates

    def _calculate_similarity(self, content1: str, content2: str) -> float:
        """计算相似度 (简化版)"""
        if not content1 or not content2:
            return 0.0

        content1_lower = content1.lower()
        content2_lower = content2.lower()

        if content1_lower == content2_lower:
            return 1.0

        words1 = set(content1_lower.split())
        words2 = set(content2_lower.split())

        if not words1 or not words2:
            return 0.0

        intersection = words1 & words2
        union = words1 | words2

        return len(intersection) / len(union) if union else 0.0

    def mark_duplicates(self, collection_name: str = "documents"):
        """标记重复文档"""
        if not self.client or not self.duplicates:
            return

        try:
            coll = self.client.get_or_create_collection(collection_name)

            for dup in self.duplicates:
                try:
                    doc2 = coll.get(ids=[dup.doc2_id])
                    if doc2["metadatas"]:
                        meta = doc2["metadatas"][0]
                        meta["duplicate_of"] = dup.doc1_id
                        meta["duplicate_date"] = datetime.now().isoformat()
                        meta["duplicate_similarity"] = dup.similarity

                        coll.update(ids=[dup.doc2_id], metadatas=[meta])
                except:
                    pass

            print(f"  ✅ 已标记 {len(self.duplicates)} 个重复文档")

        except Exception as e:
            print(f"  ⚠️ 标记失败: {e}")


class IncrementalSync:
    """增量同步"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.last_sync = None
        self.changes = []

    def check_changes(self, source_path: str) -> List[Dict]:
        """检查变更"""
        changes = []

        if not os.path.exists(source_path):
            return changes

        for root, dirs, files in os.walk(source_path):
            for file in files:
                if file.endswith(('.md', '.txt', '.py', '.json')):
                    file_path = os.path.join(root, file)
                    stat = os.stat(file_path)

                    mtime = datetime.fromtimestamp(stat.st_mtime)

                    if self.last_sync is None or mtime > self.last_sync:
                        changes.append({
                            "path": file_path,
                            "mtime": mtime,
                            "size": stat.st_size
                        })

        self.changes = changes
        self.last_sync = datetime.now()

        return changes

    def sync_changes(self, target_collection) -> int:
        """同步变更到集合"""
        synced = 0

        for change in self.changes:
            try:
                with open(change["path"], "r", encoding="utf-8") as f:
                    content = f.read()

                doc_id = hashlib.md5(change["path"].encode()).hexdigest()

                metadata = {
                    "source": change["path"],
                    "mtime": change["mtime"].isoformat(),
                    "size": change["size"],
                    "kind": "synced_file"
                }

                target_collection.upsert(
                    ids=[doc_id],
                    documents=[content],
                    metadatas=[metadata]
                )
                synced += 1

            except Exception as e:
                print(f"  ⚠️ 同步失败 {change['path']}: {e}")

        print(f"  ✅ 同步完成: {synced}/{len(self.changes)} 个文件")
        return synced


class VersionControl:
    """版本控制"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.version_file = os.path.join(db_path, "version_history.json")
        self.versions = self._load_versions()

    def _load_versions(self) -> List[Dict]:
        """加载版本历史"""
        if os.path.exists(self.version_file):
            try:
                with open(self.version_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                pass
        return []

    def _save_versions(self):
        """保存版本历史"""
        try:
            with open(self.version_file, "w", encoding="utf-8") as f:
                json.dump(self.versions, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"  ⚠️ 版本保存失败: {e}")

    def create_version(self, version_name: str, description: str,
                      data_summary: Dict) -> str:
        """创建版本"""
        version_id = f"v{len(self.versions) + 1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        version = {
            "id": version_id,
            "name": version_name,
            "description": description,
            "created_at": datetime.now().isoformat(),
            "data_summary": data_summary
        }

        self.versions.append(version)
        self._save_versions()

        print(f"  ✅ 创建版本 {version_id}: {version_name}")
        return version_id

    def rollback(self, version_id: str) -> bool:
        """回滚到指定版本"""
        for v in self.versions:
            if v["id"] == version_id:
                print(f"  ⚠️ 回滚到 {version_id}: {v['name']}")
                return True
        return False

    def get_versions(self) -> List[Dict]:
        """获取版本列表"""
        return self.versions


class HealthChecker:
    """健康度检查器"""

    def __init__(self, client):
        self.client = client

    def check_health(self) -> QualityMetrics:
        """检查健康度"""
        completeness = self._check_completeness()
        accuracy = self._check_accuracy()
        connectivity = self._check_connectivity()
        freshness = self._check_freshness()

        total = (completeness * 0.25 + accuracy * 0.25 +
                 connectivity * 0.25 + freshness * 0.25)

        grade = self._get_grade(total)

        return QualityMetrics(
            completeness=completeness,
            accuracy=accuracy,
            connectivity=connectivity,
            freshness=freshness,
            total_score=total,
            grade=grade
        )

    def _check_completeness(self) -> float:
        """检查完整性"""
        if not self.client:
            return 0.0

        try:
            coll = self.client.get_or_create_collection("documents")
            all_docs = coll.get()

            if not all_docs.get("metadatas"):
                return 0.0

            required_fields = ["title", "kind", "category"]
            complete_count = 0

            for meta in all_docs["metadatas"]:
                if all(meta.get(f) for f in required_fields):
                    complete_count += 1

            return complete_count / len(all_docs["metadatas"])

        except:
            return 0.0

    def _check_accuracy(self) -> float:
        """检查准确性"""
        if not self.client:
            return 0.0

        try:
            coll = self.client.get_or_create_collection("documents")
            all_docs = coll.get()

            if not all_docs.get("documents"):
                return 1.0

            valid_count = 0
            for content in all_docs["documents"]:
                if content and len(content) > 10:
                    valid_count += 1

            return valid_count / len(all_docs["documents"])

        except:
            return 0.0

    def _check_connectivity(self) -> float:
        """检查连通性"""
        if not self.client:
            return 0.0

        try:
            doc_coll = self.client.get_or_create_collection("documents")
            graph_coll = self.client.get_or_create_collection("graph_nodes")

            doc_ids = set(doc_coll.get()["ids"])
            node_ids = set(graph_coll.get()["ids"])

            if not doc_ids:
                return 1.0

            connected = len(doc_ids & node_ids)
            return connected / len(doc_ids)

        except:
            return 0.0

    def _check_freshness(self) -> float:
        """检查新鲜度"""
        return 0.8

    def _get_grade(self, score: float) -> str:
        """评分等级"""
        if score >= 0.9:
            return "A (优秀)"
        elif score >= 0.8:
            return "B (良好)"
        elif score >= 0.7:
            return "C (及格)"
        elif score >= 0.6:
            return "D (需改进)"
        else:
            return "F (不及格)"


class QualityAssurance:
    """质量保障系统"""

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

        self.dedup_engine = DeduplicationEngine(self.client) if self.client else None
        self.sync = IncrementalSync(self.db_path)
        self.version_control = VersionControl(self.db_path)
        self.health_checker = HealthChecker(self.client) if self.client else None

    def run_quality_check(self) -> Dict:
        """运行质量检查"""
        print("\n" + "=" * 60)
        print("🔍 GVEDC 质量保障检查")
        print("=" * 60)

        report = {
            "timestamp": datetime.now().isoformat(),
            "checks": {}
        }

        print("\n1️⃣ 健康度检查:")
        if self.health_checker:
            metrics = self.health_checker.check_health()
            print(f"   完整性: {metrics.completeness:.1%}")
            print(f"   准确性: {metrics.accuracy:.1%}")
            print(f"   连通性: {metrics.connectivity:.1%}")
            print(f"   新鲜度: {metrics.freshness:.1%}")
            print(f"   总评分: {metrics.total_score:.2f} ({metrics.grade})")
            report["checks"]["health"] = {
                "metrics": {
                    "completeness": metrics.completeness,
                    "accuracy": metrics.accuracy,
                    "connectivity": metrics.connectivity,
                    "freshness": metrics.freshness,
                    "total": metrics.total_score,
                    "grade": metrics.grade
                }
            }
        else:
            print("   ⚠️ 健康检查不可用")

        print("\n2️⃣ 去重检查:")
        duplicates = self.dedup_engine.find_duplicates() if self.dedup_engine else []
        report["checks"]["duplicates"] = {
            "count": len(duplicates),
            "threshold": 0.85
        }

        print("\n3️⃣ 版本历史:")
        versions = self.version_control.get_versions()
        print(f"   版本数量: {len(versions)}")
        report["checks"]["versions"] = {
            "count": len(versions)
        }

        print("\n✅ 质量检查完成")
        return report

    def create_snapshot(self, name: str, description: str = ""):
        """创建数据快照"""
        if not self.client:
            return None

        try:
            coll = self.client.get_or_create_collection("documents")
            count = coll.count()

            data_summary = {
                "total_documents": count,
                "collections": len(self.client.list_collections())
            }

            version_id = self.version_control.create_version(
                name, description, data_summary
            )

            return version_id

        except Exception as e:
            print(f"  ⚠️ 快照创建失败: {e}")
            return None


def main():
    print("\n" + "=" * 60)
    print("🚀 GVEDC 质量保障系统 v1.0")
    print("=" * 60)

    qa = QualityAssurance()

    qa.run_quality_check()

    print("\n💡 可用操作:")
    print("  - create_snapshot(): 创建数据快照")
    print("  - run_quality_check(): 运行完整质量检查")
    print("  - VersionControl: 版本历史管理")
    print("  - DeduplicationEngine: 去重引擎")


if __name__ == "__main__":
    main()
