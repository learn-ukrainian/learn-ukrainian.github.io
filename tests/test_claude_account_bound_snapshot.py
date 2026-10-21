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

import copy
import io
import json
import marshal
import operator
import pickle
from collections.abc import Callable, Mapping
from datetime import UTC, datetime
from typing import Any

import pytest

from scripts import delegate
from scripts.agent_runtime import model_pause, target_admission
from scripts.fleet import claude_account_lane, credit_lane
from scripts.fleet.claude_account_lane import AccountRequired, AccountSnapshot, bind_snapshot, select_account
from scripts.orchestration import curriculum_coordinator as coordinator
from scripts.review import bench_health, closeout_cli, reviewer_resolver, reviewer_scheduler
from scripts.review.reviewer_resolver import REVIEW_CANDIDATES, ResolverInputs, resolve_reviewer
from tests.claude_route_accounts import HOST_ACCOUNT, account, bound, unresolved
from tests.test_claude_account_route_key import _agreement_snapshot, _route_key_for
from tests.test_delegate_check_budget import _account_row

B = account("b")
A_REMAINING, B_REMAINING = 90.0, 0.5
CLAUDE = REVIEW_CANDIDATES["claude-opus-5-5"]
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
    # The view holds frozen copies (deeply immutable), so "unchanged" is equality, not identity.
    if label == "a":
        assert claude == raw["agents"]["claude"]  # the default account keeps its lane row unchanged
        assert view["ranked_by_headroom"] == raw["ranked_by_headroom"]
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
    assert view["agents"]["codex"] == raw["agents"]["codex"] and ranked["codex"] == raw["ranked_by_headroom"][1]
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


# --- round 2 (review-s2b-adbd73eb): derivation, conversion and alias bypasses ---------------------


def _claude_selected(snapshot: Any, route_account: Any) -> bool:
    """Whether the resolver selects a claude reviewer for a GPT author at critical risk on ``snapshot``."""
    result = resolve_reviewer(
        ResolverInputs(
            author_model="gpt-6.1-sol", risk="critical", routing_snapshot=snapshot, claude_account=route_account
        )
    )
    return result.selected is not None and result.selected.route == "claude"


def _a_exhausted_b_healthy() -> dict:
    """The mirror of :func:`_reversed`: account a near cap on its lane row, account b with 89% left."""
    raw = _agreement_snapshot("near_cap", _account_row(89.0))
    raw["claude_accounts"]["claude:a"] = _account_row(0.5)
    return raw


def test_a_derived_view_cannot_carry_another_accounts_meter():
    """Blocker 1: ``evolve`` may not replace b's meter with the raw payload's (account a's) meter."""
    raw = _reversed()
    b = bind_snapshot(raw, account=B)
    assert not _claude_selected(b, B)  # b has 0.5% left: no claude reviewer
    derivations = {
        "agents": lambda: b.evolve(agents=raw["agents"]),
        "alias_record": lambda: b.evolve(agents={**b["agents"], "claude-opus-5-5": raw["agents"]["claude"]}),
        "claude_accounts": lambda: b.evolve(claude_accounts=raw["claude_accounts"]),
        "ranked_by_headroom": lambda: b.evolve(ranked_by_headroom=raw["ranked_by_headroom"]),
        "preferred_claude_account": lambda: b.evolve(preferred_claude_account="a"),
        "dropped_meter": lambda: b.evolve(agents={"codex": raw["agents"]["codex"]}),
    }
    for name, derive in derivations.items():
        with pytest.raises(AccountRequired, match="may not change its claude meter"):
            contaminated = derive()
            # Reached only where the derivation is accepted (adbd73eb98): a's 90% then selects a claude seat.
            assert not _claude_selected(contaminated, B), name
    # Nor may a derivation carry values taken from another account's view, which would relabel them as b's.
    with pytest.raises(AccountRequired, match="taken from a snapshot bound to claude account 'a'"):
        b.evolve(stash=bind_snapshot(raw, account=HOST_ACCOUNT)["agents"])
    # A decision's derived view that keeps the meter is still allowed, bound to the same account.
    derived = b.evolve(agents=dict(b["agents"].items()), review_capacity_exclusions={"x": "y"})
    assert derived.account is B and derived["agents"]["claude"] == b["agents"]["claude"]
    assert derived["review_capacity_exclusions"] == {"x": "y"} and not _claude_selected(derived, B)


