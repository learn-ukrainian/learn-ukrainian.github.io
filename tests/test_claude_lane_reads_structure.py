"""#10630 S2: no consumer reads the routing snapshot's claude lane without naming the account.

The routing-budget payload's ``agents`` map holds the ``claude`` lane row (the
Monitor host's default account's meter) and ``claude_accounts`` holds every
other account's row. ``scripts/fleet/claude_account_lane.py`` owns both reads
and requires a ``ClaudeAccount`` for the claude lane. This static check is a
closed allowlist and fails closed: inside every covered consumer, a value
derived from the routing snapshot may reach only the uses listed below, and
any other use is a violation.

A value is derived from the snapshot when it is a name in
:data:`SNAPSHOT_NAMES` (a parameter or a local), an attribute with such a name
(``inputs.routing_snapshot``) or ``getattr`` of one, the result of a call whose
name contains a :data:`SOURCE_PARTS` part (``_fetch_routing_budget()``), the
result of a covered function that returns such a value, a covered function's
parameter that receives one, or a local alias, ``x or {}``, ``a if c else b``,
``await`` or ``:=`` of one. The allowed uses, and why each is safe:

- the first argument of an accessor in :data:`ACCESSORS`, with an explicit
  ``account=`` that is not ``None``: each requires a ``ClaudeAccount``
  (``require_account``) and reads the claude lane as that account
  (``other_lane_record`` takes none and refuses the claude lane);
- ``routing_snapshot=`` of ``ResolverInputs(...)``/``.resolver_inputs(...)``
  with an explicit ``claude_account=`` (or a sealed keyword dict, below): the
  resolver reads the snapshot as that account; ``routing_snapshot=`` of
  ``dataclasses.replace``, which keeps the account the inputs carry;
- an argument passed unchanged to a function defined in a covered module: the
  receiving parameter is then derived too and checked where it is used (the
  owner's own functions are reachable only as accessors);
- ``x.get(<field>)``/``x[<field>]`` with a literal in :data:`SAFE_FIELDS`:
  top-level fields the producer fills with no Claude account meter (each
  member says what it holds), so the result is not derived;
- ``isinstance``, ``is None``/``is not None``, truth tests, a discarded
  value, ``return``, a plain-name alias in the same scope (not through
  ``global``/``nonlocal``) and an attribute store under a snapshot name: none
  reads the value, and the alias, the returned value and the attribute stay
  derived.

A sealed keyword dict is a dict literal, bound once to a name used only as
``**`` operands of ``ResolverInputs``/``resolver_inputs``, with a literal
``claude_account`` key and no ``**`` entry: nothing can drop or add that key
before the call. Everything else (attribute access, a method or a reference
such as ``.get``/``.items``, a subscript or ``get`` with any other key, a
container literal, an unpacking, ``*``/``**``, iteration, a comparison, a call
the check cannot resolve) is a violation. In addition the map names
``"agents"`` and ``"claude_accounts"`` may not appear as string literals in a
covered consumer at all, whatever object they are used on, so a read through a
name the check does not know as a snapshot is still caught when it names a
map. The owner module itself is not checked. Separately, every
``ResolverInputs(...)``/``.resolver_inputs(...)`` call under ``scripts/`` must
name ``claude_account`` explicitly or through a sealed keyword dict, with a
value that is not ``None``.

A use the closed allowlist rejects is either migrated to an accessor or
listed in :data:`EXCEPTIONS`: one entry per site (its function and its
source text), with the reason that site is safe, and no count. Findings and
exceptions must match one to one, so a new site fails even inside a listed
function, and a listed site that is gone fails too. The ceiling is history,
not the candidate commit: :func:`exception_ceiling_violations` parses this
file as it is at the merge base of ``HEAD`` with ``origin/main`` (or, when that
commit predates the file, at ``origin/main``'s tip), without executing it, and
fails when a function lists more sites there than it did, when
:data:`SAFE_FIELDS`, :data:`ACCESSORS` or :data:`EXEMPT` gained a member, or
when :data:`SNAPSHOT_MAPS`, :data:`SNAPSHOT_NAMES`, :data:`SOURCE_PARTS` or
:data:`ACCOUNT_REQUIRING_CALLS` lost one. A later commit therefore cannot
raise a ceiling by editing this file, because the copy it is compared with is
already on main. Only while ``origin/main`` has never had the file (its first
PR) is there no history: then the literals below are the ceiling, approved by
that PR's review, and a file main had and lost fails closed.
``test_a_raised_exception_ceiling_fails_in_a_real_repository`` shows a second
commit raising a count failing on real commits in a scratch repository. This
file reads history, so it runs on the history shard
(``scripts/ci/history-tests.txt``).

Coverage is every module outside the producer (``scripts/api/``) that names a
routing snapshot source or the snapshot itself (:func:`_snapshot_modules`);
:data:`EXEMPT` lists the ones that mention one without reading it. Limits: the
check is syntactic and flow-insensitive (a name is derived when any of its
bindings is, which lists a few unrelated values named ``snapshot`` as
exceptions). A snapshot held under a name it does not know, read with a key
built at run time (never the literal map name), or through ``eval``, ``vars``
or ``__dict__``, is not seen; the check's own rules are reviewed, not held to
a ceiling; an exception's reason is asserted here, not proven. The runtime checks (``require_account``, the required
``ResolverInputs.claude_account``, the admission backstop) and the agreement
test (``tests/test_claude_account_route_key.py``) are the backstop.
"""

from __future__ import annotations

import ast
import functools
import os
import re
import subprocess
from collections import Counter
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
THIS_FILE = "tests/test_claude_lane_reads_structure.py"
OWNER = "scripts/fleet/claude_account_lane.py"
OWNER_DOTTED = "scripts.fleet.claude_account_lane"
SNAPSHOT_MAPS = frozenset({"agents", "claude_accounts"})
_SOURCE_MARKERS = (
    "routing-budget",
    "compute_routing_budget",
    "read_routing_budget",
    "_fetch_routing_budget",
    "routing_snapshot",
    "claude_accounts",
)
# Names that hold a routing snapshot wherever they appear, and call-name parts that return one.
SNAPSHOT_NAMES = frozenset({"snap", "snapshot", "routing_snapshot", "budget", "routing_budget", "runtime_state"})
SOURCE_PARTS = ("routing_budget", "routing_snapshot")
# The typed accessors (scripts/fleet/claude_account_lane.py): whether each requires ``account=``.
ACCESSORS = {
    "select_account": True,  # the payload read as the account, plus its evidence
    "account_agents": True,  # the lane records, the claude lane read as the account
    "lane_record": True,  # one lane record, the claude lane read as the account
    "capacity_verdict": True,  # hot / healthy / unknown for the account's claude seat
    "account_weekly_used_pct": True,  # the account's fresh weekly used-%
    "other_lane_record": False,  # a lane no account owns; raises ValueError for the claude lane
}
# Top-level routing-budget fields with no Claude account meter in them.
SAFE_FIELDS = {
    "diagnostics": "snapshot-wide freshness and provenance (stale, data_age_s, sources); the owner reads it too",
    "generated_at": "the snapshot's timestamp",
    "in_flight": "in-flight dispatch counts per agent, from task records, not a meter",
    "api_accounts": "the prepaid API lanes (openrouter, deepseek); no Claude account",
    "source": "transport provenance a reader adds (monitor-api, in-process-fresh)",
    "transport": "transport provenance a reader adds",
    "review_capacity_exclusions": "added by the dispatch guard from the account-read lane records",
}
ACCOUNT_REQUIRING_CALLS = frozenset({"ResolverInputs", "resolver_inputs"})
ACCOUNT_KEYWORD = "claude_account"

