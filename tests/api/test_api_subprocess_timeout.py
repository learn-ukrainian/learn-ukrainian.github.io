"""AST gate: every subprocess call under scripts/api/ passes timeout= (#8521)."""

from __future__ import annotations

import ast
import subprocess
from pathlib import Path

import pytest

from scripts.api import release_snapshot

_BOUNDED = frozenset({"run", "check_output", "check_call"})
_REPO_ROOT = Path(__file__).resolve().parents[2]
_API_ROOT = _REPO_ROOT / "scripts" / "api"

pytestmark = pytest.mark.repo_wide


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


_ALLOW_PREFIX = "subprocess-timeout-allow:"


def _parents(tree: ast.AST) -> dict[ast.AST, ast.AST]:
    parents: dict[ast.AST, ast.AST] = {}
    for parent in ast.walk(tree):
        for child in ast.iter_child_nodes(parent):
            parents[child] = parent
    return parents


def _bounded_reference(node: ast.AST, aliases: dict[str, str | None]) -> str | None:
    """Return the subprocess name when ``node`` is a bare run/check_* reference."""
    if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
        base = node.value.id
        if base in aliases and aliases[base] is None and node.attr in _BOUNDED:
            return f"subprocess.{node.attr}"
    elif isinstance(node, ast.Name):
        attr = aliases.get(node.id)
        if attr in _BOUNDED:
            return f"subprocess.{attr}"
    return None


def _supplies_timeout(call: ast.Call) -> bool:
    return any(keyword.arg == "timeout" for keyword in call.keywords)


def _call_bounds_reference(node: ast.AST, parents: dict[ast.AST, ast.AST]) -> bool:
    """True when this reference is a call, or a call argument, that passes timeout=."""
    parent = parents.get(node)
    if isinstance(parent, ast.keyword):
        call = parents.get(parent)
        return isinstance(call, ast.Call) and parent.value is node and _supplies_timeout(call)
    return isinstance(parent, ast.Call) and _supplies_timeout(parent) and (
        parent.func is node or any(arg is node for arg in parent.args)
    )


def _line_allows_unbounded(source: str, lineno: int) -> bool:
    lines = source.splitlines()
    if lineno < 1 or lineno > len(lines):
        return False
    comment = lines[lineno - 1].split("#", 1)
    if len(comment) < 2:
        return False
    marker = comment[1].find(_ALLOW_PREFIX)
    if marker < 0:
        return False
    return bool(comment[1][marker + len(_ALLOW_PREFIX) :].strip())


def timeout_less_subprocess_calls(source: str) -> list[tuple[int, str]]:
    """Return (lineno, name) for unbounded run/check_output/check_call references.

    A direct call is bounded only when that call passes ``timeout=``. A reference
    passed into ``to_thread``, ``partial``, ``run_in_executor``, a default, or an
    assignment is bounded only when that same call supplies ``timeout=``. An
    inline ``subprocess-timeout-allow:`` comment with a justification is the
    only other exemption.
    """
    tree = ast.parse(source)
    aliases = _subprocess_aliases(tree)
    parents = _parents(tree)
    found: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        name = _bounded_reference(node, aliases)
        if name is None or not hasattr(node, "lineno"):
            continue
        if _call_bounds_reference(node, parents) or _line_allows_unbounded(source, node.lineno):
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


def test_timeout_keyword_guard_flags_callable_forms() -> None:
    to_thread = "import asyncio, subprocess\nasyncio.to_thread(subprocess.run, ['sleep'])\n"
    assert timeout_less_subprocess_calls(to_thread) == [(2, "subprocess.run")]

    partial = "import functools, subprocess\nfunctools.partial(subprocess.check_output, ['echo'])\n"
    assert timeout_less_subprocess_calls(partial) == [(2, "subprocess.check_output")]

    executor = "import subprocess\nloop.run_in_executor(None, subprocess.check_call)\n"
    assert timeout_less_subprocess_calls(executor) == [(2, "subprocess.check_call")]

    default = "import subprocess\ndef scan(runner=subprocess.run):\n    return runner\n"
    assert timeout_less_subprocess_calls(default) == [(2, "subprocess.run")]

    assigned = "import subprocess\nrunner = subprocess.run\n"
    assert timeout_less_subprocess_calls(assigned) == [(2, "subprocess.run")]

    alias = "from subprocess import run\nimport asyncio\nasyncio.to_thread(run, ['sleep'])\n"
    assert timeout_less_subprocess_calls(alias) == [(3, "subprocess.run")]


def test_timeout_keyword_guard_allows_timeout_at_the_same_call_site() -> None:
    to_thread = "import asyncio, subprocess\nasyncio.to_thread(subprocess.run, ['sleep'], timeout=1)\n"
    assert timeout_less_subprocess_calls(to_thread) == []

    partial = "import functools, subprocess\nfunctools.partial(subprocess.check_output, ['echo'], timeout=1)\n"
    assert timeout_less_subprocess_calls(partial) == []

    executor = (
        "import functools, subprocess\n"
        "loop.run_in_executor(None, functools.partial(subprocess.check_call, ['echo'], timeout=1))\n"
    )
    assert timeout_less_subprocess_calls(executor) == []


def test_timeout_keyword_guard_allow_comment_needs_a_justification() -> None:
    bare_comment = "import subprocess\nrunner = subprocess.run  # used as a default\n"
    assert timeout_less_subprocess_calls(bare_comment) == [(2, "subprocess.run")]

    allowed = (
        "import subprocess\n"
        "runner = subprocess.run  # subprocess-timeout-allow: caller passes timeout=\n"
    )
    assert timeout_less_subprocess_calls(allowed) == []


def test_release_snapshot_default_lsof_runner_is_bounded(monkeypatch, tmp_path: Path) -> None:
    observed: dict[str, object] = {}

    def _expire(*args: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
        observed["timeout"] = kwargs.get("timeout")
        raise subprocess.TimeoutExpired(cmd=args[0] if args else "lsof", timeout=1)

    monkeypatch.setattr(release_snapshot.subprocess, "run", _expire)

    assert release_snapshot._live_release_shas(tmp_path) is None
    timeout = observed["timeout"]
    assert isinstance(timeout, (int, float)) and timeout > 0
    assert timeout == release_snapshot.LSOF_TIMEOUT_S
