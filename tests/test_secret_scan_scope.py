"""Tests for bounded landing-event secret-scan ranges (#7141, #10839)."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from scripts.ci import secret_scan_scope
from scripts.ci.secret_scan_scope import resolve_scan_scope


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


def _ancestor(root: Path, ancestor: str, descendant: str) -> bool:
    result = subprocess.run(
        ["git", "merge-base", "--is-ancestor", ancestor, descendant],
        cwd=root,
        capture_output=True,
        check=False,
        timeout=30,
    )
    return result.returncode == 0


def _in_resolved_range(root: Path, base: str, head: str, sha: str) -> bool:
    """True when ``sha`` is inside the exclusive ``base..head`` scan (empty base = whole branch)."""

    if base == head or not _ancestor(root, sha, head):
        return False
    if base == "":
        return True
    if sha == base:
        return False
    return not _ancestor(root, sha, base)


def _commit_tree(root: Path, text: str, message: str, when: str, parents: list[str], *, move_head: bool) -> str:
    blob = subprocess.check_output(
        ["git", "hash-object", "-w", "--stdin"],
        cwd=root,
        input=text,
        text=True,
        timeout=30,
    ).strip()
    tree = subprocess.check_output(
        ["git", "mktree"],
        cwd=root,
        input=f"100644 blob {blob}\tREADME.md\n",
        text=True,
        timeout=30,
    ).strip()
    command = ["git", "commit-tree", tree]
    for parent in parents:
        command.extend(["-p", parent])
    env = os.environ.copy()
    env["GIT_AUTHOR_DATE"] = when
    env["GIT_COMMITTER_DATE"] = when
    env["GIT_AUTHOR_NAME"] = "ci"
    env["GIT_AUTHOR_EMAIL"] = "ci@example.com"
    env["GIT_COMMITTER_NAME"] = "ci"
    env["GIT_COMMITTER_EMAIL"] = "ci@example.com"
    sha = subprocess.check_output(command, cwd=root, input=message + "\n", text=True, env=env, timeout=30).strip()
    if move_head:
        _git(root, "update-ref", "refs/heads/main", sha)
    return sha


def _pad_first_parent(root: Path, count: int, when: str) -> None:
    """Append ``count`` first-parent commits that share one tree."""

    parent = _git(root, "rev-parse", "HEAD")
    blob = subprocess.check_output(
        ["git", "hash-object", "-w", "--stdin"],
        cwd=root,
        input="pad\n",
        text=True,
        timeout=30,
    ).strip()
    tree = subprocess.check_output(
        ["git", "mktree"],
        cwd=root,
        input=f"100644 blob {blob}\tREADME.md\n",
        text=True,
        timeout=30,
    ).strip()
    env = os.environ.copy()
    env["GIT_AUTHOR_DATE"] = when
    env["GIT_COMMITTER_DATE"] = when
    env["GIT_AUTHOR_NAME"] = "ci"
    env["GIT_AUTHOR_EMAIL"] = "ci@example.com"
    env["GIT_COMMITTER_NAME"] = "ci"
    env["GIT_COMMITTER_EMAIL"] = "ci@example.com"
    for index in range(count):
        parent = subprocess.check_output(
            ["git", "commit-tree", tree, "-p", parent],
            cwd=root,
            input=f"pad {index}\n",
            text=True,
            env=env,
            timeout=30,
        ).strip()
    _git(root, "update-ref", "refs/heads/main", parent)


def _repo_secret_before_tip(root: Path, secret_text: str = "secret-slot\n") -> dict[str, str]:
    """Baseline, a middle commit, then a clean tip. Dates are explicit."""

    _init_repo(root)
    baseline = _commit_at(root, "baseline\n", "baseline", "2026-10-01T00:00:00Z")
    secret = _commit_at(root, secret_text, "secret", "2026-10-15T12:00:00Z")
    tip = _commit_at(root, "tip\n", "tip", "2026-10-16T12:00:00Z")
    return {"baseline": baseline, "secret": secret, "tip": tip}


def _repo_clock_skew(root: Path, secret_text: str = "secret-slot\n") -> dict[str, str]:
    """Reviewer graph: an old-dated descendant sits after the middle commit."""

    _init_repo(root)
    baseline = _commit_at(root, "baseline\n", "baseline", "2026-10-01T00:00:00Z")
    secret = _commit_at(root, secret_text, "secret", "2026-10-15T12:00:00Z")
    descendant = _commit_at(root, "descendant\n", "descendant", "2026-10-01T00:00:00Z")
    tip = _commit_at(root, "tip\n", "tip", "2026-10-16T12:00:00Z")
    return {"baseline": baseline, "secret": secret, "descendant": descendant, "tip": tip}


def test_schedule_secret_before_the_tip_stays_in_the_resolved_range(tmp_path: Path) -> None:
    """HEAD^..HEAD would drop the secret. The ancestry window keeps it.

    The reviewer's resolve time was 2026-10-16 16:00 UTC. The window does not
    read that clock.
    """

    commits = _repo_secret_before_tip(tmp_path)
    scope = resolve_scan_scope("schedule", repo_root=tmp_path)
    parent = _git(tmp_path, "rev-parse", "HEAD^")

    assert parent == commits["secret"]
    assert commits["secret"] not in _git(tmp_path, "rev-list", f"{parent}..HEAD").splitlines()
    assert scope.mode == "schedule"
    assert scope.reason == "branch-history"
    assert scope.trufflehog_base == ""
    assert scope.trufflehog_head == commits["tip"]
    assert scope.trufflehog_base != scope.trufflehog_head
    assert scope.opsec_range == ""
    assert _in_resolved_range(tmp_path, scope.trufflehog_base, scope.trufflehog_head, commits["secret"])


def test_schedule_clock_skew_keeps_the_secret_in_the_resolved_range(tmp_path: Path) -> None:
    """An old-dated descendant must not become the base and hide the secret."""

    commits = _repo_clock_skew(tmp_path)
    scope = resolve_scan_scope("schedule", repo_root=tmp_path)

    assert scope.trufflehog_base != commits["descendant"]
    assert scope.trufflehog_base != scope.trufflehog_head
    assert scope.trufflehog_head == commits["tip"]
    assert commits["secret"] not in _git(tmp_path, "rev-list", f"{commits['descendant']}..HEAD").splitlines()
    assert _in_resolved_range(tmp_path, scope.trufflehog_base, scope.trufflehog_head, commits["secret"])
    assert _in_resolved_range(tmp_path, scope.trufflehog_base, scope.trufflehog_head, commits["descendant"])


def test_schedule_clock_skew_on_a_long_history_walks_first_parent(tmp_path: Path) -> None:
    depth = secret_scan_scope.SCHEDULE_FIRST_PARENT_STEPS
    _init_repo(tmp_path)
    _commit_at(tmp_path, "root\n", "root", "2026-09-01T00:00:00Z")
    _pad_first_parent(tmp_path, depth, "2026-09-01T00:00:00Z")
    commits = {
        "baseline": _commit_at(tmp_path, "baseline\n", "baseline", "2026-10-01T00:00:00Z"),
        "secret": _commit_at(tmp_path, "secret-slot\n", "secret", "2026-10-15T12:00:00Z"),
        "descendant": _commit_at(tmp_path, "descendant\n", "descendant", "2026-10-01T00:00:00Z"),
        "tip": _commit_at(tmp_path, "tip\n", "tip", "2026-10-16T12:00:00Z"),
    }

    scope = resolve_scan_scope("schedule", repo_root=tmp_path)

    assert scope.reason == "ancestry-window"
    assert scope.trufflehog_base == _git(tmp_path, "rev-parse", f"HEAD~{depth}")
    assert scope.trufflehog_head == commits["tip"]
    assert scope.trufflehog_base != commits["descendant"]
    assert scope.trufflehog_base != scope.trufflehog_head
    assert _in_resolved_range(tmp_path, scope.trufflehog_base, scope.trufflehog_head, commits["secret"])


def test_schedule_clean_tip_scans_the_ancestry_window(tmp_path: Path) -> None:
    """A clean, old tip is not narrowed to HEAD^..HEAD."""

    depth = secret_scan_scope.SCHEDULE_FIRST_PARENT_STEPS
    _init_repo(tmp_path)
    _commit_at(tmp_path, "root\n", "root", "2026-09-01T00:00:00Z")
    _pad_first_parent(tmp_path, depth, "2026-09-01T00:00:00Z")
    tip = _commit_at(tmp_path, "clean tip\n", "clean tip", "2026-09-02T00:00:00Z")

    scope = resolve_scan_scope("schedule", repo_root=tmp_path)
    parent = _git(tmp_path, "rev-parse", "HEAD^")
    oldest_included = _git(tmp_path, "rev-parse", f"HEAD~{depth - 1}")

    assert scope.reason == "ancestry-window"
    assert scope.trufflehog_base == _git(tmp_path, "rev-parse", f"HEAD~{depth}")
    assert scope.trufflehog_base != parent
    assert scope.trufflehog_head == tip
    assert scope.trufflehog_base != scope.trufflehog_head
    assert _in_resolved_range(tmp_path, scope.trufflehog_base, scope.trufflehog_head, oldest_included)


def test_schedule_short_history_scans_the_whole_branch(tmp_path: Path) -> None:
    depth = secret_scan_scope.SCHEDULE_FIRST_PARENT_STEPS
    _init_repo(tmp_path)
    root = _commit_at(tmp_path, "root\n", "root", "2026-09-01T00:00:00Z")
    _pad_first_parent(tmp_path, depth - 1, "2026-09-02T00:00:00Z")
    head = _git(tmp_path, "rev-parse", "HEAD")

    scope = resolve_scan_scope("schedule", repo_root=tmp_path)

    assert scope.reason == "branch-history"
    assert scope.trufflehog_base == ""
    assert scope.trufflehog_head == head
    assert scope.trufflehog_base != scope.trufflehog_head
    assert _in_resolved_range(tmp_path, scope.trufflehog_base, scope.trufflehog_head, root)


def test_schedule_scans_the_branch_when_history_is_only_a_few_commits(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    first = _commit_at(tmp_path, "first\n", "first", "2026-10-16T10:00:00Z")
    head = _commit_at(tmp_path, "second\n", "second", "2026-10-16T12:00:00Z")

    scope = resolve_scan_scope("schedule", repo_root=tmp_path)

    assert scope.reason == "branch-history"
    assert scope.trufflehog_base == ""
    assert scope.trufflehog_head == head
    assert scope.trufflehog_base != scope.trufflehog_head
    assert _in_resolved_range(tmp_path, scope.trufflehog_base, scope.trufflehog_head, first)


def test_schedule_root_commit_is_not_an_identical_pair(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    head = _commit_at(tmp_path, "root\n", "root", "2026-09-01T00:00:00Z")

    scope = resolve_scan_scope("schedule", repo_root=tmp_path)

    assert scope.reason == "branch-history"
    assert scope.trufflehog_head == head
    assert scope.trufflehog_base != scope.trufflehog_head
    assert _in_resolved_range(tmp_path, scope.trufflehog_base, scope.trufflehog_head, head)


def test_schedule_range_includes_a_merged_side_commit(tmp_path: Path) -> None:
    depth = secret_scan_scope.SCHEDULE_FIRST_PARENT_STEPS
    _init_repo(tmp_path)
    _commit_at(tmp_path, "root\n", "root", "2026-09-01T00:00:00Z")
    _pad_first_parent(tmp_path, depth, "2026-09-01T00:00:00Z")
    main_tip = _git(tmp_path, "rev-parse", "HEAD")
    side = _commit_tree(tmp_path, "side\n", "side", "2026-10-15T12:00:00Z", [main_tip], move_head=False)
    merge = _commit_tree(tmp_path, "merge\n", "merge", "2026-10-16T12:00:00Z", [main_tip, side], move_head=True)
    tip = _commit_tree(tmp_path, "tip\n", "tip", "2026-10-16T15:00:00Z", [merge], move_head=True)

    scope = resolve_scan_scope("schedule", repo_root=tmp_path)
    first_parents = set(
        _git(
            tmp_path,
            "rev-list",
            "--first-parent",
            f"{scope.trufflehog_base}..{scope.trufflehog_head}",
        ).splitlines()
    )

    assert scope.reason == "ancestry-window"
    assert scope.trufflehog_base == _git(tmp_path, "rev-parse", f"HEAD~{depth}")
    assert scope.trufflehog_head == tip
    assert side not in first_parents
    assert _in_resolved_range(tmp_path, scope.trufflehog_base, scope.trufflehog_head, side)
    assert scope.trufflehog_base != scope.trufflehog_head


def test_schedule_lookup_failure_exits_nonzero_instead_of_narrowing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    commits = _repo_secret_before_tip(tmp_path)
    parent = commits["secret"]
    assert commits["secret"] not in _git(tmp_path, "rev-list", f"{parent}..HEAD").splitlines()
    real_run = subprocess.run

    def fail_rev_list(args: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        if "rev-list" in args:
            raise subprocess.TimeoutExpired(args, secret_scan_scope.GIT_REV_LIST_TIMEOUT_SECONDS)
        return real_run(args, **kwargs)  # type: ignore[arg-type]

    with patch("scripts.ci.secret_scan_scope.subprocess.run", side_effect=fail_rev_list):
        with pytest.raises(secret_scan_scope.SecretScanScopeError, match="refusing to narrow"):
            resolve_scan_scope("schedule", repo_root=tmp_path)

    output = tmp_path / "github_output.txt"
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("EVENT_NAME", "schedule")
    monkeypatch.setenv("GITHUB_OUTPUT", str(output))
    for key in ("MERGE_GROUP_BASE_SHA", "MERGE_GROUP_HEAD_SHA", "PUSH_BEFORE_SHA", "PUSH_AFTER_SHA"):
        monkeypatch.delenv(key, raising=False)
    with patch("scripts.ci.secret_scan_scope.subprocess.run", side_effect=fail_rev_list):
        code = secret_scan_scope.main()
    captured = capsys.readouterr()

    assert code != 0
    assert "timed out" in captured.err
    assert "refusing to narrow" in captured.err
    assert not output.exists()


def test_schedule_rev_list_error_exits_nonzero(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _init_repo(tmp_path)
    _commit_at(tmp_path, "root\n", "root", "2026-10-01T00:00:00Z")
    real_run = subprocess.run

    def fail_rev_list(args: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        if "rev-list" in args:
            return subprocess.CompletedProcess(args, 128, stdout="", stderr="fatal: bad revision")
        return real_run(args, **kwargs)  # type: ignore[arg-type]

    output = tmp_path / "github_output.txt"
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("EVENT_NAME", "schedule")
    monkeypatch.setenv("GITHUB_OUTPUT", str(output))
    with patch("scripts.ci.secret_scan_scope.subprocess.run", side_effect=fail_rev_list):
        code = secret_scan_scope.main()
    captured = capsys.readouterr()

    assert code == 1
    assert "exited 128" in captured.err
    assert "refusing to narrow" in captured.err
    assert not output.exists()


def test_schedule_refuses_identical_base_and_head(tmp_path: Path) -> None:
    sha = "a" * 40
    fake = MagicMock()
    fake.returncode = 0
    fake.stdout = (sha + "\n") * (secret_scan_scope.SCHEDULE_FIRST_PARENT_STEPS + 1)
    fake.stderr = ""

    with patch("scripts.ci.secret_scan_scope.subprocess.run", return_value=fake):
        with pytest.raises(secret_scan_scope.SecretScanScopeError, match="identical"):
            resolve_scan_scope("schedule", repo_root=tmp_path)


def test_schedule_rev_list_garbage_refuses_to_narrow(tmp_path: Path) -> None:
    fake = MagicMock()
    fake.returncode = 0
    fake.stderr = ""
    fake.stdout = "not-a-commit\n"

    with patch("scripts.ci.secret_scan_scope.subprocess.run", return_value=fake):
        with pytest.raises(secret_scan_scope.SecretScanScopeError, match="non-commit"):
            resolve_scan_scope("schedule", repo_root=tmp_path)

    fake.stdout = "\n"
    with patch("scripts.ci.secret_scan_scope.subprocess.run", return_value=fake):
        with pytest.raises(secret_scan_scope.SecretScanScopeError, match="no commits"):
            resolve_scan_scope("schedule", repo_root=tmp_path)


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

    clean = resolve_scan_scope("schedule", repo_root=tmp_path)
    assert clean.trufflehog_base != clean.trufflehog_head
    assert scan(clean.trufflehog_base, clean.trufflehog_head) == 0

    _commit_at(tmp_path, "added " + _planted_uri() + "\n", "planted", "2026-10-16T18:00:00Z")
    planted = resolve_scan_scope("schedule", repo_root=tmp_path)
    assert planted.trufflehog_base != planted.trufflehog_head
    assert scan(planted.trufflehog_base, planted.trufflehog_head) == 183


@pytest.mark.skipif(shutil.which("trufflehog") is None, reason="TruffleHog is not installed")
def test_trufflehog_reproducer_ranges_exit_183_and_a_clean_range_exits_0(tmp_path: Path) -> None:
    """Both reviewer graphs keep the planted secret inside the resolved range."""

    binary = shutil.which("trufflehog")
    assert binary is not None
    planted = "added " + _planted_uri() + "\n"

    def scan(root: Path, scope_base: str, scope_head: str) -> int:
        completed = subprocess.run(
            [
                binary,
                "git",
                f"file://{root}",
                "--since-commit",
                scope_base,
                "--branch",
                scope_head,
                "--fail",
                "--no-update",
                "--results=verified,unknown",
                "--exclude-detectors=Lob",
            ],
            cwd=root,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
            timeout=120,
        )
        return completed.returncode

    skew = tmp_path / "skew"
    before_tip = tmp_path / "before-tip"
    clean = tmp_path / "clean"
    skew.mkdir()
    before_tip.mkdir()
    clean.mkdir()

    skew_commits = _repo_clock_skew(skew, planted)
    skew_scope = resolve_scan_scope("schedule", repo_root=skew)
    assert _in_resolved_range(skew, skew_scope.trufflehog_base, skew_scope.trufflehog_head, skew_commits["secret"])
    assert scan(skew, skew_scope.trufflehog_base, skew_scope.trufflehog_head) == 183

    before_commits = _repo_secret_before_tip(before_tip, planted)
    before_scope = resolve_scan_scope("schedule", repo_root=before_tip)
    assert _in_resolved_range(
        before_tip, before_scope.trufflehog_base, before_scope.trufflehog_head, before_commits["secret"]
    )
    assert scan(before_tip, before_scope.trufflehog_base, before_scope.trufflehog_head) == 183

    _repo_clock_skew(clean)
    clean_scope = resolve_scan_scope("schedule", repo_root=clean)
    assert clean_scope.trufflehog_base != clean_scope.trufflehog_head
    assert scan(clean, clean_scope.trufflehog_base, clean_scope.trufflehog_head) == 0


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
