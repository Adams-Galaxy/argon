from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping

from rich.console import Console, RenderableType
from rich.text import Text

from .template import render, render_ansi
from .tokens import ChainBroker, StaticBroker, TokenBroker, TokenFn, TokenValue


@dataclass(slots=True)
class Formatter:
    base_broker: TokenBroker
    console: Console
    ansi_console: Console | None = None
    _layers: list[dict[str, TokenValue | TokenFn]] = field(default_factory=list)

    @property
    def broker(self) -> TokenBroker:
        if not self._layers:
            return self.base_broker
        return ChainBroker(tuple(StaticBroker(layer) for layer in self._layers) + (self.base_broker,))

    def push_layer(self) -> None:
        self._layers.insert(0, {})

    def set_token(self, name: str, value: TokenValue | TokenFn) -> None:
        if not self._layers:
            self.push_layer()
        self._layers[0][name] = value

    def resolve_token(self, name: str) -> TokenValue | None:
        raw = self.broker.get(name)
        if raw is None:
            return None
        if callable(raw):
            return raw(self)  # type: ignore[arg-type]
        return raw

    def render(
        self,
        template: str,
        *,
        extra: Mapping[str, TokenValue | TokenFn] | None = None,
    ) -> RenderableType:
        broker = self.broker
        if extra:
            broker = ChainBroker((StaticBroker(dict(extra)), broker))
        return render(template, tokens=broker, formatter=self)

    def render_text(
        self,
        template: str,
        *,
        extra: Mapping[str, TokenValue | TokenFn] | None = None,
    ) -> Text:
        rendered = self.render(template, extra=extra)
        if isinstance(rendered, Text):
            return rendered
        return Text(str(rendered))

    def render_ansi(
        self,
        template: str,
        *,
        extra: Mapping[str, TokenValue | TokenFn] | None = None,
    ) -> str:
        broker = self.broker
        if extra:
            broker = ChainBroker((StaticBroker(dict(extra)), broker))
        return render_ansi(
            template,
            tokens=broker,
            console=self.ansi_console or self.console,
            formatter=self,
        )
