from __future__ import annotations

from argon.shell.ptk.repl import _execute_line_with_terminal_released


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

    def render_shell_error(self, line: str, error: Exception) -> None:
        self.events.append(f"error:{line}:{error}")


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
