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

from scripts.agent_runtime import target_admission
from scripts.agent_runtime.kimi_admission import ACP_MODE, BRIDGE_MODE, KimiAdmissionRefused
from scripts.agent_runtime.target_admission import (
    AdmittedTarget,
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
    assert warnings and "has no live holder" in warnings[0]

    (static,) = resolve_and_admit(("claude-infra",), mode=BRIDGE_MODE, slots=_channels.STATIC_VALID_AGENTS)
    assert static.recipient == "claude-infra"


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
