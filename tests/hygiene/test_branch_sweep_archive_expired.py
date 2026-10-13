"""Archive expired local report-only branches: bundle, verify, receipt, then delete.

Scratch repositories only. These tests must never delete a ref in the real checkout.
"""

from __future__ import annotations

import json
import os
import shlex
import subprocess
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from scripts.hygiene import branch_sweep as sweep
from scripts.orchestration.reap_worktrees import PullRequestState


def git(repo: Path, *args: str, env: dict[str, str] | None = None) -> str:
    command = ["git", "-c", "core.hooksPath=/dev/null", *args] if args[0] == "push" else ["git", *args]
    result = subprocess.run(
        command,
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert result.returncode == 0, f"git {args[0]} failed: {result.stderr or result.stdout}"
    return result.stdout.strip()


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    remote = tmp_path / "origin.git"
    subprocess.run(["git", "init", "--bare", str(remote)], check=True, capture_output=True, timeout=30)
    root = tmp_path / "checkout"
    root.mkdir()
    git(root, "init", "-b", "main")
    git(root, "config", "user.name", "Test")
    git(root, "config", "user.email", "test@example.invalid")
    (root / "readme").write_text("base\n", encoding="utf-8")
    git(root, "add", "readme")
    git(root, "commit", "-m", "base")
    git(root, "remote", "add", "origin", str(remote))
    git(root, "push", "-u", "origin", "main")
    return root


def _when(days: int, *, extra_hours: int = 2) -> str:
    moment = datetime.now(UTC) - timedelta(days=days, hours=extra_hours)
    return moment.strftime("%Y-%m-%dT%H:%M:%SZ")


def commit_unique(repo: Path, name: str, *, days: int) -> str:
    """Add one non-empty commit on ``name`` dated ``days`` ago, without checking it out."""
    git(repo, "branch", name, "main")
    index = repo / ".git" / f"archive-index-{name.replace('/', '-')}"
    index.unlink(missing_ok=True)
    env = os.environ.copy()
    env["GIT_INDEX_FILE"] = str(index)
    when = _when(days)
    env["GIT_AUTHOR_DATE"] = when
    env["GIT_COMMITTER_DATE"] = when
    git(repo, "read-tree", name, env=env)
    path = repo / "notes" / f"{name.replace('/', '-')}.txt"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"{name}\n", encoding="utf-8")
    git(repo, "add", "--", str(path.relative_to(repo)), env=env)
    tree = git(repo, "write-tree", env=env)
    parent = git(repo, "rev-parse", name)
    sha = git(repo, "commit-tree", tree, "-p", parent, "-m", name, env=env)
    git(repo, "update-ref", f"refs/heads/{name}", sha)
    index.unlink(missing_ok=True)
    return sha


def publish(repo: Path, name: str) -> None:
    git(repo, "push", "origin", name)


def lookup(states: dict[str, list[PullRequestState]] | None = None, error: str | None = None):
    found = {} if states is None else states

    def prs(_repo: Path, name: str) -> tuple[list[PullRequestState], str | None]:
        return found.get(name, []), error

    return prs


def run(
    repo: Path,
    *,
    apply: bool = False,
    days: int | None = None,
    states: dict[str, list[PullRequestState]] | None = None,
    error: str | None = None,
    issues: sweep.IssueLookup | None = None,
) -> list[sweep.Decision]:
    kwargs: dict[str, object] = {
        "apply": apply,
        "pr_lookup": lookup(states, error),
        "protected_lookup": lambda _repo: set(),
    }
    if days is not None:
        kwargs["archive_after_days"] = days
    if issues is not None:
        kwargs["issue_lookup"] = issues
    return sweep.sweep(repo, **kwargs)  # type: ignore[arg-type]


