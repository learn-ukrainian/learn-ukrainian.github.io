"""#9739: a writer is admitted only while a qualified reviewer outside every author family remains.

Facts come from miniature Git histories and task-provenance records, never from a
replaced calculator. The selector (``reviewer_resolver``) and the recorder
(``record_cf_verdict.record``) are each run on the same repository; refusals are
checked against the surviving selector and verdict recorder.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from scripts.orchestration import fleet_repos
from scripts.orchestration.fleet_repos import FleetRepo
from scripts.review import record_cf_verdict as recorder
from scripts.review import target_resolution
from tests.claude_route_accounts import HOST_ACCOUNT

REPOSITORY = "learn-ukrainian/learn-ukrainian.github.io"
CLAUDE_ADAPTER = "scripts/agent_runtime/adapters/claude.py"
SHARED_HOOK = "agents_extensions/shared/hooks/guard-reviewer-publish.py"
OPUS = "claude/claude-opus-5-5"
SOL = "codex/gpt-6.1-sol"
# Native and Cursor Grok review at every risk (#9769), so exhausting the reviewers takes an xAI author too.
GROK = "grok/grok-4.7"


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
    resolution = recorder.structural_review_route(fact, risk=risk, claude_account=HOST_ACCOUNT)
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
    record_kwargs = review.pop("_record_kwargs", {})
    statuses = review.pop("_statuses", None)
    task_id = review.pop("_task_id", "review")
    caller = review.pop("_caller", repo.root)
    cli = review.pop("_cli", False)
    reply = review.pop("_reply", "Checked.\n\nVERDICT: APPROVE\n")
    base, head = repo.sha("origin/main"), repo.sha("feature")
    review_root = caller / "batch_state" / "tasks" if cli else tmp_path / "review-tasks"
    review_root.mkdir(parents=True, exist_ok=True)
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
    (review_root / f"{task_id}.json").write_text(json.dumps(fields), encoding="utf-8")
    (review_root / f"{task_id}.result").write_text(reply, encoding="utf-8")
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
                    "created_at": "2026-10-05T12:01:00Z",
                    "updated_at": "2026-10-05T12:01:00Z",
                }
                comments.append(item)
                return item
            if args.verb == "read-comment":
                return comments[-1]
            raise AssertionError(args.verb)
        if args[:3] == ["gh", "pr", "view"]:
            return {"number": 42, "headRefOid": head, "headRefName": "feature", "state": "OPEN"}
        raise AssertionError(args)

    monkeypatch.setattr(recorder, "_run_json", fake_json)
    monkeypatch.setattr(recorder, "_pages", lambda request: listing or github_listing(repo, base, head))
    monkeypatch.setattr(recorder, "_repo_root", lambda: caller)
    monkeypatch.setattr(recorder.GitHubAdapter, "identity", lambda self: "fleet")
    monkeypatch.setattr(recorder.GitHubAdapter, "comments", lambda self, repository, number: list(comments))
    monkeypatch.setattr(
        recorder, "post_commit_status", lambda **kwargs: statuses.append(kwargs) if statuses is not None else None
    )
    monkeypatch.chdir(caller)
    if cli:
        return recorder.main(["--task-id", task_id, "--pr", "42"])
    return recorder.record(task_id, pr_number=42, task_root=review_root, lock_root=tmp_path / "locks", **record_kwargs)


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
def test_auto_and_unknown_authors_preserve_review_independence(
    repo, tasks, monkeypatch, tmp_path, trailer, agent, model, review
):
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
    if expected == "unknown":
        # An unknown author excludes no family, so no reviewer is provably outside it (C-2902 F1).
        with pytest.raises(recorder.RecordError, match="AUTHOR_UNRESOLVED"):
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


def test_single_family_branch_agrees_across_selector_and_recorder(repo, tasks, monkeypatch, tmp_path, capsys):
    """Full history and provenance must survive selection of a different Git object store."""
    task_record(tasks, "hot-task", agent="claude", model="claude-opus-5-5")
    task_record(tasks, "old-task", archived=True, agent="claude", model="claude-opus-5-5")
    repo.commit(OPUS, message="one")
    repo.commit("claude/hot-task", message="two")
    repo.commit("claude/old-task\nX-Agent: claude/hot-task\nX-Agent: claude/old-task", message="three")
    repo.publish()

    fact = facts(repo, tasks, writer=OPUS)

    assert fact.existing_families == {"anthropic"} and fact.receipt()["commits"] == 3
    assert len(fact.commits) == 5
    assert {commit.source for commit in fact.commits} == {"trailer-model", "task-record", "task-record-archived"}
    assert fact.author_task_ids == {"hot-task", "old-task"}
    assert fact.author_models == ("claude-opus-5-5",) * 3
    assert fact.author_task_models == ("claude-opus-5-5",)
    assert selected(fact, "critical") == "openai_frontier"
    provenance = tmp_path / "public"
    provenance.mkdir()
    _run_git("init", "-q", "-b", "trunk", cwd=provenance)
    _run_git("remote", "add", "origin", "https://github.com/owner/public.git", cwd=provenance)
    catalog = {
        "public": FleetRepo("public", "owner/public", "public", "test", True),
        "target": FleetRepo("target", REPOSITORY, repo.root.name, "test"),
    }
    monkeypatch.setattr(recorder, "load_fleet_repos", lambda: catalog)
    monkeypatch.setattr(target_resolution, "load_fleet_repos", lambda: catalog)
    monkeypatch.setattr(fleet_repos, "load_fleet_repos", lambda: catalog)
    posted = []
    # The CLI reads canonical provenance while Git history and citations use the target.
    assert record_verdict(
        monkeypatch,
        tmp_path,
        repo,
        agent="codex",
        model="gpt-6.1-sol",
        review_risk="critical",
        comments=posted,
        _caller=provenance,
        _cli=True,
        _reply=f"Checked `{repo.root}/docs/a.md`.\n\nVERDICT: APPROVE\n",
    ) == 0
    receipt = json.loads(capsys.readouterr().out)
    assert receipt["verdict"] == "APPROVED" and receipt["head"] == repo.sha("feature")
    assert len(list((provenance / "batch_state" / "locks").glob("*.lock"))) == 1
    assert not (repo.root / "batch_state").exists()
    assert str(repo.root) not in posted[0]["body"] and str(provenance) not in posted[0]["body"]
    assert "docs/a.md" in posted[0]["body"]
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
    repo.commit(f"{OPUS}\nX-Agent: {SOL}")
    repo.commit(SOL)
    repo.publish()
    fact = facts(repo, tasks, writer=OPUS)

    assert fact.existing_families == {"anthropic", "openai"}
    assert fact.receipt()["commits"] == 2 and len(fact.commits) == 3
    assert fact.author_models == ("gpt-6.1-sol", "claude-opus-5-5", "gpt-6.1-sol")
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
    # The surviving Grok Cursor route cannot review a Cursor-authored branch, and AGY has no
    # review seat (dispatch refuses read-only AGY, C-2970): nobody is left at medium risk.
    assert selected(facts(repo, tasks, writer=OPUS), "medium") == "grok-4.7-cursor-fallback"
    resolution = recorder.structural_review_route(auto, risk="medium", claude_account=HOST_ACCOUNT)
    assert resolution.selected is None
    trace = {entry.name: entry for entry in resolution.trace}
    assert "grok-4.7" not in trace
    assert trace["grok-4.7-cursor-fallback"].status == "excluded"


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
    resolution = recorder.structural_review_route(fact, risk="low", claude_account=HOST_ACCOUNT)

    assert fact.subject_seats == {"claude"}
    assert resolution.resolved_risk == "critical" and resolution.selected is None
    reasons = {entry.name: entry.reason for entry in resolution.trace}
    assert "subject exclusion" in reasons["claude-opus-5-5"]
    # D-129 (#10464): no Claude model reviews through Cursor, so no such trace row exists.
    assert not any(entry.family == "anthropic" and entry.transport == "cursor" for entry in resolution.trace)


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


def test_explicit_subjects_and_ambiguous_shared_hooks(repo, tasks, monkeypatch, tmp_path):
    repo.commit(OPUS)
    assert selected(facts(repo, tasks, writer=OPUS, seats=("codex", "grok")), "critical") is None
    unknown = facts(repo, tasks, writer=OPUS, owned=(SHARED_HOOK,))
    assert unknown.subject_seats == unknown.subject_families == frozenset()
    assert unknown.subject_evidence == ()
    assert selected(unknown, "critical") is not None
    named = facts(repo, tasks, writer=OPUS, owned=(SHARED_HOOK,), seats=("claude",))
    assert named.subject_seats == {"claude"}
    known = facts(repo, tasks, writer=OPUS, owned=(SHARED_HOOK, CLAUDE_ADAPTER), families=("meta",))
    assert known.subject_seats == {"claude"}
    assert known.subject_families == {"meta"}
    assert known.subject_evidence == (CLAUDE_ADAPTER,)

    repo.commit(OPUS, path=SHARED_HOOK)
    repo.publish()
    receipt = record_verdict(monkeypatch, tmp_path, repo, agent="codex", model="gpt-6.1-sol", review_risk="critical")
    assert receipt["verdict"] == "APPROVED"
    with pytest.raises(recorder.RecordError, match="equals an author family"):
        record_verdict(monkeypatch, tmp_path, repo, agent="claude", model="claude-opus-5-5", review_risk="critical")

    muse = "scripts/agent_runtime/adapters/muse.py"
    repo.commit(OPUS, path=muse)
    repo.publish()
    inferred = facts(repo, tasks, writer=OPUS)
    assert inferred.subject_seats == {"muse"}
    assert inferred.subject_families == frozenset()
    assert inferred.subject_evidence == (muse,)
    receipt = record_verdict(
        monkeypatch, tmp_path, repo, agent="codex", model="gpt-6.1-sol", review_risk="critical", _task_id="review-muse"
    )
    assert receipt["verdict"] == "APPROVED"


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
        ("duplicate-trailer", "3 X-Agent trailers: member 3 malformed"),
        ("repository-mismatch", "conflicts with commit trailer"),
        ("unproven-merge", "missing explicit X-Agent"),
    ],
)
def test_invalid_attribution_is_never_green(repo, tasks, case, reason):
    repo.commit(OPUS)
    if case == "missing-trailer":
        repo.commit(None)
    elif case == "duplicate-trailer":
        repo.commit(f"{OPUS}\nX-Agent: {SOL}\nX-Agent: ")
    elif case == "repository-mismatch":
        task_record(tasks, "elsewhere", agent="codex", model="gpt-6.1-sol", repository="other/repo")
        repo.commit("codex/elsewhere")
    else:
        repo.git("checkout", "-q", "-b", "side", "origin/main")
        repo.commit(SOL, path="src/app.py")
        repo.git("checkout", "-q", "feature")
        # A clean merge of the PR's own commits is exempt; a hand edit is not.
        repo.git("merge", "-q", "--no-ff", "--no-commit", "side")
        (repo.root / "docs/hand-edit.md").write_text("authored during the merge\n", encoding="utf-8")
        repo.git("add", "-A")
        repo.git("commit", "-q", "-m", "merge a non-base branch")
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


# Frozen held-out groups for #10450. No fixture reaches a provider.


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


# --- 5b / A3: dry-run evaluation and a head that moves after admission -----------------------------


# --- A7: the endpoints admission freezes are the ones the recorder and creation use ----------------

CODEX_ADAPTER = "scripts/agent_runtime/adapters/codex.py"


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


# --- round 6: admission evaluates the commits a reused checkout actually ends up with ----------------


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


def test_pr_review_facts_drop_a_main_squash_merged_onto_a_stale_base(repo, tasks, monkeypatch):
    repo.git("symbolic-ref", "refs/remotes/origin/HEAD", "refs/remotes/origin/main")
    stale = repo.sha("origin/main")
    own = repo.commit(OPUS, message="branch author")
    repo.git("checkout", "-q", "trunk")
    squash = repo.commit(f"{OPUS}\nX-Agent: {SOL}", path="src/app.py", message="main squash")
    repo.publish("trunk", to="main")
    repo.git("checkout", "-q", "feature")
    repo.git("merge", "-q", "--no-ff", "origin/main", "-m", "sync base")
    head = repo.sha("HEAD")
    listing = github_listing(repo, stale, head)
    assert squash in {entry["sha"] for entry in listing}

    monkeypatch.setattr(
        recorder,
        "_run_json",
        lambda _args, **_kwargs: {"baseRefName": "main", "baseRefOid": stale, "headRefOid": head},
    )
    monkeypatch.setattr(recorder, "_pages", lambda _request: listing)
    facts = recorder.pr_review_facts(REPOSITORY, 42, head_sha=head, task_root=tasks, repo_root=repo.root)
    assert facts.existing_families == {"anthropic"}
    shas = {commit.sha for commit in facts.commits}
    assert own in shas and squash not in shas

    monkeypatch.setattr(
        recorder,
        "_run_json",
        lambda _args, **_kwargs: {"baseRefName": "release", "baseRefOid": stale, "headRefOid": head},
    )
    # The PR's base is never read (C-2902 F6): a retargeted PR keeps the default-branch range.
    release = recorder.pr_review_facts(REPOSITORY, 42, head_sha=head, task_root=tasks, repo_root=repo.root)
    assert release.commits == facts.commits and release.existing_families == {"anthropic"}


def _assert_admits_a_reviewer_outside(fact):
    resolution = recorder.structural_review_route(fact, risk="medium", claude_account=HOST_ACCOUNT)
    assert resolution.fail_closed_reason is None
    assert resolution.selected is not None
    assert resolution.selected.family != fact.incoming_family


def _merge_main_onto_a_branch_with_no_commit(repo):
    """No-ff merge of a newer default-branch tip onto a branch that has not authored a commit."""
    base = repo.sha("origin/main")
    repo.git("checkout", "-q", "trunk")
    squash = repo.commit(f"{OPUS}\nX-Agent: {SOL}", path="src/app.py", message="main squash")
    repo.publish("trunk", to="main")
    repo.git("checkout", "-q", "feature")
    repo.git("merge", "-q", "--no-ff", "origin/main", "-m", "sync base")
    return base, squash


def test_clean_base_merge_still_admits_the_incoming_writer(repo, tasks):
    """A known writer is admitted after a clean base merge, as on a fast-forward."""
    base, squash = _merge_main_onto_a_branch_with_no_commit(repo)
    common = {
        "repository": REPOSITORY,
        "repo_root": repo.root,
        "base_tip_sha": base,
        "task_root": tasks,
        "incoming_agent": "claude",
        "incoming_model": "claude-opus-5-5",
        "authorship_exclude_sha": squash,
    }
    admitted = recorder.collect_branch_review_facts(**common, head_sha=repo.sha("HEAD"))
    assert admitted.existing_families == set()
    assert admitted.incoming_family == "anthropic"
    assert admitted.incoming_writer == "claude/claude-opus-5-5"
    assert admitted.commits
    assert all(commit.family is None for commit in admitted.commits)
    assert squash not in {commit.sha for commit in admitted.commits}
    _assert_admits_a_reviewer_outside(admitted)

    forwarded = recorder.collect_branch_review_facts(**common, head_sha=squash)
    assert forwarded.commits == ()
    assert forwarded.existing_families == set()
    assert forwarded.incoming_family == admitted.incoming_family
    _assert_admits_a_reviewer_outside(forwarded)


def test_a_main_merge_with_no_branch_commit_still_refuses(repo, tasks, monkeypatch):
    base, squash = _merge_main_onto_a_branch_with_no_commit(repo)
    head = repo.sha("HEAD")
    facts = recorder.collect_branch_review_facts(
        repository=REPOSITORY,
        repo_root=repo.root,
        base_tip_sha=base,
        head_sha=head,
        task_root=tasks,
        authorship_exclude_sha=squash,
    )
    with pytest.raises(recorder.BranchFactsError, match="missing explicit X-Agent") as refused:
        recorder.refuse_excluded_only_range(facts, repo_root=repo.root, exclude_sha=squash)
    assert refused.value.code == recorder.FACTS_AUTHORSHIP_UNKNOWN

    repo.git("symbolic-ref", "refs/remotes/origin/HEAD", "refs/remotes/origin/main")
    monkeypatch.setattr(
        recorder,
        "_run_json",
        lambda _args, **_kwargs: {"baseRefName": "main", "baseRefOid": base, "headRefOid": head},
    )
    monkeypatch.setattr(recorder, "_pages", lambda _request: github_listing(repo, base, head))
    with pytest.raises(recorder.BranchFactsError, match="missing explicit X-Agent"):
        recorder.pr_review_facts(REPOSITORY, 42, head_sha=head, task_root=tasks, repo_root=repo.root)


def test_github_sha_filter_uses_one_bounded_enumeration(repo, monkeypatch):
    base = repo.sha("HEAD")
    own = repo.commit(OPUS, message="branch author")
    repo.git("checkout", "-q", "trunk")
    later = repo.commit(SOL, path="src/app.py", message="later main")
    calls: list[tuple] = []
    real = recorder._facts_git

    def spy(repo_root, args, **kwargs):
        calls.append((args, kwargs.get("deadline"), kwargs.get("input_bytes")))
        return real(repo_root, args, **kwargs)

    monkeypatch.setattr(recorder, "_facts_git", spy)
    assert recorder._shas_not_reachable_from(repo.root, [own, "not-a-sha"], None) == [own, "not-a-sha"]
    assert calls == []

    kept = recorder._shas_not_reachable_from(repo.root, [base, own, later, "not-a-sha", later], later)
    assert len(calls) == 1
    args, deadline, payload = calls[0]
    assert args == ["rev-list", "--no-walk", "--stdin"]
    assert deadline is not None
    assert payload == f"{base}\n{own}\n{later}\n{later}\n^{later}\n".encode("ascii")
    assert kept == [own, "not-a-sha"]

    def timed_out(repo_root, args, **kwargs):
        raise recorder.BranchFactsError(recorder.FACTS_AUTHORSHIP_UNKNOWN, "git rev-list timed out", timed_out=True)

    monkeypatch.setattr(recorder, "_facts_git", timed_out)
    with pytest.raises(recorder.BranchFactsError, match="timed out") as refused:
        recorder._shas_not_reachable_from(repo.root, [own, base], later)
    assert refused.value.timed_out


@pytest.mark.parametrize(
    "spelling",
    ["main", "origin/main", "remotes/origin/main", "refs/remotes/origin/main", "refs/heads/main"],
)
def test_authorship_exclude_sha_is_the_default_tip_only(repo, spelling):
    assert recorder.authorship_exclude_sha(repo.root, base_branch="origin/main") is None
    repo.git("symbolic-ref", "refs/remotes/origin/HEAD", "refs/remotes/origin/main")
    tip = repo.sha("origin/main")
    assert recorder.authorship_exclude_sha(repo.root, base_branch=spelling) == tip
    assert recorder.authorship_exclude_sha(repo.root, base_branch="release") is None
    assert recorder.authorship_exclude_sha(repo.root, base_branch="refs/remotes/origin/release") is None
    assert recorder.authorship_exclude_sha(repo.root, base_branch="refs/heads/release") is None
    assert recorder.authorship_exclude_sha(repo.root, base_branch=None) is None


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


def test_closeout_unknown_history_preview_preserves_default_refusal(repo, tasks, tmp_path):
    historical = repo.commit(None, message="historical conflict resolution")
    repo.commit(SOL, message="validated current author")
    state = tmp_path / "resolution.json"
    from scripts.review.closeout_cli import main

    assert (
        main(
            [
                "--state-file",
                str(state),
                "target",
                "--mode",
                "branch",
                "--branch",
                "feature",
                "--base",
                "origin/main",
                "--repo-root",
                str(repo.root),
            ]
        )
        == 0
    )
    args = [
        "--state-file",
        str(state),
        "resolve-reviewer",
        "--author-model",
        "gpt-6.1-sol",
        "--repository",
        REPOSITORY,
        "--task-root",
        str(tasks),
        "--risk",
        "critical",
    ]
    assert main(args) == 1
    refusal = json.loads(state.read_text())["resolved_reviewer"]
    assert refusal["selected"] is None
    assert (
        f"commit {historical[:12]}: author model unknown: missing explicit X-Agent model trailer"
        in refusal["fail_closed_reason"]
    )
    assert main([*args, "--review-mode", "red_team"]) == 0
    resolved = json.loads(state.read_text())["resolved_reviewer"]
    assert resolved["selected"]["concrete_model"] == "claude-opus-5-5"
    assert resolved["review_mode"] == "red_team" and resolved["limitation"]
    facts = resolved["branch_facts"]
    assert facts["unknown_history"] == [historical]
    assert {"anthropic", "openai", "google", "xai"} <= set(facts["excluded_families"])
    assert not list(tasks.glob("*.json"))


# --- verified app-bot authorship (#10531) --------------------------------------------------------
#
# Denominator: agent trailer; human without trailer; Dependabot without trailer; a human commit claiming
# to be Dependabot; a bot commit followed by a human commit; a forged bot field in local data; GitHub
# unreachable. Only GitHub's live commit data for the exact SHA proves a bot.

DEPENDABOT_EMAIL = "49699333+dependabot[bot]@users.noreply.github.com"
BUMP = "Bump actions/checkout from 4 to 5"


def github_commit(
    sha: str,
    *,
    login: str = "dependabot[bot]",
    account_id: int = 49699333,
    kind: str = "Bot",
    name: str = "dependabot[bot]",
    email: str = DEPENDABOT_EMAIL,
    committer: str = "web-flow",
    verified: bool = True,
) -> dict:
    """GitHub's REST commit object for ``sha``; the defaults are a real Dependabot commit's fields."""
    return {
        "sha": sha,
        "url": f"https://api.github.com/repos/{REPOSITORY}/commits/{sha}",
        "html_url": f"https://github.com/{REPOSITORY}/commit/{sha}",
        "author": {"login": login, "id": account_id, "type": kind},
        "committer": {"login": committer, "id": 19864447, "type": "User"},
        "commit": {
            "url": f"https://api.github.com/repos/{REPOSITORY}/git/commits/{sha}",
            "author": {"name": name, "email": email},
            "committer": {"name": "GitHub", "email": "noreply@github.com"},
            "verification": {"verified": verified, "reason": "valid" if verified else "unsigned"},
        },
    }


def human_commit(sha: str) -> dict:
    return github_commit(
        sha, login="maintainer", account_id=7, kind="User", name="maintainer", email="maintainer@example.invalid"
    )


def serve_github_commits(monkeypatch, commits: dict[str, dict] | None) -> list[str]:
    """Answer the recorder's live single-commit reads from ``commits``; None makes GitHub unreachable.

    Returns the SHAs read, in order.
    """
    from scripts.publish.github import Request

    requested: list[str] = []
    original = recorder._run_json

    def fake(args, *, input_text=None):
        if isinstance(args, Request) and args.verb == "read-commit":
            assert args.fields["repo"] == REPOSITORY
            requested.append(args.fields["sha"])
            if commits is None or args.fields["sha"] not in commits:
                raise recorder.RecordError("GitHub lookup or publication unavailable")
            return commits[args.fields["sha"]]
        return original(args, input_text=input_text)

    monkeypatch.setattr(recorder, "_run_json", fake)
    return requested


def test_agent_trailer_never_consults_github(repo, tasks, monkeypatch):
    repo.commit(OPUS)
    requested = serve_github_commits(monkeypatch, {})
    fact = facts(repo, tasks)
    assert [commit.source for commit in fact.commits] == ["trailer-model"]
    assert fact.existing_families == {"anthropic"} and fact.app_bot_commits == ()
    assert requested == []


def test_forged_bot_field_in_local_data_is_never_proof(repo, tasks, monkeypatch, tmp_path):
    head = repo.commit(None, message=BUMP)
    repo.publish()
    forged = {**github_commit(head), "is_bot": True}
    # A local cache beside the task records, and the commit entry itself, both claim the bot.
    (tasks / f"{head}.json").write_text(json.dumps(forged), encoding="utf-8")
    (tasks / "github-commit-cache.json").write_text(json.dumps({head: forged}), encoding="utf-8")
    serve_github_commits(monkeypatch, {head: human_commit(head)})
    with pytest.raises(recorder.BranchFactsError, match="missing explicit X-Agent"):
        facts(repo, tasks)
    entry = {**forged, "commit": {**forged["commit"], "message": f"{BUMP}\n", "tree": {"sha": "0" * 40}}}
    with pytest.raises(recorder.RecordError, match="missing explicit X-Agent"):
        recorder._attribute_commit(
            entry,
            repository=REPOSITORY,
            task_root=tasks,
            base_sha=lambda: repo.sha("origin/main"),
            app_bot_login=lambda _sha: None,
        )
    # A GitHub listing whose entry carries only a bot flag proves nothing either.
    listing = github_listing(repo, repo.sha("origin/main"), head)
    listing[0].update({"author": {"login": "dependabot[bot]", "is_bot": True}})
    with pytest.raises(recorder.RecordError, match="missing explicit X-Agent"):
        record_verdict(monkeypatch, tmp_path, repo, agent="codex", model="gpt-6.1-sol", listing=listing)


def test_github_unreachable_fails_closed(repo, tasks, monkeypatch, tmp_path):
    head = repo.commit(None, message=BUMP)
    repo.publish()
    requested = serve_github_commits(monkeypatch, None)
    with pytest.raises(recorder.BranchFactsError, match="missing explicit X-Agent"):
        facts(repo, tasks)
    assert requested == [head]
    # The recorder's PR listing without author data (GitHub returned no proof) refuses too.
    with pytest.raises(recorder.RecordError, match="missing explicit X-Agent"):
        record_verdict(monkeypatch, tmp_path, repo, agent="codex", model="gpt-6.1-sol")


def listing_with_authors(repo: MiniRepo, authors: dict[str, dict]) -> list[dict]:
    """GitHub's live PR commit listing, carrying each listed commit's GitHub author data."""
    listing = github_listing(repo, repo.sha("origin/main"), repo.sha("feature"))
    for entry in listing:
        github = authors.get(entry["sha"], {})
        entry.update({key: github[key] for key in ("author", "committer", "url", "html_url") if key in github})
        entry["commit"].update({key: value for key, value in github.get("commit", {}).items()})
    return listing


def test_verified_dependabot_branch_is_attributed_reviewed_and_recorded_without_a_model(
    repo, tasks, monkeypatch, tmp_path
):
    head = repo.commit(None, message=BUMP)
    repo.publish()
    requested = serve_github_commits(monkeypatch, {head: github_commit(head)})

    fact = facts(repo, tasks)

    assert requested == [head]
    (commit,) = fact.commits
    assert (commit.sha, commit.source, commit.authorship) == (head, "verified_app_bot", "verified_app_bot")
    assert commit.author_models == () and commit.task_id is None
    assert fact.existing_families == {"verified_app_bot"} and fact.app_bot_commits == (head,)
    assert fact.receipt()["app_bot_commits"] == [head] and "authorship" not in fact.receipt()
    # A bot has no model and no model family: no reviewer family is excluded, the risk floor still binds.
    inputs = fact.resolver_inputs(risk="critical", claude_account=HOST_ACCOUNT)
    assert inputs.author_models == ()
    trace = {
        entry.name: entry
        for entry in recorder.structural_review_route(fact, risk="critical", claude_account=HOST_ACCOUNT).trace
    }
    assert {trace["claude-opus-5-5"].status, trace["openai_frontier"].status} <= {"selected", "eligible"}
    assert "same family" not in " ".join(str(entry.reason) for entry in trace.values())
    assert selected(fact, "critical") is not None

    listing = listing_with_authors(repo, {head: github_commit(head)})
    for agent, model in (("codex", "gpt-6.1-sol"), ("claude", "claude-opus-5-5")):
        posted: list[dict] = []
        receipt = record_verdict(
            monkeypatch,
            tmp_path,
            repo,
            agent=agent,
            model=model,
            review_risk="critical",
            listing=listing,
            comments=posted,
        )
        assert receipt["verdict"] == "APPROVED" and receipt["head"] == head
        assert receipt["authorship"] == "verified_app_bot" and receipt["app_bot_commits"] == [head]
        body = posted[0]["body"]
        family = recorder.resolve_family(model)
        assert body.rstrip().endswith(f"model={model} family={family} authorship=verified_app_bot -->")
        assert "Authorship: verified_app_bot\nNo author model assumed.\n" in body
        marker = recorder.parse_marker(body)
        assert marker["authorship"] == "verified_app_bot" and marker["model"] == model
        # The unchanged head's marker is consumed again rather than re-posted.
        again = record_verdict(
            monkeypatch,
            tmp_path,
            repo,
            agent=agent,
            model=model,
            review_risk="critical",
            listing=listing,
            comments=posted,
        )
        assert again["comment"] == "existing" and len(posted) == 1
    # The risk floor and qualification still apply to a bot-authored head.
    with pytest.raises(recorder.RecordError, match="not qualified"):
        record_verdict(
            monkeypatch,
            tmp_path,
            repo,
            agent="claude",
            model="claude-sonnet-5-5",
            review_risk="critical",
            listing=listing,
        )


def test_human_commit_without_trailer_keeps_its_refusal(repo, tasks, monkeypatch, tmp_path):
    head = repo.commit(None)
    repo.publish()
    requested = serve_github_commits(monkeypatch, {head: human_commit(head)})
    with pytest.raises(recorder.BranchFactsError, match="missing explicit X-Agent") as refused:
        facts(repo, tasks)
    assert refused.value.code == recorder.FACTS_AUTHORSHIP_UNKNOWN and requested == [head]
    listing = listing_with_authors(repo, {head: human_commit(head)})
    with pytest.raises(recorder.RecordError, match="missing explicit X-Agent"):
        record_verdict(monkeypatch, tmp_path, repo, agent="codex", model="gpt-6.1-sol", listing=listing)


@pytest.mark.parametrize(
    "github",
    [
        pytest.param({}, id="github-reports-the-human"),
        pytest.param({"committer": "maintainer", "verified": False}, id="spoofed-email-pushed-from-a-checkout"),
        pytest.param({"committer": "maintainer"}, id="signed-by-the-human-not-github"),
        pytest.param({"verified": False}, id="unsigned"),
        pytest.param({"kind": "User"}, id="user-account-type"),
        pytest.param({"account_id": 1}, id="other-account-id"),
        pytest.param({"login": "dependabot-preview[bot]"}, id="login-off-allowlist"),
        pytest.param({"name": "Dependabot"}, id="author-name-mismatch"),
        pytest.param({"email": "dependabot@example.invalid"}, id="author-email-mismatch"),
    ],
)
def test_human_commit_claiming_to_be_dependabot_keeps_its_refusal(repo, tasks, monkeypatch, tmp_path, github):
    """The message and the local Git identity both claim Dependabot; only GitHub's full proof could attribute it."""
    (repo.root / "docs/a.md").write_text("bumped\n", encoding="utf-8")
    repo.git("add", "-A")
    repo.git(
        "-c",
        "user.name=dependabot[bot]",
        "-c",
        f"user.email={DEPENDABOT_EMAIL}",
        "commit",
        "-q",
        "-m",
        f"{BUMP}\n\nSigned-off-by: dependabot[bot] <{DEPENDABOT_EMAIL}>\n",
    )
    head = repo.sha("HEAD")
    repo.publish()
    data = human_commit(head) if not github else github_commit(head, **github)
    requested = serve_github_commits(monkeypatch, {head: data})
    with pytest.raises(recorder.BranchFactsError, match="missing explicit X-Agent"):
        facts(repo, tasks)
    # Refused because GitHub's live data for this SHA proves no bot, never because it went unchecked.
    assert requested == [head]
    with pytest.raises(recorder.RecordError, match="missing explicit X-Agent"):
        record_verdict(
            monkeypatch,
            tmp_path,
            repo,
            agent="codex",
            model="gpt-6.1-sol",
            listing=listing_with_authors(repo, {head: data}),
        )


