"""#10630 S2: no consumer reads the routing snapshot's claude lane without naming the account.

The routing-budget payload's ``agents`` map holds the ``claude`` lane row (the
Monitor host's default account's meter) and ``claude_accounts`` holds every
other account's row. ``scripts/fleet/claude_account_lane.py`` owns both reads
and requires a ``ClaudeAccount`` for the claude lane (``other_lane_record``
refuses it). This bounded static check fails when, in any covered consumer:

- a read of either map is not in the baseline with its disposition. A read is
  a subscript, ``get``/``pop``/``setdefault``/``__getitem__`` (also through
  ``getattr(x, "get")`` or ``dict.get(x, key)``) or ``operator.itemgetter``
  whose key is a string literal or a local name bound only to string literals
  (constant propagation within the function, then the module). A comprehension,
  lambda or ``.items()``/``.keys()``/``.values()`` loop that compares its own
  iteration variable with ``"claude"`` or a map name is a read too;
- a subscript or getter on a snapshot object has a key the check cannot
  resolve (fail closed: such a read is listed in the baseline as map
  ``<dynamic>`` or it fails; decision consumers list none). A snapshot object is a name called ``snapshot``,
  ``routing_snapshot``, ``budget`` (and the like), a name bound from a
  routing-budget source call or ``.routing_snapshot``, an alias of one, or a
  name the same function reads a map from with a literal key;
- a ``ClaudeAccount`` is constructed outside its owner module;
- a ``ResolverInputs(...)`` or ``.resolver_inputs(...)`` call does not name
  ``claude_account``: keywords, plus ``**`` forwarding of a dict literal
  followed through aliases, ``dict(...)``, ``{**...}``, item assignment and
  ``update``. A ``**`` of anything else is unresolvable and fails closed.

The baseline (``tests/fixtures/claude_lane_reads_baseline.json``) may only
shrink. It must equal what the scan finds (a removed read is removed there
too), and :func:`test_the_baseline_only_shrinks` compares it with the
committed versions: the last commit (``HEAD``) and the merge base with
``origin/main``. A key or count above either fails. The first version of the
file has no predecessor; once it is on ``main`` every later change is held to
it. The file needs history, so it runs on the history shard
(``scripts/ci/history-tests.txt``).

Coverage is every module outside the producer (``scripts/api/``) that names a
routing snapshot source or the snapshot itself (:func:`_snapshot_modules`);
:data:`EXEMPT` lists the ones that mention one without reading it. The check is
syntactic: a read through another module's helper, ``eval`` or a key built at
run time from non-literal parts on an object it cannot tell is a snapshot is
not seen, and a baseline disposition is asserted here, not proven. The runtime
checks (``require_account``, the required ``ResolverInputs.claude_account``,
the admission backstop) and the agreement test
(``tests/test_claude_account_route_key.py``) are the backstop.
"""

from __future__ import annotations

import ast
import functools
import json
import subprocess
from collections import Counter
from collections.abc import Iterator
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
OWNER = "scripts/fleet/claude_account_lane.py"
BASELINE_PATH = "tests/fixtures/claude_lane_reads_baseline.json"
SNAPSHOT_MAPS = frozenset({"agents", "claude_accounts"})
# What an iteration filter may test its own variable against to pick the claude lane out of a map.
FILTER_KEYS = SNAPSHOT_MAPS | {"claude"}
_SOURCE_MARKERS = (
    "routing-budget",
    "compute_routing_budget",
    "read_routing_budget",
    "_fetch_routing_budget",
    "routing_snapshot",
    "claude_accounts",
)
# Names that hold a routing snapshot wherever they appear, and source calls that return one.
SNAPSHOT_NAMES = frozenset({"snap", "snapshot", "routing_snapshot", "budget", "routing_budget", "runtime_state"})
SNAPSHOT_SOURCE_PARTS = ("routing_budget", "routing_snapshot")
GETTERS = frozenset({"get", "pop", "setdefault", "__getitem__"})
ACCOUNT_REQUIRING_CALLS = frozenset({"ResolverInputs", "resolver_inputs"})
ACCOUNT_KEYWORD = "claude_account"
# The baseline's map name for a snapshot read whose key the scan cannot resolve.
DYNAMIC = "<dynamic>"

