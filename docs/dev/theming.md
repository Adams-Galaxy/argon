## Theming

Argon uses a stable semantic theme namespace. Themes should target these
semantic keys rather than compatibility aliases like `argon.command` or
`argon.error`.

### Style Groups

`foundation`
- `argon.surface.base`
- `argon.surface.panel`
- `argon.surface.muted`
- `argon.selection.active`
- `argon.selection.inactive`
- `argon.chrome.border`

`text`
- `argon.text.primary`
- `argon.text.muted`
- `argon.text.title`
- `argon.text.heading`

`feedback`
- `argon.feedback.success`
- `argon.feedback.warning`
- `argon.feedback.error`

`shell`
- `argon.shell.command`
- `argon.shell.option`
- `argon.shell.value`
- `argon.shell.string`
- `argon.shell.number`
- `argon.shell.error`

`prompt`
- `argon.prompt.brand`
- `argon.prompt.context`
- `argon.prompt.meta`
- `argon.prompt.symbol`

`live`
- `argon.live.spinner`
- `argon.live.message`
- `argon.live.elapsed`
- `argon.progress.description`
- `argon.progress.bar`
- `argon.progress.complete`
- `argon.progress.remaining`
- `argon.progress.percentage`

`ptk`
- `argon.ptk.menu`
- `argon.ptk.menu.current`
- `argon.ptk.menu.meta`
- `argon.ptk.menu.meta.current`
- `argon.ptk.scrollbar`
- `argon.ptk.scrollbar.dim`

### Composition Rules

- `ArgonTheme` is layered: base theme plus any number of named overrides.
- Style values can reference other styles with `{argon.some.style}`.
- All required semantic keys must exist after merging theme layers.
- Rich and prompt_toolkit both derive from the same resolved semantic theme.

### Token Namespaces

Prompt and formatter tokens also have stable namespaces.

- `app.*`: application metadata such as `app.name`, `app.help`, `app.version`
- `session.*`: mutable shell/session state carried by the console
- `system.*`: built-in runtime tokens such as `system.time`, `system.date`, `system.cwd`

Prompt-local tokens can be added through `PromptConfig.tokens`. These can be
plain values or callbacks that return Rich renderables.

### Live Output

Argon's live command UI is Rich-first and should render through the real Rich
console, not the prompt ANSI capture path.

- `ctx.out.status(...)`: themed spinner plus elapsed timer
- `ctx.out.spinner(...)`: alias for `status(...)`
- `ctx.out.progress()`: themed `Progress` instance
- `ctx.out.track(...)`: themed sequence tracker
- `ctx.out.awaiting(...)`: async helper that shows a spinner while awaiting
- `ctx.out.gather(...)`: multi-task async progress on one display
- `ctx.out.stages(...)`: grouped stage pipeline on one display

Status helpers also support finish policies:

- `final="success"`: replace the spinner with a success mark and keep the line
- `final="error"`: replace the spinner with an error mark and keep the line
- `final="clear"`: remove the live line when it completes
- `final="leave"`: preserve the last spinner frame

Argon defaults:

- `ctx.out.status(...)` defaults to `final="success"`
- `ctx.out.awaiting(...)` defaults to `final="clear"`

Progress helpers support the same finish policy model:

- `ctx.out.progress(..., final=..., failed_final=...)`
- `ctx.out.track(..., final=..., failed_final=...)`
- `ctx.out.stages(..., final=..., failed_final=...)`
- `ctx.out.gather(..., final=..., failed_final=...)`

And dynamic finalization on the progress object:

```python
with ctx.out.progress(final="success", failed_final="error") as progress:
    task_id = progress.add_task("Rollout", total=3)
    ...
    if degraded:
        progress.fail("Rollout failed")
    else:
        progress.succeed("Rollout completed")
```

These defaults can be configured in `ShellConfig.live`.
That config also controls the default spinner name, progress transience, and the
success / error symbols used for final spinner states.

Result-driven finish state is also supported. If a command can only determine
success or failure after awaiting work, use `resolve_final=` or manually finish
the status object:

```python
result = await ctx.out.awaiting(
    probe(),
    message="Probing service",
    final="success",
    resolve_final=lambda value: "success" if value == "healthy" else "error",
    resolve_message=lambda value: f"Probe result: {value}",
)
```

Or:

```python
async with ctx.out.status("Probing") as status:
    result = await probe()
    if result == "healthy":
        status.succeed()
    else:
        status.fail()
```

Nested live displays are guarded. If a command opens a second live display while
another one is active, Argon raises `LiveDisplayError` rather than letting Rich
surfaces fight over the terminal.

### File-backed Config

Argon can load static shell/theme config from JSON files:

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

Static values work well in config files. Dynamic prompt tokens remain Python
callbacks layered on top of the loaded config.

### Example

```python
import argon

theme = (
    argon.default_theme()
    .with_overrides(
        "brand",
        {
            "argon.shell.command": "bold bright_yellow",
            "argon.prompt.brand": "{argon.shell.command}",
            "argon.ptk.menu.current": "bold black on bright_yellow",
        },
    )
)

app = argon.App(
    name="demo",
    theme=theme,
    shell_config=argon.ShellConfig(
        prompt=argon.PromptConfig(
            template="[argon.prompt.brand]{app.name}[/argon.prompt.brand] {system.time}",
        )
    ),
)
```

Compatibility aliases such as `argon.command`, `argon.error`, `argon.prompt`,
and `argon.border` still exist for v1, but new themes should treat them as
derived aliases rather than primary keys.
