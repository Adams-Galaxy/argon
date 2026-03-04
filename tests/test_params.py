from __future__ import annotations

import argon
from argon.models import ArgumentInfo, OptionInfo


def test_option_factory_returns_option_info() -> None:
    info = argon.Option("--times", "-t", help="Repeat count")
    assert isinstance(info, OptionInfo)
    assert info.param_decls == ("--times", "-t")
    assert info.help == "Repeat count"


def test_argument_factory_returns_argument_info() -> None:
    info = argon.Argument(help="Target name")
    assert isinstance(info, ArgumentInfo)
    assert info.help == "Target name"


def test_option_factory_supports_required_and_envvar() -> None:
    info = argon.Option("--profile", required=True, envvar="APP_PROFILE")
    assert info.required is True
    assert info.envvar == "APP_PROFILE"


def test_argument_factory_supports_envvar() -> None:
    info = argon.Argument(envvar=["USER_NAME", "USER"])
    assert info.envvar == ["USER_NAME", "USER"]
