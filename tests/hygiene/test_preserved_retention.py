"""C-2428 defect classes, using disposable preservation trees only."""

from __future__ import annotations

import errno
import hashlib
import json
import os
from datetime import UTC, datetime, timedelta

import pytest

from scripts.hygiene import preserved_retention as retention


@pytest.fixture
def batch(tmp_path):
    root = tmp_path / "batch_state"
    (root / "preserved").mkdir(parents=True)
    (root / "tasks").mkdir()
    (root / "preserved-keep.txt").write_text("")
    return root


def make_entry(batch, name="old-task", *, days=4, status="done", bundle="evidence-example", **fields):
    entry = batch / "preserved" / name
    (entry / bundle).mkdir(parents=True)
    (entry / bundle / "report.txt").write_text("evidence\n")
    manifest = {
        "schema": "runtime-evidence.v1",
        "task_id": name,
        "run_nonce": "run-one",
        "location": f"batch_state/preserved/{name}/{bundle}",
        "preserved_at": (datetime.now(UTC) - timedelta(days=days)).isoformat(),
        **fields,
    }
    (entry / f"{bundle}.manifest.json").write_text(json.dumps(manifest))
    (batch / "tasks" / f"{name}.json").write_text(json.dumps({"task_id": name, "status": status, "run_nonce": "run-one"}))
    return entry


def invoke(batch, *, apply=True, **options):
    args = ["--batch-root", str(batch)]
    if apply:
        args.append("--apply")
    for key, value in options.items():
        if value is True:
            args.append("--" + key.replace("_", "-"))
        elif value is not False:
            args.extend(["--" + key.replace("_", "-"), str(value)])
    code = retention.main(args)
    files = sorted((batch / "reports").glob("*.jsonl"))
    rows = [json.loads(line) for line in files[-1].read_text().splitlines()] if files else []
    return code, rows


def test_old_valid_manifest_deletes_direct_child(batch):
    entry = make_entry(batch)
    code, rows = invoke(batch)
    assert code == 0
    assert not entry.exists()
    assert rows[0]["result"] == "deleted"


def test_inherited_old_mtime_never_overrides_fresh_manifest(batch):
    entry = make_entry(batch, days=1)
    old = (datetime.now(UTC) - timedelta(days=30)).timestamp()
    for path in [*entry.rglob("*"), entry]:
        os.utime(path, (old, old))
    code, rows = invoke(batch)
    assert code == 0
    assert entry.exists()
    assert rows[0]["result"] == "skipped:fresh"


@pytest.mark.parametrize("contents", [None, "{broken", "[]", '"scalar"', '\ufffd'])
def test_missing_or_corrupt_manifest_is_skipped(batch, contents):
    entry = make_entry(batch)
    manifest = entry / "evidence-example.manifest.json"
    if contents is None:
        manifest.unlink()
    else:
        manifest.write_text(contents)
    code, rows = invoke(batch)
    assert code == 0
    assert entry.exists()
    assert rows[0]["result"].startswith("skipped:")


@pytest.mark.parametrize("status", ["running", "spawning", "unknown", None])
def test_live_or_uncertain_task_state_is_skipped(batch, status):
    entry = make_entry(batch, status=status)
    code, rows = invoke(batch)
    assert code == 0
    assert entry.exists()
    assert rows[0]["result"] == "skipped:task_state"


@pytest.mark.parametrize("contents", [None, "bad-json", "[]"])
def test_missing_or_corrupt_task_record_is_skipped(batch, contents):
    entry = make_entry(batch)
    task = batch / "tasks" / f"{entry.name}.json"
    if contents is None:
        task.unlink()
    else:
        task.write_text(contents)
    code, rows = invoke(batch)
    assert code == 0
    assert entry.exists()
    assert rows[0]["result"].startswith("skipped:task_")


def test_keep_list_entry_is_kept(batch):
    entry = make_entry(batch)
    custom = batch / "custom-keep.txt"
    custom.write_text(entry.name + "\n")
    code, rows = invoke(batch, keep_list=custom)
    assert code == 0
    assert entry.exists()
    assert rows[0]["result"] == "skipped:keep_list"


def test_unreadable_manifest_never_authorizes_deletion(batch, monkeypatch):
    entry = make_entry(batch)
    original = retention.read_at

    def deny_manifest(parent, name):
        if name.endswith(".manifest.json"):
            raise PermissionError(errno.EACCES, "denied")
        return original(parent, name)

    monkeypatch.setattr(retention, "read_at", deny_manifest)
    code, rows = invoke(batch)
    assert code == 0
    assert entry.exists()
    assert rows[0]["result"] == "skipped:manifest_unreadable"


def test_unreadable_keep_list_prevents_all_deletion(batch, monkeypatch):
    first = make_entry(batch, "a")
    second = make_entry(batch, "b")
    original = retention.read_text

    def deny_keep_list(path):
        if path.name == "preserved-keep.txt":
            raise PermissionError(errno.EACCES, "denied")
        return original(path)

    monkeypatch.setattr(retention, "read_text", deny_keep_list)
    code, rows = invoke(batch)
    assert code == 1
    assert first.exists() and second.exists()
    assert [r["result"] for r in rows] == ["skipped:keep_list_unreadable"] * 2