# The decision consumers of the claude lane: every read goes through the owner.
DECISION_CONSUMERS = (
    "scripts/delegate.py",  # budget guard, launch route, admission plumbing, worker re-admission
    "scripts/agent_runtime/model_pause.py",  # plan-headroom stop
    "scripts/agent_runtime/target_admission.py",  # reviewer admission, final-route backstop
    "scripts/review/closeout_cli.py",  # resolve-reviewer
    OWNER,  # the snapshot read API itself
    "scripts/review/bench_health.py",  # bench inventory, keyed like resolve-reviewer
    "scripts/review/record_cf_verdict.py",  # reviewer qualification (no claude meter)
    "scripts/review/capacity.py",  # review allowance of a record it is given
    "scripts/fleet/credit_lane.py",  # credit-period refusal: credit lanes only
)
# Consumers whose remaining raw reads are listed in the baseline with their disposition.
LISTED_CONSUMERS = (
    "scripts/lib/claude_weekly_used.py",
    "scripts/fleet/capacity_pick.py",
    "scripts/fleet/usage.py",
    "scripts/review/reviewer_resolver.py",
    "scripts/review/reviewer_scheduler.py",
    "scripts/orchestration/curriculum_coordinator.py",
)
COVERED = (*DECISION_CONSUMERS, *LISTED_CONSUMERS)
EXEMPT = {
    "scripts/agent_runtime/attempt_boundary.py": "names the private bindings file, not the routing snapshot",
    "scripts/agent_runtime/usage.py": "a comment; reads runtime usage records, not the snapshot",
    "scripts/audit/lint_dispatch_brief.py": "a document path",
    "scripts/review/role_resolution.py": "route health only (normalize_routing_snapshot), a fact no account owns",
}


# --- the scan -------------------------------------------------------------------------------


def _call_name(node: ast.AST) -> str | None:
    return node.id if isinstance(node, ast.Name) else node.attr if isinstance(node, ast.Attribute) else None


def _scope_nodes(body: list[ast.stmt]) -> Iterator[ast.AST]:
    """Every node of a scope, without descending into nested functions or classes (their own scopes)."""
    stack: list[ast.AST] = list(reversed(body))
    while stack:
        node = stack.pop()
        yield node
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef | ast.Lambda):
            continue
        stack.extend(reversed(list(ast.iter_child_nodes(node))))


