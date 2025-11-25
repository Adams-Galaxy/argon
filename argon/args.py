from __future__ import annotations
from typing import Any, Dict, List, Optional, Set, Union

class ParsedArgs:
    """Container exposing arguments via multiple paradigms."""

    def __init__(
        self,
        positionals: Optional[List[str]] = None,
        options: Optional[Dict[str, Any]] = None,
        flags: Optional[Set[str]] = None,
    ) -> None:
        self.positionals = positionals or []
        self.options = options or {}
        self.flags = flags or set()

    def __iter__(self):
        return iter(self.positionals)

    def __len__(self) -> int:
        return len(self.positionals)

    def __getitem__(self, key: Union[int, str]):
        if isinstance(key, int):
            return self.positionals[key]
        return self.options.get(key)

    def __getattr__(self, item: str) -> Any:
        if item in self.options:
            return self.options[item]
        raise AttributeError(item)

    def get(self, key: str, default: Any = None) -> Any:
        return self.options.get(key, default)

    @property
    def list(self) -> List[str]:
        return self.positionals

    @property
    def dict(self) -> Dict[str, Any]:
        return self.options

    def to_dict(self) -> Dict[str, Any]:
        data = dict(self.options)
        data["_positionals"] = list(self.positionals)
        return data

__all__ = ["ParsedArgs"]
