from __future__ import annotations

import json
import os
import sqlite3
import uuid
from pathlib import Path

import pytest

from scripts.hygiene import codex_rollout_reconcile as reconcile

NOW = 1_800_000_000
OLD = NOW - 3 * 24 * 60 * 60
RECENT = NOW - 60
IDS = {
    name: str(uuid.uuid5(uuid.NAMESPACE_URL, f"codex-rollout-test-{name}"))
    for name in ("old", "present", "pinned", "recent", "outside", "malformed", "archived")
}


def _rollout(
    home: Path,
    thread_id: str,
    *,
    archived: bool = False,
    present: bool = False,
    filename_id: str | None = None,
) -> Path:
    root = home / ("archived_sessions" if archived else "sessions") / "2026" / "07"
    path = root / f"rollout-2026-07-31-{filename_id or thread_id}.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    if present:
        path.write_text("{}\n", encoding="utf-8")
    return path


def _db(
    home: Path,
    *,
    include_pinned: bool = True,
    edge_fks: bool = False,
    archived_row: bool = False,
) -> Path:
    home.mkdir(parents=True, exist_ok=True)
    database = home / "state_5.sqlite"
    connection = sqlite3.connect(database)
    pinned_column = ", is_pinned INTEGER NOT NULL DEFAULT 0" if include_pinned else ""
    edge_foreign_keys = (
        ", FOREIGN KEY(parent_thread_id) REFERENCES threads(id),"
        " FOREIGN KEY(child_thread_id) REFERENCES threads(id)"
        if edge_fks
        else ""
    )
    connection.executescript(
        f"""
        CREATE TABLE threads (
            id TEXT PRIMARY KEY, rollout_path TEXT NOT NULL, created_at INTEGER NOT NULL,
            updated_at INTEGER NOT NULL, archived INTEGER NOT NULL DEFAULT 0{pinned_column}
        );
        CREATE TABLE thread_spawn_edges (
            parent_thread_id TEXT NOT NULL, child_thread_id TEXT NOT NULL PRIMARY KEY,
            status TEXT NOT NULL{edge_foreign_keys}
        );
        CREATE TABLE thread_dynamic_tools (
            thread_id TEXT PRIMARY KEY REFERENCES threads(id) ON DELETE CASCADE, payload TEXT NOT NULL
        );
        """
    )
    rows = [
        (IDS["old"], str(_rollout(home, IDS["old"])), OLD, OLD, 0, 0),
        (IDS["present"], str(_rollout(home, IDS["present"], present=True)), OLD, OLD, 0, 0),
        (IDS["pinned"], str(_rollout(home, IDS["pinned"])), OLD, OLD, 0, 1),
        (IDS["recent"], str(_rollout(home, IDS["recent"])), RECENT, RECENT, 0, 0),
        (IDS["outside"], str(home.parent / "outside" / f"rollout-{IDS['outside']}.jsonl"), OLD, OLD, 0, 0),
        (IDS["malformed"], str(home / "sessions" / "2026" / f"note-{IDS['malformed']}.txt"), OLD, OLD, 0, 0),
    ]
    if archived_row:
        rows.append((IDS["archived"], str(_rollout(home, IDS["archived"], archived=True)), OLD, OLD, 1, 0))
    if include_pinned:
        connection.executemany(
            "INSERT INTO threads(id, rollout_path, created_at, updated_at, archived, is_pinned) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            rows,
        )
    else:
        connection.executemany(
            "INSERT INTO threads(id, rollout_path, created_at, updated_at, archived) VALUES (?, ?, ?, ?, ?)",
            [row[:5] for row in rows],
        )
    if edge_fks:
        connection.executemany(
            "INSERT INTO thread_spawn_edges VALUES (?, ?, ?)",
            [(IDS["old"], IDS["recent"], "done"), (IDS["recent"], IDS["old"], "done")],
        )
    else:
        connection.executemany(
            "INSERT INTO thread_spawn_edges VALUES (?, ?, ?)",
            [(IDS["old"], IDS["recent"], "done"), (IDS["recent"], IDS["old"], "done")],
        )
    connection.execute("INSERT INTO thread_dynamic_tools VALUES (?, ?)", (IDS["old"], "tool"))
    connection.commit()
    connection.close()
    return database


