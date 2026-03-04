from __future__ import annotations

import asyncio

import argon


def test_context_output_methods_render(capsys) -> None:
    app = argon.App(name="demo")

    @app.command()
    def show(ctx: argon.Context) -> None:
        ctx.out.text("hello")
        ctx.out.success("ok")
        ctx.out.warning("warn")
        ctx.out.error("err")
        ctx.out.kv("Info", {"name": "Ada"})

    app.run_argv(["show"])
    out = capsys.readouterr().out
    assert "hello" in out
    assert "ok" in out
    assert "warn" in out
    assert "err" in out
    assert "name: Ada" in out


def test_context_forward_and_invoke() -> None:
    app = argon.App(name="demo")

    def helper(ctx: argon.Context, name: str) -> str:
        return f"helper:{name}"

    @app.command()
    def greet(ctx: argon.Context, name: str) -> tuple[str, str]:
        return ctx.invoke(helper, name=name), ctx.forward(helper)

    assert app.run_argv(["greet", "Ada"]) == ("helper:Ada", "helper:Ada")


def test_async_command_can_use_awaiting(capsys) -> None:
    app = argon.App(name="demo")

    @app.command()
    async def wait(ctx: argon.Context) -> str:
        result = await ctx.out.awaiting(
            asyncio.sleep(0, result="done"),
            message="Waiting",
        )
        ctx.out.success(result)
        return result

    assert app.run_argv(["wait"]) == "done"
    out = capsys.readouterr().out
    assert "done" in out


def test_progress_and_track_helpers_render(capsys) -> None:
    app = argon.App(name="demo")

    @app.command()
    def work(ctx: argon.Context) -> None:
        with ctx.out.progress() as progress:
            task_id = progress.add_task("Work", total=2)
            progress.advance(task_id)
            progress.advance(task_id)
        for _ in ctx.out.track(range(2), description="Track", total=2):
            pass

    app.run_argv(["work"])
    out = capsys.readouterr().out
    assert "Work" in out
    assert "Track" in out


def test_status_finish_modes_render_sensible_final_state(capsys) -> None:
    app = argon.App(name="demo")

    @app.command()
    def show(ctx: argon.Context) -> None:
        with ctx.out.status("Done", final="success"):
            pass

    app.run_argv(["show"])
    out = capsys.readouterr().out
    assert "Done" in out
    assert "✓" in out


def test_status_can_be_finished_dynamically_from_result(capsys) -> None:
    app = argon.App(name="demo")

    @app.command()
    async def probe(ctx: argon.Context, healthy: bool = False) -> str:
        result = await ctx.out.awaiting(
            asyncio.sleep(0, result="healthy" if healthy else "degraded"),
            message="Probe",
            final="success",
            resolve_final=lambda value: "success" if value == "healthy" else "error",
        )
        return result

    degraded = app.run_argv(["probe"])
    healthy = app.run_argv(["probe", "--healthy"])
    out = capsys.readouterr().out
    assert degraded == "degraded"
    assert healthy == "healthy"
    assert "✗" in out
    assert "✓" in out


def test_awaiting_can_replace_final_message(capsys) -> None:
    app = argon.App(name="demo")

    @app.command()
    async def probe(ctx: argon.Context) -> str:
        return await ctx.out.awaiting(
            asyncio.sleep(0, result="healthy"),
            message="Probe",
            final="success",
            resolve_message=lambda value: f"Probe result: {value}",
        )

    result = app.run_argv(["probe"])
    out = capsys.readouterr().out
    assert result == "healthy"
    assert "Probe result: healthy" in out


def test_nested_live_displays_raise_guard_error() -> None:
    app = argon.App(name="demo")

    @app.command()
    def nested(ctx: argon.Context) -> str:
        with ctx.out.status("Outer"):
            try:
                with ctx.out.progress():
                    pass
            except argon.LiveDisplayError as exc:
                return str(exc)
        return "no error"

    message = app.run_argv(["nested"])
    assert message == "Another live display is already active"


def test_stages_and_gather_helpers_render(capsys) -> None:
    app = argon.App(name="demo")

    @app.command()
    async def orchestration(ctx: argon.Context) -> dict[str, str]:
        with ctx.out.stages(("resolve", "publish"), description="Pipeline") as stages:
            for _ in stages.iter():
                pass
        result = await ctx.out.gather(
            {
                "alpha": asyncio.sleep(0, result="ok"),
                "beta": asyncio.sleep(0, result="ok"),
            }
        )
        ctx.out.kv("Gather", result)
        return result

    result = app.run_argv(["orchestration"])
    out = capsys.readouterr().out
    assert result == {"alpha": "ok", "beta": "ok"}
    assert "Pipeline" in out
    assert "alpha" in out
    assert "beta" in out


def test_progress_uses_shell_live_defaults(capsys) -> None:
    app = argon.App(
        name="demo",
        shell_config=argon.ShellConfig(
            live=argon.LiveConfig(progress_final="success", success_symbol="✔"),
        ),
    )

    @app.command()
    def work(ctx: argon.Context) -> None:
        with ctx.out.progress() as progress:
            task_id = progress.add_task("Work", total=1)
            progress.advance(task_id)

    app.run_argv(["work"])
    out = capsys.readouterr().out
    assert "Work" in out
    assert "✔" in out


def test_progress_can_finish_dynamically_with_message(capsys) -> None:
    app = argon.App(name="demo")

    @app.command()
    def rollout(ctx: argon.Context, fail: bool = False) -> str:
        with ctx.out.progress(final="success", failed_final="error") as progress:
            task_id = progress.add_task("Rollout", total=1)
            progress.advance(task_id)
            if fail:
                progress.fail("Rollout failed")
                return "failed"
            progress.succeed("Rollout complete")
            return "completed"

    assert app.run_argv(["rollout", "--fail"]) == "failed"
    assert app.run_argv(["rollout"]) == "completed"
    out = capsys.readouterr().out
    assert "Rollout failed" in out
    assert "Rollout complete" in out
    assert "✗" in out
    assert "✓" in out
