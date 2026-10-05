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


class MiniRepo:
    """A throwaway repository whose ``origin/<branch>`` refs are local refs (nothing is fetched)."""

    def __init__(self, root: Path) -> None:
        self.root = root

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

    def publish(self, branch: str = "feature") -> str:
        head = self.sha(branch)
        self.git("update-ref", f"refs/remotes/origin/{branch}", head)
        return head

    def snapshot(self) -> tuple[str, str, str]:
        return (
            self.git("for-each-ref", "--format=%(refname) %(objectname)"),
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
def repo(tmp_path, monkeypatch) -> MiniRepo:
    return mini_repo(tmp_path, monkeypatch)


def mini_repo(tmp_path: Path, monkeypatch) -> MiniRepo:
    """A repository at ``<tmp_path>/primary`` on branch ``feature``, forked from ``origin/main``."""
    for key in list(os.environ):
        if key.startswith("GIT_"):
            monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", os.devnull)
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    root = tmp_path / "primary"
    root.mkdir()
    mini = MiniRepo(root)
    # A non-protected local branch name: agent Git shims refuse branch creation on main.
    mini.git("init", "-q", "-b", "trunk")
    mini.git("config", "user.name", "Fixture")
    mini.git("config", "user.email", "fixture@example.invalid")
    mini.git("config", "core.hooksPath", os.devnull)
    for path in ("docs/a.md", "src/app.py", CLAUDE_ADAPTER, SHARED_HOOK):
        (root / path).parent.mkdir(parents=True, exist_ok=True)
        (root / path).write_text(f"base {path}\n", encoding="utf-8")
    (root / ".gitignore").write_text(".worktrees/\n", encoding="utf-8")
    mini.git("add", "-A")
    mini.git("commit", "-q", "-m", f"base\n\nX-Agent: {OPUS}\n")
    mini.git("update-ref", "refs/remotes/origin/main", "HEAD")
    mini.git("checkout", "-q", "-b", "feature")
    return mini


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
    for index, trailer in enumerate(order):
        repo.commit(trailer, message=f"commit {index}")
    fact = facts(repo, tasks, writer=writer)

    assert fact.existing_families == {"anthropic", "openai"}
    assert selected(fact, "critical") is None


def test_mixed_family_at_lower_risk_keeps_a_third_family(repo, tasks, monkeypatch, tmp_path):
    repo.commit(OPUS)
    repo.commit(SOL)
    repo.publish()
    fact = facts(repo, tasks, writer=OPUS)

    assert selected(fact, "medium") == "grok-4.7-cursor-fallback"
    receipt = record_verdict(
        monkeypatch, tmp_path, repo, agent="cursor", model="auto", review_risk="medium", **GROK_RECEIPT
    )
    assert receipt["verdict"] == "APPROVED"
    # Every author stays attributed: neither frontier family may approve.
    for agent, model in (("codex", "gpt-6.1-sol"), ("claude", "claude-opus-5-5")):
        with pytest.raises(recorder.RecordError, match="equals an author family"):
            record_verdict(monkeypatch, tmp_path, repo, agent=agent, model=model, review_risk="medium")


def test_recorder_holds_a_below_critical_reviewer_to_the_recorded_risk(repo, tasks, monkeypatch, tmp_path):
    repo.commit(OPUS)
    repo.commit(SOL)
    repo.publish()
    with pytest.raises(recorder.RecordError, match="not qualified"):
        record_verdict(
            monkeypatch, tmp_path, repo, agent="cursor", model="auto", review_risk="critical", **GROK_RECEIPT
        )


# --- 3. incoming-family exclusion ----------------------------------------------------------------


def test_incoming_family_joins_the_authors(repo, tasks):
    repo.commit(OPUS)
    assert selected(facts(repo, tasks, writer=SOL), "critical") is None
    assert selected(facts(repo, tasks, writer="claude/claude-sonnet-5-5"), "critical") == "openai_frontier"


def test_cursor_auto_incoming_writer_is_the_xai_moonshot_union(repo, tasks):
    repo.commit(OPUS)
    repo.commit(SOL)
    auto = facts(repo, tasks, writer="cursor/auto")

    assert auto.incoming_family == "cursor-auto-union"
    assert auto.excluded_families == {"anthropic", "openai", "xai", "moonshot"}
    # Without Auto the Cursor Grok seat reviews at medium; with it, nothing remains.
    assert selected(facts(repo, tasks, writer=OPUS), "medium") == "grok-4.7-cursor-fallback"
    assert selected(auto, "medium") is None


@pytest.mark.parametrize(
    "record,attributed",
    [
        ({"resolved_model_known": True, "resolved_model": "claude-opus-5-5-high"}, True),
        ({"resolved_model_known": False, "resolved_model": "unknown"}, False),
    ],
)
def test_committed_cursor_authorship_needs_a_runtime_attested_model(repo, tasks, record, attributed):
    task_record(tasks, "run", agent="cursor", model="auto", **record)
    repo.commit("cursor/run")
    if attributed:
        assert facts(repo, tasks).existing_families == {"anthropic"}
    else:
        with pytest.raises(recorder.BranchFactsError, match="author family unknown") as refused:
            facts(repo, tasks)
        assert refused.value.code == recorder.FACTS_AUTHORSHIP_UNKNOWN


# --- 4. protected-scope qualification ------------------------------------------------------------


def test_claude_adapter_raises_risk_and_excludes_every_claude_reviewer(repo, tasks):
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
    assert selected(facts(repo, tasks, writer=OPUS, seats=("codex",)), "critical") is None
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
        ("missing-record", "provenance unavailable"),
        ("repository-mismatch", "conflicts with commit trailer"),
        ("conflicting-model", "author family unknown"),
        ("unproven-merge", "missing explicit X-Agent"),
    ],
)
def test_unknown_attribution_is_never_green(repo, tasks, case, reason):
    repo.commit(OPUS)
    if case == "missing-trailer":
        repo.commit(None)
    elif case == "duplicate-trailer":
        repo.commit(f"{OPUS}\nX-Agent: {SOL}")
    elif case == "missing-record":
        repo.commit("codex/no-such-task")
    elif case == "repository-mismatch":
        task_record(tasks, "elsewhere", agent="codex", model="gpt-6.1-sol", repository="other/repo")
        repo.commit("codex/elsewhere")
    elif case == "conflicting-model":
        task_record(tasks, "odd", agent="codex", model="not-a-catalog-model")
        repo.commit("codex/odd")
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


