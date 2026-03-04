# Argon v1 Contract

Status: locked working contract

Purpose: define the public API and architectural boundaries for the Argon rewrite so implementation stays aligned with the intended product shape.

Core question:

> What if Typer's authoring model was designed for shell-first terminal UX from the beginning?

This document is the north star for that answer.

## Product Thesis

Argon is:

- Typer-inspired in authoring style
- shell-first in runtime design
- Rich-first in formatting
- prompt_toolkit-backed at the terminal frontend
- UI-neutral in its core parsing, dispatch, completion, and highlighting contracts

Argon is not:

- a reimplementation of Typer internals
- a generic TUI framework
- a PTK-bound command engine
- a string-only CLI helper

## First Principles

1. One command model, multiple execution surfaces.
2. The shell is a frontend, not the source of truth.
3. Rich formatting is canonical; ANSI is derived from it.
4. The public API should feel familiar to Typer users.
5. Interactive shell UX is a first-class use case, not an afterthought.

## Top-Level Architecture

Argon has two primary runtime layers.

### Console

The `Console` is the backend runtime for the CLI.

It owns:

- command registration model
- parse and invocation model
- dispatch
- context creation
- semantic completion generation
- semantic highlighting generation
- help generation
- formatting integration
- output API backing `ctx.out`

It does not own:

- prompt session lifecycle
- terminal history UI
- PTK keybindings
- PTK menus
- PTK lexer objects

### Shell

The `Shell` is the physical terminal frontend.

It owns:

- interactive prompt loop
- PTK session integration
- history
- keybindings
- completion menu materialization
- lexer adapter materialization
- prompt rendering at the terminal boundary

It does not own:

- command parsing rules
- command tree semantics
- help semantics
- completion logic
- highlighting logic
- command dispatch

## Public API

The v1 public surface is intentionally small.

```python
from argon import (
    App,
    Context,
    Argument,
    Option,
    Shell,
    Console,
    Abort,
    Exit,
    BadParameter,
    UsageError,
    run,
)
```

Anything not listed above is internal unless deliberately promoted later.

## Public Types

### App

`App` is the main user-facing application object.

It is responsible for:

- defining commands and groups
- nesting sub-apps
- exposing `Console` and `Shell` entrypoints
- executing argv or line input

Public methods:

```python
class App:
    def __init__(
        self,
        *,
        name: str | None = None,
        help: str | None = None,
        version: str | None = None,
        no_args_is_help: bool = False,
        invoke_without_command: bool = False,
    ) -> None: ...

    def command(
        self,
        name: str | None = None,
        *,
        help: str | None = None,
        hidden: bool = False,
        deprecated: bool = False,
        aliases: tuple[str, ...] = (),
    ): ...

    def group(
        self,
        name: str | None = None,
        *,
        help: str | None = None,
        hidden: bool = False,
        aliases: tuple[str, ...] = (),
    ): ...

    def callback(
        self,
        *,
        invoke_without_command: bool | None = None,
        no_args_is_help: bool | None = None,
    ): ...

    def add_typer(
        self,
        app: "App",
        *,
        name: str | None = None,
        help: str | None = None,
    ) -> None: ...

    def console(self) -> "Console": ...
    def shell(self, **kwargs) -> "Shell": ...

    def run_argv(self, argv: list[str] | None = None) -> object: ...
    def run_line(self, line: str) -> object: ...
    def run_shell(self, **kwargs) -> int: ...

    def __call__(self) -> object: ...
```

Behavioral rules:

- `App()` should be sufficient for the common case.
- `@app.command()` should feel immediately familiar to Typer users.
- `app()` should execute argv-style CLI behavior.
- `app.run_shell()` should launch the interactive shell using the same command graph.
- `app.console()` must return the backend execution surface for tooling and testing.

### Context

`Context` is injected into command handlers when requested.

Public attributes:

```python
class Context:
    app: App
    console: Console
    command_path: tuple[str, ...]
    args: tuple[object, ...]
    params: dict[str, object]
    raw_argv: tuple[str, ...]
    passthrough: tuple[str, ...]
    obj: object | None
    meta: dict[str, object]
    out: "Output"
    parent: "Context | None"
```

