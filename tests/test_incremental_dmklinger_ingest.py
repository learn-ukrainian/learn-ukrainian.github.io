"""Real SQLite and builder-oracle tests for the translations-only boundary."""
import hashlib
import json
import select
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.ingest import incremental_dmklinger_ingest as ingest
from scripts.wiki import build_sources_db as builder


def read_rows(path):
    with sqlite3.connect(path) as conn:
        return ingest.table_rows(conn)


@pytest.fixture
def staged(tmp_path, monkeypatch):
    chunks = tmp_path / "chunks.jsonl"
    definitions = [[f"item {i}" for i in range(13)], ["short", 'quote " \\ \n'], [f"last {i}" for i in range(11)]]
    entries = [
        {"id": f"dmk-{i:06d}", "word": "sample", "pos": "verb" if i == 2 else "noun",
         "translations": items, "text": "stable first-five text", "source": "synthetic"}
        for i, items in enumerate(definitions)
    ]
    chunks.write_text("".join(json.dumps(entry, ensure_ascii=False) + "\n" for entry in entries), encoding="utf-8")
    db, oracle = tmp_path / "staged.db", tmp_path / "oracle.db"
    legacy = tmp_path / "old.jsonl"
    legacy.write_text("".join(json.dumps({**entry, "translations": entry["translations"][:10]}) + "\n" for entry in entries))
    for path, input_path in ((db, legacy), (oracle, chunks)):
        with sqlite3.connect(path) as conn:
            conn.executescript(builder.SCHEMA)
            builder._ingest_jsonl(conn, ingest.TABLE, input_path, list(ingest.COLUMNS[1:]), "fixture")
            conn.execute("CREATE TABLE unrelated (id INTEGER PRIMARY KEY, value BLOB)")
            conn.execute("INSERT INTO unrelated VALUES (3, X'010203')")
    monkeypatch.setattr(ingest, "INPUT_SHA256", hashlib.sha256(chunks.read_bytes()).hexdigest())
    monkeypatch.setattr(ingest, "PREIMAGE_SHA256", ingest.rows_digest(read_rows(db)))
    monkeypatch.setattr(ingest, "POSTIMAGE_SHA256", ingest.rows_digest(read_rows(oracle)))
    monkeypatch.setattr(ingest, "EXPECTED_CHANGED_ROWS", 2)
    monkeypatch.setattr(ingest, "EXPECTED_RESTORED_ITEMS", 4)
    return db, chunks, oracle, tmp_path / "receipt.json"


def run(staged, **kwargs):
    db, chunks, _, receipt = staged
    return ingest.ingest(db, chunks, input_sha256=ingest.INPUT_SHA256, receipt_path=receipt, **kwargs)


def test_dry_run_apply_builder_equivalence_and_verify_only_rerun(staged, monkeypatch):
    db, _, oracle, receipt = staged
    before = db.read_bytes()
    result = run(staged)
    assert result["status"] == "dry_run"
    assert result["changed_rows"] == 2 and result["restored_items"] == 4
    assert db.read_bytes() == before
    result = run(staged, apply=True)
    assert result["status"] == "committed"
    assert result["postimage_sha256"] == ingest.POSTIMAGE_SHA256
    assert read_rows(db) == read_rows(oracle)
    with sqlite3.connect(db) as conn:
        assert conn.execute("SELECT * FROM unrelated").fetchall() == [(3, b"\x01\x02\x03")]
        assert conn.execute("PRAGMA integrity_check").fetchall() == [("ok",)]
    before = db.read_bytes()
    install_fault(monkeypatch, deny_writes=True)
    assert run(staged, apply=True)["status"] == "already_applied"
    assert run(staged)["status"] == "already_applied"
    assert db.read_bytes() == before
    assert json.loads(receipt.read_text())["status"] == "already_applied"


@pytest.mark.parametrize("mutation", ["drop_item", "reorder_items", "pos", "byte", "drop_row", "reorder_rows", "duplicate_row"])
def test_mutated_input_refused_even_with_its_supplied_digest(staged, mutation):
    db, chunks, _, receipt = staged
    with chunks.open(encoding="utf-8") as handle:
        rows = [json.loads(line) for line in handle]
    if mutation == "drop_item":
        rows[0]["translations"].pop()
    elif mutation == "reorder_items":
        rows[0]["translations"].reverse()
    elif mutation == "pos":
        rows[0]["pos"] = "changed"
    elif mutation == "byte":
        rows[0]["text"] += "!"
    elif mutation == "drop_row":
        rows.pop()
    elif mutation == "reorder_rows":
        rows.reverse()
    else:
        rows.append(rows[0])
    chunks.write_text("".join(json.dumps(row) + "\n" for row in rows))
    before = db.read_bytes()
    with pytest.raises(ingest.IngestError, match="input SHA256"):
        ingest.ingest(db, chunks, input_sha256=hashlib.sha256(chunks.read_bytes()).hexdigest(), receipt_path=receipt, apply=True)
    assert db.read_bytes() == before and not receipt.exists()


