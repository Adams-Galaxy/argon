from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable, Iterable, Iterator, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from rich.panel import Panel
from rich.progress import BarColumn, Progress, ProgressColumn, SpinnerColumn, Task, TextColumn
from rich.rule import Rule
from rich.text import Text


class LiveDisplayError(RuntimeError):
    pass


class _ElapsedColumn(ProgressColumn):
    def __init__(self, style: str) -> None:
        super().__init__()
        self.style = style

    def render(self, task: Task) -> Text:
        elapsed = task.finished_time if task.finished else task.elapsed
        if elapsed is None:
            return Text("--.-s", style=self.style)
        return Text(f"{elapsed:0.1f}s", style=self.style)


class _RemainingColumn(ProgressColumn):
    def __init__(self, style: str) -> None:
        super().__init__()
        self.style = style

    def render(self, task: Task) -> Text:
        remaining = task.time_remaining
        if remaining is None:
            return Text("--.-s", style=self.style)
        return Text(f"{remaining:0.1f}s", style=self.style)


class _PercentageColumn(ProgressColumn):
    def __init__(self, style: str) -> None:
        super().__init__()
        self.style = style

    def render(self, task: Task) -> Text:
        if not task.total:
            return Text("", style=self.style)
        percentage = task.percentage or 0.0
        return Text(f"{percentage:>5.1f}%", style=self.style)


try:
    from rich.progress import TaskID
except Exception:  # pragma: no cover
    TaskID = int  # type: ignore[misc, assignment]


def _coerce_finish_text(
    value: str | Text,
    *,
    fallback_style: str,
    success_symbol: str = "✓",
    error_symbol: str = "✗",
) -> Text:
    if isinstance(value, Text):
        return value
    if value == "success":
        return Text(success_symbol, style="argon.feedback.success")
    if value == "error":
        return Text(error_symbol, style="argon.feedback.error")
    if value == "blank":
        return Text(" ", style=fallback_style)
    return Text.from_markup(value, style=fallback_style)


@dataclass(slots=True)
class _LiveOwner:
    output: Output
    progress: Progress
    claimed: bool = False

    def start(self) -> None:
        self.output._claim_live(self)
        self.claimed = True
        self.progress.start()

    def stop(self) -> None:
        try:
            self.progress.stop()
        finally:
            if self.claimed:
                self.output._release_live(self)
                self.claimed = False


@dataclass(slots=True)
class StatusDisplay(_LiveOwner):
    task_id: TaskID = 0
    final: str | Text = "success"
    failed_final: str | Text = "error"
    resolved_final: str | Text | None = None

    def __enter__(self) -> "StatusDisplay":
        self.start()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # type: ignore[no-untyped-def]
        final = self.resolved_final
        if final is None:
            final = self.failed_final if exc_type is not None else self.final
        if final != "leave":
            self.progress.update(self.task_id, total=1, completed=1)
        self.stop()

    async def __aenter__(self) -> "StatusDisplay":
        return self.__enter__()

    async def __aexit__(self, exc_type, exc, tb) -> None:  # type: ignore[no-untyped-def]
        self.__exit__(exc_type, exc, tb)

    def update(self, message: str) -> None:
        self.progress.update(self.task_id, description=message)

    def finish(self, final: str | Text, *, message: str | None = None) -> None:
        self.resolved_final = final
        live = self.output.live_config
        spinner_column = next(
            (column for column in self.progress.columns if isinstance(column, SpinnerColumn)),
            None,
        )
        if spinner_column is not None:
            spinner_column.finished_text = _coerce_finish_text(
                "blank" if final == "clear" else final,
                fallback_style="argon.live.spinner",
                success_symbol=getattr(live, "success_symbol", "✓"),
                error_symbol=getattr(live, "error_symbol", "✗"),
            )
        if message is not None:
            self.update(message)

    def succeed(self, message: str | None = None) -> None:
        self.finish("success", message=message)

    def fail(self, message: str | None = None) -> None:
        self.finish("error", message=message)


