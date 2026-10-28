"""Report-only batch_state staleness check (#9737)."""

from __future__ import annotations

import json
import os
import subprocess
import time
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts.hygiene import batch_state_retention as retention
from scripts.hygiene import tmp_sweep

DAY = 86400


def make(root: Path, name: str, age_days: float, *, nested: str = "deep/file") -> Path:
    path = root / name
    leaf = path / nested
    leaf.parent.mkdir(parents=True, exist_ok=True)
    leaf.write_bytes(b"x" * 8192)
    stamp = time.time() - age_days * DAY
    for node in [*sorted(path.rglob("*"), reverse=True), path]:
        os.utime(node, (stamp, stamp), follow_symlinks=False)
    return path


def holds_file(tmp_path: Path, holds: list[dict]) -> Path:
    path = tmp_path / "retention.json"
    path.write_text(json.dumps({"schema": retention.SCHEMA, "holds": holds}))
    return path


@pytest.fixture
def batch(tmp_path):
    root = tmp_path / "batch_state"
    root.mkdir()
    return root


def test_stale_fresh_excluded_and_held(batch, tmp_path):
    make(batch, "old-run", 10)
    make(batch, "busy-run", 10)
    os.utime(batch / "busy-run" / "deep" / "file")  # one recent deep write keeps it fresh
    for name in ("tasks", "preserved", "reports", "branch-archive"):
        make(batch, name, 30)
    make(batch, "codex-atlas", 30, nested="session-20260929-resume/evidence")
    (batch / "loose-file").write_text("not a directory")
    (batch / "linked").symlink_to(batch / "old-run")
    holds = retention.load_holds(
        holds_file(tmp_path, [{"path": "batch_state/codex-atlas/session-20260929-resume/", "reason": "#9250"}])
    )
    before = {node: node.lstat().st_mtime_ns for node in batch.rglob("*")}
    result = retention.report(batch, holds=holds)
    rows = {row["path"]: row for row in result["rows"]}
    assert set(rows) == {"batch_state/old-run/", "batch_state/codex-atlas/"}
    assert rows["batch_state/old-run/"]["status"] == "stale" and rows["batch_state/old-run/"]["bytes"] > 8192
    assert rows["batch_state/codex-atlas/"]["status"] == "held"
    assert rows["batch_state/codex-atlas/"]["holds"] == [
        {"path": "batch_state/codex-atlas/session-20260929-resume/", "reason": "#9250"}
    ]
    assert result["counts"] == {"excluded": 4, "fresh": 1, "held": 1, "stale": 1, "unknown": 0}
    assert result["stale_bytes"] == rows["batch_state/old-run/"]["bytes"]
    # Report only: nothing created, removed or modified.
    assert {node: node.lstat().st_mtime_ns for node in batch.rglob("*")} == before


def test_symlinks_and_mounts_are_not_followed(batch, tmp_path, monkeypatch):
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "fresh").write_text("new")
    run = make(batch, "run", 10)
    (run / "link").symlink_to(outside, target_is_directory=True)
    os.utime(run / "link", (time.time() - 10 * DAY,) * 2, follow_symlinks=False)
    os.utime(run, (time.time() - 10 * DAY,) * 2)
    assert retention.report(batch, holds=[])["rows"][0]["status"] == "stale"
    monkeypatch.setattr(retention, "mount_points", lambda: frozenset({str(run / "deep")}))
    row = retention.report(batch, holds=[])["rows"][0]
    assert row["status"] == "unknown" and row["reason"] == "mount_point"
    monkeypatch.setattr(retention, "mount_points", lambda: None)
    assert retention.report(batch, holds=[])["rows"][0]["reason"] == "mount_probe_unknown"


@pytest.mark.parametrize(
    "payload",
    [
        "not json",
        {"schema": "other", "holds": []},
        {"schema": retention.SCHEMA, "holds": {}},
        {"schema": retention.SCHEMA, "holds": [{"path": "batch_state/x/"}]},
        {"schema": retention.SCHEMA, "holds": [{"path": "/abs/batch_state/x", "reason": "r"}]},
        {"schema": retention.SCHEMA, "holds": [{"path": "batch_state/../x", "reason": "r"}]},
        {"schema": retention.SCHEMA, "holds": [{"path": "batch_state", "reason": "r"}]},
    ],
)
def test_malformed_retention_list_refused(tmp_path, payload):
    path = tmp_path / "retention.json"
    path.write_text(payload if isinstance(payload, str) else json.dumps(payload))
    with pytest.raises(retention.RetentionListError):
        retention.load_holds(path)