@pytest.mark.parametrize("sql", [
    "UPDATE dmklinger_uk_en SET word='changed' WHERE id=1",
    "UPDATE dmklinger_uk_en SET pos='changed' WHERE id=1",
    "UPDATE dmklinger_uk_en SET text='changed' WHERE id=1",
    "UPDATE dmklinger_uk_en SET source='changed' WHERE id=1",
    "UPDATE dmklinger_uk_en SET translations='[]' WHERE id=1",
    "UPDATE dmklinger_uk_en SET id=8 WHERE id=1",
    "DELETE FROM dmklinger_uk_en WHERE id=1",
    "ALTER TABLE dmklinger_uk_en ADD COLUMN unexpected TEXT",
    "DROP INDEX idx_dmklinger_word",
    "CREATE TRIGGER unsafe AFTER UPDATE ON dmklinger_uk_en BEGIN UPDATE unrelated SET value='changed'; END",
])
def test_wrong_preimage_schema_triggers_ids_text_refused_without_writes(staged, sql):
    db, _, _, receipt = staged
    with sqlite3.connect(db) as conn:
        conn.execute(sql)
    before = db.read_bytes()
    with pytest.raises(ingest.IngestError, match=r"preimage|schema/index"):
        run(staged, apply=True)
    assert db.read_bytes() == before and not receipt.exists()


def install_fault(monkeypatch, *, execute_error=None, update_error=False, deny_writes=False, bad_result=None):
    original = sqlite3.connect

    class FaultConnection(sqlite3.Connection):
        def execute(self, sql, parameters=()):
            if execute_error and sql.startswith(execute_error):
                raise sqlite3.OperationalError("injected SQLite failure")
            if bad_result and sql.startswith(bad_result[0]):
                return iter(bad_result[1]) if "integrity_check" in sql else FakeCursor(bad_result[1])
            if deny_writes:
                assert not sql.startswith(("UPDATE", "INSERT", "DELETE", "PRAGMA wal_checkpoint"))
            return super().execute(sql, parameters)

        def executemany(self, sql, parameters):
            assert not deny_writes
            if update_error:
                first, *_ = parameters
                super().execute(sql, first)
                raise sqlite3.OperationalError("injected failure after first UPDATE")
            return super().executemany(sql, parameters)

    class FakeCursor:
        def __init__(self, value):
            self.value = value

        def fetchone(self):
            return self.value

    def connect(database, *args, **kwargs):
        if "mode=rw" in str(database):
            kwargs["factory"] = FaultConnection
        return original(database, *args, **kwargs)

    monkeypatch.setattr(sqlite3, "connect", connect)


@pytest.mark.parametrize("fault", ["update", "commit", "integrity", "postimage"])
def test_failure_rolls_back_every_update(staged, monkeypatch, fault):
    db = staged[0]
    before = read_rows(db)
    if fault == "update":
        install_fault(monkeypatch, update_error=True)
    elif fault == "commit":
        install_fault(monkeypatch, execute_error="COMMIT")
    elif fault == "integrity":
        install_fault(monkeypatch, bad_result=("PRAGMA integrity_check", [("injected corruption",)]))
    else:
        original = ingest.table_rows
        calls = 0

        def wrong_after_update(conn):
            nonlocal calls
            calls += 1
            rows = original(conn)
            return rows[:-1] if calls == 3 else rows

        monkeypatch.setattr(ingest, "table_rows", wrong_after_update)
    with pytest.raises((ingest.IngestError, sqlite3.OperationalError)):
        run(staged, apply=True)
    assert read_rows(db) == before


@pytest.mark.parametrize("fault", ["checkpoint_exception", "checkpoint_busy", "receipt"])
def test_postcommit_failures_report_committed_and_do_not_claim_rollback(staged, monkeypatch, fault):
    db, _, oracle, receipt = staged
    with sqlite3.connect(db) as conn:
        conn.execute("PRAGMA journal_mode=WAL")
    if fault == "checkpoint_exception":
        install_fault(monkeypatch, execute_error="PRAGMA wal_checkpoint")
    elif fault == "checkpoint_busy":
        install_fault(monkeypatch, bad_result=("PRAGMA wal_checkpoint", [1, 2, 1]))
    else:
        def fail_receipt(*args):
            raise OSError("injected durable receipt failure")
        monkeypatch.setattr(ingest, "atomic_write", fail_receipt)
    result = run(staged, apply=True)
    assert result["status"] == "committed_with_post_commit_error"
    assert result["post_commit_error"]
    assert read_rows(db) == read_rows(oracle)
    if fault != "receipt":
        assert json.loads(receipt.read_text())["status"] == "committed_with_post_commit_error"


