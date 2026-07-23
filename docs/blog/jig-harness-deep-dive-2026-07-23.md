# 当巨头都在谈"Harness"，Jig 的 Harness 有什么不同？

> deepagents 自称 "batteries-included agent harness"，OpenAI Agents SDK 打上 harness 标签。
> 但它们的 harness 和 Jig 的 Harness 是完全两个物种。一个靠 prompt，一个靠代码。

---

## 一、2026，"Harness" 成了热词

2026 年，"Harness" 突然成了 Agent 框架赛道的热词：

- **deepagents** (26.7k★) — "The batteries-included agent harness"，LangChain 出品
- **OpenAI Agents SDK** (28.1k★) — GitHub topics 里赫然标着 "harness"
- **Hive** (10.8k★) — "Multi-Agent Harness for Production"
- **Strands harness-sdk** (6.7k★) — 名字直接叫 harness

但仔细看它们的实现——安全保障都在 prompt 层面。没有一个是代码级的事前拦截。

---

## 二、"trust the LLM" 模式的根本缺陷

deepagents 自己在 README 承认：

> *"Deep Agents follows a 'trust the LLM' model. The agent can do anything its tools allow."*

翻译成人话：**Agent 想干什么就能干什么，安全边界全靠 prompt 劝。**

三行 prompt 就能绕过：

```python
# deepagents: prompt 级别的"安全"——Agent 可以无视
system_prompt = "You should not delete files or run dangerous commands..."

# Agent 实际回复：
# "I'll just run `rm -rf /` to clean up the workspace"  ← 拦不住
```

OpenAI Agents SDK 的 guardrails 也是 prompt-level 的——做输入输出验证，但不阻断工具调用本身。

这不是它们的疏忽，而是架构选择：**它们选择了"便利"，牺牲了"安全"。**

但 Agent 在企业落地时，真正需要的恰恰是后者。

---

## 三、Jig 的 Harness：代码级，事前，不可绕过

Jig 的 ToolGuard 有三层拦截机制：

```
Agent Tool Call
    │
    ▼
[Layer 1: Whitelist]  → PM agent 只能 read/search，不能 write/bash
    │ Pass
    ▼
[Layer 2: Denylist]   → 全局禁止 rm -rf /, drop table, shutdown...
    │ Pass
    ▼
[Layer 3: PreToolUse Hook] → 自定义回调，运行时动态判断
    │ Pass
    ▼
Execute Tool
```

关键代码（摘自 `src/jig/adapters/mcp_client.py`）：

```python
class ToolGuard:
    WHITELIST = {
        "pm": ["web_search", "fetch_page", "Read", "Grep"],
        "coding": ["Read", "Write", "Edit", "Bash", "Glob", "Grep"],
    }
    DENYLIST = [
        "Bash(rm -rf /)", "Bash(drop table)", "Write(/etc/)",
    ]

    @classmethod
    def check(cls, agent_role, tool_name, tool_args="") -> bool:
        # 黑名单 → 代码级阻断
        for denied in cls.DENYLIST:
            if tool_name in denied:
                return False  # Agent 绕不过
        # 白名单 → 按角色放行
        allowed = cls.WHITELIST.get(agent_role, [])
        if tool_name in allowed:
            return True
        return False  # 默认拦截未授权工具
```

对比一下：

```python
# 用户问："帮我清理服务器"
# deepagents: prompt 劝 → Agent 可能删
# Jig: ToolGuard.check("pm", "Bash(rm -rf /)") → False + raise BlockedError
```

---

## 四、不只是 ToolGuard：完整的 Harness 安全体系

Jig 的 Harness 不只是 ToolGuard——它是一个完整的"事前-事中-事后"安全体系：

### 事前：ToolGuard + GlobalConstraints
- 工具调用前白名单/黑名单检查
- 所有 Agent 共享的不可变约束规则
- 放在 DeepSeek 缓存前缀中，零开销

### 事中：LOOP SOP 5 级门禁
每个阶段必须通过验收才能推进，不通过自动回退：
```
PRD → Spec → Tasks → Code → Acceptance
  ↑       ↑       ↑      ↑         ↑
  └─ 门禁 ┴─ 门禁 ┴─ 门禁 ┴─ 门禁 ─┘
```

### 事后：CircuitBreaker + DriftDetector
- **CircuitBreaker**：连续失败自动 OPEN，保护下游不被击穿
- **DriftDetector**：Agent 输出偏离预期模式时触发重检
- **Checkpoint 恢复**：崩溃后从断点续跑，不重跑已完成节点

---

## 五、Jig 的 Harness 也能管巨头的 Agent（Meta-Harness）

这是弯道超车的核心：Jig 不需要比 deepagents/OpenAI 的 Agent 更聪明——它可以是这些 Agent 的**安全外挂**。

```python
# 用 Jig 的 ToolGuard 管控 Claude Code 的工具调用
from jig.adapters.external_agent import ClaudeCodeAdapter

adapter = ClaudeCodeAdapter(tool_guard=ToolGuard)
adapter.start()  # Claude Code 的每次工具调用都经过 Jig 三层拦截
```

这意味着：
- 你不用放弃 deepagents 或 Claude Code
- 你只需要在它们前面加一个 Jig 的 Harness 层
- 工具调用先过 Jig 再进 Agent——**Agent Firewall 模式**

---

## 六、两个 Harness，两个物种

| 对比维度 | 巨头的 Harness | Jig 的 Harness |
|---------|:--------------:|:--------------:|
| **安全层** | prompt 劝说 | **代码级阻断** |
| **拦截时机** | 事后审查 | **事前拦截** |
| **能否绕过** | ✅ Agent 一句话就能绕 | **❌ 代码层面绕不过** |
| **管自己的 Agent** | ✅ | ✅ |
| **管别人的 Agent** | ❌ | ✅ **Meta-Harness** |
| **成本治理** | ❌ | ✅ **CostAwareRouter** |
| **收敛检测** | ❌ | ✅ **LoopEngine** |

当巨头还在用 prompt "建议" Agent 不要做坏事时，Jig 在代码层面直接说 "No"。

---

*想试试？`pip install jig` 然后开一个 `.env` 写入 `DEEPSEEK_API_KEY=...` 即可。*

*技术白皮书：`docs/technical-whitepaper-v3.md`*
*定位文档：`docs/agent-firewall-positioning.md`*
*GitHub：`github.com/luyi14-bits/jig`*