def _assign_lane(view, raw):
    view["agents"]["claude"] = raw["agents"]["claude"]


def _assign_meter(view, raw):
    view["agents"]["claude"]["remaining_pct"] = A_REMAINING


def _assign_codexbar(view, raw):
    view["agents"]["claude"]["codexbar"]["weekly_remaining_pct"] = A_REMAINING


def _update_agents(view, raw):
    view["agents"].update(claude=raw["agents"]["claude"])


def _merge_agents(view, raw):
    agents = view["agents"]
    agents |= {"claude": raw["agents"]["claude"]}


def _setdefault_alias(view, raw):
    view["agents"].setdefault("claude-opus-5-5", raw["agents"]["claude"])


def _pop_lane(view, raw):
    view["agents"].pop("claude")


def _delete_lane(view, raw):
    del view["agents"]["claude"]


def _clear_agents(view, raw):
    view["agents"].clear()


def _add_account_row(view, raw):
    view["claude_accounts"]["claude:a"] = raw["claude_accounts"]["claude:a"]


def _append_ranked(view, raw):
    view["ranked_by_headroom"].append(raw["ranked_by_headroom"][0])


def _replace_ranked(view, raw):
    view["ranked_by_headroom"][0] = raw["ranked_by_headroom"][0]


def _extend_ranked(view, raw):
    rows = view["ranked_by_headroom"]
    rows += [raw["ranked_by_headroom"][0]]


def _assign_ranked_meter(view, raw):
    view["ranked_by_headroom"][0]["remaining_pct"] = A_REMAINING


NESTED_MUTATIONS = (
    _assign_lane,
    _assign_meter,
    _assign_codexbar,
    _update_agents,
    _merge_agents,
    _setdefault_alias,
    _pop_lane,
    _delete_lane,
    _clear_agents,
    _add_account_row,
    _append_ranked,
    _replace_ranked,
    _extend_ranked,
    _assign_ranked_meter,
)


@pytest.mark.parametrize("mutate", NESTED_MUTATIONS, ids=lambda mutate: mutate.__name__.lstrip("_"))
def test_a_bound_view_is_deeply_immutable(mutate):
    """Blocker 1: ``b["agents"]["claude"] = raw["agents"]["claude"]`` (and every other nested write) is refused."""
    raw = _reversed()
    b = bind_snapshot(raw, account=B)
    with pytest.raises(TypeError, match="immutable"):
        mutate(b, raw)
    assert b["agents"]["claude"]["remaining_pct"] == pytest.approx(B_REMAINING)
    assert set(b["claude_accounts"]) == {"claude:b"} and not _claude_selected(b, B)
    # A copy is a plain, mutable dict; writing it never reaches the view.
    copied = dict(b["agents"])
    copied["claude"] = raw["agents"]["claude"]
    assert b["agents"]["claude"]["remaining_pct"] == pytest.approx(B_REMAINING)


def test_trusting_a_bound_view_verifies_its_meter_not_its_label():
    """An existing view is trusted only when its meter seal verifies, never by its label alone."""
    raw = _reversed()
    b = bind_snapshot(raw, account=B)
    # An unbound C-level write the frozen type cannot intercept, then a relabelled view.
    dict.__setitem__(b["agents"], "claude", raw["agents"]["claude"])
    for trust in (
        lambda: bind_snapshot(b, account=B),
        lambda: ResolverInputs(author_model="gpt-6.1-sol", routing_snapshot=b, claude_account=B),
        lambda: reviewer_scheduler.metrics_for(CLAUDE, b),
    ):
        with pytest.raises(AccountRequired, match="does not verify"):
            trust()
    relabelled = bind_snapshot(raw, account=B)
    object.__setattr__(relabelled, "_account", HOST_ACCOUNT)
    with pytest.raises(AccountRequired, match="does not verify"):
        bind_snapshot(relabelled, account=HOST_ACCOUNT)


def _plain_copy(view):
    return dict(view)


def _unpacked(view):
    return {**view}


def _json_copy(view):
    return json.loads(json.dumps(dict(view)))


def _without_binding(view):
    return {key: value for key, value in view.items() if key != getattr(claude_account_lane, "BINDING_KEY", None)}


