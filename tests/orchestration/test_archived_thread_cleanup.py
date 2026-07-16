from __future__ import annotations

import json
import sqlite3
import stat
import subprocess
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from scripts.orchestration import archived_thread_cleanup as cleanup
from scripts.orchestration import task_identity

NOW = datetime(2026, 7, 16, 18, 0, tzinfo=UTC)
THREAD_A = "00000000-0000-4000-8000-000000000001"
THREAD_B = "00000000-0000-4000-8000-000000000002"
THREAD_C = "00000000-0000-4000-8000-000000000003"


def _database(path: Path, rows: list[tuple[object, ...]]) -> Path:
    connection = sqlite3.connect(path)
    connection.execute(
        """
        create table threads (
            id text primary key,
            rollout_path text not null,
            created_at integer not null,
            updated_at integer not null,
            source text not null default '',
            model_provider text not null default '',
            cwd text not null,
            title text not null,
            sandbox_policy text not null default '',
            approval_mode text not null default '',
            archived integer not null default 0,
            archived_at integer
        )
        """
    )
    connection.executemany(
        """
        insert into threads (
            id, rollout_path, created_at, updated_at, cwd, title, archived, archived_at
        ) values (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        rows,
    )
    connection.commit()
    connection.close()
    return path


def _row(
    thread_id: str,
    transcript: Path,
    *,
    archived_at: datetime,
    title: str = "Archived task",
) -> tuple[object, ...]:
    timestamp = int(archived_at.timestamp())
    return (
        thread_id,
        str(transcript),
        timestamp - 100,
        timestamp,
        str(transcript.parent),
        title,
        1,
        timestamp,
    )


def _codex_home(path: Path, *, pinned: list[str] | None = None) -> Path:
    path.mkdir()
    (path / ".codex-global-state.json").write_text(
        json.dumps(
            {
                "pinned-thread-ids": pinned or [],
                "active-workspace-roots": [],
            }
        ),
        encoding="utf-8",
    )
    return path


def _write_live_rollover_lease(root: Path, *, source_thread_id: str) -> None:
    prepared_at = "2026-07-16T09:00:00Z"
    lineage_id = "cleanup-protection"
    rollover_id = "rollover-cleanup-protection"
    identity = task_identity.build_identity(
        repository=task_identity.DEFAULT_REPOSITORY,
        stream_epic=None,
        stream_epic_url=None,
        github_issue_number=None,
        github_issue_url=None,
        semantic_title="Cleanup protection fixture",
        task_family="thread-rollover",
        role="codex",
        predecessor_task_id=source_thread_id,
        replacement_task_id=None,
        lineage_id=lineage_id,
        generation=1,
        terminal_goal="merge",
    )
    lease = {
        "schema_version": 2,
        "agent": "codex",
        "lineage_id": lineage_id,
        "rollover_id": rollover_id,
        "active": {
            "thread_id": source_thread_id,
            "generation": 0,
            "lineage_id": lineage_id,
            "started_at": prepared_at,
            "last_seen_at": prepared_at,
        },
        "replacement": {
            "rollover_id": rollover_id,
            "lineage_id": lineage_id,
            "generation": 1,
            "status": "pending_start",
            "prepared_at": prepared_at,
            "identity": identity,
            "title_transition": task_identity.new_title_transition(
                harness="codex-app",
                visible_title_value=identity["visible_title"],
                prepared_at=prepared_at,
            ),
        },
        "updated_at": prepared_at,
    }
    path = root / ".agent" / "thread-rollovers" / "codex" / lineage_id / "lease.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(lease), encoding="utf-8")


def _runner(db: Path, transcript_by_id: dict[str, Path], *, fail: set[str] | None = None):
    commands: list[tuple[str, ...]] = []
    failures = fail or set()

    def run(command):
        normalized = tuple(command)
        commands.append(normalized)
        thread_id = normalized[-1]
        if thread_id in failures:
            return subprocess.CompletedProcess(normalized, 9, "", "synthetic failure")
        connection = sqlite3.connect(db)
        connection.execute("delete from threads where id = ?", (thread_id,))
        connection.commit()
        connection.close()
        transcript_by_id[thread_id].unlink()
        return subprocess.CompletedProcess(normalized, 0, "deleted", "")

    return run, commands


def test_dry_run_observes_old_thread_and_protects_pinned(tmp_path: Path) -> None:
    home = _codex_home(tmp_path / "codex", pinned=[THREAD_B])
    state_dir = tmp_path / "cleanup"
    first = tmp_path / "first.jsonl"
    second = tmp_path / "second.jsonl"
    first.write_bytes(b"a" * 4096)
    second.write_bytes(b"b" * 2048)
    db = _database(
        tmp_path / "state_5.sqlite",
        [
            _row(THREAD_A, first, archived_at=NOW - timedelta(days=31)),
            _row(THREAD_B, second, archived_at=NOW - timedelta(days=90)),
        ],
    )

    receipt = cleanup.run_cleanup(
        codex_home=home,
        db_path=db,
        state_dir=state_dir,
        now=NOW,
        current_cwd=tmp_path,
    )

    by_id = {item["thread_id"]: item for item in receipt["outcomes"]}
    assert receipt["mode"] == "dry-run"
    assert by_id[THREAD_A]["outcome"] == "observing"
    assert by_id[THREAD_B]["outcome"] == "protected"
    assert by_id[THREAD_B]["reasons"] == ["pinned"]
    assert first.exists() and second.exists()
    state = json.loads((state_dir / "state-v1.json").read_text(encoding="utf-8"))
    assert list(state["observations"]) == [THREAD_A]
    assert Path(receipt["receipt_path"]).is_file()


def test_second_unchanged_observation_deletes_through_exact_cli(tmp_path: Path) -> None:
    home = _codex_home(tmp_path / "codex")
    state_dir = tmp_path / "cleanup"
    transcript = tmp_path / "thread.jsonl"
    transcript.write_bytes(b"payload" * 1000)
    db = _database(
        tmp_path / "state_5.sqlite",
        [_row(THREAD_A, transcript, archived_at=NOW - timedelta(days=40))],
    )
    cleanup.run_cleanup(
        apply=True,
        codex_home=home,
        db_path=db,
        state_dir=state_dir,
        now=NOW,
        current_cwd=tmp_path,
    )
    runner, commands = _runner(db, {THREAD_A: transcript})

    receipt = cleanup.run_cleanup(
        apply=True,
        codex_home=home,
        db_path=db,
        state_dir=state_dir,
        now=NOW + timedelta(days=8),
        runner=runner,
        sleep=lambda _: None,
        codex_binary="/opt/codex/bin/codex",
        current_cwd=tmp_path,
    )

    assert commands == [("/opt/codex/bin/codex", "delete", "--force", THREAD_A)]
    outcome = receipt["outcomes"][0]
    assert outcome["outcome"] == "deleted"
    assert outcome["reclaimed_bytes"] > 0
    assert not transcript.exists()
    state = json.loads((state_dir / "state-v1.json").read_text(encoding="utf-8"))
    assert state["observations"] == {}


def test_changed_fingerprint_restarts_observation(tmp_path: Path) -> None:
    home = _codex_home(tmp_path / "codex")
    state_dir = tmp_path / "cleanup"
    transcript = tmp_path / "thread.jsonl"
    transcript.write_text("original", encoding="utf-8")
    db = _database(
        tmp_path / "state_5.sqlite",
        [_row(THREAD_A, transcript, archived_at=NOW - timedelta(days=45))],
    )
    cleanup.run_cleanup(
        codex_home=home,
        db_path=db,
        state_dir=state_dir,
        now=NOW,
        current_cwd=tmp_path,
    )
    connection = sqlite3.connect(db)
    connection.execute("update threads set title = ? where id = ?", ("changed", THREAD_A))
    connection.commit()
    connection.close()
    runner, commands = _runner(db, {THREAD_A: transcript})

    receipt = cleanup.run_cleanup(
        apply=True,
        codex_home=home,
        db_path=db,
        state_dir=state_dir,
        now=NOW + timedelta(days=8),
        runner=runner,
        current_cwd=tmp_path,
    )

    assert commands == []
    assert receipt["outcomes"][0]["outcome"] == "observing"
    assert transcript.exists()


def test_malformed_pin_registry_blocks_apply_and_clears_observations(tmp_path: Path) -> None:
    home = _codex_home(tmp_path / "codex")
    (home / ".codex-global-state.json").write_text("{}", encoding="utf-8")
    transcript = tmp_path / "thread.jsonl"
    transcript.write_text("payload", encoding="utf-8")
    db = _database(
        tmp_path / "state_5.sqlite",
        [_row(THREAD_A, transcript, archived_at=NOW - timedelta(days=100))],
    )
    runner, commands = _runner(db, {THREAD_A: transcript})

    receipt = cleanup.run_cleanup(
        apply=True,
        codex_home=home,
        db_path=db,
        state_dir=tmp_path / "cleanup",
        now=NOW,
        runner=runner,
        current_cwd=tmp_path,
    )

    assert commands == []
    assert receipt["protection_errors"]
    assert receipt["outcomes"][0]["outcome"] == "protected"
    assert "protection_registry_unavailable" in receipt["outcomes"][0]["reasons"]


def test_automation_and_rollover_references_are_protected(
    tmp_path: Path,
) -> None:
    home = _codex_home(tmp_path / "codex")
    automation_dir = home / "automations" / "weekly"
    automation_dir.mkdir(parents=True)
    (automation_dir / "automation.toml").write_text(
        f'prompt = "inspect {THREAD_A}"\ncwds = []\n',
        encoding="utf-8",
    )
    first = tmp_path / "a.jsonl"
    second = tmp_path / "b.jsonl"
    first.write_text("a", encoding="utf-8")
    second.write_text("b", encoding="utf-8")
    db = _database(
        tmp_path / "state_5.sqlite",
        [
            _row(THREAD_A, first, archived_at=NOW - timedelta(days=100)),
            _row(THREAD_B, second, archived_at=NOW - timedelta(days=100)),
        ],
    )
    _write_live_rollover_lease(tmp_path, source_thread_id=THREAD_B)

    receipt = cleanup.run_cleanup(
        codex_home=home,
        db_path=db,
        state_dir=tmp_path / "cleanup",
        now=NOW,
        current_cwd=tmp_path,
    )

    by_id = {item["thread_id"]: item for item in receipt["outcomes"]}
    assert by_id[THREAD_A]["reasons"] == ["automation_reference"]
    assert by_id[THREAD_B]["reasons"] == ["live_rollover_reference"]


def test_delete_failure_does_not_prevent_later_candidate(tmp_path: Path) -> None:
    home = _codex_home(tmp_path / "codex")
    state_dir = tmp_path / "cleanup"
    first = tmp_path / "a.jsonl"
    second = tmp_path / "b.jsonl"
    first.write_bytes(b"a" * 100)
    second.write_bytes(b"b" * 100)
    db = _database(
        tmp_path / "state_5.sqlite",
        [
            _row(THREAD_A, first, archived_at=NOW - timedelta(days=100)),
            _row(THREAD_B, second, archived_at=NOW - timedelta(days=100)),
        ],
    )
    cleanup.run_cleanup(
        codex_home=home,
        db_path=db,
        state_dir=state_dir,
        now=NOW,
        current_cwd=tmp_path,
    )
    runner, commands = _runner(
        db,
        {THREAD_A: first, THREAD_B: second},
        fail={THREAD_A},
    )

    receipt = cleanup.run_cleanup(
        apply=True,
        codex_home=home,
        db_path=db,
        state_dir=state_dir,
        now=NOW + timedelta(days=8),
        runner=runner,
        sleep=lambda _: None,
        current_cwd=tmp_path,
    )

    assert [command[-1] for command in commands] == [THREAD_A, THREAD_B]
    by_id = {item["thread_id"]: item for item in receipt["outcomes"]}
    assert by_id[THREAD_A]["outcome"] == "delete_failed"
    assert by_id[THREAD_B]["outcome"] == "deleted"
    assert first.exists() and not second.exists()


def test_cleanup_lock_refuses_concurrent_run(tmp_path: Path) -> None:
    state_dir = tmp_path / "cleanup"
    with cleanup.cleanup_lock(state_dir):
        assert stat.S_IMODE(state_dir.stat().st_mode) == 0o700
        with pytest.raises(cleanup.CleanupBusyError):
            with cleanup.cleanup_lock(state_dir):
                pass


def test_receipt_writer_restricts_directory_and_file_permissions(tmp_path: Path) -> None:
    destination = tmp_path / "receipts" / "v1" / "receipt.json"

    cleanup._write_json(destination, {"status": "ok"})

    assert stat.S_IMODE(destination.parent.stat().st_mode) == 0o700
    assert stat.S_IMODE(destination.stat().st_mode) == 0o600
