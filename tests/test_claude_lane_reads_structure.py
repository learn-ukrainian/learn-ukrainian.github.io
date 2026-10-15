"""#10630 S2: no consumer reads the routing snapshot's claude lane without naming the account.

The routing-budget payload's ``agents`` map holds the ``claude`` lane row (the
Monitor host's default account's meter) and ``claude_accounts`` holds every
other account's row. ``scripts/fleet/claude_account_lane.py`` owns both reads
and requires a ``ClaudeAccount`` for the claude lane (``other_lane_record``
refuses it). This bounded static check fails when, in any covered consumer:

- a read of either map (``X["agents"]``, ``X.get("agents")``, and the same for
  ``claude_accounts``) is not in :data:`BASELINE` with its disposition. The
  baseline may only shrink: a listed read that is gone (or fewer) fails too;
- a ``ClaudeAccount`` is constructed outside its owner module;
- a ``ResolverInputs(...)`` or ``.resolver_inputs(...)`` call passes a
  ``routing_snapshot`` without naming ``claude_account``.

Coverage is every module outside the producer (``scripts/api/``) that names a
routing snapshot source or the snapshot itself (:func:`_snapshot_modules`);
:data:`EXEMPT` lists the ones that mention one without reading it. The check is
syntactic: a read through ``getattr``, an aliased key or another module's
helper is not seen, and a baseline disposition is asserted here, not proven.
The runtime checks (``require_account``, the admission backstop) and the
agreement test (``tests/test_claude_account_route_key.py``) are the backstop.
"""

from __future__ import annotations

import ast
import functools
from collections import Counter
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
OWNER = "scripts/fleet/claude_account_lane.py"
SNAPSHOT_MAPS = frozenset({"agents", "claude_accounts"})
_SOURCE_MARKERS = (
    "routing-budget",
    "compute_routing_budget",
    "read_routing_budget",
    "_fetch_routing_budget",
    "routing_snapshot",
    "claude_accounts",
)

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
# Consumers whose remaining raw reads are listed in BASELINE with their disposition.
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

CALLER_KEYED = "caller-keyed: reads the snapshot its caller passed, already claude_account_lane.select_account's view"
DISPLAY = "display: prints or validates lane rows; no routing decision reads the result"
ISOLATED = (
    "isolated launcher reader (python -I cannot import the owner): reads agents.claude only for "
    "the default account and claude_accounts only for the account launch_account() names"
)
# (module, function, map): (count, disposition). May only shrink.
BASELINE: dict[tuple[str, str, str], tuple[int, str]] = {
    ("scripts/lib/claude_weekly_used.py", "_weekly_used_pct", "agents"): (1, ISOLATED),
    ("scripts/lib/claude_weekly_used.py", "_weekly_used_pct", "claude_accounts"): (1, ISOLATED),
    (
        "scripts/fleet/capacity_pick.py",
        "build_lane_rows",
        "agents",
    ): (2, "advisory picker display: the dispatch budget guard re-judges the claude seat on its account"),
    ("scripts/fleet/usage.py", "_attach_status_observations", "agents"): (1, DISPLAY),
    ("scripts/fleet/usage.py", "format_human", "agents"): (4, DISPLAY),
    ("scripts/fleet/usage.py", "qa_snapshot", "agents"): (2, DISPLAY),
    ("scripts/review/reviewer_resolver.py", "normalize_routing_snapshot", "agents"): (1, CALLER_KEYED),
    ("scripts/review/reviewer_resolver.py", "_near_cap_credit", "agents"): (1, CALLER_KEYED),
    ("scripts/review/reviewer_resolver.py", "resolve_reviewer", "agents"): (1, CALLER_KEYED),
    ("scripts/review/reviewer_scheduler.py", "_route_record", "agents"): (1, CALLER_KEYED),
    (
        "scripts/orchestration/curriculum_coordinator.py",
        "_health_assessment",
        "agents",
    ): (1, CALLER_KEYED + " (default_health_probe keys it)"),
}


def _is_map_key(node: ast.AST) -> str | None:
    return node.value if isinstance(node, ast.Constant) and node.value in SNAPSHOT_MAPS else None


