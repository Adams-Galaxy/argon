from __future__ import annotations

from ...console.errors import Interrupted
from .completions import make_completer
from .history import build_history
from .keybindings import build_key_bindings
from .lexer import make_lexer
from .style import build_style


def _execute_line_with_terminal_released(ptk, console, line: str) -> None:
    with ptk.app.input.cooked_mode():
        try:
            console.execute_line(line)
        except (Interrupted, KeyboardInterrupt):
            console.render_shell_interrupt()
        except Exception as exc:  # noqa: BLE001
            console.render_shell_error(line, exc)


async def _execute_line_with_terminal_released_async(ptk, console, line: str) -> None:
    with ptk.app.input.cooked_mode():
        try:
            await console.execute_line_async(line)
        except (Interrupted, KeyboardInterrupt):
            console.render_shell_interrupt()
        except Exception as exc:  # noqa: BLE001
            console.render_shell_error(line, exc)


def _build_prompt_session(console, session, *, mouse_support: bool = False):
    from prompt_toolkit import PromptSession

    return PromptSession(
        completer=make_completer(console),
        lexer=make_lexer(console),
        style=build_style(theme=console.app.theme),
        history=build_history(str(session.history_path) if session.history_path else None),
        key_bindings=build_key_bindings(),
        mouse_support=mouse_support,
    )


def run_ptk_repl(console, session, *, mouse_support: bool = False) -> int:
    from prompt_toolkit.formatted_text import ANSI

    ptk = _build_prompt_session(console, session, mouse_support=mouse_support)

    while True:
        try:
            prompt = console.formatter.render_ansi(
                session.prompt,
                extra=session.prompt_tokens,
            )
            line = ptk.prompt(ANSI(prompt))
        except (EOFError, KeyboardInterrupt):
            return 0
        if not line.strip():
            continue
        session.history.append(line)
        _execute_line_with_terminal_released(ptk, console, line)


async def run_ptk_repl_async(console, session, *, mouse_support: bool = False) -> int:
    from prompt_toolkit.formatted_text import ANSI

    ptk = _build_prompt_session(console, session, mouse_support=mouse_support)

    while True:
        try:
            prompt = console.formatter.render_ansi(
                session.prompt,
                extra=session.prompt_tokens,
            )
            line = await ptk.prompt_async(ANSI(prompt))
        except (EOFError, KeyboardInterrupt):
            return 0
        if not line.strip():
            continue
        session.history.append(line)
        await _execute_line_with_terminal_released_async(ptk, console, line)
