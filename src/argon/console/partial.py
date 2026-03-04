from __future__ import annotations

from dataclasses import dataclass

from .parser import split_line
from .registry import Resolution, resolve


@dataclass(frozen=True, slots=True)
class PartialParse:
    tokens: tuple[str, ...]
    resolution: Resolution
    current: str
    replace_start: int
    replace_end: int


def parse_partial(root, line: str, cursor: int | None = None) -> PartialParse:
    cur = len(line) if cursor is None else max(0, min(cursor, len(line)))
    before = line[:cur]
    tokens = split_line(before) if before.strip() else []
    resolution = resolve(root, tokens)
    if before and not before[-1].isspace():
        current = tokens[-1] if tokens else ""
        replace_end = cur
        replace_start = cur - len(current)
    else:
        current = ""
        replace_start = cur
        replace_end = cur
    return PartialParse(
        tokens=tuple(tokens),
        resolution=resolution,
        current=current,
        replace_start=replace_start,
        replace_end=replace_end,
    )
