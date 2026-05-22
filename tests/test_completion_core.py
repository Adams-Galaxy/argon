from __future__ import annotations

import enum
from typing import Annotated, Literal

import argon


class Profile(enum.Enum):
    local = "local"
    prod = "prod"


def _items(app: argon.App, line: str) -> list[str]:
    return [item.text for item in app.console().complete(line).items]


def _git_app() -> argon.App:
    app = argon.App(name="git")
    git = app.group("git")

    @git.command()
    def stash() -> None:
        return None

    @git.command()
    def status(
        *path: Annotated[
            str,
            argon.Argument(completion=("src", "tests")),
        ],
        branch: Annotated[
            str,
            argon.Option("--branch", "-b", completion=("main", "next")),
        ] = "main",
        format_: Annotated[
            str,
            argon.Option("--format", completion=("long", "porcelain", "short")),
        ] = "short",
    ) -> None:
        return None

    @git.command()
    def stripspace() -> None:
        return None

    @git.command()
    def switch() -> None:
        return None

    @git.command(hidden=True)
    def stage() -> None:
        return None

    return app


def test_complete_top_level_commands(demo_app: argon.App) -> None:
    result = demo_app.console().complete("gr")
    assert [item.text for item in result.items] == ["greet"]


def test_complete_group_commands_from_command_prefix() -> None:
    result = _git_app().console().complete("git st")
    assert [item.text for item in result.items] == ["stash", "status", "stripspace"]
    assert (result.replace_start, result.replace_end) == (4, 6)


def test_complete_hidden_group_commands_are_omitted() -> None:
    assert _items(_git_app(), "git sta") == ["stash", "status"]


def test_complete_nested_group_commands(demo_app: argon.App) -> None:
    result = demo_app.console().complete("users a")
    assert [item.text for item in result.items] == ["add"]


def test_complete_commands_after_group_alias(demo_app: argon.App) -> None:
    assert _items(demo_app, "u a") == ["add"]


def test_complete_hidden_groups_are_omitted() -> None:
    app = argon.App(name="demo")
    visible = app.group("visible")
    app.group("private", hidden=True)

    @visible.command()
    def ping() -> None:
        return None

    assert _items(app, "") == ["visible", "help"]


def test_complete_option_names(demo_app: argon.App) -> None:
    result = demo_app.console().complete("greet Ada --")
    texts = [item.text for item in result.items]
    assert "--times" in texts
    assert "--loud" in texts


def test_completion_replacement_range(demo_app: argon.App) -> None:
    result = demo_app.console().complete("gr")
    assert result.replace_start == 0
    assert result.replace_end == 2


def test_completion_includes_root_builtins(demo_app: argon.App) -> None:
    demo_app.version = "1.0.0"
    result = demo_app.console().complete("ve")
    assert [item.text for item in result.items] == ["version"]


def test_completion_uses_option_value_autocompletion() -> None:
    app = argon.App(name="demo")

    @app.command()
    def run(
        target: Annotated[str, argon.Argument()],
        mode: Annotated[
            str,
            argon.Option("--mode", completion=lambda prefix: ["fast", "full"]),
        ] = "fast",
    ) -> None:
        return None

    result = app.console().complete("run build --mode fa")
    assert "fast" in [item.text for item in result.items]
    assert "full" not in [item.text for item in result.items]


def test_completion_accepts_static_completion_items() -> None:
    app = argon.App(name="demo")

    @app.command()
    def deploy(
        profile: Annotated[
            str,
            argon.Argument(
                completion=(
                    argon.CompletionItem("prod", meta="Production"),
                    argon.CompletionItem("preview", display="preview build"),
                )
            ),
        ],
    ) -> None:
        return None

    result = app.console().complete("deploy pr")
    assert result.items == [
        argon.CompletionItem("prod", meta="Production"),
        argon.CompletionItem("preview", display="preview build"),
    ]


def test_completion_treats_static_string_as_one_item() -> None:
    app = argon.App(name="demo")

    @app.command()
    def deploy(
        profile: Annotated[str, argon.Argument(completion="prod")],
    ) -> None:
        return None

    assert _items(app, "deploy p") == ["prod"]