def _digest(home: Path, database: Path) -> str:
    return reconcile.scan(codex_home=home, db_path=database, now=NOW)["eligible_digest"]


def _insert_thread(
    database: Path,
    *,
    thread_id: str,
    rollout_path: Path,
    updated_at: int = OLD,
    archived: int = 0,
    pinned: int = 0,
) -> None:
    with sqlite3.connect(database) as connection:
        connection.execute(
            "INSERT INTO threads(id, rollout_path, created_at, updated_at, archived, is_pinned) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (thread_id, str(rollout_path), updated_at, updated_at, archived, pinned),
        )


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
    assert len(report["eligible_digest"]) == 64
    assert [row["id"] for row in report["rows"]] == sorted(IDS[name] for name in IDS if name != "archived")


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


@pytest.mark.parametrize("value", [float("nan"), float("inf"), float("-inf")])
def test_scan_rejects_non_finite_inputs(tmp_path: Path, value: float) -> None:
    home = tmp_path / "codex"
    _db(home)
    with pytest.raises(reconcile.ReconcileError, match="finite"):
        reconcile.scan(codex_home=home, min_age_seconds=value, now=NOW)
    with pytest.raises(reconcile.ReconcileError, match="finite"):
        reconcile.scan(codex_home=home, min_age_seconds=0, now=value)


def test_apply_requires_digest_and_refuses_same_count_substitution(tmp_path: Path) -> None:
    home = tmp_path / "codex"
    database = _db(home)
    report = reconcile.scan(codex_home=home, db_path=database, now=NOW)
    missing_digest = reconcile.apply(
        codex_home=home, db_path=database, expected_eligible_stale=1, acknowledge=True, now=NOW
    )
    assert missing_digest["error"] == "expected_digest_required"

    replacement_id = str(uuid.uuid4())
    with sqlite3.connect(database) as connection:
        connection.execute("DELETE FROM threads WHERE id = ?", (IDS["old"],))
        connection.execute(
            "INSERT INTO threads(id, rollout_path, created_at, updated_at, archived, is_pinned) VALUES (?, ?, ?, ?, 0, 0)",
            (replacement_id, str(_rollout(home, replacement_id)), OLD, OLD),
        )
    result = reconcile.apply(
        codex_home=home,
        db_path=database,
        backup_dir=tmp_path / "backups",
        expected_eligible_stale=1,
        expected_eligible_digest=report["eligible_digest"],
        acknowledge=True,
        now=NOW,
    )

    assert result["error"] == "expected_digest_mismatch"
    assert not (tmp_path / "backups").exists()
    with sqlite3.connect(database) as connection:
        assert connection.execute("SELECT count(*) FROM threads WHERE id = ?", (replacement_id,)).fetchone()[0] == 1


