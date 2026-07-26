# Architecture

```
Agent Firewall (Control Plane): ToolGuard · LOOP SOP · CircuitBreaker
Agent Plane: SkillParser → SkillRegistry → AgentFactory
Orchestration Plane: SOPRunner · Graph · LoopEngine · Memory
Tool Plane: MCP · ModelRouter · CacheEngine · CostAwareRouter
```
