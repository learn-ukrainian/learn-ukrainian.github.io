"""Synthetic storage controls for #11362; never open the real owner cache."""

import hashlib
import json
import os
import signal
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.common import github_client as owner
from scripts.maintenance import github_cache as maintenance
from tests.common.github_cache_isolation import isolate_github_client_cache


@pytest.fixture(autouse=True)
def isolated(tmp_path, monkeypatch):
    yield from isolate_github_client_cache(tmp_path, monkeypatch)


@pytest.fixture
def cache(tmp_path, monkeypatch):
    directory = tmp_path / "private-cache"
    directory.mkdir(mode=0o700)
    monkeypatch.setenv("LU_GITHUB_CACHE_DIR", str(directory))
    path = directory / "cache.sqlite3"
    with sqlite3.connect(path) as db:
        # Literal owner-compatible schema, independent of production constants.
        db.execute(
            "CREATE TABLE cache (scope TEXT, key TEXT, body BLOB, headers TEXT, at REAL, PRIMARY KEY(scope,key))"
        )
        db.execute(
            "CREATE TABLE budget (scope TEXT, resource TEXT, remaining INTEGER, reset INTEGER, PRIMARY KEY(scope,resource))"
        )
        db.executemany(
            "INSERT INTO cache VALUES(?,?,?,?,?)",
            [
                ("credential-a", "literal:credential-scoped:key", b'{"retained":true}', '{"ETag":"one"}', 1000),
                ("credential-b", "literal:credential-scoped:key", b'"other scope"', "{}", 2000),
                ("credential-a", "old-response", b'"expired but not ours to evict"', "{}", 1),
                ("unknown", "malformed-headers", b"\x00\xffprivate-body", "{broken", 99),
                (None, None, 42, None, "unclassified"),
            ],
        )
        db.executemany(
            "INSERT INTO budget VALUES(?,?,?,?)",
            [
                ("credential-a", "core", 499, 9999999999),
                ("credential-b", "retry_after", 0, 9999999999),
                ("unknown", "future-resource", "opaque", None),
            ],
        )
        db.execute("INSERT INTO cache VALUES('deleted','payload',zeroblob(2097152),'{}',1)")
        db.execute("DELETE FROM cache WHERE scope='deleted'")
    path.chmod(0o600)
    return path


def rows(path):
    with sqlite3.connect(path.as_uri() + "?mode=ro", uri=True) as db:
        assert db.execute("PRAGMA integrity_check").fetchone() == ("ok",)
        return {name: db.execute(f"SELECT * FROM {name} ORDER BY rowid").fetchall() for name in ("cache", "budget")}


def test_report_never_prunes_or_changes_file_bytes(cache):
    before = cache.read_bytes()
    result = maintenance.maintain()
    assert result["outcome"] == "report"
    assert result["eligible"] is True and result["applied"] is False
    assert result["before"]["response_rows"] == 3
    assert result["before"]["unclassified_rows"] == 2
    assert result["before"]["budget_rows"] == 3
    assert result["before"]["logical_response_bytes"] == 79
    assert result["before"]["freelist_count"] > 0
    assert result["before"]["file_bytes"] == len(before)
    assert result["before"]["allocated_bytes"] == cache.stat().st_blocks * 512
    assert cache.read_bytes() == before
    assert sorted(p.name for p in cache.parent.iterdir()) == ["cache.sqlite3"]


def test_apply_reclaims_physical_bytes_preserving_all_scopes_budgets_and_unknown_rows(cache, request):
    original = rows(cache)
    before = cache.stat()
    with sqlite3.connect(cache) as db:
        schema_before = db.execute("SELECT type,name,sql FROM sqlite_schema ORDER BY name").fetchall()
    result = maintenance.maintain(apply=True)
    assert result["outcome"] == "reclaimed" and result["applied"] is True
    assert cache.stat().st_size < before.st_size
    assert cache.stat().st_ino == before.st_ino
    assert result["reclaimed_file_bytes"] == before.st_size - cache.stat().st_size
    assert result["after"]["freelist_count"] == 0
    observed = rows(cache)
    assert observed == original
    with sqlite3.connect(cache) as db:
        schema_after = db.execute("SELECT type,name,sql FROM sqlite_schema ORDER BY name").fetchall()

    def digest(value):
        return hashlib.sha256(repr(value).encode()).hexdigest()

    before_digests = {"schema": digest(schema_before), **{name: digest(value) for name, value in original.items()}}
    after_digests = {"schema": digest(schema_after), **{name: digest(value) for name, value in observed.items()}}
    assert before_digests == after_digests
    request.node.user_properties.append(
        (
            "physical_preservation_probe",
            json.dumps(
                {
                    "proof_role": "supplemental_author_fixture",
                    "apply": result,
                    "raw_digests_before": before_digests,
                    "raw_digests_after": after_digests,
                    "integrity_check": "ok",
                }
            ),
        )
    )
    # A second apply is a literal no-op, including bytes and mode.
    compact = cache.read_bytes()
    assert maintenance.maintain(apply=True)["outcome"] == "no_op"
    assert cache.read_bytes() == compact and cache.stat().st_mode & 0o777 == 0o600


