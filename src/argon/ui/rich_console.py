from __future__ import annotations

from rich.console import Console

from .theme import ArgonTheme, build_theme


def build_console(
    *,
    theme: ArgonTheme | None = None,
    force_terminal: bool = False,
    width: int | None = None,
) -> Console:
    color_system = "standard" if force_terminal else "auto"
    return Console(
        theme=build_theme(theme),
        highlight=False,
        force_terminal=force_terminal,
        color_system=color_system,
        width=width,
    )
