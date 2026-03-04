from __future__ import annotations

import ast
from pathlib import Path


def test_prompt_toolkit_imports_are_isolated() -> None:
    root = Path("src/argon")
    violations: list[str] = []
    for path in root.rglob("*.py"):
        if "shell/ptk" in path.as_posix():
            continue
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                names = [node.module or ""]
            else:
                continue
            if any(name.startswith("prompt_toolkit") for name in names):
                violations.append(path.as_posix())
    assert violations == []
