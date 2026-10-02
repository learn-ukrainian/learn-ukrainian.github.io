"""Byte preservation and fail-closed removal guards for #9449."""

from __future__ import annotations

import json
import os
import subprocess
import threading
from pathlib import Path

import pytest

from scripts.orchestration import worktree_artifacts as wa
from tests import _worktree_artifact_links as links


@pytest.fixture
def checkout(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    subprocess.run(["git", "init", str(repo)], check=True, capture_output=True, env=env, timeout=30)
    (repo / ".gitignore").write_text("batch_state/\nignored/\n.pytest_cache/\n__pycache__/\n")
    # The helper only needs an index; this fixture does not commit or remove anything.
    subprocess.run(["git", "add", ".gitignore"], cwd=repo, check=True, env=env, timeout=30)
    primary = tmp_path / "primary"
    primary.mkdir()
    tasks = primary / "batch_state/tasks"
    tasks.mkdir(parents=True)
    return repo, primary, tasks


def guard(checkout, *, task_id="artifact-task", record=None):
    repo, primary, tasks = checkout
    return wa.preserve_worktree_artifacts(repo, primary=primary, task_id=task_id, tasks_dir=tasks, task_record=record)


def artifact(checkout, name="batch_state/sub/report.bin", payload=b"proof\x00\xff"):
    path = checkout[0] / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)
    return path


def test_preserved_bytes_record_and_idempotency(checkout):
    source = artifact(checkout)
    record = {"status": "done", "response": "Capture `batch_state/sub/report.bin`."}
    (checkout[2] / "artifact-task.json").write_text(json.dumps(record))
    ok, reason, metadata = guard(checkout, record=record)
    assert ok and not reason
    assert metadata["count"] == 1
    copy = Path(metadata["location"]) / "batch_state/sub/report.bin"
    assert copy.read_bytes() == source.read_bytes()
    assert wa._fingerprint(copy) == wa._fingerprint(source)
    saved = json.loads((checkout[2] / "artifact-task.json").read_text())
    assert saved["preserved_artifacts"] == record["preserved_artifacts"] == metadata
    assert guard(checkout)[0]  # Repeated guard retains verified existing bytes.


def test_empty_files_dirs_and_pycache_do_not_need_identity(checkout):
    artifact(checkout, payload=b"")
    artifact(checkout, "batch_state/__pycache__/worker.pyc")
    (checkout[0] / "batch_state/empty").mkdir()
    assert guard(checkout, task_id=None) == (True, "", None)
    assert not (checkout[1] / "batch_state/preserved").exists()


@pytest.mark.parametrize("task_id", [None, "../escape", "..", "bad/id"])
def test_missing_or_unsafe_identity_blocks_copy(checkout, task_id):
    source = artifact(checkout)
    ok, reason, _ = guard(checkout, task_id=task_id)
    assert not ok and "safe task identity" in reason
    assert source.exists()


@pytest.mark.parametrize("failure", ["copy", "corruption", "record"])
def test_failed_copy_verification_or_record_blocks_removal(checkout, monkeypatch, failure):
    source = artifact(checkout)
    (checkout[2] / "artifact-task.json").write_text(json.dumps({"status": "done"}))
    if failure == "copy":

        def fail_copy(*_args):
            raise OSError("copy denied")

        monkeypatch.setattr(wa.shutil, "copyfile", fail_copy)
    elif failure == "corruption":
        monkeypatch.setattr(wa.shutil, "copyfile", lambda _source, destination: destination.write_bytes(b"wrong"))
    else:

        def fail_record(*_args):
            raise OSError("record denied")

        monkeypatch.setattr(wa.reaper_lifecycle, "_atomic_write", fail_record)
    ok, reason, _ = guard(checkout)
    assert not ok and "artifact preservation failed" in reason
    assert source.read_bytes() == b"proof\x00\xff"
    assert not list((checkout[1] / "batch_state/preserved").rglob(".preserve-*"))


def test_different_existing_copy_is_never_overwritten(checkout):
    artifact(checkout)
    destination = checkout[1] / "batch_state/preserved/artifact-task/batch_state/sub/report.bin"
    destination.parent.mkdir(parents=True)
    destination.write_bytes(b"previous evidence")
    ok, reason, _ = guard(checkout)
    assert not ok and "different bytes" in reason
    assert destination.read_bytes() == b"previous evidence"


@pytest.mark.parametrize("destination", [False, True])
def test_symlink_paths_block_preservation(checkout, destination):
    source = artifact(checkout)
    elsewhere = checkout[1] / "elsewhere"
    elsewhere.mkdir()
    if destination:
        (checkout[1] / "batch_state/preserved").symlink_to(elsewhere, target_is_directory=True)
    else:
        source.unlink()
        source.symlink_to(checkout[0] / ".gitignore")
    ok, reason, _ = guard(checkout)
    assert not ok and ("symlink" in reason or "regular file" in reason)
    assert not list(elsewhere.iterdir())


def test_primary_task_sidecar_is_not_copied(checkout):
    shared = checkout[2] / "artifact-task.result"
    shared.write_bytes(b"already durable")
    source = artifact(checkout)
    source.unlink()
    source.symlink_to(shared)
    assert guard(checkout) == (True, "", None)
    assert shared.read_bytes() == b"already durable"


@pytest.mark.parametrize(
    "reference",
    [
        "`ignored/a report.txt`",
        "[report](ignored/a report.txt)",
        "'ignored/a report.txt'",
        "`ignored/a report.txt:12`",
        "`batch_state/../ignored/a report.txt`",
    ],
)
def test_named_ignored_artifact_outside_batch_state_preserved(checkout, reference):
    source = artifact(checkout, "ignored/a report.txt")
    ok, _reason, metadata = guard(checkout, record={"response": f"Capture {reference}."})
    assert ok
    assert metadata["count"] == 1
    assert (Path(metadata["location"]) / "ignored/a report.txt").read_bytes() == source.read_bytes()


