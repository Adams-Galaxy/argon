from __future__ import annotations

import asyncio
import sys
import time
from pathlib import Path
from typing import Annotated, Literal

import argon
from rich.text import Text


WORKSPACES = ("core", "design", "infra", "labs")
PROFILES = ("local", "staging", "prod")
TASKS = ("build", "test", "release", "doctor")

DEMO_CONFIG = argon.AppConfig.from_file(Path(__file__).with_name("demo.config.json"))
DEMO_THEME = DEMO_CONFIG.theme or argon.default_theme()
DEMO_SHELL_CONFIG = DEMO_CONFIG.shell


def _complete_workspace(prefix: str) -> list[str]:
    return [name for name in WORKSPACES if name.startswith(prefix)]


def _complete_profile(prefix: str) -> list[str]:
    return [name for name in PROFILES if name.startswith(prefix)]


def _complete_task(prefix: str) -> list[str]:
    return [name for name in TASKS if name.startswith(prefix)]


def _prompt_profile(formatter: object | None) -> Text:
    if formatter is None:
        return Text()
    profile = getattr(formatter, "resolve_token")("session.profile")
    if not profile:
        return Text()
    return Text(f" [{profile}]", style="argon.prompt.context")


def _prompt_workspace(formatter: object | None) -> Text:
    if formatter is None:
        return Text()
    workspace = getattr(formatter, "resolve_token")("session.workspace")
    if not workspace:
        return Text()
    return Text(f" {workspace}", style="argon.shell.command")


def _prompt_time(formatter: object | None) -> Text:
    if formatter is None:
        return Text()
    current = getattr(formatter, "resolve_token")("system.time")
    if not current:
        return Text()
    return Text(f" {current}", style="argon.prompt.meta")


app = argon.App(
    name="argon-demo",
    help="Shell-first reference app showing the intended Argon authoring flow.",
    version="1.0.0",
    theme=DEMO_THEME,
    no_args_is_help=True,
    shell_config=DEMO_SHELL_CONFIG.with_prompt_tokens(
        {
            "session.workspace_badge": _prompt_workspace,
            "session.profile_badge": _prompt_profile,
            "system.time_badge": _prompt_time,
        }
    ),
)


@app.callback()
def root(ctx: argon.Context) -> None:
    ctx.meta.setdefault("profile", "local")
    ctx.meta.setdefault("workspace", "")


@app.command(help="Show the current shell session state")
def status(ctx: argon.Context) -> None:
    ctx.out.kv(
        "Session",
        {
            "app": ctx.app.name,
            "profile": ctx.meta.get("profile", "local"),
            "workspace": ctx.meta.get("workspace") or "(none)",
            "path": " ".join(ctx.command_path) or "(root)",
            "mode": "shell-first",
        },
    )


@app.command(help="Greet someone using the preferred Argon command style")
def greet(
    ctx: argon.Context,
    name: Annotated[str, argon.Argument(help="Who to greet")],
    times: Annotated[int, argon.Option("--times", "-t", help="Repeat count", envvar="ARGON_DEMO_TIMES")] = 1,
    loud: Annotated[bool, argon.Option("--loud", help="Uppercase the greeting")] = False,
) -> str:
    message = f"Hello {name}"
    if loud:
        message = message.upper()
    for _ in range(times):
        ctx.out.text(message)
    return message


workspace = app.group("workspace", help="Workspace-oriented commands")


@workspace.callback(invoke_without_command=True)
def workspace_root(ctx: argon.Context) -> None:
    if ctx.command_path == ("workspace",):
        ctx.out.panel(
            "Workspace",
            "\n".join(
                [
                    "Use `workspace list` to inspect available workspaces.",
                    "Use `workspace use <name>` to switch context.",
                ]
            ),
        )


@workspace.command(help="Switch to a workspace")
def use(
    ctx: argon.Context,
    name: Annotated[str, argon.Argument(help="Workspace name", autocompletion=_complete_workspace)],
    profile: Annotated[
        Literal["local", "staging", "prod"],
        argon.Option("--profile", "-p", help="Execution profile", autocompletion=_complete_profile),
    ] = "local",
) -> None:
    ctx.meta["profile"] = profile
    ctx.meta["workspace"] = name
    ctx.out.success(f"Workspace {name} active on {profile}")


@workspace.command(help="List known workspaces")
def list_(ctx: argon.Context) -> None:
    ctx.out.panel("Workspaces", "\n".join(f"- {name}" for name in WORKSPACES))


tasks = app.group("task", help="Task execution flow")


@tasks.command(help="Run a named task")
def run(
    ctx: argon.Context,
    target: Annotated[str, argon.Argument(help="Task name", autocompletion=_complete_task)],
    mode: Annotated[
        Literal["fast", "full"],
        argon.Option("--mode", help="Execution mode", autocompletion=lambda prefix: ["fast", "full"]),
    ] = "fast",
    dry_run: Annotated[bool, argon.Option("--dry-run", help="Preview without executing")] = False,
) -> None:
    ctx.out.rule(f"task {target}")
    ctx.out.kv(
        "Plan",
        {
            "target": target,
            "mode": mode,
            "dry_run": dry_run,
            "profile": ctx.meta.get("profile", "local"),
        },
    )
    if dry_run:
        ctx.out.warning("Dry run only, nothing was executed.")
        return
    ctx.out.success(f"Executed {target}")


