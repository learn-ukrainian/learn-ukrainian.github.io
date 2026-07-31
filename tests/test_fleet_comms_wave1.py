"""Wave 1 fleet: PR-B1 adapter conformance, PR-C artifacts, PR-D request executor."""

from __future__ import annotations

import hashlib
import json
import sqlite3
import stat
from pathlib import Path

import pytest

from scripts.fleet_comms.adapter_conformance import (
    CaptureInput,
    conform,
    raw_capture_matches,
)
from scripts.fleet_comms.artifacts import ArtifactStore, ArtifactStoreError
from scripts.fleet_comms.contracts import CompletionState
from scripts.fleet_comms.request_executor import RequestExecutor

# ── PR-C: artifact store ────────────────────────────────────────────────────


def test_artifact_store_round_trip_and_dedup(tmp_path: Path) -> None:
    with ArtifactStore(root=tmp_path / "v1") as store:
        a = store.store_text("hello fleet", producer="test", logical_filename="hello.txt")
        assert a.bytes == len(b"hello fleet")
        assert a.sha256 == hashlib.sha256(b"hello fleet").hexdigest()
        assert a.blob_path.is_file()
        assert store.read_bytes(a.artifact_id) == b"hello fleet"
        b = store.store_bytes(b"hello fleet", producer="other")
        assert b.artifact_id == a.artifact_id  # content-addressed reuse
        assert b.sha256 == a.sha256


def test_artifact_store_uses_durable_sqlite_and_private_modes(tmp_path: Path) -> None:
    root = tmp_path / "fresh" / "fleet-comms" / "v1"
    with ArtifactStore(root=root) as store:
        store.store_text("private conversation", producer="test")
        assert store.connection.execute("PRAGMA journal_mode").fetchone()[0] == "wal"
        assert store.connection.execute("PRAGMA synchronous").fetchone()[0] == 2
        assert store.connection.execute("PRAGMA foreign_keys").fetchone()[0] == 1
        assert store.connection.execute("PRAGMA busy_timeout").fetchone()[0] == 5_000
        assert stat.S_IMODE((tmp_path / "fresh").stat().st_mode) == 0o700
        assert stat.S_IMODE((tmp_path / "fresh" / "fleet-comms").stat().st_mode) == 0o700
        assert stat.S_IMODE(root.stat().st_mode) == 0o700
        assert stat.S_IMODE((root / "blobs").stat().st_mode) == 0o700
        assert stat.S_IMODE(store.blob_root.stat().st_mode) == 0o700
        assert stat.S_IMODE(store.db_path.stat().st_mode) == 0o600

        with ArtifactStore(root=root) as reader:
            store.connection.execute("BEGIN IMMEDIATE")
            try:
                assert reader.connection.execute(
                    "SELECT COUNT(*) FROM artifacts"
                ).fetchone()[0] == 1
            finally:
                store.connection.rollback()


def test_artifact_store_wal_setup_retries_fast_lock_failures(monkeypatch) -> None:
    class FakeCursor:
        def fetchone(self):
            return ("wal",)

    class RacingConnection:
        calls = 0

        def execute(self, _statement):
            self.calls += 1
            if self.calls < 3:
                raise sqlite3.OperationalError("database is locked")
            return FakeCursor()

    sleeps: list[float] = []
    connection = RacingConnection()
    store = ArtifactStore.__new__(ArtifactStore)
    store._conn = connection
    monkeypatch.setattr("scripts.fleet_comms.artifacts.time.monotonic", lambda: 0.0)
    monkeypatch.setattr(
        "scripts.fleet_comms.artifacts.time.sleep",
        lambda seconds: sleeps.append(seconds),
    )

    store._enable_wal()

    assert connection.calls == 3
    assert sleeps == [0.05, 0.05]


def test_artifact_store_rejects_traversal_filename(tmp_path: Path) -> None:
    with ArtifactStore(root=tmp_path / "v1") as store:
        with pytest.raises(ArtifactStoreError, match=r"traversal|unsafe"):
            store.store_text("x", producer="t", logical_filename="../etc/passwd")
        with pytest.raises(ArtifactStoreError, match=r"traversal|unsafe"):
            store.store_text("x", producer="t", logical_filename="/abs/name.txt")


def test_artifact_store_deferred_commit_requires_active_transaction(tmp_path: Path) -> None:
    with ArtifactStore(root=tmp_path / "v1") as store:
        persisted = store.store_text("persisted", producer="t")

        with pytest.raises(ArtifactStoreError, match="caller-owned active transaction"):
            store.store_text("uncommitted", producer="t", commit=False)
        with pytest.raises(ArtifactStoreError, match="caller-owned active transaction"):
            store.reference("message-uncommitted", persisted.artifact_id, commit=False)

        store.connection.execute("BEGIN IMMEDIATE")
        try:
            deferred = store.store_text("deferred", producer="t", commit=False)
            store.reference("message-deferred", deferred.artifact_id, commit=False)
            store.connection.commit()
        except Exception:
            store.connection.rollback()
            raise

        assert store.connection.execute(
            "SELECT 1 FROM message_artifacts WHERE message_id = ? AND artifact_id = ?",
            ("message-deferred", deferred.artifact_id),
        ).fetchone() is not None