Public methods:

```python
class Context:
    def abort(self, message: str | None = None) -> "NoReturn": ...
    def exit(self, code: int = 0) -> "NoReturn": ...
    def invoke(self, fn, /, *args, **kwargs): ...
    def forward(self, fn, /, **overrides): ...
```

Behavioral rules:

- `Context` must expose execution state without leaking PTK concerns.
- `ctx.out` is the canonical output surface for handlers.
- `ctx.abort()` and `ctx.exit()` must terminate execution in a controlled way.

### Console

`Console` is the public backend runtime.

Public methods:

```python
class Console:
    def execute_argv(self, argv: list[str]) -> object: ...
    def execute_line(self, line: str) -> object: ...

    def complete(self, line: str, cursor: int | None = None) -> "CompletionResult": ...
    def highlight(self, line: str) -> list["StyledSpan"]: ...
    def help(self, path: tuple[str, ...] = ()) -> object: ...
```

Behavioral rules:

- `execute_argv()` and `execute_line()` must target the same command graph.
- `complete()` must be UI-neutral.
- `highlight()` must return semantic spans, not PTK fragments.
- `help()` must produce Rich-first output.

### Shell

`Shell` is the public interactive session wrapper.

Public methods:

```python
class Shell:
    def __init__(
        self,
        console: Console,
        *,
        prompt: str = "{app.name}> ",
        history: bool = True,
        mouse_support: bool = False,
    ) -> None: ...

    def run(self) -> int: ...
```

Behavioral rules:

- `Shell` must adapt console contracts into PTK behavior.
- `Shell` must not reimplement parsing or dispatch.

### Option and Argument

Argon supports Typer-like parameter metadata through `Annotated`.

Preferred style:

```python
from typing import Annotated
import argon

@app.command()
def greet(
    ctx: argon.Context,
    name: Annotated[str, argon.Argument(help="Target name")],
    times: Annotated[int, argon.Option("--times", "-t", help="Repeat count")] = 1,
):
    ...
```

Minimal inferred style is also supported:

```python
@app.command()
def greet(name: str, times: int = 1):
    ...
```

Public factories:

```python
def Option(
    *param_decls: str,
    help: str | None = None,
    metavar: str | None = None,
    envvar: str | list[str] | None = None,
    parser: callable | None = None,
    autocompletion: callable | None = None,
    default_factory: callable | None = None,
    hidden: bool = False,
    show_default: bool | str = True,
    rich_help_panel: str | None = None,
) -> object: ...
```

```python
def Argument(
    *,
    help: str | None = None,
    metavar: str | None = None,
    parser: callable | None = None,
    autocompletion: callable | None = None,
    default_factory: callable | None = None,
    hidden: bool = False,
    show_default: bool | str = True,
    rich_help_panel: str | None = None,
) -> object: ...
```

Behavioral rules:

- The public authoring model should feel close to Typer.
- Parameter metadata should be represented internally as structured model objects, not ad hoc flags.
- Boolean options should be inferred from type/default in v1 unless explicit support proves necessary.

### Output

`ctx.out` is a first-class output surface, not a thin alias for `print()`.

Public methods:

```python
class Output:
    def text(self, value: str = "", *, style: str | None = None) -> None: ...
    def rich(self, renderable: object) -> None: ...
    def error(self, message: str) -> None: ...
    def warning(self, message: str) -> None: ...
    def success(self, message: str) -> None: ...
    def panel(self, title: str, body: object) -> None: ...
    def kv(self, title: str, data: dict[str, object] | str) -> None: ...
    def rule(self, title: str | None = None) -> None: ...
```

Behavioral rules:

- User handlers should write via `ctx.out`, not `print()`.
- Rich renderables must be first-class output values.
- Output should remain backend-owned so shell and non-shell execution stay consistent.

### Exceptions

Public exceptions:

```python
class ArgonError(Exception): ...
class UsageError(ArgonError): ...
class BadParameter(UsageError): ...
class Abort(ArgonError): ...
class Exit(ArgonError):
    code: int
```

Behavioral rules:

- user code may raise these intentionally
- usage and validation failures should map to `UsageError`/`BadParameter`
- controlled termination should map to `Abort`/`Exit`

