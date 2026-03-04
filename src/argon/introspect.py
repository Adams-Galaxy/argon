from __future__ import annotations

import inspect
from copy import deepcopy
from typing import Annotated, Any, get_args, get_origin, get_type_hints

from .models import ArgumentInfo, OptionInfo, ParamMeta, ParameterInfo, Required


class IntrospectionError(ValueError):
    """Raised when a function cannot be converted into Argon metadata."""


def _split_annotation(annotation: Any) -> tuple[Any, list[ParameterInfo]]:
    if get_origin(annotation) is not Annotated:
        return annotation, []
    base_annotation, *meta = get_args(annotation)
    infos = [item for item in meta if isinstance(item, ParameterInfo)]
    return base_annotation, infos


def _looks_like_context(name: str, annotation: Any) -> bool:
    if name == "ctx":
        return True
    return getattr(annotation, "__name__", None) == "Context"


def _infer_option_decl(name: str) -> tuple[str, ...]:
    long_name = f"--{name.replace('_', '-')}"
    return (long_name,)


def get_params_from_function(func: Any) -> list[ParamMeta]:
    signature = inspect.signature(func, eval_str=True)
    type_hints = get_type_hints(func, include_extras=True)
    params: list[ParamMeta] = []
    for param in signature.parameters.values():
        annotation = type_hints.get(param.name, param.annotation)
        annotation, meta_infos = _split_annotation(annotation)
        if len(meta_infos) > 1:
            raise IntrospectionError(
                f"Multiple Argon parameter annotations found for {param.name!r}"
            )

        is_context = _looks_like_context(param.name, annotation)

        parameter_info: ParameterInfo
        default: Any = param.default

        if meta_infos:
            parameter_info = deepcopy(meta_infos[0])
            if param.default is not inspect._empty:
                parameter_info.default = param.default
        elif isinstance(param.default, ParameterInfo):
            parameter_info = deepcopy(param.default)
            default = parameter_info.default
        elif is_context:
            parameter_info = ArgumentInfo(default=Required)
            default = Required
        elif param.default is inspect._empty:
            parameter_info = ArgumentInfo(default=Required)
            default = Required
        else:
            parameter_info = OptionInfo(default=param.default, param_decls=_infer_option_decl(param.name))
            default = param.default

        if isinstance(parameter_info, OptionInfo) and not parameter_info.param_decls:
            parameter_info.param_decls = _infer_option_decl(param.name)
        if parameter_info.default_factory is not None and parameter_info.default is Required:
            parameter_info.default = parameter_info.default_factory()

        params.append(
            ParamMeta(
                name=param.name,
                annotation=annotation,
                default=default,
                kind=param.kind,
                parameter_info=parameter_info,
                is_context=is_context,
            )
        )
    return params
