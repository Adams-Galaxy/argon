from __future__ import annotations

from examples.demo import DEMO_SHELL_CONFIG, DEMO_THEME, app


def test_demo_reference_app_runs(capsys) -> None:
    app.console().meta.clear()
    result = app.run_argv(["greet", "Ada", "--times", "2"])
    assert result == "Hello Ada"
    out = capsys.readouterr().out
    assert out.count("Hello Ada") == 2


def test_demo_workspace_flow(capsys) -> None:
    app.console().meta.clear()
    app.run_argv(["workspace", "use", "core", "--profile", "staging"])
    out = capsys.readouterr().out
    assert "Workspace core active on staging" in out
    assert app.console().meta["workspace"] == "core"
    assert app.console().meta["profile"] == "staging"


def test_demo_release_channel_completion() -> None:
    result = app.console().complete("release api --channel p")
    assert "preview" in [item.text for item in result.items]


def test_demo_shell_prompt_uses_dynamic_tokens() -> None:
    app.console().meta.clear()
    shell = app.shell()
    initial_prompt = app.console().formatter.render_ansi(
        shell.session.prompt,
        extra=shell.session.prompt_tokens,
    )
    assert "local" in initial_prompt

    app.run_argv(["workspace", "use", "infra", "--profile", "prod"])
    prompt = app.console().formatter.render_ansi(
        shell.session.prompt,
        extra=shell.session.prompt_tokens,
    )
    assert "argon-demo" in prompt
    assert "infra" in prompt
    assert "prod" in prompt
    assert "\x1b[" in prompt


def test_demo_theme_is_layered_and_resolved() -> None:
    styles = DEMO_THEME.resolved_styles()
    assert styles["argon.shell.command"] == "bold bright_yellow"
    assert styles["argon.prompt.brand"] == "bold bright_yellow"
    assert styles["argon.ptk.menu.current"] == "bold black on bright_yellow"


def test_demo_shell_config_is_defined_in_python() -> None:
    assert DEMO_SHELL_CONFIG.history_path == ".argon-demo-history"
    assert DEMO_SHELL_CONFIG.completion.option_display == "long"
    assert DEMO_SHELL_CONFIG.completion.show_help_tooltips is False
    assert DEMO_SHELL_CONFIG.prompt.tokens


def test_demo_release_runs_async_live_output(capsys) -> None:
    result = app.run_argv(["release", "api", "--channel", "preview"])
    out = capsys.readouterr().out
    assert result == {"build": "ready", "package": "ready", "publish": "done"}
    assert "Release" in out
    assert "api" in out
    assert "preview" in out
