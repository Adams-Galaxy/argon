from __future__ import annotations

import inspect
import re
from pathlib import Path

import argon


def test_public_docs_tree_exists() -> None:
    required = [
        "docs/index.md",
        "docs/getting-started.md",
        "docs/authoring.md",
        "docs/shell.md",
        "docs/output-live.md",
        "docs/configuration.md",
        "docs/async.md",
        "docs/theming.md",
        "docs/api-reference.md",
        "docs/migration-v1.md",
        "docs/release-checklist.md",
    ]
    for rel in required:
        assert Path(rel).exists(), rel


def test_readme_docs_links_exist() -> None:
    readme = Path("README.md").read_text()
    links = re.findall(r"\[[^\]]+\]\(([^)]+)\)", readme)
    docs_links = [link for link in links if link.startswith("docs/")]
    for link in docs_links:
        assert Path(link).exists(), link


def test_public_exports_have_docstrings() -> None:
    for name in argon.__all__:
        obj = getattr(argon, name)
        assert inspect.getdoc(obj), name


def test_public_api_docstrings_use_doxygen_tags() -> None:
    targets = [
        argon.App.command,
        argon.App.group,
        argon.App.callback,
        argon.App.add_typer,
        argon.App.console,
        argon.App.shell,
        argon.App.run_argv,
        argon.App.run_argv_async,
        argon.App.run_line,
        argon.App.run_line_async,
        argon.App.run_shell,
        argon.Console.execute_argv,
        argon.Console.execute_argv_async,
        argon.Console.execute_line,
        argon.Console.execute_line_async,
        argon.Console.complete,
        argon.Console.highlight,
        argon.Console.help,
        argon.run,
        argon.Option,
        argon.Argument,
    ]
    for target in targets:
        doc = inspect.getdoc(target)
        assert doc is not None
        params = [param for param in inspect.signature(target).parameters.values() if param.name != "self"]
        if params:
            assert "@param" in doc