@pytest.mark.parametrize("kind", ["entry", "directory", "file", "manifest", "task"])
def test_symlinks_are_never_traversed_and_targets_survive(batch, tmp_path, kind):
    outside = tmp_path / "outside"
    outside.mkdir()
    sentinel = outside / "sentinel"
    sentinel.write_text("untouched")
    entry = make_entry(batch)
    if kind == "entry":
        (batch / "preserved" / "linked").symlink_to(outside, target_is_directory=True)
    elif kind in {"file", "directory"}:
        (entry / "evidence-example" / "link").symlink_to(outside if kind == "directory" else sentinel)
    else:
        path = entry / "evidence-example.manifest.json" if kind == "manifest" else batch / "tasks" / f"{entry.name}.json"
        target = outside / "record.json"
        target.write_bytes(path.read_bytes())
        path.unlink()
        path.symlink_to(target)
    code, rows = invoke(batch)
    assert code == 0
    assert sentinel.read_text() == "untouched"
    if kind == "entry":
        assert (batch / "preserved" / "linked").is_symlink()
        assert next(r for r in rows if r["name"] == "linked")["result"] == "skipped:symlink"
    else:
        assert entry.exists()
        assert rows[0]["result"].startswith("skipped:")


def test_dry_run_never_deletes_and_receipts_have_lstat_sizes(batch):
    entries = [make_entry(batch, "first"), make_entry(batch, "second")]
    sizes = {p.name: sum(node.lstat().st_size for node in [p, *p.rglob("*")]) for p in entries}
    code, rows = invoke(batch, apply=False)
    assert code == 0
    assert all(p.exists() for p in entries)
    assert rows == [{"name": name, "bytes": size, "result": "skipped:dry_run"} for name, size in sizes.items()]


@pytest.mark.parametrize("stamp", [None, "2020-01-01T00:00:00", "bad-date", 1, False])
def test_missing_or_uncertain_preservation_timestamp_is_kept(batch, stamp):
    entry = make_entry(batch, preserved_at=stamp)
    code, rows = invoke(batch)
    assert code == 0
    assert entry.exists()
    assert rows[0]["result"].startswith("skipped:")


def test_latest_manifest_controls_whole_entry_age(batch):
    entry = make_entry(batch)
    data = json.loads((entry / "evidence-example.manifest.json").read_text())
    data["preserved_at"] = datetime.now(UTC).isoformat()
    (entry / "new.manifest.json").write_text(json.dumps(data))
    code, rows = invoke(batch)
    assert code == 0
    assert entry.exists()
    assert rows[0]["result"] == "skipped:fresh"


@pytest.mark.parametrize("released", [False, True])
def test_held_manifest_cannot_self_release_without_nonce_and_digest_proof(batch, released):
    fields = {"retention_disposition": "released"} if released else {}
    entry = make_entry(batch, bundle="held-example", schema="runtime-held-work.v1", **fields)
    code, rows = invoke(batch)
    assert code == 0
    assert entry.exists()
    assert rows[0]["result"] == "skipped:held"


@pytest.mark.parametrize("pin", [{"keep_worktree": True}, {"preserved_artifacts": {"retention_disposition": "retained"}}])
def test_unresolved_task_pin_is_kept(batch, pin):
    entry = make_entry(batch)
    path = batch / "tasks" / f"{entry.name}.json"
    path.write_text(json.dumps({"task_id": entry.name, "status": "done", **pin}))
    code, rows = invoke(batch)
    assert code == 0
    assert entry.exists()
    assert rows[0]["result"] == "skipped:pin"


def test_deletion_errno_is_receipted(batch, monkeypatch):
    entry = make_entry(batch)

    def refuse(*args, **kwargs):
        raise OSError(errno.EACCES, "denied")

    monkeypatch.setattr(retention, "_remove_invocation_dir", refuse)
    code, rows = invoke(batch)
    assert code == 1
    assert entry.exists()
    assert rows[0]["result"] == "error:13"


def test_partial_deletion_containment_failure_is_an_error(batch, monkeypatch):
    entry = make_entry(batch)
    payload = entry / "evidence-example" / "report.txt"

    def partial(*args, **kwargs):
        payload.unlink()
        raise retention.ContainmentError("directory changed before rmdir")

    monkeypatch.setattr(retention, "_remove_invocation_dir", partial)
    code, rows = invoke(batch)
    assert code == 1
    assert entry.exists() and not payload.exists()
    assert rows[0]["result"] == "error:5"


@pytest.mark.parametrize("defect", [None, "flag_only", "no_proof", "no_release", "nonce", "task_nonce", "release_nonce", "owner", "digest", "manifest_digest", "location", "paths", "bytes", "schema", "other_bundle"])
def test_released_task_pin_must_match_manifest_run(batch, defect):
    entry = make_entry(batch, retention_disposition="retained")
    manifest = entry / "evidence-example.manifest.json"
    record = json.loads(manifest.read_text())
    file_hash = hashlib.sha256(b"evidence\n").hexdigest()
    digest = hashlib.sha256(json.dumps([("report.txt", 9, file_hash)]).encode()).hexdigest()
    record.update(
        schema="worktree-preserved-artifacts.v1", content_sha256=digest,
        retrieval_proof_sha256=digest,
        paths=[{"path": "report.txt", "size": 9, "sha256": file_hash}],
    )
    manifest.write_text(json.dumps(record))
    pin = dict(record, retention_disposition="released", retention_release={
        "owner": entry.name, "run_nonce": "run-one", "retrieval_proof_sha256": digest,
    })
    if defect == "flag_only":
        pin = {"retention_disposition": "released", "run_nonce": "run-one"}
    elif defect == "no_proof":
        del pin["retrieval_proof_sha256"]
    elif defect == "no_release":
        del pin["retention_release"]
    elif defect == "nonce":
        pin["run_nonce"] = "other-run"
    elif defect in {"release_nonce", "owner", "digest"}:
        key = {"release_nonce": "run_nonce", "owner": "owner", "digest": "retrieval_proof_sha256"}[defect]
        pin["retention_release"][key] = "mismatch"
    elif defect == "manifest_digest":
        record["retrieval_proof_sha256"] = "b" * 64
        manifest.write_text(json.dumps(record))
    elif defect == "location":
        pin["location"] = "batch_state/preserved/other/evidence-example"
    elif defect == "paths":
        pin["paths"] = []
    elif defect == "bytes":
        (entry / "evidence-example" / "report.txt").write_text("changed\n")
    elif defect in {"schema", "other_bundle"}:
        if defect == "schema":
            record["schema"] = "unknown.v1"
        else:
            other = make_entry(batch, name="other-task")
            record["location"] = f"batch_state/preserved/{other.name}/evidence-example"
        pin.update({key: record[key] for key in ("schema", "location")})
        manifest.write_text(json.dumps(record))
    task = {
        "task_id": entry.name,
        "status": "done",
        "run_nonce": "other-run" if defect == "task_nonce" else "run-one",
        "preserved_artifacts": pin,
    }
    (batch / "tasks" / f"{entry.name}.json").write_text(json.dumps(task))
    code, rows = invoke(batch)
    assert code == 0
    assert entry.exists() is (defect is not None)
    assert rows[0]["result"] == ("deleted" if defect is None else "skipped:pin")


