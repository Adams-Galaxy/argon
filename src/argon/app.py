from __future__ import annotations

import inspect
import sys
from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from .config import ShellConfig
from .introspect import get_params_from_function
from .models import CommandSpec, GroupSpec
from .ui.theme import ArgonTheme

if TYPE_CHECKING:  # pragma: no cover
    from .console.runtime import Console
    from .shell.run import Shell


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
    """Primary Argon application object.

    @param name Application name used in help/version/prompt defaults.
    @param help Optional top-level help text.
    @param version Optional application version string.
    @param no_args_is_help Whether root invocation with no args should render help.
    @param invoke_without_command Whether root callback runs without a subcommand.
    @param theme Optional semantic theme override.
    @param shell_config Optional shell frontend configuration.
    """

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
        self._console_instance: Console | None = None
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
        """Register a command on the root group.

        @param name Optional command name. Defaults to function name with dashes.
        @param help Optional help override for the command.
        @param hidden Whether the command is hidden from help/completion.
        @param deprecated Whether the command should be marked deprecated in help.
        @param aliases Optional alternate command names.
        @returns A decorator that registers the command callback.
        """

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
        """Register a root sub-group.

        @param name Group name.
        @param help Optional help text.
        @param hidden Whether the group is hidden from help/completion.
        @param aliases Optional alternate group names.
        @returns Group builder used to register nested commands/groups/callbacks.
        @raises ValueError If `name` is empty.
        """

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
        """Register a callback for the root group.

        @param invoke_without_command Optional override for callback invocation behavior.
        @param no_args_is_help Optional override for help-on-empty behavior.
        @returns A decorator that registers the callback.
        """

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
        """Mount another Argon app under this app.

        @param app App instance to mount.
        @param name Optional mount group name.
        @param help Optional help override for the mount group.
        """

        self._add_typer(self.root, app, name=name, help=help)

    def console(self) -> Console:
        """Return the canonical backend console instance.

        @returns Stable `Console` instance for execution/help/completion APIs.
        """

        from .console.runtime import Console

        if self._console_instance is None:
            self._console_instance = Console(self)
        return self._console_instance

    def shell(self, **kwargs: Any) -> Shell:
        """Create a shell frontend bound to this app's console.

        @param kwargs Optional shell constructor overrides.
        @returns New `Shell` instance.
        """

        from .shell.run import Shell

        return Shell(self.console(), **kwargs)

    def run_argv(self, argv: list[str] | None = None) -> object:
        """Execute command graph from argv tokens.

        @param argv Argv token list. Defaults to `sys.argv[1:]`.
        @returns Command callback result or builtin/help render output.
        """

        return self.console().execute_argv(list(argv if argv is not None else sys.argv[1:]))

    async def run_argv_async(self, argv: list[str] | None = None) -> object:
        """Execute command graph from argv tokens in async contexts.

        @param argv Argv token list. Defaults to `sys.argv[1:]`.
        @returns Awaited command callback result or builtin/help render output.
        """

        return await self.console().execute_argv_async(list(argv if argv is not None else sys.argv[1:]))

    def run_line(self, line: str) -> object:
        """Execute command graph from a shell-like command line.

        @param line Command line input string.
        @returns Command callback result or builtin/help render output.
        """

        return self.console().execute_line(line)

    async def run_line_async(self, line: str) -> object:
        """Execute command graph from a shell line in async contexts.

        @param line Command line input string.
        @returns Awaited command callback result or builtin/help render output.
        """

        return await self.console().execute_line_async(line)

    def run_shell(self, **kwargs: Any) -> int:
        """Run the interactive shell frontend.

        @param kwargs Optional shell constructor overrides.
        @returns Shell exit code.
        """

        return self.shell(**kwargs).run()

    def __call__(self) -> object:
        """Execute this app from process argv.

        @returns Same as `run_argv()` with default argv source.
        """

        return self.run_argv()
