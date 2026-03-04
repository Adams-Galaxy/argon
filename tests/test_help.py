from __future__ import annotations

import argon


def _render(console, renderable) -> str:
    with console.capture() as capture:
        console.print(renderable)
    return capture.get()


def test_app_help_renders_groups_and_commands(demo_app: argon.App) -> None:
    renderable = demo_app.console().help()
    text = _render(demo_app.console().rich_console, renderable)
    assert "greet" in text
    assert "users" in text


def test_command_help_renders_parameter_help(demo_app: argon.App) -> None:
    renderable = demo_app.console().help(("greet",))
    text = _render(demo_app.console().rich_console, renderable)
    assert "Repeat count" in text
    assert "--times" in text


def test_hidden_command_is_omitted_from_group_help() -> None:
    app = argon.App(name="demo")

    @app.command(hidden=True)
    def hidden() -> None:
        return None

    renderable = app.console().help()
    text = _render(app.console().rich_console, renderable)
    assert "hidden" not in text


def test_help_includes_usage_line(demo_app: argon.App) -> None:
    renderable = demo_app.console().help(("greet",))
    text = _render(demo_app.console().rich_console, renderable)
    assert "Usage:" in text
