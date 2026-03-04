# Configuration

Argon v1 uses a versioned config schema validated by Pydantic v2.

## Top-level Shape

```json
{
  "schema_version": 1,
  "shell": {
    "history": true,
    "mouse_support": false,
    "history_path": ".argon-history",
    "completion": {
      "option_display": "long",
      "show_help_tooltips": false
    },
    "prompt": {
      "template": "{app.name}> ",
      "tokens": {}
    },
    "live": {
      "spinner": "dots",
      "show_elapsed": true
    }
  },
  "theme": {
    "base": {
      "name": "my-theme",
      "styles": {}
    }
  }
}
```

## Loading

```python
import argon

config = argon.AppConfig.from_file("my.config.json")
app = argon.App(theme=config.theme, shell_config=config.shell)
```

## Schema Version

- `schema_version` defaults to `1` when omitted (legacy v1 compatibility).
- Any value other than `1` raises a config validation error.

## Completion Config

`ShellConfig.completion`:

- `option_display`: `long | short | all | none` (default `long`)
- `show_help_tooltips`: `bool` (default `False`)