def _spliced_lane(view):
    raw = _a_exhausted_b_healthy()
    return {**raw, "agents": {**raw["agents"], "claude": view["agents"]["claude"]}}


def _spliced_agents(view):
    return {**_a_exhausted_b_healthy(), "agents": view["agents"]}


CONVERSIONS = (_plain_copy, _unpacked, _json_copy, _without_binding, _spliced_lane, _spliced_agents)


@pytest.mark.parametrize("convert", CONVERSIONS, ids=lambda convert: convert.__name__.lstrip("_"))
def test_a_plain_copy_of_a_bound_view_is_never_bound_as_another_account(convert):
    """Blocker 2: ``bind_snapshot(dict(b), account=a)`` relabelled b's meter as a; it is refused now."""
    raw = _a_exhausted_b_healthy()
    assert not _claude_selected(raw, HOST_ACCOUNT)  # account a is near cap: no claude reviewer for a
    b = bind_snapshot(raw, account=B)
    assert _claude_selected(b, B)  # b has 89% left
    converted = convert(b)
    with pytest.raises(AccountRequired, match="not read as 'a'"):
        relabelled = bind_snapshot(converted, account=HOST_ACCOUNT)
        # Reached only where the copy is accepted (adbd73eb98): b's 89% selects a claude seat for account a.
        assert not _claude_selected(relabelled, HOST_ACCOUNT)
    with pytest.raises(AccountRequired, match="not read as 'a'"):
        ResolverInputs(author_model="gpt-6.1-sol", routing_snapshot=converted, claude_account=HOST_ACCOUNT)


def test_a_plain_copy_is_bound_again_only_as_its_own_account_and_only_unaltered():
    raw = _reversed()
    b = bind_snapshot(raw, account=B)
    for copy_of_b in (dict(b), {**b}, json.loads(json.dumps(dict(b)))):
        again = bind_snapshot(copy_of_b, account=B)
        assert again == b and again.account is B
        assert select_account(copy_of_b, account=B)[1] == select_account(b, account=B)[1]
    # A top-level field that is no meter may change; the meter may not.
    assert bind_snapshot({**b, "review_capacity_exclusions": {}}, account=B)["review_capacity_exclusions"] == {}
    altered = json.loads(json.dumps(dict(b)))
    altered["agents"]["claude"] = raw["agents"]["claude"]
    for tampered in (altered, {**b, "claude_accounts": {"claude:b": raw["claude_accounts"]["claude:a"]}}):
        with pytest.raises(AccountRequired, match="does not verify"):
            bind_snapshot(tampered, account=B)
    forged = {**raw, claude_account_lane.BINDING_KEY: {"label": "a", "evidence": {}, "seal": "0" * 64}}
    with pytest.raises(AccountRequired, match="does not verify"):
        bind_snapshot(forged, account=HOST_ACCOUNT)


# --- round 3 (review-s2b-b105f5d6): derivation from an invalid view, nested serialization -----------


def _lane_written(view, raw):
    dict.__setitem__(view["agents"], "claude", raw["agents"]["claude"])


def _relabelled(view, raw):
    object.__setattr__(view, "_account", HOST_ACCOUNT)


INVALIDATIONS = (_lane_written, _relabelled)


@pytest.mark.parametrize("invalidate", INVALIDATIONS, ids=lambda invalidate: invalidate.__name__.lstrip("_"))
def test_a_view_is_derived_only_from_a_snapshot_that_verifies(invalidate):
    """Blocker 1: ``evolve`` resealed an altered meter or label as the view's account; it now verifies first."""
    a_raw = _reversed()  # a's lane row has 90% left, b's row 0.5%
    view = bind_snapshot(a_raw if invalidate is _lane_written else _a_exhausted_b_healthy(), account=B)
    invalidate(view, a_raw)
    with pytest.raises(AccountRequired, match="does not verify"):
        derived = view.evolve(review_capacity_exclusions={})
        # Reached only where the derivation is accepted (b105f5d62e): the resealed view selects a claude seat on
        # a meter that is not its account's (a's 90% read as b's, or b's 89% read as the exhausted account a's).
        assert not _claude_selected(derived, derived.account), invalidate.__name__


def _pickled(value):
    return pickle.loads(pickle.dumps(value))