@app.command(help="Show the key Argon design patterns used in this demo")
def doctor(ctx: argon.Context) -> None:
    ctx.out.panel(
        "Patterns",
        "\n".join(
            [
                "1. Start with `app = argon.App(...)`.",
                "2. Prefer `Annotated[..., argon.Argument/Option(...)]`.",
                "3. Use `ctx.out` for all terminal output.",
                "4. Use `ctx.out.status()` and `ctx.out.progress()` for live terminal UI.",
                "5. Share the same command graph between argv and shell execution.",
                "6. Compose themes in layers against stable semantic keys.",
                "7. In active event loops, use `run_argv_async()` / `run_line_async()`.",
                "8. Tune completion UX with `ShellConfig.completion`.",
            ]
        ),
    )


@app.command(help="Wait asynchronously with a themed spinner and elapsed timer")
async def wait(
    ctx: argon.Context,
    seconds: Annotated[float, argon.Option("--seconds", "-s", help="How long to wait")] = 0.5,
) -> str:
    result = await ctx.out.awaiting(
        asyncio.sleep(seconds, result="remote task complete"),
        message="Waiting for remote task",
    )
    ctx.out.success(result)
    return result


@app.command(help="Choose spinner completion state from the awaited result")
async def probe(
    ctx: argon.Context,
    healthy: Annotated[bool, argon.Option("--healthy", help="Return a healthy result")] = False,
) -> str:
    async def check() -> str:
        await asyncio.sleep(0.05)
        return "healthy" if healthy else "degraded"

    result = await ctx.out.awaiting(
        check(),
        message="Probing service",
        final="success",
        resolve_final=lambda value: "success" if value == "healthy" else "error",
        resolve_message=lambda value: f"Probe result: {value}",
    )
    if result == "healthy":
        ctx.out.success("Service is healthy")
    else:
        ctx.out.warning("Service is degraded")
    return result


@app.command(help="Render a themed progress bar using Argon's live output surface")
def build(
    ctx: argon.Context,
    steps: Annotated[int, argon.Option("--steps", help="Number of build steps")] = 5,
) -> None:
    with ctx.out.progress() as progress:
        task_id = progress.add_task("Building release", total=steps)
        for _ in range(steps):
            time.sleep(0.02)
            progress.advance(task_id)
    ctx.out.success("Build complete")


@app.command(help="Track a sequence with Argon's progress helper")
def sync(
    ctx: argon.Context,
    items: Annotated[int, argon.Option("--items", help="Number of items to sync")] = 5,
) -> None:
    for _ in ctx.out.track(range(items), description="Syncing artifacts", total=items):
        time.sleep(0.01)
    ctx.out.success("Sync complete")


@app.command(help="Run grouped stages on a single progress line")
def pipeline(ctx: argon.Context) -> None:
    with ctx.out.stages(
        ("resolve", "build", "package", "publish"),
        description="Release pipeline",
    ) as stages:
        for stage in stages.iter():
            time.sleep(0.02)
            ctx.out.text(f"stage {stage}", style="argon.dim")
    ctx.out.success("Pipeline complete")


@app.command(help="Render concurrent async tasks on a shared progress display")
async def fanout(ctx: argon.Context) -> None:
    results = await ctx.out.gather(
        {
            "index": asyncio.sleep(0.01, result="ok"),
            "package": asyncio.sleep(0.02, result="ok"),
            "publish": asyncio.sleep(0.03, result="ok"),
        }
    )
    ctx.out.kv("Fanout", results)


@app.command(help="Finalize a progress display with command-level policies")
def rollout(
    ctx: argon.Context,
    fail: Annotated[bool, argon.Option("--fail", help="Force rollout failure")] = False,
) -> str:
    with ctx.out.progress(
        final="success",
        failed_final="error",
        final_message="Rollout completed",
        failed_final_message="Rollout failed",
    ) as progress:
        task_id = progress.add_task("Rollout", total=3)
        for _ in range(3):
            time.sleep(0.02)
            progress.advance(task_id)
        if fail:
            progress.fail("Rollout failed")
            ctx.out.warning("Rolled back changes")
            return "failed"
        progress.succeed("Rollout completed")
    ctx.out.success("Changes applied")
    return "completed"


@app.command(help="Show the nested live display guard in action")
def nested(ctx: argon.Context) -> None:
    try:
        with ctx.out.status("Outer status"):
            with ctx.out.progress():
                pass
    except argon.LiveDisplayError as exc:
        ctx.out.warning(str(exc))


def main() -> None:
    argv = sys.argv[1:]
    if not argv:
        app.run_shell()
        return
    if argv == ["shell"]:
        app.run_shell()
        return
    app.run_argv(argv)


if __name__ == "__main__":
    main()
