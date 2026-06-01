# Changelog

## 1.0.2 - 2026-06-01

- Added `ctx.input` and `ctx.inp` for prompt, key, and interruptible sleep flows.
- Added `ctx.output` as the long-form output surface while keeping `ctx.out`.
- Added guarded `ctx.output.live()` for custom Rich live renderables.
- Released prompt_toolkit terminal input mode while shell commands run so command
  key handling can own arrows and other terminal input.
- Updated the reference demo to exercise the new input/live APIs.

## 1.0.1 - 2026-05-23

- Improved shell usage-error display controls for resolved commands.
- Fixed completion sequencing for consumed arguments and inline option values.
- Added ergonomic completion sources with static values, public rich completion
  items, default prefix filtering, and inferred string `Literal`/enum values.
- Tightened the release toolchain with Ruff formatting/lint gates, coverage
  reporting, package artifact validation, and supported-Python CI.

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
