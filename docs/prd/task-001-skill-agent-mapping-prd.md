# TASK-001: Skill → Agent 映射架构设计（DeepSeek 专用版）PRD

> **版本**：v0.1 | **作者**：PM Mentor (Luyi14-pm-mentor) | **日期**：2026-07-13 | **状态**：初稿

---

## 1. Executive Summary

本项目旨在创建一个 **Jig 系统**，将结构化的 skill 定义文件自动映射为独立的 AI Agent，支持树形 SOP 编排、DeepSeek V4 Pro/Flash 混用策略、以及缓存优化架构。核心产出是一个可嵌入编程 AI 工具或独立部署的 Agent 编排引擎，让开发工作流中的每个 skill（PM、架构师、编码员、验收员等）自动获得独立 Agent 能力，按树形 SOP 协同完成软件开发。

---

## 2. Problem Statement

### 用户痛点

| 痛点 | 频率 | 严重度 | 业务影响 |
|------|:----:|:------:|---------|
| 每次开发迭代需要在不同 Agent 手动切换上下文 | 每天数次 | 🔴 严重 | 效率损失 30%+，频繁出界 |
| 同一 session 中 Pro 模型做简单编码太贵 | 每次请求 | 🟠 中等 | API 成本浪费 60-70% |
| DeepSeek 缓存命中率波动导致费用不可控 | 每轮迭代 | 🟠 中等 | 费用从 $0.01 到 $10+ 不可控 |
| Agent 定义格式不一致，跨项目复用困难 | 每周数次 | 🔴 严重 | 每次新项目从零配 |
| Function Calling 在 DeepSeek 上频繁踩坑 | 每次集成 | 🟠 中等 | 调试耗时数小时 |
| 没有树形 SOP 结构，复杂任务无法拆解为子 Agent 协作 | 每次大功能 | 🔴 严重 | 单 Agent 上下文爆满 |

### 业务影响

- 当前单次复杂开发迭代的 API 成本可控制在 **$0.02-0.10**（cache hit 价格）
- 项目周期从"周"级压缩到"天"级
- 减少 80% 的手动 Agent 上下文切换

---

## 3. Goals & Metrics

### SMART 目标

| 指标 | 当前 | 目标 | 测量方式 |
|------|:----:|:----:|---------|
| 缓存命中率 | 不适用（新项目） | >99% session 级 | cache-guard CI 测试 |
| 模型成本效率 | 全 Pro | Flash 覆盖 70% 简单任务 | Token 计费分析 |
| Skill → Agent 映射时间 | 手动配置数小时 | 自动 0 延迟 | 启动时延基准测试 |
| SOP 编排支持层级 | 无 | ≥3 层树形嵌套 | 端到端 SOP 测试 |
| DeepSeek API 兼容性 | 无适配层 | 零 400 错误 | CI 兼容性测试 |

---

## 4. User Personas

### Persona 1：AI 编程工具用户（老板）
- **背景**：使用 Cursor/Continue/WindSurf 等 AI 编程工具的开发者
- **需求**：一键启动复杂开发流程，多个 Agent 自动接力
- **痛点**：手动切换 Agent 模式、重复写提示词

### Persona 2：Tree-SOP 系统开发者
- **背景**：维护和扩展 Jig 系统的工程师
- **需求**：清晰的 skill 定义格式、可测试的映射引擎、明确的扩展点
- **痛点**：文档不全、API 兼容性陷阱多

### Persona 3：独立部署用户
- **背景**：后端服务集成场景
- **需求**：REST API / CLI 调用 Jig 工作流
- **优先级**：P2（后续迭代）

---

## 5. User Stories

### Story 1：Skill 自动映射为 Agent
```gherkin
Given 我有一个定义好的 skill 文件（SKILL.md）包含角色描述和工具列表
When 系统启动时加载这个 skill
Then 自动生成一个对应角色的 Agent 实例
And 该 Agent 具备 skill 中定义的角色预设和工具集
```

### Story 2：Pro/Flash 分模型策略
```gherkin
Given 系统配置了 Pro（复杂推理）和 Flash（快速执行）两种模型
When PM/Mentor/Security skill 被调度
Then 使用 Pro 模型处理
When Coding/TDD 等执行型 skill 被调度
Then 使用 Flash 模型处理
And 不同模型的 session 互相独立
```

### Story 3：缓存命中率保障
```gherkin
Given 系统正在运行一个 session
When 每次 API 请求发送前
Then 系统提示词前缀（system + tools + memory + skill 索引）被验证为字节级不变
And 任何变更导致前缀变化被记录到诊断日志
```

