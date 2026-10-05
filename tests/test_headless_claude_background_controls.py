"""Every headless Claude Code launch under ``scripts/`` carries the #9690 controls (#9750).

A print-mode run (``claude -p`` / ``--print``) ends with its final turn, so any
background work it started is lost. The Claude adapter defines the two
controls once: ``HEADLESS_BACKGROUND_ENV`` (disables background execution) and
``HEADLESS_BACKGROUND_TOOL_DENIES`` (denies the tools that variable leaves
available). This test parses every Python module under ``scripts/``, finds each
argv that runs Claude Code in print mode, and fails when the code building it
does not reach both constants. A shell launcher that runs ``claude -p`` must be
started by a Python harness that supplies them.

An argv is a Claude print-mode argv when it holds a ``-p``/``--print`` string and
its program is Claude: a string literal naming ``claude``, an expression whose
identifiers name Claude (``CLAUDE_BIN``, ``*CLAUDE_CMD``, ``_get_claude_bin()``),
or, when the program is not a literal (an extension such as
``cmd.append("-p")``, or a generic ``binary``), an enclosing function or class
named for Claude. The argv is controlled when its enclosing function reaches
``HEADLESS_BACKGROUND_TOOL_DENIES`` (directly or through same-module callees)
and that function or one of its same-module callers reaches
``HEADLESS_BACKGROUND_ENV``.
"""

from __future__ import annotations

import ast
import re
import textwrap
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = REPO_ROOT / "scripts"
ADAPTER = "scripts/agent_runtime/adapters/claude.py"
ENV = "HEADLESS_BACKGROUND_ENV"
DENIES = "HEADLESS_BACKGROUND_TOOL_DENIES"
PRINT_FLAGS = frozenset({"-p", "--print"})

# Headless Claude launches that do not yet carry the controls. Each entry is a
# residual (#9750 residual policy): owner and reason. The test fails when an
# entry is fixed (remove it) or when an unlisted launch appears.
RESIDUAL: dict[str, str] = {
    "scripts/review/isolation.py::build_claude_review_argv": (
        "owner: claude-infra (#9750 driver). Outside the #9750 five-caller scope. The argv pins "
        "--tools Read,Grep,Glob, so Bash, Agent and the four background tools are absent; no "
        "production caller was found (tests only)."
    ),
    "scripts/eval/zno_nmt/adapters.py::run_claude": (
        "owner: claude-infra (#9750 driver). Outside the #9750 five-caller scope. The argv pins "
        '--tools "" (no built-in tools), so no background tool is reachable.'
    ),
}

# Shell launchers that run ``claude -p`` mapped to the Python harness that
# starts them; the harness must reach both controls and forward them.
SHELL_LAUNCHERS: dict[str, str] = {
    "scripts/agent_runtime/kimicc_headless.sh": "scripts/agent_runtime/adapters/kimicc.py",
}
_SHELL_CLAUDE_PRINT = re.compile(r"""(?:\bclaude\b|CLAUDE_BIN)["'}]*\s+(?:-p|--print)\b""")


@dataclass(frozen=True)
class Invocation:
    path: str
    scope: str
    line: int
    controlled: bool

    @property
    def key(self) -> str:
        return f"{self.path}::{self.scope}"


def _identifiers(node: ast.AST) -> Iterator[str]:
    for child in ast.walk(node):
        if isinstance(child, ast.Name):
            yield child.id
        elif isinstance(child, ast.Attribute):
            yield child.attr


def _called_names(node: ast.AST) -> set[str]:
    called: set[str] = set()
    for child in ast.walk(node):
        if isinstance(child, ast.Call):
            if isinstance(child.func, ast.Name):
                called.add(child.func.id)
            elif isinstance(child.func, ast.Attribute):
                called.add(child.func.attr)
    return called


def _is_print_flag(node: ast.AST) -> bool:
    return isinstance(node, ast.Constant) and node.value in PRINT_FLAGS


class _Scanner(ast.NodeVisitor):
    """Collect print-mode argv sites with their enclosing scopes."""

    def __init__(self) -> None:
        self.stack: list[ast.AST] = []
        self.sites: list[tuple[ast.AST, tuple[ast.AST, ...]]] = []
        self.functions: dict[str, list[ast.AST]] = {}

    def _scoped(self, node: ast.AST) -> None:
        self.stack.append(node)
        self.generic_visit(node)
        self.stack.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self.functions.setdefault(node.name, []).append(node)
        self._scoped(node)

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self._scoped(node)

    def _site(self, node: ast.AST) -> None:
        self.sites.append((node, tuple(self.stack)))

    def visit_List(self, node: ast.List) -> None:
        if any(_is_print_flag(elt) for elt in node.elts):
            self._site(node)
        self.generic_visit(node)

    visit_Tuple = visit_List

    def visit_Call(self, node: ast.Call) -> None:
        func = node.func
        if (
            isinstance(func, ast.Attribute)
            and func.attr in {"append", "insert"}
            and any(map(_is_print_flag, node.args))
        ):
            self._site(node)
        self.generic_visit(node)


def _names_claude(names: Iterator[str]) -> bool:
    return any("claude" in name.lower() for name in names)


