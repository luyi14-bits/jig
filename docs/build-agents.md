# Building Agents

Create `skills/my-agent/SKILL.md`:

```yaml
---
name: my-agent
description: "My custom agent"
model: flash
tools: [read, write, search]
---
```

Jig loads it automatically:

```python
from jig import Jig
app = Jig(skills_dir="./skills")
print(app.list_agents())
```
