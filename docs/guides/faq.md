# FAQ

## Q: ModuleNotFoundError on import?
A: Run `pip install jig-toolguard`. If using from source, set `PYTHONPATH=src`.

## Q: How to add a new agent?
A: Create a SKILL.md in your skills directory. See [Best Practices](best-practices.md).

## Q: How to change the model?
A: Set `model: pro` or `model_name: deepseek-chat` in SKILL.md frontmatter.

## Q: How to enable HITL approval?
A: Set `requires_approval: True` on the SOPNode.

## Q: How to export metrics?
A: Run with `--server` flag, then curl `http://localhost:8088/metrics`.
