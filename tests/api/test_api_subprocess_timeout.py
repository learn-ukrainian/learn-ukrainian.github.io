"""AST gate: every subprocess call under scripts/api/ passes timeout= (#8521)."""

from __future__ import annotations

import ast
from pathlib import Path

_BOUNDED = frozenset({"run", "check_output", "check_call"})
_REPO_ROOT = Path(__file__).resolve().parents[2]
_API_ROOT = _REPO_ROOT / "scripts" / "api"


def _subprocess_aliases(tree: ast.AST) -> dict[str, str | None]:
    """Map a local name to a subprocess attribute, or None when it is the module."""
    aliases: dict[str, str | None] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == "subprocess":
            for alias in node.names:
                if alias.name in _BOUNDED:
                    aliases[alias.asname or alias.name] = alias.name
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "subprocess":
                    aliases[alias.asname or alias.name] = None
    return aliases


def _callee_name(node: ast.Call, aliases: dict[str, str | None]) -> str | None:
    func = node.func
    if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
        base = func.value.id
        if base in aliases and aliases[base] is None and func.attr in _BOUNDED:
            return f"subprocess.{func.attr}"
    elif isinstance(func, ast.Name) and func.id in aliases:
        attr = aliases[func.id]
        if attr in _BOUNDED:
            return f"subprocess.{attr}"
    return None


def timeout_less_subprocess_calls(source: str) -> list[tuple[int, str]]:
    """Return (lineno, callee) for run/check_output/check_call calls without timeout=."""
    tree = ast.parse(source)
    aliases = _subprocess_aliases(tree)
    found: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        name = _callee_name(node, aliases)
        if name is None:
            continue
        if any(keyword.arg == "timeout" for keyword in node.keywords):
            continue
        found.append((node.lineno, name))
    return found


def test_scripts_api_subprocess_calls_have_timeout() -> None:
    offenders: list[str] = []
    for path in sorted(_API_ROOT.rglob("*.py")):
        source = path.read_text(encoding="utf-8")
        for lineno, name in timeout_less_subprocess_calls(source):
            relative = path.relative_to(_REPO_ROOT)
            offenders.append(f"{relative}:{lineno} {name}")
    assert not offenders, "subprocess calls missing timeout=:\n" + "\n".join(offenders)


def test_timeout_keyword_guard_flags_bare_subprocess_run() -> None:
    bare = "import subprocess\nsubprocess.run(['sleep', '999'])\n"
    assert timeout_less_subprocess_calls(bare) == [(2, "subprocess.run")]

    bounded = "import subprocess\nsubprocess.run(['sleep', '1'], timeout=1)\n"
    assert timeout_less_subprocess_calls(bounded) == []

    imported = "from subprocess import check_call as invoke\ninvoke(['echo'])\n"
    assert timeout_less_subprocess_calls(imported) == [(2, "subprocess.check_call")]
