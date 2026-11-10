"""Offline execution of shared memory's branch-before-PR review example (#10065)."""

from __future__ import annotations

import json
import os
import re
import shlex
import subprocess
from pathlib import Path

import pytest
from lu_machinery.dispatcher import cli as dispatch_cli
from lu_machinery.dispatcher import git as dispatch_git
from lu_machinery.review import record_cf_verdict as recorder

# Product fixtures retained from the machinery test consumers (C-5048).
_authoring_SOL = "codex/gpt-6.1-sol"


def _authoring_run_git(*args: str, cwd: Path | None = None, env: dict | None = None, stdin: str | None = None) -> str:
    proc = subprocess.run(
        ["git", *args], cwd=cwd, env=env, input=stdin, capture_output=True, text=True, check=True, timeout=30
    )
    return proc.stdout.strip()


class _authoring_MiniRepo:
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
        _authoring_run_git(
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
        return _authoring_run_git("--git-dir", str(remote or self.remote), "rev-parse", f"refs/heads/{branch}")

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
        parent = _authoring_run_git("--git-dir", bare, "rev-parse", f"refs/heads/{branch}")
        _authoring_run_git("--git-dir", bare, "read-tree", parent, env=env)
        blob = _authoring_run_git("--git-dir", bare, "hash-object", "-w", "--stdin", stdin=f"remote {trailer}\n")
        _authoring_run_git("--git-dir", bare, "update-index", "--add", "--cacheinfo", f"100644,{blob},{path}", env=env)
        tree = _authoring_run_git("--git-dir", bare, "write-tree", env=env)
        message = f"remote {branch}\n\nX-Agent: {trailer}\n"
        head = _authoring_run_git("--git-dir", bare, "commit-tree", tree, "-p", parent, "-m", message, env=env)
        _authoring_run_git("--git-dir", bare, "update-ref", f"refs/heads/{branch}", head, parent)
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


_authoring_REPOSITORY = "learn-ukrainian/learn-ukrainian.github.io"

_authoring_CANONICAL_URL = f"https://github.com/{_authoring_REPOSITORY}.git"

_authoring_CLAUDE_ADAPTER = "lu_machinery/agent_runtime/adapters/claude.py"

_authoring_SHARED_HOOK = "agents_extensions/shared/hooks/guard-reviewer-publish.py"


def _authoring_bare_remote(path: Path, *, default_branch: str = "main") -> Path:
    _authoring_run_git("init", "-q", "--bare", str(path))
    _authoring_run_git("--git-dir", str(path), "symbolic-ref", "HEAD", f"refs/heads/{default_branch}")
    return path


_authoring_OPUS = "claude/claude-opus-5-5"


def _authoring_mini_repo(tmp_path: Path, monkeypatch, *, default_branch: str = "main") -> _authoring_MiniRepo:
    """A repository at ``<tmp_path>/primary`` on branch ``feature``, forked from ``origin/<default_branch>``."""
    for key in list(os.environ):
        if key.startswith("GIT_"):
            monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", os.devnull)
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    root = tmp_path / "primary"
    root.mkdir()
    mini = _authoring_MiniRepo(root, _authoring_bare_remote(tmp_path / "canonical.git", default_branch=default_branch))
    mini.git("init", "-q", "-b", "trunk")
    mini.git("config", "user.name", "Fixture")
    mini.git("config", "user.email", "fixture@example.invalid")
    mini.git("config", "core.hooksPath", os.devnull)
    mini.git("remote", "add", "origin", _authoring_CANONICAL_URL)
    mini.git("config", f"url.{mini.remote}.insteadOf", _authoring_CANONICAL_URL)
    for path in ("docs/a.md", "src/app.py", _authoring_CLAUDE_ADAPTER, _authoring_SHARED_HOOK):
        (root / path).parent.mkdir(parents=True, exist_ok=True)
        (root / path).write_text(f"base {path}\n", encoding="utf-8")
    (root / ".gitignore").write_text(".worktrees/\n", encoding="utf-8")
    mini.git("add", "-A")
    mini.git("commit", "-q", "-m", f"base\n\nX-Agent: {_authoring_OPUS}\n")
    mini.publish("trunk", to=default_branch)
    mini.git("checkout", "-q", "-b", "feature")
    return mini


SOL = _authoring_SOL
mini_repo = _authoring_mini_repo

MEMORY = Path(__file__).resolve().parents[1] / "agents_extensions/shared/memory/MEMORY.md"


def _review_section():
    body = MEMORY.read_text(encoding="utf-8")
    return body.split("## #0H —", 1)[1].split("\n## ", 1)[0]


@pytest.mark.parametrize("moved_head", [False, True], ids=["pushed-head", "remote-drift"])
def test_documented_ask_reaches_native_branch_pin_admission(monkeypatch, tmp_path, moved_head):
    """The documented v2 command pins a local Git object even when its remote moves."""
    repo = mini_repo(tmp_path, monkeypatch)
    head = repo.commit(SOL)
    repo.publish()
    recipe = re.search(r"`(printf .*?-m lu_machinery\.dispatch dispatch.*?)`", _review_section())
    assert recipe is not None
    tokens = shlex.split(recipe.group(1))
    pipe = tokens.index("|")
    assert tokens[:2] == ["printf", "%s\\n"] and pipe == 3
    replacements = {
        "<branch>": "feature", "<SHA>": head, "<lane>": "claude",
        "<id>": "fixture", "<resolved-model>": "claude-opus-5-5",
    }
    for old, new in replacements.items():
        tokens = [token.replace(old, new) for token in tokens]
    assert tokens[pipe + 1:pipe + 4] == [".venv/bin/python", "-m", "lu_machinery.dispatch"]
    args = dispatch_cli.build_parser().parse_args(tokens[pipe + 4:])
    assert args.command == "dispatch" and args.agent == "claude"
    assert args.branch == "feature" and args.pr is None
    assert args.model == "claude-opus-5-5" and args.effort == "high"
    assert args.mode == "read-only" and args.worktree == ""
    assert args.prompt_file == "-" and args.require_review_verdict
    assert args.pinned_head == head
    if moved_head:
        assert repo.advance_remote("feature", SOL) != head
    worktree, branch, base = dispatch_git.worktree_plan(
        repo.root, args.agent, args.task_id, args.pinned_head
    )
    assert base == head
    assert branch == "claude/review-fixture"
    assert worktree == repo.root / ".worktrees/dispatch/claude/review-fixture"


def test_documented_recorder_uses_completed_review_task_and_pr(monkeypatch, capsys):
    """Parse the publication example at the existing recorder's external boundary."""
    recipe = re.search(r"`([^`]*-m lu_machinery\.review\.record_cf_verdict.*?)`", _review_section())
    assert recipe is not None
    argv = shlex.split(recipe.group(1).replace("<id>", "fixture").replace("<N>", "7"))
    calls = []

    def publication_boundary(task_id, **kwargs):
        calls.append((task_id, kwargs))
        return {"status": "posted"}

    monkeypatch.setattr(recorder, "record", publication_boundary)
    assert recorder.main(argv[3:]) == 0
    assert calls == [("review-fixture", {"pr_number": 7, "review_mode": None, "red_team_prompt": None})]
    assert json.loads(capsys.readouterr().out) == {"status": "posted"}
