"""C-2428 defect classes, using disposable preservation trees only."""

from __future__ import annotations

import errno
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
def test_unresolved_held_bundle_requires_explicit_manifest_release(batch, released):
    fields = {"retention_disposition": "released"} if released else {}
    entry = make_entry(batch, bundle="held-example", **fields)
    code, rows = invoke(batch)
    assert code == 0
    assert entry.exists() is not released
    assert rows[0]["result"] == ("deleted" if released else "skipped:held")


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


@pytest.mark.parametrize("nonce", ["run-one", "other-run"])
def test_released_task_pin_must_match_manifest_run(batch, nonce):
    entry = make_entry(batch, retention_disposition="retained")
    task = {
        "task_id": entry.name,
        "status": "done",
        "run_nonce": "run-one",
        "preserved_artifacts": {"retention_disposition": "released", "run_nonce": nonce},
    }
    (batch / "tasks" / f"{entry.name}.json").write_text(json.dumps(task))
    code, rows = invoke(batch)
    assert code == 0
    assert entry.exists() is (nonce != "run-one")
    assert rows[0]["result"] == ("deleted" if nonce == "run-one" else "skipped:pin")


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
        "worktree_dirty_on_exit": False, **fields,
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


@pytest.mark.parametrize("state", ["MERGED", "CLOSED", "OPEN", "unavailable", "absent", "malformed", "wrong_branch", "fork"])
def test_pushed_write_task_releases_only_proven_merged_or_closed_pr(batch, monkeypatch, state):
    entry = held_task(batch, mode="workspace-write", push_state="pushed", head_sha="a" * 40, remote_head_sha="a" * 40, branch="task-branch")
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
