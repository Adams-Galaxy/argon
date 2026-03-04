from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path

from ..ui.tokens import TokenFn, TokenValue


@dataclass(slots=True)
class ShellSession:
    prompt: str = "{app.name}> "
    history: list[str] = field(default_factory=list)
    history_path: Path | None = None
    prompt_tokens: Mapping[str, TokenValue | TokenFn] = field(default_factory=dict)
