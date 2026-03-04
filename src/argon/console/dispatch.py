from __future__ import annotations

import asyncio
import inspect
from collections.abc import Coroutine
from typing import Any, cast

from ..introspect import get_params_from_function
from ..models import CommandSpec, ParamMeta
from .context import Context
from .errors import BadParameter, UsageError


def finalize_result_sync(result: Any) -> Any:
    # Sync execution is deterministic: either concrete value or explicit guidance
    # to use async entrypoints when already running inside an event loop.
    if not inspect.isawaitable(result):
        return result
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(cast(Coroutine[Any, Any, Any], result))
    if inspect.iscoroutine(result):
        result.close()
    raise UsageError(
        "Cannot execute async command from sync API inside a running event loop. "
        "Use App.run_argv_async()/run_line_async() or Console.execute_argv_async()/execute_line_async()."
    )


async def finalize_result_async(result: Any) -> Any:
    if inspect.isawaitable(result):
        return await result
    return result


def finalize_result(result: Any) -> Any:
    """Backward-compatible alias for sync finalization."""

    return finalize_result_sync(result)


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
    return finalize_result_sync(command.callback(*args, **kwargs))


async def invoke_command_async(command: CommandSpec, ctx: Context, values: dict[str, object]) -> Any:
    args, kwargs = _build_call(command.params, ctx, values)
    return await finalize_result_async(command.callback(*args, **kwargs))


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
        value: Any
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