def test_released_flag_without_retrieval_proof_can_only_use_strict_release(batch):
    entry = held_task(batch, preserved_artifacts={"retention_disposition": "released", "run_nonce": "run-one"})
    manifest = entry / "held-example.manifest.json"
    record = json.loads(manifest.read_text())
    record.update(retention_disposition="retained", schema="runtime-evidence.v1")
    manifest.rename(entry / "evidence.manifest.json")
    (entry / "evidence.manifest.json").write_text(json.dumps(record))
    (entry / "held-example").rename(entry / "evidence")
    code, rows = invoke(batch)
    assert code == 0 and not entry.exists()
    assert rows[0]["reason"] == "released:read_only"


def archive_task(batch, entry):
    hot = batch / "tasks" / f"{entry.name}.json"
    archive = batch / "tasks" / "archive"
    archive.mkdir()
    return hot.rename(archive / hot.name)


@pytest.mark.parametrize("apply", [False, True])
def test_archive_only_terminal_task_makes_old_preserved_entry_eligible_read_only(batch, apply):
    entry = make_entry(batch)
    archived = archive_task(batch, entry)
    before = archived.read_bytes(), archived.stat().st_mtime_ns
    code, rows = invoke(batch, apply=apply)
    assert code == 0
    assert entry.exists() is not apply
    assert rows[0]["result"] == ("deleted" if apply else "skipped:dry_run")
    assert (archived.read_bytes(), archived.stat().st_mtime_ns) == before


@pytest.mark.parametrize("status", ["running", "spawning", "unknown", None])
def test_archive_only_nonterminal_task_keeps_preserved_entry(batch, status):
    entry = make_entry(batch, status=status)
    archive_task(batch, entry)
    code, rows = invoke(batch)
    assert code == 0
    assert entry.exists()
    assert rows[0]["result"] == "skipped:task_state"


@pytest.mark.parametrize("contents", ["bad-json", "[]", '{"task_id":"other","status":"done","run_nonce":"run-one"}'])
def test_archive_only_invalid_or_identity_mismatched_task_keeps_preserved_entry(batch, contents):
    entry = make_entry(batch)
    archived = archive_task(batch, entry)
    archived.write_text(contents)
    code, rows = invoke(batch)
    assert code == 0
    assert entry.exists()
    assert rows[0]["result"] == ("skipped:task_unreadable" if contents == "bad-json" else "skipped:task_state")
    assert archived.read_text() == contents


def test_archive_only_unreadable_task_keeps_preserved_entry(batch, monkeypatch):
    entry = make_entry(batch)
    archived = archive_task(batch, entry)
    original = retention.read_text

    def deny_archive(path):
        if path == archived:
            raise PermissionError(errno.EACCES, "denied")
        return original(path)

    monkeypatch.setattr(retention, "read_text", deny_archive)
    code, rows = invoke(batch)
    assert code == 0
    assert entry.exists()
    assert rows[0]["result"] == "skipped:task_unreadable"


@pytest.mark.parametrize("nonce", ["other-run", None, ""])
def test_archive_only_nonce_mismatched_or_unknown_task_keeps_preserved_entry(batch, nonce):
    entry = make_entry(batch)
    archived = archive_task(batch, entry)
    archived.write_text(json.dumps({"task_id": entry.name, "status": "done", "run_nonce": nonce}))
    code, rows = invoke(batch)
    assert code == 0
    assert entry.exists()
    assert rows[0]["result"] == "skipped:manifest_identity"


@pytest.mark.parametrize("hot_status,archive_status", [("running", "done"), ("done", "running")])
def test_hot_task_record_wins_over_archived_task(batch, hot_status, archive_status):
    entry = make_entry(batch, status=archive_status)
    archived = archive_task(batch, entry)
    before = archived.read_bytes()
    (batch / "tasks" / f"{entry.name}.json").write_text(json.dumps({"task_id": entry.name, "status": hot_status}))
    code, rows = invoke(batch)
    assert code == 0
    assert entry.exists() is (hot_status != "done")
    assert rows[0]["result"] == ("deleted" if hot_status == "done" else "skipped:task_state")
    assert archived.read_bytes() == before


@pytest.mark.parametrize("contents", ["bad-json", "[]", '{"task_id":"other","status":"done"}'])
def test_invalid_hot_task_never_falls_back_to_terminal_archive(batch, contents):
    entry = make_entry(batch)
    archive_task(batch, entry)
    (batch / "tasks" / f"{entry.name}.json").write_text(contents)
    code, rows = invoke(batch)
    assert code == 0
    assert entry.exists()
    assert rows[0]["result"].startswith("skipped:task_")


