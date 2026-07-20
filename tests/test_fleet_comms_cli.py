"""Unit tests for thin fleet-comms CLI (plane-status + formal-job get)."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

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
        assert apply_migrations(conn) == 1
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
    assert data["mode"] == "off"
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
