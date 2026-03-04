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
    """Create option parameter metadata.

    @param param_decls Option declarations such as `--times` or `-t`.
    @param help Help text shown in command help and completion metadata.
    @param metavar Placeholder label for help rendering.
    @param envvar Environment variable name(s) used for default resolution.
    @param parser Optional custom string-to-value parser.
    @param autocompletion Optional completion callback for option values.
    @param default_factory Optional callable used to produce default values.
    @param hidden Whether the option is hidden from help/completion.
    @param required Whether the option must be provided.
    @param show_default Whether and how defaults are shown in help.
    @param rich_help_panel Optional named help panel section.
    @returns `OptionInfo` metadata for use with `Annotated` or default assignment.
    """

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
    """Create argument parameter metadata.

    @param help Help text shown in command help.
    @param metavar Placeholder label for help rendering.
    @param envvar Environment variable name(s) used for default resolution.
    @param parser Optional custom string-to-value parser.
    @param autocompletion Optional completion callback for argument values.
    @param default_factory Optional callable used to produce default values.
    @param hidden Whether the argument is hidden from help/completion.
    @param required Whether the argument must be provided.
    @param show_default Whether and how defaults are shown in help.
    @param rich_help_panel Optional named help panel section.
    @returns `ArgumentInfo` metadata for use with `Annotated` or default assignment.
    """

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
