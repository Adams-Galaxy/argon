from __future__ import annotations
from dataclasses import dataclass
from typing import Callable, TYPE_CHECKING
from .args import ParsedArgs
from .specs import CommandSpec

if TYPE_CHECKING:  # pragma: no cover
    from .core import Interface

@dataclass
class Context:
    cli: "Interface"
    command: CommandSpec
    parsed: ParsedArgs
    global_options: ParsedArgs
    output: Callable[[str], None]

    def emit(self, text: str = "", *, to: str | None = None) -> None:
        """Emit output text.

        Parameters:
            text: The line to emit.
            to: Optional logical destination / channel. When provided and the
                underlying output callback exposes a 'send(text, to)' method,
                that method is used; otherwise falls back to broadcast via
                the basic single-argument output callable.

        This keeps backward compatibility: existing single-sink output
        functions still work, while richer routers (e.g. an OutputBus) can
        implement a 'send' method to target specific sessions.
        """
        if to is None:
            self.output(text)
            return
        # Best-effort: attempt a richer router interface
        send = getattr(self.output, 'send', None)
        if callable(send):  # type: ignore[truthy-bool]
            try:
                send(text, to)
                return
            except Exception:  # pragma: no cover - defensive
                pass
        # Fallback broadcast
        self.output(text)

__all__ = ["Context"]
