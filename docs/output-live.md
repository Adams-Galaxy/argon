# Output and Live Displays

Use `ctx.out` as the canonical output API in command handlers.

## Core Output Helpers

- `text()`
- `rich()`
- `error()`
- `warning()`
- `success()`
- `panel()`
- `kv()`
- `rule()`

## Status/Spinner

```python
with ctx.out.status("Waiting for remote task"):
    ...
```

Or async:

```python
result = await ctx.out.awaiting(coro(), message="Waiting")
```

## Progress

```python
with ctx.out.progress() as progress:
    task_id = progress.add_task("Build", total=5)
    ...
```

Helpers:

- `track()`
- `stages()`
- `gather()`

## Finish Policies

Live helpers support finish policies:

- `success`
- `error`
- `clear`
- `leave`

Example:

```python
with ctx.out.progress(final="success", failed_final="error") as progress:
    ...
```

Dynamic finalization:

```python
if ok:
    progress.succeed("Rollout complete")
else:
    progress.fail("Rollout failed")
```