def test_result_sidecar_is_read_and_tracked_named_files_are_safe(checkout):
    sidecar = checkout[2] / "artifact-task.result"
    sidecar.write_text("Capture `ignored/note.txt`. Read `.gitignore`.")
    source = artifact(checkout, "ignored/note.txt")
    ok, _reason, metadata = guard(checkout, record={"result_file": str(sidecar)})
    assert ok
    assert (Path(metadata["location"]) / "ignored/note.txt").read_bytes() == source.read_bytes()
    source.unlink()
    assert guard(checkout, record={"result_file": str(sidecar)})[0]


def test_unreadable_inventory_retains_artifact(checkout, monkeypatch):
    source = artifact(checkout)

    def fail_inventory(*_args):
        raise subprocess.CalledProcessError(128, "git ls-files")

    monkeypatch.setattr(wa, "_git_paths", fail_inventory)
    assert not guard(checkout)[0]
    assert source.exists()


def test_malformed_task_record_is_not_overwritten(checkout):
    path = checkout[2] / "artifact-task.json"
    path.write_text("broken JSON")
    assert not guard(checkout)[0]
    assert path.read_text() == "broken JSON"


def test_batch_state_symlink_cannot_hide_local_artifacts(checkout):
    source = artifact(checkout, "ignored/hidden.txt")
    (checkout[0] / "batch_state").symlink_to(source.parent, target_is_directory=True)
    ok, reason, _ = guard(checkout)
    assert not ok and "batch_state is a symlink" in reason
    assert source.exists()


def test_batch_state_link_loop_is_a_recorded_refusal(checkout):
    (checkout[2] / "artifact-task.json").write_text(json.dumps({"status": "done"}))
    (checkout[0] / "batch_state").mkdir()
    (checkout[0] / "batch_state/loop").symlink_to("loop")
    ok, reason, metadata = guard(checkout)
    assert not ok and "Symlink loop" in reason and metadata is None
    assert reason == json.loads((checkout[2] / "artifact-task.json").read_text())["artifact_preservation_error"]


@pytest.mark.parametrize(
    ("reference", "refused"),
    [
        ("../outside.txt", False),
        ("absolute", False),
        ("ignored/sub/../../link", True),
        ("ignored/dir/../../link", True),
    ],
)
def test_outbound_refusal_needs_a_link_inside_the_checkout(checkout, tmp_path, reference, refused):
    outside = tmp_path / "outside.txt"
    outside.write_bytes(b"lives outside the checkout")
    (checkout[0] / "ignored/sub").mkdir(parents=True)
    (checkout[0] / "ignored/dir").symlink_to("sub", target_is_directory=True)
    (checkout[0] / "link").symlink_to(outside)
    reference = str(outside) if reference == "absolute" else reference
    ok, reason, metadata = guard(checkout, record={"response": f"Read `{reference}`."})
    assert (ok, metadata) == (not refused, None)
    assert (links.REFUSAL in reason) is refused
    assert outside.read_bytes() == b"lives outside the checkout"


@pytest.mark.parametrize("reference", ["root", "./", "ignored", ".pytest_cache/cache.txt"])
def test_named_directory_or_cache_does_not_block(checkout, reference):
    artifact(checkout, "ignored/report.txt")
    cache = artifact(checkout, ".pytest_cache/cache.txt")
    reference = str(checkout[0]) if reference == "root" else reference
    assert guard(checkout, record={"response": f"Worked in `{reference}`."}) == (True, "", None)
    assert cache.exists()


def test_record_changed_during_copy_keeps_other_writers_fields(checkout, monkeypatch):
    artifact(checkout)
    path = checkout[2] / "artifact-task.json"
    path.write_text(json.dumps({"status": "done", "response": "original"}))
    copy = wa.shutil.copyfile

    def concurrent_writer(source, destination):
        from scripts.orchestration.dead_worker_state import task_state_lock

        with task_state_lock(path):
            path.write_text(json.dumps({"status": "failed", "response": "new", "other_writer": True}))
        return copy(source, destination)

    monkeypatch.setattr(wa.shutil, "copyfile", concurrent_writer)
    assert guard(checkout, record={"stale_field": "do not merge"})[0]
    saved = json.loads(path.read_text())
    assert saved["status"] == "failed"
    assert saved["response"] == "new"
    assert saved["other_writer"] is True
    assert "stale_field" not in saved
    assert saved["preserved_artifacts"]["count"] == 1


def test_missing_record_is_not_created(checkout):
    source = artifact(checkout)
    ok, reason, metadata = guard(checkout)
    assert ok
    assert "task record missing" in reason
    assert metadata["record_update"] == "skipped_missing_record"
    assert (Path(metadata["location"]) / "batch_state/sub/report.bin").read_bytes() == source.read_bytes()
    assert not (checkout[2] / "artifact-task.json").exists()


def test_named_external_symlink_refuses_removal(checkout, tmp_path):
    target = tmp_path / "outside.txt"
    target.write_bytes(b"lives outside the checkout")
    (checkout[0] / "ignored").mkdir()
    (checkout[0] / "ignored/link.txt").symlink_to(target)
    path = checkout[2] / "artifact-task.json"
    path.write_text(json.dumps({"status": "done"}))
    ok, reason, metadata = guard(checkout, record={"response": "Wrote `ignored/link.txt`."})
    assert not ok and links.REFUSAL in reason and metadata is None
    assert links.REFUSAL in json.loads(path.read_text())["artifact_preservation_error"]
    assert target.read_bytes() == b"lives outside the checkout"
    assert not (checkout[1] / "batch_state/preserved").exists()


