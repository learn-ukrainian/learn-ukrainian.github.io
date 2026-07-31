from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path

import pytest

from scripts.hygiene import codex_rollout_reconcile as reconcile

NOW = 1_800_000_000
OLD = NOW - 3 * 24 * 60 * 60
RECENT = NOW - 60
IDS = {name: f"thread-{index}" for index, name in enumerate(("old", "present", "pinned", "recent", "outside", "malformed"))}


def _rollout(home: Path, name: str, *, present: bool = False) -> Path:
    path = home / "sessions" / "2026" / "07" / f"rollout-{name}.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    if present:
        path.write_text("{}\n", encoding="utf-8")
    return path


def _db(home: Path, *, include_pinned: bool = True) -> Path:
    home.mkdir(parents=True, exist_ok=True)
    database = home / "state_5.sqlite"
    connection = sqlite3.connect(database)
    pinned_column = ", is_pinned INTEGER NOT NULL DEFAULT 0" if include_pinned else ""
    connection.executescript(
        f"""
        CREATE TABLE threads (
            id TEXT PRIMARY KEY, rollout_path TEXT NOT NULL, created_at INTEGER NOT NULL,
            updated_at INTEGER NOT NULL{pinned_column}
        );
        CREATE TABLE thread_spawn_edges (
            parent_thread_id TEXT NOT NULL, child_thread_id TEXT NOT NULL PRIMARY KEY, status TEXT NOT NULL
        );
        CREATE TABLE thread_dynamic_tools (
            thread_id TEXT PRIMARY KEY REFERENCES threads(id) ON DELETE CASCADE, payload TEXT NOT NULL
        );
        """
    )
    home.joinpath("sessions").mkdir(parents=True, exist_ok=True)
    rows = [
        (IDS["old"], str(_rollout(home, "old")), OLD, OLD, 0),
        (IDS["present"], str(_rollout(home, "present", present=True)), OLD, OLD, 0),
        (IDS["pinned"], str(_rollout(home, "pinned")), OLD, OLD, 1),
        (IDS["recent"], str(_rollout(home, "recent")), RECENT, RECENT, 0),
        (IDS["outside"], str(home.parent / "outside" / "rollout-outside.jsonl"), OLD, OLD, 0),
        (IDS["malformed"], str(home / "sessions" / "2026" / "note.txt"), OLD, OLD, 0),
    ]
    if include_pinned:
        connection.executemany(
            "INSERT INTO threads(id, rollout_path, created_at, updated_at, is_pinned) VALUES (?, ?, ?, ?, ?)",
            rows,
        )
    else:
        connection.executemany(
            "INSERT INTO threads(id, rollout_path, created_at, updated_at) VALUES (?, ?, ?, ?)",
            [row[:4] for row in rows],
        )
    connection.executemany(
        "INSERT INTO thread_spawn_edges VALUES (?, ?, ?)",
        [(IDS["old"], IDS["recent"], "done"), (IDS["recent"], IDS["old"], "done")],
    )
    connection.execute("INSERT INTO thread_dynamic_tools VALUES (?, ?)", (IDS["old"], "tool"))
    connection.commit()
    connection.close()
    return database


def test_scan_classifies_present_stale_protected_and_suspicious(tmp_path: Path) -> None:
    home = tmp_path / "codex"
    database = _db(home)
    report = reconcile.scan(codex_home=home, now=NOW)

    assert report["counts"] == {
        "present": 1,
        "eligible_stale": 1,
        "protected_pinned": 1,
        "protected_recent": 1,
        "suspicious_path": 2,
        "suspicious_schema": 0,
    }
    assert report["eligible_stale_ids"] == [IDS["old"]]
    assert [row["id"] for row in report["rows"]] == sorted(IDS.values())


def test_scan_protects_unknown_schema_and_global_pin(tmp_path: Path) -> None:
    home = tmp_path / "codex"
    database = _db(home, include_pinned=False)
    home.joinpath(".codex-global-state.json").write_text(
        json.dumps({"pinned-thread-ids": [IDS["old"]]}), encoding="utf-8"
    )
    report = reconcile.scan(codex_home=home, db_path=database, now=NOW)

    assert report["counts"]["eligible_stale"] == 0
    assert report["counts"]["suspicious_schema"] == 3
    assert report["counts"]["present"] == 1


