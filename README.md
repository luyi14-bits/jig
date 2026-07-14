<div align="center">

# 🌲 Tree-SOP Agent

**群聊式多 Agent 软件开发工厂 —— 11 个角色、5 层记忆、硬约束 Harness**

[![License: AGPL v3](https://img.shields.io/badge/License-AGPL_v3-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python)](https://python.org)
[![DeepSeek](https://img.shields.io/badge/LLM-DeepSeek_V4-4B32C3)](https://deepseek.com)
[![Tauri](https://img.shields.io/badge/Desktop-Tauri_v2-FFC131?logo=tauri)](https://tauri.app)
[![Status](https://img.shields.io/badge/Status-Alpha_0.1-orange)](CHANGELOG.md)

</div>

---

> ⚠️ **声明**：本项目当前为**技术路线展示与技术验证**阶段，尚未达到生产可用级别。架构设计、核心模块和 SOP 管道已完成概念验证，欢迎研究、讨论和贡献。

---

## 这是什么？

Tree-SOP Agent 是一个**群聊式多 Agent 软件开发框架**。你像在群里发消息一样输入需求，11 个 AI 角色自动协作——从需求分析、架构评审、编码、测试到安全审计和部署，全流程自动完成。

**对标项目**：受 [Superpowers](https://github.com/obra/superpowers) (76k+★) 的 Skill→Agent 理念和 [CrewAI](https://github.com/crewAIInc/crewAI) 的角色编排模式启发，融入了自研的**硬约束 Harness 层**和**四层记忆体系**。

```
你: "帮我做一个登录功能，支持手机号+验证码"
         │
         ▼
    Dispatcher ─── 理解意图，启动管道
         │
         ▼
    PM Agent ───→ Trinity 架构评审
         │
         ▼
    Spec-Pipeline ─── 拆分任务 + 验收清单
         │
         ▼
    Coding Agent ───→ Code-Review Agent
         │                    │
         ▼                    ▼
    TDD Agent ←────── CR Report
         │
         ▼
    Acceptance + Security（并行验收 + 安全审计）
         │
         ▼
    DevOps Agent ─── 构建发布
         │
         ▼
    Secretary Agent ─── 留痕看板 + 版本快照
```

---

## 🆚 与同类项目的关键差异

| 维度 | CrewAI | MetaGPT | AutoGPT | OpenHands | **Tree-SOP Agent** |
|------|:------:|:-------:|:-------:|:---------:|:------------------:|
| **硬约束层** | ❌ prompt-only | ❌ prompt-only | ❌ prompt-only | ❌ prompt-only | ✅ **ToolGuard + LOOP SOP 5 级门禁** |
| **角色体系** | 通用可定义 | 软件公司模拟 | 单 Agent | 编码 Agent | ✅ **11 个预设角色 + 自定义挂载** |
| **记忆架构** | 短期记忆 | 消息共享 | 向量存储 | 对话上下文 | ✅ **四层记忆 + 五层压缩** |
| **缓存优化** | — | — | — | — | ✅ **前缀 hash 不变性 + 三层 Context 分区** |
| **失败处理** | 手动重试 | 手动重试 | 循环重试 | 无内置 | ✅ **自动降级 + 熔断器 + 检查点恢复** |
| **桌面应用** | ❌ | ❌ | ❌ | ❌ | ✅ **Tauri v2 + Monaco + xterm.js** |
| **开源协议** | MIT | MIT | Apache 2.0 | MIT | **AGPL v3** |

---

## 🏗️ 架构

```
┌──────────────────────────────────────────────────────────────┐
│                    Control Plane (Harness)                    │
│   LOOP SOP · ToolGuard · GlobalConstraints · MemoryRouter    │
├──────────────────────────────────────────────────────────────┤
│                    Agent Plane                                │
│   SkillParser → SkillRegistry → AgentFactory → Agent         │
│   HandoverPackage · Dispatcher · IntentRouter                │
├──────────────────────────────────────────────────────────────┤
│                    Orchestration Plane                        │
│   SequentialOrch · ParallelOrch · HierarchicalOrch           │
│   CheckpointManager · ConversationCompressor                │
├──────────────────────────────────────────────────────────────┤
│                    Tool Plane                                 │
│   MCPClient · ToolGuard · RepoMap · EmbeddingIndex           │
│   DeepSeekAdapter · CacheEngine · ContextPartitioner         │
└──────────────────────────────────────────────────────────────┘
```

### 四层记忆体系

```
Layer 1: CacheEngine         — 前缀组装 + SHA-256 hash 快照，最大化 DeepSeek 缓存命中
Layer 2: ContextPartitioner  — immutable / append-only / volatile 三层分区
Layer 3: EmbeddingIndex      — Skill 语义检索（sentence-transformers / 关键词降级）
        + ConversationCompressor — hybrid/truncate/summarize 三模式压缩
Layer 4: CheckpointManager   — JSON 检查点持久化
        + write_log()        — Agent 自动留痕 LOG.md
```

---

## 🚀 快速开始

### 环境要求

- Python 3.10+
- DeepSeek API Key（环境变量 `DEEPSEEK_API_KEY`）

### 安装

```bash
git clone https://github.com/luyi14-bits/tree-sop-agent.git
cd tree-sop-agent
pip install pydantic pydantic-settings pyyaml
```

### 运行

```bash
# CLI 模式 — 加载所有 Skill 并自检
python auto_test.py

# 群聊模式 — Dispatcher 入口
python run.py

# 挂载自定义 Skill
python run.py --attach my-custom-skill

# 查看 Agent prompt 组装结果
python -m src.tree_sop_agent.cli.main --skill-dir skills --inspect pm-mentor
```

---

## 📁 项目结构

```
tree-sop-agent/
├── src/tree_sop_agent/
│   ├── core/            # SkillDef · Parser · Registry · AgentFactory
│   ├── adapters/        # DeepSeekAdapter · CacheEngine · Context · MCPClient
│   ├── orchestrator/    # Sequential · Parallel · Hierarchical · Checkpoint
│   ├── cli/             # CLI 入口
│   └── server/          # FastAPI 独立部署
├── skills/              # Agent 定义 SKILL.md + 留痕 LOG.md
├── desktop/             # Tauri v2 桌面应用壳
├── tests/               # pytest 测试套件（47 个测试）
├── docs/                # 技术白皮书 · PRD · 框架调研
└── versions/            # 版本快照
```

---

## 🗺️ 路线图

| 阶段 | 内容 | 状态 |
|------|------|:----:|
| Phase 0 | 调研 10+ 开源 Agent 框架 | ✅ |
| Phase 1–2 | Skill→Agent 映射 + DeepSeek 双模型接入 | ✅ v0.1.0 |
| Phase 3–4 | 编排调度器 + 检查点 + 上下文压缩 | ✅ v0.2.0 |
| Phase 5 | 完整 5 级 SOP 管道 + 自测 | ✅ v0.4.0 |
| Phase 6 | Tauri 桌面应用壳 | ✅ v1.0.0 |
| Phase 7 | 真·Tauri 原生桌面（IDEA-018 P0） | 🔄 开发中 |
| Phase 8 | SQLite 持久记忆 + 跨 session RAG（IDEA-022 P0） | 💡 |
| Phase 9 | CircuitBreaker + DriftDetector（IDEA-021 P1） | 💡 |
| Phase 10 | HyDE 查询路由 + 生产级稳定（IDEA-020 P1） | 💡 |

---

## 📄 开源协议

[GNU Affero General Public License v3.0](LICENSE)

> AGPL v3 要求：如果你修改了本项目并作为网络服务提供，你必须公开修改后的源代码。

---

<div align="center">
  <sub>Built with ❤️ by Tree-SOP Agent Contributors · 2026</sub>
</div>
