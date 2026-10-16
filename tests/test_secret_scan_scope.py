"""Tests for bounded landing-event secret-scan ranges (#7141, #10839)."""

from __future__ import annotations

import os
import shutil
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from scripts.ci import secret_scan_scope
from scripts.ci.secret_scan_scope import resolve_scan_scope

_NOW = datetime(2026, 10, 16, 16, 0, tzinfo=UTC)


def _git(root: Path, *args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=root, text=True, timeout=30).strip()


def _repo_with_range(root: Path) -> tuple[str, str, str]:
    _git(root, "init", "--initial-branch=main")
    _git(root, "config", "user.email", "ci@example.com")
    _git(root, "config", "user.name", "ci")
    (root / "README.md").write_text("base\n", encoding="utf-8")
    _git(root, "add", "README.md")
    _git(root, "commit", "-m", "base")
    base = _git(root, "rev-parse", "HEAD")

    (root / "README.md").write_text("head\n", encoding="utf-8")
    _git(root, "commit", "-am", "head")
    head = _git(root, "rev-parse", "HEAD")

    empty_tree = subprocess.check_output(["git", "mktree"], cwd=root, input="", text=True, timeout=30).strip()
    unrelated = subprocess.check_output(
        ["git", "commit-tree", empty_tree],
        cwd=root,
        input="unrelated\n",
        text=True,
        timeout=30,
    ).strip()
    return base, head, unrelated


def _repo_with_merge_group(root: Path) -> tuple[str, str]:
    _git(root, "init", "--initial-branch=main")
    _git(root, "config", "user.email", "ci@example.com")
    _git(root, "config", "user.name", "ci")
    (root / "README.md").write_text("base\n", encoding="utf-8")
    _git(root, "add", "README.md")
    _git(root, "commit", "-m", "base")
    base = _git(root, "rev-parse", "HEAD")

    (root / "README.md").write_text("queued\n", encoding="utf-8")
    _git(root, "commit", "-am", "queued change")
    queued_head = _git(root, "rev-parse", "HEAD")
    tree = _git(root, "rev-parse", "HEAD^{tree}")
    merge_group_head = subprocess.check_output(
        ["git", "commit-tree", tree, "-p", base, "-p", queued_head],
        cwd=root,
        input="merge group\n",
        text=True,
        timeout=30,
    ).strip()
    return base, merge_group_head


def test_merge_group_uses_documented_base_and_head_range(tmp_path: Path) -> None:
    base, head = _repo_with_merge_group(tmp_path)
    event = {
        "action": "checks_requested",
        "merge_group": {
            "base_ref": "refs/heads/main",
            "base_sha": base,
            "head_sha": head,
        },
    }

    scope = resolve_scan_scope(
        "merge_group",
        merge_group_base_sha=event["merge_group"]["base_sha"],
        merge_group_head_sha=event["merge_group"]["head_sha"],
        repo_root=tmp_path,
    )

    assert scope.mode == "scoped"
    assert scope.reason == "validated-range"
    assert scope.trufflehog_base == base
    assert scope.trufflehog_head == head
    assert scope.opsec_range == f"{base}..{head}"


def test_push_uses_event_before_and_after(tmp_path: Path) -> None:
    base, head, _ = _repo_with_range(tmp_path)

    scope = resolve_scan_scope(
        "push",
        push_before_sha=base,
        push_after_sha=head,
        repo_root=tmp_path,
    )

    assert scope.mode == "scoped"
    assert scope.trufflehog_base == base
    assert scope.trufflehog_head == head


@pytest.mark.parametrize(
    ("event_name", "base_field", "head_field", "reason"),
    [
        ("merge_group", "merge_group_base_sha", "merge_group_head_sha", "missing-base-sha"),
        ("push", "push_before_sha", "push_after_sha", "zero-base-sha"),
    ],
)
def test_unresolvable_landing_range_forces_full_scan(
    tmp_path: Path,
    event_name: str,
    base_field: str,
    head_field: str,
    reason: str,
) -> None:
    _, head, _ = _repo_with_range(tmp_path)
    values = {
        base_field: "" if reason == "missing-base-sha" else "0" * 40,
        head_field: head,
        "repo_root": tmp_path,
    }

    scope = resolve_scan_scope(event_name, **values)

    assert scope.mode == "full-fallback"
    assert scope.reason == reason
    assert scope.trufflehog_base == ""
    assert scope.trufflehog_head == "HEAD"
    assert scope.opsec_range == ""


