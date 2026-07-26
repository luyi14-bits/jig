# Agent Firewall

Jig's core differentiator: **pre-execution tool interception**.

## ToolGuard

Every tool call passes through ToolGuard before execution:

1. **Whitelist check** — agent role must have permission for the tool
2. **Denylist check** — dangerous operations blocked globally
3. **Runtime hook** — custom pre-use validation

```python
from jig.adapters.mcp_client import ToolGuard

# Blocked
ToolGuard.check("pm", "Bash(rm -rf /)")  # → False

# Allowed
ToolGuard.check("coding", "Write", "src/app.py")  # → True
```

## CircuitBreaker

Three-state circuit breaker protects against cascading failures:

- CLOSED — normal operation
- OPEN — failing, calls rejected
- HALF_OPEN — recovery probe

## Comparison

| Feature | deepagents | OpenAI SDK | Jig |
|---------|:----------:|:----------:|:---:|
| Pre-execution intercept | ❌ | ❌ | ✅ |
| Hard constraints | ❌ prompt | ❌ prompt | ✅ code |
| External agent governance | ❌ | ❌ | ✅ Meta-Harness |
