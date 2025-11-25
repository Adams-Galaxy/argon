from __future__ import annotations

class CLIError(Exception):
    """Base exception for CLI system."""

class CommandNotFound(CLIError):
    """Raised when a command path cannot be resolved."""

class CommandUsageError(CLIError):
    """Raised for user-facing usage / validation errors."""

class CommandExecutionError(CLIError):
    """Raised for unexpected execution errors from command callbacks."""

__all__ = [
    "CLIError",
    "CommandNotFound",
    "CommandUsageError",
    "CommandExecutionError",
]
