# Contributing to Argon

Thanks for your interest in improving Argon! This document outlines the basic workflow for proposing changes.

## Development environment

1. Create and activate a Python 3.10+ virtual environment.
2. Install the project in editable mode along with dev dependencies:
   ```bash
   pip install -e .[dev]
   ```
3. Install the pre-commit tooling you prefer (e.g., ruff, mypy) so issues are caught early.

## Making changes

- Keep pull requests focused and well scoped. Use descriptive branch names.
- Update or add tests for every behavior change.
- Run the full check pipeline locally before opening a pull request:
  ```bash
  pytest
  ruff check .
  mypy argon
  ```
- Update documentation, examples, and the changelog when public behavior changes.

## Code style & guidelines

- The codebase targets Python 3.10+ and uses type hints throughout.
- Follow the existing formatting conventions (Black-compatible, 4-space indents).
- Prefer small, composable functions with docstrings when behavior is non-obvious.

## Submitting a pull request

1. Fork the repository and push your branch.
2. Ensure your branch has a descriptive summary and references any related issues.
3. Open a pull request describing the motivation, design decisions, and testing performed.
4. Be responsive to review feedback; small follow-up commits are encouraged.

Thank you for helping make Argon better!
