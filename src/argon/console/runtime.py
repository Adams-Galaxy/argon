from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, cast

from ..models import GroupSpec
from ..ui.formatter import Formatter
from ..ui.rich_console import build_console
from ..ui.tokens import (
    ChainBroker,
    PrefixBroker,
    StaticBroker,
    TokenFn,
    TokenValue,
    build_system_broker,
)
from .completion import complete
from .context import Context
from .dispatch import (
    finalize_result_sync,
    forward_callable,
    invoke_callable,
    invoke_command,
    invoke_command_async,
)
from .errors import UsageError
from .help import render_command_help, render_group_help
from .highlighting import highlight
from .output import Output
from .parser import parse_tokens, split_line
from .registry import resolve


@dataclass(slots=True)
class Console:
    """Canonical backend runtime for command execution and shell semantics.

    @param app Argon app instance that owns command graph/config/theme.
    """

    app: Any
    rich_console: Any = field(init=False)
    output: Output = field(init=False)
    formatter: Formatter = field(init=False)
    meta: dict[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        app_tokens: dict[str, str] = {
            "name": str(self.app.name),
            "help": str(self.app.help or ""),
            "version": str(self.app.version or ""),
        }
        session_tokens = cast(dict[str, TokenValue | TokenFn], self.meta)
        self.rich_console = build_console(theme=self.app.theme)
        self.output = Output(
            self.rich_console,
            ui_console=self.rich_console,
            live_config=self.app.shell_config.live,
        )
        self.formatter = Formatter(
            base_broker=ChainBroker(
                (
                    PrefixBroker(
                        "app.",
                        StaticBroker(app_tokens),
                    ),
                    PrefixBroker("session.", StaticBroker(session_tokens)),
                    PrefixBroker("system.", build_system_broker()),
                )
            ),
            console=self.rich_console,
            ansi_console=build_console(theme=self.app.theme, force_terminal=True),
        )

    def _bind_rich_console(self, rich_console: Any) -> None:
        self.rich_console = rich_console
        self.output.data_console = rich_console
        self.output.ui_console = rich_console
        self.formatter.console = rich_console

    @contextmanager
    def terminal_output(self):
        """Force terminal-capable Rich consoles during interactive shell sessions.

        @returns Context manager yielding this console with terminal-bound output handles.
        """

        previous_console = self.rich_console
        previous_ansi_console = self.formatter.ansi_console
        forced_console = build_console(theme=self.app.theme, force_terminal=True)
        forced_ansi_console = build_console(theme=self.app.theme, force_terminal=True)
        self._bind_rich_console(forced_console)
        self.formatter.ansi_console = forced_ansi_console
        try:
            yield self
        finally:
            self._bind_rich_console(previous_console)
            self.formatter.ansi_console = previous_ansi_console

    @property
    def root(self) -> GroupSpec:
        return self.app.root

    def _build_context(
        self,
        *,
        command,
        result,
        parent: Context | None = None,
    ) -> Context:
        params = dict(result.values)
        params.update(result.invocation.options)
        return Context(
            app=self.app,
            console=self,
            command_path=result.invocation.path,
            args=result.invocation.args,
            params=params,
            raw_argv=result.invocation.argv,
            passthrough=result.invocation.passthrough,
            out=self.output,
            meta=self.meta,
            parent=parent,
        )

    def _invoke_group_callbacks(self, groups: tuple[GroupSpec, ...], ctx: Context) -> None:
        for group in groups:
            if group.callback is not None:
                finalize_result_sync(self.invoke_callable(group.callback, ctx, args=(), kwargs={}))

    async def _invoke_group_callbacks_async(self, groups: tuple[GroupSpec, ...], ctx: Context) -> None:
        from .dispatch import finalize_result_async

        for group in groups:
            if group.callback is not None:
                await finalize_result_async(self.invoke_callable(group.callback, ctx, args=(), kwargs={}))

    def _render_help(self, resolution) -> object:
        if resolution.command is not None:
            return render_command_help(app_name=self.app.name, command=resolution.command)
        return render_group_help(app_name=self.app.name, group=resolution.groups[-1])

    def help(self, path: tuple[str, ...] = ()) -> object:
        """Render help for a group or command path.

        @param path Command/group path tokens.
        @returns Rich renderable help object.
        """

        resolution = resolve(self.root, list(path))
        return self._render_help(resolution)

    def _handle_builtin(self, argv: list[str]) -> object | None:
        if argv and argv[0] == "help":
            resolution = resolve(self.root, argv[1:])
            help_renderable = self._render_help(resolution)
            self.output.rich(help_renderable)
            return help_renderable
        if "--version" in argv or (argv and argv[0] == "version"):
            if not self.app.version:
                raise UsageError("Version is not configured for this application")
            message = f"{self.app.name} {self.app.version}"
            self.output.text(message, style="argon.title")
            return message
        return None

    def execute_argv(self, argv: list[str]) -> object:
        """Execute a command invocation from argv tokens.

        @param argv Argv token list.
        @returns Command callback result or builtin/help render output.
        @raises UsageError On parse/usage failures.
        """

        builtin = self._handle_builtin(argv)
        if builtin is not None:
            return builtin
        if not argv:
            if self.root.no_args_is_help:
                help_renderable = self.help()
                self.output.rich(help_renderable)
                return help_renderable
            raise UsageError("No command provided")

        if any(token in {"-h", "--help"} for token in argv):
            filtered = [token for token in argv if token not in {"-h", "--help"}]
            resolution = resolve(self.root, filtered)
            help_renderable = self._render_help(resolution)
            self.output.rich(help_renderable)
            return help_renderable

        resolution = resolve(self.root, argv)
        if resolution.command is None:
            group = resolution.groups[-1]
            if group.callback is not None and group.invoke_without_command:
                empty_ctx = Context(
                    app=self.app,
                    console=self,
                    command_path=resolution.path,
                    args=(),
                    params={},
                    raw_argv=tuple(argv),
                    passthrough=(),
                    out=self.output,
                    meta=self.meta,
                )
                return finalize_result_sync(self.invoke_callable(group.callback, empty_ctx, args=(), kwargs={}))
            if not resolution.path and self.root.no_args_is_help:
                help_renderable = self.help()
                self.output.rich(help_renderable)
                return help_renderable
            raise UsageError(f"Unknown command: {' '.join(argv)}")

        parsed = parse_tokens(resolution.command, list(resolution.remaining))
        ctx = self._build_context(command=resolution.command, result=parsed)
        self._invoke_group_callbacks(resolution.groups, ctx)
        return invoke_command(resolution.command, ctx, parsed.values)

    def execute_line(self, line: str) -> object:
        """Execute a command invocation from a shell-style line.

        @param line Command line string.
        @returns Command callback result or builtin/help render output.
        @raises UsageError On split/parse/usage failures.
        """

        tokens = split_line(line)
        return self.execute_argv(tokens)

    async def execute_argv_async(self, argv: list[str]) -> object:
        """Execute argv tokens and await async command callbacks.

        @param argv Argv token list.
        @returns Awaited command callback result or builtin/help render output.
        @raises UsageError On parse/usage failures.
        """

        from .dispatch import finalize_result_async

        builtin = self._handle_builtin(argv)
        if builtin is not None:
            return builtin
        if not argv:
            if self.root.no_args_is_help:
                help_renderable = self.help()
                self.output.rich(help_renderable)
                return help_renderable
            raise UsageError("No command provided")

        if any(token in {"-h", "--help"} for token in argv):
            filtered = [token for token in argv if token not in {"-h", "--help"}]
            resolution = resolve(self.root, filtered)
            help_renderable = self._render_help(resolution)
            self.output.rich(help_renderable)
            return help_renderable

        resolution = resolve(self.root, argv)
        if resolution.command is None:
            group = resolution.groups[-1]
            if group.callback is not None and group.invoke_without_command:
                empty_ctx = Context(
                    app=self.app,
                    console=self,
                    command_path=resolution.path,
                    args=(),
                    params={},
                    raw_argv=tuple(argv),
                    passthrough=(),
                    out=self.output,
                    meta=self.meta,
                )
                return await finalize_result_async(
                    self.invoke_callable(group.callback, empty_ctx, args=(), kwargs={})
                )
            if not resolution.path and self.root.no_args_is_help:
                help_renderable = self.help()
                self.output.rich(help_renderable)
                return help_renderable
            raise UsageError(f"Unknown command: {' '.join(argv)}")

        parsed = parse_tokens(resolution.command, list(resolution.remaining))
        ctx = self._build_context(command=resolution.command, result=parsed)
        await self._invoke_group_callbacks_async(resolution.groups, ctx)
        return await invoke_command_async(resolution.command, ctx, parsed.values)

    async def execute_line_async(self, line: str) -> object:
        """Execute a shell line and await async command callbacks.

        @param line Command line string.
        @returns Awaited command callback result or builtin/help render output.
        @raises UsageError On split/parse/usage failures.
        """

        tokens = split_line(line)
        return await self.execute_argv_async(tokens)

    def complete(self, line: str, cursor: int | None = None):
        """Return completion candidates for interactive shell input.

        @param line Full input line.
        @param cursor Cursor position within the line.
        @returns Completion result with items and replacement span.
        """

        return complete(
            self.root,
            line,
            cursor,
            app_version=self.app.version,
            option_display=self.app.shell_config.completion.option_display,
        )

    def highlight(self, line: str):
        """Return semantic highlight spans for shell input.

        @param line Full input line.
        @returns Semantic styled spans with source offsets.
        """

        return highlight(self.root, line)

    def invoke_callable(self, fn: Any, ctx: Context, *, args: tuple[Any, ...], kwargs: dict[str, Any]) -> Any:
        return invoke_callable(fn, ctx, args=args, kwargs=kwargs)

    def forward_callable(self, fn: Any, ctx: Context, *, overrides: dict[str, Any]) -> Any:
        return forward_callable(fn, ctx, overrides=overrides)