class _Scope:
    """One function's (or the module's) bindings: string constants, dict-literal keys and snapshot objects."""

    def __init__(self, node: ast.AST, body: list[ast.stmt], parent: _Scope | None) -> None:
        self.parent = parent
        self.bindings: dict[str, list[ast.AST | None]] = {}
        self.item_keys: dict[str, set[str]] = {}
        self.iteration_names: set[str] = set()
        params: list[str] = []
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.Lambda):
            args = node.args
            params = [a.arg for a in (*args.posonlyargs, *args.args, *args.kwonlyargs)]
            params += [a.arg for a in (args.vararg, args.kwarg) if a is not None]
        for name in params:
            self.bindings.setdefault(name, []).append(None)  # a parameter's value is unknown
        if isinstance(node, ast.Lambda):
            self.iteration_names |= set(params)  # ``filter(lambda kv: kv[0] == "claude", ...)``
        for item in _scope_nodes(body):
            self._bind(item)

    def _bind(self, item: ast.AST) -> None:
        if isinstance(item, ast.Assign):
            for target in item.targets:
                self._bind_target(target, item.value)
        elif isinstance(item, ast.AnnAssign | ast.AugAssign | ast.NamedExpr):
            value = None if isinstance(item, ast.AugAssign) else item.value
            self._bind_target(item.target, value)
        elif isinstance(item, ast.For | ast.AsyncFor | ast.comprehension):
            self._bind_loop(item.target, item.iter)
        elif isinstance(item, ast.withitem) and item.optional_vars is not None:
            self._bind_target(item.optional_vars, None)
        elif isinstance(item, ast.Import | ast.ImportFrom):
            for alias in item.names:
                self.bindings.setdefault((alias.asname or alias.name).split(".")[0], []).append(None)
        elif isinstance(item, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
            self.bindings.setdefault(item.name, []).append(None)
        elif isinstance(item, ast.Call) and isinstance(item.func, ast.Attribute):
            # ``d.update(k=...)``, ``d.update({"k": ...})`` and ``d.setdefault("k", ...)`` add keys.
            owner = item.func.value
            if isinstance(owner, ast.Name) and item.func.attr == "update":
                keys = {kw.arg for kw in item.keywords if kw.arg}
                for arg in item.args:
                    keys |= set(self.dict_keys(arg) or {"<unresolved>"})
                self.item_keys.setdefault(owner.id, set()).update(keys)
            elif isinstance(owner, ast.Name) and item.func.attr == "setdefault" and item.args:
                self.item_keys.setdefault(owner.id, set()).update(self.keys_of(item.args[0]) or {"<unresolved>"})

    def _bind_loop(self, target: ast.AST, iterable: ast.AST) -> None:
        """A loop over literals binds each literal; one over a map's ``items()``/``keys()`` is a lane filter."""
        if isinstance(target, ast.Name) and isinstance(iterable, ast.Tuple | ast.List | ast.Set):
            for element in iterable.elts:
                self.bindings.setdefault(target.id, []).append(element if isinstance(element, ast.Constant) else None)
            return
        self._bind_target(target, None)
        if isinstance(iterable, ast.Call) and _call_name(iterable.func) in {"items", "keys", "values"}:
            self.iteration_names |= _names(target)

    def _bind_target(self, target: ast.AST, value: ast.AST | None) -> None:
        if isinstance(target, ast.Name):
            self.bindings.setdefault(target.id, []).append(value)
        elif isinstance(target, ast.Subscript) and isinstance(target.value, ast.Name):
            # ``d["k"] = v`` adds the key to a forwarded dict.
            self.item_keys.setdefault(target.value.id, set()).update(self.keys_of(target.slice) or {"<unresolved>"})
        elif isinstance(target, ast.Tuple | ast.List | ast.Starred):
            for name in _names(target):
                self.bindings.setdefault(name, []).append(None)

    def _lookup(self, name: str) -> list[ast.AST | None] | None:
        scope: _Scope | None = self
        while scope is not None:
            if name in scope.bindings:
                return scope.bindings[name]
            scope = scope.parent
        return None

    def _owner(self, name: str) -> _Scope | None:
        scope: _Scope | None = self
        while scope is not None:
            if name in scope.bindings:
                return scope
            scope = scope.parent
        return None

    # String-constant propagation: the literal keys a node can be, or None when it can be anything else.
    def keys_of(self, node: ast.AST, seen: frozenset[str] = frozenset()) -> frozenset[str] | None:
        if isinstance(node, ast.Constant):
            return frozenset({node.value}) if isinstance(node.value, str) else frozenset()
        if isinstance(node, ast.IfExp):
            body, orelse = self.keys_of(node.body, seen), self.keys_of(node.orelse, seen)
            return None if body is None or orelse is None else body | orelse
        if isinstance(node, ast.Name) and node.id not in seen:
            owner = self._owner(node.id)
            values = owner.bindings[node.id] if owner is not None else None
            if not values:
                return None
            found: set[str] = set()
            for value in values:
                keys = None if value is None else owner.keys_of(value, seen | {node.id})
                if keys is None:
                    return None
                found |= keys
            return frozenset(found)
        return None

    # Dict-literal dataflow: the keyword names a ``**`` operand carries, or None when it is unresolvable.
    def dict_keys(self, node: ast.AST, seen: frozenset[str] = frozenset()) -> frozenset[str] | None:
        if isinstance(node, ast.Dict):
            found: set[str] = set()
            for key, value in zip(node.keys, node.values, strict=True):
                if key is None:  # ``{**other}``
                    nested = self.dict_keys(value, seen)
                    if nested is None:
                        return None
                    found |= nested
                else:
                    keys = self.keys_of(key)
                    if keys is None:
                        return None
                    found |= keys
            return frozenset(found)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "dict":
            found = {kw.arg for kw in node.keywords if kw.arg}
            for part in [*node.args, *(kw.value for kw in node.keywords if kw.arg is None)]:
                nested = self.dict_keys(part, seen)
                if nested is None:
                    return None
                found |= nested
            return frozenset(found)
        if isinstance(node, ast.Name) and node.id not in seen:
            owner = self._owner(node.id)
            values = owner.bindings[node.id] if owner is not None else None
            if not values:
                return None
            found = set(owner.item_keys.get(node.id, ()))
            if "<unresolved>" in found:
                return None
            for value in values:
                keys = None if value is None else owner.dict_keys(value, seen | {node.id})
                if keys is None:
                    return None
                found |= keys
            return frozenset(found)
        return None

    def is_snapshot(self, node: ast.AST, seen: frozenset[str] = frozenset(), *, literal_roots: set[str]) -> bool:
        """Whether ``node`` holds a routing snapshot (see the module docstring)."""
        if isinstance(node, ast.BoolOp):
            return any(self.is_snapshot(value, seen, literal_roots=literal_roots) for value in node.values)
        if isinstance(node, ast.Attribute):
            return node.attr in SNAPSHOT_NAMES
        if isinstance(node, ast.Call):
            name = _call_name(node.func) or ""
            if any(part in name for part in SNAPSHOT_SOURCE_PARTS):
                return True
            # ``dict(snapshot)`` is the snapshot.
            return name == "dict" and any(self.is_snapshot(a, seen, literal_roots=literal_roots) for a in node.args)
        if isinstance(node, ast.Dict):
            return any(
                key is None and self.is_snapshot(value, seen, literal_roots=literal_roots)
                for key, value in zip(node.keys, node.values, strict=True)
            )
        if isinstance(node, ast.Name):
            if node.id in SNAPSHOT_NAMES or node.id in literal_roots:
                return True
            if node.id in seen:
                return False
            owner = self._owner(node.id)
            return owner is not None and any(
                value is not None and owner.is_snapshot(value, seen | {node.id}, literal_roots=literal_roots)
                for value in owner.bindings[node.id]
            )
        return False


def _names(target: ast.AST) -> set[str]:
    return {node.id for node in ast.walk(target) if isinstance(node, ast.Name)}


class _Scan(ast.NodeVisitor):
    """Snapshot-map reads, unresolvable snapshot keys, ``ClaudeAccount`` constructions and account-less calls."""

    def __init__(self) -> None:
        self.stack: list[str] = []
        self.scopes: list[_Scope] = []
        self.reads: Counter[tuple[str, str]] = Counter()
        self.dynamic: list[tuple[str, int]] = []
        self.constructions: list[tuple[str, int]] = []
        self.unnamed_accounts: list[tuple[str, int]] = []
        self._literal_roots: list[set[str]] = []

    def _where(self) -> str:
        return ".".join(self.stack) or "<module>"

    def _enter(self, node: ast.AST, body: list[ast.stmt]) -> None:
        scope = _Scope(node, body, self.scopes[-1] if self.scopes else None)
        self.scopes.append(scope)
        # Names this scope reads a snapshot map from with a resolvable key are snapshot objects here.
        roots: set[str] = set()
        for item in _scope_nodes(body):
            for target, key in self._read_sites(item, scope):
                keys = scope.keys_of(key) if key is not None else None
                if keys and keys & SNAPSHOT_MAPS and isinstance(target, ast.Name):
                    roots.add(target.id)
        self._literal_roots.append(roots)

    def _leave(self) -> None:
        self.scopes.pop()
        self._literal_roots.pop()

    def visit_Module(self, node: ast.Module) -> None:
        self._enter(node, node.body)
        self.generic_visit(node)
        self._leave()

    def visit_FunctionDef(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        for decorator in node.decorator_list:
            self.visit(decorator)
        self.stack.append(node.name)
        self._enter(node, node.body)
        for statement in node.body:
            self.visit(statement)
        self._leave()
        self.stack.pop()

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self.stack.append(node.name)
        self.generic_visit(node)
        self.stack.pop()

    @staticmethod
    def _read_sites(node: ast.AST, scope: _Scope) -> list[tuple[ast.AST | None, ast.AST | None]]:
        """``(object, key)`` for each map read ``node`` makes; a None key is a key the scan cannot see."""
        if isinstance(node, ast.Subscript) and isinstance(node.ctx, ast.Load):
            return [(node.value, node.slice)]
        if not isinstance(node, ast.Call):
            return []
        func = node.func
        if isinstance(func, ast.Attribute) and func.attr in GETTERS:
            if isinstance(func.value, ast.Name) and func.value.id in {"dict", "Mapping"}:
                return [(node.args[0], node.args[1])] if len(node.args) >= 2 else []
            return [(func.value, node.args[0] if node.args else None)]
        if (
            isinstance(func, ast.Call)
            and _call_name(func.func) == "getattr"
            and len(func.args) >= 2
            and (scope.keys_of(func.args[1]) or frozenset()) & GETTERS
        ):
            return [(func.args[0], node.args[0] if node.args else None)]
        if _call_name(func) == "getattr" and len(node.args) >= 2 and scope.keys_of(node.args[1]) is None:
            return [(node.args[0], None)]  # ``getattr(snapshot, name)``: a method the scan cannot see
        if _call_name(func) == "itemgetter":
            return [(None, arg) for arg in node.args]
        return []

    def _visit_read(self, node: ast.AST) -> None:
        scope = self.scopes[-1]
        for target, key in self._read_sites(node, scope):
            keys = scope.keys_of(key) if key is not None else None
            if keys is None:
                # Fail closed: a key the scan cannot resolve, on a snapshot object or an itemgetter.
                if target is None or scope.is_snapshot(target, literal_roots=self._literal_roots[-1]):
                    self.dynamic.append((self._where(), getattr(node, "lineno", 0)))
                continue
            for key_name in sorted(keys & SNAPSHOT_MAPS):
                self.reads[(self._where(), key_name)] += 1

    def visit_Subscript(self, node: ast.Subscript) -> None:
        self._visit_read(node)
        self.generic_visit(node)

    def visit_Compare(self, node: ast.Compare) -> None:
        # ``k == "claude"`` / ``k in ("claude",)`` on an iteration variable picks a lane out of a map.
        scope = self.scopes[-1]
        operands = [node.left, *node.comparators]
        tested = {
            key
            for operand in operands
            for element in (operand.elts if isinstance(operand, ast.Tuple | ast.List | ast.Set) else [operand])
            for key in (scope.keys_of(element) if isinstance(element, ast.Constant) else None) or ()
        } & FILTER_KEYS
        iterated = any(
            isinstance(base := (o.value if isinstance(o, ast.Subscript) else o), ast.Name)
            and base.id in scope.iteration_names
            for o in operands
        )
        if tested and iterated:
            for key in sorted(tested):
                self.reads[(self._where(), key)] += 1
        self.generic_visit(node)

    def visit_Lambda(self, node: ast.Lambda) -> None:
        self._enter(node, [ast.Expr(node.body)])
        self.visit(node.body)
        self._leave()

    def visit_Call(self, node: ast.Call) -> None:
        self._visit_read(node)
        name = _call_name(node.func)
        if name == "ClaudeAccount":
            self.constructions.append((self._where(), node.lineno))
        if name in ACCOUNT_REQUIRING_CALLS:
            scope = self.scopes[-1]
            keywords: set[str] = {kw.arg for kw in node.keywords if kw.arg is not None}
            for keyword in node.keywords:
                if keyword.arg is None:
                    keywords |= scope.dict_keys(keyword.value) or set()
            # An unresolvable ``**`` cannot name the account: it fails closed unless the call names it.
            if ACCOUNT_KEYWORD not in keywords:
                self.unnamed_accounts.append((self._where(), node.lineno))
        self.generic_visit(node)


def scan(source: str) -> _Scan:
    visitor = _Scan()
    visitor.visit(ast.parse(source))
    return visitor


# --- the baseline --------------------------------------------------------------------------


def load_baseline(text: str | None = None) -> dict[tuple[str, str, str], tuple[int, str]]:
    """``(module, function, map) -> (count, disposition)`` from the committed baseline file (or ``text``)."""
    payload = json.loads(text if text is not None else (REPO_ROOT / BASELINE_PATH).read_text(encoding="utf-8"))
    return {
        (row["module"], row["function"], row["map"]): (int(row["count"]), str(row["disposition"]))
        for row in payload["reads"]
    }


def baseline_growth(current: dict, previous: dict) -> dict[tuple[str, str, str], tuple[int, int]]:
    """Every key whose count is above ``previous`` (a key ``previous`` lacks counts from zero)."""
    return {
        key: (previous.get(key, (0, ""))[0], count)
        for key, (count, _reason) in current.items()
        if count > previous.get(key, (0, ""))[0]
    }


def module_violations(module: str, source: str) -> list[str]:
    """Why ``module``'s ``source`` fails the check (empty when it passes)."""
    found = scan(source)
    reads = found.reads + Counter((where, DYNAMIC) for where, _line in found.dynamic)
    actual = {(module, where, key): count for (where, key), count in reads.items()}
    listed = {key: count for key, (count, _reason) in load_baseline().items() if key[0] == module}
    problems = [
        f"unlisted {'unresolvable snapshot key' if key[2] == DYNAMIC else 'read'} {key}: {count}"
        for key, count in sorted(actual.items())
        if key not in listed
    ]
    problems += [
        f"baseline {key} lists {count}, found {actual.get(key, 0)}"
        for key, count in sorted(listed.items())
        if actual.get(key, 0) != count
    ]
    problems += [
        f"{where} (line {line}) builds resolver inputs without claude_account" for where, line in found.unnamed_accounts
    ]
    return problems


@functools.cache
def _scripts_sources() -> dict[str, str]:
    """Every tracked-tree Python source under ``scripts/``, by repository-relative path."""
    return {
        path.relative_to(REPO_ROOT).as_posix(): path.read_text(encoding="utf-8")
        for path in sorted((REPO_ROOT / "scripts").rglob("*.py"))
    }


def _snapshot_modules() -> set[str]:
    """Every module outside the producer that names a routing snapshot source or the snapshot."""
    return {
        module
        for module, text in _scripts_sources().items()
        if not module.startswith("scripts/api/") and any(marker in text for marker in _SOURCE_MARKERS)
    }


# --- the real tree passes -------------------------------------------------------------------


@pytest.mark.repo_wide
def test_every_snapshot_consumer_is_covered_or_exempt():
    assert _snapshot_modules() - set(COVERED) - set(EXEMPT) == set()
    # A covered or exempt module that no longer names a snapshot is removed from the list.
    assert set(EXEMPT) <= _snapshot_modules()
    assert all(reason.strip() for reason in EXEMPT.values())


@pytest.mark.parametrize("module", [module for module in COVERED if module != OWNER])
def test_no_consumer_reads_the_snapshot_lane_maps_outside_the_baseline(module):
    problems = module_violations(module, (REPO_ROOT / module).read_text(encoding="utf-8"))
    assert problems == [], (
        "read the claude lane through scripts.fleet.claude_account_lane with a named ClaudeAccount "
        "(lane_record, account_agents, other_lane_record), not the snapshot's maps; a removed read "
        f"leaves the baseline too: {problems}"
    )


def test_decision_consumers_have_no_baseline_reads():
    baseline = load_baseline()
    assert {key for key in baseline if key[0] in DECISION_CONSUMERS} == set()
    assert {key[0] for key in baseline} <= set(LISTED_CONSUMERS)
    assert all(reason.strip() for _count, reason in baseline.values())


def _committed_baseline(ref: str) -> dict | None:
    """The baseline file at ``ref``, or None when ``ref`` has no such file (its first version)."""
    result = subprocess.run(
        ["git", "show", f"{ref}:{BASELINE_PATH}"], cwd=REPO_ROOT, capture_output=True, text=True, timeout=30
    )
    if result.returncode == 0:
        return load_baseline(result.stdout)
    exists = subprocess.run(
        ["git", "cat-file", "-e", f"{ref}^{{commit}}"], cwd=REPO_ROOT, capture_output=True, timeout=30
    )
    assert exists.returncode == 0, f"{ref} is not available: the shrink-only check needs history"
    return None


def test_the_baseline_only_shrinks():
    """No key or count above the last commit's file, or the file at the merge base with origin/main."""
    merge_base = subprocess.run(
        ["git", "merge-base", "HEAD", "origin/main"], cwd=REPO_ROOT, capture_output=True, text=True, timeout=30
    )
    assert merge_base.returncode == 0, "origin/main is not available: the shrink-only check needs history"
    current = load_baseline()
    for ref in ("HEAD", merge_base.stdout.strip()):
        previous = _committed_baseline(ref)
        if previous is not None:
            assert baseline_growth(current, previous) == {}, f"the baseline may only shrink; it grew against {ref}"


@pytest.mark.repo_wide
def test_claude_accounts_are_built_only_by_their_owner():
    built = {
        module: scan(text).constructions for module, text in _scripts_sources().items() if "ClaudeAccount(" in text
    }
    assert {module for module, sites in built.items() if sites} == {OWNER}


@pytest.mark.repo_wide
def test_every_resolver_snapshot_names_its_claude_account():
    unnamed = {
        module: sites
        for module, text in _scripts_sources().items()
        if "resolver_inputs" in text or "ResolverInputs" in text
        if (sites := scan(text).unnamed_accounts)
    }
    assert unnamed == {}


# --- the check itself: an injected bypass is caught -----------------------------------------

# The four bypasses the review of e98e30c5 found, and their siblings. Each is a function appended to a consumer.
INJECTIONS = {
    "subscript_through_a_variable": 'def _injected_bypass(snap):\n    key = "agents"\n    return snap[key]["claude"]\n',
    "getattr_get": 'def _injected_bypass(snap):\n    return getattr(snap, "get")("agents", {})["claude"]\n',
    "comprehension_filter": (
        'def _injected_bypass(snap):\n    key = "agents"\n'
        '    return [v for k, v in snap.get(key, {}).items() if k == "claude"]\n'
    ),
    "kwargs_forwarding": (
        'def _injected_bypass(snap):\n    common = {"routing_snapshot": snap}\n    forwarded = common\n'
        "    return ResolverInputs(**forwarded)\n"
    ),
    # Siblings of the same classes.
    "module_constant_key": '_LANES = "agents"\n\n\ndef _injected_bypass(payload):\n    return payload[_LANES]\n',
    "dynamic_key_on_a_snapshot": "def _injected_bypass(snapshot, key):\n    return snapshot[key]\n",
    "dynamic_get_on_a_literal_root": (
        'def _injected_bypass(payload, key):\n    payload.get("agents")\n    return payload.get(key)\n'
    ),
    "dynamic_getattr_on_a_snapshot": "def _injected_bypass(budget, method):\n    return getattr(budget, method)\n",
    "dict_get_unbound": 'def _injected_bypass(payload):\n    return dict.get(payload, "claude_accounts")\n',
    "itemgetter": 'import operator\n\n\ndef _injected_bypass(payload):\n    return operator.itemgetter("agents")(payload)\n',
    "lambda_filter": (
        'def _injected_bypass(lanes):\n    return dict(filter(lambda kv: kv[0] == "claude", lanes.items()))\n'
    ),
    "loop_filter": (
        "def _injected_bypass(lanes):\n    for lane, row in lanes.items():\n"
        '        if lane == "claude":\n            return row\n'
    ),
    "aliased_dict_update": (
        "def _injected_bypass(snap):\n    common = {}\n    common.update(routing_snapshot=snap)\n"
        "    return ResolverInputs(**dict(common))\n"
    ),
    "unresolvable_forwarding": "def _injected_bypass(options):\n    return ResolverInputs(**options)\n",
    "method_forwarding": 'def _injected_bypass(facts, snap):\n    return facts.resolver_inputs(risk="low", routing_snapshot=snap)\n',
}
INJECTED_CONSUMERS = [module for module in COVERED if module != OWNER]


@pytest.mark.parametrize("module", INJECTED_CONSUMERS)
@pytest.mark.parametrize("injection", sorted(INJECTIONS))
def test_a_scratch_copy_with_an_injected_bypass_fails_the_check(module, injection, tmp_path):
    copy = tmp_path / Path(module).name
    copy.write_text((REPO_ROOT / module).read_text(encoding="utf-8") + "\n\n" + INJECTIONS[injection])
    problems = module_violations(module, copy.read_text(encoding="utf-8"))
    assert problems, f"{injection} injected into {module} passed the check"
    assert all("_injected_bypass" in problem for problem in problems), problems


def test_the_scan_names_what_each_injection_is():
    reads = {name: scan(text) for name, text in INJECTIONS.items()}
    assert reads["subscript_through_a_variable"].reads == Counter({("_injected_bypass", "agents"): 1})
    assert reads["getattr_get"].reads == Counter({("_injected_bypass", "agents"): 1})
    assert reads["comprehension_filter"].reads == Counter(
        {("_injected_bypass", "agents"): 1, ("_injected_bypass", "claude"): 1}
    )
    assert reads["kwargs_forwarding"].unnamed_accounts == [("_injected_bypass", 4)]
    assert reads["dynamic_key_on_a_snapshot"].dynamic == [("_injected_bypass", 2)]
    assert reads["dynamic_get_on_a_literal_root"].dynamic == [("_injected_bypass", 3)]
    assert reads["lambda_filter"].reads == Counter({("_injected_bypass", "claude"): 1})
    assert reads["unresolvable_forwarding"].unnamed_accounts == [("_injected_bypass", 2)]


@pytest.mark.parametrize(
    "source",
    [
        # A literal key that is not a map, and a dynamic key on an object that is no snapshot.
        'def f(snap):\n    return snap["recommendation"]\n',
        "def f(record, key):\n    return record[key]\n",
        # A key bound to non-map literals only.
        'def f(snap, flag):\n    key = "diagnostics" if flag else "recommendation"\n    return snap[key]\n',
        # A loop over a literal tuple of seat names compares names, not a map's lanes.
        'def f():\n    for seat in ("claude", "codex"):\n        if seat == "claude":\n            return seat\n',
        # Named accounts, directly and through forwarding.
        "def f(snapshot, acct):\n    return ResolverInputs(author_model='x', routing_snapshot=snapshot, claude_account=acct)\n",
        'def f(snap, acct):\n    common = {"routing_snapshot": snap}\n    common["claude_account"] = acct\n'
        "    return x.resolver_inputs(risk='low', **common)\n",
        "def f(acct, **overrides):\n    return ResolverInputs(claude_account=acct, **overrides)\n",
    ],
)
def test_the_scan_passes_what_is_not_a_bypass(source):
    found = scan(source)
    assert (sum(found.reads.values()), found.dynamic, found.unnamed_accounts) == (0, [], [])


def test_the_scan_catches_an_injected_account_construction():
    assert scan('def f():\n    return ClaudeAccount("a", "builtin")\n').constructions


def test_a_grown_baseline_is_refused():
    current = load_baseline()
    key = next(iter(current))
    count, reason = current[key]
    assert baseline_growth(current, current) == {}
    assert baseline_growth({**current, key: (count + 1, reason)}, current) == {key: (count, count + 1)}
    new = ("scripts/fleet/usage.py", "new_reader", "agents")
    assert baseline_growth({**current, new: (1, "display")}, current) == {new: (0, 1)}
    # Shrinking is always allowed.
    assert baseline_growth({k: v for k, v in current.items() if k != key}, current) == {}
