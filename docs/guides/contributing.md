# Contributing to Jig

Thanks for your interest in contributing! Jig is an open-source multi-agent orchestration framework.

## Getting Started

```bash
git clone https://github.com/luyi14-bits/jig.git
cd jig
pip install -e .
pytest
```

## Pull Request Process

1. Run `pytest tests/` to confirm all tests pass
2. Update `CHANGELOG.md` if adding features
3. Keep PRs focused on a single change

## Code Style

- Python 3.10+ type annotations required
- Follow existing patterns in the codebase
- Public API changes must update `__init__.py` exports

## Testing

- All new features need tests
- Run `python -m pytest tests/ -q` before submitting
- Smoke tests requiring API key are in `test_smoke_live.py` (skipped without key)
