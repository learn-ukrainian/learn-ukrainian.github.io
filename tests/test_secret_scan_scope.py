"""Tests for bounded landing-event secret-scan ranges (#7141)."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from scripts.ci.secret_scan_scope import resolve_scan_scope


def _git(root: Path, *args: str) -> str:
    return subprocess.check_output(
        ["git", *args], cwd=root, text=True, timeout=30
    ).strip()


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

    empty_tree = subprocess.check_output(
        ["git", "mktree"], cwd=root, input="", text=True, timeout=30
    ).strip()
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


def test_pull_request_keeps_action_defaults_untouched(tmp_path: Path) -> None:
    scope = resolve_scan_scope("pull_request", repo_root=tmp_path)

    assert scope == resolve_scan_scope("workflow_dispatch", repo_root=tmp_path)
    assert scope.trufflehog_base == ""
    assert scope.trufflehog_head == ""
    assert scope.opsec_range == ""
