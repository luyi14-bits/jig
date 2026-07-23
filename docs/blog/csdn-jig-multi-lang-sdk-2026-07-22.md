---
copyright: true
author: luyi14-bits
date: 2026-07-22
---

# Jig 多语言 SDK 设计之路 — 同一套 Agent 定义，三种语言实现

> 用 git orphan 分支实现 Python / TypeScript / Rust 三语言 SDK 的独立演进。SKILL.md 是共享协议，ToolGuard 是共享架构，各语言自由优化。

---

## 一、为什么需要多语言？

Agent 框架的用户不全是 Python 工程师。

- **Python 工程师**想要 `pip install jig` 之后 5 行代码跑通管道
- **Web 全栈开发者**想要 `npm install @jig/sdk` 在 Node/Deno/Bun 里编排 Agent
- **性能敏感场景**想要 `cargo install jig-rs` 纳秒级 ToolGuard 拦截

单一语言绑死了一个框架的用户上限。LangGraph 有 Python 和 JS 两个版本，CrewAI 只有 Python。Jig 从架构设计第一天就考虑了多语言——不是事后移植，是原生平行。

---

## 二、架构：SKILL.md 作为共享协议

多语言 SDK 的核心挑战不是"同一套代码翻译成不同语言"，而是**同一套 Agent 定义在不同语言中行为一致**。

Jig 的解法：**SKILL.md 是语言无关的 Agent 定义协议**。

```markdown
---
name: code-reviewer
description: "代码审查 Agent"
model: pro
tools: [read, write]
---

## 角色

高级代码审查工程师。检查 OWASP Top 10、性能反模式、代码风格。
```

这份文件在 Python 中被 Jig 的 `SkillParser` 解析，在 TypeScript 中被 `@jig/sdk` 解析，在 Rust 中被 `jig-rs` 解析。解析结果——Agent 名称、角色描述、模型分配、工具白名单——完全一致。

---

## 三、分支策略：孤儿分支

三种语言在**同一个 GitHub 仓库的三个孤儿分支**上独立演进：

```
GitHub: github.com/luyi14-bits/jig
├── python   ← Python SDK（当前，v0.5.0）
├── ts       ← TypeScript SDK（孤儿，从零开始）
└── rust     ← Rust Harness（孤儿，从零开始）
```

孤儿分支（orphan）意味着：
- 零共享 Git 历史，`python` 的提交不会出现在 `ts` 中
- 切换分支 = 完全不同的文件树
- 互不干扰，各自独立发布

但共享的是**协议层**——SKILL.md 规范、MCP 协议、A2A 协议、HandoverPackage 数据结构——这些在技术白皮书中定义，各语言独立实现。

---

## 四、TS SDK：抢用户

**为什么先做 TypeScript？**

| 因素 | 分析 |
|------|------|
| 用户基数 | npm 生态第一大语言，Web/全栈开发者必选 |
| LLM 生态 | OpenAI、Anthropic、Vercel AI SDK 全线支持 |
| 竞争空白 | **零个 TypeScript 原生多 Agent 编排框架** |
| 部署优势 | Wasm、Edge Functions、Deno/Bun 现代运行时 |

**如果已经有了 LangGraph.js，为什么还需要 Jig TS？** LangGraph.js 社区影响力远不如 Python 版，且继承自 LangGraph 的图状态机模型——Jig 的 SOP 管道模型更贴近实际开发流程。

**TS 分支初始结构**：
```
ts/
├── package.json
├── tsconfig.json
├── README.md
├── src/
│   ├── index.ts          # Jig class
│   ├── agent-factory.ts  # Agent 工厂
│   ├── skill-parser.ts   # SKILL.md 解析
│   ├── harness/
│   │   └── tool-guard.ts # ToolGuard 实现
│   └── adapters/
│       └── model-provider.ts
└── tests/
```

---

## 五、Rust SDK：建护城河

**为什么 Rust 是终极形态？**

| 优势 | 说明 |
|------|------|
| 性能 | ToolGuard 拦截在纳秒级，Python 方案毫秒级 |
| 安全背书 | Rust 的内存安全招牌与 ToolGuard "硬约束" 品牌完美对齐 |
| Wasm 编译 | 浏览器内运行 ToolGuard，Python 做不到 |
| 2026 势头 | 首次进入 TIOBE TOP10，社区狂热 |

**TS 和 Rust 的协同方式**：
- Rust 实现 ToolGuard / LoopEngine / CacheEngine 核心
- 通过 Wasm 编译，TS SDK 直接调用
- 未来 Python SDK 通过 PyO3 绑定调用同一套 Rust 核心

最终架构：
```
Python SDK ──→ PyO3 ──┐
                      │
TS SDK ──→ Wasm ──────┼──→ Rust Harness (ToolGuard + LoopEngine)
                      │
Rust SDK ─────────────┘
```

---

## 六、三种 SDK 的发布节奏

```
Phase 1 (现在)     Python SDK     已发布 v0.5.0
Phase 2 (近期)     TypeScript SDK  npm publish @jig/sdk
Phase 3 (中期)     Rust Harness    cargo publish jig-rs
Phase 4 (远期)     PyO3/Wasm 桥接  Rust → Python + TS 共享 Harness
```

三种 SDK 不追求同步发布。Python 继续迭代完善 API，TS 从零构建，Rust 聚焦核心引擎。每个 SDK 独立版本号、独立 CHANGELOG、独立 CI/CD。

---

## 七、挑战与应对

| 挑战 | 应对 |
|------|------|
| 各语言 API 不一致 | 统一 Spec：`Jig.run(prompt)` 行为必须一致 |
| 测试覆盖差距 | 各语言独立测试，共享 Scenario 文档 |
| 文档维护成本 | mkdocs 多语言版本，同一定位+不同代码示例 |
| 社区碎片化 | 统一 Issues 仓库，标签区分语言 |

---

## 八、总结

- **三语言不是"写三遍"**，而是同一套 Agent 定义协议的三种实现
- **SKILL.md 是共享协议**，语言无关
- **孤儿分支 + 独立文件树**，不互相干扰
- **TS 抢用户，Rust 建护城河，Python 稳基本盘**

> GitHub: [github.com/luyi14-bits/jig](https://github.com/luyi14-bits/jig)  
> 分支: `python` / `ts` / `rust`

**作者**：luyi14-bits | **协议**：MIT
