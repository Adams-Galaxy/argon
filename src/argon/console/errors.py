from __future__ import annotations


class ArgonError(Exception):
    """Base error for Argon."""


class UsageError(ArgonError):
    """Raised for CLI usage failures."""


class BadParameter(UsageError):
    """Raised for parameter binding or conversion failures."""


class Abort(ArgonError):
    """Raised when execution should terminate early."""


class Exit(ArgonError):
    """Raised to exit with a specific code."""

    def __init__(self, code: int = 0):
        super().__init__(code)
        self.code = code
