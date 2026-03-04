from __future__ import annotations

from pathlib import Path


def build_history(path: str | None = None):
    from prompt_toolkit.history import FileHistory, InMemoryHistory

    if path is None:
        return InMemoryHistory()
    location = Path(path)
    location.parent.mkdir(parents=True, exist_ok=True)
    return FileHistory(str(location))
