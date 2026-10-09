"""Real Git fixtures for the approved first slice of #10227."""
from __future__ import annotations

import io
import json
import os
import stat
import subprocess
import urllib.request

import pytest

from scripts import delegate
from scripts.fleet import ignored_task_output
from scripts.orchestration import reap_worktrees, worktree_artifacts, worktree_claims


def git(root, *args):
    return subprocess.run(["git", *args], cwd=root, check=True, capture_output=True, text=True, timeout=30).stdout.strip()


@pytest.fixture
def holder(tmp_path, monkeypatch):
    primary = tmp_path / "repo"
    primary.mkdir()
    git(primary, "init", "-b", "main")
    git(primary, "config", "user.name", "Release Test")
    git(primary, "config", "user.email", "release@example.invalid")
    (primary / ".gitignore").write_text(".worktrees/\nbatch_state/\nignored/\nnode_modules\n")
    (primary / "source.txt").write_text("tracked\n")
    git(primary, "add", ".")
    git(primary, "commit", "-m", "base")
    remote = tmp_path / "remote.git"
    git(primary, "init", "--bare", str(remote))
    git(primary, "remote", "add", "origin", str(remote))
    branch = "codex/finished"
    path = primary / ".worktrees" / "dispatch" / "codex" / "finished"
    git(primary, "worktree", "add", "-b", branch, str(path))
    git(path, "push", "-u", "origin", branch)
    tasks = primary / "batch_state" / "tasks"
    tasks.mkdir(parents=True)
    record = tasks / "finished.json"
    record.write_text(json.dumps({
        "task_id": "finished", "run_nonce": "attempt-1", "status": "done", "pid": None,
        "worktree_path": str(path), "worktree_branch": branch, "worktree_reused": False,
    }))
    monkeypatch.setattr(delegate, "_REPO_ROOT", primary)
    monkeypatch.setattr(delegate, "tasks_dir", lambda: tasks)
    monkeypatch.setattr(delegate, "_branch_holder_active_task_ids", lambda: set(), raising=False)
    monkeypatch.setattr(reap_worktrees, "_live_cwd_paths", lambda _repo: set())
    monkeypatch.setattr(reap_worktrees, "_open_file_activity_reason", lambda _path: None)
    return primary, path, branch, record


def release(holder):
    _, path, branch, _ = holder
    return delegate._release_stale_branch_holders(branch=branch, holders=[path], dry_run=False)


def snapshot(path):
    entries = []
    for file in path.rglob("*"):
        info = file.lstat()
        entries.append((str(file.relative_to(path)), info.st_mode, info.st_ino, info.st_nlink,
                        file.read_bytes() if stat.S_ISREG(info.st_mode) else None))
    return sorted(entries)


@pytest.mark.parametrize("names", [
    ["source.txt.orig", "fix.patch"], ["pytest_out.txt"],
    ["source.txt.orig", "ignored/log.txt"], ["dir/a\nwith space.patch"],
])
def test_archives_all_bytes_and_releases_exact_branch(holder, names, capsys):
    primary, path, branch, record = holder
    expected = {}
    for i, name in enumerate(names):
        file = path / name
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_bytes(b"" if i else b"scratch\x00bytes\n")
        expected[name] = file.read_bytes()
    assert release(holder) == [path]
    assert not path.exists()
    receipt = json.loads(record.read_text())["branch_holder_archive"]
    assert receipt["count"] == len(names)
    assert {e["path"] for e in receipt["paths"]} == set(names)
    assert ignored_task_output.verify_retrieval(primary, receipt) == receipt["retrieval_proof_sha256"]
    for name, payload in expected.items():
        assert (primary / receipt["location"] / name).read_bytes() == payload
    assert (primary / receipt["manifest_path"]).is_file()
    output = capsys.readouterr().err
    for key in ("manifest_path", "content_sha256", "retrieval_proof_sha256"):
        assert receipt[key] in output
    # The caller can actually attach the same branch, without another name.
    git(primary, "worktree", "add", str(primary / ".worktrees" / "next"), branch)