# Every consumer of the routing snapshot the check covers.
COVERED = (
    "scripts/delegate.py",  # budget guard, launch route, admission plumbing, worker re-admission
    "scripts/agent_runtime/model_pause.py",  # plan-headroom stop
    "scripts/agent_runtime/target_admission.py",  # reviewer admission, final-route backstop
    "scripts/review/closeout_cli.py",  # resolve-reviewer
    "scripts/review/bench_health.py",  # bench inventory, keyed like resolve-reviewer
    "scripts/review/record_cf_verdict.py",  # reviewer qualification (no claude meter)
    "scripts/review/capacity.py",  # review allowance of a record it is given
    "scripts/fleet/credit_lane.py",  # credit-period refusal: credit lanes only
    "scripts/lib/claude_weekly_used.py",  # isolated launcher reader
    "scripts/fleet/capacity_pick.py",  # advisory picker
    "scripts/fleet/usage.py",  # usage display
    "scripts/review/reviewer_resolver.py",  # the resolver
    "scripts/review/reviewer_scheduler.py",  # the resolver's ranking
    "scripts/orchestration/curriculum_coordinator.py",  # coordinator health
)
EXEMPT = {
    "scripts/agent_runtime/attempt_boundary.py": "names the private bindings file, not the routing snapshot",
    "scripts/agent_runtime/usage.py": "a comment; reads runtime usage records, not the snapshot",
    "scripts/audit/lint_dispatch_brief.py": "a document path",
    "scripts/review/role_resolution.py": "route health only (normalize_routing_snapshot), a fact no account owns",
}

# --- named exceptions: one entry per site --------------------------------------------------

_CHECKOUT = "a read-only checkout snapshot (path -> status record), not the routing snapshot"
_PUBLISH = "a publish-cause message string named snapshot (and the last_error it joins), not the routing snapshot"
_FRESHNESS = "the snapshot freshness class (a string from snapshot_freshness), not the routing snapshot"
_GUARD = (
    "advisory only: the producer's recommendation and ranked rows feed printed warnings and the "
    "spawn-health check (a route fact no account owns); by the review selector payload is "
    "select_account's view, and the agents it hands on are account_agents for the dispatch's account"
)
_LAUNCHER = (
    "isolated launcher reader (python -I cannot import the owner): agents.claude only for the "
    "default account and claude_accounts only for the account launch_account() names"
)
_PICKER = "advisory picker display: the dispatch budget guard re-judges the claude seat on its account"
_DISPLAY = "display: prints or validates lane rows; no routing decision reads the result"
_RESOLVER = (
    "account-keyed in the resolver: resolve_reviewer and evaluate_candidate first replace "
    "inputs.routing_snapshot with select_account's view for inputs.claude_account (_account_inputs)"
)
_HEALTH_MAP = (
    "the route -> status map normalize_routing_snapshot builds from inputs.routing_snapshot, "
    "already select_account's view for inputs.claude_account"
)
_SCHEDULER = "caller-keyed: the resolver passes select_account's view for inputs.claude_account"
_COORDINATOR = (
    "caller-keyed: reads the snapshot its caller passed, already "
    "claude_account_lane.select_account's view (default_health_probe keys it)"
)

EXCEPTIONS: dict[tuple[str, str], tuple[str, tuple[str, ...]]] = {
    ("scripts/delegate.py", "_canonical_snapshot_bytes"): (
        _CHECKOUT,
        ("json.dumps(payload, separators=(',', ':'))",),
    ),
    ("scripts/delegate.py", "_core_terminal_fields"): (
        _PUBLISH,
        ("{'status': status, 'finished_at': datetime.now(UTC).isoformat(), 'duration_s': round(duration_s, 3),",),
    ),
    ("scripts/delegate.py", "_read_only_dispatch_sandbox_roots"): (
        _CHECKOUT,
        ("for path in snapshot if (root := _read_only_dispatch_sandbox_root(path)) is not None",),
    ),
    ("scripts/delegate.py", "_read_only_task_record_snapshot"): (
        _CHECKOUT,
        (
            "snapshot[name]",
            "(snapshot, None)",
        ),
    ),
    ("scripts/delegate.py", "_resolve_agent_with_budget_guard"): (
        _GUARD,
        (
            "payload.get('recommendation')",
            "payload.get('ranked_by_headroom')",
            "payload.get('ranked_by_headroom')",
            "{**payload, 'agents': {lane: info if isinstance(info, Mapping) else {} for lane, info in agents.item",
        ),
    ),
    ("scripts/delegate.py", "_run_worker"): (
        _PUBLISH,
        (
            "{last_error}",
            "{last_error}",
            "{last_error}",
            "{snapshot}",
            "{last_error}",
            "{snapshot}",
        ),
    ),
    ("scripts/delegate.py", "_snapshot_digest_phase"): (
        _CHECKOUT,
        ("len(payload)",),
    ),
    ("scripts/delegate.py", "_write_read_only_snapshot_sidecar"): (
        _CHECKOUT,
        ("json.dumps(snapshot if snapshot is not None else {}, separators=(',', ':'))",),
    ),
    ("scripts/fleet/capacity_pick.py", "build_lane_rows"): (
        _PICKER,
        (
            "budget.get('agents')",
            "budget.get('agents')",
        ),
    ),
    ("scripts/fleet/capacity_pick.py", "build_report"): (
        _PICKER,
        (
            "budget.get('recommendation')",
            "budget.get('recommendation')",
        ),
    ),
    ("scripts/fleet/credit_lane.py", "observation_freshness"): (
        _FRESHNESS,
        (
            "snapshot == STALE",
            "snapshot == UNKNOWN",
        ),
    ),
    ("scripts/fleet/credit_lane.py", "routing_facts"): (
        _FRESHNESS,
        (
            "snapshot == STALE",
            "RoutingFacts(lane=lane_key, model=model, observed_at=_iso(current), plan_remaining_pct=remaining, re",
        ),
    ),
    ("scripts/fleet/usage.py", "_attach_status_observations"): (
        _DISPLAY,
        (
            "budget.get('agents')",
            "{**budget, 'agents': agents}",
        ),
    ),
    ("scripts/fleet/usage.py", "format_human"): (
        _DISPLAY,
        (
            "budget.get('agents')",
            "budget.get('agents')",
            "budget.get('agents')",
            "budget.get('agents')",
        ),
    ),
    ("scripts/fleet/usage.py", "main"): (
        _DISPLAY,
        ("json.dumps(budget, indent=2, sort_keys=True)",),
    ),
    ("scripts/fleet/usage.py", "qa_snapshot"): (
        _DISPLAY,
        (
            "budget.get('agents')",
            "budget.get('agents')",
        ),
    ),
    ("scripts/fleet/usage.py", "read_budget"): (
        _DISPLAY,
        (
            "('agents', 'api_accounts')",
            "budget.get(k)",
            "{**budget, 'source': 'monitor-api'}",
            "{**budget, 'source': 'in-process-fresh'}",
        ),
    ),
    ("scripts/lib/claude_weekly_used.py", "_weekly_used_pct"): (
        _LAUNCHER,
        (
            "data['agents']",
            "data['claude_accounts']",
        ),
    ),
    ("scripts/orchestration/curriculum_coordinator.py", "_health_assessment"): (
        _COORDINATOR,
        ("snapshot.get('agents')",),
    ),
    ("scripts/review/reviewer_resolver.py", "_health_of"): (
        _HEALTH_MAP,
        (
            "health.get(candidate.name)",
            "health.get(candidate.route)",
            "health.get(candidate.concrete_model)",
            "health.get(candidate.family)",
            "health[key]",
            "key in health",
        ),
    ),
    ("scripts/review/reviewer_resolver.py", "_near_cap_credit"): (
        _RESOLVER,
        ("snapshot.get('agents')",),
    ),
    ("scripts/review/reviewer_resolver.py", "normalize_routing_snapshot"): (
        _RESOLVER,
        (
            "'agents' not in snapshot",
            "snapshot.items()",
            "snapshot.get('agents')",
        ),
    ),
    ("scripts/review/reviewer_resolver.py", "resolve_reviewer"): (
        _RESOLVER,
        ("(inputs.routing_snapshot or {}).get('agents', {})",),
    ),
    ("scripts/review/reviewer_scheduler.py", "_route_record"): (
        _SCHEDULER,
        (
            "snapshot.get('agents')",
            "snapshot.get(key)",
        ),
    ),
}

