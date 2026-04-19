import chromadb
from chromadb.config import Settings
import time
from typing import Dict, List, Optional, Any

class VectorStore:
    def __init__(self, db_path: str = "db"):
        self.client = chromadb.PersistentClient(
            path=db_path,
            settings=Settings(allow_reset=True)
        )
        self.collections = {}
        self._init_collections()

    def _init_collections(self):
        self.collections['documents'] = self.client.get_or_create_collection(
            name="documents",
            metadata={"description": "百科化文档集合"}
        )
        self.collections['graph_nodes'] = self.client.get_or_create_collection(
            name="graph_nodes",
            metadata={"description": "图谱节点集合"}
        )
        self.collections['graph_edges'] = self.client.get_or_create_collection(
            name="graph_edges",
            metadata={"description": "图谱边集合"}
        )
        self.collections['recalls'] = self.client.get_or_create_collection(
            name="recalls",
            metadata={"description": "检索记录集合"}
        )

    def get_collection(self, name: str):
        if name not in self.collections:
            self.collections[name] = self.client.get_or_create_collection(name=name)
        return self.collections[name]

    def add_document(
        self,
        content: str,
        metadata: Dict[str, Any],
        doc_id: Optional[str] = None,
        collection_name: str = "documents"
    ) -> str:
        collection = self.get_collection(collection_name)
        if doc_id is None:
            doc_id = f"doc-{int(time.time())}-{hash(content) % 100000}"

        collection.add(
            documents=[content],
            metadatas=[metadata],
            ids=[doc_id]
        )
        
        # 如果添加的是文档且不是图谱报告，自动更新图谱
        if collection_name == "documents" and metadata.get("kind") != "graph_report":
            self._update_graph()
            
        return doc_id
        
    def _update_graph(self):
        """自动更新图谱"""
        try:
            from src.graph.graph_builder import GraphBuilder
            
            # 初始化图谱构建器
            graph_builder = GraphBuilder(vector_store=self)
            
            # 构建并存储图谱
            graph_data = graph_builder.build_graph()
            
            # 生成图谱报告
            graph_report = graph_builder.get_graph_report(graph_data)
            
            # 存储图谱报告到数据库
            report_id = f"graph-report-{int(time.time())}"
            self.add_document(
                content=graph_report,
                metadata={
                    "id": report_id,
                    "kind": "graph_report",
                    "type": "graph",
                    "title": "自动更新图谱报告",
                    "category": ["计算机科学"],
                    "source": "GVEDC自动更新",
                    "stats": str(graph_data.get('stats', {}))
                },
                doc_id=report_id,
                collection_name="documents"
            )
            
            print(f"✅ 图谱已自动更新，报告ID: {report_id}")
        except Exception as e:
            print(f"⚠️ 自动更新图谱失败: {e}")

    def get_document(
        self,
        doc_id: str,
        collection_name: str = "documents"
    ) -> Optional[Dict[str, Any]]:
        collection = self.get_collection(collection_name)
        result = collection.get(ids=[doc_id])
        if result['ids']:
            return {
                'id': result['ids'][0],
                'content': result['documents'][0],
                'metadata': result['metadatas'][0]
            }
        return None

    def delete_document(
        self,
        doc_id: str,
        collection_name: str = "documents"
    ) -> bool:
        collection = self.get_collection(collection_name)
        try:
            collection.delete(ids=[doc_id])
            return True
        except Exception:
            return False

    def search(
        self,
        query: str,
        n_results: int = 8,
        where: Optional[Dict] = None,
        collection_name: str = "documents"
    ) -> List[Dict[str, Any]]:
        collection = self.get_collection(collection_name)
        kwargs = {
            'query_texts': [query],
            'n_results': n_results
        }
        if where:
            kwargs['where'] = where

        results = collection.query(**kwargs)

        documents = []
        for i in range(len(results['ids'][0])):
            documents.append({
                'id': results['ids'][0][i],
                'content': results['documents'][0][i],
                'metadata': results['metadatas'][0][i],
                'distance': results['distances'][0][i] if 'distances' in results else None
            })
        return documents

    def count(self, collection_name: str = "documents") -> int:
        collection = self.get_collection(collection_name)
        return collection.count()

    def list_collections(self) -> List[str]:
        return list(self.collections.keys())

    def reset(self):
        self.client.reset()
        self._init_collections()