@pytest.mark.parametrize("kind", ["directory", "record"])
def test_symlinked_archive_path_is_refused(batch, tmp_path, kind):
    entry = make_entry(batch)
    archived = archive_task(batch, entry)
    target = tmp_path / "target"
    source = archived.parent if kind == "directory" else archived
    source.rename(target)
    source.symlink_to(target, target_is_directory=kind == "directory")
    before = (target / archived.name if kind == "directory" else target).read_bytes()
    code, rows = invoke(batch)
    assert code == 0
    assert entry.exists()
    assert rows[0]["result"] == "skipped:task_unreadable"
    assert (target / archived.name if kind == "directory" else target).read_bytes() == before


def test_symlinked_state_ancestor_refuses_configuration(batch, tmp_path):
    make_entry(batch)
    alias = tmp_path / "alias"
    alias.symlink_to(batch, target_is_directory=True)
    assert retention.main(["--batch-root", str(alias), "--apply"]) == 2
    assert not (batch / "reports").exists()


def test_cli_help_documents_defaults_outputs_and_exit_codes(capsys):
    with pytest.raises(SystemExit) as exc:
        retention.main(["--help"])
    assert exc.value.code == 0
    text = " ".join(capsys.readouterr().out.split())
    assert all(term in text for term in ("DRY-RUN", "Outputs:", "Exit codes:", "--apply", "preserved-keep.txt", "--allow-empty-keep-list", "Explicit paths must be readable", "--apply refuses it unless"))


def held_task(batch, **fields):
    entry = make_entry(batch, bundle="held-example", schema="runtime-held-work.v1", preserved_at=None)
    task = {
        "task_id": entry.name, "status": "done", "run_nonce": "run-one",
        "mode": "read-only", "push_state": "not_applicable",
        "finished_at": (datetime.now(UTC) - timedelta(days=4)).isoformat(),
        "worktree_dirty_on_exit": False, "commits_ahead": 0, **fields,
    }
    (batch / "tasks" / f"{entry.name}.json").write_text(json.dumps(task))
    return entry


@pytest.mark.parametrize("status", ["done", "failed", "timeout", "crashed", "cancelled", "no_deliverable"])
@pytest.mark.parametrize("apply", [False, True])
def test_read_only_terminal_held_bundle_older_than_three_days_is_released(batch, status, apply):
    entry = held_task(batch, status=status)
    code, rows = invoke(batch, apply=apply)
    assert code == 0
    assert entry.exists() is not apply
    assert rows[0]["result"] == ("deleted" if apply else "released:read_only")
    assert rows[0]["reason"] == "released:read_only"


@pytest.mark.parametrize("pin", [{"keep_worktree": True}, {"preserved_artifacts": {"retention_disposition": "retained"}}])
def test_terminal_read_only_pin_uses_finished_at_without_manifest_timestamp(batch, pin):
    entry = held_task(batch, **pin)
    manifest = entry / "held-example.manifest.json"
    record = json.loads(manifest.read_text())
    record["schema"] = "runtime-evidence.v1"
    manifest.rename(entry / "evidence.manifest.json")
    (entry / "evidence.manifest.json").write_text(json.dumps(record))
    (entry / "held-example").rename(entry / "evidence")
    code, rows = invoke(batch)
    assert code == 0 and not entry.exists()
    assert rows[0]["reason"] == "released:read_only"


@pytest.mark.parametrize("fields", [
    {"push_state": "unpushed"}, {"push_state": "unknown"}, {"push_state": None},
    {"worktree_dirty_on_exit": True}, {"run_nonce": "other-run"},
    {"finished_at": datetime.now(UTC).isoformat()}, {"finished_at": None},
    {"finished_at": "2020-01-01T00:00:00"}, {"finished_at": "invalid"},
    {"status": "running"}, {"status": "needs_finalize"}, {"status": "dry_run"},
])
def test_unsafe_push_dirty_nonce_young_or_uncertain_finished_at_held_bundle_is_kept(batch, fields):
    entry = held_task(batch, **fields)
    code, rows = invoke(batch)
    assert code == 0 and entry.exists()
    assert rows[0]["result"].startswith("skipped:")
    assert "reason" not in rows[0]


def test_missing_push_state_held_bundle_is_kept(batch):
    entry = held_task(batch)
    path = batch / "tasks" / f"{entry.name}.json"
    task = json.loads(path.read_text())
    del task["push_state"]
    path.write_text(json.dumps(task))
    code, rows = invoke(batch)
    assert code == 0 and entry.exists()
    assert rows[0]["result"] == "skipped:held"


@pytest.mark.parametrize("field,value", [
    ("commits_ahead", 1), ("commits_ahead", None), ("commits_ahead", "0"),
    ("commits_ahead", False), ("commits_ahead", "missing"),
    ("worktree_dirty_on_exit", "missing"), ("worktree_dirty_on_exit", None),
    ("worktree_dirty_on_exit", 0),
])
def test_read_only_release_requires_zero_commits_and_explicit_clean_flag(batch, field, value):
    entry = held_task(batch)
    path = batch / "tasks" / f"{entry.name}.json"
    task = json.loads(path.read_text())
    if value == "missing":
        del task[field]
    else:
        task[field] = value
    path.write_text(json.dumps(task))
    code, rows = invoke(batch)
    assert code == 0 and entry.exists()
    assert rows[0]["result"] == "skipped:held"
    assert "reason" not in rows[0]