class _Scan(ast.NodeVisitor):
    """Raw snapshot-map reads, ``ClaudeAccount`` constructions and resolver-input calls, by enclosing function."""

    def __init__(self) -> None:
        self.stack: list[str] = []
        self.reads: Counter[tuple[str, str]] = Counter()
        self.constructions: list[tuple[str, int]] = []
        self.unnamed_snapshots: list[tuple[str, int]] = []
        self.dict_literals: list[dict[str, set[str]]] = [{}]

    def _where(self) -> str:
        return ".".join(self.stack) or "<module>"

    def visit_FunctionDef(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        # Dict literals bound to a local name, so ``**common`` keyword sets are seen.
        literals: dict[str, set[str]] = {}
        for item in ast.walk(node):
            targets = (
                item.targets
                if isinstance(item, ast.Assign)
                else [item.target]
                if isinstance(item, ast.AnnAssign) and item.value is not None
                else []
            )
            value = item.value if isinstance(item, ast.Assign | ast.AnnAssign) else None
            if isinstance(value, ast.Dict):
                for target in targets:
                    if isinstance(target, ast.Name):
                        literals[target.id] = {
                            key.value
                            for key in value.keys
                            if isinstance(key, ast.Constant) and isinstance(key.value, str)
                        }
        self.stack.append(node.name)
        self.dict_literals.append(literals)
        self.generic_visit(node)
        self.dict_literals.pop()
        self.stack.pop()

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self.stack.append(node.name)
        self.generic_visit(node)
        self.stack.pop()

    def visit_Subscript(self, node: ast.Subscript) -> None:
        key = _is_map_key(node.slice)
        if key and isinstance(node.ctx, ast.Load):
            self.reads[(self._where(), key)] += 1
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        func = node.func
        name = func.id if isinstance(func, ast.Name) else func.attr if isinstance(func, ast.Attribute) else None
        if isinstance(func, ast.Attribute) and func.attr in {"get", "pop", "setdefault"} and node.args:
            key = _is_map_key(node.args[0])
            if key:
                self.reads[(self._where(), key)] += 1
        if name == "ClaudeAccount":
            self.constructions.append((self._where(), node.lineno))
        if name in {"ResolverInputs", "resolver_inputs"}:
            keywords: set[str] = set()
            for keyword in node.keywords:
                if keyword.arg is not None:
                    keywords.add(keyword.arg)
                elif isinstance(keyword.value, ast.Name) and keyword.value.id in self.dict_literals[-1]:
                    keywords |= self.dict_literals[-1][keyword.value.id]
            if "routing_snapshot" in keywords and "claude_account" not in keywords:
                self.unnamed_snapshots.append((self._where(), node.lineno))
        self.generic_visit(node)


def scan(source: str) -> _Scan:
    visitor = _Scan()
    visitor.visit(ast.parse(source))
    return visitor


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


def _reads(module: str) -> Counter[tuple[str, str]]:
    return scan((REPO_ROOT / module).read_text(encoding="utf-8")).reads


@pytest.mark.repo_wide
def test_every_snapshot_consumer_is_covered_or_exempt():
    assert _snapshot_modules() - set(COVERED) - set(EXEMPT) == set()
    # A covered or exempt module that no longer names a snapshot is removed from the list.
    assert set(EXEMPT) <= _snapshot_modules()
    assert all(reason.strip() for reason in EXEMPT.values())


@pytest.mark.parametrize("module", [module for module in COVERED if module != OWNER])
def test_no_consumer_reads_the_snapshot_lane_maps_outside_the_baseline(module):
    actual = {(module, where, key): count for (where, key), count in _reads(module).items()}
    listed = {key: count for key, (count, _reason) in BASELINE.items() if key[0] == module}
    unlisted = {key: count for key, count in actual.items() if key not in listed}
    assert unlisted == {}, (
        "read the claude lane through scripts.fleet.claude_account_lane with a named ClaudeAccount "
        f"(lane_record, account_agents, other_lane_record), not the snapshot's maps: {unlisted}"
    )
    # The baseline only shrinks: a listed read that was removed (or reduced) is removed here too.
    assert {key: actual.get(key, 0) for key in listed} == listed


def test_decision_consumers_have_no_baseline_reads():
    assert {key for key in BASELINE if key[0] in DECISION_CONSUMERS} == set()
    assert all(reason.strip() for _count, reason in BASELINE.values())


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
        if (sites := scan(text).unnamed_snapshots)
    }
    assert unnamed == {}


# --- the check itself: an injected bare read, construction or unnamed snapshot is caught ---


@pytest.mark.parametrize(
    "injected",
    [
        'def budget_guard(payload):\n    return payload["agents"]["claude"]["status"]\n',
        'def budget_guard(payload):\n    return (payload.get("agents") or {}).get("claude", {})\n',
        'def budget_guard(payload, lane):\n    agents = payload.get("agents", {})\n    return agents.get(lane)\n',
        'def headroom(payload):\n    return payload["claude_accounts"]["claude:b"]\n',
        'def headroom(payload):\n    return payload.get("claude_accounts")\n',
    ],
)
def test_the_scan_catches_an_injected_bare_lane_read(injected):
    reads = scan(injected).reads
    assert sum(reads.values()) >= 1
    source = (REPO_ROOT / "scripts/agent_runtime/model_pause.py").read_text(encoding="utf-8")
    # The same read injected into a decision consumer would be an unlisted read there.
    assert set(scan(source + "\n\n" + injected).reads) - set(scan(source).reads)


def test_the_scan_catches_an_injected_account_construction_and_unnamed_snapshot():
    assert scan('def f():\n    return ClaudeAccount("a", "builtin")\n').constructions
    assert scan("def f(snapshot):\n    return ResolverInputs(routing_snapshot=snapshot)\n").unnamed_snapshots
    assert scan(
        'def f(snapshot):\n    common = {"routing_snapshot": snapshot}\n    return ResolverInputs(**common)\n'
    ).unnamed_snapshots
    named = 'def f(snapshot, acct):\n    common = {"routing_snapshot": snapshot, "claude_account": acct}\n'
    assert not scan(named + "    return x.resolver_inputs(risk='low', **common)\n").unnamed_snapshots
