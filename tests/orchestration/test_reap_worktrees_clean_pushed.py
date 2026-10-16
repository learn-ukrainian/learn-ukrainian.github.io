"""Clean, fully pushed, idle dispatch worktree reaping (#10778).

Guard tests run real Git in temporary repositories with real linked
worktrees; only the ``fuser`` executable is substituted where a test must
control what it reports.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import pytest

from scripts.orchestration import reap_worktrees as rw
from scripts.orchestration import reaper_lifecycle, worktree_claims

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SYSTEMD = PROJECT_ROOT / "packaging" / "systemd"
SERVICE = SYSTEMD / "learn-ukrainian-worktree-reaper.service"
TIMER = SYSTEMD / "learn-ukrainian-worktree-reaper.timer"
DROPIN = SYSTEMD / "dropins" / "learn-ukrainian-worktree-reaper.service.d" / "data-volume.conf"
TWO_HOURS = 2 * 3600
_TEMPLATE: Path | None = None


def git_env() -> dict[str, str]:
    return {
        key: value
        for key, value in os.environ.items()
        if not key.startswith(("GIT_", "PRE_COMMIT")) and key != "AGENT_NO_MERGE"
    }


def git(cwd: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True, text=True, check=False, env=git_env(), timeout=30
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout
    return proc.stdout.strip()


@pytest.fixture(scope="module", autouse=True)
def _template(tmp_path_factory: pytest.TempPathFactory):
    global _TEMPLATE
    root = tmp_path_factory.mktemp("clean-pushed-template")
    repo = root / "repo"
    git(root, "init", "--bare", str(root / "origin.git"))
    git(root, "init", "--initial-branch=main", str(repo))
    git(repo, "config", "user.email", "tester@example.com")
    git(repo, "config", "user.name", "Test User")
    (repo / ".gitignore").write_text(".worktrees/\nbatch_state/\nout/\n", encoding="utf-8")
    (repo / "README.md").write_text("base\n", encoding="utf-8")
    git(repo, "add", ".gitignore", "README.md")
    git(repo, "commit", "-m", "base")
    git(repo, "remote", "add", "origin", str(root / "origin.git"))
    git(repo, "push", "-u", "origin", "main")
    _TEMPLATE = root
    yield
    _TEMPLATE = None


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    assert _TEMPLATE is not None
    shutil.copytree(_TEMPLATE / "repo", tmp_path / "repo")
    shutil.copytree(_TEMPLATE / "origin.git", tmp_path / "origin.git")
    git(tmp_path / "repo", "remote", "set-url", "origin", str(tmp_path / "origin.git"))
    return tmp_path / "repo"


_UNINSPECTABLE_IN_SCOPE: set[int] = set()
_REAL_UNINSPECTABLE = rw._uninspectable_same_user


@pytest.fixture(autouse=True)
def _host_processes_out_of_scope(monkeypatch: pytest.MonkeyPatch):
    """Judge only the uninspectable processes a test starts.

    The classification itself runs for real on those; any other
    non-dumpable process on the test host would otherwise keep every tree.
    """

    def scoped(base: Path, proc_root: Path) -> bool:
        return int(base.name) in _UNINSPECTABLE_IN_SCOPE and _REAL_UNINSPECTABLE(base, proc_root)

    monkeypatch.setattr(rw, "_uninspectable_same_user", scoped)
    yield
    _UNINSPECTABLE_IN_SCOPE.clear()


@pytest.fixture
def free_fuser(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A ``fuser`` that reports no user, so the process-table scan alone decides."""
    return fake_fuser(tmp_path, monkeypatch, "exit 1")


def fake_fuser(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, body: str) -> Path:
    script = tmp_path / "bin" / "fuser"
    script.parent.mkdir(exist_ok=True)
    script.write_text(f"#!/bin/sh\n{body}\n", encoding="utf-8")
    script.chmod(0o755)
    monkeypatch.setattr(rw, "_FUSER", str(script))
    return script


def admin_dir(worktree: Path) -> Path:
    pointer = (worktree / ".git").read_text(encoding="utf-8").split("gitdir:", 1)[1].strip()
    return Path(pointer)


def age(paths: list[Path], seconds: float = TWO_HOURS) -> None:
    stamp = time.time() - seconds
    for path in paths:
        if path.exists():
            os.utime(path, (stamp, stamp))


def age_tree(worktree: Path, repo: Path, task_id: str | None = None) -> None:
    git_dir = admin_dir(worktree)
    paths = [git_dir / "HEAD", git_dir / "index", git_dir / "logs" / "HEAD"]
    if task_id:
        paths.append(repo / "batch_state" / "tasks" / f"{task_id}.json")
    age(paths)


def write_task(repo: Path, task_id: str, worktree: Path, **fields: Any) -> Path:
    tasks = repo / "batch_state" / "tasks"
    tasks.mkdir(parents=True, exist_ok=True)
    record = {"task_id": task_id, "status": "needs_finalize", "worktree_path": str(worktree), **fields}
    path = tasks / f"{task_id}.json"
    path.write_text(json.dumps(record), encoding="utf-8")
    return path


def dispatch_tree(
    repo: Path, task_id: str = "task-a", *, detached: bool = False, status: str | None = "needs_finalize"
) -> Path:
    """A clean dispatch checkout whose HEAD is on origin, idle for two hours."""
    worktree = repo / ".worktrees" / "dispatch" / "codex" / task_id
    worktree.parent.mkdir(parents=True, exist_ok=True)
    if detached:
        git(repo, "worktree", "add", "--detach", str(worktree), "main")
    else:
        git(repo, "worktree", "add", "-b", f"codex/{task_id}", str(worktree), "main")
    if status is not None:
        write_task(repo, task_id, worktree, status=status)
    age_tree(worktree, repo, task_id if status is not None else None)
    return worktree