@pytest.mark.parametrize("kind,reason", [
    ("tracked", "tracked_modification"), ("assume_unchanged", "tracked_modification"), ("skip_worktree", "tracked_modification"), ("unpushed", "live_remote_tip_unknown_or_mismatch"),
    ("symlink", "not_regular_file"), ("hardlink", "hard_link"),
    ("nested", "nested_repository"), ("unknown", "non_allowlisted_untracked"),
    ("orphan_orig", "non_allowlisted_untracked"), ("stale_tip", "live_remote_tip_unknown_or_mismatch"),
    ("failed_probe", "active-task probe unavailable"), ("missing_tasks", "active-task probe unavailable"),
    ("cwd_unknown", "process-CWD activity probe unavailable"), ("open_unknown", "open-file activity probe unavailable"),
    ("active", "active dispatch"), ("open_live", "live process has open"),
    ("submodule", "submodule"), ("special", "not_regular_file"),
    ("ignored_link", "not_regular_file"), ("ignored_hardlink", "hard_link"),
    ("cap", "file_size_cap"), ("missing_owner", "scratch_owner_unknown"),
    ("ambiguous_owner", "scratch_owner_ambiguous"), ("running", "task still active"),
])
def test_refusal_keeps_every_source(holder, monkeypatch, kind, reason, capsys):
    primary, path, branch, record = holder
    scratch = path / "pytest_out.txt"
    scratch.write_text("keep these bytes")
    if kind in {"tracked", "assume_unchanged", "skip_worktree"}:
        (path / "source.txt").write_text("uncommitted")
        if kind != "tracked":
            git(path, "update-index", "--" + kind.replace("_", "-"), "source.txt")
    elif kind == "unpushed":
        (path / "source.txt").write_text("commit")
        git(path, "add", "source.txt")
        git(path, "commit", "-m", "unpushed")
    elif kind == "symlink":
        (path / "link.patch").symlink_to("source.txt")
    elif kind == "hardlink":
        os.link(scratch, path / "other.patch")
    elif kind == "nested":
        git(path, "init", "nested")
        (path / "nested" / "nested.patch").write_text("nested work")
    elif kind in {"unknown", "orphan_orig"}:
        (path / ("unique.txt" if kind == "unknown" else "missing.orig")).write_text("unique")
    elif kind == "stale_tip":
        # Change the remote without updating this repository's tracking ref.
        git(primary, "update-ref", "refs/heads/new-tip", git(primary, "commit-tree", "HEAD^{tree}", "-p", "HEAD", "-m", "new remote"))
        git(primary, "push", "origin", f"new-tip:refs/heads/{branch}")
        git(path, "update-ref", f"refs/remotes/origin/{branch}", git(path, "rev-parse", "HEAD"))
    elif kind in {"failed_probe", "missing_tasks"}:
        monkeypatch.setattr(delegate, "_branch_holder_active_task_ids", lambda: None)
    elif kind == "cwd_unknown":
        monkeypatch.setattr(reap_worktrees, "_live_cwd_paths", lambda _repo: None)
    elif kind in {"open_unknown", "open_live"}:
        monkeypatch.setattr(reap_worktrees, "_open_file_activity_reason", lambda _path: reason)
    elif kind == "active":
        monkeypatch.setattr(delegate, "_branch_holder_active_task_ids", lambda: {"finished"})
    elif kind == "submodule":
        git(path, "update-index", "--add", "--cacheinfo", f"160000,{git(path, 'rev-parse', 'HEAD')},sub")
        git(path, "commit", "-m", "gitlink")
        git(path, "push", "origin", branch)
    elif kind == "special":
        os.mkfifo(path / "pipe.patch")
    elif kind.startswith("ignored_"):
        (path / "ignored").mkdir()
        if kind == "ignored_link":
            (path / "ignored" / "link").symlink_to("../source.txt")
        else:
            os.link(scratch, path / "ignored" / "link")
    elif kind == "cap":
        monkeypatch.setattr("scripts.fleet.regenerable_output.MAX_BRANCH_HOLDER_FILE_BYTES", 1)
    elif kind == "missing_owner":
        record.unlink()
    elif kind == "ambiguous_owner":
        second = json.loads(record.read_text())
        second["task_id"] = "other"
        (record.parent / "other.json").write_text(json.dumps(second))
    elif kind == "running":
        data = json.loads(record.read_text())
        data["status"] = "running"
        record.write_text(json.dumps(data))
    # Do not read FIFO fixtures; preserve names, metadata and all regular bytes.
    before = snapshot(path)
    assert release(holder) == []
    assert path.exists() and scratch.read_text() == "keep these bytes"
    assert snapshot(path) == before
    assert reason in capsys.readouterr().err


