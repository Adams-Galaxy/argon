from __future__ import annotations
from typing import List, Tuple, Any
import textwrap
import difflib
from .specs import CommandSpec
from typing import TYPE_CHECKING
if TYPE_CHECKING:  # pragma: no cover
    from .core import CommandGroup

class HelpMixin:
    color: bool
    name: str
    version: str
    description: str
    root: Any  # avoids hard import of CommandGroup
    _global_options: dict

    def _c(self, text: str, color: str, bold: bool = False) -> str:  # provided by Interface but fallback
        if not getattr(self, 'color', False):
            return text
        colors = {
            'red': 31,
            'green': 32,
            'yellow': 33,
            'blue': 34,
            'magenta': 35,
            'cyan': 36,
            'white': 37,
        }
        code = colors.get(color, 37)
        prefix = f"\033[{1 if bold else 0};{code}m"
        return f"{prefix}{text}\033[0m"

    def render_help_overview(self) -> str:
        lines = [self._c(f"{self.name} v{self.version}", 'cyan', bold=True)]
        if self.description:
            lines.append(self.description)
        groups: List[Tuple[str, str]] = []
        commands: List[CommandSpec] = []
        for name, child in self.root.children.items():
            if hasattr(child, "children") and hasattr(child, "help_text") and not isinstance(child, CommandSpec):
                # treat as group
                if child is not self.root:
                    groups.append((name, getattr(child, 'help_text', '')))
            elif isinstance(child, CommandSpec):  # pragma: no cover
                commands.append(child)
        lines.append("")
        if groups:
            lines.append("Groups:")
            for gname, desc in sorted(groups):
                lines.append(f"  {gname + '/':<22} {desc}")
        if commands:
            lines.append("")
            lines.append("Commands:")
            for spec in sorted(commands, key=lambda s: s.name):
                alias = f" ({', '.join(spec.aliases)})" if spec.aliases else ""
                lines.append(f"  {spec.name:<15}{alias:<20} {spec.help}")
        lines.append("")
        lines.append("Use <group> -h to see its commands, or <command> -h for details.")
        return "\n".join(lines)

    def render_command_help(self, spec: CommandSpec) -> str:
        parts: List[str] = []
        fq = " ".join(spec.group_path + (spec.name,))
        parts.append(fq)
        for p in spec.positionals:
            parts.append(f"<{p}>")
        if spec.vararg:
            parts.append(f"<{spec.vararg}...>")
        if spec.options or self._global_options:
            parts.append("[options]")
        usage_line = f"Usage: {self.name} {' '.join(parts)}"
        lines = [self._c(usage_line, 'yellow', bold=True)]
        if spec.help:
            lines.append("")
            lines.append(textwrap.fill(spec.help, width=88))
        if spec.options:
            lines.append("")
            lines.append("Options:")
            for o in spec.options:
                flags = ", ".join(o.flags)
                placeholder = "" if o.is_flag else f" <{o.name}>"
                default = f" (default: {o.default})" if (o.default not in (None, False) and not o.is_flag) else ""
                lines.append(f"  {self._c(flags + placeholder, 'green')} {o.help}{default}")
        if self._global_options:
            lines.append("")
            lines.append("Global Options:")
            for g in self._global_options.values():
                flags = ", ".join(g.flags)
                placeholder = "" if g.is_flag else f" <{g.name}>"
                lines.append(f"  {self._c(flags + placeholder, 'magenta')} {g.help}")
        return "\n".join(lines)

    def render_group_help(self, group: 'CommandGroup') -> str:  # type: ignore[name-defined]
        lines: List[str] = []
        path: List[str] = []
        def dfs(cur, stack: List[str]) -> bool:  # duck-typed
            if cur is group:
                path.extend(stack[1:])
                return True
            for n, ch in cur.children.items():
                if hasattr(ch, 'children') and dfs(ch, stack + [n]):
                    return True
            return False
        dfs(self.root, [self.root.name])
        header = f"Group: {' '.join(path) if path else self.name}" if path else f"Group: {self.name}"
        lines.append(self._c(header, 'cyan', bold=True))
        if group.help_text:
            lines.append(textwrap.fill(group.help_text, width=88))
        lines.append("")
        lines.append("Commands:")
        cmds: List[Tuple[str, str]] = []
        for name, child in group.children.items():
            if isinstance(child, CommandSpec):
                cmds.append((name, child.help))
            elif isinstance(child, CommandGroup):
                cmds.append((name+"/", child.help_text))
        for name, desc in sorted(cmds):
            lines.append(f"  {name:<18} {desc}")
        lines.append("")
        lines.append("Use -h after a command for its usage, e.g.:")
        lines.append(f"  {self.name} {' '.join(path) if path else ''} <command> -h")
        return "\n".join(lines)

    def _suggest(self, token: str) -> str:
        cmds = self.root.collect_commands()
        names: List[str] = []
        for s in cmds:
            names.append(s.name)
            names.extend(s.aliases)
        token_cmp = token.lower()
        candidates = list({n.lower(): n for n in names}.values())
        matches = difflib.get_close_matches(token_cmp, candidates, n=3, cutoff=0.3)
        if not matches:
            return f"Unknown command '{token}'"
        return f"Unknown command '{token}'. Did you mean: {', '.join(matches)}?"

__all__ = ["HelpMixin"]
