from __future__ import annotations

from pathlib import Path

import argon
import pytest


def test_app_config_loads_demo_file() -> None:
    config = argon.AppConfig.from_file(Path("examples/demo.config.json"))
    assert config.schema_version == 1
    assert config.theme is not None
    assert config.shell.history_path == ".argon-demo-history"
    assert config.shell.completion.option_display == "long"
    assert config.shell.completion.show_help_tooltips is False
    assert config.shell.live.awaiting_final == "clear"
    assert config.shell.live.success_symbol == "✔"
    assert config.shell.live.error_symbol == "✖"
    assert config.shell.live.progress_final == "success"
    assert config.shell.live.progress_failed_final == "error"
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


def test_app_config_defaults_schema_version_for_legacy_payload() -> None:
    config = argon.AppConfig.from_mapping({"shell": {"history": True}})
    assert config.schema_version == 1


def test_app_config_rejects_unsupported_schema_version() -> None:
    with pytest.raises(ValueError):
        argon.AppConfig.from_mapping({"schema_version": 2})


def test_shell_config_rejects_invalid_completion_policy() -> None:
    with pytest.raises(ValueError):
        argon.ShellConfig.from_mapping({"completion": {"option_display": "invalid"}})


def test_app_config_round_trip_from_mapping() -> None:
    loaded = argon.AppConfig.from_file(Path("examples/demo.config.json"))
    round_trip = argon.AppConfig.from_mapping(loaded.model_dump(mode="python"))
    assert round_trip.schema_version == loaded.schema_version
    assert round_trip.shell.history_path == loaded.shell.history_path
    assert round_trip.shell.completion.option_display == loaded.shell.completion.option_display
