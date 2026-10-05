"""Every headless Claude Code run under ``scripts/`` is spawned by the adapter's wrappers (#9750).

A print-mode run (``claude -p`` / ``--print``) ends with its final turn, so any
background work it started is lost (#9690). ``scripts/agent_runtime/adapters/claude.py``
owns the spawn: ``run_headless_claude`` and ``popen_headless_claude`` copy the
caller's exact base environment (the ambient one only when it is omitted), force
``CLAUDE_CODE_DISABLE_BACKGROUND_TASKS=1`` last, merge the background-tool denies
into the argv, and refuse ``env=``, ``shell=`` and ``executable=``. Nothing a
caller does to its own environment beforehand can reach the child unforced.

Two layers:

1. **Behaviour.** For each caller, a test drives its real code path with the
   process boundary patched and asserts what the child receives: the switch
   ``1`` under an ambient ``0``, the denies, the caller's environment exclusions,
   and its timeout and cleanup behaviour.
2. **A closed syntactic rule.** In every *Claude-referencing* module under
   ``scripts/`` (one with a string naming the Claude executable or an
   identifier containing ``claude``), every reference to a named process-spawn
   API and every ``InvocationPlan`` construction is either a wrapper's own
   spawn or a reviewed entry in ``headless_claude_spawn_exceptions.yaml``. The
   rule never interprets data flow, loops, branches or closures. It also
   rejects aliased, from- or dynamic imports of the spawn modules; shadowing or
   rebinding of the spawn modules and wrappers; non-canonical wrapper
   bindings; ``env=``/``shell=``/``executable=`` or a string argv at a wrapper
   call; shell-command literals that run ``claude -p``; and a function that
   holds a Claude program token and a print flag without calling a wrapper or
   the argv builder (an argv handed to an opaque helper). An exception entry
   that matches no site fails.

Documented limits (not proven safe by any test here):

- **Opaque values.** A module that neither names Claude nor holds a Claude
  identifier is not checked: it can only get the executable through another
  module's value or the environment
  (``test_limit_a_module_without_a_claude_reference_is_not_checked``).
- **Opaque helpers.** A repository helper in another module that spawns an argv
  it receives is that module's spawn site, checked only if that module
  references Claude. A Claude argv built in one function and handed to such a
  helper from another function, or with a print flag imported from elsewhere,
  is not tied to the helper (``test_limit_an_argv_handed_on_across_functions_is_not_tied``).
- **Dynamic and third-party spawning** (``ctypes``, ``pexpect``, ``sh``,
  ``multiprocessing`` targets, ``exec`` of generated code) is outside the named
  spawn API set.
- Exceptions with category ``generic-runner`` spawn an argv the rule cannot
  see; each entry names why no Claude print-mode argv reaches it, and the
  callers that route Claude around it are behaviour-tested below.

Agent-runtime plans (``InvocationPlan``) are launched by the shared runner; a
plan in a Claude-referencing module is a ``runtime`` exception only in a harness
listed in ``tests/agent_runtime/test_claude_no_background.py::_CLAUDE_CODE_HARNESSES``,
whose tests drive the real runner. A shell script that runs ``claude -p`` must
be named by a behavioural test there.
"""

from __future__ import annotations

import ast
import json
import re
import shlex
import subprocess
import textwrap
from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pytest
import yaml

from scripts.agent_runtime.adapters import claude as claude_adapter
from scripts.agent_runtime.adapters.claude import (
    HEADLESS_BACKGROUND_TOOL_DENIES,
    headless_claude_argv,
    popen_headless_claude,
    run_headless_claude,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = REPO_ROOT / "scripts"
ADAPTER = "scripts/agent_runtime/adapters/claude.py"
EXCEPTIONS_FILE = Path(__file__).with_name("headless_claude_spawn_exceptions.yaml")
NO_BACKGROUND_TESTS = REPO_ROOT / "tests/agent_runtime/test_claude_no_background.py"
PRINT_FLAGS = frozenset({"-p", "--print"})
SWITCH = "CLAUDE_CODE_DISABLE_BACKGROUND_TASKS"
DENIES = ",".join(HEADLESS_BACKGROUND_TOOL_DENIES)

WRAPPERS = frozenset({run_headless_claude.__name__, popen_headless_claude.__name__})
ARGV_BUILDER = headless_claude_argv.__name__
# The only spawns of a headless argv: each wrapper's own call, in the adapter.
WRAPPER_SPAWNS = frozenset(
    {
        (ADAPTER, run_headless_claude.__name__, "subprocess.run"),
        (ADAPTER, popen_headless_claude.__name__, "subprocess.Popen"),
    }
)

# Shell scripts that run ``claude -p``, each mapped to the test in
# NO_BACKGROUND_TESTS that launches it through the real runner.
SHELL_LAUNCHERS: dict[str, str] = {
    "scripts/agent_runtime/kimicc_headless.sh": "test_kimicc_runner_launch_carries_switch_and_denies",
}

# Each caller's function and the wrapper it must call. The rule keeps other
# spawns out; this keeps the callers on the wrappers.
KNOWN_WRAPPER_CALLS = {
    ("scripts/batch/batch_dispatcher_helpers.py", "dispatch_claude_fix"): "run_headless_claude",
    ("scripts/pipeline/dispatch.py", "dispatch_claude_phase"): "run_headless_claude",
    ("scripts/audit/code_review_benchmark.py", "run_subprocess"): "run_headless_claude",
    ("scripts/audit/judge_calibration_matrix.py", "run_subprocess"): "run_headless_claude",
    ("scripts/ai_agent_bridge/openai_proxy.py", "_run_backend_command"): "run_headless_claude",
    ("scripts/eval/zno_nmt/adapters.py", "_run_claude_process"): "popen_headless_claude",
    ("scripts/review/isolation.py", "run_claude_review"): "run_headless_claude",
}

# --- The frozen grammar ----------------------------------------------------------

# The complete named spawn API set, by canonical module binding.
_SUBPROCESS_APIS = frozenset({"run", "Popen", "call", "check_call", "check_output", "getoutput", "getstatusoutput"})
_ASYNCIO_APIS = frozenset({"create_subprocess_exec", "create_subprocess_shell"})
SPAWN_APIS: dict[str, frozenset[str]] = {
    "subprocess": _SUBPROCESS_APIS,
    "os": frozenset(
        {
            "system",
            "popen",
            "startfile",
            "posix_spawn",
            "posix_spawnp",
            *(f"exec{suffix}" for suffix in ("l", "le", "lp", "lpe", "v", "ve", "vp", "vpe")),
            *(f"spawn{suffix}" for suffix in ("l", "le", "lp", "lpe", "v", "ve", "vp", "vpe")),
        }
    ),
    "asyncio": _ASYNCIO_APIS,
    "asyncio.subprocess": _ASYNCIO_APIS,
    "pty": frozenset({"spawn"}),
}
SPAWN_MODULES = frozenset(name.split(".")[0] for name in SPAWN_APIS)
PLAN = "InvocationPlan"
# Where each API takes its program (position, keyword): the program key names
# an exception entry.
_PROGRAM_ARG: dict[str, tuple[int, str | None]] = {
    **{f"subprocess.{name}": (0, "args") for name in _SUBPROCESS_APIS},
    "subprocess.getoutput": (0, "cmd"),
    "subprocess.getstatusoutput": (0, "cmd"),
    "os.system": (0, "command"),
    "os.popen": (0, "cmd"),
    **{f"os.spawn{suffix}": (1, None) for suffix in ("l", "le", "lp", "lpe", "v", "ve", "vp", "vpe")},
    PLAN: (0, "cmd"),
}
_ADAPTER_MODULES = ("agent_runtime.adapters.claude",)

CATEGORIES = frozenset({"non-claude", "claude-probe", "runtime", "generic-runner", "argv-builder"})


def names_claude_executable(text: str) -> bool:
    """A string with a word naming the Claude Code executable or its package."""
    for token in re.split(r"[\s;&|()<>'\"`=,:]+", text):
        name = token.rstrip("/").rsplit("/", 1)[-1].lower()
        if name in {"claude", "claude.exe"} or name.startswith("claude-code"):
            return True
        if re.fullmatch(r"\$\{?\w*claude\w*\}?", name):
            return True
    return False


def _identifiers(tree: ast.AST) -> Iterator[str]:
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            yield node.id
        elif isinstance(node, ast.Attribute):
            yield node.attr
        elif isinstance(node, ast.alias):
            yield node.name
            if node.asname:
                yield node.asname
        elif isinstance(node, ast.arg):
            yield node.arg
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            yield node.name
        elif isinstance(node, ast.keyword) and node.arg:
            yield node.arg


def _strings(tree: ast.AST) -> Iterator[ast.Constant]:
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            yield node


def references_claude(tree: ast.AST) -> bool:
    """A Claude-referencing module: a string naming the executable or an identifier containing ``claude``."""
    return any(names_claude_executable(node.value) for node in _strings(tree)) or any(
        "claude" in name.lower() for name in _identifiers(tree)
    )


def _dotted(node: ast.AST) -> str | None:
    parts: list[str] = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if not isinstance(node, ast.Name):
        return None
    parts.append(node.id)
    return ".".join(reversed(parts))


def spawn_api(node: ast.AST) -> str | None:
    """The canonical ``module.api`` when ``node`` is ``<...>.<spawn module>.<spawn API>``."""
    if not isinstance(node, ast.Attribute):
        return None
    owner = node.value
    module = owner.id if isinstance(owner, ast.Name) else owner.attr if isinstance(owner, ast.Attribute) else None
    if module is None:
        return None
    if node.attr in _ASYNCIO_APIS and module in {"asyncio", "subprocess"}:
        return f"asyncio.{node.attr}"
    return f"{module}.{node.attr}" if node.attr in SPAWN_APIS.get(module, ()) else None


def _canonically_reached(node: ast.Attribute) -> bool:
    """``subprocess.run``, ``os.system``, ``asyncio.create_subprocess_exec``, ``asyncio.subprocess.<api>``."""
    return _dotted(node.value) in SPAWN_APIS


def program_key(expr: ast.expr | None) -> str:
    """The program a spawn runs, as written: a literal's first word, else the expression's source."""
    if expr is None:
        return "<none>"
    if isinstance(expr, (ast.List, ast.Tuple)):
        return program_key(expr.elts[0]) if expr.elts else "<empty>"
    if isinstance(expr, ast.Starred):
        return "*" + ast.unparse(expr.value)
    if isinstance(expr, ast.Constant) and isinstance(expr.value, str):
        words = expr.value.split()
        return words[0] if words else "<empty>"
    if isinstance(expr, ast.JoinedStr):
        head = expr.values[0] if expr.values else None
        if isinstance(head, ast.Constant) and str(head.value).split():
            return str(head.value).split()[0]
        return "<f-string>"
    return ast.unparse(expr)


def _literal(expr: ast.expr | None) -> tuple[str | None, ...] | None:
    if not isinstance(expr, (ast.List, ast.Tuple)):
        return None
    return tuple(
        elt.value if isinstance(elt, ast.Constant) and isinstance(elt.value, str) else None for elt in expr.elts
    )


def _program_expr(api: str, call: ast.Call) -> ast.expr | None:
    position, keyword = _PROGRAM_ARG.get(api, (0, None))
    if len(call.args) > position:
        return call.args[position]
    return next((kw.value for kw in call.keywords if keyword and kw.arg == keyword), None)


@dataclass(frozen=True)
class Site:
    """A spawn-API reference or ``InvocationPlan`` construction."""

    path: str
    function: str
    api: str
    program: str
    line: int
    # A literal argv's elements (``None`` for a non-constant one); ``None`` when the argv is not a literal.
    literal: tuple[str | None, ...] | None = None

    @property
    def key(self) -> tuple[str, str, str]:
        return (self.path, self.function, self.program)


@dataclass(frozen=True)
class ArgvHolder:
    """A function holding a Claude program token and a print flag without calling a wrapper or the builder."""

    path: str
    function: str
    line: int


@dataclass
class ModuleFindings:
    sites: list[Site] = field(default_factory=list)
    holders: list[ArgvHolder] = field(default_factory=list)
    violations: list[str] = field(default_factory=list)
    wrapper_calls: set[tuple[str, str]] = field(default_factory=set)  # (function, wrapper)


HOLDER = "<argv-holder>"  # the program key of an exception that clears an argv holder


def _bound_name(alias: ast.alias, *, from_import: bool) -> str:
    return alias.asname or (alias.name if from_import else alias.name.split(".")[0])


def _is_adapter_import(node: ast.ImportFrom) -> bool:
    module = node.module or ""
    if node.level:
        return module in {"claude", "adapters.claude"}
    return any(module == name or module.endswith(f".{name}") for name in _ADAPTER_MODULES)


def _is_docstring(node: ast.AST) -> bool:
    """A bare string statement: never passed anywhere, so never part of a launch."""
    return isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str)


