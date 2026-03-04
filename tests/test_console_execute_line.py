from __future__ import annotations

import argon


def test_line_execution_matches_argv(demo_app: argon.App, capsys) -> None:
    result = demo_app.run_line('greet "Ada Lovelace" --times 2')
    assert result == "Hello Ada Lovelace"
    out = capsys.readouterr().out
    assert out.count("Hello Ada Lovelace") == 2


def test_line_help_request_renders_help(demo_app: argon.App, capsys) -> None:
    demo_app.run_line("greet --help")
    out = capsys.readouterr().out
    assert "Repeat count" in out
