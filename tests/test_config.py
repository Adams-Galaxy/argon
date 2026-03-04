from __future__ import annotations

from pathlib import Path

import argon


def test_app_config_loads_demo_file() -> None:
    config = argon.AppConfig.from_file(Path("examples/demo.config.json"))
    assert config.theme is not None
    assert config.shell.history_path == ".argon-demo-history"
    assert config.shell.live.awaiting_final == "clear"
    assert config.shell.live.success_symbol == "✔"
    assert config.shell.live.error_symbol == "✖"
    assert "argon.shell.command" in config.theme.resolved_styles()


def test_shell_config_can_merge_prompt_tokens() -> None:
    config = argon.ShellConfig.from_mapping(
        {
            "prompt": {
                "template": "{app.name}> ",
                "tokens": {"static": "value"},
            }
        }
    )
    merged = config.with_prompt_tokens({"dynamic": "other"})
    assert merged.prompt.tokens["static"] == "value"
    assert merged.prompt.tokens["dynamic"] == "other"
