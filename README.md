# GVEDC-trading-stocks-refine

<!-- Badges -->
<div align="center">

[![Version](https://img.shields.io/badge/version-1.0.1-blue.svg)](https://github.com/quick123-666/GVEDC-trading-stocks-refine)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8+-yellow.svg)](https://www.python.org/)
[![Agent](https://img.shields.io/badge/agent-multi--agent-orange.svg)]()
[![Status](https://img.shields.io/badge/status-active-success.svg)]()

</div>

---

## 📖 项目简介

**GVEDC-trading-stocks-refine** 是一个基于五层决策迭代机制的项目执行分析系统，从AI炒股系统的决策机制演变而来。

系统通过多Agent团队协作，实现遇到错误时自动分析问题、生成解决方案并执行修复的智能迭代能力。

---

## 🎯 核心特性

### 1. 五层决策迭代机制
> 遇到错误才迭代，不是定时60秒

| 层级 | 功能 | 说明 |
|:---:|------|------|
| 数据层 | 收集错误上下文 | 采集错误信息、traceback、上下文 |
| 模型层 | 分析问题根因 | 识别错误类型、严重度 |
| 策略层 | 生成分层策略 | 顶层→中间层→细节层 |
| 执行层 | 执行修复命令 | 自动化执行解决方案 |
| 评估层 | 评估修复效果 | 验证修复成功率 |

### 2. 分层策略系统

```
┌─────────────────────────────────────────────────────┐
│                    顶层策略（Top Layer）              │
│              确定修复方向：自动修复依赖问题           │
├─────────────────────────────────────────────────────┤
│                    中间层策略（Middle Layer）        │
│              具体方法：pip安装 / 语法检查           │
├─────────────────────────────────────────────────────┤
│                    细节层策略（Bottom Layer）        │
│              具体命令：pip install <package>        │
└─────────────────────────────────────────────────────┘
```

### 3. 多Agent团队

| Agent | 职责 | 状态 |
|------|------|:----:|
| 🏢 主Agent | 协调工作流程 | ✅ |
| 📊 数据采集Agent | 收集错误上下文 | ✅ |
| 🔍 分析Agent | 分析问题根因 | ✅ |
| 📋 策略Agent | 生成分层策略 | ✅ |
| ⚙️ 执行Agent | 执行修复命令 | ✅ |
| 📈 评估Agent | 评估修复效果 | ✅ |

---

## 🏗️ 系统架构

```
GVEDC-trading-stocks-refine/
│
├── config/                          # 配置文件
│   ├── databases.yml                # 数据库配置
│   ├── compression.yml             # 压缩策略
│   ├── routing.yml                  # 查询路由
│   └── sync.yml                     # 数据同步
│
├── scripts/                         # 脚本文件
│   ├── setup.bat                    # 系统初始化
│   ├── start.bat                    # 启动服务
│   ├── stop.bat                     # 停止服务
│   ├── backup.bat                   # 数据备份
│   └── monitor.bat                  # 系统监控
│
├── services/                        # 服务代码
│   ├── iteration/                   # 迭代核心
│   │   ├── main.py                  # 主迭代系统
│   │   └── layered_strategy.py      # 分层策略
│   │
│   └── agent_team.py                # Agent团队
│
└── data/                           # 数据存储
    ├── agent_team.db                # Agent日志
    ├── strategies.db                # 分层策略
    └── project.db                   # 错误历史
```

---

## 🚀 快速开始

### 环境要求

- Python 3.8+
- SQLite3
- ChromaDB (可选，向量搜索)

### 安装依赖

```bash
pip install chromadb
```

### 运行Agent团队

```bash
python services/agent_team.py
```

### 运行迭代系统

```bash
python services/iteration/main.py
```

---

## 📊 工作流程

```
检测到错误
    │
    ▼
┌─────────────────┐
│ 数据采集Agent    │ ──→ 收集错误上下文
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   分析Agent      │ ──→ 分析问题根因
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   策略Agent      │ ──→ 生成分层策略
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   执行Agent      │ ──→ 执行修复命令
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   评估Agent      │ ──→ 评估修复效果
└─────────────────┘
```

---

## 💡 技术栈

| 技术 | 用途 | 状态 |
|------|------|:----:|
| Python | 核心开发语言 | ✅ |
| SQLite | 结构化数据存储 | ✅ |
| ChromaDB | 向量数据库 | ✅ |
| Agent模式 | 多Agent协作 | ✅ |
| 分层策略 | 决策机制 | ✅ |

---

## 📁 数据存储

所有数据保存在 `data/` 目录：

| 文件 | 用途 | 说明 |
|------|------|------|
| `agent_team.db` | Agent日志 | 记录各Agent活动 |
| `strategies.db` | 分层策略 | 存储策略层级关系 |
| `project.db` | 错误历史 | 错误和解决方案记录 |

---

## 🔄 版本历史

| 版本 | 日期 | 更新内容 |
|:----:|------|----------|
| v1.0.1 | 2026-04-19 | 分层策略 + 多Agent团队 |
| v1.0 | 2026-04-19 | 初始版本 |

---

## 📖 来源说明

本项目从**AI炒股系统**的决策机制演变而来：

| 炒股系统 | 项目执行系统 |
|----------|--------------|
| 市场数据分析 | 项目错误分析 |
| 交易策略生成 | 解决方案生成 |
| 交易执行 | 修复执行 |
| 收益评估 | 修复效果评估 |

---

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

---

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

---

<div align="center">

**如果这个项目对您有帮助，请给一个 ⭐**

Made with ❤️ by [quick123-666](https://github.com/quick123-666)

</div>