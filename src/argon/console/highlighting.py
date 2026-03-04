from __future__ import annotations

from dataclasses import dataclass

from ..models import StyledSpan
from .registry import resolve


@dataclass(frozen=True, slots=True)
class TokenSpan:
    kind: str
    start: int
    end: int


def tokenize(line: str) -> list[TokenSpan]:
    spans: list[TokenSpan] = []
    i = 0
    while i < len(line):
        ch = line[i]
        if ch.isspace():
            j = i + 1
            while j < len(line) and line[j].isspace():
                j += 1
            spans.append(TokenSpan("ws", i, j))
            i = j
            continue
        if ch in {'"', "'"}:
            quote = ch
            j = i + 1
            while j < len(line) and line[j] != quote:
                if quote == '"' and line[j] == "\\":
                    j += 2
                else:
                    j += 1
            if j < len(line):
                j += 1
                spans.append(TokenSpan("quoted", i, j))
                i = j
            else:
                spans.append(TokenSpan("error", i, len(line)))
                break
            continue
        j = i + 1
        while j < len(line) and not line[j].isspace() and line[j] not in {'"', "'"}:
            j += 1
        spans.append(TokenSpan("word", i, j))
        i = j
    return spans


def highlight(root, line: str) -> list[StyledSpan]:
    spans = tokenize(line)
    if not spans:
        return []
    words = [line[span.start : span.end] for span in spans if span.kind != "ws"]
    builtin_words = words
    builtin_mode: str | None = None
    if words and words[0] == "help":
        builtin_mode = "help"
        builtin_words = words[1:]
    elif words and words[0] == "version":
        builtin_mode = "version"
        builtin_words = []

    resolution = resolve(root, builtin_words)
    command_len = len(resolution.path)
    out: list[StyledSpan] = []
    word_index = 0
    unresolved_command = (
        builtin_mode is None
        and bool(words)
        and resolution.command is None
        and len(resolution.path) == 0
    )
    for span in spans:
        text = line[span.start : span.end]
        if span.kind == "ws":
            out.append(StyledSpan(span.start, span.end, ()))
            continue
        if span.kind == "error":
            out.append(StyledSpan(span.start, span.end, ("argon.error",)))
            word_index += 1
            continue
        if unresolved_command and word_index == 0:
            out.append(StyledSpan(span.start, span.end, ("argon.error",)))
            word_index += 1
            continue

        if builtin_mode is not None and word_index == 0:
            out.append(StyledSpan(span.start, span.end, ("argon.command",)))
            word_index += 1
            continue

        if text.startswith("-") and "=" in text:
            key, value = text.split("=", 1)
            eq_idx = span.start + len(key)
            out.append(StyledSpan(span.start, eq_idx, ("argon.option",)))
            out.append(StyledSpan(eq_idx, eq_idx + 1, ()))
            if value.isdigit():
                value_style = ("argon.number",)
            elif value.startswith('"') or value.startswith("'"):
                value_style = ("argon.string",)
            else:
                value_style = ("argon.value",)
            out.append(StyledSpan(eq_idx + 1, span.end, value_style))
            word_index += 1
            continue

        effective_word_index = word_index - 1 if builtin_mode is not None else word_index
        if builtin_mode == "version":
            styles = ("argon.value",)
        elif effective_word_index < command_len:
            styles = ("argon.command",)
        elif text.startswith("-"):
            styles = ("argon.option",)
        elif span.kind == "quoted":
            styles = ("argon.string",)
        elif text.lstrip("-").replace(".", "", 1).isdigit():
            styles = ("argon.number",)
        else:
            styles = ("argon.value",)
        out.append(StyledSpan(span.start, span.end, styles))
        word_index += 1
    return out
