"""Real-Git regression coverage for scoped clean-pushed reaping (#11025)."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any

import pytest

from scripts.orchestration import reap_worktrees as rw


def git(cwd: Path, *args: str) -> str:
    env = {
        key: value
        for key, value in os.environ.items()
        if not key.startswith(("GIT_", "PRE_COMMIT")) and key != "AGENT_NO_MERGE"
    }
    proc = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=False, env=env, timeout=30)
    assert proc.returncode == 0, proc.stderr or proc.stdout
    return proc.stdout.strip()


@pytest.fixture(scope="module")
def template(tmp_path_factory: pytest.TempPathFactory) -> Path:
    root = tmp_path_factory.mktemp("scoped-clean-pushed-template")
    repo = root / "repo"
    git(root, "init", "--bare", str(root / "origin.git"))
    git(root, "init", "--initial-branch=main", str(repo))
    git(repo, "config", "user.email", "tester@example.com")
    git(repo, "config", "user.name", "Test User")
    (repo / ".gitignore").write_text(".worktrees/\nbatch_state/\n", encoding="utf-8")
    (repo / "README.md").write_text("base\n", encoding="utf-8")
    git(repo, "add", ".gitignore", "README.md")
    git(repo, "commit", "-m", "base")
    git(repo, "remote", "add", "origin", str(root / "origin.git"))
    git(repo, "push", "-u", "origin", "main")
    return root


def copy_repo(template: Path, root: Path) -> Path:
    repo = root / "repo"
    shutil.copytree(template / "repo", repo)
    shutil.copytree(template / "origin.git", root / "origin.git")
    git(repo, "remote", "set-url", "origin", str(root / "origin.git"))
    return repo


@pytest.fixture
def repo(template: Path, tmp_path: Path) -> Path:
    return copy_repo(template, tmp_path)


@pytest.fixture(autouse=True)
def free_processes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # As in the existing clean-pushed fixtures, host processes that these
    # tests did not start cannot make the disposable checkouts uninspectable.
    monkeypatch.setattr(rw, "_uninspectable_same_user", lambda base, proc_root: False)
    fuser = tmp_path / "fuser"
    fuser.write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
    fuser.chmod(0o755)
    monkeypatch.setattr(rw, "_FUSER", str(fuser))


def age_tree(tree: Path) -> None:
    admin = Path((tree / ".git").read_text(encoding="utf-8").split("gitdir:", 1)[1].strip())
    stamp = int(time.time()) - 7200
    log = admin / "logs" / "HEAD"
    # Reflog entry timestamps, rather than just the file mtime, decide idleness.
    log.write_text(
        re.sub(
            r" [0-9]+ ([+-][0-9]{4})(?=\t|$)",
            f" {stamp} \\1",
            log.read_text(encoding="utf-8"),
            flags=re.MULTILINE,
        ),
        encoding="utf-8",
    )
    for path in (admin / "HEAD", admin / "index", log):
        os.utime(path, (stamp, stamp))


def dispatch_tree(repo: Path, name: str) -> Path:
    tree = repo / ".worktrees" / "dispatch" / "codex" / name
    tree.parent.mkdir(parents=True, exist_ok=True)
    git(repo, "worktree", "add", "-b", f"codex/{name}", str(tree), "main")
    age_tree(tree)
    return tree


def outcome(payload: dict[str, Any], tree: Path, repo: Path) -> dict[str, Any]:
    shown = tree.relative_to(repo).as_posix()
    matches = [row for row in (*payload["removed"], *payload["skipped"]) if row["path"] == shown]
    assert len(matches) == 1, payload
    return matches[0]


def cli(capsys: pytest.CaptureFixture[str], *args: str) -> list[dict[str, Any]]:
    assert rw.main(["--clean-pushed", "--json", *args]) == 0
    raw = capsys.readouterr().out.strip()
    reports = []
    while raw:
        report, end = json.JSONDecoder().raw_decode(raw)
        reports.append(report)
        raw = raw[end:].lstrip()
    return reports


@pytest.mark.parametrize("apply", [False, True])
def test_cli_selects_only_named_tree(repo: Path, capsys: pytest.CaptureFixture[str], apply: bool) -> None:
    a, b = dispatch_tree(repo, "task-a"), dispatch_tree(repo, "task-b")

    [report] = cli(capsys, "--repo-root", str(repo), "--worktree", str(a), *(["--apply"] if apply else []))

    assert [row["path"] for row in report["removed"]] == [a.relative_to(repo).as_posix()], report
    assert outcome(report, a, repo)["action"] == ("removed" if apply else "would_remove")
    assert outcome(report, b, repo)["action"] == "skipped"
    assert outcome(report, b, repo)["reason"] == "not_selected"
    assert a.exists() is not apply
    assert b.is_dir()
    assert str(b) in git(repo, "worktree", "list", "--porcelain")


@pytest.mark.parametrize("apply", [False, True])
def test_cli_without_filter_keeps_existing_report(repo: Path, capsys: pytest.CaptureFixture[str], apply: bool) -> None:
    a, b = dispatch_tree(repo, "task-a"), dispatch_tree(repo, "task-b")

    [report] = cli(capsys, "--repo-root", str(repo), *(["--apply"] if apply else []))

    assert [row["path"] for row in report["removed"]] == [p.relative_to(repo).as_posix() for p in (a, b)]
    assert [row["action"] for row in report["removed"]] == ["removed" if apply else "would_remove"] * 2
    assert report["skipped"] == [
        {
            "path": ".",
            "action": "skipped",
            "reason": "primary checkout",
            "head": git(repo, "rev-parse", "HEAD"),
            "branch": "main",
            "task_status": None,
            "size_mb": None,
        }
    ]
    assert set(report) == {
        "dry_run",
        "removed",
        "skipped",
        "freed_mb",
        "lock_busy",
        "refusal",
        "refs_stale",
        "uninspectable",
        "late_change",
        "unpublished_reflog_commit",
        "census_refs",
        "census_missing",
    }
    assert a.exists() is not apply and b.exists() is not apply


def test_explicit_none_is_byte_identical_to_default(repo: Path) -> None:
    dispatch_tree(repo, "task-a")
    dispatch_tree(repo, "task-b")
    default = rw.reap_clean_pushed(repo_root=repo).as_dict()
    explicit = rw.reap_clean_pushed(repo_root=repo, target_paths=None).as_dict()
    assert json.dumps(explicit) == json.dumps(default)


@pytest.mark.parametrize("kind", ["unknown", "dispatch-parent", "agent-parent", "prefix-sibling"])
@pytest.mark.parametrize("apply", [False, True])
def test_nonmatching_path_never_widens_selection(
    repo: Path, capsys: pytest.CaptureFixture[str], kind: str, apply: bool
) -> None:
    survivor = dispatch_tree(repo, "task-extra")
    target = {
        "unknown": repo / "unregistered",
        "dispatch-parent": survivor.parent.parent,
        "agent-parent": survivor.parent,
        "prefix-sibling": survivor.with_name("task"),
    }[kind]

    [report] = cli(capsys, "--repo-root", str(repo), "--worktree", str(target), *(["--apply"] if apply else []))

    assert report["removed"] == []
    assert outcome(report, target, repo)["action"] == "skipped"
    assert outcome(report, target, repo)["reason"] == "not_registered"
    assert outcome(report, survivor, repo)["reason"] == "not_selected"
    assert survivor.is_dir()


def test_empty_sequence_selects_nobody(repo: Path) -> None:
    survivor = dispatch_tree(repo, "task-a")
    report = rw.reap_clean_pushed(repo_root=repo, target_paths=[], dry_run=False).as_dict()
    assert report["removed"] == ()
    assert outcome(report, survivor, repo)["reason"] == "not_selected"
    assert survivor.is_dir()


@pytest.mark.parametrize("apply", [False, True])
def test_repeatable_worktree_selects_both(repo: Path, capsys: pytest.CaptureFixture[str], apply: bool) -> None:
    a, b = dispatch_tree(repo, "task-a"), dispatch_tree(repo, "task-b")
    c = dispatch_tree(repo, "task-c")
    [report] = cli(
        capsys,
        "--repo-root",
        str(repo),
        "--worktree",
        str(a),
        "--worktree",
        str(b),
        *(["--apply"] if apply else []),
    )
    assert [row["path"] for row in report["removed"]] == [p.relative_to(repo).as_posix() for p in (a, b)]
    assert outcome(report, c, repo)["reason"] == "not_selected"
    assert a.exists() is not apply and b.exists() is not apply
    assert c.is_dir()


@pytest.mark.parametrize("spelling", ["relative", "symlink"])
def test_argument_resolves_against_process_cwd(
    repo: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch, spelling: str
) -> None:
    a, b = dispatch_tree(repo, "task-a"), dispatch_tree(repo, "task-b")
    monkeypatch.chdir(tmp_path)
    if spelling == "relative":
        target = a.relative_to(tmp_path)
    else:
        target = tmp_path / "alias"
        target.symlink_to(a, target_is_directory=True)
    [report] = cli(capsys, "--repo-root", str(repo), "--worktree", str(target), "--apply")
    assert [row["path"] for row in report["removed"]] == [a.relative_to(repo).as_posix()]
    assert outcome(report, b, repo)["reason"] == "not_selected"
    assert not a.exists() and b.is_dir()


@pytest.mark.parametrize("apply", [False, True])
def test_scoped_multi_repo_does_not_drop_filter(
    repo: Path, template: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str], apply: bool
) -> None:
    a = dispatch_tree(repo, "task-a")
    other = copy_repo(template, tmp_path / "second")
    survivor = dispatch_tree(other, "task-a")
    first, second = cli(
        capsys,
        "--repo-root",
        str(repo),
        "--repo-root",
        str(other),
        "--worktree",
        str(a),
        *(["--apply"] if apply else []),
    )
    assert [row["path"] for row in first["removed"]] == [a.relative_to(repo).as_posix()]
    assert second["removed"] == []
    assert outcome(second, survivor, other)["reason"] == "not_selected"
    assert any(row["reason"] == "not_registered" for row in second["skipped"])
    assert a.exists() is not apply and survivor.is_dir()


@pytest.mark.parametrize(
    ("guard", "reason"),
    [
        ("dirty", "dirty or untracked files"),
        ("unpushed", "commits not on origin"),
        ("outside", "outside .worktrees/dispatch/"),
        ("symlink-checkout", "path is a symlink, missing, or not a directory"),
        ("symlink-parent", "path is a symlink, missing, or not a directory"),
    ],
)
def test_symlink_argument_preserves_existing_refusals(
    repo: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str], guard: str, reason: str
) -> None:
    a, b = dispatch_tree(repo, "task-a"), dispatch_tree(repo, "task-b")
    if guard == "dirty":
        (a / "README.md").write_text("changed\n", encoding="utf-8")
    elif guard == "unpushed":
        (a / "README.md").write_text("local only\n", encoding="utf-8")
        git(a, "commit", "-am", "local only")
        age_tree(a)
    elif guard == "outside":
        a = repo / ".worktrees" / "review"
        git(repo, "worktree", "add", "--detach", str(a), "main")
        age_tree(a)
    elif guard == "symlink-checkout":
        moved = tmp_path / "moved-checkout"
        a.rename(moved)
        a.symlink_to(moved, target_is_directory=True)
    else:
        # Only this checkout's parent becomes a symlink; B stays eligible.
        parent = a.parent.parent / "other-agent"
        parent.mkdir()
        git(repo, "worktree", "move", str(a), str(parent / a.name))
        a = parent / a.name
        moved = tmp_path / "moved-parent"
        parent.rename(moved)
        parent.symlink_to(moved, target_is_directory=True)
    alias = tmp_path / "alias"
    alias.symlink_to(a, target_is_directory=True)

    [report] = cli(capsys, "--repo-root", str(repo), "--worktree", str(alias), "--apply")

    assert report["removed"] == []
    row = outcome(report, a, repo)
    assert (row["action"], row["reason"]) == ("skipped", reason)
    assert a.is_dir() and b.is_dir()
    assert outcome(report, b, repo)["reason"] == "not_selected"


def test_default_repository_keeps_worktree_filter(
    repo: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    a, b = dispatch_tree(repo, "task-a"), dispatch_tree(repo, "task-b")
    monkeypatch.setattr(rw, "resolve_repo_root", lambda: repo)

    [report] = cli(capsys, "--worktree", str(a), "--apply")

    assert [row["path"] for row in report["removed"]] == [a.relative_to(repo).as_posix()]
    assert outcome(report, b, repo)["reason"] == "not_selected"
    assert not a.exists() and b.is_dir()


def test_selected_tree_cannot_bypass_failed_origin_refresh(repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    a, b = dispatch_tree(repo, "task-a"), dispatch_tree(repo, "task-b")
    git(repo, "remote", "set-url", "origin", str(repo.parent / "missing-origin.git"))

    # Stale refs keep the existing CLI exit status of zero, with a typed refusal.
    assert rw.main(["--clean-pushed", "--repo-root", str(repo), "--worktree", str(a), "--apply", "--json"]) == 0

    report = json.loads(capsys.readouterr().out)
    assert report["refs_stale"] is True
    assert report["refusal"].startswith("refs_stale:")
    assert report["removed"] == []
    assert a.is_dir() and b.is_dir()


def test_scoped_journal_failure_reports_error_without_removal(
    repo: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    a, b = dispatch_tree(repo, "task-a"), dispatch_tree(repo, "task-b")

    def unavailable(*args: Any, **kwargs: Any) -> None:
        raise OSError("test journal unavailable")

    monkeypatch.setattr(rw.reaper_lifecycle, "append_journal", unavailable)

    assert rw.main(["--clean-pushed", "--repo-root", str(repo), "--worktree", str(a), "--apply", "--json"]) == 1

    report = json.loads(capsys.readouterr().out)
    row = outcome(report, a, repo)
    assert row["action"] == "error"
    assert row["reason"] == "journal write failed (test journal unavailable); run stopped"
    assert report["removed"] == []
    assert a.is_dir() and b.is_dir()


def test_scoped_run_refuses_unsafe_lock(repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    a, b = dispatch_tree(repo, "task-a"), dispatch_tree(repo, "task-b")
    (repo / ".git" / "worktree-reaper.lock").mkdir()

    assert rw.main(["--clean-pushed", "--repo-root", str(repo), "--worktree", str(a), "--apply", "--json"]) == 2

    report = json.loads(capsys.readouterr().out)
    assert report["refusal"].startswith("reaper lock unavailable or unsafe:")
    assert report["removed"] == []
    assert a.is_dir() and b.is_dir()
