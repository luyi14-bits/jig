# v0.5.0 — 多模型 + 流式

**Date**: 2026-07-22  
**IDEA**: 058 + 059  
**内容**: 多模型 Provider 抽象 + 流式输出

## 新增
- BaseModelProvider 抽象基类
- DeepSeekProvider（deepseek-v4-flash / deepseek-v4-pro）
- OpenAIProvider（兼容 OpenAI API）
- ModelRouter（多 Provider 注册/路由）
- StreamChunk + chat_stream 异步迭代器
- ModelResponse 统一响应格式

## 回退命令
```bash
git revert v0.5.0
```
