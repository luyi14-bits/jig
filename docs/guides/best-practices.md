# Best Practices

## Skill Writing
- Keep SKILL.md under 200 chars in description
- Use `model: flash` for simple tasks, `model: pro` for complex
- Prefix skill files with the agent role (e.g., `agent-`)

## Error Handling
- Always check `HandoverPackage.confidence` 
- If confidence < 0.5, escalate to HITL

## Performance
- Use `arun()` for pipelines with > 10 nodes
- Enable metrics via `/metrics` endpoint
- Set `timeout_seconds` on CPU-heavy nodes