@pytest.mark.parametrize("disposition", [None, "released"])
def test_unknown_held_schema_is_unresolved_even_with_release_proof(batch, disposition):
    entry = held_task(batch)
    manifest = entry / "held-example.manifest.json"
    record = json.loads(manifest.read_text())
    record.update(schema="runtime-held-work.v99", retention_disposition=disposition,
                  preserved_at=(datetime.now(UTC) - timedelta(days=4)).isoformat())
    manifest.write_text(json.dumps(record))
    code, rows = invoke(batch)
    assert code == 0 and entry.exists()
    assert rows[0]["result"] == "skipped:held"


@pytest.mark.parametrize("contents", [None, "invalid"])
def test_absent_or_unreadable_bound_task_never_releases_held_bundle(batch, contents):
    entry = held_task(batch)
    path = batch / "tasks" / f"{entry.name}.json"
    if contents is None:
        path.unlink()
    else:
        path.write_text(contents)
    code, rows = invoke(batch)
    assert code == 0 and entry.exists()
    assert rows[0]["result"] == "skipped:task_unreadable"


def test_archive_only_terminal_read_only_held_bundle_is_released(batch):
    entry = held_task(batch)
    archived = archive_task(batch, entry)
    before = archived.read_bytes(), archived.stat().st_mtime_ns
    code, rows = invoke(batch)
    assert code == 0 and not entry.exists()
    assert rows[0]["reason"] == "released:read_only"
    assert (archived.read_bytes(), archived.stat().st_mtime_ns) == before


def test_symlinked_held_bundle_is_kept_without_following_target(batch, tmp_path):
    entry = held_task(batch)
    outside = tmp_path / "outside"
    (entry / "held-example").rename(outside)
    (entry / "held-example").symlink_to(outside, target_is_directory=True)
    code, rows = invoke(batch)
    assert code == 0 and entry.exists()
    assert (outside / "report.txt").read_text() == "evidence\n"
    assert rows[0]["result"] == "skipped:symlink_or_special"


@pytest.mark.parametrize("branch_field", ["branch", "worktree_branch"])
@pytest.mark.parametrize("state", ["MERGED", "CLOSED", "OPEN", "unavailable", "absent", "malformed", "wrong_branch", "fork"])
def test_pushed_write_task_releases_only_proven_merged_or_closed_pr(batch, monkeypatch, state, branch_field):
    entry = held_task(batch, mode="workspace-write", push_state="pushed", head_sha="a" * 40, remote_head_sha="a" * 40, **{branch_field: "task-branch"})
    retention.landed_reason.cache_clear()
    monkeypatch.setattr(retention.subprocess, "run", lambda *a, **kw: retention.subprocess.CompletedProcess(a, 1))
    monkeypatch.setattr(retention.pr_identity, "resolve_repo_slug", lambda root: "owner/repo")
    monkeypatch.setattr(retention.pr_identity, "probe_open_pr_for_branch", lambda **kw: (None, "unavailable") if state == "unavailable" else (state == "OPEN", None))
    row = {"number": 1, "state": state, "headRefName": "task-branch", "headRefOid": "a" * 40, "isCrossRepository": False}
    if state == "wrong_branch":
        row.update(state="MERGED", headRefName="other")
    if state == "fork":
        row.update(state="MERGED", isCrossRepository=True)
    payload = [] if state == "absent" else [row]
    monkeypatch.setattr(retention.pr_identity, "_run_gh", lambda *a, **kw: retention.subprocess.CompletedProcess(a, 0, "bad-json" if state == "malformed" else json.dumps(payload)))
    try:
        code, rows = invoke(batch)
        released = state in {"MERGED", "CLOSED"}
        assert code == 0 and entry.exists() is not released
        assert rows[0]["result"] == ("deleted" if released else "skipped:held")
        if released:
            assert rows[0]["reason"] == "released:pushed_" + state.lower()
    finally:
        retention.landed_reason.cache_clear()


def test_pushed_head_ancestor_of_origin_main_releases_using_real_local_git(batch, tmp_path, monkeypatch):
    import subprocess

    repo = tmp_path / "repo"
    repo.mkdir()

    def git(*args):
        return subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, timeout=30, check=True).stdout.strip()

    git("init")
    git("-c", "user.name=Test", "-c", "user.email=test@example.com", "commit", "--allow-empty", "-m", "base")
    head = git("rev-parse", "HEAD")
    git("-c", "user.name=Test", "-c", "user.email=test@example.com", "commit", "--allow-empty", "-m", "main")
    git("update-ref", "refs/remotes/origin/main", "HEAD")
    monkeypatch.setattr(retention, "__file__", str(repo / "scripts" / "hygiene" / "preserved_retention.py"))

    def forbid_network(**kwargs):
        pytest.fail("local ancestry must not query PRs")

    monkeypatch.setattr(retention.pr_identity, "probe_open_pr_for_branch", forbid_network)
    entry = held_task(batch, mode="workspace-write", push_state="pushed", head_sha=head, remote_head_sha=head, branch="task-branch")
    retention.landed_reason.cache_clear()
    try:
        code, rows = invoke(batch)
        assert code == 0 and not entry.exists()
        assert rows[0]["reason"] == "released:ancestor_of_main"
    finally:
        retention.landed_reason.cache_clear()


@pytest.mark.parametrize("fields", [
    {"push_state": "unpushed"}, {"push_state": "unknown"}, {"push_state": None},
    {"worktree_dirty_on_exit": True}, {"worktree_dirty_on_exit": None},
    {"remote_head_sha": "b" * 40}, {"head_sha": None},
])
def test_write_held_bundle_with_unsafe_push_dirty_or_head_record_is_kept(batch, monkeypatch, fields):
    data = dict(mode="workspace-write", push_state="pushed", head_sha="a" * 40, remote_head_sha="a" * 40, branch="task-branch")
    data.update(fields)
    entry = held_task(batch, **data)

    def no_proof(*args):
        pytest.fail("unsafe delivery record must not reach landing proof")

    monkeypatch.setattr(retention, "landed_reason", no_proof)
    code, rows = invoke(batch)
    assert code == 0 and entry.exists()
    assert rows[0]["result"] == "skipped:held"


