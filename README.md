# GVEDC-trading-stocks-refine

## 版本

**v1.0.1** - 分层策略 + 多Agent团队版

## 项目简介

GVEDC-trading-stocks-refine 是一个基于五层决策迭代机制的项目执行分析系统，从AI炒股系统的决策机制演变而来。

## 核心特性

### 1. 五层决策迭代机制

- **遇到错误才迭代**（不是定时60秒）
- 数据层 → 模型层 → 策略层 → 执行层 → 评估层

### 2. 分层策略系统

- **顶层策略**：确定修复方向
- **中间层策略**：具体执行方法
- **细节层策略**：具体操作命令

### 3. 多Agent团队

- **主Agent**：协调工作流程
- **数据采集Agent**：收集错误上下文
- **分析Agent**：分析问题根因
- **策略Agent**：生成分层策略
- **执行Agent**：执行修复命令
- **评估Agent**：评估修复效果

### 4. 轻量级数据库

- **SQLite**：存储结构化数据
- **ChromaDB**：向量数据库（可选）

## 系统架构

```
GVEDC-trading-stocks-refine/
├── config/                # 配置文件
├── scripts/               # 脚本文件
├── services/             # 服务代码
│   ├── iteration/         # 迭代核心
│   │   ├── main.py        # 主迭代系统
│   │   └── layered_strategy.py  # 分层策略
│   └── agent_team.py     # Agent团队
└── data/                 # 数据存储
```

## 快速开始

### 1. 安装依赖

```bash
pip install chromadb
```

### 2. 运行Agent团队

```bash
python services/agent_team.py
```

### 3. 运行迭代系统

```bash
python services/iteration/main.py
```

## 工作流程

```
检测到错误
    ↓
数据采集Agent → 收集错误上下文
    ↓
分析Agent → 分析问题根因
    ↓
策略Agent → 生成分层策略
    ↓
执行Agent → 执行修复
    ↓
评估Agent → 评估效果
```

## 数据存储

所有数据保存在 `data/` 目录：

- `agent_team.db` - Agent日志
- `strategies.db` - 分层策略
- `project.db` - 错误历史

## 来源

本项目从AI炒股系统的决策机制演变而来，将：

- 市场数据分析 → 项目错误分析
- 交易策略生成 → 解决方案生成
- 交易执行 → 修复执行
- 收益评估 → 修复效果评估

## 许可证

MIT License