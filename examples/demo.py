"""Executable demo showing core Argon CLI & shell features.

Run with: python -m examples.demo
Then interactively type commands (e.g., `hello world --times=3`, `data summary 1 2 3`, `auth login admin secret -v`).
Type `exit` or `quit` to leave the terminal.
"""
from argon import Interface, Shell, default_logging

default_logging()

cli = Interface(
    name="demo",
    version="0.1.0",
    description="Demo CLI for showcasing Argon features",
    allow_free_options=True,
)

# Global option (e.g. --verbose)
cli.add_global_option(
    "verbose",
    flags=["-v", "--verbose"],
    is_flag=True,
    help="Enable verbose logging output",
)

@cli.command(help="Say hello a number of times (infers --times)")
def hello(ctx, name: str, times: int = 1):
    for i in range(times):
        ctx.emit(f"[{i+1}] Hello {name}")

# Group with nested command and alias
data = cli.group("data", help="Data operations")

@data.command(help="Print stats for numbers", aliases=["stats"])
def summary(ctx, *values: str):
    nums = [float(v) for v in values]
    if not nums:
        ctx.emit("No numbers provided")
        return
    ctx.emit(f"count={len(nums)} min={min(nums)} max={max(nums)} avg={sum(nums)/len(nums):.2f}")

# Group inside group
adv = data.group("advanced", help="Advanced operations")

@adv.command(help="Multiply numbers (requires at least 2)", min_positionals=2)
def multiply(ctx, *values: str):
    result = 1
    for v in values:
        result *= float(v)
    ctx.emit(str(result))

# Demonstrate context injection
auth = cli.group("auth", help="Authentication commands")

@auth.command(help="Login with username/password")
def login(ctx, username: str, password: str):  # ctx first param required
    if ctx.global_options.get("verbose"):
        ctx.emit("[verbose] Attempting login...")
    # (Fake) authentication logic
    if username == "admin" and password == "secret":
        ctx.emit("Logged in!")
    else:
        ctx.emit("Invalid credentials")

# Middleware example
cli.add_middleware(lambda parsed, spec: None)  # placeholder no-op

if __name__ == "__main__":
    # Quick scripted examples
    cli.run_line("hello world --times=2")
    cli.run_line("data summary 1 2 3 4 5")
    cli.run_line("data stats 10 20 30")  # alias
    cli.run_line("data advanced multiply 2 3 4")
    cli.run_line("auth login admin secret -v")

    # Launch interactive terminal (console input/output)
    term = Shell(cli)
    term.loop()
