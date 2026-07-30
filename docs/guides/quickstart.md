# Jig Quick Start

## Install

```bash
pip install jig-toolguard
```

## Hello World

```python
from jig import Jig

# Load skills and run
app = Jig(skills_dir="./skills")
result = app.run("帮我做个简单的加法")
print(result)
```

## CLI

```bash
# List agents
jig --list

# Chat mode
jig --chat

# Run single prompt
jig --run "帮我写个python脚本"

# Eval
jig eval dataset.json --report report.md
```

## Next Steps

- [CLI Reference](cli-reference.md)
- [API Reference](api-reference.md)
- [Best Practices](best-practices.md)
