"""Evidence deletion: stable patch-ids, a closing merged pull request, and the receipt."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest

from scripts.hygiene import branch_sweep as sweep
from scripts.orchestration.reap_worktrees import PullRequestState


def git(repo: Path, *args: str) -> str:
    command = ["git", "-c", "core.hooksPath=/dev/null", *args] if args[0] == "push" else ["git", *args]
    result = subprocess.run(command, cwd=repo, capture_output=True, text=True, check=False, timeout=30)
    assert result.returncode == 0, f"git {args[0]} failed: {result.stderr}"
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
    (root / "readme").write_text("base\n")
    git(root, "add", "readme")
    git(root, "commit", "-m", "base")
    git(root, "remote", "add", "origin", str(remote))
    git(root, "push", "-u", "origin", "main")
    return root


def commit_files(repo: Path, branch: str, files: dict[str, str], message: str) -> str:
    """Commit ``files`` on ``branch`` without checking it out."""
    index = repo / ".git" / "evidence-index"
    index.unlink(missing_ok=True)
    env = os.environ.copy()
    env["GIT_INDEX_FILE"] = str(index)

    def run(*args: str) -> str:
        result = subprocess.run(
            ["git", *args], cwd=repo, env=env, capture_output=True, text=True, check=False, timeout=30
        )
        assert result.returncode == 0, f"git {args[0]} failed: {result.stderr}"
        return result.stdout.strip()

    run("read-tree", branch)
    for name, content in files.items():
        path = repo / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
        run("add", "--", name)
    tree = run("write-tree")
    parent = git(repo, "rev-parse", branch)
    sha = run("commit-tree", tree, "-p", parent, "-m", message)
    git(repo, "update-ref", f"refs/heads/{branch}", sha)
    index.unlink(missing_ok=True)
    return sha


def publish(repo: Path, *names: str) -> None:
    for name in names:
        git(repo, "push", "origin", name)


def start(repo: Path, name: str) -> None:
    git(repo, "branch", name, "main")


def closure(number: int | None) -> sweep.IssueLookup:
    def lookup(_repo: Path, _issue: int) -> tuple[sweep.IssueClosure | None, str | None]:
        return sweep.IssueClosure(number), None

    return lookup


def only(
    repo: Path,
    name: str,
    *,
    apply: bool = False,
    states: dict[str, list[PullRequestState]] | None = None,
    issues: sweep.IssueLookup | None = None,
) -> sweep.Decision:
    states = states or {}

    def prs(_repo: Path, branch: str) -> tuple[list[PullRequestState], str | None]:
        return states.get(branch, []), None

    return next(
        item
        for item in sweep.sweep(
            repo,
            apply=apply,
            pr_lookup=prs,
            protected_lookup=lambda _repo: set(),
            issue_lookup=issues or closure(None),
        )
        if item.branch == name
    )


def ledger(repo: Path) -> Path:
    return sweep._ledger_file(repo)


def same_change(repo: Path, name: str) -> str:
    """A branch commit whose patch-id is on main under a different SHA."""
    start(repo, name)
    tip = commit_files(repo, name, {"alpha.txt": "same\n"}, f"work on {name}")
    commit_files(repo, "main", {"alpha.txt": "same\n"}, "landed with another message")
    publish(repo, "main", name)
    return tip


def http(body: object, *, status: str = "200 OK", link: str | None = None) -> str:
    headers = [f"HTTP/2.0 {status}"]
    if link:
        headers.append(f"Link: {link}")
    return "\r\n".join(headers) + "\r\n\r\n" + json.dumps(body)


def timeline_pr(number: int, merged_at: str, title: str, body: str = "") -> dict[str, object]:
    return {
        "event": "cross-referenced",
        "source": {
            "type": "issue",
            "issue": {
                "number": number,
                "title": title,
                "body": body,
                "pull_request": {"merged_at": merged_at},
            },
        },
    }


def test_patch_id_equivalent_branch_is_deleted_after_its_receipt(repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    tip = same_change(repo, "codex/impl-1001")
    seen: list[str] = []
    original = sweep._git

    def capture(root: Path, *args: str, **kwargs):
        if args and args[0] == "push":
            text = ledger(repo).read_text(encoding="utf-8")
            assert tip in text
            seen.append(text)
        return original(root, *args, **kwargs)

    monkeypatch.setattr(sweep, "_git", capture)
    item = only(repo, "codex/impl-1001", apply=True)
    assert item.classification == "delete-evidence"
    assert item.evidence_kind == "patch-id"
    assert item.remote_deleted and item.local_deleted
    assert seen
    receipt = json.loads(ledger(repo).read_text(encoding="utf-8").splitlines()[0])
    assert receipt["branch"] == "codex/impl-1001"
    assert receipt["tip_sha"] == tip
    assert receipt["evidence_kind"] == "patch-id"
    assert receipt["at"].endswith("Z")
    assert not git(repo, "ls-remote", "--heads", "origin", "codex/impl-1001")
    assert not git(repo, "branch", "--list", "codex/impl-1001")


def test_dry_run_reports_patch_id_evidence_without_writing_or_deleting(repo: Path) -> None:
    same_change(repo, "codex/impl-1001")
    item = only(repo, "codex/impl-1001")
    assert item.classification == "delete-evidence"
    assert item.evidence_kind == "patch-id"
    assert not item.remote_deleted and not item.local_deleted
    assert not ledger(repo).exists()
    assert git(repo, "ls-remote", "--heads", "origin", "codex/impl-1001")


def test_superseded_branch_is_accepted_when_merged_pr_covers_its_files(repo: Path) -> None:
    start(repo, "codex/impl-2002")
    tip = commit_files(repo, "codex/impl-2002", {"alpha.txt": "branch\n"}, "rewrite the guard")
    commit_files(repo, "main", {"alpha.txt": "landed\n", "extra.txt": "y\n"}, "land the guard (#2002) (#4444)")
    publish(repo, "main", "codex/impl-2002")
    item = only(repo, "codex/impl-2002", apply=True, issues=closure(4444))
    assert item.classification == "delete-evidence"
    assert item.evidence_kind == "merged-pr"
    assert "4444" in item.reason
    receipt = json.loads(ledger(repo).read_text(encoding="utf-8"))
    assert receipt["tip_sha"] == tip
    assert receipt["evidence_kind"] == "merged-pr"
    assert not git(repo, "branch", "--list", "codex/impl-2002")


def test_unique_files_outside_the_merged_pr_are_refused(repo: Path) -> None:
    start(repo, "codex/impl-2002")
    commit_files(
        repo,
        "codex/impl-2002",
        {"alpha.txt": "branch\n", "only-on-branch.txt": "keep\n"},
        "extra file",
    )
    commit_files(repo, "main", {"alpha.txt": "landed\n"}, "land part (#4444)")
    publish(repo, "main", "codex/impl-2002")
    item = only(repo, "codex/impl-2002", apply=True, issues=closure(4444))
    assert item.classification == "report-only"
    assert "do not cover" in item.reason
    assert not ledger(repo).exists()
    assert git(repo, "ls-remote", "--heads", "origin", "codex/impl-2002")
    assert git(repo, "branch", "--list", "codex/impl-2002")


def test_open_pr_worktree_and_running_task_refuse_patch_id_evidence(repo: Path, tmp_path: Path) -> None:
    tip = same_change(repo, "codex/impl-1001")
    calls: list[int] = []

    def explode(_repo: Path, issue: int) -> tuple[sweep.IssueClosure | None, str | None]:
        calls.append(issue)
        raise AssertionError("evidence must not be consulted")

    open_pr = only(
        repo,
        "codex/impl-1001",
        apply=True,
        states={"codex/impl-1001": [PullRequestState(9, "OPEN", tip)]},
        issues=explode,
    )
    assert open_pr.classification == "skipped-open-PR"
    git(repo, "worktree", "add", str(tmp_path / "other"), "codex/impl-1001")
    checked_out = only(repo, "codex/impl-1001", apply=True, issues=explode)
    assert checked_out.classification == "skipped-worktree"
    git(repo, "worktree", "remove", str(tmp_path / "other"))
    directory = repo / "batch_state" / "tasks"
    directory.mkdir(parents=True)
    (directory / "live.json").write_text(json.dumps({"status": "running", "worktree_branch": "codex/impl-1001"}))
    running = only(repo, "codex/impl-1001", apply=True, issues=explode)
    assert running.classification == "skipped-live-task"
    assert calls == []
    assert not ledger(repo).exists()
    assert git(repo, "ls-remote", "--heads", "origin", "codex/impl-1001")


def test_finished_task_does_not_block_patch_id_deletion(repo: Path) -> None:
    same_change(repo, "codex/impl-1001")
    directory = repo / "batch_state" / "tasks"
    directory.mkdir(parents=True)
    (directory / "done.json").write_text(json.dumps({"status": "done", "worktree_branch": "codex/impl-1001"}))
    item = only(repo, "codex/impl-1001", apply=True)
    assert item.classification == "delete-evidence"
    assert not git(repo, "branch", "--list", "codex/impl-1001")


def test_unreadable_evidence_is_one_refusal_and_keeps_the_branch(repo: Path) -> None:
    start(repo, "codex/impl-2002")
    commit_files(repo, "codex/impl-2002", {"alpha.txt": "different\n"}, "not on main")
    publish(repo, "codex/impl-2002")
    calls: list[int] = []

    def unreadable(_repo: Path, issue: int) -> tuple[sweep.IssueClosure | None, str | None]:
        calls.append(issue)
        return None, "HTTP 503"

    item = only(repo, "codex/impl-2002", apply=True, issues=unreadable)
    assert item.classification == "report-only"
    assert "unreadable" in item.reason
    assert calls == [2002]
    assert not ledger(repo).exists()
    assert git(repo, "ls-remote", "--heads", "origin", "codex/impl-2002")


def test_rescue_branch_ignores_file_coverage_and_accepts_patch_id(repo: Path) -> None:
    start(repo, "rescue/grok/impl-3003")
    commit_files(repo, "rescue/grok/impl-3003", {"alpha.txt": "branch\n"}, "rescue rewrite")
    commit_files(repo, "main", {"alpha.txt": "landed\n"}, "land rescue work (#3003) (#5555)")
    publish(repo, "main", "rescue/grok/impl-3003")
    calls: list[int] = []

    def lookup(_repo: Path, issue: int) -> tuple[sweep.IssueClosure | None, str | None]:
        calls.append(issue)
        return sweep.IssueClosure(5555), None

    refused = only(repo, "rescue/grok/impl-3003", apply=True, issues=lookup)
    assert refused.classification == "report-only"
    assert "rescue" in refused.reason
    assert calls == []
    assert git(repo, "ls-remote", "--heads", "origin", "rescue/grok/impl-3003")

    git(repo, "push", "origin", "--delete", "rescue/grok/impl-3003")
    git(repo, "branch", "-D", "rescue/grok/impl-3003")
    tip = same_change(repo, "rescue/grok/impl-3004")
    accepted = only(repo, "rescue/grok/impl-3004", apply=True, issues=lookup)
    assert accepted.classification == "delete-evidence"
    assert accepted.evidence_kind == "patch-id"
    assert calls == []
    assert json.loads(ledger(repo).read_text(encoding="utf-8"))["tip_sha"] == tip


def test_issue_number_comes_from_the_commit_when_the_name_has_none(repo: Path) -> None:
    start(repo, "codex/notes")
    commit_files(repo, "codex/notes", {"alpha.txt": "branch\n"}, "Fixes #2002")
    commit_files(repo, "main", {"alpha.txt": "landed\n"}, "land notes (#4444)")
    publish(repo, "main", "codex/notes")
    seen: list[int] = []

    def lookup(_repo: Path, issue: int) -> tuple[sweep.IssueClosure | None, str | None]:
        seen.append(issue)
        return sweep.IssueClosure(4444), None

    item = only(repo, "codex/notes", apply=True, issues=lookup)
    assert seen == [2002]
    assert item.classification == "delete-evidence"
    assert item.evidence_kind == "merged-pr"


def test_missing_merge_commit_and_receipt_failure_keep_the_branch(repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    start(repo, "codex/impl-2002")
    commit_files(repo, "codex/impl-2002", {"alpha.txt": "branch\n"}, "not landed")
    publish(repo, "codex/impl-2002")
    missing = only(repo, "codex/impl-2002", apply=True, issues=closure(4444))
    assert missing.classification == "report-only"
    assert "not on origin/main" in missing.reason
    assert git(repo, "branch", "--list", "codex/impl-2002")

    def fail_receipt(_repo: Path, _branch: sweep.Branch, _verdict: sweep.Decision) -> None:
        raise OSError("disk full")

    monkeypatch.setattr(sweep, "_append_receipt", fail_receipt)
    blocked = only(repo, "codex/impl-2002", apply=True, issues=closure(None))
    # The same unique commit is not patch-id equivalent, and the injected closure has no PR,
    # so this call refuses before a receipt. Use a patch-id branch for the receipt failure.
    assert blocked.classification == "report-only"
    tip = same_change(repo, "codex/impl-1001")
    refused = only(repo, "codex/impl-1001", apply=True)
    assert refused.classification == "report-only"
    assert "receipt" in refused.reason
    assert git(repo, "rev-parse", "refs/heads/codex/impl-1001") == tip
    assert git(repo, "ls-remote", "--heads", "origin", "codex/impl-1001")


def test_apply_rereads_the_cached_issue_once(repo: Path) -> None:
    start(repo, "codex/impl-2002")
    commit_files(repo, "codex/impl-2002", {"alpha.txt": "branch\n"}, "rewrite")
    commit_files(repo, "main", {"alpha.txt": "landed\n"}, "land it (#4444)")
    publish(repo, "main", "codex/impl-2002")
    calls: list[int] = []

    def lookup(_repo: Path, issue: int) -> tuple[sweep.IssueClosure | None, str | None]:
        calls.append(issue)
        return sweep.IssueClosure(4444), None

    item = only(repo, "codex/impl-2002", apply=True, issues=lookup)
    assert item.classification == "delete-evidence"
    assert calls == [2002]


def test_ancestor_and_merged_head_rules_stay_in_place(repo: Path) -> None:
    ancestor_sha = git(repo, "rev-parse", "main")
    git(repo, "branch", "agy/old", "main")
    publish(repo, "agy/old")
    ancestor = only(repo, "agy/old", apply=True)
    assert ancestor.classification == "delete-ancestor"
    assert ancestor.evidence_kind == "ancestor"
    assert json.loads(ledger(repo).read_text(encoding="utf-8"))["tip_sha"] == ancestor_sha

    parent = git(repo, "rev-parse", "main")
    tree = git(repo, "rev-parse", "main^{tree}")
    unique = git(repo, "commit-tree", tree, "-p", parent, "-m", "codex/finished")
    git(repo, "update-ref", "refs/heads/codex/finished", unique)
    publish(repo, "codex/finished")
    merged = only(
        repo,
        "codex/finished",
        apply=True,
        states={"codex/finished": [PullRequestState(4, "MERGED", unique)]},
    )
    assert merged.classification == "delete-merged"
    assert merged.evidence_kind == "merged-head"
    lines = ledger(repo).read_text(encoding="utf-8").splitlines()
    assert [json.loads(line)["tip_sha"] for line in lines] == [ancestor_sha, unique]


def test_timeline_parser_selects_one_closing_pull_request() -> None:
    closed = {"event": "closed", "created_at": "2026-10-01T00:00:10Z"}
    keyword = timeline_pr(44, "2026-10-01T00:00:08Z", "other", "Closes #1200.")
    titled = timeline_pr(55, "2026-10-01T00:00:09Z", "land the work (#1200)")
    later_keyword = timeline_pr(66, "2026-10-01T00:00:09Z", "also", "Fixes #1200")
    closure, error = sweep._parse_issue_timeline(http([keyword, titled, closed]), 1200)
    assert error is None
    assert closure is not None and closure.closing_pr == 44
    closure, error = sweep._parse_issue_timeline(http([keyword, later_keyword, closed]), 1200)
    assert error is None
    assert closure is not None and closure.closing_pr == 66
    part_of = timeline_pr(77, "2026-10-01T00:00:08Z", "notes", "Part of #1200")
    closure, error = sweep._parse_issue_timeline(http([part_of, titled, closed]), 1200)
    assert error is None
    assert closure is not None and closure.closing_pr == 55
    reopened = [
        keyword,
        {"event": "closed", "created_at": "2026-10-01T00:00:10Z"},
        {"event": "reopened", "created_at": "2026-10-02T00:00:00Z"},
        {"event": "closed", "created_at": "2026-10-03T00:00:00Z"},
    ]
    closure, error = sweep._parse_issue_timeline(http(reopened), 1200)
    assert error is None
    assert closure is not None and closure.closing_pr is None
    same_time = [
        timeline_pr(1, "2026-10-01T00:00:08Z", "a", "Closes #1200"),
        timeline_pr(2, "2026-10-01T00:00:08Z", "b", "Fixes #1200"),
        closed,
    ]
    closure, error = sweep._parse_issue_timeline(http(same_time), 1200)
    assert error is None
    assert closure is not None and closure.closing_pr is None


def test_timeline_parser_refuses_unreadable_payloads() -> None:
    body = [{"event": "closed", "created_at": "2026-10-01T00:00:00Z"}]
    for raw in (
        http(body, status="503 Service Unavailable"),
        http(body, link='<https://example.test?page=2>; rel="next"'),
        "HTTP/2.0 200 OK\r\n\r\nnot-json",
        "not an http response",
    ):
        closure, error = sweep._parse_issue_timeline(raw, 1200)
        assert closure is None
        assert error is not None


def test_issue_read_disables_forced_color(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CLICOLOR_FORCE", "1")
    monkeypatch.setenv("FORCE_COLOR", "1")
    seen: dict[str, dict[str, str]] = {}

    def fake_run(args: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        env = kwargs.get("env")
        assert isinstance(env, dict)
        seen["env"] = env
        return subprocess.CompletedProcess(args, 0, stdout="", stderr="")

    monkeypatch.setattr(sweep.subprocess, "run", fake_run)
    sweep._run_gh(Path("."), ["gh", "api", "repos/example/example"])
    assert seen["env"]["NO_COLOR"] == "1"
    assert seen["env"]["GH_FORCE_TTY"] == "0"
    assert "CLICOLOR_FORCE" not in seen["env"]
    assert "FORCE_COLOR" not in seen["env"]


def test_issue_read_is_one_rest_get_without_pagination(repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    git(repo, "remote", "set-url", "origin", "https://github.com/example/example.git")
    seen: list[list[str]] = []

    def fake(_repo: Path, args: list[str]) -> subprocess.CompletedProcess[str]:
        seen.append(args)
        stdout = http([{"event": "closed", "created_at": "2026-10-01T00:00:00Z"}])
        return subprocess.CompletedProcess(args, 0, stdout=stdout, stderr="")

    monkeypatch.setattr(sweep, "_run_gh", fake)
    closure, error = sweep._query_issue_closure(repo, 1200)
    assert error is None
    assert closure is not None and closure.closing_pr is None
    assert seen == [
        [
            "gh",
            "api",
            "--include",
            "-X",
            "GET",
            "repos/example/example/issues/1200/timeline?per_page=100",
        ]
    ]
    assert "--paginate" not in seen[0]
