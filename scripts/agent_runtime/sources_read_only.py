"""Sources grants derived from the server's behavior-audited annotations.

Read declarations without importing the server (which imports the receipt ledger
and initializes unrelated dependencies). Unknown declaration shapes fail closed.
The side-effect audit tests these annotations against actual persistent writes.
"""

from __future__ import annotations

import ast
from functools import lru_cache
from pathlib import Path

SERVER_PATH = Path(__file__).resolve().parents[2] / ".mcp/servers/sources/server.py"


@lru_cache(maxsize=1)
def sources_tool_sets(server_path: Path = SERVER_PATH) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Lazily partition declarations once per process, without executing code.

    Missing or unreadable declarations propagate their error: callers must not
    fall back to unrestricted tools. Failed reads are not cached.
    """
    tree = ast.parse(server_path.read_text(encoding="utf-8"))
    annotations = {}
    for node in tree.body:
        if (
            isinstance(node, ast.Assign)
            and isinstance(node.value, ast.Call)
            and isinstance(node.value.func, ast.Name)
            and node.value.func.id == "ToolAnnotations"
        ):
            hints = {kw.arg: kw.value for kw in node.value.keywords}
            hint = hints.get("readOnlyHint")
            for target in node.targets:
                if isinstance(target, ast.Name):
                    annotations[target.id] = isinstance(hint, ast.Constant) and hint.value is True
    helper = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "_tool")
    defaults = [
        node.args[1]
        for node in ast.walk(helper)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "setdefault"
        and len(node.args) == 2
        and isinstance(node.args[0], ast.Constant)
        and node.args[0].value == "annotations"
    ]
    if len(defaults) != 1 or not isinstance(defaults[0], ast.Name):
        raise ValueError("sources_tool_annotation_default_unknown")
    function = next(node for node in tree.body if isinstance(node, ast.AsyncFunctionDef) and node.name == "list_tools")
    returns = [node for node in function.body if isinstance(node, ast.Return)]
    if len(returns) != 1 or not isinstance(returns[0].value, ast.List):
        raise ValueError("sources_tool_declarations_unknown")
    read_only, persisting, seen = [], [], set()
    for call in returns[0].value.elts:
        if not isinstance(call, ast.Call) or not isinstance(call.func, ast.Name) or call.func.id != "_tool":
            raise ValueError("sources_tool_declaration_unknown")
        fields = {kw.arg: kw.value for kw in call.keywords}
        name = fields.get("name")
        annotation = fields.get("annotations", defaults[0])
        if not isinstance(name, ast.Constant) or not isinstance(name.value, str) or name.value in seen:
            raise ValueError("sources_tool_name_unknown_or_duplicate")
        if not isinstance(annotation, ast.Name) or annotation.id not in annotations:
            raise ValueError("sources_tool_annotation_unknown")
        seen.add(name.value)
        (read_only if annotations[annotation.id] else persisting).append(name.value)
    if not read_only:
        raise ValueError("sources_read_only_tools_empty")
    return tuple(sorted(read_only)), tuple(sorted(persisting))