def _scope_names_claude(stack: tuple[ast.AST, ...]) -> bool:
    return _names_claude(getattr(node, "name", "") for node in stack)


def _is_claude_site(node: ast.AST, stack: tuple[ast.AST, ...]) -> bool:
    if isinstance(node, (ast.List, ast.Tuple)) and node.elts:
        head = node.elts[0]
        if isinstance(head, ast.Constant) and isinstance(head.value, str) and not head.value.startswith("-"):
            return "claude" in Path(head.value).name.lower()
        if not isinstance(head, ast.Constant) and _names_claude(_identifiers(head)):
            return True
    return _scope_names_claude(stack)


def scan_source(source: str, path: str) -> list[Invocation]:
    """Return every Claude print-mode argv in ``source`` with its control status."""
    tree = ast.parse(source, filename=path)
    scanner = _Scanner()
    scanner.visit(tree)

    direct: dict[ast.AST, set[str]] = {}
    calls: dict[ast.AST, set[str]] = {}
    for nodes in scanner.functions.values():
        for fn in nodes:
            direct[fn] = set(_identifiers(fn))
            calls[fn] = _called_names(fn)

    reach_cache: dict[ast.AST, set[str]] = {}

    def reach(fn: ast.AST, seen: frozenset[ast.AST] = frozenset()) -> set[str]:
        if fn in reach_cache:
            return reach_cache[fn]
        names = set(direct[fn])
        for callee_name in calls[fn]:
            for callee in scanner.functions.get(callee_name, ()):
                if callee is not fn and callee not in seen:
                    names |= reach(callee, seen | {fn})
        if not seen:
            reach_cache[fn] = names
        return names

    found: list[Invocation] = []
    for node, stack in scanner.sites:
        if not _is_claude_site(node, stack):
            continue
        functions = [scope for scope in stack if isinstance(scope, (ast.FunctionDef, ast.AsyncFunctionDef))]
        if functions:
            fn = functions[-1]
            own = reach(fn)
            callers = [other for other, names in calls.items() if fn.name in names and other is not fn]
            env_scope = own.union(*(reach(caller) for caller in callers))
            controlled = DENIES in own and ENV in env_scope
        else:
            module_names = set(_identifiers(tree))
            controlled = {ENV, DENIES} <= module_names
        scope = ".".join(s.name for s in stack) or "<module>"
        found.append(Invocation(path, scope, getattr(node, "lineno", 0), controlled))
    return found