@dataclass(slots=True)
class ProgressDisplay(_LiveOwner):
    def __enter__(self) -> "ProgressDisplay":
        self.start()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # type: ignore[no-untyped-def]
        self.stop()

    async def __aenter__(self) -> "ProgressDisplay":
        return self.__enter__()

    async def __aexit__(self, exc_type, exc, tb) -> None:  # type: ignore[no-untyped-def]
        self.__exit__(exc_type, exc, tb)

    def add_task(self, description: str, *, total: float | None = None, start: bool = True) -> TaskID:
        return self.progress.add_task(description, total=total, start=start)

    def advance(self, task_id: TaskID, advance: float = 1.0) -> None:
        self.progress.advance(task_id, advance)

    def update(self, task_id: TaskID, **kwargs: Any) -> None:
        self.progress.update(task_id, **kwargs)

    async def gather(self, tasks: Mapping[str, Awaitable[Any]]) -> dict[str, Any]:
        task_ids = {name: self.add_task(name, total=1) for name in tasks}

        async def runner(name: str, awaitable: Awaitable[Any]) -> tuple[str, Any]:
            try:
                result = await awaitable
            except Exception:
                self.update(task_ids[name], description=f"{name} failed", completed=1)
                raise
            self.update(task_ids[name], completed=1)
            return name, result

        results = await asyncio.gather(*(runner(name, awaitable) for name, awaitable in tasks.items()))
        return dict(results)


@dataclass(slots=True)
class StageDisplay:
    display: ProgressDisplay
    task_id: TaskID
    description: str
    stage_names: tuple[str, ...]

    def __enter__(self) -> "StageDisplay":
        self.display.__enter__()
        if self.stage_names:
            self.display.update(self.task_id, description=f"{self.description}: {self.stage_names[0]}")
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # type: ignore[no-untyped-def]
        self.display.__exit__(exc_type, exc, tb)

    async def __aenter__(self) -> "StageDisplay":
        return self.__enter__()

    async def __aexit__(self, exc_type, exc, tb) -> None:  # type: ignore[no-untyped-def]
        self.__exit__(exc_type, exc, tb)

    def advance(self, stage_name: str | None = None) -> None:
        if stage_name is not None:
            self.display.update(self.task_id, description=f"{self.description}: {stage_name}")
        self.display.advance(self.task_id)

    def iter(self) -> Iterator[str]:
        for stage_name in self.stage_names:
            self.display.update(self.task_id, description=f"{self.description}: {stage_name}")
            yield stage_name
            self.display.advance(self.task_id)

    async def run(self, stage_name: str, action: Callable[[], Awaitable[Any]] | Awaitable[Any]) -> Any:
        self.display.update(self.task_id, description=f"{self.description}: {stage_name}")
        awaitable = action() if callable(action) else action
        result = await awaitable
        self.display.advance(self.task_id)
        return result


