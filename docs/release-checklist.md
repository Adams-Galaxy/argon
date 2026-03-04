# Release Checklist (v1.0)

## Validation Matrix

Run before tagging:

```bash
python -m pytest -q
python -m ruff check .
python -m mypy src
```

## Release Gates

- Public API exports match `docs/api-reference.md`.
- All public docs under `docs/` are current.
- Internal docs remain under `docs/dev/`.
- `examples/demo.py` and `examples/demo.config.json` reflect v1 defaults.
- `pyproject.toml` version is `1.0.0`.
- `CHANGELOG.md` includes v1 release notes.