@pytest.mark.parametrize("failure", ["partial_copy", "receipt", "race_new", "race_bytes", "race_head", "race_branch", "race_claim", "race_liveness", "corrupt_archive", "keep", "total_cap"])
def test_archive_and_final_recheck_failures_delete_nothing(holder, monkeypatch, failure, capsys):
    primary, path, _branch, record = holder
    (path / "pytest_out.txt").write_text("first")
    (path / "second.patch").write_text("second")
    before = {"pytest_out.txt": b"first", "second.patch": b"second"}
    copy = worktree_artifacts._copy_verified
    calls = 0

    def copying(source, destination, **kwargs):
        nonlocal calls
        calls += 1
        if failure == "partial_copy" and calls == 2:
            raise OSError("injected copy failure")
        copy(source, destination, **kwargs)
    monkeypatch.setattr(worktree_artifacts, "_copy_verified", copying)
    if failure == "receipt":
        monkeypatch.setattr(worktree_artifacts.reaper_lifecycle, "_atomic_write", lambda *_a: (_ for _ in ()).throw(OSError("receipt failed")))
    elif failure == "keep":
        data = json.loads(record.read_text())
        data["keep_worktree"] = True
        record.write_text(json.dumps(data))
    elif failure == "total_cap":
        monkeypatch.setattr(ignored_task_output, "MAX_PRESERVED_BYTES", 8)
    else:
        unlink = worktree_artifacts.unlink_archived_regular_files
        def before_delete(root, entries, *, recheck):
            if failure == "race_new":
                (root / "new.patch").write_text("appeared")
            elif failure == "race_bytes":
                (root / "second.patch").write_text("changed")
                before["second.patch"] = b"changed"
            elif failure == "race_head":
                git(root, "commit", "--allow-empty", "-m", "raced head")
            elif failure == "race_branch":
                git(root, "switch", "-c", "other-owner")
            elif failure == "race_claim":
                (record.parent / "reader.json").write_text(json.dumps({"task_id": "reader", "status": "running", "worktree_path": str(root)}))
            elif failure == "race_liveness":
                monkeypatch.setattr(delegate, "_branch_holder_active_task_ids", lambda: None)
            elif failure == "corrupt_archive":
                receipt = json.loads(record.read_text())["branch_holder_archive"]
                (primary / receipt["location"] / "second.patch").write_text("corrupt")
            unlink(root, entries, recheck=recheck)
        monkeypatch.setattr(worktree_artifacts, "unlink_archived_regular_files", before_delete)
    assert release(holder) == []
    assert path.exists()
    assert {name: (path / name).read_bytes() for name in before} == before
    output = capsys.readouterr().err
    assert "artifact preservation failed" in output or "scratch_release_refused" in output
    if failure.startswith("race_") or failure == "corrupt_archive":
        receipt = json.loads(record.read_text())["branch_holder_archive"]
        for key in ("manifest_path", "content_sha256", "retrieval_proof_sha256"):
            assert receipt[key] in output


@pytest.mark.parametrize("payload", [{}, {"tasks": None}, {"tasks": [{}]}, {"tasks": []}])
def test_strict_api_response_requires_tasks_list(monkeypatch, payload):
    monkeypatch.setattr(urllib.request, "urlopen", lambda *_a, **_k: io.BytesIO(json.dumps(payload).encode()))
    assert delegate._branch_holder_active_task_ids() == (set() if payload == {"tasks": []} else None)


def test_dry_run_never_archives_or_unlinks(holder):
    primary, path, branch, record = holder
    (path / "pytest_out.txt").write_text("scratch")
    assert delegate._release_stale_branch_holders(branch=branch, holders=[path], dry_run=True) == [path]
    assert (path / "pytest_out.txt").read_text() == "scratch"
    assert "branch_holder_archive" not in json.loads(record.read_text())
    assert not (primary / "batch_state" / "preserved").exists()


