# Loop #2 PRD: 多模型支持 + 流式输出

**IDEA**: 058 + 059  
**Priority**: P0 (框架不成立)  
**Version**: v0.5.0  
**Date**: 2026-07-22

## 1. Executive Summary

Jig 当前只支持 DeepSeek，且 `run()` 返回纯字符串。这使得框架无法与其他模型配合，也无法提供实时用户体验。本 PRD 覆盖两个致命缺失：**多模型 Provider 抽象** 和 **流式输出**。

## 2. Problem Statement

- **多模型缺失**：开发者如果不用 DeepSeek，Jig 完全不可用
- **流式缺失**：Agent 返回完整结果才能展示，大任务等待时间 >30s
- **框架不成立**：LangGraph/PydanticAI 都标配多模型+流式

## 3. Functional Requirements

- FR-1: BaseModelProvider 抽象基类（chat + chat_stream + count_tokens）
- FR-2: DeepSeekProvider（deepseek-v4-flash / deepseek-v4-pro）
- FR-3: OpenAIProvider（兼容 OpenAI / 任何 OpenAI 兼容 API）
- FR-4: ModelRouter（注册/获取/默认/路由/可用列表）
- FR-5: StreamChunk 数据类（content / done / finish_reason）
- FR-6: chat_stream 异步迭代器（SSE 实时推送）
- FR-7: ModelResponse 统一格式（content / model / usage / finish_reason）

## 4. Out of Scope

- Anthropic/Claude Provider（接入简单，延后到社区 PR）
- Ollama 本地 Provider（延后）
- 多 Provider 自动故障切换（v0.6.0）

## 5. Success Metrics

- `from jig import ModelRouter, DeepSeekProvider, OpenAIProvider` 正常
- `router.chat(messages)` 正常返回
- `router.chat_stream(messages)` 异步迭代器正常
- 10+ 单元测试全绿
