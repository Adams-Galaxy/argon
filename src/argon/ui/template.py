from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from rich.console import Console, Group, RenderableType
from rich.markup import escape
from rich.text import Text

from .tokens import StaticBroker, TokenBroker, TokenFn, TokenValue


@dataclass(slots=True)
class _Resolution:
    active: set[str]


def render(
    template: str,
    *,
    tokens: Mapping[str, TokenValue | TokenFn] | TokenBroker,
    formatter: object | None = None,
    resolution: _Resolution | None = None,
    strict: bool = False,
) -> RenderableType:
    broker = StaticBroker(tokens) if isinstance(tokens, Mapping) else tokens
    active_resolution = resolution or _Resolution(active=set())
    result = _render_segments(
        _collapse_bracketed_placeholders(
            template,
            broker,
            strict=strict,
            formatter=formatter,
            resolution=active_resolution,
        ),
        broker,
        strict=strict,
        formatter=formatter,
        resolution=active_resolution,
    )
    if all(isinstance(part, Text) for part in result):
        out = Text()
        for part in result:
            if isinstance(part, Text):
                out.append_text(part)
        return out
    return Group(*result)


def render_ansi(
    template: str,
    *,
    tokens: Mapping[str, TokenValue | TokenFn] | TokenBroker,
    console: Console,
    formatter: object | None = None,
    resolution: _Resolution | None = None,
    strict: bool = False,
) -> str:
    renderable = render(
        template,
        tokens=tokens,
        formatter=formatter,
        resolution=resolution,
        strict=strict,
    )
    with console.capture() as capture:
        console.print(renderable, end="")
    out = capture.get()
    if not out.endswith("\x1b[0m"):
        out += "\x1b[0m"
    return out


def _token_is_empty(value: TokenValue | None) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return value == ""
    if isinstance(value, Text):
        return value.plain == ""
    return False


def _resolve_token(
    broker: TokenBroker,
    name: str,
    *,
    strict: bool,
    formatter: object | None,
    resolution: _Resolution,
) -> TokenValue | None:
    if name in resolution.active:
        if strict:
            raise RuntimeError(f"Token cycle detected: {name}")
        return ""
    resolution.active.add(name)
    raw = broker.get(name)
    try:
        if raw is None:
            if strict:
                raise KeyError(name)
            return None
        if callable(raw):
            return raw(formatter)  # type: ignore[arg-type]
        return raw
    finally:
        resolution.active.discard(name)


def _render_segments(
    template: str,
    broker: TokenBroker,
    *,
    strict: bool,
    formatter: object | None,
    resolution: _Resolution,
) -> list[RenderableType]:
    out: list[RenderableType] = []
    buf: list[str] = []

    def flush_buf() -> None:
        if not buf:
            return
        out.append(Text.from_markup("".join(buf)))
        buf.clear()

    i = 0
    while i < len(template):
        if template[i : i + 2] == "{{":
            buf.append("{")
            i += 2
            continue
        if template[i : i + 2] == "}}":
            buf.append("}")
            i += 2
            continue
        if template[i] != "{":
            buf.append(template[i])
            i += 1
            continue

        j = template.find("}", i + 1)
        if j == -1:
            buf.append(template[i])
            i += 1
            continue

        expr = template[i + 1 : j].strip()
        if not expr:
            buf.append("{}")
            i = j + 1
            continue

        name, sep, fallback = expr.partition("|")
        value = _resolve_token(
            broker,
            name.strip(),
            strict=strict,
            formatter=formatter,
            resolution=resolution,
        )
        if _token_is_empty(value) and sep:
            value = fallback.strip()
        if _token_is_empty(value):
            value = ""

        if isinstance(value, Text):
            flush_buf()
            out.append(value)
        elif isinstance(value, str):
            buf.append(escape(value))
        else:
            flush_buf()
            out.append(value)  # type: ignore[arg-type]
        i = j + 1

    flush_buf()
    return out


def _collapse_bracketed_placeholders(
    template: str,
    broker: TokenBroker,
    *,
    strict: bool,
    formatter: object | None,
    resolution: _Resolution,
) -> str:
    out: list[str] = []
    i = 0

    while i < len(template):
        if template[i] != "[":
            out.append(template[i])
            i += 1
            continue

        end = template.find("]", i + 1)
        if end == -1:
            out.append(template[i])
            i += 1
            continue

        inner = template[i + 1 : end].strip()
        if not (inner.startswith("{") and inner.endswith("}")):
            out.append(template[i : end + 1])
            i = end + 1
            continue

        expr = inner[1:-1].strip()
        name, sep, fallback = expr.partition("|")
        value = _resolve_token(
            broker,
            name.strip(),
            strict=strict,
            formatter=formatter,
            resolution=resolution,
        )
        if _token_is_empty(value) and sep:
            value = fallback.strip()
        if _token_is_empty(value):
            i = end + 1
            continue
        out.append(str(value))
        i = end + 1

    return "".join(out)
