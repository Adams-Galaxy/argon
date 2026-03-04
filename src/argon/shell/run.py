from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ..ui.tokens import TokenFn, TokenValue
from .session import ShellSession


@dataclass(slots=True)
class Shell:
    """Interactive shell adapter over the backend console.

    @param console Backend `Console` instance.
    @param prompt Optional prompt template override.
    @param history Optional history enable override.
    @param mouse_support Optional mouse support override.
    @param history_path Optional history file path override.
    @param prompt_tokens Optional prompt token override mapping.
    """

    console: Any
    prompt: str | None = None
    history: bool | None = None
    mouse_support: bool | None = None
    history_path: str | None = None
    prompt_tokens: Mapping[str, TokenValue | TokenFn] | None = None
    session: ShellSession = field(init=False)

    def __post_init__(self) -> None:
        shell_config = self.console.app.shell_config
        history_enabled = shell_config.history if self.history is None else self.history
        prompt_template = shell_config.prompt.template if self.prompt is None else self.prompt
        prompt_tokens = shell_config.prompt.tokens if self.prompt_tokens is None else self.prompt_tokens
        history_path = self.history_path if self.history_path is not None else shell_config.history_path
        resolved_history = Path(history_path) if history_enabled and history_path else None
        self.history = history_enabled
        self.mouse_support = (
            shell_config.mouse_support if self.mouse_support is None else self.mouse_support
        )
        self.session = ShellSession(
            prompt=prompt_template,
            history_path=resolved_history,
            prompt_tokens=prompt_tokens,
        )

    def run(self) -> int:
        """Run the shell prompt loop.

        @returns Shell exit code.
        """

        with self.console.terminal_output():
            try:
                from .ptk.repl import run_ptk_repl
            except Exception:  # noqa: BLE001
                return self._run_basic()
            return run_ptk_repl(self.console, self.session, mouse_support=bool(self.mouse_support))

    def _run_basic(self) -> int:
        while True:
            try:
                prompt = self.console.formatter.render_ansi(
                    self.session.prompt,
                    extra=self.session.prompt_tokens,
                )
                line = input(prompt)
            except (EOFError, KeyboardInterrupt):
                return 0
            if not line.strip():
                continue
            try:
                self.console.execute_line(line)
            except Exception as exc:  # noqa: BLE001
                self.console.output.error(str(exc))
        return 0