class _ModuleCheck(ast.NodeVisitor):
    """One pass over a Claude-referencing module: sites, argv holders and grammar violations."""

    def __init__(self, path: str) -> None:
        self.path = path
        self.found = ModuleFindings()
        self.scope: list[str] = []
        self.parents: dict[int, ast.AST] = {}
        self.called: set[int] = set()
        self.annotations: set[int] = set()

    # -- scopes ------------------------------------------------------------------

    @property
    def function(self) -> str:
        return ".".join(self.scope) or "<module>"

    def _violation(self, node: ast.AST, message: str) -> None:
        self.found.violations.append(f"{self.path}:{getattr(node, 'lineno', 0)} {message}")

    def run(self, tree: ast.Module) -> ModuleFindings:
        for parent in ast.walk(tree):
            for child in ast.iter_child_nodes(parent):
                self.parents[id(child)] = parent
            # Annotations name types (``subprocess.Popen[str]``); they never spawn.
            annotation = getattr(parent, "annotation", None) or getattr(parent, "returns", None)
            if isinstance(annotation, ast.AST):
                self.annotations.update(id(node) for node in ast.walk(annotation))
        self._check_holder(tree, tree.body)
        self.visit(tree)
        return self.found

    def _scoped(self, node: ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef) -> None:
        self._protect_binding(node, node.name)
        self.scope.append(node.name)
        if not isinstance(node, ast.ClassDef):
            self._check_holder(node, node.body)
        self.generic_visit(node)
        self.scope.pop()

    visit_FunctionDef = visit_AsyncFunctionDef = visit_ClassDef = _scoped

    # -- argv holders (a Claude argv handed to an opaque helper) --------------------

    def _own_nodes(self, body: list[ast.stmt]) -> Iterator[ast.AST]:
        stack: list[ast.AST] = list(body)
        while stack:
            node = stack.pop()
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) or _is_docstring(node):
                continue
            yield node
            stack.extend(ast.iter_child_nodes(node))

    def _check_holder(self, node: ast.AST, body: list[ast.stmt]) -> None:
        names_claude = has_flag = calls_wrapper = False
        for sub in self._own_nodes(body):
            if isinstance(sub, ast.Constant) and isinstance(sub.value, str):
                has_flag = has_flag or sub.value in PRINT_FLAGS
                names_claude = names_claude or names_claude_executable(sub.value)
            elif isinstance(sub, (ast.Name, ast.Attribute)):
                name = sub.id if isinstance(sub, ast.Name) else sub.attr
                names_claude = names_claude or "claude" in name.lower()
            if isinstance(sub, ast.Call) and isinstance(sub.func, ast.Name):
                calls_wrapper = calls_wrapper or sub.func.id in WRAPPERS | {ARGV_BUILDER}
        if names_claude and has_flag and not calls_wrapper:
            self.found.holders.append(ArgvHolder(self.path, self.function, getattr(node, "lineno", 1)))

    # -- spawn sites -----------------------------------------------------------------

    def visit_Call(self, node: ast.Call) -> None:
        api = spawn_api(node.func)
        if api is None and isinstance(node.func, ast.Name) and node.func.id == PLAN:
            api = PLAN
        if api is not None:
            self.called.add(id(node.func))
            expr = _program_expr(api, node)
            self.found.sites.append(Site(self.path, self.function, api, program_key(expr), node.lineno, _literal(expr)))
        if isinstance(node.func, ast.Name) and node.func.id in WRAPPERS:
            self.called.add(id(node.func))
            self.found.wrapper_calls.add((self.function, node.func.id))
            self._check_wrapper_call(node)
        dynamic = _dotted(node.func) in {"__import__", "importlib.import_module", "import_module"}
        if dynamic and any(
            isinstance(a, ast.Constant) and str(a.value).split(".")[0] in SPAWN_MODULES for a in node.args
        ):
            self._violation(node, "dynamic import of a spawn module")
        self.generic_visit(node)

    def _check_wrapper_call(self, node: ast.Call) -> None:
        owned = sorted(kw.arg for kw in node.keywords if kw.arg in {"env", "shell", "executable"})
        if owned:
            self._violation(node, f"wrapper call passes {', '.join(owned)} (the wrapper owns them; use base_env)")
        argv = node.args[0] if node.args else None
        if isinstance(argv, ast.JoinedStr) or (isinstance(argv, ast.Constant) and isinstance(argv.value, str)):
            self._violation(node, "wrapper call passes a shell command string, not an argv list")

    def visit_Attribute(self, node: ast.Attribute) -> None:
        if id(node) in self.annotations:
            return
        api = spawn_api(node)
        if api is not None and id(node) not in self.called:
            self.found.sites.append(Site(self.path, self.function, api, "<reference>", node.lineno))
        if api is not None and not _canonically_reached(node):
            self._violation(node, f"{api} reached through {ast.unparse(node)}, not its canonical module binding")
        if node.attr in WRAPPERS | {ARGV_BUILDER}:
            self._violation(node, f"{node.attr} reached through an attribute, not its canonical import")
        target = (_dotted(node) or "").split(".")
        if (
            isinstance(node.ctx, (ast.Store, ast.Del))
            and target[0] in SPAWN_MODULES
            and target[:2] != ["os", "environ"]
        ):
            self._violation(node, f"assigns {_dotted(node)} (spawn module rebinding)")
        self.generic_visit(node)

    def visit_Name(self, node: ast.Name) -> None:
        if id(node) in self.annotations:
            return
        if isinstance(node.ctx, (ast.Store, ast.Del)):
            self._protect_binding(node, node.id)
        elif node.id in SPAWN_MODULES and not self._attribute_owner(node):
            self._violation(node, f"spawn module {node.id} used as a value")
        elif node.id in WRAPPERS and id(node) not in self.called:
            self._violation(node, f"wrapper {node.id} used as a value, not called")
        self.generic_visit(node)

    def _attribute_owner(self, node: ast.Name) -> bool:
        """``module.attr``, or ``getattr``/``hasattr(module, "<constant that is no spawn API>")``."""
        parent = self.parents.get(id(node))
        if isinstance(parent, ast.Attribute):
            return parent.value is node
        if not (isinstance(parent, ast.Call) and _dotted(parent.func) in {"getattr", "hasattr"} and parent.args):
            return False
        name = parent.args[1] if len(parent.args) > 1 else None
        return (
            parent.args[0] is node
            and isinstance(name, ast.Constant)
            and isinstance(name.value, str)
            and all(name.value not in apis for apis in SPAWN_APIS.values())
        )

    def visit_Subscript(self, node: ast.Subscript) -> None:
        index = node.slice
        if (
            _dotted(node.value) == "sys.modules"
            and isinstance(index, ast.Constant)
            and str(index.value).split(".")[0] in SPAWN_MODULES
        ):
            self._violation(node, "spawn module reached through sys.modules")
        self.generic_visit(node)

    # -- bindings: shadowing, rebinding, canonical imports --------------------------------

    def _protect_binding(self, node: ast.AST, name: str) -> None:
        if name in SPAWN_MODULES or name in WRAPPERS or name == ARGV_BUILDER:
            if self.path == ADAPTER and isinstance(node, ast.FunctionDef) and name in WRAPPERS | {ARGV_BUILDER}:
                return
            self._violation(node, f"rebinds {name}")

    def visit_arg(self, node: ast.arg) -> None:
        self._protect_binding(node, node.arg)
        self.generic_visit(node)

    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
        if node.name:
            self._protect_binding(node, node.name)
        self.generic_visit(node)

    def visit_Global(self, node: ast.Global | ast.Nonlocal) -> None:
        for name in node.names:
            self._protect_binding(node, name)

    visit_Nonlocal = visit_Global

    def visit_MatchAs(self, node: ast.MatchAs) -> None:
        if node.name:
            self._protect_binding(node, node.name)
        self.generic_visit(node)

    def visit_MatchStar(self, node: ast.MatchStar) -> None:
        if node.name:
            self._protect_binding(node, node.name)

    def visit_MatchMapping(self, node: ast.MatchMapping) -> None:
        if node.rest:
            self._protect_binding(node, node.rest)
        self.generic_visit(node)

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            bound = _bound_name(alias, from_import=False)
            if alias.name in SPAWN_APIS and alias.asname and alias.asname != alias.name:
                self._violation(node, f"aliased import of spawn module {alias.name} as {alias.asname}")
            elif bound in SPAWN_MODULES | WRAPPERS | {ARGV_BUILDER} and (
                alias.asname or alias.name.split(".")[0] not in SPAWN_MODULES
            ):
                self._violation(node, f"rebinds {bound} by import")

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        module = node.module or ""
        for alias in node.names:
            bound = _bound_name(alias, from_import=True)
            if not node.level and module in SPAWN_APIS and (alias.name == "*" or alias.name in SPAWN_APIS[module]):
                self._violation(node, f"from-import of spawn API {module}.{alias.name}")
            elif not node.level and module == "asyncio" and alias.name == "subprocess":
                self._violation(node, "from-import of asyncio.subprocess")
            elif alias.name in WRAPPERS | {ARGV_BUILDER} or bound in WRAPPERS | {ARGV_BUILDER}:
                if alias.asname or not _is_adapter_import(node):
                    self._violation(
                        node, f"non-canonical binding of {alias.name} (import it from the adapter, unaliased)"
                    )
            elif bound in SPAWN_MODULES:
                self._violation(node, f"rebinds {bound} by import")

    # -- shell-command literals ------------------------------------------------------------

    def visit_Expr(self, node: ast.Expr) -> None:
        if not _is_docstring(node):
            self.generic_visit(node)

    def visit_Constant(self, node: ast.Constant) -> None:
        if isinstance(node.value, str) and "claude" in node.value.lower() and shell_claude_print_lines(node.value):
            self._violation(node, "shell-command literal runs claude in print mode")


