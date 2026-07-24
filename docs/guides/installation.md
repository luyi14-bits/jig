# Installation

## From PyPI

```bash
pip install jig
```

## From Source

```bash
git clone https://github.com/luyi14-bits/jig.git
cd jig
pip install -e .
```

## Dependencies

- Python 3.10+
- DeepSeek API Key (for default provider)
- Optional: `pip install torch torchvision pillow transformers` for VisionTool

## Verify Installation

```python
from jig import Jig
print("Jig imported successfully")
```
