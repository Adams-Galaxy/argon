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
- `ctx.output` Rich-first output helpers (`ctx.out` is the established short alias)
- `ctx.input` terminal input helpers (`ctx.inp` is the short alias)
- `ctx.abort()` / `ctx.exit()`

## Input and Live Views

Use `ctx.input` for prompts and key-driven terminal flows. Key reads normalize
common terminal sequences such as arrows, enter, escape, delete, and backspace.

```python
@app.command()
async def poll(ctx: argon.Context) -> None:
    while True:
        ...
        if await ctx.input.sleep(1.0, stop_keys={"q", " "}):
            return
```

Use `ctx.out.live()` for custom Rich live renderables that should participate in
Argon's nested-live guard.

```python
@app.command()
def browse(ctx: argon.Context) -> None:
    with ctx.output.live(render_view(), transient=True) as live:
        with ctx.input.keys() as keys:
            while True:
                key = keys.read_key(0.03)
                if key in {"q", "escape"}:
                    return
                live.update(render_view(), refresh=True)
```

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
