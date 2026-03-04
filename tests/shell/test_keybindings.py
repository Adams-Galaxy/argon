from __future__ import annotations

from types import SimpleNamespace

from argon.shell.ptk.keybindings import common_prefix_suffix, handle_tab, longest_common_prefix


def test_longest_common_prefix() -> None:
    assert longest_common_prefix(["alpha", "alpine", "alps"]) == "alp"


def test_common_prefix_suffix_returns_insertable_suffix() -> None:
    assert common_prefix_suffix(current="al", candidates=["alpha", "alpine"]) == "p"


def test_common_prefix_suffix_returns_none_when_no_extension() -> None:
    assert common_prefix_suffix(current="alpha", candidates=["alpha", "alpha"]) is None


class _FakeDocument:
    def __init__(self, word: str) -> None:
        self._word = word

    def get_word_before_cursor(self, WORD: bool = True) -> str:  # noqa: N803
        return self._word


class _FakeCompletion:
    def __init__(self, text: str) -> None:
        self.text = text


class _FakeCompleter:
    def __init__(self, items: list[str]) -> None:
        self.items = items

    def get_completions(self, document, event):  # type: ignore[no-untyped-def]
        return [_FakeCompletion(item) for item in self.items]


class _FakeBuffer:
    def __init__(self, *, word: str = "", items: list[str] | None = None) -> None:
        self.document = _FakeDocument(word)
        self.completer = _FakeCompleter(items or [])
        self.complete_state = None
        self.inserted: list[str] = []
        self.started = False
        self.next_calls = 0

    def insert_text(self, value: str) -> None:
        self.inserted.append(value)

    def start_completion(self, *, select_first: bool = False) -> None:
        self.started = True
        self.complete_state = object()

    def complete_next(self) -> None:
        self.next_calls += 1


def test_handle_tab_cycles_existing_completion_state() -> None:
    buffer = _FakeBuffer()
    buffer.complete_state = object()
    handle_tab(buffer, SimpleNamespace())
    assert buffer.next_calls == 1


def test_handle_tab_inserts_common_prefix_then_opens_completion() -> None:
    buffer = _FakeBuffer(word="al", items=["alpha", "alpine"])
    handle_tab(buffer, SimpleNamespace())
    assert buffer.inserted == ["p"]
    assert buffer.started is True
