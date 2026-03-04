from __future__ import annotations

import argon


def test_complete_top_level_commands(demo_app: argon.App) -> None:
    result = demo_app.console().complete("gr")
    assert [item.text for item in result.items] == ["greet"]


def test_complete_nested_group_commands(demo_app: argon.App) -> None:
    result = demo_app.console().complete("users a")
    assert [item.text for item in result.items] == ["add"]


def test_complete_option_names(demo_app: argon.App) -> None:
    result = demo_app.console().complete("greet Ada --")
    texts = [item.text for item in result.items]
    assert "--times" in texts
    assert "--loud" in texts


def test_completion_replacement_range(demo_app: argon.App) -> None:
    result = demo_app.console().complete("gr")
    assert result.replace_start == 0
    assert result.replace_end == 2


def test_completion_includes_root_builtins(demo_app: argon.App) -> None:
    demo_app.version = "1.0.0"
    result = demo_app.console().complete("ve")
    assert [item.text for item in result.items] == ["version"]


def test_completion_uses_option_value_autocompletion() -> None:
    app = argon.App(name="demo")

    @app.command()
    def run(
        target: str,
        mode: str = argon.Option("--mode", autocompletion=lambda prefix: ["fast", "full"]),
    ) -> None:
        return None

    result = app.console().complete("run build --mode f")
    assert "fast" in [item.text for item in result.items]


def test_completion_option_policy_short_prefers_short_when_available() -> None:
    app = argon.App(
        name="demo",
        shell_config=argon.ShellConfig(
            completion=argon.CompletionConfig(option_display="short"),
        ),
    )

    @app.command()
    def greet(
        name: str,
        times: int = argon.Option("--times", "-t"),
        loud: bool = argon.Option("--loud"),
    ) -> None:
        return None

    result = app.console().complete("greet Ada -")
    texts = [item.text for item in result.items]
    assert "-t" in texts
    assert "--times" not in texts
    assert "--loud" in texts


def test_completion_option_policy_all_returns_all_decls() -> None:
    app = argon.App(
        name="demo",
        shell_config=argon.ShellConfig(
            completion=argon.CompletionConfig(option_display="all"),
        ),
    )

    @app.command()
    def greet(name: str, times: int = argon.Option("--times", "-t")) -> None:
        return None

    result = app.console().complete("greet Ada -")
    texts = [item.text for item in result.items]
    assert "--times" in texts
    assert "-t" in texts


def test_completion_option_policy_none_suppresses_option_completions() -> None:
    app = argon.App(
        name="demo",
        shell_config=argon.ShellConfig(
            completion=argon.CompletionConfig(option_display="none"),
        ),
    )

    @app.command()
    def greet(name: str, times: int = argon.Option("--times", "-t")) -> None:
        return None

    result = app.console().complete("greet Ada --")
    assert [item.text for item in result.items] == []
