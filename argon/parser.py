from __future__ import annotations
from typing import Any, List, Dict, Sequence, Tuple, Set
import shlex

class Parser:
    def parse(self, line: str) -> List[str]:
        return shlex.split(line)

    def classify(self, tokens: Sequence[str]) -> Tuple[List[str], Dict[str, Any], Set[str]]:
        positionals: List[str] = []
        options: Dict[str, Any] = {}
        flags: Set[str] = set()
        i = 0
        while i < len(tokens):
            t = tokens[i]
            if self._looks_like_number(t):
                positionals.append(t)
                i += 1
                continue
            if t.startswith("--") and len(t) > 2:
                if "=" in t:
                    name, val = t[2:].split("=", 1)
                    options[name.replace('-', '_')] = val
                else:
                    name = t[2:]
                    if i + 1 < len(tokens) and not tokens[i + 1].startswith("-"):
                        options[name.replace('-', '_')] = tokens[i + 1]
                        i += 1
                    else:
                        flags.add(name.replace('-', '_'))
                        options[name.replace('-', '_')] = True
            elif t.startswith("-") and len(t) > 1:
                cluster = t[1:]
                if len(cluster) > 1 and not cluster.isdigit():
                    for c in cluster:
                        flags.add(c)
                        options[c] = True
                else:
                    name = cluster
                    if i + 1 < len(tokens) and not tokens[i + 1].startswith("-"):
                        options[name] = tokens[i + 1]
                        i += 1
                    else:
                        flags.add(name)
                        options[name] = True
            else:
                positionals.append(t)
            i += 1
        return positionals, options, flags

    @staticmethod
    def _looks_like_number(token: str) -> bool:
        if not token:
            return False
        if token[0] not in {"-", "+"}:
            return False
        try:
            int(token, 0)
            return True
        except ValueError:
            try:
                float(token)
                return True
            except ValueError:
                return False

__all__ = ["Parser"]
