from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any

from .models import ArgumentInfo, OptionInfo


def Option(
    *param_decls: str,
    help: str | None = None,
    metavar: str | None = None,
    envvar: str | list[str] | None = None,
    parser: Callable[[str], Any] | None = None,
    autocompletion: Callable[..., Sequence[str]] | None = None,
    default_factory: Callable[[], Any] | None = None,
    hidden: bool = False,
    required: bool = False,
    show_default: bool | str = True,
    rich_help_panel: str | None = None,
) -> OptionInfo:
    return OptionInfo(
        param_decls=tuple(param_decls),
        help=help,
        metavar=metavar,
        envvar=envvar,
        parser=parser,
        autocompletion=autocompletion,
        default_factory=default_factory,
        hidden=hidden,
        required=required,
        show_default=show_default,
        rich_help_panel=rich_help_panel,
    )


def Argument(
    *,
    help: str | None = None,
    metavar: str | None = None,
    envvar: str | list[str] | None = None,
    parser: Callable[[str], Any] | None = None,
    autocompletion: Callable[..., Sequence[str]] | None = None,
    default_factory: Callable[[], Any] | None = None,
    hidden: bool = False,
    required: bool = False,
    show_default: bool | str = True,
    rich_help_panel: str | None = None,
) -> ArgumentInfo:
    return ArgumentInfo(
        help=help,
        metavar=metavar,
        envvar=envvar,
        parser=parser,
        autocompletion=autocompletion,
        default_factory=default_factory,
        hidden=hidden,
        required=required,
        show_default=show_default,
        rich_help_panel=rich_help_panel,
    )