def test_force_push_and_equal_range_fail_closed_to_full_scan(tmp_path: Path) -> None:
    base, head, unrelated = _repo_with_range(tmp_path)

    forced = resolve_scan_scope(
        "push",
        push_before_sha=base,
        push_after_sha=unrelated,
        repo_root=tmp_path,
    )
    empty = resolve_scan_scope(
        "merge_group",
        merge_group_base_sha=head,
        merge_group_head_sha=head,
        repo_root=tmp_path,
    )

    assert forced.reason == "base-not-ancestor"
    assert forced.trufflehog_head == "HEAD"
    assert empty.reason == "empty-range"
    assert empty.trufflehog_head == "HEAD"


def _commit_at(root: Path, text: str, message: str, when: str) -> str:
    (root / "README.md").write_text(text, encoding="utf-8")
    _git(root, "add", "README.md")
    env = os.environ.copy()
    env["GIT_AUTHOR_DATE"] = when
    env["GIT_COMMITTER_DATE"] = when
    subprocess.check_call(["git", "commit", "-m", message], cwd=root, env=env, timeout=30)
    return _git(root, "rev-parse", "HEAD")


def _init_repo(root: Path) -> None:
    _git(root, "init", "--initial-branch=main")
    _git(root, "config", "user.email", "ci@example.com")
    _git(root, "config", "user.name", "ci")