@pytest.mark.parametrize("scenario", links.SCENARIOS)
def test_named_symlink_preserves_or_refuses(checkout, tmp_path, scenario):
    repo, primary, tasks = checkout
    outside = tmp_path / "outside"
    named, preserved, target = links.build_named_link(repo, primary, outside, scenario)
    (tasks / "artifact-task.json").write_text(json.dumps({"status": "done"}))
    ok, reason, metadata = guard(checkout, record={"response": links.worker_response(named)})
    links.restore_access(repo)
    saved = json.loads((tasks / "artifact-task.json").read_text())
    assert target is None or target.read_bytes() == links.PAYLOAD
    if scenario in links.REFUSALS:
        assert not ok and links.REFUSALS[scenario] in reason
        assert links.REFUSALS[scenario] in saved["artifact_preservation_error"]
        assert "\x00" not in reason and "x" * 300 not in reason
    elif preserved is None:
        assert (ok, reason, metadata) == (True, "", None)
        assert not (primary / "batch_state/preserved").exists()
        assert "artifact_preservation_error" not in saved
    else:
        assert ok and not reason and metadata["count"] == 1
        assert (Path(metadata["location"]) / preserved).read_bytes() == links.PAYLOAD
        assert saved["preserved_artifacts"] == metadata


def test_record_update_waits_for_the_shared_writer_lock(checkout):
    """Removing ``task_state_lock`` from the update lets it race and lose the other writer's fields."""
    from scripts.orchestration.dead_worker_state import task_state_lock

    path = checkout[2] / "artifact-task.json"
    path.write_text(json.dumps({"status": "running"}))
    held, release = threading.Event(), threading.Event()

    def other_writer():
        # A locked read-modify-write: an unlocked update landing mid-section is overwritten.
        with task_state_lock(path):
            record = json.loads(path.read_text())
            held.set()
            release.wait(10)
            path.write_text(json.dumps({**record, "status": "done", "other_writer": True}))

    holder = threading.Thread(target=other_writer)
    holder.start()
    assert held.wait(10)
    updater = threading.Thread(
        target=wa._update_existing_task_record, args=(path, {"preserved_artifacts": {"count": 1}})
    )
    updater.start()
    updater.join(0.5)
    waited = updater.is_alive()
    release.set()
    holder.join(10)
    updater.join(10)
    assert waited, "update did not wait for the task-record writer lock"
    saved = json.loads(path.read_text())
    assert saved == {"status": "done", "other_writer": True, "preserved_artifacts": {"count": 1}}


def test_success_clears_a_stale_preservation_error(checkout):
    artifact(checkout)
    path = checkout[2] / "artifact-task.json"
    path.write_text(json.dumps({"status": "done", "artifact_preservation_error": "earlier copy failed"}))
    record = {"artifact_preservation_error": "earlier copy failed"}
    assert guard(checkout, record=record)[0]
    assert "artifact_preservation_error" not in json.loads(path.read_text())
    assert "artifact_preservation_error" not in record


_GIT_ENV = {
    **{k: v for k, v in os.environ.items() if not k.startswith("GIT_") and k != "AGENT_NO_MERGE"},
    "GIT_AUTHOR_NAME": "Test Worker",
    "GIT_AUTHOR_EMAIL": "worker@example.com",
    "GIT_COMMITTER_NAME": "Test Worker",
    "GIT_COMMITTER_EMAIL": "worker@example.com",
    "GIT_CONFIG_GLOBAL": "/dev/null",
    "GIT_CONFIG_SYSTEM": "/dev/null",
    "GIT_CONFIG_NOSYSTEM": "1",
}


def test_ignored_artifact_directory_of_regular_files(checkout):
    """Denominator row 2: a directory of regular files has its files discovered and preserved."""
    (checkout[2] / "artifact-task.json").write_text(json.dumps({"status": "done"}))
    f1 = artifact(checkout, "batch_state/reports/probe/report1.json", payload=b'{"metric": 1}')
    f2 = artifact(checkout, "batch_state/reports/probe/report2.json", payload=b'{"metric": 2}')
    (checkout[0] / "batch_state/reports/probe/__pycache__").mkdir(parents=True, exist_ok=True)
    (checkout[0] / "batch_state/reports/probe/__pycache__/cached.pyc").write_bytes(b"disposable")

    ok, reason, metadata = guard(checkout)
    assert ok and not reason
    assert metadata["count"] == 2
    location = Path(metadata["location"])
    assert (location / "batch_state/reports/probe/report1.json").read_bytes() == f1.read_bytes()
    assert (location / "batch_state/reports/probe/report2.json").read_bytes() == f2.read_bytes()
    assert not (location / "batch_state/reports/probe/__pycache__").exists()


def test_ignored_artifact_nested_repo_no_unpushed_commits(checkout, tmp_path):
    """Denominator row 3 & AC-01: nested repo with no unpushed commits refuses removal with actionable command."""
    # Create upstream remote
    upstream = tmp_path / "upstream"
    subprocess.run(["git", "-c", "core.hooksPath=/dev/null", "init", "--bare", str(upstream)], check=True, capture_output=True, env=_GIT_ENV, timeout=30)

    # Clone upstream into batch_state
    scratch_dir = checkout[0] / "batch_state/reports/scratch_repo"
    subprocess.run(["git", "-c", "core.hooksPath=/dev/null", "clone", str(upstream), str(scratch_dir)], check=True, capture_output=True, env=_GIT_ENV, timeout=30)
    # Add and push a commit so there are zero unpushed commits
    (scratch_dir / "probe.txt").write_text("probe output\n")
    subprocess.run(["git", "add", "probe.txt"], cwd=scratch_dir, check=True, env=_GIT_ENV, timeout=30)
    subprocess.run(["git", "commit", "-m", "init probe"], cwd=scratch_dir, check=True, env=_GIT_ENV, timeout=30)
    subprocess.run(["git", "-c", "core.hooksPath=/dev/null", "push", "origin", "HEAD:refs/heads/topic"], cwd=scratch_dir, check=True, capture_output=True, env=_GIT_ENV, timeout=30)
    subprocess.run(["git", "fetch", "origin"], cwd=scratch_dir, check=True, capture_output=True, env=_GIT_ENV, timeout=30)

    ok, reason, metadata = guard(checkout)
    assert not ok and metadata is None
    assert "artifact is a nested git repository with no unpushed commits" in reason
    assert "files" in reason and "bytes" in reason
    assert "batch_state/reports/scratch_repo" in reason
    assert "clear with: rm -rf batch_state/reports/scratch_repo" in reason

    # AC-01: Actionable single command removes the scratch repo and allows worktree release
    import shutil
    shutil.rmtree(scratch_dir)
    ok_after, reason_after, _ = guard(checkout)
    assert ok_after and not reason_after


