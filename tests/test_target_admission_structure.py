"""Static proof that targets are admitted in the same step they are resolved.

``scripts/agent_runtime/target_admission.py`` ``resolve_and_admit`` is the only
producer of an ``AdmittedTarget``: it runs every resolution step and then the
Kimi gate. This scan of the bridge, fleet-comms, agent runtime and
``delegate.py`` fails when

- a resolver (slot holders, attachment merging, fallback substitution, ACP
  route and compat lookups) is called or imported outside that module;
- the Kimi gate is called directly instead of through ``resolve_and_admit``
  (``kimi_admission`` keeps its execution-time re-check);
- an ``AdmittedTarget`` is constructed outside that module;
- a delivery, insertion, wake or launch sink (any parameter annotated
  ``AdmittedTarget``, and the required sinks below) is called with a value
  that is not produced by ``resolve_and_admit`` or an admitter built on it.

The data flow is checked per function and flow-insensitively: a name is
admitted only when every binding of it in the function is admitted (a
greatest fixpoint, so a loop variable reused across loops over admitted
targets stays admitted).
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
HOME = REPO_ROOT / "scripts" / "agent_runtime" / "target_admission.py"
GATE_HOME = REPO_ROOT / "scripts" / "agent_runtime" / "kimi_admission.py"


def _scanned_files() -> list[Path]:
    files: list[Path] = []
    for package in ("ai_agent_bridge", "fleet_comms", "agent_runtime"):
        files.extend(sorted((REPO_ROOT / "scripts" / package).rglob("*.py")))
    files.append(REPO_ROOT / "scripts" / "delegate.py")
    return files


# Functions that resolve who a request reaches. Called from target_admission.py only.
RESOLVERS = frozenset(
    {
        "resolve_slot_holder",  # a role slot to its live holder
        "effective_request_targets",  # data attachments to seats and models
        "_resolve_delivery_agent",  # removed: resolved a slot after the channel gate
        "_slot_holder",
        "_substitute_seat",
        "_acp_routes",
        "_compat_names",
    }
)
# The gate itself; reached through resolve_and_admit (kimi_admission keeps its execution re-check).
GATE = "refuse_kimi_if_disallowed"

# Functions whose result is (or carries) targets from resolve_and_admit. Each one
# other than resolve_and_admit must itself call an admitter (checked below).
ADMITTERS = frozenset(
    {
        "resolve_and_admit",
        "admit_compat_target",
        "_admit_recipients",
        "_admitted_subscribers",
        "_resolve_quota_substitution",
        "_substitute_seat_for_decision",
        "_admit_dispatch_target",
        "_kimi_dispatch_gate",
        "_kimi_worker_refusal",
    }
)
# ``require_admitted(x)`` is admitted exactly when ``x`` is.
PASS_THROUGH = frozenset({"require_admitted"})

# Every delivery, insertion, wake and launch sink, and the parameter that takes the target.
REQUIRED_SINKS = {
    "_insert_message": "target",  # bridge message row
    "_insert_delivery": "target",  # channel delivery row
    "_touch_wake_file": "target",  # channel wake file
    "_run_single_acp_job": "target",  # ACP job enqueue and invocation
    "maybe_forward_compat_ask": "target",  # job-host ask forward
    "build_ask_review_dispatch_command": "target",  # headless review launch argv
    "_worker_route_argv": "target",  # delegate worker launch argv
    "_subscribe_tx": "target",  # fleet-comms subscriber row
    "_publish_message_tx": "targets",  # fleet-comms message and delivery rows
}


def _rel(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def _call_name(node: ast.Call) -> str | None:
    func = node.func
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return None


def _annotation_text(node: ast.expr | None) -> str:
    return ast.unparse(node) if node is not None else ""


@dataclass(frozen=True)
class Sink:
    name: str
    param: str
    index: int | None  # positional index at the call site (self/cls excluded)


def _function_params(node: ast.FunctionDef | ast.AsyncFunctionDef) -> list[ast.arg]:
    return [*node.args.posonlyargs, *node.args.args]


def _is_method(node: ast.FunctionDef | ast.AsyncFunctionDef, parents: dict[ast.AST, ast.AST]) -> bool:
    return isinstance(parents.get(node), ast.ClassDef)


class Scan:
    def __init__(self) -> None:
        self.trees: dict[Path, ast.Module] = {}
        self.parents: dict[Path, dict[ast.AST, ast.AST]] = {}
        for path in _scanned_files():
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            self.trees[path] = tree
            self.parents[path] = {child: parent for parent in ast.walk(tree) for child in ast.iter_child_nodes(parent)}
        self.sinks = self._collect_sinks()

    def functions(self) -> list[tuple[Path, ast.FunctionDef | ast.AsyncFunctionDef]]:
        return [
            (path, node)
            for path, tree in self.trees.items()
            for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        ]

    def _collect_sinks(self) -> dict[str, Sink]:
        sinks: dict[str, Sink] = {}
        for path, node in self.functions():
            params = _function_params(node)
            offset = 1 if _is_method(node, self.parents[path]) and params and params[0].arg in {"self", "cls"} else 0
            for position, arg in enumerate(params):
                if "AdmittedTarget" in _annotation_text(arg.annotation):
                    sinks[node.name] = Sink(node.name, arg.arg, position - offset)
            for arg in node.args.kwonlyargs:
                if "AdmittedTarget" in _annotation_text(arg.annotation):
                    sinks[node.name] = Sink(node.name, arg.arg, None)
        return sinks


@pytest.fixture(scope="module")
def scan() -> Scan:
    return Scan()


def _enclosing_function(node: ast.AST, parents: dict[ast.AST, ast.AST]) -> ast.AST | None:
    current = parents.get(node)
    while current is not None and not isinstance(current, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
        current = parents.get(current)
    return current


class AdmittedNames:
    """Names admitted in one function: every binding comes from an admitter (flow-insensitive)."""

    def __init__(self, function: ast.AST, outer: AdmittedNames | None) -> None:
        self.outer = outer
        self.bindings: dict[str, list[ast.expr | None]] = {}
        self.appends: dict[str, list[ast.expr]] = {}
        own_nodes = self._own_nodes(function)
        if isinstance(function, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for arg in [*_function_params(function), *function.args.kwonlyargs]:
                annotated = "AdmittedTarget" in _annotation_text(arg.annotation)
                # An annotated parameter is admitted: its callers are checked as sink calls.
                self.bindings.setdefault(arg.arg, []).append(ast.Name(id="__admitted__") if annotated else None)
        elif isinstance(function, ast.Lambda):
            for arg in function.args.args:
                self.bindings.setdefault(arg.arg, []).append(None)
        for node in own_nodes:
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    self._bind(target, node.value)
            elif isinstance(node, (ast.AnnAssign, ast.AugAssign)) and isinstance(node.target, ast.Name):
                self._bind(node.target, getattr(node, "value", None))
            elif isinstance(node, (ast.For, ast.AsyncFor, ast.comprehension)):
                self._bind(node.target, ast.Subscript(value=node.iter, slice=ast.Constant(0)))
            elif isinstance(node, ast.NamedExpr):
                self._bind(node.target, node.value)
            elif isinstance(node, ast.With):
                for item in node.items:
                    if item.optional_vars is not None:
                        self._bind(item.optional_vars, None)
            elif (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr in {"append", "extend"}
                and isinstance(node.func.value, ast.Name)
                and node.args
            ):
                value = node.args[0]
                if node.func.attr == "extend":
                    value = ast.Subscript(value=value, slice=ast.Constant(0))
                self.appends.setdefault(node.func.value.id, []).append(value)
        # Greatest fixpoint: assume every bound name admitted, then drop any name with a
        # binding that is not, until stable. Cycles among admitted sources stay admitted.
        self.admitted: set[str] = set(self.bindings)
        changed = True
        while changed:
            changed = False
            for name, values in self.bindings.items():
                if name in self.admitted and not all(self._binding_admitted(name, value) for value in values):
                    self.admitted.discard(name)
                    changed = True

    @staticmethod
    def _own_nodes(function: ast.AST) -> list[ast.AST]:
        """The nodes of ``function`` excluding nested function bodies."""
        nodes: list[ast.AST] = []
        stack = list(ast.iter_child_nodes(function))
        while stack:
            node = stack.pop()
            nodes.append(node)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.ClassDef)):
                continue
            stack.extend(ast.iter_child_nodes(node))
        return nodes

    def _bind(self, target: ast.expr, value: ast.expr | None) -> None:
        if isinstance(target, ast.Name):
            self.bindings.setdefault(target.id, []).append(value)
        elif isinstance(target, (ast.Tuple, ast.List)):
            if isinstance(value, (ast.Tuple, ast.List)) and len(value.elts) == len(target.elts):
                for element, element_value in zip(target.elts, value.elts, strict=True):
                    self._bind(element, element_value)
            else:
                for element in target.elts:
                    inner = element.value if isinstance(element, ast.Starred) else element
                    self._bind(inner, value)
        elif isinstance(target, ast.Starred):
            self._bind(target.value, value)

    def _binding_admitted(self, name: str, value: ast.expr | None) -> bool:
        if value is None:
            return False
        if isinstance(value, ast.List) and not value.elts:
            appended = self.appends.get(name)
            return bool(appended) and all(self.is_admitted(item) for item in appended)
        return self.is_admitted(value)

    def is_admitted(self, expr: ast.expr) -> bool:
        if isinstance(expr, ast.Name):
            if expr.id == "__admitted__" or expr.id in self.admitted:
                return True
            if expr.id not in self.bindings and self.outer is not None:
                return self.outer.is_admitted(expr)
            return False
        if isinstance(expr, ast.Call):
            name = _call_name(expr)
            if name in ADMITTERS:
                return True
            if name in PASS_THROUGH and expr.args:
                return self.is_admitted(expr.args[0])
            return False
        if isinstance(expr, (ast.Tuple, ast.List)):
            return bool(expr.elts) and all(self.is_admitted(element) for element in expr.elts)
        if isinstance(expr, ast.Subscript):
            return self.is_admitted(expr.value)
        if isinstance(expr, ast.IfExp):
            return all(
                self.is_admitted(branch) or (isinstance(branch, ast.Constant) and branch.value is None)
                for branch in (expr.body, expr.orelse)
            )
        return False


def _admitted_names(path: Path, function: ast.AST | None, scan: Scan, cache: dict) -> AdmittedNames | None:
    if function is None:
        return None
    key = (path, id(function))
    if key not in cache:
        outer = _admitted_names(path, _enclosing_function(function, scan.parents[path]), scan, cache)
        cache[key] = AdmittedNames(function, outer)
    return cache[key]


def test_every_required_sink_takes_an_admitted_target(scan):
    missing = {
        name: param
        for name, param in REQUIRED_SINKS.items()
        if name not in scan.sinks or scan.sinks[name].param != param
    }
    assert not missing, f"sinks without an AdmittedTarget-annotated parameter: {missing}"


def test_every_admitter_is_built_on_resolve_and_admit(scan):
    defined: dict[str, list[ast.AST]] = {}
    for _path, node in scan.functions():
        if node.name in ADMITTERS:
            defined.setdefault(node.name, []).append(node)
    assert set(defined) == ADMITTERS, f"admitters not defined: {sorted(ADMITTERS - set(defined))}"
    ungrounded = []
    for name, nodes in defined.items():
        if name == "resolve_and_admit":
            continue
        for node in nodes:
            calls = {_call_name(call) for call in ast.walk(node) if isinstance(call, ast.Call)}
            if not calls & ADMITTERS:
                ungrounded.append(name)
    assert not ungrounded, f"admitters that never call resolve_and_admit or another admitter: {ungrounded}"


def test_sinks_are_called_only_with_admitted_targets(scan):
    violations = []
    cache: dict = {}
    for path, tree in scan.trees.items():
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            sink = scan.sinks.get(_call_name(node) or "")
            if sink is None:
                continue
            value = next((kw.value for kw in node.keywords if kw.arg == sink.param), None)
            if value is None and sink.index is not None and sink.index < len(node.args):
                value = node.args[sink.index]
            if value is None:
                violations.append(f"{_rel(path)}:{node.lineno} {sink.name}() without its {sink.param!r} target")
                continue
            if isinstance(value, ast.Constant) and value.value is None:
                continue  # an explicit "no targets" (fleet-comms subscriber fan-out and history import)
            names = _admitted_names(path, _enclosing_function(node, scan.parents[path]), scan, cache)
            if names is None or not names.is_admitted(value):
                violations.append(
                    f"{_rel(path)}:{node.lineno} {sink.name}({sink.param}={ast.unparse(value)}) "
                    "is not a target from resolve_and_admit"
                )
    assert not violations, "\n".join(violations)


def test_resolvers_and_the_gate_are_called_only_through_resolve_and_admit(scan):
    violations = []
    for path, tree in scan.trees.items():
        if path == HOME:
            continue
        for node in ast.walk(tree):
            names: list[tuple[str, int]] = []
            if isinstance(node, ast.Call):
                names.append((_call_name(node) or "", node.lineno))
            elif isinstance(node, ast.ImportFrom):
                names.extend((alias.name, node.lineno) for alias in node.names)
            for name, line in names:
                if name in RESOLVERS:
                    violations.append(f"{_rel(path)}:{line} resolver {name} outside resolve_and_admit")
                if name == GATE and path != GATE_HOME:
                    violations.append(f"{_rel(path)}:{line} direct Kimi gate {name}; use resolve_and_admit")
                if name == "AdmittedTarget" and isinstance(node, ast.Call):
                    violations.append(f"{_rel(path)}:{line} AdmittedTarget constructed outside resolve_and_admit")
    assert not violations, "\n".join(violations)


def test_compat_targets_are_looked_up_only_in_resolve_and_admit(scan):
    violations = []
    for path, tree in scan.trees.items():
        if path == HOME:
            continue
        aliases = {
            alias.asname or alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
            for alias in node.names
            if alias.name == "COMPAT_TARGETS"
        }
        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and node.id in aliases and isinstance(node.ctx, ast.Load):
                violations.append(f"{_rel(path)}:{node.lineno} compat names resolved outside resolve_and_admit")
    assert not violations, "\n".join(violations)


# --- the scanner itself catches the failure shapes ---------------------------------


def _admitted_in(source: str, expr: str) -> bool:
    tree = ast.parse(source)
    function = next(node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef))
    return AdmittedNames(function, None).is_admitted(ast.parse(expr, mode="eval").body)


@pytest.mark.parametrize(
    ("source", "expr", "admitted"),
    [
        ("def f(x):\n    t = resolve_and_admit((x,), mode=m)\n", "t", True),
        ("def f(x):\n    (t,) = resolve_and_admit((x,), mode=m)\n", "t", True),
        ("def f(x):\n    for t in resolve_and_admit(x, mode=m):\n        pass\n", "t", True),
        # re-resolution after the gate: the name has a non-admitted binding
        ("def f(x):\n    t = resolve_and_admit((x,), mode=m)\n    t = _resolve_delivery_agent(t)\n", "t", False),
        ("def f(x):\n    t = resolve_and_admit((x,), mode=m)\n", "t.recipient", False),
        ("def f(x):\n    return x\n", "x", False),
        ("def f(x: AdmittedTarget):\n    return x\n", "x", True),
        ("def f(x):\n    w = []\n    for t in resolve_and_admit(x, mode=m):\n        w.append(t)\n", "w", True),
        ("def f(x):\n    w = []\n    w.append(x)\n", "w", False),
        ("def f(x):\n    return 0\n", "require_admitted(x)", False),
    ],
)
def test_the_scanner_tells_admitted_values_from_raw_ones(source, expr, admitted):
    assert _admitted_in(source, expr) is admitted
