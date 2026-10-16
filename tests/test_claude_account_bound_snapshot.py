"""#10770 S2b: a decision reads a claude meter only from a snapshot bound to its ClaudeAccount.

The routing-budget payload carries several Claude accounts' meters: the
``claude`` lane row (the host's default account ``a``), every
``claude_accounts`` row, the claude rows of ``ranked_by_headroom`` and
``preferred_claude_account``. A decision consumer binds the payload where it
enters (``claude_account_lane.bind_snapshot``); the bound view holds the
account's own meter and no other, so however a covered module reads what it
holds (walrus, decorators, rebinding, dynamic keys, ``eval``, ``vars``,
``__dict__``, aliased getters, helper forwarding) it reads that account's
meter or fails closed. A decision helper reaching the claude lane of an
unbound payload raises ``AccountRequired``, which no broad handler turns into
missing data. Display consumers keep the plain payload.

The reversed-meter fixture is the reviews' reproducer: account ``a`` has 90%
remaining, account ``b`` 0.5%.
"""

from __future__ import annotations

import ast
import copy
import io
import json
import operator
import pickle
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

import pytest

from scripts import delegate
from scripts.agent_runtime import model_pause, target_admission
from scripts.fleet import capacity_pick, claude_account_lane, credit_lane, usage
from scripts.fleet.claude_account_lane import AccountRequired, AccountSnapshot, bind_snapshot, select_account
from scripts.lib import claude_weekly_used
from scripts.orchestration import curriculum_coordinator as coordinator
from scripts.review import bench_health, closeout_cli, reviewer_resolver, reviewer_scheduler
from scripts.review.reviewer_resolver import REVIEW_CANDIDATES, ResolverInputs, resolve_reviewer
from tests.claude_route_accounts import HOST_ACCOUNT, account, bound, unresolved
from tests.test_claude_account_route_key import _agreement_snapshot, _route_key_for
from tests.test_delegate_check_budget import _account_row

REPO_ROOT = Path(__file__).resolve().parents[1]
B = account("b")
A_REMAINING, B_REMAINING = 90.0, 0.5
CLAUDE = REVIEW_CANDIDATES["claude-opus-5-5"]
CODEX = next(candidate for candidate in REVIEW_CANDIDATES.values() if candidate.route == "codex")


def _reversed() -> dict:
    """Account a: 90% remaining on the lane row and its own row; account b: 0.5% on its row."""
    raw = _agreement_snapshot("healthy", _account_row(B_REMAINING))
    raw["claude_accounts"]["claude:a"] = _account_row(A_REMAINING)
    raw["preferred_claude_account"] = "a"
    raw["ranked_by_headroom"] = [
        {
            "lane": lane,
            "type": "subscription",
            "status": info["status"],
            "burn_pct_7d": info.get("burn_pct_7d"),
            "remaining_pct": info.get("remaining_pct"),
            "resets_at": info.get("resets_at"),
            "in_flight": 0,
            "health": info["health"],
        }
        for lane, info in raw["agents"].items()
    ]
    assert raw["agents"]["claude"]["remaining_pct"] == A_REMAINING
    return raw


# --- the bound view ---------------------------------------------------------------------------


@pytest.mark.parametrize("label", ["a", "b", None])
def test_the_view_holds_only_the_bound_accounts_meter(label):
    raw = _reversed()
    before = copy.deepcopy(raw)
    route_account = unresolved("claude_account_unknown") if label is None else account(label)

    view, evidence = select_account(raw, account=route_account)

    assert isinstance(view, AccountSnapshot) and not isinstance(view, dict)
    assert view.account is route_account and evidence["label"] == label
    assert "preferred_claude_account" not in view
    assert set(view["claude_accounts"]) == ({f"claude:{label}"} if label else set())
    claude = view["agents"]["claude"]
    ranked = {row["lane"]: row for row in view["ranked_by_headroom"]}
    if label == "a":
        assert claude is raw["agents"]["claude"]  # the default account keeps its lane row unchanged
        assert view["ranked_by_headroom"] is raw["ranked_by_headroom"]
    elif label == "b":
        assert claude["remaining_pct"] == pytest.approx(B_REMAINING)
        assert ranked["claude"]["remaining_pct"] == pytest.approx(B_REMAINING)
        assert ranked["claude"]["status"] == claude["status"]
    else:
        assert claude["status"] == "unknown" and "remaining_pct" not in claude
        assert ranked["claude"]["status"] == "unknown" and ranked["claude"]["remaining_pct"] is None
    # Route facts and every other lane are the payload's own.
    assert claude["health"] == raw["agents"]["claude"]["health"]
    assert ranked["claude"]["health"] == raw["ranked_by_headroom"][0]["health"]
    assert view["agents"]["codex"] is raw["agents"]["codex"] and ranked["codex"] is raw["ranked_by_headroom"][1]
    assert {key: view[key] for key in ("diagnostics", "recommendation")} == {
        key: raw[key] for key in ("diagnostics", "recommendation")
    }
    assert raw == before  # the caller's payload is not modified


