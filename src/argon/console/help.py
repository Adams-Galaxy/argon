from __future__ import annotations

from rich.console import Group
from rich.table import Table
from rich.text import Text

from ..models import CommandSpec, GroupSpec, OptionInfo, Required


def _usage_for_group(app_name: str, group: GroupSpec) -> str:
    target = " ".join(group.path)
    if target:
        return f"Usage: {app_name} {target} COMMAND [ARGS]..."
    return f"Usage: {app_name} COMMAND [ARGS]..."


def _usage_for_command(app_name: str, command: CommandSpec) -> str:
    parts = [app_name, *command.path]
    for param in command.visible_params:
        if isinstance(param.parameter_info, OptionInfo):
            continue
        label = param.parameter_info.metavar or param.name.upper()
        if param.kind.name == "VAR_POSITIONAL":
            parts.append(f"[{label}...]")
        else:
            parts.append(f"<{label}>")
    if any(isinstance(param.parameter_info, OptionInfo) for param in command.visible_params):
        parts.append("[OPTIONS]")
    return "Usage: " + " ".join(parts)


def render_group_help(*, app_name: str, group: GroupSpec) -> Group:
    table = Table(show_header=True, header_style="argon.heading")
    table.add_column("Type", style="argon.dim", no_wrap=True)
    table.add_column("Name", style="argon.command", no_wrap=True)
    table.add_column("Help")
    for name, child in sorted(group.groups.items()):
        if child.hidden:
            continue
        table.add_row("group", name, child.help or "")
    for name, command_spec in sorted(group.commands.items()):
        if command_spec.hidden:
            continue
        table.add_row("command", name, command_spec.help or "")
    title = Text(f"{app_name} {' '.join(group.path)}".strip() or app_name, style="argon.title")
    usage = Text(_usage_for_group(app_name, group), style="argon.dim")
    description = Text(group.help or "")
    return Group(title, usage, description, table)


def render_command_help(*, app_name: str, command: CommandSpec) -> Group:
    table = Table(show_header=True, header_style="argon.heading")
    table.add_column("Parameter", style="argon.command", no_wrap=True)
    table.add_column("Kind", style="argon.dim", no_wrap=True)
    table.add_column("Help")
    table.add_column("Default", style="argon.dim")
    for param in command.visible_params:
        info = param.parameter_info
        default = info.resolved_default()
        default_text = "" if default is Required else repr(default)
        kind = "option" if isinstance(info, OptionInfo) else "argument"
        label = ", ".join(info.param_decls) if isinstance(info, OptionInfo) and info.param_decls else param.name
        help_parts = [info.help or ""]
        if info.required:
            help_parts.append("required")
        if info.envvar:
            env_label = ", ".join(info.envvar) if isinstance(info.envvar, list) else info.envvar
            help_parts.append(f"env: {env_label}")
        table.add_row(label, kind, " | ".join(part for part in help_parts if part), default_text)
    title = Text(f"{app_name} {' '.join(command.path)}".strip(), style="argon.title")
    usage = Text(_usage_for_command(app_name, command), style="argon.dim")
    alias_text = ""
    if command.aliases:
        alias_text = f"Aliases: {', '.join(command.aliases)}"
    description = Text("\n".join(part for part in [command.help or "", alias_text] if part))
    return Group(title, usage, description, table)
