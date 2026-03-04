from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from rich.theme import Theme


_REF_RE = re.compile(r"\{([a-zA-Z0-9_.-]+)\}")

SEMANTIC_STYLE_GROUPS: dict[str, tuple[str, ...]] = {
    "foundation": (
        "argon.surface.base",
        "argon.surface.panel",
        "argon.surface.muted",
        "argon.selection.active",
        "argon.selection.inactive",
        "argon.chrome.border",
    ),
    "text": (
        "argon.text.primary",
        "argon.text.muted",
        "argon.text.title",
        "argon.text.heading",
    ),
    "feedback": (
        "argon.feedback.success",
        "argon.feedback.warning",
        "argon.feedback.error",
    ),
    "shell": (
        "argon.shell.command",
        "argon.shell.option",
        "argon.shell.value",
        "argon.shell.string",
        "argon.shell.number",
        "argon.shell.error",
    ),
    "prompt": (
        "argon.prompt.brand",
        "argon.prompt.context",
        "argon.prompt.meta",
        "argon.prompt.symbol",
    ),
    "live": (
        "argon.live.spinner",
        "argon.live.message",
        "argon.live.elapsed",
        "argon.progress.description",
        "argon.progress.bar",
        "argon.progress.complete",
        "argon.progress.remaining",
        "argon.progress.percentage",
    ),
    "ptk": (
        "argon.ptk.menu",
        "argon.ptk.menu.current",
        "argon.ptk.menu.meta",
        "argon.ptk.menu.meta.current",
        "argon.ptk.scrollbar",
        "argon.ptk.scrollbar.dim",
    ),
}

SEMANTIC_STYLE_KEYS: tuple[str, ...] = tuple(
    key for keys in SEMANTIC_STYLE_GROUPS.values() for key in keys
)


class ThemeResolutionError(RuntimeError):
    """Base error for semantic theme resolution failures."""

    pass


class ThemeMissingKeysError(ThemeResolutionError):
    def __init__(self, missing: list[str]):
        super().__init__("Theme is missing required semantic styles: " + ", ".join(missing))
        self.missing = missing


class ThemeCycleError(ThemeResolutionError):
    def __init__(self, cycle: list[str]):
        super().__init__("Theme style cycle detected: " + " -> ".join(cycle))
        self.cycle = cycle


class ThemeMissingReferenceError(ThemeResolutionError):
    def __init__(self, *, key: str, missing: str):
        super().__init__(f"Theme style '{key}' references unknown style '{missing}'")
        self.key = key
        self.missing = missing


@dataclass(frozen=True, slots=True)
class ThemeLayer:
    """Named map of semantic styles.

    @param name Layer name used for diagnostics/composition.
    @param styles Style map keyed by semantic token name.
    """

    name: str
    styles: Mapping[str, str]


