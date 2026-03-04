from __future__ import annotations

from prompt_toolkit.document import Document

from argon.shell.ptk.completions import make_completer


def test_ptk_completer_adapts_console_completion(demo_app) -> None:
    completer = make_completer(demo_app.console())
    doc = Document(text="gr", cursor_position=2)
    texts = [item.text for item in completer.get_completions(doc, None)]  # type: ignore[arg-type]
    assert "greet" in texts


def test_ptk_completer_hides_meta_by_default(demo_app) -> None:
    completer = make_completer(demo_app.console())
    doc = Document(text="greet Ada --", cursor_position=12)
    completions = list(completer.get_completions(doc, None))  # type: ignore[arg-type]
    assert completions
    assert all(item.display_meta_text == "" for item in completions)


def test_ptk_completer_can_show_meta_when_enabled() -> None:
    import argon

    app = argon.App(
        name="demo",
        shell_config=argon.ShellConfig(
            completion=argon.CompletionConfig(show_help_tooltips=True),
        ),
    )

    @app.command()
    def greet(name: str, times: int = argon.Option("--times", help="Repeat count")) -> None:
        return None

    completer = make_completer(app.console())
    doc = Document(text="greet Ada --", cursor_position=12)
    completions = list(completer.get_completions(doc, None))  # type: ignore[arg-type]
    assert any(item.text == "--times" for item in completions)
    assert any(item.display_meta is not None for item in completions)