# --- the scan -------------------------------------------------------------------------------

_SCOPES = (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)
_SITE_CHARS = 100


def _dotted(path: str) -> str:
    return path.removesuffix(".py").replace("/", ".")


def _call_name(node: ast.AST) -> str | None:
    return node.id if isinstance(node, ast.Name) else node.attr if isinstance(node, ast.Attribute) else None


def _none_like(node: ast.AST) -> bool:
    """A value that is or may be ``None``: the literal, or a branch of ``a if c else b`` / ``a or b``."""
    if isinstance(node, ast.Constant):
        return node.value is None
    if isinstance(node, ast.IfExp):
        return _none_like(node.body) or _none_like(node.orelse)
    if isinstance(node, ast.BoolOp):
        return any(_none_like(value) for value in node.values)
    return False


@dataclass
class _Scope:
    node: ast.AST
    qualname: str
    parent: _Scope | None
    cls: str | None
    bindings: dict[str, list[ast.AST | None]] = field(default_factory=dict)
    declared: set[str] = field(default_factory=set)  # ``global``/``nonlocal`` names: bound outside this scope


class _Module:
    """One parsed module: parents, scopes and their bindings, imports and function definitions."""

    def __init__(self, path: str, source: str) -> None:
        self.path = path
        self.tree = ast.parse(source)
        self.parent: dict[ast.AST, ast.AST] = {
            child: node for node in ast.walk(self.tree) for child in ast.iter_child_nodes(node)
        }
        self.imports: dict[str, str] = {}
        self.ambiguous: set[str] = set()
        self.rebound: set[str] = set()
        self.scopes: dict[ast.AST, _Scope] = {}
        self.functions: dict[str, ast.FunctionDef | ast.AsyncFunctionDef] = {}
        self._build(self.tree, _Scope(self.tree, "<module>", None, None), [])

    def _build(self, node: ast.AST, scope: _Scope, names: list[str]) -> None:
        self.scopes[node] = scope
        if isinstance(node, _SCOPES):
            args = node.args
            for arg in (*args.posonlyargs, *args.args, *args.kwonlyargs, args.vararg, args.kwarg):
                if arg is not None:
                    scope.bindings.setdefault(arg.arg, []).append(None)
                    self.rebound.add(arg.arg)
            body: list[ast.AST] = [node.body] if isinstance(node, ast.Lambda) else list(node.body)
        else:
            body = list(getattr(node, "body", []))
        stack = list(reversed(body))
        while stack:
            item = stack.pop()
            self.scopes.setdefault(item, scope)
            if isinstance(item, ast.FunctionDef | ast.AsyncFunctionDef):
                self._define(item, scope, names, None, stack)
            elif isinstance(item, ast.Lambda):
                stack.extend(item.args.defaults)
                self._build(item, _Scope(item, ".".join([*names, "<lambda>"]), scope, None), [*names, "<lambda>"])
            elif isinstance(item, ast.ClassDef):
                scope.bindings.setdefault(item.name, []).append(None)
                self.rebound.add(item.name)
                stack.extend(reversed([*item.decorator_list, *item.bases]))
                for statement in item.body:
                    if isinstance(statement, ast.FunctionDef | ast.AsyncFunctionDef):
                        self._define(statement, scope, [*names, item.name], item.name, stack, bind=False)
                    else:
                        stack.append(statement)
            else:
                self._bind(item, scope)
                stack.extend(reversed(list(ast.iter_child_nodes(item))))

    def _define(self, item, scope: _Scope, names: list[str], cls: str | None, stack: list, *, bind=True) -> None:
        if bind:
            scope.bindings.setdefault(item.name, []).append(None)
            self.rebound.add(item.name)
        stack.extend([*item.decorator_list, *item.args.defaults, *(d for d in item.args.kw_defaults if d)])
        qualname = ".".join([*names, item.name])
        self.functions[qualname] = item
        self._build(item, _Scope(item, qualname, scope, cls), [*names, item.name])

    def _bind_target(self, target: ast.AST, value: ast.AST | None, scope: _Scope) -> None:
        if isinstance(target, ast.Name):
            scope.bindings.setdefault(target.id, []).append(value)
            self.rebound.add(target.id)
        elif isinstance(target, ast.Tuple | ast.List):
            for element in target.elts:
                self._bind_target(element, None, scope)
        elif isinstance(target, ast.Starred):
            self._bind_target(target.value, None, scope)

    def _import(self, local: str, target: str, scope: _Scope) -> None:
        if self.imports.get(local, target) != target:
            self.ambiguous.add(local)
        self.imports[local] = target
        scope.bindings.setdefault(local, []).append(None)

    def _bind(self, item: ast.AST, scope: _Scope) -> None:
        if isinstance(item, ast.Assign):
            for target in item.targets:
                self._bind_target(target, item.value, scope)
        elif isinstance(item, ast.AnnAssign | ast.NamedExpr):
            self._bind_target(item.target, item.value, scope)
        elif isinstance(item, ast.AugAssign | ast.For | ast.AsyncFor | ast.comprehension):
            self._bind_target(item.target, None, scope)
        elif isinstance(item, ast.withitem) and item.optional_vars is not None:
            self._bind_target(item.optional_vars, None, scope)
        elif isinstance(item, ast.Global | ast.Nonlocal):
            scope.declared.update(item.names)
        elif isinstance(item, ast.ExceptHandler) and item.name:
            self._bind_target(ast.Name(item.name), None, scope)
        elif isinstance(item, ast.Import):
            for alias in item.names:
                if alias.asname:
                    self._import(alias.asname, alias.name, scope)
                else:
                    self._import(alias.name.split(".")[0], alias.name.split(".")[0], scope)
        elif isinstance(item, ast.ImportFrom):
            package = _dotted(self.path).split(".")[: -item.level] if item.level else []
            base = ".".join([*package, *([item.module] if item.module else [])])
            for alias in item.names:
                self._import(alias.asname or alias.name, f"{base}.{alias.name}", scope)

    def scope_of(self, node: ast.AST) -> _Scope:
        while node not in self.scopes:
            node = self.parent[node]
        return self.scopes[node]

    def owner_scope(self, name: str, scope: _Scope) -> _Scope | None:
        current: _Scope | None = scope
        while current is not None:
            if name in current.bindings:
                return current
            current = current.parent
        return None


def _ancestors(module: _Module, node: ast.AST) -> Iterator[ast.AST]:
    while True:
        yield node
        node = module.parent[node]


@dataclass(frozen=True)
class Finding:
    module: str
    function: str
    site: str
    line: int

    def __str__(self) -> str:
        return f"{self.module}:{self.line} in {self.function}: {self.site}"


