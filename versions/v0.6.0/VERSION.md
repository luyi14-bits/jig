# Version Snapshot — v0.6.0

> **日期**: 2026-07-23
> **分支**: `python`
> **Commit**: `48836bb`

## 交付内容

### 核心
- ToolGuard 三层硬约束（白名单+黑名单+PreToolUse Hook）
- SOPRunner（Checkpoint/Retry/Escalate/Resume）
- LoopEngine 收敛检测 + CircuitBreaker 三态熔断 + DriftDetector
- GraphOrchestrator（条件路由/并行/自环）
- Memory 四层体系（Cache→Partition→Embedding→SQLite）
- 多模型：DeepSeekProvider + OpenAIProvider + ModelRouter
- SSE 流式输出（StreamManager/chat_stream）

### 外围
- 12 个预置 Luyi14 Agent 角色
- CLI 入口 `python run.py`
- MkDocs 文档站点
- Agent Firewall 定位文档 + CSDN 文章 4 篇
- awesome-deepseek-agent PR #310

### 测试
- 127/127 全绿
- modular export fixes (adapters + orchestrator __init__.py)

## 缺失
- [ ] 多模型抽象 BaseModelProvider 待验收
- [ ] 流式输出 StreamManager 待集成
- [ ] Durable Execution 中断恢复
- [ ] Meta-Harness 外部 Agent 治理层
- [ ] PyPI 正式发布