@pytest.mark.parametrize("route_account", [HOST_ACCOUNT, B, unresolved("claude_account_unknown")])
def test_same_account_reselection_is_a_fixed_point_and_rebinding_is_refused(route_account):
    view, evidence = select_account(_reversed(), account=route_account)

    assert select_account(view, account=route_account) == (view, evidence)
    assert bind_snapshot(view, account=route_account) is view
    same_label = (
        account(route_account.label, "default-file")
        if route_account.resolved
        else unresolved("claude_account_binding_missing")
    )
    assert bind_snapshot(view, account=same_label) is view
    derived = view.evolve(review_capacity_exclusions={})
    assert derived.account is route_account and bind_snapshot(derived, account=route_account) is derived
    for other in (HOST_ACCOUNT, B, unresolved("claude_account_unknown")):
        if other.label != route_account.label:
            with pytest.raises(AccountRequired, match="not read as"):
                bind_snapshot(view, account=other)


def test_the_view_is_immutable_built_only_by_its_owner_and_never_serialized():
    view = bind_snapshot(_reversed(), account=B)
    for attempt in (
        lambda: setattr(view, "_data", {}),
        lambda: delattr(view, "_account"),
        lambda: vars(view),
        lambda: view.__dict__,
        lambda: dict.get(view, "agents"),
        lambda: dict.__getitem__(view, "agents"),
        lambda: json.dumps(view),
        lambda: pickle.dumps(view),
        lambda: copy.copy(view),
        lambda: copy.deepcopy(view),
        lambda: AccountSnapshot({}, B, {}),
    ):
        with pytest.raises((AttributeError, TypeError)):
            attempt()
    with pytest.raises(TypeError, match="a mapping"):
        bind_snapshot(["not", "a", "snapshot"], account=B)  # type: ignore[arg-type]
    # A deserialized payload is bound again; the plain copy carries only b's meter.
    plain = json.loads(json.dumps(dict(view)))
    assert bind_snapshot(plain, account=B)["agents"]["claude"]["remaining_pct"] == pytest.approx(B_REMAINING)


def test_account_required_is_a_contract_failure_no_broad_handler_absorbs():
    assert issubclass(AccountRequired, BaseException)
    assert not issubclass(AccountRequired, Exception)  # so neither ValueError nor Exception handlers catch it

    def swallow() -> None:
        try:
            claude_account_lane.other_lane_record(_reversed(), "claude")
        except Exception:
            pytest.fail("a broad handler absorbed AccountRequired")

    with pytest.raises(AccountRequired):
        swallow()


# --- the reviews' reproducers (review-s2-b7258c53, review-s2-eb22e901), replayed -----------------


def _walrus(snap):
    if (agents := snap["agents"]) is not None:
        return agents["claude"]["remaining_pct"]
    return None


def _passthrough(function):
    return function


@_passthrough
def _decorated(snap):
    return snap["agents"]["claude"]["remaining_pct"]


def _bound_getter(snap):
    read = snap.get
    return read("agents", {})["claude"]["remaining_pct"]


def _rebound_helper(snap):
    pick = _decorated
    pick = operator.itemgetter("agents")  # the helper name rebound to an unchecked reader
    return pick(snap)["claude"]["remaining_pct"]


def _shadowed_isinstance(snap, isinstance=lambda *_a: True):
    return snap["agents"]["claude"]["remaining_pct"] if isinstance(snap, Mapping) else None


def _dynamic_name(snap):
    lane, method = "".join(("cla", "ude")), "".join(("g", "et"))
    return getattr(snap, method)("agents")[lane]["remaining_pct"]


def _eval(snap):
    return eval('snap["agents"]["claude"]["remaining_pct"]', {}, {"snap": snap})