class Analysis:
    """The closed-allowlist check over a set of modules (see the module docstring)."""

    def __init__(self, modules: dict[str, _Module]) -> None:
        self.modules = modules
        self.by_dotted = {_dotted(path): module for path, module in modules.items() if path != OWNER}
        self.tainted_params: set[tuple[str, str, str]] = set()
        self.returns: set[tuple[str, str]] = set()

    # Name resolution.
    def resolve_dotted(self, module: _Module, node: ast.AST) -> str | None:
        if isinstance(node, ast.Name):
            if node.id in module.imports and node.id not in module.rebound | module.ambiguous:
                return module.imports[node.id]
            return None
        if isinstance(node, ast.Attribute):
            base = self.resolve_dotted(module, node.value)
            return f"{base}.{node.attr}" if base else None
        return None

    def resolve_function(self, module: _Module, func: ast.AST, scope: _Scope) -> tuple[_Module, str, int] | None:
        """The covered function a call reaches: (module, qualname, positional offset), or None."""
        if isinstance(func, ast.Name):
            owner = module.owner_scope(func.id, scope)
            if owner is not None and all(value is None for value in owner.bindings[func.id]):
                qualname = func.id if owner.qualname == "<module>" else f"{owner.qualname}.{func.id}"
                if qualname in module.functions:
                    return module, qualname, 0
        if (
            isinstance(func, ast.Attribute)
            and isinstance(func.value, ast.Name)
            and func.value.id == "self"
            and scope.cls is not None
        ):
            qualname = f"{scope.qualname.rsplit('.', 1)[0]}.{func.attr}"
            if qualname in module.functions:
                return module, qualname, 1
        full = self.resolve_dotted(module, func)
        if full:
            module_name, _, name = full.rpartition(".")
            target = self.by_dotted.get(module_name)
            if target is not None and name in target.functions:
                return target, name, 0
        return None

    def accessor(self, module: _Module, func: ast.AST) -> str | None:
        module_name, _, name = (self.resolve_dotted(module, func) or "").rpartition(".")
        return name if module_name == OWNER_DOTTED and name in ACCESSORS else None

    # Taint.
    def _name_tainted(self, module: _Module, name: str, scope: _Scope, seen: frozenset) -> bool:
        if name in SNAPSHOT_NAMES:
            return True
        owner = module.owner_scope(name, scope)
        if owner is None:
            return False
        if (module.path, owner.qualname, name) in self.tainted_params:
            return True
        key = (id(owner), name)
        if key in seen:
            return False
        return any(
            value is not None and self.tainted(module, value, owner, seen | {key}) for value in owner.bindings[name]
        )

    def tainted(self, module: _Module, node: ast.AST, scope: _Scope, seen: frozenset = frozenset()) -> bool:
        if isinstance(node, ast.Name):
            return isinstance(node.ctx, ast.Load) and self._name_tainted(module, node.id, scope, seen)
        if isinstance(node, ast.Attribute):
            return isinstance(node.ctx, ast.Load) and node.attr in SNAPSHOT_NAMES
        if isinstance(node, ast.Call):
            if (
                _call_name(node.func) == "getattr"
                and len(node.args) >= 2
                and isinstance(node.args[1], ast.Constant)
                and node.args[1].value in SNAPSHOT_NAMES
            ):
                return True
            if any(part in (_call_name(node.func) or "") for part in SOURCE_PARTS):
                return True
            target = self.resolve_function(module, node.func, scope)
            return target is not None and (target[0].path, target[1]) in self.returns
        if isinstance(node, ast.BoolOp):
            return any(self.tainted(module, value, scope, seen) for value in node.values)
        if isinstance(node, ast.IfExp):
            return self.tainted(module, node.body, scope, seen) or self.tainted(module, node.orelse, scope, seen)
        if isinstance(node, ast.Await | ast.NamedExpr):
            return self.tainted(module, node.value, scope, seen)
        return False

    # The sealed keyword dict.
    def sealed_kwargs(self, module: _Module, name: str, scope: _Scope) -> ast.Dict | None:
        """The dict literal ``name`` is bound to when it is sealed (see the module docstring), else None."""
        owner = module.owner_scope(name, scope)
        if owner is None or len(owner.bindings[name]) != 1 or not isinstance(owner.bindings[name][0], ast.Dict):
            return None
        literal = owner.bindings[name][0]
        account = [
            value
            for key, value in zip(literal.keys, literal.values, strict=True)
            if isinstance(key, ast.Constant) and key.value == ACCOUNT_KEYWORD
        ]
        if None in literal.keys or len(account) != 1 or _none_like(account[0]):
            return None
        for node in ast.walk(owner.node):
            if not isinstance(node, ast.Name) or node.id != name or node.ctx.__class__ is ast.Store:
                continue
            keyword = module.parent.get(node)
            call = module.parent.get(keyword)
            if not (
                isinstance(node.ctx, ast.Load)
                and isinstance(keyword, ast.keyword)
                and keyword.arg is None
                and isinstance(call, ast.Call)
                and _call_name(call.func) in ACCOUNT_REQUIRING_CALLS
            ):
                return None
        return literal

    def names_account(self, module: _Module, call: ast.Call, scope: _Scope) -> bool:
        for keyword in call.keywords:
            if keyword.arg == ACCOUNT_KEYWORD and not _none_like(keyword.value):
                return True
            if (
                keyword.arg is None
                and isinstance(keyword.value, ast.Name)
                and self.sealed_kwargs(module, keyword.value.id, scope) is not None
            ):
                return True
        return False

    # Uses.
    def _allowed_call_use(self, module: _Module, node: ast.AST, call: ast.Call, kw, scope: _Scope) -> bool:
        if call.func is node:
            return any(part in (_call_name(node) or "") for part in SOURCE_PARTS)
        func = call.func
        if _call_name(func) == "isinstance" and call.args and call.args[0] is node:
            return True
        accessor = self.accessor(module, func)
        if accessor is not None and ((kw is None and call.args[0] is node) or (kw is not None and kw.arg == "payload")):
            account = [k.value for k in call.keywords if k.arg == "account"]
            return not ACCESSORS[accessor] or (len(account) == 1 and not _none_like(account[0]))
        if kw is not None and kw.arg == "routing_snapshot":
            if _call_name(func) in ACCOUNT_REQUIRING_CALLS:
                return self.names_account(module, call, scope)
            if self.resolve_dotted(module, func) == "dataclasses.replace":
                return True
        target = self.resolve_function(module, func, scope)
        if target is None or any(isinstance(arg, ast.Starred) for arg in call.args):
            return False
        target_module, qualname, offset = target
        args = target_module.functions[qualname].args
        positional = [arg.arg for arg in (*args.posonlyargs, *args.args)][offset:]
        if kw is None:
            index = call.args.index(node)
            param = positional[index] if index < len(positional) else None
        else:
            param = kw.arg if kw.arg in {arg.arg for arg in (*args.args, *args.kwonlyargs)} else None
        if param is None:
            return False
        self.tainted_params.add((target_module.path, qualname, param))
        return True

    def _allowed_use(self, module: _Module, node: ast.AST, scope: _Scope) -> bool:
        parent = module.parent.get(node)
        grand = module.parent.get(parent) if parent is not None else None
        if isinstance(parent, ast.BoolOp | ast.IfExp | ast.Await | ast.NamedExpr | ast.Expr):
            return True  # the operator is derived too and checked where it is used; a discarded value is no read
        if isinstance(parent, ast.If | ast.While | ast.Assert) and parent.test is node:
            return True
        if isinstance(parent, ast.UnaryOp) and isinstance(parent.op, ast.Not):
            return True
        if isinstance(parent, ast.Compare):
            others = [operand for operand in (parent.left, *parent.comparators) if operand is not node]
            return all(isinstance(op, ast.Is | ast.IsNot) for op in parent.ops) and all(
                isinstance(other, ast.Constant) and other.value is None for other in others
            )
        if isinstance(parent, ast.Return):
            self.returns.add((module.path, scope.qualname))
            return True
        if isinstance(parent, ast.Assign | ast.AnnAssign) and parent.value is node:
            targets = parent.targets if isinstance(parent, ast.Assign) else [parent.target]
            # An alias stays in this scope; a ``global``/``nonlocal`` one would leave the analysis.
            return all(
                (isinstance(target, ast.Name) and target.id not in scope.declared)
                or (isinstance(target, ast.Attribute) and target.attr in SNAPSHOT_NAMES)
                for target in targets
            )
        if isinstance(parent, ast.Subscript) and parent.value is node:
            return isinstance(parent.slice, ast.Constant) and parent.slice.value in SAFE_FIELDS
        if isinstance(parent, ast.Attribute) and parent.attr == "get" and isinstance(grand, ast.Call):
            return (
                grand.func is parent
                and 1 <= len(grand.args) <= 2
                and not grand.keywords
                and isinstance(grand.args[0], ast.Constant)
                and grand.args[0].value in SAFE_FIELDS
            )
        if isinstance(parent, ast.Dict) and isinstance(grand, ast.Assign | ast.AnnAssign):
            # A value of a sealed keyword dict under ``routing_snapshot``.
            keys = dict(zip(map(id, parent.values), parent.keys, strict=True))
            key = keys.get(id(node))
            targets = grand.targets if isinstance(grand, ast.Assign) else [grand.target]
            return (
                isinstance(key, ast.Constant)
                and key.value == "routing_snapshot"
                and len(targets) == 1
                and isinstance(targets[0], ast.Name)
                and self.sealed_kwargs(module, targets[0].id, scope) is parent
            )
        if isinstance(parent, ast.keyword) and isinstance(grand, ast.Call):
            return self._allowed_call_use(module, node, grand, parent, scope)
        if isinstance(parent, ast.Call) and (parent.func is node or node in parent.args):
            return self._allowed_call_use(module, node, parent, None, scope)
        return False

    def _site(self, module: _Module, node: ast.AST) -> ast.AST:
        parent = module.parent.get(node, node)
        grand = module.parent.get(parent)
        if isinstance(parent, ast.keyword) and grand is not None:
            return grand
        if isinstance(parent, ast.Attribute) and isinstance(grand, ast.Call) and grand.func is parent:
            return grand
        return parent

    def _pass(self, paths) -> list[Finding]:
        sites: dict[int, Finding] = {}
        for path in paths:
            module = self.modules[path]
            for node in ast.walk(module.tree):
                if isinstance(node, ast.Constant) and node.value in SNAPSHOT_MAPS:
                    if isinstance(module.parent.get(node), ast.Expr):
                        continue  # a docstring
                elif not (
                    isinstance(node, ast.Name | ast.Attribute | ast.Call | ast.BoolOp | ast.IfExp | ast.Await)
                    and self.tainted(module, node, module.scope_of(node))
                    and not self._allowed_use(module, node, module.scope_of(node))
                ):
                    continue
                site = self._site(module, node)
                text = " ".join(ast.unparse(site).split())[:_SITE_CHARS]
                line = next(n.lineno for n in _ancestors(module, site) if hasattr(n, "lineno"))
                sites.setdefault(id(site), Finding(path, module.scope_of(site).qualname, text, line))
        return sorted(sites.values(), key=lambda finding: (finding.module, finding.line, finding.site))

    def run(self, paths=None) -> list[Finding]:
        """Findings in ``paths`` (default: every module but the owner), after the fixpoint of derived flow."""
        paths = [path for path in (paths or self.modules) if path != OWNER]
        while True:
            before = (len(self.tainted_params), len(self.returns))
            found = self._pass(paths)
            if (len(self.tainted_params), len(self.returns)) == before:
                return found


