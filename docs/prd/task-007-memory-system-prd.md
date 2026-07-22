# IDEA-022: Agent Memory 体系重构 — PRD

> **版本**: v0.1 | **作者**: PM (Luyi14-pm-mentor) | **日期**: 2026-07-15

---

## 1. Executive Summary

新增统一的 MemoryManager 层，整合现有 CacheEngine / ContextPartitioner / EmbeddingIndex / ConversationCompressor 为一条完整的记忆管线。核心三大组件：LocalStore（SQLite 持久化）、MemoryRouter（分层路由）、Consolidator（记忆合并/老化）。

## 2. 架构

```
MemoryManager
├── LocalStore — SQLite 持久化（zero-dependency）
│   ├── profiles     — 用户/Agent 画像
│   ├── sessions     — 会话元数据（metadata）
│   └── memory_log   — 记忆日志
├── MemoryRouter — 分层路由
│   ├── working      → ContextPartitioner.immutable (现有)
│   ├── summary      → Flash LLM 定期摘要 (新增)
│   ├── episodic     → SQLite 存 HandoverPackage 历史 (新增)
│   └── semantic     → EmbeddingIndex 索引对话记忆 (增强)
└── Consolidator — 记忆合并与老化
    ├── forget()     — 低价值记忆衰退
    └── merge()      — 相似记忆融合
```

## 3. 组件详述

### 3.1 LocalStore
- SQLite 三表，标准库自带，零外部依赖
- `profiles`: agent TEXT, key TEXT, value_json TEXT, updated_at TIMESTAMP
- `sessions`: session_id TEXT, metadata_json TEXT, created_at TIMESTAMP
- `memory_log`: id INTEGER PK, agent TEXT, type TEXT(working/summary/episodic/semantic), content_json TEXT, created_at TIMESTAMP

### 3.2 MemoryRouter
- `working`：现有 ContextPartitioner.immutable 区，不动
- `summary`：调用 ConversationCompressor（升级为 Flash LLM 摘要，离线降级保留）
- `episodic`：存入 SQLite memory_log，支持按 agent/时间/类型查询
- `semantic`：EmbeddingIndex 增强，同时索引 skill body + 对话记忆

### 3.3 Consolidator
- `forget()`：根据访问频率和时效性评分，低于阈值标记删除
- `merge()`：相同 topic 的连续摘要合并为一条综合摘要

## 4. 文件改动清单

| 文件 | 改动 |
|------|------|
| `src/jig/core/__init__.py` | 导出 MemoryManager |
| `src/jig/orchestrator/memory.py` | **新建** — MemoryManager + LocalStore + Consolidator |
| `src/jig/adapters/conversation_compressor.py` | 升级 _make_summary 为 Flash LLM 模式 |
| `src/jig/adapters/embedding_index.py` | 新增 add_conversation()，双索引 |
| `tests/test_memory.py` | **新建** — 5 个测试 |

## 5. Out of Scope
- IDEA-021 的 Consolidator 老化机制（共享设计，先只做持久化不做过期删除）
- IDEA-023~027 的用户配置界面（后续迭代）

## 6. Success Metrics
- test_memory.py 5/5 通过
- 全量测试 无回归
- LocalStore 读写延迟 < 50ms
