from __future__ import annotations

import asyncio

import argon
import pytest


def test_async_api_executes_command_in_running_loop() -> None:
    app = argon.App(name="demo")

    @app.command()
    async def wait() -> str:
        await asyncio.sleep(0)
        return "done"

    async def runner() -> str:
        return await app.run_argv_async(["wait"])

    assert asyncio.run(runner()) == "done"


def test_async_line_api_executes_command_in_running_loop() -> None:
    app = argon.App(name="demo")

    @app.command()
    async def wait() -> str:
        await asyncio.sleep(0)
        return "done"

    async def runner() -> str:
        return await app.run_line_async("wait")

    assert asyncio.run(runner()) == "done"


def test_sync_api_raises_in_running_loop_for_async_commands() -> None:
    app = argon.App(name="demo")

    @app.command()
    async def wait() -> str:
        await asyncio.sleep(0)
        return "done"

    async def runner() -> None:
        with pytest.raises(argon.UsageError):
            app.run_argv(["wait"])

    asyncio.run(runner())


def test_console_async_api_executes_command() -> None:
    app = argon.App(name="demo")

    @app.command()
    async def wait() -> str:
        await asyncio.sleep(0)
        return "done"

    async def runner() -> str:
        return await app.console().execute_argv_async(["wait"])

    assert asyncio.run(runner()) == "done"