@functools.cache
def _parsed(path: str, source: str) -> _Module:
    return _Module(path, source)


def _covered_sources() -> dict[str, str]:
    return {path: (REPO_ROOT / path).read_text(encoding="utf-8") for path in (*COVERED, OWNER)}


@functools.cache
def _real_analysis() -> tuple[Analysis, tuple[Finding, ...]]:
    analysis = Analysis({path: _parsed(path, text) for path, text in _covered_sources().items()})
    return analysis, tuple(analysis.run())


def findings_with(module: str, source: str) -> list[Finding]:
    """Findings in ``module`` when its source is ``source``, every other covered module as it is.

    The derived flow of the real tree seeds the analysis, so the copy is
    checked with every parameter and return the rest of the tree derives.
    """
    real, _ = _real_analysis()
    analysis = Analysis({**real.modules, module: _Module(module, source)})
    analysis.tainted_params = set(real.tainted_params)
    analysis.returns = set(real.returns)
    return analysis.run([module])


def unlisted(findings: list[Finding], exceptions=None) -> tuple[list[Finding], list[tuple[str, str, str]]]:
    """Findings no exception lists, and exception sites no finding matches (both empty when the tree passes)."""
    exceptions = EXCEPTIONS if exceptions is None else exceptions
    listed = Counter(
        (module, function, site) for (module, function), (_reason, sites) in exceptions.items() for site in sites
    )
    remaining = Counter(listed)
    extra = []
    for finding in findings:
        key = (finding.module, finding.function, finding.site)
        if remaining[key] > 0:
            remaining[key] -= 1
        else:
            extra.append(finding)
    return extra, sorted(remaining.elements())


def account_less_calls(module: str, source: str) -> list[Finding]:
    """``ResolverInputs``/``resolver_inputs`` calls that do not name an account (explicit or sealed)."""
    parsed = _Module(module, source)
    analysis = Analysis({module: parsed})
    return [
        Finding(module, parsed.scope_of(node).qualname, "resolver inputs without claude_account", node.lineno)
        for node in ast.walk(parsed.tree)
        if isinstance(node, ast.Call)
        and _call_name(node.func) in ACCOUNT_REQUIRING_CALLS
        and not analysis.names_account(parsed, node, parsed.scope_of(node))
    ]


def account_constructions(source: str) -> list[int]:
    return [
        node.lineno
        for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.Call) and _call_name(node.func) == "ClaudeAccount"
    ]


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


# --- the ceiling ---------------------------------------------------------------------------


def _literal(tree: ast.Module, name: str) -> ast.AST | None:
    for statement in tree.body:
        targets = statement.targets if isinstance(statement, ast.Assign) else [getattr(statement, "target", None)]
        if any(isinstance(target, ast.Name) and target.id == name for target in targets):
            return statement.value
    return None


CEILINGS = ("EXCEPTIONS", "SAFE_FIELDS", "ACCESSORS", "EXEMPT")  # may not grow
FLOORS = ("SNAPSHOT_MAPS", "SNAPSHOT_NAMES", "SOURCE_PARTS", "ACCOUNT_REQUIRING_CALLS")  # may not shrink


def ceiling_literals(text: str) -> dict[str, Counter]:
    """The held literals of this file's ``text``, read from its syntax tree (nothing is executed).

    ``EXCEPTIONS`` gives the number of sites each function lists; the other
    :data:`CEILINGS` their member names; the :data:`FLOORS` every string in them.
    """
    tree = ast.parse(text)
    held: dict[str, Counter] = {"EXCEPTIONS": Counter()}
    node = _literal(tree, "EXCEPTIONS")
    for key, value in zip(node.keys, node.values, strict=True) if isinstance(node, ast.Dict) else ():
        sites = value.elts[1] if isinstance(value, ast.Tuple) and len(value.elts) == 2 else None
        # An entry the parser cannot count (``**`` or a computed tuple) counts as unbounded and fails.
        count = len(sites.elts) if isinstance(sites, ast.Tuple) and key is not None else 10**6
        held["EXCEPTIONS"][str(ast.literal_eval(key)) if key is not None else "<unpacked>"] += count
    for name in CEILINGS[1:]:
        node = _literal(tree, name)
        keys = node.keys if isinstance(node, ast.Dict) else []
        held[name] = Counter(str(ast.literal_eval(key)) if key is not None else "<unpacked>" for key in keys)
    for name in FLOORS:
        node = _literal(tree, name)
        strings = [] if node is None else [n.value for n in ast.walk(node) if isinstance(n, ast.Constant)]
        held[name] = Counter(value for value in strings if isinstance(value, str))
    return held