def _vars(snap):
    return vars()["snap"]["agents"]["claude"]["remaining_pct"]


def _dunder_dict(snap):
    holder = type("Holder", (), {})()
    holder.__dict__["snapshot"] = snap
    return holder.__dict__["snapshot"]["agents"]["claude"]["remaining_pct"]


def _vars_of_snapshot(snap):
    return vars(snap)["_data"]["agents"]["claude"]["remaining_pct"]


def _dict_method(snap):
    return dict.get(snap, "agents")["claude"]["remaining_pct"]


def _comprehension(snap):
    return {lane: info for lane, info in snap["agents"].items()}["claude"]["remaining_pct"]


def _copied(snap):
    return copy.copy(snap)["agents"]["claude"]["remaining_pct"]


def _json_round_trip(snap):
    return json.loads(json.dumps(snap))["agents"]["claude"]["remaining_pct"]


def _account_row_of_a(snap):
    return snap["claude_accounts"]["claude:a"]["weekly"]["left_pct"]


def _ranked_row(snap):
    return next(row for row in snap["ranked_by_headroom"] if row["lane"] == "claude")["remaining_pct"]


def _forwarded_route_record(snap):
    return reviewer_scheduler._route_record(CLAUDE, snap)["remaining_pct"]


REPRODUCERS: dict[str, Callable[[Any], Any]] = {
    "walrus": _walrus,
    "decorator": _decorated,
    "bound_getter": _bound_getter,
    "helper_rebinding": _rebound_helper,
    "shadowed_isinstance": _shadowed_isinstance,
    "dynamic_name": _dynamic_name,
    "eval": _eval,
    "vars": _vars,
    "dunder_dict": _dunder_dict,
    "vars_of_snapshot": _vars_of_snapshot,
    "dict_method": _dict_method,
    "comprehension": _comprehension,
    "copy": _copied,
    "json_round_trip": _json_round_trip,
    "claude_accounts_row_of_a": _account_row_of_a,
    "ranked_by_headroom": _ranked_row,
    "route_record_forwarding": _forwarded_route_record,
}


def _outcome(reader: Callable[[Any], Any], snapshot: Any) -> object:
    try:
        return reader(snapshot)
    except (AccountRequired, AttributeError, KeyError, StopIteration, TypeError) as exc:
        return type(exc)


def test_on_the_raw_payload_the_reproducers_read_account_as_meter():
    """What the reviews demonstrated: a raw payload hands account a's 90% to any reader."""
    raw = _reversed()
    escaped = {name: _outcome(reader, raw) for name, reader in REPRODUCERS.items()}
    assert escaped.pop("route_record_forwarding") is AccountRequired  # #10770: the helper now refuses
    assert escaped.pop("vars_of_snapshot") is TypeError  # a dict has no instance namespace
    assert escaped == dict.fromkeys(escaped, A_REMAINING)


def _capture_resolver(monkeypatch) -> list[Any]:
    held: list[Any] = []
    original = reviewer_resolver._evaluate_candidate

    def capture(candidate, inputs, **kwargs):
        held.append(inputs.routing_snapshot)
        return original(candidate, inputs, **kwargs)

    monkeypatch.setattr(reviewer_resolver, "_evaluate_candidate", capture)
    return held


def _held_by_resolver_inputs(raw, monkeypatch, tmp_path, capsys):
    held = _capture_resolver(monkeypatch)
    resolve_reviewer(
        ResolverInputs(author_model="gpt-6.1-sol", risk="critical", routing_snapshot=raw, claude_account=B)
    )
    return held


def _held_by_resolver_runtime_state(raw, monkeypatch, tmp_path, capsys):
    held = _capture_resolver(monkeypatch)
    resolve_reviewer(ResolverInputs(author_model="gpt-6.1-sol", risk="critical", claude_account=B), runtime_state=raw)
    return held


def _held_by_delegate_guard(raw, monkeypatch, tmp_path, capsys):
    held: list[Any] = []
    monkeypatch.setattr(delegate, "_fetch_routing_budget", lambda: raw)
    monkeypatch.setattr(delegate, "_load_reset_reserve", lambda *_a, **_k: {})

    def review_select(snapshot, _seat):
        held.append(snapshot)
        return "claude", None

    delegate._resolve_agent_with_budget_guard("claude", fallbacks={}, review_select=review_select, claude_account=B)
    return held


