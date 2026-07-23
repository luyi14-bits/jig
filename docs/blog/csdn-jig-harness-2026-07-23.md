---
copyright: true
top: true
author: luyi14-bits
date: 2026-07-23
updated: 2026-07-23
tags: [Agent, Harness, ToolGuard, 安全, DeepSeek]
---

# 当 OpenAI 和 LangChain 都在谈"Harness"，Jig 的 Harness 凭什么不一样？

> deepagents 说 "trust the LLM"。Jig 说 "verify before execute"。
> 代码级事前拦截 vs prompt 级事后劝说——这就是差距。

---

## 一、巨头入场，"Harness" 成了 2026 热词

2026 年，Agent 框架赛道突然集体打上了 "Harness" 标签：

- **deepagents**（26.7k★）— LangChain 出品，自称 "The batteries-included agent harness"
- **OpenAI Agents SDK**（28.1k★）— GitHub topics 里赫然标着 "harness"
- **Hive**（10.8k★）— "Multi-Agent Harness for Production"
- **Strands harness-sdk**（6.7k★）— 名字直接就叫 harness

听起来很美——"Agent 的缰绳"、"Agent 的管控层"。

但仔细看它们的实现，你会发现它们的 "harness" 其实是一个**便利层**：集成工具、管理子 Agent、传递上下文。安全保障全部停在 prompt 层面。

deepagents 自己在 README 里承认得非常坦白：

> *"Deep Agents follows a 'trust the LLM' model. The agent can do anything its tools allow."*

翻译成人话：Agent 想干什么就能干什么，安全边界全靠 prompt 劝。

这是一个巨大的盲区——而 Jig 的 Harness，就是填补这个盲区而生的。

---

## 二、prompt 级"安全"为什么形同虚设

先看巨头们的做法：

```python
# 巨头的"安全"——全在 prompt 里
system_prompt = "你是安全助手，不要删除文件、不要执行危险命令"

# 但 Agent 实际执行时：
# "Let me clean up by running rm -rf /tmp/*"
# → 没有任何机制阻止它
```

这不是 bug，这是架构选择。LLM 本身就是 text-in-text-out，prompt 对它来说只是"建议"，不是"命令"。当用户说"帮我清理服务器"时，Agent 完全可能推断出应该先 `rm -rf`。

再看 Jig 的做法：

```python
from jig.adapters.mcp_client import ToolGuard

# Agent 想删除文件 — 代码级阻断
ToolGuard.check("coding", "Bash(rm -rf /)")  # → False，直接拦截
```

核心区别：

| | prompt 级别 | 代码级别 |
|---|---|---|
| 性质 | 建议 | **法律** |
| Agent 能绕过吗 | ✅ 一句话就行 | **❌ 绕不过** |
| 修改成本 | 改一行 prompt | **改代码，走 CI/CD** |

prompt 是"建议"，代码是"法律"。Agent 可以选择忽略建议，但绕不过代码。

---

## 三、拆解 ToolGuard — 真正的 Agent 防火墙

Jig 的 ToolGuard 有三层拦截架构：

```
Agent 发起工具调用
    │
    ▼
[Layer 1: 白名单] ── 不匹配 → 🚫 拦截 + 写日志
    │ 通过
    ▼
[Layer 2: 黑名单] ── 命中   → 🚫 拦截 + 写日志
    │ 通过
    ▼
[Layer 3: PreToolUse 钩子] ── 不通过 → 🚫 拦截 + 写日志
    │ 通过
    ▼
✅ 真正执行工具
```

真实代码取自 `src/jig/adapters/mcp_client.py`：

```python
class ToolGuard:
    # 白名单：每个角色能调什么工具，精确到工具级别
    WHITELIST = {
        "pm":     ["web_search", "fetch_page", "Read", "Grep"],
        "coding": ["Read", "Write", "Edit", "Bash", "Glob", "Grep"],
        "ops":    ["Bash", "Glob", "Read", "Write"],
    }

    # 黑名单：全局禁止的操作——谁都不行
    DENYLIST = [
        "Bash(rm -rf /)",      # 删根目录
        "Bash(drop table)",    # 删数据库
        "Bash(shutdown)",      # 关机
        "Write(/etc/)",        # 写系统配置文件
    ]

    @classmethod
    def check(cls, agent_role: str, tool_name: str, tool_args: str = "") -> bool:
        # Step 1: 黑名单优先
        for denied in cls.DENYLIST:
            if tool_name in denied:
                return False  # 代码级阻断，Agent 绕不过

        # Step 2: 白名单检查
        allowed = cls.WHITELIST.get(agent_role, [])
        if tool_name in allowed:
            return True  # 在白名单内，放行

        # Step 3: 默认拒绝
        return False
```

