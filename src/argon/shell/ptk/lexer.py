from __future__ import annotations


def make_lexer(console):
    from prompt_toolkit.lexers import Lexer

    class ArgonLexer(Lexer):
        def lex_document(self, document):  # type: ignore[override]
            text = document.text

            def get_line(_lineno: int):
                spans = console.highlight(text)
                segments: list[tuple[str, str]] = []
                for span in spans:
                    fragment = text[span.start : span.end]
                    if not fragment:
                        continue
                    style = " ".join(f"class:{name}" for name in span.styles if name)
                    if segments and segments[-1][0] == style:
                        segments[-1] = (segments[-1][0], segments[-1][1] + fragment)
                    else:
                        segments.append((style, fragment))
                return segments or [("", text)]

            return get_line

    return ArgonLexer()
