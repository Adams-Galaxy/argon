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


def test_completion_item_is_public() -> None:
    item = argon.CompletionItem("prod", display="production", meta="Primary")
    assert item.text == "prod"
    assert item.display == "production"
    assert item.meta == "Primary"


def test_completion_keeps_autocompletion_alias() -> None:
    source = ("prod",)
    assert argon.Option(autocompletion=source).autocompletion is source
    assert argon.Argument(autocompletion=source).autocompletion is source


def test_completion_aliases_are_mutually_exclusive() -> None:
    try:
        argon.Option(completion=("prod",), autocompletion=("preview",))
    except ValueError as exc:
        assert str(exc) == "Use either completion or autocompletion, not both"
    else:  # pragma: no cover
        raise AssertionError("expected completion alias conflict")
