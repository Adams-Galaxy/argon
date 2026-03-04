from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .ui.theme import ArgonTheme
from .ui.tokens import TokenFn, TokenValue


class PromptConfig(BaseModel):
    """Prompt rendering configuration.

    @param template Prompt template string with token placeholders.
    @param tokens Mapping of prompt-local token names to static values or callbacks.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True, extra="forbid")

    template: str = "{app.name}> "
    tokens: dict[str, TokenValue | TokenFn] = Field(default_factory=dict)

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any] | None = None) -> "PromptConfig":
        """Construct a prompt config from a mapping.

        @param data Mapping payload, usually decoded JSON.
        @returns Parsed prompt config.
        @raises TypeError If the payload or tokens type is invalid.
        """

        payload = data or {}
        if not isinstance(payload, Mapping):
            raise TypeError("Prompt config payload must be a mapping")
        tokens = payload.get("tokens", {})
        if not isinstance(tokens, Mapping):
            raise TypeError("PromptConfig.tokens must be a mapping")
        return cls.model_validate(
            {
                **dict(payload),
                "tokens": dict(tokens),
            }
        )

    @classmethod
    def from_file(cls, path: str | Path) -> "PromptConfig":
        """Load prompt config from a JSON file.

        @param path Path to a JSON object payload.
        @returns Parsed prompt config.
        @raises TypeError If the file does not contain a JSON object.
        """

        payload = json.loads(Path(path).read_text())
        if not isinstance(payload, Mapping):
            raise TypeError("Prompt config file must contain an object")
        return cls.from_mapping(payload)

    def with_tokens(self, tokens: Mapping[str, TokenValue | TokenFn]) -> "PromptConfig":
        """Return a copy with merged prompt tokens.

        @param tokens Additional prompt token bindings.
        @returns New prompt config with merged token map.
        """

        merged = dict(self.tokens)
        merged.update(tokens)
        return self.model_copy(update={"tokens": merged})


LiveFinishPolicy = Literal["success", "error", "clear", "leave"]
OptionDisplayPolicy = Literal["long", "short", "all", "none"]


class LiveConfig(BaseModel):
    """Live display defaults for spinner/progress behavior.

    @param spinner Rich spinner preset name.
    @param show_elapsed Whether elapsed time should be shown for status displays.
    @param success_symbol Symbol used for successful finalized live displays.
    @param error_symbol Symbol used for failed finalized live displays.
    @param status_final Default status finalization policy.
    @param status_failed_final Default status failure finalization policy.
    @param awaiting_final Default awaiting success finalization policy.
    @param awaiting_failed_final Default awaiting failure finalization policy.
    @param progress_transient Whether progress displays should be transient.
    @param progress_final Default progress success finalization policy.
    @param progress_failed_final Default progress failure finalization policy.
    @param progress_final_message Optional default progress completion message.
    @param progress_failed_final_message Optional default progress failure message.
    """

    model_config = ConfigDict(extra="forbid")

    spinner: str = "dots"
    show_elapsed: bool = True
    success_symbol: str = "✓"
    error_symbol: str = "✗"
    status_final: LiveFinishPolicy = "success"
    status_failed_final: LiveFinishPolicy = "error"
    awaiting_final: LiveFinishPolicy = "clear"
    awaiting_failed_final: LiveFinishPolicy = "error"
    progress_transient: bool = False
    progress_final: LiveFinishPolicy = "leave"
    progress_failed_final: LiveFinishPolicy = "error"
    progress_final_message: str | None = None
    progress_failed_final_message: str | None = None

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any] | None = None) -> "LiveConfig":
        """Construct a live config from a mapping.

        @param data Mapping payload, usually decoded JSON.
        @returns Parsed live config.
        """

        payload = data or {}
        if not isinstance(payload, Mapping):
            raise TypeError("Live config payload must be a mapping")
        return cls.model_validate(dict(payload))


class CompletionConfig(BaseModel):
    """Completion UX behavior controls.

    @param option_display Policy for showing short/long option declarations.
    @param show_help_tooltips Whether PTK completion metadata/help should render.
    """

    model_config = ConfigDict(extra="forbid")

    option_display: OptionDisplayPolicy = "long"
    show_help_tooltips: bool = False

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any] | None = None) -> "CompletionConfig":
        """Construct completion config from a mapping.

        @param data Mapping payload, usually decoded JSON.
        @returns Parsed completion config.
        """

        payload = data or {}
        if not isinstance(payload, Mapping):
            raise TypeError("Completion config payload must be a mapping")
        return cls.model_validate(dict(payload))


class ShellConfig(BaseModel):
    """Shell frontend configuration.

    @param prompt Prompt template and prompt token bindings.
    @param live Live output defaults for status and progress.
    @param completion Completion menu behavior controls.
    @param history Whether prompt history is enabled.
    @param mouse_support Whether mouse support is enabled in PTK.
    @param history_path Optional path for persistent shell history.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True, extra="forbid")

    prompt: PromptConfig = Field(default_factory=PromptConfig)
    live: LiveConfig = Field(default_factory=LiveConfig)
    completion: CompletionConfig = Field(default_factory=CompletionConfig)
    history: bool = True
    mouse_support: bool = False
    history_path: str | None = None

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any] | None = None) -> "ShellConfig":
        """Construct shell config from a mapping.

        @param data Mapping payload, usually decoded JSON.
        @returns Parsed shell config.
        @raises TypeError If the payload is not a mapping.
        """

        payload = data or {}
        if not isinstance(payload, Mapping):
            raise TypeError("Shell config payload must be a mapping")
        return cls.model_validate(dict(payload))

    @classmethod
    def from_file(cls, path: str | Path) -> "ShellConfig":
        """Load shell config from a JSON file.

        @param path Path to a JSON object payload.
        @returns Parsed shell config.
        @raises TypeError If the file does not contain a JSON object.
        """

        payload = json.loads(Path(path).read_text())
        if not isinstance(payload, Mapping):
            raise TypeError("Shell config file must contain an object")
        return cls.from_mapping(payload)

    def with_prompt(self, prompt: PromptConfig) -> "ShellConfig":
        """Return a copy with a replaced prompt config.

        @param prompt Prompt configuration to apply.
        @returns New shell config with updated prompt.
        """

        return self.model_copy(update={"prompt": prompt})

    def with_prompt_tokens(self, tokens: Mapping[str, TokenValue | TokenFn]) -> "ShellConfig":
        """Return a copy with merged prompt tokens.

        @param tokens Additional prompt token bindings.
        @returns New shell config with updated prompt tokens.
        """

        return self.with_prompt(self.prompt.with_tokens(tokens))