def test_completion_infers_literal_option_values() -> None:
    app = argon.App(name="demo")

    @app.command()
    def release(
        channel: Annotated[
            Literal["stable", "preview"],
            argon.Option("--channel"),
        ] = "stable",
    ) -> None:
        return None

    assert _items(app, "release --channel p") == ["preview"]


def test_completion_infers_string_enum_argument_values() -> None:
    app = argon.App(name="demo")

    @app.command()
    def deploy(profile: Annotated[Profile, argon.Argument()]) -> None:
        return None

    assert _items(app, "deploy p") == ["prod"]


def test_completion_stops_fixed_argument_suggestions_after_argument_is_consumed() -> None:
    app = argon.App(name="demo")

    @app.command()
    def release(
        service: Annotated[
            str,
            argon.Argument(completion=lambda prefix: ["api", "worker"]),
        ],
    ) -> None:
        return None

    result = app.console().complete("release api ")
    assert [item.text for item in result.items] == []


def test_completion_moves_to_next_positional_argument_after_options() -> None:
    app = argon.App(name="demo")

    @app.command()
    def release(
        service: Annotated[
            str,
            argon.Argument(completion=lambda prefix: ["api", "worker"]),
        ],
        region: Annotated[
            str,
            argon.Argument(completion=lambda prefix: ["ap-southeast", "us-east"]),
        ],
        channel: Annotated[
            str,
            argon.Option("--channel", completion=lambda prefix: ["stable"]),
        ] = "stable",
    ) -> None:
        return None

    result = app.console().complete("release api --channel stable ")
    assert [item.text for item in result.items] == ["ap-southeast", "us-east"]


def test_completion_option_policy_short_prefers_short_when_available() -> None:
    app = argon.App(
        name="demo",
        shell_config=argon.ShellConfig(
            completion=argon.CompletionConfig(option_display="short"),
        ),
    )

    @app.command()
    def greet(
        name: Annotated[str, argon.Argument()],
        times: Annotated[int, argon.Option("--times", "-t")] = 1,
        loud: Annotated[bool, argon.Option("--loud")] = False,
    ) -> None:
        return None

    result = app.console().complete("greet Ada -")
    texts = [item.text for item in result.items]
    assert "-t" in texts
    assert "--times" not in texts
    assert "--loud" in texts


def test_completion_option_policy_all_returns_all_decls() -> None:
    app = argon.App(
        name="demo",
        shell_config=argon.ShellConfig(
            completion=argon.CompletionConfig(option_display="all"),
        ),
    )

    @app.command()
    def greet(
        name: Annotated[str, argon.Argument()],
        times: Annotated[int, argon.Option("--times", "-t")] = 1,
    ) -> None:
        return None

    result = app.console().complete("greet Ada -")
    texts = [item.text for item in result.items]
    assert "--times" in texts
    assert "-t" in texts


def test_completion_option_policy_none_suppresses_option_completions() -> None:
    app = argon.App(
        name="demo",
        shell_config=argon.ShellConfig(
            completion=argon.CompletionConfig(option_display="none"),
        ),
    )

    @app.command()
    def greet(
        name: Annotated[str, argon.Argument()],
        times: Annotated[int, argon.Option("--times", "-t")] = 1,
    ) -> None:
        return None

    result = app.console().complete("greet Ada --")
    assert [item.text for item in result.items] == []


def test_completion_suggests_option_names_after_positional_arguments() -> None:
    assert _items(_git_app(), "git status src --") == ["--branch", "--format"]


def test_completion_uses_short_option_value_completion() -> None:
    assert _items(_git_app(), "git status -b n") == ["next"]


def test_completion_uses_inline_long_option_value_completion() -> None:
    result = _git_app().console().complete("git status --format=p")
    assert [item.text for item in result.items] == ["porcelain"]
    assert (result.replace_start, result.replace_end) == (20, 21)


def test_completion_keeps_variadic_argument_completion_active() -> None:
    assert _items(_git_app(), "git status src t") == ["tests"]


def test_completion_returns_no_items_for_unterminated_quotes(demo_app: argon.App) -> None:
    result = demo_app.console().complete('greet "Ada')
    assert result.items == []
