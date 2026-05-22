from __future__ import annotations

from typing import Annotated

import argon


def _fragments(app: argon.App, line: str) -> list[tuple[str, tuple[str, ...]]]:
    return [
        (line[span.start : span.end], span.styles)
        for span in app.console().highlight(line)
        if span.styles
    ]


def test_highlight_empty_line(demo_app: argon.App) -> None:
    assert demo_app.console().highlight("") == []


def test_highlight_command_option_and_value(demo_app: argon.App) -> None:
    spans = demo_app.console().highlight("greet Ada --times 2")
    assert spans[0].styles == ("argon.command",)
    assert any(span.styles == ("argon.option",) for span in spans)
    assert any(span.styles == ("argon.number",) for span in spans)


def test_highlight_nested_command_path_and_typed_values() -> None:
    app = argon.App(name="git")
    remote = app.group("remote")

    @remote.command()
    def add(
        name: Annotated[str, argon.Argument()],
        url: Annotated[str, argon.Argument()],
        retries: Annotated[int, argon.Option("--retries")] = 1,
        timeout: Annotated[float, argon.Option("--timeout")] = 1.5,
        dry_run: Annotated[bool, argon.Option("--dry-run")] = False,
    ) -> None:
        return None

    line = 'remote add origin "ssh://git/repo" --retries -2 --timeout=1.5 --dry-run'
    assert _fragments(app, line) == [
        ("remote", ("argon.command",)),
        ("add", ("argon.command",)),
        ("origin", ("argon.value",)),
        ('"ssh://git/repo"', ("argon.string",)),
        ("--retries", ("argon.option",)),
        ("-2", ("argon.number",)),
        ("--timeout", ("argon.option",)),
        ("1.5", ("argon.number",)),
        ("--dry-run", ("argon.option",)),
    ]


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


def test_highlight_option_equals_keeps_key_separator_and_number_distinct(
    demo_app: argon.App,
) -> None:
    line = "greet Ada --times=2"
    fragments = [
        (line[span.start : span.end], span.styles) for span in demo_app.console().highlight(line)
    ]
    assert ("--times", ("argon.option",)) in fragments
    assert ("=", ()) in fragments
    assert ("2", ("argon.number",)) in fragments


def test_highlight_help_builtin_as_command(demo_app: argon.App) -> None:
    spans = demo_app.console().highlight("help greet")
    assert spans[0].styles == ("argon.command",)
    assert any(span.styles == ("argon.command",) for span in spans[2:])


def test_highlight_version_builtin_as_command(demo_app: argon.App) -> None:
    spans = demo_app.console().highlight("version")
    assert spans[0].styles == ("argon.command",)
