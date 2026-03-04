from __future__ import annotations

import asyncio
import inspect
from typing import Any

from ..introspect import get_params_from_function
from ..models import CommandSpec, ParamMeta
from .context import Context
from .errors import BadParameter


def finalize_result(result: Any) -> Any:
    if not inspect.isawaitable(result):
        return result
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(result)
    return result


def _build_call(
    params: list[ParamMeta],
    ctx: Context,
    values: dict[str, object],
) -> tuple[list[object], dict[str, object]]:
    args: list[object] = []
    kwargs: dict[str, object] = {}
    for param in params:
        if param.is_context:
            value: object = ctx
        else:
            value = values[param.name]
        if param.kind in (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD):
            args.append(value)
        elif param.kind == inspect.Parameter.VAR_POSITIONAL:
            args.extend(value if isinstance(value, tuple) else (value,))
        else:
            kwargs[param.name] = value
    return args, kwargs


def invoke_command(command: CommandSpec, ctx: Context, values: dict[str, object]) -> Any:
    args, kwargs = _build_call(command.params, ctx, values)
    return finalize_result(command.callback(*args, **kwargs))


def invoke_callable(fn: Any, ctx: Context, *, args: tuple[Any, ...], kwargs: dict[str, Any]) -> Any:
    params = get_params_from_function(fn)
    call_args: list[Any] = list(args)
    call_kwargs = dict(kwargs)
    for index, param in enumerate(params):
        if not param.is_context:
            continue
        if index <= len(call_args):
            call_args.insert(index, ctx)
        else:
            call_kwargs[param.name] = ctx
        break
    return fn(*call_args, **call_kwargs)


def forward_callable(fn: Any, ctx: Context, *, overrides: dict[str, Any]) -> Any:
    params = get_params_from_function(fn)
    call_args: list[Any] = []
    call_kwargs: dict[str, Any] = {}
    for param in params:
        if param.is_context:
            value = ctx
        elif param.name in overrides:
            value = overrides[param.name]
        elif param.name in ctx.params:
            value = ctx.params[param.name]
        else:
            raise BadParameter(f"Cannot forward missing parameter: {param.name}")

        if param.kind in (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD):
            call_args.append(value)
        elif param.kind == inspect.Parameter.VAR_POSITIONAL:
            call_args.extend(value if isinstance(value, tuple) else (value,))
        else:
            call_kwargs[param.name] = value
    return fn(*call_args, **call_kwargs)