@dataclass(slots=True)
class Output:
    data_console: Any
    ui_console: Any | None = None
    live_config: Any | None = None
    records: list[object] = field(default_factory=list)
    _active_live: object | None = field(default=None, init=False)

    def __post_init__(self) -> None:
        if self.ui_console is None:
            self.ui_console = self.data_console

    def _claim_live(self, owner: object) -> None:
        if self._active_live is not None and self._active_live is not owner:
            raise LiveDisplayError("Another live display is already active")
        self._active_live = owner

    def _release_live(self, owner: object) -> None:
        if self._active_live is owner:
            self._active_live = None

    def _emit(self, renderable: object) -> None:
        self.records.append(renderable)
        self.data_console.print(renderable)

    def text(self, value: str = "", *, style: str | None = None) -> None:
        self._emit(Text(value, style=style or "argon.text.primary"))

    def rich(self, renderable: object) -> None:
        self._emit(renderable)

    def error(self, message: str) -> None:
        self._emit(Text(message, style="argon.error"))

    def warning(self, message: str) -> None:
        self._emit(Text(message, style="argon.warning"))

    def success(self, message: str) -> None:
        self._emit(Text(message, style="argon.success"))

    def panel(self, title: str, body: object) -> None:
        self._emit(Panel.fit(body, title=title, border_style="argon.border"))

    def kv(self, title: str, data: dict[str, object] | str) -> None:
        if isinstance(data, str):
            body = data
        else:
            body = "\n".join(f"{key}: {value}" for key, value in data.items())
        self.panel(title, body)

    def rule(self, title: str | None = None) -> None:
        self._emit(Rule(title or ""))

    def _build_status_progress(
        self,
        *,
        spinner: str,
        transient: bool,
        show_elapsed: bool,
        finished_text: Text,
    ) -> Progress:
        columns: list[ProgressColumn] = [
            SpinnerColumn(
                spinner_name=spinner,
                style="argon.live.spinner",
                finished_text=finished_text,
            ),
            TextColumn("[argon.live.message]{task.description}"),
        ]
        if show_elapsed:
            columns.append(_ElapsedColumn("argon.live.elapsed"))
        return Progress(
            *columns,
            console=self.ui_console,
            transient=transient,
            auto_refresh=True,
        )

    def status(
        self,
        message: str,
        *,
        spinner: str | None = None,
        transient: bool = False,
        show_elapsed: bool | None = None,
        final: str | Text | None = None,
        failed_final: str | Text | None = None,
    ) -> StatusDisplay:
        live = self.live_config
        resolved_spinner = spinner or getattr(live, "spinner", "dots")
        resolved_show_elapsed = (
            getattr(live, "show_elapsed", True) if show_elapsed is None else show_elapsed
        )
        resolved_final_policy = final if final is not None else getattr(live, "status_final", "success")
        resolved_failed_policy = (
            failed_final if failed_final is not None else getattr(live, "status_failed_final", "error")
        )
        resolved_transient = transient or resolved_final_policy == "clear"
        progress = self._build_status_progress(
            spinner=resolved_spinner,
            transient=resolved_transient,
            show_elapsed=resolved_show_elapsed,
            finished_text=_coerce_finish_text(
                "blank" if resolved_final_policy == "clear" else resolved_final_policy,
                fallback_style="argon.live.spinner",
                success_symbol=getattr(live, "success_symbol", "✓"),
                error_symbol=getattr(live, "error_symbol", "✗"),
            ),
        )
        task_id = progress.add_task(message, total=None)
        return StatusDisplay(
            output=self,
            progress=progress,
            task_id=task_id,
            final=resolved_final_policy,
            failed_final=resolved_failed_policy,
        )

    def spinner(
        self,
        message: str,
        *,
        spinner: str | None = None,
        transient: bool = False,
        show_elapsed: bool | None = None,
        final: str | Text | None = None,
        failed_final: str | Text | None = None,
    ) -> StatusDisplay:
        return self.status(
            message,
            spinner=spinner,
            transient=transient,
            show_elapsed=show_elapsed,
            final=final,
            failed_final=failed_final,
        )

    def progress(self, *, transient: bool | None = None) -> ProgressDisplay:
        live = self.live_config
        resolved_transient = getattr(live, "progress_transient", False) if transient is None else transient
        progress = Progress(
            SpinnerColumn(style="argon.live.spinner"),
            TextColumn("[argon.progress.description]{task.description}"),
            BarColumn(
                style="argon.progress.bar",
                complete_style="argon.progress.complete",
                finished_style="argon.progress.complete",
                pulse_style="argon.progress.bar",
            ),
            _PercentageColumn("argon.progress.percentage"),
            _ElapsedColumn("argon.live.elapsed"),
            _RemainingColumn("argon.progress.remaining"),
            console=self.ui_console,
            transient=resolved_transient,
            auto_refresh=True,
        )
        return ProgressDisplay(output=self, progress=progress)

    def track(
        self,
        sequence: Iterable[Any],
        *,
        description: str,
        total: int | None = None,
        transient: bool | None = None,
    ) -> Iterator[Any]:
        progress = self.progress(transient=transient)
        resolved_total = total if total is not None else len(sequence) if hasattr(sequence, "__len__") else None

        def iterator() -> Iterator[Any]:
            with progress as display:
                task_id = display.add_task(description, total=resolved_total)
                for item in sequence:
                    yield item
                    display.advance(task_id)

        return iterator()

    def stages(
        self,
        stage_names: Sequence[str],
        *,
        description: str = "Stages",
        transient: bool | None = None,
    ) -> StageDisplay:
        display = self.progress(transient=transient)
        task_id = display.add_task(description, total=len(stage_names), start=False)
        return StageDisplay(
            display=display,
            task_id=task_id,
            description=description,
            stage_names=tuple(stage_names),
        )

    async def awaiting(
        self,
        awaitable: Awaitable[Any],
        *,
        message: str,
        spinner: str | None = None,
        transient: bool = False,
        show_elapsed: bool | None = None,
        final: str | Text | None = None,
        failed_final: str | Text | None = None,
        resolve_final: Callable[[Any], str | Text] | None = None,
        resolve_message: Callable[[Any], str | None] | None = None,
    ) -> Any:
        live = self.live_config
        resolved_final = final if final is not None else getattr(live, "awaiting_final", "clear")
        resolved_failed_final = (
            failed_final if failed_final is not None else getattr(live, "awaiting_failed_final", "error")
        )
        async with self.status(
            message,
            spinner=spinner,
            transient=transient,
            show_elapsed=show_elapsed,
            final=resolved_final,
            failed_final=resolved_failed_final,
        ) as status:
            result = await awaitable
            if resolve_final is not None:
                status.finish(resolve_final(result))
            if resolve_message is not None:
                message = resolve_message(result)
                if message is not None:
                    status.update(message)
            return result

    async def gather(
        self,
        tasks: Mapping[str, Awaitable[Any]],
        *,
        transient: bool | None = None,
    ) -> dict[str, Any]:
        async with self.progress(transient=transient) as display:
            return await display.gather(tasks)