### run()

`run()` is the single-function shortcut.

```python
def run(
    fn,
    *,
    name: str | None = None,
    help: str | None = None,
    version: str | None = None,
) -> object: ...
```

Behavioral rules:

- `run(func)` should provide a zero-friction onboarding path.
- It should compile a temporary app from a single function.

## Canonical Runtime Contracts

These contracts define the internal semantic model that multiple frontends can share.

### Invocation

```python
@dataclass
class Invocation:
    path: tuple[str, ...]
    argv: tuple[str, ...]
    args: tuple[object, ...]
    options: dict[str, object]
    passthrough: tuple[str, ...] = ()
```

Rules:

- `Invocation` is the canonical parse result.
- argv execution and shell execution must converge into the same invocation shape.

### CompletionItem

```python
@dataclass(frozen=True)
class CompletionItem:
    text: str
    display: str | None = None
    meta: str | None = None
```

Rules:

- completion generation must be UI-neutral
- PTK must adapt this model, not replace it

### StyledSpan

```python
@dataclass(frozen=True)
class StyledSpan:
    start: int
    end: int
    styles: tuple[str, ...]
```

Rules:

- highlighting output must be semantic and UI-neutral
- spans refer to offsets in the original line
- PTK/Textual adapters may transform spans later

### CommandResult

```python
@dataclass
class CommandResult:
    value: object = None
    exit_code: int = 0
    renderable: object | None = None
```

Rules:

- commands may return plain values
- the runtime may also represent richer rendered outcomes explicitly
- exact internal use can evolve as long as public behavior remains stable

## Parsing Model

Argon will support two parse surfaces that compile into the same invocation model.

### argv Parser

Properties:

- strict
- deterministic
- command-execution focused
- close to Typer user expectations

### shell Parser

Properties:

- incremental
- partial-parse friendly
- span-preserving
- suitable for completions and highlighting

Rule:

- both parsers must converge into the same invocation and dispatch semantics

## Formatting Model

Argon is Rich-first.

Formatting is a first-class subsystem, not scattered helpers.

The formatter subsystem should provide:

- semantic tokens
- token brokers
- template rendering
- Rich renderable output
- ANSI output derived from Rich rendering

Rules:

- help text, prompt text, and runtime output must share the same formatting philosophy
- ANSI should be derived from Rich, not maintained separately
- semantic style names should be stable and backend-neutral

## Adapter Isolation Rules

These are hard architecture rules.

1. No `prompt_toolkit` imports outside `argon/shell/ptk`.
2. No shell frontend logic inside the command model or dispatch core.
3. No help/completion/highlighting semantics inside PTK adapter code.
4. No direct terminal rendering assumptions in command handlers.

## Authoring Expectations

Argon should support:

- Typer-like decorators
- type-hint driven parameter inference
- `Annotated[..., Option(...)]` and `Annotated[..., Argument(...)]`
- nested groups
- callback-style app hooks
- shell-first execution without changing author code

Argon does not need v1 parity with every Typer feature.

The important compatibility target is:

- familiar mental model
- familiar parameter declaration style
- familiar help/error expectations

## Example Target UX

```python
from typing import Annotated
import argon

app = argon.App(name="demo", help="Shell-first CLI")

@app.command()
def greet(
    ctx: argon.Context,
    name: Annotated[str, argon.Argument(help="Target name")],
    times: Annotated[int, argon.Option("--times", "-t", help="Repeat count")] = 1,
):
    for _ in range(times):
        ctx.out.text(f"Hello {name}")

if __name__ == "__main__":
    app()
```

The same app should also support:

```python
app.run_shell()
```

without a separate command definition model.

## Explicit Non-Goals For v1

These are intentionally out of scope unless implementation forces a revisit.

- Textual UI
- plugin ecosystem
- shell scripting or macro language
- full Click compatibility
- every Typer parameter edge case
- arbitrary custom PTK frontend APIs in the public surface

## Decision Filters

When implementation decisions are unclear, choose the option that best preserves:

1. Typer-like authoring ergonomics
2. Console/Shell separation
3. UI-neutral core contracts
4. Rich-first formatting
5. a shell-native user experience