def ceiling_growth(current_text: str, ceiling_text: str) -> list[str]:
    """Every held literal of ``current_text`` above (or, for a floor, below) ``ceiling_text``'s."""
    current, ceiling = ceiling_literals(current_text), ceiling_literals(ceiling_text)
    problems = [
        f"{name} {key!r}: {count} above the ceiling {ceiling[name][key]}"
        for name in CEILINGS
        for key, count in sorted(current[name].items())
        if count > ceiling[name][key]
    ]
    problems += [f"{name} lost {key!r}" for name in FLOORS for key in sorted(ceiling[name]) if key not in current[name]]
    return problems


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess:
    # A pre-push hook exports GIT_DIR and the like; they must not redirect a scratch repository to this one.
    env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    return subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, timeout=60, env=env)


def exception_ceiling_violations(repo: Path, path: str = THIS_FILE) -> list[str]:
    """What ``repo``'s working copy of ``path`` holds above its ceiling (see the module docstring)."""
    base = _git(repo, "merge-base", "HEAD", "origin/main")
    assert base.returncode == 0, f"origin/main is not available: the exception ceiling needs history: {base.stderr}"
    for ref in (base.stdout.strip(), "origin/main"):
        shown = _git(repo, "show", f"{ref}:{path}")
        if shown.returncode == 0:
            return ceiling_growth((repo / path).read_text(encoding="utf-8"), shown.stdout)
    history = _git(repo, "log", "-1", "--format=%H", "origin/main", "--", path)
    assert history.returncode == 0, history.stderr
    if history.stdout.strip():
        return [f"{path} was on origin/main ({history.stdout.strip()}) and is gone: no ceiling to hold it to"]
    return []  # its first PR: the literals in this file are the ceiling its reviewers approve


# --- the real tree passes -------------------------------------------------------------------


@pytest.mark.repo_wide
def test_every_snapshot_consumer_is_covered_or_exempt():
    assert _snapshot_modules() - set(COVERED) - {OWNER} - set(EXEMPT) == set()
    # A covered or exempt module that no longer names a snapshot is removed from the list.
    assert set(EXEMPT) <= _snapshot_modules()
    assert all(reason.strip() for reason in EXEMPT.values())


def test_no_consumer_uses_the_routing_snapshot_outside_the_allowlist():
    _, findings = _real_analysis()
    extra, stale = unlisted(list(findings))
    problems = [f"unlisted use of the routing snapshot: {finding}" for finding in extra]
    problems += [f"exception matches no site: {site}" for site in stale]
    assert problems == [], (
        "read the claude lane through scripts.fleet.claude_account_lane with a named ClaudeAccount "
        f"(select_account, account_agents, lane_record, capacity_verdict); see the module docstring: {problems}"
    )


def test_every_exception_names_a_covered_function_and_a_reason():
    for (module, function), (reason, sites) in EXCEPTIONS.items():
        assert module in COVERED and module != OWNER, module
        assert function and reason.strip() and sites, (module, function)
    assert all(reason.strip() for reason in SAFE_FIELDS.values())
    assert not SAFE_FIELDS.keys() & SNAPSHOT_MAPS


def test_the_exceptions_stay_under_their_ceiling():
    """No function lists more sites, and no allowlist grows, than this file at the merge base (module docstring)."""
    assert exception_ceiling_violations(REPO_ROOT) == []


@pytest.mark.repo_wide
def test_claude_accounts_are_built_only_by_their_owner():
    built = {
        module: account_constructions(text) for module, text in _scripts_sources().items() if "ClaudeAccount(" in text
    }
    assert {module for module, sites in built.items() if sites} == {OWNER}


@pytest.mark.repo_wide
def test_every_resolver_snapshot_names_its_claude_account():
    unnamed = [
        str(problem)
        for module, text in _scripts_sources().items()
        if "resolver_inputs" in text or "ResolverInputs" in text
        for problem in account_less_calls(module, text)
    ]
    assert unnamed == []


# --- the check itself: an injected bypass is caught -----------------------------------------

