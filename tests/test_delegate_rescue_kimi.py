"""#9878: ``delegate.py rescue`` preserves a terminal Kimi task's work past its worktree push block.

Real git: a primary repository with a bare ``origin``, and one linked Kimi
dispatch worktree carrying the boundary ``kimi_boundary.install`` sets up.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import delegate
from scripts.agent_runtime import kimi_boundary
from tests.test_delegate import (  # noqa: F401
    _fixture_worktree_lock_dir,
    _keep_delegate_unit_tests_local,
    _sanitize_git_env_for_test,
    tmp_tasks_dir,
)

pytestmark = pytest.mark.usefixtures("tmp_tasks_dir")

TASK_ID = "kimi-rescue"
BRANCH = f"kimi/{TASK_ID}"
RESCUE_REF = f"rescue/kimi/{delegate._x_agent_task_id('kimi', TASK_ID)}"
OWNED = "site/src/components/"
LABEL = "site/src/components/Label.tsx"


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True, timeout=60).stdout


def _git_proc(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=repo, check=False, capture_output=True, text=True, timeout=60)


def _remote_heads(origin: Path) -> dict[str, str]:
    lines = _git(origin, "for-each-ref", "--format=%(refname:short) %(objectname)", "refs/heads").splitlines()
    return dict(line.split(" ", 1) for line in lines)


@pytest.fixture
def kimi_rescue(tmp_path, monkeypatch):
    """A failed Kimi task whose worktree holds the boundary; ``write(text, commit=...)`` leaves its work."""
    from scripts.orchestration import reap_worktrees

    _sanitize_git_env_for_test(monkeypatch)
    primary = tmp_path / "primary"
    origin = tmp_path / "origin.git"
    _git(tmp_path, "init", "--bare", "--initial-branch=main", str(origin))
    _git(tmp_path, "init", "--initial-branch=main", str(primary))
    for key, value in (("user.email", "test@example.com"), ("user.name", "test"), ("commit.gpgsign", "false")):
        _git(primary, "config", key, value)
    (primary / "README.md").write_text("base\n", encoding="utf-8")
    _git(primary, "add", "-A")
    _git(primary, "commit", "-m", "base")
    _git(primary, "remote", "add", "origin", str(origin))
    _git(primary, "push", "origin", "HEAD:refs/heads/main")
    worktree = primary / ".worktrees" / "dispatch" / "kimi" / TASK_ID
    worktree.parent.mkdir(parents=True)
    _git(primary, "worktree", "add", "-b", BRANCH, str(worktree), "HEAD")
    monkeypatch.setattr(delegate, "_REPO_ROOT", primary.resolve())
    monkeypatch.setattr(reap_worktrees, "_active_task_ids", lambda: set())
    monkeypatch.setattr(reap_worktrees, "_live_cwd_paths", lambda _root: set())
    kimi_boundary.install(worktree, agent="kimi", base_ref="origin/main", owned_paths=[OWNED])
    state_path = delegate._state_path(TASK_ID)
    delegate._write_state_atomic(
        state_path,
        {
            "task_id": TASK_ID,
            "agent": "kimi",
            "status": "failed",
            "finished_at": "2020-01-01T00:00:00Z",
            "worktree_path": str(worktree.resolve()),
            "worktree_branch": BRANCH,
            "worktree_base": "main",
            "worktree_reused": False,
            "owned_paths": [OWNED],
        },
    )

    def write(text: str, *, commit: bool = False) -> None:
        label = worktree / LABEL
        label.parent.mkdir(parents=True, exist_ok=True)
        label.write_text(text, encoding="utf-8")
        if commit:
            _git(worktree, "add", "-A")
            _git(worktree, "commit", "--no-verify", "-m", "worker commit")

    return worktree.resolve(), origin, state_path, write


def _assert_push_block_intact(worktree: Path) -> None:
    assert kimi_boundary.is_installed(worktree)
    assert kimi_boundary.PUSH_BLOCK_URL in _git(worktree, "config", "--get-all", "remote.origin.pushurl").splitlines()
    proc = _git_proc(worktree, "push", "origin", "HEAD:refs/heads/worker-push")
    assert proc.returncode != 0 and "kimi-push-disabled" in proc.stderr


@pytest.mark.parametrize("committed", [False, True])
def test_rescue_pushes_clean_kimi_work_and_leaves_the_push_block_in_place(kimi_rescue, committed):
    worktree, origin, state_path, write = kimi_rescue
    write("export const label = 'Lesson';\n", commit=committed)

    result = delegate._rescue_task(state_path, apply=True)

    assert result["action"] == "rescued", result
    assert _remote_heads(origin)[RESCUE_REF] == result["head"]
    assert _git(origin, "show", f"{RESCUE_REF}:{LABEL}") == "export const label = 'Lesson';\n"
    state = delegate._read_state(state_path)
    assert (state["rescue_ref"], state["rescue_status"]) == (RESCUE_REF, "rescued")
    _assert_push_block_intact(worktree)
    assert "worker-push" not in _remote_heads(origin)


def test_rescue_dry_run_reports_clean_kimi_work_without_pushing(kimi_rescue):
    _worktree, origin, state_path, write = kimi_rescue
    write("export const label = 'Lesson';\n")

    result = delegate._rescue_task(state_path, apply=False)

    assert (result["action"], result["rescue_ref"]) == ("candidate", RESCUE_REF)
    assert RESCUE_REF not in _remote_heads(origin)


@pytest.mark.parametrize("committed", [False, True])
@pytest.mark.parametrize("apply", [False, True])
def test_rescue_refuses_kimi_work_that_fails_the_content_check(kimi_rescue, committed, apply):
    worktree, origin, state_path, write = kimi_rescue
    write("export const label = 'Урок';\n", commit=committed)
    head = _git(worktree, "rev-parse", "HEAD")
    status = _git(worktree, "status", "--porcelain")

    result = delegate._rescue_task(state_path, apply=apply)

    assert result["action"] == "error"
    assert result["failure_code"] == "kimi_content_refused"
    assert "KIMI CODING-ONLY" in result["reason"] and LABEL in result["reason"]
    assert RESCUE_REF not in _remote_heads(origin)
    assert _git(worktree, "rev-parse", "HEAD") == head
    assert _git(worktree, "status", "--porcelain") == status
    assert delegate._read_state(state_path).get("rescue_ref") is None
    _assert_push_block_intact(worktree)


def test_rescue_checks_a_kimi_record_even_without_its_boundary(kimi_rescue):
    worktree, origin, state_path, write = kimi_rescue
    kimi_boundary.remove(worktree)
    write("export const label = 'Урок';\n")

    result = delegate._rescue_task(state_path, apply=True)

    assert (result["action"], result["failure_code"]) == ("error", "kimi_content_refused")
    assert RESCUE_REF not in _remote_heads(origin)


def test_rescue_refuses_when_the_main_repository_push_url_is_blocked_too(kimi_rescue):
    worktree, origin, state_path, write = kimi_rescue
    _git(worktree, "config", "remote.origin.pushurl", kimi_boundary.PUSH_BLOCK_URL)  # the shared config
    write("export const label = 'Lesson';\n", commit=True)

    result = delegate._rescue_task(state_path, apply=True)

    assert result["action"] == "error"
    assert result["reason"] == "main repository has no single usable push URL for origin"
    assert RESCUE_REF not in _remote_heads(origin)


def test_rescue_ignores_a_push_url_the_kimi_worktree_set_for_itself(kimi_rescue, tmp_path):
    """The canonical URL comes from the main repository, never the worker's worktree-scoped config."""
    worktree, origin, state_path, write = kimi_rescue
    decoy = tmp_path / "decoy.git"
    _git(tmp_path, "init", "--bare", str(decoy))
    _git(worktree, "config", "--worktree", "remote.origin.url", str(decoy))
    write("export const label = 'Lesson';\n", commit=True)

    result = delegate._rescue_task(state_path, apply=True)

    assert result["action"] == "rescued", result
    assert _remote_heads(origin)[RESCUE_REF] == result["head"]
    assert _remote_heads(decoy) == {}
