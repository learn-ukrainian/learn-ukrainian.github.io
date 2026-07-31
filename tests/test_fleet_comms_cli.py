"""Unit tests for thin fleet-comms CLI (plane-status + formal-job get)."""

from __future__ import annotations

import io
import json
import os
import sqlite3
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts.fleet_comms.cli import (
    EXIT_ERROR,
    EXIT_NOT_FOUND,
    EXIT_OK,
    FleetCommsCliError,
    get_formal_review_job,
    main,
)
from scripts.fleet_comms.migrations import apply_migrations


def _seed_plane_db(root: Path) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    db_path = root / "comms.sqlite3"
    conn = sqlite3.connect(str(db_path))
    try:
        assert apply_migrations(conn) == 3
        conn.execute(
            """INSERT INTO formal_review_jobs(
                review_id, repository, pr_number, head_sha, gate_kind,
                state, snapshot_artifact_id, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                "rev-abc",
                "learn-ukrainian/learn-ukrainian.github.io",
                5512,
                "deadbeefcafebabe0123456789abcdef01234567",
                "cross-family-review",
                "open",
                None,
                "2026-07-20T12:00:00Z",
            ),
        )
        conn.execute(
            """INSERT INTO formal_review_attempts(
                review_attempt_id, review_id, attempt_number,
                completion_state, raw_capture_artifact_id, created_at
            ) VALUES (?, ?, ?, ?, ?, ?)""",
            (
                "att-1",
                "rev-abc",
                1,
                "incomplete",
                None,
                "2026-07-20T12:01:00Z",
            ),
        )
        conn.commit()
    finally:
        conn.close()
    return db_path


def test_plane_status_cli_json(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys) -> None:
    monkeypatch.setenv("FLEET_COMMS_MESSAGE_PLANE", "shadow")
    monkeypatch.setenv("FLEET_COMMS_ROOT", str(tmp_path / "plane"))
    tele = tmp_path / "tele.jsonl"
    tele.write_text(
        json.dumps({"event": "plane_complete", "parity_ok": True}) + "\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("FLEET_COMMS_PLANE_TELEMETRY", str(tele))

    rc = main(["plane-status"])
    assert rc == EXIT_OK
    out = capsys.readouterr().out
    data = json.loads(out)
    assert data["mode"] == "shadow"
    assert data["enabled"] is True
    assert data["read_only"] is True
    assert data["plane_root"] == str(tmp_path / "plane")
    assert data["parity_telemetry"]["event_count"] == 1


def test_plane_status_cli_root_flag(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys) -> None:
    monkeypatch.delenv("FLEET_COMMS_MESSAGE_PLANE", raising=False)
    monkeypatch.delenv("FLEET_COMMS_ROOT", raising=False)
    root = tmp_path / "custom-root"
    root.mkdir()
    rc = main(["plane-status", "--root", str(root)])
    assert rc == EXIT_OK
    data = json.loads(capsys.readouterr().out)
    # Config default is shadow; --root only redirects storage, not mode.
    assert data["mode"] == "shadow"
    assert data["plane_root"] == str(root)


def test_get_formal_review_job_helper(tmp_path: Path) -> None:
    root = tmp_path / "plane"
    _seed_plane_db(root)
    job = get_formal_review_job("rev-abc", root=root)
    assert job["review_id"] == "rev-abc"
    assert job["pr_number"] == 5512
    assert job["gate_kind"] == "cross-family-review"
    assert len(job["attempts"]) == 1
    assert job["attempts"][0]["review_attempt_id"] == "att-1"


def test_formal_job_get_cli(tmp_path: Path, capsys) -> None:
    root = tmp_path / "plane"
    _seed_plane_db(root)
    rc = main(["formal-job", "get", "rev-abc", "--root", str(root)])
    assert rc == EXIT_OK
    data = json.loads(capsys.readouterr().out)
    assert data["review_id"] == "rev-abc"
    assert data["repository"] == "learn-ukrainian/learn-ukrainian.github.io"
    assert data["attempts"][0]["completion_state"] == "incomplete"


def test_formal_job_get_no_attempts(tmp_path: Path, capsys) -> None:
    root = tmp_path / "plane"
    _seed_plane_db(root)
    rc = main(["formal-job", "get", "rev-abc", "--root", str(root), "--no-attempts"])
    assert rc == EXIT_OK
    data = json.loads(capsys.readouterr().out)
    assert data["attempts"] == []


def test_formal_job_get_not_found(tmp_path: Path, capsys) -> None:
    root = tmp_path / "plane"
    _seed_plane_db(root)
    rc = main(["formal-job", "get", "missing", "--root", str(root)])
    assert rc == EXIT_NOT_FOUND
    err = capsys.readouterr().err
    assert "not found" in err


def test_formal_job_get_missing_db(tmp_path: Path, capsys) -> None:
    rc = main(["formal-job", "get", "rev-abc", "--root", str(tmp_path / "empty")])
    assert rc == EXIT_ERROR
    assert "plane DB not found" in capsys.readouterr().err


def test_get_formal_review_job_empty_id(tmp_path: Path) -> None:
    with pytest.raises(FleetCommsCliError, match="review_id is required"):
        get_formal_review_job("  ", root=tmp_path)


def test_acp_discuss_cli_scopes_active_transport_and_restores_environment(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys,
) -> None:
    from scripts.agent_runtime import acpx_discuss

    observed: list[str | None] = []

    def fake_run_discussion(**_kwargs):
        observed.append(os.environ.get("LU_ACPX_TRANSPORT"))
        return {"state": "COMPLETE"}

    monkeypatch.setenv("LU_ACPX_TRANSPORT", "shadow")
    monkeypatch.setattr(acpx_discuss, "run_discussion", fake_run_discussion)
    monkeypatch.setattr("sys.stdin", io.StringIO("bounded design question"))

    rc = main(
        [
            "acp-discuss",
            "--cwd",
            str(tmp_path),
            "--task-id",
            "task-6094",
            "--correlation-id",
            "corr-6094",
            "--idempotency-key",
            "idem-6094",
            "--rounds",
            "2",
            "--json",
        ]
    )

    assert rc == EXIT_OK
    assert observed == ["active"]
    assert os.environ["LU_ACPX_TRANSPORT"] == "shadow"
    assert json.loads(capsys.readouterr().out) == {"state": "COMPLETE"}


def test_launcher_transport_routes_supported_bridge_command_to_durable_acp(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys,
) -> None:
    from scripts.ai_agent_bridge import _channels, _channels_cli, _config, _db

    db_path = tmp_path / "bridge.db"
    monkeypatch.setattr(_config, "DB_PATH", db_path)
    monkeypatch.setattr(_db, "DB_PATH", db_path)
    monkeypatch.setattr(_channels, "fetch_monitor_state", lambda: None)
    monkeypatch.setattr(_channels, "context_sha256", lambda path: "")
    monkeypatch.setattr(
        _channels,
        "load_channel_context",
        lambda channel: {"body": "", "revs": {}, "missing": []},
    )
    monkeypatch.setenv("LU_AGENT_COMM_TRANSPORT", "acp")
    _channels.create_channel("architecture", exist_ok=False)
    observed: dict[str, object] = {}

    def fake_run_discussion(**kwargs):
        observed.update(kwargs)
        return {
            "conversation_id": "conversation_" + ("a" * 32),
            "state": "COMPLETE",
            "rounds_completed": 2,
            "synthesis": "ACP synthesis",
        }

    monkeypatch.setattr("agent_runtime.acpx_discuss.run_discussion", fake_run_discussion)
    monkeypatch.setattr(
        "agent_runtime.runner.invoke",
        lambda *_a, **_k: pytest.fail("eligible ACP discussion must not call bridge runtime"),
    )
    args = SimpleNamespace(
        channel="architecture",
        body="Compare the bounded options.",
        with_agents="kimicc,pool",
        max_rounds=2,
        review=False,
        models=None,
    )

    assert _channels_cli._handle_discuss(args) == 0
    assert observed["participants"] == ("kimicc", "pool")
    assert "Compare the bounded options." in str(observed["prompt"])
    assert "--- monitor: project state" not in str(observed["prompt"])
    output = capsys.readouterr().out
    assert "transport: ACP (kimicc, pool)" in output
    assert "/acp.html?conversation=conversation_" in output
    messages = _channels.read("architecture", tail=10)
    assert any("[ACP COMPLETE]" in message["body"] for message in messages)


def test_acp_discuss_cli_busy_is_body_free_no_queue_json(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys,
) -> None:
    from scripts.agent_runtime import acpx_discuss

    def refuse_busy(**_kwargs):
        raise acpx_discuss.AcpxDiscussionBusyError("private holder details")

    monkeypatch.setattr(acpx_discuss, "run_discussion", refuse_busy)
    monkeypatch.setattr("sys.stdin", io.StringIO("bounded design question"))

    rc = main(
        [
            "acp-discuss",
            "--cwd",
            str(tmp_path),
            "--task-id",
            "task-6094",
            "--correlation-id",
            "corr-6094",
            "--idempotency-key",
            "idem-6094",
            "--json",
        ]
    )

    output = capsys.readouterr()
    assert rc == EXIT_ERROR
    assert json.loads(output.out) == {
        "classification": "busy",
        "queued": False,
        "retryable": False,
        "state": "BUSY",
    }
    assert output.err == ""
    assert "private holder details" not in output.out


def test_acp_verify_cli_exit_codes_and_compact_receipt(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys,
) -> None:
    from scripts.agent_runtime import acpx_discuss

    conversation_id = "conversation_" + ("a" * 32)
    monkeypatch.setattr(
        acpx_discuss,
        "verify_discussion_receipt",
        lambda **_kwargs: {
            "conversation_id": conversation_id,
            "verified": True,
            "content_included": False,
        },
    )

    rc = main(
        [
            "acp-verify",
            "--conversation-id",
            conversation_id,
            "--root",
            str(tmp_path),
            "--require-replay",
            "--json",
        ]
    )

    assert rc == EXIT_OK
    assert json.loads(capsys.readouterr().out) == {
        "content_included": False,
        "conversation_id": conversation_id,
        "verified": True,
    }


def test_acp_verify_cli_maps_missing_receipt_to_not_found(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys,
) -> None:
    from scripts.agent_runtime import acpx_discuss

    def missing(**_kwargs):
        raise acpx_discuss.AcpxDiscussionNotFoundError("receipt missing")

    monkeypatch.setattr(acpx_discuss, "verify_discussion_receipt", missing)

    rc = main(
        [
            "acp-verify",
            "--conversation-id",
            "conversation_" + ("b" * 32),
            "--root",
            str(tmp_path),
        ]
    )

    assert rc == EXIT_NOT_FOUND
    assert "receipt missing" in capsys.readouterr().err
