from __future__ import annotations

import enum
import inspect
from collections.abc import Sequence
from typing import Any, Literal, get_args, get_origin

from ..models import ArgumentInfo, CompletionItem, CompletionResult, CompletionSource, OptionInfo
from .errors import UsageError
from .partial import parse_partial

OptionDisplayPolicy = str


def _root_builtins(version: str | None) -> list[CompletionItem]:
    items = [CompletionItem(text="help", meta="Show help for commands and groups")]
    if version:
        items.append(CompletionItem(text="version", meta="Show application version"))
    return items


def _coerce_items(items: Sequence[str | CompletionItem]) -> list[CompletionItem]:
    out: list[CompletionItem] = []
    for item in items:
        if isinstance(item, CompletionItem):
            out.append(item)
        else:
            out.append(CompletionItem(text=item))
    return out


def _call_autocompletion(fn: Any, prefix: str) -> list[CompletionItem]:
    try:
        sig = inspect.signature(fn)
    except (TypeError, ValueError):
        return []
    params = list(sig.parameters.values())
    if not params:
        return _coerce_items(fn())
    if len(params) == 1:
        return _coerce_items(fn(prefix))
    return _coerce_items(fn(None, prefix))


def _inferred_completion_items(param) -> list[CompletionItem]:
    annotation = param.annotation
    if get_origin(annotation) is Literal:
        return _coerce_items([value for value in get_args(annotation) if isinstance(value, str)])
    if isinstance(annotation, type) and issubclass(annotation, enum.Enum):
        return _coerce_items(
            [member.value for member in annotation if isinstance(member.value, str)]
        )
    return []


def _completion_items(source: CompletionSource | None, param, prefix: str) -> list[CompletionItem]:
    if source is None:
        items = _inferred_completion_items(param)
    elif callable(source):
        items = _call_autocompletion(source, prefix)
    elif isinstance(source, str):
        items = _coerce_items((source,))
    else:
        items = _coerce_items(source)
    if not prefix:
        return items
    return [item for item in items if item.text.startswith(prefix)]


def _split_option_decls(decls: tuple[str, ...]) -> tuple[list[str], list[str]]:
    long_decls: list[str] = []
    short_decls: list[str] = []
    for decl in decls:
        if decl.startswith("--"):
            long_decls.append(decl)
        elif decl.startswith("-"):
            short_decls.append(decl)
    return long_decls, short_decls


def _selected_option_decls(decls: tuple[str, ...], policy: OptionDisplayPolicy) -> list[str]:
    # Completion policy is resolved in the backend so shell frontends stay thin.
    long_decls, short_decls = _split_option_decls(decls)
    if policy == "none":
        return []
    if policy == "all":
        return list(decls)
    if policy == "short":
        return short_decls if short_decls else long_decls
    return long_decls if long_decls else short_decls


def _active_argument_param(command, tokens: list[str]):
    arguments = [
        param for param in command.visible_params if isinstance(param.parameter_info, ArgumentInfo)
    ]
    option_by_decl = {
        decl: param
        for param in command.visible_params
        if isinstance(param.parameter_info, OptionInfo)
        for decl in param.parameter_info.param_decls
    }

    positionals = 0
    i = 0
    while i < len(tokens):
        token = tokens[i]
        if token == "--":
            return None
        if token.startswith("-") and token != "-":
            option_token = token.split("=", 1)[0] if token.startswith("--") else token
            option_param = option_by_decl.get(option_token)
            if option_param is None:
                i += 1
                continue
            has_inline_value = option_token != token
            if option_param.annotation is not bool and not has_inline_value:
                i += 2
                continue
            i += 1
            continue
        positionals += 1
        i += 1

    for param in arguments:
        if param.kind == inspect.Parameter.VAR_POSITIONAL:
            return param
        if positionals == 0:
            return param
        positionals -= 1
    return None


def _inline_option_value_param(command, current: str):
    if not current.startswith("--") or "=" not in current:
        return None
    option_token, value_prefix = current.split("=", 1)
    for param in command.visible_params:
        info = param.parameter_info
        if isinstance(info, OptionInfo) and option_token in info.param_decls:
            return param, value_prefix
    return None


def complete(
    root,
    line: str,
    cursor: int | None = None,
    *,
    app_version: str | None = None,
    option_display: OptionDisplayPolicy = "long",
) -> CompletionResult:
    try:
        partial = parse_partial(root, line, cursor)
    except UsageError:
        cur = len(line) if cursor is None else max(0, min(cursor, len(line)))
        return CompletionResult(items=[], replace_start=cur, replace_end=cur)
    resolution = partial.resolution
    prefix = partial.current
    items: list[CompletionItem] = []
    replace_start = partial.replace_start

    if resolution.command is None:
        group = resolution.groups[-1]
        names = [
            *sorted(name for name, child in group.groups.items() if not child.hidden),
            *sorted(name for name, child in group.commands.items() if not child.hidden),
        ]
        items = [
            CompletionItem(text=name) for name in names if not prefix or name.startswith(prefix)
        ]
        if group is root:
            items.extend(
                item
                for item in _root_builtins(app_version)
                if not prefix or item.text.startswith(prefix)
            )
    else:
        command = resolution.command
        tokens = list(resolution.remaining)
        inline_option = _inline_option_value_param(command, prefix)
        expecting_option_value = False
        active_option_param = None
        if prefix and tokens and partial.replace_start != partial.replace_end:
            tokens = tokens[:-1]
        if tokens:
            last = tokens[-1]
            for param in command.visible_params:
                info = param.parameter_info
                if isinstance(info, OptionInfo) and last in info.param_decls:
                    if param.annotation is not bool:
                        expecting_option_value = True
                        active_option_param = param
                    break
        if inline_option is not None:
            inline_option_param, value_prefix = inline_option
            info = inline_option_param.parameter_info
            replace_start = partial.replace_end - len(value_prefix)
            items = _completion_items(info.autocompletion, inline_option_param, value_prefix)
        elif expecting_option_value and active_option_param is not None:
            info = active_option_param.parameter_info
            items = _completion_items(info.autocompletion, active_option_param, prefix)
        elif prefix.startswith("-"):
            for param in command.visible_params:
                info = param.parameter_info
                if not isinstance(info, OptionInfo):
                    continue
                for decl in _selected_option_decls(info.param_decls, option_display):
                    if prefix and not decl.startswith(prefix):
                        continue
                    items.append(CompletionItem(text=decl, meta=info.help))
        else:
            param = _active_argument_param(command, tokens)
            if param is not None:
                info = param.parameter_info
                items.extend(_completion_items(info.autocompletion, param, prefix))

    return CompletionResult(
        items=items, replace_start=replace_start, replace_end=partial.replace_end
    )
