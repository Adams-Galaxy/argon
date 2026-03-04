from __future__ import annotations

from typing import Annotated

import pytest

import argon


@pytest.fixture()
def demo_app() -> argon.App:
    app = argon.App(name="demo", help="Demo application", no_args_is_help=True)

    @app.command(help="Greet someone", aliases=("hello",))
    def greet(
        ctx: argon.Context,
        name: Annotated[str, argon.Argument(help="Who to greet")],
        times: Annotated[int, argon.Option("--times", "-t", help="Repeat count")] = 1,
        loud: bool = False,
    ) -> str:
        message = f"Hello {name}"
        if loud:
            message = message.upper()
        for _ in range(times):
            ctx.out.text(message)
        return message

    users = app.group("users", help="User commands", aliases=("u",))

    @users.command(help="Add a user")
    def add(name: str) -> str:
        return f"added:{name}"

    return app
