from __future__ import annotations

from typing import Literal

import pytest

import argon


def test_basic_command_execution(demo_app: argon.App, capsys) -> None:
    result = demo_app.run_argv(["greet", "Ada", "--times", "2"])
    assert result == "Hello Ada"
    out = capsys.readouterr().out
    assert out.count("Hello Ada") == 2


def test_alias_and_nested_group_execution(demo_app: argon.App) -> None:
    assert demo_app.run_argv(["hello", "Ada"]) == "Hello Ada"
    assert demo_app.run_argv(["users", "add", "Ada"]) == "added:Ada"


def test_missing_argument_raises_usage_error(demo_app: argon.App) -> None:
    with pytest.raises(argon.UsageError):
        demo_app.run_argv(["greet"])


def test_bool_flag_parsing(demo_app: argon.App, capsys) -> None:
    result = demo_app.run_argv(["greet", "Ada", "--loud"])
    assert result == "HELLO ADA"
    assert "HELLO ADA" in capsys.readouterr().out


def test_unknown_option_raises_usage_error(demo_app: argon.App) -> None:
    with pytest.raises(argon.UsageError):
        demo_app.run_argv(["greet", "Ada", "--bogus"])


def test_version_builtin_renders(demo_app: argon.App, capsys) -> None:
    demo_app.version = "1.2.3"
    assert demo_app.run_argv(["version"]) == "demo 1.2.3"
    assert "demo 1.2.3" in capsys.readouterr().out


def test_help_builtin_renders_command_help(demo_app: argon.App, capsys) -> None:
    demo_app.run_argv(["help", "greet"])
    out = capsys.readouterr().out
    assert "Repeat count" in out


def test_root_callback_runs_before_command(capsys) -> None:
    app = argon.App(name="demo")

    @app.callback()
    def root(ctx: argon.Context) -> None:
        ctx.meta["profile"] = "local"

    @app.command()
    def show(ctx: argon.Context) -> str:
        ctx.out.text(ctx.meta["profile"])
        return ctx.meta["profile"]

    assert app.run_argv(["show"]) == "local"
    assert "local" in capsys.readouterr().out


def test_group_callback_invoke_without_command(capsys) -> None:
    app = argon.App(name="demo")
    workspace = app.group("workspace")

    @workspace.callback(invoke_without_command=True)
    def root(ctx: argon.Context) -> str:
        ctx.out.text("workspace root")
        return "workspace root"

    assert app.run_argv(["workspace"]) == "workspace root"
    assert "workspace root" in capsys.readouterr().out


def test_required_option_raises_usage_error() -> None:
    app = argon.App(name="demo")

    @app.command()
    def deploy(profile: str = argon.Option("--profile", required=True)) -> str:
        return profile

    with pytest.raises(argon.UsageError):
        app.run_argv(["deploy"])


def test_envvar_supplies_missing_option(monkeypatch) -> None:
    monkeypatch.setenv("APP_PROFILE", "staging")
    app = argon.App(name="demo")

    @app.command()
    def deploy(profile: str = argon.Option("--profile", envvar="APP_PROFILE")) -> str:
        return profile

    assert app.run_argv(["deploy"]) == "staging"


def test_envvar_supplies_missing_argument(monkeypatch) -> None:
    monkeypatch.setenv("APP_NAME", "Ada")
    app = argon.App(name="demo")

    @app.command()
    def greet(name: str = argon.Argument(envvar="APP_NAME")) -> str:
        return name

    assert app.run_argv(["greet"]) == "Ada"


def test_literal_option_validation() -> None:
    app = argon.App(name="demo")

    @app.command()
    def run(mode: Literal["fast", "full"] = argon.Option("--mode")) -> str:
        return mode

    assert app.run_argv(["run", "--mode", "fast"]) == "fast"
    with pytest.raises(argon.BadParameter):
        app.run_argv(["run", "--mode", "slow"])
