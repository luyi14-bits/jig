<div align="center">

# ⚡ Jig

**A self-built multi-agent orchestration framework with hard-constraint Harness layer.**

[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-112%2F117-brightgreen)](tests/)
[![Multi-Model](https://img.shields.io/badge/Models-DeepSeek+OpenAI-4B32C3)](https://platform.deepseek.com)
[![Status](https://img.shields.io/badge/Status-Alpha_v0.5.0-orange)](CHANGELOG.md)

</div>

---

> ⚠️ **Alpha Status**: Jig is in active development (v0.5.0). Framework core is complete: 13 agents, 41 modules, 112 tests. Production use is not yet recommended. Contributions welcome.

---

## Quick Start

```bash
pip install jig
export JIG_API_KEY="sk-your-deepseek-key"

python -c "
from jig import Jig
app = Jig(skills_dir='./skills')
print(app.run('Build a login flow'))
"
```

## Why Jig?

| You need... | Use Jig because... |
|-------------|-------------------|
| Multi-agent orchestration | 13 preset roles + custom SKILL.md mounting |
| **Hard-constraint safety** | **Only framework with ToolGuard (pre-execution interception)** |
| DeepSeek optimization | SHA-256 prefix caching + CostAwareRouter + FC auto-repair |
| Multi-model support | DeepSeek + OpenAI (extensible via BaseModelProvider) |
| Graph workflow | GraphOrchestrator (conditional/parallel/loop) |
| Streaming output | Async chat_stream with SSE support |
| External agent governance | Meta-Harness adapters for Claude Code, Codex, Cursor |
| Cost control | Flash-first routing + token budgets + circuit breaker |

## Key Features

- ⚡ **Harness Layer** — ToolGuard pre-execution interception + LOOP SOP 5-stage gating + GlobalConstraints
- 🧩 **13 Preset Agents** — PM · Trinity · Spec-Pipeline · Coding · Code-Review · TDD · Acceptance · Security · DevOps · Secretary · LOOP SOP · Horror-Story-Writer + custom mounts
- 🧠 **4-Layer Memory** — CacheEngine (SHA-256) → ContextPartitioner (3-zone) → EmbeddingIndex → SQLite (MemoryRouter + Consolidator)
- 🌐 **Multi-Model** — DeepSeekProvider + OpenAIProvider + BaseModelProvider abstraction (extensible)
- 🔄 **Graph Engine** — GraphOrchestrator with conditional routing, parallel execution, loop detection
- ⏱️ **Streaming** — Async chat_stream with SSE Server-Sent Events support
- 🛡️ **Safety** — CircuitBreaker (3-state) + DriftDetector + Risk Mode + 19 security red lines
- 💰 **Cost Optimization** — CostAwareRouter (Flash-first, auto-upgrade to Pro) + TokenBudget + CacheStats
- 🔌 **Plugin System** — VisionTool (free local Florence-2), ImageReader, PluginMarket (planned)
- 🔗 **Interop** — MCP Client + Server, A2A Protocol, Meta-Harness (external agent governance)
- 🎯 **Intent Routing** — IntentRouter with HyDE rewrite + multi-intent decomposition
- 🛠️ **Loop Engineering** — LoopEngine with convergence detection, quality validation, checkpoint restore, event replay
- 📦 **Public SDK** — `from jig import Jig · ModelRouter · SkillRegistry · ConfigManager · LoopEngine · GraphOrchestrator`

## Architecture

```
Control Plane (Harness): LOOP SOP · ToolGuard · GlobalConstraints · MemoryRouter · CircuitBreaker
Agent Plane:             SkillParser → SkillRegistry → AgentFactory → 13 Agents
Orchestration Plane:    Sequential · Parallel · Hierarchical · Graph · LoopEngine · Checkpoint
Tool Plane:             MCPClient · Server · RepoMap · EmbeddingIndex · ModelRouter
                        CacheEngine · ContextPartitioner · CostAwareRouter · IntentRouter
Plugin Plane:           VisionTool · ImageReader · PluginMarket (optional, from jig.contrib)
```

## Build-in Agents

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
| 12 | **Horror Writer** | luyi14-horror-story-writer | Flash |

## Comparison

| Dimension | LangGraph | CrewAI | PydanticAI | **Jig** |
|-----------|:---------:|:------:|:----------:|:-------:|
| **Hard Constraint** | ❌ | ❌ | ❌ | ✅ **ToolGuard pre-execution** |
| **DeepSeek Cache** | — | — | — | ✅ **SHA-256 prefix hashing** |
| **Memory** | Checkpointer | Short-term | Context | ✅ **4-layer (Cache→Partition→Embedding→SQLite)** |
| **Graph Engine** | ✅ Native | ❌ | ❌ | ✅ **GraphOrchestrator** |
| **Streaming** | ✅ | ✅ | ✅ | ✅ **SSE chat_stream** |
| **Multi-Model** | ✅ 20+ | ✅ 10+ | ✅ 20+ | ✅ **DS + OpenAI + extensible** |
| **MCP** | ✅ Client | ✅ Client | ❌ | ✅ **Client + Server** |
| **External Agent Gov.** | ❌ | ❌ | ❌ | ✅ **Meta-Harness adapters** |
| **Cost Governance** | — | — | — | ✅ **CostAwareRouter + TokenBudget** |
| **Loop Engineering** | ❌ | ❌ | ❌ | ✅ **LoopEngine (convergence + replay)** |
| **License** | MIT | MIT | MIT | **MIT** |

## Project Structure

```
jig/
├── src/jig/                    # Framework core
│   ├── core/                   # SkillDef · Parser · Registry · AgentFactory · Config
│   ├── adapters/               # ModelRouter · DeepSeekProvider · OpenAIProvider · CacheEngine · Context · MCPClient · MCPProtocol · Streaming · CostAwareRouter · IntentRouter
│   ├── orchestrator/           # Sequential · Parallel · Hierarchical · GraphOrchestrator · LoopEngine · CircuitBreaker · Dispatcher · Memory · Checkpoint
│   ├── contrib/                # VisionTool · ImageReader (optional plugins)
│   ├── cli/                    # CLI entry point
│   └── server/                 # FastAPI + AsyncApp
├── tests/                      # 117 tests (pytest)
├── skills/                     # 13 Agent SKILL.md definitions
├── docs/                       # Whitepapers · PRDs · Comparison reports · Gap analysis
├── versions/                   # Version snapshots (v0.1.0 through v0.5.0)
├── .trae/specs/               # Spec documents
├── pyproject.toml              # Build config
└── CHANGELOG.md                # Release history
```

## Roadmap

| Phase | Content | Status |
|-------|---------|:------:|
| 0 | Research 10+ agent frameworks | ✅ |
| 1–2 | Skill→Agent mapping + DS dual-model | ✅ v0.1.0 |
| 3–4 | Orchestrator + Checkpoint + Context | ✅ v0.2.0 |
| 5 | Full SOP pipeline + self-test suite | ✅ v0.4.0 |
| 6–7 | Memory refactor + Config + Risk mode | ✅ vA.0.2 |
| 8 | HyDE routing + Circuit breaker | ✅ vA.0.3 |
| 9 | Multi-model + Streaming (IDEA-058+059) | ✅ v0.5.0 |
| 10 | Graph Engine + Durable (IDEA-060+061) | ✅ v0.6.0 |
| 11 | Real project validation (IDEA-053) | 🚧 In progress |
| 12 | pip + Docs site (IDEA-042) | 📝 Planned |
| 13 | Plugin interface (VisionTool, etc.) | 💡 Planned |

## License

MIT — Copyright (c) 2026 Jig Contributors
