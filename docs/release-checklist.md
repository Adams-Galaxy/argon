# Release Checklist

## Validation Matrix

Run before tagging:

```bash
python -m pytest -q
python -m ruff check .
python -m ruff format --check .
python -m mypy src
python -m pytest --cov=argon --cov-report=term-missing
python -m build
python -m twine check --strict dist/*
```

## Release Gates

- Public API exports match `docs/api-reference.md`.
- All public docs under `docs/` are current.
- Internal docs remain under `docs/dev/`.
- `examples/demo.py` reflects v1 defaults.
- Supported Python versions pass CI.
- Coverage remains at or above the configured floor.
- The wheel contains `argon/py.typed` while the package is classified as typed.
- `pyproject.toml` version matches the intended release tag.
- `CHANGELOG.md` includes notes for the intended release.
