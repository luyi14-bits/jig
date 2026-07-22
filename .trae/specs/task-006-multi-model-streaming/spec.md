# Spec: 多模型支持 + 流式输出

## Requirements

### ADDED
- R1: BaseModelProvider 抽象基类，定义 chat / chat_stream / count_tokens 接口
- R2: DeepSeekProvider 实现 DeepSeek V4 API
- R3: OpenAIProvider 实现 OpenAI 兼容 API
- R4: ModelRouter 管理多 Provider 注册/获取/路由
- R5: StreamChunk 数据类，支持流式块传输
- R6: chat_stream 异步迭代器，Server-Sent Events 实时推送
- R7: ModelResponse 统一响应格式

### Scenario (Gherkin)
```gherkin
Feature: 多模型支持

  Scenario: 注册并使用 DeepSeek Provider
    Given 一个已注册的 DeepSeekProvider
    When 调用 router.chat([{"role":"user","content":"hi"}])
    Then 返回 ModelResponse，content 非空

  Scenario: 注册并使用 OpenAI Provider
    Given 一个已注册的 OpenAIProvider
    When 调用 router.chat([{"role":"user","content":"hi"}], provider="openai")
    Then 返回 ModelResponse，model 包含 "gpt"

  Scenario: 流式输出
    Given 一个已注册的 Provider
    When 调用 router.chat_stream(messages)
    Then 逐块返回 StreamChunk
    And 最后一个 chunk 的 done=True
```

## Tasks

| # | Task | Est. | Status |
|---|------|:----:|:------:|
| 1 | BaseModelProvider 抽象基类 | 1h | ✅ DONE |
| 2 | DeepSeekProvider 实现 | 2h | ✅ DONE |
| 3 | OpenAIProvider 实现 | 2h | ✅ DONE |
| 4 | ModelRouter 实现 | 1h | ✅ DONE |
| 5 | StreamChunk + chat_stream | 2h | ✅ DONE |
| 6 | ModelResponse 数据类 | 0.5h | ✅ DONE |
| 7 | 单元测试 (10+) | 2h | ✅ DONE |

## Checklist

- [ ] `from jig import ModelRouter` 可导入
- [ ] `from jig import DeepSeekProvider` 可导入
- [ ] `from jig import OpenAIProvider` 可导入
- [ ] `router.register("ds", DeepSeekProvider(...))` 正常
- [ ] `router.chat(messages)` 正常
- [ ] `router.chat_stream(messages)` 异步迭代器正常
- [ ] `router.get("nonexistent")` 抛出 KeyError
- [ ] `StreamChunk(content="", done=True)` 格式正确
- [ ] `ModelResponse(content="...", model="...")` 格式正确
- [ ] 测试覆盖率 ≥90%
