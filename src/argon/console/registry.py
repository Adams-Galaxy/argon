from __future__ import annotations

from dataclasses import dataclass

from ..models import CommandSpec, GroupSpec


@dataclass(frozen=True, slots=True)
class Resolution:
    command: CommandSpec | None
    groups: tuple[GroupSpec, ...]
    path: tuple[str, ...]
    remaining: tuple[str, ...]


def _find_group(group: GroupSpec, token: str) -> GroupSpec | None:
    if token in group.groups:
        return group.groups[token]
    for child in group.groups.values():
        if token in child.aliases:
            return child
    return None


def _find_command(group: GroupSpec, token: str) -> CommandSpec | None:
    if token in group.commands:
        return group.commands[token]
    for child in group.commands.values():
        if token in child.aliases:
            return child
    return None


def resolve(root: GroupSpec, tokens: list[str]) -> Resolution:
    current = root
    groups: list[GroupSpec] = [root]
    path: list[str] = []
    rest = list(tokens)
    while rest:
        token = rest[0]
        next_group = _find_group(current, token)
        if next_group is not None:
            current = next_group
            groups.append(current)
            path.append(current.name)
            rest.pop(0)
            continue
        command = _find_command(current, token)
        if command is not None:
            path.append(command.name)
            rest.pop(0)
            return Resolution(command=command, groups=tuple(groups), path=tuple(path), remaining=tuple(rest))
        break
    return Resolution(command=None, groups=tuple(groups), path=tuple(path), remaining=tuple(rest))