def check_module(source: str, path: str) -> ModuleFindings | None:
    """Findings for a Claude-referencing module, ``None`` for any other."""
    tree = ast.parse(source, filename=path)
    if not references_claude(tree):
        return None
    return _ModuleCheck(path).run(tree)


# --- Exceptions -------------------------------------------------------------------------


@dataclass(frozen=True)
class Exception_:
    module: str
    function: str
    program: str
    category: str
    reason: str
    spawned_by: str | None = None

    @property
    def key(self) -> tuple[str, str, str]:
        return (self.module, self.function, self.program)


def load_exceptions(text: str) -> list[Exception_]:
    data = yaml.safe_load(text) or {}
    return [Exception_(**entry) for entry in data.get("exceptions", [])]


def problems(findings: dict[str, ModuleFindings], exceptions: Iterable[Exception_]) -> list[str]:
    """Every site, holder or violation the wrappers and the exceptions do not account for."""
    allowed = {entry.key for entry in exceptions}
    out: list[str] = []
    for _path, found in sorted(findings.items()):
        out.extend(found.violations)
        for site in found.sites:
            if (site.path, site.function, site.api) in WRAPPER_SPAWNS or site.key in allowed:
                continue
            out.append(f"{site.path}:{site.line} {site.function} spawns {site.program!r} via {site.api}")
        for holder in found.holders:
            if (holder.path, holder.function, HOLDER) not in allowed:
                out.append(
                    f"{holder.path}:{holder.line} {holder.function} holds a Claude print-mode argv "
                    "but calls no wrapper (an opaque helper may run it)"
                )
    return out


# --- Shell command lines ---------------------------------------------------------

_SHELL_PUNCT = frozenset({";", "&", "|", "&&", "||", "(", ")", ";;", "|&", "{", "}", "$"})
_SHELL_KEYWORDS = frozenset(
    {"if", "then", "else", "elif", "fi", "do", "done", "while", "until", "case", "esac", "!", "[[", "]]"}
)
_DECLARATIONS = frozenset({"local", "export", "declare", "readonly", "typeset", "alias"})
_PROGRAM_WRAPPERS = frozenset(
    {
        "builtin",
        "bunx",
        "command",
        "env",
        "eval",
        "exec",
        "ionice",
        "nice",
        "nohup",
        "npx",
        "pnpx",
        "setsid",
        "stdbuf",
        "sudo",
        "systemd-run",
        "time",
        "timeout",
        "unbuffer",
        "xvfb-run",
    }
)
_ASSIGNMENT = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)(\[[^\]]*\])?\+?=(.*)$", re.S)
_WRAPPER_ARG = re.compile(r"^(-.*|[A-Za-z_][A-Za-z0-9_]*=.*|\d+(\.\d+)?[smhd]?)$", re.S)
_HEREDOC = re.compile(r"(?<!<)<<(?!<)-?\s*['\"]?([A-Za-z_][A-Za-z0-9_]*)['\"]?")
_FUNCTION = re.compile(r"^\s*(?:function\s+)?([A-Za-z_][A-Za-z0-9_:-]*)\s*\(\s*\)|^\s*function\s+([A-Za-z_][\w:-]*)")


def _logical_shell_lines(text: str) -> Iterator[tuple[int, str]]:
    """Yield ``(line number, line)`` with continuations joined and heredoc bodies dropped."""
    lines = text.splitlines()
    index = 0
    heredoc: str | None = None
    while index < len(lines):
        start = index + 1
        line = lines[index]
        index += 1
        if heredoc is not None:
            if line.strip() == heredoc:
                heredoc = None
            continue
        while line.endswith("\\") and (len(line) - len(line.rstrip("\\"))) % 2 == 1 and index < len(lines):
            line = line[:-1] + " " + lines[index]
            index += 1
        match = _HEREDOC.search(line)
        if match:
            heredoc = match.group(1)
        yield start, line


def _shell_tokens(line: str) -> list[str]:
    prepared = line.replace("$(", " ( ").replace("`", " ; ")
    lexer = shlex.shlex(prepared, posix=True, punctuation_chars=";&|()")
    lexer.whitespace_split = True
    lexer.commenters = "#"
    try:
        return list(lexer)
    except ValueError:
        return re.findall(r"[;&|()]+|[^\s;&|()]+", prepared.split(" #", 1)[0])


def _shell_commands(tokens: list[str]) -> Iterator[list[str]]:
    current: list[str] = []
    for token in tokens:
        if token in _SHELL_PUNCT or (token and set(token) <= set(";&|()")):
            if current:
                yield current
            current = []
        else:
            current.append(token)
    if current:
        yield current


def _shell_program(command: list[str]) -> int | None:
    index = 0
    while index < len(command):
        token = command[index]
        if token in _SHELL_KEYWORDS or _ASSIGNMENT.match(token):
            index += 1
        elif token in _DECLARATIONS:
            return None
        elif Path(token.lstrip("\\")).name in _PROGRAM_WRAPPERS:
            index += 1
            while index < len(command) and _WRAPPER_ARG.match(command[index]):
                index += 1
        else:
            return index
    return None


def _shell_names_claude(token: str, aliases: set[str]) -> bool:
    name = Path(token.lstrip("\\")).name if "/" in token else token.lstrip("\\")
    variable = re.match(r"^\$\{?([A-Za-z_][A-Za-z0-9_]*)", name)
    if variable:
        return "claude" in variable.group(1).lower() or variable.group(1) in aliases
    return "claude" in name.lower() or name in aliases