@pytest.fixture
def boundary(repo, tasks, monkeypatch):
    """``delegate.cmd_dispatch`` on the miniature repository, with a tripwire on every side effect."""
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
        (delegate, "_fetch_existing_branch", "fetch"),
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


def assert_refused(boundary, capsys, repo, tasks, result, code):
    rc, before = result
    err = capsys.readouterr().err
    assert rc == 2, err
    assert f"❌ {code}:" in err and "provider_calls=0" in err
    receipt = json.loads(err.strip().splitlines()[-1])["authoring_review_admission"]
    assert receipt["refusal"] == code and receipt["reviewer_availability"] == "unknown"
    assert boundary.calls == []
    assert repo.snapshot() == before
    assert list(tasks.rglob("*")) == []
    assert not (repo.root / ".worktrees").exists()
    return receipt


@pytest.mark.parametrize(
    "override",
    [(), ("--force-agent",), ("--force-admission", "hotfix"), ("--allow-dor-warn", "accepted warning")],
)
def test_mixed_branch_refuses_a_writer_and_no_flag_overrides_it(boundary, capsys, repo, tasks, override):
    repo.commit(OPUS)
    repo.commit(SOL)
    repo.publish()
    receipt = assert_refused(
        boundary,
        capsys,
        repo,
        tasks,
        boundary("--branch", "feature", "--owned-path", "docs/a.md", *override),
        delegate.AUTHORING_REVIEW_NO_ROUTE,
    )
    assert receipt["existing_families"] == ["anthropic", "openai"] and receipt["risk"] == "critical"


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
    repo.publish()
    receipt = assert_refused(
        boundary,
        capsys,
        repo,
        tasks,
        boundary(*target, "--owned-path", CLAUDE_ADAPTER),
        delegate.AUTHORING_REVIEW_NO_ROUTE,
    )
    assert receipt["existing_families"] == ["anthropic", "openai"]
    assert receipt["review_base"] == "origin/main"
    assert receipt["base_tip_sha"] == repo.sha("origin/main")