def _held_by_closeout(source: str):
    def run(raw, monkeypatch, tmp_path, capsys):
        assert _route_key_for(tmp_path, monkeypatch, b"b\n") == account("b", "default-file")
        held = _capture_resolver(monkeypatch)
        argv = ["--state-file", str(tmp_path / "state.json"), "resolve-reviewer", "--author-model", "gpt-6.1-sol"]
        argv += ["--risk", "critical", "--owned-path", "ordinary.py"]
        if source == "file":
            path = tmp_path / "snapshot.json"
            path.write_text(json.dumps(raw))
            argv += ["--routing-snapshot-file", str(path)]
        else:
            monkeypatch.setattr(credit_lane, "read_routing_budget", lambda **_k: raw)
        closeout_cli.main(argv)
        capsys.readouterr()
        return held

    return run


def _held_by_bench(raw, monkeypatch, tmp_path, capsys):
    _route_key_for(tmp_path, monkeypatch, b"b\n")
    held = _capture_resolver(monkeypatch)
    bench_health._bench_inventory(raw, data_egress_policy="local_interactive", review_profile="code", risk="medium")
    return held


def _held_by_target_admission(raw, monkeypatch, tmp_path, capsys):
    held = _capture_resolver(monkeypatch)
    target_admission._resolve_review_target(
        "claude",
        "claude-opus-5-5",
        author_model="gpt-6.1-sol",
        risk="critical",
        profile="code",
        attempt=False,
        snapshot=raw,
        budget_seat="claude",
        owned_paths=("ordinary.py",),
        claude_account=B,
    )
    return held


def _held_by_coordinator(raw, monkeypatch, tmp_path, capsys):
    _route_key_for(tmp_path, monkeypatch, b"b\n")
    held: list[Any] = []
    original = coordinator._health_assessment

    def capture(snapshot, *args, **kwargs):
        held.append(snapshot)
        return original(snapshot, *args, **kwargs)

    monkeypatch.setattr(coordinator, "_health_assessment", capture)
    coordinator._probe_health(lambda: raw, coordinator.load_config())
    return held


def _held_by_model_pause(raw, monkeypatch, tmp_path, capsys):
    held: list[Any] = []
    original = claude_account_lane.account_weekly_used_pct

    def capture(snapshot, **kwargs):
        held.append(snapshot)
        return original(snapshot, **kwargs)

    monkeypatch.setattr(claude_account_lane, "account_weekly_used_pct", capture)
    monkeypatch.setattr(model_pause.urllib.request, "urlopen", lambda *a, **k: io.StringIO(json.dumps(raw)))
    assert model_pause.routing_budget_used_pct("claude", account=B) == pytest.approx(100.0 - B_REMAINING)
    return held


CONSUMERS = {
    "resolver_inputs": _held_by_resolver_inputs,
    "resolver_runtime_state": _held_by_resolver_runtime_state,
    "delegate_budget_guard": _held_by_delegate_guard,
    "closeout_live_fetch": _held_by_closeout("live"),
    "closeout_snapshot_file": _held_by_closeout("file"),
    "bench_health": _held_by_bench,
    "target_admission": _held_by_target_admission,
    "curriculum_coordinator": _held_by_coordinator,
    "model_pause": _held_by_model_pause,
}


@pytest.mark.parametrize("consumer", sorted(CONSUMERS))
def test_every_reproducer_reads_only_the_bound_accounts_meter(consumer, monkeypatch, tmp_path, capsys):
    held = CONSUMERS[consumer](_reversed(), monkeypatch, tmp_path, capsys)

    assert held and all(isinstance(snapshot, AccountSnapshot) and snapshot.account.label == "b" for snapshot in held)
    outcomes = {name: _outcome(reader, held[-1]) for name, reader in REPRODUCERS.items()}
    assert A_REMAINING not in outcomes.values()
    read = {name: value for name, value in outcomes.items() if not isinstance(value, type)}
    assert read == {name: pytest.approx(B_REMAINING) for name in read}
    refused = {name for name, value in outcomes.items() if isinstance(value, type)}
    # What fails closed rather than returning b's meter: no other account's row, no dict, no serialization.
    assert refused == {"claude_accounts_row_of_a", "copy", "dict_method", "json_round_trip", "vars_of_snapshot"}


# --- the scheduler helper refuses an unbound claude read ----------------------------------------


