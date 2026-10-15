"""Archive expired local report-only branches: bundle, verify, receipt, then delete.

Scratch repositories only. These tests must never delete a ref in the real checkout.
"""

from __future__ import annotations

import errno
import fcntl
import hashlib
import json
import os
import shlex
import subprocess
import threading
from concurrent.futures import ThreadPoolExecutor
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
def repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("GIT_CONFIG_COUNT", "0")
    scratch = tmp_path / "managed-scratch"
    scratch.mkdir()
    monkeypatch.setenv("TMPDIR", str(scratch))
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


def occupy_branch(repo: Path, name: str, mode: str, *, linked: bool) -> tuple[Path, str]:
    """Pause native Git operations with HEAD away from the branch's original tip."""
    # All operation hooks are disabled only in this disposable synthetic repo.
    git(repo, "config", "core.hooksPath", "/dev/null")
    git(repo, "branch", name, "main")
    if mode == "bisect":
        commit_at(repo, name, {"first": "first\n"}, "first", when=_when(10))
        tip = commit_at(repo, name, {"second": "second\n"}, "second", when=_when(9))
    else:
        tip = commit_at(repo, name, {"readme": "branch\n"}, "branch", when=_when(9))
        git(repo, "branch", "upstream", "main")
        commit_at(repo, "upstream", {"readme": "upstream\n"}, "upstream", when=_when(8))
    path = repo.parent / "occupied" if linked else repo
    if linked:
        git(repo, "worktree", "add", str(path), name)
    else:
        git(repo, "symbolic-ref", "HEAD", f"refs/heads/{name}")
        git(repo, "reset", "--hard", name)
    if mode == "bisect":
        git(path, "bisect", "start", name, "main")
    elif mode in {"merge", "apply", "update-refs"}:
        options = [f"--{mode}"]
        if mode == "update-refs":
            git(repo, "branch", "codex/update-target", name)
            options = ["--merge", "--update-refs"]
        result = sweep._git(path, "rebase", *options, "upstream")
        assert result.returncode == 1
    elif mode == "merge-operation":
        assert sweep._git(path, "merge", "upstream").returncode == 1
    elif mode == "cherry-pick":
        assert sweep._git(path, "cherry-pick", "upstream").returncode == 1
    elif mode == "am":
        state = Path(git(path, "rev-parse", "--absolute-git-dir")) / "rebase-apply"
        state.mkdir()
        (state / "applying").write_text("", encoding="utf-8")
    elif mode == "revert":
        original = tip
        (path / "readme").write_text("later\n", encoding="utf-8")
        git(path, "add", "readme")
        git(path, "commit", "-m", "later")
        tip = git(path, "rev-parse", "HEAD")
        assert sweep._git(path, "revert", original).returncode == 1
    if mode in {"merge", "apply", "bisect", "update-refs"}:
        assert git(path, "rev-parse", "HEAD") != tip
    refused = sweep._git(repo, "branch", "-D", name)
    assert refused.returncode == 1 and "used by worktree" in refused.stderr
    assert ref_sha(repo, name) == tip
    return path, tip


@pytest.mark.parametrize(
    "mode", ["checkout", "merge", "apply", "bisect", "merge-operation", "cherry-pick", "revert", "am"]
)
@pytest.mark.parametrize("linked", [False, True])
def test_native_occupation_final_guard_keeps_complete_batch(repo: Path, mode: str, linked: bool) -> None:
    other = commit_unique(repo, "codex/free", days=9)
    _, tip = occupy_branch(repo, "codex/occupied", mode, linked=linked)
    with pytest.raises(RuntimeError, match="skipped-worktree" if mode == "checkout" else "in-progress operation"):
        sweep._delete_archived_refs(repo, [("codex/free", other), ("codex/occupied", tip)])
    assert ref_sha(repo, "codex/occupied") == tip
    assert ref_sha(repo, "codex/free") == other


@pytest.mark.parametrize(
    "mode", ["checkout", "merge", "apply", "bisect", "merge-operation", "cherry-pick", "revert", "am"]
)
@pytest.mark.parametrize("apply", [False, True])
def test_native_occupation_cli_retains_branch(
    repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], mode: str, apply: bool
) -> None:
    _, tip = occupy_branch(repo, "codex/occupied", mode, linked=True)
    original = sweep.sweep

    def synthetic(root: Path, *, apply: bool = False) -> list[sweep.Decision]:
        return original(root, apply=apply, pr_lookup=lookup(), protected_lookup=lambda _: set())

    monkeypatch.setattr(sweep.reaper, "resolve_repo_root", lambda: repo)
    monkeypatch.setattr(sweep, "sweep", synthetic)
    assert sweep.main(["--json", *(["--apply"] if apply else [])]) == (0 if mode == "checkout" else 1)
    payload = json.loads(capsys.readouterr().out)
    if mode == "checkout":
        item = next(row for row in payload["decisions"] if row["branch"] == "codex/occupied")
        assert item["classification"] == "skipped-worktree"
        assert not item["local_deleted"] and not item["remote_deleted"]
    else:
        assert payload["ok"] is False
        assert "in-progress operation" in payload["error"]
        assert payload["decisions"] == []
    assert ref_sha(repo, "codex/occupied") == tip
    assert not list((repo / sweep.ARCHIVE_DIR).glob("*.bundle"))
    assert not (repo / sweep.RECEIPT_PATH).exists()