SPLICES = {
    "agents": lambda b, raw: {"agents": _pickled(b["agents"])},
    "lane_record": lambda b, raw: {**raw, "agents": {**raw["agents"], "claude": _pickled(b["agents"]["claude"])}},
}


@pytest.mark.parametrize("splice", SPLICES.values(), ids=SPLICES)
def test_a_value_taken_from_a_bound_view_is_never_pickled(splice):
    """Blocker 2: a pickled ``b["agents"]`` came back as a plain dict that bound b's meter as account a's."""
    raw = _a_exhausted_b_healthy()
    assert not _claude_selected(raw, HOST_ACCOUNT)  # account a is near cap: no claude reviewer for a
    b = bind_snapshot(raw, account=B)
    with pytest.raises(TypeError, match="never pickled"):
        relabelled = bind_snapshot(splice(b, raw), account=HOST_ACCOUNT)
        # Reached only where pickling strips the account (b105f5d62e): b's 89% selects a claude seat for account a.
        assert not _claude_selected(relabelled, HOST_ACCOUNT)
    view = bind_snapshot({**_reversed(), "lanes": ["claude", "codex"]}, account=B)
    for part in (
        view["ranked_by_headroom"],
        view["lanes"],
        view["claude_accounts"],
        view["agents"]["claude"],
        dict(view),
    ):
        with pytest.raises(TypeError, match="never pickled"):
            pickle.dumps(part)


# --- round 4 (review-s2b-684f5fa8): plain-data copies of any part of a bound view --------------------


