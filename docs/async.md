# Async Execution

Argon supports async command callbacks in both sync and async runtimes.

## Sync Entry Points

- `App.run_argv()`
- `App.run_line()`
- `Console.execute_argv()`
- `Console.execute_line()`

Behavior:

- If no event loop is running, Argon executes awaitables to completion.
- If an event loop is already running and a command returns an awaitable, Argon raises a `UsageError` with guidance to use async APIs.

## Async Entry Points

- `App.run_argv_async()`
- `App.run_line_async()`
- `App.run_async()`
- `App.run_shell_async()`
- `Console.execute_argv_async()`
- `Console.execute_line_async()`
- `Shell.run_async()`

These APIs are safe inside active event loops and always await async command results. `App.run_async()` and `Shell.run_async()` run the interactive shell through prompt_toolkit's async prompt pathway when available, so Argon can be embedded in an existing event loop.

## Interrupts

During command execution, `KeyboardInterrupt` and async cancellation are normalized to `argon.Interrupted`.
Interactive shells render the interrupt and continue running; programmatic sync and async APIs raise `argon.Interrupted` for callers to handle.

## Example

```python
import asyncio
import argon

app = argon.App(name="demo")


@app.command()
async def wait() -> str:
    await asyncio.sleep(0.1)
    return "done"


async def run_inside_loop() -> str:
    return await app.run_argv_async(["wait"])


async def run_shell_inside_loop() -> int:
    return await app.run_async()
```
