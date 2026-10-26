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
    (batch / "tasks" / f"{name}.json").write_text(json.dumps({"task_id": name, "status": status}))
    return entry


def invoke(batch, *, apply=True, **options):
    args = ["--batch-root", str(batch)]
    if apply:
        args.append("--apply")
    for key, value in options.items():
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


def test_archived_record_cannot_override_missing_required_hot_task_record(batch):
    entry = make_entry(batch)
    hot = batch / "tasks" / f"{entry.name}.json"
    archive = batch / "tasks" / "archive"
    archive.mkdir()
    hot.rename(archive / hot.name)
    code, rows = invoke(batch)
    assert code == 0
    assert entry.exists()
    assert rows[0]["result"] == "skipped:task_unreadable"


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
    text = capsys.readouterr().out
    assert all(term in text for term in ("DRY-RUN", "Outputs:", "Exit codes:", "--apply", "preserved-keep.txt"))
