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
    assert events == ["clean-pushed-remove"]


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

    removes = [call for call in calls if call[:2] == ["worktree", "remove"]]
    assert removes == [["worktree", "remove", str(worktree)]]
    assert not worktree.exists()


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
    assert calls == [["worktree", "remove", str(worktree)]]
    assert worktree.exists()
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
    monkeypatch.setattr(rw, "_proc_users_inside", lambda root, *, deadline: None)
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
    # No network: the mode makes no GitHub call. Enforced in user managers (seccomp).
    assert "RestrictAddressFamilies=AF_UNIX" in lines
    assert "IPAddressDeny=any" in lines
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
