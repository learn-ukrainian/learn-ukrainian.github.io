"""Behaviour of ``resolve_and_admit``: every resolution step runs before the Kimi gate.

A slot holder, compat name, registry successor or quota substitute that
resolves to a Kimi seat is refused with zero effects; non-Kimi resolutions
reach their sinks unchanged.
"""

from __future__ import annotations

import dataclasses
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from scripts.agent_runtime import kimi_admission, target_admission
from scripts.agent_runtime.kimi_admission import ACP_MODE, BRIDGE_MODE, KimiAdmissionRefused
from scripts.agent_runtime.target_admission import (
    AdmittedTarget,
    ReviewAdmissionRefused,
    SubstituteUnavailable,
    require_admitted,
    resolve_and_admit,
)
from scripts.ai_agent_bridge import _channels, _db
from scripts.orchestration import slot_routing

_TOKEN = "KIMI CODING-ONLY"
_KIMI_HOLDERS = ("kimi", "kimicc", "kimi-infra", "acpx-kimi-shadow")


def _fail(*_args, **_kwargs):
    raise AssertionError("an effect ran before the Kimi gate")


def _holder(agent: str | None):
    def resolve(slot: str, **_kwargs: object) -> slot_routing.SlotHolderResult:
        if agent is None:
            return slot_routing.SlotHolderResult(
                has_holder=False, slot=slot, queue_location=f"queue for '{slot}'", reason="no-live-holder"
            )
        return slot_routing.SlotHolderResult(has_holder=True, slot=slot, holder_agent=agent)

    return resolve


@pytest.fixture
def channel_db(tmp_path, monkeypatch):
    db_file = tmp_path / "messages.db"
    monkeypatch.setattr(_channels, "WAKE_ROOT", tmp_path / "wake")
    with (
        patch("scripts.ai_agent_bridge._config.DB_PATH", db_file),
        patch("scripts.ai_agent_bridge._db.DB_PATH", db_file),
    ):
        _db.init_db()
        _channels.create_channel("topic")
        yield tmp_path


# --- the reviewer's reproduction: a slot whose live holder is Kimi -------------------


@pytest.mark.parametrize("holder", _KIMI_HOLDERS)
def test_a_slot_held_by_kimi_is_refused_before_snapshots_broker_inserts_or_wakes(channel_db, monkeypatch, holder):
    monkeypatch.setattr(slot_routing, "resolve_slot_holder", _holder(holder))
    for effect in ("get_db", "fetch_monitor_state", "context_sha256", "_touch_wake_file", "_insert_delivery"):
        monkeypatch.setattr(_channels, effect, _fail)

    # The bridge loads the gate as ``agent_runtime``: its KimiAdmissionRefused is a ValueError of that copy.
    with pytest.raises(ValueError, match=_TOKEN) as refused:
        _channels.post("topic", "user", "Consult on this design.", to_agents=["claude-folk"])

    assert holder in str(refused.value)
    assert not (channel_db / "wake").exists()


def test_a_slot_held_by_a_non_kimi_seat_is_delivered_to_and_woken_at_its_holder(channel_db, monkeypatch):
    monkeypatch.setattr(slot_routing, "resolve_slot_holder", _holder("claude-infra"))

    result = _channels.post(
        "topic", "user", "hello", to_agents=["claude-folk"], to_model="claude-opus-5-5", auto_snapshot=False
    )

    [delivery] = _channels.deliveries_for_message(result["message_id"])
    assert (delivery["to_agent"], delivery["to_model"]) == ("claude-infra", "claude-opus-5-5")
    assert (channel_db / "wake" / "claude-infra").is_file()
    assert result["warnings"] == []


def test_an_explicit_kimi_slot_is_refused_before_the_slot_is_looked_up(channel_db, monkeypatch):
    monkeypatch.setattr(slot_routing, "resolve_slot_holder", _fail)
    with pytest.raises(KimiAdmissionRefused, match=_TOKEN):
        resolve_and_admit(("kimi-infra",), mode=BRIDGE_MODE, slots=_channels.STATIC_VALID_AGENTS)


# --- every resolution step is inside the gate ----------------------------------------


