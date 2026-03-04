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
- `Console.execute_argv_async()`
- `Console.execute_line_async()`

These APIs are safe inside active event loops and always await async command results.

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
```
