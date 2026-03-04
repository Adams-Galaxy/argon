from __future__ import annotations

import inspect
from collections.abc import Sequence
from typing import Any

from ..models import ArgumentInfo, CompletionItem, CompletionResult, OptionInfo
from .partial import parse_partial


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


def complete(root, line: str, cursor: int | None = None, *, app_version: str | None = None) -> CompletionResult:
    partial = parse_partial(root, line, cursor)
    resolution = partial.resolution
    prefix = partial.current
    items: list[CompletionItem] = []

    if resolution.command is None:
        group = resolution.groups[-1]
        names = [
            *sorted(name for name, child in group.groups.items() if not child.hidden),
            *sorted(name for name, child in group.commands.items() if not child.hidden),
        ]
        items = [CompletionItem(text=name) for name in names if not prefix or name.startswith(prefix)]
        if group is root:
            items.extend(item for item in _root_builtins(app_version) if not prefix or item.text.startswith(prefix))
    else:
        command = resolution.command
        tokens = list(resolution.remaining)
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
        if expecting_option_value and active_option_param is not None:
            info = active_option_param.parameter_info
            if info.autocompletion is not None:
                items = _call_autocompletion(info.autocompletion, prefix)
        elif prefix.startswith("-"):
            for param in command.visible_params:
                info = param.parameter_info
                if not isinstance(info, OptionInfo):
                    continue
                for decl in info.param_decls:
                    if prefix and not decl.startswith(prefix):
                        continue
                    items.append(CompletionItem(text=decl, meta=info.help))
        else:
            for param in command.visible_params:
                info = param.parameter_info
                if not isinstance(info, ArgumentInfo) or info.autocompletion is None:
                    continue
                items.extend(_call_autocompletion(info.autocompletion, prefix))

    return CompletionResult(items=items, replace_start=partial.replace_start, replace_end=partial.replace_end)