def test_native_rebase_update_refs_targets_are_occupied(repo: Path) -> None:
    _, tip = occupy_branch(repo, "codex/occupied", "update-refs", linked=True)
    refused = sweep._git(repo, "branch", "-D", "codex/update-target")
    assert refused.returncode == 1 and "used by worktree" in refused.stderr
    free = commit_unique(repo, "codex/free", days=9)
    with pytest.raises(RuntimeError, match="in-progress operation"):
        sweep._delete_archived_refs(repo, [("codex/free", free), ("codex/update-target", tip)])
    with pytest.raises(sweep.SweepError, match="in-progress operation"):
        run(repo)
    assert ref_sha(repo, "codex/update-target") == tip
    assert ref_sha(repo, "codex/free") == free


@pytest.mark.parametrize("separator", ["\u2028", "\u0085"])
def test_unicode_update_refs_final_guard_retains_real_target(repo: Path, separator: str) -> None:
    """E1/E2: native Git refuses the real LF-delimited target; the final guard must too."""
    path, tip = occupy_branch(repo, "codex/occupied", "update-refs", linked=True)
    name = f"codex/x{separator}{tip}{separator}{tip}{separator}refs/heads/codex/z"
    git(repo, "check-ref-format", "--branch", name)
    git(repo, "update-ref", f"refs/heads/{name}", tip)
    updates = Path(git(path, "rev-parse", "--absolute-git-dir")) / "rebase-merge" / "update-refs"
    updates.write_text(f"refs/heads/{name}\n{tip}\n{'0' * 40}\n", encoding="utf-8")
    refused = sweep._git(repo, "branch", "-D", name)
    assert refused.returncode == 1 and "used by worktree" in refused.stderr
    with pytest.raises(RuntimeError, match="in-progress operation"):
        sweep._delete_archived_refs(repo, [(name, tip)])
    assert ref_sha(repo, name) == tip
    with pytest.raises(sweep.SweepError):
        run(repo, apply=True)
    assert ref_sha(repo, name) == tip


@pytest.mark.parametrize("linked", [False, True])
@pytest.mark.parametrize("mode", ["merge", "apply", "bisect", "merge-operation", "cherry-pick", "revert", "am"])
def test_unrelated_native_operation_refuses_unbound_archive(repo: Path, linked: bool, mode: str) -> None:
    free = commit_unique(repo, "codex/free", days=9)
    occupy_branch(repo, "unrelated", mode, linked=linked)
    with pytest.raises(sweep.SweepError, match="in-progress operation") as caught:
        run(repo, apply=True)
    assert caught.value.decisions == []
    with pytest.raises(RuntimeError, match="in-progress operation"):
        sweep._delete_archived_refs(repo, [("codex/free", free)])
    assert ref_sha(repo, "codex/free") == free
    assert not list((repo / sweep.ARCHIVE_DIR).glob("*.bundle"))
    assert not (repo / sweep.RECEIPT_PATH).exists()


@pytest.mark.parametrize(
    "marker", ["BISECT_START", "BISECT_LOG", "MERGE_HEAD", "CHERRY_PICK_HEAD", "REVERT_HEAD", "REBASE_HEAD"]
)
def test_operation_marker_presence_refuses_without_parsing(repo: Path, marker: str) -> None:
    free = commit_unique(repo, "codex/free", days=9)
    (repo / ".git" / marker).write_text("malformed\u2028state\n", encoding="utf-8")
    with pytest.raises(sweep.SweepError, match="in-progress operation"):
        run(repo, apply=True)
    with pytest.raises(RuntimeError, match="in-progress operation"):
        sweep._delete_archived_refs(repo, [("codex/free", free)])
    assert ref_sha(repo, "codex/free") == free


def test_normal_linked_and_detached_checkouts_allow_only_unbound_archive(repo: Path) -> None:
    bound = commit_unique(repo, "codex/bound", days=9)
    detached = commit_unique(repo, "codex/detached", days=9)
    free = commit_unique(repo, "codex/free", days=9)
    git(repo, "worktree", "add", str(repo.parent / "bound"), "codex/bound")
    git(repo, "worktree", "add", "--detach", str(repo.parent / "detached"), "codex/detached")
    preview = by_name(run(repo))
    assert preview["codex/bound"].classification == "skipped-worktree"
    assert preview["codex/detached"].classification == "skipped-worktree"
    assert preview["codex/free"].classification == "archive-expired"
    for name, sha in (("codex/bound", bound), ("codex/detached", detached)):
        with pytest.raises(RuntimeError, match="skipped-worktree"):
            sweep._delete_archived_refs(repo, [("codex/free", free), (name, sha)])
        assert ref_sha(repo, "codex/free") == free
    applied = by_name(run(repo, apply=True))
    assert applied["codex/free"].local_deleted
    assert ref_sha(repo, "codex/bound") == bound
    assert ref_sha(repo, "codex/detached") == detached
    row = next(row for row in receipt_rows(repo) if row["branch"] == "codex/free")
    clone = repo.parent / "restore"
    git(repo, "clone", "--quiet", git(repo, "remote", "get-url", "origin"), str(clone))
    git(clone, *shlex.split(str(row["restore"]))[1:])
    assert ref_sha(clone, "codex/free") == free


@pytest.mark.parametrize("marker", ["rebase-merge", "MERGE_HEAD"])
def test_operation_started_at_final_boundary_retains_receipted_batch(
    repo: Path, monkeypatch: pytest.MonkeyPatch, marker: str
) -> None:
    heads = {name: commit_unique(repo, name, days=9) for name in ("codex/first", "codex/second")}
    original = sweep._delete_archived_refs

    def start_operation(root: Path, pairs: list[tuple[str, str]]) -> None:
        assert {row["branch"]: row["sha"] for row in receipt_rows(root)} == heads
        # The operation is on primary main, unrelated to either archived branch.
        state = root / ".git" / marker
        if marker == "rebase-merge":
            state.mkdir()
        else:
            state.write_text(heads["codex/first"] + "\n", encoding="utf-8")
        original(root, pairs)

    monkeypatch.setattr(sweep, "_delete_archived_refs", start_operation)
    found = by_name(run(repo, apply=True))
    for name, sha in heads.items():
        assert not found[name].local_deleted
        assert "in-progress operation" in found[name].reason
        assert ref_sha(repo, name) == sha
    assert len(list((repo / sweep.ARCHIVE_DIR).glob("*.bundle"))) == 1


