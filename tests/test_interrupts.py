from __future__ import annotations

import asyncio

import pytest
from rich.text import Text

import argon


def test_sync_command_keyboard_interrupt_becomes_argon_interrupted() -> None:
    app = argon.App(name="demo")

    @app.command()
    def stop() -> None:
        raise KeyboardInterrupt

    with pytest.raises(argon.Interrupted, match="Interrupted"):
        app.run_argv(["stop"])


def test_async_command_keyboard_interrupt_becomes_argon_interrupted() -> None:
    app = argon.App(name="demo")

    @app.command()
    async def stop() -> None:
        await asyncio.sleep(0)
        raise KeyboardInterrupt

    with pytest.raises(argon.Interrupted, match="Interrupted"):
        app.run_argv(["stop"])


def test_async_command_cancellation_becomes_argon_interrupted() -> None:
    app = argon.App(name="demo")

    @app.command()
    async def stop() -> None:
        await asyncio.sleep(0)
        raise asyncio.CancelledError

    async def runner() -> None:
        with pytest.raises(argon.Interrupted, match="Interrupted"):
            await app.run_argv_async(["stop"])

    asyncio.run(runner())


def test_live_display_releases_guard_after_keyboard_interrupt() -> None:
    app = argon.App(name="demo")

    @app.command()
    def stop(ctx: argon.Context) -> None:
        with ctx.output.live(Text("running")):
            raise KeyboardInterrupt

    @app.command()
    def view(ctx: argon.Context) -> str:
        with ctx.output.live(Text("ok")):
            pass
        return "released"

    with pytest.raises(argon.Interrupted):
        app.run_argv(["stop"])

    assert app.run_argv(["view"]) == "released"