def shell_claude_print_lines(text: str) -> list[int]:
    """Lines of a shell script or command string that run Claude Code in print mode."""
    commands: list[tuple[int, list[str], str | None]] = []
    assignments: list[tuple[str, list[str]]] = []
    function: str | None = None
    depth = 0
    for lineno, line in _logical_shell_lines(text):
        tokens = _shell_tokens(line)
        for index, token in enumerate(tokens):
            assignment = _ASSIGNMENT.match(token)
            if assignment is None:
                continue
            if assignment.group(3):
                assignments.append((assignment.group(1), _shell_tokens(assignment.group(3))[:1]))
            elif tokens[index + 1 : index + 2] == ["("]:
                inner = tokens[index + 2 : tokens.index(")", index) if ")" in tokens[index:] else len(tokens)]
                assignments.append((assignment.group(1), [t for t in inner if not t.startswith("-")]))
        defined = _FUNCTION.match(line)
        if defined and depth == 0:
            function = defined.group(1) or defined.group(2)
        depth = max(0, depth + tokens.count("{") - tokens.count("}"))
        for command in _shell_commands(tokens):
            commands.append((lineno, command, function if depth or defined else None))
        if depth == 0 and not defined:
            function = None

    aliases: set[str] = set()
    changed = True
    while changed:
        changed = False
        for name, values in assignments:
            if name not in aliases and any(_shell_names_claude(value, aliases) for value in values):
                aliases.add(name)
                changed = True
        for _, command, function in commands:
            program = _shell_program(command)
            if (
                function is not None
                and function not in aliases
                and program is not None
                and _shell_names_claude(command[program], aliases)
            ):
                aliases.add(function)
                changed = True

    hits: list[int] = []
    for lineno, command, _ in commands:
        program = _shell_program(command)
        if program is None:
            continue
        if _shell_names_claude(command[program], aliases) and PRINT_FLAGS & set(command[program + 1 :]):
            hits.append(lineno)
    return sorted(set(hits))


# --- Repository ---------------------------------------------------------------------------

RUNTIME_LAUNCHERS = frozenset({"scripts/agent_runtime/runner.py", "scripts/delegate.py"})