def test_cli_dry_run_apply_rerun_and_error_codes(staged, capsys, monkeypatch):
    db, chunks, _, receipt = staged
    argv = ["--db", str(db), "--input", str(chunks), "--input-sha256", ingest.INPUT_SHA256, "--receipt", str(receipt)]
    assert ingest.main(argv) == 0
    assert ingest.main([*argv, "--apply"]) == 0
    assert ingest.main([*argv, "--apply"]) == 0
    assert '"status": "already_applied"' in capsys.readouterr().out
    receipt.unlink()
    monkeypatch.setattr(ingest, "PREIMAGE_SHA256", "wrong")
    chunks.write_text("wrong")
    assert ingest.main(argv) == 2
    assert "REFUSED" in capsys.readouterr().err


def test_cli_postcommit_receipt_error_exit_three(staged, monkeypatch, capsys):
    db, chunks, _, receipt = staged
    def fail(*args):
        raise OSError("receipt failed")
    monkeypatch.setattr(ingest, "atomic_write", fail)
    assert ingest.main(["--db", str(db), "--input", str(chunks), "--input-sha256", ingest.INPUT_SHA256,
                        "--receipt", str(receipt), "--apply"]) == 3
    assert "committed_with_post_commit_error" in capsys.readouterr().out


def test_missing_files_and_receipt_collision_refused(staged):
    db, chunks, _, receipt = staged
    with pytest.raises(ingest.IngestError, match="already exist"):
        ingest.ingest(db.parent / "missing.db", chunks, input_sha256=ingest.INPUT_SHA256, receipt_path=receipt)
    for path in (db, chunks):
        with pytest.raises(ingest.IngestError, match="overwrite"):
            ingest.ingest(db, chunks, input_sha256=ingest.INPUT_SHA256, receipt_path=path, apply=True)
    chunks.unlink()
    with pytest.raises(FileNotFoundError):
        run(staged)


@pytest.mark.parametrize("apply", [False, True], ids=["dry-run", "apply"])
@pytest.mark.parametrize("entrypoint", ["callable", "cli"])
@pytest.mark.parametrize("target", ["database", "input", "-wal", "-shm", "-journal"])
@pytest.mark.parametrize("alias", ["direct", "symlink", "hardlink"])
def test_receipt_collisions_preserve_every_protected_file(staged, capsys, apply, entrypoint, target, alias):
    db, chunks, _, independent_receipt = staged
    sidecars = [Path(f"{db}{suffix}") for suffix in ("-wal", "-shm", "-journal")]
    for sidecar in sidecars:
        sidecar.write_bytes(b'{"status":"existing receipt-shaped sidecar"}\n')
    protected = [db, chunks, *sidecars]
    destination = {"database": db, "input": chunks}.get(target, Path(f"{db}{target}"))
    receipt = destination
    if alias != "direct":
        receipt = db.parent / "receipt-alias.json"
        if alias == "symlink":
            receipt.symlink_to(destination)
        else:
            receipt.hardlink_to(destination)
    before = {path: path.read_bytes() for path in [*protected, receipt]}
    if entrypoint == "callable":
        with pytest.raises(ingest.IngestError, match="receipt must not overwrite"):
            ingest.ingest(db, chunks, input_sha256=ingest.INPUT_SHA256, receipt_path=receipt, apply=apply)
    else:
        args = ["--db", str(db), "--input", str(chunks), "--input-sha256", ingest.INPUT_SHA256,
                "--receipt", str(receipt)]
        assert ingest.main([*args, *(["--apply"] if apply else [])]) == 2
        output = capsys.readouterr()
        assert output.out == ""
        assert "REFUSED: receipt must not overwrite" in output.err
    assert {path: path.read_bytes() for path in before} == before
    assert not independent_receipt.exists()
    if alias == "symlink":
        assert receipt.is_symlink()
    elif alias == "hardlink":
        assert receipt.samefile(destination)


