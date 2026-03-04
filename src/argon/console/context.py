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
        if message:
            self.out.error(message)
        raise Abort(message or "")

    def exit(self, code: int = 0) -> None:
        raise Exit(code)

    def invoke(self, fn: Any, /, *args: Any, **kwargs: Any) -> Any:
        return self.console.invoke_callable(fn, self, args=args, kwargs=kwargs)

    def forward(self, fn: Any, /, **overrides: Any) -> Any:
        return self.console.forward_callable(fn, self, overrides=overrides)
