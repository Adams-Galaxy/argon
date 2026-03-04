# Theming

Argon uses a stable semantic style namespace. Themes should target semantic keys instead of compatibility aliases.

## Semantic Style Groups

- `foundation`: surface/chrome/selection primitives
- `text`: primary/title/muted text
- `feedback`: success/warning/error
- `shell`: command/option/value/string/number/error highlighting
- `prompt`: brand/context/meta/symbol prompt styles
- `live`: spinner/progress/status styles
- `ptk`: completion menu and scrollbar styles

Use `argon.semantic_style_groups()` to inspect the canonical key set.

## Compose Themes

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
```

## Apply Theme

```python
app = argon.App(name="demo", theme=theme)
```

## JSON Theme Config

`AppConfig.theme` accepts an Argon theme mapping. See `examples/demo.config.json`.