def test_route_record_refuses_an_unbound_claude_read_and_absence_is_not_empty():
    raw = _reversed()
    for snapshot in (raw, {**raw, "agents": {"codex": raw["agents"]["codex"]}}, {"agents": {}}):
        with pytest.raises(AccountRequired, match="reviewer candidate claude-opus-5-5"):
            reviewer_scheduler._route_record(CLAUDE, snapshot)
        with pytest.raises(AccountRequired):
            reviewer_scheduler.metrics_for(CLAUDE, snapshot)
    # Non-claude candidates and flat health maps hold no claude meter: unchanged.
    assert reviewer_scheduler._route_record(CODEX, raw) is raw["agents"]["codex"]
    assert reviewer_scheduler._route_record(CLAUDE, {"claude": "Healthy"}) == {"status": "healthy"}
    assert reviewer_scheduler._route_record(CLAUDE, None) == {}
    # A bound snapshot reads its own account, and its absence reads as absent.
    assert reviewer_scheduler._route_record(CLAUDE, bound(raw, B))["remaining_pct"] == pytest.approx(B_REMAINING)
    assert reviewer_scheduler._route_record(CLAUDE, bound({"agents": {}}, B)) == {}


# --- entry paths ------------------------------------------------------------------------------


def test_resolver_binds_before_normalizing_so_another_accounts_row_cannot_fail_it_closed():
    """Normalization reads every lane; it now reads the bound account's claude record, not account a's."""
    raw = _reversed()
    raw["agents"]["claude"] = {**raw["agents"]["claude"], "status": "not-a-health-status"}

    host = resolve_reviewer(
        ResolverInputs(author_model="gpt-6.1-sol", risk="critical", routing_snapshot=raw, claude_account=HOST_ACCOUNT)
    )
    other = resolve_reviewer(
        ResolverInputs(author_model="gpt-6.1-sol", risk="critical", routing_snapshot=raw, claude_account=B)
    )

    assert host.selected is None and "unsupported health status" in (host.fail_closed_reason or "")
    assert other.fail_closed_reason is None and other.selected is not None


def test_resolver_inputs_bind_on_construction_and_refuse_another_accounts_view():
    raw = _reversed()
    inputs = ResolverInputs(author_model="gpt-6.1-sol", routing_snapshot=raw, claude_account=B)
    assert isinstance(inputs.routing_snapshot, AccountSnapshot) and inputs.routing_snapshot.account is B
    assert reviewer_resolver.replace(inputs, risk="high").routing_snapshot is inputs.routing_snapshot
    flat = ResolverInputs(author_model="gpt-6.1-sol", routing_snapshot={"claude": "healthy"}, claude_account=B)
    assert dict(flat.routing_snapshot or {}) == {"claude": "healthy"}
    with pytest.raises(AccountRequired, match="not read as 'a'"):
        ResolverInputs(author_model="gpt-6.1-sol", routing_snapshot=bound(raw, B), claude_account=HOST_ACCOUNT)
    with pytest.raises(AccountRequired):
        reviewer_resolver.replace(inputs, claude_account=HOST_ACCOUNT)


@pytest.mark.parametrize(("route_account", "seat"), [(HOST_ACCOUNT, "claude"), (B, "codex")])
def test_the_dispatch_guard_judges_the_bound_accounts_meter(monkeypatch, capsys, route_account, seat):
    raw = _reversed()
    monkeypatch.setattr(delegate, "_fetch_routing_budget", lambda: raw)
    monkeypatch.setattr(delegate, "_load_reset_reserve", lambda *_a, **_k: {})
    sink: dict = {}

    chosen = delegate._resolve_agent_with_budget_guard(
        "claude", fallbacks={"claude": "codex"}, diagnostic_sink=sink, claude_account=route_account
    )

    assert chosen == seat
    assert sink["claude_account"]["label"] == route_account.label
    assert "preferred" not in capsys.readouterr().err


def test_model_pause_binds_the_fetched_snapshot_and_lets_account_required_through(monkeypatch):
    raw = _reversed()
    monkeypatch.setattr(model_pause.urllib.request, "urlopen", lambda *a, **k: io.StringIO(json.dumps(raw)))
    assert model_pause.routing_budget_used_pct("claude", account=HOST_ACCOUNT) == pytest.approx(10.0)
    assert model_pause.routing_budget_used_pct("claude", account=B) == pytest.approx(100.0 - B_REMAINING)
    assert model_pause.routing_budget_used_pct("claude", account=None) is None
    assert model_pause.routing_budget_used_pct("codex", account=None) is None  # fixture codex has no fresh used-%

    def contract_failure(*_a, **_k):
        raise AccountRequired("unbound read")

    monkeypatch.setattr(model_pause.urllib.request, "urlopen", contract_failure)
    with pytest.raises(AccountRequired):  # not "unreachable": the (OSError, ValueError, ...) handler lets it through
        model_pause.routing_budget_used_pct("codex", account=B)