def test_seeded_retention_list_is_valid():
    holds = retention.load_holds(retention.RETENTION_LIST)
    assert ("codex-atlas", "session-20260929-resume") in {hold["parts"] for hold in holds}


def test_cli_json_table_and_errors(batch, tmp_path, capsys):
    make(batch, "old-run", 10)
    argv = ["--batch-root", str(batch), "--retention-list", str(holds_file(tmp_path, []))]
    assert retention.main([*argv, "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["counts"]["stale"] == 1
    assert retention.main(argv) == 0
    out = capsys.readouterr().out
    assert "| batch_state/old-run/ | stale |" in out and str(tmp_path) not in out
    with pytest.raises(SystemExit) as exc:
        retention.main(["--batch-root", str(batch), "--retention-list", str(tmp_path / "missing.json")])
    assert exc.value.code == 2


@pytest.fixture
def expiry_box(tmp_path, monkeypatch, isolated_state_home):
    """Real batch-state scratch, Git index, task record and quarantine; only host probes are isolated."""
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q", str(repo)], check=True, timeout=30)
    root = repo / "batch_state"
    root.mkdir()
    tasks = root / "tasks"
    tasks.mkdir()
    task = tasks / "settled-owner.json"
    task.write_text(json.dumps({"task_id": "settled-owner", "status": "done", "finished_at": "2020-01-01T00:00:00Z"}))
    entry = make(root, "arbitrary-scratch-name", 10)
    clock = SimpleNamespace(now=time.time() + 10 * DAY)
    metadata = {"schema": "batch-state-scratch.v1", "owner": "settled-owner", "purpose": "disposable probe",
                "delete_after": datetime.fromtimestamp(clock.now - DAY, UTC).isoformat()}
    marker = entry / ".scratch-expiry.json"
    marker.write_text(json.dumps(metadata))
    holds = holds_file(tmp_path, [])
    monkeypatch.setattr(retention, "RETENTION_LIST", holds)
    monkeypatch.setattr(tmp_sweep, "time", SimpleNamespace(time=lambda: clock.now))
    monkeypatch.setattr(tmp_sweep, "process_snapshot", lambda: ([], True))
    monkeypatch.setattr(tmp_sweep, "registered_worktrees", lambda _: set())
    monkeypatch.setattr(tmp_sweep, "protected_roots", lambda: set())

    def run(apply=False):
        return tmp_sweep.sweep(temp_root=root, repo_root=repo, task_root=tasks, batch_state=True, apply=apply)

    return SimpleNamespace(repo=repo, root=root, entry=entry, task=task, clock=clock, metadata=metadata,
                           marker=marker, holds=holds, run=run)


def test_expired_scratch_is_recoverable_then_purged_without_name_inference(expiry_box):
    b = expiry_box
    dry = b.run()
    row = next(row for row in dry["rows"] if row["name"] == b.entry.name)
    assert row["decision"] == "would_reap" and row["task"] == "settled-owner"
    assert b.entry.is_dir()
    applied = b.run(True)
    assert applied["quarantined_entries"] == 1
    assert not b.entry.exists()
    quarantine = next(b.root.glob(tmp_sweep.QUARANTINE_PREFIX + "*")) / b.entry.name
    assert (quarantine / "deep/file").read_bytes() == b"x" * 8192
    b.clock.now += 8 * DAY
    assert b.run()["purgeable_entries"] == 1 and quarantine.is_dir()
    purged = b.run(True)
    assert purged["purged_entries"] == 1 and purged["errors"] == 0
    assert not quarantine.exists()


@pytest.mark.parametrize("case", ["missing", "malformed", "naive_time", "future", "missing_owner", "empty_purpose",
                                  "active_task", "unknown_task", "bad_finish", "held", "tracked", "git", "process",
                                  "unknown_process", "unknown_inventory", "mount", "metadata_link", "reused"])
def test_expiry_never_releases_unknown_live_held_or_tracked_state(expiry_box, monkeypatch, case):
    b = expiry_box
    if case in {"missing", "malformed", "metadata_link"}:
        b.marker.unlink()
        if case == "malformed":
            b.marker.write_text("not-json")
        elif case == "metadata_link":
            b.marker.symlink_to(b.task)
    elif case in {"naive_time", "future", "missing_owner", "empty_purpose"}:
        b.metadata.update({"naive_time": {"delete_after": "2020-01-01T00:00:00"},
                           "future": {"delete_after": "2099-01-01T00:00:00Z"},
                           "missing_owner": {"owner": "nonexistent"}, "empty_purpose": {"purpose": ""}}[case])
        b.marker.write_text(json.dumps(b.metadata))
    elif case in {"active_task", "bad_finish"}:
        record = json.loads(b.task.read_text())
        record.update({"active_task": {"status": "running"}, "bad_finish": {"finished_at": None}}[case])
        b.task.write_text(json.dumps(record))
    elif case == "unknown_task":
        b.task.unlink()
    elif case == "unknown_inventory":
        (b.task.parent / "broken.json").write_text("invalid")
    elif case == "held":
        b.holds.write_text(json.dumps({"schema": retention.SCHEMA,
                                      "holds": [{"path": f"batch_state/{b.entry.name}/deep/file", "reason": "evidence"}]}))
    elif case == "tracked":
        subprocess.run(["git", "-C", str(b.repo), "add", "batch_state"], check=True, timeout=30)
    elif case == "git":
        (b.entry / ".git").write_text("gitdir: elsewhere")
    elif case in {"process", "unknown_process"}:
        monkeypatch.setattr(tmp_sweep, "process_snapshot", lambda: ([(42, b.entry)] if case == "process" else [],
                                                                   case != "unknown_process"))
    elif case == "mount":
        monkeypatch.setattr(tmp_sweep, "mount_points", lambda: frozenset({str(b.entry / "deep")}))
    elif case == "reused":
        b.metadata["delete_after"] = datetime.fromtimestamp(time.time() - DAY, UTC).isoformat()
        b.marker.write_text(json.dumps(b.metadata))
    result = b.run(True)
    row = next(row for row in result["rows"] if row["name"] == b.entry.name)
    assert row["decision"] == "preserve", row
    assert (b.entry / "deep/file").read_bytes() == b"x" * 8192
    assert not list(b.root.glob(tmp_sweep.QUARANTINE_PREFIX + "*"))


@pytest.mark.parametrize("change", ["hold", "task", "expiry", "tracked"])
def test_quarantine_rechecks_new_holds_task_state_metadata_and_tracked_files(expiry_box, change):
    b = expiry_box
    assert b.run(True)["quarantined_entries"] == 1
    b.clock.now += 8 * DAY
    location = next(b.root.glob(tmp_sweep.QUARANTINE_PREFIX + "*")) / b.entry.name
    if change == "hold":
        b.holds.write_text(json.dumps({"schema": retention.SCHEMA,
                                      "holds": [{"path": f"batch_state/{b.entry.name}/deep", "reason": "new hold"}]}))
    elif change == "task":
        record = json.loads(b.task.read_text())
        record["status"] = "running"
        b.task.write_text(json.dumps(record))
    elif change == "expiry":
        (location / ".scratch-expiry.json").write_text("{}")
    else:
        # Index entry can outlive its working file; protection is checked against the original path.
        blob = subprocess.run(["git", "-C", str(b.repo), "hash-object", "-w", "--stdin"], input=b"kept", capture_output=True,
                              check=True, timeout=30).stdout.decode().strip()
        subprocess.run(["git", "-C", str(b.repo), "update-index", "--add", "--cacheinfo",
                        f"100644,{blob},batch_state/{b.entry.name}/deep/file"], check=True, timeout=30)
    result = b.run(True)
    assert result["purged_entries"] == 0
    assert (location / "deep/file").read_bytes() == b"x" * 8192


def test_writer_defaults_to_seven_days_without_overwriting_metadata(batch):
    entry = batch / "scratch"
    entry.mkdir()
    before = datetime.now(UTC).timestamp() + 7 * DAY
    retention.write_scratch_expiry(entry, owner="canonical-task", purpose="probe")
    after = datetime.now(UTC).timestamp() + 7 * DAY
    metadata = json.loads((entry / retention.EXPIRY_FILE).read_text())
    assert metadata["owner"] == "canonical-task" and metadata["purpose"] == "probe"
    assert before <= datetime.fromisoformat(metadata["delete_after"]).timestamp() <= after
    with pytest.raises(FileExistsError):
        retention.write_scratch_expiry(entry, owner="other-task", purpose="different")
    assert json.loads((entry / retention.EXPIRY_FILE).read_text()) == metadata


def test_missing_metadata_does_not_release_a_name_matched_terminal_task(expiry_box):
    b = expiry_box
    b.marker.unlink()
    named = b.entry.with_name("settled-owner-output")
    b.entry.rename(named)
    row = next(row for row in b.run(True)["rows"] if row["name"] == named.name)
    assert row["decision"] == "preserve"
    assert (named / "deep/file").exists()


def test_hard_exclusions_and_quarantine_are_not_staleness_candidates(expiry_box):
    b = expiry_box
    # A misplaced marker must not opt a live machinery directory in.
    (b.root / "tasks" / retention.EXPIRY_FILE).write_text(json.dumps(b.metadata))
    row = next(row for row in b.run(True)["rows"] if row["name"] == "tasks")
    assert row["decision"] == "preserve" and row["reason"] == "expiry_excluded"
    b.clock.now += 20 * DAY
    result = retention.report(b.root, holds=[], now=b.clock.now)
    assert all(not row["path"].split("/")[1].startswith(tmp_sweep.QUARANTINE_PREFIX) for row in result["rows"])


def test_unreadable_holds_refuse_batch_mutation(expiry_box):
    b = expiry_box
    b.holds.write_text("invalid")
    with pytest.raises(retention.RetentionListError):
        b.run(True)
    assert b.entry.is_dir() and not list(b.root.glob(tmp_sweep.QUARANTINE_PREFIX + "*"))


def test_batch_cli_rejects_generic_temp_modes(capsys):
    for extra in (["--temp-root", "batch_state"], ["--unattributed-scratch"]):
        with pytest.raises(SystemExit) as exc:
            tmp_sweep.main(["--batch-state", *extra])
        assert exc.value.code == 2
        assert "cannot be combined" in capsys.readouterr().err


def test_batch_root_cannot_be_replaced_by_an_arbitrary_or_symlinked_root(expiry_box):
    b = expiry_box
    with pytest.raises(ValueError):
        tmp_sweep.sweep(temp_root=b.entry, repo_root=b.repo, task_root=b.task.parent, batch_state=True, apply=True)
    alias = b.repo / "alias"
    alias.symlink_to(b.root, target_is_directory=True)
    with pytest.raises(ValueError):
        tmp_sweep.sweep(temp_root=alias, repo_root=b.repo, task_root=b.task.parent, batch_state=True, apply=True)
    assert (b.entry / "deep/file").exists()


def test_new_hold_during_quarantine_rename_restores_scratch(expiry_box, monkeypatch):
    b = expiry_box
    rename = tmp_sweep.rename_noreplace

    def racing_rename(src_fd, src, dst_fd, dst):
        rename(src_fd, src, dst_fd, dst)
        b.holds.write_text(json.dumps({"schema": retention.SCHEMA,
                                      "holds": [{"path": f"batch_state/{b.entry.name}", "reason": "racing hold"}]}))

    monkeypatch.setattr(tmp_sweep, "rename_noreplace", racing_rename)
    result = b.run(True)
    assert result["quarantined_entries"] == 0
    assert (b.entry / "deep/file").read_bytes() == b"x" * 8192


def test_temp_pass_cannot_purge_batch_quarantine_or_run_pytest_twice(expiry_box, monkeypatch):
    from scripts.hygiene import pytest_retention

    b = expiry_box
    monkeypatch.setattr(pytest_retention, "sweep_pytest_runs", lambda **kw: pytest.fail("batch mode ran pytest cleanup"))
    assert b.run(True)["quarantined_entries"] == 1
    b.clock.now += 8 * DAY
    location = next(b.root.glob(tmp_sweep.QUARANTINE_PREFIX + "*")) / b.entry.name
    temp = b.repo / "temp"
    temp.mkdir()
    monkeypatch.setattr(pytest_retention, "sweep_pytest_runs", lambda **kw: {"rows": [], "errors": 0})
    monkeypatch.setattr(tmp_sweep, "SYSTEM_TEMP_AREAS", (temp,))
    result = tmp_sweep.sweep(temp_root=temp, task_root=b.task.parent, repo_root=b.repo, apply=True)
    assert result["purged_entries"] == 0 and (location / "deep/file").exists()
