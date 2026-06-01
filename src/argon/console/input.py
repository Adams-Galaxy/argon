from __future__ import annotations

import asyncio
import select
import sys
import termios
import time
import tty
from collections.abc import Callable, Iterable
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, TextIO

KeySource = Callable[[float], str | None]


class KeyReader:
    """Non-blocking key reader used by `Input.keys()`."""

    def read_key(self, timeout: float = 0.0) -> str | None:
        """Read one normalized key name, or `None` when no key is available.

        @param timeout Maximum seconds to wait for a key.
        @returns Normalized key name such as `enter`, `escape`, `up`, or a literal character.
        """
        raise NotImplementedError


@dataclass(slots=True)
class _NullKeyReader(KeyReader):
    def read_key(self, timeout: float = 0.0) -> str | None:
        return None


@dataclass(slots=True)
class _SourceKeyReader(KeyReader):
    source: KeySource

    def read_key(self, timeout: float = 0.0) -> str | None:
        value = self.source(timeout)
        return _normalize_key(value, self.source)


@dataclass(slots=True)
class _TerminalKeyReader(KeyReader):
    stream: TextIO
    _fd: int | None = field(default=None, init=False)
    _settings: Any = field(default=None, init=False)

    def __enter__(self) -> _TerminalKeyReader:
        self._fd = self.stream.fileno()
        self._settings = termios.tcgetattr(self._fd)
        tty.setcbreak(self._fd)
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # type: ignore[no-untyped-def]
        if self._fd is not None and self._settings is not None:
            termios.tcsetattr(self._fd, termios.TCSADRAIN, self._settings)

    def _read_char(self, timeout: float = 0.0) -> str | None:
        if self._fd is None:
            return None
        readable, _, _ = select.select([self.stream], [], [], max(0.0, timeout))
        if not readable:
            return None
        return self.stream.read(1)

    def read_key(self, timeout: float = 0.0) -> str | None:
        return _normalize_key(self._read_char(timeout), self._read_char)


def _normalize_key(value: str | None, read_next: KeySource) -> str | None:
    if value is None:
        return None
    if value in {"\r", "\n"}:
        return "enter"
    if value in {"\x7f", "\b"}:
        return "backspace"
    if value == "\t":
        return "tab"
    if value == "\x1b":
        second = read_next(0.15)
        if second != "[":
            return "escape"
        third = read_next(0.15)
        if third == "A":
            return "up"
        if third == "B":
            return "down"
        if third == "C":
            return "right"
        if third == "D":
            return "left"
        if third == "3" and read_next(0.15) == "~":
            return "delete"
        return "escape"
    return value


@dataclass(slots=True)
class Input:
    """Input helper surface exposed as `ctx.input`.

    @param stdin Input stream. Defaults to `sys.stdin`.
    @param key_source Optional test/custom key source returning raw key characters.
    """

    stdin: TextIO = field(default_factory=lambda: sys.stdin)
    key_source: KeySource | None = None

    @property
    def interactive(self) -> bool:
        """Whether the input stream is attached to an interactive terminal."""
        return bool(getattr(self.stdin, "isatty", lambda: False)())

    def prompt(self, message: str = "", *, default: str | None = None) -> str:
        """Prompt for a line of text.

        @param message Prompt text.
        @param default Value returned when the user submits an empty line.
        @returns Entered text or the configured default.
        """
        value = input(message)
        if value == "" and default is not None:
            return default
        return value

    async def prompt_async(self, message: str = "", *, default: str | None = None) -> str:
        """Prompt for a line of text without blocking the active event loop.

        @param message Prompt text.
        @param default Value returned when the user submits an empty line.
        @returns Entered text or the configured default.
        """
        return await asyncio.to_thread(self.prompt, message, default=default)

    @contextmanager
    def keys(self):
        """Open a raw key reader context.

        @returns Context manager yielding a `KeyReader`.
        """
        if self.key_source is not None:
            yield _SourceKeyReader(self.key_source)
            return
        if not self.interactive:
            yield _NullKeyReader()
            return
        with _TerminalKeyReader(self.stdin) as reader:
            yield reader

    def read_key(self, timeout: float = 0.0) -> str | None:
        """Read one normalized key name.

        @param timeout Maximum seconds to wait for a key.
        @returns Normalized key name, literal character, or `None`.
        """
        with self.keys() as keys:
            return keys.read_key(timeout)

    def wait_key(
        self,
        keys: Iterable[str] | None = None,
        *,
        timeout: float | None = None,
        interval: float = 0.03,
    ) -> str | None:
        """Wait until a key is pressed.

        @param keys Optional accepted key names.
        @param timeout Maximum seconds to wait.
        @param interval Polling interval.
        @returns The matching key, or `None` when timed out or non-interactive.
        """
        if not self.interactive and self.key_source is None:
            return None
        accepted = set(keys) if keys is not None else None
        deadline = None if timeout is None else time.monotonic() + timeout
        with self.keys() as reader:
            while deadline is None or time.monotonic() < deadline:
                key = reader.read_key(interval)
                if key is None:
                    continue
                if accepted is None or key in accepted:
                    return key
        return None

    async def wait_key_async(
        self,
        keys: Iterable[str] | None = None,
        *,
        timeout: float | None = None,
        interval: float = 0.03,
    ) -> str | None:
        """Wait for a key without blocking the active event loop.

        @param keys Optional accepted key names.
        @param timeout Maximum seconds to wait.
        @param interval Polling interval.
        @returns The matching key, or `None` when timed out or non-interactive.
        """
        return await asyncio.to_thread(
            self.wait_key,
            keys,
            timeout=timeout,
            interval=interval,
        )

    async def sleep(
        self,
        seconds: float,
        *,
        stop_keys: Iterable[str] | None = None,
        interval: float = 0.05,
    ) -> str | None:
        """Sleep while allowing configured keys to interrupt the wait.

        @param seconds Seconds to sleep.
        @param stop_keys Keys that stop the sleep early.
        @param interval Polling interval while interactive.
        @returns The key that stopped the sleep, or `None`.
        """
        if not self.interactive and self.key_source is None:
            await asyncio.sleep(seconds)
            return None

        accepted = set(stop_keys or ())
        deadline = time.monotonic() + max(0.0, seconds)
        with self.keys() as reader:
            while time.monotonic() < deadline:
                key = reader.read_key(0)
                if key is not None and (not accepted or key in accepted):
                    return key
                await asyncio.sleep(min(interval, max(0.0, deadline - time.monotonic())))
            key = reader.read_key(0)
            if key is not None and (not accepted or key in accepted):
                return key
        return None
