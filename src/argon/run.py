from __future__ import annotations

import sys
from typing import Any

from .app import App


def run(
    fn: Any,
    *,
    name: str | None = None,
    help: str | None = None,
    version: str | None = None,
) -> object:
    """Run a single-function Argon app.

    @param fn Callable to expose as the app's primary command.
    @param name Optional app name.
    @param help Optional help text for app and command.
    @param version Optional app version string.
    @returns Command callback result.
    """

    app = App(name=name or getattr(fn, "__name__", "app"), help=help, version=version)
    command_name = getattr(fn, "__name__", "main").replace("_", "-")
    app.command(name=command_name, help=help)(fn)
    argv = list(sys.argv[1:])
    if not argv or argv[0] != command_name:
        argv = [command_name, *argv]
    return app.run_argv(argv)
