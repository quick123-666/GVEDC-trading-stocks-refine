import os

# 数据库路径（项目根目录下的db文件夹）
DB_PATH = os.path.dirname(os.path.abspath(__file__)) or "."

# ChromaDB配置
CHROMA_COLLECTIONS = {
    "documents": "documents",
    "graph_nodes": "graph_nodes",
    "graph_edges": "graph_edges",
    "recalls": "recalls"
}

# SQLite配置
SQLITE_DB_PATH = os.path.join(DB_PATH, "gvedc.db")

# 向量配置
EMBEDDING_DIMENSION = 1536
EMBEDDING_MODEL = "text-embedding-ada-002"

# 检索配置
DEFAULT_RETRIEVAL_MODE = "graph_vector"
RETRIEVAL_MODES = ["graph_only", "vector_only", "graph_vector", "hybrid"]

# Graph→Recall配置
GRAPH_RECALL = {
    "enabled": True,
    "limit": 50,
    "min_score": 0.3,
    "use_god_nodes": True,
    "navigation_depth": 3
}

# Vector Recall配置
VECTOR_RECALL = {
    "enabled": True,
    "top_k": 8,
    "min_score": 0.5,
    "use_filter": True,
    "rerank": True
}

# Dual Fusion配置
DUAL_FUSION = {
    "enabled": True,
    "graph_weight": 0.3,
    "vector_weight": 0.7,
    "fusion_method": "weighted_sum",
    "deduplicate": True
}

# Hints配置
HINTS_CONFIG = {
    "enabled": True,
    "max_hints": 5,
    "expand_query": True
}

# 缓存配置
CACHE = {
    "enabled": True,
    "ttl": 3600,
    "max_size": 1000
}

# 监控配置
MONITORING = {
    "enabled": True,
    "log_level": "INFO"
}

# 默认层级
DEFAULT_WING = "general"
DEFAULT_ROOM = "chat"
DEFAULT_HALL = "facts"

# 百科化配置
SUPPORTED_FORMATS = ['.pdf', '.docx', '.md', '.txt']
ABSTRACT_MAX_LENGTH = 200
MAX_KEYWORDS = 10

# 图谱配置
MIN_ENTITY_FREQUENCY = 2
ENTITY_TYPES = ["PERSON", "ORG", "TECH", "CONCEPT", "LOCATION"]
GOD_NODES_LIMIT = 10