def ref_sha(repo: Path, name: str) -> str | None:
    result = subprocess.run(
        ["git", "rev-parse", "--verify", f"refs/heads/{name}"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def move_head(repo: Path, name: str) -> str:
    parent = git(repo, "rev-parse", name)
    tree = git(repo, "rev-parse", f"{name}^{{tree}}")
    sha = git(repo, "commit-tree", tree, "-p", parent, "-m", f"move {name}")
    git(repo, "update-ref", f"refs/heads/{name}", sha)
    return sha


def commit_at(repo: Path, branch: str, files: dict[str, str], message: str, *, when: str) -> str:
    """Commit ``files`` on ``branch`` at ``when`` without checking the branch out."""
    index = repo / ".git" / f"archive-index-{branch.replace('/', '-')}"
    index.unlink(missing_ok=True)
    env = os.environ.copy()
    env["GIT_INDEX_FILE"] = str(index)
    env["GIT_AUTHOR_DATE"] = when
    env["GIT_COMMITTER_DATE"] = when
    git(repo, "read-tree", branch, env=env)
    for name, content in files.items():
        path = repo / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        git(repo, "add", "--", name, env=env)
    tree = git(repo, "write-tree", env=env)
    parent = git(repo, "rev-parse", branch)
    sha = git(repo, "commit-tree", tree, "-p", parent, "-m", message, env=env)
    git(repo, "update-ref", f"refs/heads/{branch}", sha)
    index.unlink(missing_ok=True)
    return sha


def _payload_bytes(data: object) -> bytes:
    if isinstance(data, bytes):
        return data
    if isinstance(data, memoryview):
        return data.tobytes()
    return bytes(data)


def by_name(decisions: list[sweep.Decision]) -> dict[str, sweep.Decision]:
    return {item.branch: item for item in decisions}


def local_ref(repo: Path, name: str) -> str:
    return git(repo, "rev-parse", "--verify", f"refs/heads/{name}")


def remote_sha(repo: Path, name: str) -> str:
    output = git(repo, "ls-remote", "--heads", "origin", f"refs/heads/{name}")
    assert output, f"{name} is absent from origin"
    return output.split()[0]


def receipt_rows(repo: Path) -> list[dict[str, object]]:
    path = repo / "batch_state" / "branch-archive" / "stale-local-receipts.jsonl"
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def test_dry_run_reports_only_expired_local_branches(repo: Path, tmp_path: Path) -> None:
    old_local = commit_unique(repo, "codex/old-local", days=8)
    old_remote = commit_unique(repo, "codex/old-remote", days=8)
    publish(repo, "codex/old-remote")
    commit_unique(repo, "codex/young", days=3)
    closed = commit_unique(repo, "codex/closed-pr", days=10)
    opened = commit_unique(repo, "claude/open-pr", days=10)
    commit_unique(repo, "agy/checked-out", days=10)
    git(repo, "worktree", "add", str(tmp_path / "other"), "agy/checked-out")
    commit_unique(repo, "grok/live", days=10)
    task_dir = repo / "batch_state" / "tasks"
    task_dir.mkdir(parents=True)
    (task_dir / "live.json").write_text(
        json.dumps({"worktree_branch": "grok/live", "status": "running"}),
        encoding="utf-8",
    )

    decisions = run(
        repo,
        states={
            "codex/closed-pr": [PullRequestState(4, "CLOSED", closed)],
            "claude/open-pr": [PullRequestState(5, "OPEN", opened)],
        },
    )
    found = by_name(decisions)
    expired = {name for name, item in found.items() if item.classification == "archive-expired"}
    assert expired == {"codex/old-local", "codex/old-remote"}
    assert found["codex/old-local"].local_deleted is False
    assert found["codex/old-local"].remote_deleted is False
    assert found["codex/old-remote"].remote_deleted is False
    assert found["codex/young"].classification == "report-only"
    assert found["codex/closed-pr"].classification == "report-only"
    assert found["claude/open-pr"].classification == "skipped-open-PR"
    assert found["agy/checked-out"].classification == "skipped-worktree"
    assert found["grok/live"].classification == "skipped-live-task"
    assert local_ref(repo, "codex/old-local") == old_local
    assert local_ref(repo, "codex/old-remote") == old_remote
    assert remote_sha(repo, "codex/old-remote") == old_remote
    assert not (repo / "batch_state" / "branch-archive" / "stale-local-receipts.jsonl").exists()
    assert list((repo / "batch_state" / "branch-archive").glob("*.bundle")) == []


def test_apply_bundles_verifies_receipts_then_deletes_local_refs_only(repo: Path) -> None:
    local_sha = commit_unique(repo, "codex/old-local", days=8)
    remote_sha_value = commit_unique(repo, "codex/old-remote", days=9)
    publish(repo, "codex/old-remote")
    issue_sha = commit_unique(repo, "codex/impl-9539", days=8)
    rescue_sha = commit_unique(repo, "rescue/old-task", days=8)
    young_sha = commit_unique(repo, "kimi/young", days=2)

    events: list[str] = []
    original_git = sweep._git
    pushes: list[tuple[str, ...]] = []

    def capture_git(root: Path, *args: str, **kwargs: object):
        if args[0] == "push":
            pushes.append(args)
        if args[:2] == ("bundle", "create"):
            events.append("create")
            assert "--not" in args
            assert "refs/remotes/origin/main" in args
        elif args[:2] == ("bundle", "verify"):
            events.append("verify")
        elif args[:2] == ("bundle", "list-heads"):
            events.append("list-heads")
        elif args[:2] == ("update-ref", "--stdin"):
            text = (repo / "batch_state" / "branch-archive" / "stale-local-receipts.jsonl").read_text(encoding="utf-8")
            script = str(kwargs.get("input") or "")
            assert "delete refs/heads/codex/old-local" in script
            assert "codex/old-local" in text
            assert "verify" in events and "list-heads" in events
            events.append("delete")
        return original_git(root, *args, **kwargs)

    def forbid_prune(*_args: object, **_kwargs: object) -> str:
        raise AssertionError("archive delete used git branch -D")

    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(sweep, "_git", capture_git)
    monkeypatch.setattr(sweep.reaper, "_prune_branch", forbid_prune)
    try:
        decisions = run(repo, apply=True)
    finally:
        monkeypatch.undo()

    found = by_name(decisions)
    archived = ("codex/old-local", "codex/old-remote", "codex/impl-9539")
    for name in archived:
        assert found[name].classification == "archive-expired"
        assert found[name].local_deleted is True
        assert found[name].remote_deleted is False
        with pytest.raises(AssertionError):
            local_ref(repo, name)
    assert found["rescue/old-task"].classification == "report-only"
    assert found["rescue/old-task"].local_deleted is False
    assert local_ref(repo, "rescue/old-task") == rescue_sha
    assert found["kimi/young"].classification == "report-only"
    assert local_ref(repo, "kimi/young") == young_sha
    assert remote_sha(repo, "codex/old-remote") == remote_sha_value
    assert not any("codex/old-remote" in " ".join(push) for push in pushes)
    assert events.index("create") < events.index("verify") < events.index("list-heads")
    assert events.index("list-heads") < events.index("delete")

    rows = receipt_rows(repo)
    by_branch = {str(row["branch"]): row for row in rows}
    assert set(by_branch) == set(archived)
    expected = {
        "codex/old-local": (local_sha, False),
        "codex/old-remote": (remote_sha_value, True),
        "codex/impl-9539": (issue_sha, False),
    }
    bundles = {(repo / str(row["bundle"])).resolve() for row in rows}
    assert len(bundles) == 1
    bundle = bundles.pop()
    assert bundle.is_file()
    listed = git(repo, "bundle", "list-heads", str(bundle))
    for name, (sha, copied) in expected.items():
        row = by_branch[name]
        assert row["sha"] == sha
        assert row["remote_copy"] is copied
        assert row["bundle"] == str(bundle.relative_to(repo))
        assert isinstance(row["at"], str) and str(row["at"]).endswith("Z")
        assert f"refs/heads/{name}" in listed
        assert sha in listed
        scratch = repo.parent / f"restore-{name.replace('/', '-')}"
        origin = git(repo, "remote", "get-url", "origin")
        subprocess.run(
            ["git", "clone", "--quiet", origin, str(scratch)],
            check=True,
            capture_output=True,
            timeout=60,
        )
        restored = subprocess.run(
            shlex.split(str(row["restore"])),
            cwd=scratch,
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )
        assert restored.returncode == 0, restored.stderr
        assert git(scratch, "rev-parse", f"refs/heads/{name}") == sha


def test_verify_failure_deletes_nothing(repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    sha = commit_unique(repo, "codex/old-local", days=8)
    publish(repo, "codex/old-local")
    events: list[str] = []
    original = sweep._git

    def fail_verify(root: Path, *args: str, **kwargs: object):
        if args[:2] == ("bundle", "create"):
            events.append("create")
        elif args[:2] == ("bundle", "verify"):
            events.append("verify")
            return subprocess.CompletedProcess(args, 1, "", "verify failed")
        return original(root, *args, **kwargs)

    def forbid_delete(*_args: object, **_kwargs: object) -> str:
        events.append("delete")
        raise AssertionError("ref deletion ran after verify failed")

    monkeypatch.setattr(sweep, "_git", fail_verify)
    monkeypatch.setattr(sweep.reaper, "_prune_branch", forbid_delete)
    found = by_name(run(repo, apply=True))
    item = found["codex/old-local"]
    assert events[:2] == ["create", "verify"]
    assert "delete" not in events
    assert item.local_deleted is False
    assert item.remote_deleted is False
    assert "verify" in item.reason
    assert local_ref(repo, "codex/old-local") == sha
    assert remote_sha(repo, "codex/old-local") == sha
    assert receipt_rows(repo) == []


def test_missing_bundle_head_deletes_nothing(repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    sha = commit_unique(repo, "codex/old-local", days=8)
    events: list[str] = []
    original = sweep._git

    def hide_heads(root: Path, *args: str, **kwargs: object):
        if args[:2] == ("bundle", "create"):
            events.append("create")
        elif args[:2] == ("bundle", "verify"):
            events.append("verify")
        elif args[:2] == ("bundle", "list-heads"):
            events.append("list-heads")
            return subprocess.CompletedProcess(args, 0, "", "")
        return original(root, *args, **kwargs)

    def forbid_delete(*_args: object, **_kwargs: object) -> str:
        events.append("delete")
        raise AssertionError("ref deletion ran when the bundle was missing a head")

    monkeypatch.setattr(sweep, "_git", hide_heads)
    monkeypatch.setattr(sweep.reaper, "_prune_branch", forbid_delete)
    item = by_name(run(repo, apply=True))["codex/old-local"]
    assert events == ["create", "verify", "list-heads"]
    assert item.local_deleted is False
    assert item.remote_deleted is False
    assert "missing a head" in item.reason
    assert local_ref(repo, "codex/old-local") == sha
    assert receipt_rows(repo) == []


def test_unwritable_archive_directory_deletes_nothing(repo: Path) -> None:
    sha = commit_unique(repo, "codex/old-local", days=8)
    archive = repo / "batch_state" / "branch-archive"
    archive.parent.mkdir(parents=True)
    archive.write_text("not a directory\n", encoding="utf-8")
    item = by_name(run(repo, apply=True))["codex/old-local"]
    assert item.classification == "report-only"
    assert item.local_deleted is False
    assert item.remote_deleted is False
    assert "unwritable" in item.reason
    assert local_ref(repo, "codex/old-local") == sha
    assert archive.is_file()


def test_symlink_archive_directory_deletes_nothing(repo: Path, tmp_path: Path) -> None:
    sha = commit_unique(repo, "codex/old-local", days=8)
    outside = tmp_path / "outside"
    outside.mkdir()
    parent = repo / "batch_state"
    parent.mkdir()
    (parent / "branch-archive").symlink_to(outside, target_is_directory=True)
    item = by_name(run(repo, apply=True))["codex/old-local"]
    assert item.local_deleted is False
    assert item.remote_deleted is False
    assert "symlink" in item.reason
    assert local_ref(repo, "codex/old-local") == sha
    assert list(outside.iterdir()) == []


def test_threshold_defaults_to_seven_days_and_is_configurable(repo: Path) -> None:
    week = commit_unique(repo, "codex/just-one-week", days=7)
    younger = commit_unique(repo, "codex/six-days", days=6)
    defaulted = by_name(run(repo, apply=False))
    assert defaulted["codex/just-one-week"].classification == "archive-expired"
    assert defaulted["codex/six-days"].classification == "report-only"
    sooner = by_name(run(repo, apply=False, days=6))
    assert sooner["codex/six-days"].classification == "archive-expired"
    later = by_name(run(repo, apply=False, days=30))
    assert later["codex/just-one-week"].classification == "report-only"
    assert local_ref(repo, "codex/just-one-week") == week
    assert local_ref(repo, "codex/six-days") == younger
    assert sweep.build_parser().get_default("archive_after_days") == 7
    help_text = sweep.build_parser().format_help()
    assert "--archive-after-days" in help_text
    assert "default: 7" in help_text
    assert "90" in help_text


def test_bundles_older_than_ninety_days_are_listed_and_kept(repo: Path) -> None:
    archive = repo / "batch_state" / "branch-archive"
    archive.mkdir(parents=True)
    old = archive / "stale-local-20200101T000000Z.bundle"
    boundary = archive / "stale-local-boundary.bundle"
    recent = archive / "stale-local-recent.bundle"
    linked = archive / "stale-local-link.bundle"
    for path in (old, boundary, recent):
        path.write_bytes(b"bundle-bytes")
    linked.symlink_to(old.name)
    now = datetime.now(UTC).timestamp()
    os.utime(old, (now, now - (100 * 86400)))
    os.utime(boundary, (now, now - (90 * 86400 + 3600)))
    os.utime(recent, (now, now - (89 * 86400 + 3600)))
    commit_unique(repo, "codex/old-local", days=8)

    dry = run(repo, apply=False)
    listed = {item.branch for item in dry if item.classification == "review-bundle"}
    assert listed == {
        "batch_state/branch-archive/stale-local-20200101T000000Z.bundle",
        "batch_state/branch-archive/stale-local-boundary.bundle",
    }
    assert all(
        item.local_deleted is False and item.remote_deleted is False
        for item in dry
        if item.classification == "review-bundle"
    )

    run(repo, apply=True)
    assert old.is_file() and boundary.is_file() and recent.is_file() and linked.is_symlink()
    assert old.read_bytes() == b"bundle-bytes"
    assert "codex/old-local" not in listed


def test_diverged_and_unknown_pr_branches_stay_report_only(repo: Path) -> None:
    commit_unique(repo, "cursor/diverged", days=10)
    publish(repo, "cursor/diverged")
    parent = git(repo, "rev-parse", "cursor/diverged")
    tree = git(repo, "rev-parse", "cursor/diverged^{tree}")
    env = os.environ.copy()
    env["GIT_AUTHOR_DATE"] = _when(10)
    env["GIT_COMMITTER_DATE"] = _when(10)
    moved = git(repo, "commit-tree", tree, "-p", parent, "-m", "later", env=env)
    git(repo, "update-ref", "refs/heads/cursor/diverged", moved)
    commit_unique(repo, "glm/unknown", days=10)

    found = by_name(run(repo, apply=True, error="quota exhausted"))
    assert found["cursor/diverged"].classification == "report-only"
    assert "tips differ" in found["cursor/diverged"].reason
    assert local_ref(repo, "cursor/diverged") == moved
    assert found["glm/unknown"].classification == "report-only"
    assert "unavailable" in found["glm/unknown"].reason
    assert local_ref(repo, "glm/unknown")


def test_cli_passes_archive_after_days(
    repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    seen: dict[str, object] = {}

    def capture(root: Path, *, apply: bool = False) -> list[sweep.Decision]:
        seen["root"] = root
        seen["apply"] = apply
        seen["days"] = sweep.current_archive_after_days()
        return []

    monkeypatch.setattr(sweep.reaper, "resolve_repo_root", lambda: repo)
    monkeypatch.setattr(sweep, "sweep", capture)
    assert sweep.main(["--archive-after-days", "12", "--apply", "--json"]) == 0
    assert seen == {"root": repo, "apply": True, "days": 12}
    payload = json.loads(capsys.readouterr().out)
    assert payload["archive_after_days"] == 12
    assert payload["apply"] is True
    with pytest.raises(SystemExit) as caught:
        sweep.main(["--archive-after-days", "-1"])
    assert caught.value.code == 2


def test_moved_head_and_peer_stay_when_compare_and_delete_fails(repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Findings 1 and 6: one compare-and-delete, or the whole batch stays."""
    first = commit_unique(repo, "codex/first", days=8)
    commit_unique(repo, "codex/second", days=8)
    moved: dict[str, str | None] = {"sha": None}
    original_run = sweep.reaper._run
    original_git = sweep._git

    def intercept_run(args, *, cwd, timeout=None, env_overrides=None):
        result = original_run(args, cwd=cwd, timeout=timeout, env_overrides=env_overrides)
        if (
            list(args[:3]) == ["git", "rev-parse", "--verify"]
            and args[-1] == "refs/heads/codex/second"
            and moved["sha"] is None
        ):
            moved["sha"] = move_head(repo, "codex/second")
        return result

    def intercept_git(root: Path, *args: str, **kwargs: object):
        if args[:2] == ("update-ref", "--stdin") and moved["sha"] is None:
            moved["sha"] = move_head(repo, "codex/second")
        return original_git(root, *args, **kwargs)

    monkeypatch.setattr(sweep.reaper, "_run", intercept_run)
    monkeypatch.setattr(sweep, "_git", intercept_git)
    found = by_name(run(repo, apply=True))
    assert moved["sha"] is not None
    assert ref_sha(repo, "codex/first") == first
    assert ref_sha(repo, "codex/second") == moved["sha"]
    assert found["codex/first"].local_deleted is False
    assert found["codex/second"].local_deleted is False
    assert found["codex/first"].remote_deleted is False
    assert found["codex/second"].remote_deleted is False


def test_pr_and_task_guards_are_reread_immediately_before_delete(repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Finding 2: a task or pull request that appears after the receipt blocks the batch."""
    task_sha = commit_unique(repo, "codex/late-task", days=8)
    pr_sha = commit_unique(repo, "codex/late-pr", days=8)
    states: dict[str, list[PullRequestState]] = {}
    original = sweep._write_archive_receipts

    def plant(root: Path, confirmed, **kwargs: object):
        original(root, confirmed, **kwargs)
        task_dir = root / "batch_state" / "tasks"
        task_dir.mkdir(parents=True, exist_ok=True)
        (task_dir / "late.json").write_text(
            json.dumps({"status": "running", "worktree_branch": "codex/late-task"}),
            encoding="utf-8",
        )
        states["codex/late-pr"] = [PullRequestState(9, "OPEN", pr_sha)]

    monkeypatch.setattr(sweep, "_write_archive_receipts", plant)
    found = by_name(run(repo, apply=True, states=states))
    assert ref_sha(repo, "codex/late-task") == task_sha
    assert ref_sha(repo, "codex/late-pr") == pr_sha
    assert found["codex/late-task"].local_deleted is False
    assert found["codex/late-pr"].local_deleted is False
    assert list((repo / "batch_state" / "branch-archive").glob("*.bundle"))
    assert "skipped-live-task" in found["codex/late-task"].reason
    assert "open PR" in found["codex/late-pr"].reason


def test_newer_than_closing_merge_blocks_archive_before_file_coverage(repo: Path) -> None:
    """Finding 3: a commit newer than the closing merge is not archived for another reason."""
    git(repo, "branch", "codex/impl-10532", "main")
    branch_sha = commit_at(
        repo,
        "codex/impl-10532",
        {"covered.txt": "branch\n", "extra.txt": "only-on-branch\n"},
        "later unique work",
        when=_when(8),
    )
    commit_at(
        repo,
        "main",
        {"covered.txt": "landed\n"},
        "land part (#4444)",
        when=_when(20),
    )
    publish(repo, "main")
    publish(repo, "codex/impl-10532")

    def issues(_repo: Path, number: int) -> tuple[sweep.IssueClosure | None, str | None]:
        assert number == 10532
        return sweep.IssueClosure(4444), None

    item = by_name(run(repo, apply=True, issues=issues))["codex/impl-10532"]
    assert item.classification == "report-only"
    assert item.local_deleted is False
    assert "newer than the closing merge" in item.reason
    assert ref_sha(repo, "codex/impl-10532") == branch_sha


def _wait_for_free_bundle_second(repo: Path) -> None:
    """The bundle name is the UTC second. A second apply in that second is retained."""
    archive = repo / "batch_state" / "branch-archive"
    deadline = time.monotonic() + 3
    while True:
        stamp = datetime.now(UTC).strftime("stale-local-%Y%m%dT%H%M%SZ.bundle")
        if not (archive / stamp).exists():
            return
        if time.monotonic() >= deadline:
            raise AssertionError(f"bundle name stayed in use: {stamp}")
        time.sleep(0.05)


def test_truncated_receipt_does_not_authorize_delete(repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Finding 4: a short write is finished and re-read before any ref is deleted."""
    real_write = os.write
    lie_sha = commit_unique(repo, "codex/lie-receipt", days=8)

    def lie(_fd: int, data: object) -> int:
        raw = _payload_bytes(data)
        if not raw.startswith(b"{"):
            return real_write(_fd, data)  # type: ignore[arg-type]
        real_write(_fd, raw[:1])
        return len(raw)

    monkeypatch.setattr(os, "write", lie)
    lied = by_name(run(repo, apply=True))["codex/lie-receipt"]
    receipt = repo / "batch_state" / "branch-archive" / "stale-local-receipts.jsonl"
    assert lied.local_deleted is False
    assert ref_sha(repo, "codex/lie-receipt") == lie_sha
    assert lie_sha not in receipt.read_text(encoding="utf-8")

    short_sha = commit_unique(repo, "codex/short-receipt", days=8)

    def short(_fd: int, data: object) -> int:
        raw = _payload_bytes(data)
        if not raw.startswith(b"{"):
            return real_write(_fd, data)  # type: ignore[arg-type]
        half = max(1, len(raw) // 2)
        return real_write(_fd, raw[:half])

    monkeypatch.setattr(os, "write", short)
    _wait_for_free_bundle_second(repo)
    shortened = by_name(run(repo, apply=True))["codex/short-receipt"]
    rows = [row for row in receipt.read_text(encoding="utf-8").split("\n") if short_sha in row]
    assert len(rows) == 1
    assert json.loads(rows[0])["sha"] == short_sha
    assert shortened.local_deleted is True
    assert ref_sha(repo, "codex/short-receipt") is None


def test_rescue_upstream_and_recent_tasks_are_not_archived(repo: Path) -> None:
    """Finding 5: rescue refs, unpushed upstreams, and recent released tasks stay."""
    rescue = commit_unique(repo, "rescue/held-patch", days=8)
    unpushed = commit_unique(repo, "codex/unpushed", days=8)
    git(repo, "branch", "--set-upstream-to=origin/main", "codex/unpushed")
    recent = commit_unique(repo, "codex/just-failed", days=8)
    old = commit_unique(repo, "codex/long-failed", days=8)
    task_dir = repo / "batch_state" / "tasks"
    task_dir.mkdir(parents=True)
    now = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    long_ago = (datetime.now(UTC) - timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%SZ")
    (task_dir / "just-failed.json").write_text(
        json.dumps({"status": "failed", "worktree_branch": "codex/just-failed", "finished_at": now}),
        encoding="utf-8",
    )
    (task_dir / "long-failed.json").write_text(
        json.dumps({"status": "failed", "worktree_branch": "codex/long-failed", "finished_at": long_ago}),
        encoding="utf-8",
    )

    found = by_name(run(repo, apply=True))
    assert found["rescue/held-patch"].classification == "report-only"
    assert found["rescue/held-patch"].local_deleted is False
    assert "rescue" in found["rescue/held-patch"].reason
    assert ref_sha(repo, "rescue/held-patch") == rescue
    assert found["codex/unpushed"].classification == "report-only"
    assert found["codex/unpushed"].local_deleted is False
    assert "unpushed" in found["codex/unpushed"].reason
    assert ref_sha(repo, "codex/unpushed") == unpushed
    assert found["codex/just-failed"].classification == "report-only"
    assert found["codex/just-failed"].local_deleted is False
    assert ref_sha(repo, "codex/just-failed") == recent
    assert found["codex/long-failed"].classification == "archive-expired"
    assert found["codex/long-failed"].local_deleted is True
    assert ref_sha(repo, "codex/long-failed") is None
    assert old not in {ref_sha(repo, "codex/long-failed")}


def test_archive_bundle_is_thin_and_restores_into_a_clone(repo: Path) -> None:
    """Finding 7: the bundle excludes origin/main and restores only after a clone."""
    (repo / "weight.bin").write_bytes(os.urandom(256 * 1024))
    git(repo, "add", "weight.bin")
    git(repo, "commit", "-m", "weight on main")
    git(repo, "push", "origin", "main")
    sha = commit_unique(repo, "codex/thin-me", days=8)
    full = repo.parent / "full-history.bundle"
    git(repo, "bundle", "create", str(full), "refs/heads/codex/thin-me")
    item = by_name(run(repo, apply=True))["codex/thin-me"]
    assert item.local_deleted is True
    row = next(entry for entry in receipt_rows(repo) if entry["branch"] == "codex/thin-me")
    bundle = repo / str(row["bundle"])
    thin_size = bundle.stat().st_size
    full_size = full.stat().st_size
    assert thin_size < full_size, f"thin={thin_size} full={full_size}"
    assert thin_size < 100_000, thin_size
    assert full_size > 200_000, full_size
    verified = subprocess.run(
        ["git", "bundle", "verify", str(bundle)],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert verified.returncode == 0, verified.stderr
    assert "requires" in (verified.stdout + verified.stderr).lower()

    origin = git(repo, "remote", "get-url", "origin")
    clone = repo.parent / "thin-clone"
    subprocess.run(["git", "clone", "--quiet", origin, str(clone)], check=True, capture_output=True, timeout=60)
    restored = subprocess.run(
        shlex.split(str(row["restore"])),
        cwd=clone,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert restored.returncode == 0, restored.stderr
    assert git(clone, "rev-parse", "refs/heads/codex/thin-me") == sha

    empty = repo.parent / "thin-empty"
    subprocess.run(["git", "init", "-q", "-b", "main", str(empty)], check=True, capture_output=True, timeout=30)
    refused = subprocess.run(
        shlex.split(str(row["restore"])),
        cwd=empty,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert refused.returncode != 0


def test_pr_checkout_names_are_not_archived(repo: Path) -> None:
    """Finding 8: pr-* and review-* local checkouts are not archive-expired."""
    pr_sha = commit_unique(repo, "pr-4242", days=30)
    review_sha = commit_unique(repo, "claude/review-4242", days=30)
    plain = commit_unique(repo, "codex/plain-old", days=30)
    found = by_name(run(repo, apply=True))
    assert found["pr-4242"].classification == "report-only"
    assert found["pr-4242"].local_deleted is False
    assert ref_sha(repo, "pr-4242") == pr_sha
    assert "pull request" not in found["pr-4242"].reason.lower() or "not archived" in found["pr-4242"].reason
    assert found["claude/review-4242"].classification == "report-only"
    assert found["claude/review-4242"].local_deleted is False
    assert ref_sha(repo, "claude/review-4242") == review_sha
    assert found["codex/plain-old"].classification == "archive-expired"
    assert found["codex/plain-old"].local_deleted is True
    assert ref_sha(repo, "codex/plain-old") is None
    assert plain