def test_ignored_artifact_nested_repo_with_unpushed_commits_never_discarded(checkout):
    """Denominator row 4 & AC-02: nested repo with unpushed commits refuses and is never discarded."""
    unpushed_dir = checkout[0] / "batch_state/reports/unpushed_repo"
    unpushed_dir.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", str(unpushed_dir)], check=True, capture_output=True, env=_GIT_ENV, timeout=30)
    (unpushed_dir / "unpushed_work.txt").write_text("valuable local probe data\n")
    subprocess.run(["git", "add", "unpushed_work.txt"], cwd=unpushed_dir, check=True, env=_GIT_ENV, timeout=30)
    subprocess.run(["git", "commit", "-m", "valuable unpushed probe"], cwd=unpushed_dir, check=True, env=_GIT_ENV, timeout=30)

    rev_proc = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=unpushed_dir, check=True, capture_output=True, env=_GIT_ENV, text=True, timeout=30
    )
    commit_sha = rev_proc.stdout.strip()

    ok, reason, metadata = guard(checkout)
    assert not ok and metadata is None
    assert "artifact is a nested git repository with unpushed commits" in reason
    assert "unpushed work must not be discarded" in reason
    assert commit_sha[:7] in reason or commit_sha in reason
    assert "files" in reason and "bytes" in reason

    # AC-02: The unpushed repo and its commits are preserved intact on disk
    assert unpushed_dir.exists()
    assert (unpushed_dir / "unpushed_work.txt").read_text() == "valuable local probe data\n"
    log_proc = subprocess.run(["git", "log", "-1", "--oneline"], cwd=unpushed_dir, check=True, capture_output=True, text=True, env=_GIT_ENV, timeout=30)
    assert "valuable unpushed probe" in log_proc.stdout


def test_ignored_artifact_nested_linked_worktree_pointing_at_another_artifact(checkout):
    """Denominator row 5: nested linked worktree pointing at another artifact refuses removal."""
    primary_repo = checkout[0] / "batch_state/reports/primary_repo"
    primary_repo.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", str(primary_repo)], check=True, capture_output=True, env=_GIT_ENV, timeout=30)
    (primary_repo / "initial.txt").write_text("seed\n")
    subprocess.run(["git", "add", "initial.txt"], cwd=primary_repo, check=True, env=_GIT_ENV, timeout=30)
    subprocess.run(["git", "commit", "-m", "seed"], cwd=primary_repo, check=True, env=_GIT_ENV, timeout=30)

    linked_wt = checkout[0] / "batch_state/reports/linked_wt"
    subprocess.run(
        ["git", "worktree", "add", str(linked_wt), "-b", "wt-branch"],
        cwd=primary_repo,
        check=True,
        capture_output=True,
        env=_GIT_ENV,
        timeout=30,
    )

    ok, reason, metadata = guard(checkout)
    assert not ok and metadata is None
    assert "artifact is a nested linked worktree whose gitdir pointer points at another artifact" in reason
    assert "batch_state/reports/primary_repo" in reason


def test_ignored_artifact_nested_repo_symlink_dot_git(checkout, tmp_path):
    """A directory whose .git is a symlink fails closed."""
    real_git_repo = tmp_path / "real_git_repo"
    subprocess.run(["git", "init", str(real_git_repo)], check=True, capture_output=True, env=_GIT_ENV, timeout=30)
    bad_repo = checkout[0] / "batch_state/reports/bad_repo"
    bad_repo.mkdir(parents=True, exist_ok=True)
    (bad_repo / ".git").symlink_to(real_git_repo / ".git")

    ok, reason, metadata = guard(checkout)
    assert not ok and metadata is None
    assert "artifact has a symlinked .git entry" in reason


def test_ignored_artifact_nested_repo_corrupt_fails_closed(checkout):
    """A nested repo with corrupted git internals fails closed."""
    corrupt_dir = checkout[0] / "batch_state/reports/corrupt_repo"
    subprocess.run(["git", "init", str(corrupt_dir)], check=True, capture_output=True, env=_GIT_ENV, timeout=30)
    (corrupt_dir / ".git/config").write_text("bad config syntax [[[")
    ok, reason, metadata = guard(checkout)
    assert not ok and metadata is None
    assert "artifact is an invalid nested git repository" in reason


def test_ignored_artifact_nested_repo_detached_head_unpushed_never_discarded(checkout):
    """AC-02 & P1: unpushed commits on a detached HEAD must refuse without a cleanup command."""
    detached_dir = checkout[0] / "batch_state/reports/detached_unpushed"
    detached_dir.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "-c", "core.hooksPath=/dev/null", "init", str(detached_dir)], check=True, capture_output=True, env=_GIT_ENV, timeout=30)
    (detached_dir / "unpushed.txt").write_text("detached unpushed data\n")
    subprocess.run(["git", "add", "unpushed.txt"], cwd=detached_dir, check=True, env=_GIT_ENV, timeout=30)
    subprocess.run(["git", "commit", "-m", "detached commit"], cwd=detached_dir, check=True, env=_GIT_ENV, timeout=30)
    subprocess.run(["git", "checkout", "--detach", "HEAD"], cwd=detached_dir, check=True, capture_output=True, env=_GIT_ENV, timeout=30)

    ok, reason, metadata = guard(checkout)
    assert not ok and metadata is None
    assert "artifact is a nested git repository with unpushed commits" in reason
    assert "unpushed work must not be discarded" in reason
    assert "clear with: rm -rf" not in reason