@dataclass(frozen=True, slots=True)
class ArgonTheme:
    """Composable semantic theme model.

    @param base Required base theme layer.
    @param overrides Optional override layers applied in-order.
    """

    base: ThemeLayer
    overrides: tuple[ThemeLayer, ...] = ()

    @classmethod
    def from_mapping(cls, data: Mapping[str, object] | None = None) -> "ArgonTheme":
        """Build a theme from a mapping payload.

        @param data Mapping payload from Python/JSON sources.
        @returns Parsed theme instance.
        @raises TypeError If payload shape is invalid.
        """

        payload = data or {}
        base_data = payload.get("base")
        inherited_defaults = default_styles()
        if isinstance(base_data, Mapping):
            base_name = str(base_data.get("name", "loaded"))
            base_styles = base_data.get("styles", {})
            if not isinstance(base_styles, Mapping):
                raise TypeError("Theme base styles must be a mapping")
            merged_base_styles = dict(inherited_defaults)
            merged_base_styles.update({str(key): str(value) for key, value in base_styles.items()})
        else:
            base_name = str(payload.get("name", "loaded"))
            base_styles = payload.get("styles", default_styles())
            if not isinstance(base_styles, Mapping):
                raise TypeError("Theme styles must be a mapping")
            merged_base_styles = dict(inherited_defaults)
            merged_base_styles.update({str(key): str(value) for key, value in base_styles.items()})

        overrides: list[ThemeLayer] = []
        raw_overrides = payload.get("overrides", ())
        if not isinstance(raw_overrides, (list, tuple)):
            raise TypeError("Theme overrides must be a list")
        for index, item in enumerate(raw_overrides):
            if not isinstance(item, Mapping):
                raise TypeError("Theme override entries must be objects")
            styles = item.get("styles", {})
            if not isinstance(styles, Mapping):
                raise TypeError("Theme override styles must be a mapping")
            overrides.append(
                ThemeLayer(
                    name=str(item.get("name", f"override-{index}")),
                    styles={str(key): str(value) for key, value in styles.items()},
                )
            )

        return cls(
            base=ThemeLayer(
                name=base_name,
                styles=merged_base_styles,
            ),
            overrides=tuple(overrides),
        )

    @classmethod
    def from_file(cls, path: str | Path) -> "ArgonTheme":
        """Load a theme from a JSON file.

        @param path Path to a JSON object payload.
        @returns Parsed theme instance.
        @raises TypeError If the file does not contain a JSON object.
        """

        payload = json.loads(Path(path).read_text())
        if not isinstance(payload, Mapping):
            raise TypeError("Theme file must contain an object")
        return cls.from_mapping(payload)

    def with_overrides(self, name: str, styles: Mapping[str, str]) -> "ArgonTheme":
        """Return a copy with an appended override layer.

        @param name Override layer name.
        @param styles Semantic style updates.
        @returns New theme instance with appended layer.
        """

        return ArgonTheme(
            base=self.base,
            overrides=self.overrides + (ThemeLayer(name=name, styles=styles),),
        )

    def merged_styles(self) -> dict[str, str]:
        """Merge base and override layers without resolving references.

        @returns Flat style mapping before reference expansion.
        """

        merged = dict(self.base.styles)
        for layer in self.overrides:
            merged.update(layer.styles)
        return merged

    def resolved_styles(self) -> dict[str, str]:
        """Resolve merged styles and validate semantic completeness.

        @returns Fully resolved style mapping.
        @raises ThemeResolutionError On missing keys, cycles, or bad references.
        """

        merged = self.merged_styles()
        validate_semantic_styles(merged)
        return resolve_style_references(merged)


def semantic_style_groups() -> dict[str, tuple[str, ...]]:
    """Return semantic style groups for documentation/tooling.

    @returns Mapping of style group names to semantic style keys.
    """

    return dict(SEMANTIC_STYLE_GROUPS)


def validate_semantic_styles(styles: Mapping[str, str]) -> None:
    """Validate that all required semantic style keys are present.

    @param styles Candidate style map.
    @raises ThemeMissingKeysError If required keys are missing.
    """

    missing = [key for key in SEMANTIC_STYLE_KEYS if key not in styles]
    if missing:
        raise ThemeMissingKeysError(missing)


def resolve_style_references(styles: Mapping[str, str]) -> dict[str, str]:
    """Resolve `{style.reference}` indirections in a style map.

    @param styles Style mapping with optional symbolic references.
    @returns Resolved style mapping.
    @raises ThemeResolutionError On missing keys, cycles, or bad references.
    """

    resolved: dict[str, str] = {}
    visiting: list[str] = []

    def resolve_key(key: str) -> str:
        if key in resolved:
            return resolved[key]
        if key in visiting:
            index = visiting.index(key)
            raise ThemeCycleError(visiting[index:] + [key])
        if key not in styles:
            raise ThemeMissingReferenceError(key=key, missing=key)

        visiting.append(key)
        raw = styles[key]

        def repl(match: re.Match[str]) -> str:
            ref = match.group(1)
            if ref not in styles:
                raise ThemeMissingReferenceError(key=key, missing=ref)
            return resolve_key(ref)

        value = raw
        while True:
            expanded = _REF_RE.sub(repl, value)
            if expanded == value:
                break
            value = expanded

        visiting.pop()
        resolved[key] = value
        return value

    for key in styles:
        resolve_key(key)
    return resolved


