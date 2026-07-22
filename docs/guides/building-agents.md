# Building Agents with Jig

Jig is a **framework for building agents** — not an agent itself. You use it the same way you'd use LangGraph or PydanticAI: write a few lines of code, define your agent's behavior, and let Jig handle the orchestration, safety, and optimization.

---

## 1. Your First Agent

### Step 1: Install

```bash
pip install jig
```

### Step 2: Create a SKILL.md

Create `skills/translator/SKILL.md`:

```markdown
---
name: translator
description: "Translates text between languages"
agent_name: Translator
model: flash
tags: [utility, translation]
---

## Role
You are a professional translator. Translate the user's input to the target language.

## Rules
1. Always preserve the original formatting
2. Output only the translation, no explanations
3. If the input language is unknown, detect it automatically
```

### Step 3: Use it in code

```python
from jig import Jig

app = Jig(skills_dir="./skills")
agents = app.list_agents()
print(agents)
# → [{"name": "translator", "description": "Translates text...", "model": "flash"}]
```

---

## 2. SKILL.md Reference

Every agent in Jig is defined by a `SKILL.md` file with YAML frontmatter + Markdown body.

### Frontmatter Fields

```yaml
---
name: my-agent              # Required. Unique agent identifier
description: "Does X"       # Required. Short description
agent_name: MyAgent         # Optional. Display name (defaults to name)
model: flash                # Optional. "flash" or "pro" (default: flash)
tools: [read, write, mcp]   # Optional. Tool whitelist
tags: [dev, utility]        # Optional. Categorization tags
---
```

### Body

The body is the agent's system prompt. Write it in Markdown. It's the full instruction set for your agent — role, goals, rules, output format, and constraints.

Best practice:
```markdown
## Role
What kind of agent you are.

## Workflow
1. First step
2. Second step  
3. Final step

## Rules
- Rule 1
- Rule 2

## Output Format
```json
{...}
```
```

---

## 3. Tool Configuration

Tools are whitelisted per agent via the `tools` frontmatter field:

```yaml
tools: [read, write]  # Agent can only read and write files
```

Available built-in tools:

| Tool | Description |
|------|-------------|
| `read` | Read files from disk |
| `write` | Write files to disk |
| `bash` | Execute shell commands |
| `glob` | Find files by pattern |
| `mcp` | MCP protocol tools |
| `web_search` | Web search (optional plugin) |

### ToolGuard — Safety Layer

Every tool call passes through ToolGuard:

```
Agent calls tool → Whitelist check → Denylist check → PreToolUse hook → Execute
```

Configure per agent via `ConfigManager`:

```python
from jig import ConfigManager

cfg = ConfigManager()
cfg.set_agent_config("my-agent", {
    "allow_tools": ["read", "write"],
    "deny_tools": ["rm", "sudo"],
})
```

---

## 4. Model Assignment

Models are assigned in the SKILL.md frontmatter:

```yaml
model: flash    # Cheaper, faster, for simple tasks
model: pro      # More capable, for complex reasoning
```

The `CostAwareRouter` upgrades flash to pro automatically when a request exceeds 100 tokens:

```python
from jig import ModelRouter, DeepSeekProvider, OpenAIProvider

router = ModelRouter()
router.register("ds", DeepSeekProvider(api_key="sk-..."))
router.register("openai", OpenAIProvider(api_key="sk-..."))
```

---

## 5. SOP Pipeline

Agents execute in a defined pipeline order. Default:

```
Dispatcher → PM → Trinity → Spec → Coding → Code-Review → TDD → Acceptance ∥ Security → DevOps → Secretary
```

Each step outputs a `HandoverPackage`:

```python
@dataclass
class HandoverPackage:
    source_agent: str      # Who produced this
    target_agent: str      # Who should receive it
    summary: str           # What was done
    artifacts: Dict        # Output data
    decisions: List[str]   # Key decisions
    confidence: float      # 0.0-1.0
```

---

## 6. Complete Example: SQL Review Agent

```markdown
---
name: sql-review
description: "Reviews SQL queries for performance and security"
agent_name: SQLReviewer  
model: pro
tools: [read, write]
---

## Role
You are a senior DBA. Review SQL queries for performance issues and security vulnerabilities.

## Workflow
1. Read the SQL file
2. Check for: missing indexes, full table scans, SQL injection, N+1 queries
3. Output review report with severity: CRITICAL / WARNING / INFO
```

Mount it and run:

```python
from jig import Jig

app = Jig(skills_dir="./skills")
app.add_agent_tool("vision", None)  # Optional plugins

# Run the pipeline
result = app.run("Review all SQL files in src/db/")
print(result)
```

---

## 7. Debugging

### Inspect agent prompt

```bash
python -m jig.cli.main --skill-dir skills --inspect sql-review
```

### Event replay

```python
from jig import LoopEngine
engine = LoopEngine()
# ... run pipeline ...
replay = engine.replay()  # Full event log
```

### Agent log

Each agent writes to `skills/<name>/LOG.md` automatically.

---

## 8. Best Practices

1. **One skill = one responsibility** — don't cram multiple roles into one SKILL.md
2. **Use `model: flash` by default** — only use `pro` when you need complex reasoning
3. **Set `tools` explicitly** — never leave tools empty (agent can't do anything) or too broad
4. **Write detailed rules** — agents follow the body as their constitution
5. **Test with `--inspect`** — verify the assembled prompt before running
6. **Mount, don't modify** — use `--attach` for custom skills, don't edit built-in ones