@pytest.mark.parametrize("apply", [False, True])
@pytest.mark.parametrize("allow", [False, True])
def test_explicit_missing_keep_list_refuses_even_with_empty_override(batch, apply, allow, capsys):
    entries = [make_entry(batch, "first"), make_entry(batch, "second")]
    code, rows = invoke(batch, apply=apply, keep_list=batch / "typo.txt", allow_empty_keep_list=allow)
    assert code == 1
    assert all(entry.exists() for entry in entries)
    assert [row["result"] for row in rows] == ["skipped:keep_list_unreadable"] * 2
    assert "explicit path is absent" in capsys.readouterr().err


@pytest.mark.parametrize("apply", [False, True])
@pytest.mark.parametrize("allow", [False, True])
def test_missing_default_keep_list_requires_apply_opt_in(batch, apply, allow, capsys):
    entry = make_entry(batch)
    (batch / "preserved-keep.txt").unlink()
    code, rows = invoke(batch, apply=apply, allow_empty_keep_list=allow)
    refused = apply and not allow
    assert code == int(refused)
    assert entry.exists() is not (apply and allow)
    assert rows[0]["result"] == ("skipped:keep_list_unreadable" if refused else "deleted" if apply else "skipped:dry_run")
    if refused:
        assert "default path is absent; --apply requires --allow-empty-keep-list" in capsys.readouterr().err


@pytest.mark.parametrize("change", ["new_bundle", "manifest_replaced", "manifest_modified"])
def test_changed_child_set_or_manifest_during_landing_probe_prevents_deletion(batch, monkeypatch, change):
    entry = held_task(batch, mode="workspace-write", push_state="pushed", head_sha="a" * 40, remote_head_sha="a" * 40, branch="task-branch")
    manifest = entry / "held-example.manifest.json"

    def landing_probe(*args):
        if change == "new_bundle":
            (entry / "held-new").mkdir()
            (entry / "held-new" / "work.txt").write_text("unclassified work")
        elif change == "manifest_replaced":
            replacement = entry / "replacement"
            replacement.write_bytes(manifest.read_bytes())
            os.utime(replacement, ns=(manifest.stat().st_atime_ns, manifest.stat().st_mtime_ns))
            replacement.replace(manifest)
        else:
            before = manifest.stat()
            os.utime(manifest, ns=(before.st_atime_ns, before.st_mtime_ns + 1_000_000))
        return "pushed_merged"

    monkeypatch.setattr(retention, "landed_reason", landing_probe)
    code, rows = invoke(batch)
    assert code == 0 and entry.exists()
    assert (entry / "held-example" / "report.txt").read_text() == "evidence\n"
    assert rows[0]["result"] == "skipped:changed_during_scan"
    assert "reason" not in rows[0]
    if change == "new_bundle":
        assert (entry / "held-new" / "work.txt").read_text() == "unclassified work"


@pytest.mark.parametrize("state", ["MERGED", "CLOSED"])
@pytest.mark.parametrize("pr_head", [None, "b" * 40])
def test_merged_or_closed_pr_with_missing_or_different_head_keeps_held_bundle(batch, monkeypatch, state, pr_head):
    entry = held_task(batch, mode="workspace-write", push_state="pushed", head_sha="a" * 40, remote_head_sha="a" * 40, branch="task-branch")
    monkeypatch.setattr(retention.subprocess, "run", lambda *a, **kw: retention.subprocess.CompletedProcess(a, 1))
    monkeypatch.setattr(retention.pr_identity, "resolve_repo_slug", lambda root: "owner/repo")
    monkeypatch.setattr(retention.pr_identity, "probe_open_pr_for_branch", lambda **kw: (False, None))
    row = {"number": 1, "state": state, "headRefName": "task-branch", "isCrossRepository": False}
    if pr_head is not None:
        row["headRefOid"] = pr_head
    monkeypatch.setattr(retention.pr_identity, "_run_gh", lambda *a, **kw: retention.subprocess.CompletedProcess(a, 0, json.dumps([row])))
    retention.landed_reason.cache_clear()
    try:
        code, rows = invoke(batch)
        assert code == 0 and entry.exists()
        assert rows[0]["result"] == "skipped:held"
        assert "reason" not in rows[0]
    finally:
        retention.landed_reason.cache_clear()


def test_write_task_with_not_applicable_push_state_cannot_use_read_only_release(batch):
    entry = held_task(batch, mode="workspace-write", push_state="not_applicable")
    code, rows = invoke(batch)
    assert code == 0 and entry.exists()
    assert rows[0]["result"] == "skipped:held"
    assert "reason" not in rows[0]


@pytest.mark.parametrize("bundle", ["held-copy-interrupted", "evidence-copy-interrupted"])
def test_preexisting_unmanifested_copy_keeps_entry_with_other_releasable_manifest(batch, bundle):
    entry = held_task(batch)
    # Simulate a crash after copying, before the writer creates its manifest.
    incomplete = entry / bundle
    incomplete.mkdir()
    (incomplete / "only-copy.txt").write_text("irreplaceable work")
    code, rows = invoke(batch)
    assert code == 0 and entry.exists()
    assert (incomplete / "only-copy.txt").read_text() == "irreplaceable work"
    assert rows[0]["result"] == "skipped:missing_manifest"
    assert "reason" not in rows[0]


