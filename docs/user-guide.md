# Jig 用户指南

> **版本**: Alpha 0.2 | **适用**: Python 3.10+

---

## 快速开始

### 安装

```bash
pip install jig
```

或从源码安装：

```bash
git clone https://github.com/luyi14-bits/jig.git
cd jig
pip install -e .
```

### 配置

设置 DeepSeek API Key：

```bash
export JIG_API_KEY="sk-your-key-here"
```

### 最小示例

```python
from jig import Jig

# 5 行代码启动 SOP 管道
app = Jig(skills_dir="./skills")
result = app.run("做一个登录功能")
print(result)
```

---

## CLI 使用

### 查看所有可用 Agent

```bash
python -m jig.cli.main --skill-dir skills --list
```

### 启动群聊模式

```bash
python run.py
```

### 审查 Agent 的完整 Prompt

```bash
python -m jig.cli.main --skill-dir skills --inspect pm-mentor
```

### 挂载自定义 Skill

```bash
python run.py --attach my-custom-skill
```

---

## FastAPI 服务

```bash
python -m jig.server.app
# POST /execute  — 运行管道
# GET  /status   — 服务健康检查
```

---

## Skill 自定义

Skill 是 Jig 的核心扩展机制。每个 Skill 是一个 `SKILL.md` 文件：

```markdown
---
name: my-agent
description: "我的自定义 Agent"
model: flash
tags: [custom, utility]
---

## 角色设定

你是一个自定义 Agent...

## 工作流程

1. 接收用户需求
2. 分析并执行
3. 产出 HandoverPackage
```

将 `my-agent/SKILL.md` 放入 `skills/` 目录后，Jig 自动加载。

---

## 架构概述

```
Jig
├── Harness 层     — ToolGuard + LOOP SOP 门禁 + 全局约束
├── Agent 层       — 13 个预设角色 + 自定义 Skill 映射
├── 编排层         — 顺序/并行/层级调度 + 检查点 + 熔断
└── 工具层         — MCP 客户端 + 缓存引擎 + 上下文分区 + 嵌入索引
```
