# Argon

Argon is a Typer-inspired, shell-first CLI framework built around Rich and
prompt_toolkit.

It keeps a familiar decorator-based authoring model while treating interactive
terminal UX as a first-class runtime concern.

## Status

Argon v1.0.0 is the current stable release.

Public docs start at [`docs/index.md`](docs/index.md).

Internal architecture contracts are maintained under `docs/dev/`, including:

- [`docs/dev/contract.md`](docs/dev/contract.md)
- [`docs/dev/theming.md`](docs/dev/theming.md)

The stable theme namespace is documented in
[`docs/theming.md`](docs/theming.md).

## Example

```python
from typing import Annotated

import argon

app = argon.App(name="demo", help="Shell-first CLI")


@app.command()
def greet(
    ctx: argon.Context,
    name: Annotated[str, argon.Argument(help="Who to greet")],
    times: Annotated[int, argon.Option("--times", "-t", help="Repeat count")] = 1,
) -> None:
    for _ in range(times):
        ctx.out.text(f"Hello {name}")


if __name__ == "__main__":
    app()
```

You can also run the same command graph interactively:

```python
app.run_shell()
```

Prompts and shell behavior can be configured at the app layer:

```python
app = argon.App(
    name="demo",
    theme=argon.default_theme().with_overrides(
        "brand",
        {
            "argon.shell.command": "bold bright_yellow",
            "argon.prompt.brand": "{argon.shell.command}",
            "argon.ptk.menu.current": "bold black on bright_yellow",
        },
    ),
    shell_config=argon.ShellConfig(
        history_path=".demo-history",
        completion=argon.CompletionConfig(
            option_display="long",
            show_help_tooltips=False,
        ),
        prompt=argon.PromptConfig(
            template="[argon.prompt.brand]{app.name}[/argon.prompt.brand]{system.time_badge} [argon.prompt.symbol]>[/argon.prompt.symbol] ",
            tokens={
                "system.time_badge": lambda formatter: f" {formatter.resolve_token('system.time')}",
            },
        ),
    ),
)
```

Static shell/theme config can also be loaded from JSON and then extended in
Python with dynamic prompt tokens:

```python
config = argon.AppConfig.from_file("examples/demo.config.json")

app = argon.App(
    name="demo",
    theme=config.theme,
    shell_config=config.shell.with_prompt_tokens(
        {
            "system.time_badge": lambda formatter: f" {formatter.resolve_token('system.time')}",
        }
    ),
)
```

Argon also has first-class live Rich output on `ctx.out` for shell-facing
commands:

```python
@app.command()
async def deploy(ctx: argon.Context) -> None:
    await ctx.out.awaiting(run_deploy(), message="Deploying")

@app.command()
def build(ctx: argon.Context) -> None:
    with ctx.out.progress() as progress:
        task_id = progress.add_task("Building", total=5)
        ...

@app.command()
async def fanout(ctx: argon.Context) -> None:
    await ctx.out.gather(
        {
            "index": index_job(),
            "publish": publish_job(),
        }
    )
```

Live completion behavior can come from config defaults or from the command
result itself:

```python
result = await ctx.out.awaiting(
    probe(),
    message="Probing service",
    final="success",
    resolve_final=lambda value: "success" if value == "healthy" else "error",
)
```

## Reference Demo

The reference Argon demo lives in:

- [`examples/demo.py`](examples/demo.py)

It shows the intended flow for Argon apps:

- start with `app = argon.App(...)`
- prefer `Annotated[..., argon.Argument(...)]` and `Annotated[..., argon.Option(...)]`
- send terminal output through `ctx.out`
- keep argv execution and shell execution on the same command graph
- compose theme layers against stable semantic style keys
- default to a shell-first experience when the app is run with no argv
