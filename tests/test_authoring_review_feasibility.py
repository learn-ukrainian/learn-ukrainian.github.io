"""#9739: a writer is admitted only while a qualified reviewer outside every author family remains.

Facts come from miniature Git histories and task-provenance records, never from a
replaced calculator. The selector (``reviewer_resolver``) and the recorder
(``record_cf_verdict.record``) are each run on the same repository; refusals are
driven through ``delegate.cmd_dispatch`` with tripwires on every side effect.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from contextlib import contextmanager
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import delegate
from scripts.orchestration import job_host_exec
from scripts.review import record_cf_verdict as recorder
from scripts.review.model_catalog import ModelCatalogError

REPOSITORY = "learn-ukrainian/learn-ukrainian.github.io"
CLAUDE_ADAPTER = "scripts/agent_runtime/adapters/claude.py"
SHARED_HOOK = "agents_extensions/shared/hooks/guard-reviewer-publish.py"
OPUS = "claude/claude-opus-5-5"
SOL = "codex/gpt-6.1-sol"
# Native and Cursor Grok review at every risk (#9769), so exhausting the reviewers takes an xAI author too.
GROK = "grok/grok-4.7"
GROK_ADAPTER = "scripts/agent_runtime/adapters/grok_build.py"


CANONICAL_URL = f"https://github.com/{REPOSITORY}.git"


def _run_git(*args: str, cwd: Path | None = None, env: dict | None = None, stdin: str | None = None) -> str:
    proc = subprocess.run(
        ["git", *args], cwd=cwd, env=env, input=stdin, capture_output=True, text=True, check=True, timeout=30
    )
    return proc.stdout.strip()


class MiniRepo:
    """A throwaway repository whose canonical GitHub remote is a local bare repository.

    ``origin`` carries the canonical GitHub URL, rewritten by ``insteadOf`` to
    ``<tmp>/canonical.git``, so dispatch observes and fetches it exactly as it
    would GitHub (#7522). The remote is only ever written by fetching into it:
    nothing is pushed.
    """

    def __init__(self, root: Path, remote: Path | None = None) -> None:
        self.root = root
        self.remote = remote

    def git(self, *args: str, check: bool = True) -> str:
        proc = subprocess.run(["git", *args], cwd=self.root, capture_output=True, text=True, check=check, timeout=30)
        return proc.stdout.strip()

    def sha(self, ref: str) -> str:
        return self.git("rev-parse", f"{ref}^{{commit}}")

    def commit(self, trailer: str | None, *, path: str = "docs/a.md", text: str | None = None, message: str = "work"):
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text if text is not None else f"{message} {trailer}\n", encoding="utf-8")
        self.git("add", "-A")
        body = f"{message}\n\nX-Agent: {trailer}\n" if trailer else f"{message}\n"
        self.git("commit", "-q", "-m", body)
        return self.sha("HEAD")

    def change(self, trailer: str, *args: str, message: str = "move") -> str:
        """Commit a ``git rm``/``git mv`` style change."""
        self.git(*args)
        self.git("commit", "-q", "-m", f"{message}\n\nX-Agent: {trailer}\n")
        return self.sha("HEAD")

    def publish(self, branch: str = "feature", *, to: str | None = None, remote: Path | None = None) -> str:
        """Serve local ``branch`` as ``to`` on the canonical remote and track it as ``origin/<to>``."""
        target = to or branch
        head = self.sha(branch)
        _run_git(
            "--git-dir",
            str(remote or self.remote),
            "fetch",
            "-q",
            str(self.root),
            f"+refs/heads/{branch}:refs/heads/{target}",
        )
        self.git("update-ref", f"refs/remotes/origin/{target}", head)
        return head

    def remote_sha(self, branch: str, *, remote: Path | None = None) -> str:
        return _run_git("--git-dir", str(remote or self.remote), "rev-parse", f"refs/heads/{branch}")

    def advance_remote(self, branch: str, trailer: str, *, path: str = "docs/a.md") -> str:
        """Another writer's commit on the canonical ``branch``, made in the remote itself with plumbing (no
        checkout, no push), so it is absent from this repository and its tracking refs."""
        bare = str(self.remote)
        env = {
            **os.environ,
            "GIT_INDEX_FILE": str(self.root.parent / "other-writer.index"),
            "GIT_AUTHOR_NAME": "Other",
            "GIT_AUTHOR_EMAIL": "other@example.invalid",
            "GIT_COMMITTER_NAME": "Other",
            "GIT_COMMITTER_EMAIL": "other@example.invalid",
        }
        parent = _run_git("--git-dir", bare, "rev-parse", f"refs/heads/{branch}")
        _run_git("--git-dir", bare, "read-tree", parent, env=env)
        blob = _run_git("--git-dir", bare, "hash-object", "-w", "--stdin", stdin=f"remote {trailer}\n")
        _run_git("--git-dir", bare, "update-index", "--add", "--cacheinfo", f"100644,{blob},{path}", env=env)
        tree = _run_git("--git-dir", bare, "write-tree", env=env)
        message = f"remote {branch}\n\nX-Agent: {trailer}\n"
        head = _run_git("--git-dir", bare, "commit-tree", tree, "-p", parent, "-m", message, env=env)
        _run_git("--git-dir", bare, "update-ref", f"refs/heads/{branch}", head, parent)
        return head

    def snapshot(self) -> tuple[str, str, str, str]:
        """Local branches, checkouts and files. Remote-tracking refs are excluded: admission may fetch to mirror
        the canonical remote before it decides (A7 M1)."""
        return (
            self.git("for-each-ref", "--format=%(refname) %(objectname)", "refs/heads", "refs/tags"),
            self.git("worktree", "list", "--porcelain"),
            self.git("rev-parse", "HEAD"),
            self.git("status", "--porcelain", "--untracked-files=all"),
        )


@pytest.fixture
def tasks(tmp_path, monkeypatch) -> Path:
    root = tmp_path / "tasks"
    root.mkdir()
    monkeypatch.setenv("LU_TASKS_DIR", str(root))
    monkeypatch.setenv("LU_SCRATCH_ROOT", str(tmp_path / "scratch"))
    return root


@pytest.fixture
def repo(tmp_path, monkeypatch, request) -> MiniRepo:
    """The miniature repository; ``indirect`` parametrization names its default branch."""
    return mini_repo(tmp_path, monkeypatch, default_branch=getattr(request, "param", "main"))


def bare_remote(path: Path, *, default_branch: str = "main") -> Path:
    _run_git("init", "-q", "--bare", str(path))
    _run_git("--git-dir", str(path), "symbolic-ref", "HEAD", f"refs/heads/{default_branch}")
    return path


def mini_repo(tmp_path: Path, monkeypatch, *, default_branch: str = "main") -> MiniRepo:
    """A repository at ``<tmp_path>/primary`` on branch ``feature``, forked from ``origin/<default_branch>``."""
    for key in list(os.environ):
        if key.startswith("GIT_"):
            monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", os.devnull)
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    root = tmp_path / "primary"
    root.mkdir()
    mini = MiniRepo(root, bare_remote(tmp_path / "canonical.git", default_branch=default_branch))
    # A non-protected local branch name: agent Git shims refuse branch creation on main.
    mini.git("init", "-q", "-b", "trunk")
    mini.git("config", "user.name", "Fixture")
    mini.git("config", "user.email", "fixture@example.invalid")
    mini.git("config", "core.hooksPath", os.devnull)
    mini.git("remote", "add", "origin", CANONICAL_URL)
    mini.git("config", f"url.{mini.remote}.insteadOf", CANONICAL_URL)
    for path in ("docs/a.md", "src/app.py", CLAUDE_ADAPTER, SHARED_HOOK):
        (root / path).parent.mkdir(parents=True, exist_ok=True)
        (root / path).write_text(f"base {path}\n", encoding="utf-8")
    (root / ".gitignore").write_text(".worktrees/\n", encoding="utf-8")
    mini.git("add", "-A")
    mini.git("commit", "-q", "-m", f"base\n\nX-Agent: {OPUS}\n")
    mini.publish("trunk", to=default_branch)
    mini.git("checkout", "-q", "-b", "feature")
    return mini


def pin_review_target(monkeypatch, sha: str, *, default_branch: str = "main") -> None:
    """For dispatch tests about something else: the canonical default branch is ``sha``, no PR is open and the
    mirror fetch is a no-op. This file observes and fetches a real (local) remote instead (#9739 A7)."""
    monkeypatch.setattr(delegate, "_authoring_default_branch", lambda _remote: (default_branch, sha))
    monkeypatch.setattr(delegate, "_authoring_open_pr_bases", lambda _repository, _head_branch: [])
    monkeypatch.setattr(delegate, "_fetch_base", lambda _base: True)


def task_record(tasks: Path, task_id: str, *, archived: bool = False, **fields) -> None:
    directory = tasks / "archive" if archived else tasks
    path = directory / f"{task_id}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"repository": REPOSITORY, **fields}), encoding="utf-8")


def facts(repo: MiniRepo, tasks: Path, *, writer: str | None = None, owned=("docs/a.md",), seats=(), families=()):
    agent, _, model = (writer or "").partition("/")
    return recorder.collect_branch_review_facts(
        repository=REPOSITORY,
        repo_root=repo.root,
        base_tip_sha=repo.sha("origin/main"),
        head_sha=repo.sha("feature"),
        task_root=tasks,
        incoming_agent=agent or None,
        incoming_model=model or None,
        owned_paths=owned,
        subject_seats=seats,
        subject_families=families,
    )


def selected(fact, risk: str) -> str | None:
    resolution = recorder.structural_review_route(fact, risk=risk)
    return resolution.selected.name if resolution.selected else None


# --- the recorder, end to end on the same repository ---------------------------------------------


@pytest.fixture(autouse=True)
def recorder_matcher(synthetic_opsec):
    from tests.opsec_fixtures import synthetic_rules

    rules = synthetic_rules(rule="3-absolute-path", level=3, pattern=r"(?<![<\w:])/[A-Za-z][^\s`'\"<>),;\]}|*]*")
    (synthetic_opsec / "rules.json").write_text(json.dumps(rules))


def github_listing(repo: MiniRepo, base: str, head: str) -> list[dict]:
    """GitHub's PR commit listing, derived from the repository itself."""
    return [
        {
            "sha": sha,
            "commit": {
                "message": repo.git("show", "--no-patch", "--format=%B", sha),
                "tree": {"sha": repo.git("show", "--no-patch", "--format=%T", sha)},
            },
            "parents": [{"sha": parent} for parent in repo.git("show", "--no-patch", "--format=%P", sha).split()],
        }
        for sha in repo.git("rev-list", "--reverse", f"{base}..{head}").splitlines()
    ]


def record_verdict(
    monkeypatch, tmp_path, repo: MiniRepo, *, agent: str, model: str, listing=None, comments=None, **review
):
    """Run ``record_cf_verdict.record`` for a finished review of ``feature``; return its receipt."""
    base, head = repo.sha("origin/main"), repo.sha("feature")
    review_root = tmp_path / "review-tasks"
    review_root.mkdir(exist_ok=True)
    fields = {
        "repository": REPOSITORY,
        "worktree_branch": "feature",
        "worktree_base_sha": head,
        "agent": agent,
        "model": model,
        "started_at": "2026-10-05T12:00:00.000001+00:00",
        "status": "done",
        **review,
    }
    (review_root / "review.json").write_text(json.dumps(fields), encoding="utf-8")
    (review_root / "review.result").write_text("Checked.\n\nVERDICT: APPROVE\n", encoding="utf-8")
    # Author provenance lives with the dispatch task records.
    for source in tmp_path.joinpath("tasks").rglob("*.json"):
        target = review_root / source.relative_to(tmp_path / "tasks")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
    comments = [] if comments is None else comments

    def fake_json(args, *, input_text=None):
        from scripts.publish.github import Request

        if isinstance(args, Request):
            if args.verb == "issue-comment-json":
                item = {
                    "id": 1,
                    "body": args.fields["body"],
                    "user": {"login": "fleet"},
                    "author_association": "MEMBER",
                    "created_at": "t",
                    "updated_at": "t",
                }
                comments.append(item)
                return item
            if args.verb == "read-comment":
                return comments[-1]
            raise AssertionError(args.verb)
        if args[-2:] == ["--json", "baseRefOid,headRefOid"]:
            return {"baseRefOid": base, "headRefOid": head}
        if args[:3] == ["gh", "pr", "view"]:
            return {"number": 42, "headRefOid": head, "headRefName": "feature", "state": "OPEN"}
        raise AssertionError(args)

    monkeypatch.setattr(recorder, "_run_json", fake_json)
    monkeypatch.setattr(recorder, "_pages", lambda request: listing or github_listing(repo, base, head))
    monkeypatch.setattr(recorder, "_repo_root", lambda: repo.root)
    monkeypatch.setattr(recorder.GitHubAdapter, "identity", lambda self: "fleet")
    monkeypatch.setattr(recorder.GitHubAdapter, "comments", lambda self, repository, number: list(comments))
    monkeypatch.setattr(recorder, "post_commit_status", lambda **kwargs: None)
    monkeypatch.chdir(repo.root)
    return recorder.record("review", pr_number=42, task_root=review_root, lock_root=tmp_path / "locks")


GROK_RECEIPT = {
    "resolved_model": "Grok 4.7 256K High",
    "resolved_model_known": True,
    "resolved_model_source": "cursor-stream-json",
}


@pytest.mark.parametrize("trailer", ["cursor/feature", "cursor/auto", "cursor/unattested", "codex/unrecognized"])
@pytest.mark.parametrize(
    "agent,model,review",
    [("claude", "claude-opus-5-5", {}), ("codex", "gpt-6.1-sol", {}), ("cursor", "grok-4.7-high", GROK_RECEIPT)],
)
def test_auto_and_unknown_authors_preserve_review_independence(repo, tasks, monkeypatch, tmp_path, trailer, agent, model, review):
    task_record(tasks, "unattested", agent="cursor", resolved_model_known=False, resolved_model="unknown")
    task_record(tasks, "unrecognized", agent="codex", model="not-a-catalog-model")
    head = repo.commit(trailer)
    repo.publish()
    expected = "cursor" if trailer == "cursor/auto" else "unknown"
    assert facts(repo, tasks).existing_families == {expected}
    if expected == "cursor" and agent == "cursor":
        with pytest.raises(recorder.RecordError, match="Cursor-authored work"):
            record_verdict(monkeypatch, tmp_path, repo, agent=agent, model=model, **review)
        return
    receipt = record_verdict(monkeypatch, tmp_path, repo, agent=agent, model=model, **review)
    assert receipt["head"] == head and receipt["verdict"] == "APPROVED"
    assert receipt["comment"] == "posted" and receipt["status"] == "posted"


def test_unknown_author_cannot_record_an_unknown_reviewer_verdict(repo, tasks, monkeypatch, tmp_path):
    repo.commit("cursor/feature")
    repo.publish()
    posted = []
    with pytest.raises(recorder.RecordError, match="reviewer family unknown"):
        record_verdict(monkeypatch, tmp_path, repo, agent="codex", model="unknown", comments=posted)
    assert posted == []


# --- 1. single-family eligible -------------------------------------------------------------------


def test_single_family_branch_agrees_across_selector_and_recorder(repo, tasks, monkeypatch, tmp_path):
    task_record(tasks, "hot-task", agent="claude", model="claude-opus-5-5")
    task_record(tasks, "old-task", archived=True, agent="claude", model="claude-opus-5-5")
    repo.commit(OPUS, message="one")
    repo.commit("claude/hot-task", message="two")
    repo.commit("claude/old-task", message="three")
    repo.publish()

    fact = facts(repo, tasks, writer=OPUS)

    assert fact.existing_families == {"anthropic"} and len(fact.commits) == 3
    assert {commit.source for commit in fact.commits} == {"trailer-model", "task-record", "task-record-archived"}
    assert selected(fact, "critical") == "openai_frontier"
    # The recorder, run independently on the same repository, accepts that reviewer ...
    receipt = record_verdict(monkeypatch, tmp_path, repo, agent="codex", model="gpt-6.1-sol", review_risk="critical")
    assert receipt["verdict"] == "APPROVED" and receipt["head"] == repo.sha("feature")
    # ... and refuses an author-family one.
    with pytest.raises(recorder.RecordError, match="equals an author family"):
        record_verdict(monkeypatch, tmp_path, repo, agent="claude", model="claude-opus-5-5")


def test_unchanged_head_approval_stays_reusable_when_quota_changes(repo, tasks, monkeypatch, tmp_path):
    repo.commit(OPUS)
    repo.publish()
    posted: list[dict] = []
    first = record_verdict(monkeypatch, tmp_path, repo, agent="codex", model="gpt-6.1-sol", comments=posted)
    # The recorder never consults routing health, so a later quota swing cannot invalidate it.
    second = record_verdict(monkeypatch, tmp_path, repo, agent="codex", model="gpt-6.1-sol", comments=posted)
    assert (first["comment"], second["comment"]) == ("posted", "existing")


def test_fresh_branch_with_one_family_has_a_reviewer(repo, tasks):
    fresh = facts(repo, tasks, writer=SOL, owned=(CLAUDE_ADAPTER.replace("claude", "codex"),))
    assert fresh.commits == () and fresh.author_families == {"openai"}
    assert selected(fresh, "critical") == "claude-opus-5-5"


# --- 2. mixed-family exhausted -------------------------------------------------------------------


@pytest.mark.parametrize("order", [(OPUS, SOL), (SOL, OPUS)])
@pytest.mark.parametrize("writer", [OPUS, SOL])
def test_mixed_family_critical_branch_has_no_reviewer_whatever_the_order_or_writer(repo, tasks, order, writer):
    repo.commit(GROK, message="xai commit")
    for index, trailer in enumerate(order):
        repo.commit(trailer, message=f"commit {index}")
    fact = facts(repo, tasks, writer=writer)

    assert fact.existing_families == {"anthropic", "openai", "xai"}
    assert selected(fact, "critical") is None


def test_mixed_family_at_lower_risk_keeps_a_third_family(repo, tasks, monkeypatch, tmp_path):
    repo.commit(OPUS)
    repo.commit(SOL)
    repo.publish()
    fact = facts(repo, tasks, writer=OPUS)

    assert selected(fact, "medium") == "grok-4.7"
    receipt = record_verdict(
        monkeypatch, tmp_path, repo, agent="cursor", model="auto", review_risk="medium", **GROK_RECEIPT
    )
    assert receipt["verdict"] == "APPROVED"
    # Every author stays attributed: neither frontier family may approve.
    for agent, model in (("codex", "gpt-6.1-sol"), ("claude", "claude-opus-5-5")):
        with pytest.raises(recorder.RecordError, match="equals an author family"):
            record_verdict(monkeypatch, tmp_path, repo, agent=agent, model=model, review_risk="medium")


def test_recorder_holds_a_below_critical_reviewer_to_the_recorded_risk(repo, tasks, monkeypatch, tmp_path):
    repo.commit(SOL)
    repo.publish()
    # Sonnet reviews this branch at medium but not at the recorded critical risk.
    assert (
        record_verdict(monkeypatch, tmp_path, repo, agent="claude", model="claude-sonnet-5-5", review_risk="medium")[
            "verdict"
        ]
        == "APPROVED"
    )
    with pytest.raises(recorder.RecordError, match="not qualified"):
        record_verdict(monkeypatch, tmp_path, repo, agent="claude", model="claude-sonnet-5-5", review_risk="critical")


# --- 3. incoming-family exclusion ----------------------------------------------------------------


def test_incoming_family_joins_the_authors(repo, tasks):
    repo.commit(OPUS)
    repo.commit(GROK)
    assert selected(facts(repo, tasks, writer=SOL), "critical") is None
    assert selected(facts(repo, tasks, writer="claude/claude-sonnet-5-5"), "critical") == "openai_frontier"


def test_cursor_auto_incoming_writer_adds_only_cursor_family(repo, tasks):
    repo.commit(OPUS)
    repo.commit(SOL)
    auto = facts(repo, tasks, writer="cursor/auto")

    assert auto.incoming_family == "cursor"
    assert auto.excluded_families == {"anthropic", "openai", "cursor"}
    # Native Grok remains eligible when Cursor Auto joins the authors.
    assert selected(facts(repo, tasks, writer=OPUS), "medium") == "grok-4.7"
    assert selected(auto, "medium") == "grok-4.7"


@pytest.mark.parametrize(
    "record,attributed",
    [
        ({"resolved_model_known": True, "resolved_model": "claude-opus-5-5-high"}, True),
        ({"resolved_model_known": False, "resolved_model": "unknown"}, False),
    ],
)
def test_committed_cursor_authorship_is_unknown_without_runtime_attestation(repo, tasks, record, attributed):
    task_record(tasks, "run", agent="cursor", model="grok-4.7-high", **record)
    repo.commit("cursor/run")
    if attributed:
        assert facts(repo, tasks).existing_families == {"anthropic"}
    else:
        assert facts(repo, tasks).existing_families == {"unknown"}


# --- 4. protected-scope qualification ------------------------------------------------------------


def test_claude_adapter_raises_risk_and_excludes_every_claude_reviewer(repo, tasks):
    repo.commit(GROK)
    repo.commit(SOL, path=CLAUDE_ADAPTER)
    fact = facts(repo, tasks, writer=SOL, owned=(CLAUDE_ADAPTER,))
    resolution = recorder.structural_review_route(fact, risk="low")

    assert fact.subject_seats == {"claude"}
    assert resolution.resolved_risk == "critical" and resolution.selected is None
    reasons = {entry.name: entry.reason for entry in resolution.trace}
    assert "subject exclusion" in reasons["claude-opus-5-5"]
    assert "subject exclusion" in reasons["claude-opus-5-5-cursor-fallback"]


@pytest.mark.parametrize("kind", ["earlier-commit", "rename-source", "deletion"])
def test_protected_changes_stay_in_scope_beyond_a_narrow_latest_packet(repo, tasks, kind):
    repo.commit(GROK, path="src/app.py")
    if kind == "earlier-commit":
        repo.commit(SOL, path=CLAUDE_ADAPTER)
    elif kind == "rename-source":
        repo.change(SOL, "mv", CLAUDE_ADAPTER, "src/moved.py")
    else:
        repo.change(SOL, "rm", "-q", CLAUDE_ADAPTER)
    repo.commit(SOL, path="docs/a.md", message="narrow follow-up")
    fact = facts(repo, tasks, writer=SOL, owned=("docs/a.md",))

    assert CLAUDE_ADAPTER in fact.scope_paths and fact.subject_seats == {"claude"}
    assert selected(fact, "low") is None


def test_explicit_subjects_and_ambiguous_shared_hooks(repo, tasks):
    repo.commit(OPUS)
    assert selected(facts(repo, tasks, writer=OPUS, seats=("codex", "grok")), "critical") is None
    with pytest.raises(recorder.BranchFactsError, match="ambiguous subject-seat") as refused:
        facts(repo, tasks, writer=OPUS, owned=(SHARED_HOOK,))
    assert refused.value.code == recorder.FACTS_SCOPE_UNKNOWN
    named = facts(repo, tasks, writer=OPUS, owned=(SHARED_HOOK,), seats=("claude",))
    assert named.subject_seats == {"claude"}


def test_recorder_applies_protected_seats_to_the_actual_reviewer(repo, tasks, monkeypatch, tmp_path):
    repo.commit(OPUS, path="scripts/agent_runtime/adapters/codex.py")
    repo.publish()
    # Sol is outside the author family but governs this change's seat.
    with pytest.raises(recorder.RecordError, match="subject exclusion"):
        record_verdict(monkeypatch, tmp_path, repo, agent="codex", model="gpt-6.1-sol", review_risk="critical")


# --- 5a. commit-set agreement (A1) ---------------------------------------------------------------


def test_recorder_refuses_a_github_listing_that_differs_from_rev_list(repo, tasks, monkeypatch, tmp_path):
    repo.commit(OPUS, message="one")
    repo.commit(OPUS, message="two")
    repo.publish()
    listing = github_listing(repo, repo.sha("origin/main"), repo.sha("feature"))
    with pytest.raises(recorder.RecordError, match=r"differs from the local base\.\.head enumeration"):
        record_verdict(monkeypatch, tmp_path, repo, agent="codex", model="gpt-6.1-sol", listing=listing[1:])
    assert (
        record_verdict(monkeypatch, tmp_path, repo, agent="codex", model="gpt-6.1-sol", listing=listing)["verdict"]
        == "APPROVED"
    )


# --- 5. unknown attribution ----------------------------------------------------------------------


@pytest.mark.parametrize(
    "case,reason",
    [
        ("missing-trailer", "missing explicit X-Agent"),
        ("duplicate-trailer", "missing explicit X-Agent"),
        ("repository-mismatch", "conflicts with commit trailer"),
        ("unproven-merge", "missing explicit X-Agent"),
    ],
)
def test_invalid_attribution_is_never_green(repo, tasks, case, reason):
    repo.commit(OPUS)
    if case == "missing-trailer":
        repo.commit(None)
    elif case == "duplicate-trailer":
        repo.commit(f"{OPUS}\nX-Agent: {SOL}")
    elif case == "repository-mismatch":
        task_record(tasks, "elsewhere", agent="codex", model="gpt-6.1-sol", repository="other/repo")
        repo.commit("codex/elsewhere")
    else:
        repo.git("checkout", "-q", "-b", "side", "origin/main")
        repo.commit(SOL, path="src/app.py")
        repo.git("checkout", "-q", "feature")
        repo.git("merge", "-q", "--no-ff", "side", "-m", "merge a non-base branch")
    with pytest.raises(recorder.BranchFactsError, match=reason) as refused:
        facts(repo, tasks, writer=OPUS)
    assert refused.value.code == recorder.FACTS_AUTHORSHIP_UNKNOWN


def test_proven_clean_base_merge_authors_nothing(repo, tasks):
    repo.commit(OPUS)
    repo.git("checkout", "-q", "trunk")
    repo.commit(SOL, path="src/app.py", message="base moves")
    repo.git("update-ref", "refs/remotes/origin/main", "HEAD")
    repo.git("checkout", "-q", "feature")
    repo.git("merge", "-q", "--no-ff", "trunk", "-m", "update branch")
    fact = facts(repo, tasks, writer=OPUS)
    assert fact.existing_families == {"anthropic"}
    assert [commit.source for commit in fact.commits].count("clean-base-merge") == 1


def test_incomplete_enumeration_refuses_instead_of_truncating(repo, tasks):
    repo.commit(OPUS)
    with pytest.raises(recorder.BranchFactsError, match="timed out") as refused:
        recorder.collect_branch_review_facts(
            repository=REPOSITORY,
            repo_root=repo.root,
            base_tip_sha=repo.sha("origin/main"),
            head_sha=repo.sha("feature"),
            task_root=tasks,
            timeout_s=0,
        )
    assert refused.value.code == recorder.FACTS_TARGET_UNKNOWN


def test_head_missing_locally_refuses(repo, tasks):
    with pytest.raises(recorder.BranchFactsError, match="not available locally") as refused:
        recorder.collect_branch_review_facts(
            repository=REPOSITORY,
            repo_root=repo.root,
            base_tip_sha=repo.sha("origin/main"),
            head_sha="f" * 40,
            task_root=tasks,
        )
    assert refused.value.code == recorder.FACTS_TARGET_UNKNOWN


# --- the dispatch boundary -----------------------------------------------------------------------


class _Admitted:
    exempt = True
    thresholds = None


def pr_row(number: int, base: str, base_sha: str, *, head: str = "feature", fork: bool = False, state: str = "OPEN"):
    """A PR as ``gh pr list``/``gh pr view --json`` describes it."""
    return {
        "number": number,
        "state": state,
        "headRefName": head,
        "isCrossRepository": fork,
        "baseRefName": base,
        "baseRefOid": base_sha,
    }


class FakeGitHub:
    """The ``gh`` reads admission makes, answered from ``prs``; any other ``gh`` command fails the test.

    ``gh pr list --head`` matches the branch name only, so fork PRs of the same
    name are listed too, as GitHub lists them.
    """

    def __init__(self) -> None:
        self.prs: list[dict] = []
        self.failure: str | None = None  # "timeout" | "quota" | "unavailable"
        self.calls: list[list[str]] = []

    def run(self, command: list[str]) -> subprocess.CompletedProcess:
        self.calls.append(command)
        if self.failure == "timeout":
            raise subprocess.TimeoutExpired(command, 1)
        if self.failure == "quota":
            return subprocess.CompletedProcess(command, 1, "", "GraphQL: API rate limit exceeded for user ID 1.")
        if self.failure == "unavailable":
            return subprocess.CompletedProcess(command, 1, "", "error connecting to api.github.com")
        assert command[command.index("--repo") + 1] == REPOSITORY, command
        if command[:3] == ["gh", "pr", "list"]:
            assert command[command.index("--state") + 1] == "open", command
            head = command[command.index("--head") + 1]
            rows = [row for row in self.prs if row["headRefName"] == head and row["state"] == "OPEN"]
            return subprocess.CompletedProcess(command, 0, json.dumps(rows), "")
        if command[:3] == ["gh", "pr", "view"]:
            rows = [row for row in self.prs if row["number"] == int(command[3])]
            if not rows:
                return subprocess.CompletedProcess(command, 1, "", "no pull requests found")
            return subprocess.CompletedProcess(command, 0, json.dumps(rows[0]), "")
        raise AssertionError(f"unexpected gh command {command}")


@pytest.fixture
def github(monkeypatch) -> FakeGitHub:
    fake = FakeGitHub()
    real_run = subprocess.run

    def run(command, *args, **kwargs):
        if isinstance(command, list) and command and command[0] == "gh":
            return fake.run(command)
        return real_run(command, *args, **kwargs)

    monkeypatch.setattr(delegate.subprocess, "run", run)
    return fake


@pytest.fixture
def boundary(repo, tasks, monkeypatch, github):
    """``delegate.cmd_dispatch`` on the miniature repository, with a tripwire on every side effect.

    Fetching from the canonical remote is not one: admission may mirror remote
    state before it decides (A7 M1); the snapshot leaves remote-tracking refs out.
    """
    monkeypatch.setattr(delegate, "_REPO_ROOT", repo.root)
    monkeypatch.setattr(delegate, "_local_repo_root", repo.root)
    monkeypatch.chdir(repo.root)
    # Live host and lane state are outside this check; they must not decide these tests.
    monkeypatch.setattr(delegate, "_credit_period_refusal", lambda *_args: None)
    monkeypatch.setattr(delegate, "_check_capacity_hint", lambda *_args, **_kwargs: None)
    for name in ("_resolve_dirty_primary_checkout_error", "_resolve_primary_integrity_error"):
        monkeypatch.setattr(delegate, name, lambda **_kwargs: None)
    for name in (
        "_warn_node_modules_integrity",
        "_warn_venv_integrity",
        "_warn_worktree_cleanup_integrity",
        "_warn_if_monitor_api_unreachable",
    ):
        monkeypatch.setattr(delegate, name, lambda: None)
    calls: list[str] = []

    def tripwire(name):
        def fire(*_args, **_kwargs):
            calls.append(name)
            raise AssertionError(f"{name} ran for a refused dispatch")

        return fire

    for target, name, label in (
        (delegate.dispatch_isolation, "spawn_detached_worker", "provider launch"),
        (delegate, "_adapter_model_rejection", "model probe"),
        (job_host_exec, "forward_dispatch", "forwarding"),
        (job_host_exec, "decide_dispatch_placement", "placement"),
        (delegate, "_archive_task_artifacts", "archival"),
        (delegate, "_sweep_runtime_tmp_orphans", "runtime cleanup"),
        (delegate, "_resolve_worktree_base_sha", "rebase"),
        (delegate, "_validate_existing_worktree", "rebase"),
        (delegate, "_ensure_worktree", "worktree creation"),
    ):
        monkeypatch.setattr(target, name, tripwire(label))

    def dispatch(*extra: str, writer: str = OPUS, mode: str = "workspace-write", task_id: str = "writer-1"):
        agent, _, model = writer.partition("/")
        argv = [
            "dispatch",
            "--agent",
            agent,
            "--model",
            model,
            "--task-id",
            task_id,
            "--initiator",
            "claude",
            "--mode",
            mode,
            "--prompt",
            "Implement the change.",
            *extra,
        ]
        before = repo.snapshot()
        rc = delegate.cmd_dispatch(delegate.build_parser().parse_args(argv))
        return rc, before

    dispatch.calls = calls
    return dispatch


def assert_refused(boundary, capsys, repo, tasks, result, code, *, reused: bool = False):
    """A typed refusal with no side effect; ``reused`` keeps a checkout the test made itself (snapshotted)."""
    rc, before = result
    err = capsys.readouterr().err
    assert rc == 2, err
    assert f"❌ {code}:" in err and "provider_calls=0" in err
    receipt = json.loads(err.strip().splitlines()[-1])["authoring_review_admission"]
    assert receipt["refusal"] == code and receipt["reviewer_availability"] == "unknown"
    assert boundary.calls == []
    assert repo.snapshot() == before
    assert list(tasks.rglob("*")) == []
    assert reused or not (repo.root / ".worktrees").exists()
    return receipt


@pytest.mark.parametrize(
    "override",
    [(), ("--force-agent",), ("--force-admission", "hotfix"), ("--allow-dor-warn", "accepted warning")],
)
def test_mixed_branch_refuses_a_writer_and_no_flag_overrides_it(boundary, capsys, repo, tasks, override):
    repo.commit(OPUS)
    repo.commit(SOL)
    repo.commit(GROK)
    repo.publish()
    receipt = assert_refused(
        boundary,
        capsys,
        repo,
        tasks,
        boundary("--branch", "feature", "--owned-path", "docs/a.md", *override),
        delegate.AUTHORING_REVIEW_NO_ROUTE,
    )
    assert receipt["existing_families"] == ["anthropic", "openai", "xai"] and receipt["risk"] == "critical"


@pytest.mark.parametrize(
    "target",
    [("--branch", "feature", "--base", "feature"), ("--worktree", "--base", "feature")],
    ids=["attach-with-base-equal-to-branch", "new-branch-started-from-a-mixed-branch"],
)
def test_caller_base_never_erases_existing_authors(boundary, capsys, repo, tasks, target):
    """Held-out probe of the review of record: --base equal to the branch used to enumerate no commits, admitting
    an OpenAI reviewer the recorder (which reads the PR base) then rejects. Authors come from the review base."""
    repo.commit(OPUS)
    repo.commit(SOL)
    repo.commit(GROK)
    repo.publish()
    receipt = assert_refused(
        boundary,
        capsys,
        repo,
        tasks,
        boundary(*target, "--owned-path", CLAUDE_ADAPTER),
        delegate.AUTHORING_REVIEW_NO_ROUTE,
    )
    assert receipt["existing_families"] == ["anthropic", "openai", "xai"]
    assert receipt["review_base"] == {
        "repository": REPOSITORY,
        "branch": "main",
        "pr": None,
        "source": "default-branch",
    }
    assert receipt["review_base_sha"] == receipt["base_tip_sha"] == repo.sha("origin/main")


BASE_SHA = "b" * 40
DEFAULT_TIP = ("main", "a" * 40)


def review_base(*, pr: int | None = None, head: str = "feature"):
    return delegate._authoring_review_base(REPOSITORY, pr=pr, head_branch=head, default_branch=lambda: DEFAULT_TIP)


def test_review_base_is_the_open_pr_base_or_the_actual_default_branch(github):
    """A7 §2: zero open PRs of the head branch, one, or the PR named by --pr; the caller's --base never enters."""
    assert review_base() == delegate._ReviewBase("a" * 40, "main", None, "default-branch")
    github.prs = [pr_row(7, "release", BASE_SHA)]
    assert review_base() == delegate._ReviewBase(BASE_SHA, "release", 7, "open-pr")
    assert review_base(pr=7) == delegate._ReviewBase(BASE_SHA, "release", 7, "pr")
    assert [command[:3] for command in github.calls] == [["gh", "pr", "list"]] * 2 + [["gh", "pr", "view"]]


def test_a_same_named_fork_pr_is_not_this_repositorys_pr(github):
    """M6: a fork's branch named like ours is another repository's PR; it neither binds nor blocks the dispatch."""
    github.prs = [pr_row(9, "main", "c" * 40, fork=True)]
    assert review_base().source == "default-branch"
    github.prs.append(pr_row(7, "release", BASE_SHA))
    assert review_base() == delegate._ReviewBase(BASE_SHA, "release", 7, "open-pr")


@pytest.mark.parametrize(
    "case,reason",
    [
        ("two-open-prs", "2 open PRs are headed by feature, so the review base is ambiguous"),
        ("limit-saturated", "the open-PR lookup reached its limit, so it is incomplete"),
        ("timeout", "the open-PR lookup timed out"),
        ("quota", "the open-PR lookup hit the GitHub API quota"),
        ("unavailable", "the open-PR lookup is unavailable"),
        ("malformed-row", "the open-PR lookup returned a malformed answer"),
        ("malformed-base", "the open-PR lookup returned a malformed answer"),
    ],
)
def test_an_open_pr_lookup_that_does_not_establish_the_base_is_unknown(github, case, reason):
    """M3: incomplete, ambiguous, failed or malformed lookups refuse, with a reason that echoes nothing from GitHub."""
    if case == "two-open-prs":
        github.prs = [pr_row(7, "release", BASE_SHA), pr_row(8, "main", "a" * 40)]
    elif case == "limit-saturated":
        # Even rows that would be dropped as forks count: a full page may hide this repository's PR.
        github.prs = [pr_row(n, "main", "c" * 40, fork=True) for n in range(delegate.AUTHORING_REVIEW_PR_LOOKUP_LIMIT)]
    elif case == "malformed-row":
        github.prs = [{"number": 7, "state": "OPEN", "headRefName": "feature", "baseRefName": "main"}]
    elif case == "malformed-base":
        github.prs = [pr_row(7, "main", "not-a-sha")]
    else:
        github.failure = case
    with pytest.raises(delegate._AuthoringObservationUnknown) as unknown:
        review_base()
    assert str(unknown.value) == reason


@pytest.mark.parametrize(
    "row,reason",
    [
        (pr_row(5, "main", BASE_SHA, head="other"), "PR #5 is headed by another branch than feature"),
        (pr_row(5, "main", BASE_SHA, fork=True), f"PR #5 is not an open PR headed in {REPOSITORY}"),
        (pr_row(5, "main", BASE_SHA, state="MERGED"), f"PR #5 is not an open PR headed in {REPOSITORY}"),
    ],
    ids=["different-head-branch", "fork-head", "not-open"],
)
def test_a_pr_that_does_not_head_the_target_branch_binds_nothing(github, row, reason):
    """M6: --pr is validated against this repository and the dispatch's head branch, never trusted by number."""
    github.prs = [row]
    with pytest.raises(delegate._AuthoringObservationUnknown) as unknown:
        review_base(pr=5)
    assert str(unknown.value) == reason


def test_undeterminable_review_base_is_unknown_authorship(boundary, github, capsys, repo, tasks):
    repo.commit(OPUS)
    repo.publish()
    github.failure = "unavailable"
    receipt = assert_refused(
        boundary,
        capsys,
        repo,
        tasks,
        boundary("--branch", "feature", "--owned-path", "docs/a.md"),
        delegate.AUTHORING_REVIEW_AUTHORSHIP_UNKNOWN,
    )
    assert receipt["head_branch"] == "feature" and "api.github.com" not in json.dumps(receipt)


def test_adding_openai_to_an_anthropic_and_xai_branch_refuses(boundary, capsys, repo, tasks):
    repo.commit(OPUS)
    repo.commit(GROK)
    repo.publish()
    receipt = assert_refused(
        boundary,
        capsys,
        repo,
        tasks,
        boundary("--branch", "feature", "--owned-path", "docs/a.md", writer=SOL),
        delegate.AUTHORING_REVIEW_NO_ROUTE,
    )
    assert receipt["incoming_family"] == "openai"


def test_budget_substitution_checks_the_substituted_writer(boundary, capsys, repo, tasks, monkeypatch):
    repo.commit(OPUS)
    repo.commit(GROK)
    repo.publish()
    monkeypatch.setattr(
        delegate,
        "_fetch_routing_budget",
        lambda: {
            "agents": {"claude": {"status": "near_cap"}, "codex": {"status": "cool"}},
            "diagnostics": {"records_loaded": 5},
        },
    )
    monkeypatch.setattr(delegate, "_load_reset_reserve", lambda *_args, **_kwargs: {})
    monkeypatch.setattr(delegate, "_resolve_substitution_model", lambda agent, model: ("gpt-6.1-sol", "mapped"))
    receipt = assert_refused(
        boundary,
        capsys,
        repo,
        tasks,
        boundary("--branch", "feature", "--owned-path", "docs/a.md", "--check-budget"),
        delegate.AUTHORING_REVIEW_NO_ROUTE,
    )
    assert (receipt["incoming_agent"], receipt["incoming_family"]) == ("codex", "openai")


def test_new_protected_branch_refuses_an_author_whose_reviewer_is_the_governed_seat(boundary, capsys, repo, tasks):
    receipt = assert_refused(
        boundary,
        capsys,
        repo,
        tasks,
        boundary("--worktree", "--owned-path", CLAUDE_ADAPTER, "--owned-path", GROK_ADAPTER, writer=SOL),
        delegate.AUTHORING_REVIEW_NO_ROUTE,
    )
    assert receipt["target"] == "new-branch" and receipt["subject_seats"] == ["claude", "grok"]


def test_cursor_auto_writer_refuses_where_only_the_cursor_seat_could_review(boundary, capsys, repo, tasks, monkeypatch):
    repo.commit(OPUS)
    repo.commit(SOL)
    repo.commit(GROK)
    repo.publish()
    pass_card = {"issues": [9739], "warnings": {}, "allow_warn_reason": None}
    monkeypatch.setattr(delegate, "_run_dor_preflight", lambda *_args, **_kwargs: (None, pass_card))
    receipt = assert_refused(
        boundary,
        capsys,
        repo,
        tasks,
        boundary(
            "--branch",
            "feature",
            "--owned-path",
            "docs/a.md",
            "--authoring-review-risk",
            "medium",
            "--research-role",
            "implementation",
            writer="cursor/auto",
        ),
        delegate.AUTHORING_REVIEW_NO_ROUTE,
    )
    assert receipt["incoming_family"] == "cursor"


@pytest.mark.parametrize(
    "extra,code",
    [
        (("--worktree",), delegate.AUTHORING_REVIEW_SCOPE_UNKNOWN),
        (("--worktree", "--owned-path", SHARED_HOOK), delegate.AUTHORING_REVIEW_SCOPE_UNKNOWN),
        (("--branch", "feature", "--owned-path", "docs/a.md"), delegate.AUTHORING_REVIEW_AUTHORSHIP_UNKNOWN),
        (("--branch", "absent", "--owned-path", "docs/a.md"), "DISPATCH_BRANCH_NOT_FOUND"),
    ],
)
def test_unknown_scope_or_authorship_refuses_at_the_boundary(boundary, capsys, repo, tasks, extra, code):
    repo.commit(None)  # an unattributed commit on feature
    repo.publish()
    result = boundary(*extra)
    if code == "DISPATCH_BRANCH_NOT_FOUND":
        # #9874: an absent branch is refused before authoring review admission.
        rc, before = result
        assert rc == 2
        assert capsys.readouterr().err == (
            "❌ DISPATCH_BRANCH_NOT_FOUND: --branch 'absent' does not exist on the canonical remote. "
            "--branch continues an existing remote branch; for a new branch omit --branch "
            "(default: <agent>/<task-id>), optionally with --base.\n"
        )
        assert boundary.calls == []
        assert repo.snapshot() == before
        assert list(tasks.rglob("*")) == []
        assert not (repo.root / ".worktrees").exists()
    else:
        assert_refused(boundary, capsys, repo, tasks, result, code)


def test_catalog_failure_keeps_its_own_reason(boundary, capsys, repo, tasks, monkeypatch):
    repo.commit(OPUS)
    repo.publish()

    def broken(*_args, **_kwargs):
        raise ModelCatalogError("catalog unreadable")

    monkeypatch.setattr(recorder, "structural_review_route", broken)
    assert_refused(
        boundary,
        capsys,
        repo,
        tasks,
        boundary("--branch", "feature", "--owned-path", "docs/a.md"),
        delegate.AUTHORING_REVIEW_CATALOG_UNKNOWN,
    )


# --- 5b / A3: dry-run evaluation and a head that moves after admission -----------------------------


@contextmanager
def _admitted_host(monkeypatch, on_admission=None):
    def admitted(*_args, **_kwargs):
        if on_admission is not None:
            on_admission()
        return _Admitted()

    monkeypatch.setattr(delegate, "_evaluate_dispatch_admission", admitted)
    monkeypatch.setattr(delegate, "_report_dispatch_admission", lambda *_args, **_kwargs: None)
    yield


def test_dry_run_evaluates_the_check_without_side_effects(boundary, capsys, repo, tasks, monkeypatch):
    repo.commit(OPUS)
    repo.publish()
    head = repo.sha("feature")
    worktree = repo.root / "wt"
    monkeypatch.setattr(delegate, "_resolve_worktree_base_sha", lambda **_kwargs: head)
    monkeypatch.setattr(delegate, "_ensure_worktree", lambda **_kwargs: (worktree, "feature", {"base_sha": head}))

    class _Telemetry:
        model, effort, cli_version = "claude-opus-5-5", None, None

    import agent_runtime.telemetry as telemetry

    monkeypatch.setattr(telemetry, "resolve_dispatch_start_telemetry", lambda **_kwargs: _Telemetry())
    with _admitted_host(monkeypatch):
        rc, before = boundary("--branch", "feature", "--owned-path", "docs/a.md", "--dry-run")
    assert rc == 0, capsys.readouterr().err
    record = json.loads((tasks / "writer-1.json").read_text(encoding="utf-8"))
    admission = record[delegate.AUTHORING_REVIEW_STATE_KEY]
    assert record["status"] == "dry_run"
    assert admission["reviewer"]["name"] == "openai_frontier" and admission["reviewer_availability"] == "unknown"
    assert admission["head_sha"] == head and admission["applicable"] is True
    assert repo.snapshot() == before and not worktree.exists()
    assert boundary.calls == []


@pytest.mark.parametrize("trailer", ["cursor/feature", "cursor/auto", "cursor/unattested"])
def test_branch_fix_writer_is_admitted_with_unknown_committed_author(
    boundary, capsys, repo, tasks, monkeypatch, dry_run_telemetry, trailer
):
    task_record(tasks, "unattested", agent="cursor", resolved_model_known=False, resolved_model="unknown")
    head = repo.commit(trailer)
    repo.publish()
    worktree = repo.root / "wt"
    monkeypatch.setattr(delegate, "_resolve_worktree_base_sha", lambda **_kwargs: head)
    monkeypatch.setattr(delegate, "_ensure_worktree", lambda **_kwargs: (worktree, "feature", {"base_sha": head}))
    with _admitted_host(monkeypatch):
        rc, before = boundary("--branch", "feature", "--owned-path", "docs/a.md", "--dry-run")
    assert rc == 0, capsys.readouterr().err
    admission = dry_run_admission(tasks)
    expected = "cursor" if trailer == "cursor/auto" else "unknown"
    assert admission["existing_families"] == [expected]
    assert admission["author_families"] == ["anthropic", expected]
    assert admission["reviewer"]["name"] == "openai_frontier" and admission["head_sha"] == head
    assert repo.snapshot() == before and boundary.calls == []


def test_dry_run_refusal_writes_nothing(boundary, capsys, repo, tasks):
    repo.commit(OPUS)
    repo.commit(SOL)
    repo.commit(GROK)
    repo.publish()
    assert_refused(
        boundary,
        capsys,
        repo,
        tasks,
        boundary("--branch", "feature", "--owned-path", "docs/a.md", "--dry-run"),
        delegate.AUTHORING_REVIEW_NO_ROUTE,
    )


def assert_moved_refusal(rc, capsys, tasks):
    """A6: a moved head is refused like the initial refusals: exit 2, one JSON receipt line, no task record."""
    err = capsys.readouterr().err
    assert rc == 2, err
    assert f"❌ {delegate.AUTHORING_REVIEW_TARGET_MOVED}:" in err and "provider_calls=0" in err
    receipt = json.loads(err.strip().splitlines()[-1])[delegate.AUTHORING_REVIEW_STATE_KEY]
    assert receipt["refusal"] == delegate.AUTHORING_REVIEW_TARGET_MOVED
    assert receipt["reviewer_availability"] == "unknown"
    assert list(tasks.rglob("*")) == []
    return receipt


def test_reused_worktree_head_moving_after_admission_refuses_before_any_rebase(
    boundary, capsys, repo, tasks, monkeypatch
):
    repo.commit(OPUS)
    checkout = delegate._auto_worktree_path("claude", "writer-1", repo_root=repo.root)
    repo.git("worktree", "add", "-q", "-b", "claude/writer-1", str(checkout), "feature")
    moved = MiniRepo(checkout)

    with _admitted_host(monkeypatch, on_admission=lambda: moved.commit(SOL, message="another writer")):
        rc, _ = boundary("--worktree", "--owned-path", "docs/a.md", "--dry-run")
    receipt = assert_moved_refusal(rc, capsys, tasks)
    assert receipt["current_head_sha"] == moved.sha("HEAD") != receipt["head_sha"]
    assert boundary.calls == []  # the rebase helper never ran


def test_attached_branch_fetched_past_its_admitted_head_refuses(boundary, capsys, repo, tasks, monkeypatch):
    repo.commit(OPUS)
    repo.publish()
    pushed = repo.commit(SOL, message="pushed after admission")
    monkeypatch.setattr(delegate, "_resolve_worktree_base_sha", lambda **_kwargs: pushed)
    with _admitted_host(monkeypatch):
        rc, _ = boundary("--branch", "feature", "--owned-path", "docs/a.md", "--dry-run")
    receipt = assert_moved_refusal(rc, capsys, tasks)
    assert receipt["current_head_sha"] == pushed != receipt["head_sha"]


# --- A7: the endpoints admission freezes are the ones the recorder and creation use ----------------

CODEX_ADAPTER = "scripts/agent_runtime/adapters/codex.py"
MIRROR_URL = "https://mirror.invalid/learn-ukrainian.git"
REAL_RESOLVER = delegate._resolve_worktree_base_sha
REAL_VALIDATOR = delegate._validate_existing_worktree


@pytest.fixture
def dry_run_telemetry(monkeypatch):
    class _Telemetry:
        model, effort, cli_version = "fixture-model", None, None

    import agent_runtime.telemetry as telemetry

    monkeypatch.setattr(telemetry, "resolve_dispatch_start_telemetry", lambda **_kwargs: _Telemetry())


def admitted_dispatch_cleanup(monkeypatch) -> None:
    """An ordinary dispatch past initial admission sweeps runtime leases and decides placement before the worktree
    lock; both effects precede the re-check and stay accepted (A3, M5). It stays on this host."""
    sweep = {"leases_reaped": 0, "bytes_freed": 0, "errors": 0, "error_details": []}
    monkeypatch.setattr(delegate, "_sweep_runtime_tmp_orphans", lambda: sweep)
    monkeypatch.setattr(job_host_exec, "decide_dispatch_placement", lambda **_kwargs: ("notebook", "test", None))


def dry_run_admission(tasks: Path) -> dict:
    record = json.loads((tasks / "writer-1.json").read_text(encoding="utf-8"))
    assert record["status"] == "dry_run"
    return record[delegate.AUTHORING_REVIEW_STATE_KEY]


def last_receipt(err: str) -> dict:
    return json.loads(err.strip().splitlines()[-1])[delegate.AUTHORING_REVIEW_STATE_KEY]


@pytest.mark.parametrize("mode", [(), ("--dry-run",)], ids=["dispatch", "dry-run"])
def test_attach_without_pr_enumerates_from_the_open_prs_older_release_base(
    boundary, github, capsys, repo, tasks, monkeypatch, mode
):
    """Round-2 reproduction 1 (#9739): an OpenAI commit on main, an Anthropic commit on the feature branch, and a PR
    into an older release. Admission without --pr used to enumerate from main, saw only Anthropic and selected an
    OpenAI reviewer the recorder then refused. It now reads the PR's base and refuses at critical risk."""
    release = repo.publish("trunk", to="release")
    repo.git("checkout", "-q", "trunk")
    repo.commit(SOL, path="src/app.py", message="main moves on")
    repo.publish("trunk", to="main")
    repo.git("checkout", "-q", "-B", "feature", "trunk")
    repo.commit(OPUS, message="feature work")
    head = repo.commit(GROK, message="more feature work")
    repo.publish()
    github.prs = [pr_row(42, "release", release)]

    receipt = assert_refused(
        boundary,
        capsys,
        repo,
        tasks,
        boundary("--branch", "feature", "--owned-path", "docs/a.md", *mode),
        delegate.AUTHORING_REVIEW_NO_ROUTE,
    )
    assert receipt["existing_families"] == ["anthropic", "openai", "xai"] and receipt["risk"] == "critical"
    assert receipt["review_base"] == {"repository": REPOSITORY, "branch": "release", "pr": 42, "source": "open-pr"}
    assert (receipt["review_base_sha"], receipt["base_tip_sha"], receipt["head_sha"]) == (release, release, head)

    # The recorder, run on its own on the same history, reads that base, sees both families and qualifies no one.
    monkeypatch.setattr(recorder, "_run_json", lambda _args: {"baseRefOid": release, "headRefOid": head})
    monkeypatch.setattr(recorder, "_pages", lambda _request: github_listing(repo, release, head))
    pr_facts = recorder.pr_review_facts(REPOSITORY, 42, head_sha=head, task_root=tasks, repo_root=repo.root)
    assert pr_facts.existing_families == {"anthropic", "openai", "xai"}
    assert selected(pr_facts, "critical") is None


@pytest.mark.parametrize("mode", [(), ("--dry-run",)], ids=["dispatch", "dry-run"])
def test_new_branch_enumerates_the_custom_base_it_starts_at_not_a_stale_local_copy(boundary, capsys, repo, tasks, mode):
    """Round-2 reproduction 2 (#9739): the local ``origin/custom`` is the clean base (a feasible, empty author set)
    while the canonical ``custom`` carries an Anthropic commit. Admission used to read the local copy and the
    resolver then started the branch at the fetched tip. Admission now observes and enumerates that tip."""
    repo.publish("trunk", to="custom")
    repo.advance_remote("custom", OPUS)
    tip = repo.advance_remote("custom", GROK)
    assert repo.sha("origin/custom") != tip

    receipt = assert_refused(
        boundary,
        capsys,
        repo,
        tasks,
        boundary("--worktree", "--base", "custom", "--owned-path", CODEX_ADAPTER, *mode, writer=SOL),
        delegate.AUTHORING_REVIEW_NO_ROUTE,
    )
    assert receipt["target"] == "new-branch" and receipt["creation_base"] == "custom"
    assert receipt["creation_sha"] == receipt["head_sha"] == tip
    assert receipt["existing_families"] == ["anthropic", "xai"] and receipt["incoming_family"] == "openai"


def test_the_stale_custom_base_alone_would_have_been_feasible(repo, tasks):
    """Control for reproduction 2: on the stale local copy the same writer and scope do have a reviewer."""
    repo.publish("trunk", to="custom")
    stale = recorder.collect_branch_review_facts(
        repository=REPOSITORY,
        repo_root=repo.root,
        base_tip_sha=repo.sha("origin/main"),
        head_sha=repo.sha("origin/custom"),
        task_root=tasks,
        incoming_agent="codex",
        incoming_model="gpt-6.1-sol",
        owned_paths=(CODEX_ADAPTER,),
    )
    assert selected(stale, "critical") == "claude-opus-5-5"


@pytest.mark.parametrize("mode", [(), ("--dry-run",)], ids=["dispatch", "dry-run"])
def test_a_creation_base_that_moves_after_admission_refuses_as_moved(boundary, capsys, repo, tasks, monkeypatch, mode):
    """A7 §3: the commit a new branch starts at is frozen at admission; a different one before use is a move."""
    admitted = repo.publish("trunk", to="custom")
    admitted_dispatch_cleanup(monkeypatch)
    with _admitted_host(monkeypatch, on_admission=lambda: repo.advance_remote("custom", OPUS)):
        rc, before = boundary("--worktree", "--base", "custom", "--owned-path", CODEX_ADAPTER, *mode, writer=SOL)
    receipt = assert_moved_refusal(rc, capsys, tasks)
    assert (receipt["binding"], receipt["admitted_sha"]) == ("creation", admitted)
    assert receipt["current_sha"] == repo.remote_sha("custom") != admitted
    assert boundary.calls == [] and repo.snapshot() == before


def test_a_checkout_reaped_before_the_lock_is_admitted_again_at_its_actual_start_commit(
    boundary, capsys, repo, tasks, monkeypatch
):
    """A7 §3: when the admitted checkout is reaped while dispatch waits, the fresh worktree is admitted in full; becoming
    a new branch exempts nothing, so the moved custom base is enumerated and refused."""
    repo.publish("trunk", to="custom")
    checkout = delegate._auto_worktree_path("codex", "writer-1", repo_root=repo.root)
    repo.git("worktree", "add", "-q", "-b", "codex/writer-1", str(checkout), "trunk")

    def reap_and_advance():
        repo.git("worktree", "remove", "--force", str(checkout))
        repo.git("branch", "-q", "-D", "codex/writer-1")
        repo.advance_remote("custom", OPUS)
        repo.advance_remote("custom", GROK)

    with _admitted_host(monkeypatch, on_admission=reap_and_advance):
        rc, _ = boundary("--worktree", "--base", "custom", "--owned-path", CODEX_ADAPTER, "--dry-run", writer=SOL)
    err = capsys.readouterr().err
    assert rc == 2, err
    assert f"❌ {delegate.AUTHORING_REVIEW_NO_ROUTE}:" in err and "provider_calls=0" in err
    receipt = last_receipt(err)
    assert receipt["target"] == "new-branch" and receipt["creation_sha"] == repo.remote_sha("custom")
    assert receipt["existing_families"] == ["anthropic", "xai"]
    assert list(tasks.rglob("*")) == [] and boundary.calls == []


def test_a_pr_retargeted_after_admission_refuses_as_moved(boundary, github, capsys, repo, tasks, monkeypatch):
    repo.commit(OPUS)
    repo.publish()
    main = repo.sha("origin/main")
    repo.git("checkout", "-q", "-b", "release", "trunk")
    release = repo.commit(OPUS, path="src/app.py", message="release fix")
    repo.publish("release")
    github.prs = [pr_row(42, "main", main)]

    def retarget():
        github.prs[0] = pr_row(42, "release", release)

    with _admitted_host(monkeypatch, on_admission=retarget):
        rc, _ = boundary("--branch", "feature", "--owned-path", "docs/a.md", "--dry-run")
    receipt = assert_moved_refusal(rc, capsys, tasks)
    assert (receipt["binding"], receipt["admitted_sha"], receipt["current_sha"]) == ("review_base", main, release)
    assert receipt["current_review_base"]["branch"] == "release" and receipt["review_base"]["branch"] == "main"


def test_a_default_branch_that_moves_after_admission_refuses_as_moved(boundary, capsys, repo, tasks, monkeypatch):
    repo.commit(OPUS)
    repo.publish()
    admitted = repo.sha("origin/main")
    with _admitted_host(monkeypatch, on_admission=lambda: repo.advance_remote("main", SOL, path="src/app.py")):
        rc, _ = boundary("--branch", "feature", "--owned-path", "docs/a.md", "--dry-run")
    receipt = assert_moved_refusal(rc, capsys, tasks)
    assert (receipt["binding"], receipt["admitted_sha"]) == ("review_base", admitted)
    assert receipt["current_sha"] == repo.remote_sha("main") != admitted


def test_a_review_base_commit_that_cannot_be_fetched_is_unknown(boundary, github, capsys, repo, tasks):
    repo.commit(OPUS)
    repo.publish()
    github.prs = [pr_row(42, "main", "e" * 40)]
    receipt = assert_refused(
        boundary,
        capsys,
        repo,
        tasks,
        boundary("--branch", "feature", "--owned-path", "docs/a.md"),
        delegate.AUTHORING_REVIEW_AUTHORSHIP_UNKNOWN,
    )
    assert receipt["review_base_sha"] == "e" * 40


def test_a_stale_tracking_ref_is_observed_on_the_remote_and_not_reported_as_moved(
    boundary, capsys, repo, tasks, monkeypatch, dry_run_telemetry
):
    """M6: another writer advanced the canonical branch; this repository neither has the commit nor knows the tip.
    Admission observes the remote tip, fetches it and admits it, so the resolver's fetch finds no move."""
    repo.commit(OPUS)
    repo.publish()
    pushed = repo.advance_remote("feature", OPUS)
    assert repo.sha("origin/feature") != pushed
    monkeypatch.setattr(delegate, "_resolve_worktree_base_sha", REAL_RESOLVER)
    worktree = repo.root / "wt"
    monkeypatch.setattr(delegate, "_ensure_worktree", lambda **_kwargs: (worktree, "feature", {"base_sha": pushed}))
    with _admitted_host(monkeypatch):
        rc, _ = boundary("--branch", "feature", "--owned-path", "docs/a.md", "--dry-run")
    assert rc == 0, capsys.readouterr().err
    admission = dry_run_admission(tasks)
    assert admission["head_sha"] == pushed and admission["reviewer"]["name"] == "openai_frontier"


def test_admission_observes_the_canonical_remote_not_a_lagging_mirror(boundary, capsys, repo, tasks, tmp_path):
    """M2/M6 (#7522): ``origin`` is a mirror that lags; the canonical GitHub remote carries an OpenAI commit."""
    repo.commit(OPUS)
    repo.commit(GROK)
    repo.publish()
    mirror = bare_remote(tmp_path / "mirror.git")
    repo.publish("trunk", to="main", remote=mirror)
    repo.publish("feature", remote=mirror)
    repo.git("remote", "set-url", "origin", MIRROR_URL)
    repo.git("config", f"url.{mirror}.insteadOf", MIRROR_URL)
    repo.git("remote", "add", "github", CANONICAL_URL)
    head = repo.advance_remote("feature", SOL, path="src/app.py")

    receipt = assert_refused(
        boundary,
        capsys,
        repo,
        tasks,
        boundary("--branch", "feature", "--owned-path", "docs/a.md"),
        delegate.AUTHORING_REVIEW_NO_ROUTE,
    )
    assert receipt["head_sha"] == head and receipt["existing_families"] == ["anthropic", "openai", "xai"]


@pytest.mark.parametrize("repo", ["develop"], indirect=True)
def test_the_default_branch_is_discovered_not_assumed_to_be_main(
    boundary, capsys, repo, tasks, monkeypatch, dry_run_telemetry
):
    """M4: a repository whose default branch is ``develop`` (and has no ``main``) reviews and starts from it."""
    develop = repo.sha("origin/develop")
    with _admitted_host(monkeypatch):
        rc, _ = boundary("--worktree", "--owned-path", CODEX_ADAPTER, "--dry-run", writer=SOL)
    assert rc == 0, capsys.readouterr().err
    admission = dry_run_admission(tasks)
    assert admission["review_base"]["branch"] == admission["creation_base"] == "develop"
    assert admission["review_base_sha"] == admission["creation_sha"] == develop
    assert admission["reviewer"]["name"] == "claude-opus-5-5"


def test_a_detached_checkout_has_no_known_pr_and_refuses(boundary, capsys, repo, tasks):
    """M6: a detached HEAD names no head branch, so no PR, and so no review base, can be bound to it."""
    repo.commit(OPUS)
    checkout = delegate._auto_worktree_path("claude", "writer-1", repo_root=repo.root)
    repo.git("worktree", "add", "-q", "--detach", str(checkout), "feature")
    rc, before = boundary("--worktree", "--owned-path", "docs/a.md")
    err = capsys.readouterr().err
    assert rc == 2, err
    assert f"❌ {delegate.AUTHORING_REVIEW_AUTHORSHIP_UNKNOWN}: the checkout has a detached HEAD" in err
    assert last_receipt(err)["target"] == "existing-worktree"
    assert repo.snapshot() == before and list(tasks.rglob("*")) == [] and boundary.calls == []


def test_a_same_named_fork_pr_does_not_refuse_the_dispatch(
    boundary, github, capsys, repo, tasks, monkeypatch, dry_run_telemetry
):
    """M6: a fork's PR from a branch also named ``feature`` is not this branch's PR; it must not block dispatch."""
    repo.commit(OPUS)
    head = repo.publish()
    github.prs = [pr_row(9, "main", "c" * 40, fork=True)]
    worktree = repo.root / "wt"
    monkeypatch.setattr(delegate, "_resolve_worktree_base_sha", lambda **_kwargs: head)
    monkeypatch.setattr(delegate, "_ensure_worktree", lambda **_kwargs: (worktree, "feature", {"base_sha": head}))
    with _admitted_host(monkeypatch):
        rc, _ = boundary("--branch", "feature", "--owned-path", "docs/a.md", "--dry-run")
    assert rc == 0, capsys.readouterr().err
    assert dry_run_admission(tasks)["review_base"]["source"] == "default-branch"


def test_an_admitted_new_branch_is_created_at_the_frozen_creation_commit(boundary, capsys, repo, tasks, monkeypatch):
    """A7 §3 feasible control, ordinary dispatch: creation receives the admitted commit and resolves no base again."""
    admitted = repo.publish("trunk", to="custom")
    created: dict = {}

    class _Created(Exception):
        pass

    def ensure_worktree(**kwargs):
        created.update(kwargs)
        raise _Created

    monkeypatch.setattr(delegate, "_ensure_worktree", ensure_worktree)
    admitted_dispatch_cleanup(monkeypatch)
    with _admitted_host(monkeypatch), pytest.raises(_Created):
        boundary("--worktree", "--base", "custom", "--owned-path", CODEX_ADAPTER, writer=SOL)
    assert created["resolved_base_sha"] == admitted and created["branch"] is None
    assert boundary.calls == []  # the base resolver (a fetch and dereference) never ran


# --- round 6: admission evaluates the commits a reused checkout actually ends up with ----------------


class _Provisioned(Exception):
    """Raised by a stub ``_ensure_worktree``: the dispatch was admitted and reached provisioning."""


def reused_worktree_behind_main(
    repo: MiniRepo, github: FakeGitHub, *, main_trailer: str | None
) -> tuple[Path, str, str]:
    """A reused worktree whose main PR has an older frozen base while main gained a ``main_trailer`` commit.

    Returns the checkout, the release commit (the PR's review base) and the new ``main`` tip.
    """
    release = repo.publish("trunk", to="release")
    repo.git("checkout", "-q", "trunk")
    main = repo.commit(main_trailer, path="src/app.py", message="main moves on")
    repo.publish("trunk", to="main")
    checkout = delegate._auto_worktree_path("claude", "writer-1", repo_root=repo.root)
    repo.git("worktree", "add", "-q", "-b", "claude/writer-1", str(checkout), release)
    MiniRepo(checkout).commit(OPUS, message="feature work")
    github.prs = [pr_row(42, "main", release, head="claude/writer-1")]
    return checkout, release, main


@pytest.mark.parametrize("main_trailer", [OPUS, SOL, None, "codex/impl-a\n\nX-Agent: codex/impl-b"])
def test_rebase_admits_only_branch_authors_and_pins_onto(
    boundary, github, capsys, repo, tasks, monkeypatch, main_trailer
):
    """#9988: unknown/multi-trailer main squashes and other families never become branch authors."""
    checkout, release, main = reused_worktree_behind_main(repo, github, main_trailer=main_trailer)
    monkeypatch.setattr(delegate, "_resolve_worktree_base_sha", REAL_RESOLVER)
    monkeypatch.setattr(delegate, "_validate_existing_worktree", REAL_VALIDATOR)
    planned_onto: list[str] = []
    admissions: list = []
    real_plan = delegate._authoring_rebase_plan

    def plan(admission, *, base):
        admissions.append(admission)
        planned_onto.append(real_plan(admission, base=base))
        repo.advance_remote("main", SOL, path="src/app.py")
        return planned_onto[-1]

    monkeypatch.setattr(delegate, "_authoring_rebase_plan", plan)
    created: dict = {}

    def ensure_worktree(**kwargs):
        created.update(kwargs)
        raise _Provisioned

    monkeypatch.setattr(delegate, "_ensure_worktree", ensure_worktree)
    admitted_dispatch_cleanup(monkeypatch)
    with _admitted_host(monkeypatch), pytest.raises(_Provisioned):
        boundary("--worktree", "--owned-path", "docs/a.md")
    rebased = MiniRepo(checkout).sha("HEAD")
    assert planned_onto == [main] and created["resolved_base_sha"] == rebased
    assert MiniRepo(checkout).git("rev-parse", "HEAD^") == main
    assert admissions[0].record["rebase_existing_families"] == ["anthropic"]
    assert admissions[0].record["rebased_existing_families"] == ["anthropic"]
    # Preserve A7's stale-base diff, independently of excluded authorship.
    actual = recorder.collect_branch_review_facts(
        repository=REPOSITORY,
        repo_root=repo.root,
        base_tip_sha=release,
        head_sha=rebased,
        task_root=tasks,
        incoming_agent="claude",
        incoming_model="claude-opus-5-5",
        owned_paths=("docs/a.md",),
        authorship_exclude_sha=main,
    )
    assert actual.existing_families == {"anthropic"}
    assert set(actual.changed_paths) == {"docs/a.md", "src/app.py"}
    assert boundary.calls == []


def test_rebase_still_refuses_forbidden_branch_authors(boundary, github, capsys, repo, tasks, monkeypatch):
    checkout, _, _ = reused_worktree_behind_main(repo, github, main_trailer=None)
    MiniRepo(checkout).commit(SOL, message="other branch author")
    MiniRepo(checkout).commit(GROK, message="third branch author")
    admitted_dispatch_cleanup(monkeypatch)
    with _admitted_host(monkeypatch):
        result = boundary("--worktree", "--owned-path", "docs/a.md")
    receipt = assert_refused(boundary, capsys, repo, tasks, result, delegate.AUTHORING_REVIEW_NO_ROUTE, reused=True)
    assert receipt["existing_families"] == ["anthropic", "openai", "xai"]


def test_rebase_preserves_main_side_protected_scope(boundary, github, capsys, repo, tasks, monkeypatch):
    checkout, _, _ = reused_worktree_behind_main(repo, github, main_trailer=SOL)
    repo.commit(None, path=CODEX_ADAPTER, message="protected main change")
    main = repo.publish("trunk", to="main")
    MiniRepo(checkout).commit(GROK, message="second branch author")
    admitted_dispatch_cleanup(monkeypatch)
    with _admitted_host(monkeypatch):
        result = boundary("--worktree", "--owned-path", "docs/a.md")
    receipt = assert_refused(boundary, capsys, repo, tasks, result, delegate.AUTHORING_REVIEW_NO_ROUTE, reused=True)
    assert receipt["rebase_onto"] == main
    assert receipt["rebase_existing_families"] == ["anthropic", "xai"]
    assert receipt["reviewer"] is None


def test_a_rebase_result_that_is_not_the_planned_one_refuses(boundary, github, capsys, repo, tasks, monkeypatch):
    """The plan admits Anthropic only; another writer commits in the checkout before the rebase replays it. The
    rebased head is checked against the plan and refused before any task record or worker."""
    checkout, _release, main = reused_worktree_behind_main(repo, github, main_trailer=OPUS)
    monkeypatch.setattr(delegate, "_validate_existing_worktree", REAL_VALIDATOR)

    def resolve_after_another_writer(**kwargs):
        MiniRepo(checkout).commit(SOL, message="another writer")
        return REAL_RESOLVER(**kwargs)

    monkeypatch.setattr(delegate, "_resolve_worktree_base_sha", resolve_after_another_writer)
    admitted_dispatch_cleanup(monkeypatch)
    with _admitted_host(monkeypatch):
        rc, _ = boundary("--worktree", "--owned-path", "docs/a.md")
    receipt = assert_moved_refusal(rc, capsys, tasks)
    assert (receipt["binding"], receipt["rebase_onto"]) == ("rebase", main)
    assert receipt["rebase_existing_families"] == ["anthropic"]
    assert receipt["current_existing_families"] == ["anthropic", "openai"]
    assert receipt["current_sha"] == MiniRepo(checkout).sha("HEAD") != receipt["admitted_sha"]


def test_an_unobservable_rebase_target_refuses_as_unknown_before_any_rebase(
    boundary, github, capsys, repo, tasks, monkeypatch
):
    """A rebase target the canonical remote does not serve: its authors are unknown, so nothing is rebased."""
    reused_worktree_behind_main(repo, github, main_trailer=OPUS)
    monkeypatch.setattr(delegate, "_ls_remote_branch_sha", lambda _remote, _branch: None)
    admitted_dispatch_cleanup(monkeypatch)
    with _admitted_host(monkeypatch):
        result = boundary("--worktree", "--base", "release", "--owned-path", "docs/a.md")
    assert_refused(boundary, capsys, repo, tasks, result, delegate.AUTHORING_REVIEW_AUTHORSHIP_UNKNOWN, reused=True)


def test_a_cwd_branch_switch_at_the_same_commit_refuses_as_moved(boundary, github, capsys, repo, tasks, monkeypatch):
    """Round-6 probe 2 (#9739): the --cwd checkout was admitted on a branch whose PR targets main; under the lock it
    is on another branch at the same commit, whose PR targets an older release. The branch binding refuses, and the
    refusal leaves no log file behind."""
    release = repo.publish("trunk", to="release")
    repo.git("checkout", "-q", "trunk")
    main = repo.commit(SOL, path="src/app.py", message="main moves on")
    repo.publish("trunk", to="main")
    checkout = delegate._auto_worktree_path("claude", "earlier-task", repo_root=repo.root)
    repo.git("worktree", "add", "-q", "-b", "feat-a", str(checkout), main)
    head = MiniRepo(checkout).commit(OPUS, message="feature work")
    repo.git("branch", "feat-b", head)
    github.prs = [pr_row(42, "main", main, head="feat-a"), pr_row(43, "release", release, head="feat-b")]
    admitted_dispatch_cleanup(monkeypatch)
    with _admitted_host(monkeypatch, on_admission=lambda: MiniRepo(checkout).git("checkout", "-q", "feat-b")):
        rc, _ = boundary("--cwd", str(checkout), "--owned-path", "docs/a.md")
    err = capsys.readouterr().err
    assert rc == 2, err
    assert f"❌ {delegate.AUTHORING_REVIEW_TARGET_MOVED}:" in err and "provider_calls=0" in err
    receipt = last_receipt(err)
    assert (receipt["binding"], receipt["admitted_branch"], receipt["current_branch"]) == (
        "head_branch",
        "feat-a",
        "feat-b",
    )
    assert receipt["review_base"]["pr"] == 42 and receipt["head_sha"] == MiniRepo(checkout).sha("HEAD")
    assert [path for path in tasks.rglob("*") if path.is_file()] == []
    assert boundary.calls == []


def test_a_cwd_checkout_detached_at_the_same_commit_refuses_as_moved(
    boundary, github, capsys, repo, tasks, monkeypatch
):
    repo.commit(OPUS)
    repo.publish()
    checkout = delegate._auto_worktree_path("claude", "earlier-task", repo_root=repo.root)
    repo.git("worktree", "add", "-q", "-b", "feat-a", str(checkout), "feature")
    admitted_dispatch_cleanup(monkeypatch)
    detach = lambda: MiniRepo(checkout).git("checkout", "-q", "--detach")  # noqa: E731
    with _admitted_host(monkeypatch, on_admission=detach):
        rc, _ = boundary("--cwd", str(checkout), "--owned-path", "docs/a.md")
    err = capsys.readouterr().err
    assert rc == 2, err
    assert "now a detached HEAD" in err
    assert last_receipt(err)["current_branch"] == "HEAD"
    assert [path for path in tasks.rglob("*") if path.is_file()] == []


@pytest.mark.parametrize(
    "case", ["same-writer", "other-writer", "unknown-writer", "diverged", "dirty", "remote-moved", "remote-rewound"]
)
def test_ahead_of_remote_continuation_is_bound_to_same_writer_and_remote(
    boundary, github, capsys, repo, tasks, monkeypatch, case
):
    """Real Git: retain finished local work only under #9988's continuation rule."""
    checkout, release, _ = reused_worktree_behind_main(repo, github, main_trailer=None)
    branch = "claude/writer-1"
    remote_head = repo.publish(branch)
    local_head = MiniRepo(checkout).commit(
        SOL if case == "other-writer" else None if case == "unknown-writer" else OPUS,
        message="finished unpushed work",
    )
    if case == "diverged":
        repo.advance_remote(branch, OPUS, path="src/app.py")
    if case == "dirty":
        (checkout / "docs/a.md").write_text("uncommitted work\n")
    monkeypatch.setattr(delegate, "_resolve_worktree_base_sha", REAL_RESOLVER)
    monkeypatch.setattr(delegate, "_validate_existing_worktree", REAL_VALIDATOR)
    created: dict = {}

    def ensure_worktree(**kwargs):
        created.update(kwargs)
        raise _Provisioned

    monkeypatch.setattr(delegate, "_ensure_worktree", ensure_worktree)
    admitted_dispatch_cleanup(monkeypatch)

    def move_remote():
        if case == "remote-moved":
            repo.advance_remote(branch, OPUS, path="src/app.py")
        elif case == "remote-rewound":
            _run_git("--git-dir", str(repo.remote), "update-ref", f"refs/heads/{branch}", release)

    with _admitted_host(monkeypatch, on_admission=move_remote):
        if case == "same-writer":
            with pytest.raises(_Provisioned):
                boundary("--worktree", str(checkout), "--branch", branch, "--owned-path", "docs/a.md")
            assert created["resolved_base_sha"] == local_head
            assert repo.remote_sha(branch) == remote_head
        else:
            rc, _ = boundary("--worktree", str(checkout), "--branch", branch, "--owned-path", "docs/a.md")
            err = capsys.readouterr().err
            assert rc in (1, 2), err
            assert not created
            if case in {"other-writer", "unknown-writer"}:
                assert delegate.AUTHORING_REVIEW_AUTHORSHIP_UNKNOWN in err
            elif case == "dirty":
                assert "uncommitted changes" in err
            else:
                assert "behind" in err or "not an ancestor" in err
    assert MiniRepo(checkout).sha("HEAD") == local_head
    assert release != local_head
    assert boundary.calls == []


def test_stale_main_base_excludes_merged_main_authors_but_not_branch_authors(repo, tasks):
    base = repo.sha("origin/main")
    branch_head = repo.commit(OPUS)
    repo.git("checkout", "-q", "trunk")
    main = repo.commit(None, path="src/app.py", message="unattributable squash")
    repo.publish("trunk", to="main")
    repo.git("checkout", "-q", "feature")
    repo.git("merge", "-q", "--no-ff", main, "-m", "sync base")
    fact = recorder.collect_branch_review_facts(
        repository=REPOSITORY,
        repo_root=repo.root,
        base_tip_sha=base,
        head_sha=repo.sha("HEAD"),
        task_root=tasks,
        incoming_agent="claude",
        incoming_model="claude-opus-5-5",
        owned_paths=("docs/a.md",),
        authorship_exclude_sha=main,
    )
    assert fact.existing_families == {"anthropic"}
    assert branch_head in {commit.sha for commit in fact.commits}
    assert main not in {commit.sha for commit in fact.commits}
    assert set(fact.changed_paths) == {"docs/a.md", "src/app.py"}


@pytest.mark.parametrize("exclude", ["not-a-sha", "a" * 40])
def test_authorship_exclusion_requires_a_real_commit(repo, tasks, exclude):
    with pytest.raises(recorder.BranchFactsError) as refused:
        recorder.collect_branch_review_facts(
            repository=REPOSITORY,
            repo_root=repo.root,
            base_tip_sha=repo.sha("origin/main"),
            head_sha=repo.sha("HEAD"),
            task_root=tasks,
            authorship_exclude_sha=exclude,
        )
    assert refused.value.code == recorder.FACTS_TARGET_UNKNOWN
