from __future__ import annotations

import inspect
import sys
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from .config import ShellConfig
from .introspect import get_params_from_function
from .models import CommandSpec, GroupSpec
from .ui.theme import ArgonTheme


@dataclass(slots=True)
class _GroupBuilder:
    app: "App"
    spec: GroupSpec

    def command(
        self,
        name: str | None = None,
        *,
        help: str | None = None,
        hidden: bool = False,
        deprecated: bool = False,
        aliases: tuple[str, ...] = (),
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        return self.app._command(self.spec, name, help, hidden, deprecated, aliases)

    def group(
        self,
        name: str | None = None,
        *,
        help: str | None = None,
        hidden: bool = False,
        aliases: tuple[str, ...] = (),
    ) -> "_GroupBuilder":
        return self.app._group(self.spec, name, help, hidden, aliases)

    def callback(
        self,
        *,
        invoke_without_command: bool | None = None,
        no_args_is_help: bool | None = None,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        return self.app._callback(self.spec, invoke_without_command, no_args_is_help)

    def add_typer(self, app: "App", *, name: str | None = None, help: str | None = None) -> None:
        self.app._add_typer(self.spec, app, name=name, help=help)


class App:
    def __init__(
        self,
        *,
        name: str | None = None,
        help: str | None = None,
        version: str | None = None,
        no_args_is_help: bool = False,
        invoke_without_command: bool = False,
        theme: ArgonTheme | None = None,
        shell_config: ShellConfig | None = None,
    ) -> None:
        self.name = name or "app"
        self.help = help
        self.version = version
        self.theme = theme
        self.shell_config = shell_config or ShellConfig()
        self._console_instance = None
        self.root = GroupSpec(
            name="",
            help=help,
            no_args_is_help=no_args_is_help,
            invoke_without_command=invoke_without_command,
        )

    def _command(
        self,
        parent: GroupSpec,
        name: str | None,
        help: str | None,
        hidden: bool,
        deprecated: bool,
        aliases: tuple[str, ...],
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
            command_name = name or fn.__name__.replace("_", "-")
            spec = CommandSpec(
                name=command_name,
                callback=fn,
                help=help or inspect.getdoc(fn) or None,
                hidden=hidden,
                deprecated=deprecated,
                aliases=aliases,
                params=get_params_from_function(fn),
                parent=parent,
            )
            parent.commands[command_name] = spec
            return fn

        return decorator

    def command(
        self,
        name: str | None = None,
        *,
        help: str | None = None,
        hidden: bool = False,
        deprecated: bool = False,
        aliases: tuple[str, ...] = (),
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        return self._command(self.root, name, help, hidden, deprecated, aliases)

    def _group(
        self,
        parent: GroupSpec,
        name: str | None,
        help: str | None,
        hidden: bool,
        aliases: tuple[str, ...],
    ) -> _GroupBuilder:
        if not name:
            raise ValueError("Group name is required")
        group = GroupSpec(name=name, help=help, hidden=hidden, aliases=aliases, parent=parent)
        parent.groups[name] = group
        return _GroupBuilder(app=self, spec=group)

    def group(
        self,
        name: str | None = None,
        *,
        help: str | None = None,
        hidden: bool = False,
        aliases: tuple[str, ...] = (),
    ) -> _GroupBuilder:
        return self._group(self.root, name, help, hidden, aliases)

    def _callback(
        self,
        group: GroupSpec,
        invoke_without_command: bool | None,
        no_args_is_help: bool | None,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
            group.callback = fn
            group.callback_params = get_params_from_function(fn)
            if invoke_without_command is not None:
                group.invoke_without_command = invoke_without_command
            if no_args_is_help is not None:
                group.no_args_is_help = no_args_is_help
            return fn

        return decorator

    def callback(
        self,
        *,
        invoke_without_command: bool | None = None,
        no_args_is_help: bool | None = None,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        return self._callback(self.root, invoke_without_command, no_args_is_help)

    def _add_typer(
        self,
        parent: GroupSpec,
        app: "App",
        *,
        name: str | None = None,
        help: str | None = None,
    ) -> None:
        group_name = name or app.name
        mounted = GroupSpec(
            name=group_name,
            help=help or app.help,
            parent=parent,
            invoke_without_command=app.root.invoke_without_command,
            no_args_is_help=app.root.no_args_is_help,
            callback=app.root.callback,
            callback_params=app.root.callback_params,
            groups=app.root.groups,
            commands=app.root.commands,
        )
        for group in mounted.groups.values():
            group.parent = mounted
        for command in mounted.commands.values():
            command.parent = mounted
        parent.groups[group_name] = mounted

    def add_typer(self, app: "App", *, name: str | None = None, help: str | None = None) -> None:
        self._add_typer(self.root, app, name=name, help=help)

    def console(self) -> "Console":
        from .console.runtime import Console

        if self._console_instance is None:
            self._console_instance = Console(self)
        return self._console_instance

    def shell(self, **kwargs: Any) -> "Shell":
        from .shell.run import Shell

        return Shell(self.console(), **kwargs)

    def run_argv(self, argv: list[str] | None = None) -> object:
        return self.console().execute_argv(list(argv if argv is not None else sys.argv[1:]))

    def run_line(self, line: str) -> object:
        return self.console().execute_line(line)

    def run_shell(self, **kwargs: Any) -> int:
        return self.shell(**kwargs).run()

    def __call__(self) -> object:
        return self.run_argv()
