# Jig

**A self-built multi-agent orchestration framework with hard-constraint Harness layer.**

[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/luyi14-bits/jig/blob/main/LICENSE)
[![Tests](https://img.shields.io/badge/Tests-112%2F117-brightgreen)](https://github.com/luyi14-bits/jig/actions)

Jig lets developers assemble their own agents with a few lines of code — with **DeepSeek cache optimization** and **ToolGuard hard constraints** built-in, not bolted on.

```python
from jig import Jig

app = Jig(model="deepseek-v4-flash")
result = app.run("Build a login flow with OTP")
print(result)
```

## Why Jig?

- ⚡ **Harness-first**: ToolGuard pre-execution interception (unique vs LangGraph/CrewAI)
- 🧩 **12 preset agents**: PM · Trinity · Spec · Coding · Review · TDD · Acceptance · Security · DevOps · Secretary · LOOP SOP
- 🧠 **4-layer memory**: SHA-256 cache → Context partition → Embedding → SQLite
- 🌐 **Multi-model**: DeepSeek + OpenAI (extensible via BaseModelProvider)
- 🔄 **Graph engine**: Conditional routing, parallel execution, loop detection
- 🔌 **Plugin system**: VisionTool (free local Florence-2), ImageReader
