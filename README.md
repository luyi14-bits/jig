<div align="center">

# ⚡ Jig-ToolGuard

**The first pre-execution Agent Firewall. Intercept before they act.**

[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-124%2F124-brightgreen)](tests/)
[![PyPI](https://img.shields.io/badge/PyPI-jig--toolguard-blue)](https://pypi.org/project/jig-toolguard/)
[![Status](https://img.shields.io/badge/Status-Alpha_v0.6.0-orange)](CHANGELOG.md)

---

**Jig-ToolGuard** is a Python multi-agent orchestration framework with a unique differentiator: **pre-execution safety gates**. While other frameworks rely on prompt-level guardrails that agents can bypass, Jig intercepts tool calls at the code level before execution.

Key capabilities:

- **ToolGuard** — Code-level whitelist/denylist for every tool call. No other framework does this.
- **11 preset agents** — PM, Spec, Coding, Code-Review, TDD, Acceptance, Security, DevOps, Secretary, Trinity, LOOP SOP
- **DeepSeek-native** — SHA-256 prefix caching, Flash-first cost routing, automatic FC repair
- **Multi-model** — DeepSeek + OpenAI extensible
- **SSE Streaming** — Real-time event stream via POST /stream
- **Graph Orchestration** — DAG-based pipeline with conditional routing
- **Memory** — 4-layer: Cache → Partition → Embedding → SQLite
- **CircuitBreaker** — 3-state (CLOSED/OPEN/HALF_OPEN) fault isolation
- **Convergence detection** — Automatic loop termination via LoopEngine
- **124 test suite** — Fully covered

```bash
pip install jig-toolguard
```

```python
from jig import Jig
app = Jig(skills_dir="./skills")
result = app.run("Review this code for security issues")
print(result)
```

---

> ⚠️ **Alpha Status**: v0.6.0. Core Agent Firewall is complete. Production use not yet recommended.

## Why Jig-ToolGuard?

- **🛡️ Pre-execution safety** — ToolGuard intercepts every tool call *before* execution via whitelist/blacklist at the code level. No other framework does this.
- **🧠 DeepSeek-native** — SHA-256 prefix caching, Flash-first cost-aware routing, automatic FC repair. Optimized for DeepSeek V4.
- **🔄 Loop Engineering** — Convergence detection, quality validation, checkpoint restore, event replay.
- **🧩 11 agents out of the box** — PM → Trinity → Spec → Coding → Code-Review → TDD → Acceptance → Security → DevOps → Secretary → LOOP SOP.
- **🌐 Multi-model + Streaming + Graph** — DeepSeek, OpenAI (extensible), SSE streaming, GraphOrchestrator.

---

## Quick Start

### 1. Install

```bash
pip install jig-toolguard
```

Or from source:

```bash
git clone https://github.com/luyi14-bits/jig.git
cd jig
pip install -e .
```

### 2. Configure

```bash
export DEEPSEEK_API_KEY="sk-your-key"
```

### 3. Run

```python
from jig import Jig

app = Jig(skills_dir="./skills")
result = app.run("Review src/ for security issues")
print(result)
```

### 4. CLI mode

```bash
python run.py
```

## Agent Firewall in 30 seconds

```python
from jig.adapters.mcp_client import ToolGuard

# PM agent tries to delete files — blocked at code level
ToolGuard.check("pm", "Bash(rm -rf /)")        # → False (blacklisted)
ToolGuard.check("pm", "Write(/etc/passwd)")    # → False (blacklisted)

# Coding agent tries to write code — allowed
ToolGuard.check("coding", "Write", "src/app.py")  # → True (whitelisted)
```

> **deepagents says "trust the LLM". Jig says "verify before execute."**

## SDK API

```python
from jig import Jig
from jig.adapters.mcp_protocol import MCPServer
from jig.core.skill_registry import SkillRegistry

app = Jig(skills_dir="./skills")
agents = app.list_agents()
result = app.run("Analyze this request")

# MCP protocol access
registry = SkillRegistry()
registry.register_skill_dir("./skills")
registry.load_all()
server = MCPServer(registry)
tools = server.list_tools()
```

## Architecture

```
Agent Firewall (Control Plane): ToolGuard · LOOP SOP · GlobalConstraints · CircuitBreaker
Agent Plane:             SkillParser → SkillRegistry → AgentFactory → Agents (via SKILL.md)
Orchestration Plane:    SOPRunner · Graph · LoopEngine · Memory · Checkpoint
Tool Plane:             MCP · ModelRouter · CacheEngine · CostAwareRouter · Streaming
```

## Comparison

| Dimension | deepagents | OpenAI SDK | LangGraph | CrewAI | PydanticAI | **Jig** |
|-----------|:----------:|:----------:|:---------:|:------:|:----------:|:-------:|
| **Pre-execution Intercept** | ❌ "trust LLM" | ❌ | ❌ | ❌ | ❌ | ✅ **Code-level** |
| **Hard Constraint** | ❌ prompt-only | ❌ prompt-only | ❌ | ❌ | ❌ | ✅ **Whitelist+Denylist** |
| **DeepSeek Cache** | — | — | — | — | — | ✅ **SHA-256 prefix** |
| **Memory** | Short-term | — | Checkpointer | Short-term | Context | ✅ **4-layer** |
| **Graph Engine** | ❌ | ✅ | ✅ Native | ❌ | ❌ | ✅ **GraphOrch** |
| **Streaming** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ **SSE** |
| **Multi-Model** | ✅ 20+ | ❌ OpenAI | ✅ 20+ | ✅ 10+ | ✅ 20+ | ✅ **DS+OpenAI** |
| **External Agent Gov.** | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ **Meta-Harness** |
| **Cost Governance** | — | — | — | — | — | ✅ **CostAwareRouter** |
| **Loop Engineering** | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ **LoopEngine** |

## Roadmap

| Phase | Content | Status |
|-------|---------|:------:|
| 0 | Research agent frameworks | ✅ |
| 1–2 | Skill→Agent mapping + DS dual-model | ✅ v0.1.0 |
| 3–4 | Orchestrator + Checkpoint + Context | ✅ v0.2.0 |
| 5 | Full SOP pipeline + self-test | ✅ v0.4.0 |
| 6–8 | Memory + Config + HyDE + CircuitBreaker | ✅ vA.0.2–3 |
| 9 | Multi-model + Streaming | ✅ v0.5.0 (integrated: ModelRouter unified, /stream SSE, 7 tests) |
| 10 | Graph Engine + Durable | ✅ v0.6.0 |
| 11 | Docs + Building Agents guide | ✅ Current |
| 12 | Meta-Harness (external governance) | 🚧 |
| 13 | PyPI release + CI | 🚧 |
| 14 | Plugin interface | 💡 Planned |

## Project Structure

```
├── src/jig/              # Framework core (adapters/core/orchestrator/cli/server)
├── tests/                # 135 test suite
├── skills/               # 11 Agent SKILL.md definitions
├── scripts/              # Utility scripts
├── docs/                 # Guides · Reports · Whitepapers · Blog
│   ├── guides/           # User guides
│   ├── reports/          # Comparison · Gap analysis · Security audits
│   ├── whitepapers/      # Technical whitepapers v1–v4
│   ├── blog/             # CSDN blog posts
│   └── awesome-deepseek/ # DeepSeek ecosystem guides
├── examples/             # Example projects (web/data/code-review)
├── .github/              # Issue templates · PR template · Workflows
├── versions/             # Version snapshots (v0.1.0–v0.6.0)
├── pyproject.toml        # Build config
└── CHANGELOG.md          # Release history
```

## License

MIT — Copyright (c) 2026 Jig Contributors