@pytest.mark.parametrize(
    "failure",
    [
        "empty-list",
        "duplicate",
        "unknown-head",
        "contradictory",
        "head-mismatch",
        "unreadable-head",
        "unreadable-census",
        "missing-head",
    ],
)
def test_unknown_census_without_operations_refuses_archive(
    repo: Path, monkeypatch: pytest.MonkeyPatch, failure: str
) -> None:
    free = commit_unique(repo, "codex/free", days=9)
    trees = sweep.reaper.list_git_worktrees(repo)
    primary = trees[0]
    if failure in {"empty-list", "duplicate", "unknown-head", "contradictory", "head-mismatch"}:
        from dataclasses import replace

        changed = {
            "empty-list": [],
            "duplicate": [primary, primary],
            "unknown-head": [replace(primary, head=None)],
            "contradictory": [replace(primary, detached=True)],
            "head-mismatch": [replace(primary, branch="codex/free")],
        }[failure]
        monkeypatch.setattr(sweep.reaper, "list_git_worktrees", lambda _: changed)
    elif failure == "unreadable-census":
        original_directory = sweep._occupation_directory

        def refuse_directory(path: Path) -> bool:
            if path.name == "worktrees":
                raise PermissionError("synthetic census read refusal")
            return original_directory(path)

        monkeypatch.setattr(sweep, "_occupation_directory", refuse_directory)
    else:
        original_file = sweep._occupation_file

        def refuse_head(path: Path) -> str | None:
            if path == repo / ".git" / "HEAD":
                if failure == "missing-head":
                    return None
                raise PermissionError("synthetic HEAD read refusal")
            return original_file(path)

        monkeypatch.setattr(sweep, "_occupation_file", refuse_head)
    with pytest.raises(sweep.SweepError):
        run(repo, apply=True)
    with pytest.raises((OSError, RuntimeError)):
        sweep._delete_archived_refs(repo, [("codex/free", free)])
    assert ref_sha(repo, "codex/free") == free
    assert not list((repo / sweep.ARCHIVE_DIR).glob("*.bundle"))
    assert not (repo / sweep.RECEIPT_PATH).exists()


@pytest.mark.parametrize("mode", ["merge", "apply", "bisect"])
@pytest.mark.parametrize("registration", ["locked", "prunable", "relative"])
def test_native_occupation_survives_linked_checkout_state(repo: Path, mode: str, registration: str) -> None:
    path, tip = occupy_branch(repo, "codex/occupied", mode, linked=True)
    if registration == "locked":
        git(repo, "worktree", "lock", str(path))
    elif registration == "prunable":
        path.rename(repo.parent / "moved-checkout")
    else:
        admin = Path(git(path, "rev-parse", "--absolute-git-dir"))
        (admin / "gitdir").write_text(os.path.relpath(path / ".git", admin) + "\n", encoding="utf-8")
    refused = sweep._git(repo, "branch", "-D", "codex/occupied")
    assert refused.returncode == 1 and "used by worktree" in refused.stderr
    with pytest.raises(sweep.SweepError, match="in-progress operation"):
        run(repo)
    with pytest.raises(RuntimeError, match="in-progress operation"):
        sweep._delete_archived_refs(repo, [("codex/occupied", tip)])
    assert ref_sha(repo, "codex/occupied") == tip


@pytest.mark.parametrize("mode", ["merge", "apply", "bisect"])
def test_native_occupation_blocks_merged_evidence_and_remote_deletion(repo: Path, mode: str) -> None:
    _, tip = occupy_branch(repo, "codex/occupied", mode, linked=True)
    publish(repo, "codex/occupied")
    with pytest.raises(sweep.SweepError, match="in-progress operation"):
        run(repo, apply=True, states={"codex/occupied": [PullRequestState(1, "MERGED", tip)]})
    assert ref_sha(repo, "codex/occupied") == tip
    assert git(repo, "ls-remote", "--heads", "origin", "codex/occupied").split()[0] == tip