def test_slots_resolve_to_the_live_holder_or_keep_the_identity_with_a_warning(monkeypatch):
    monkeypatch.setattr(slot_routing, "resolve_slot_holder", _holder("claude-infra"))
    (held,) = resolve_and_admit(("claude-folk",), mode=BRIDGE_MODE, slots=_channels.STATIC_VALID_AGENTS)
    assert (held.recipient, held.reason) == ("claude-infra", "slot:claude-folk")

    monkeypatch.setattr(slot_routing, "resolve_slot_holder", _holder(None))
    warnings: list[str] = []
    (unheld,) = resolve_and_admit(
        ("claude-folk",), mode=BRIDGE_MODE, slots=_channels.STATIC_VALID_AGENTS, warnings=warnings
    )
    assert (unheld.recipient, unheld.reason) == ("claude-folk", "explicit")
    assert warnings and "recipient claude slot has no live holder (no-live-holder)" in warnings[0]
    # #9739: the caller's slot string never reaches the log text.
    assert "claude-folk" not in warnings[0]

    (static,) = resolve_and_admit(("claude-infra",), mode=BRIDGE_MODE, slots=_channels.STATIC_VALID_AGENTS)
    assert static.recipient == "claude-infra"


def test_slot_log_label_comes_from_the_seat_list_and_taxonomy_area():
    # #9739: log text names a slot by its static seat prefix and taxonomy area.
    seats = _channels.STATIC_VALID_AGENTS
    assert target_admission._slot_label("grok-infra", seats, "infra") == "grok slot in area 'infra'"
    assert target_admission._slot_label("claude-infra-x", seats) == "claude-infra slot"  # longest prefix
    assert target_admission._slot_label("nobody-infra", seats) == "slot with an unregistered seat prefix"


def test_slot_resolver_failure_warning_omits_the_caller_slot_string(monkeypatch, capsys):
    def boom(_slot: str, **_kwargs: object) -> None:
        raise RuntimeError("resolver down")

    monkeypatch.setattr(slot_routing, "resolve_slot_holder", boom)
    warnings: list[str] = []
    (target,) = resolve_and_admit(
        ("claude-folk",), mode=BRIDGE_MODE, slots=_channels.STATIC_VALID_AGENTS, warnings=warnings
    )
    assert target.recipient == "claude-folk"
    expected = "slot resolver failed for the claude slot (RuntimeError: resolver down) — queued at its identity"
    assert warnings and expected in warnings[0]
    err = capsys.readouterr().err
    assert expected in err
    assert "claude-folk" not in err


def test_compat_names_resolve_to_their_participant_and_unknown_names_fail():
    (target,) = resolve_and_admit(("gemini",), mode=ACP_MODE, compat=True)
    assert (target.recipient, target.reason) == ("agy", "compat:gemini")
    with pytest.raises(ValueError, match="no enabled ACP route"):
        resolve_and_admit(("nobody",), mode=ACP_MODE, compat=True)
    with pytest.raises(KimiAdmissionRefused, match=_TOKEN):
        resolve_and_admit(("kimi",), mode=ACP_MODE, compat=True)


def test_a_quota_substitute_is_admitted_like_any_target(tmp_path):
    config = tmp_path / "fallbacks.yaml"
    config.write_text("dispatch_fallbacks:\n  codex: cursor\n  claude: kimi\n  grok: nobody\n", encoding="utf-8")

    (target,) = resolve_and_admit(
        ("codex",), mode=ACP_MODE, model="gpt-6.1-sol", compat=True, substitute="rate_limited", fallbacks_path=config
    )
    assert (target.recipient, target.model, target.reason) == ("cursor", None, "substitute:codex:rate_limited")
    with pytest.raises(KimiAdmissionRefused, match=_TOKEN):
        resolve_and_admit(("claude",), mode=ACP_MODE, compat=True, substitute="rate_limited", fallbacks_path=config)
    with pytest.raises(SubstituteUnavailable, match="not an enabled ACP ask seat"):
        resolve_and_admit(("grok",), mode=ACP_MODE, compat=True, substitute="rate_limited", fallbacks_path=config)
    with pytest.raises(SubstituteUnavailable, match="has no substitute"):
        resolve_and_admit(("agy",), mode=ACP_MODE, compat=True, substitute="rate_limited", fallbacks_path=config)


def test_a_registry_lookup_runs_inside_the_gate():
    (target,) = resolve_and_admit(("old-seat",), mode=ACP_MODE, resolver=lambda name: "claude")
    assert (target.recipient, target.reason) == ("claude", "registry:old-seat")
    with pytest.raises(KimiAdmissionRefused, match=_TOKEN):
        resolve_and_admit(("old-seat",), mode=ACP_MODE, resolver=lambda name: "kimicc")


def _recording_route(seat: str, model: str | None):
    calls: list[target_admission.RouteRequest] = []

    def route(request: target_admission.RouteRequest) -> tuple[str, str | None, str]:
        calls.append(request)
        return seat, model, "route:budget-guard"

    return route, calls


