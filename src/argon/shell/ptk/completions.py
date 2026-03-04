from __future__ import annotations


def make_completer(console):
    from prompt_toolkit.completion import Completer, Completion

    show_help_tooltips = bool(console.app.shell_config.completion.show_help_tooltips)

    class ArgonCompleter(Completer):
        def get_completions(self, document, complete_event):  # type: ignore[override]
            result = console.complete(document.text_before_cursor, document.cursor_position)
            start_position = result.replace_start - result.replace_end
            for item in result.items:
                yield Completion(
                    item.text,
                    start_position=start_position,
                    display=item.display or item.text,
                    display_meta=item.meta if show_help_tooltips else "",
                )

    return ArgonCompleter()