@pytest.mark.parametrize("head", ["a" * 39, "a" * 41, "g" * 40, "", "aB" * 20])
def test_invalid_head_sha_keeps_held_bundle_even_when_remote_head_matches(batch, monkeypatch, head):
    entry = held_task(batch, mode="workspace-write", push_state="pushed", head_sha=head, remote_head_sha=head, branch="task-branch")
    monkeypatch.setattr(retention, "landed_reason", lambda *args: "pushed_merged")
    code, rows = invoke(batch)
    assert code == 0 and entry.exists()
    assert rows[0]["result"] == "skipped:held"
    assert "reason" not in rows[0]


@pytest.mark.parametrize("branch", [None, ""])
def test_missing_or_empty_branch_keeps_pushed_held_bundle(batch, monkeypatch, branch):
    entry = held_task(batch, mode="workspace-write", push_state="pushed", head_sha="a" * 40, remote_head_sha="a" * 40, branch=branch)
    monkeypatch.setattr(retention, "landed_reason", lambda *args: "pushed_merged")
    code, rows = invoke(batch)
    assert code == 0 and entry.exists()
    assert rows[0]["result"] == "skipped:held"
    assert "reason" not in rows[0]


@pytest.mark.parametrize("invalid", [
    {"number": None}, {"number": "1"}, {"number": True}, {"number": 0}, {"number": -1},
    {"state": None}, {"state": "UNKNOWN"}, {"state": "OPEN"},
    {"isCrossRepository": True},
], ids=["missing-number", "string-number", "boolean-number", "zero-number", "negative-number",
        "missing-state", "unknown-state", "open-despite-probe", "different-repository"])
def test_invalid_individual_pr_row_keeps_held_bundle_despite_valid_merged_row(batch, monkeypatch, invalid):
    entry = held_task(batch, mode="workspace-write", push_state="pushed", head_sha="a" * 40, remote_head_sha="a" * 40, branch="task-branch")
    monkeypatch.setattr(retention.subprocess, "run", lambda *a, **kw: retention.subprocess.CompletedProcess(a, 1))
    monkeypatch.setattr(retention.pr_identity, "resolve_repo_slug", lambda root: "owner/repo")
    # An OPEN row must be rejected independently of this optimistic probe.
    monkeypatch.setattr(retention.pr_identity, "probe_open_pr_for_branch", lambda **kw: (False, None))
    valid = {"number": 1, "state": "MERGED", "headRefName": "task-branch", "headRefOid": "a" * 40, "isCrossRepository": False}
    bad = {**valid, "number": 2, **invalid}
    bad = {key: value for key, value in bad.items() if value is not None}
    monkeypatch.setattr(retention.pr_identity, "_run_gh", lambda *a, **kw: retention.subprocess.CompletedProcess(a, 0, json.dumps([valid, bad])))
    retention.landed_reason.cache_clear()
    try:
        code, rows = invoke(batch)
        assert code == 0 and entry.exists()
        assert rows[0]["result"] == "skipped:held"
        assert "reason" not in rows[0]
    finally:
        retention.landed_reason.cache_clear()


@pytest.mark.parametrize("line", ["old-task ", "  old-task\t", "\told-task\t"])
def test_keep_list_whitespace_preserves_named_entry(batch, line):
    entry = make_entry(batch)
    (batch / "preserved-keep.txt").write_text("\n  # explanation\n" + line + "\n\t\n")
    code, rows = invoke(batch)
    assert code == 0 and entry.exists()
    assert rows[0]["result"] == "skipped:keep_list"


@pytest.mark.parametrize("prefix", ["", "  "])
def test_keep_list_comment_lines_do_not_pin_matching_entry_names(batch, prefix):
    entry = make_entry(batch, "# comment")
    (batch / "preserved-keep.txt").write_text("\n \t\n" + prefix + entry.name + "\n")
    code, rows = invoke(batch)
    assert code == 0 and not entry.exists()
    assert rows[0]["result"] == "deleted"


@pytest.mark.parametrize("archived", [False, True])
@pytest.mark.parametrize("pin", [
    {"keep_worktree": True},
    {"preserved_artifacts": {"retention_disposition": "retained"}},
])
def test_task_pin_added_during_landing_probe_prevents_removal(batch, monkeypatch, archived, pin):
    entry = held_task(batch, mode="workspace-write", push_state="pushed", head_sha="a" * 40, remote_head_sha="a" * 40, branch="task-branch")
    path = archive_task(batch, entry) if archived else batch / "tasks" / f"{entry.name}.json"

    def landing_probe(*args):
        task = json.loads(path.read_text())
        path.write_text(json.dumps({**task, **pin}))
        return "pushed_merged"

    monkeypatch.setattr(retention, "landed_reason", landing_probe)
    code, rows = invoke(batch)
    assert code == 0 and entry.exists()
    assert (entry / "held-example" / "report.txt").read_text() == "evidence\n"
    assert rows[0]["result"] == "skipped:changed_before_removal"
    assert "reason" not in rows[0]


@pytest.mark.parametrize("kind", ["default", "custom", "absent-default"])
def test_keep_list_pin_added_during_landing_probe_prevents_removal(batch, monkeypatch, kind):
    entry = held_task(batch, mode="workspace-write", push_state="pushed", head_sha="a" * 40, remote_head_sha="a" * 40, branch="task-branch")
    path = batch / ("custom-keep.txt" if kind == "custom" else "preserved-keep.txt")
    if kind == "absent-default":
        path.unlink()
    else:
        path.write_text("")

    def landing_probe(*args):
        path.write_text("\n # newly pinned\n  " + entry.name + " \n")
        return "pushed_merged"

    monkeypatch.setattr(retention, "landed_reason", landing_probe)
    options = {"keep_list": path} if kind == "custom" else {"allow_empty_keep_list": True}
    code, rows = invoke(batch, **options)
    assert code == 0 and entry.exists()
    assert (entry / "held-example" / "report.txt").read_text() == "evidence\n"
    assert rows[0]["result"] == "skipped:changed_before_removal"
    assert "reason" not in rows[0]