def test_credit_lane_reads_credit_lanes_from_a_snapshot_bound_to_no_account(monkeypatch):
    raw = _reversed()
    held: list[Any] = []
    original = claude_account_lane.other_lane_record

    def capture(snapshot, lane):
        held.append(snapshot)
        return original(snapshot, lane)

    monkeypatch.setattr(credit_lane, "read_routing_budget", lambda **_k: raw)
    monkeypatch.setattr(claude_account_lane, "other_lane_record", capture)
    assert credit_lane.dispatch_refusal("codex", "not-on-the-allowlist") is None  # no credit balance in the fixture
    [snapshot] = held
    assert isinstance(snapshot, AccountSnapshot) and not snapshot.account.resolved
    assert snapshot["agents"]["claude"]["status"] == "unknown" and snapshot["claude_accounts"] == {}
    with pytest.raises(AccountRequired, match="named account"):
        original(raw, "claude")


def test_bench_health_binds_injected_and_produced_snapshots(monkeypatch, tmp_path):
    for default_file, claude_eligible in ((None, True), (b"b\n", False)):
        _route_key_for(tmp_path, monkeypatch, default_file)
        eligible, excluded = bench_health._bench_inventory(
            _reversed(), data_egress_policy="local_interactive", review_profile="code", risk="medium"
        )
        # Account a has 90% left and keeps its claude seats; account b has 0.5% and loses them to its own meter.
        assert ("claude-opus-5-5" in eligible["openai"]) is claude_eligible
        if not claude_eligible:
            assert "near cap" in excluded["openai"]["claude-opus-5-5"]

    def contract_failure(**_k):
        raise AccountRequired("unbound read")

    monkeypatch.setattr("scripts.api.state_router.compute_routing_budget", contract_failure)
    with pytest.raises(AccountRequired):  # the producer's ``except Exception`` does not absorb it
        bench_health._bench_inventory(
            None, data_egress_policy="local_interactive", review_profile="code", risk="medium"
        )


def test_the_coordinator_binds_probe_snapshots_and_refuses_unbound_or_rebound_ones(monkeypatch, tmp_path):
    raw = _reversed()
    health = coordinator.load_config()["health"]
    with pytest.raises(AccountRequired, match="wave health gate"):
        coordinator._health_assessment(raw, health)
    _route_key_for(tmp_path, monkeypatch, None)  # the default account
    assert coordinator._probe_health(lambda: raw, coordinator.load_config()) == coordinator._health_assessment(
        bound(raw), health
    )
    with pytest.raises(AccountRequired, match="not read as 'a'"):
        coordinator._probe_health(lambda: bound(raw, B), coordinator.load_config())

    def contract_failure():
        raise AccountRequired("unbound read")

    with pytest.raises(AccountRequired):  # the probe's ``except Exception`` does not absorb it
        coordinator._probe_health(contract_failure, coordinator.load_config())


@pytest.mark.parametrize(("label", "used"), [("a", 10.0), ("b", 100.0 - B_REMAINING)])
def test_the_launcher_reader_keeps_its_explicit_launch_account_selection(label, used):
    raw = _reversed()
    raw["agents"]["claude"]["codexbar"]["stale"] = False
    assert claude_weekly_used._weekly_used_pct(raw, label) == pytest.approx(used)


def test_display_consumers_keep_the_plain_payload(monkeypatch, capsys):
    raw = _reversed()
    monkeypatch.setattr(usage, "read_budget", lambda **_k: raw)
    assert usage.main(["json"]) == 0
    assert json.loads(capsys.readouterr().out) == json.loads(json.dumps(raw))  # every account's row, unchanged
    rows = {row["lane"]: row for row in capacity_pick.build_lane_rows(raw)}
    assert rows["claude"]["remaining_pct"] == A_REMAINING  # the display shows the host lane row as before


# --- source inventory: where a decision module receives a raw routing snapshot -------------------

