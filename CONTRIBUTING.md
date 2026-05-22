# Contributing

Thanks for helping improve Argon.

## Development

Use Python 3.11 or newer and install the development extras:

```bash
python -m pip install -e ".[dev]"
```

Before opening a change, run the same core checks as CI:

```bash
python -m ruff check .
python -m ruff format --check .
python -m mypy src
python -m pytest -q
python -m pytest --cov=argon --cov-report=term-missing
```

Keep user-facing behavior documented under `docs/`, update tests around changed
shell behavior, and add release notes to `CHANGELOG.md` for release-facing work.