def _plain(value):
    """``value`` as built-in data, as a recursive ``dict``/``list`` conversion copies it."""
    if isinstance(value, Mapping):
        return {key: _plain(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_plain(item) for item in value]
    return value


def _json(value):
    return json.loads(json.dumps(value))


def _lane_spliced(raw, record):
    return {**raw, "agents": {**raw["agents"], "claude": record}}


PART_COPIES = {
    "json_agents": lambda b, raw: {"agents": _json(b["agents"])},
    "json_lane_record": lambda b, raw: _lane_spliced(raw, _json(b["agents"]["claude"])),
    "dict_agents": lambda b, raw: {"agents": _plain(b["agents"])},
    "dict_lane_record": lambda b, raw: _lane_spliced(raw, _plain(b["agents"]["claude"])),
    "marshal_agents": lambda b, raw: {"agents": marshal.loads(marshal.dumps(_plain(b["agents"])))},
    "marshal_lane_record": lambda b, raw: _lane_spliced(
        raw, marshal.loads(marshal.dumps(_plain(b["agents"]["claude"])))
    ),
    "deepcopy_then_json_agents": lambda b, raw: {"agents": _json(copy.deepcopy(b["agents"]))},
}


@pytest.mark.parametrize("part_copy", PART_COPIES.values(), ids=PART_COPIES)
def test_a_plain_data_copy_of_any_part_of_a_bound_view_keeps_its_account(part_copy):
    """Blocker: ``json.loads(json.dumps(b["agents"]))`` bound as account a read b's meter as a's; it is refused now."""
    raw = _a_exhausted_b_healthy()
    assert not _claude_selected(raw, HOST_ACCOUNT)  # account a is near cap: no claude reviewer for a
    b = bind_snapshot(raw, account=B)
    copied = part_copy(b, raw)
    with pytest.raises(AccountRequired, match="stamped for claude account 'b' and is not read as 'a'"):
        relabelled = bind_snapshot(copied, account=HOST_ACCOUNT)
        # Reached only where the copy is accepted (684f5fa86d): b's 89% selects a claude seat for account a.
        assert not _claude_selected(relabelled, HOST_ACCOUNT)
    with pytest.raises(AccountRequired, match="not read as 'a'"):
        ResolverInputs(author_model="gpt-6.1-sol", routing_snapshot=copied, claude_account=HOST_ACCOUNT)
    # Bound again as its own account, the copy is accepted and b reads its own meter.
    assert bind_snapshot(copied, account=B).account is B


def test_every_claude_meter_record_of_another_accounts_view_is_stamped_and_the_hosts_never():
    stamp = claude_account_lane.STAMP_KEY
    raw = _reversed()
    host = bind_snapshot(raw, account=HOST_ACCOUNT)
    assert stamp not in host["agents"]["claude"] and all(stamp not in row for row in host["ranked_by_headroom"])
    for route_account in (B, unresolved("claude_account_unknown")):
        view = bind_snapshot(raw, account=route_account)
        record = view["agents"]["claude"]
        claude_rows = [row for row in view["ranked_by_headroom"] if row["lane"] == "claude"]
        assert record[stamp]["label"] == route_account.label
        assert claude_rows and all(row[stamp]["label"] == route_account.label for row in claude_rows)
        assert all(stamp not in row for row in view["ranked_by_headroom"] if row["lane"] != "claude")
        # A reader takes fields by name, so the stamp changes no reading.
        unstamped = {key: value for key, value in record.items() if key != stamp}
        now = datetime.now(UTC)
        readings = [credit_lane.routing_facts("claude", lane, model=None, now=now) for lane in (record, unstamped)]
        assert readings[0].summary() == readings[1].summary()
        # Any copied part of the view, a ranked row included, is refused as the host account's.
        for part in (
            {"agents": _json(view["agents"])},
            {**raw, "ranked_by_headroom": _json(view["ranked_by_headroom"])},
        ):
            with pytest.raises(AccountRequired, match=f"stamped for claude account {route_account.label!r}"):
                bind_snapshot(part, account=HOST_ACCOUNT)
    unresolved_part = {"agents": _json(bind_snapshot(raw, account=unresolved("claude_account_unknown"))["agents"])}
    with pytest.raises(AccountRequired, match="stamped for claude account None and is not read as 'b'"):
        bind_snapshot(unresolved_part, account=B)


def _altered_meter(record):
    record["remaining_pct"] = A_REMAINING


def _relabelled_stamp(record):
    record[claude_account_lane.STAMP_KEY]["label"] = "a"


def _dropped_seal(record):
    del record[claude_account_lane.STAMP_KEY]["seal"]


def _non_ascii_seal(record):
    record[claude_account_lane.STAMP_KEY]["seal"] = "é" * 64


STAMP_TAMPERING = (_altered_meter, _relabelled_stamp, _dropped_seal, _non_ascii_seal)


@pytest.mark.parametrize("tamper", STAMP_TAMPERING, ids=lambda tamper: tamper.__name__.lstrip("_"))
def test_a_stamped_record_whose_stamp_does_not_verify_is_refused_for_every_account(tamper):
    raw = _a_exhausted_b_healthy()
    record = _json(bind_snapshot(raw, account=B)["agents"]["claude"])
    tamper(record)
    for route_account in (HOST_ACCOUNT, B, unresolved("claude_account_unknown")):
        with pytest.raises(AccountRequired, match="whose stamp does not verify"):
            bind_snapshot(_lane_spliced(raw, record), account=route_account)


@pytest.mark.parametrize("label", ["a", "b"])
def test_claude_alias_records_are_the_host_accounts_and_never_reach_another_accounts_decision(label):
    """Blocker 3: an alias-keyed copy of account a's lane row reached b's scheduler metrics; b's view drops it.

    An alias names no account, so it is the host account's meter, as the lane
    row is: account a keeps it as on main (``test_review_capacity_rule``), and
    a ``claude:<account>`` key naming another account is dropped everywhere.
    """
    raw = _reversed()
    raw["claude_accounts"]["claude:b"] = _account_row(80.0)
    aliases = ("claude-opus-5-5", "claude:a", "Claude", "anthropic")
    for alias in (*aliases, "claude:b"):
        raw["agents"][alias] = raw["agents"]["claude"]  # account a's 90%
    raw["ranked_by_headroom"].append({**raw["ranked_by_headroom"][0], "lane": "claude-opus-5-5"})
    view = bind_snapshot(raw, account=account(label))

    expected = A_REMAINING if label == "a" else 80.0
    assert reviewer_scheduler.metrics_for(CLAUDE, view).quota_remaining_pct == pytest.approx(expected)
    assert reviewer_scheduler._route_record(CLAUDE, view, prefer_route=True)["remaining_pct"] == pytest.approx(expected)
    kept = set(aliases) if label == "a" else set()
    assert set(view["agents"]) == {"claude", "codex", "grok", "cursor"} | kept
    ranked_aliases = [row["lane"] for row in view["ranked_by_headroom"]].count("claude-opus-5-5")
    assert ranked_aliases == (1 if label == "a" else 0)
