"""Ports of tests/test_authoring_review_feasibility.py to dispatch v2.

Each test retains its legacy name and assertions. The boundary uses the v2
CLI and substitutes only the launch/worktree side effects.
"""
from __future__ import annotations

import json
import os
import subprocess
from contextlib import contextmanager
from pathlib import Path

import pytest

from scripts.dispatcher import authoring as delegate
from scripts.dispatcher import checks, cli, git, worker
from scripts.review import record_cf_verdict as recorder
from scripts.review.model_catalog import ModelCatalogError
from tests.claude_route_accounts import HOST_ACCOUNT

REPOSITORY = "learn-ukrainian/learn-ukrainian.github.io"
CLAUDE_ADAPTER = "scripts/agent_runtime/adapters/claude.py"
CODEX_ADAPTER = "scripts/agent_runtime/adapters/codex.py"
SHARED_HOOK = "agents_extensions/shared/hooks/guard-reviewer-publish.py"
GROK_ADAPTER = "scripts/agent_runtime/adapters/grok_build.py"
OPUS = "claude/claude-opus-5-5"
SOL = "codex/gpt-6.1-sol"
GROK = "grok/grok-4.7"
CANONICAL_URL = f"https://github.com/{REPOSITORY}.git"
MIRROR_URL = "https://mirror.invalid/learn-ukrainian.git"
BASE_SHA = "b" * 40
DEFAULT_TIP = ("main", "a" * 40)

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


@pytest.fixture(autouse=True)
def recorder_matcher(synthetic_opsec):
    from tests.opsec_fixtures import synthetic_rules

    rules = synthetic_rules(rule="3-absolute-path", level=3, pattern=r"(?<![<\w:])/[A-Za-z][^\s`'\"<>),;\]}|*]*")
    (synthetic_opsec / "rules.json").write_text(json.dumps(rules))


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


def review_base(*, pr: int | None = None, head: str = "feature"):
    return delegate._authoring_review_base(REPOSITORY, pr=pr, head_branch=head, default_branch=lambda: DEFAULT_TIP)


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


@pytest.fixture
def boundary(repo, tasks, monkeypatch, github):
    """Legacy side-effect tripwires adapted to cli.main."""
    monkeypatch.setattr(delegate, '_REPO_ROOT', repo.root)
    monkeypatch.chdir(repo.root)
    monkeypatch.setattr(git, 'resolve_repo', lambda _: (repo.root, dict(
        key='public', github=REPOSITORY, default=True)))
    monkeypatch.setattr(checks, 'check_resources', lambda _: None)
    calls = []

    def tripwire(name):
        def fire(*args, **kwargs):
            calls.append(name)
            raise AssertionError(f'{name} ran for a refused dispatch')
        return fire

    monkeypatch.setattr(git, 'create_worktree', tripwire('worktree creation'))
    monkeypatch.setattr(worker, 'start', tripwire('provider launch'))

    def dispatch(*extra, writer=OPUS, mode='workspace-write', task_id='writer-1'):
        agent, _, model = writer.partition('/')
        argv = ['dispatch', '--agent', agent, '--model', model, '--task-id', task_id,
                '--initiator', 'claude', '--mode', mode, '--prompt', 'Implement the change.', *extra]
        before = repo.snapshot()
        return cli.main(argv), before

    dispatch.calls = calls
    return dispatch


@contextmanager
def _admitted_host(monkeypatch, on_admission=None):
    # This is v2's post-admission, pre-lock observation boundary.
    def resources(_):
        if on_admission is not None:
            on_admission()
    monkeypatch.setattr(checks, 'check_resources', resources)
    yield


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


@pytest.mark.parametrize("mode", [(), ("--dry-run",)], ids=["dispatch", "dry-run"])
def test_a_creation_base_that_moves_after_admission_refuses_as_moved(boundary, capsys, repo, tasks, monkeypatch, mode):
    """A7 §3: the commit a new branch starts at is frozen at admission; a different one before use is a move."""
    admitted = repo.publish("trunk", to="custom")
    with _admitted_host(monkeypatch, on_admission=lambda: repo.advance_remote("custom", OPUS)):
        rc, before = boundary("--worktree", "--base", "custom", "--owned-path", CODEX_ADAPTER, *mode, writer=SOL)
    receipt = assert_moved_refusal(rc, capsys, tasks)
    assert (receipt["binding"], receipt["admitted_sha"]) == ("creation", admitted)
    assert receipt["current_sha"] == repo.remote_sha("custom") != admitted
    assert boundary.calls == [] and repo.snapshot() == before


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
