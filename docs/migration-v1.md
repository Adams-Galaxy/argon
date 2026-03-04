# Migration to v1.0

## Highlights

- Config is now validated by Pydantic v2 models.
- Config schema is versioned with `schema_version` (v1 supports `1`).
- Completion menu behavior is configurable via `ShellConfig.completion`.
- Async-safe execution entrypoints are now explicit (`*_async` APIs).
- Public docs live under `docs/`; internal design docs remain in `docs/dev/`.

## Config Changes

Add top-level version:

```json
{
  "schema_version": 1
}
```

Optional completion controls:

```json
{
  "shell": {
    "completion": {
      "option_display": "long",
      "show_help_tooltips": false
    }
  }
}
```

## Async Contract Change

When calling sync APIs from inside an already-running event loop, async command callbacks now raise a clear `UsageError` directing callers to async APIs.