@pytest.mark.parametrize("apply", [False, True])
def test_missing_target_never_creates_database_or_parent(tmp_path, monkeypatch, apply):
    absent = tmp_path / "absent"
    monkeypatch.setenv("LU_GITHUB_CACHE_DIR", str(absent))
    assert maintenance.maintain(apply=apply) == {
        "outcome": "refused",
        "reason": "missing_database",
        "eligible": False,
        "applied": False,
    }
    assert not absent.exists()


def test_unresolved_owner_never_falls_back_to_memory(monkeypatch):
    monkeypatch.setattr(owner, "_cache_directory", lambda: None)
    assert maintenance.maintain(apply=True)["reason"] == "target_unresolved"


@pytest.mark.parametrize(
    "shape", ["text", "empty", "lookalike", "extra_table", "trigger", "different_index", "altered_predicate"]
)
def test_non_cache_or_ambiguous_schema_is_unchanged(cache, shape):
    if shape == "text":
        cache.write_bytes(b"not a sqlite database")
    elif shape == "empty":
        cache.write_bytes(b"")
    else:
        with sqlite3.connect(cache) as db:
            if shape == "lookalike":
                db.execute("ALTER TABLE cache ADD COLUMN unexpected TEXT")
            elif shape == "extra_table":
                db.execute("CREATE TABLE unrelated (secret TEXT)")
            elif shape == "trigger":
                db.execute("CREATE TRIGGER surprising AFTER INSERT ON cache BEGIN DELETE FROM budget; END")
            elif shape == "altered_predicate":
                db.execute(owner.CACHE_SCHEMA[-1].replace("_github_binary", "_GITHUB_BINARY"))
            else:
                db.execute("CREATE INDEX cache_retention ON cache(key)")
    before = cache.read_bytes()
    assert maintenance.maintain(apply=True)["reason"] == "wrong_schema"
    assert cache.read_bytes() == before


@pytest.mark.parametrize(
    "kind",
    [
        "database_symlink",
        "parent_symlink",
        "hardlink",
        "writable_file",
        "writable_parent",
        "sidecar_symlink",
        "directory",
        "fifo",
        "traversal",
    ],
)
def test_unsafe_targets_refuse_without_mutating_destination(cache, tmp_path, monkeypatch, kind):
    before = hashlib.sha256(cache.read_bytes()).hexdigest()
    destination = cache
    if kind == "database_symlink":
        destination = cache.with_name("original")
        cache.rename(destination)
        cache.symlink_to(destination)
    elif kind == "parent_symlink":
        alias = tmp_path / "alias"
        alias.symlink_to(cache.parent, target_is_directory=True)
        monkeypatch.setenv("LU_GITHUB_CACHE_DIR", str(alias))
    elif kind == "hardlink":
        os.link(cache, cache.with_name("alias"))
    elif kind == "writable_file":
        cache.chmod(0o666)
    elif kind == "writable_parent":
        cache.parent.chmod(0o777)
    elif kind == "sidecar_symlink":
        Path(str(cache) + "-journal").symlink_to(cache)
    elif kind in {"directory", "fifo"}:
        destination = cache.with_name("original")
        cache.rename(destination)
        if kind == "directory":
            cache.mkdir()
        else:
            os.mkfifo(cache)
    else:
        monkeypatch.setenv("LU_GITHUB_CACHE_DIR", str(cache.parent / ".." / cache.parent.name))
    assert maintenance.maintain(apply=True)["outcome"] == "refused"
    assert hashlib.sha256(destination.read_bytes()).hexdigest() == before


@pytest.mark.parametrize("transaction", ["BEGIN", "BEGIN IMMEDIATE", "BEGIN EXCLUSIVE"])
def test_busy_live_reader_or_writer_refuses_bounded_without_changes(cache, transaction):
    original = rows(cache)
    with sqlite3.connect(cache) as active:
        active.execute(transaction)
        active.execute("SELECT * FROM cache").fetchall()
        result = maintenance.maintain(apply=True, timeout_seconds=0.05)
        assert result["outcome"] == "refused" and result["reason"] == "busy"
        assert result["applied"] is False
        active.rollback()
    assert rows(cache) == original


