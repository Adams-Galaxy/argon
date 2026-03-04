from __future__ import annotations

from examples.demo import DEMO_CONFIG, DEMO_THEME, app


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


def test_demo_task_mode_completion() -> None:
    result = app.console().complete("task run build --mode f")
    assert "fast" in [item.text for item in result.items]


def test_demo_shell_prompt_uses_dynamic_tokens() -> None:
    app.console().meta.clear()
    app.run_argv(["workspace", "use", "infra", "--profile", "prod"])
    shell = app.shell()
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


def test_demo_config_is_loaded_from_file() -> None:
    assert DEMO_CONFIG.theme is not None
    assert DEMO_CONFIG.shell.history_path == ".argon-demo-history"


def test_demo_wait_command_runs_async_spinner(capsys) -> None:
    result = app.run_argv(["wait", "--seconds", "0"])
    assert result == "remote task complete"
    out = capsys.readouterr().out
    assert "remote task complete" in out


def test_demo_progress_commands_render(capsys) -> None:
    app.run_argv(["build", "--steps", "2"])
    app.run_argv(["sync", "--items", "2"])
    out = capsys.readouterr().out
    assert "Building release" in out
    assert "Syncing artifacts" in out


def test_demo_pipeline_and_fanout_render(capsys) -> None:
    app.run_argv(["pipeline"])
    app.run_argv(["fanout"])
    out = capsys.readouterr().out
    assert "Release pipeline" in out
    assert "Fanout" in out
    assert "publish" in out


def test_demo_probe_uses_result_driven_finish_state(capsys) -> None:
    degraded = app.run_argv(["probe"])
    healthy = app.run_argv(["probe", "--healthy"])
    out = capsys.readouterr().out
    assert degraded == "degraded"
    assert healthy == "healthy"
    assert "Probe result: degraded" in out
    assert "Probe result: healthy" in out
    assert "Service is degraded" in out
    assert "Service is healthy" in out


def test_demo_nested_guard_command(capsys) -> None:
    app.run_argv(["nested"])
    out = capsys.readouterr().out
    assert "Another live display is already active" in out
