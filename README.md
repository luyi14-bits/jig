<div align="center">

# ⚡ AgentHarness

**A self-built multi-agent orchestration framework with 12 preset roles, 4-layer memory, and hard-constraint harness.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python)](https://python.org)
[![DeepSeek](https://img.shields.io/badge/LLM-DeepSeek_V3-4B32C3)](https://deepseek.com)
[![Status](https://img.shields.io/badge/Status-Alpha_0.2-orange)](CHANGELOG.md)
[![Tests](https://img.shields.io/badge/Tests-62%2F62-brightgreen)](tests/)

</div>

---

> ⚠️ **Alpha Status**: AgentHarness is in active development (Alpha 0.2). Core architecture, agent pipeline, and SOP orchestration are proof-of-concept complete. Production use is not yet recommended. Contributions and feedback welcome.

---

## 📖 Table of Contents

- [What is AgentHarness?](#what-is-agentharness)
- [Key Features](#key-features)
- [Quick Start](#quick-start)
- [Usage](#usage)
- [Architecture](#architecture)
- [Built-in Agents](#built-in-agents)
- [Comparison](#comparison)
- [Roadmap](#roadmap)
- [Project Structure](#project-structure)
- [Contributing](#contributing)
- [License](#license)

---

## What is AgentHarness?

AgentHarness is a **self-built multi-agent orchestration framework** — not a wrapper around existing agent libraries. It introduces a **hard-constraint Harness layer** (ToolGuard + LOOP SOP gating) that intercepts tool calls *before* execution — a capability absent in prompt-only frameworks like CrewAI, MetaGPT, and AutoGPT. The 4-tier memory architecture is purpose-built for DeepSeek Context Caching with SHA-256 prefix hashing.

Unlike fork-based projects, AgentHarness is written from scratch with its own orchestration engine, memory system, and agent definition protocol.

```
You: "Build a login flow with phone + OTP"
         │
         ▼
  Dispatcher ─── Routes intent, launches pipeline
         │
         ▼
  PM Agent ────→ Trinity Architecture Review
         │
         ▼
  Spec-Pipeline ─── Task breakdown + acceptance checklist
         │
         ▼
  Coding Agent ──→ Code-Review Agent ──→ TDD Agent
         │
         ▼
  Acceptance + Security (parallel verification + security audit)
         │
         ▼
  DevOps Agent ─── Build & release
         │
         ▼
  Secretary Agent ─── Kanban update + version snapshot
```

---

## Key Features

- 🧩 **12 Preset Agent Roles** — PM, Trinity (3 AI experts), Spec-Pipeline, Coding, Code-Review, TDD (3 testing legends), Acceptance, Security (3 auditors), DevOps, Secretary, LOOP SOP, plus extensible custom agents
- 🛡️ **Hard-Constraint Harness** — ToolGuard whitelist/denylist/PreToolUse hook intercepts tools *before* execution; prompt-only frameworks can't do this
- 🚦 **5-Stage LOOP SOP Gating** — Every pipeline stage has a gate check; auto-degrade on failure (circuit breaker, drift detection, max-iteration cap)
- 🧠 **4-Layer Memory Architecture** — CacheEngine (SHA-256 prefix hashing) → ContextPartitioner (immutable/append-only/volatile) → EmbeddingIndex (semantic skill retrieval) → SQLite CheckpointManager
- 💰 **Dual-Model Cost Optimization** — Pro model for planning/review; Flash model for coding/testing. Targets 60-70% API cost reduction
- 📦 **Skill → Agent Mapping Engine** — Any `SKILL.md` with YAML frontmatter becomes a runnable agent. Mount custom skills at runtime with `--attach`
- 🔄 **HandoverPackage Protocol** — Typed handoff schema (`source → target + summary + artifacts + decisions + confidence`) ensures no information loss between agents
- 🧪 **62 Tests, Full Green** — pytest suite covering parser, registry, factory, orchestrator, memory, context compression, and end-to-end pipeline

---

## Quick Start

### Prerequisites

- **Python 3.10+**
- **DeepSeek API Key** — [Get one here](https://platform.deepseek.com/api_keys)

### Installation

```bash
# Clone the repo
git clone https://github.com/luyi14-bits/agent-harness.git
cd agent-harness

# Install dependencies
pip install pydantic>=2.0 pydantic-settings>=2.0 pyyaml>=6.0

# (Optional) Dev install
pip install -e .

# (Optional) Install test dependencies
pip install pytest

# Development install (editable)
pip install -e .
```

### Configuration

Set your DeepSeek API key as an environment variable:

```bash
# Linux / macOS
export DEEPSEEK_API_KEY="sk-your-key-here"

# Windows (PowerShell)
$env:DEEPSEEK_API_KEY="sk-your-key-here"

# Windows (CMD)
set DEEPSEEK_API_KEY=sk-your-key-here
```

Alternatively, create a `.env` file in the project root:

```
DEEPSEEK_API_KEY=sk-your-key-here
```

All configuration is managed via `src/jig/settings.py` (Pydantic `BaseSettings`). See the file for advanced options: model selection, temperature, cache prefix order, session timeout, etc.

### 5-Minute Smoke Test

```bash
# Run the self-test suite (CLI, no IDE needed)
python auto_test.py
```

Expected output: all checks pass, skill parser works, agent factory creates instances, dependencies verified.

---

## Usage

### CLI — Chat Mode (Dispatcher)

```bash
# Start interactive group-chat with natural language routing
python run.py

# You'll see:
#   Tree-SOP Agent — 纯终端群聊模式
#   Skills: .../skills
#   已加载 12 个 Agent
# >
# Type your request and the Dispatcher routes it to the right agent.
```

### CLI — Inspect an Agent's Assembled Prompt

```bash
python -m src.forge.cli.main --skill-dir skills --inspect pm-mentor
```

### CLI — Mount Custom Skills at Runtime

```bash
python run.py --attach my-custom-skill
```

### Python API

```python
from jig.orchestrator.dispatcher import Dispatcher

# Initialize with skill directory
dispatcher = Dispatcher(skill_dir="./skills")
print(f"Loaded {dispatcher.registry.count()} agents")

# Dispatch a natural-language request
result = dispatcher.handle("Create a PRD for a user login feature")
print(result)
```

For advanced orchestration (sequential, parallel, hierarchical), see `src/jig/orchestrator/orchestrator.py`.

### FastAPI Server (Standalone)

```bash
python -m src.forge.server.app
# Endpoints:
#   POST /execute  — run a pipeline
#   GET  /status   — check server health
```

---

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                 Control Plane (Harness)                       │
│  LOOP SOP · ToolGuard · GlobalConstraints · MemoryRouter     │
├──────────────────────────────────────────────────────────────┤
│                 Agent Plane                                   │
│  SkillParser → SkillRegistry → AgentFactory → Agent (12)     │
│  HandoverPackage · Dispatcher · IntentRouter                 │
├──────────────────────────────────────────────────────────────┤
│                 Orchestration Plane                           │
│  SequentialOrch · ParallelOrch · HierarchicalOrch            │
│  CheckpointManager · CircuitBreaker · DriftDetector          │
├──────────────────────────────────────────────────────────────┤
│                 Tool Plane                                    │
│  MCPClient · ToolGuard · RepoMap · EmbeddingIndex            │
│  DeepSeekAdapter · CacheEngine · ContextPartitioner          │
└──────────────────────────────────────────────────────────────┘
```

### SOP Pipeline

```
Dispatcher → PM → Trinity → Spec → Coding → Code-Review
          → TDD → Acceptance ∥ Security → DevOps → Secretary
```

### 5-Stage LOOP SOP Gating

| Gate   | Check                                        | On Failure        |
|--------|----------------------------------------------|-------------------|
| G0→1   | PRD complete + priority set + Out of Scope   | Return to Stage 0 |
| G1→2   | Spec + Tasks + Checklist ready + BREAKING    | Return to Stage 1 |
| G2→3   | Self-test exit(0) + tests green + 24 checks  | Return to Stage 2 (max 3×) |
| G3→4   | Acceptance PASS + Security zero-red          | Return to Stage 2 |
| G4→end | Version snapshot + Kanban + trace log        | Return to Stage 4 |

### 4-Layer Memory

| Layer | Component            | Mechanism                                          |
|:-----:|----------------------|----------------------------------------------------|
| 1     | **CacheEngine**      | SHA-256 prefix hashing for DeepSeek cache hit max. |
| 2     | **ContextPartitioner** | immutable / append-only / volatile 3-zone context |
| 3     | **EmbeddingIndex**   | Semantic skill retrieval (sentence-transformers, keyword fallback) |
| 4     | **CheckpointManager** | JSON checkpoint persist + resume                  |

### ToolGuard — 3-Layer Hard Constraint

```
Tool Call Request
      │
      ▼
 [Whitelist Check] ── Fail → Block + Log
      │ Pass
      ▼
 [Denylist Check]  ── Hit  → Block + Log
      │ Pass
      ▼
 [PreToolUse Hook] ── Fail → Block + Log
      │ Pass
      ▼
   Execute Tool
```

---

## Built-in Agents

| # | Agent | Skill File | Role | Model |
|---|-------|-----------|------|:-----:|
| 0 | **Dispatcher** | (built-in) | Intent routing, pipeline launch | — |
| 1 | **PM** | `Luyi14-pm-mentor` | Requirements, PRD (12-section), RICE scoring | Pro |
| 2 | **Trinity** | `Luyi14-trinity-mentors` | 3 AI/ML experts (Raschka, Karpathy, Lyalin) for architecture review | Pro |
| 3 | **Spec-Pipeline** | `Luyi14-spec-pipeline` | Spec writing, task breakdown, checklist, complexity control | Pro |
| 4 | **Coding** | (built-in) | Code generation with Coding Ethics (八荣八耻) enforcement | Flash |
| 5 | **Code-Review** | `Luyi14-code-review` | Code style, bugs, security, performance anti-patterns | Pro |
| 6 | **TDD** | `Luyi14-test-driven-development` | 3 testing legends (Beck, Stewart, Okken) for test strategy | Flash |
| 7 | **Acceptance** | `Luyi14-acceptance-testing` | Evidence-based verification, severity grading, fix tracking | Flash |
| 8 | **Security** | `Luyi14-security-academy` | 3 security experts (Miessler, Kettle, Ormandy) for audit | Pro |
| 9 | **DevOps** | `Luyi14-devops` | Build, packaging, tagging, release, rollback | Flash |
| 10 | **Secretary** | `Luyi14-project-secretary` | File organization, kanban, docs, git, cross-team coordination | Flash |
| 11 | **LOOP SOP** | `Luyi14-loop-sop` | Gate checking, degradation trigger, iteration tracking | Pro |

---

## Comparison

| Dimension | CrewAI | MetaGPT | AutoGPT | **AgentHarness** |
|-----------|:------:|:-------:|:-------:|:----------------:|
| **Hard Constraint Layer** | ❌ prompt-only | ❌ prompt-only | ❌ prompt-only | ✅ **ToolGuard + 5-stage gating (pre-execution)** |
| **Harness Level** | ❌ | ❌ | ❌ | ✅ **Built-in framework harness** |
| **Role System** | Generic, user-defined | Software company sim | Single agent | ✅ **12 preset roles + custom mount** |
| **Memory Architecture** | Short-term | Message sharing | Vector store | ✅ **4-layer + 5-level compression** |
| **Cache Optimization** | — | — | — | ✅ **Prefix SHA-256 hashing for DeepSeek cache** |
| **Failure Handling** | Manual retry | Manual retry | Loop retry | ✅ **Auto-degrade + circuit breaker + checkpoint resume** |
| **License** | MIT | MIT | Apache 2.0 | **MIT** |

> 📊 Full 10+ framework comparison: [Framework Comparison Report](docs/framework-comparison-report.md)

---

## Roadmap

| Phase | Content | Status |
|-------|---------|:------:|
| 0 | Research 10+ open-source agent frameworks | ✅ |
| 1–2 | Skill→Agent mapping + DeepSeek dual-model adapter | ✅ v0.1.0 |
| 3–4 | Orchestrator + Checkpoint + Context compression | ✅ v0.2.0 |
| 5 | Full 5-stage SOP pipeline + self-test suite | ✅ v0.4.0 |
| 6 | Tauri desktop shell (archived) | ✅ vA.0.1 |
| 7 | Memory system refactor + Config + Risk mode | ✅ vA.0.2 |
| 8 | HyDE routing + Circuit breaker detection | ✅ vA.0.3 |
| 9 | PyPI publishing + GitHub Actions CI + MkDocs | 🚧 In progress |
| 10 | Stable release + community validation | 💡 Planned |

---

## Project Structure

```
agent-harness/
├── src/jig/
│   ├── core/              # SkillDef · Parser · Registry · AgentFactory · Config
│   ├── adapters/          # DeepSeekAdapter · CacheEngine · Context · MCPClient · RepoMap
│   ├── orchestrator/      # Sequential · Parallel · Hierarchical · CircuitBreaker · Memory
│   ├── cli/               # CLI entry point
│   └── server/            # FastAPI standalone deployment
├── skills/                # 12 Agent SKILL.md definitions + trace LOG.md
├── tests/                 # pytest suite (62 tests)
├── docs/                  # Whitepaper · Framework comparison · PRD · Security audit
├── desktop/               # Tauri v2 desktop app shell (archived)
├── versions/              # Version snapshots (v0.1.0 through Alpha-0.2)
├── auto_test.py           # Self-test CLI script
├── run.py                 # Dispatcher group-chat entry
├── pyproject.toml         # Build config
└── CHANGELOG.md           # Release history
```

---

## Contributing

AgentHarness is in Alpha. We welcome:

- 🐛 **Bug reports** — Open an [issue](https://github.com/luyi14-bits/agent-harness/issues)
- 💡 **Feature ideas** — Discuss in issues before coding
- 🔧 **Pull requests** — Keep them small and focused; run `pytest` before submitting
- 📝 **Documentation** — Improvements to docs, README, or inline comments

See [CHANGELOG.md](CHANGELOG.md) for the full release history and [PIPELINE_KANBAN.md](PIPELINE_KANBAN.md) for the idea pipeline.

---

## License

[MIT](LICENSE) · Copyright (c) 2026 AgentHarness Contributors

---

<div align="center">
  <sub>Built with ❤️ by AgentHarness Contributors · 2026</sub>
</div>