def test_review_base_is_the_pr_base_or_the_default_branch_never_the_caller_base(monkeypatch):
    calls: list[list[str]] = []

    def gh(command, **_kwargs):
        calls.append(command)
        return subprocess.CompletedProcess(command, 0, stdout=json.dumps({"baseRefName": "release"}))

    monkeypatch.setattr(delegate.subprocess, "run", gh)
    namespace = __import__("argparse").Namespace
    assert delegate._authoring_review_base(namespace(base="feature"), repository=REPOSITORY) == "main"
    assert calls == []
    assert delegate._authoring_review_base(namespace(base="feature", pr=12), repository=REPOSITORY) == "release"
    assert calls[-1][:5] == ["gh", "pr", "view", "12", "--repo"]

    monkeypatch.setattr(delegate.subprocess, "run", lambda command, **_kw: subprocess.CompletedProcess(command, 1))
    assert delegate._authoring_review_base(namespace(base="feature", pr=12), repository=REPOSITORY) is None


def test_undeterminable_review_base_is_unknown_authorship(boundary, capsys, repo, tasks, monkeypatch):
    repo.commit(OPUS)
    repo.publish()
    monkeypatch.setattr(delegate, "_authoring_review_base", lambda *_args, **_kwargs: None)
    assert_refused(
        boundary,
        capsys,
        repo,
        tasks,
        boundary("--branch", "feature", "--owned-path", "docs/a.md"),
        delegate.AUTHORING_REVIEW_AUTHORSHIP_UNKNOWN,
    )


def test_adding_openai_to_an_anthropic_branch_refuses(boundary, capsys, repo, tasks):
    repo.commit(OPUS)
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
        boundary("--worktree", "--owned-path", CLAUDE_ADAPTER, writer=SOL),
        delegate.AUTHORING_REVIEW_NO_ROUTE,
    )
    assert receipt["target"] == "new-branch" and receipt["subject_seats"] == ["claude"]


def test_cursor_auto_writer_refuses_where_only_the_cursor_seat_could_review(boundary, capsys, repo, tasks, monkeypatch):
    repo.commit(OPUS)
    repo.commit(SOL)
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
    assert receipt["incoming_family"] == "cursor-auto-union"


@pytest.mark.parametrize(
    "extra,code",
    [
        (("--worktree",), delegate.AUTHORING_REVIEW_SCOPE_UNKNOWN),
        (("--worktree", "--owned-path", SHARED_HOOK), delegate.AUTHORING_REVIEW_SCOPE_UNKNOWN),
        (("--branch", "feature", "--owned-path", "docs/a.md"), delegate.AUTHORING_REVIEW_AUTHORSHIP_UNKNOWN),
        (("--branch", "absent", "--owned-path", "docs/a.md"), delegate.AUTHORING_REVIEW_AUTHORSHIP_UNKNOWN),
    ],
)
def test_unknown_scope_or_authorship_refuses_at_the_boundary(boundary, capsys, repo, tasks, extra, code):
    repo.commit(None)  # an unattributed commit on feature
    repo.publish()
    assert_refused(boundary, capsys, repo, tasks, boundary(*extra), code)


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


def test_dry_run_refusal_writes_nothing(boundary, capsys, repo, tasks):
    repo.commit(OPUS)
    repo.commit(SOL)
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
