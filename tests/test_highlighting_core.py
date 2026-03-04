from __future__ import annotations

import argon


def test_highlight_empty_line(demo_app: argon.App) -> None:
    assert demo_app.console().highlight("") == []


def test_highlight_command_option_and_value(demo_app: argon.App) -> None:
    spans = demo_app.console().highlight("greet Ada --times 2")
    assert spans[0].styles == ("argon.command",)
    assert any(span.styles == ("argon.option",) for span in spans)
    assert any(span.styles == ("argon.number",) for span in spans)


def test_highlight_quoted_string(demo_app: argon.App) -> None:
    spans = demo_app.console().highlight('greet "Ada Lovelace"')
    assert any(span.styles == ("argon.string",) for span in spans)


def test_highlight_malformed_quote_marks_error(demo_app: argon.App) -> None:
    spans = demo_app.console().highlight('greet "Ada')
    assert spans[-1].styles == ("argon.error",)


def test_highlight_span_boundaries_are_valid(demo_app: argon.App) -> None:
    line = "greet Ada --times 2"
    spans = demo_app.console().highlight(line)
    for span in spans:
        assert 0 <= span.start <= span.end <= len(line)


def test_highlight_unknown_command_marks_error(demo_app: argon.App) -> None:
    spans = demo_app.console().highlight("bogus test")
    assert spans[0].styles == ("argon.error",)


def test_highlight_option_equals_splits_value(demo_app: argon.App) -> None:
    spans = demo_app.console().highlight("greet Ada --times=2")
    assert any(span.styles == ("argon.option",) for span in spans)
    assert any(span.styles == ("argon.number",) for span in spans)


def test_highlight_help_builtin_as_command(demo_app: argon.App) -> None:
    spans = demo_app.console().highlight("help greet")
    assert spans[0].styles == ("argon.command",)
    assert any(span.styles == ("argon.command",) for span in spans[2:])


def test_highlight_version_builtin_as_command(demo_app: argon.App) -> None:
    spans = demo_app.console().highlight("version")
    assert spans[0].styles == ("argon.command",)