@pytest.mark.parametrize(
    ("agent", "model"),
    [
        ("codex", "kimi-code/k3"),  # the reviewer's case: a substitute would replace the Kimi model
        ("codex", "k3"),  # a catalog alias of a Kimi model
        ("kimi", None),
        ("gemini", "kimi-code/k3"),  # a retired CLI name with a Kimi model
    ],
)
def test_the_original_request_is_gated_before_the_launch_route_runs(tmp_path, agent, model):
    """An explicitly Kimi request is refused before the route can probe or substitute it away."""
    route, calls = _recording_route("cursor", "grok-4.7")
    config = tmp_path / "fallbacks.yaml"
    config.write_text("dispatch_fallbacks:\n  codex: cursor\n", encoding="utf-8")
    with pytest.raises(KimiAdmissionRefused, match=_TOKEN):
        resolve_and_admit((agent,), model=model, mode="read-only", route=route, fallbacks_path=config)
    assert calls == []


def test_a_launch_route_onto_kimi_is_refused_after_it_resolves():
    route, calls = _recording_route("kimi", "kimi-code/k3")
    with pytest.raises(KimiAdmissionRefused, match=_TOKEN):
        resolve_and_admit(("codex",), model="gpt-6.1-sol", mode="read-only", route=route)
    assert len(calls) == 1


def test_a_launch_route_gets_the_retired_successor_and_the_fallback_table(tmp_path):
    config = tmp_path / "fallbacks.yaml"
    config.write_text("dispatch_fallbacks:\n  codex: cursor\n", encoding="utf-8")
    route, calls = _recording_route("cursor", "grok-4.7")

    (target,) = resolve_and_admit(("gemini",), model="m", mode="read-only", route=route, fallbacks_path=config)
    assert (target.recipient, target.model, target.reason) == ("cursor", "grok-4.7", "route:budget-guard")
    assert calls == [target_admission.RouteRequest("gemini", "m", "agy", {"codex": "cursor"})]
    (target,) = resolve_and_admit(("claude",), mode="read-only", route=lambda request: (request.seat, None, "explicit"))
    assert (target.recipient, target.model, target.reason) == ("claude", None, "explicit")


def test_the_gate_runs_once_when_resolution_adds_no_name(monkeypatch):
    """An unchanged route is not gated a second time, so a Kimi worker's owned tree is read once."""
    reads: list[str] = []

    def trees():
        reads.append("read")
        return [kimi_admission.DirectoryTree(Path(__file__).resolve().parent.parent)]

    (target,) = resolve_and_admit(
        ("kimi",),
        mode="workspace-write",
        paths=["scripts/agent_runtime/runner.py"],
        route=lambda request: (request.seat, request.model, "explicit"),
        trees=trees,
    )
    assert target.recipient == "kimi" and reads == ["read"]


def test_attached_models_and_recipients_are_gated_and_an_explicit_model_wins():
    with pytest.raises(KimiAdmissionRefused, match=_TOKEN):
        resolve_and_admit(("claude",), mode=BRIDGE_MODE, attachments=('{"to_model": "kimi-code/k3"}',))
    with pytest.raises(KimiAdmissionRefused, match=_TOKEN):
        resolve_and_admit(("claude",), mode=BRIDGE_MODE, attachments=({"recipients": ["codex", "kimi"]},))
    (target,) = resolve_and_admit(
        ("claude",), mode=BRIDGE_MODE, model="claude-opus-5-5", attachments=('{"to_model": "kimi-code/k3"}',)
    )
    assert (target.recipient, target.model) == ("claude", "claude-opus-5-5")


def test_a_non_kimi_request_resolves_unchanged():
    targets = resolve_and_admit(("claude", "codex"), mode=BRIDGE_MODE, model="m")
    assert [(t.recipient, t.model, t.reason) for t in targets] == [
        ("claude", "m", "explicit"),
        ("codex", "m", "explicit"),
    ]
    assert resolve_and_admit((), mode=BRIDGE_MODE) == ()


