from __future__ import annotations

from ...ui.theme import ArgonTheme, default_theme


def _rich_style_to_ptk(style: object) -> str:
    if style is None:
        return ""
    raw = str(style).strip()
    if not raw or raw == "none":
        return ""

    attrs: list[str] = []
    fg: str | None = None
    bg: str | None = None

    ansi_map = {
        "black": "ansiblack",
        "red": "ansired",
        "green": "ansigreen",
        "yellow": "ansiyellow",
        "blue": "ansiblue",
        "magenta": "ansimagenta",
        "cyan": "ansicyan",
        "white": "ansigray",
        "bright_black": "ansibrightblack",
        "bright_red": "ansibrightred",
        "bright_green": "ansibrightgreen",
        "bright_yellow": "ansibrightyellow",
        "bright_blue": "ansibrightblue",
        "bright_magenta": "ansibrightmagenta",
        "bright_cyan": "ansibrightcyan",
        "bright_white": "ansiwhite",
        "gray": "ansigray",
        "grey": "ansigray",
        "bright_gray": "ansiwhite",
        "bright_grey": "ansiwhite",
    }

    def to_ansi(name: str) -> str | None:
        color = name.strip().lower()
        if not color or color == "none":
            return None
        if color in {"default"}:
            return color
        if color.startswith("#"):
            return color
        if color.startswith("ansi"):
            return color
        mapped = ansi_map.get(color)
        if mapped is not None:
            return mapped
        if color.startswith("bright_"):
            base = color.removeprefix("bright_")
            if base == "white":
                return "ansiwhite"
            if base in {"black", "red", "green", "yellow", "blue", "magenta", "cyan"}:
                return f"ansibright{base}"
        return color

    tokens = iter(raw.split())
    for token in tokens:
        if token in {"bold", "dim", "italic", "underline", "reverse"}:
            attrs.append(token)
            continue
        if token == "on":
            try:
                bg = to_ansi(next(tokens))
            except StopIteration:
                break
            continue
        fg = to_ansi(token)

    parts = [*attrs]
    if fg:
        parts.append(fg)
    if bg:
        parts.append(f"bg:{bg}")
    return " ".join(parts)


def build_style(*, theme: ArgonTheme | None = None):
    from prompt_toolkit.styles import Style

    styles = (theme or default_theme()).resolved_styles()
    return Style.from_dict(
        {
            "argon.command": _rich_style_to_ptk(styles["argon.shell.command"]),
            "argon.option": _rich_style_to_ptk(styles["argon.shell.option"]),
            "argon.value": _rich_style_to_ptk(styles["argon.shell.value"]),
            "argon.string": _rich_style_to_ptk(styles["argon.shell.string"]),
            "argon.number": _rich_style_to_ptk(styles["argon.shell.number"]),
            "argon.error": _rich_style_to_ptk(styles["argon.shell.error"]),
            "completion-menu": _rich_style_to_ptk(styles["argon.ptk.menu"]),
            "completion-menu.completion": _rich_style_to_ptk(styles["argon.ptk.menu"]),
            "completion-menu.completion.current": _rich_style_to_ptk(
                styles["argon.ptk.menu.current"]
            ),
            "completion-menu.meta.completion": _rich_style_to_ptk(styles["argon.ptk.menu.meta"]),
            "completion-menu.meta.completion.current": _rich_style_to_ptk(
                styles["argon.ptk.menu.meta.current"]
            ),
            "completion-toolbar": _rich_style_to_ptk(styles["argon.ptk.menu"]),
            "completion-toolbar.completion.current": _rich_style_to_ptk(
                styles["argon.ptk.menu.current"]
            ),
            "scrollbar.background": _rich_style_to_ptk(styles["argon.ptk.scrollbar.dim"]),
            "scrollbar.button": _rich_style_to_ptk(styles["argon.ptk.scrollbar"]),
            "scrollbar.arrow": _rich_style_to_ptk(styles["argon.chrome.border"]),
        }
    )
