from __future__ import annotations

import enum
import inspect
import os
import shlex
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, Union, get_args, get_origin

from ..models import ArgumentInfo, CommandSpec, Invocation, OptionInfo, ParamMeta, Required
from .errors import BadParameter, UsageError


@dataclass(slots=True)
class ParseResult:
    invocation: Invocation
    values: dict[str, object]


def split_passthrough(tokens: list[str]) -> tuple[list[str], list[str]]:
    if "--" not in tokens:
        return list(tokens), []
    idx = tokens.index("--")
    return tokens[:idx], tokens[idx + 1 :]


def split_line(line: str) -> list[str]:
    try:
        return shlex.split(line)
    except ValueError as exc:  # pragma: no cover - exercised by runtime tests
        raise UsageError(str(exc)) from exc


def _is_flag(param: ParamMeta) -> bool:
    return isinstance(param.parameter_info, OptionInfo) and param.annotation is bool


def _option_names(param: ParamMeta) -> tuple[str, ...]:
    info = param.parameter_info
    if not isinstance(info, OptionInfo):
        return ()
    if info.param_decls:
        return info.param_decls
    return (f"--{param.name.replace('_', '-')}",)


def _convert_scalar(value: str, param: ParamMeta) -> object:
    info = param.parameter_info
    if info.parser is not None:
        try:
            return info.parser(value)
        except Exception as exc:  # noqa: BLE001
            raise BadParameter(f"Invalid value for {param.name!r}: {exc}") from exc

    annotation = param.annotation
    if annotation in (inspect._empty, Any, str):  # noqa: SLF001
        return value
    origin = get_origin(annotation)
    if origin is Literal:
        choices = get_args(annotation)
        if value in choices:
            return value
        raise BadParameter(f"Invalid choice for {param.name!r}: {value!r}")
    if origin in (Union, getattr(__import__("types"), "UnionType", Union)):
        for candidate in get_args(annotation):
            if candidate is type(None):
                if value.lower() in {"none", "null"}:
                    return None
                continue
            try:
                fake = ParamMeta(
                    name=param.name,
                    annotation=candidate,
                    default=Required,
                    kind=param.kind,
                    parameter_info=param.parameter_info,
                )
                return _convert_scalar(value, fake)
            except BadParameter:
                continue
        raise BadParameter(f"Invalid value for {param.name!r}: {value!r}")
    if annotation is bool:
        lowered = value.lower()
        if lowered in {"1", "true", "yes", "on"}:
            return True
        if lowered in {"0", "false", "no", "off"}:
            return False
        raise BadParameter(f"Invalid boolean value for {param.name!r}: {value!r}")
    if annotation is int:
        try:
            return int(value)
        except ValueError as exc:
            raise BadParameter(f"Invalid integer value for {param.name!r}: {value!r}") from exc
    if annotation is float:
        try:
            return float(value)
        except ValueError as exc:
            raise BadParameter(f"Invalid number value for {param.name!r}: {value!r}") from exc
    if annotation is Path:
        return Path(value)
    if isinstance(annotation, type) and issubclass(annotation, enum.Enum):
        try:
            return annotation(value)
        except ValueError as exc:
            raise BadParameter(f"Invalid choice for {param.name!r}: {value!r}") from exc
    try:
        return annotation(value)
    except Exception:  # noqa: BLE001
        return value


def _convert_option_values(values: list[str], param: ParamMeta) -> object:
    origin = get_origin(param.annotation)
    if origin in (list, tuple, set):
        item_type = get_args(param.annotation)[0] if get_args(param.annotation) else str
        fake = ParamMeta(
            name=param.name,
            annotation=item_type,
            default=Required,
            kind=param.kind,
            parameter_info=param.parameter_info,
        )
        converted = [_convert_scalar(value, fake) for value in values]
        if origin is tuple:
            return tuple(converted)
        if origin is set:
            return set(converted)
        return converted
    return _convert_scalar(values[-1], param)


def _resolve_default(param: ParamMeta) -> object:
    envvar = param.parameter_info.envvar
    if envvar:
        names = [envvar] if isinstance(envvar, str) else list(envvar)
        for name in names:
            if name in os.environ:
                return _convert_scalar(os.environ[name], param)
    default = param.parameter_info.resolved_default()
    if default is Required:
        return Required
    return default


def parse_tokens(command: CommandSpec, tokens: list[str]) -> ParseResult:
    option_params = [param for param in command.visible_params if isinstance(param.parameter_info, OptionInfo)]
    argument_params = [param for param in command.visible_params if isinstance(param.parameter_info, ArgumentInfo)]
    option_by_name = {
        name: param
        for param in option_params
        for name in _option_names(param)
    }

    argv, passthrough = split_passthrough(tokens)
    option_values: dict[str, list[str]] = {}
    positionals: list[str] = []

    i = 0
    while i < len(argv):
        token = argv[i]
        if token.startswith("-") and token != "-":
            option_token = token
            inline_value: str | None = None
            if token.startswith("--") and "=" in token:
                option_token, inline_value = token.split("=", 1)
            param = option_by_name.get(option_token)
            if param is None:
                raise UsageError(f"Unknown option: {option_token}")
            if _is_flag(param):
                option_values.setdefault(param.name, []).append("true")
                i += 1
                continue
            if inline_value is not None:
                option_values.setdefault(param.name, []).append(inline_value)
                i += 1
                continue
            if i + 1 >= len(argv):
                raise UsageError(f"Missing option value: {option_token}")
            option_values.setdefault(param.name, []).append(argv[i + 1])
            i += 2
            continue
        positionals.append(token)
        i += 1

    values: dict[str, object] = {}
    for param in option_params:
        if param.name in option_values:
            values[param.name] = _convert_option_values(option_values[param.name], param)
            continue
        default = _resolve_default(param)
        if default is Required:
            raise UsageError(f"Missing option: {_option_names(param)[0]}")
        values[param.name] = default

    positional_index = 0
    bound_args: list[object] = []
    for param in argument_params:
        if param.kind == inspect.Parameter.VAR_POSITIONAL:
            remaining = positionals[positional_index:]
            fake_values = [_convert_scalar(value, param) for value in remaining]
            values[param.name] = tuple(fake_values)
            bound_args.extend(fake_values)
            positional_index = len(positionals)
            continue
        if positional_index < len(positionals):
            converted = _convert_scalar(positionals[positional_index], param)
            values[param.name] = converted
            bound_args.append(converted)
            positional_index += 1
            continue
        default = _resolve_default(param)
        if default is Required:
            raise UsageError(f"Missing argument: {param.name}")
        values[param.name] = default
        bound_args.append(default)

    if positional_index < len(positionals):
        raise UsageError(f"Unexpected extra arguments: {' '.join(positionals[positional_index:])}")

    return ParseResult(
        invocation=Invocation(
            path=command.path,
            argv=tuple(tokens),
            args=tuple(bound_args),
            options={name: value for name, value in values.items() if name in {param.name for param in option_params}},
            passthrough=tuple(passthrough),
        ),
        values=values,
    )
