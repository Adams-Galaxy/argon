from __future__ import annotations

import pytest

from argon.shell.ptk.style import build_style
from argon.ui.theme import (
    ArgonTheme,
    SEMANTIC_STYLE_KEYS,
    ThemeCycleError,
    ThemeLayer,
    ThemeMissingKeysError,
    default_theme,
    semantic_style_groups,
)


def test_theme_resolves_style_references() -> None:
    theme = default_theme().with_overrides(
        "test",
        {
            "argon.shell.command": "bold green",
            "argon.prompt.brand": "{argon.shell.command}",
        },
    )
    styles = theme.resolved_styles()
    assert styles["argon.prompt.brand"] == "bold green"


def test_theme_detects_cycles() -> None:
    theme = default_theme().with_overrides(
        "cycle",
        {
            "argon.shell.command": "{argon.prompt.brand}",
            "argon.prompt.brand": "{argon.shell.command}",
        },
    )
    with pytest.raises(ThemeCycleError):
        theme.resolved_styles()


def test_ptk_style_uses_resolved_theme_values() -> None:
    theme = default_theme().with_overrides(
        "test",
        {
            "argon.shell.command": "bold green",
            "argon.ptk.menu.current": "bold black on bright_green",
        },
    )
    style = build_style(theme=theme)
    attrs = style.get_attrs_for_style_str("class:argon.command")
    assert attrs.bold is True
    assert attrs.color is not None


def test_theme_exposes_stable_semantic_groups() -> None:
    groups = semantic_style_groups()
    assert "shell" in groups
    assert "prompt" in groups
    assert "live" in groups
    assert "argon.shell.command" in groups["shell"]
    assert "argon.progress.bar" in groups["live"]
    assert set(SEMANTIC_STYLE_KEYS).issuperset(groups["ptk"])


def test_theme_rejects_missing_semantic_keys() -> None:
    theme = ArgonTheme(
        base=ThemeLayer(
            name="broken",
            styles={
                "argon.shell.command": "bold cyan",
            },
        )
    )
    with pytest.raises(ThemeMissingKeysError):
        theme.resolved_styles()
