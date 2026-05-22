from __future__ import annotations

import json

import pytest

import argon

APP_CONFIG_PAYLOAD = {
    "schema_version": 1,
    "shell": {
        "history_path": ".argon-history",
        "completion": {
            "option_display": "long",
            "show_help_tooltips": False,
        },
        "live": {
            "success_symbol": "✔",
            "error_symbol": "✖",
            "progress_final": "success",
            "progress_failed_final": "error",
        },
    },
    "theme": {
        "base": {
            "name": "loaded",
            "styles": {
                "argon.shell.command": "bold bright_yellow",
            },
        },
    },
}


def test_app_config_loads_file(tmp_path) -> None:
    path = tmp_path / "app.config.json"
    path.write_text(json.dumps(APP_CONFIG_PAYLOAD))

    config = argon.AppConfig.from_file(path)
    assert config.schema_version == 1
    assert config.theme is not None
    assert config.shell.history_path == ".argon-history"
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
    assert config.shell.usage_error_display == "help"


def test_app_config_rejects_unsupported_schema_version() -> None:
    with pytest.raises(ValueError):
        argon.AppConfig.from_mapping({"schema_version": 2})


def test_shell_config_rejects_invalid_completion_policy() -> None:
    with pytest.raises(ValueError):
        argon.ShellConfig.from_mapping({"completion": {"option_display": "invalid"}})


def test_shell_config_rejects_invalid_usage_error_display() -> None:
    with pytest.raises(ValueError):
        argon.ShellConfig.from_mapping({"usage_error_display": "invalid"})


def test_app_config_round_trip_from_mapping() -> None:
    loaded = argon.AppConfig.from_mapping(APP_CONFIG_PAYLOAD)
    round_trip = argon.AppConfig.from_mapping(loaded.model_dump(mode="python"))
    assert round_trip.schema_version == loaded.schema_version
    assert round_trip.shell.history_path == loaded.shell.history_path
    assert round_trip.shell.completion.option_display == loaded.shell.completion.option_display
