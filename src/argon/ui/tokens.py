from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable, Protocol, TypeAlias

from rich.console import RenderableType
from rich.text import Text

TokenValue: TypeAlias = str | Text | RenderableType
TokenFn: TypeAlias = Callable[[object | None], TokenValue]


class TokenBroker(Protocol):
    def get(self, name: str) -> TokenValue | TokenFn | None: ...
    def keys(self) -> Iterable[str]: ...


@dataclass(frozen=True, slots=True)
class StaticBroker:
    tokens: Mapping[str, TokenValue | TokenFn]

    def get(self, name: str) -> TokenValue | TokenFn | None:
        return self.tokens.get(name)

    def keys(self) -> Iterable[str]:
        return self.tokens.keys()


@dataclass(frozen=True, slots=True)
class CallableBroker:
    resolver: Callable[[str], TokenValue | TokenFn | None]
    known_keys: tuple[str, ...] = ()

    def get(self, name: str) -> TokenValue | TokenFn | None:
        return self.resolver(name)

    def keys(self) -> Iterable[str]:
        return self.known_keys


@dataclass(frozen=True, slots=True)
class PrefixBroker:
    prefix: str
    child: TokenBroker

    def get(self, name: str) -> TokenValue | TokenFn | None:
        if not name.startswith(self.prefix):
            return None
        return self.child.get(name[len(self.prefix) :])

    def keys(self) -> Iterable[str]:
        return (self.prefix + key for key in self.child.keys())


@dataclass(frozen=True, slots=True)
class ChainBroker:
    brokers: tuple[TokenBroker, ...]

    def get(self, name: str) -> TokenValue | TokenFn | None:
        for broker in self.brokers:
            value = broker.get(name)
            if value is not None:
                return value
        return None

    def keys(self) -> Iterable[str]:
        seen: set[str] = set()
        for broker in self.brokers:
            for key in broker.keys():
                if key in seen:
                    continue
                seen.add(key)
                yield key


def system_token_resolver(name: str) -> TokenValue | None:
    now = datetime.now()
    cwd = Path.cwd()
    values: dict[str, TokenValue] = {
        "time": now.strftime("%H:%M"),
        "date": now.strftime("%Y-%m-%d"),
        "datetime": now.strftime("%Y-%m-%d %H:%M:%S"),
        "cwd": str(cwd),
        "cwd.name": cwd.name,
    }
    return values.get(name)


def build_system_broker() -> TokenBroker:
    return CallableBroker(
        resolver=system_token_resolver,
        known_keys=("time", "date", "datetime", "cwd", "cwd.name"),
    )
