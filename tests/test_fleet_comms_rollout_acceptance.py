"""Rollout acceptance coverage for the fleet-comms message plane (#5512)."""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Callable
from pathlib import Path

import pytest

from scripts.ai_agent_bridge import _ask_lifecycle as lifecycle
from scripts.ai_agent_bridge import _claude, _codex, _config, _db, _gemini
from scripts.fleet_comms.artifacts import ArtifactStore
from scripts.fleet_comms.formal_review_finalize import finalize_formal_review_verdict
from scripts.fleet_comms.formal_review_jobs import FormalReviewJobService
from scripts.fleet_comms.message_plane import MessagePlane, read_plane_status
from scripts.fleet_comms.migrations import MIGRATIONS
from scripts.fleet_comms.request_executor import RequestExecutor

_REPOSITORY = "learn-ukrainian/learn-ukrainian.github.io"
_HEAD_SHA = "a" * 40


@pytest.fixture
def dual_write_bridge(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, Path]:
    """Point the legacy bridge and opt-in plane at isolated durable stores."""
    legacy_db = tmp_path / "legacy" / "messages.db"
    plane_root = tmp_path / "batch_state" / "fleet-comms" / "v1"
    monkeypatch.setattr(_config, "DB_PATH", legacy_db)
    monkeypatch.setattr(_db, "DB_PATH", legacy_db)
    monkeypatch.setattr(lifecycle, "_PLANE_ROOT_OVERRIDE", plane_root)
    monkeypatch.setenv("FLEET_COMMS_MESSAGE_PLANE", "dual_write")
    with _db.init_db() as conn:
        assert conn.execute("SELECT 1").fetchone() is not None
    return legacy_db, plane_root


def _legacy_message(legacy_db: Path, message_id: int) -> tuple[str, str, str]:
    with sqlite3.connect(legacy_db) as conn:
        row = conn.execute(
            "SELECT from_llm, to_llm, status FROM messages WHERE id = ?", (message_id,)
        ).fetchone()
    assert row is not None
    return tuple(str(value) for value in row)


def _request_for_legacy_message(plane_root: Path, message_id: int) -> tuple[str, str]:
    with sqlite3.connect(plane_root / "comms.sqlite3") as conn:
        row = conn.execute(
            """
            SELECT request_id, requested_recipient
            FROM requests
            JOIN comms_messages
              ON comms_messages.message_id = requests.request_message_id
            WHERE json_extract(comms_messages.metadata_json, '$.legacy_message_id') = ?
            """,
            (message_id,),
        ).fetchone()
    assert row is not None
    return str(row[0]), str(row[1])