@pytest.mark.parametrize(
    "failure",
    [
        "missing-binding",
        "invalid-binding",
        "invalid-update-refs",
        "invalid-update-hashes",
        "missing-bisect-binding",
        "invalid-operation-head",
        "symlink",
        "fifo",
        "oversized",
        "utf8",
        "permission",
        "unsafe-directory",
        "missing-registration",
        "failed-list",
        "detached-merge",
        "detached-cherry-pick",
        "detached-revert",
        "detached-sequencer",
        "detached-apply",
    ],
)
def test_unknown_occupation_cli_and_final_guard_retain_refs(
    repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], failure: str
) -> None:
    heads = {name: commit_unique(repo, name, days=9) for name in ("codex/alpha", "codex/beta")}
    directory = repo / ".git" / "rebase-merge"
    directory.mkdir()
    binding = directory / "head-name"
    binding.write_text("refs/heads/codex/alpha\n", encoding="utf-8")
    if failure == "missing-binding":
        binding.unlink()
    elif failure == "invalid-binding":
        binding.write_text("refs/heads/invalid name\n", encoding="utf-8")
    elif failure == "invalid-update-refs":
        (directory / "update-refs").write_text("refs/heads/codex/beta\n", encoding="utf-8")
    elif failure == "invalid-update-hashes":
        (directory / "update-refs").write_text("refs/heads/codex/beta\n" + ("0" * 64 + "\n") * 2, encoding="utf-8")
    elif failure == "missing-bisect-binding":
        (repo / ".git" / "BISECT_LOG").write_text("", encoding="utf-8")
    elif failure == "invalid-operation-head":
        (repo / ".git" / "MERGE_HEAD").write_text("0" * 64 + "\n", encoding="utf-8")
    elif failure in {"symlink", "fifo", "oversized", "utf8"}:
        binding.unlink()
        if failure == "symlink":
            binding.symlink_to(repo / "readme")
        elif failure == "fifo":
            os.mkfifo(binding)
        elif failure == "oversized":
            binding.write_bytes(b"x" * (1024 * 1024 + 1))
        else:
            binding.write_bytes(b"\xff\n")
    elif failure == "permission":
        original_read = sweep._occupation_file

        def refuse(path: Path) -> str | None:
            if path == binding:
                raise PermissionError("synthetic evidence read refusal")
            return original_read(path)

        monkeypatch.setattr(sweep, "_occupation_file", refuse)
    elif failure == "unsafe-directory":
        binding.unlink()
        directory.rmdir()
        directory.symlink_to(repo)
    elif failure == "missing-registration":
        registration = repo / ".git" / "worktrees" / "missing"
        registration.mkdir(parents=True)
    elif failure == "failed-list":

        def refuse_list(_repo: Path) -> list[sweep.reaper.WorktreeInfo]:
            raise RuntimeError("synthetic Git worktree read refusal")

        monkeypatch.setattr(sweep.reaper, "list_git_worktrees", refuse_list)
    elif failure.startswith("detached-"):
        path = repo.parent / "detached"
        git(repo, "worktree", "add", "--detach", str(path), "main")
        admin = Path(git(path, "rev-parse", "--absolute-git-dir"))
        if failure == "detached-apply":
            state = admin / "rebase-apply"
            state.mkdir()
            (state / "applying").write_text("", encoding="utf-8")
        elif failure == "detached-sequencer":
            (admin / "sequencer").mkdir()
        else:
            marker = {
                "detached-merge": "MERGE_HEAD",
                "detached-cherry-pick": "CHERRY_PICK_HEAD",
                "detached-revert": "REVERT_HEAD",
            }[failure]
            (admin / marker).write_text(heads["codex/alpha"] + "\n", encoding="utf-8")
    with pytest.raises((OSError, RuntimeError)):
        sweep._delete_archived_refs(repo, list(heads.items()))
    original = sweep.sweep

    def synthetic(root: Path, *, apply: bool = False) -> list[sweep.Decision]:
        return original(root, apply=apply, pr_lookup=lookup(), protected_lookup=lambda _: set())

    monkeypatch.setattr(sweep.reaper, "resolve_repo_root", lambda: repo)
    monkeypatch.setattr(sweep, "sweep", synthetic)
    assert sweep.main(["--apply", "--json"]) == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is False and payload["error"]
    assert {name: ref_sha(repo, name) for name in heads} == heads
    assert not list((repo / sweep.ARCHIVE_DIR).glob("*.bundle"))
    assert not (repo / sweep.RECEIPT_PATH).exists()


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


