# Quick Start

```bash
pip install jig-toolguard
export DEEPSEEK_API_KEY="sk-your-key"
```

```python
from jig import Jig
app = Jig(skills_dir="./skills")
result = app.run("Analyze this request")
print(result)
```
