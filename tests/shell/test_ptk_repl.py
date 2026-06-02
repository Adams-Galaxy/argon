from __future__ import annotations

import asyncio

import argon
from argon.shell.ptk.repl import (
    _execute_line_with_terminal_released,
    _execute_line_with_terminal_released_async,
    run_ptk_repl,
    run_ptk_repl_async,
)


class _CookedMode:
    def __init__(self, events: list[str]) -> None:
        self.events = events

    def __enter__(self) -> None:
        self.events.append("enter-cooked")

    def __exit__(self, exc_type, exc, tb) -> None:  # type: ignore[no-untyped-def]
        self.events.append("exit-cooked")


class _Input:
    def __init__(self, events: list[str]) -> None:
        self.events = events

    def cooked_mode(self) -> _CookedMode:
        return _CookedMode(self.events)


class _App:
    def __init__(self, events: list[str]) -> None:
        self.input = _Input(events)


class _Session:
    def __init__(self, events: list[str]) -> None:
        self.app = _App(events)


class _Console:
    def __init__(self, events: list[str]) -> None:
        self.events = events

    def execute_line(self, line: str) -> None:
        self.events.append(f"execute:{line}")

    async def execute_line_async(self, line: str) -> None:
        self.events.append(f"execute-async:{line}")

    def render_shell_error(self, line: str, error: Exception) -> None:
        self.events.append(f"error:{line}:{error}")

    def render_shell_interrupt(self) -> None:
        self.events.append("interrupt")


def test_ptk_releases_terminal_input_while_command_runs() -> None:
    events: list[str] = []
    _execute_line_with_terminal_released(_Session(events), _Console(events), "browse")
    assert events == ["enter-cooked", "execute:browse", "exit-cooked"]


def test_ptk_releases_terminal_input_while_rendering_command_errors() -> None:
    class FailingConsole(_Console):
        def execute_line(self, line: str) -> None:
            raise RuntimeError("boom")

    events: list[str] = []
    _execute_line_with_terminal_released(_Session(events), FailingConsole(events), "browse")
    assert events == ["enter-cooked", "error:browse:boom", "exit-cooked"]


def test_ptk_releases_terminal_input_and_continues_after_keyboard_interrupt() -> None:
    class InterruptedConsole(_Console):
        def execute_line(self, line: str) -> None:
            raise KeyboardInterrupt

    events: list[str] = []
    _execute_line_with_terminal_released(_Session(events), InterruptedConsole(events), "browse")
    assert events == ["enter-cooked", "interrupt", "exit-cooked"]


def test_ptk_async_releases_terminal_input_while_command_runs() -> None:
    events: list[str] = []

    async def runner() -> None:
        await _execute_line_with_terminal_released_async(
            _Session(events),
            _Console(events),
            "browse",
        )

    asyncio.run(runner())
    assert events == ["enter-cooked", "execute-async:browse", "exit-cooked"]


def test_ptk_prompt_interrupt_exits_repl(monkeypatch, capsys) -> None:
    app = argon.App(name="demo")
    shell = argon.Shell(app.console(), history=False)
    prompts = iter(["interrupt"])

    class FakePromptSession:
        def __init__(self, **kwargs) -> None:  # type: ignore[no-untyped-def]
            del kwargs

        def prompt(self, prompt) -> str:  # type: ignore[no-untyped-def]
            del prompt
            event = next(prompts)
            if event == "interrupt":
                raise KeyboardInterrupt
            raise EOFError

    monkeypatch.setattr("prompt_toolkit.PromptSession", FakePromptSession)

    assert run_ptk_repl(app.console(), shell.session) == 0
    out = capsys.readouterr().out
    assert "Interrupted" not in out


def test_ptk_prompt_async_runs_async_repl(monkeypatch, capsys) -> None:
    app = argon.App(name="demo")
    shell = argon.Shell(app.console(), history=False)
    prompts = iter(["wait", "eof"])

    @app.command()
    async def wait(ctx: argon.Context) -> None:
        await asyncio.sleep(0)
        ctx.output.success("done")

    class FakePromptSession:
        def __init__(self, **kwargs) -> None:  # type: ignore[no-untyped-def]
            del kwargs
            self.app = _App([])

        async def prompt_async(self, prompt) -> str:  # type: ignore[no-untyped-def]
            del prompt
            event = next(prompts)
            if event == "eof":
                raise EOFError
            return event

    monkeypatch.setattr("prompt_toolkit.PromptSession", FakePromptSession)

    async def runner() -> int:
        return await run_ptk_repl_async(app.console(), shell.session)

    assert asyncio.run(runner()) == 0
    out = capsys.readouterr().out
    assert "done" in out


def test_ptk_prompt_async_interrupt_exits_repl(monkeypatch, capsys) -> None:
    app = argon.App(name="demo")
    shell = argon.Shell(app.console(), history=False)
    prompts = iter(["interrupt"])

    class FakePromptSession:
        def __init__(self, **kwargs) -> None:  # type: ignore[no-untyped-def]
            del kwargs

        async def prompt_async(self, prompt) -> str:  # type: ignore[no-untyped-def]
            del prompt
            event = next(prompts)
            if event == "interrupt":
                raise KeyboardInterrupt
            raise EOFError

    monkeypatch.setattr("prompt_toolkit.PromptSession", FakePromptSession)

    async def runner() -> int:
        return await run_ptk_repl_async(app.console(), shell.session)

    assert asyncio.run(runner()) == 0
    out = capsys.readouterr().out
    assert "Interrupted" not in out
