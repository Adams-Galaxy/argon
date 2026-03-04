from __future__ import annotations

from typing import Annotated

import argon
from argon.introspect import get_params_from_function
from argon.models import ArgumentInfo, OptionInfo


def test_introspect_infers_argument_and_option() -> None:
    def greet(name: str, times: int = 1) -> None:
        return None

    params = get_params_from_function(greet)
    assert isinstance(params[0].parameter_info, ArgumentInfo)
    assert isinstance(params[1].parameter_info, OptionInfo)
    assert params[1].parameter_info.param_decls == ("--times",)


def test_introspect_keeps_annotated_metadata() -> None:
    def greet(
        name: Annotated[str, argon.Argument(help="Who")],
        times: Annotated[int, argon.Option("--times", "-t", help="Repeat")] = 1,
    ) -> None:
        return None

    params = get_params_from_function(greet)
    assert params[0].parameter_info.help == "Who"
    assert params[1].parameter_info.param_decls == ("--times", "-t")


def test_introspect_detects_context() -> None:
    def greet(ctx: argon.Context, name: str) -> None:
        return None

    params = get_params_from_function(greet)
    assert params[0].is_context is True
    assert params[1].is_context is False


def test_introspect_bool_option_inference() -> None:
    def greet(verbose: bool = False) -> None:
        return None

    params = get_params_from_function(greet)
    assert isinstance(params[0].parameter_info, OptionInfo)
    assert params[0].annotation is bool