def test_apply_locks_before_backup_and_includes_completed_wal_commit(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    home = tmp_path / "codex"
    database = _db(home)
    with sqlite3.connect(database) as connection:
        connection.execute("PRAGMA journal_mode = WAL")
        connection.commit()
    report = reconcile.scan(codex_home=home, db_path=database, now=NOW)
    live_id = str(uuid.uuid4())
    live_rollout = _rollout(home, live_id, present=True)
    original_open = reconcile._open_writable

    def open_with_completed_writer(path: Path) -> sqlite3.Connection:
        writable = original_open(path)
        with sqlite3.connect(database) as live_writer:
            live_writer.execute(
                "INSERT INTO threads(id, rollout_path, created_at, updated_at, archived, is_pinned) "
                "VALUES (?, ?, ?, ?, 0, 0)",
                (live_id, str(live_rollout), OLD, OLD),
            )
        return writable

    monkeypatch.setattr(reconcile, "_open_writable", open_with_completed_writer)
    result = reconcile.apply(
        codex_home=home,
        db_path=database,
        expected_eligible_stale=1,
        expected_eligible_digest=report["eligible_digest"],
        acknowledge=True,
        now=NOW,
    )

    assert result["post_apply_parity"] is True
    with sqlite3.connect(Path(result["backup_path"])) as connection:
        assert connection.execute("SELECT count(*) FROM threads WHERE id = ?", (live_id,)).fetchone()[0] == 1


def test_apply_validates_backup_integrity_and_deletes_fk_edges_first(tmp_path: Path) -> None:
    home = tmp_path / "codex"
    database = _db(home, edge_fks=True)
    result = reconcile.scan(codex_home=home, db_path=database, now=NOW)
    receipt = reconcile.apply(
        codex_home=home,
        db_path=database,
        backup_dir=tmp_path / "backups",
        expected_eligible_stale=1,
        expected_eligible_digest=result["eligible_digest"],
        acknowledge=True,
        now=NOW,
    )

    assert receipt["post_apply_parity"] is True
    assert receipt["integrity_check"] == "ok"
    assert receipt["counts"] == {"deleted": 1, "skipped": 0, "spawn_edges_deleted": 2}
    backup = Path(receipt["backup_path"])
    assert backup.is_file()
    assert os.stat(backup).st_mode & 0o777 == 0o600
    assert os.stat(backup.parent).st_mode & 0o777 == 0o700
    with sqlite3.connect(backup) as connection:
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert connection.execute("SELECT count(*) FROM threads WHERE id = ?", (IDS["old"],)).fetchone()[0] == 1
    with sqlite3.connect(database) as connection:
        assert connection.execute("SELECT count(*) FROM threads WHERE id = ?", (IDS["old"],)).fetchone()[0] == 0
        assert connection.execute("SELECT count(*) FROM thread_dynamic_tools WHERE thread_id = ?", (IDS["old"],)).fetchone()[0] == 0
        assert connection.execute("SELECT count(*) FROM thread_spawn_edges").fetchone()[0] == 0


def test_unknown_dependency_protects_missing_rows_and_refuses_apply(tmp_path: Path) -> None:
    home = tmp_path / "codex"
    database = _db(home)
    with sqlite3.connect(database) as connection:
        connection.execute(
            "CREATE TABLE unknown_thread_dependency(thread_id TEXT REFERENCES threads(id) ON DELETE CASCADE)"
        )
    report = reconcile.scan(codex_home=home, db_path=database, now=NOW)
    assert report["counts"]["eligible_stale"] == 0
    assert report["rows"][[row["id"] for row in report["rows"]].index(IDS["old"])]["classification"] == "suspicious_schema"
    receipt = reconcile.apply(
        codex_home=home,
        db_path=database,
        backup_dir=tmp_path / "backups",
        expected_eligible_stale=0,
        expected_eligible_digest=report["eligible_digest"],
        acknowledge=True,
        now=NOW,
    )
    assert receipt["error"] == "unsafe_schema"
    assert not (tmp_path / "backups").exists()


def test_delete_trigger_is_unsupported(tmp_path: Path) -> None:
    home = tmp_path / "codex"
    database = _db(home)
    with sqlite3.connect(database) as connection:
        connection.execute("CREATE TRIGGER block_thread_delete BEFORE DELETE ON threads BEGIN SELECT RAISE(ABORT, 'blocked'); END")
    report = reconcile.scan(codex_home=home, db_path=database, now=NOW)
    assert report["counts"]["eligible_stale"] == 0
    assert any("trigger" in issue for issue in report["schema_issues"])


def test_uuid_archived_identity_and_symlinks_are_suspicious(tmp_path: Path) -> None:
    home = tmp_path / "codex"
    database = _db(home, archived_row=True)
    wrong_root_id = str(uuid.uuid4())
    wrong_root_path = _rollout(home, wrong_root_id, archived=True)
    wrong_root_path.unlink(missing_ok=True)
    _insert_thread(database, thread_id=wrong_root_id, rollout_path=wrong_root_path)
    wrong_name_id = str(uuid.uuid4())
    _insert_thread(database, thread_id=wrong_name_id, rollout_path=_rollout(home, wrong_name_id, filename_id=IDS["old"]))
    invalid_archived_id = str(uuid.uuid4())
    invalid_archived_path = _rollout(home, invalid_archived_id)
    _insert_thread(database, thread_id=invalid_archived_id, rollout_path=invalid_archived_path, archived=2)
    symlink_id = str(uuid.uuid4())
    symlink_path = _rollout(home, symlink_id)
    symlink_path.symlink_to(_rollout(home, str(uuid.uuid4()), present=True))
    _insert_thread(database, thread_id=symlink_id, rollout_path=symlink_path)
    dangling_id = str(uuid.uuid4())
    dangling_path = _rollout(home, dangling_id)
    dangling_path.symlink_to(dangling_path.with_name("not-there.jsonl"))
    _insert_thread(database, thread_id=dangling_id, rollout_path=dangling_path)
    non_uuid_id = "not-a-uuid"
    _insert_thread(database, thread_id=non_uuid_id, rollout_path=home / "sessions" / "rollout-not-a-uuid.jsonl")

    report = reconcile.scan(codex_home=home, db_path=database, now=NOW)
    by_id = {row["id"]: row for row in report["rows"]}
    assert by_id[IDS["archived"]]["classification"] == "eligible_stale"
    assert by_id[wrong_root_id]["classification"] == "suspicious_path"
    assert by_id[wrong_name_id]["classification"] == "suspicious_path"
    assert by_id[invalid_archived_id]["classification"] == "suspicious_schema"
    assert by_id[symlink_id]["classification"] == "suspicious_path"
    assert by_id[dangling_id]["classification"] == "suspicious_path"
    assert by_id[non_uuid_id]["classification"] == "suspicious_schema"


def test_explicit_database_must_be_real_and_directly_under_home(tmp_path: Path) -> None:
    home = tmp_path / "codex"
    database = _db(home)
    with pytest.raises(reconcile.ReconcileError, match="directly under"):
        reconcile.discover_database(home, tmp_path / "state_5.sqlite")
    link = home / "state_link.sqlite"
    link.symlink_to(database)
    with pytest.raises(reconcile.ReconcileError, match="regular file"):
        reconcile.discover_database(home, link)
    directory = home / "state_directory.sqlite"
    directory.mkdir()
    with pytest.raises(reconcile.ReconcileError, match="regular file"):
        reconcile.discover_database(home, directory)


def test_post_commit_verification_failure_reports_actual_mutation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    home = tmp_path / "codex"
    database = _db(home)
    digest = _digest(home, database)

    def fail_scan(*args: object, **kwargs: object) -> dict[str, object]:
        raise reconcile.ReconcileError("forced verification failure")

    monkeypatch.setattr(reconcile, "scan", fail_scan)
    receipt = reconcile.apply(
        codex_home=home,
        db_path=database,
        expected_eligible_stale=1,
        expected_eligible_digest=digest,
        acknowledge=True,
        now=NOW,
    )

    assert receipt["error"] == "post_commit_verification_failed"
    assert receipt["deleted_ids"] == [IDS["old"]]
    assert receipt["counts"]["deleted"] == 1
    assert receipt["mutation_committed"] is True
    assert receipt["backup_path"] is not None
    with sqlite3.connect(database) as connection:
        assert connection.execute("SELECT count(*) FROM threads WHERE id = ?", (IDS["old"],)).fetchone()[0] == 0


def test_missing_skipped_candidate_fails_parity(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    home = tmp_path / "codex"
    database = _db(home)
    digest = _digest(home, database)
    original_backup = reconcile._create_backup
    original_row_report = reconcile._row_report
    original_scan = reconcile.scan

    def backup_then_skip(path: Path, directory: Path) -> Path:
        backup = original_backup(path, directory)

        def skip_old(row: sqlite3.Row, **kwargs: object) -> dict[str, object]:
            report = original_row_report(row, **kwargs)
            if row["id"] == IDS["old"]:
                report["classification"] = "protected_recent"
            return report

        monkeypatch.setattr(reconcile, "_row_report", skip_old)
        return backup

    def scan_without_skipped(*args: object, **kwargs: object) -> dict[str, object]:
        report = original_scan(*args, **kwargs)
        report["rows"] = [row for row in report["rows"] if row["id"] != IDS["old"]]
        return report

    monkeypatch.setattr(reconcile, "_create_backup", backup_then_skip)
    monkeypatch.setattr(reconcile, "scan", scan_without_skipped)
    receipt = reconcile.apply(
        codex_home=home,
        db_path=database,
        expected_eligible_stale=1,
        expected_eligible_digest=digest,
        acknowledge=True,
        now=NOW,
    )

    assert receipt["error"] == "post_commit_verification_failed"
    assert receipt["counts"]["deleted"] == 0
    assert receipt["mutation_committed"] is True


def test_changed_candidate_is_skipped_without_deletion(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    home = tmp_path / "codex"
    database = _db(home)
    digest = _digest(home, database)
    original_backup = reconcile._create_backup
    original_row_report = reconcile._row_report

    def backup_then_change(path: Path, directory: Path) -> Path:
        backup = original_backup(path, directory)

        def changed_old(row: sqlite3.Row, **kwargs: object) -> dict[str, object]:
            report = original_row_report(row, **kwargs)
            if row["id"] == IDS["old"]:
                report["classification"] = "protected_recent"
            return report

        monkeypatch.setattr(reconcile, "_row_report", changed_old)
        return backup

    monkeypatch.setattr(reconcile, "_create_backup", backup_then_change)
    result = reconcile.apply(
        codex_home=home,
        db_path=database,
        expected_eligible_stale=1,
        expected_eligible_digest=digest,
        acknowledge=True,
        now=NOW,
    )

    assert result["counts"]["deleted"] == 0
    assert result["skipped"] == [{"id": IDS["old"], "reason": "protected_recent"}]
    assert result["post_apply_parity"] is True


def test_apply_is_idempotent_and_fail_on_stale_is_read_only(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    home = tmp_path / "codex"
    database = _db(home)
    first_scan = reconcile.scan(codex_home=home, db_path=database, now=NOW)
    assert reconcile.main(
        ["scan", "--codex-home", str(home), "--db", str(database), "--fail-on-stale", "--now", str(NOW)]
    ) == 1
    assert json.loads(capsys.readouterr().out)["counts"]["eligible_stale"] == 1
    first = reconcile.apply(
        codex_home=home,
        db_path=database,
        expected_eligible_stale=1,
        expected_eligible_digest=first_scan["eligible_digest"],
        acknowledge=True,
        now=NOW,
    )
    assert first["counts"]["deleted"] == 1
    second_scan = reconcile.scan(codex_home=home, db_path=database, now=NOW)
    second = reconcile.apply(
        codex_home=home,
        db_path=database,
        expected_eligible_stale=0,
        expected_eligible_digest=second_scan["eligible_digest"],
        acknowledge=True,
        now=NOW,
    )
    assert second["counts"]["deleted"] == 0
    assert second["backup_path"] is None
    assert reconcile.main(
        ["scan", "--codex-home", str(home), "--db", str(database), "--fail-on-stale", "--now", str(NOW)]
    ) == 0
    assert json.loads(capsys.readouterr().out)["counts"]["eligible_stale"] == 0