def test_count_mismatch_refuses_before_backup_or_write(tmp_path: Path) -> None:
    home = tmp_path / "codex"
    database = _db(home)
    result = reconcile.apply(
        codex_home=home,
        db_path=database,
        backup_dir=tmp_path / "backups",
        expected_eligible_stale=2,
        acknowledge=True,
        now=NOW,
    )

    assert result["error"] == "expected_count_mismatch"
    assert not (tmp_path / "backups").exists()
    with sqlite3.connect(database) as connection:
        assert connection.execute("SELECT count(*) FROM threads WHERE id = ?", (IDS["old"],)).fetchone()[0] == 1


def test_apply_backs_up_revalidates_edges_and_preserves_rollout(tmp_path: Path) -> None:
    home = tmp_path / "codex"
    database = _db(home)
    preserved_rollout = _rollout(home, "present", present=True)
    result = reconcile.apply(
        codex_home=home,
        db_path=database,
        backup_dir=tmp_path / "backups",
        expected_eligible_stale=1,
        acknowledge=True,
        now=NOW,
    )

    assert result["post_apply_parity"] is True
    assert result["integrity_check"] == "ok"
    assert result["counts"] == {"deleted": 1, "skipped": 0, "spawn_edges_deleted": 2}
    backup = Path(result["backup_path"])
    assert backup.is_file()
    assert os.stat(backup).st_mode & 0o777 == 0o600
    with sqlite3.connect(backup) as connection:
        assert connection.execute("SELECT count(*) FROM threads WHERE id = ?", (IDS["old"],)).fetchone()[0] == 1
    assert preserved_rollout.is_file()
    with sqlite3.connect(database) as connection:
        assert connection.execute("SELECT count(*) FROM threads WHERE id = ?", (IDS["old"],)).fetchone()[0] == 0
        assert connection.execute("SELECT count(*) FROM thread_dynamic_tools WHERE thread_id = ?", (IDS["old"],)).fetchone()[0] == 0
        assert connection.execute("SELECT count(*) FROM thread_spawn_edges").fetchone()[0] == 0


def test_apply_skips_changed_candidate_inside_transaction(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    home = tmp_path / "codex"
    database = _db(home)
    original_backup = reconcile._create_backup

    def backup_then_change(path: Path, directory: Path) -> Path:
        backup = original_backup(path, directory)
        with sqlite3.connect(database) as connection:
            connection.execute("UPDATE threads SET updated_at = ? WHERE id = ?", (NOW, IDS["old"]))
            connection.commit()
        return backup

    monkeypatch.setattr(reconcile, "_create_backup", backup_then_change)
    result = reconcile.apply(
        codex_home=home,
        db_path=database,
        backup_dir=tmp_path / "backups",
        expected_eligible_stale=1,
        acknowledge=True,
        now=NOW,
    )

    assert result["counts"]["deleted"] == 0
    assert result["skipped"] == [{"id": IDS["old"], "reason": "row_changed"}]
    assert result["post_apply_parity"] is True


def test_apply_is_idempotent_and_fail_on_stale_is_read_only(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    home = tmp_path / "codex"
    database = _db(home)
    assert reconcile.main(["scan", "--codex-home", str(home), "--db", str(database), "--fail-on-stale", "--now", str(NOW)]) == 1
    assert json.loads(capsys.readouterr().out)["counts"]["eligible_stale"] == 1
    first = reconcile.apply(
        codex_home=home, db_path=database, expected_eligible_stale=1, acknowledge=True, now=NOW
    )
    assert first["counts"]["deleted"] == 1
    second = reconcile.apply(
        codex_home=home, db_path=database, expected_eligible_stale=0, acknowledge=True, now=NOW
    )
    assert second["counts"]["deleted"] == 0
    assert second["backup_path"] is None
    assert reconcile.main(["scan", "--codex-home", str(home), "--db", str(database), "--fail-on-stale", "--now", str(NOW)]) == 0
    assert json.loads(capsys.readouterr().out)["counts"]["eligible_stale"] == 0