def test_ignored_artifact_nested_repo_shell_quoting_in_cleanup_recommendation(checkout, tmp_path):
    """P1: paths with apostrophes or spaces in cleanup recommendations are safely shell-quoted."""
    upstream = tmp_path / "upstream"
    subprocess.run(["git", "-c", "core.hooksPath=/dev/null", "init", "--bare", str(upstream)], check=True, capture_output=True, env=_GIT_ENV, timeout=30)

    scratch_dir = checkout[0] / "batch_state/reports/probe' 'valuable"
    scratch_dir.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "-c", "core.hooksPath=/dev/null", "clone", str(upstream), str(scratch_dir)], check=True, capture_output=True, env=_GIT_ENV, timeout=30)

    (scratch_dir / "probe.txt").write_text("pushed data\n")
    subprocess.run(["git", "add", "probe.txt"], cwd=scratch_dir, check=True, env=_GIT_ENV, timeout=30)
    subprocess.run(["git", "commit", "-m", "probe"], cwd=scratch_dir, check=True, env=_GIT_ENV, timeout=30)
    subprocess.run(["git", "-c", "core.hooksPath=/dev/null", "push", "origin", "HEAD:refs/heads/topic"], cwd=scratch_dir, check=True, capture_output=True, env=_GIT_ENV, timeout=30)
    subprocess.run(["git", "fetch", "origin"], cwd=scratch_dir, check=True, capture_output=True, env=_GIT_ENV, timeout=30)

    ok, reason, metadata = guard(checkout)
    assert not ok and metadata is None
    assert "artifact is a nested git repository with no unpushed commits" in reason
    assert "clear with: " in reason

    import shlex
    cmd_part = reason.split("clear with: ")[1].split(";")[0].strip()
    tokens = shlex.split(cmd_part)
    assert tokens[:2] == ["rm", "-rf"]
    assert len(tokens) == 3, f"Expected exactly 1 target path, got: {tokens[2:]}"
    assert tokens[2] == "batch_state/reports/probe' 'valuable"


def test_ignored_artifact_nested_repo_unpushed_tag_never_discarded(checkout, tmp_path):
    """P1: unpushed commits referenced only by a local tag refuse removal without recommending deletion."""
    upstream = tmp_path / "upstream"
    subprocess.run(["git", "-c", "core.hooksPath=/dev/null", "init", "--bare", str(upstream)], check=True, capture_output=True, env=_GIT_ENV, timeout=30)

    repo_dir = checkout[0] / "batch_state/reports/tag_repo"
    subprocess.run(["git", "-c", "core.hooksPath=/dev/null", "clone", str(upstream), str(repo_dir)], check=True, capture_output=True, env=_GIT_ENV, timeout=30)
    (repo_dir / "base.txt").write_text("base\n")
    subprocess.run(["git", "add", "base.txt"], cwd=repo_dir, check=True, env=_GIT_ENV, timeout=30)
    subprocess.run(["git", "commit", "-m", "base"], cwd=repo_dir, check=True, env=_GIT_ENV, timeout=30)
    subprocess.run(["git", "-c", "core.hooksPath=/dev/null", "push", "origin", "HEAD:refs/heads/topic"], cwd=repo_dir, check=True, capture_output=True, env=_GIT_ENV, timeout=30)
    subprocess.run(["git", "fetch", "origin"], cwd=repo_dir, check=True, capture_output=True, env=_GIT_ENV, timeout=30)

    # Add commit on tag only, then move branch back to base
    (repo_dir / "tagged.txt").write_text("tagged commit\n")
    subprocess.run(["git", "add", "tagged.txt"], cwd=repo_dir, check=True, env=_GIT_ENV, timeout=30)
    subprocess.run(["git", "commit", "-m", "tagged commit"], cwd=repo_dir, check=True, env=_GIT_ENV, timeout=30)
    subprocess.run(["git", "tag", "v0.9.0"], cwd=repo_dir, check=True, env=_GIT_ENV, timeout=30)
    subprocess.run(["git", "reset", "--hard", "HEAD~1"], cwd=repo_dir, check=True, env=_GIT_ENV, timeout=30)

    ok, reason, metadata = guard(checkout)
    assert not ok and metadata is None
    assert "artifact is a nested git repository with unpushed commits" in reason
    assert "unpushed work must not be discarded" in reason
    assert "clear with: rm -rf" not in reason


def test_ignored_artifact_nested_repo_unpushed_stash_never_discarded(checkout, tmp_path):
    """P1: unpushed commits referenced only by refs/stash refuse removal without recommending deletion."""
    upstream = tmp_path / "upstream"
    subprocess.run(["git", "-c", "core.hooksPath=/dev/null", "init", "--bare", str(upstream)], check=True, capture_output=True, env=_GIT_ENV, timeout=30)

    repo_dir = checkout[0] / "batch_state/reports/stash_repo"
    subprocess.run(["git", "-c", "core.hooksPath=/dev/null", "clone", str(upstream), str(repo_dir)], check=True, capture_output=True, env=_GIT_ENV, timeout=30)
    (repo_dir / "base.txt").write_text("base\n")
    subprocess.run(["git", "add", "base.txt"], cwd=repo_dir, check=True, env=_GIT_ENV, timeout=30)
    subprocess.run(["git", "commit", "-m", "base"], cwd=repo_dir, check=True, env=_GIT_ENV, timeout=30)
    subprocess.run(["git", "-c", "core.hooksPath=/dev/null", "push", "origin", "HEAD:refs/heads/topic"], cwd=repo_dir, check=True, capture_output=True, env=_GIT_ENV, timeout=30)
    subprocess.run(["git", "fetch", "origin"], cwd=repo_dir, check=True, capture_output=True, env=_GIT_ENV, timeout=30)

    # Modify file and stash changes
    (repo_dir / "base.txt").write_text("stashed modification\n")
    subprocess.run(["git", "stash"], cwd=repo_dir, check=True, capture_output=True, env=_GIT_ENV, timeout=30)

    ok, reason, metadata = guard(checkout)
    assert not ok and metadata is None
    assert "artifact is a nested git repository with unpushed commits" in reason
    assert "unpushed work must not be discarded" in reason
    assert "clear with: rm -rf" not in reason


