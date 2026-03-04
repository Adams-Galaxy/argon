from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

from .ui.tokens import TokenFn, TokenValue

if TYPE_CHECKING:  # pragma: no cover
    from .ui.theme import ArgonTheme


@dataclass(slots=True)
class PromptConfig:
    template: str = "{app.name}> "
    tokens: Mapping[str, TokenValue | TokenFn] = field(default_factory=dict)

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any] | None = None) -> "PromptConfig":
        payload = data or {}
        tokens = payload.get("tokens", {})
        if not isinstance(tokens, Mapping):
            raise TypeError("PromptConfig.tokens must be a mapping")
        return cls(
            template=str(payload.get("template", "{app.name}> ")),
            tokens=dict(tokens),
        )

    @classmethod
    def from_file(cls, path: str | Path) -> "PromptConfig":
        payload = json.loads(Path(path).read_text())
        if not isinstance(payload, Mapping):
            raise TypeError("Prompt config file must contain an object")
        return cls.from_mapping(payload)

    def with_tokens(self, tokens: Mapping[str, TokenValue | TokenFn]) -> "PromptConfig":
        merged = dict(self.tokens)
        merged.update(tokens)
        return PromptConfig(template=self.template, tokens=merged)


@dataclass(slots=True)
class LiveConfig:
    spinner: str = "dots"
    show_elapsed: bool = True
    success_symbol: str = "✓"
    error_symbol: str = "✗"
    status_final: str = "success"
    status_failed_final: str = "error"
    awaiting_final: str = "clear"
    awaiting_failed_final: str = "error"
    progress_transient: bool = False

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any] | None = None) -> "LiveConfig":
        payload = data or {}
        return cls(
            spinner=str(payload.get("spinner", "dots")),
            show_elapsed=bool(payload.get("show_elapsed", True)),
            success_symbol=str(payload.get("success_symbol", "✓")),
            error_symbol=str(payload.get("error_symbol", "✗")),
            status_final=str(payload.get("status_final", "success")),
            status_failed_final=str(payload.get("status_failed_final", "error")),
            awaiting_final=str(payload.get("awaiting_final", "clear")),
            awaiting_failed_final=str(payload.get("awaiting_failed_final", "error")),
            progress_transient=bool(payload.get("progress_transient", False)),
        )


@dataclass(slots=True)
class ShellConfig:
    prompt: PromptConfig = field(default_factory=PromptConfig)
    live: LiveConfig = field(default_factory=LiveConfig)
    history: bool = True
    mouse_support: bool = False
    history_path: str | None = None

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any] | None = None) -> "ShellConfig":
        payload = data or {}
        prompt = PromptConfig.from_mapping(payload.get("prompt"))
        live = LiveConfig.from_mapping(payload.get("live"))
        history_path = payload.get("history_path")
        return cls(
            prompt=prompt,
            live=live,
            history=bool(payload.get("history", True)),
            mouse_support=bool(payload.get("mouse_support", False)),
            history_path=str(history_path) if history_path is not None else None,
        )

    @classmethod
    def from_file(cls, path: str | Path) -> "ShellConfig":
        payload = json.loads(Path(path).read_text())
        if not isinstance(payload, Mapping):
            raise TypeError("Shell config file must contain an object")
        return cls.from_mapping(payload)

    def with_prompt(self, prompt: PromptConfig) -> "ShellConfig":
        return ShellConfig(
            prompt=prompt,
            live=self.live,
            history=self.history,
            mouse_support=self.mouse_support,
            history_path=self.history_path,
        )

    def with_prompt_tokens(self, tokens: Mapping[str, TokenValue | TokenFn]) -> "ShellConfig":
        return self.with_prompt(self.prompt.with_tokens(tokens))


@dataclass(slots=True)
class AppConfig:
    shell: ShellConfig = field(default_factory=ShellConfig)
    theme: "ArgonTheme | None" = None

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any] | None = None) -> "AppConfig":
        from .ui.theme import ArgonTheme

        payload = data or {}
        theme_data = payload.get("theme")
        theme = ArgonTheme.from_mapping(theme_data) if isinstance(theme_data, Mapping) else None
        shell = ShellConfig.from_mapping(payload.get("shell"))
        return cls(shell=shell, theme=theme)

    @classmethod
    def from_file(cls, path: str | Path) -> "AppConfig":
        payload = json.loads(Path(path).read_text())
        if not isinstance(payload, Mapping):
            raise TypeError("App config file must contain an object")
        return cls.from_mapping(payload)