### Story 4：Function Calling 兼容
```gherkin
Given DeepSeek API 在 thinking 模式下有特定的 reasoning_content 规则
When 系统发送带 tool_calls 的请求
Then 必须原样保留上轮 response 中的 reasoning_content
When 消息不含 tool_calls
Then 不发送 reasoning_content
```

### Story 5：三层 Context 分区
```gherkin
Given 系统构建 API context
When 组织消息结构
Then 分为不可变前缀、追加日志、易失暂存三个区域
And 不可变前缀整 session 命中缓存
```

### Story 6：树形 SOP 编排
```gherkin
Given 有一个定义了多个阶段和子 Agent 的 SOP 树
When 系统执行这个 SOP
Then 按定义的顺序/并行/层级调度子 Agent
And 每个子 Agent 只获取其角色相关上下文
```

---

## 6. Functional Requirements

### FR-1：Skill 定义格式规范
| ID | 需求 | 优先级 |
|----|------|:----:|
| FR-1.1 | Skill 定义文件使用结构化 Markdown（类似 SKILL.md 格式） | P0 |
| FR-1.2 | frontmatter 必须包含 name、description、tools、model 字段 | P0 |
| FR-1.3 | 支持树形 SOP 嵌套定义（子 Skill 引用） | P0 |
| FR-1.4 | 支持工具声明（MCP server / shell / API） | P0 |

### FR-2：Agent 映射引擎
| ID | 需求 | 优先级 |
|----|------|:----:|
| FR-2.1 | Skill 加载时自动解析 frontmatter 生成 Agent 配置 | P0 |
| FR-2.2 | Agent 实例化时注入角色预设（system prompt） | P0 |
| FR-2.3 | 支持 Agent 间上下文隔离（不互相污染） | P0 |
| FR-2.4 | 支持 Agent 间结果传递（交接包协议） | P0 |

### FR-3：DeepSeek 模型策略
| ID | 需求 | 优先级 |
|----|------|:----:|
| FR-3.1 | Pro 模型用于规划/审查/安全/PM 类 skill | P0 |
| FR-3.2 | Flash 模型用于编码/测试/执行类 skill | P0 |
| FR-3.3 | 不同模型使用独立 session（各自缓存前缀独立） | P0 |
| FR-3.4 | 支持用户覆盖默认模型分配 | P1 |

### FR-4：缓存优化
| ID | 需求 | 优先级 |
|----|------|:----:|
| FR-4.1 | 系统提示词前缀按固定顺序组装（base → output style → language → memory → skill 索引） | P0 |
| FR-4.2 | skill 正文按需加载不进缓存前缀 | P0 |
| FR-4.3 | 每轮请求记录前缀快照与命中率诊断 | P1 |
| FR-4.4 | CI 中 cache-guard 测试防止缓存退化 | P1 |

### FR-5：Function Calling 适配层
| ID | 需求 | 优先级 |
|----|------|:----:|
| FR-5.1 | 带 tool_calls 的 assistant 消息原样回传 reasoning_content | P0 |
| FR-5.2 | 不带 tool_calls 的消息不回传 reasoning_content | P0 |
| FR-5.3 | tool_choice 支持显式指定函数名称 | P0 |
| FR-5.4 | 多轮对话保留完整 tool_calls 历史 | P0 |
| FR-5.5 | deepseek-reasoner 模式不支持 FC 时自动降级 | P0 |

### FR-6：三层 Context 分区
| ID | 需求 | 优先级 |
|----|------|:----:|
| FR-6.1 | 不可变前缀：system + tools + memory | P0 |
| FR-6.2 | 追加日志：对话历史 append-only | P0 |
| FR-6.3 | 易失暂存：推理过程不发给 API | P0 |

### FR-7：编排调度器
| ID | 需求 | 优先级 |
|----|------|:----:|
| FR-7.1 | 支持顺序调度（串行执行子 Agent） | P0 |
| FR-7.2 | 支持并行调度（同时执行多个子 Agent） | P1 |
| FR-7.3 | 支持层级调度（树形 SOP 递归展开） | P0 |
| FR-7.4 | 子 Agent 执行结果汇总到父 Agent | P1 |

---

## 7. Non-Functional Requirements

