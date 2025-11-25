"""High-level orchestration layer tying together parser, specs, args, context.

This module defines the user-facing CLI, Shell, AsyncShell, and helper
decorators. Lower-level building blocks live in sibling modules:
	- exceptions.py (error types)
	- args.py (ParsedArgs)
	- specs.py (OptionSpec, CommandSpec)
	- parser.py (Parser tokenizer/classifier)
	- context.py (Context dataclass)
Splitting keeps responsibilities focused and simplifies maintenance.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple, Union, Set
import inspect
import shlex
import sys
import textwrap
import logging
import asyncio

from .exceptions import (
	CLIError,
	CommandNotFound,
	CommandUsageError,
	CommandExecutionError,
)
from .args import ParsedArgs
from .specs import OptionSpec, CommandSpec
from .parser import Parser
from .context import Context
from .help import HelpMixin
from dataclasses import dataclass

log = logging.getLogger("argon")


@dataclass
class CommandNode:
	name: str
	help_text: str = ""

	def is_group(self) -> bool:
		return False

	def as_group(self) -> "CommandGroup":  # pragma: no cover - defensive
		raise TypeError("Not a group")


class CommandGroup(CommandNode):
	def __init__(self, name: str, help_text: str = "") -> None:  # noqa: D401
		super().__init__(name, help_text)
		self.children: Dict[str, Union[CommandSpec, "CommandGroup"]] = {}

	def is_group(self) -> bool:  # type: ignore[override]
		return True

	def as_group(self) -> "CommandGroup":  # type: ignore[override]
		return self

	def add_group(self, name: str, help_text: str = "") -> "CommandGroup":
		existing = self.children.get(name)
		if isinstance(existing, CommandGroup):
			return existing
		grp = CommandGroup(name, help_text)
		self.children[name] = grp
		return grp

	def add_command(self, spec: CommandSpec) -> None:
		self.children[spec.name] = spec

	def collect_commands(self, prefix: Tuple[str, ...] = ()) -> List[CommandSpec]:
		out: List[CommandSpec] = []
		for name, child in self.children.items():
			if isinstance(child, CommandGroup):
				out.extend(child.collect_commands(prefix + (name,)))
			else:
				child.group_path = prefix
				out.append(child)
		return out


# CLI Orchestrator ---------------------------------------------------------


class Interface(HelpMixin):
	def __init__(
		self,
		name: str = "cli",
		version: str = "0.0.0",
		description: str = "",
		*,
		case_insensitive: bool = False,
		color: bool = True,
		allow_free_options: bool = True,
		output: Optional[Callable[[str], None]] = None,
	) -> None:
		self.name = name
		self.version = version
		self.description = description
		self.root = CommandGroup(name)
		self.parser = Parser()
		self._middleware: List[Callable[[ParsedArgs, CommandSpec], None]] = []
		self._pre_hooks: List[Callable[[Context], None]] = []
		self._post_hooks: List[Callable[[Context, Any], None]] = []
		self._global_options: Dict[str, OptionSpec] = {}
		self.case_insensitive = case_insensitive
		self.color = color
		self.allow_free_options = allow_free_options
		self._out: Callable[[str], None] = output or (lambda s: print(s))
		self._register_builtin_commands()

	def _register_builtin_commands(self) -> None:
		@self.command(name="help", help="Show help for a command or list groups")
		def _help(ctx: Context, *path: str):  # noqa: D401
			if not path:
				ctx.emit(self.render_help_overview())
				return
			node, _residual, group = self._resolve_path(path)
			if isinstance(node, CommandSpec):
				ctx.emit(self.render_command_help(node))
			elif group is not None:
				ctx.emit(self.render_group_help(group))
			else:
				ctx.emit(self._suggest(path[-1]))

		@self.command(name="version", help="Show CLI version")
		def _version(ctx: Context):  # noqa: D401
			ctx.emit(f"{self.name} v{self.version}")

	def add_middleware(self, func: Callable[[ParsedArgs, CommandSpec], None]) -> None:
		self._middleware.append(func)

	def add_pre_hook(self, func: Callable[[Context], None]) -> None:
		self._pre_hooks.append(func)

	def add_post_hook(self, func: Callable[[Context, Any], None]) -> None:
		self._post_hooks.append(func)

	def add_global_option(
		self,
		name: str,
		*,
		flags: Sequence[str],
		type: Callable[[str], Any] = str,
		default: Any = None,
		is_flag: bool = False,
		help: str = "",
	) -> None:
		self._global_options[name] = OptionSpec(
			name=name,
			flags=flags,
			type=type,
			default=default,
			is_flag=is_flag,
			help=help,
		)

	def group(self, name: str, help: str = "") -> "GroupDecorator":
		grp = self.root.add_group(name, help)
		return GroupDecorator(self, grp)

	def command(
		self,
		name: Optional[str] = None,
		*,
		help: str = "",
		options: Optional[Sequence[OptionSpec]] = None,
		aliases: Optional[Sequence[str]] = None,
		min_positionals: int = 0,
		max_positionals: Optional[int] = None,
		infer_options: bool = True,
	) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
		def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
			cmd_name = name or func.__name__.replace("_", "-")
			alias_list = list(aliases or [])
			final_options: List[OptionSpec] = list(options or [])
			positional_params: List[str] = []
			vararg: Optional[str] = None
			if infer_options and not options:
				sig = inspect.signature(func)
				taken_short: Set[str] = set()
				for pname, param in sig.parameters.items():
					if param.kind not in (param.POSITIONAL_OR_KEYWORD, param.KEYWORD_ONLY, param.VAR_POSITIONAL):
						continue
					if pname == "ctx":
						continue
					if param.kind == param.VAR_POSITIONAL:
						vararg = pname
						continue
					if param.default is inspect._empty:
						positional_params.append(pname)
						continue
					annot = param.annotation if param.annotation is not inspect._empty else str
					is_flag = annot is bool and (param.default in (False, None))
					long_flag = f"--{pname.replace('_','-')}"
					short_flag = f"-{pname[0]}" if pname[0] not in taken_short else None
					if short_flag:
						taken_short.add(pname[0])
						flags = [short_flag, long_flag]
					else:
						flags = [long_flag]
					final_options.append(
						OptionSpec(
							name=pname,
							flags=flags,
							type=(bool if is_flag else annot if callable(annot) else str),
							default=param.default,
							is_flag=is_flag,
							help="",
						)
					)
			spec = CommandSpec(
				name=cmd_name,
				callback=func,
				help=help or inspect.getdoc(func) or "",
				options=final_options,
				aliases=alias_list,
				positionals=positional_params,
				vararg=vararg,
				min_positionals=min_positionals,
				max_positionals=max_positionals,
			)
			self.root.add_command(spec)
			for al in alias_list:
				self.root.children[al] = spec
			return func

		return decorator

	def run_line(self, line: str) -> Any:
		tokens = self.parser.parse(line)
		if not tokens:
			return ""
		help_requested = any(t in {"-h", "--help"} for t in tokens)
		if help_requested:
			tokens = [t for t in tokens if t not in {"-h", "--help"}]
		g_opts, tokens = self._extract_global_options(tokens)
		node, residual, group = self._resolve_path(tokens)
		if help_requested:
			if node is None and group is None:
				self._out(self.render_help_overview())
				return ""
			if isinstance(node, CommandSpec):
				self._out(self.render_command_help(node))
				return ""
			if group is not None:
				self._out(self.render_group_help(group))
				return ""
		if node is None:
			raise CommandNotFound(self._suggest(tokens[0]))
		spec = node
		parsed = self._parse_arguments(spec, residual)
		ctx = Context(cli=self, command=spec, parsed=parsed, global_options=g_opts, output=self._out)
		for pre_hook in self._pre_hooks:
			pre_hook(ctx)
		for mw in self._middleware:
			mw(parsed, spec)
		result = self._invoke(spec, parsed, ctx)
		# If the command is async, run it in an event loop (best-effort synchronous wrapper)
		if inspect.iscoroutine(result):  # type: ignore[arg-type]
			try:
				result = asyncio.run(result)  # type: ignore[arg-type]
			except RuntimeError:  # already running loop
				# Fallback: schedule and wait using current loop (will deadlock if not awaited externally)
				loop = asyncio.get_event_loop()
				result = loop.create_task(result)  # type: ignore[arg-type]
		for post_hook in self._post_hooks:
			post_hook(ctx, result)
		return result

	def run_argv(self, argv: Optional[Sequence[str]] = None) -> Any:
		"""Execute using argv-style input (defaults to ``sys.argv[1:]``)."""
		args = list(argv if argv is not None else sys.argv[1:])
		if not args:
			return ""
		return self.run_line(shlex.join(args))

	async def run_line_async(self, line: str) -> Any:
		"""Asynchronous variant of run_line.

		If the resolved command is synchronous it executes normally; if it
		returns a coroutine it is awaited. Use this inside existing event
		loops (e.g. asyncio applications, notebooks, async frameworks) to
		avoid nested loop issues.
		"""
		tokens = self.parser.parse(line)
		if not tokens:
			return None
		help_requested = any(t in {"-h", "--help"} for t in tokens)
		if help_requested:
			tokens = [t for t in tokens if t not in {"-h", "--help"}]
		g_opts, tokens = self._extract_global_options(tokens)
		node, residual, group = self._resolve_path(tokens)
		if help_requested:
			if node is None and group is None:
				self._out(self.render_help_overview())
				return None
			if isinstance(node, CommandSpec):
				self._out(self.render_command_help(node))
				return None
			if group is not None:
				self._out(self.render_group_help(group))
				return None
		if node is None:
			raise CommandNotFound(self._suggest(tokens[0]))
		spec = node
		parsed = self._parse_arguments(spec, residual)
		ctx = Context(cli=self, command=spec, parsed=parsed, global_options=g_opts, output=self._out)
		for pre_hook in self._pre_hooks:
			pre_hook(ctx)
		for mw in self._middleware:
			mw(parsed, spec)
		result = self._invoke(spec, parsed, ctx)
		if inspect.iscoroutine(result):
			result = await result  # type: ignore[assignment]
		for post_hook in self._post_hooks:
			post_hook(ctx, result)
		return result

	def repl(self, prompt: str = "> ") -> None:
		self._out(f"{self.name} shell. Type 'exit' or 'quit' to leave.")
		while True:
			try:
				line = input(prompt)
			except EOFError:
				self._out("")
				break
			if line.strip().lower() in {"exit", "quit"}:
				break
			if not line.strip():
				continue
			try:
				self.run_line(line)
			except CLIError as e:
				self._out(str(e))
			except Exception as e:  # noqa: BLE001
				self._out(f"Unhandled error: {e}")

	def generate_completion(self) -> str:
		cmds = " ".join(sorted({c.name for c in self.root.collect_commands()}))
		script = f"""
		# {self.name} completion
		_{self.name}_complete() {{
			COMPREPLY=()
			local cur="${{COMP_WORDS[COMP_CWORD]}}"
			local opts="{cmds}"
			COMPREPLY=( $(compgen -W "$opts" -- "$cur") )
			return 0
		}}
		complete -F _{self.name}_complete {self.name}
		""".strip()
		return textwrap.dedent(script)

	def load_plugins(self, entry_point_group: str) -> None:
		try:
			from importlib.metadata import entry_points  # type: ignore
		except Exception:  # noqa: BLE001
			return
		try:
			for ep in entry_points().select(group=entry_point_group):  # type: ignore[attr-defined]
				try:
					plugin = ep.load()
					if callable(plugin):
						plugin(self)
				except Exception as e:  # noqa: BLE001
					log.warning("Failed loading plugin %s: %s", ep.name, e)
		except Exception:  # noqa: BLE001
			pass

	def _extract_global_options(self, tokens: List[str]) -> Tuple[ParsedArgs, List[str]]:
		if not self._global_options:
			return ParsedArgs(), tokens
		g_tokens: List[str] = []
		remaining: List[str] = []
		collecting = True
		for t in tokens:
			if collecting and t.startswith('-'):
				g_tokens.append(t)
				continue
			collecting = False
			remaining.append(t)
		pos, opts, flags = self.parser.classify(g_tokens)
		values: Dict[str, Any] = {}
		for spec in self._global_options.values():
			if spec.is_flag:
				values[spec.name] = False
			if spec.default is not None:
				values[spec.name] = spec.default
		for raw, val in opts.items():
			for spec in self._global_options.values():
				if raw == spec.name or raw in [f.lstrip('-') for f in spec.flags]:
					if spec.is_flag:
						values[spec.name] = True
					else:
						try:
							values[spec.name] = spec.type(val)
						except Exception:  # noqa: BLE001
							values[spec.name] = val
					break
		return ParsedArgs(positionals=pos, options=values, flags=flags), remaining

	def _resolve_path(
		self, tokens: Sequence[str]
	) -> Tuple[Optional[CommandSpec], List[str], Optional[CommandGroup]]:
		current = self.root
		i = 0
		found: Optional[CommandSpec] = None
		while i < len(tokens):
			t = tokens[i]
			child = current.children.get(t)
			if child is None and self.case_insensitive:
				for k, v in current.children.items():
					if k.lower() == t.lower():
						child = v
						break
			if child is None:
				break
			i += 1
			if isinstance(child, CommandGroup):
				current = child
				continue
			found = child
			break
		group = current if found is None and current is not self.root else None
		return found, list(tokens[i:]), group

	def _parse_arguments(self, spec: CommandSpec, tokens: Sequence[str]) -> ParsedArgs:
		positionals, options_map, _flags = self.parser.classify(tokens)
		canonical: Dict[str, OptionSpec] = {o.name: o for o in spec.options}
		values: Dict[str, Any] = {}
		for o in canonical.values():
			if o.is_flag:
				values[o.name] = False
			if o.default is not None:
				values[o.name] = o.default
		unknown: Dict[str, Any] = {}
		for raw_name, raw_val in options_map.items():
			matched: Optional[OptionSpec] = None
			for opt in canonical.values():
				if raw_name == opt.name or raw_name in [f.lstrip('-').replace('-', '_') for f in opt.flags]:
					matched = opt
					break
			if matched:
				if matched.is_flag:
					values[matched.name] = True
				else:
					try:
						values[matched.name] = matched.type(raw_val)
					except Exception as e:  # noqa: BLE001
						raise CommandUsageError(
							f"Invalid value for --{matched.name}: {raw_val} ({e})"
						) from e
			else:
				unknown[raw_name] = raw_val
		if unknown and not self.allow_free_options:
			raise CommandUsageError(
				"Unknown option(s): " + ", ".join(sorted(unknown.keys()))
			)
		for raw_name, raw_val in unknown.items():
			cast_val: Any = raw_val
			if isinstance(raw_val, str):
				low = raw_val.lower()
				if low in {"true", "false"}:
					cast_val = low == "true"
				else:
					try:
						cast_val = int(raw_val)
					except ValueError:
						try:
							cast_val = float(raw_val)
						except ValueError:
							cast_val = raw_val
			values[raw_name] = cast_val
		missing = [o.name for o in canonical.values() if o.required and o.name not in values]
		if missing:
			raise CommandUsageError(f"Missing required options: {', '.join(missing)}")
		if len(positionals) < spec.min_positionals:
			raise CommandUsageError(
				f"Expected at least {spec.min_positionals} positional args, got {len(positionals)}"
			)
		if spec.max_positionals is not None and len(positionals) > spec.max_positionals:
			raise CommandUsageError(
				f"Expected at most {spec.max_positionals} positional args, got {len(positionals)}"
			)
		return ParsedArgs(positionals=positionals, options=values, flags={k for k, v in values.items() if v is True})

	def _invoke(self, spec: CommandSpec, parsed: ParsedArgs, ctx: Context) -> Any:
		func = spec.callback
		sig = inspect.signature(func)
		params = list(sig.parameters.values())
		if not params or params[0].name != "ctx":
			raise CommandUsageError(
				f"First parameter of command '{spec.name}' must be 'ctx' (got: {params[0].name if params else 'none'})"
			)
		kwargs: Dict[str, Any] = {}
		positional_consumed = 0
		vararg_name: Optional[str] = None
		for i, param in enumerate(params):
			pname = param.name
			if i == 0:  # ctx
				continue
			if param.kind == param.VAR_POSITIONAL:
				vararg_name = pname
				continue
			if pname in parsed.options:
				kwargs[pname] = parsed.options[pname]
				continue
			if param.annotation is bool:
				kwargs[pname] = bool(parsed.options.get(pname, False))
				continue
			if positional_consumed < len(parsed.positionals):
				raw = parsed.positionals[positional_consumed]
				positional_consumed += 1
				kwargs[pname] = self._convert(raw, param.annotation)
				continue
			if param.default is not inspect._empty:  # noqa: SLF001
				kwargs[pname] = param.default
				continue
			raise CommandUsageError(f"Missing argument: {pname}")
		args_tuple: Tuple[Any, ...] = ()
		if vararg_name is not None:
			remaining = parsed.positionals[positional_consumed:]
			var_param = sig.parameters[vararg_name]
			ann = var_param.annotation
			if ann is not inspect._empty and ann not in (str, Any):  # noqa: SLF001
				converted = [self._convert(v, ann) for v in remaining]
			else:
				converted = remaining
			args_tuple = tuple(converted)
		try:
			if vararg_name is not None:
				res = func(ctx, *args_tuple, **kwargs)
			else:
				res = func(ctx, **kwargs)
			return res
		except CommandUsageError:
			raise
		except Exception as e:  # noqa: BLE001
			raise CommandExecutionError(f"Execution failed: {e}") from e

	@staticmethod
	def _convert(value: str, annotation: Any) -> Any:
		if annotation in (inspect._empty, str, Any):  # noqa: SLF001
			return value
		try:
			if annotation is int:
				return int(value)
			if annotation is float:
				return float(value)
			if annotation is bool:
				return value.lower() in {"1", "true", "yes", "on"}
		except Exception as e:  # noqa: BLE001
			raise CommandUsageError(f"Could not convert '{value}' to {annotation}: {e}") from e
		if callable(annotation):
			return annotation(value)
		return value

	# Help / suggestion methods now provided by HelpMixin.


# Group Decorator Helper ---------------------------------------------------



class GroupDecorator:
	def __init__(self, cli: Interface, group: CommandGroup):
		self._cli = cli
		self._group = group

	def group(self, name: str, help: str = "") -> "GroupDecorator":
		return GroupDecorator(self._cli, self._group.add_group(name, help))

	def command(
		self,
		name: Optional[str] = None,
		*,
		help: str = "",
		options: Optional[Sequence[OptionSpec]] = None,
		aliases: Optional[Sequence[str]] = None,
		min_positionals: int = 0,
		max_positionals: Optional[int] = None,
		infer_options: bool = True,
	) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
		def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
			cmd_name = name or func.__name__.replace("_", "-")
			alias_list = list(aliases or [])
			final_opts: List[OptionSpec] = list(options or [])
			positional_params: List[str] = []
			vararg: Optional[str] = None
			if infer_options and not options:
				sig = inspect.signature(func)
				used_short: Set[str] = set()
				for pname, param in sig.parameters.items():
					if pname == "ctx":
						continue
					if param.default is inspect._empty and param.kind != param.VAR_POSITIONAL:
						positional_params.append(pname)
						continue
					if param.kind == param.VAR_POSITIONAL:
						vararg = pname
						continue
					annotation = (
						param.annotation if param.annotation is not inspect._empty else str
					)
					is_flag = annotation is bool and (param.default in (False, None))
					long_flag = f"--{pname.replace('_','-')}"
					short_char = pname[0]
					short_flag = (
						f"-{short_char}" if short_char not in used_short else None
					)
					if short_flag:
						used_short.add(short_char)
						flags = [short_flag, long_flag]
					else:
						flags = [long_flag]
					final_opts.append(
						OptionSpec(
							name=pname,
							flags=flags,
							type=(bool if is_flag else annotation if callable(annotation) else str),
							default=param.default,
							is_flag=is_flag,
						)
					)
			spec = CommandSpec(
				name=cmd_name,
				callback=func,
				help=help or inspect.getdoc(func) or "",
				options=final_opts,
				aliases=alias_list,
				positionals=positional_params,
				vararg=vararg,
				min_positionals=min_positionals,
				max_positionals=max_positionals,
				group_path=self._compute_path(),
			)
			self._group.add_command(spec)
			for al in alias_list:
				self._group.children[al] = spec
			return func

		return decorator

	def _compute_path(self) -> Tuple[str, ...]:
		path: List[str] = []
		def dfs(current: CommandGroup, stack: List[str]) -> bool:
			if current is self._group:
				path.extend(stack[1:])
				return True
			for n, ch in current.children.items():
				if isinstance(ch, CommandGroup) and dfs(ch, stack + [n]):
					return True
			return False
		dfs(self._cli.root, [self._cli.root.name])
		return tuple(path)




def default_logging(level: int = logging.INFO) -> None:
	logging.basicConfig(level=level, format="[%(levelname)s] %(message)s")


__all__ = [
	"Interface",
	"ParsedArgs",
	"OptionSpec",
	"CommandSpec",
	"CLIError",
	"CommandNotFound",
	"CommandUsageError",
	"CommandExecutionError",
	"Context",
	"default_logging",
]
