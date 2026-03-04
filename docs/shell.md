# Shell

`Shell` is an interactive frontend over the backend `Console`.

## Run

```python
app.run_shell()
```

`App.run_shell()` uses the same command graph as `run_argv()` and `run_line()`.

## Configuration

Shell behavior is configured through `ShellConfig`:

```python
import argon

app = argon.App(
    shell_config=argon.ShellConfig(
        history=True,
        history_path=".argon-history",
        mouse_support=False,
    )
)
```

## Completion Menu Controls

```python
import argon

app = argon.App(
    shell_config=argon.ShellConfig(
        completion=argon.CompletionConfig(
            option_display="long",       # long | short | all | none
            show_help_tooltips=False,    # hide PTK completion metadata column
        )
    )
)
```

`option_display` behavior:

- `long`: show long options when available, otherwise short-only options.
- `short`: show short options when available, otherwise long-only options.
- `all`: show both short and long option declarations.
- `none`: suppress option-name completion suggestions.
