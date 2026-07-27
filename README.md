<div align="center">

# ⚡ Jig-ToolGuard

**The first pre-execution Agent Firewall. Intercept tool calls before execution.**

[![Python](https://img.shields.io/badge/python-3.10%2B-blue?logo=python&logoColor=white)](https://python.org)
[![PyPI](https://img.shields.io/badge/pypi-jig--toolguard-blue?logo=pypi)](https://pypi.org/project/jig-toolguard/)
[![Tests](https://img.shields.io/badge/tests-124%2F124-brightgreen)](tests/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Status](https://img.shields.io/badge/status-alpha_v0.6.3-orange)](CHANGELOG.md)
[![PRs](https://img.shields.io/badge/PRs-welcome-brightgreen)](CONTRIBUTING.md)

---

[Why Jig?](#why-jig) • [Quick Start](#quick-start) • [Features](#features) • [Comparison](#comparison) • [Architecture](#architecture) • [Install](#install) • [Docs](#docs)

</div>

## Why Jig?

Every agent framework claims safety. But they all stop at prompt-level guardrails — suggestions, not enforcement. Jig is different.

**Jig intercepts every tool call at the code level, before execution.** Not in a prompt. Not after the fact. Before.

```python
# deepagents: "You should not delete files..." — Agent ignores this
# Jig:
from jig.adapters.mcp_client import ToolGuard
ToolGuard.check("coding", "Bash(rm -rf /)")  # → False, blocked at code level
```

While other frameworks "trust the LLM" (deepagents' own words), Jig enforces boundaries that agents cannot bypass.

## Quick Start

```bash
pip install jig-toolguard
```

```python
from jig import Jig

# Load 11 built-in agents and run a pipeline
app = Jig(skills_dir="./skills")
result = app.run("Review this code for security issues")
print(result)
```

<details>
<summary>📺 Or run the terminal UI</summary>

```bash
# Clone and run
git clone https://github.com/luyi14-bits/jig.git
cd jig
pip install -e .
echo "exit" | python run.py
```
</details>

## Install

```bash
pip install jig-toolguard
```

Or from source:

```bash
git clone https://github.com/luyi14-bits/jig.git
cd jig
pip install -e .
```

Requires Python 3.10+. Set your DeepSeek API key:

```bash
export DEEPSEEK_API_KEY="sk-your-key"
```

## Features

### 🛡️ Pre-execution Safety (Agent Firewall)
Every tool call passes through three layers before execution:

1. **Whitelist** — agent role must have explicit permission for the tool
2. **Denylist** — dangerous operations (`rm -rf /`, `drop table`) globally blocked
3. **Runtime hook** — custom validation callback

No other agent framework implements code-level pre-execution interception.

### 🧠 DeepSeek-Native Optimization
- SHA-256 prefix caching (session-level byte invariance)
- Flash-first cost-aware routing (auto-upgrade to Pro for complex tasks)
- Automatic Function Calling repair

### 🤖 11 Preset Agents
| Role | Skill | Function |
|------|-------|----------|
| PM | `Luyi14-pm-mentor` | Requirements analysis, PRD writing, RICE scoring |
| Spec | `Luyi14-spec-pipeline` | Specifications, task breakdown, checklist |
| Coding | `Luyi14-coding-ethics` | Code implementation with 24 self-checks |
| Review | `Luyi14-code-review` | 4-dimensional code audit |
| TDD | `Luyi14-tdd` | Test-driven development |
| Acceptance | `Luyi14-acceptance-testing` | Acceptance testing |
| Security | `Luyi14-security-academy` | 5-stage security audit |
| DevOps | `Luyi14-devops` | Deployment, build, CI/CD |
| Secretary | `Luyi14-project-secretary` | Documentation, versioning, kanban |
| Trinity | `Luyi14-trinity-mentors` | Architecture/requirements/code triage |
| LOOP SOP | `Luyi14-loop-sop` | Pipeline orchestration, gates, escalation |

### 🌐 Multi-Model + Streaming
- `DeepSeekProvider` — fully optimized with caching and FC repair
- `OpenAIProvider` — extensible interface
- SSE streaming — `POST /stream` endpoint with real-time events

### 🔄 Loop Engineering
- **Convergence detection** — automatic stop when output stabilizes
- **Quality validation** — per-node output quality scoring
- **Checkpoint resume** — crash recovery without re-running completed nodes
- **CircuitBreaker** — 3-state (CLOSED/OPEN/HALF_OPEN) fault isolation

### 🗄️ 4-Layer Memory
| Layer | Storage | Purpose |
|-------|---------|---------|
| 1 | DeepSeek prefix cache | Recent N turns, zero overhead |
| 2 | Time-window partition | Long conversation archival |
| 3 | Embedding index | Semantic history retrieval |
| 4 | SQLite | Cross-session persistence |

### 🧩 Graph Orchestration
- DAG-based pipeline with conditional routing, parallel branches, and self-loops
- Replace linear SOPNode with dynamic GraphOrchestrator

## Comparison

| Dimension | deepagents | OpenAI SDK | LangGraph | CrewAI | PydanticAI | **Jig** |
|-----------|:----------:|:----------:|:---------:|:------:|:----------:|:-------:|
| **Pre-execution intercept** | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ **Code-level** |
| **Hard constraints** | ❌ prompt | ❌ prompt | ❌ | ❌ | ❌ | ✅ **Whitelist+Denylist** |
| **DeepSeek cache** | — | — | — | — | — | ✅ **SHA-256 prefix** |
| **Memory** | Short | — | Checkpoint | Short | Context | ✅ **4-layer** |
| **Graph engine** | ❌ | ✅ | ✅ | ❌ | ❌ | ✅ **GraphOrch** |
| **Streaming** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ **SSE** |
| **External agent governance** | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ **Meta-Harness** |
| **Cost governance** | — | — | — | — | — | ✅ **CostAwareRouter** |
| **Loop engineering** | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ **LoopEngine** |

## Architecture

```
Agent Firewall (Control Plane):
  ToolGuard · LOOP SOP · CircuitBreaker · GlobalConstraints

Agent Plane:
  SkillParser → SkillRegistry → AgentFactory → Agents (SKILL.md)

Orchestration Plane:
  SOPRunner · GraphOrchestrator · LoopEngine · Memory · Checkpoint

Tool Plane:
  MCP · ModelRouter · CacheEngine · CostAwareRouter · Streaming
```

## Project Structure

```
├── src/jig/           # Framework core (adapters/core/orchestrator/cli/server)
├── tests/             # 124 test suite
├── skills/            # 11 Agent SKILL.md definitions
├── docs/              # Guides · Reports · Whitepapers · Blog
│   ├── guides/        # User guides
│   ├── reports/       # Comparison · Gap analysis · Security audits
│   └── whitepapers/   # Technical whitepapers v1–v4
├── examples/          # Example projects
├── scripts/           # Utility scripts
├── .github/           # Issue templates · PR template
├── pyproject.toml     # Build config → pip install jig-toolguard
└── CHANGELOG.md
```

## Roadmap

| Phase | Content | Status |
|-------|---------|:------:|
| 1–2 | Skill→Agent mapping + DeepSeek dual-model | ✅ v0.1.0 |
| 3–4 | Orchestrator + Checkpoint + Context | ✅ v0.2.0 |
| 5 | Full SOP pipeline + self-test | ✅ v0.4.0 |
| 6–8 | Memory + Config + CircuitBreaker + RiskMode | ✅ vA.0.2–3 |
| 9 | Multi-model + Streaming | ✅ v0.5.0 |
| 10 | Graph Engine + LoopEngine | ✅ v0.6.0 |
| 11–12 | Meta-Harness + PyPI release | 🚧 |
| 13+ | Durable Execution, OTel, Evals | 💡 Planned |

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). PRs welcome!

## License

MIT — Copyright (c) 2026 Jig Contributors.
