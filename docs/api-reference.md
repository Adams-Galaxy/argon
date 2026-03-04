# API Reference

## Public Exports

```python
from argon import (
    App,
    Context,
    Console,
    Shell,
    Argument,
    Option,
    run,
    AppConfig,
    ShellConfig,
    PromptConfig,
    LiveConfig,
    CompletionConfig,
    ArgonTheme,
    ThemeLayer,
    default_theme,
    semantic_style_groups,
    Abort,
    Exit,
    BadParameter,
    UsageError,
    ArgonError,
    LiveDisplayError,
)
```

## App

- registration: `command()`, `group()`, `callback()`, `add_typer()`
- backend access: `console()`
- shell access: `shell()`, `run_shell()`
- sync execution: `run_argv()`, `run_line()`, `__call__()`
- async execution: `run_argv_async()`, `run_line_async()`

## Console

- sync execution: `execute_argv()`, `execute_line()`
- async execution: `execute_argv_async()`, `execute_line_async()`
- shell semantics: `complete()`, `highlight()`, `help()`

## Context

- execution metadata: `command_path`, `args`, `params`, `raw_argv`, `passthrough`
- output: `ctx.out`
- control flow: `abort()`, `exit()`
- command composition: `invoke()`, `forward()`

## Config Models

- `AppConfig`
- `ShellConfig`
- `PromptConfig`
- `LiveConfig`
- `CompletionConfig`

All config models provide:

- `from_mapping()`
- `from_file()`

`ShellConfig` also provides:

- `with_prompt()`
- `with_prompt_tokens()`
