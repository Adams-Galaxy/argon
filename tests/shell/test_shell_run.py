from __future__ import annotations

import argon


def test_shell_run_uses_ptk_adapter(monkeypatch, demo_app: argon.App) -> None:
    called = {"value": False}

    def fake_run_ptk_repl(console, session, *, mouse_support: bool = False) -> int:
        called["value"] = True
        assert console is demo_app.console()
        assert session.prompt == "{app.name}> "
        assert console.rich_console.is_terminal is True
        return 0

    monkeypatch.setattr("argon.shell.ptk.repl.run_ptk_repl", fake_run_ptk_repl)
    shell = argon.Shell(demo_app.console())
    assert shell.run() == 0
    assert called["value"] is True


def test_shell_carries_history_path(demo_app: argon.App) -> None:
    shell = argon.Shell(demo_app.console(), history_path=".demo-history")
    assert shell.session.history_path is not None
    assert shell.session.history_path.name == ".demo-history"


def test_shell_uses_app_shell_config_defaults() -> None:
    app = argon.App(
        name="demo",
        shell_config=argon.ShellConfig(
            history_path=".argon-history",
            prompt=argon.PromptConfig(template="{app.name} {system.time}> "),
        ),
    )
    shell = argon.Shell(app.console())
    assert shell.session.prompt == "{app.name} {system.time}> "
    assert shell.session.history_path is not None
    assert shell.session.history_path.name == ".argon-history"