@pytest.mark.parametrize("model", [None, "gemini-3.8-flash-high"])
@pytest.mark.parametrize("risk", [None, "", "invalid"])
@pytest.mark.parametrize("branch_facts", [False, True])
def test_explicit_review_risk_direct_agy_requires_valid_declaration(tmp_path, monkeypatch, model, risk, branch_facts):
    """D1: neither legacy inputs nor complete facts may infer AGY's risk."""
    from scripts.review.record_cf_verdict import collect_branch_review_facts
    from tests.test_authoring_review_feasibility import REPOSITORY, SOL, mini_repo

    facts = None
    if branch_facts:
        repo = mini_repo(tmp_path, monkeypatch)
        repo.commit(SOL, message="review author")
        facts = collect_branch_review_facts(
            repository=REPOSITORY,
            repo_root=repo.root,
            base_tip_sha=repo.sha("origin/main"),
            head_sha=repo.sha("feature"),
            task_root=tmp_path / "tasks",
        )
        assert facts.author_families == frozenset({"openai"})
    with pytest.raises(ReviewAdmissionRefused, match="explicit --review-risk") as refused:
        target_admission._resolve_review_target(
            "agy",
            model,
            author_model=None,
            risk=risk,
            profile="code",
            attempt=False,
            snapshot=None,
            budget_seat="agy",
            facts=facts,
        )
    assert all(value in str(refused.value) for value in ("low", "medium", "high", "critical"))


@pytest.mark.parametrize("stage", ["selection", "budget", "route", "registry"])
def test_explicit_review_risk_selected_agy_cannot_bypass_declaration(monkeypatch, stage):
    """D2: check risk even if an upstream selection unexpectedly returns AGY."""
    selected = ("agy", "gemini-3.8-flash-high")
    calls = []
    if stage in {"selection", "budget"}:

        def select(seat, model, **kwargs):
            calls.append(kwargs["snapshot"])
            # Exercise review_select's safety boundary for both initial and
            # capacity/retained-candidate results, without depending on rankings.
            return selected if stage == "selection" or kwargs["snapshot"] is not None else (seat, model)

        monkeypatch.setattr(target_admission, "_resolve_review_target", select)

    def route(request):
        if stage == "budget":
            return (*request.review_select({"agents": {}}, request.seat), "budget")
        return (*selected, "route")

    with pytest.raises(ReviewAdmissionRefused, match="explicit --review-risk"):
        resolve_and_admit(
            ("codex",),
            model="gpt-6.1-sol",
            mode="read-only",
            review_dispatch=True,
            route=None if stage == "registry" else route,
            resolver=(lambda _seat: "agy") if stage == "registry" else None,
        )
    if stage == "budget":
        assert calls == [None, {"agents": {}}]


@pytest.mark.parametrize("risk", ["low", "medium"])
@pytest.mark.parametrize("path_kind", ["changed", "owned"])
def test_explicit_review_risk_security_floor_excludes_agy(risk, path_kind):
    """D5/D6: declared low risk never bypasses a security floor or attempt identity."""
    paths = {f"review_{path_kind}_paths": ("scripts/delegate.py",)}
    with pytest.raises(ReviewAdmissionRefused, match="REVIEW_ATTEMPT_IDENTITY_REFUSED"):
        resolve_and_admit(
            ("agy",),
            model="gemini-3.8-flash-high",
            mode="read-only",
            review_dispatch=True,
            review_author_model="gpt-6.1-sol",
            review_risk=risk,
            review_attempt=True,
            **paths,
        )


@pytest.mark.parametrize(
    "seat,model,review,profile",
    [
        ("agy", "gemini-3.8-flash-high", True, "ukrainian"),
        ("codex", "gpt-6.1-sol", True, "code"),
        ("claude", "claude-opus-5-5", True, "code"),
        ("agy", "gemini-3.8-flash-high", False, "code"),
    ],
)
def test_explicit_review_risk_other_work_remains_unaffected(seat, model, review, profile):
    """D7: omission stays valid for Ukrainian, non-AGY and ordinary work."""
    (target,) = resolve_and_admit(
        (seat,),
        model=model,
        mode="read-only",
        review_dispatch=review,
        review_profile=profile,
    )
    assert (target.recipient, target.model) == (seat, model)


# --- only resolve_and_admit produces a target ----------------------------------------


def test_an_admitted_target_cannot_be_forged_or_rewritten():
    (target,) = resolve_and_admit(("claude",), mode=BRIDGE_MODE)
    with pytest.raises(TypeError, match="only by resolve_and_admit"):
        AdmittedTarget("kimi", None, "forged")
    with pytest.raises(TypeError, match="only by resolve_and_admit"):
        dataclasses.replace(target, recipient="kimi")
    with pytest.raises(dataclasses.FrozenInstanceError):
        target.recipient = "kimi"  # type: ignore[misc]


def test_sinks_refuse_raw_names():
    assert require_admitted(resolve_and_admit(("claude",), mode=BRIDGE_MODE)[0]).recipient == "claude"
    for raw in ("claude", "kimi", None):
        with pytest.raises(TypeError, match="AdmittedTarget"):
            require_admitted(raw)
    with pytest.raises(TypeError, match="AdmittedTarget"):
        _channels._touch_wake_file("kimi")


