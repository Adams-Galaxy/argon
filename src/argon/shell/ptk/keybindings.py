from __future__ import annotations


def longest_common_prefix(items: list[str]) -> str:
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    start = min(items)
    end = max(items)
    i = 0
    while i < min(len(start), len(end)) and start[i] == end[i]:
        i += 1
    return start[:i]


def common_prefix_suffix(*, current: str, candidates: list[str]) -> str | None:
    matches = [candidate for candidate in candidates if candidate.startswith(current)]
    if len(matches) <= 1:
        return None
    prefix = longest_common_prefix(matches)
    if len(prefix) <= len(current):
        return None
    return prefix[len(current) :]


def handle_tab(buffer, event) -> None:  # type: ignore[no-untyped-def]
    if buffer.complete_state is not None:
        buffer.complete_next()
        return

    document = buffer.document
    word = document.get_word_before_cursor(WORD=True)
    completer = buffer.completer
    if completer is not None:
        completions = list(completer.get_completions(document, event))
        suffix = common_prefix_suffix(
            current=word,
            candidates=[completion.text for completion in completions],
        )
        if suffix:
            buffer.insert_text(suffix)
            try:
                buffer.start_completion(select_first=False)
            except Exception:  # noqa: BLE001
                pass
            return
    buffer.start_completion(select_first=False)


def build_key_bindings():
    from prompt_toolkit.key_binding import KeyBindings

    kb = KeyBindings()

    @kb.add("tab")
    def _(event):  # type: ignore[no-untyped-def]
        try:
            handle_tab(event.current_buffer, event)
        except Exception:  # noqa: BLE001
            event.current_buffer.complete_next()

    @kb.add("s-tab")
    def _(event):  # type: ignore[no-untyped-def]
        buffer = event.current_buffer
        if buffer.complete_state is not None:
            buffer.complete_previous()
            return
        try:
            buffer.start_completion(select_first=False)
        except Exception:  # noqa: BLE001
            pass

    return kb