| ID | 需求 | 指标 | 优先级 |
|----|------|:----:|:----:|
| NFR-1 | session 级缓存命中率 | >99% | P0 |
| NFR-2 | Agent 启动延迟 | <500ms | P1 |
| NFR-3 | API 费用可控 | Flash 覆盖 70% 请求 | P0 |
| NFR-4 | System prompt 前缀字节级不变性 | 零漂移 | P0 |
| NFR-5 | skill 正文懒加载 | 不影响前缀缓存 | P0 |
| NFR-6 | 多模型 session 完全隔离 | 无上下文泄漏 | P0 |
| NFR-7 | Function Calling 零 400 错误 | 100% | P0 |

---

## 8. Technical Considerations

### 架构要点
- **Skill 定义层**：结构化 Markdown + frontmatter → 类似 SKILL.md 但增加树形 SOP 字段
- **映射引擎层**：Skill → Agent 反射工厂 → Skill frontmatter → Agent config → 实例化
- **DeepSeek 适配层**：缓存前缀组装 + reasoning_content 处理 + FC 兼容
- **编排调度层**：顺序/并行/层级三种调度器

### 数据模型要点
- Skill 定义 → Agent 配置 → Session → Context → API 请求，逐层映射
- 缓存前缀不可变：`base prompt + output style + language + memory + skill 索引`
- skill 正文不在前缀中，通过 "name + description" 索引引用

### API 要点
- OpenAI 兼容接口（Reasonix 协议层可复用）
- DeepSeek 特有字段：`reasoning_content` 必须在 tool_calls 消息中原样回传
- `deepseek-reasoner` 不支持 FC → 自动降级到 `deepseek-chat`

---

## 9. Dependencies

| 前置条件 | 类型 | 状态 | 说明 |
|---------|:----:|:----:|------|
| Phase 0 调研报告 | 知识 | ✅ 完成 | 开源 Agent 框架调研完成 |
| Reasonix 源码分析 | 知识 | ✅ 完成 | 缓存策略、Context 分区、boot 流程 |
| DeepSeek API 文档 | 外部 | ✅ 已获取 | 缓存机制、FC 兼容性 |
| 现有 Luyi14 Skill 体系 | 内部 | ✅ 就绪 | 10 个 skill 已定义 |
| 编程 AI 工具接入规范 | 外部 | 🔄 待确认 | Cursor/Continue/WindSurf 插件规范 |

---

## 10. Out of Scope

| 项目 | 原因 | 后续迭代 |
|------|------|:--------:|
| 独立部署模式（REST API） | 当前专注 AI 编程工具插件 | P2 迭代 |
| 状态管理与检查点 | 核心映射引擎优先 | P1 迭代 |
| 完整开发工作流 UI | 先实现内核 | P1 迭代 |
| 多平台 GUI 界面 | CLI + 配置优先 | P2 迭代 |
| 非 DeepSeek 模型适配（仅 API 兼容层） | 当前专注 DeepSeek V4 | P2 迭代 |
| cache-guard CI 自动化 | 先实现缓存诊断基础 | P1 迭代 |

---

## 11. Success Metrics

| 指标 | 测量方法 | 目标值 |
|------|---------|:------:|
| 缓存命中率 | cache-guard 诊断 | >99% session 级 |
| 模型成本降低 | Pro vs Flash 请求比例 | Flash 覆盖 70% |
| Skill → Agent 映射覆盖 | 自动化测试 | 10/10 skill 正确映射 |
| SOP 编排正确性 | 端到端测试 | 100% 路径覆盖 |
| FC 适配层稳定性 | CI 兼容性测试 | 零 400 错误 |

---

## 12. Open Questions

| # | 问题 | 决策者 | 状态 |
|---|------|--------|:----:|
| 1 | Skill 定义文件的具体 frontmatter 字段列表（name/description/tools/model 外还需要什么？） | Spec-Pipeline + Trinity | 🔄 待决策 |
| 2 | 编程 AI 工具接入方式：custom tool / MCP server / raw API？ | 老板 | 🔄 待确认 |
| 3 | Pro/Flash session 隔离的具体粒度：按 skill / 按任务 / 按阶段？ | Spec-Pipeline | 🔄 待决策 |
| 4 | 缓存前缀组装顺序在内存中如何快速校验不变性？hash 快照 vs 字节级比对？ | Spec-Pipeline + Trinity | 🔄 待决策 |
| 5 | Skill 树形 SOP 嵌套的最大深度限制？ | Spec-Pipeline | 🔄 待决策 |

---

*PRD 版本：v0.1 | 下一阶段：移交 Spec-Pipeline 进行 Spec 编写和任务拆分*