def test_inventory_refuses_escaped_components(holder):
    primary, path, _, _ = holder
    with pytest.raises(ValueError, match="outside"):
        worktree_artifacts.unlink_archived_regular_files(path, [{"path": "../escape.patch"}], recheck=lambda: None)
    from scripts.fleet.regenerable_output import branch_holder_scratch_inventory

    assert branch_holder_scratch_inventory(path, primary=primary)["paths"] == []


def test_final_proof_and_non_force_removal_hold_attachment_lock(holder, monkeypatch):
    _, path, _branch, _ = holder
    (path / "pytest_out.txt").write_text("scratch")
    proof = delegate._stale_branch_holder_releasable
    seen = []
    def under_lock(*args):
        assert worktree_claims.existing_worktree_lock_refusal(path, lock_dir=delegate._worktree_lock_dir()) is not None
        seen.append("proof")
        return proof(*args)
    monkeypatch.setattr(delegate, "_stale_branch_holder_releasable", under_lock)
    remove = worktree_claims.git_worktree_remove
    def removing(*args, **kwargs):
        assert kwargs["force"] is False
        seen.append("remove")
        return remove(*args, **kwargs)
    monkeypatch.setattr(worktree_claims, "git_worktree_remove", removing)
    assert release(holder) == [path]
    assert seen == ["proof", "proof", "remove"]


@pytest.mark.parametrize("race", ["replacement", "bytes", "symlink", "restore_failure", "restore_conflict", "receipt_failure"])
def test_final_stat_rename_race_refuses_and_preserves_replacement(holder, monkeypatch, tmp_path, capsys, race):
    """#10227: replacement after the last source stat must never be unlinked."""
    primary, path, _branch, record = holder
    (path / "pytest_out.txt").write_bytes(b"first")
    (path / "second.patch").write_bytes(b"archived")
    replacement = tmp_path / "replacement"
    if race == "symlink":
        replacement.symlink_to("source.txt")
    else:
        replacement.write_bytes(b"replacement")
    unlink = worktree_artifacts.unlink_archived_regular_files
    real_stat, real_link, real_rename = os.stat, os.link, os.rename
    armed = False
    injected = False

    def raced_stat(name, *args, **kwargs):
        nonlocal injected
        info = real_stat(name, *args, **kwargs)
        if armed and not injected and name == "second.patch" and kwargs.get("dir_fd") is not None:
            injected = True
            if race == "bytes":
                (path / "second.patch").write_bytes(b"replaced")
                os.utime(path / "second.patch", ns=(info.st_atime_ns, info.st_mtime_ns))
            else:
                real_rename(replacement, path / "second.patch")
        return info

    def restore_link(source, destination, **kwargs):
        if str(source).startswith(".release-") and destination == "second.patch":
            if race in {"restore_failure", "receipt_failure"}:
                raise OSError("injected restore failure")
            if race == "restore_conflict":
                (path / "second.patch").write_bytes(b"new arrival")
        return real_link(source, destination, **kwargs)

    def before_delete(root, entries, *, recheck):
        def checked():
            nonlocal armed
            recheck()
            armed = True
        with monkeypatch.context() as patch:
            patch.setattr(os, "stat", raced_stat)
            patch.setattr(os, "link", restore_link)
            unlink(root, entries, recheck=checked)

    monkeypatch.setattr(worktree_artifacts, "unlink_archived_regular_files", before_delete)
    if race == "receipt_failure":
        def failed_receipt(*_args, **_kwargs):
            raise OSError("injected receipt failure")
        monkeypatch.setattr(ignored_task_output, "_update_bound_task_record", failed_receipt)
    assert release(holder) == []
    assert injected and path.exists()
    assert (path / "pytest_out.txt").read_bytes() == b"first"
    output = capsys.readouterr().err
    saved = json.loads(record.read_text())
    assert (primary / saved["branch_holder_archive"]["location"] / "second.patch").read_bytes() == b"archived"
    if race in {"restore_failure", "restore_conflict", "receipt_failure"}:
        if race == "receipt_failure":
            assert '"receipt_recorded": false' in output
            private = next(path.glob(".release-*"))
            receipt = {"kind": "source_restore_failed", "paths": [{"source": "second.patch", "private": private.name}]}
        else:
            receipt = saved["branch_holder_release_refusal"]
        assert receipt["kind"] == "source_restore_failed"
        assert len(receipt["paths"]) == 1
        names = receipt["paths"][0]
        assert names["source"] == "second.patch"
        assert names["private"].startswith(".release-")
        assert (path / names["private"]).read_bytes() == b"replacement"
        assert all(names[key] in output for key in ("source", "private"))
        if race == "restore_conflict":
            assert (path / "second.patch").read_bytes() == b"new arrival"
    elif race == "symlink":
        assert (path / "second.patch").is_symlink()
        assert os.readlink(path / "second.patch") == "source.txt"
        assert "source_changed" in output
        assert not list(path.glob(".release-*"))
    else:
        assert (path / "second.patch").read_bytes() == (b"replaced" if race == "bytes" else b"replacement")
        assert "source_changed" in output
        assert not list(path.glob(".release-*"))


