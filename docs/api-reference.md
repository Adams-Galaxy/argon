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
    CompletionItem,
    Input,
    KeyReader,
    ArgonTheme,
    ThemeLayer,
    default_theme,
    semantic_style_groups,
    Abort,
    Exit,
    Interrupted,
    BadParameter,
    UsageError,
    ArgonError,
    LiveDisplayError,
)
```

## App

- registration: `command()`, `group()`, `callback()`, `add_typer()`
- backend access: `console()`
- shell access: `shell()`, `run()`, `run_shell()`
- sync execution: `run_argv()`, `run_line()`
- async execution: `run_argv_async()`, `run_line_async()`
- async shell: `run_async()`, `run_shell_async()`
- shell shortcut: `__call__()`

## Console

- sync execution: `execute_argv()`, `execute_line()`
- async execution: `execute_argv_async()`, `execute_line_async()`
- shell semantics: `complete()`, `highlight()`, `help()`

## Context

- execution metadata: `command_path`, `args`, `params`, `raw_argv`, `passthrough`
- output: `ctx.output` (`ctx.out` alias)
- input: `ctx.input` (`ctx.inp` alias)
- control flow: `abort()`, `exit()`
- command composition: `invoke()`, `forward()`

## Interrupts

- `KeyboardInterrupt` and async cancellation inside command execution are normalized to `Interrupted`.
- Interactive shells render `Interrupted` and keep the shell open.
- Programmatic APIs (`run_argv()`, `run_line()`, async variants, and `Console` execution methods) raise `Interrupted` so callers can choose their own shutdown behavior.

## Input

- line prompts: `prompt()`, `prompt_async()`
- keys: `keys()`, `read_key()`, `wait_key()`, `wait_key_async()`
- interruptible async sleeps: `sleep()`

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

## Completion

- rich candidates: `CompletionItem(text, display=None, meta=None)`
