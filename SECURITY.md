# Security Policy

## Reporting a Vulnerability

Jig is an Alpha-stage research framework. Security is our top priority.

**Do not** open public issues for security vulnerabilities. Instead, email the maintainers directly.

## Scope

Security reviews cover:
- **ToolGuard** — pre-execution intercept logic
- **API Key handling** — no hardcoded secrets, .env-only
- **MCP protocol** — tool call serialization safety
- **External Agent Adapters** — sandbox boundary

## Supported Versions

| Version | Supported |
|---------|:---------:|
| v0.6.x  | ✅ Active |
| < v0.6  | ❌ |
