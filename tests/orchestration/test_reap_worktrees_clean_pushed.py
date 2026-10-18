"""Clean, fully pushed, idle dispatch worktree reaping (#10778).

Guard tests run real Git in temporary repositories with real linked
worktrees; only the ``fuser`` executable is substituted where a test must
control what it reports.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import stat
import subprocess
import sys
import threading
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


def _git_subcommand(args: list[str]) -> str | None:
    """The git verb in ``args``, skipping a leading ``git`` and ``-c`` overrides."""
    index = 1 if args[:1] == ["git"] else 0
    while index < len(args):
        if args[index] == "-c":
            index += 2
            continue
        if args[index].startswith("-"):
            index += 1
            continue
        return args[index]
    return None


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


_REFLOG_STAMP = re.compile(r"^((?:[0-9a-f]{40} [0-9a-f]{40}|[0-9a-f]{64} [0-9a-f]{64}) .+ )([0-9]+) ([+-][0-9]{4})$")


def _rewrite_reflog_stamps(path: Path, stamp: int) -> None:
    """Move each ``logs/HEAD`` entry's committer time; the file mtime is set by the caller."""
    text = path.read_text(encoding="utf-8")
    if not text.strip():
        return
    rewritten: list[str] = []
    for line in text.splitlines():
        header, sep, message = line.partition("\t")
        match = _REFLOG_STAMP.fullmatch(header)
        if match is None:
            rewritten.append(line)
            continue
        rewritten.append(f"{match.group(1)}{stamp} {match.group(3)}" + (sep + message if sep else ""))
    body = "\n".join(rewritten)
    if text.endswith("\n"):
        body += "\n"
    path.write_text(body, encoding="utf-8")


def age(paths: list[Path], seconds: float = TWO_HOURS) -> None:
    stamp = time.time() - seconds
    for path in paths:
        if not path.exists():
            continue
        if path.name == "HEAD" and path.parent.name == "logs":
            _rewrite_reflog_stamps(path, int(stamp))
        os.utime(path, (stamp, stamp))


def write_published_head_reflog(worktree: Path) -> None:
    """Replace an emptied ``logs/HEAD`` with one entry that names only the current HEAD."""
    head = git(worktree, "rev-parse", "HEAD")
    log = admin_dir(worktree) / "logs" / "HEAD"
    log.parent.mkdir(parents=True, exist_ok=True)
    log.write_text(
        f"{head} {head} Test User <tester@example.com> 1700000000 +0000\treset: moving to HEAD\n",
        encoding="utf-8",
    )


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


def test_reflog_file_rewritten_in_place_is_still_reaped(repo: Path, free_fuser: Path) -> None:
    """A gc-style rewrite refreshes ``logs/HEAD`` mtime and leaves old entries."""
    worktree = dispatch_tree(repo)
    log = admin_dir(worktree) / "logs" / "HEAD"
    original = log.read_bytes()
    assert b"\n" in original
    log.write_bytes(original)
    assert time.time() - log.stat().st_mtime < 60

    report = rw.reap_clean_pushed(repo_root=repo, dry_run=False)

    assert outcome_for(report, worktree, repo).action == "removed"
    assert not worktree.exists()


def test_new_reflog_entry_stays_active_when_the_file_mtime_is_old(repo: Path, free_fuser: Path) -> None:
    worktree = dispatch_tree(repo)
    log = admin_dir(worktree) / "logs" / "HEAD"
    text = log.read_text(encoding="utf-8")
    lines = text.splitlines()
    header, sep, message = lines[-1].partition("\t")
    match = _REFLOG_STAMP.fullmatch(header)
    assert match is not None
    lines[-1] = f"{match.group(1)}{int(time.time())} {match.group(3)}" + (sep + message if sep else "")
    body = "\n".join(lines)
    if text.endswith("\n"):
        body += "\n"
    log.write_text(body, encoding="utf-8")
    old = time.time() - TWO_HOURS
    os.utime(log, (old, old))

    assert _refusal(repo, worktree) == "last activity 0 min ago (< 60 min)"


@pytest.mark.parametrize("name", ["index", "HEAD"])
def test_fresh_head_or_index_mtime_stays_active(repo: Path, free_fuser: Path, name: str) -> None:
    worktree = dispatch_tree(repo)
    os.utime(admin_dir(worktree) / name)

    assert _refusal(repo, worktree) == "last activity 0 min ago (< 60 min)"


@pytest.mark.parametrize(
    ("content", "reason"),
    [
        ("", "logs/HEAD empty; activity unknown"),
        ("\n", "logs/HEAD empty; activity unknown"),
        ("not a reflog line\n", "logs/HEAD unparseable; activity unknown"),
        ("deadbeef 1700000000 +0000\n", "logs/HEAD unparseable; activity unknown"),
    ],
)
def test_empty_or_unparseable_head_reflog_is_not_reaped(
    repo: Path, free_fuser: Path, content: str, reason: str
) -> None:
    worktree = dispatch_tree(repo)
    log = admin_dir(worktree) / "logs" / "HEAD"
    log.write_text(content, encoding="utf-8")
    age(
        [
            admin_dir(worktree) / "HEAD",
            admin_dir(worktree) / "index",
            repo / "batch_state" / "tasks" / "task-a.json",
        ]
    )

    assert _refusal(repo, worktree) == reason


def _append_reflog_stamp(log: Path, stamp: int) -> None:
    text = log.read_text(encoding="utf-8")
    lines = [line for line in text.splitlines() if line.strip()]
    header, separator, message = lines[-1].partition("\t")
    match = _REFLOG_STAMP.fullmatch(header)
    assert match is not None
    entry = f"{match.group(1)}{stamp} {match.group(3)}"
    if separator:
        entry += f"{separator}{message}"
    log.write_text(text if text.endswith("\n") else text + "\n", encoding="utf-8")
    with log.open("a", encoding="utf-8") as handle:
        handle.write(entry + "\n")


def _keep_once(repo: Path, worktree: Path) -> None:
    """Apply once while the index is fresh so the reflog fingerprint is stored."""
    os.utime(admin_dir(worktree) / "index")
    report = rw.reap_clean_pushed(repo_root=repo, dry_run=False)
    outcome = outcome_for(report, worktree, repo)
    assert outcome.action == "skipped" and outcome.reason.startswith("last activity"), outcome
    watch = repo / "batch_state" / "worktree-reaper" / "head-reflog-watch.json"
    assert watch.is_file()
    assert watch.stat().st_mode & 0o777 == 0o600