def test_ignored_artifact_nested_repo_dirty_working_tree_never_discarded(checkout, tmp_path):
    """P1: repositories with uncommitted working-tree or index changes refuse removal without recommending deletion."""
    upstream = tmp_path / "upstream"
    subprocess.run(["git", "-c", "core.hooksPath=/dev/null", "init", "--bare", str(upstream)], check=True, capture_output=True, env=_GIT_ENV, timeout=30)

    repo_dir = checkout[0] / "batch_state/reports/dirty_repo"
    subprocess.run(["git", "-c", "core.hooksPath=/dev/null", "clone", str(upstream), str(repo_dir)], check=True, capture_output=True, env=_GIT_ENV, timeout=30)
    (repo_dir / "base.txt").write_text("base\n")
    subprocess.run(["git", "add", "base.txt"], cwd=repo_dir, check=True, env=_GIT_ENV, timeout=30)
    subprocess.run(["git", "commit", "-m", "base"], cwd=repo_dir, check=True, env=_GIT_ENV, timeout=30)
    subprocess.run(["git", "-c", "core.hooksPath=/dev/null", "push", "origin", "HEAD:refs/heads/topic"], cwd=repo_dir, check=True, capture_output=True, env=_GIT_ENV, timeout=30)
    subprocess.run(["git", "fetch", "origin"], cwd=repo_dir, check=True, capture_output=True, env=_GIT_ENV, timeout=30)

    # Modify file without committing
    (repo_dir / "base.txt").write_text("uncommitted dirty changes\n")

    ok, reason, metadata = guard(checkout)
    assert not ok and metadata is None
    assert "artifact is a nested git repository with uncommitted" in reason
    assert "uncommitted work must not be discarded" in reason
    assert "clear with: rm -rf" not in reason


def test_ignored_artifact_nested_repo_fsmonitor_hook_disabled(checkout):
    """P1: nested repository core.fsmonitor hooks must never execute during inspection."""
    repo_dir = checkout[0] / "batch_state/reports/fsmonitor_repo"
    repo_dir.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "-c", "core.hooksPath=/dev/null", "init", str(repo_dir)], check=True, capture_output=True, env=_GIT_ENV, timeout=30)
    marker = repo_dir / "hook_executed.marker"
    hook_script = repo_dir / "fsmonitor_hook.sh"
    hook_script.write_text(f"#!/bin/sh\ntouch '{marker}'\nexit 0\n")
    hook_script.chmod(0o755)
    subprocess.run(["git", "config", "core.fsmonitor", str(hook_script)], cwd=repo_dir, check=True, env=_GIT_ENV, timeout=30)

    guard(checkout)
    assert not marker.exists(), "core.fsmonitor hook script in nested repository was executed!"


def test_ignored_artifact_nested_repo_ignored_evidence_never_discarded(checkout, tmp_path):
    """P1: non-disposable ignored files in a nested repository must never be recommended for deletion."""
    upstream = tmp_path / "upstream"
    subprocess.run(["git", "-c", "core.hooksPath=/dev/null", "init", "--bare", str(upstream)], check=True, capture_output=True, env=_GIT_ENV, timeout=30)

    repo_dir = checkout[0] / "batch_state/reports/ignored_evidence_repo"
    subprocess.run(["git", "-c", "core.hooksPath=/dev/null", "clone", str(upstream), str(repo_dir)], check=True, capture_output=True, env=_GIT_ENV, timeout=30)
    (repo_dir / ".gitignore").write_text("*.json\n")
    subprocess.run(["git", "add", ".gitignore"], cwd=repo_dir, check=True, env=_GIT_ENV, timeout=30)
    subprocess.run(["git", "commit", "-m", "ignore json"], cwd=repo_dir, check=True, env=_GIT_ENV, timeout=30)
    subprocess.run(["git", "-c", "core.hooksPath=/dev/null", "push", "origin", "HEAD:refs/heads/topic"], cwd=repo_dir, check=True, capture_output=True, env=_GIT_ENV, timeout=30)
    subprocess.run(["git", "fetch", "origin"], cwd=repo_dir, check=True, capture_output=True, env=_GIT_ENV, timeout=30)

    # Add ignored evidence file
    (repo_dir / "valuable.json").write_text('{"evidence": "important probe"}')

    ok, reason, metadata = guard(checkout)
    assert not ok and metadata is None
    assert "artifact is a nested git repository with uncommitted or ignored changes" in reason
    assert "uncommitted work must not be discarded" in reason
    assert "clear with: rm -rf" not in reason


def test_ignored_artifact_nested_repo_reflog_only_commits_never_discarded(checkout, tmp_path):
    """P1: unpushed commits referenced only by reflogs must refuse removal without recommending deletion."""
    upstream = tmp_path / "upstream"
    subprocess.run(["git", "-c", "core.hooksPath=/dev/null", "init", "--bare", str(upstream)], check=True, capture_output=True, env=_GIT_ENV, timeout=30)

    repo_dir = checkout[0] / "batch_state/reports/reflog_repo"
    subprocess.run(["git", "-c", "core.hooksPath=/dev/null", "clone", str(upstream), str(repo_dir)], check=True, capture_output=True, env=_GIT_ENV, timeout=30)
    (repo_dir / "base.txt").write_text("base\n")
    subprocess.run(["git", "add", "base.txt"], cwd=repo_dir, check=True, env=_GIT_ENV, timeout=30)
    subprocess.run(["git", "commit", "-m", "base"], cwd=repo_dir, check=True, env=_GIT_ENV, timeout=30)
    subprocess.run(["git", "-c", "core.hooksPath=/dev/null", "push", "origin", "HEAD:refs/heads/topic"], cwd=repo_dir, check=True, capture_output=True, env=_GIT_ENV, timeout=30)
    subprocess.run(["git", "fetch", "origin"], cwd=repo_dir, check=True, capture_output=True, env=_GIT_ENV, timeout=30)

    # Add unpushed commit then reset --hard back to base
    (repo_dir / "reflog_work.txt").write_text("unpushed reflog work\n")
    subprocess.run(["git", "add", "reflog_work.txt"], cwd=repo_dir, check=True, env=_GIT_ENV, timeout=30)
    subprocess.run(["git", "commit", "-m", "unpushed reflog commit"], cwd=repo_dir, check=True, env=_GIT_ENV, timeout=30)
    subprocess.run(["git", "reset", "--hard", "HEAD~1"], cwd=repo_dir, check=True, env=_GIT_ENV, timeout=30)

    ok, reason, metadata = guard(checkout)
    assert not ok and metadata is None
    assert "artifact is a nested git repository with unpushed commits" in reason
    assert "unpushed work must not be discarded" in reason
    assert "clear with: rm -rf" not in reason