def test_artifact_reference_default_commit_rolls_back_failed_stub(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    with ArtifactStore(root=tmp_path / "v1") as store:
        persisted = store.store_text("persisted", producer="t")
        original_stub = store._ensure_message_stub

        def fail_after_stub(message_id: str) -> None:
            original_stub(message_id)
            raise sqlite3.IntegrityError("injected link failure")

        monkeypatch.setattr(store, "_ensure_message_stub", fail_after_stub)

        with pytest.raises(sqlite3.IntegrityError):
            store.reference("message-failed", persisted.artifact_id)

        assert store.connection.in_transaction is False
        assert store.connection.execute(
            "SELECT 1 FROM comms_messages WHERE message_id = ?",
            ("message-failed",),
        ).fetchone() is None


def test_artifact_import_materialize_and_gc(tmp_path: Path) -> None:
    src = tmp_path / "src.bin"
    src.write_bytes(b"payload-bytes")
    with ArtifactStore(root=tmp_path / "v1") as store:
        rec = store.import_path(src, producer="import-test")
        scratch = tmp_path / "scratch"
        out = store.materialize(rec.artifact_id, scratch, filename="payload.bin")
        assert out.read_bytes() == b"payload-bytes"
        assert out.stat().st_mode & 0o222 == 0  # readonly

        # Unreferenced + zero grace → GC deletes
        deleted = store.garbage_collect_unreferenced(grace_seconds=0)
        assert rec.artifact_id in deleted
        with pytest.raises(ArtifactStoreError, match="not found"):
            store.get(rec.artifact_id)

        # Re-store and reference → GC spares it
        rec2 = store.store_bytes(b"kept", producer="t")
        store.reference("message_keep_1", rec2.artifact_id)
        deleted2 = store.garbage_collect_unreferenced(grace_seconds=0)
        assert rec2.artifact_id not in deleted2
        assert store.get(rec2.artifact_id).sha256 == hashlib.sha256(b"kept").hexdigest()


def test_artifact_missing_blob_is_integrity_failure(tmp_path: Path) -> None:
    with ArtifactStore(root=tmp_path / "v1") as store:
        rec = store.store_bytes(b"gone", producer="t")
        rec.blob_path.unlink()
        with pytest.raises(ArtifactStoreError, match=r"missing blob|integrity"):
            store.read_bytes(rec.artifact_id)


def test_artifact_import_refuses_symlink(tmp_path: Path) -> None:
    real = tmp_path / "real.txt"
    real.write_text("x", encoding="utf-8")
    link = tmp_path / "link.txt"
    link.symlink_to(real)
    with ArtifactStore(root=tmp_path / "v1") as store:
        with pytest.raises(ArtifactStoreError, match="symlink"):
            store.import_path(link, producer="t")


# ── PR-B1: adapter conformance ──────────────────────────────────────────────


def _codex_complete_jsonl() -> str:
    return "\n".join(
        [
            json.dumps({"type": "agent_message", "text": "part-one "}),
            json.dumps({"type": "agent_message", "text": "part-two"}),
            json.dumps({"type": "task_complete", "reason": "stop"}),
        ]
    )


def test_codex_complete_requires_task_complete_and_keeps_order() -> None:
    raw = _codex_complete_jsonl().encode("utf-8")
    env = conform(
        CaptureInput(adapter="codex", stdout=_codex_complete_jsonl(), returncode=0, raw_bytes=raw)
    )
    assert env.completion_state is CompletionState.COMPLETE
    assert env.terminal_event_observed is True
    assert env.response_text == "part-one part-two"
    assert [s.sequence for s in env.segments] == [0, 1]
    assert raw_capture_matches(env, raw)


def test_codex_exit0_text_without_terminal_is_unknown_not_complete() -> None:
    stdout = json.dumps({"type": "agent_message", "text": "looks done"})
    env = conform(CaptureInput(adapter="codex", stdout=stdout, returncode=0))
    assert env.completion_state is CompletionState.UNKNOWN
    assert env.terminal_event_observed is False
    assert env.is_formal_review_eligible is False


def test_codex_length_limited() -> None:
    stdout = "\n".join(
        [
            json.dumps({"type": "agent_message", "text": "truncated..."}),
            json.dumps({"type": "task_complete", "reason": "length"}),
        ]
    )
    env = conform(CaptureInput(adapter="codex", stdout=stdout, returncode=0))
    assert env.completion_state is CompletionState.LENGTH_LIMITED
    assert "truncated" in env.response_text


def test_codex_nonzero_exit_with_output_is_transport_incomplete() -> None:
    stdout = json.dumps({"type": "agent_message", "text": "partial"})
    env = conform(CaptureInput(adapter="codex", stdout=stdout, returncode=1))
    assert env.completion_state is CompletionState.TRANSPORT_INCOMPLETE
    assert env.response_text == "partial"


def test_claude_result_event_is_complete_multi_segment() -> None:
    lines = [
        json.dumps(
            {
                "type": "assistant",
                "message": {"content": [{"type": "text", "text": "first "}]},
                "session_id": "sess-1",
            }
        ),
        json.dumps(
            {
                "type": "assistant",
                "message": {"content": [{"type": "text", "text": "second"}]},
            }
        ),
        json.dumps({"type": "result", "result": "first second", "subtype": "success"}),
    ]
    stdout = "\n".join(lines)
    raw = stdout.encode("utf-8")
    env = conform(CaptureInput(adapter="claude", stdout=stdout, returncode=0, raw_bytes=raw))
    assert env.completion_state is CompletionState.COMPLETE
    assert env.session_id == "sess-1"
    # ordered segments retained (assistant texts + final result)
    assert env.segments[0].text == "first "
    assert env.segments[1].text == "second"
    assert raw_capture_matches(env, raw)


def test_claude_missing_result_is_unknown() -> None:
    stdout = json.dumps(
        {"type": "assistant", "message": {"content": [{"type": "text", "text": "hi"}]}}
    )
    env = conform(CaptureInput(adapter="claude", stdout=stdout, returncode=0))
    assert env.completion_state is CompletionState.UNKNOWN


def test_agy_result_marker_complete() -> None:
    stdout = "RESULT: hello from agy\nline2"
    env = conform(CaptureInput(adapter="agy", stdout=stdout, returncode=0))
    assert env.completion_state is CompletionState.COMPLETE
    assert "hello from agy" in env.response_text


def test_agy_json_done_event() -> None:
    stdout = "\n".join(
        [
            json.dumps({"type": "assistant", "text": "a"}),
            json.dumps({"type": "done", "result": "a b"}),
        ]
    )
    env = conform(CaptureInput(adapter="agy", stdout=stdout, returncode=0))
    assert env.completion_state is CompletionState.COMPLETE


def test_b2_adapters_plain_text_without_terminal_is_unknown_not_review_eligible() -> None:
    """B2 real conformers still refuse complete on exit 0 + text alone."""
    for name in ("grok", "kimi", "cursor", "hermes", "opencode"):
        env = conform(CaptureInput(adapter=name, stdout="looks fine", returncode=0))
        assert env.completion_state is CompletionState.UNKNOWN
        assert env.is_formal_review_eligible is False


# ── PR-D: request executor ──────────────────────────────────────────────────


def test_request_executor_gemini_retires_to_agy_and_completes(tmp_path: Path) -> None:
    with RequestExecutor(root=tmp_path / "v1") as ex:
        req = ex.create_request(recipient="gemini", body="ping")
        assert req.requested_recipient == "gemini"
        assert req.resolved_recipient == "agy"
        assert req.state == "queued"

        stdout = _codex_complete_jsonl()  # use codex-shaped complete for adapter override
        # Resolve path is agy — feed agy RESULT capture
        done = ex.execute_capture(
            req.request_id,
            adapter="agy",
            stdout="RESULT: pong",
            returncode=0,
        )
        assert done.state == "complete"
        assert done.completion_state == CompletionState.COMPLETE.value
        assert done.envelope is not None
        assert done.envelope.response_text.startswith("pong")
        assert done.raw_capture_artifact_id
        # artifact readable
        body = ex.store.read_bytes(done.raw_capture_artifact_id)
        assert b"pong" in body or b"RESULT" in body


def test_request_executor_unknown_stays_incomplete(tmp_path: Path) -> None:
    with RequestExecutor(root=tmp_path / "v1") as ex:
        req = ex.create_request(recipient="codex", body="x")
        # exit 0 + text, no terminal
        stdout = json.dumps({"type": "agent_message", "text": "not proven"})
        done = ex.execute_capture(req.request_id, adapter="codex", stdout=stdout, returncode=0)
        assert done.state == "incomplete"
        assert done.completion_state == CompletionState.UNKNOWN.value
        assert done.envelope is not None
        assert done.envelope.is_formal_review_eligible is False


def test_request_executor_failed_on_nonzero_empty(tmp_path: Path) -> None:
    with RequestExecutor(root=tmp_path / "v1") as ex:
        req = ex.create_request(recipient="claude", body="x")
        done = ex.execute_capture(req.request_id, adapter="claude", stdout="", returncode=2)
        assert done.state == "failed"
        assert done.completion_state == CompletionState.FAILED.value
