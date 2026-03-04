from __future__ import annotations

from typing import Annotated

import argon


def test_public_exports() -> None:
    assert "App" in argon.__all__
    assert "AppConfig" in argon.__all__
    assert "LiveDisplayError" in argon.__all__
    assert "LiveConfig" in argon.__all__
    assert "Shell" in argon.__all__
    assert "run" in argon.__all__
    assert "default_theme" in argon.__all__
    assert "semantic_style_groups" in argon.__all__


def test_group_and_add_typer(demo_app: argon.App) -> None:
    child = argon.App(name="admin", help="Admin tools")

    @child.command()
    def ping() -> str:
        return "pong"

    demo_app.add_typer(child, name="admin")
    assert demo_app.run_argv(["admin", "ping"]) == "pong"


def test_app_call_uses_sys_argv(monkeypatch) -> None:
    app = argon.App(name="demo")

    @app.command()
    def greet(name: str) -> str:
        return name

    monkeypatch.setattr("sys.argv", ["demo", "greet", "Ada"])
    assert app() == "Ada"


def test_run_single_function_shortcut(monkeypatch) -> None:
    def main(name: Annotated[str, argon.Argument(help="Name")]) -> str:
        return name

    monkeypatch.setattr("sys.argv", ["demo", "Ada"])
    assert argon.run(main) == "Ada"


def test_app_console_is_stable_instance(demo_app: argon.App) -> None:
    assert demo_app.console() is demo_app.console()
