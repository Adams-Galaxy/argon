# Authoring Commands

Argon follows a Typer-like authoring model with `Annotated` metadata preferred.

## Preferred Style

```python
from typing import Annotated
import argon

app = argon.App(name="demo")


@app.command()
def greet(
    ctx: argon.Context,
    name: Annotated[str, argon.Argument(help="Target name")],
    times: Annotated[int, argon.Option("--times", "-t", help="Repeat count")] = 1,
) -> None:
    for _ in range(times):
        ctx.out.text(f"Hello {name}")
```

## Inferred Style

```python
@app.command()
def greet(name: str, times: int = 1) -> None:
    ...
```

## Groups and Subcommands

```python
users = app.group("users", help="User operations")


@users.command()
def add(name: str) -> None:
    ...
```

## Context

Request `argon.Context` in callback parameters to access:

- `ctx.params` / `ctx.args`
- `ctx.meta` session-level metadata
- `ctx.out` Rich-first output helpers
- `ctx.abort()` / `ctx.exit()`

## Completion

Arguments and options accept static completion values or callable completion
sources. Argon prefix-filters the returned items.

```python
@app.command()
def release(
    service: Annotated[
        str,
        argon.Argument(completion=("api", "worker", "web")),
    ],
    channel: Annotated[
        Literal["stable", "preview"],
        argon.Option("--channel", "-c"),
    ] = "stable",
) -> None:
    ...
```

String `Literal` values and string-valued enums complete automatically when no
explicit completion source is configured. Use `argon.CompletionItem` when a
candidate needs distinct display or metadata text.

## Single-function Shortcut

```python
import argon

def main(name: str) -> str:
    return name

argon.run(main)
```
