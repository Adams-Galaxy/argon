from __future__ import annotations

import asyncio
from typing import Annotated, Literal

from rich.text import Text

import argon
from argon import App, Argument, Context, Option

WORKSPACES = ("core", "design", "infra", "labs")
SERVICES = ("api", "worker", "web")

DEMO_THEME = argon.default_theme().with_overrides(
    "demo",
    {
        "argon.selection.active": "bold black on bright_yellow",
        "argon.shell.command": "bold bright_yellow",
        "argon.shell.option": "bright_cyan",
        "argon.prompt.context": "bright_cyan",
        "argon.prompt.symbol": "bold bright_white",
        "argon.live.spinner": "bright_yellow",
        "argon.progress.bar": "bright_cyan",
        "argon.ptk.menu.current": "bold black on bright_yellow",
    },
)


def _prompt_profile(formatter: object | None) -> Text:
    if formatter is None:
        return Text()
    profile = formatter.resolve_token("session.profile") or "local"
    if not profile:
        return Text()
    return Text(f" [{profile}]", style="argon.prompt.context")


def _prompt_workspace(formatter: object | None) -> Text:
    if formatter is None:
        return Text()
    workspace = formatter.resolve_token("session.workspace")
    if not workspace:
        return Text()
    return Text(f" {workspace}", style="argon.shell.command")


DEMO_SHELL_CONFIG = argon.ShellConfig(
    history=True,
    history_path=".argon-demo-history",
    mouse_support=False,
    completion=argon.CompletionConfig(
        option_display="long",
        show_help_tooltips=False,
    ),
    live=argon.LiveConfig(
        success_symbol="✔",
        error_symbol="✖",
        progress_final="success",
    ),
    prompt=argon.PromptConfig(
        template=(
            "[argon.prompt.brand]{app.name}[/argon.prompt.brand]"
            "{session.workspace_badge}{session.profile_badge}\n"
            "[argon.prompt.symbol]>[/argon.prompt.symbol] "
        ),
        tokens={
            "session.workspace_badge": _prompt_workspace,
            "session.profile_badge": _prompt_profile,
        },
    ),
)


app = App(
    name="argon-demo",
    help="Shell-first reference app showing the intended Argon authoring flow.",
    version="1.0.2",
    theme=DEMO_THEME,
    no_args_is_help=True,
    shell_config=DEMO_SHELL_CONFIG,
)


@app.callback()
def root(ctx: Context) -> None:
    ctx.meta.setdefault("profile", "local")
    ctx.meta.setdefault("workspace", "")


@app.command(help="Show the current shell session state")
def status(ctx: Context) -> None:
    ctx.output.kv(
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
    ctx: Context,
    name: Annotated[str, Argument(help="Who to greet")],
    times: Annotated[
        int, Option("--times", "-t", help="Repeat count", envvar="ARGON_DEMO_TIMES")
    ] = 1,
    loud: Annotated[bool, Option("--loud", help="Uppercase the greeting")] = False,
) -> str:
    message = f"Hello {name}"
    if loud:
        message = message.upper()
    for _ in range(times):
        ctx.output.text(message)
    return message


workspace = app.group("workspace", help="Workspace-oriented commands")


@workspace.callback(invoke_without_command=True)
def workspace_root(ctx: Context) -> None:
    if ctx.command_path == ("workspace",):
        ctx.output.text("Use `workspace use <name>` to set shell context.")


@workspace.command(help="Switch to a workspace")
def use(
    ctx: Context,
    name: Annotated[str, Argument(help="Workspace name", completion=WORKSPACES)],
    profile: Annotated[
        Literal["local", "staging", "prod"],
        Option("--profile", "-p", help="Execution profile"),
    ] = "local",
) -> None:
    ctx.meta["profile"] = profile
    ctx.meta["workspace"] = name
    ctx.output.success(f"Workspace {name} active on {profile}")


@app.command(help="Release one service with concurrent async preparation")
async def release(
    ctx: Context,
    service: Annotated[str, Argument(help="Service name", completion=SERVICES)],
    channel: Annotated[
        Literal["stable", "preview"],
        Option("--channel", "-c", help="Release channel"),
    ] = "stable",
) -> dict[str, str]:
    results = await ctx.output.gather(
        {
            "build": asyncio.sleep(0.02, result="ready"),
            "package": asyncio.sleep(0.03, result="ready"),
        }
    )
    results["publish"] = await ctx.output.awaiting(
        asyncio.sleep(0.02, result="done"),
        message=f"Publishing {service}",
    )
    ctx.output.kv(
        "Release",
        {
            "service": service,
            "channel": channel,
            "workspace": ctx.meta.get("workspace") or "(none)",
            **results,
        },
    )
    return results


@app.command(help="Show a key-interruptible live renderable")
async def monitor(
    ctx: Context,
    once: Annotated[bool, Option("--once", help="Render one frame and exit")] = False,
) -> str:
    with ctx.output.live(Text("monitor: starting", style="argon.live.message")) as live:
        live.update(Text("monitor: ready", style="argon.live.message"), refresh=True)
        if once:
            return "ready"

        key = await ctx.input.wait_key_async({"q", " "})
        state = "stopped by space" if key == " " else f"stopped by {key}"
        live.update(Text(f"monitor: {state}", style="argon.live.message"), refresh=True)
        return state


def main() -> None:
    app()


if __name__ == "__main__":
    main()