def test_schedule_lookback_scans_commits_after_the_cutoff(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    old = _commit_at(tmp_path, "old\n", "old", "2026-10-01T00:00:00Z")
    head = _commit_at(tmp_path, "new\n", "new", "2026-10-16T12:00:00Z")

    scope = resolve_scan_scope("schedule", repo_root=tmp_path, now=_NOW)

    assert scope.mode == "schedule"
    assert scope.reason == "lookback"
    assert scope.trufflehog_base == old
    assert scope.trufflehog_head == head
    assert scope.trufflehog_base != scope.trufflehog_head
    assert scope.opsec_range == ""


def test_schedule_with_nothing_new_scans_the_tip_commit(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    parent = _commit_at(tmp_path, "old\n", "old", "2026-09-01T00:00:00Z")
    head = _commit_at(tmp_path, "older\n", "still old", "2026-09-02T00:00:00Z")

    scope = resolve_scan_scope("schedule", repo_root=tmp_path, now=_NOW)

    assert scope.reason == "tip-commit"
    assert scope.trufflehog_base == parent
    assert scope.trufflehog_head == head
    assert scope.trufflehog_base != scope.trufflehog_head
    assert scope.opsec_range == ""


def test_schedule_scans_the_branch_when_every_commit_is_inside_the_window(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    _commit_at(tmp_path, "first\n", "first", "2026-10-16T10:00:00Z")
    head = _commit_at(tmp_path, "second\n", "second", "2026-10-16T12:00:00Z")

    scope = resolve_scan_scope("schedule", repo_root=tmp_path, now=_NOW)

    assert scope.reason == "branch-history"
    assert scope.trufflehog_base == ""
    assert scope.trufflehog_head == head
    assert scope.trufflehog_base != scope.trufflehog_head


def test_schedule_root_commit_is_not_an_identical_pair(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    head = _commit_at(tmp_path, "root\n", "root", "2026-09-01T00:00:00Z")

    scope = resolve_scan_scope("schedule", repo_root=tmp_path, now=_NOW)

    assert scope.trufflehog_head == head
    assert scope.trufflehog_base != scope.trufflehog_head


def test_schedule_lookback_failure_scans_the_tip_commit(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    parent = _commit_at(tmp_path, "old\n", "old", "2026-10-01T00:00:00Z")
    head = _commit_at(tmp_path, "new\n", "new", "2026-10-16T12:00:00Z")
    real_run = subprocess.run

    def fail_rev_list(args: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        if "rev-list" in args:
            raise subprocess.TimeoutExpired(args, secret_scan_scope.GIT_REV_LIST_TIMEOUT_SECONDS)
        return real_run(args, **kwargs)  # type: ignore[arg-type]

    with patch("scripts.ci.secret_scan_scope.subprocess.run", side_effect=fail_rev_list):
        scope = resolve_scan_scope("schedule", repo_root=tmp_path, now=_NOW)

    assert scope.reason == "lookback-unresolved"
    assert scope.trufflehog_base == parent
    assert scope.trufflehog_head == head
    assert scope.trufflehog_base != scope.trufflehog_head


def test_schedule_without_head_does_not_pass_an_identical_pair(tmp_path: Path) -> None:
    with patch("scripts.ci.secret_scan_scope.subprocess.run", side_effect=subprocess.TimeoutExpired(["git"], 10)):
        scope = resolve_scan_scope("schedule", repo_root=tmp_path, now=_NOW)

    assert scope.reason == "unresolvable-head-sha"
    assert scope.trufflehog_base != scope.trufflehog_head


def _planted_uri() -> str:
    # Pieces stay separate so the test source is not a credential literal.
    user = "ci-user"
    secret = "ci-password"
    host = "example.invalid"
    return "https://" + user + ":" + secret + "@" + host + "/resource"


@pytest.mark.skipif(shutil.which("trufflehog") is None, reason="TruffleHog is not installed")
def test_schedule_range_passes_when_clean_and_fails_when_a_secret_is_planted(tmp_path: Path) -> None:
    """The arguments the workflow passes: a clean lookback exits 0, a planted secret exits 183."""

    _init_repo(tmp_path)
    _commit_at(tmp_path, "old\n", "old", "2026-10-01T00:00:00Z")
    _commit_at(tmp_path, "clean\n", "clean", "2026-10-16T12:00:00Z")
    binary = shutil.which("trufflehog")
    assert binary is not None

    def scan(scope_base: str, scope_head: str) -> int:
        completed = subprocess.run(
            [
                binary,
                "git",
                f"file://{tmp_path}",
                "--since-commit",
                scope_base,
                "--branch",
                scope_head,
                "--fail",
                "--no-update",
                "--results=verified,unknown",
                "--exclude-detectors=Lob",
            ],
            cwd=tmp_path,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
            timeout=120,
        )
        return completed.returncode

    clean = resolve_scan_scope("schedule", repo_root=tmp_path, now=_NOW)
    assert clean.trufflehog_base != clean.trufflehog_head
    assert scan(clean.trufflehog_base, clean.trufflehog_head) == 0

    _commit_at(tmp_path, "added " + _planted_uri() + "\n", "planted", "2026-10-16T18:00:00Z")
    planted_at = datetime(2026, 10, 16, 20, 0, tzinfo=UTC)
    planted = resolve_scan_scope("schedule", repo_root=tmp_path, now=planted_at)
    assert planted.trufflehog_base != planted.trufflehog_head
    assert scan(planted.trufflehog_base, planted.trufflehog_head) == 183


def test_pull_request_keeps_action_defaults_untouched(tmp_path: Path) -> None:
    scope = resolve_scan_scope("pull_request", repo_root=tmp_path)

    assert scope == resolve_scan_scope("workflow_dispatch", repo_root=tmp_path)
    assert scope.trufflehog_base == ""
    assert scope.trufflehog_head == ""
    assert scope.opsec_range == ""


def test_commit_exists_passes_timeout_and_handles_timeout(tmp_path: Path) -> None:
    fake = MagicMock()
    fake.returncode = 0
    with patch("subprocess.run", return_value=fake) as run_mock:
        assert secret_scan_scope._commit_exists(tmp_path, "a" * 40) is True

    assert run_mock.call_args.kwargs.get("timeout") == secret_scan_scope.GIT_CAT_FILE_TIMEOUT_SECONDS

    with patch("subprocess.run", side_effect=subprocess.TimeoutExpired(["git", "cat-file"], 10)):
        assert secret_scan_scope._commit_exists(tmp_path, "a" * 40) is False


def test_is_ancestor_passes_timeout_and_handles_timeout(tmp_path: Path) -> None:
    fake = MagicMock()
    fake.returncode = 0
    with patch("subprocess.run", return_value=fake) as run_mock:
        assert secret_scan_scope._is_ancestor(tmp_path, "a" * 40, "b" * 40) is True

    assert run_mock.call_args.kwargs.get("timeout") == secret_scan_scope.GIT_IS_ANCESTOR_TIMEOUT_SECONDS

    with patch("subprocess.run", side_effect=subprocess.TimeoutExpired(["git", "merge-base"], 30)):
        assert secret_scan_scope._is_ancestor(tmp_path, "a" * 40, "b" * 40) is False