def outcome_for(report: rw.CleanPushedReport, worktree: Path, repo: Path) -> rw.CleanPushedOutcome:
    shown = worktree.relative_to(repo).as_posix()
    matches = [item for item in (*report.removed, *report.skipped) if item.path == shown]
    assert len(matches) == 1, report
    return matches[0]


def abandon_log(repo: Path) -> list[dict[str, Any]]:
    path = repo / "batch_state" / "worktree-abandon-log.jsonl"
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


@pytest.mark.parametrize("detached", [False, True])
def test_clean_old_pushed_tree_is_removed_and_logged(repo: Path, free_fuser: Path, detached: bool) -> None:
    worktree = dispatch_tree(repo, detached=detached)
    head = git(worktree, "rev-parse", "HEAD")

    report = rw.reap_clean_pushed(repo_root=repo, dry_run=False, actor="test-actor")

    removed = outcome_for(report, worktree, repo)
    assert removed.action == "removed", removed
    assert not worktree.exists()
    assert report.freed_mb == removed.size_mb
    [entry] = abandon_log(repo)
    assert set(entry) == {"ts", "actor", "path", "head", "branch", "task_status", "reason", "size_mb"}
    assert entry["actor"] == "test-actor"
    assert entry["path"] == ".worktrees/dispatch/codex/task-a"
    assert entry["head"] == head
    assert entry["branch"] == (None if detached else "codex/task-a")
    assert entry["task_status"] == "needs_finalize"
    assert entry["reason"] == rw.CLEAN_PUSHED_REASON
    assert isinstance(entry["size_mb"], int)
    assert entry["ts"].endswith("+00:00")
    if not detached:
        assert git(repo, "rev-parse", "--verify", "codex/task-a") == head  # branches are never deleted
    events = [json.loads(line)["event"] for line in reaper_lifecycle.journal_path(repo).read_text().splitlines()]
    assert events == ["clean-pushed-remove", "clean-pushed-removed"]  # intent, then confirmed


def test_tree_without_any_task_record_is_removed(repo: Path, free_fuser: Path) -> None:
    worktree = dispatch_tree(repo, status=None)

    report = rw.reap_clean_pushed(repo_root=repo, dry_run=False)

    assert outcome_for(report, worktree, repo).action == "removed"
    assert abandon_log(repo)[0]["task_status"] is None