class AppConfig(BaseModel):
    """Top-level app configuration payload.

    @param schema_version Config schema version. Argon v1 requires value `1`.
    @param shell Shell frontend configuration.
    @param theme Optional semantic theme definition.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True, extra="forbid")

    schema_version: int = 1
    shell: ShellConfig = Field(default_factory=ShellConfig)
    theme: ArgonTheme | None = None

    @field_validator("schema_version")
    @classmethod
    def _validate_schema_version(cls, value: int) -> int:
        if value != 1:
            raise ValueError(
                f"Unsupported config schema_version={value}. Argon v1 supports schema_version=1."
            )
        return value

    @field_validator("theme", mode="before")
    @classmethod
    def _coerce_theme(cls, value: object) -> object:
        if value is None or isinstance(value, ArgonTheme):
            return value
        if isinstance(value, Mapping):
            return ArgonTheme.from_mapping(value)
        raise TypeError("AppConfig.theme must be a mapping, ArgonTheme, or null")

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any] | None = None) -> "AppConfig":
        """Construct app config from a mapping.

        @param data Mapping payload, usually decoded JSON.
        @returns Parsed app config.
        @raises TypeError If the payload is not a mapping.
        """

        payload = data or {}
        if not isinstance(payload, Mapping):
            raise TypeError("App config payload must be a mapping")
        return cls.model_validate(dict(payload))

    @classmethod
    def from_file(cls, path: str | Path) -> "AppConfig":
        """Load app config from a JSON file.

        @param path Path to a JSON object payload.
        @returns Parsed app config.
        @raises TypeError If the file does not contain a JSON object.
        """

        payload = json.loads(Path(path).read_text())
        if not isinstance(payload, Mapping):
            raise TypeError("App config file must contain an object")
        return cls.from_mapping(payload)
