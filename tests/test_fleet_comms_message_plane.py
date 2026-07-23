"""PR-E message-plane: shadow/dual_write, parity, incomplete never replied."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.fleet_comms.contracts import CompletionState
from scripts.fleet_comms.message_plane import (
    MAX_CONTINUATIONS,
    MessagePlane,
    invocation_digest,
    resolve_plane_mode,
)


def test_resolve_plane_mode() -> None:
    assert resolve_plane_mode("off") == "off"
    assert resolve_plane_mode("shadow") == "shadow"
    assert resolve_plane_mode("dual_write") == "dual_write"
    assert resolve_plane_mode("dual-write") == "dual_write"
    with pytest.raises(ValueError):
        resolve_plane_mode("production")


def test_resolve_plane_mode_env_unset_uses_configured_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Gate A: production default is config message_plane.default_mode (shadow)."""
    monkeypatch.delenv("FLEET_COMMS_MESSAGE_PLANE", raising=False)
    # Config on main/this PR pins shadow after parity window + operator finish GO.
    assert resolve_plane_mode(None) == "shadow"
    monkeypatch.setenv("FLEET_COMMS_MESSAGE_PLANE", "off")
    assert resolve_plane_mode(None) == "off"
    monkeypatch.setenv("FLEET_COMMS_MESSAGE_PLANE", "dual_write")
    assert resolve_plane_mode(None) == "dual_write"


def test_invocation_digest_stable_for_fg_bg_parity() -> None:
    a = invocation_digest(recipient="codex", body="hello", model="m", mode="read-only", cwd="/tmp/x")
    b = invocation_digest(recipient="codex", body="hello", model="m", mode="read-only", cwd="/tmp/x")
    c = invocation_digest(recipient="codex", body="hello!", model="m", mode="read-only", cwd="/tmp/x")
    assert a == b
    assert a != c


def test_off_mode_is_noop(tmp_path: Path) -> None:
    with MessagePlane(mode="off", root=tmp_path / "v1") as plane:
        assert plane.open_ask(recipient="codex", body="x") is None
        result = plane.complete_ask("request_missing")
        assert result.request is None
        assert result.projected_legacy_replied is False


def test_shadow_records_incomplete_without_legacy_replied(tmp_path: Path) -> None:
    tele = tmp_path / "tele.jsonl"
    with MessagePlane(mode="shadow", root=tmp_path / "v1", telemetry_path=tele) as plane:
        req = plane.open_ask(
            recipient="codex",
            body="ping",
            legacy_message_id=42,
            task_id="t1",
            model="gpt-test",
        )
        assert req is not None
        assert req.state == "queued"
        # exit 0 + text without terminal → unknown → incomplete
        stdout = json.dumps({"type": "agent_message", "text": "partial"})
        out = plane.complete_ask(
            req.request_id,
            adapter="codex",
            stdout=stdout,
            returncode=0,
            legacy_message_id=42,
        )
        assert out.request is not None
        assert out.request.state == "incomplete"
        assert out.request.completion_state == CompletionState.UNKNOWN.value
        assert out.projected_legacy_replied is False
        assert out.parity is not None
        assert out.parity.parity_ok is True  # no legacy replied status fed
        # reload by id only (background worker contract)
        loaded = plane.load_request(req.request_id)
        assert loaded.request_id == req.request_id

    events = [json.loads(line) for line in tele.read_text(encoding="utf-8").splitlines() if line]
    assert any(e.get("event") == "plane_complete" for e in events)


def test_dual_write_refuses_unproven_replied_projection(tmp_path: Path) -> None:
    projected: list[tuple[int, str]] = []

    def writer(mid: int, rid: str) -> None:
        projected.append((mid, rid))

    with MessagePlane(mode="dual_write", root=tmp_path / "v1") as plane:
        req = plane.open_ask(recipient="codex", body="x", legacy_message_id=7)
        assert req is not None
        stdout = json.dumps({"type": "agent_message", "text": "no terminal"})
        out = plane.complete_ask(
            req.request_id,
            adapter="codex",
            stdout=stdout,
            returncode=0,
            legacy_message_id=7,
            legacy_status_writer=writer,
        )
        assert out.projected_legacy_replied is False
        assert projected == []
        assert plane.may_mark_legacy_replied(req.request_id) is False


def test_dual_write_projects_only_when_complete(tmp_path: Path) -> None:
    projected: list[tuple[int, str]] = []

    def writer(mid: int, rid: str) -> None:
        projected.append((mid, rid))

    complete_stdout = "\n".join(
        [
            json.dumps({"type": "agent_message", "text": "done"}),
            json.dumps({"type": "task_complete", "reason": "stop"}),
        ]
    )
    with MessagePlane(mode="dual_write", root=tmp_path / "v1") as plane:
        req = plane.open_ask(recipient="codex", body="x", legacy_message_id=9)
        assert req is not None
        out = plane.complete_ask(
            req.request_id,
            adapter="codex",
            stdout=complete_stdout,
            returncode=0,
            legacy_message_id=9,
            legacy_status_writer=writer,
        )
        assert out.request is not None
        assert out.request.state == "complete"
        assert out.projected_legacy_replied is True
        assert projected == [(9, req.request_id)]
        assert plane.may_mark_legacy_replied(req.request_id) is True


def test_parity_flags_legacy_replied_when_incomplete(tmp_path: Path) -> None:
    with MessagePlane(mode="shadow", root=tmp_path / "v1") as plane:
        req = plane.open_ask(recipient="codex", body="x")
        assert req is not None
        stdout = json.dumps({"type": "agent_message", "text": "x"})
        plane.complete_ask(req.request_id, adapter="codex", stdout=stdout, returncode=0)
        report = plane.compute_parity(
            req.request_id,
            legacy_message_id=1,
            legacy_status="replied:99",
        )
        assert report.parity_ok is False
        assert "incomplete_classified_as_replied" in report.notes or "unproven_completion_marked_replied" in report.notes


def test_length_limited_increments_continuation_budget(tmp_path: Path) -> None:
    length_stdout = "\n".join(
        [
            json.dumps({"type": "agent_message", "text": "trunc"}),
            json.dumps({"type": "task_complete", "reason": "length"}),
        ]
    )
    with MessagePlane(mode="shadow", root=tmp_path / "v1") as plane:
        req = plane.open_ask(recipient="codex", body="x")
        assert req is not None
        # First capture already completes request to incomplete — continuation
        # bump happens on length_limited envelope.
        out = plane.complete_ask(
            req.request_id,
            adapter="codex",
            stdout=length_stdout,
            returncode=0,
        )
        assert out.request is not None
        assert out.request.completion_state == CompletionState.LENGTH_LIMITED.value
        assert out.continuation_used == 1
        assert out.continuation_used <= MAX_CONTINUATIONS


def test_gemini_opens_as_agy_on_plane(tmp_path: Path) -> None:
    with MessagePlane(mode="shadow", root=tmp_path / "v1") as plane:
        req = plane.open_ask(recipient="gemini", body="hi")
        assert req is not None
        assert req.requested_recipient == "gemini"
        assert req.resolved_recipient == "agy"
