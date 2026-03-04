from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from inspect import Parameter
from typing import Any


class _RequiredSentinel:
    def __repr__(self) -> str:
        return "Required"

    def __copy__(self) -> "_RequiredSentinel":
        return self

    def __deepcopy__(self, memo: dict[int, object]) -> "_RequiredSentinel":
        return self


Required = _RequiredSentinel()


@dataclass(slots=True)
class ParameterInfo:
    default: Any = Required
    param_decls: tuple[str, ...] = ()
    help: str | None = None
    metavar: str | None = None
    envvar: str | list[str] | None = None
    parser: Callable[[str], Any] | None = None
    autocompletion: Callable[..., Sequence[str | "CompletionItem"]] | None = None
    default_factory: Callable[[], Any] | None = None
    hidden: bool = False
    required: bool = False
    show_default: bool | str = True
    rich_help_panel: str | None = None

    def resolved_default(self) -> Any:
        if self.required:
            return Required
        if self.default_factory is not None:
            return self.default_factory()
        if self.default is Required:
            return Required
        return self.default


@dataclass(slots=True)
class OptionInfo(ParameterInfo):
    pass


@dataclass(slots=True)
class ArgumentInfo(ParameterInfo):
    pass


@dataclass(slots=True)
class ParamMeta:
    name: str
    annotation: Any
    default: Any
    kind: Parameter.kind
    parameter_info: ParameterInfo
    is_context: bool = False

    @property
    def required(self) -> bool:
        return self.parameter_info.resolved_default() is Required


@dataclass(slots=True)
class CommandSpec:
    name: str
    callback: Callable[..., Any]
    help: str | None = None
    hidden: bool = False
    deprecated: bool = False
    aliases: tuple[str, ...] = ()
    params: list[ParamMeta] = field(default_factory=list)
    parent: GroupSpec | None = None

    @property
    def path(self) -> tuple[str, ...]:
        parts: list[str] = []
        parent = self.parent
        while parent is not None and parent.name:
            parts.append(parent.name)
            parent = parent.parent
        return tuple(reversed(parts)) + (self.name,)

    @property
    def visible_params(self) -> list[ParamMeta]:
        return [param for param in self.params if not param.is_context]


@dataclass(slots=True)
class GroupSpec:
    name: str
    help: str | None = None
    hidden: bool = False
    aliases: tuple[str, ...] = ()
    parent: GroupSpec | None = None
    commands: dict[str, CommandSpec] = field(default_factory=dict)
    groups: dict[str, GroupSpec] = field(default_factory=dict)
    callback: Callable[..., Any] | None = None
    callback_params: list[ParamMeta] = field(default_factory=list)
    invoke_without_command: bool = False
    no_args_is_help: bool = False

    @property
    def path(self) -> tuple[str, ...]:
        parts: list[str] = []
        cur: GroupSpec | None = self
        while cur is not None and cur.name:
            parts.append(cur.name)
            cur = cur.parent
        return tuple(reversed(parts))


@dataclass(frozen=True, slots=True)
class Invocation:
    path: tuple[str, ...]
    argv: tuple[str, ...]
    args: tuple[object, ...]
    options: dict[str, object]
    passthrough: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class CompletionItem:
    text: str
    display: str | None = None
    meta: str | None = None


@dataclass(frozen=True, slots=True)
class CompletionResult:
    items: list[CompletionItem]
    replace_start: int
    replace_end: int


@dataclass(frozen=True, slots=True)
class StyledSpan:
    start: int
    end: int
    styles: tuple[str, ...]