@pytest.fixture
def backstop_clock(monkeypatch):
    now = 1_800_000_000 * 10**9
    monkeypatch.setattr(retention.time, "time_ns", lambda: now)
    return now


def age_entry(entry, stamp):
    for path in [*entry.rglob("*"), entry] if entry.is_dir() else [entry]:
        os.utime(path, ns=(stamp, stamp), follow_symlinks=False)


@pytest.mark.parametrize("kind", ["unproven", "held", "pinned", "file"])
def test_backstop_deletes_expired_entries_without_proof_rules(batch, backstop_clock, kind, monkeypatch):
    entry = batch / "preserved" / "residue"
    if kind == "file":
        entry.write_text("residue")
    else:
        entry = make_entry(batch, bundle="held-example" if kind == "held" else "bundle", status="running")
        (batch / "tasks" / f"{entry.name}.json").write_text('{"keep_worktree": true}')
    age_entry(entry, backstop_clock - 25 * 3600 * 10**9)
    monkeypatch.setattr(retention, "eligible", lambda *args: pytest.fail("backstop consulted proof rules"))
    (batch / "preserved-keep.txt").unlink()
    code, rows = invoke(batch, expire_older_than_hours=24, allow_empty_keep_list=True)
    assert code == 0 and not entry.exists()
    assert rows[0]["decision"] == "deleted" and rows[0]["reason"] == "expired"
    assert rows[0]["bytes"] > 0


@pytest.mark.parametrize("offset", [-1, 0, 1])
def test_backstop_never_deletes_entries_newer_than_the_cutoff(batch, backstop_clock, offset):
    entry = make_entry(batch)
    age_entry(entry, backstop_clock - 25 * 3600 * 10**9)
    newest = backstop_clock - 24 * 3600 * 10**9 + offset
    os.utime(entry / "evidence-example" / "report.txt", ns=(newest, newest))
    code, rows = invoke(batch, expire_older_than_hours=24)
    assert code == 0 and entry.exists() == (offset >= 0)
    assert rows[0]["newest_mtime_ns"] == newest
    assert rows[0]["result"] == ("skipped:fresh" if offset >= 0 else "deleted")


def test_backstop_honors_the_keep_list_for_expired_entries(batch, backstop_clock):
    entry = make_entry(batch)
    age_entry(entry, backstop_clock - 25 * 3600 * 10**9)
    (batch / "preserved-keep.txt").write_text(entry.name + "\n")
    code, rows = invoke(batch, expire_older_than_hours=24)
    assert code == 0 and entry.exists() and rows[0]["reason"] == "keep_list"


@pytest.mark.parametrize("direct", [False, True])
def test_backstop_never_follows_symlinks_out_of_preserved(batch, tmp_path, backstop_clock, direct):
    outside = tmp_path / "outside"
    outside.mkdir()
    target = outside / "data.txt"
    target.write_text("untouched")
    entry = batch / "preserved" / "linked"
    if not direct:
        entry.mkdir()
    link = entry if direct else entry / "link"
    link.symlink_to(outside, target_is_directory=True)
    os.utime(link, ns=(0, 0), follow_symlinks=False)
    code, rows = invoke(batch, expire_older_than_hours=24)
    assert code == 0 and link.is_symlink() and target.read_text() == "untouched"
    assert rows[0]["reason"] == ("symlink" if direct else "symlink_or_special")


def test_backstop_skips_an_entry_with_unreadable_age(batch, backstop_clock, monkeypatch):
    entry = make_entry(batch)
    monkeypatch.setattr(retention, "measure", lambda *args, **kwargs: (_ for _ in ()).throw(PermissionError()))
    code, rows = invoke(batch, expire_older_than_hours=24)
    assert code == 0 and entry.exists()
    assert rows[0]["reason"] == "age_unreadable" and rows[0]["newest_mtime_ns"] is None


def test_backstop_dry_run_deletes_nothing_and_writes_receipts(batch, backstop_clock):
    entry = make_entry(batch)
    age_entry(entry, backstop_clock - 25 * 3600 * 10**9)
    code, rows = invoke(batch, apply=False, expire_older_than_hours=24)
    assert code == 0 and entry.exists() and len(rows) == 1
    assert rows[0]["result"] == "skipped:dry_run" and rows[0]["reason"] == "expired"


@pytest.mark.parametrize("invalid", ["0", "-1", "1.5", "text"])
def test_backstop_rejects_invalid_hour_values(batch, invalid):
    with pytest.raises(SystemExit) as error:
        invoke(batch, expire_older_than_hours=invalid)
    assert error.value.code == 2 and not (batch / "reports").exists()


@pytest.mark.parametrize("change", ["keep", "age"])
def test_backstop_rechecks_keep_list_and_age_before_removal(batch, backstop_clock, monkeypatch, change):
    entry = make_entry(batch)
    age_entry(entry, backstop_clock - 25 * 3600 * 10**9)
    original = retention.measure

    def changed_scan(fd, **kwargs):
        result = original(fd, **kwargs)
        if change == "keep":
            (batch / "preserved-keep.txt").write_text(entry.name + "\n")
        else:
            os.utime(entry, ns=(backstop_clock, backstop_clock))
        return result

    monkeypatch.setattr(retention, "measure", changed_scan)
    code, rows = invoke(batch, expire_older_than_hours=24)
    assert code == 0 and entry.exists() and rows[0]["decision"] == "skipped"