def test_ignored_artifact_nested_repo_clean_filter_hook_rejected_without_execution(checkout):
    """P1: nested repository clean filter configuration is rejected before git execution."""
    repo_dir = checkout[0] / "batch_state/reports/clean_filter_repo"
    repo_dir.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "-c", "core.hooksPath=/dev/null", "init", str(repo_dir)], check=True, capture_output=True, env=_GIT_ENV, timeout=30)
    marker = repo_dir / "clean_filter_executed.marker"
    script = repo_dir / "clean_hook.sh"
    script.write_text(f"#!/bin/sh\ntouch '{marker}'\ncat\n")
    script.chmod(0o755)
    subprocess.run(["git", "config", "filter.probe.clean", str(script)], cwd=repo_dir, check=True, env=_GIT_ENV, timeout=30)
    (repo_dir / ".gitattributes").write_text("* filter=probe\n")
    (repo_dir / "tracked.txt").write_text("initial content\n")

    ok, reason, metadata = guard(checkout)
    assert not ok and metadata is None
    assert "artifact is a nested git repository with executable or filter configuration" in reason
    assert not marker.exists(), "clean filter was executed!"


def test_ignored_artifact_nested_repo_assume_unchanged_never_discarded(checkout, tmp_path):
    """P1: tracked files marked assume-unchanged refuse removal without recommending deletion."""
    upstream = tmp_path / "upstream"
    subprocess.run(["git", "-c", "core.hooksPath=/dev/null", "init", "--bare", str(upstream)], check=True, capture_output=True, env=_GIT_ENV, timeout=30)

    repo_dir = checkout[0] / "batch_state/reports/assume_unchanged_repo"
    subprocess.run(["git", "-c", "core.hooksPath=/dev/null", "clone", str(upstream), str(repo_dir)], check=True, capture_output=True, env=_GIT_ENV, timeout=30)
    (repo_dir / "probe.txt").write_text("base content\n")
    subprocess.run(["git", "add", "probe.txt"], cwd=repo_dir, check=True, env=_GIT_ENV, timeout=30)
    subprocess.run(["git", "commit", "-m", "base"], cwd=repo_dir, check=True, env=_GIT_ENV, timeout=30)
    subprocess.run(["git", "-c", "core.hooksPath=/dev/null", "push", "origin", "HEAD:refs/heads/topic"], cwd=repo_dir, check=True, capture_output=True, env=_GIT_ENV, timeout=30)
    subprocess.run(["git", "fetch", "origin"], cwd=repo_dir, check=True, capture_output=True, env=_GIT_ENV, timeout=30)

    # Mark assume-unchanged and modify content
    subprocess.run(["git", "update-index", "--assume-unchanged", "probe.txt"], cwd=repo_dir, check=True, env=_GIT_ENV, timeout=30)
    (repo_dir / "probe.txt").write_text("modified concealed\n")

    ok, reason, metadata = guard(checkout)
    assert not ok and metadata is None
    assert "concealed tracked changes" in reason
    assert "uncommitted work must not be discarded" in reason
    assert "clear with: rm -rf" not in reason


def test_ignored_artifact_nested_repo_skip_worktree_never_discarded(checkout, tmp_path):
    """P1: tracked files marked skip-worktree refuse removal without recommending deletion."""
    upstream = tmp_path / "upstream"
    subprocess.run(["git", "-c", "core.hooksPath=/dev/null", "init", "--bare", str(upstream)], check=True, capture_output=True, env=_GIT_ENV, timeout=30)

    repo_dir = checkout[0] / "batch_state/reports/skip_worktree_repo"
    subprocess.run(["git", "-c", "core.hooksPath=/dev/null", "clone", str(upstream), str(repo_dir)], check=True, capture_output=True, env=_GIT_ENV, timeout=30)
    (repo_dir / "probe.txt").write_text("base content\n")
    subprocess.run(["git", "add", "probe.txt"], cwd=repo_dir, check=True, env=_GIT_ENV, timeout=30)
    subprocess.run(["git", "commit", "-m", "base"], cwd=repo_dir, check=True, env=_GIT_ENV, timeout=30)
    subprocess.run(["git", "-c", "core.hooksPath=/dev/null", "push", "origin", "HEAD:refs/heads/topic"], cwd=repo_dir, check=True, capture_output=True, env=_GIT_ENV, timeout=30)
    subprocess.run(["git", "fetch", "origin"], cwd=repo_dir, check=True, capture_output=True, env=_GIT_ENV, timeout=30)

    # Mark skip-worktree and modify content
    subprocess.run(["git", "update-index", "--skip-worktree", "probe.txt"], cwd=repo_dir, check=True, env=_GIT_ENV, timeout=30)
    (repo_dir / "probe.txt").write_text("modified concealed\n")

    ok, reason, metadata = guard(checkout)
    assert not ok and metadata is None
    assert "concealed tracked changes" in reason
    assert "uncommitted work must not be discarded" in reason
    assert "clear with: rm -rf" not in reason