def test_force_is_never_passed(repo: Path, free_fuser: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    worktree = dispatch_tree(repo)
    calls: list[list[str]] = []
    real_safe_git = worktree_claims.safe_git

    def spy(args: list[str], **kwargs: Any) -> Any:
        calls.append(list(args))
        return real_safe_git(args, **kwargs)

    monkeypatch.setattr(worktree_claims, "safe_git", spy)

    rw.reap_clean_pushed(repo_root=repo, dry_run=False)

    [remove] = [call for call in calls if call[:2] == ["worktree", "remove"]]
    assert "--force" not in remove and len(remove) == 3
    staged = Path(remove[2])  # the quarantined checkout
    assert staged.name == worktree.name and staged.parent.parent == repo / ".worktrees" / ".reaping"
    assert not worktree.exists() and not staged.exists()
    assert list((repo / ".worktrees" / ".reaping").iterdir()) == []


def test_failed_removal_is_reported_and_never_retried(
    repo: Path, free_fuser: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    worktree = dispatch_tree(repo)
    calls: list[list[str]] = []
    real_safe_git = worktree_claims.safe_git

    def failing_remove(args: list[str], **kwargs: Any) -> Any:
        if args[:2] != ["worktree", "remove"]:
            return real_safe_git(args, **kwargs)
        calls.append(list(args))
        return subprocess.CompletedProcess(args, 128, "", "fatal: simulated failure")

    monkeypatch.setattr(worktree_claims, "safe_git", failing_remove)

    report = rw.reap_clean_pushed(repo_root=repo, dry_run=False)

    outcome = outcome_for(report, worktree, repo)
    assert outcome.action == "error"
    assert outcome.reason == "worktree removal failed: fatal: simulated failure"
    [call] = calls
    assert call[:2] == ["worktree", "remove"] and Path(call[2]).parent.parent == repo / ".worktrees" / ".reaping"
    assert worktree.is_dir()  # moved back from the quarantine
    assert list((repo / ".worktrees" / ".reaping").iterdir()) == []
    assert abandon_log(repo) == []


def test_dry_run_changes_nothing(repo: Path, free_fuser: Path) -> None:
    worktree = dispatch_tree(repo)

    report = rw.reap_clean_pushed(repo_root=repo)

    assert report.dry_run
    assert outcome_for(report, worktree, repo).action == "would_remove"
    assert worktree.is_dir()
    assert abandon_log(repo) == []
    assert not reaper_lifecycle.journal_path(repo).exists()


def _refusal(repo: Path, worktree: Path) -> str:
    report = rw.reap_clean_pushed(repo_root=repo, dry_run=False)
    outcome = outcome_for(report, worktree, repo)
    assert outcome.action == "skipped", outcome
    assert worktree.exists() or worktree.is_symlink()
    assert abandon_log(repo) == []
    return outcome.reason


def test_dirty_tracked_file_refuses(repo: Path, free_fuser: Path) -> None:
    worktree = dispatch_tree(repo)
    (worktree / "README.md").write_text("changed\n", encoding="utf-8")
    assert _refusal(repo, worktree) == "dirty or untracked files"


def test_untracked_file_refuses(repo: Path, free_fuser: Path) -> None:
    worktree = dispatch_tree(repo)
    (worktree / "notes" / "deep").mkdir(parents=True)
    (worktree / "notes" / "deep" / "scratch.txt").write_text("x\n", encoding="utf-8")
    assert _refusal(repo, worktree) == "dirty or untracked files"


def test_one_unpushed_commit_refuses(repo: Path, free_fuser: Path) -> None:
    worktree = dispatch_tree(repo)
    (worktree / "README.md").write_text("local only\n", encoding="utf-8")
    git(worktree, "commit", "-am", "local only")
    age_tree(worktree, repo, "task-a")
    assert _refusal(repo, worktree) == "commits not on origin"


def test_detached_unpushed_commit_refuses(repo: Path, free_fuser: Path) -> None:
    worktree = dispatch_tree(repo, detached=True)
    (worktree / "README.md").write_text("local only\n", encoding="utf-8")
    git(worktree, "commit", "-am", "local only")
    age_tree(worktree, repo, "task-a")
    assert _refusal(repo, worktree) == "commits not on origin"


def test_process_working_inside_the_tree_refuses(repo: Path, free_fuser: Path) -> None:
    worktree = dispatch_tree(repo)
    subdir = worktree / "sub"
    subdir.mkdir()
    (subdir / ".gitkeep").write_text("", encoding="utf-8")
    git(worktree, "add", "sub/.gitkeep")
    git(worktree, "commit", "-m", "sub")
    git(worktree, "push", "-u", "origin", "codex/task-a")
    age_tree(worktree, repo, "task-a")
    holder = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"], cwd=subdir)
    try:
        assert _refusal(repo, worktree) == "in use: a process works inside the checkout"
    finally:
        holder.kill()
        holder.wait(timeout=30)


@pytest.mark.skipif(shutil.which("fuser") is None, reason="real fuser not installed")
def test_real_fuser_reports_a_process_in_the_tree(repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(rw, "_FUSER", "fuser")
    worktree = dispatch_tree(repo)
    holder = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"], cwd=worktree)
    try:
        assert _refusal(repo, worktree) == "in use: fuser reports a process using the checkout"
    finally:
        holder.kill()
        holder.wait(timeout=30)


@pytest.mark.parametrize(
    ("body", "reason"),
    [
        ("exit 0", "in use: fuser reports a process using the checkout"),
        ("echo 'Specified filename does not exist.' >&2; exit 1", "fuser failed (exit 1); treated as in use"),
        ("exit 2", "fuser failed (exit 2); treated as in use"),
        ("sleep 5", "fuser timed out; treated as in use"),
    ],
)
def test_fuser_in_use_or_failure_refuses(
    repo: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, body: str, reason: str
) -> None:
    fake_fuser(tmp_path, monkeypatch, body)
    monkeypatch.setattr(rw, "_CLEAN_PUSHED_PROBE_TIMEOUT_S", 0.5)
    worktree = dispatch_tree(repo)
    assert _refusal(repo, worktree) == reason


def test_fuser_unavailable_refuses(repo: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(rw, "_FUSER", str(tmp_path / "missing" / "fuser"))
    worktree = dispatch_tree(repo)
    assert _refusal(repo, worktree) == "fuser unavailable; treated as in use"


def test_unlistable_process_table_refuses(repo: Path, free_fuser: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    worktree = dispatch_tree(repo)
    monkeypatch.setattr(rw, "_proc_users_inside", lambda root, *, deadline, **_: None)
    assert _refusal(repo, worktree) == "process table probe unavailable; treated as in use"


@pytest.mark.parametrize("status", ["running", "spawning"])
def test_live_task_refuses(repo: Path, free_fuser: Path, status: str) -> None:
    worktree = dispatch_tree(repo, status=status)
    assert _refusal(repo, worktree) == f"task task-a is {status}"


def test_task_of_another_id_claiming_the_tree_refuses(repo: Path, free_fuser: Path) -> None:
    worktree = dispatch_tree(repo)
    record = write_task(repo, "reuser", worktree, status="running")
    age([record])
    assert _refusal(repo, worktree) == "task reuser is running"


@pytest.mark.parametrize("status", ["queued", "", None])
def test_unsettled_task_status_refuses(repo: Path, free_fuser: Path, status: str | None) -> None:
    worktree = dispatch_tree(repo, status="done")
    record = write_task(repo, "task-a", worktree, status=status)
    age([record])
    assert _refusal(repo, worktree) == f"task task-a status {status!r} is not settled"


def test_task_with_live_worker_refuses(repo: Path, free_fuser: Path) -> None:
    worktree = dispatch_tree(repo)
    record = write_task(repo, "task-a", worktree, status="needs_finalize", pid=os.getpid())
    age([record])
    assert _refusal(repo, worktree) == "task task-a worker is live or unknown"


def test_younger_than_sixty_minutes_refuses(repo: Path, free_fuser: Path) -> None:
    worktree = dispatch_tree(repo)
    age_tree(worktree, repo, "task-a")
    age([admin_dir(worktree) / "index"], seconds=59 * 60)
    assert _refusal(repo, worktree) == "last activity 59 min ago (< 60 min)"


def test_recent_task_file_refuses(repo: Path, free_fuser: Path) -> None:
    worktree = dispatch_tree(repo)
    os.utime(repo / "batch_state" / "tasks" / "task-a.json")
    assert _refusal(repo, worktree) == "last activity 0 min ago (< 60 min)"


def test_fresh_checkout_refuses(repo: Path, free_fuser: Path) -> None:
    worktree = repo / ".worktrees" / "dispatch" / "codex" / "fresh"
    worktree.parent.mkdir(parents=True)
    git(repo, "worktree", "add", "-b", "codex/fresh", str(worktree), "main")
    assert _refusal(repo, worktree) == "last activity 0 min ago (< 60 min)"


def test_unparsable_task_record_refuses(repo: Path, free_fuser: Path) -> None:
    worktree = dispatch_tree(repo)
    (repo / "batch_state" / "tasks" / "broken.json").write_text('{"status": "runn', encoding="utf-8")
    assert _refusal(repo, worktree) == "task record broken.json unreadable"


@pytest.mark.skipif(os.geteuid() == 0, reason="root reads mode-000 files")
def test_unreadable_task_record_refuses(repo: Path, free_fuser: Path) -> None:
    worktree = dispatch_tree(repo)
    locked = repo / "batch_state" / "tasks" / "locked.json"
    locked.write_text("{}", encoding="utf-8")
    locked.chmod(0)
    try:
        assert _refusal(repo, worktree) == "task record locked.json unreadable"
    finally:
        locked.chmod(0o600)


def test_finished_corrupt_record_naming_another_tree_does_not_block(repo: Path, free_fuser: Path) -> None:
    worktree = dispatch_tree(repo)
    (repo / "batch_state" / "tasks" / "other.json").write_text(
        '{"status": "done", "worktree_path": [1]}', encoding="utf-8"
    )
    report = rw.reap_clean_pushed(repo_root=repo, dry_run=False)
    assert outcome_for(report, worktree, repo).action == "removed"


def test_path_outside_dispatch_refuses(repo: Path, free_fuser: Path) -> None:
    worktree = repo / ".worktrees" / "review-123"
    git(repo, "worktree", "add", "--detach", str(worktree), "main")
    age_tree(worktree, repo)
    assert _refusal(repo, worktree) == "outside .worktrees/dispatch/"


def test_nested_dispatch_path_refuses(repo: Path, free_fuser: Path) -> None:
    worktree = repo / ".worktrees" / "dispatch" / "codex" / "group" / "task"
    worktree.parent.mkdir(parents=True)
    git(repo, "worktree", "add", "--detach", str(worktree), "main")
    age_tree(worktree, repo)
    assert _refusal(repo, worktree) == "not a .worktrees/dispatch/<agent>/<task>/ checkout"


def test_primary_checkout_is_never_a_candidate(repo: Path, free_fuser: Path) -> None:
    report = rw.reap_clean_pushed(repo_root=repo, dry_run=False)
    [primary] = [item for item in report.skipped if item.path == "."]
    assert primary.reason == "primary checkout"
    assert (repo / ".git").is_dir()


def test_symlinked_registered_path_refuses(repo: Path, free_fuser: Path, tmp_path: Path) -> None:
    worktree = dispatch_tree(repo)
    elsewhere = tmp_path / "elsewhere"
    worktree.rename(elsewhere)
    worktree.symlink_to(elsewhere, target_is_directory=True)
    assert _refusal(repo, worktree) == "path is a symlink, missing, or not a directory"
    assert elsewhere.is_dir()


def test_non_directory_registered_path_refuses(repo: Path, free_fuser: Path) -> None:
    worktree = dispatch_tree(repo)
    shutil.rmtree(worktree)
    worktree.write_text("not a checkout\n", encoding="utf-8")
    assert _refusal(repo, worktree) == "path is a symlink, missing, or not a directory"
    assert worktree.read_text(encoding="utf-8") == "not a checkout\n"


def test_locked_worktree_refuses(repo: Path, free_fuser: Path) -> None:
    worktree = dispatch_tree(repo)
    git(repo, "worktree", "lock", "--reason", "hold", str(worktree))
    assert _refusal(repo, worktree) == "git worktree is locked"


def test_ignored_output_over_the_preservation_cap_is_retained(repo: Path, free_fuser: Path) -> None:
    worktree = dispatch_tree(repo)
    (worktree / "out").mkdir()
    with (worktree / "out" / "big.bin").open("wb") as handle:
        handle.truncate(300 * 1024 * 1024)  # sparse: no real disk use
    age_tree(worktree, repo, "task-a")

    report = rw.reap_clean_pushed(repo_root=repo, dry_run=False)

    outcome = outcome_for(report, worktree, repo)
    assert outcome.action == "skipped", outcome
    assert outcome.reason == (
        "artifact preservation failed: ignored output exceeds preservation cap "
        "(314572800 > 268435456 bytes); refusing worktree removal"
    )
    assert (worktree / "out" / "big.bin").exists()
    assert abandon_log(repo) == []


def test_recheck_under_the_lock_refuses_a_tree_that_changed(
    repo: Path, free_fuser: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    worktree = dispatch_tree(repo)
    real_remove = worktree_claims.remove_unclaimed_worktree

    def change_then_remove(path: Path, **kwargs: Any) -> worktree_claims.WorktreeRemoval:
        (path / "late.txt").write_text("written after selection\n", encoding="utf-8")
        return real_remove(path, **kwargs)

    monkeypatch.setattr(worktree_claims, "remove_unclaimed_worktree", change_then_remove)

    report = rw.reap_clean_pushed(repo_root=repo, dry_run=False)

    outcome = outcome_for(report, worktree, repo)
    assert (outcome.action, outcome.reason) == ("skipped", "re-check: dirty or untracked files")
    assert (worktree / "late.txt").exists()


def test_task_spawned_after_selection_is_caught_by_the_claim_scan(
    repo: Path, free_fuser: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    worktree = dispatch_tree(repo)
    real_remove = worktree_claims.remove_unclaimed_worktree

    def spawn_then_remove(path: Path, **kwargs: Any) -> worktree_claims.WorktreeRemoval:
        age([write_task(repo, "late-task", path, status="spawning")])
        return real_remove(path, **kwargs)

    monkeypatch.setattr(worktree_claims, "remove_unclaimed_worktree", spawn_then_remove)

    report = rw.reap_clean_pushed(repo_root=repo, dry_run=False)

    outcome = outcome_for(report, worktree, repo)
    assert outcome.action == "skipped"
    assert outcome.reason == "worktree claimed by active task late-task"
    assert worktree.is_dir()


def test_concurrent_second_run_is_a_no_op(repo: Path, free_fuser: Path) -> None:
    worktree = dispatch_tree(repo)
    with rw._ReapLock(repo):
        report = rw.reap_clean_pushed(repo_root=repo, dry_run=False, lock_timeout_s=0.2)
    assert report.lock_busy
    assert report.removed == () and report.skipped == ()
    assert report.refusal and "another worktree cleanup holds" in report.refusal
    assert worktree.is_dir()
    assert abandon_log(repo) == []


def test_concurrent_second_process_is_a_no_op(repo: Path, free_fuser: Path) -> None:
    worktree = dispatch_tree(repo)
    code = (
        "import sys, time; from pathlib import Path; "
        "from scripts.orchestration import reap_worktrees as rw; "
        "lock = rw._ReapLock(Path(sys.argv[1])); lock.__enter__(); print('held', flush=True); time.sleep(30)"
    )
    holder = subprocess.Popen(
        [sys.executable, "-c", code, str(repo)], cwd=PROJECT_ROOT, stdout=subprocess.PIPE, text=True
    )
    try:
        assert holder.stdout is not None and holder.stdout.readline().strip() == "held"
        report = rw.reap_clean_pushed(repo_root=repo, dry_run=False, lock_timeout_s=0.2)
    finally:
        holder.kill()
        holder.wait(timeout=30)
    assert report.lock_busy and report.removed == ()
    assert worktree.is_dir()


def test_kill_switch_disables_apply(repo: Path, free_fuser: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    worktree = dispatch_tree(repo)
    monkeypatch.setenv("LU_REAPER_DISABLED", "1")
    report = rw.reap_clean_pushed(repo_root=repo, dry_run=False)
    assert report.refusal == "reaper disabled by LU_REAPER_DISABLED=1"
    assert worktree.is_dir()


def test_cli_dry_run_by_default_and_apply(repo: Path, free_fuser: Path, capsys: pytest.CaptureFixture[str]) -> None:
    worktree = dispatch_tree(repo)

    assert rw.main(["--clean-pushed", "--repo-root", str(repo), "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["dry_run"] is True
    assert [item["path"] for item in payload["removed"]] == [".worktrees/dispatch/codex/task-a"]
    assert worktree.is_dir()

    assert rw.main(["--clean-pushed", "--apply", "--repo-root", str(repo)]) == 0
    out = capsys.readouterr().out
    assert out.startswith("APPLY clean-pushed: 1 removed")
    assert "REMOVED .worktrees/dispatch/codex/task-a" in out
    assert str(repo) not in out  # repository-relative paths only
    assert not worktree.exists()


def test_systemd_service_and_timer_text() -> None:
    service = SERVICE.read_text(encoding="utf-8")
    timer = TIMER.read_text(encoding="utf-8")
    lines = service.splitlines()
    starts = [line for line in lines if line.startswith("ExecStart=")]
    assert starts == [
        "ExecStart=@REPO_ROOT@/.venv/bin/python -m scripts.orchestration.reap_worktrees --clean-pushed --apply"
    ]
    assert "--force" not in service
    assert "Type=oneshot" in lines
    assert "WorkingDirectory=@REPO_ROOT@" in lines
    timeout = [line for line in lines if line.startswith("TimeoutStartSec=")]
    assert timeout and 0 < int(timeout[0].split("=", 1)[1]) < 1800  # finishes inside one cadence
    # Network only for the bounded `git fetch --prune origin`; no other socket
    # family. Enforced in user managers (seccomp).
    assert "RestrictAddressFamilies=AF_UNIX AF_INET AF_INET6" in lines
    timer_lines = timer.splitlines()
    assert "OnCalendar=*:00/30" in timer_lines
    assert "Persistent=false" in timer_lines
    assert "Unit=learn-ukrainian-worktree-reaper.service" in timer_lines
    assert "WantedBy=timers.target" in timer_lines
    # Overlap: a oneshot unit never starts twice, and the reaper lock makes a
    # second process a no-op (test_concurrent_second_process_is_a_no_op).
    dropin = DROPIN.read_text(encoding="utf-8")
    assert dropin.splitlines()[1:3] == [
        "ExecStart=",
        "ExecStart=/usr/bin/env bash @REPO_ROOT@/scripts/storage/data_volume_guard.sh -- "
        + starts[0].removeprefix("ExecStart="),
    ]
    assert "--force" not in dropin


# Round 2 (#10778): the five data-loss reproducers of the exact-head review of
# 513a2591. Each failed (the tree was removed) on that commit.

HIDDEN = "hidden change: a file flagged assume-unchanged or skip-worktree differs from the index"
REFLOG = "unpublished_reflog_commit: the HEAD reflog names a commit no origin ref contains"
SHOWN = ".worktrees/dispatch/codex/task-a"


def quarantine_entries(repo: Path) -> list[Path]:
    root = repo / ".worktrees" / ".reaping"
    return sorted(root.iterdir()) if root.exists() else []


@pytest.mark.parametrize("flag", ["--assume-unchanged", "--skip-worktree"])
@pytest.mark.parametrize("edit", ["a longer hidden edit\n", "BASE\n"])  # "BASE\n": same size as "base\n"
def test_edit_hidden_by_an_index_flag_refuses(repo: Path, free_fuser: Path, flag: str, edit: str) -> None:
    worktree = dispatch_tree(repo)
    git(worktree, "update-index", flag, "README.md")
    (worktree / "README.md").write_text(edit, encoding="utf-8")
    assert git(worktree, "status", "--porcelain", "--untracked-files=all") == ""  # invisible to status
    age_tree(worktree, repo, "task-a")

    assert _refusal(repo, worktree) == HIDDEN
    assert (worktree / "README.md").read_text(encoding="utf-8") == edit


def test_exec_bit_hidden_by_an_index_flag_refuses(repo: Path, free_fuser: Path) -> None:
    worktree = dispatch_tree(repo)
    git(worktree, "update-index", "--assume-unchanged", "README.md")
    (worktree / "README.md").chmod(0o755)
    age_tree(worktree, repo, "task-a")
    assert _refusal(repo, worktree) == HIDDEN


def test_unchanged_flagged_file_and_sparse_exclusions_do_not_refuse(repo: Path, free_fuser: Path) -> None:
    worktree = dispatch_tree(repo)
    git(worktree, "sparse-checkout", "set", "--no-cone", "/.gitignore")  # README.md: skip-worktree, absent
    assert not (worktree / "README.md").exists()
    git(worktree, "update-index", "--assume-unchanged", ".gitignore")  # flagged, present, unchanged
    age_tree(worktree, repo, "task-a")

    report = rw.reap_clean_pushed(repo_root=repo, dry_run=False)

    assert outcome_for(report, worktree, repo).action == "removed"
    assert not worktree.exists()


@pytest.mark.parametrize("detached", [True, False])
def test_commit_only_in_the_head_reflog_refuses(repo: Path, free_fuser: Path, detached: bool) -> None:
    worktree = dispatch_tree(repo, detached=detached)
    (worktree / "README.md").write_text("unpublished\n", encoding="utf-8")
    git(worktree, "commit", "-am", "unpublished")
    lost = git(worktree, "rev-parse", "HEAD")
    git(worktree, "reset", "--hard", "origin/main")
    age_tree(worktree, repo, "task-a")

    report = rw.reap_clean_pushed(repo_root=repo, dry_run=False)

    outcome = outcome_for(report, worktree, repo)
    assert (outcome.action, outcome.reason) == ("skipped", REFLOG)
    assert report.unpublished_reflog_commit == (SHOWN,)
    assert worktree.is_dir()
    assert lost in git(worktree, "rev-list", "--walk-reflogs", "HEAD").split()


def test_commit_only_in_a_per_worktree_ref_refuses(repo: Path, free_fuser: Path) -> None:
    worktree = dispatch_tree(repo, detached=True)
    tree = git(worktree, "rev-parse", "HEAD^{tree}")
    commit = git(worktree, "commit-tree", tree, "-p", "HEAD", "-m", "kept by a per-worktree ref")
    git(worktree, "update-ref", "refs/worktree/keep", commit)
    age_tree(worktree, repo, "task-a")
    assert _refusal(repo, worktree) == REFLOG


def test_reflog_of_pushed_commits_does_not_refuse(repo: Path, free_fuser: Path) -> None:
    worktree = dispatch_tree(repo)
    (worktree / "README.md").write_text("pushed\n", encoding="utf-8")
    git(worktree, "commit", "-am", "pushed")
    git(worktree, "push", "-u", "origin", "codex/task-a")
    age_tree(worktree, repo, "task-a")

    report = rw.reap_clean_pushed(repo_root=repo, dry_run=False)

    assert outcome_for(report, worktree, repo).action == "removed"
    assert report.unpublished_reflog_commit == ()


_NON_DUMPABLE_HOLDER = (
    "import ctypes, sys, time\n"
    "held = open(sys.argv[1], 'rb')\n"
    "assert ctypes.CDLL(None, use_errno=True).prctl(4, 0, 0, 0, 0) == 0  # PR_SET_DUMPABLE, 0\n"
    "print('ready', flush=True)\n"
    "time.sleep(60)\n"
)


@pytest.mark.skipif(not sys.platform.startswith("linux"), reason="prctl and /proc are Linux")
@pytest.mark.skipif(os.geteuid() == 0, reason="root inspects non-dumpable processes")
def test_uninspectable_same_user_process_keeps_every_tree(repo: Path, free_fuser: Path, tmp_path: Path) -> None:
    worktree = dispatch_tree(repo)
    other = dispatch_tree(repo, "task-b")
    holder = subprocess.Popen(
        [sys.executable, "-c", _NON_DUMPABLE_HOLDER, str(worktree / "README.md")],
        cwd=tmp_path,
        stdout=subprocess.PIPE,
        text=True,
    )
    try:
        assert holder.stdout is not None and holder.stdout.readline().strip() == "ready"
        _UNINSPECTABLE_IN_SCOPE.add(holder.pid)
        with pytest.raises(PermissionError):
            os.listdir(f"/proc/{holder.pid}/fd")  # the open file is really hidden

        report = rw.reap_clean_pushed(repo_root=repo, dry_run=False)
    finally:
        holder.kill()
        holder.wait(timeout=30)

    for tree in (worktree, other):
        outcome = outcome_for(report, tree, repo)
        assert outcome.action == "skipped", outcome
        assert outcome.reason == f"uninspectable_process {holder.pid}: a process of this user cannot be inspected"
        assert tree.is_dir()
    assert abandon_log(repo) == []
    assert report.uninspectable == (holder.pid,)


@pytest.mark.skipif(not sys.platform.startswith("linux"), reason="/proc is Linux")
def test_session_infrastructure_and_dead_or_foreign_processes_are_not_uninspectable(tmp_path: Path) -> None:
    proc = tmp_path / "proc"
    uid = os.getuid()

    def fake(pid: int, *, name: str, ppid: int, uids: int, state: str = "S", cgroup: str = "/lu.scope") -> Path:
        base = proc / str(pid)
        base.mkdir(parents=True)
        (base / "status").write_text(
            f"Name:\t{name}\nState:\t{state} (x)\nPPid:\t{ppid}\nUid:\t{uids}\t{uids}\t{uids}\t{uids}\n",
            encoding="utf-8",
        )
        (base / "cgroup").write_text(f"0::{cgroup}\n", encoding="utf-8")
        return base

    manager = f"/user.slice/user-{uid}.slice/user@{uid}.service/init.scope"
    fake(10, name="sshd-session", ppid=1, uids=0)
    cases = {
        fake(20, name="systemd", ppid=1, uids=uid, cgroup=manager): False,
        fake(21, name="(sd-pam)", ppid=20, uids=uid, cgroup=manager): False,
        fake(22, name="sshd-session", ppid=10, uids=uid): False,
        fake(23, name="bash", ppid=1, uids=uid, state="Z"): False,
        fake(24, name="kworker", ppid=2, uids=uid): False,
        fake(25, name="other", ppid=1, uids=uid + 1): False,
        fake(30, name="codex", ppid=1, uids=uid): True,  # an orphan is not session infrastructure
        fake(31, name="sshd-session", ppid=30, uids=uid): True,  # its parent is not the root sshd
        fake(32, name="worker", ppid=20, uids=uid, cgroup=manager.replace("init.scope", "a.scope")): True,
    }
    assert {base.name: _REAL_UNINSPECTABLE(base, proc) for base in cases} == {
        base.name: expected for base, expected in cases.items()
    }


def wrap_moves(
    monkeypatch: pytest.MonkeyPatch,
    *,
    before: Any = None,
    after: Any = None,
) -> list[tuple[Path, Path]]:
    """Run ``before(original)`` / ``after(quarantined)`` around the first ``git worktree move``."""
    real = rw.safe_git
    moves: list[tuple[Path, Path]] = []

    def spy(args: list[str], **kwargs: Any) -> Any:
        if args[:2] != ["worktree", "move"]:
            return real(args, **kwargs)
        source, destination = Path(args[2]), Path(args[3])
        moves.append((source, destination))
        first = len(moves) == 1
        if first and before is not None:
            before(source)
        result = real(args, **kwargs)
        if first and after is not None:
            after(destination / source.name)
        return result

    monkeypatch.setattr(rw, "safe_git", spy)
    return moves


def late_commit(tree: Path) -> None:
    (tree / "README.md").write_text("late commit\n", encoding="utf-8")
    git(tree, "commit", "-am", "late commit")


def late_file(tree: Path) -> None:
    (tree / "late.txt").write_text("late\n", encoding="utf-8")


_HOLDERS: list[subprocess.Popen[bytes]] = []


def late_process(tree: Path) -> None:
    _HOLDERS.append(subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"], cwd=tree))


@pytest.fixture
def holders():
    yield _HOLDERS
    for holder in _HOLDERS:
        holder.kill()
        holder.wait(timeout=30)
    _HOLDERS.clear()


@pytest.mark.parametrize("window", ["before_move", "after_move"])
@pytest.mark.parametrize(
    ("change", "reason"),
    [
        (late_commit, "late_change: last activity 0 min ago (< 60 min)"),  # the commit wrote HEAD
        (late_file, "late_change: dirty or untracked files"),
        (late_process, "late_change: in use: a process works inside the checkout"),
    ],
)
def test_late_change_around_the_quarantine_move_keeps_the_tree(
    repo: Path,
    free_fuser: Path,
    monkeypatch: pytest.MonkeyPatch,
    holders: list[Any],
    window: str,
    change: Any,
    reason: str,
) -> None:
    worktree = dispatch_tree(repo, detached=True)
    moves = wrap_moves(monkeypatch, **{window.removesuffix("_move"): change})

    report = rw.reap_clean_pushed(repo_root=repo, dry_run=False)

    outcome = outcome_for(report, worktree, repo)
    assert (outcome.action, outcome.reason) == ("skipped", reason)
    assert report.late_change == (SHOWN,)
    assert [source for source, _ in moves] == [worktree, moves[0][1] / worktree.name]  # out, then back
    assert worktree.is_dir() and quarantine_entries(repo) == []
    assert str(worktree) in git(repo, "worktree", "list", "--porcelain")
    if change is late_commit:
        assert git(worktree, "log", "-1", "--format=%s") == "late commit"
    assert abandon_log(repo) == []
    events = [json.loads(line)["event"] for line in reaper_lifecycle.journal_path(repo).read_text().splitlines()]
    assert events == ["clean-pushed-remove"]  # intent only: never confirmed


def test_failed_move_back_keeps_the_tree_in_the_quarantine_and_later_runs_report_it(
    repo: Path, free_fuser: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    worktree = dispatch_tree(repo, detached=True)
    real_safe_git = rw.safe_git

    def block_return(staged: Path) -> None:
        late_file(staged)
        worktree.mkdir()  # the original path exists again: no move back over it

    wrap_moves(monkeypatch, after=block_return)

    report = rw.reap_clean_pushed(repo_root=repo, dry_run=False)

    outcome = outcome_for(report, worktree, repo)
    assert outcome.action == "error"
    assert "kept in quarantine" in outcome.reason
    [holder] = quarantine_entries(repo)
    staged = holder / worktree.name
    assert (staged / "late.txt").exists() and (staged / "README.md").exists()

    worktree.rmdir()
    monkeypatch.setattr(rw, "safe_git", real_safe_git)
    later = rw.reap_clean_pushed(repo_root=repo)
    [kept] = [item for item in later.skipped if item.path.startswith(".worktrees/.reaping/")]
    assert kept.reason == "left in the reaper quarantine by an interrupted run; restore it (runbook)"
    assert staged.is_dir()


def origin(repo: Path) -> Path:
    return repo.parent / "origin.git"


def pushed_detached_tree(repo: Path) -> tuple[Path, str]:
    worktree = dispatch_tree(repo, detached=True)
    (worktree / "README.md").write_text("pushed to a side branch\n", encoding="utf-8")
    git(worktree, "commit", "-am", "side")
    git(worktree, "push", "origin", "HEAD:refs/heads/side")
    age_tree(worktree, repo, "task-a")
    return worktree, git(worktree, "rev-parse", "HEAD")


@pytest.mark.parametrize("change", ["delete", "force_move"])
def test_commit_gone_from_origin_behind_stale_tracking_refs_refuses(repo: Path, free_fuser: Path, change: str) -> None:
    worktree, head = pushed_detached_tree(repo)
    if change == "delete":
        git(origin(repo), "update-ref", "-d", "refs/heads/side")
    else:
        git(origin(repo), "update-ref", "refs/heads/side", git(repo, "rev-parse", "main"))
    assert git(repo, "rev-parse", "refs/remotes/origin/side") == head  # stale local proof

    assert _refusal(repo, worktree) == "commits not on origin"


def test_commit_still_on_origin_is_removed_after_the_fetch(repo: Path, free_fuser: Path) -> None:
    worktree, _head = pushed_detached_tree(repo)
    report = rw.reap_clean_pushed(repo_root=repo, dry_run=False)
    assert outcome_for(report, worktree, repo).action == "removed"


@pytest.mark.parametrize("dry_run", [True, False])
def test_failed_fetch_skips_the_whole_run(
    repo: Path, free_fuser: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str], dry_run: bool
) -> None:
    worktree = dispatch_tree(repo)
    git(repo, "remote", "set-url", "origin", str(tmp_path / "missing.git"))

    report = rw.reap_clean_pushed(repo_root=repo, dry_run=dry_run)

    assert report.refs_stale
    assert report.refusal == "refs_stale: git fetch --prune origin failed (exit 128)"
    assert report.removed == () and report.skipped == ()
    assert worktree.is_dir()
    assert rw.main(["--clean-pushed", "--repo-root", str(repo), *([] if dry_run else ["--apply"])]) == 0
    assert "nothing done: refs_stale" in capsys.readouterr().out


def test_fetch_timeout_skips_the_whole_run(repo: Path, free_fuser: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    worktree = dispatch_tree(repo)
    real_run = rw._run

    def slow_fetch(args: list[str], **kwargs: Any) -> Any:
        if args[:2] == ["git", "fetch"]:
            assert kwargs["timeout"] == 60.0
            raise subprocess.TimeoutExpired(args, kwargs["timeout"])
        return real_run(args, **kwargs)

    monkeypatch.setattr(rw, "_run", slow_fetch)
    report = rw.reap_clean_pushed(repo_root=repo, dry_run=False)
    assert report.refs_stale and report.refusal == "refs_stale: git fetch --prune origin timed out after 60s"
    assert worktree.is_dir()


def test_fetch_runs_before_the_reaper_lock_and_once(
    repo: Path, free_fuser: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    dispatch_tree(repo)
    events: list[str] = []
    real_run = rw._run
    real_enter = rw._ReapLock.__enter__

    def spy_run(args: list[str], **kwargs: Any) -> Any:
        if args[:2] == ["git", "fetch"]:
            events.append(" ".join(args))
        return real_run(args, **kwargs)

    def spy_enter(self: Any) -> None:
        events.append("lock")
        real_enter(self)

    monkeypatch.setattr(rw, "_run", spy_run)
    monkeypatch.setattr(rw._ReapLock, "__enter__", spy_enter)

    assert rw.main(["--clean-pushed", "--repo-root", str(repo)]) == 0

    assert events == ["git fetch --no-tags origin --prune", "lock"]
    assert "origin refs refreshed (git fetch --prune origin)" in capsys.readouterr().out


@pytest.mark.parametrize(
    "args",
    [
        ["worktree", "move", "relative", "/abs"],
        ["worktree", "move", "/abs"],
        ["worktree", "move", "--force", "/a", "/b"],
        ["worktree", "move", "-f", "/b"],
    ],
)
def test_safe_git_admits_only_a_plain_absolute_worktree_move(tmp_path: Path, args: list[str]) -> None:
    from scripts.orchestration.execution_safe_git import run_git

    with pytest.raises(ValueError, match="unsupported worktree move operation"):
        run_git(args, cwd=tmp_path)
