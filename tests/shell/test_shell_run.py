from __future__ import annotations

import asyncio

import pytest

import argon


def test_shell_run_uses_ptk_adapter(monkeypatch, demo_app: argon.App) -> None:
    called = {"value": False}

    def fake_run_ptk_repl(console, session, *, mouse_support: bool = False) -> int:
        called["value"] = True
        assert console is demo_app.console()
        assert session.prompt == "{app.name}> "
        assert console.rich_console.is_terminal is True
        return 0

    monkeypatch.setattr("argon.shell.ptk.repl.run_ptk_repl", fake_run_ptk_repl)
    shell = argon.Shell(demo_app.console())
    assert shell.run() == 0
    assert called["value"] is True


def test_shell_run_async_uses_ptk_async_adapter(monkeypatch, demo_app: argon.App) -> None:
    called = {"value": False}

    async def fake_run_ptk_repl_async(console, session, *, mouse_support: bool = False) -> int:
        called["value"] = True
        assert console is demo_app.console()
        assert session.prompt == "{app.name}> "
        assert console.rich_console.is_terminal is True
        return 0

    monkeypatch.setattr("argon.shell.ptk.repl.run_ptk_repl_async", fake_run_ptk_repl_async)
    shell = argon.Shell(demo_app.console())

    async def runner() -> int:
        return await shell.run_async()

    assert asyncio.run(runner()) == 0
    assert called["value"] is True


def test_shell_carries_history_path(demo_app: argon.App) -> None:
    shell = argon.Shell(demo_app.console(), history_path=".demo-history")
    assert shell.session.history_path is not None
    assert shell.session.history_path.name == ".demo-history"


def test_shell_uses_app_shell_config_defaults() -> None:
    app = argon.App(
        name="demo",
        shell_config=argon.ShellConfig(
            history_path=".argon-history",
            prompt=argon.PromptConfig(template="{app.name} {system.time}> "),
        ),
    )
    shell = argon.Shell(app.console())
    assert shell.session.prompt == "{app.name} {system.time}> "
    assert shell.session.history_path is not None
    assert shell.session.history_path.name == ".argon-history"


def _render_shell_usage_error(app: argon.App, line: str) -> None:
    with pytest.raises(argon.UsageError) as exc_info:
        app.run_line(line)
    app.console().render_shell_error(line, exc_info.value)


def test_shell_resolved_usage_errors_default_to_command_help(demo_app: argon.App, capsys) -> None:
    _render_shell_usage_error(demo_app, "greet")
    out = capsys.readouterr().out
    assert "Usage:" in out
    assert "Missing argument: name" not in out


def test_shell_unknown_commands_still_render_error(demo_app: argon.App, capsys) -> None:
    _render_shell_usage_error(demo_app, "missing")
    out = capsys.readouterr().out
    assert "Unknown command: missing" in out


def test_shell_can_render_resolved_usage_error_only(capsys) -> None:
    app = argon.App(
        name="demo",
        shell_config=argon.ShellConfig(usage_error_display="error"),
    )

    @app.command()
    def greet(name: str) -> str:
        return name

    _render_shell_usage_error(app, "greet")
    out = capsys.readouterr().out
    assert "Missing argument: name" in out
    assert "Usage:" not in out


def test_shell_can_render_resolved_usage_error_before_help(capsys) -> None:
    app = argon.App(
        name="demo",
        shell_config=argon.ShellConfig(usage_error_display="both"),
    )

    @app.command()
    def greet(name: str) -> str:
        return name

    _render_shell_usage_error(app, "greet")
    out = capsys.readouterr().out
    error_index = out.index("Missing argument: name")
    help_index = out.index("Usage:")
    assert error_index < help_index


def test_basic_shell_renders_interrupt_and_keeps_running(monkeypatch, capsys) -> None:
    app = argon.App(name="demo")
    lines = iter(["stop"])

    @app.command()
    def stop() -> None:
        raise KeyboardInterrupt

    def fake_input(prompt: str) -> str:
        del prompt
        try:
            return next(lines)
        except StopIteration:
            raise EOFError from None

    monkeypatch.setattr("builtins.input", fake_input)

    shell = argon.Shell(app.console(), history=False)
    assert shell._run_basic() == 0
    out = capsys.readouterr().out
    assert "Interrupted" in out


def test_basic_shell_prompt_interrupt_exits(monkeypatch, capsys) -> None:
    app = argon.App(name="demo")

    def fake_input(prompt: str) -> str:
        del prompt
        raise KeyboardInterrupt

    monkeypatch.setattr("builtins.input", fake_input)

    shell = argon.Shell(app.console(), history=False)
    assert shell._run_basic() == 0
    out = capsys.readouterr().out
    assert "Interrupted" not in out


def test_basic_shell_async_runs_async_commands(monkeypatch, capsys) -> None:
    app = argon.App(name="demo")
    lines = iter(["wait"])

    @app.command()
    async def wait(ctx: argon.Context) -> None:
        await asyncio.sleep(0)
        ctx.output.success("done")

    def fake_input(prompt: str) -> str:
        del prompt
        try:
            return next(lines)
        except StopIteration:
            raise EOFError from None

    monkeypatch.setattr("builtins.input", fake_input)

    shell = argon.Shell(app.console(), history=False)

    async def runner() -> int:
        return await shell._run_basic_async()

    assert asyncio.run(runner()) == 0
    out = capsys.readouterr().out
    assert "done" in out


def test_basic_shell_async_prompt_interrupt_exits(monkeypatch, capsys) -> None:
    app = argon.App(name="demo")

    def fake_input(prompt: str) -> str:
        del prompt
        raise KeyboardInterrupt

    monkeypatch.setattr("builtins.input", fake_input)

    shell = argon.Shell(app.console(), history=False)

    async def runner() -> int:
        return await shell._run_basic_async()

    assert asyncio.run(runner()) == 0
    out = capsys.readouterr().out
    assert "Interrupted" not in out