def test_contending_archives_hold_lock_through_deletion(repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    frozen_now = datetime.now(UTC)
    heads = {name: commit_unique(repo, name, days=8) for name in ("codex/alpha", "codex/beta")}
    selected = by_name(run(repo))
    snapshot = sweep._archive_local_snapshot(repo)
    first_bundling = threading.Event()
    release_first = threading.Event()
    contended = threading.Event()
    lane = threading.local()
    events: list[tuple[str, str]] = []
    original_flock = fcntl.flock
    lock_path = repo / sweep.ARCHIVE_LOCK_PATH

    class FrozenDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            return frozen_now

    monkeypatch.setattr(sweep, "datetime", FrozenDatetime)

    def flock(descriptor, operation):
        if (
            getattr(lane, "name", None) == "codex/beta"
            and os.fstat(descriptor).st_ino == lock_path.stat().st_ino
            and operation == fcntl.LOCK_EX
        ):
            with pytest.raises(BlockingIOError):
                original_flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
            contended.set()
        return original_flock(descriptor, operation)

    monkeypatch.setattr(fcntl, "flock", flock)

    def observe(stage, function):
        def call(*args, **kwargs):
            descriptor = os.open(lock_path, os.O_RDWR | os.O_NOFOLLOW)
            try:
                with pytest.raises(BlockingIOError):
                    original_flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
            finally:
                os.close(descriptor)
            events.append((lane.name, stage))
            if lane.name == "codex/alpha" and stage == "bundle":
                first_bundling.set()
                assert release_first.wait(30), "first archive was never released"
            return function(*args, **kwargs)

        return call

    for stage, name in (
        ("bundle", "_write_verified_bundle"),
        ("receipts", "_write_archive_receipts"),
        ("guards", "_archive_delete_blockers"),
        ("delete", "_delete_archived_refs"),
    ):
        monkeypatch.setattr(sweep, name, observe(stage, getattr(sweep, name)))

    def archive(name):
        lane.name = name
        return sweep._apply_archive(
            repo,
            [selected[name]],
            protected=set(sweep.PROTECTED),
            pr_lookup=lookup(),
            issue_lookup=lambda *_: (False, "unused"),
            evidence_cache=sweep._EvidenceCache(),
            archive_after_days=7,
            classification_snapshot=snapshot,
        )

    with ThreadPoolExecutor(max_workers=2) as workers:
        first = workers.submit(archive, "codex/alpha")
        second = None
        try:
            assert first_bundling.wait(30), "first archive never reached bundling"
            second = workers.submit(archive, "codex/beta")
            assert contended.wait(30), "second archive never contended on the held lock"
            assert events == [("codex/alpha", "bundle")]
            assert {name: ref_sha(repo, name) for name in heads} == heads
        finally:
            release_first.set()
        results = first.result(timeout=30) + second.result(timeout=30)

    assert all(item.local_deleted and not item.remote_deleted for item in results)
    assert events == [(name, stage) for name in heads for stage in ("bundle", "receipts", "guards", "delete")]
    rows = receipt_rows(repo)
    assert {row["branch"]: row["sha"] for row in rows} == heads
    assert len({row["bundle"] for row in rows}) == 2
    for row in rows:
        bundle = repo / str(row["bundle"])
        assert row["sha256"] == hashlib.sha256(bundle.read_bytes()).hexdigest()
        assert git(repo, "bundle", "list-heads", str(bundle)) == f"{row['sha']} refs/heads/{row['branch']}"
        assert ref_sha(repo, str(row["branch"])) is None
    assert lock_path.is_file()
    with sweep._archive_lock(repo):
        pass
    assert not list((repo / sweep.ARCHIVE_DIR).glob("*.tmp"))


@pytest.mark.parametrize("collision", ["existing", "at-publication", "symlink"])
def test_bundle_publication_never_overwrites_an_archive(
    repo: Path, monkeypatch: pytest.MonkeyPatch, collision: str
) -> None:
    heads = {name: commit_unique(repo, name, days=8) for name in ("codex/alpha", "codex/beta")}
    original_mkstemp = sweep.tempfile.mkstemp
    original_link = os.link
    existing: list[Path] = []
    old_bytes = b"previously published archive\n"

    def allocate(**kwargs):
        descriptor, name = original_mkstemp(**kwargs)
        staging = Path(name)
        destination = repo / sweep.ARCHIVE_DIR / (staging.name.removeprefix(".").removesuffix(".tmp") + ".bundle")
        existing.append(destination)
        if collision == "existing":
            destination.write_bytes(old_bytes)
        elif collision == "symlink":
            target = repo.parent / "existing-archive"
            target.write_bytes(old_bytes)
            destination.symlink_to(target)
        return descriptor, name

    def publish(source, destination, **kwargs):
        assert Path(source).read_bytes().startswith(b"# v")
        if collision == "at-publication":
            Path(destination).write_bytes(old_bytes)
        return original_link(source, destination, **kwargs)

    monkeypatch.setattr(sweep.tempfile, "mkstemp", allocate)
    monkeypatch.setattr(os, "link", publish)
    found = by_name(run(repo, apply=True))
    assert len(existing) == 1
    assert existing[0].read_bytes() == old_bytes
    assert all(not found[name].local_deleted and found[name].classification == "report-only" for name in heads)
    assert all("File exists" in found[name].reason for name in heads)
    assert {name: ref_sha(repo, name) for name in heads} == heads
    assert receipt_rows(repo) == []
    assert list((repo / sweep.ARCHIVE_DIR).glob("*.bundle")) == existing
    assert not list((repo / sweep.ARCHIVE_DIR).glob("*.tmp"))
    assert not list(Path(os.environ["TMPDIR"]).glob(".stale-local-*"))


@pytest.mark.parametrize("tmpdir_state", ["set", "unset", "empty"])
def test_bundle_stages_in_managed_scratch_and_publishes_verified_bytes(
    repo: Path, monkeypatch: pytest.MonkeyPatch, tmpdir_state: str
) -> None:
    sha = commit_unique(repo, "codex/old-local", days=8)
    scratch = Path(os.environ["TMPDIR"])
    if tmpdir_state != "set":
        if tmpdir_state == "unset":
            monkeypatch.delenv("TMPDIR")
        else:
            monkeypatch.setenv("TMPDIR", "")
        monkeypatch.setenv("LU_SCRATCH_ROOT", str(scratch))
    else:

        def refuse_fallback():
            raise AssertionError("configured TMPDIR must not create fallback scratch")

        monkeypatch.setattr(sweep, "ensure_scratch_root", refuse_fallback)
    original_git = sweep._git
    staged: list[Path] = []

    def capture_git(root: Path, *args: str, **kwargs: object):
        if args[:2] == ("bundle", "create"):
            path = Path(args[2])
            assert path.parent == scratch
            assert not path.is_relative_to(repo)
            assert path.stat().st_mode & 0o777 == 0o600
            staged.append(path)
        return original_git(root, *args, **kwargs)

    monkeypatch.setattr(sweep, "_git", capture_git)
    found = by_name(run(repo, apply=True))
    assert found["codex/old-local"].local_deleted
    assert ref_sha(repo, "codex/old-local") is None
    assert len(staged) == 1 and not staged[0].exists()
    (row,) = receipt_rows(repo)
    bundle = repo / str(row["bundle"])
    assert bundle.parent == repo / sweep.ARCHIVE_DIR
    assert bundle.stat().st_mode & 0o777 == 0o600
    assert git(repo, "bundle", "list-heads", str(bundle)) == f"{sha} refs/heads/codex/old-local"
    assert row["sha256"] == hashlib.sha256(bundle.read_bytes()).hexdigest()


@pytest.mark.parametrize("failure", ["scratch-unwritable", "cross-filesystem"])
def test_managed_staging_failure_retains_all_refs_without_receipts(
    repo: Path, monkeypatch: pytest.MonkeyPatch, failure: str
) -> None:
    heads = {name: commit_unique(repo, name, days=8) for name in ("codex/alpha", "codex/beta")}
    scratch = Path(os.environ["TMPDIR"])
    if failure == "scratch-unwritable":
        blocked = scratch / "not-a-directory"
        blocked.write_bytes(b"blocked\n")
        monkeypatch.setenv("TMPDIR", str(blocked))
        expected_error = "Not a directory"
    else:

        def refuse_link(source, destination, **kwargs):
            assert Path(source).parent == scratch
            assert Path(source).read_bytes().startswith(b"# v")
            assert Path(destination).parent == repo / sweep.ARCHIVE_DIR
            raise OSError(errno.EXDEV, "Invalid cross-device link")

        monkeypatch.setattr(os, "link", refuse_link)
        expected_error = "Invalid cross-device link"
    found = by_name(run(repo, apply=True))
    assert all(found[name].classification == "report-only" and not found[name].local_deleted for name in heads)
    assert all(expected_error in found[name].reason for name in heads)
    assert {name: ref_sha(repo, name) for name in heads} == heads
    assert receipt_rows(repo) == []
    assert not list((repo / sweep.ARCHIVE_DIR).glob("*.bundle"))
    assert not list(scratch.glob(".stale-local-*"))


@pytest.mark.parametrize("failure", ["symlink", "directory", "flock"])
def test_archive_lock_failure_retains_the_batch(repo: Path, monkeypatch: pytest.MonkeyPatch, failure: str) -> None:
    heads = {name: commit_unique(repo, name, days=8) for name in ("codex/alpha", "codex/beta")}
    lock = repo / sweep.ARCHIVE_LOCK_PATH
    lock.parent.mkdir(parents=True)
    if failure == "symlink":
        target = repo.parent / "unrelated-file"
        target.write_bytes(b"keep")
        lock.symlink_to(target)
    elif failure == "directory":
        lock.mkdir()
    else:

        def refuse(*_):
            raise OSError("lock refused")

        monkeypatch.setattr(fcntl, "flock", refuse)
    found = by_name(run(repo, apply=True))
    assert all(not found[name].local_deleted and found[name].classification == "report-only" for name in heads)
    assert {name: ref_sha(repo, name) for name in heads} == heads
    assert receipt_rows(repo) == []
    assert not list(lock.parent.glob("*.bundle"))
    if failure == "symlink":
        assert target.read_bytes() == b"keep"


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


def test_symbolic_alias_cannot_archive_protected_main(repo: Path) -> None:
    sha = commit_at(repo, "main", {"unique.txt": "keep\n"}, "unique main", when=_when(8))
    git(repo, "symbolic-ref", "refs/heads/codex/alias", "refs/heads/main")
    found = by_name(run(repo, apply=True))
    assert ref_sha(repo, "main") == sha
    assert ref_sha(repo, "codex/alias") == sha
    assert found["codex/alias"].local_deleted is False
    assert "symbolic" in found["codex/alias"].reason
    assert not list((repo / sweep.ARCHIVE_DIR).glob("*.bundle"))


def _plant_guard(repo: Path, name: str, sha: str, guard: str, states: dict[str, list[PullRequestState]]) -> None:
    if guard in {"OPEN", "CLOSED", "MERGED"}:
        states[name] = [PullRequestState(99, guard, sha)]
    elif guard in {"task", "recent-task"}:
        directory = repo / "batch_state" / "tasks"
        directory.mkdir(parents=True, exist_ok=True)
        payload = {"worktree_branch": name, "status": "running" if guard == "task" else "failed"}
        (directory / "late.json").write_text(json.dumps(payload), encoding="utf-8")
    else:
        path = repo.parent / "late-worktree"
        git(repo, "worktree", "add", str(path), name)
        if guard == "prunable-worktree":
            # Git still registers the branch after a checkout directory goes missing.
            path.rename(repo.parent / "moved-worktree")


@pytest.mark.parametrize("guard", ["OPEN", "CLOSED", "MERGED", "task", "recent-task", "worktree", "prunable-worktree"])
def test_guard_on_earlier_candidate_during_last_pr_lookup_keeps_batch(
    repo: Path, monkeypatch: pytest.MonkeyPatch, guard: str
) -> None:
    heads = {name: commit_unique(repo, name, days=8) for name in ("codex/aa", "codex/bb", "codex/cc")}
    states: dict[str, list[PullRequestState]] = {}
    receipted = False
    planted = False
    original = sweep._write_archive_receipts

    def receipt(root, confirmed, **kwargs):
        nonlocal receipted
        original(root, confirmed, **kwargs)
        receipted = True

    def prs(root, name):
        nonlocal planted
        if receipted and name == "codex/cc" and not planted:
            _plant_guard(root, "codex/aa", heads["codex/aa"], guard, states)
            planted = True
        return states.get(name, []), None

    monkeypatch.setattr(sweep, "_write_archive_receipts", receipt)
    found = by_name(sweep.sweep(repo, apply=True, pr_lookup=prs, protected_lookup=lambda _: set()))
    assert planted
    assert {name: ref_sha(repo, name) for name in heads} == heads
    assert all(not found[name].local_deleted for name in heads)
    assert "batch kept" in found["codex/aa"].reason
    if guard == "worktree":
        assert git(repo.parent / "late-worktree", "rev-parse", "HEAD") == heads["codex/aa"]


@pytest.mark.parametrize("guard", ["OPEN", "task", "worktree", "head"])
def test_pre_bundle_guard_failure_keeps_entire_selected_batch(
    repo: Path, monkeypatch: pytest.MonkeyPatch, guard: str
) -> None:
    heads = {name: commit_unique(repo, name, days=8) for name in ("codex/alpha", "codex/beta")}
    states: dict[str, list[PullRequestState]] = {}
    original = sweep._apply_archive

    def apply(root, decisions, **kwargs):
        if guard == "head":
            heads["codex/alpha"] = move_head(root, "codex/alpha")
        else:
            _plant_guard(root, "codex/alpha", heads["codex/alpha"], guard, states)
        return original(root, decisions, **kwargs)

    monkeypatch.setattr(sweep, "_apply_archive", apply)
    found = by_name(run(repo, apply=True, states=states))
    assert {name: ref_sha(repo, name) for name in heads} == heads
    assert all(not found[name].local_deleted for name in heads)
    assert not list((repo / sweep.ARCHIVE_DIR).glob("*.bundle"))
    assert not (repo / sweep.RECEIPT_PATH).exists()
    assert "batch kept" in found["codex/beta"].reason


@pytest.mark.parametrize("body", [b"{", b"{}", b"{}\n{", b"bad\n", b"\xff\n", b"\n", b"[]\n"])
def test_existing_broken_receipt_keeps_batch(repo: Path, body: bytes) -> None:
    heads = {name: commit_unique(repo, name, days=8) for name in ("codex/alpha", "codex/beta")}
    path = repo / sweep.RECEIPT_PATH
    path.parent.mkdir(parents=True)
    path.write_bytes(body)
    found = by_name(run(repo, apply=True))
    assert {name: ref_sha(repo, name) for name in heads} == heads
    assert all(not found[name].local_deleted for name in heads)
    assert path.read_bytes() == body
    assert all(sweep.RECEIPT_PATH.as_posix() in found[name].reason for name in heads)


@pytest.mark.parametrize("body", [b"", b"{}\n", b"{}\r\n", '{"note":"a\u2028b"}\n'.encode()])
def test_existing_complete_receipt_allows_archive(repo: Path, body: bytes) -> None:
    commit_unique(repo, "codex/alpha", days=8)
    path = repo / sweep.RECEIPT_PATH
    path.parent.mkdir(parents=True)
    path.write_bytes(body)
    found = by_name(run(repo, apply=True))
    assert found["codex/alpha"].local_deleted is True
    assert ref_sha(repo, "codex/alpha") is None
    assert path.read_bytes().startswith(body)


def test_transaction_does_not_follow_a_last_moment_symbolic_ref(repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    sha = commit_unique(repo, "codex/alias", days=8)
    git(repo, "update-ref", "refs/heads/main", sha)
    original = sweep._git

    def intercept(root, *args, **kwargs):
        if args[:2] == ("update-ref", "--stdin"):
            git(root, "symbolic-ref", "refs/heads/codex/alias", "refs/heads/main")
        return original(root, *args, **kwargs)

    monkeypatch.setattr(sweep, "_git", intercept)
    run(repo, apply=True)
    assert ref_sha(repo, "main") == sha


@pytest.mark.parametrize(
    ("guard", "classification"),
    [
        ("symbolic", "report-only"),
        ("OPEN", "skipped-open-PR"),
        ("CLOSED", "report-only"),
        ("MERGED", "delete-merged"),
        ("task", "skipped-live-task"),
        ("recent-task", "report-only"),
        ("worktree", "skipped-worktree"),
        ("prunable-worktree", "skipped-worktree"),
        ("protected", "protected"),
        ("rescue", "report-only"),
        ("review", "report-only"),
        ("unpushed", "report-only"),
        ("pushed", "archive-expired"),
    ],
)
def test_archive_guard_class_table(repo: Path, guard: str, classification: str) -> None:
    name = {"protected": "codex/protected", "rescue": "rescue/held", "review": "codex/review-1"}.get(
        guard, "codex/alpha"
    )
    sha = commit_unique(repo, name, days=8)
    states: dict[str, list[PullRequestState]] = {}
    if guard == "symbolic":
        git(repo, "branch", "codex/target", sha)
        git(repo, "symbolic-ref", f"refs/heads/{name}", "refs/heads/codex/target")
    elif guard == "unpushed":
        git(repo, "branch", "--set-upstream-to=origin/main", name)
    elif guard == "pushed":
        publish(repo, name)
    elif guard in {"OPEN", "CLOSED", "MERGED", "task", "recent-task", "worktree", "prunable-worktree"}:
        _plant_guard(repo, name, sha, guard, states)
    found = by_name(
        sweep.sweep(
            repo,
            pr_lookup=lookup(states),
            protected_lookup=lambda _: {name} if guard == "protected" else set(),
        )
    )
    assert found[name].classification == classification
    assert not found[name].local_deleted
    assert ref_sha(repo, name) == sha


@pytest.mark.parametrize("guard", ["task", "worktree"])
def test_last_local_check_keeps_batch(repo: Path, monkeypatch: pytest.MonkeyPatch, guard: str) -> None:
    heads = {name: commit_unique(repo, name, days=8) for name in ("codex/alpha", "codex/beta")}
    original = sweep._delete_archived_refs

    def delete(root, pairs):
        _plant_guard(root, "codex/alpha", heads["codex/alpha"], guard, {})
        return original(root, pairs)

    monkeypatch.setattr(sweep, "_delete_archived_refs", delete)
    found = by_name(run(repo, apply=True))
    assert {name: ref_sha(repo, name) for name in heads} == heads
    assert all(not found[name].local_deleted for name in heads)
    assert "final delete check" in found["codex/alpha"].reason


@pytest.mark.parametrize("change", ["task-record", "worktree-registration"])
def test_changed_but_still_eligible_guard_snapshot_keeps_batch(
    repo: Path, monkeypatch: pytest.MonkeyPatch, change: str
) -> None:
    heads = {name: commit_unique(repo, name, days=8) for name in ("codex/alpha", "codex/beta")}
    original = sweep._write_archive_receipts

    def receipt(root, confirmed, **kwargs):
        original(root, confirmed, **kwargs)
        if change == "task-record":
            directory = root / "batch_state" / "tasks"
            directory.mkdir(parents=True)
            (directory / "old.json").write_text(
                json.dumps({"branch": "codex/alpha", "status": "failed", "finished_at": _when(30)}),
                encoding="utf-8",
            )
        else:
            path = root.parent / "late-detached"
            git(root, "worktree", "add", "--detach", str(path), heads["codex/alpha"])

    monkeypatch.setattr(sweep, "_write_archive_receipts", receipt)
    found = by_name(run(repo, apply=True))
    assert {name: ref_sha(repo, name) for name in heads} == heads
    assert all(not found[name].local_deleted for name in heads)


def test_receipt_explains_thin_bundle_prerequisites(repo: Path) -> None:
    commit_unique(repo, "codex/alpha", days=8)
    run(repo, apply=True)
    row = receipt_rows(repo)[0]
    assert row["restore_prerequisites"] == (
        "This thin bundle needs its prerequisite commits present. Fetch them from origin "
        "or run the restore command in a clone of this repository."
    )


@pytest.mark.parametrize(
    "fault",
    [
        None,
        "page",
        "missing",
        "errors",
        "blank",
        "scalar",
        "row",
        "number",
        "state",
        "sha",
        "transport",
        "timeout",
        "missing-tool",
    ],
)
def test_production_pr_snapshot_reads_whole_batch_once(
    repo: Path, monkeypatch: pytest.MonkeyPatch, fault: str | None
) -> None:
    sha = git(repo, "rev-parse", "main")
    row = {"number": 7, "state": "OPEN", "headRefOid": sha}
    connection = {"nodes": [row], "pageInfo": {"hasNextPage": fault == "page"}}
    payload: object = {
        "data": {"repository": {"b0": connection, "b1": {"nodes": [], "pageInfo": {"hasNextPage": False}}}}
    }
    if fault == "missing":
        payload = {"data": {"repository": {"b0": connection}}}
    elif fault == "errors":
        payload = {"errors": [{"message": "unavailable"}]}
    elif fault == "scalar":
        payload = 1
    elif fault == "row":
        connection["nodes"] = [None]
    elif fault in {"number", "state", "sha"}:
        row[{"number": "number", "state": "state", "sha": "headRefOid"}[fault]] = None
    calls = []

    def query(args, **kwargs):
        calls.append(args)
        assert kwargs["fresh"] is True
        assert kwargs["cwd"] == repo
        assert kwargs["capture_output"] is True and kwargs["text"] is True
        assert 'headRefName:"codex/alpha"' in args[-1]
        assert 'headRefName:"codex/beta"' in args[-1]
        if fault == "timeout":
            raise subprocess.TimeoutExpired(args, 30)
        if fault == "missing-tool":
            raise FileNotFoundError("missing test tool")
        return subprocess.CompletedProcess(
            args, 1 if fault == "transport" else 0, "" if fault == "blank" else json.dumps(payload), ""
        )

    monkeypatch.setattr(sweep.reaper, "_github_owner_repo", lambda _: ("example", "project"))
    monkeypatch.setattr(sweep.github_client, "run", query)
    found = sweep._archive_pr_snapshot(repo, ["codex/alpha", "codex/beta"], sweep.reaper._query_pr_states)
    assert len(calls) == 1
    if fault:
        assert all(error == "batch PR snapshot unavailable or incomplete" for _, error in found.values())
    else:
        assert found == {"codex/alpha": ([PullRequestState(7, "OPEN", sha)], None), "codex/beta": ([], None)}


@pytest.mark.parametrize("guard", ["OPEN", "task", "worktree"])
def test_production_batch_response_precedes_local_guard_reads(
    repo: Path, monkeypatch: pytest.MonkeyPatch, guard: str
) -> None:
    heads = {name: commit_unique(repo, name, days=8) for name in ("codex/alpha", "codex/beta")}
    original = sweep._archive_pr_snapshot
    queries = []

    def query(args, **kwargs):
        queries.append(args)
        states: dict[str, list[PullRequestState]] = {}
        _plant_guard(repo, "codex/alpha", heads["codex/alpha"], guard, states)
        nodes = [{"number": 99, "state": "OPEN", "headRefOid": heads["codex/alpha"]}] if guard == "OPEN" else []
        payload = {
            "data": {
                "repository": {
                    "b0": {"nodes": nodes, "pageInfo": {"hasNextPage": False}},
                    "b1": {"nodes": [], "pageInfo": {"hasNextPage": False}},
                }
            }
        }
        return subprocess.CompletedProcess(args, 0, json.dumps(payload), "")

    monkeypatch.setattr(sweep.reaper, "_github_owner_repo", lambda _: ("example", "project"))
    monkeypatch.setattr(sweep.github_client, "run", query)
    monkeypatch.setattr(
        sweep, "_archive_pr_snapshot", lambda root, names, _: original(root, names, sweep.reaper._query_pr_states)
    )
    found = by_name(run(repo, apply=True))
    assert len(queries) == 1
    assert {name: ref_sha(repo, name) for name in heads} == heads
    assert all(not found[name].local_deleted for name in heads)