def test_ignored_artifact_nested_repo_include_indirection_rejected_without_execution(checkout):
    """P1: nested repository include indirection is rejected before git execution."""
    repo_dir = checkout[0] / "batch_state/reports/include_repo"
    repo_dir.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "-c", "core.hooksPath=/dev/null", "init", str(repo_dir)], check=True, capture_output=True, env=_GIT_ENV, timeout=30)
    marker = repo_dir / "filter_executed.marker"
    script = repo_dir / "clean_hook.sh"
    script.write_text(f"#!/bin/sh\ntouch '{marker}'\ncat\n")
    script.chmod(0o755)
    extra_cfg = repo_dir / "extra.config"
    extra_cfg.write_text(f'[filter "probe"]\n  clean = "{script}"\n')
    cfg = repo_dir / ".git" / "config"
    with open(cfg, "a", encoding="utf-8") as fp:
        fp.write(f"\n[include]\n  path = {extra_cfg}\n")
    (repo_dir / ".gitattributes").write_text("* filter=probe\n")
    (repo_dir / "tracked.txt").write_text("initial content\n")

    ok, reason, metadata = guard(checkout)
    assert not ok and metadata is None
    assert "configuration indirection (include/includeIf)" in reason
    assert not marker.exists(), "clean filter was executed via include indirection!"
    assert "clear with: rm -rf" not in reason


def test_ignored_artifact_nested_repo_includeif_indirection_rejected_without_execution(checkout):
    """P1: nested repository includeIf indirection is rejected before git execution."""
    repo_dir = checkout[0] / "batch_state/reports/includeif_repo"
    repo_dir.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "-c", "core.hooksPath=/dev/null", "init", str(repo_dir)], check=True, capture_output=True, env=_GIT_ENV, timeout=30)
    marker = repo_dir / "filter_executed.marker"
    script = repo_dir / "clean_hook.sh"
    script.write_text(f"#!/bin/sh\ntouch '{marker}'\ncat\n")
    script.chmod(0o755)
    extra_cfg = repo_dir / "extra.config"
    extra_cfg.write_text(f'[filter "probe"]\n  clean = "{script}"\n')
    cfg = repo_dir / ".git" / "config"
    with open(cfg, "a", encoding="utf-8") as fp:
        fp.write(f'\n[includeIf "gitdir:*"]\n  path = {extra_cfg}\n')
    (repo_dir / ".gitattributes").write_text("* filter=probe\n")
    (repo_dir / "tracked.txt").write_text("initial content\n")

    ok, reason, metadata = guard(checkout)
    assert not ok and metadata is None
    assert "configuration indirection (include/includeIf)" in reason
    assert not marker.exists(), "clean filter was executed via includeIf indirection!"
    assert "clear with: rm -rf" not in reason


def test_ignored_artifact_nested_repo_config_worktree_filter_rejected_without_execution(checkout):
    """P1: nested repository config.worktree filter is rejected before git execution."""
    repo_dir = checkout[0] / "batch_state/reports/config_worktree_repo"
    repo_dir.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "-c", "core.hooksPath=/dev/null", "init", str(repo_dir)], check=True, capture_output=True, env=_GIT_ENV, timeout=30)
    subprocess.run(["git", "config", "extensions.worktreeConfig", "true"], cwd=repo_dir, check=True, env=_GIT_ENV, timeout=30)
    marker = repo_dir / "filter_executed.marker"
    script = repo_dir / "clean_hook.sh"
    script.write_text(f"#!/bin/sh\ntouch '{marker}'\ncat\n")
    script.chmod(0o755)
    cfg_wt = repo_dir / ".git" / "config.worktree"
    cfg_wt.write_text(f'[filter "probe"]\n  clean = "{script}"\n')
    (repo_dir / ".gitattributes").write_text("* filter=probe\n")
    (repo_dir / "tracked.txt").write_text("initial content\n")

    ok, reason, metadata = guard(checkout)
    assert not ok and metadata is None
    assert "artifact is a nested git repository with executable or filter configuration" in reason
    assert not marker.exists(), "clean filter was executed via config.worktree!"
    assert "clear with: rm -rf" not in reason


def test_ignored_artifact_nested_repo_core_worktree_redirection_never_discarded(checkout, tmp_path):
    """P1: nested repo with core.worktree pointing to clean dir never discards dirty artifact."""
    upstream = tmp_path / "upstream"
    subprocess.run(["git", "-c", "core.hooksPath=/dev/null", "init", "--bare", str(upstream)], check=True, capture_output=True, env=_GIT_ENV, timeout=30)

    clean_external = tmp_path / "clean_external"
    clean_external.mkdir()

    repo_dir = checkout[0] / "batch_state/reports/redirected_worktree_repo"
    subprocess.run(["git", "-c", "core.hooksPath=/dev/null", "clone", str(upstream), str(repo_dir)], check=True, capture_output=True, env=_GIT_ENV, timeout=30)
    (repo_dir / "probe.txt").write_text("base content\n")
    subprocess.run(["git", "add", "probe.txt"], cwd=repo_dir, check=True, env=_GIT_ENV, timeout=30)
    subprocess.run(["git", "commit", "-m", "base"], cwd=repo_dir, check=True, env=_GIT_ENV, timeout=30)
    subprocess.run(["git", "-c", "core.hooksPath=/dev/null", "push", "origin", "HEAD:refs/heads/topic"], cwd=repo_dir, check=True, capture_output=True, env=_GIT_ENV, timeout=30)
    subprocess.run(["git", "fetch", "origin"], cwd=repo_dir, check=True, capture_output=True, env=_GIT_ENV, timeout=30)

    # Modify the actual artifact file so it has uncommitted bytes
    (repo_dir / "probe.txt").write_text("modified dirty content in artifact\n")

    # Mirror base file to external clean dir and point core.worktree there
    (clean_external / "probe.txt").write_text("base content\n")
    subprocess.run(["git", "config", "core.worktree", str(clean_external)], cwd=repo_dir, check=True, env=_GIT_ENV, timeout=30)

    ok, reason, metadata = guard(checkout)
    assert not ok and metadata is None
    assert (
        "redirected worktree (core.worktree)" in reason
        or "does not match expected directory" in reason
    )
    assert "clear with: rm -rf" not in reason
