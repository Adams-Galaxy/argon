from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Callable, List, Optional, Sequence, Tuple

@dataclass
class OptionSpec:
    name: str
    flags: Sequence[str]
    type: Callable[[str], Any] = str
    default: Any = None
    is_flag: bool = False
    help: str = ""
    required: bool = False

    def format_usage(self) -> str:
        forms = ",".join(self.flags)
        return forms if self.is_flag else f"{forms} <{self.name}>"

@dataclass
class CommandSpec:
    name: str
    callback: Callable[..., Any]
    help: str = ""
    options: List[OptionSpec] = field(default_factory=list)
    aliases: List[str] = field(default_factory=list)
    positionals: List[str] = field(default_factory=list)
    vararg: Optional[str] = None
    min_positionals: int = 0
    max_positionals: Optional[int] = None
    group_path: Tuple[str, ...] = field(default_factory=tuple)

    def usage(self) -> str:
        parts = [" ".join(self.group_path + (self.name,))]
        if self.options:
            parts.append("[options]")
        if self.max_positionals is None or self.max_positionals != 0:
            parts.append("[args...]")
        return " ".join(p for p in parts if p)

__all__ = ["OptionSpec", "CommandSpec"]
