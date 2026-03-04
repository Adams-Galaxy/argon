from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from .errors import Abort, Exit

if TYPE_CHECKING:  # pragma: no cover
    from ..app import App
    from .output import Output
    from .runtime import Console


@dataclass(slots=True)
class Context:
    """Execution context injected into command callbacks.

    @param app Application instance handling the command.
    @param console Backend console instance.
    @param command_path Resolved command path tokens.
    @param args Positional argument values bound for invocation.
    @param params Bound parameter map including options/arguments.
    @param raw_argv Raw argv tokens for this command invocation.
    @param passthrough Tokens after `--` passthrough separator.
    @param out Output helper surface.
    @param obj Optional user object slot.
    @param meta Mutable context metadata dictionary.
    @param parent Optional parent context for nested invocations.
    """

    app: "App"
    console: "Console"
    command_path: tuple[str, ...]
    args: tuple[object, ...]
    params: dict[str, object]
    raw_argv: tuple[str, ...]
    passthrough: tuple[str, ...]
    out: "Output"
    obj: object | None = None
    meta: dict[str, object] = field(default_factory=dict)
    parent: "Context | None" = None

    def abort(self, message: str | None = None) -> None:
        """Abort execution immediately.

        @param message Optional error text emitted via `ctx.out.error`.
        @raises Abort Always raises `Abort`.
        """

        if message:
            self.out.error(message)
        raise Abort(message or "")

    def exit(self, code: int = 0) -> None:
        """Exit execution with a status code.

        @param code Process-like exit code.
        @raises Exit Always raises `Exit`.
        """

        raise Exit(code)

    def invoke(self, fn: Any, /, *args: Any, **kwargs: Any) -> Any:
        """Invoke another callable with automatic context injection.

        @param fn Callable to invoke.
        @param args Positional arguments for the callable.
        @param kwargs Keyword arguments for the callable.
        @returns Callable result.
        """

        return self.console.invoke_callable(fn, self, args=args, kwargs=kwargs)

    def forward(self, fn: Any, /, **overrides: Any) -> Any:
        """Forward current context params into another callable.

        @param fn Callable to invoke.
        @param overrides Parameter overrides to apply before forwarding.
        @returns Callable result.
        @raises BadParameter If a forwarded parameter cannot be resolved.
        """

        return self.console.forward_callable(fn, self, overrides=overrides)
