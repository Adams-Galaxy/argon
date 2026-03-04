from __future__ import annotations

from prompt_toolkit.document import Document

from argon.shell.ptk.lexer import make_lexer


def test_ptk_lexer_adapts_spans(demo_app) -> None:
    lexer = make_lexer(demo_app.console())
    get_line = lexer.lex_document(Document(text="greet Ada", cursor_position=9))
    segments = get_line(0)
    assert any("class:argon.command" in style for style, _ in segments)