def test_writer_racing_after_selection_is_refused(cache, monkeypatch):
    original_target = maintenance._target
    with sqlite3.connect(cache) as active:

        def race(stack):
            result = original_target(stack)
            active.execute("BEGIN IMMEDIATE")
            return result

        monkeypatch.setattr(maintenance, "_target", race)
        assert maintenance.maintain(apply=True, timeout_seconds=0.05)["reason"] == "busy"
        active.rollback()
    assert rows(cache)["budget"][0] == ("credential-a", "core", 499, 9999999999)


def test_exclusive_lock_remains_between_admission_and_vacuum(cache, monkeypatch):
    snapshot = maintenance._snapshot
    attempts = []

    def probe(db, path, original):
        if attempts:
            with sqlite3.connect(path, timeout=0) as contender:
                with pytest.raises(sqlite3.OperationalError, match="locked"):
                    contender.execute("SELECT * FROM cache").fetchall()
                with pytest.raises(sqlite3.OperationalError, match="locked"):
                    contender.execute("INSERT INTO budget VALUES('race','core',1,1)")
        attempts.append(True)
        return snapshot(db, path, original)

    monkeypatch.setattr(maintenance, "_snapshot", probe)
    assert maintenance.maintain(apply=True)["outcome"] == "reclaimed"
    assert len(attempts) == 2


@pytest.mark.parametrize("timeout", [0, -1, 301, float("inf"), float("nan"), "30", True])
def test_invalid_deadline_never_opens_target(monkeypatch, timeout):
    monkeypatch.setattr(owner, "_cache_directory", lambda: pytest.fail("opened target"))
    assert maintenance.maintain(apply=True, timeout_seconds=timeout)["reason"] == "invalid_timeout"


def test_pending_journal_refuses_without_recovery_or_deletion(cache):
    journal = Path(str(cache) + "-journal")
    journal.write_bytes(b"pending private journal")
    journal.chmod(0o600)
    before = cache.read_bytes()
    assert maintenance.maintain()["reason"] == "pending_journal"
    assert maintenance.maintain(apply=True)["reason"] == "pending_journal"
    assert cache.read_bytes() == before and journal.read_bytes() == b"pending private journal"


def test_wal_input_refuses_without_creating_sidecars_or_changing_mode(cache):
    with sqlite3.connect(cache) as db:
        db.execute("PRAGMA journal_mode=WAL")
    db.close()
    before = cache.read_bytes()
    assert maintenance.maintain(apply=True)["reason"] == "unsupported_journal"
    assert cache.read_bytes() == before
    assert sorted(p.name for p in cache.parent.iterdir()) == ["cache.sqlite3"]


def test_target_swap_is_detected_before_database_sql(cache, monkeypatch):
    real_connect = sqlite3.connect
    other = cache.with_name("replacement")
    other.write_bytes(cache.read_bytes())

    def swap(*args, **kwargs):
        result = real_connect(*args, **kwargs)
        os.replace(other, cache)
        return result

    monkeypatch.setattr(maintenance.sqlite3, "connect", swap)
    assert maintenance.maintain(apply=True)["reason"] == "target_changed"
    monkeypatch.setattr(maintenance.sqlite3, "connect", real_connect)
    assert rows(cache)["cache"][0][0] == "credential-a"


def test_deadline_and_cancellation_leave_intact_rows(cache, monkeypatch):
    original = rows(cache)
    assert maintenance.maintain(apply=True, cancelled=lambda: True)["reason"] == "interrupted"
    assert rows(cache) == original
    ticks = iter([0, 31])
    monkeypatch.setattr(maintenance.time, "monotonic", lambda: next(ticks, 31))
    assert maintenance.maintain(apply=True)["reason"] == "deadline"
    assert rows(cache) == original


def test_interrupt_inside_vacuum_rolls_back_retained_data(cache, monkeypatch):
    original = rows(cache)
    real_connect = sqlite3.connect

    class Interrupted(sqlite3.Connection):
        def execute(self, sql, *args, **kwargs):
            if sql == "VACUUM":
                # SQLite itself interrupts the real operation through its VM.
                self.set_progress_handler(lambda: 1, 1)
            return super().execute(sql, *args, **kwargs)

    monkeypatch.setattr(maintenance.sqlite3, "connect", lambda *a, **kw: real_connect(*a, **kw, factory=Interrupted))
    result = maintenance.maintain(apply=True)
    assert result["reason"] == "interrupted" and result["applied"] is False
    assert rows(cache) == original