关键设计细节：**PM agent 的白名单没有 Write 和 Bash**，所以即使 prompt 被注入，PM agent 也永远不可能写文件或执行命令。

很多团队问："那你放行的工具怎么保证安全？"
答案是**按角色收敛权限面**——Coding agent 能写代码但不能操作数据库，Ops agent 能执行命令但不能修改业务代码。每个 Agent 的权限精确到工具+参数级别。

---

## 四、不只有 ToolGuard — Harness 的完整武器库

ToolGuard 只是 Jig 的 Harness 体系的第一道防线。完整武器库还包括：

### 1. LOOP SOP 5 级门禁

每个阶段必须通过验收才能推进：

```
G0(PRD) → G1(Spec) → G2(Tasks) → G3(Code) → G4(Acceptance)
   ↑          ↑          ↑          ↑            ↑
   └── 门禁 ──┴── 门禁 ──┴── 门禁 ──┴── 门禁 ────┘
```

不通过自动回退到上一阶段。代码示例：

```python
class GateCheck:
    @staticmethod
    def pass_gate(gate: str, artifacts: dict) -> bool:
        if gate == "G1":
            return "spec.md" in artifacts and "tasks.md" in artifacts
        elif gate == "G3":
            return all(t.passed for t in artifacts["tests"])
        # ...
```

### 2. CircuitBreaker 三态熔断

```python
class CircuitBreaker:
    def __init__(self, failure_threshold=3):
        self._state = "CLOSED"
        self._failures = 0

    def call(self, fn):
        if self._state == "OPEN":
            raise CircuitOpenError("熔断已激活")
        try:
            result = fn()
            self._failures = 0
            return result
        except Exception as e:
            self._failures += 1
            if self._failures >= 3:
                self._state = "OPEN"  # 自动熔断
            raise
```

连续失败 3 次后自动 OPEN，保护下游不被击穿。

### 3. DriftDetector 漂移检测

Agent 的输出偏离预期模式时触发重检。例如 Coding agent 突然开始输出 SQL 而非代码，DriftDetector 会报警并中断执行。

### 4. GlobalConstraints 不可变约束

所有 Agent 共享的"铁律"——比如"永远不要连接生产数据库"、"不允许对外部 API 执行 POST 操作"。这些约束放在 DeepSeek 的缓存前缀中，每次请求自动命中，零额外延迟。

---

## 五、Meta-Harness — 你能用 Jig 管住别人的 Agent

这是 Jig 弯道超车的杀手锏：你不用放弃 deepagents、OpenAI SDK 或 Claude Code——你可以继续用它们，同时用 Jig 给它们加一层安全防护。

```python
# 让 Claude Code 每次工具调用都经过 Jig 的三层拦截
from jig.adapters.external_agent import ClaudeCodeAdapter

adapter = ClaudeCodeAdapter(tool_guard=ToolGuard)
adapter.start()

# Claude Code 尝试 rm -rf / 时，在 Jig 这层就会被直接拒绝
# Claude Code 完全不知道自己在被管控
```

这意味着，Jig 不需要比巨头的 Agent 更聪明——

**Jig 可以成为所有 Agent 的共享安全层。**

---

## 六、一张表说清楚

| 对比维度 | 巨头的 "Harness" | Jig 的 Harness |
|---------|:---------------:|:--------------:|
| **安全机制** | prompt 劝说 | **代码级阻断** |
| **拦截时机** | 事后审查或不审查 | **事前拦截** |
| **Agent 能绕过吗** | ✅ 一句话就能 | **❌ 代码层面绕不过** |
| **管自己的 Agent** | ✅ | ✅ |
| **管别人的 Agent** | ❌ | ✅ **Meta-Harness** |
| **成本治理** | ❌ | ✅ **CostAwareRouter** |
| **收敛检测** | ❌ | ✅ **LoopEngine** |
| **开源协议** | MIT / Apache | **MIT** |

---

Jig 不是一个"又一个 Agent 框架"。
它是在所有框架都选择 "trust the LLM" 的时候，唯一选择了 "verify before execute" 的那个。

当你团队用 deepagents 跑通第一个 POC 时觉得很爽——但想想生产环境上线时，谁敢让 Agent 有权限执行任意 Bash 命令？

Agent 的能力很强。**但能力越强，越需要 Harness。**

---

**GitHub**: https://github.com/luyi14-bits/jig  
**安装**: `pip install jig`  
**技术白皮书**: `docs/technical-whitepaper-v3.md`  
**架构定位**: `docs/agent-firewall-positioning.md`
