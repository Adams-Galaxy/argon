# Changelog

## 1.0.0 - 2026-03-05

- Locked public API for `App`, `Console`, `Shell`, `Context`, parameter factories, and core exceptions.
- Added async-safe execution entrypoints:
  - `App.run_argv_async()`
  - `App.run_line_async()`
  - `Console.execute_argv_async()`
  - `Console.execute_line_async()`
- Finalized sync async-command behavior in running loops with explicit `UsageError` guidance.
- Migrated config to Pydantic v2 models with schema versioning (`schema_version=1`).
- Added `CompletionConfig` and shell completion controls:
  - `option_display`: `long | short | all | none`
  - `show_help_tooltips`: bool
- Expanded public docs under `docs/` and kept internal docs under `docs/dev/`.
- Added doxygen-style docstrings on public API surfaces.
