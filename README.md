# GVEDC-trading-stocks-refine

## 项目简介

GVEDC-trading-stocks-refine 是一个整合了多种数据库类型的智能炒股数据系统，包括：

- **知识图谱**：存储股票、行业、概念之间的关联关系
- **向量数据库**：存储股票相关文本的语义向量，支持语义搜索
- **百科知识库**：存储结构化的股票知识和分析报告
- **关系型数据库**：存储交易数据和元数据
- **时序数据库**：存储股票价格和性能指标的时间序列数据

## 系统架构

```
GVEDC-trading-stocks-refine/
├── config/                # 配置文件
├── scripts/               # 脚本文件
├── services/              # 服务代码
├── data/                  # 数据存储
├── logs/                  # 日志文件
├── backups/               # 备份文件
└── docs/                  # 文档
```

## 系统要求

### 数据库服务
- **Elasticsearch** 8.10.0+
- **ChromaDB** 最新版本
- **Neo4j** 5.10+
- **PostgreSQL** 15+
- **InfluxDB** 2.7+

### 依赖软件
- **Node.js** 16+
- **Python** 3.8+
- **npm** 8+
- **curl**

## 安装与配置

1. **安装数据库服务**：
   - 下载并安装Elasticsearch、ChromaDB、Neo4j、PostgreSQL和InfluxDB
   - 按照各数据库的官方文档进行配置

2. **配置数据库**：
   - 设置数据库用户名和密码（与config/databases.yml中的配置一致）
   - 启动所有数据库服务

3. **安装依赖**：
   - 安装Node.js和Python
   - 安装npm包：`npm install express axios dotenv winston`
   - 安装Python包：`pip install sentence-transformers chromadb neo4j psycopg2-binary elasticsearch influxdb-client`

4. **初始化系统**：
   - 运行初始化脚本：`scripts/setup.bat`（Windows）或 `scripts/setup.sh`（Linux/Mac）

5. **启动服务**：
   - 运行启动脚本：`scripts/start.bat`（Windows）或 `scripts/start.sh`（Linux/Mac）

## 使用方法

### 1. 初始化系统
```bash
# Windows
scripts\setup.bat

# Linux/Mac
chmod +x scripts/setup.sh
./scripts/setup.sh
```

### 2. 启动服务
```bash
# Windows
scripts\start.bat

# Linux/Mac
chmod +x scripts/start.sh
./scripts/start.sh
```

### 3. 停止服务
```bash
# Windows
scripts\stop.bat

# Linux/Mac
chmod +x scripts/stop.sh
./scripts/stop.sh
```

### 4. 备份数据
```bash
# Windows
scripts\backup.bat

# Linux/Mac
chmod +x scripts/backup.sh
./scripts/backup.sh
```

### 5. 监控系统
```bash
# Windows
scripts\monitor.bat

# Linux/Mac
chmod +x scripts/monitor.sh
./scripts/monitor.sh
```

## API接口

- **GET /health**：检查服务健康状态
- **GET /search**：全文搜索（使用百科知识库）
- **GET /similarity**：语义搜索（使用向量数据库）
- **GET /graph**：关系查询（使用知识图谱）
- **GET /metadata**：元数据查询（使用关系型数据库）
- **GET /history**：历史查询（使用时序数据库）

## 数据同步

系统支持三种同步策略：
- **实时同步**：每秒执行一次，处理小批量数据
- **定期同步**：每5分钟执行一次，处理中等批量数据
- **全量同步**：每24小时执行一次，处理大批量数据

## 压缩策略

系统根据数据热度采用不同的压缩策略：
- **热数据**：轻量级压缩，优先考虑性能
- **温数据**：中等压缩，平衡性能和存储
- **冷数据**：高压缩比，优先考虑存储效率

## 注意事项

1. 确保所有数据库服务正常运行
2. 定期备份数据，防止数据丢失
3. 监控系统性能，及时调整配置
4. 根据实际需求调整压缩和同步策略

## 故障排除

- **数据库连接失败**：检查数据库服务是否运行，配置是否正确
- **API服务启动失败**：检查Node.js和依赖是否正确安装
- **同步失败**：检查网络连接和数据库权限
- **性能问题**：调整数据库配置和压缩策略

## 许可证

本项目采用MIT许可证。
