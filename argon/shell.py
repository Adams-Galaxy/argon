from __future__ import annotations
import asyncio
from typing import Callable, Optional, Sequence, List, Union, Any, TYPE_CHECKING
from .exceptions import CLIError

if TYPE_CHECKING:  # pragma: no cover
    from .core import Interface

class Shell:
    def __init__(
        self,
        cli: "Interface",
        *,
        input_fn: Optional[Callable[[], str]] = None,
        output_fn: Optional[Callable[[str], None]] = None,
        prompt: str = "> ",
        exit_commands: Optional[Sequence[str]] = None,
        catch_exceptions: bool = True,
    ) -> None:
        self.cli = cli
        self.input_fn = input_fn or (lambda: input(prompt))  # type: ignore[arg-type]
        self.output_fn = output_fn or (lambda s: print(s))
        self.prompt = prompt
        self.exit_commands = set(c.lower() for c in (exit_commands or ["exit", "quit"]))
        self.catch_exceptions = catch_exceptions
        self.history: List[str] = []

    def write(self, text: str = "") -> None:
        self.output_fn(text)

    def once(self, line: str) -> None:
        if not line.strip():
            return
        self.history.append(line)
        if line.strip().lower() in self.exit_commands:
            raise EOFError()
        try:
            self.cli.run_line(line)
        except CLIError as e:
            self.write(str(e))
        except EOFError:
            raise
        except Exception as e:  # noqa: BLE001
            if self.catch_exceptions:
                self.write(f"Error: {e}")
            else:
                raise

        def loop(self) -> None:
            self.write(f"{self.cli.name} shell. Type 'exit' to leave.")
            while True:
                try:
                    line = self.input_fn()
                    if line is None:  # pragma: no cover
                        break
                    line = line.rstrip("\n")
                    self.once(line)
                except EOFError:
                    break

    def get_history(self) -> List[str]:
        return list(self.history)


class AsyncShell:
    """Asynchronous shell loop supporting async command coroutines."""

    def __init__(
        self,
        cli: "Interface",
        *,
        input_fn: Optional[Callable[[], Union[str, Any]]] = None,
        output_fn: Optional[Callable[[str], None]] = None,
        prompt: str = "> ",
        exit_commands: Optional[Sequence[str]] = None,
        catch_exceptions: bool = True,
    ) -> None:
        self.cli = cli
        self._raw_input_fn = input_fn or (lambda: input(prompt))  # blocking
        self.output_fn = output_fn or (lambda s: print(s))
        self.prompt = prompt
        self.exit_commands = set(c.lower() for c in (exit_commands or ["exit", "quit"]))
        self.catch_exceptions = catch_exceptions
        self.history: List[str] = []

    def write(self, text: str = "") -> None:
        self.output_fn(text)

    async def _read_line(self) -> str:
        return await asyncio.to_thread(self._raw_input_fn)

    async def once(self, line: str) -> None:
        if not line.strip():
            return
        self.history.append(line)
        if line.strip().lower() in self.exit_commands:
            raise EOFError()
        try:
            await self.cli.run_line_async(line)
        except CLIError as e:
            self.write(str(e))
        except EOFError:
            raise
        except Exception as e:  # noqa: BLE001
            if self.catch_exceptions:
                self.write(f"Error: {e}")
            else:
                raise

        async def loop(self) -> None:
            self.write(f"{self.cli.name} shell (async). Type 'exit' to leave.")
            while True:
                try:
                    line = await self._read_line()
                    line = line.rstrip("\n")
                    await self.once(line)
                except EOFError:
                    break

    def get_history(self) -> List[str]:
        return list(self.history)

__all__ = ["Shell", "AsyncShell"]