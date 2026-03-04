from __future__ import annotations

from prompt_toolkit.document import Document

from argon.shell.ptk.completions import make_completer


def test_ptk_completer_adapts_console_completion(demo_app) -> None:
    completer = make_completer(demo_app.console())
    doc = Document(text="gr", cursor_position=2)
    texts = [item.text for item in completer.get_completions(doc, None)]  # type: ignore[arg-type]
    assert "greet" in texts
