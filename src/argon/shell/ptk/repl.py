from __future__ import annotations

from .completions import make_completer
from .history import build_history
from .keybindings import build_key_bindings
from .lexer import make_lexer
from .style import build_style


def run_ptk_repl(console, session, *, mouse_support: bool = False) -> int:
    from prompt_toolkit import PromptSession
    from prompt_toolkit.formatted_text import ANSI

    ptk: PromptSession[str] = PromptSession(
        completer=make_completer(console),
        lexer=make_lexer(console),
        style=build_style(theme=console.app.theme),
        history=build_history(str(session.history_path) if session.history_path else None),
        key_bindings=build_key_bindings(),
        mouse_support=mouse_support,
    )

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
        try:
            console.execute_line(line)
        except Exception as exc:  # noqa: BLE001
            console.output.error(str(exc))