def test_ignored_output_is_archived_once_with_scratch(holder, monkeypatch):
    primary, path, _branch, record = holder
    (path / "pytest_out.txt").write_bytes(b"scratch")
    (path / "ignored").mkdir()
    (path / "ignored/log.txt").write_bytes(b"ignored")
    copy = worktree_artifacts._copy_verified
    copied = []
    preserve = ignored_task_output.preserve_worktree_artifacts
    extras = []

    def preserving(*args, **kwargs):
        if "extra_files" in kwargs:
            extras.append(kwargs["extra_files"])
        return preserve(*args, **kwargs)

    def copying(source, destination, **kwargs):
        copied.append(source.relative_to(path).as_posix())
        return copy(source, destination, **kwargs)

    monkeypatch.setattr(worktree_artifacts, "_copy_verified", copying)
    monkeypatch.setattr(ignored_task_output, "preserve_worktree_artifacts", preserving)
    assert release(holder) == [path]
    assert copied.count("ignored/log.txt") == 1
    assert extras == [["pytest_out.txt"]]
    saved = json.loads(record.read_text())
    assert saved["preserved_artifacts"] == saved["branch_holder_archive"]
    assert len(list((primary / "batch_state/preserved/finished").glob("*.manifest.json"))) == 1



def test_staging_failure_restores_every_source_before_refusing(holder, monkeypatch, capsys):
    _primary, path, _branch, _record = holder
    (path / "pytest_out.txt").write_bytes(b"first")
    (path / "second.patch").write_bytes(b"second")
    rename = os.rename

    def failed_rename(source, destination, **kwargs):
        if source == "second.patch" and str(destination).startswith(".release-"):
            raise OSError("injected staging failure")
        return rename(source, destination, **kwargs)

    monkeypatch.setattr(os, "rename", failed_rename)
    assert release(holder) == []
    assert (path / "pytest_out.txt").read_bytes() == b"first"
    assert (path / "second.patch").read_bytes() == b"second"
    assert not list(path.glob(".release-*"))
    assert "scratch_release_refused" in capsys.readouterr().err



def test_generated_output_exempt_from_archive_is_not_explicitly_unlinked(holder, monkeypatch):
    primary, path, _branch, record = holder
    (primary / ".git/info/exclude").write_text("site/dist/\n")
    generated = path / "site/dist/page.html"
    generated.parent.mkdir(parents=True)
    generated.write_bytes(b"regenerable")
    (path / "pytest_out.txt").write_bytes(b"scratch")
    unlink = worktree_artifacts.unlink_archived_regular_files
    seen = []

    def unlinking(root, entries, *, recheck):
        seen.extend(entry["path"] for entry in entries)
        return unlink(root, entries, recheck=recheck)

    monkeypatch.setattr(worktree_artifacts, "unlink_archived_regular_files", unlinking)
    assert release(holder) == [path]
    assert seen == ["pytest_out.txt"]
    saved = json.loads(record.read_text())
    assert saved["branch_holder_archive"]["count"] == 1
    assert saved["preserved_artifacts"] == saved["branch_holder_archive"]