def test_bot_commit_then_human_commit_applies_the_human_rule(repo, tasks, monkeypatch, tmp_path):
    bot = repo.commit(None, message=BUMP)
    human = repo.commit(None, path="src/app.py", message="fix the workflow")
    repo.publish()
    authors = {bot: github_commit(bot), human: human_commit(human)}
    requested = serve_github_commits(monkeypatch, authors)
    with pytest.raises(recorder.BranchFactsError, match=f"commit {human[:12]}: author model unknown"):
        facts(repo, tasks)
    assert human in requested
    with pytest.raises(recorder.RecordError, match="missing explicit X-Agent"):
        record_verdict(
            monkeypatch, tmp_path, repo, agent="codex", model="gpt-6.1-sol", listing=listing_with_authors(repo, authors)
        )


def test_bot_commit_then_agent_commit_keeps_the_agent_family(repo, tasks, monkeypatch, tmp_path):
    bot = repo.commit(None, message=BUMP)
    repo.commit(OPUS, path="src/app.py", message="fix the workflow")
    repo.publish()
    serve_github_commits(monkeypatch, {bot: github_commit(bot)})
    fact = facts(repo, tasks)
    assert {commit.source for commit in fact.commits} == {"verified_app_bot", "trailer-model"}
    assert fact.existing_families == {"verified_app_bot", "anthropic"} and fact.app_bot_commits == (bot,)
    assert selected(fact, "critical") == "openai_frontier"
    listing = listing_with_authors(repo, {bot: github_commit(bot)})
    with pytest.raises(recorder.RecordError, match="equals an author family"):
        record_verdict(monkeypatch, tmp_path, repo, agent="claude", model="claude-opus-5-5", listing=listing)
    receipt = record_verdict(monkeypatch, tmp_path, repo, agent="codex", model="gpt-6.1-sol", listing=listing)
    assert receipt["verdict"] == "APPROVED" and receipt["app_bot_commits"] == [bot]