@pytest.mark.parametrize("apply", [False, True], ids=["dry-run", "apply"])
@pytest.mark.parametrize("suffix", ["-wal", "-shm", "-journal"])
@pytest.mark.parametrize("alias", ["direct", "receipt-symlink", "database-symlink", "parent-symlink"])
def test_absent_sidecar_receipt_refused_before_reading_missing_input(staged, apply, suffix, alias):
    db, chunks, _, _ = staged
    sidecar = Path(f"{db}{suffix}")
    receipt = sidecar
    if alias == "receipt-symlink":
        receipt = db.parent / "dangling-receipt.json"
        receipt.symlink_to(sidecar)
    elif alias == "database-symlink":
        db_alias = db.parent / "database-alias.db"
        db_alias.symlink_to(db)
        db = db_alias
    elif alias == "parent-symlink":
        directory_alias = db.parent / "directory-alias"
        directory_alias.symlink_to(db.parent, target_is_directory=True)
        receipt = directory_alias / sidecar.name
    before = db.read_bytes()
    missing_input = chunks.parent / "missing.jsonl"
    with pytest.raises(ingest.IngestError, match="receipt must not overwrite"):
        ingest.ingest(db, missing_input, input_sha256="invalid", receipt_path=receipt, apply=apply)
    assert db.read_bytes() == before
    assert not sidecar.exists()
    assert not receipt.exists()
    assert not missing_input.exists()


@pytest.mark.parametrize("apply", [False, True], ids=["dry-run", "apply"])
@pytest.mark.parametrize("suffix", ["-wal", "-shm", "-journal"])
def test_refusal_preserves_independent_wal_commit_after_writer_crash(staged, apply, suffix):
    db, chunks, _, _ = staged
    writer_code = """
import sqlite3
import sys
conn = sqlite3.connect(sys.argv[1])
assert conn.execute('PRAGMA journal_mode=WAL').fetchone() == ('wal',)
conn.execute('PRAGMA wal_autocheckpoint=0')
conn.execute('CREATE TABLE independent_marker (value INTEGER)')
conn.execute('INSERT INTO independent_marker VALUES (42)')
conn.commit()
print('committed', flush=True)
sys.stdin.read()
"""
    writer = subprocess.Popen([sys.executable, "-c", writer_code, str(db)],
                              stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        assert select.select([writer.stdout], [], [], 15)[0], "WAL writer did not report commit"
        assert writer.stdout.readline() == "committed\n"
        wal, shm, journal = (Path(f"{db}{ending}") for ending in ("-wal", "-shm", "-journal"))
        assert wal.stat().st_size > 0 and shm.is_file()
        protected = [db, chunks, wal, shm]
        if suffix == "-journal":
            journal.write_bytes(b'{"status":"existing receipt-shaped sidecar"}\n')
            protected.append(journal)
        before = {path: path.read_bytes() for path in protected}
        with pytest.raises(ingest.IngestError, match="receipt must not overwrite"):
            ingest.ingest(db, chunks, input_sha256=ingest.INPUT_SHA256,
                          receipt_path=Path(f"{db}{suffix}"), apply=apply)
        assert {path: path.read_bytes() for path in protected} == before
    finally:
        writer.kill()
        writer.communicate(timeout=15)
    with sqlite3.connect(db) as conn:
        assert conn.execute("SELECT value FROM independent_marker").fetchall() == [(42,)]
        assert conn.execute("PRAGMA integrity_check").fetchall() == [("ok",)]


@pytest.mark.parametrize("apply, status", [(False, "dry_run"), (True, "committed")])
def test_independent_receipt_with_absent_sidecars_succeeds(staged, apply, status):
    db, chunks, oracle, receipt = staged
    before = db.read_bytes(), chunks.read_bytes()
    assert all(not Path(f"{db}{suffix}").exists() for suffix in ("-wal", "-shm", "-journal"))
    result = run(staged, apply=apply)
    assert result["status"] == status
    assert json.loads(receipt.read_text())["status"] == status
    assert chunks.read_bytes() == before[1]
    if apply:
        assert read_rows(db) == read_rows(oracle)
    else:
        assert db.read_bytes() == before[0]


def test_postimage_pin_and_unexpected_delta_refused(staged, monkeypatch):
    before = staged[0].read_bytes()
    with monkeypatch.context() as m:
        m.setattr(ingest, "POSTIMAGE_SHA256", "wrong")
        with pytest.raises(ingest.IngestError, match="builder output"):
            run(staged, apply=True)
    monkeypatch.setattr(ingest, "EXPECTED_CHANGED_ROWS", 3)
    with pytest.raises(ingest.IngestError, match="changed-row"):
        run(staged, apply=True)
    assert staged[0].read_bytes() == before


def test_direct_cli_help_and_missing_required_arguments():
    command = [sys.executable, str(Path(ingest.__file__))]
    result = subprocess.run([*command, "--help"], text=True, capture_output=True, timeout=30)
    assert result.returncode == 0 and "Outputs:" in result.stdout
    assert "Exit codes:" in result.stdout and "--input-sha256" in result.stdout
    result = subprocess.run(command, text=True, capture_output=True, timeout=30)
    assert result.returncode == 2 and "required" in result.stderr