def _python_sources() -> Iterator[tuple[str, str]]:
    for path in sorted(SCRIPTS.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        yield path.relative_to(REPO_ROOT).as_posix(), path.read_text(encoding="utf-8")


def _harness_table() -> set[str]:
    """Keys of ``_CLAUDE_CODE_HARNESSES`` in NO_BACKGROUND_TESTS (adapter files it drives)."""
    tree = ast.parse(NO_BACKGROUND_TESTS.read_text(encoding="utf-8"))
    for node in tree.body:
        targets = node.targets if isinstance(node, ast.Assign) else []
        if any(isinstance(t, ast.Name) and t.id == "_CLAUDE_CODE_HARNESSES" for t in targets):
            assert isinstance(node.value, ast.Dict)
            return {key.value for key in node.value.keys if isinstance(key, ast.Constant)}
    raise AssertionError("_CLAUDE_CODE_HARNESSES not found")


def _run_program(site: Site) -> str | None:
    """The literal program a site runs once ``timeout``/``env``/``nohup``-style wrappers are skipped."""
    args = list(site.literal or ())
    index = 0
    while index < len(args) and args[index] is not None and Path(args[index] or "").name in _PROGRAM_WRAPPERS:
        index += 1
        while index < len(args) and args[index] is not None and _WRAPPER_ARG.match(args[index] or ""):
            index += 1
    return args[index] if index < len(args) else None


def exception_errors(
    findings: dict[str, ModuleFindings], exceptions: list[Exception_], harnesses: set[str]
) -> list[str]:
    """Malformed, miscategorised or stale exception entries."""
    sites: dict[tuple[str, str, str], list[Site]] = {}
    for found in findings.values():
        for site in found.sites:
            sites.setdefault(site.key, []).append(site)
        for holder in found.holders:
            sites.setdefault((holder.path, holder.function, HOLDER), [])
    errors: list[str] = []
    seen: set[tuple[str, str, str]] = set()
    for entry in exceptions:
        label = f"{entry.module}::{entry.function} {entry.program!r}"
        if entry.key in seen:
            errors.append(f"duplicate exception: {label}")
        seen.add(entry.key)
        if entry.category not in CATEGORIES or not entry.reason.strip():
            errors.append(f"exception needs a known category and a reason: {label}")
        if entry.key not in sites:
            errors.append(f"stale exception (matches no spawn site): {label}")
            continue
        matched = sites[entry.key]
        holder = entry.program == HOLDER
        if (
            entry.category == "non-claude"
            and not holder
            and (
                "claude" in entry.program.lower()
                or any(names_claude_executable(_run_program(s) or "") for s in matched)
            )
        ):
            errors.append(f"non-claude exception runs a Claude program: {label}")
        if entry.category == "claude-probe":
            for site in matched:
                args = set(site.literal or ())
                if site.literal is not None and (args & PRINT_FLAGS or not args & {"--version", "--help"}):
                    errors.append(f"claude-probe is not a fixed --version/--help probe: {label}:{site.line}")
        if entry.category == "runtime":
            runtime_path = entry.module.removeprefix("scripts/agent_runtime/")
            is_plan = any(site.api == PLAN for site in matched)
            allowed = runtime_path in harnesses if (is_plan or holder) else entry.module in RUNTIME_LAUNCHERS
            if not allowed:
                errors.append(f"runtime exception outside the runner and the runner-tested harnesses: {label}")
        if entry.category == "argv-builder":
            calls = findings[entry.module].wrapper_calls if entry.module in findings else set()
            if not holder or entry.spawned_by is None or not any(fn == entry.spawned_by for fn, _ in calls):
                errors.append(
                    f"argv-builder must clear a holder and name a same-module function calling a wrapper: {label}"
                )
    return errors


@pytest.fixture(scope="module")
def repo_findings() -> dict[str, ModuleFindings]:
    found: dict[str, ModuleFindings] = {}
    for rel, source in _python_sources():
        module = check_module(source, rel)
        if module is not None:
            found[rel] = module
    return found


@pytest.fixture(scope="module")
def exceptions() -> list[Exception_]:
    return load_exceptions(EXCEPTIONS_FILE.read_text(encoding="utf-8"))


# --- Repository invariants -------------------------------------------------------------


@pytest.mark.repo_wide
def test_every_spawn_in_a_claude_referencing_module_is_a_wrapper_or_a_reviewed_exception(
    repo_findings: dict[str, ModuleFindings], exceptions: list[Exception_]
) -> None:
    """The closed rule: no other spawn, rebinding, shell literal or unwrapped argv holder under scripts/."""
    found = problems(repo_findings, exceptions)
    assert not found, (
        f"spawn headless Claude only through {sorted(WRAPPERS)} in {ADAPTER}, or add a reviewed entry to "
        f"{EXCEPTIONS_FILE.name}: {found}"
    )


@pytest.mark.repo_wide
def test_exceptions_are_live_categorised_and_justified(
    repo_findings: dict[str, ModuleFindings], exceptions: list[Exception_]
) -> None:
    assert exceptions, "the exceptions file lost its entries"
    assert not exception_errors(repo_findings, exceptions, _harness_table())


@pytest.mark.repo_wide
def test_wrapper_spawns_and_known_callers_are_wired(repo_findings: dict[str, ModuleFindings]) -> None:
    """The wrappers' own spawns exist, and each caller's function calls its wrapper."""
    adapter_sites = {(site.path, site.function, site.api) for site in repo_findings[ADAPTER].sites}
    assert adapter_sites >= WRAPPER_SPAWNS
    for (path, function), wrapper in KNOWN_WRAPPER_CALLS.items():
        assert (function, wrapper) in repo_findings[path].wrapper_calls, f"{path}::{function} no longer calls {wrapper}"


def _shell_launcher_errors(launching: set[str], mapping: dict[str, str], tests_source: str) -> list[str]:
    errors = [f"unmapped shell launcher: {path}" for path in sorted(launching - set(mapping))]
    errors += [f"mapped script no longer launches claude -p: {path}" for path in sorted(set(mapping) - launching)]
    functions = {
        node.name: ast.get_source_segment(tests_source, node) or ""
        for node in ast.parse(tests_source).body
        if isinstance(node, ast.FunctionDef)
    }
    for script, test_name in mapping.items():
        if Path(script).name not in functions.get(test_name, ""):
            errors.append(f"{test_name} does not launch {Path(script).name}")
    return errors


@pytest.mark.repo_wide
def test_shell_launchers_are_proven_by_a_runner_test() -> None:
    """Each shell script running claude -p is named by a test that launches it through the real runner."""
    launching = {
        path.relative_to(REPO_ROOT).as_posix()
        for path in SCRIPTS.rglob("*.sh")
        if shell_claude_print_lines(path.read_text(encoding="utf-8"))
    }
    errors = _shell_launcher_errors(launching, SHELL_LAUNCHERS, NO_BACKGROUND_TESTS.read_text(encoding="utf-8"))
    assert not errors


@pytest.mark.repo_wide
def test_controls_have_a_single_source() -> None:
    """Only the adapter defines the controls, the wrappers or the argv builder; callers import them from it."""
    owned = {"HEADLESS_BACKGROUND_ENV", "HEADLESS_BACKGROUND_TOOL_DENIES", ARGV_BUILDER, *WRAPPERS}
    for rel, source in _python_sources():
        if rel == ADAPTER or not any(name in source for name in owned):
            continue
        tree = ast.parse(source, filename=rel)
        for node in ast.walk(tree):
            if isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
                targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                bound = {sub.id for target in targets for sub in ast.walk(target) if isinstance(sub, ast.Name)}
                assert not bound & owned, f"{rel}:{node.lineno} redefines a #9690 control"
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                assert node.name not in owned, f"{rel}:{node.lineno} redefines {node.name}"
            if isinstance(node, ast.ImportFrom) and {alias.name for alias in node.names} & owned:
                assert _is_adapter_import(node), f"{rel}:{node.lineno} imports a #9690 control from {node.module!r}"


# --- The wrappers ----------------------------------------------------------------------


@pytest.fixture
def ambient_switch_off(monkeypatch: pytest.MonkeyPatch) -> None:
    """The test process's own env has background tasks *enabled*.

    A parent that already carries the switch (a Claude session running the
    suite) would otherwise let a caller that forwards ``os.environ`` pass.
    """
    monkeypatch.setenv(SWITCH, "0")
    monkeypatch.setenv("LU_AMBIENT_PROBE", "ambient")


@pytest.fixture
def spawned(monkeypatch: pytest.MonkeyPatch) -> list[dict[str, Any]]:
    """Record every ``subprocess.run``/``Popen`` the wrappers make, without starting a process."""
    calls: list[dict[str, Any]] = []

    def fake_run(argv: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        calls.append({"api": "run", "argv": argv, **kwargs})
        return subprocess.CompletedProcess(argv, 0, stdout="out", stderr="")

    def fake_popen(argv: list[str], **kwargs: Any) -> str:
        calls.append({"api": "Popen", "argv": argv, **kwargs})
        return "process"

    monkeypatch.setattr(claude_adapter.subprocess, "run", fake_run)
    monkeypatch.setattr(claude_adapter.subprocess, "Popen", fake_popen)
    return calls


def test_argv_builder_adds_denies_before_the_end_of_options_marker() -> None:
    argv = headless_claude_argv(["claude", "-p", "--model", "m", "--", "prompt"])
    assert argv == ["claude", "-p", "--model", "m", "--disallowedTools", DENIES, "--", "prompt"]


def test_argv_builder_appends_denies_without_a_marker_and_is_idempotent() -> None:
    argv = headless_claude_argv(("claude", "-p", "prompt"))
    assert argv == ["claude", "-p", "prompt", "--disallowedTools", DENIES]
    assert headless_claude_argv(argv) == argv


@pytest.mark.parametrize("flag", ["--disallowedTools", "--disallowed-tools"])
def test_argv_builder_merges_into_a_stricter_existing_list(flag: str) -> None:
    base = ["claude", "-p", flag, "Edit,Bash(git push *),Monitor", "--", "a --disallowedTools b"]
    assert headless_claude_argv(base) == [
        "claude",
        "-p",
        flag,
        "Edit,Bash(git push *),Monitor,ScheduleWakeup,CronCreate,Workflow",
        "--",
        "a --disallowedTools b",
    ]


def test_argv_builder_merges_the_equals_form_and_leaves_its_input_unchanged() -> None:
    base = ["claude", "-p", "--disallowedTools=Edit"]
    assert headless_claude_argv(base) == ["claude", "-p", f"--disallowedTools=Edit,{DENIES}"]
    assert base == ["claude", "-p", "--disallowedTools=Edit"]


# How each wrapper's callers bound the run: ``run`` takes a timeout, a Popen caller bounds communicate().
_BOUNDS: dict[Any, dict[str, Any]] = {
    run_headless_claude: {"timeout": 5},
    popen_headless_claude: {"start_new_session": True},
}


@pytest.mark.usefixtures("ambient_switch_off")
@pytest.mark.parametrize("wrapper", list(_BOUNDS))
def test_wrapper_child_gets_exactly_the_base_env_plus_the_switch(wrapper: Any, spawned: list[dict[str, Any]]) -> None:
    base = {"PATH": "/bin", SWITCH: "0"}
    wrapper(["claude", "-p", "x"], base_env=base, cwd="/w", **_BOUNDS[wrapper])
    (call,) = spawned
    assert call["env"] == {"PATH": "/bin", SWITCH: "1"}, "ambient must not leak into an exact base env"
    assert base == {"PATH": "/bin", SWITCH: "0"}, "the caller's mapping is copied, never mutated"
    assert call["argv"] == ["claude", "-p", "x", "--disallowedTools", DENIES]
    assert call["cwd"] == "/w" and call.items() >= _BOUNDS[wrapper].items()
    assert "shell" not in call and "executable" not in call


def test_run_wrapper_requires_a_timeout(spawned: list[dict[str, Any]]) -> None:
    with pytest.raises(TypeError, match="timeout"):
        run_headless_claude(["claude", "-p", "x"])  # type: ignore[call-arg]
    assert spawned == []


@pytest.mark.usefixtures("ambient_switch_off")
@pytest.mark.parametrize("wrapper", list(_BOUNDS))
def test_wrapper_without_a_base_env_copies_the_ambient_env_and_forces_the_switch(
    wrapper: Any, spawned: list[dict[str, Any]]
) -> None:
    import os

    wrapper(["claude", "-p", "x"], **_BOUNDS[wrapper])
    (call,) = spawned
    assert call["env"]["LU_AMBIENT_PROBE"] == "ambient"
    assert call["env"][SWITCH] == "1"
    assert os.environ[SWITCH] == "0"


@pytest.mark.parametrize("wrapper", list(_BOUNDS))
@pytest.mark.parametrize(
    ("argv", "kwargs"),
    [
        (["claude", "-p"], {"env": {SWITCH: "0"}}),
        (["claude", "-p"], {"shell": True}),
        (["claude", "-p"], {"shell": False}),
        (["claude", "-p"], {"executable": "/bin/sh"}),
        ("claude -p hello", {}),
        (b"claude -p hello", {}),
        (["claude", "-p", Path("prompt")], {}),
    ],
    ids=["env", "shell-true", "shell-false", "executable", "str-argv", "bytes-argv", "non-str-element"],
)
def test_wrapper_refuses_env_shell_executable_and_non_argv(
    wrapper: Any, argv: Any, kwargs: dict[str, Any], spawned: list[dict[str, Any]]
) -> None:
    with pytest.raises(TypeError, match=r"own|argv"):
        wrapper(argv, **kwargs, **_BOUNDS[wrapper])
    assert spawned == []


# --- Behaviour: each caller's child gets both controls and keeps its own policy ---------------


def _assert_child_controlled(argv: list[str], env: dict[str, str]) -> None:
    flag = argv.index("--disallowedTools")
    assert set(HEADLESS_BACKGROUND_TOOL_DENIES) <= set(argv[flag + 1].split(","))
    if "--" in argv:
        assert flag < argv.index("--")
    assert env[SWITCH] == "1"


@pytest.mark.usefixtures("ambient_switch_off")
def test_batch_rebuild_child_is_controlled(monkeypatch: pytest.MonkeyPatch, spawned: list[dict[str, Any]]) -> None:
    monkeypatch.syspath_prepend(str(SCRIPTS))
    from batch import batch_dispatcher_helpers as helpers

    monkeypatch.setattr(helpers, "supports_exclude_dynamic_system_prompt_sections", lambda _bin: False)

    assert helpers.dispatch_claude_fix("a1", "greetings", 1, timeout=77)["success"] is True
    (call,) = spawned
    _assert_child_controlled(call["argv"], call["env"])
    assert call["env"]["LU_AMBIENT_PROBE"] == "ambient"
    assert call["argv"][call["argv"].index("--permission-mode") + 1] == "bypassPermissions"
    assert (call["timeout"], call["cwd"], call["capture_output"]) == (77, str(helpers.PROJECT_ROOT), True)


def test_batch_rebuild_timeout_is_still_reported(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.syspath_prepend(str(SCRIPTS))
    from batch import batch_dispatcher_helpers as helpers

    def timed_out(argv: list[str], **kwargs: Any) -> None:
        raise subprocess.TimeoutExpired(argv, kwargs["timeout"])

    monkeypatch.setattr(claude_adapter.subprocess, "run", timed_out)
    monkeypatch.setattr(helpers, "supports_exclude_dynamic_system_prompt_sections", lambda _bin: False)
    result = helpers.dispatch_claude_fix("a1", "greetings", 1, timeout=3)
    assert (result["success"], result["returncode"], result["stdout_tail"]) == (False, -1, "TimeoutExpired")


@pytest.mark.usefixtures("ambient_switch_off")
def test_pipeline_phase_child_is_controlled_without_claudecode(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, spawned: list[dict[str, Any]]
) -> None:
    from scripts.pipeline import dispatch

    monkeypatch.setattr(dispatch, "supports_exclude_dynamic_system_prompt_sections", lambda _bin: False)
    monkeypatch.setenv("CLAUDECODE", "1")
    prompt_file = tmp_path / "phase.md"
    prompt_file.write_text("write the content", encoding="utf-8")

    ok, _ = dispatch.dispatch_claude_phase(prompt_file, "B content", timeout=44)

    assert ok
    (call,) = spawned
    _assert_child_controlled(call["argv"], call["env"])
    assert "CLAUDECODE" not in call["env"], "the pipeline's exclusion must survive the wrapper"
    assert call["env"]["LU_AMBIENT_PROBE"] == "ambient"
    assert (call["input"], call["timeout"]) == ("write the content", 44)


def test_pipeline_phase_stops_its_heartbeat_on_timeout(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    from scripts.pipeline import dispatch

    threads: list[Any] = []

    class RecordedThread(dispatch.threading.Thread):
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            super().__init__(*args, **kwargs)
            threads.append(self)

    def timed_out(argv: list[str], **kwargs: Any) -> None:
        raise subprocess.TimeoutExpired(argv, kwargs["timeout"])

    monkeypatch.setattr(dispatch.threading, "Thread", RecordedThread)
    monkeypatch.setattr(claude_adapter.subprocess, "run", timed_out)
    monkeypatch.setattr(dispatch, "supports_exclude_dynamic_system_prompt_sections", lambda _bin: False)
    prompt_file = tmp_path / "phase.md"
    prompt_file.write_text("write the content", encoding="utf-8")

    assert dispatch.dispatch_claude_phase(prompt_file, "B content", timeout=1) == (False, "")
    (thread,) = threads
    assert not thread.is_alive(), "the heartbeat thread must stop when the run ends"


@pytest.mark.usefixtures("ambient_switch_off")
@pytest.mark.parametrize("module_name", ["code_review_benchmark", "judge_calibration_matrix"])
def test_native_claude_benchmark_child_is_controlled(
    monkeypatch: pytest.MonkeyPatch, module_name: str, spawned: list[dict[str, Any]]
) -> None:
    import importlib

    module = importlib.import_module(f"scripts.audit.{module_name}")
    cell = module.Cell("anthropic", "claude-opus-5-5", "native_cli", "high", "no_mcp")

    call = module.run_native_cli(cell, "prompt")

    assert call.ok
    (child,) = spawned
    _assert_child_controlled(child["argv"], child["env"])
    assert child["argv"][-2:] == ["--", "prompt"]
    assert list(call.cmd) == child["argv"], "telemetry records the argv the child received"
    assert (child["timeout"], child["cwd"]) == (module.REQUEST_TIMEOUT_S, str(module.PROJECT_ROOT))


@pytest.mark.parametrize("module_name", ["code_review_benchmark", "judge_calibration_matrix"])
def test_native_benchmark_timeout_and_other_providers_are_retained(
    monkeypatch: pytest.MonkeyPatch, module_name: str
) -> None:
    import importlib

    module = importlib.import_module(f"scripts.audit.{module_name}")
    direct: list[list[str]] = []

    def timed_out(argv: list[str], **kwargs: Any) -> None:
        raise subprocess.TimeoutExpired(argv, kwargs["timeout"])

    def other_provider(argv: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        assert "env" not in kwargs
        direct.append(argv)
        return subprocess.CompletedProcess(argv, 0, stdout="verdict", stderr="")

    monkeypatch.setattr(claude_adapter.subprocess, "run", timed_out)
    call = module.run_native_cli(module.Cell("anthropic", "claude-opus-5-5", "native_cli", "high", "no_mcp"), "p")
    assert (call.ok, call.error) == (False, f"timed out after {module.REQUEST_TIMEOUT_S}s")

    monkeypatch.setattr(module.subprocess, "run", other_provider)
    assert module.run_native_cli(module.Cell("openai", "gpt-6.1-sol", "native_cli", "medium", "no_mcp"), "p").ok
    (argv,) = direct
    assert argv[0] == "codex" and "--disallowedTools" not in argv


@pytest.mark.usefixtures("ambient_switch_off")
def test_openai_proxy_claude_child_keeps_the_parent_env_exclusions(spawned: list[dict[str, Any]]) -> None:
    from scripts.ai_agent_bridge import openai_proxy as proxy

    response = proxy._claude_backend("claude-opus-5-5", [proxy.Message(role="user", content="hello")])

    assert response.content == "out"
    (call,) = spawned
    _assert_child_controlled(call["argv"], call["env"])
    expected = {"TERM": "xterm-256color", "COLORTERM": "truecolor", **proxy._PARENT_ENV, SWITCH: "1"}
    assert call["env"] == expected, "the child gets _PARENT_ENV, never the ambient env"
    assert "LU_AMBIENT_PROBE" not in call["env"]
    assert "hello" in call["input"]
    assert call["timeout"] == proxy._backend_timeout_s()


def test_openai_proxy_claude_failure_is_still_translated(monkeypatch: pytest.MonkeyPatch) -> None:
    from scripts.ai_agent_bridge import openai_proxy as proxy

    monkeypatch.setattr(
        claude_adapter.subprocess,
        "run",
        lambda argv, **kwargs: subprocess.CompletedProcess(argv, 3, stdout="", stderr="quota"),
    )
    with pytest.raises(subprocess.CalledProcessError) as raised:
        proxy._claude_backend("claude-opus-5-5", [proxy.Message(role="user", content="hello")])
    assert (raised.value.returncode, raised.value.stderr) == (3, "quota")


_ZNO_CONFIG = {
    "schema": "zno-nmt.config.v1",
    "adapter": "claude",
    "model": "local-test-model",
    "effort": None,
    "timeout_seconds": 15,
    "max_output_tokens": 100,
    "max_tool_calls": 2,
    "repeats": 1,
    "tools": ["verify_word"],
    "corpus_id": "fixture-corpus",
    "claude_bin": "claude-fixture",
}
_ZNO_PACKET = {
    "schema": "zno-nmt.questions.v1",
    "packet_sha256": "a" * 64,
    "items": [{"id": "opaque-1", "kind": "single", "question": "Q", "options": [{"id": "A", "text": "A"}], "rows": []}],
}


@pytest.mark.usefixtures("ambient_switch_off")
def test_zno_eval_claude_child_keeps_its_restricted_env(monkeypatch: pytest.MonkeyPatch) -> None:
    from scripts.eval.zno_nmt import adapters

    seen: dict[str, Any] = {}
    stdout = "\n".join(
        [
            json.dumps({"type": "system", "subtype": "init", "model": "local-test-model", "tools": []}),
            json.dumps({"type": "result", "result": json.dumps({"responses": {"opaque-1": "A"}})}),
        ]
    )

    class FakePopen:
        def __init__(self, argv: list[str], **kwargs: Any) -> None:
            seen.update(argv=argv, **kwargs)
            self.pid = 0
            self.returncode = 0

        def communicate(self, prompt: str | None = None, timeout: float | None = None) -> tuple[str, str]:
            seen["input"] = prompt
            return stdout, ""

    monkeypatch.setattr(adapters, "_claude_capabilities", lambda *_args, **_kwargs: ("claude-fixture", "2.1.fixture"))
    monkeypatch.setattr(claude_adapter.subprocess, "Popen", FakePopen)

    result = adapters.run_claude(_ZNO_PACKET, _ZNO_CONFIG, "closed-book", sources_url=None, prompt="exam")

    assert result["responses"] == {"opaque-1": "A"}
    _assert_child_controlled(seen["argv"], seen["env"])
    assert seen["env"] == {**adapters._child_env(100), SWITCH: "1"}, "only the allowlisted env reaches the child"
    assert "LU_AMBIENT_PROBE" not in seen["env"]
    assert seen["argv"][seen["argv"].index("--tools") + 1] == ""
    assert seen["start_new_session"] is True
    assert seen["input"] == "exam"


def test_zno_eval_timeout_kills_the_process_group_and_drains(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    from scripts.eval.zno_nmt import adapters

    seen: dict[str, Any] = {"drained": 0}

    class TimedOutProcess:
        pid = 321

        def communicate(self, _prompt: str | None = None, *, timeout: float | None = None) -> tuple[str, str]:
            if timeout is not None:
                raise subprocess.TimeoutExpired("claude", timeout)
            seen["drained"] += 1
            return "", ""

    monkeypatch.setattr(
        claude_adapter.subprocess, "Popen", lambda argv, **kwargs: seen.update(env=kwargs["env"]) or TimedOutProcess()
    )
    monkeypatch.setattr(adapters.os, "killpg", lambda pid, sig: seen.update(kill=(pid, sig)))

    with pytest.raises(adapters.AdapterError, match="timeout"):
        adapters._run_claude_process(["claude", "-p"], cwd=tmp_path, env={"PATH": "/bin"}, prompt="exam", timeout=1)
    assert seen["kill"] == (321, adapters.signal.SIGKILL)
    assert seen["drained"] == 1
    assert seen["env"] == {"PATH": "/bin", SWITCH: "1"}


@pytest.mark.usefixtures("ambient_switch_off")
def test_isolated_claude_review_spawn_is_controlled_and_keeps_the_reviewer_env(
    tmp_path: Path, spawned: list[dict[str, Any]]
) -> None:
    from scripts.review.isolation import build_claude_review_argv, run_claude_review

    binary = tmp_path / "claude"
    binary.write_text("#!/bin/sh\n", encoding="utf-8")
    reviewer_env = {"HOME": "/h", "PATH": "/usr/bin", SWITCH: "0"}

    completed = run_claude_review(
        binary, prompt="review", json_schema={"type": "object"}, env=reviewer_env, timeout=30, cwd=tmp_path
    )

    assert completed.stdout == "out"
    (call,) = spawned
    _assert_child_controlled(call["argv"], call["env"])
    assert call["env"] == {"HOME": "/h", "PATH": "/usr/bin", SWITCH: "1"}, "only the reviewer env reaches the child"
    assert call["argv"] == build_claude_review_argv(binary, prompt="review", json_schema={"type": "object"})
    assert call["argv"][call["argv"].index("--tools") + 1] == "Read,Grep,Glob"
    assert call["argv"][-2:] == ["--", "review"]
    assert (call["timeout"], call["cwd"], call["capture_output"]) == (30, str(tmp_path), True)


# --- The round-3 bypass shapes lose their window ---------------------------------------------
#
# Each shape below hid an ambient env from the old data-flow scanner. Through a
# raw spawn the rule rejects it (fixtures further down); through the wrapper the
# env it computes is only a base, and the child still gets the switch.


def _loop_exit(slug: str) -> None:
    import os

    env = {SWITCH: "1"}
    while slug == "retry":
        env = dict(os.environ)
        break
    else:
        env = {SWITCH: "1"}
    run_headless_claude(["claude", "-p", slug], base_env=env, timeout=5)


def _long_back_edge(slug: str) -> None:
    import os

    e1 = e2 = e3 = e4 = e5 = {SWITCH: "1"}
    for _ in range(6):
        e1, e2, e3, e4, e5 = e2, e3, e4, e5, dict(os.environ)
    run_headless_claude(["claude", "-p", slug], base_env=e1, timeout=5)


def _closure(slug: str) -> None:
    import os

    env = {SWITCH: "1"}

    def reset() -> None:
        nonlocal env
        env = dict(os.environ)

    reset()
    run_headless_claude(["claude", "-p", slug], base_env=env, timeout=5)


@pytest.mark.usefixtures("ambient_switch_off")
@pytest.mark.parametrize("shape", [_loop_exit, _long_back_edge, _closure], ids=["loop-exit", "back-edge", "nonlocal"])
def test_round3_shapes_through_the_wrapper_still_force_the_switch(shape: Any, spawned: list[dict[str, Any]]) -> None:
    shape("retry")
    (call,) = spawned
    assert call["env"]["LU_AMBIENT_PROBE"] == "ambient", "the shape did smuggle the ambient env in"
    _assert_child_controlled(call["argv"], call["env"])


# --- The rule: rejection and acceptance fixtures ------------------------------------------------

_IMPORT = (
    "import os, shlex, subprocess, asyncio\nfrom scripts.agent_runtime.adapters.claude import run_headless_claude\n"
)


def _problems(body: str, exceptions: list[Exception_] | None = None) -> list[str]:
    path = "scripts/fixture.py"
    findings = check_module(_IMPORT + textwrap.dedent(body), path)
    assert findings is not None, "fixture is not a Claude-referencing module"
    return problems({path: findings}, exceptions or [])


_REJECTED = {
    # Direct spawns of every named API (each escaped or was caught by earlier scanners).
    "run-literal": 'def run(p):\n    subprocess.run(["claude", "-p", p])\n',
    "absolute-path": 'def run(p):\n    subprocess.run(["/usr/local/bin/claude", "--print", "--", p])\n',
    "named-binary": "def run(p):\n    subprocess.run([CLAUDE_BIN, '-p', p], env=os.environ)\n",
    "spread-command": 'def run(p):\n    subprocess.run([*CLAUDE_CMD, "--print", "--bare"], input=p)\n',
    "shlex-split": 'def run(prompt):\n    subprocess.run(shlex.split("claude --print") + [prompt])\n',
    "shell-string": 'def run():\n    subprocess.run("claude -p hello", shell=True)\n',
    "os-system": 'def run():\n    os.system("env A=1 claude -p hi")\n',
    "os-popen": 'def run():\n    os.popen("claude -p hi")\n',
    "bash-c": 'def run():\n    subprocess.run(["bash", "-c", "claude -p hi"])\n',
    "exe-variable": 'def run(prompt):\n    exe = "claude"\n    subprocess.run([exe, "-p", prompt])\n',
    "imported-print-flag": 'from elsewhere import FLAGS\ndef run(p):\n    subprocess.run(["claude", *FLAGS, p])\n',
    "wrapped-timeout": 'def run(p):\n    subprocess.run(["timeout", "60", "claude", "-p", p])\n',
    "popen-kw": 'def run(p):\n    subprocess.Popen(args=["claude", "-p", p])\n',
    "check-output": 'def run(p):\n    subprocess.check_output(["claude", "-p", p])\n',
    "getoutput": 'def run():\n    subprocess.getoutput("claude -p hi")\n',
    "asyncio-exec": 'async def run(p):\n    await asyncio.create_subprocess_exec("claude", "-p", p)\n',
    "asyncio-shell": 'async def run():\n    await asyncio.create_subprocess_shell("claude -p hi")\n',
    "asyncio-subprocess": 'async def run(p):\n    await asyncio.subprocess.create_subprocess_exec("claude", "-p", p)\n',
    "execvp": 'def run(p):\n    os.execvp("claude", ["claude", "-p", p])\n',
    "spawnvp": 'def run(p):\n    os.spawnvp(os.P_WAIT, "claude", ["claude", "-p", p])\n',
    "posix-spawn": 'def run(p):\n    os.posix_spawn("/bin/claude", ["claude", "-p", p], {})\n',
    "pty-spawn": 'import pty\ndef run(p):\n    pty.spawn(["claude", "-p", p])\n',
    "local-wrapper": 'def _go(argv, env=None):\n    return subprocess.run(argv, env=env)\ndef run(p):\n    return _go(["claude", "-p", p])\n',
    "module-level": 'subprocess.run(["claude", "-p", "hi"])\n',
    # Round 1-2 forms: controls computed but bypassed; any raw spawn is now a site.
    "constants-unused": (
        "from scripts.agent_runtime.adapters.claude import HEADLESS_BACKGROUND_ENV\n"
        'def run(p):\n    unused = HEADLESS_BACKGROUND_ENV\n    subprocess.run(["claude", "-p", p])\n'
    ),
    "env-replaced-on-a-branch": (
        'def run(p, raw):\n    env = {**os.environ, "CLAUDE_CODE_DISABLE_BACKGROUND_TASKS": "1"}\n'
        '    if raw:\n        env = os.environ\n    subprocess.run(["claude", "-p", p], env=env)\n'
    ),
    "switch-removed-on-a-branch": (
        'def run(p, raw):\n    env = {**os.environ, "CLAUDE_CODE_DISABLE_BACKGROUND_TASKS": "1"}\n'
        '    if raw:\n        env.pop("CLAUDE_CODE_DISABLE_BACKGROUND_TASKS")\n    subprocess.run(["claude", "-p", p], env=env)\n'
    ),
    # Round-3 probes, raw spawn form.
    "round3-loop-exit": (
        'def run(p, slug):\n    env = {"CLAUDE_CODE_DISABLE_BACKGROUND_TASKS": "1"}\n'
        "    while slug == 'retry':\n        env = dict(os.environ)\n        break\n    else:\n        pass\n"
        '    subprocess.run(["claude", "-p", p], env=env)\n'
    ),
    "round3-back-edge": (
        'def run(p):\n    e1 = e2 = e3 = e4 = e5 = {"CLAUDE_CODE_DISABLE_BACKGROUND_TASKS": "1"}\n'
        "    for _ in range(6):\n        e1, e2, e3, e4, e5 = e2, e3, e4, e5, dict(os.environ)\n"
        '    subprocess.run(["claude", "-p", p], env=e1)\n'
    ),
    "round3-nonlocal": (
        "def run(p):\n    env = {}\n    def reset():\n        nonlocal env\n        env = dict(os.environ)\n"
        '    reset()\n    subprocess.run(["claude", "-p", p], env=env)\n'
    ),
    # Round-3 probes, wrapper form passing the env itself.
    "round3-wrapper-env": (
        "def run(p):\n    env = {}\n    def reset():\n        nonlocal env\n        env = dict(os.environ)\n"
        '    reset()\n    run_headless_claude(["claude", "-p", p], env=env)\n'
    ),
    # The decision's opaque-helper example: a Claude argv handed to a repository helper.
    "generic-runner-launch": (
        'from generic_runner import launch\ndef run(prompt):\n    argv = ["claude", "-p", prompt]\n'
        "    launch(argv, env=os.environ)\n"
    ),
    "argv-to-local-opaque-call": 'def run(p):\n    _helpers.execute([CLAUDE_BIN, "--print", p])\n',
    # Shell-command literals that run claude -p, wherever they go.
    "shell-literal-to-helper": 'def run():\n    run_shell("cd /tmp && claude -p hello")\n',
    "shell-fstring-to-helper": 'def run(p):\n    run_shell(f"cd /tmp && claude --model m -p {p}")\n',
    # Import aliases and dynamic access to the spawn modules.
    "aliased-module": 'import subprocess as sp\ndef run(p):\n    sp.run(["claude", "-p", p])\n',
    "from-import-run": 'from subprocess import run as go\ndef run_it(p):\n    go(["claude", "-p", p])\n',
    "from-import-popen": "from subprocess import Popen\n",
    "from-import-system": "from os import system\n",
    "from-import-star": "from subprocess import *\n",
    "from-import-asyncio-api": "from asyncio import create_subprocess_exec\n",
    "from-asyncio-import-subprocess": "from asyncio import subprocess as aio\n",
    "importlib": 'import importlib\ndef run(p):\n    importlib.import_module("subprocess").run(["claude", "-p", p])\n',
    "dunder-import": 'def run(p):\n    __import__("subprocess").run(["claude", "-p", p])\n',
    "sys-modules": 'import sys\ndef run(p):\n    sys.modules["subprocess"].run(["claude", "-p", p])\n',
    "getattr-api": 'def run(p):\n    getattr(subprocess, "run")(["claude", "-p", p])\n',
    "module-as-value": 'def run(p):\n    helper(subprocess).run(["claude", "-p", p])\n',
    "api-reference": 'def run(p):\n    go = subprocess.run\n    go(["claude", "-p", p])\n',
    "partial": 'import functools\ndef run(p):\n    functools.partial(subprocess.Popen, ["claude", "-p", p])()\n',
    "api-through-another-module": (
        'from scripts.agent_runtime.adapters import claude as adapter\ndef run(p):\n    adapter.subprocess.run(["claude", "-p", p])\n'
    ),
    # Shadowing and rebinding of the spawn modules.
    "shadow-assign": "subprocess = object()\n",
    "shadow-param": "def run(p, subprocess):\n    return subprocess\n",
    "shadow-for": "def run(mods):\n    for os in mods:\n        pass\n",
    "shadow-with": "def run(cm):\n    with cm as subprocess:\n        pass\n",
    "shadow-except": "def run():\n    try:\n        pass\n    except OSError as os:\n        pass\n",
    "shadow-walrus": "def run(x):\n    if (subprocess := x):\n        pass\n",
    "shadow-global": "def run():\n    global subprocess\n",
    "shadow-import": "import fake_spawner as subprocess\n",
    "shadow-def": "def subprocess():\n    pass\n",
    "shadow-match": "def run(x):\n    match x:\n        case subprocess:\n            pass\n",
    "monkeypatch-api": "subprocess.run = print\n",
    "delete-module": "del subprocess\n",
    # Canonical wrapper bindings.
    "wrapper-env": 'def run(p):\n    run_headless_claude(["claude", "-p", p], env=os.environ)\n',
    "wrapper-shell": 'def run():\n    run_headless_claude("claude -p hi", shell=True)\n',
    "wrapper-executable": 'def run(p):\n    run_headless_claude(["x", "-p", p], executable="/bin/claude")\n',
    "wrapper-string-argv": 'def run(p):\n    run_headless_claude(f"claude -p {p}")\n',
    "wrapper-rebound": "def run_headless_claude(argv, **kwargs):\n    return None\n",
    "wrapper-shadowed-locally": "def run(p):\n    run_headless_claude = print\n",
    "wrapper-as-value": "def run(p):\n    return helper(run_headless_claude)\n",
    "wrapper-aliased": "from scripts.agent_runtime.adapters.claude import run_headless_claude as rhc\n",
    "wrapper-from-elsewhere": "from scripts.elsewhere import popen_headless_claude\n",
    "wrapper-via-attribute": (
        'from scripts.agent_runtime.adapters import claude as adapter\ndef run(p):\n    adapter.run_headless_claude(["claude", "-p", p])\n'
    ),
}


@pytest.mark.parametrize("body", list(_REJECTED.values()), ids=list(_REJECTED))
def test_rule_rejects(body: str) -> None:
    assert _problems(body)


_ACCEPTED = {
    "wrapper": 'def run(p):\n    return run_headless_claude(["claude", "-p", p], base_env={"PATH": "/bin"}, timeout=5)\n',
    "wrapper-kwargs": 'def run(p, **options):\n    return run_headless_claude([CLAUDE_BIN, "--print", p], **options)\n',
    "popen-wrapper": (
        "from scripts.agent_runtime.adapters.claude import popen_headless_claude\n"
        'def run(p):\n    return popen_headless_claude(["claude", "-p", p], start_new_session=True)\n'
    ),
    "builder-then-wrapper": (
        "from scripts.agent_runtime.adapters.claude import headless_claude_argv\n"
        'def build(p):\n    return headless_claude_argv(["claude", "-p", p])\n'
    ),
    "non-spawn-uses": (
        "def run(proc):\n    try:\n        return subprocess.PIPE, os.environ.get('CLAUDE_BIN'), os.pathsep\n"
        "    except subprocess.TimeoutExpired:\n        return getattr(os, 'O_NOFOLLOW', 0)\n"
    ),
    "annotation": "def run(proc: subprocess.Popen[str]) -> subprocess.Popen[str]:\n    return proc\n",
    "docstring": 'def run():\n    """Start ``claude -p hello`` through the wrapper."""\n',
    "claude-probe-text": 'MESSAGE = "install claude, then run it"\n',
    "relative-adapter-import": "from .claude import popen_headless_claude\n",
}


@pytest.mark.parametrize("body", list(_ACCEPTED.values()), ids=list(_ACCEPTED))
def test_rule_accepts(body: str) -> None:
    assert _problems(body) == []


def test_rule_accepts_a_reviewed_exception_and_only_for_its_program() -> None:
    body = 'def status():\n    return subprocess.run(["git", "status"])\n'
    entry = Exception_("scripts/fixture.py", "status", "git", "non-claude", "runs git")
    assert _problems(body, [entry]) == []
    assert _problems(body.replace('"git"', '"claude"'), [entry]), "an entry covers its program only"


def test_exception_checks_catch_stale_and_miscategorised_entries() -> None:
    path = "scripts/fixture.py"
    source = (
        _IMPORT
        + 'def probe():\n    subprocess.run(["claude", "-p", "x"])\ndef build(p):\n    return [CLAUDE_BIN, "-p", p]\n'
    )
    module = check_module(source, path)
    assert module is not None
    findings = {path: module}
    entries = [
        Exception_(path, "probe", "claude", "claude-probe", "not a probe"),
        Exception_(path, "probe", "claude", "claude-probe", "duplicate"),
        Exception_(path, "gone", "git", "non-claude", "stale"),
        Exception_(path, "probe", "claude", "nonsense", ""),
        Exception_(path, "build", HOLDER, "argv-builder", "no spawner", spawned_by="probe"),
    ]
    errors = exception_errors(findings, entries, set())
    assert any("not a fixed --version/--help probe" in e for e in errors)
    assert any("duplicate exception" in e for e in errors)
    assert any("stale exception" in e for e in errors)
    assert any("known category and a reason" in e for e in errors)
    assert any("argv-builder must" in e for e in errors)


def test_limit_a_module_without_a_claude_reference_is_not_checked() -> None:
    """Documented limit: the executable reaches it only as another module's value or from the environment."""
    source = 'import subprocess\nfrom cfg import BIN\ndef run(p):\n    subprocess.run([BIN, "-p", p])\n'
    assert check_module(source, "scripts/opaque.py") is None


def test_limit_an_argv_handed_on_across_functions_is_not_tied() -> None:
    """Documented opaque-helper limit: the holder rule needs a Claude token and a print-flag literal in one
    function. A print flag imported from elsewhere, or a builder whose program is an opaque value, handed
    to a helper is not tied to it. (A builder that names Claude and a print flag is held.)"""
    assert _problems('from elsewhere import FLAGS\ndef run(p):\n    launch(["claude", *FLAGS, p])\n') == []
    assert (
        _problems('def build(p):\n    return [BIN, "-p", p]\ndef run(p):\n    launch(build(p))\nX = "claude"\n') == []
    )
    assert _problems('def build(p):\n    return ["claude", "-p", p]\n')


# --- Shell discovery ----------------------------------------------------------------------


@pytest.mark.parametrize(
    "script",
    [
        "claude -p hello\n",
        'claude --model "$M" -p hello\n',
        "claude --model m \\\n  --output-format text \\\n  -p hello\n",
        "alias cc='claude --model m'\ncc -p hello\n",
        'CLAUDE_BIN="${KIMICC_CLAUDE_BIN:-claude}"\nCMD=("$CLAUDE_BIN" -p --bare)\nexec "${CMD[@]}"\n',
        'BIN=$(command -v claude)\n"$BIN" --print hi\n',
        'out=$(timeout 60 claude -p "$prompt")\n',
        'run_cc() {\n  claude "$@"\n}\nrun_cc -p hi\n',
        "if true; then env A=1 /opt/bin/claude -p x; fi\n",
    ],
)
def test_shell_scan_finds_print_mode_claude(script: str) -> None:
    assert shell_claude_print_lines(script)


@pytest.mark.parametrize(
    "script",
    [
        'mkdir -p "$HOME/.claude/hooks"\n',
        "# claude -p is how headless runs start\n",
        'echo "run claude -p yourself"\n',
        "cat <<EOF\nclaude -p hello\nEOF\n",
        'exec claude --model "$M" "$@"\n',
        '"$CLAUDE_DIR/hooks/guard.sh" -p\n',
    ],
)
def test_shell_scan_ignores_other_commands(script: str) -> None:
    assert shell_claude_print_lines(script) == []


def test_shell_launcher_check_requires_a_runner_test_naming_the_script() -> None:
    """Imported-but-unused constants or an unrelated test cannot vouch for a shell launcher."""
    tests_source = (
        "from x import HEADLESS_BACKGROUND_ENV, HEADLESS_BACKGROUND_TOOL_DENIES\n"
        "def test_unrelated():\n    assert HEADLESS_BACKGROUND_ENV and HEADLESS_BACKGROUND_TOOL_DENIES\n"
        "def test_runs_new():\n    launch('new_headless.sh')\n"
    )
    launching = {"scripts/new_headless.sh"}
    assert _shell_launcher_errors(launching, {}, tests_source) == ["unmapped shell launcher: scripts/new_headless.sh"]
    assert _shell_launcher_errors(launching, {"scripts/new_headless.sh": "test_unrelated"}, tests_source) == [
        "test_unrelated does not launch new_headless.sh"
    ]
    assert _shell_launcher_errors(launching, {"scripts/new_headless.sh": "test_runs_new"}, tests_source) == []