def default_styles() -> dict[str, str]:
    """Return Argon's default semantic style mapping.

    @returns Default style map including compatibility aliases.
    """

    return {
        "argon.surface.base": "white on black",
        "argon.surface.panel": "white on black",
        "argon.surface.muted": "bright_black on black",
        "argon.selection.active": "bold black on bright_cyan",
        "argon.selection.inactive": "black on bright_black",
        "argon.chrome.border": "dim",
        "argon.text.primary": "none",
        "argon.text.muted": "dim",
        "argon.text.title": "bold cyan",
        "argon.text.heading": "bold",
        "argon.feedback.success": "bold green",
        "argon.feedback.warning": "bold yellow",
        "argon.feedback.error": "bold red",
        "argon.shell.command": "bold cyan",
        "argon.shell.option": "cyan",
        "argon.shell.value": "{argon.text.primary}",
        "argon.shell.string": "green",
        "argon.shell.number": "magenta",
        "argon.shell.error": "{argon.feedback.error}",
        "argon.prompt.brand": "{argon.shell.command}",
        "argon.prompt.context": "{argon.text.muted}",
        "argon.prompt.meta": "{argon.text.muted}",
        "argon.prompt.symbol": "{argon.text.primary}",
        "argon.live.spinner": "{argon.shell.option}",
        "argon.live.message": "{argon.text.primary}",
        "argon.live.elapsed": "{argon.text.muted}",
        "argon.progress.description": "{argon.text.primary}",
        "argon.progress.bar": "{argon.shell.option}",
        "argon.progress.complete": "{argon.feedback.success}",
        "argon.progress.remaining": "{argon.text.muted}",
        "argon.progress.percentage": "{argon.text.muted}",
        "argon.ptk.menu": "{argon.surface.base}",
        "argon.ptk.menu.current": "{argon.selection.active}",
        "argon.ptk.menu.meta": "{argon.surface.muted}",
        "argon.ptk.menu.meta.current": "{argon.selection.inactive}",
        "argon.ptk.scrollbar": "bright_black on black",
        "argon.ptk.scrollbar.dim": "black on black",
        "argon.title": "{argon.text.title}",
        "argon.heading": "{argon.text.heading}",
        "argon.command": "{argon.shell.command}",
        "argon.option": "{argon.shell.option}",
        "argon.value": "{argon.shell.value}",
        "argon.string": "{argon.shell.string}",
        "argon.number": "{argon.shell.number}",
        "argon.error": "{argon.feedback.error}",
        "argon.warning": "{argon.feedback.warning}",
        "argon.success": "{argon.feedback.success}",
        "argon.dim": "{argon.text.muted}",
        "argon.border": "{argon.chrome.border}",
        "argon.prompt": "{argon.prompt.brand}",
        "argon.prompt.dim": "{argon.prompt.context}",
        "argon.prompt.time": "{argon.prompt.meta}",
        "argon.surface": "{argon.surface.base}",
        "argon.surface.dim": "{argon.surface.muted}",
        "argon.selection": "{argon.selection.active}",
        "argon.selection.dim": "{argon.selection.inactive}",
        "argon.scrollbar": "{argon.ptk.scrollbar}",
        "argon.scrollbar.dim": "{argon.ptk.scrollbar.dim}",
    }


def default_theme() -> ArgonTheme:
    """Create the default Argon semantic theme.

    @returns Default `ArgonTheme` instance.
    """

    return ArgonTheme(base=ThemeLayer(name="default", styles=default_styles()))


def build_theme(theme: ArgonTheme | None = None) -> Theme:
    """Build a Rich `Theme` from an Argon semantic theme.

    @param theme Optional Argon theme. Uses defaults when omitted.
    @returns Rich theme object.
    """

    resolved = (theme or default_theme()).resolved_styles()
    return Theme(resolved)