def test_backdated_soft_reset_cannot_hide_reflog_activity(repo: Path, free_fuser: Path) -> None:
    """A backdated append on an already-old log is activity once the bytes were observed."""
    worktree = dispatch_tree(repo)
    _keep_once(repo, worktree)
    admin = admin_dir(worktree)
    env = git_env()
    env["GIT_COMMITTER_DATE"] = "2001-01-01T00:00:00+0000"
    proc = subprocess.run(
        ["git", "reset", "--soft", "HEAD"],
        cwd=worktree,
        env=env,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert proc.returncode == 0, proc.stderr
    age([admin / "HEAD", admin / "index", repo / "batch_state" / "tasks" / "task-a.json"])

    assert _refusal(repo, worktree).startswith("last activity")


def _observe_then_backdate(repo: Path, worktree: Path) -> None:
    """Store a fingerprint, age HEAD and the index, then append a backdated reset.

    The reset does not move those mtimes. The stored fingerprint makes the new
    bytes recent activity, so a dry run keeps the tree before the test breaks
    the watch.
    """
    _keep_once(repo, worktree)
    admin = admin_dir(worktree)
    age([admin / "HEAD", admin / "index", repo / "batch_state" / "tasks" / "task-a.json"])
    before = [(admin / name).stat().st_mtime_ns for name in ("HEAD", "index")]
    env = git_env()
    env["GIT_COMMITTER_DATE"] = "2001-01-01T00:00:00+0000"
    proc = subprocess.run(
        ["git", "reset", "--soft", "HEAD"],
        cwd=worktree,
        env=env,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert proc.returncode == 0, proc.stderr
    after = [(admin / name).stat().st_mtime_ns for name in ("HEAD", "index")]
    assert before == after
    report = rw.reap_clean_pushed(repo_root=repo, dry_run=True)
    outcome = outcome_for(report, worktree, repo)
    assert outcome.action == "skipped" and outcome.reason.startswith("last activity"), outcome
    assert worktree.is_dir()


def _kept_for_reason(repo: Path, worktree: Path, reason: str) -> None:
    """Dry run and apply both keep the tree for ``reason`` and write no abandon log."""
    for dry_run in (True, False):
        report = rw.reap_clean_pushed(repo_root=repo, dry_run=dry_run)
        outcome = outcome_for(report, worktree, repo)
        assert outcome.action == "skipped", outcome
        assert outcome.reason == reason, outcome
        assert worktree.is_dir()
    assert abandon_log(repo) == []


def test_parsed_watch_without_this_tree_is_still_first_sight(repo: Path, free_fuser: Path) -> None:
    """A successful read with no entry for this git dir is first sight, not a failure."""
    worktree = dispatch_tree(repo)
    watch = rw._head_reflog_watch_path(repo)
    watch.parent.mkdir(parents=True, mode=0o700)
    digest = "a" * 64
    watch.write_text(
        json.dumps(
            {
                "schema_version": "worktree-reaper-head-reflog.v1",
                "trees": {"/not/this/tree": {"sha256": digest, "entries": 1, "changed_at": None}},
            }
        )
        + "\n",
        encoding="utf-8",
    )
    report = rw.reap_clean_pushed(repo_root=repo, dry_run=True)
    assert outcome_for(report, worktree, repo).action == "would_remove"


@pytest.mark.parametrize(
    ("payload", "reason"),
    [
        ("{", "head reflog watch unparseable; activity unknown"),
        ("[]", "head reflog watch schema invalid; activity unknown"),
        ("null", "head reflog watch schema invalid; activity unknown"),
        (
            '{"schema_version": "worktree-reaper-head-reflog.v1", "trees": []}',
            "head reflog watch schema invalid; activity unknown",
        ),
        (
            '{"schema_version": "nope", "trees": {}}',
            "head reflog watch schema invalid; activity unknown",
        ),
        ('{"trees": {}}', "head reflog watch schema invalid; activity unknown"),
    ],
)
def test_bad_reflog_watch_body_keeps_a_backdated_reset(repo: Path, free_fuser: Path, payload: str, reason: str) -> None:
    worktree = dispatch_tree(repo)
    _observe_then_backdate(repo, worktree)
    watch = rw._head_reflog_watch_path(repo)
    watch.write_text(payload, encoding="utf-8")
    _kept_for_reason(repo, worktree, reason)
    assert watch.read_text(encoding="utf-8") == payload


@pytest.mark.parametrize("kind", ["sha256", "entries", "changed_at", "changed_at_text", "value"])
def test_wrong_watch_entry_type_keeps_a_backdated_reset(repo: Path, free_fuser: Path, kind: str) -> None:
    worktree = dispatch_tree(repo)
    _observe_then_backdate(repo, worktree)
    watch = rw._head_reflog_watch_path(repo)
    payload = json.loads(watch.read_text(encoding="utf-8"))
    key = next(iter(payload["trees"]))
    entry = payload["trees"][key]
    if kind == "sha256":
        entry["sha256"] = "nope"
    elif kind == "entries":
        entry["entries"] = True
    elif kind == "changed_at":
        entry["changed_at"] = -1
    elif kind == "changed_at_text":
        entry["changed_at"] = "1"
    else:
        payload["trees"][key] = []
    encoded = json.dumps(payload) + "\n"
    watch.write_text(encoded, encoding="utf-8")
    _kept_for_reason(repo, worktree, "head reflog watch schema invalid; activity unknown")
    assert watch.read_text(encoding="utf-8") == encoded


@pytest.mark.parametrize("kind", ["unreadable", "directory", "symlink", "fifo", "oversized"])
def test_unusable_reflog_watch_keeps_a_backdated_reset(repo: Path, free_fuser: Path, kind: str) -> None:
    if kind == "unreadable" and os.geteuid() == 0:
        pytest.skip("root reads mode-000 files")
    worktree = dispatch_tree(repo)
    _observe_then_backdate(repo, worktree)
    watch = rw._head_reflog_watch_path(repo)
    original = watch.read_bytes()
    if kind == "unreadable":
        watch.chmod(0)
    elif kind == "directory":
        watch.unlink()
        watch.mkdir()
    elif kind == "symlink":
        target = watch.with_name("watch-target.json")
        target.write_bytes(original)
        watch.unlink()
        watch.symlink_to(target.name)
    elif kind == "fifo":
        watch.unlink()
        os.mkfifo(watch)
    else:
        watch.write_bytes(b"x" * (rw._HEAD_REFLOG_MAX_BYTES + 1))
    reason = (
        "head reflog watch oversized; activity unknown"
        if kind == "oversized"
        else "head reflog watch unreadable; activity unknown"
    )
    try:
        _kept_for_reason(repo, worktree, reason)
        if kind == "unreadable":
            assert watch.stat().st_mode & 0o777 == 0
        elif kind == "directory":
            assert watch.is_dir() and not watch.is_symlink()
        elif kind == "symlink":
            assert watch.is_symlink()
        elif kind == "fifo":
            assert stat.S_ISFIFO(watch.lstat().st_mode)
        else:
            assert watch.stat().st_size > rw._HEAD_REFLOG_MAX_BYTES
    finally:
        if kind == "unreadable" and watch.exists():
            watch.chmod(0o600)


@pytest.mark.parametrize("kind", ["unreadable", "directory", "symlink", "fifo"])
def test_reflog_watch_lock_open_failure_keeps_a_backdated_reset(repo: Path, free_fuser: Path, kind: str) -> None:
    if kind == "unreadable" and os.geteuid() == 0:
        pytest.skip("root reads mode-000 files")
    worktree = dispatch_tree(repo)
    _observe_then_backdate(repo, worktree)
    watch = rw._head_reflog_watch_path(repo)
    original = watch.read_bytes()
    lock = watch.with_suffix(".lock")
    assert lock.is_file()
    if kind == "unreadable":
        lock.chmod(0)
    elif kind == "directory":
        lock.unlink()
        lock.mkdir()
    elif kind == "symlink":
        target = lock.with_name("lock-target")
        target.write_text("elsewhere\n", encoding="utf-8")
        lock.unlink()
        lock.symlink_to(target.name)
    else:
        lock.unlink()
        os.mkfifo(lock)
    try:
        _kept_for_reason(repo, worktree, "head reflog watch lock unavailable; activity unknown")
        assert watch.read_bytes() == original
    finally:
        if kind == "unreadable" and lock.exists():
            lock.chmod(0o600)


_LOCK_HOLDER = """\
import fcntl, os, sys, time
fd = os.open(sys.argv[1], os.O_RDWR | os.O_NOFOLLOW)
fcntl.flock(fd, fcntl.LOCK_EX)
sys.stdout.write("held\\n")
sys.stdout.flush()
time.sleep(60)
"""


def test_reflog_watch_lock_held_by_another_process_keeps_a_backdated_reset(
    repo: Path, free_fuser: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    assert rw._HEAD_REFLOG_LOCK_WAIT_S == 2.0
    wait_s = 0.3
    monkeypatch.setattr(rw, "_HEAD_REFLOG_LOCK_WAIT_S", wait_s)
    slept: list[float] = []
    real_sleep = time.sleep

    def spy_sleep(seconds: float) -> None:
        slept.append(seconds)
        real_sleep(seconds)

    monkeypatch.setattr(time, "sleep", spy_sleep)
    worktree = dispatch_tree(repo)
    _observe_then_backdate(repo, worktree)
    slept.clear()
    lock = rw._head_reflog_watch_path(repo).with_suffix(".lock")
    holder = subprocess.Popen(
        [sys.executable, "-c", _LOCK_HOLDER, str(lock)],
        stdout=subprocess.PIPE,
        text=True,
    )
    try:
        assert holder.stdout is not None
        assert holder.stdout.readline().strip() == "held"
        for dry_run in (True, False):
            box: dict[str, object] = {}

            def run(dry_run: bool = dry_run, box: dict[str, object] = box) -> None:
                try:
                    report = rw.reap_clean_pushed(repo_root=repo, dry_run=dry_run)
                    box["outcome"] = outcome_for(report, worktree, repo)
                except Exception as exc:
                    box["error"] = exc

            worker = threading.Thread(target=run)
            worker.start()
            worker.join(timeout=5)
            assert not worker.is_alive(), "reaper blocked on the fingerprint lock"
            error = box.get("error")
            if error is not None:
                raise error
            outcome = box["outcome"]
            assert isinstance(outcome, rw.CleanPushedOutcome)
            assert outcome.action == "skipped", outcome
            assert outcome.reason == "head reflog watch lock busy; activity unknown", outcome
            assert worktree.is_dir()
        assert sum(slept) >= (wait_s * 2) - 0.05
        assert abandon_log(repo) == []
    finally:
        holder.kill()
        holder.wait(timeout=5)


def test_recent_entry_then_backdated_entry_stays_active(repo: Path, free_fuser: Path) -> None:
    worktree = dispatch_tree(repo)
    log = admin_dir(worktree) / "logs" / "HEAD"
    _append_reflog_stamp(log, int(time.time()))
    _append_reflog_stamp(log, 978307200)
    old = time.time() - TWO_HOURS
    os.utime(log, (old, old))
    age(
        [
            admin_dir(worktree) / "HEAD",
            admin_dir(worktree) / "index",
            repo / "batch_state" / "tasks" / "task-a.json",
        ]
    )

    assert _refusal(repo, worktree) == "last activity 0 min ago (< 60 min)"


def test_identical_reflog_bytes_after_observation_are_still_reaped(repo: Path, free_fuser: Path) -> None:
    worktree = dispatch_tree(repo)
    _keep_once(repo, worktree)
    log = admin_dir(worktree) / "logs" / "HEAD"
    log.write_bytes(log.read_bytes())
    age(
        [
            admin_dir(worktree) / "HEAD",
            admin_dir(worktree) / "index",
            repo / "batch_state" / "tasks" / "task-a.json",
        ]
    )

    report = rw.reap_clean_pushed(repo_root=repo, dry_run=False)

    assert outcome_for(report, worktree, repo).action == "removed"
    assert not worktree.exists()


@pytest.mark.parametrize(
    ("kind", "reason"),
    [
        ("missing", "logs/HEAD missing; activity unknown"),
        ("unreadable", "logs/HEAD unreadable; activity unknown"),
        ("directory", "logs/HEAD unreadable; activity unknown"),
        ("symlink", "logs/HEAD unreadable; activity unknown"),
        ("fifo", "logs/HEAD unreadable; activity unknown"),
    ],
)
def test_unusable_head_reflog_is_not_reaped(repo: Path, free_fuser: Path, kind: str, reason: str) -> None:
    if kind == "unreadable" and os.geteuid() == 0:
        pytest.skip("root reads mode-000 files")
    worktree = dispatch_tree(repo)
    log = admin_dir(worktree) / "logs" / "HEAD"
    if kind == "missing":
        log.unlink()
    elif kind == "unreadable":
        log.chmod(0)
    elif kind == "directory":
        log.unlink()
        log.mkdir()
    elif kind == "symlink":
        target = log.parent / "not-a-log"
        target.write_text("elsewhere\n", encoding="utf-8")
        log.unlink()
        log.symlink_to(target.name)
    else:
        log.unlink()
        os.mkfifo(log)
    age(
        [
            admin_dir(worktree) / "HEAD",
            admin_dir(worktree) / "index",
            repo / "batch_state" / "tasks" / "task-a.json",
        ]
    )
    try:
        assert _refusal(repo, worktree) == reason
    finally:
        if kind == "unreadable" and log.exists():
            log.chmod(0o644)


def test_oversized_reflog_timestamp_does_not_abort_the_sweep(repo: Path, free_fuser: Path) -> None:
    worktree = dispatch_tree(repo)
    head = git(worktree, "rev-parse", "HEAD")
    log = admin_dir(worktree) / "logs" / "HEAD"
    log.write_text(
        f"{head} {head} Test User <tester@example.com> {'9' * 400} +0000\treset: moving to HEAD\n",
        encoding="utf-8",
    )
    age(
        [
            admin_dir(worktree) / "HEAD",
            admin_dir(worktree) / "index",
            repo / "batch_state" / "tasks" / "task-a.json",
        ]
    )

    assert _refusal(repo, worktree) == "logs/HEAD timestamp out of range; activity unknown"


def test_oversized_head_reflog_is_activity_unknown(repo: Path, free_fuser: Path) -> None:
    worktree = dispatch_tree(repo)
    log = admin_dir(worktree) / "logs" / "HEAD"
    log.write_bytes(b"x" * (rw._HEAD_REFLOG_MAX_BYTES + 1))
    age(
        [
            admin_dir(worktree) / "HEAD",
            admin_dir(worktree) / "index",
            repo / "batch_state" / "tasks" / "task-a.json",
        ]
    )

    assert _refusal(repo, worktree) == "logs/HEAD oversized; activity unknown"


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
REFLOG = "unpublished_reflog_commit: the recovery history names a commit no origin ref contains"
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


def unique_commit(worktree: Path) -> str:
    """An unpublished commit no ref names; only the HEAD reflog records it until that is expired."""
    tree = git(worktree, "rev-parse", "HEAD^{tree}")
    return git(worktree, "commit-tree", tree, "-p", "HEAD", "-m", "unique unpublished work")


def assert_kept_for_history(repo: Path, worktree: Path, reason: str = REFLOG) -> None:
    report = rw.reap_clean_pushed(repo_root=repo, dry_run=False)
    outcome = outcome_for(report, worktree, repo)
    assert (outcome.action, outcome.reason) == ("skipped", reason)
    assert report.unpublished_reflog_commit == (SHOWN,)
    assert worktree.is_dir() and abandon_log(repo) == []


@pytest.mark.parametrize("ref", ["refs/worktree/recovery", "refs/bisect/bad", "refs/rewritten/onto"])
def test_commit_only_in_a_per_worktree_ref_reflog_refuses(repo: Path, free_fuser: Path, ref: str) -> None:
    """The round-3 reproducer: the ref's tip is published, its reflog still names the unique commit."""
    worktree = dispatch_tree(repo, detached=True)
    (worktree / "README.md").write_text("unique\n", encoding="utf-8")
    git(worktree, "commit", "-am", "unique")
    unique = git(worktree, "rev-parse", "HEAD")
    git(worktree, "update-ref", "--create-reflog", ref, unique)
    git(worktree, "reset", "--hard", "main")
    git(worktree, "update-ref", "--create-reflog", ref, "HEAD")
    git(worktree, "reflog", "expire", "--expire=all", "HEAD")
    write_published_head_reflog(worktree)  # expire leaves logs/HEAD empty; activity would otherwise be unknown
    (admin_dir(worktree) / "ORIG_HEAD").unlink()  # isolate the per-worktree reflog as the only record
    assert unique not in git(worktree, "rev-list", "--walk-reflogs", "HEAD").split()
    assert unique in (admin_dir(worktree) / "logs" / ref).read_text(encoding="utf-8")
    age_tree(worktree, repo, "task-a")

    assert_kept_for_history(repo, worktree)
    assert unique in (admin_dir(worktree) / "logs" / ref).read_text(encoding="utf-8")


def test_commit_only_on_the_old_side_of_a_reflog_entry_refuses(repo: Path, free_fuser: Path) -> None:
    """Expiring older entries leaves the first remaining entry's old value as the only record."""
    worktree = dispatch_tree(repo, detached=True)
    unique = unique_commit(worktree)
    main = git(worktree, "rev-parse", "main")
    log = admin_dir(worktree) / "logs" / "refs" / "worktree" / "recovery"
    log.parent.mkdir(parents=True)
    log.write_text(f"{unique} {main} Test User <tester@example.com> 1700000000 +0000\treset\n", encoding="utf-8")
    age_tree(worktree, repo, "task-a")

    assert_kept_for_history(repo, worktree)


def test_commit_only_in_orig_head_refuses(repo: Path, free_fuser: Path) -> None:
    worktree = dispatch_tree(repo, detached=True)
    (worktree / "README.md").write_text("unique\n", encoding="utf-8")
    git(worktree, "commit", "-am", "unique")
    unique = git(worktree, "rev-parse", "HEAD")
    git(worktree, "reset", "--hard", "main")  # ORIG_HEAD now names the unique commit
    git(worktree, "reflog", "expire", "--expire=all", "HEAD")
    assert (admin_dir(worktree) / "ORIG_HEAD").read_text(encoding="utf-8").strip() == unique
    write_published_head_reflog(worktree)  # expire leaves logs/HEAD empty; activity would otherwise be unknown
    age_tree(worktree, repo, "task-a")

    assert_kept_for_history(repo, worktree)


@pytest.mark.parametrize(
    ("name", "content"),
    [
        ("MERGE_HEAD", "{main}\n{unique}\n"),
        ("CHERRY_PICK_HEAD", "{unique}\n"),
        ("REVERT_HEAD", "{unique}\n"),
        ("REBASE_HEAD", "{unique}\n"),
        ("FETCH_HEAD", "{main}\t\tbranch 'main' of origin\n{unique}\tnot-for-merge\tbranch 'gone' of origin\n"),
        ("BISECT_EXPECTED_REV", "{unique}\n"),  # any other all-caps file holding one object id
    ],
)
def test_commit_only_in_a_pseudoref_refuses(repo: Path, free_fuser: Path, name: str, content: str) -> None:
    worktree = dispatch_tree(repo, detached=True)
    unique = unique_commit(worktree)
    main = git(worktree, "rev-parse", "main")
    (admin_dir(worktree) / name).write_text(content.format(main=main, unique=unique), encoding="utf-8")
    age_tree(worktree, repo, "task-a")

    assert_kept_for_history(repo, worktree)


def test_published_pseudorefs_and_free_text_files_do_not_refuse(repo: Path, free_fuser: Path) -> None:
    worktree = dispatch_tree(repo, detached=True)
    main = git(worktree, "rev-parse", "main")
    git(worktree, "fetch", "origin")  # FETCH_HEAD names published commits
    git(worktree, "reset", "--hard", "HEAD")  # ORIG_HEAD names HEAD
    (admin_dir(worktree) / "COMMIT_EDITMSG").write_text("a message, not an object id\n", encoding="utf-8")
    git(worktree, "tag", "-a", "-m", "annotated", "wt-tag", "HEAD")
    git(worktree, "update-ref", "refs/worktree/tagged", git(worktree, "rev-parse", "wt-tag"))  # a tag of a commit
    git(worktree, "tag", "-d", "wt-tag")
    assert (admin_dir(worktree) / "ORIG_HEAD").read_text(encoding="utf-8").strip() == main
    assert (admin_dir(worktree) / "FETCH_HEAD").is_file()
    age_tree(worktree, repo, "task-a")

    report = rw.reap_clean_pushed(repo_root=repo, dry_run=False)

    assert outcome_for(report, worktree, repo).action == "removed", report
    assert report.unpublished_reflog_commit == ()


@pytest.mark.parametrize(
    ("relative", "content", "why"),
    [
        ("logs/refs/worktree/recovery", "not a reflog line\n", "logs/refs/worktree/recovery unreadable or unparseable"),
        ("ORIG_HEAD", "deadbeef\n", "ORIG_HEAD unreadable or unparseable"),
        ("FETCH_HEAD", "garbage\tbranch 'main' of origin\n", "FETCH_HEAD unreadable or unparseable"),
        ("refs/worktree/broken", "not an object id\n", "refs/worktree/broken unreadable or unparseable"),
    ],
)
def test_unparseable_recovery_record_keeps_the_tree(
    repo: Path, free_fuser: Path, relative: str, content: str, why: str
) -> None:
    worktree = dispatch_tree(repo, detached=True)
    target = admin_dir(worktree) / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    age_tree(worktree, repo, "task-a")

    assert_kept_for_history(repo, worktree, f"unpublished_reflog_commit: recovery history unknown ({why})")


@pytest.mark.skipif(os.geteuid() == 0, reason="root reads mode-000 files")
def test_unreadable_reflog_keeps_the_tree(repo: Path, free_fuser: Path) -> None:
    worktree = dispatch_tree(repo, detached=True)
    log = admin_dir(worktree) / "logs" / "HEAD"
    age_tree(worktree, repo, "task-a")
    log.chmod(0)
    try:
        report = rw.reap_clean_pushed(repo_root=repo, dry_run=False)
    finally:
        log.chmod(0o644)
    outcome = outcome_for(report, worktree, repo)
    assert outcome.action == "skipped" and "logs/HEAD unreadable" in outcome.reason, outcome
    assert worktree.is_dir()


@pytest.mark.parametrize(
    ("kind", "reason"),
    [
        ("missing", "unpublished_reflog_commit: the recovery history names an object missing locally"),
        ("tree", "unpublished_reflog_commit: the recovery history names an object that is not a commit"),
        ("tag_of_tree", "unpublished_reflog_commit: the recovery history names an object that is not a commit"),
    ],
)
def test_missing_or_non_commit_recovery_object_keeps_the_tree(
    repo: Path, free_fuser: Path, kind: str, reason: str
) -> None:
    """``git rev-list`` accepts a tree, or a tag of one, and prints nothing: it would look published."""
    worktree = dispatch_tree(repo, detached=True)
    oid = "1" * 40 if kind == "missing" else git(worktree, "rev-parse", "HEAD^{tree}")
    if kind == "tag_of_tree":
        git(worktree, "tag", "-a", "-m", "a tree", "tree-tag", oid)
        oid = git(worktree, "rev-parse", "tree-tag")
        git(worktree, "tag", "-d", "tree-tag")
    (admin_dir(worktree) / "AUTO_MERGE").write_text(f"{oid}\n", encoding="utf-8")
    age_tree(worktree, repo, "task-a")

    assert_kept_for_history(repo, worktree, reason)


PENDING = "pending_operation_state"


def published_fork(worktree: Path) -> tuple[str, str]:
    """Two published commits on ``main`` that both change README.md; the detached checkout stays at ``mine``."""
    commits = []
    for name in ("theirs", "mine"):
        git(worktree, "checkout", "-q", "--detach", "main")
        (worktree / "README.md").write_text(f"{name}\n", encoding="utf-8")
        git(worktree, "commit", "-qam", name)
        git(worktree, "push", "-q", "origin", f"HEAD:refs/heads/{name}")
        commits.append(git(worktree, "rev-parse", "HEAD"))
    return commits[0], commits[1]


def assert_kept_for_pending_operation(repo: Path, worktree: Path, entries: str) -> None:
    assert git(worktree, "status", "--porcelain", "--untracked-files=all") == ""
    age_tree(worktree, repo, "task-a")
    report = rw.reap_clean_pushed(repo_root=repo, dry_run=False)
    outcome = outcome_for(report, worktree, repo)
    assert (outcome.action, outcome.reason) == ("skipped", f"{PENDING}: {entries}"), outcome
    assert report.unpublished_reflog_commit == ()  # every commit the history scan reads is published
    assert worktree.is_dir() and abandon_log(repo) == []


@pytest.mark.parametrize("stop", ["conflict", "exec"])
def test_rebase_autostash_keeps_the_tree(repo: Path, free_fuser: Path, stop: str) -> None:
    """The round-4 blocker: the only pointer to the stashed edit is ``rebase-merge/autostash``."""
    worktree = dispatch_tree(repo, detached=True)
    theirs, _mine = published_fork(worktree)
    (worktree / "README.md").write_text("UNPUBLISHED AUTOSTASH CONTENT\n", encoding="utf-8")
    args = [theirs] if stop == "conflict" else ["--exec", "false", "HEAD~1"]
    proc = subprocess.run(
        ["git", "rebase", "--autostash", *args],
        cwd=worktree,
        capture_output=True,
        env=git_env(),
        check=False,
        timeout=30,
    )
    assert proc.returncode != 0  # stopped
    if stop == "conflict":
        git(worktree, "reset", "-q", "--hard")  # the conflict discarded; the rebase stays pending
    autostash = (admin_dir(worktree) / "rebase-merge" / "autostash").read_text(encoding="utf-8").strip()
    assert git(worktree, "show", f"{autostash}:README.md") == "UNPUBLISHED AUTOSTASH CONTENT"

    assert_kept_for_pending_operation(
        repo, worktree, "REBASE_HEAD, rebase-merge" if stop == "conflict" else "rebase-merge"
    )
    assert (admin_dir(worktree) / "rebase-merge" / "autostash").read_text(encoding="utf-8").strip() == autostash


def test_interrupted_cherry_pick_sequence_keeps_the_tree(repo: Path, free_fuser: Path) -> None:
    worktree = dispatch_tree(repo, detached=True)
    theirs, mine = published_fork(worktree)
    proc = subprocess.run(
        ["git", "cherry-pick", theirs, mine], cwd=worktree, capture_output=True, env=git_env(), check=False, timeout=30
    )
    assert proc.returncode != 0  # the first pick conflicts
    git(worktree, "reset", "-q", "--hard")  # drops CHERRY_PICK_HEAD; the sequence stays pending

    assert_kept_for_pending_operation(repo, worktree, "sequencer")


def test_bisect_in_progress_keeps_the_tree(repo: Path, free_fuser: Path) -> None:
    worktree = dispatch_tree(repo, detached=True)
    _theirs, mine = published_fork(worktree)
    git(worktree, "bisect", "start", mine, "main")

    entries = sorted(path.name for path in admin_dir(worktree).iterdir() if path.name.startswith("BISECT_"))
    assert {"BISECT_LOG", "BISECT_START"} <= set(entries)
    assert_kept_for_pending_operation(repo, worktree, ", ".join(entries))


@pytest.mark.parametrize(
    ("relative", "content"),
    [
        ("MERGE_HEAD", "{main}\n"),
        ("CHERRY_PICK_HEAD", "{main}\n"),
        ("REVERT_HEAD", "{main}\n"),
        ("REBASE_HEAD", "{main}\n"),
        ("BISECT_LOG", "git bisect start\n"),
        ("BISECT_START", "main\n"),
        ("MERGE_MSG", "Merge branch 'x'\n"),
        ("rebase-apply/autostash", "{main}\n"),
        ("rebase-merge/autostash", "{main}\n"),
        ("sequencer/todo", "pick {main} base\n"),
        ("index.lock", ""),
        ("logs/HEAD.lock", ""),
        ("refs/worktree/keep.lock", "{main}\n"),  # a ref being written: the history scan reads it
        ("info/attributes", "* -text\n"),
        ("some-tool-state", "unknown\n"),
        ("some-tool-dir/state", "unknown\n"),
    ],
)
def test_operation_state_or_unknown_entry_keeps_the_tree(
    repo: Path, free_fuser: Path, relative: str, content: str
) -> None:
    worktree = dispatch_tree(repo, detached=True)
    target = admin_dir(worktree) / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content.format(main=git(worktree, "rev-parse", "main")), encoding="utf-8")
    first = relative.split("/")[0]
    shown = relative if first in {"logs", "refs", "info"} else first

    assert_kept_for_pending_operation(repo, worktree, shown)


@pytest.mark.parametrize(
    ("relative", "kind"),
    [
        ("info", "file"),
        ("info/sparse-checkout", "directory"),
        ("config.worktree", "directory"),
        ("config.worktree", "symlink"),
    ],
)
def test_inert_name_of_the_wrong_kind_keeps_the_tree(repo: Path, free_fuser: Path, relative: str, kind: str) -> None:
    worktree = dispatch_tree(repo, detached=True)
    entry = admin_dir(worktree) / relative
    entry.parent.mkdir(exist_ok=True)
    if kind == "file":
        entry.write_text("not a directory\n", encoding="utf-8")
    elif kind == "directory":
        entry.mkdir()
    else:
        entry.symlink_to(admin_dir(worktree) / "HEAD")

    assert_kept_for_pending_operation(repo, worktree, relative)


def test_sparse_checkout_layout_is_removable(repo: Path, free_fuser: Path) -> None:
    """Positive control: the inert entries of a finished dispatch checkout (sparse, fetched, reset, committed)."""
    worktree = dispatch_tree(repo)
    git(worktree, "sparse-checkout", "set", "--no-cone", "/*")
    (worktree / "README.md").write_text("pushed\n", encoding="utf-8")
    git(worktree, "commit", "-qam", "pushed")  # COMMIT_EDITMSG
    git(worktree, "push", "-q", "-u", "origin", "codex/task-a")
    git(worktree, "fetch", "-q", "origin")  # FETCH_HEAD
    git(worktree, "reset", "-q", "--hard", "HEAD")  # ORIG_HEAD
    admin = admin_dir(worktree)
    assert {path.name for path in admin.iterdir()} == {
        "COMMIT_EDITMSG",
        "FETCH_HEAD",
        "HEAD",
        "ORIG_HEAD",
        "commondir",
        "config.worktree",
        "gitdir",
        "index",
        "info",
        "logs",
        "refs",
    }
    assert [path.name for path in (admin / "info").iterdir()] == ["sparse-checkout"]
    age_tree(worktree, repo, "task-a")

    report = rw.reap_clean_pushed(repo_root=repo, dry_run=False)

    assert outcome_for(report, worktree, repo).action == "removed", report


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


@pytest.mark.skipif(not sys.platform.startswith("linux"), reason="prctl and /proc are Linux")
@pytest.mark.skipif(os.geteuid() == 0, reason="root inspects non-dumpable processes")
def test_uninspectable_process_that_is_pid_2_of_a_namespace_keeps_every_tree(
    repo: Path, free_fuser: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """In a PID namespace pid 2 is an ordinary process (#10778 round 4 reproducer).

    The process table is a view in which the non-dumpable holder is pid 2,
    as it is for a runner started second in a container.
    """
    worktree = dispatch_tree(repo)
    other = dispatch_tree(repo, "task-b")
    proc = tmp_path / "namespace-proc"
    proc.mkdir()
    real_scan = rw._proc_users_inside
    monkeypatch.setattr(rw, "_proc_users_inside", lambda root, **kw: real_scan(root, **{**kw, "proc_root": proc}))
    holder = subprocess.Popen(
        [sys.executable, "-c", _NON_DUMPABLE_HOLDER, str(worktree / "README.md")],
        cwd=tmp_path,
        stdout=subprocess.PIPE,
        text=True,
    )
    try:
        assert holder.stdout is not None and holder.stdout.readline().strip() == "ready"
        (proc / "2").symlink_to(f"/proc/{holder.pid}")
        _UNINSPECTABLE_IN_SCOPE.add(2)

        report = rw.reap_clean_pushed(repo_root=repo, dry_run=False)
    finally:
        holder.kill()
        holder.wait(timeout=30)

    for tree in (worktree, other):
        outcome = outcome_for(report, tree, repo)
        assert (outcome.action, outcome.reason) == (
            "skipped",
            "uninspectable_process 2: a process of this user cannot be inspected",
        )
        assert tree.is_dir()
    assert report.uninspectable == (2,)


def fake_process(
    proc: Path,
    pid: int,
    *,
    name: str,
    ppid: int,
    uids: int,
    state: str = "S",
    cgroup: str = "/lu.scope",
    flags: int = 0x00400100,  # PF_RANDOMIZE | PF_FORKNOEXEC: an ordinary userspace process
    stat_line: str | None = None,
) -> Path:
    """A ``/proc/<pid>`` with the ``status``, ``stat`` and ``cgroup`` files the classification reads."""
    base = proc / str(pid)
    base.mkdir(parents=True)
    (base / "status").write_text(
        f"Name:\t{name}\nState:\t{state} (x)\nPPid:\t{ppid}\nUid:\t{uids}\t{uids}\t{uids}\t{uids}\n",
        encoding="utf-8",
    )
    if stat_line is None:
        stat_line = f"{pid} ({name}) {state} {ppid} {pid} {pid} 0 -1 {flags} 0 0 0 0 0 0 0 0 20 0 1 0 100\n"
    (base / "stat").write_text(stat_line, encoding="utf-8")
    (base / "cgroup").write_text(f"0::{cgroup}\n", encoding="utf-8")
    return base


@pytest.mark.skipif(not sys.platform.startswith("linux"), reason="/proc is Linux")
def test_session_infrastructure_and_dead_or_foreign_processes_are_not_uninspectable(tmp_path: Path) -> None:
    proc = tmp_path / "proc"
    uid = os.getuid()
    manager = f"/user.slice/user-{uid}.slice/user@{uid}.service/init.scope"
    fake_process(proc, 10, name="sshd-session", ppid=1, uids=0)
    cases = {
        fake_process(proc, 20, name="systemd", ppid=1, uids=uid, cgroup=manager): False,
        fake_process(proc, 21, name="(sd-pam)", ppid=20, uids=uid, cgroup=manager): False,
        fake_process(proc, 22, name="sshd-session", ppid=10, uids=uid): False,
        fake_process(proc, 23, name="bash", ppid=1, uids=uid, state="Z"): False,
        fake_process(proc, 24, name="kworker/0:1", ppid=2, uids=uid, flags=0x04208060): False,  # PF_KTHREAD set
        fake_process(proc, 25, name="other", ppid=1, uids=uid + 1): False,
        fake_process(proc, 30, name="codex", ppid=1, uids=uid): True,  # an orphan is not session infrastructure
        fake_process(proc, 31, name="sshd-session", ppid=30, uids=uid): True,  # its parent is not the root sshd
        fake_process(proc, 32, name="worker", ppid=20, uids=uid, cgroup=manager.replace("init.scope", "a.scope")): True,
    }
    assert {base.name: _REAL_UNINSPECTABLE(base, proc) for base in cases} == {
        base.name: expected for base, expected in cases.items()
    }


@pytest.mark.skipif(not sys.platform.startswith("linux"), reason="/proc is Linux")
def test_kernel_threads_are_identified_by_the_stat_flag_never_by_pid_number(tmp_path: Path) -> None:
    """A PID namespace's pid 2 and its children are userspace; only ``PF_KTHREAD`` marks a kernel thread."""
    proc = tmp_path / "proc"
    uid = os.getuid()
    cases = {
        fake_process(proc, 2, name="pytest", ppid=1, uids=uid): True,  # namespace pid 2
        fake_process(proc, 40, name="python", ppid=2, uids=uid): True,  # a child of namespace pid 2
        fake_process(proc, 41, name="kthreadd", ppid=0, uids=uid, flags=0x00208040): False,
        # ``comm`` with spaces and parentheses: the fields follow the LAST ``)``. A parser
        # splitting at the first ``)`` would read state ``Z`` (zombie) here.
        fake_process(
            proc, 42, name="x", ppid=1, uids=uid, stat_line="42 (x) Z 1 (y) S 1 42 42 0 -1 4194560 0 0 0 0\n"
        ): True,
        # ... and would read the PF_KTHREAD bit in the flags position here.
        fake_process(
            proc, 43, name="x", ppid=1, uids=uid, stat_line="43 (a) S 1 1 1 0 -1 2097152 b) S 1 43 43 0 -1 0 0 0\n"
        ): True,
        fake_process(proc, 44, name="x", ppid=1, uids=uid, stat_line="44 (no closing parenthesis S 1\n"): True,
        fake_process(proc, 45, name="x", ppid=1, uids=uid, stat_line="45 (x) S 1 45 45 0 -1 notanumber\n"): True,
        fake_process(proc, 46, name="x", ppid=1, uids=uid, stat_line="46 (x) Z 1 46 46 0 -1 4194560 0\n"): False,
    }
    gone = fake_process(proc, 47, name="x", ppid=1, uids=uid)
    (gone / "stat").unlink()  # exited between the two reads
    cases[gone] = False
    assert {base.name: _REAL_UNINSPECTABLE(base, proc) for base in cases} == {
        base.name: expected for base, expected in cases.items()
    }
    assert rw._stat_kind(proc / "41") == "kernel" and rw._stat_kind(proc / "42") == "user"


@pytest.mark.skipif(not Path("/proc/2/stat").exists(), reason="no host kernel thread visible")
def test_a_real_kernel_thread_stat_line_is_a_kernel_thread() -> None:
    real = Path("/proc/2/stat").read_text(encoding="utf-8")
    flags = int(real.rpartition(")")[2].split()[6])
    if not flags & rw._PF_KTHREAD:
        pytest.skip("pid 2 is not kthreadd here (a PID namespace)")
    assert rw._stat_kind(Path("/proc/2")) == "kernel"


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


def late_ignored(tree: Path) -> None:
    """Ignored output written after artifact preservation: no Git guard sees it."""
    (tree / "out").mkdir(exist_ok=True)
    (tree / "out" / "evidence.txt").write_text("unpreserved evidence\n", encoding="utf-8")


def late_hidden(tree: Path) -> None:
    """An edit behind assume-unchanged (see ``flag_for``): Git status and Git removal both trust the flag."""
    (tree / "README.md").write_text("unsaved hidden edit\n", encoding="utf-8")


def flag_for(change: Any, worktree: Path, repo: Path) -> None:
    """``late_hidden`` edits a file that was flagged assume-unchanged before the tree went idle."""
    if change is late_hidden:
        git(worktree, "update-index", "--assume-unchanged", "README.md")
        age_tree(worktree, repo, "task-a")


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
        (late_hidden, f"late_change: {HIDDEN}"),
        (late_ignored, "late_change: final re-check: content changed since the pre-preservation manifest"),
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
    flag_for(change, worktree, repo)
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
    if change is late_ignored:
        assert (worktree / "out" / "evidence.txt").read_text(encoding="utf-8") == "unpreserved evidence\n"
    if change is late_hidden:
        assert (worktree / "README.md").read_text(encoding="utf-8") == "unsaved hidden edit\n"
    assert abandon_log(repo) == []
    events = [json.loads(line)["event"] for line in reaper_lifecycle.journal_path(repo).read_text().splitlines()]
    assert events == ["clean-pushed-remove"]  # intent only: never confirmed


def test_failed_move_back_keeps_the_tree_in_the_quarantine_and_a_later_run_restores_it(
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

    monkeypatch.setattr(rw, "safe_git", real_safe_git)
    (worktree / "replacement.txt").write_text("a new checkout\n", encoding="utf-8")
    occupied = rw.reap_clean_pushed(repo_root=repo, dry_run=False)
    [kept] = [item for item in occupied.skipped if item.path.startswith(".worktrees/.reaping/")]
    assert (
        kept.reason == "quarantine: kept: its original path exists again and is never overwritten; inspect it (runbook)"
    )
    assert staged.is_dir() and (worktree / "replacement.txt").exists()  # the replacement is untouched

    (worktree / "replacement.txt").unlink()
    worktree.rmdir()
    dry = rw.reap_clean_pushed(repo_root=repo)
    assert outcome_for(dry, worktree, repo).reason == "would restore it from the reaper quarantine (interrupted run)"
    assert staged.is_dir() and not worktree.exists()

    restored = rw.reap_clean_pushed(repo_root=repo, dry_run=False)
    outcome = outcome_for(restored, worktree, repo)
    assert (outcome.action, outcome.reason) == (
        "skipped",
        "restored from the reaper quarantine (interrupted run); kept this run",
    )
    assert (worktree / "late.txt").exists() and str(worktree) in git(repo, "worktree", "list", "--porcelain")
    assert quarantine_entries(repo) == []


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
        if _git_subcommand(args) == "fetch":
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
        if _git_subcommand(args) in {"fetch", "ls-remote"}:
            events.append(" ".join(args))
        return real_run(args, **kwargs)

    def spy_enter(self: Any) -> None:
        events.append("lock")
        real_enter(self)

    monkeypatch.setattr(rw, "_run", spy_run)
    monkeypatch.setattr(rw._ReapLock, "__enter__", spy_enter)

    assert rw.main(["--clean-pushed", "--repo-root", str(repo)]) == 0

    assert events == ["git fetch --no-tags origin --prune", "git ls-remote --heads --tags origin", "lock"]
    assert (
        "origin refs refreshed (git fetch --prune origin); "
        "origin census: 1 heads and tags (git ls-remote), 0 missing locally"
    ) in capsys.readouterr().out


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


# Round 3 (#10778): publication proof from a fresh census of origin, a final
# re-check before Git, crash recovery from the quarantine record, and the
# documented residual of arrivals during the Git removal call itself.


def narrow_fetch(repo: Path) -> None:
    """Fetch only main: every other remote-tracking ref goes stale."""
    git(repo, "config", "--replace-all", "remote.origin.fetch", "+refs/heads/main:refs/remotes/origin/main")


@pytest.mark.parametrize("change", ["delete", "force_move"])
def test_narrowed_fetch_refspec_cannot_prove_a_commit_gone_from_origin(
    repo: Path, free_fuser: Path, change: str
) -> None:
    worktree, head = pushed_detached_tree(repo)
    narrow_fetch(repo)
    if change == "delete":
        git(origin(repo), "update-ref", "-d", "refs/heads/side")
    else:
        git(origin(repo), "update-ref", "refs/heads/side", git(repo, "rev-parse", "main"))

    assert _refusal(repo, worktree) == "commits not on origin"
    assert git(repo, "rev-parse", "refs/remotes/origin/side") == head  # the fetch left the stale proof in place


def test_narrowed_fetch_refspec_cannot_prove_a_reflog_commit(repo: Path, free_fuser: Path) -> None:
    worktree, pushed = pushed_detached_tree(repo)
    git(worktree, "checkout", "--detach", "main")  # the side commit stays in the HEAD reflog only
    age_tree(worktree, repo, "task-a")
    narrow_fetch(repo)
    git(origin(repo), "update-ref", "refs/heads/side", git(repo, "rev-parse", "main"))
    assert git(repo, "rev-parse", "refs/remotes/origin/side") == pushed

    assert _refusal(repo, worktree) == REFLOG


def test_commit_published_only_by_an_annotated_tag_is_removed(repo: Path, free_fuser: Path) -> None:
    worktree, head = pushed_detached_tree(repo)
    git(worktree, "tag", "-a", "v-side", "-m", "release", head)
    git(worktree, "push", "origin", "refs/tags/v-side")
    git(origin(repo), "update-ref", "-d", "refs/heads/side")
    narrow_fetch(repo)
    assert git(repo, "cat-file", "-t", "v-side") == "tag"  # proof needs the peeled commit

    report = rw.reap_clean_pushed(repo_root=repo, dry_run=False)

    assert outcome_for(report, worktree, repo).action == "removed"
    assert report.census_refs == 2 and report.census_missing == 0  # main and v-side


def test_advertised_object_missing_locally_keeps_the_tree_as_refs_stale(
    repo: Path, free_fuser: Path, tmp_path: Path
) -> None:
    worktree, head = pushed_detached_tree(repo)
    other = tmp_path / "other"
    git(tmp_path, "clone", "--quiet", str(origin(repo)), str(other))
    git(other, "checkout", "--quiet", "side")
    (other / "README.md").write_text("built on the side commit elsewhere\n", encoding="utf-8")
    git(other, "-c", "user.email=o@example.com", "-c", "user.name=Other", "commit", "-qam", "on top")
    git(other, "push", "--quiet", "origin", "side")  # origin's side now contains the tree's HEAD, unseen here
    narrow_fetch(repo)
    assert git(repo, "rev-parse", "refs/remotes/origin/side") == head

    report = rw.reap_clean_pushed(repo_root=repo, dry_run=False)

    outcome = outcome_for(report, worktree, repo)
    assert (outcome.action, outcome.reason) == (
        "skipped",
        "refs_stale: publication unproven; 1 advertised origin object(s) missing locally",
    )
    assert report.census_missing == 1 and worktree.is_dir()


@pytest.mark.parametrize(
    ("stdout", "returncode", "reason"),
    [
        ("", 128, "refs_stale: git ls-remote --heads --tags origin failed (exit 128)"),
        (
            "not-an-oid\trefs/heads/main\n",
            0,
            "refs_stale: git ls-remote --heads --tags origin printed an unexpected line",
        ),
        (
            f"{'a' * 40}\trefs/pull/1/head\n",
            0,
            "refs_stale: git ls-remote --heads --tags origin printed an unexpected line",
        ),
    ],
)
def test_failed_or_unexpected_census_skips_the_whole_run(
    repo: Path, free_fuser: Path, monkeypatch: pytest.MonkeyPatch, stdout: str, returncode: int, reason: str
) -> None:
    worktree = dispatch_tree(repo)
    real_run = rw._run

    def census(args: list[str], **kwargs: Any) -> Any:
        if args[:2] == ["git", "ls-remote"]:
            return subprocess.CompletedProcess(args, returncode, stdout, "")
        return real_run(args, **kwargs)

    monkeypatch.setattr(rw, "_run", census)
    report = rw.reap_clean_pushed(repo_root=repo, dry_run=False)
    assert report.refs_stale and report.refusal == reason
    assert report.removed == () and report.skipped == () and worktree.is_dir()


def test_census_timeout_skips_the_whole_run(repo: Path, free_fuser: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    worktree = dispatch_tree(repo)
    real_run = rw._run

    def slow(args: list[str], **kwargs: Any) -> Any:
        if args[:2] == ["git", "ls-remote"]:
            assert kwargs["timeout"] == 60.0
            raise subprocess.TimeoutExpired(args, kwargs["timeout"])
        return real_run(args, **kwargs)

    monkeypatch.setattr(rw, "_run", slow)
    report = rw.reap_clean_pushed(repo_root=repo, dry_run=False)
    assert report.refusal == "refs_stale: git ls-remote --heads --tags origin timed out after 60s"
    assert worktree.is_dir()


def wrap_final_recheck(monkeypatch: pytest.MonkeyPatch, change: Any) -> None:
    """Run ``change(quarantined)`` after every guard re-ran on the quarantined tree, just before the final re-check."""
    real = rw._final_recheck

    def spy(tree: Path, baseline: Any) -> str | None:
        change(tree)
        return real(tree, baseline)

    monkeypatch.setattr(rw, "_final_recheck", spy)


@pytest.mark.parametrize(
    ("change", "reason"),
    [
        (late_hidden, "late_change: final re-check: content changed since the pre-preservation manifest"),
        (late_ignored, "late_change: final re-check: content changed since the pre-preservation manifest"),
        (late_commit, "late_change: final re-check: content changed since the pre-preservation manifest"),
        (late_process, "late_change: final re-check: in use: a process works inside the checkout"),
    ],
)
def test_final_recheck_keeps_a_tree_that_changed_after_the_full_reverification(
    repo: Path, free_fuser: Path, monkeypatch: pytest.MonkeyPatch, holders: list[Any], change: Any, reason: str
) -> None:
    worktree = dispatch_tree(repo, detached=True)
    flag_for(change, worktree, repo)
    wrap_final_recheck(monkeypatch, change)

    report = rw.reap_clean_pushed(repo_root=repo, dry_run=False)

    outcome = outcome_for(report, worktree, repo)
    assert (outcome.action, outcome.reason) == ("skipped", reason)
    assert worktree.is_dir() and quarantine_entries(repo) == []  # moved back, record cleared
    if change is late_ignored:
        assert (worktree / "out" / "evidence.txt").exists()
    if change is late_hidden:
        assert (worktree / "README.md").read_text(encoding="utf-8") == "unsaved hidden edit\n"
    if change is late_commit:
        assert git(worktree, "log", "-1", "--format=%s") == "late commit"
    assert abandon_log(repo) == []


def test_final_recheck_refuses_unknown_process_visibility(repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    worktree = dispatch_tree(repo)
    baseline = rw._manifest(worktree)
    assert rw._final_recheck(worktree, baseline) is None

    monkeypatch.setattr(rw, "_proc_users_inside", lambda root, **kwargs: None)
    assert rw._final_recheck(worktree, baseline) == "process visibility unknown"

    def denied(root: Path, *, uninspectable: list[int], **kwargs: Any) -> bool:
        uninspectable.append(4242)
        return False

    monkeypatch.setattr(rw, "_proc_users_inside", denied)
    assert rw._final_recheck(worktree, baseline) == (
        "uninspectable_process 4242: a process of this user cannot be inspected"
    )


def test_final_recheck_never_counts_the_reapers_own_handles(repo: Path) -> None:
    worktree = dispatch_tree(repo)
    git(worktree, "update-index", "--assume-unchanged", "README.md")
    baseline = rw._manifest(worktree)
    assert rw._hidden_change_refusal(worktree) is None  # the reaper just opened and hashed the flagged file

    assert rw._final_recheck(worktree, baseline) is None

    # A handle the caller's process holds is not the reaper's: dispatch admission
    # runs the reaper in-process, so it still counts.
    with (worktree / "README.md").open("rb"):
        assert rw._final_recheck(worktree, baseline) == "in use: a process works inside the checkout"


def at_the_git_call(monkeypatch: pytest.MonkeyPatch, change: Any) -> list[Path]:
    """Run ``change(quarantined)`` once every check has passed, as the non-forced ``git worktree remove`` starts."""
    real = worktree_claims.safe_git
    seen: list[Path] = []

    def spy(args: list[str], **kwargs: Any) -> Any:
        if args[:2] == ["worktree", "remove"]:
            assert "--force" not in args
            seen.append(Path(args[-1]))
            change(Path(args[-1]))
        return real(args, **kwargs)

    monkeypatch.setattr(worktree_claims, "safe_git", spy)
    return seen


@pytest.mark.parametrize("change", [late_hidden, late_ignored, late_process])
def test_arrival_during_the_git_removal_call_is_lost_documented_residual(
    repo: Path, free_fuser: Path, monkeypatch: pytest.MonkeyPatch, holders: list[Any], change: Any
) -> None:
    """Residual risk, not a guarantee (runbook): no privilege-free check excludes a same-user writer.

    Bytes or a process that arrive after the final re-check, while the
    non-forced ``git worktree remove`` runs, are not seen: Git trusts
    assume-unchanged, deletes ignored files and ignores processes.
    """
    worktree = dispatch_tree(repo, detached=True)
    flag_for(change, worktree, repo)
    seen = at_the_git_call(monkeypatch, change)

    report = rw.reap_clean_pushed(repo_root=repo, dry_run=False)

    assert outcome_for(report, worktree, repo).action == "removed"
    [staged] = seen
    assert not worktree.exists() and not staged.exists()
    if change is late_process:
        [process] = holders
        assert process.poll() is None  # still running, its working directory deleted
        assert os.readlink(f"/proc/{process.pid}/cwd").endswith(" (deleted)")


def test_tracked_edit_at_the_git_call_is_refused_by_git_and_restored(
    repo: Path, free_fuser: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    worktree = dispatch_tree(repo, detached=True)
    at_the_git_call(monkeypatch, lambda tree: (tree / "README.md").write_text("unsaved\n", encoding="utf-8"))

    report = rw.reap_clean_pushed(repo_root=repo, dry_run=False)

    outcome = outcome_for(report, worktree, repo)
    assert outcome.action == "error" and "worktree removal failed" in outcome.reason
    assert (worktree / "README.md").read_text(encoding="utf-8") == "unsaved\n"  # nothing deleted: moved back
    assert quarantine_entries(repo) == []


def holder_record(repo: Path) -> dict[str, Any]:
    [holder] = quarantine_entries(repo)
    return json.loads((holder / rw.QUARANTINE_RECORD).read_text(encoding="utf-8"))


def test_record_of_path_and_identity_is_durable_before_the_move(
    repo: Path, free_fuser: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    worktree = dispatch_tree(repo)
    identity = worktree.stat()
    records: list[dict[str, Any]] = []
    real_move = rw._move_worktree

    def spy(primary: Path, source: Path, destination: Path) -> str | None:
        if not records:
            records.append(json.loads((destination / rw.QUARANTINE_RECORD).read_text(encoding="utf-8")))
            assert stat.S_IMODE(destination.stat().st_mode) == 0o700
            assert stat.S_IMODE(destination.parent.stat().st_mode) == 0o700
            assert re.fullmatch(r"codex-[0-9a-f]{32}", destination.name)  # 128 random bits
        return real_move(primary, source, destination)

    monkeypatch.setattr(rw, "_move_worktree", spy)
    report = rw.reap_clean_pushed(repo_root=repo, dry_run=False)

    assert outcome_for(report, worktree, repo).action == "removed"
    [record] = records
    assert {key: record[key] for key in ("schema", "original", "task", "dev", "ino", "stage")} == {
        "schema": "clean-pushed-quarantine.v1",
        "original": SHOWN,
        "task": "task-a",
        "dev": identity.st_dev,
        "ino": identity.st_ino,
        "stage": "intent",
    }
    assert quarantine_entries(repo) == []


def test_per_worktree_lock_is_held_through_the_git_call(
    repo: Path, free_fuser: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    worktree = dispatch_tree(repo)
    _key, lock_file = worktree_claims.lock_path(worktree, lock_dir=worktree_claims.repository_lock_dir(repo))
    probe = "import fcntl, sys; fcntl.flock(open(sys.argv[1], 'a'), fcntl.LOCK_EX | fcntl.LOCK_NB)"
    results: list[int] = []

    def try_lock(tree: Path) -> None:
        probed = subprocess.run([sys.executable, "-c", probe, str(lock_file)], capture_output=True, timeout=30)
        results.append(probed.returncode)

    at_the_git_call(monkeypatch, try_lock)
    report = rw.reap_clean_pushed(repo_root=repo, dry_run=False)

    assert outcome_for(report, worktree, repo).action == "removed"
    assert results == [1]  # BlockingIOError: the reservation is held across quarantine, re-checks and removal


def test_partial_removal_is_kept_in_the_quarantine_and_never_restored(
    repo: Path, free_fuser: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    worktree = dispatch_tree(repo, detached=True)
    real = worktree_claims.safe_git

    def partial(args: list[str], **kwargs: Any) -> Any:
        if args[:2] != ["worktree", "remove"]:
            return real(args, **kwargs)
        (Path(args[-1]) / ".gitignore").unlink()  # Git deleted some entries, then failed
        return subprocess.CompletedProcess(args, 1, "", "error: simulated failure partway")

    monkeypatch.setattr(worktree_claims, "safe_git", partial)
    report = rw.reap_clean_pushed(repo_root=repo, dry_run=False)

    outcome = outcome_for(report, worktree, repo)
    assert outcome.action == "error" and "stopped partway" in outcome.reason
    assert not worktree.exists()
    assert holder_record(repo)["stage"] == "removing"

    monkeypatch.setattr(worktree_claims, "safe_git", real)
    later = rw.reap_clean_pushed(repo_root=repo, dry_run=False)
    [kept] = [item for item in later.skipped if item.path.startswith(".worktrees/.reaping/")]
    assert kept.reason == (
        "quarantine: kept: Git removal may have started, so it may be partially deleted; inspect it (runbook)"
    )
    assert not worktree.exists() and len(quarantine_entries(repo)) == 1


_CRASH = """
import os, sys
from pathlib import Path
from scripts.orchestration import reap_worktrees as rw
rw._FUSER = sys.argv[2]
rw._uninspectable_same_user = lambda base, proc_root: False
point = sys.argv[3]
if point == "verify":
    real = rw._clean_pushed_refusal
    def crash(info, ctx, claims, *, recheck, tree=None):
        if tree is not None and ".reaping" in tree.parts:
            os._exit(9)
        return real(info, ctx, claims, recheck=recheck, tree=tree)
    rw._clean_pushed_refusal = crash
else:
    rw._final_recheck = lambda tree, baseline: os._exit(9)
rw.reap_clean_pushed(repo_root=Path(sys.argv[1]), dry_run=False)
"""


@pytest.mark.parametrize(
    ("point", "stage", "restored"),
    [("verify", "intent", True), ("final_recheck", "removing", False)],
)
def test_crash_in_the_quarantine_is_recovered_only_when_removal_never_started(
    repo: Path, free_fuser: Path, point: str, stage: str, restored: bool
) -> None:
    worktree = dispatch_tree(repo, detached=True)
    crashed = subprocess.run(
        [sys.executable, "-c", _CRASH, str(repo), str(free_fuser), point],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert crashed.returncode == 9, crashed.stderr
    assert not worktree.exists() and holder_record(repo)["stage"] == stage

    dry = rw.reap_clean_pushed(repo_root=repo)
    assert not worktree.exists() and len(quarantine_entries(repo)) == 1  # a dry run moves nothing

    report = rw.reap_clean_pushed(repo_root=repo, dry_run=False)

    if restored:
        assert outcome_for(dry, worktree, repo).reason.startswith("would restore")
        outcome = outcome_for(report, worktree, repo)
        assert outcome.reason == "restored from the reaper quarantine (interrupted run); kept this run"
        assert worktree.is_dir() and (worktree / "README.md").exists() and quarantine_entries(repo) == []
    else:
        [kept] = [item for item in report.skipped if item.path.startswith(".worktrees/.reaping/")]
        assert "Git removal may have started" in kept.reason
        assert not worktree.exists() and len(quarantine_entries(repo)) == 1
    assert report.removed == ()


def crashed_quarantine(repo: Path, **record: Any) -> tuple[Path, Path]:
    """The state a run that died between the move and Git leaves: record, then the checkout in the holder."""
    worktree = dispatch_tree(repo, detached=True)
    identity = worktree.stat()
    holder = repo / ".worktrees" / ".reaping" / f"codex-{'0' * 32}"
    holder.parent.mkdir(mode=0o700)
    holder.mkdir(mode=0o700)
    (holder / rw.QUARANTINE_RECORD).write_text(
        json.dumps(
            {
                "schema": "clean-pushed-quarantine.v1",
                "original": SHOWN,
                "task": "task-a",
                "dev": identity.st_dev,
                "ino": identity.st_ino,
                "stage": "intent",
                **record,
            }
        ),
        encoding="utf-8",
    )
    git(repo, "worktree", "move", str(worktree), str(holder))
    return worktree, holder / "task-a"


@pytest.mark.parametrize(
    ("record", "reason"),
    [
        ({"ino": 1}, "kept: directory identity differs from the record"),
        ({"stage": "removing"}, "kept: Git removal may have started, so it may be partially deleted"),
        ({"schema": "other"}, "no readable quarantine record"),
        ({"original": ".worktrees/dispatch/../../outside/task-a"}, "no readable quarantine record"),
    ],
)
def test_ambiguous_quarantine_entries_are_kept(
    repo: Path, free_fuser: Path, record: dict[str, Any], reason: str
) -> None:
    worktree, staged = crashed_quarantine(repo, **record)

    report = rw.reap_clean_pushed(repo_root=repo, dry_run=False)

    [kept] = [item for item in report.skipped if item.path.startswith(".worktrees/.reaping/")]
    assert kept.reason == f"quarantine: {reason}; inspect it (runbook)"
    assert staged.is_dir() and not worktree.exists()
    assert report.removed == ()


def test_record_left_without_a_checkout_is_cleared(repo: Path, free_fuser: Path) -> None:
    worktree, staged = crashed_quarantine(repo)
    git(repo, "worktree", "move", str(staged), str(worktree))  # e.g. moved back by hand

    rw.reap_clean_pushed(repo_root=repo)
    assert len(quarantine_entries(repo)) == 1  # a dry run clears nothing
    report = rw.reap_clean_pushed(repo_root=repo, dry_run=False)

    assert quarantine_entries(repo) == []
    assert outcome_for(report, worktree, repo).action == "removed", report  # an ordinary candidate again


@pytest.mark.parametrize("checkout", [True, False])
def test_unexpected_entry_in_a_holder_keeps_the_record_and_is_reported(
    repo: Path, free_fuser: Path, checkout: bool
) -> None:
    """Runbook: unexpected entries are kept and reported, never restored past or cleared (#10778)."""
    worktree, staged = crashed_quarantine(repo)
    if not checkout:
        git(repo, "worktree", "move", str(staged), str(worktree))
    holder = staged.parent
    (holder / "unexpected.txt").write_text("someone's file\n", encoding="utf-8")

    report = rw.reap_clean_pushed(repo_root=repo, dry_run=False)

    [kept] = [item for item in report.skipped if item.path.startswith(".worktrees/.reaping/")]
    assert kept.reason == "quarantine: unexpected entries next to the record; inspect it (runbook)"
    assert (holder / rw.QUARANTINE_RECORD).is_file() and (holder / "unexpected.txt").is_file()
    if checkout:
        assert staged.is_dir() and not worktree.exists()  # not restored past the unexpected entry
        assert report.removed == ()


def test_clearing_a_holder_keeps_the_record_while_anything_else_is_there(tmp_path: Path) -> None:
    holder = tmp_path / "holder"
    holder.mkdir()
    (holder / rw.QUARANTINE_RECORD).write_text("{}", encoding="utf-8")
    (holder / "late.txt").write_text("x\n", encoding="utf-8")

    rw._clear_quarantine(holder)
    assert sorted(path.name for path in holder.iterdir()) == sorted([rw.QUARANTINE_RECORD, "late.txt"])

    (holder / "late.txt").unlink()
    rw._clear_quarantine(holder)
    assert not holder.exists()


def test_quarantine_root_open_to_others_is_refused(repo: Path, free_fuser: Path) -> None:
    worktree = dispatch_tree(repo)
    root = repo / ".worktrees" / ".reaping"
    root.mkdir()
    root.chmod(0o755)

    reason = _refusal(repo, worktree)

    assert reason == "quarantine unavailable (quarantine directory is not a private real directory)"
    assert list(root.iterdir()) == []


def test_move_back_never_nests_the_checkout_in_a_path_that_reappeared(
    repo: Path, free_fuser: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    worktree = dispatch_tree(repo, detached=True)
    real_move = rw._move_worktree

    def reappear_then_move(primary: Path, source: Path, destination: Path) -> str | None:
        if ".reaping" in source.parts:  # the move back, after the late file refused removal
            worktree.mkdir()  # a new checkout appears after the existence check, before Git renames
            (worktree / "new.txt").write_text("someone else's work\n", encoding="utf-8")
        return real_move(primary, source, destination)

    monkeypatch.setattr(rw, "_move_worktree", reappear_then_move)
    wrap_moves(monkeypatch, after=late_file)

    report = rw.reap_clean_pushed(repo_root=repo, dry_run=False)

    outcome = outcome_for(report, worktree, repo)
    assert outcome.action == "error" and "already exists" in outcome.reason, outcome
    assert list(worktree.iterdir()) == [worktree / "new.txt"]  # not moved inside the new directory
    [holder] = quarantine_entries(repo)
    assert (holder / worktree.name / "late.txt").exists()