@pytest.mark.parametrize(
    ("recipient", "send"),
    [
        (
            "codex",
            lambda: _codex.ask_codex("acceptance ask", task_id="rollout-codex", from_llm="test"),
        ),
        (
            "claude",
            lambda: _claude.ask_claude("acceptance ask", task_id="rollout-claude", from_llm="test"),
        ),
        (
            "gemini",
            lambda: _gemini.ask_gemini(
                "acceptance ask",
                task_id="rollout-gemini",
                from_llm="test",
                async_mode=True,
            ),
        ),
    ],
)
def test_bridge_asks_dual_write_to_legacy_and_message_plane(
    dual_write_bridge: tuple[Path, Path],
    monkeypatch: pytest.MonkeyPatch,
    recipient: str,
    send: Callable[[], int | None],
) -> None:
    """Each public ask writes its legacy row and synchronous plane request."""
    legacy_db, plane_root = dual_write_bridge
    monkeypatch.setattr(_codex, "process_for_codex", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(_claude, "process_for_claude", lambda *_args, **_kwargs: None)

    message_id = send()
    assert isinstance(message_id, int)
    assert _legacy_message(legacy_db, message_id) == ("test", recipient, "sent")
    request_id, request_recipient = _request_for_legacy_message(plane_root, message_id)
    assert request_id.startswith("request_")
    assert request_recipient == recipient


def test_schema_v2_contains_rollout_contract_tables_and_columns(tmp_path: Path) -> None:
    """A new plane root migrates to every known schema version before traffic."""
    root = tmp_path / "batch_state" / "fleet-comms" / "v1"
    with ArtifactStore(root=root) as store:
        versions = [
            tuple(row)
            for row in store.connection.execute(
                "SELECT version, name FROM comms_schema_migrations ORDER BY version"
            )
        ]
        tables = {
            str(row[0])
            for row in store.connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
        }
        review_columns = {
            str(row[1])
            for row in store.connection.execute("PRAGMA table_info(formal_review_jobs)")
        }
        request_columns = {
            str(row[1]) for row in store.connection.execute("PRAGMA table_info(requests)")
        }

    assert versions == [(migration.version, migration.name) for migration in MIGRATIONS]
    assert {
        "artifacts",
        "comms_messages",
        "comms_schema_migrations",
        "formal_review_attempts",
        "formal_review_jobs",
        "github_publications",
        "requests",
    }.issubset(tables)
    assert {"review_id", "head_sha", "sealed_verdict_artifact_id", "state"}.issubset(
        review_columns
    )
    assert {"request_id", "request_message_id", "completion_state", "state"}.issubset(
        request_columns
    )


def test_formal_review_verdict_is_sealed_as_an_immutable_json_artifact(tmp_path: Path) -> None:
    """Formal verdict provenance is durably sealed before any live publication."""
    root = tmp_path / "batch_state" / "fleet-comms" / "v1"
    result = finalize_formal_review_verdict(
        pr_number=5512,
        model="claude-sonnet-5",
        family="anthropic",
        harness="claude",
        verdict="APPROVED",
        repository=_REPOSITORY,
        head_sha=_HEAD_SHA,
        plane_root=root,
    )

    assert result.published is False
    assert result.sealed_verdict_artifact_id is not None
    with FormalReviewJobService(root=root) as service:
        job = service.get_job(result.review_id)
        assert job.sealed_verdict_artifact_id == result.sealed_verdict_artifact_id
        artifact = service.store.get(result.sealed_verdict_artifact_id)
        sealed = json.loads(service.store.read_bytes(artifact.artifact_id))

    assert artifact.retention_class == "sealed-verdict"
    assert artifact.logical_filename == f"{result.review_id}.sealed-verdict.json"
    assert sealed == {
        "family": "anthropic",
        "gate_kind": "cross-family-review",
        "harness": "claude",
        "head_sha": _HEAD_SHA,
        "model": "claude-sonnet-5",
        "pr_number": 5512,
        "repository": _REPOSITORY,
        "review_id": result.review_id,
        "verdict": "APPROVED",
    }


def test_dual_write_completion_records_clean_parity_telemetry(tmp_path: Path) -> None:
    """A proven complete plane request projects legacy state with clean parity."""
    root = tmp_path / "batch_state" / "fleet-comms" / "v1"
    telemetry = root / "telemetry" / "plane-parity.jsonl"
    legacy_db = tmp_path / "legacy.db"
    with sqlite3.connect(legacy_db) as conn:
        conn.execute("CREATE TABLE messages (id INTEGER PRIMARY KEY, status TEXT)")
        conn.execute("INSERT INTO messages(id, status) VALUES (1, 'sent')")

    with ArtifactStore(root=root) as store:
        executor = RequestExecutor(store=store)
        with MessagePlane(
            mode="dual_write",
            executor=executor,
            legacy_db=legacy_db,
            telemetry_path=telemetry,
        ) as plane:
            request = plane.open_ask(
                recipient="codex",
                body="complete rollout acceptance request",
                legacy_message_id=1,
            )
            assert request is not None

            def project_legacy(message_id: int, reply_id: str) -> None:
                with sqlite3.connect(legacy_db) as conn:
                    conn.execute(
                        "UPDATE messages SET status = ? WHERE id = ?",
                        (f"replied:{reply_id}", message_id),
                    )

            result = plane.complete_ask(
                request.request_id,
                adapter="codex",
                stdout="\n".join(
                    (
                        json.dumps({"type": "agent_message", "text": "complete"}),
                        json.dumps({"type": "task_complete", "reason": "stop"}),
                    )
                ),
                returncode=0,
                legacy_message_id=1,
                legacy_status_writer=project_legacy,
            )

    assert result.projected_legacy_replied is True
    assert result.parity is not None
    assert result.parity.parity_ok is True
    events = [json.loads(line) for line in telemetry.read_text(encoding="utf-8").splitlines()]
    assert events[-1]["event"] == "plane_complete"
    assert events[-1]["parity_ok"] is True

    status = read_plane_status(root=root, telemetry_path=telemetry)
    assert status["parity_telemetry"]["parity_ok_count"] == 1
    assert status["parity_telemetry"]["parity_fail_count"] == 0


def test_dual_write_mode_is_reported_read_only_with_migrated_plane(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The configured dual-write mode is observable without changing plane state."""
    root = tmp_path / "batch_state" / "fleet-comms" / "v1"
    monkeypatch.setenv("FLEET_COMMS_MESSAGE_PLANE", "dual_write")
    with ArtifactStore(root=root):
        pass

    status = read_plane_status(root=root)
    assert status["mode"] == "dual_write"
    assert status["enabled"] is True
    assert status["read_only"] is True
    assert status["schema"]["applied_version"] == 2