# Each is appended to a consumer; a name it defines starts with ``_inj`` so several can share a copy.
# The four bypasses the review of e98e30c5 found, and their siblings.
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
    "module_constant_key": '_inj_LANES = "agents"\n\n\ndef _injected_bypass(payload):\n    return payload[_inj_LANES]\n',
    "dynamic_key_on_a_snapshot": "def _injected_bypass(snapshot, key):\n    return snapshot[key]\n",
    "dynamic_get_on_a_literal_root": (
        'def _injected_bypass(payload, key):\n    payload.get("agents")\n    return payload.get(key)\n'
    ),
    "dynamic_getattr_on_a_snapshot": "def _injected_bypass(budget, method):\n    return getattr(budget, method)\n",
    "dict_get_unbound": 'def _injected_bypass(payload):\n    return dict.get(payload, "claude_accounts")\n',
    "itemgetter": 'import operator\n\n\ndef _injected_bypass(payload):\n    return operator.itemgetter("agents")(payload)\n',
    "lambda_filter": (
        'def _injected_bypass(snapshot):\n    return dict(filter(lambda kv: kv[0] == "claude", snapshot.items()))\n'
    ),
    "loop_filter": (
        "def _injected_bypass(snapshot):\n    for lane, row in snapshot.items():\n"
        '        if lane == "claude":\n            return row\n'
    ),
    "aliased_dict_update": (
        "def _injected_bypass(snap):\n    common = {}\n    common.update(routing_snapshot=snap)\n"
        "    return ResolverInputs(**dict(common))\n"
    ),
    "unresolvable_forwarding": "def _injected_bypass(options):\n    return ResolverInputs(**options)\n",
    "method_forwarding": 'def _injected_bypass(facts, snap):\n    return facts.resolver_inputs(risk="low", routing_snapshot=snap)\n',
}
# The ten the review of b7258c532b found (nine passed the deny-list check), as the review describes them.
SOL_INJECTIONS = {
    "sol_bound_getter": 'def _injected_bypass(snap):\n    read = snap.get\n    return read("agents", {})["claude"]\n',
    "sol_bound_getitem": "def _injected_bypass(snap, lanes):\n    read = snap.__getitem__\n    return read(lanes)['claude']\n",
    "sol_aliased_itemgetter": (
        "from operator import itemgetter as _inj_pick\n\n\n"
        "def _injected_bypass(snap, lanes):\n    return _inj_pick(lanes)(snap)['claude']\n"
    ),
    "sol_aliased_dict_get": "def _injected_bypass(snap, lanes):\n    read = dict.get\n    return read(snap, lanes)['claude']\n",
    "sol_variable_based_filter": (
        "def _injected_bypass(snap, wanted):\n    return [row for lane, row in snap.items() if lane == wanted]\n"
    ),
    "sol_plain_map_comprehension": "def _injected_bypass(snap):\n    return {lane: row for lane, row in snap.items()}\n",
    "sol_conditional_account_kwarg": (
        'def _injected_bypass(snap, account, flag):\n    kw = {"routing_snapshot": snap}\n    if flag:\n'
        '        kw["claude_account"] = account\n    return ResolverInputs(**kw)\n'
    ),
    "sol_deleted_account_kwarg": (
        'def _injected_bypass(snap, account):\n    kw = {"routing_snapshot": snap, "claude_account": account}\n'
        '    del kw["claude_account"]\n    return ResolverInputs(**kw)\n'
    ),
    "sol_popped_account_kwarg": (
        'def _injected_bypass(snap, account):\n    kw = {"routing_snapshot": snap, "claude_account": account}\n'
        '    kw.pop("claude_account")\n    return ResolverInputs(**kw)\n'
    ),
    "sol_dynamic_key_bound_getter": "def _injected_bypass(snap, key):\n    read = snap.get\n    return read(key)\n",
}
# Further uses the allowlist must reject.
OWN_INJECTIONS = {
    "getattr_snapshot_attribute": 'def _injected_bypass(inputs, key):\n    return getattr(inputs, "routing_snapshot")[key]\n',
    "attribute_items": "def _injected_bypass(inputs):\n    return dict(inputs.routing_snapshot.items())\n",
    "tuple_unpacking": "def _injected_bypass(snap):\n    first, *rest = snap\n    return first\n",
    "double_star_call": "def _injected_bypass(snap):\n    return types.SimpleNamespace(**snap)\n",
    "dict_merge": "def _injected_bypass(snap):\n    merged = {**snap}\n    return merged\n",
    "list_container": "def _injected_bypass(snap):\n    box = [snap]\n    return box[0]\n",
    "for_iteration": "def _injected_bypass(snap):\n    for key in snap:\n        return key\n",
    "next_iter_values": "def _injected_bypass(snap):\n    return next(iter(snap.values()))\n",
    "fstring": 'def _injected_bypass(snap):\n    return f"{snap}"\n',
    "json_dumps": "def _injected_bypass(snap):\n    return json.dumps(snap)\n",
    "lambda_closure": "def _injected_bypass(snap):\n    grab = lambda: snap\n    return grab()\n",
    "nested_closure": (
        "def _injected_bypass(snap, key):\n    def _inj_inner():\n        return snap.get(key)\n\n    return _inj_inner()\n"
    ),
    "covered_helper_parameter": (
        "def _inj_helper(rows, key):\n    return rows[key]\n\n\n"
        "def _injected_bypass(snap, key):\n    return _inj_helper(snap, key)\n"
    ),
    "returned_source": (
        "def _inj_fetch():\n    return _fetch_routing_budget()\n\n\n"
        "def _injected_bypass(key):\n    return _inj_fetch()[key]\n"
    ),
    "walrus_source": (
        "def _injected_bypass(key):\n    if (rows := _fetch_routing_budget()) is not None:\n        return rows[key]\n"
    ),
    "awaited_source": (
        "async def _injected_bypass(key):\n    rows = await _fetch_routing_budget_async()\n    return rows[key]\n"
    ),
    "attribute_store": "class _inj_Holder:\n    def __init__(self, snap):\n        self.rows = snap\n",
    "accessor_without_account": (
        "def _injected_bypass(snap):\n    from scripts.fleet import claude_account_lane\n\n"
        '    return claude_account_lane.lane_record(snap, "claude")\n'
    ),
    "accessor_account_none": (
        "def _injected_bypass(snap):\n    from scripts.fleet import claude_account_lane\n\n"
        '    return claude_account_lane.lane_record(snap, "claude", account=None)\n'
    ),
    "owner_non_accessor": (
        "def _injected_bypass(snap):\n    from scripts.fleet import claude_account_lane\n\n"
        "    return claude_account_lane.route_facts(snap)\n"
    ),
    "shadowed_accessor": (
        "def _injected_bypass(snap, account, key):\n    select_account = dict.fromkeys\n"
        "    return select_account(snap, account=account)[key]\n"
    ),
    "resolver_account_none": "def _injected_bypass(snap):\n    return ResolverInputs(routing_snapshot=snap, claude_account=None)\n",
    "resolver_account_maybe_none": (
        "def _injected_bypass(snap, account, flag):\n"
        "    return ResolverInputs(routing_snapshot=snap, claude_account=account if flag else None)\n"
    ),
    "kwargs_dict_used_elsewhere": (
        'def _injected_bypass(snap, account):\n    kw = {"routing_snapshot": snap, "claude_account": account}\n'
        "    _inj_log(kw)\n    return ResolverInputs(**kw)\n"
    ),
    "kwargs_dict_with_an_unpacked_entry": (
        "def _injected_bypass(snap, account, extra):\n"
        '    kw = {"routing_snapshot": snap, "claude_account": account, **extra}\n    return ResolverInputs(**kw)\n'
    ),
    "unlisted_field": 'def _injected_bypass(snap):\n    return snap.get("recommendation")\n',
    "concatenated_key": 'def _injected_bypass(snap):\n    return snap.get("age" + "nts")\n',
    "method_on_a_snapshot": "def _injected_bypass(snap):\n    return snap.copy()\n",
    "starred_argument": "def _injected_bypass(snap):\n    return _inj_sink(*snap)\n",
    "yield": "def _injected_bypass(snap):\n    yield snap\n",
    "equality": "def _injected_bypass(snap, other):\n    return snap == other\n",
    "global_alias": "_inj_HELD = None\n\n\ndef _injected_bypass(snap):\n    global _inj_HELD\n    _inj_HELD = snap\n",
    "nonlocal_alias": (
        "def _injected_bypass(snap, key):\n    held = None\n\n    def _inj_keep():\n        nonlocal held\n"
        "        held = snap\n\n    _inj_keep()\n    return held[key]\n"
    ),
    "match_statement": (
        "def _injected_bypass(snap):\n    match snap:\n        case {'agents': {'claude': row}}:\n            return row\n"
    ),
}
ALL_INJECTIONS = {**INJECTIONS, **SOL_INJECTIONS, **{f"own_{name}": text for name, text in OWN_INJECTIONS.items()}}
INJECTED_CONSUMERS = [module for module in COVERED if module != OWNER]
# The smallest covered consumer: every injection is checked alone in a copy of it.
SINGLE_HOST = "scripts/review/capacity.py"


def _tagged(name: str, text: str) -> str:
    """``text`` with every name it defines made unique to ``name``."""
    return re.sub(r"\b_inj", f"_inj_{name}_", text)


def _problems(module: str, source: str) -> list[Finding]:
    extra, _stale = unlisted(findings_with(module, source))
    return extra + account_less_calls(module, source)


@pytest.mark.parametrize("injection", sorted(ALL_INJECTIONS))
def test_an_injected_bypass_fails_the_check(injection):
    host = (REPO_ROOT / SINGLE_HOST).read_text(encoding="utf-8")
    assert _problems(SINGLE_HOST, host) == []
    copy = host + "\n\n" + ALL_INJECTIONS[injection]
    problems = _problems(SINGLE_HOST, copy)
    first = len(host.splitlines()) + 1
    assert problems, f"{injection} passed the check"
    assert all(problem.line > first for problem in problems), [str(problem) for problem in problems]


@pytest.mark.parametrize("module", INJECTED_CONSUMERS)
def test_every_injection_fails_inside_every_consumer(module):
    """One copy of ``module`` carries every injection; each injection's own lines must hold a problem."""
    source = (REPO_ROOT / module).read_text(encoding="utf-8")
    ranges: dict[str, range] = {}
    for name, text in sorted(ALL_INJECTIONS.items()):
        start = len(source.splitlines()) + 3
        source += "\n\n" + _tagged(name, text)
        ranges[name] = range(start, len(source.splitlines()) + 1)
    lines = {problem.line for problem in _problems(module, source)}
    passed = sorted(name for name, span in ranges.items() if not lines & set(span))
    assert passed == [], f"injected into {module}, these passed the check: {passed}"


def test_a_raw_read_added_inside_a_listed_function_fails():
    """The review of b7258c532b's reproducer: a further read inside ``resolve_reviewer`` is a new site."""
    module = "scripts/review/reviewer_resolver.py"
    source = (REPO_ROOT / module).read_text(encoding="utf-8")
    anchor = '                agents = (inputs.routing_snapshot or {}).get("agents", {})\n'
    assert source.count(anchor) == 1
    copy = source.replace(
        anchor, anchor + '                agents = (inputs.routing_snapshot or {}).get("agents", {})\n'
    )
    extra, _stale = unlisted(findings_with(module, copy))
    assert [(problem.function, problem.site) for problem in extra] == [
        ("resolve_reviewer", "(inputs.routing_snapshot or {}).get('agents', {})")
    ]
    # Listing it raises that function's ceiling, which a later commit cannot do.
    this = (REPO_ROOT / THIS_FILE).read_text(encoding="utf-8")
    literal = _literal(ast.parse(this), "EXCEPTIONS")
    assert isinstance(literal, ast.Dict)
    sites = next(
        value.elts[1]
        for key, value in zip(literal.keys, literal.values, strict=True)
        if ast.literal_eval(key) == (module, "resolve_reviewer")
    )
    offsets = [0]
    for line in this.splitlines(keepends=True):
        offsets.append(offsets[-1] + len(line))
    start = offsets[sites.lineno - 1] + sites.col_offset
    end = offsets[sites.end_lineno - 1] + sites.end_col_offset
    doubled = "(" + "".join(f"{element.value!r}, " for element in sites.elts * 2) + ")"
    raised = this[:start] + doubled + this[end:]
    assert ceiling_growth(raised, this) == [f"EXCEPTIONS {str((module, 'resolve_reviewer'))!r}: 2 above the ceiling 1"]


