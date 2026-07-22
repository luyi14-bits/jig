<div align="center">

# ⚡ Jig

**Agent orchestration, rethought. Hard-constraint Harness, DeepSeek-native.**

[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-112%2F117-brightgreen)](tests/)
[![Multi-Model](https://img.shields.io/badge/Models-DeepSeek+OpenAI-4B32C3)](https://platform.deepseek.com)
[![Status](https://img.shields.io/badge/Status-Alpha_v0.5.0-orange)](CHANGELOG.md)

</div>

---

> ⚠️ **Alpha Status**: Jig is in active development (v0.5.0). Core framework is complete: Harness layer, 4-tier memory, multi-model support, graph orchestration. Production use is not yet recommended. Contributions welcome.

---

## Why Jig?

- **🛡️ Pre-execution safety** — ToolGuard intercepts every tool call *before* execution. No other framework does this ([Comparison](#comparison)).
- **🧠 DeepSeek-native** — SHA-256 prefix caching, Flash-first cost-aware routing, automatic FC repair. Optimized for DeepSeek V4.
- **🔄 Loop Engineering** — Convergence detection, quality validation, checkpoint restore, event replay.
- **🧩 12 agents out of the box** — PM → Trinity → Spec → Coding → Code-Review → TDD → Acceptance → Security → DevOps → Secretary → LOOP SOP.
- **🌐 Multi-model + Streaming + Graph** — DeepSeek, OpenAI (extensible), SSE streaming, GraphOrchestrator.
- **🔌 Plugin system** — VisionTool (free local Florence-2), ImageReader, more planned.

---

## Quick Start

### 1. Install

```bash
pip install jig
```

Or from source:

```bash
git clone https://github.com/luyi14-bits/jig.git
cd jig
pip install -e .
```

### 2. Configure

```bash
export JIG_API_KEY="sk-your-deepseek-key"
```

### 3. Run your first pipeline

```python
from jig import Jig

app = Jig(skills_dir="./skills")
result = app.run("Review the code changes in src/ for security issues")
print(result)
```

That's it. The dispatcher routes your request through the SOP pipeline.

---

## Comparison

| Dimension | LangGraph | CrewAI | PydanticAI | **Jig** |
|-----------|:---------:|:------:|:----------:|:-------:|
| **Hard Constraint** | ❌ | ❌ | ❌ | ✅ **ToolGuard pre-execution** |
| **DeepSeek Cache** | — | — | — | ✅ **SHA-256 prefix hashing** |
| **Memory** | Checkpointer | Short-term | Context | ✅ **4-layer (Cache→Partition→Embedding→SQLite)** |
| **Graph Engine** | ✅ Native | ❌ | ❌ | ✅ **GraphOrchestrator** |
| **Streaming** | ✅ | ✅ | ✅ | ✅ **SSE chat_stream** |
| **Multi-Model** | ✅ 20+ | ✅ 10+ | ✅ 20+ | ✅ **DS + OpenAI + extensible** |
| **External Agent Gov.** | ❌ | ❌ | ❌ | ✅ **Meta-Harness adapters** |
| **Cost Governance** | — | — | — | ✅ **CostAwareRouter + TokenBudget** |
| **Loop Engineering** | ❌ | ❌ | ❌ | ✅ **LoopEngine (convergence + replay)** |

---

## Architecture

```
Control Plane (Harness): LOOP SOP · ToolGuard · GlobalConstraints · CircuitBreaker
Agent Plane:             SkillParser → SkillRegistry → AgentFactory → Agents (via SKILL.md)
Orchestration Plane:    Sequential · Parallel · Graph · LoopEngine · Checkpoint
Tool Plane:             MCPClient·Server · RepoMap · EmbeddingIndex · ModelRouter
Plugin Plane:           VisionTool · ImageReader (optional, from jig.contrib)
```

---

## Built-in Agents

Jig ships with preset agent definitions via SKILL.md. You can use them, customize them, or create your own.

| # | Agent | Skill | Model |
|---|-------|-------|:-----:|
| 0 | **Dispatcher** | Built-in | — |
| 1 | **PM** | Luyi14-pm-mentor | Pro |
| 2 | **Trinity** | Luyi14-trinity-mentors | Pro |
| 3 | **Spec-Pipeline** | Luyi14-spec-pipeline | Pro |
| 4 | **Coding** | Luyi14-coding-ethics | Flash |
| 5 | **Code-Review** | Luyi14-code-review | Pro |
| 6 | **TDD** | Luyi14-test-driven-development | Flash |
| 7 | **Acceptance** | Luyi14-acceptance-testing | Flash |
| 8 | **Security** | Luyi14-security-academy | Pro |
| 9 | **DevOps** | Luyi14-devops | Flash |
| 10 | **Secretary** | Luyi14-project-secretary | Flash |
| 11 | **LOOP SOP** | Luyi14-loop-sop | Pro |

---

## Build Your Own Agent

Create `skills/my-agent/SKILL.md`:

```markdown
---
name: my-agent
description: "Describe what your agent does"
agent_name: MyAgent
model: flash
tools: [read, write]
tags: [custom]
---

## Role
What kind of agent you are.

## Workflow
1. First step
2. Second step
3. Final step

## Rules
- Rule 1
- Rule 2
```

Jig loads it automatically:

```python
from jig import Jig

app = Jig(skills_dir="./skills")
print(app.list_agents())  # → includes your agent
result = app.run("Ask your agent to do something")
```

Full guide: [Building Agents with Jig](docs/guides/building-agents.md)

---

## Documentation

| Resource | Description |
|----------|-------------|
| [Building Agents Guide](docs/guides/building-agents.md) | Step-by-step tutorial for creating custom agents |
| [Technical Whitepaper v4](docs/technical-whitepaper-v4.md) | Framework architecture, Harness layer, memory, roadmap |
| [User Guide](docs/user-guide.md) | CLI usage, FastAPI server, Skill customization |
| [Framework Comparison](docs/framework-comparison-report.md) | Jig vs 10+ competing frameworks |
| [API Reference](docs/index.md) | MkDocs-generated API docs (GitHub Pages) |

---

## Roadmap

| Phase | Content | Status |
|-------|---------|:------:|
| 0 | Research agent frameworks | ✅ |
| 1–2 | Skill→Agent mapping + DS dual-model | ✅ v0.1.0 |
| 3–4 | Orchestrator + Checkpoint + Context | ✅ v0.2.0 |
| 5 | Full SOP pipeline + self-test | ✅ v0.4.0 |
| 6–8 | Memory + Config + HyDE + CircuitBreaker | ✅ vA.0.2–3 |
| 9 | Multi-model + Streaming | ✅ v0.5.0 |
| 10 | Graph Engine + Durable | ✅ v0.6.0 |
| 11 | Docs site + Building Agents guide | ✅ Current |
| 12 | PyPI release + CI | 🚧 |
| 13 | Plugin interface | 💡 Planned |

---

## Project Structure

```
jig/
├── src/jig/           # Framework core
├── tests/             # 117 pytest tests
├── skills/            # Agent SKILL.md definitions
├── docs/              # Whitepapers · Guides · PRDs · Comparison
├── versions/          # Version snapshots (v0.1.0–v0.5.0)
├── .trae/specs/       # Spec documents
├── mkdocs.yml         # Documentation config
├── pyproject.toml     # Build config
└── CHANGELOG.md       # Release history
```

---

## License

MIT — Copyright (c) 2026 Jig Contributors