def test_sqlite_io_failure_never_unlinks_or_falls_back(cache, monkeypatch):
    original = rows(cache)
    real_connect = sqlite3.connect

    class Failed(sqlite3.Connection):
        def execute(self, sql, *args, **kwargs):
            if sql == "VACUUM":
                raise sqlite3.OperationalError("private I/O detail with secret")
            return super().execute(sql, *args, **kwargs)

    monkeypatch.setattr(maintenance.sqlite3, "connect", lambda *a, **kw: real_connect(*a, **kw, factory=Failed))
    result = maintenance.maintain(apply=True)
    assert result["reason"] == "sqlite_failure"
    assert "secret" not in json.dumps(result)
    assert rows(cache) == original


def test_json_cli_defaults_and_help_never_leak_private_values(cache):
    command = [sys.executable, "-m", "scripts.maintenance.github_cache"]
    before = cache.read_bytes()
    report = subprocess.run(command, capture_output=True, text=True, check=False, timeout=30)
    assert report.returncode == 0 and json.loads(report.stdout)["outcome"] == "report"
    assert cache.read_bytes() == before
    applied = subprocess.run([*command, "--apply"], capture_output=True, text=True, check=False, timeout=30)
    assert applied.returncode == 0 and json.loads(applied.stdout)["outcome"] == "reclaimed"
    for private in (str(cache.parent), "credential-a", "private-body", "literal:credential-scoped:key", "ETag"):
        assert private not in report.stdout + report.stderr + applied.stdout + applied.stderr
    help_result = subprocess.run([*command, "--help"], capture_output=True, text=True, check=False, timeout=30)
    assert help_result.returncode == 0
    for required in ("Outputs:", "Exit codes:", "Related:", "--timeout-seconds", "--apply"):
        assert required in help_result.stdout


def test_cli_refusal_and_sigterm_are_typed_and_restore_handlers(cache, monkeypatch, capsys):
    original = rows(cache)
    old_handler = signal.getsignal(signal.SIGTERM)
    real_target = maintenance._target

    def stop(stack):
        result = real_target(stack)
        os.kill(os.getpid(), signal.SIGTERM)
        return result

    monkeypatch.setattr(maintenance, "_target", stop)
    assert maintenance.main(["--apply"]) == 130
    assert json.loads(capsys.readouterr().out)["reason"] == "interrupted"
    assert signal.getsignal(signal.SIGTERM) == old_handler
    assert rows(cache) == original
    assert maintenance.main(["--timeout-seconds", "0"]) == 2
    assert json.loads(capsys.readouterr().out)["reason"] == "invalid_timeout"


@pytest.mark.parametrize("arguments", [["--timeout-seconds", "private-input"], ["--unknown", "private-input"]])
def test_cli_invalid_arguments_do_not_echo_private_inputs(arguments):
    result = subprocess.run(
        [sys.executable, "-m", "scripts.maintenance.github_cache", *arguments],
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert result.returncode == 2 and result.stdout == ""
    assert result.stderr == "github_cache: invalid_arguments; use --help\n"


def test_post_commit_measurement_failure_is_not_reported_as_unapplied_refusal(cache, monkeypatch, capsys):
    original = rows(cache)
    size = cache.stat().st_size
    snapshot = maintenance._snapshot
    calls = []

    def fail_after(db, path, info):
        if calls:
            raise OSError("private detail")
        calls.append(True)
        return snapshot(db, path, info)

    monkeypatch.setattr(maintenance, "_snapshot", fail_after)
    assert maintenance.main(["--apply"]) == 2
    result = json.loads(capsys.readouterr().out)
    assert result["outcome"] == "applied_unverified" and result["applied"] is True
    assert result["reason"] == "unsafe_or_unavailable_target"
    assert cache.stat().st_size < size and rows(cache) == original


def test_deadline_during_vacuum_is_typed_and_rolls_back(cache, monkeypatch):
    original = rows(cache)
    real_connect = sqlite3.connect
    expired = [False]

    class Expired(sqlite3.Connection):
        def set_progress_handler(self, callback, steps):
            # Keep the production callback; shorten its interval for this tiny fixture.
            return super().set_progress_handler(callback, 1 if steps else 0)

        def execute(self, sql, *args, **kwargs):
            if sql == "VACUUM":
                expired[0] = True
            return super().execute(sql, *args, **kwargs)

    monkeypatch.setattr(maintenance.sqlite3, "connect", lambda *a, **kw: real_connect(*a, **kw, factory=Expired))
    monkeypatch.setattr(maintenance.time, "monotonic", lambda: 31 if expired[0] else 0)
    result = maintenance.maintain(apply=True)
    assert result["reason"] == "deadline" and result["applied"] is False
    assert rows(cache) == original