def _python_sources() -> Iterator[tuple[str, str]]:
    for path in sorted(SCRIPTS.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        yield path.relative_to(REPO_ROOT).as_posix(), path.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def repo_invocations() -> list[Invocation]:
    found: list[Invocation] = []
    for rel, source in _python_sources():
        if "-p" in source or "--print" in source:
            found.extend(scan_source(source, rel))
    return found


@pytest.mark.repo_wide
def test_every_headless_claude_invocation_carries_background_controls(repo_invocations: list[Invocation]) -> None:
    """No print-mode Claude argv under scripts/ lacks the env switch and tool denies, except listed residuals."""
    uncontrolled = {inv.key: inv.line for inv in repo_invocations if not inv.controlled}
    unexpected = {key: line for key, line in uncontrolled.items() if key not in RESIDUAL}
    assert not unexpected, (
        "headless claude -p without HEADLESS_BACKGROUND_ENV + HEADLESS_BACKGROUND_TOOL_DENIES "
        f"(import both from {ADAPTER}): {unexpected}"
    )
    stale = sorted(set(RESIDUAL) - set(uncontrolled))
    assert not stale, f"residual entries now controlled or gone; remove them: {stale}"


@pytest.mark.repo_wide
@pytest.mark.parametrize(
    "key",
    [
        "scripts/batch/batch_dispatcher_helpers.py::dispatch_claude_fix",
        "scripts/pipeline/dispatch.py::dispatch_claude_phase",
        "scripts/audit/code_review_benchmark.py::build_native_command",
        "scripts/audit/judge_calibration_matrix.py::build_native_command",
        "scripts/ai_agent_bridge/openai_proxy.py::_claude_backend",
        "scripts/agent_runtime/adapters/claude.py::ClaudeAdapter.build_invocation",
    ],
)
def test_scanner_finds_known_launchers_controlled(repo_invocations: list[Invocation], key: str) -> None:
    """The scanner sees the #9750 callers and the adapter, and each is controlled."""
    matches = [inv for inv in repo_invocations if inv.key == key]
    assert matches, f"scanner no longer detects {key}"
    assert all(inv.controlled for inv in matches)


@pytest.mark.repo_wide
def test_controls_have_a_single_source() -> None:
    """Callers import the constants from the Claude adapter; none redefines them."""
    for rel, source in _python_sources():
        if rel == ADAPTER or (ENV not in source and DENIES not in source):
            continue
        tree = ast.parse(source, filename=rel)
        for node in ast.walk(tree):
            if isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
                targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                bound = {name for target in targets for name in _identifiers(target)}
                assert not bound & {ENV, DENIES}, f"{rel}:{node.lineno} redefines a #9690 control"
            if isinstance(node, ast.ImportFrom) and {alias.name for alias in node.names} & {ENV, DENIES}:
                assert (node.module or "").endswith("adapters.claude") or (node.level and node.module == "claude"), (
                    f"{rel}:{node.lineno} imports a #9690 control from {node.module!r}"
                )


@pytest.mark.repo_wide
def test_shell_launchers_are_started_by_a_controlled_harness() -> None:
    """A shell script running claude -p is mapped to a harness that reaches both controls."""
    launching = {
        path.relative_to(REPO_ROOT).as_posix()
        for path in SCRIPTS.rglob("*.sh")
        if any(
            _SHELL_CLAUDE_PRINT.search(line) and not line.lstrip().startswith("#")
            for line in path.read_text(encoding="utf-8").splitlines()
        )
    }
    assert launching == set(SHELL_LAUNCHERS)
    for launcher, harness in SHELL_LAUNCHERS.items():
        text = (REPO_ROOT / harness).read_text(encoding="utf-8")
        assert Path(launcher).name in text
        assert ENV in text and DENIES in text, f"{harness} starts {launcher} without both controls"


# --- The scanner itself: a newly added uncontrolled launch is caught. ---

_CONTROLLED_IMPORT = (
    "from scripts.agent_runtime.adapters.claude import HEADLESS_BACKGROUND_ENV, HEADLESS_BACKGROUND_TOOL_DENIES\n"
)


@pytest.mark.parametrize(
    "body",
    [
        'def run(prompt):\n    subprocess.run(["claude", "-p", prompt])\n',
        'def run(prompt):\n    subprocess.run(["/usr/local/bin/claude", "--print", "--", prompt])\n',
        'def run(prompt):\n    subprocess.run([CLAUDE_BIN, "-p", prompt], env=os.environ)\n',
        'def run(prompt):\n    subprocess.run([*CLAUDE_CMD, "--print", "--bare"], input=prompt)\n',
        'def build_claude_argv(binary):\n    cmd = [str(binary)]\n    cmd.append("-p")\n    return cmd\n',
        # Only the denies, no env switch.
        'def run(prompt):\n    subprocess.run(["claude", "-p", "--disallowedTools", ",".join(HEADLESS_BACKGROUND_TOOL_DENIES)])\n',
        # Only the env switch, no denies.
        'def run(prompt):\n    subprocess.run(["claude", "-p", prompt], env={**os.environ, **HEADLESS_BACKGROUND_ENV})\n',
    ],
)
def test_scanner_flags_new_uncontrolled_launch(body: str) -> None:
    found = scan_source(_CONTROLLED_IMPORT + body, "scripts/new_module.py")
    assert [inv.controlled for inv in found] == [False]


def test_scanner_flags_uncontrolled_launch_in_temporary_module(tmp_path: Path) -> None:
    """A real file on disk with a new uncontrolled launch is flagged."""
    module = tmp_path / "late_launcher.py"
    module.write_text(
        'import subprocess\n\ndef go(p):\n    return subprocess.run(["claude", "-p", p])\n', encoding="utf-8"
    )
    found = scan_source(module.read_text(encoding="utf-8"), "scripts/late_launcher.py")
    assert [(inv.key, inv.controlled) for inv in found] == [("scripts/late_launcher.py::go", False)]


def test_scanner_accepts_controls_applied_directly_or_through_helpers() -> None:
    source = _CONTROLLED_IMPORT + textwrap.dedent(
        """
        def direct(prompt):
            cmd = ["claude", "-p", "--disallowedTools", ",".join(HEADLESS_BACKGROUND_TOOL_DENIES), prompt]
            subprocess.run(cmd, env={**os.environ, **HEADLESS_BACKGROUND_ENV})

        def _settings():
            return {"permissions": {"deny": list(HEADLESS_BACKGROUND_TOOL_DENIES)}}

        class ClaudeThing:
            def build(self):
                cmd = [self._bin(), "--settings", _settings()]
                cmd.append("-p")
                return cmd, HEADLESS_BACKGROUND_ENV

        def build_command(prompt):
            return ["claude", "-p", "--disallowedTools", ",".join(HEADLESS_BACKGROUND_TOOL_DENIES), prompt]

        def run_command(prompt):
            return subprocess.run(build_command(prompt), env={**os.environ, **HEADLESS_BACKGROUND_ENV})
        """
    )
    found = scan_source(source, "scripts/fixture.py")
    assert len(found) == 3
    assert all(inv.controlled for inv in found)


@pytest.mark.parametrize(
    "body",
    [
        'def run(p):\n    subprocess.run(["gemini", "-p", p])\n',
        'def run(p):\n    subprocess.run(["gh", "release", "download", "v1", "-p", "x"])\n',
        'def run(p):\n    subprocess.run([GROK_BIN, "-p", p])\n',
        'def build_native_command(p):\n    cmd = ["codex", "exec"]\n    cmd.extend(["-p", p])\n',
        '_FLAGS = ("--print", "--model")\n',
    ],
)
def test_scanner_ignores_other_programs(body: str) -> None:
    assert scan_source(body, "scripts/other.py") == []
