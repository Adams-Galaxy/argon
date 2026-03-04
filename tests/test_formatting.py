from __future__ import annotations

from rich.text import Text

from argon.ui.formatter import Formatter
from argon.ui.rich_console import build_console
from argon.ui.template import render, render_ansi
from argon.ui.tokens import PrefixBroker, StaticBroker, build_system_broker


def test_template_render_plain_token() -> None:
    out = render("hello {name}", tokens={"name": "world"})
    assert str(out) == "hello world"


def test_template_render_default_fallback() -> None:
    out = render("hello {name|world}", tokens={"name": ""})
    assert str(out) == "hello world"


def test_template_render_literal_braces() -> None:
    out = render("{{name}}", tokens={})
    assert str(out) == "{name}"


def test_template_collapses_empty_bracket_placeholder() -> None:
    out = render("hello[{name}]", tokens={"name": ""})
    assert str(out) == "hello"


def test_template_resolves_callable_token() -> None:
    out = render("hello {name}", tokens={"name": lambda _: "Ada"})
    assert str(out) == "hello Ada"


def test_render_ansi_ends_with_reset() -> None:
    console = build_console(force_terminal=True, width=80)
    out = render_ansi("{name}", tokens={"name": "Ada"}, console=console)
    assert out.endswith("\x1b[0m")


def test_render_ansi_includes_style_codes_when_markup_is_used() -> None:
    console = build_console(force_terminal=True, width=80)
    out = render_ansi("[argon.title]Ada[/argon.title]", tokens={}, console=console)
    assert "\x1b[" in out
    assert out != "Ada\x1b[0m"


def test_formatter_renders_text_and_layers() -> None:
    formatter = Formatter(base_broker=StaticBroker({"app.name": "argon"}), console=build_console())
    formatter.set_token("name", "Ada")
    text = formatter.render_text("hello {name}")
    assert isinstance(text, Text)
    assert text.plain == "hello Ada"


def test_formatter_exposes_dynamic_system_tokens() -> None:
    formatter = Formatter(
        base_broker=PrefixBroker("system.", build_system_broker()),
        console=build_console(),
    )
    value = formatter.resolve_token("system.time")
    assert isinstance(value, str)
    assert ":" in value