@pytest.mark.parametrize(
    "source",
    [
        # A field with no account meter, through the snapshot and through ``x or {}``.
        'def f(snap):\n    return snap.get("diagnostics"), (snap or {})["in_flight"]\n',
        # An accessor with the account, directly and from a covered helper the snapshot passes through.
        "from scripts.fleet import claude_account_lane\n\n\n"
        'def f(snap, account):\n    return claude_account_lane.lane_record(snap, "codex", account=account)\n',
        "from scripts.fleet.claude_account_lane import select_account\n\n\n"
        "def _g(rows, account):\n    return select_account(rows, account=account)\n\n\n"
        "def f(snap, account):\n    return _g(snap, account)\n",
        "from scripts.fleet import claude_account_lane\n\n\n"
        "def f(account):\n    payload = _fetch_routing_budget() or {}\n"
        "    return claude_account_lane.capacity_verdict(payload, account=account)\n",
        # Type and presence tests, a return, and a value that is no snapshot.
        "def f(snap):\n    if not snap or snap is None or isinstance(snap, dict):\n        return None\n    return snap\n",
        "def f(record, key):\n    return record[key]\n",
        # Named accounts: explicit, sealed keyword dicts, forwarding with an explicit account, replace.
        "def f(snapshot, acct):\n    return ResolverInputs(author_model='x', routing_snapshot=snapshot, claude_account=acct)\n",
        'def f(snap, acct):\n    common = {"routing_snapshot": snap, "claude_account": acct}\n'
        "    return x.resolver_inputs(risk='low', **common)\n",
        "def f(acct, **overrides):\n    return ResolverInputs(claude_account=acct, **overrides)\n",
        "from dataclasses import replace\n\n\ndef f(inputs, runtime_state):\n"
        "    return replace(inputs, routing_snapshot=runtime_state)\n",
    ],
)
def test_the_check_passes_what_is_not_a_bypass(source):
    module = "scripts/fleet/_snippet.py"
    analysis = Analysis({module: _Module(module, source)})
    assert [str(finding) for finding in analysis.run()] == []
    assert account_less_calls(module, source) == []


def test_the_check_names_the_site_of_each_use():
    module = "scripts/fleet/_snippet.py"
    found = Analysis({module: _Module(module, SOL_INJECTIONS["sol_bound_getter"])}).run()
    assert [(finding.function, finding.site, finding.line) for finding in found] == [
        ("_injected_bypass", "snap.get", 2),
        ("_injected_bypass", "read('agents', {})", 3),
    ]


def test_the_check_catches_an_injected_account_construction():
    assert account_constructions('def f():\n    return ClaudeAccount("a", "builtin")\n')


# --- the ceiling holds on real commits ------------------------------------------------------


def _committed(repo: Path, text: str, message: str) -> None:
    path = repo / THIS_FILE
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    for args in (("add", "-A"), ("commit", "-q", "-m", message)):
        result = _git(repo, *args)
        assert result.returncode == 0, result.stderr


def _scratch_repo(tmp_path: Path, name: str) -> Path:
    repo = tmp_path / name
    repo.mkdir()
    for args in (
        ("init", "-q", "-b", "main"),
        ("config", "user.name", "ceiling test"),
        ("config", "user.email", "ceiling-test@example.invalid"),
        ("config", "commit.gpgsign", "false"),
        ("config", "core.hooksPath", "/dev/null"),
    ):
        assert _git(repo, *args).returncode == 0
    return repo


def _held(sites: int, fields: tuple[str, ...] = ("diagnostics",)) -> str:
    listed = ", ".join(repr(f"site {index}") for index in range(sites))
    return (
        f'EXCEPTIONS = {{("scripts/m.py", "f"): ("why", ({listed},))}}\n'
        f"SAFE_FIELDS = {{{', '.join(f'{field!r}: {field!r}' for field in fields)}}}\n"
        'ACCESSORS = {"lane_record": True}\nEXEMPT = {}\nSNAPSHOT_MAPS = frozenset({"agents", "claude_accounts"})\n'
    )


def _head(repo: Path) -> str:
    return _git(repo, "rev-parse", "HEAD").stdout.strip()


def _move(repo: Path, ref: str, sha: str) -> None:
    """Point ``ref`` at ``sha`` (``refs/heads/main`` moves HEAD with it; no branch is switched)."""
    assert _git(repo, "update-ref", ref, sha).returncode == 0


def test_a_raised_exception_ceiling_fails_in_a_real_repository(tmp_path):
    repo = _scratch_repo(tmp_path, "landed")
    _committed(repo, _held(2), "the check lands on main")
    _move(repo, "refs/remotes/origin/main", _head(repo))
    _committed(repo, _held(2) + "# an unrelated line\n", "an unrelated change")
    assert exception_ceiling_violations(repo) == []
    # A second commit raises one function's count: the merge base's copy is the ceiling, not HEAD's.
    _committed(repo, _held(3), "list one more site")
    assert exception_ceiling_violations(repo) == ["EXCEPTIONS \"('scripts/m.py', 'f')\": 3 above the ceiling 2"]
    # A new allowlist member, and a lost map name, fail too; shrinking passes.
    _committed(repo, _held(1, ("diagnostics", "recommendation")), "allow another field")
    assert exception_ceiling_violations(repo) == ["SAFE_FIELDS 'recommendation': 1 above the ceiling 0"]
    _committed(repo, _held(1).replace('"agents", ', ""), "drop a map name")
    assert exception_ceiling_violations(repo) == ["SNAPSHOT_MAPS lost 'agents'"]
    _committed(repo, _held(1), "list fewer sites")
    assert exception_ceiling_violations(repo) == []


def test_the_first_pr_is_its_own_ceiling_and_a_removed_file_fails_closed(tmp_path):
    repo = _scratch_repo(tmp_path, "first")
    (repo / "README").write_text("main\n", encoding="utf-8")
    assert _git(repo, "add", "README").returncode == 0
    assert _git(repo, "commit", "-q", "-m", "main").returncode == 0
    main = _head(repo)
    _move(repo, "refs/remotes/origin/main", main)
    _committed(repo, _held(2), "the check, first version")
    first = _head(repo)
    _committed(repo, _held(3), "the same PR lists one more site")
    assert exception_ceiling_violations(repo) == []  # main never had the file: this PR's reviewers approve it
    # Once main has the file, a branch whose merge base lacks it is held to main's copy.
    _move(repo, "refs/remotes/origin/main", first)
    _move(repo, "refs/heads/main", main)
    _committed(repo, _held(4), "a stale branch lists more")
    assert exception_ceiling_violations(repo) == ["EXCEPTIONS \"('scripts/m.py', 'f')\": 4 above the ceiling 2"]
    # A file main had and then removed has no ceiling to hold it to: fail closed.
    assert _git(repo, "rm", "-q", THIS_FILE).returncode == 0
    assert _git(repo, "commit", "-q", "-m", "remove the check").returncode == 0
    _move(repo, "refs/remotes/origin/main", _head(repo))
    _committed(repo, _held(5), "re-add it with more")
    assert exception_ceiling_violations(repo)[0].startswith(f"{THIS_FILE} was on origin/main")
