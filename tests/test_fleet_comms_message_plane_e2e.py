"""PR-E message-plane dual_write smoke integration (#5512).

End-to-end stack: real ``ArtifactStore`` + ``RequestExecutor`` + ``MessagePlane``
in dual_write mode, using the complete codex fixture. Proves:

- raw capture is content-addressed in the artifact store
- proven complete may project legacy replied / may_mark_legacy_replied
- exit 0 + text without terminal never becomes replied
- background workers can reload by request_id only and re-check the gate
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from scripts.fleet_comms.artifacts import ArtifactStore
from scripts.fleet_comms.contracts import CompletionState
from scripts.fleet_comms.message_plane import MessagePlane
from scripts.fleet_comms.request_executor import RequestExecutor


def _codex_complete_jsonl() -> str:
    """Canonical complete codex fixture (ordered segments + terminal)."""
    return "\n".join(
        [
            json.dumps({"type": "agent_message", "text": "part-one "}),
            json.dumps({"type": "agent_message", "text": "part-two"}),
            json.dumps({"type": "task_complete", "reason": "stop"}),
        ]
    )


def _codex_missing_terminal_jsonl() -> str:
    return json.dumps({"type": "agent_message", "text": "looks done but no terminal"})


def test_dual_write_e2e_codex_complete_artifact_and_may_mark_legacy_replied(
    tmp_path: Path,
) -> None:
    """Real store + executor + dual_write plane: complete codex → gate open."""
    root = tmp_path / "fleet-comms-v1"
    tele = tmp_path / "plane-parity.jsonl"
    projected: list[tuple[int, str]] = []

    def legacy_writer(message_id: int, request_id: str) -> None:
        projected.append((message_id, request_id))

    store = ArtifactStore(root=root)
    executor = RequestExecutor(store=store)
    try:
        assert store.db_path == root / "comms.sqlite3"
        assert executor.store is store

        with MessagePlane(
            mode="dual_write",
            executor=executor,
            telemetry_path=tele,
        ) as plane:
            assert plane.mode == "dual_write"
            assert plane.may_mark_legacy_replied(None) is False

            req = plane.open_ask(
                recipient="codex",
                body="e2e complete fixture",
                sender="plane-e2e",
                legacy_message_id=5512,
                task_id="5512-plane-e2e",
                model="gpt-test",
                transport_mode="read-only",
                cwd=str(tmp_path),
            )
            assert req is not None
            assert req.state == "queued"
            assert req.requested_recipient == "codex"
            assert req.resolved_recipient == "codex"
            # Gate closed until proven complete capture.
            assert plane.may_mark_legacy_replied(req.request_id) is False

            complete_stdout = _codex_complete_jsonl()
            raw = complete_stdout.encode("utf-8")
            out = plane.complete_ask(
                req.request_id,
                adapter="codex",
                stdout=complete_stdout,
                returncode=0,
                raw_bytes=raw,
                legacy_message_id=5512,
                legacy_status_writer=legacy_writer,
            )

            assert out.request is not None
            assert out.request.state == "complete"
            assert out.request.completion_state == CompletionState.COMPLETE.value
            assert out.request.envelope is not None
            assert out.request.envelope.terminal_event_observed is True
            assert out.request.envelope.response_text == "part-one part-two"
            assert out.request.envelope.is_formal_review_eligible is True
            assert out.projected_legacy_replied is True
            assert projected == [(5512, req.request_id)]
            assert plane.may_mark_legacy_replied(req.request_id) is True

            art_id = out.request.raw_capture_artifact_id
            assert art_id
            blob = store.read_bytes(art_id)
            assert blob == raw
            assert hashlib.sha256(blob).hexdigest() == out.request.envelope.raw_capture_sha256
            rec = store.get(art_id)
            assert rec.producer == "adapter:codex"
            assert rec.retention_class == "raw-capture"
            assert rec.logical_filename == f"{req.request_id}.capture"

            # Background worker contract: reload by request_id only.
            loaded = plane.load_request(req.request_id)
            assert loaded.request_id == req.request_id
            assert loaded.state == "complete"
            assert plane.may_mark_legacy_replied(loaded.request_id) is True

            parity = plane.compute_parity(
                req.request_id,
                legacy_message_id=5512,
                legacy_status=f"replied:{req.request_id}",
            )
            assert parity.parity_ok is True
    finally:
        executor.close()

    events = [json.loads(line) for line in tele.read_text(encoding="utf-8").splitlines() if line]
    assert any(
        e.get("event") == "plane_complete"
        and e.get("projected_legacy_replied") is True
        and e.get("completion_state") == CompletionState.COMPLETE.value
        for e in events
    )


def test_dual_write_e2e_codex_missing_terminal_refuses_may_mark_legacy_replied(
    tmp_path: Path,
) -> None:
    """Exit 0 + text without terminal: artifact stored, gate stays closed."""
    root = tmp_path / "fleet-comms-v1"
    tele = tmp_path / "plane-parity.jsonl"
    projected: list[tuple[int, str]] = []

    def legacy_writer(message_id: int, request_id: str) -> None:
        projected.append((message_id, request_id))

    store = ArtifactStore(root=root)
    executor = RequestExecutor(store=store)
    try:
        with MessagePlane(
            mode="dual_write",
            executor=executor,
            telemetry_path=tele,
        ) as plane:
            req = plane.open_ask(
                recipient="codex",
                body="e2e incomplete fixture",
                legacy_message_id=77,
            )
            assert req is not None

            stdout = _codex_missing_terminal_jsonl()
            out = plane.complete_ask(
                req.request_id,
                adapter="codex",
                stdout=stdout,
                returncode=0,
                legacy_message_id=77,
                legacy_status_writer=legacy_writer,
            )

            assert out.request is not None
            assert out.request.state == "incomplete"
            assert out.request.completion_state == CompletionState.UNKNOWN.value
            assert out.request.envelope is not None
            assert out.request.envelope.terminal_event_observed is False
            assert out.request.envelope.is_formal_review_eligible is False
            assert out.projected_legacy_replied is False
            assert projected == []
            assert plane.may_mark_legacy_replied(req.request_id) is False

            # Capture still durable even when incomplete.
            art_id = out.request.raw_capture_artifact_id
            assert art_id
            assert b"looks done" in store.read_bytes(art_id)

            report = plane.compute_parity(
                req.request_id,
                legacy_message_id=77,
                legacy_status="replied:bogus",
            )
            assert report.parity_ok is False
            assert (
                "incomplete_classified_as_replied" in report.notes
                or "unproven_completion_marked_replied" in report.notes
            )
    finally:
        executor.close()

    events = [json.loads(line) for line in tele.read_text(encoding="utf-8").splitlines() if line]
    assert any(e.get("event") == "plane_refuse_legacy_replied" for e in events)
    assert any(
        e.get("event") == "plane_complete" and e.get("projected_legacy_replied") is False
        for e in events
    )


def test_dual_write_e2e_background_reload_preserves_may_mark_gate(tmp_path: Path) -> None:
    """Second process opens same ArtifactStore root and re-evaluates the gate."""
    root = tmp_path / "fleet-comms-v1"
    request_id: str

    store = ArtifactStore(root=root)
    executor = RequestExecutor(store=store)
    try:
        with MessagePlane(mode="dual_write", executor=executor) as plane:
            req = plane.open_ask(recipient="codex", body="reload me", legacy_message_id=9)
            assert req is not None
            request_id = req.request_id
            out = plane.complete_ask(
                request_id,
                adapter="codex",
                stdout=_codex_complete_jsonl(),
                returncode=0,
                legacy_message_id=9,
                legacy_status_writer=lambda _mid, _rid: None,
            )
            assert out.projected_legacy_replied is True
            assert plane.may_mark_legacy_replied(request_id) is True
    finally:
        executor.close()

    # New connections against the same durable root (background worker).
    store2 = ArtifactStore(root=root)
    executor2 = RequestExecutor(store=store2)
    try:
        with MessagePlane(mode="dual_write", executor=executor2) as plane2:
            reloaded = plane2.load_request(request_id)
            assert reloaded.state == "complete"
            assert reloaded.completion_state == CompletionState.COMPLETE.value
            assert plane2.may_mark_legacy_replied(request_id) is True
            art_id = reloaded.raw_capture_artifact_id
            # get_request alone does not hydrate artifact id on the record;
            # durable linkage lives in invocation_spec / artifact store refs.
            row = store2.connection.execute(
                "SELECT invocation_spec_json FROM requests WHERE request_id = ?",
                (request_id,),
            ).fetchone()
            assert row is not None
            spec = json.loads(str(row[0]))
            assert "raw_capture_artifact_id" in spec
            assert store2.read_bytes(spec["raw_capture_artifact_id"])
            if art_id:
                assert store2.read_bytes(art_id)
    finally:
        executor2.close()
