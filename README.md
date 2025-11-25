# Argon

Modern, fully Pythonic hierarchical CLI framework.

Features:
- Hierarchical command groups and nested commands
- Decorator-based registration (`@cli.command`, `cli.group("..."))`)
- Automatic option inference from function defaults
- Aliases for commands
- Global options (parsed before command path)
- Context injection (`ctx` parameter)
- Middleware, pre & post hooks
- Colorized help output
- REPL and shell completion generation
- Strict mode for unknown options (`allow_free_options=False`)

> Requires Python 3.10 or newer.

## Quick Start
```python
from argon import Interface

cli = Interface(name="demo", version="0.1.0")

@cli.command(help="Greet someone", aliases=["hi"])  # --times inferred
def greet(ctx, name: str, times: int = 1):
    for i in range(times):
        ctx.emit(f"[{i+1}] Hello {name}")

if __name__ == "__main__":
    cli.run_argv()
```

Output:
```
[1] Hello world
[2] Hello world
[3] Hello world
```

## Run from `sys.argv`

`Interface.run_argv()` consumes `sys.argv[1:]` (or a custom sequence) so your CLI can act like a regular executable:

```python
if __name__ == "__main__":
    cli.run_argv()  # reads sys.argv[1:]
```

Pass in an explicit sequence for testing:

```python
cli.run_argv(["greet", "team", "--times", "5"])
```
```

## Groups & Aliases
```python
data = cli.group("data", help="Data ops")

@data.command(help="Summarize numbers", aliases=["stats"])
def summary(ctx, *values: str):
    nums = [float(v) for v in values]
    if not nums:
        ctx.emit("none")
        return
    ctx.emit(f"min={min(nums)} max={max(nums)} avg={sum(nums)/len(nums):.2f}")
```
Use:
```
cli.run_line("data summary 1 2 3 4")
cli.run_line("data stats 5 6 7")  # alias
```

## Global Options
```python
cli.add_global_option(
    "verbose", flags=["-v", "--verbose"], is_flag=True, help="Verbose logging"
)
```
Global options must appear before the command path:
```
cli.run_line("-v data summary 1 2 3")
```
Access inside a command via context:
```python
@cli.command()
def action(ctx):
    if ctx.global_options.verbose:
        print("verbose on")
```

## Context Injection
Add a `ctx` parameter to receive runtime context (CLI instance, command spec, parsed args, global options):
```python
@cli.command()
def login(ctx, user: str, password: str):
    if ctx.global_options.get("verbose"):
        print("authenticating...")
```

## Strict vs Free Options
Unknown options are accepted and auto-cast by default. Disable with:
```python
cli = Interface(allow_free_options=False)
```
Then an unknown option will raise `CommandUsageError`.

## REPL
```python
cli.repl()
```
Type `help` inside to list commands.

## Async Commands & Shell
Define async commands with `async def` and use `AsyncShell` (or `await cli.run_line_async(...)`).
```python
from argon import Interface, AsyncShell
import asyncio

cli = Interface()

@cli.command()
async def fetch(url: str):
    # simulate async I/O
    await asyncio.sleep(0.1)
    print(f"fetched {url}")

async def main():
    await cli.run_line_async("fetch https://example.com")
    term = AsyncShell(cli)
    await term.loop()

asyncio.run(main())
```

## Completion Script
```python
print(cli.generate_completion())
```
Add the output to your shell configuration.

## Plugin Loading
Entry-point group usage (define in other packages):
```python
cli.load_plugins("argon.plugins")
```
Each entry point should resolve to a callable accepting the `cli` instance.

## Error Types
- `CommandNotFound`
- `CommandUsageError`
- `CommandExecutionError`

## Demo
See `examples/demo.py` for a fuller demonstration.

## Contributing
Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for environment setup, testing expectations, and pull request guidelines.

## Changelog
All notable changes are tracked in [CHANGELOG.md](CHANGELOG.md).

## License
Argon is available under the [MIT License](LICENSE).