def test_a_target_from_either_import_path_is_accepted_by_either_sink_check():
    import agent_runtime.target_admission as bridge_path

    assert bridge_path is not target_admission  # two module copies, one contract
    (target,) = bridge_path.resolve_and_admit(("claude",), mode=BRIDGE_MODE)
    assert target_admission.require_admitted(target) is target


def test_delegate_launches_only_the_admitted_route():
    import delegate

    (target,) = resolve_and_admit(("claude",), mode="read-only", model="claude-opus-5-5")
    assert delegate._worker_route_argv(target) == ["--agent", "claude", "--model", "claude-opus-5-5"]
    with pytest.raises(TypeError, match="AdmittedTarget"):
        delegate._worker_route_argv("kimi")


def test_no_dispatch_fallback_row_maps_onto_a_kimi_seat_or_model():
    """Makes the documented probe-before-final-gate limitation unreachable by data.

    A launch route's budget probe runs before the final gate (see
    ``RouteRequest``), so a fallback onto Kimi would probe once before its
    refusal. No ``dispatch_fallbacks`` destination may therefore be a Kimi
    seat, reach one through its retired successor or ACP route pin, or be
    launched with a Kimi model (a mapped substitution model or its lane
    default).
    """
    import delegate
    from scripts.common.fallback_substitutions import load_dispatch_fallbacks

    fallbacks = load_dispatch_fallbacks(delegate._FALLBACK_SUBS_PATH)
    assert fallbacks, "dispatch_fallbacks did not load; this guard would pass vacuously"
    models = delegate._load_budget_substitution_table()
    onto_kimi = []
    for source, destination in fallbacks.items():
        launch_models = [*models.get(destination, {}).values(), delegate._lane_default_model(destination)]
        if target_admission.stored_kimi_row(destination) or any(
            target_admission.stored_kimi_row(destination, model) for model in launch_models if model
        ):
            onto_kimi.append(f"{source} -> {destination}")
    assert onto_kimi == []


def test_the_fallback_guard_detects_a_kimi_destination():
    """The guard's predicate refuses a Kimi seat, a Kimi model on another seat, and a route pinned to Kimi."""
    assert target_admission.stored_kimi_row("kimi")
    assert target_admission.stored_kimi_row("kimicc")
    assert target_admission.stored_kimi_row("cursor", "kimi-code/k3")
    assert target_admission.stored_kimi_row("cursor", "k3")
    assert not target_admission.stored_kimi_row("cursor", "composer-2.5")


# --- #9739: runtime review admission excludes every branch author ---------------------------------


def test_review_admission_uses_complete_branch_authorship_like_the_recorder(tmp_path, monkeypatch):
    from scripts.agent_runtime.target_admission import ReviewAdmissionRefused
    from scripts.review import record_cf_verdict as recorder
    from tests.test_authoring_review_feasibility import OPUS, REPOSITORY, SOL, mini_repo

    repo = mini_repo(tmp_path, monkeypatch)
    repo.commit(OPUS, message="first author")
    repo.commit(SOL, message="latest author")
    facts = recorder.collect_branch_review_facts(
        repository=REPOSITORY,
        repo_root=repo.root,
        base_tip_sha=repo.sha("origin/main"),
        head_sha=repo.sha("feature"),
        task_root=tmp_path / "tasks",
    )
    trusted = {
        "mode": "read-only",
        "review_dispatch": True,
        "review_author_model": "gpt-6.1-sol",
        "review_risk": "medium",
    }

    # Without the facts, the latest author alone admits an earlier author's family.
    (legacy,) = resolve_and_admit(("claude",), model="claude-opus-5-5", **trusted)
    assert legacy.recipient == "claude"
    with pytest.raises(ReviewAdmissionRefused, match="REVIEW_ROUTE_REFUSED"):
        resolve_and_admit(("claude",), model="claude-opus-5-5", review_facts=facts, **trusted)
    (grok,) = resolve_and_admit(("cursor",), model="grok-4.7-high", review_facts=lambda: facts, **trusted)
    assert (grok.recipient, grok.model) == ("cursor", "grok-4.7-high")

    # The recorder reaches the same verdicts on the same facts.
    recorder._require_qualified_reviewer(
        facts, task={"agent": "cursor", "review_risk": "medium"}, model="grok-4.7", family="xai"
    )
    with pytest.raises(recorder.RecordError, match="not qualified"):
        recorder._require_qualified_reviewer(
            facts, task={"agent": "claude", "review_risk": "medium"}, model="claude-opus-5-5", family="anthropic"
        )
