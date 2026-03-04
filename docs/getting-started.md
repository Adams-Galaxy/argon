# Getting Started

## Install

```bash
python -m pip install argon
```

For local development:

```bash
python -m pip install -e ".[dev]"
```

## Minimal App

```python
from typing import Annotated
import argon

app = argon.App(name="demo", help="Shell-first CLI")


@app.command()
def greet(
    ctx: argon.Context,
    name: Annotated[str, argon.Argument(help="Who to greet")],
    times: Annotated[int, argon.Option("--times", "-t")] = 1,
) -> None:
    for _ in range(times):
        ctx.out.text(f"Hello {name}")


if __name__ == "__main__":
    app()
```

## Shell Mode

Run the same command graph interactively:

```python
app.run_shell()
```

Or use a shell-first `main`:

```python
import sys

def main() -> None:
    argv = sys.argv[1:]
    if not argv:
        app.run_shell()
        return
    app.run_argv(argv)
```