DECISION_MODULES = (
    "scripts/agent_runtime/model_pause.py",
    "scripts/agent_runtime/target_admission.py",
    "scripts/delegate.py",
    "scripts/fleet/credit_lane.py",
    "scripts/lib/claude_weekly_used.py",
    "scripts/orchestration/curriculum_coordinator.py",
    "scripts/review/bench_health.py",
    "scripts/review/closeout_cli.py",
    "scripts/review/reviewer_resolver.py",
    "scripts/review/reviewer_scheduler.py",
)
FETCHERS = frozenset({"_fetch_routing_budget", "compute_routing_budget", "read_routing_budget"})
BINDERS = frozenset({"bind_snapshot", "select_account", "account_weekly_used_pct"})
# (module, function) -> how the raw snapshot it receives is bound. ``None`` marks a fetch helper
# whose callers are listed here too, or a reader that selects its account itself.
RAW_SNAPSHOT_SOURCES: dict[tuple[str, str], str | None] = {
    ("scripts/delegate.py", "_fetch_routing_budget"): None,
    ("scripts/delegate.py", "_admit_dispatch_target"): "red-team initial snapshot: select_account",
    ("scripts/delegate.py", "_resolve_agent_with_budget_guard"): (
        "select_account as the dispatch's account; the raw payload is bound again only for the "
        "cooler-seat advice, as the account a re-routed claude dispatch would resolve"
    ),
    ("scripts/fleet/credit_lane.py", "read_routing_budget"): None,
    ("scripts/fleet/credit_lane.py", "dispatch_refusal"): "bind_snapshot to no account (credit lanes only)",
    ("scripts/review/closeout_cli.py", "_cmd_resolve_reviewer"): "live fetch or JSON file: select_account",
    ("scripts/agent_runtime/model_pause.py", "routing_budget_used_pct"): "bind_snapshot as the named account",
    ("scripts/review/bench_health.py", "_bench_inventory"): "select_account as a claude review dispatch would run",
    ("scripts/orchestration/curriculum_coordinator.py", "default_health_probe"): "bind_snapshot as the wave's account",
    ("scripts/lib/claude_weekly_used.py", "main"): None,  # isolated launcher reader: explicit launch account
}


def _raw_snapshot_sources(module: str) -> dict[str, set[str]]:
    """``{function: names}`` for every fetch call, constructed routing-budget URL or snapshot-file read."""
    found: dict[str, set[str]] = {}

    def visit(node: ast.AST, scope: str) -> None:
        for child in ast.iter_child_nodes(node):
            inner = child.name if isinstance(child, ast.FunctionDef | ast.AsyncFunctionDef) else scope
            source = None
            if isinstance(child, ast.Call):
                func = child.func
                name = func.id if isinstance(func, ast.Name) else func.attr if isinstance(func, ast.Attribute) else ""
                if name in FETCHERS:
                    source = name
            elif isinstance(child, ast.JoinedStr | ast.BinOp) and "/routing-budget" in ast.unparse(child):
                source = "routing-budget URL"
            elif isinstance(child, ast.Attribute) and child.attr == "routing_snapshot_file":
                source = "routing snapshot file"
            if source:
                found.setdefault(scope, set()).add(source)
            visit(child, inner)

    visit(ast.parse((REPO_ROOT / module).read_text(encoding="utf-8")), "<module>")
    return found


def _binder_calls(module: str) -> dict[str, set[str]]:
    calls: dict[str, set[str]] = {}
    for node in ast.walk(ast.parse((REPO_ROOT / module).read_text(encoding="utf-8"))):
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            names = {
                sub.func.attr if isinstance(sub.func, ast.Attribute) else getattr(sub.func, "id", "")
                for sub in ast.walk(node)
                if isinstance(sub, ast.Call)
            }
            calls[node.name] = names & BINDERS
    return calls


def test_raw_snapshot_sources_in_decision_modules_are_inventoried():
    """A tripwire, not the enforcement: a new raw-snapshot source in a decision module must be listed and bound."""
    found = {
        (module, function): sources
        for module in DECISION_MODULES
        for function, sources in _raw_snapshot_sources(module).items()
    }
    assert set(found) == set(RAW_SNAPSHOT_SOURCES), "list the new source here and bind it where it enters"
    for (module, function), how in RAW_SNAPSHOT_SOURCES.items():
        if how is not None:
            assert _binder_calls(module)[function], f"{module}:{function} receives a raw snapshot but never binds it"
