"""Unit tests for the #M-7 direct-main push pytest guard."""

from __future__ import annotations

import importlib.util
import io
import json
import os
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
GUARD_PATH = REPO_ROOT / "agents_extensions/shared" / "hooks" / "guard-push-pytest.py"
STAMP_PATH = REPO_ROOT / "agents_extensions/shared" / "hooks" / "stamp-pytest.sh"


def _load_hook():
    spec = importlib.util.spec_from_file_location("guard_push_pytest", GUARD_PATH)
    assert spec and spec.loader, f"could not load hook at {GUARD_PATH}"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


guard = _load_hook()


def _run(
    monkeypatch: pytest.MonkeyPatch,
    command: str,
    *,
    branch: str = "main",
    paths: tuple[str, ...] = ("tests/test_guard_push_pytest.py",),
    marker_fresh: bool | None = False,
) -> int:
    payload = json.dumps({"tool_input": {"command": command}})
    marker = Path("/tmp/learn-uk-pytest.main.stamp")
    monkeypatch.setattr("sys.stdin", io.StringIO(payload))
    monkeypatch.setattr(guard, "_current_branch", lambda _cwd: branch)
    monkeypatch.setattr(guard, "_changed_paths", lambda _cwd: list(paths))
    monkeypatch.setattr(guard, "_marker_path", lambda _branch: marker)
    monkeypatch.setattr(guard, "_marker_is_fresh", lambda _marker: marker_fresh)
    monkeypatch.delenv("SKIP_PYTEST_HOOK", raising=False)
    return guard.main()


def test_push_to_main_with_trigger_path_and_stale_marker_blocks(monkeypatch, capsys):
    assert _run(monkeypatch, "git push origin main") == 2
    err = capsys.readouterr().err
    assert "/tmp/learn-uk-pytest.main.stamp" in err
    assert "SKIP_PYTEST_HOOK=1" in err


def test_push_to_main_with_fresh_marker_allows(monkeypatch):
    assert _run(monkeypatch, "git push origin main", marker_fresh=True) == 0


def test_non_main_branch_allows(monkeypatch):
    assert _run(monkeypatch, "git push -u origin feature", branch="feature") == 0


def test_non_push_command_allows(monkeypatch):
    assert _run(monkeypatch, "git status") == 0


def test_skip_env_allows(monkeypatch):
    payload = json.dumps({"tool_input": {"command": "git push origin main"}})
    monkeypatch.setattr("sys.stdin", io.StringIO(payload))
    monkeypatch.setenv("SKIP_PYTEST_HOOK", "1")
    assert guard.main() == 0


def test_quoted_push_in_commit_body_allows(monkeypatch):
    assert _run(monkeypatch, 'git commit -m "docs: mention git push origin main"') == 0


def test_dry_run_push_allows(monkeypatch):
    assert _run(monkeypatch, "git push --dry-run origin main") == 0


def test_non_trigger_diff_allows(monkeypatch):
    assert _run(monkeypatch, "git push origin main", paths=("README.md",)) == 0


def test_hook_errors_fail_open(monkeypatch):
    payload = json.dumps({"tool_input": {"command": "git push origin main"}})
    monkeypatch.setattr("sys.stdin", io.StringIO(payload))
    monkeypatch.setattr(guard, "_current_branch", lambda _cwd: None)
    monkeypatch.delenv("SKIP_PYTEST_HOOK", raising=False)
    assert guard.main() == 0


def test_stamp_pytest_bash_smoke(tmp_path):
    branch = "testbranch"
    git_env = os.environ.copy()
    for key in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_PREFIX"):
        git_env.pop(key, None)

    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-b", branch], cwd=repo, env=git_env, check=True, timeout=30)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, env=git_env, check=True, timeout=30)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo, env=git_env, check=True, timeout=30)
    (repo / "README.md").write_text("test repo\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=repo, env=git_env, check=True, timeout=30)
    subprocess.run(["git", "commit", "-m", "initial"], cwd=repo, env=git_env, check=True, timeout=30)

    marker = tmp_path / f"learn-uk-pytest.{branch}.stamp"
    payload = json.dumps({"tool_input": {"command": ".venv/bin/python -m pytest tests/test_guard_push_pytest.py -q"}})
    env = git_env.copy()
    env["TMPDIR"] = str(tmp_path)

    result = subprocess.run(
        [str(STAMP_PATH)],
        cwd=repo,
        input=payload,
        capture_output=True,
        text=True,
        env=env,
        check=False,
        timeout=30,
    )

    assert result.returncode == 0
    assert marker.exists()

    marker.unlink()
    subprocess.run(["git", "checkout", "--detach", "HEAD"], cwd=repo, env=git_env, check=True, capture_output=True, text=True, timeout=30)

    detached_result = subprocess.run(
        [str(STAMP_PATH)],
        cwd=repo,
        input=payload,
        capture_output=True,
        text=True,
        env=env,
        check=False,
        timeout=30,
    )

    assert detached_result.returncode == 0
    assert not list(tmp_path.glob("learn-uk-pytest*.stamp"))


# --- #4876: glued-operator evasion class ------------------------------------


@pytest.mark.parametrize(
    "cmd",
    [
        "true 2>&1 | head -1; git push origin main",
        "echo done\ngit push origin main",
        "true;git push origin main",
        "git add -A && git commit -m 'x'; git push",
    ],
)
def test_glued_operator_push_detected(cmd):
    assert guard._contains_git_push(cmd)


def test_heredoc_push_mention_not_detected():
    cmd = "cat > /tmp/n.md <<'EOF'\nthen git push origin main\nEOF"
    assert not guard._contains_git_push(cmd)


def test_backslash_continuation_push_detected():
    assert guard._contains_git_push("git push \\\n  origin main")


# --- #4877 adversarial round (grok-build msg 2334) ---


@pytest.mark.parametrize(
    "cmd",
    [
        "env FOO=1 git push origin main",
        "FOO=1 git push origin main",
        "{ git push origin main; }",
    ],
)
def test_wrapper_assignment_brace_push_detected(cmd):
    assert guard._contains_git_push(cmd)


def test_unclosed_heredoc_does_not_hide_push():
    assert guard._contains_git_push("cat <<'NOEND'\nnote\ngit push origin main")


# --- Tests for 4945 defects ---

def test_stamp_pytest_absolute_path_venv(tmp_path):
    branch = "testbranch"
    git_env = os.environ.copy()
    for key in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_PREFIX"):
        git_env.pop(key, None)

    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-b", branch], cwd=repo, env=git_env, check=True, timeout=30)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, env=git_env, check=True, timeout=30)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo, env=git_env, check=True, timeout=30)
    (repo / "README.md").write_text("test repo\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=repo, env=git_env, check=True, timeout=30)
    subprocess.run(["git", "commit", "-m", "initial"], cwd=repo, env=git_env, check=True, timeout=30)

    marker = tmp_path / f"learn-uk-pytest.{branch}.stamp"

    # Test absolute path /abs/path/.venv/bin/python -m pytest
    payload = json.dumps({
        "tool_input": {
            "command": "/abs/path/.venv/bin/python -m pytest tests/test_guard_push_pytest.py -q"
        }
    })
    env = git_env.copy()
    env["TMPDIR"] = str(tmp_path)

    result = subprocess.run(
        [str(STAMP_PATH)],
        cwd=repo,
        input=payload,
        capture_output=True,
        text=True,
        env=env,
        check=False,
        timeout=30,
    )

    assert result.returncode == 0
    assert marker.exists()


def test_stamp_pytest_compound_command_segment_success(tmp_path):
    branch = "testbranch"
    git_env = os.environ.copy()
    for key in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_PREFIX"):
        git_env.pop(key, None)

    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-b", branch], cwd=repo, env=git_env, check=True, timeout=30)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, env=git_env, check=True, timeout=30)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo, env=git_env, check=True, timeout=30)
    (repo / "README.md").write_text("test repo\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=repo, env=git_env, check=True, timeout=30)
    subprocess.run(["git", "commit", "-m", "initial"], cwd=repo, env=git_env, check=True, timeout=30)

    env = git_env.copy()
    env["TMPDIR"] = str(tmp_path)

    # 1. Success case: pytest segment succeeds, compound fails (PostToolUseFailure)
    marker = tmp_path / f"learn-uk-pytest.{branch}.stamp"
    payload_success = json.dumps({
        "hook_event_name": "PostToolUseFailure",
        "tool_input": {
            "command": ".venv/bin/python -m pytest tests/ -v && exit 1"
        },
        "tool_output": "============================= 20 passed in 0.65s =============================="
    })

    result = subprocess.run(
        [str(STAMP_PATH)],
        cwd=repo,
        input=payload_success,
        capture_output=True,
        text=True,
        env=env,
        check=False,
        timeout=30,
    )
    assert result.returncode == 0
    assert marker.exists()

    # 2. Failure case: pytest segment fails, compound fails (PostToolUseFailure)
    marker.unlink()
    payload_fail = json.dumps({
        "hook_event_name": "PostToolUseFailure",
        "tool_input": {
            "command": ".venv/bin/python -m pytest tests/ -v && exit 1"
        },
        "tool_output": "============================= 1 failed, 19 passed in 0.65s =============================="
    })

    result = subprocess.run(
        [str(STAMP_PATH)],
        cwd=repo,
        input=payload_fail,
        capture_output=True,
        text=True,
        env=env,
        check=False,
        timeout=30,
    )
    assert result.returncode == 0
    assert not marker.exists()

    # 3. "no tests ran" must NOT stamp: a wrong test path in a failing compound
    # produces a summary with no positive "passed" signal.
    payload_no_tests = json.dumps({
        "hook_event_name": "PostToolUseFailure",
        "tool_input": {
            "command": ".venv/bin/python -m pytest tests/nonexistent && exit 1"
        },
        "tool_output": "============================= no tests ran in 0.12s ==============================",
    })

    result = subprocess.run(
        [str(STAMP_PATH)],
        cwd=repo,
        input=payload_no_tests,
        capture_output=True,
        text=True,
        env=env,
        check=False,
        timeout=30,
    )
    assert result.returncode == 0
    assert not marker.exists()


def test_inline_skip_allows(monkeypatch):
    assert _run(monkeypatch, "SKIP_PYTEST_HOOK=1 git push origin main") == 0
    assert _run(monkeypatch, "SKIP_PYTEST_HOOK=\"1\" git push origin main") == 0
    assert _run(monkeypatch, "SKIP_PYTEST_HOOK='1' git push origin main") == 0


def test_block_msg_interpolates_actual_branch():
    msg = guard._block_msg("some-feature-branch", Path("/tmp/marker"))
    assert "direct push from `some-feature-branch`" in msg
    assert "from `main`" not in msg



# --- #5771: the guard must judge the tree the push actually runs in. ---------
#
# Regression tests backed by REAL git repos, not monkeypatched helpers: the bug
# was that `_current_branch`/`_changed_paths` ran in the hook process's own cwd
# (the primary checkout, always `main` under layout A), so every dispatch-worktree
# push was judged as a push from `main` against main's diff. Monkeypatching those
# two helpers is exactly what hid it, so these tests must not.


def _git(cwd: Path, *args: str) -> None:
    env = os.environ.copy()
    for key in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_PREFIX"):
        env.pop(key, None)
    subprocess.run(
        ["git", *args], cwd=cwd, env=env, check=True,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )


@pytest.fixture
def repo_with_worktree(tmp_path: Path) -> tuple[Path, Path]:
    """A repo on `main` with a Python commit, plus a worktree on a feature branch."""
    origin = tmp_path / "origin"
    origin.mkdir()
    _git(origin, "init", "-b", "main")
    _git(origin, "config", "user.email", "t@t.t")
    _git(origin, "config", "user.name", "t")
    (origin / "seed.py").write_text("x = 1\n", encoding="utf-8")
    _git(origin, "add", "seed.py")
    _git(origin, "commit", "-m", "seed")

    main_co = tmp_path / "main_co"
    _git(tmp_path, "clone", str(origin), str(main_co))
    _git(main_co, "config", "user.email", "t@t.t")
    _git(main_co, "config", "user.name", "t")
    # An unpushed Python commit on main — the guard's trigger condition.
    (main_co / "changed.py").write_text("y = 2\n", encoding="utf-8")
    _git(main_co, "add", "changed.py")
    _git(main_co, "commit", "-m", "python change on main")

    worktree = tmp_path / "wt"
    _git(main_co, "worktree", "add", str(worktree), "-b", "claude/feature")
    return main_co, worktree


def _run_real(monkeypatch: pytest.MonkeyPatch, command: str, payload_cwd: Path) -> int:
    payload = json.dumps({"tool_input": {"command": command}, "cwd": str(payload_cwd)})
    monkeypatch.setattr("sys.stdin", io.StringIO(payload))
    monkeypatch.setattr(guard, "_marker_is_fresh", lambda _marker: False)
    monkeypatch.delenv("SKIP_PYTEST_HOOK", raising=False)
    return guard.main()


def test_push_from_worktree_branch_is_not_judged_as_main(monkeypatch, repo_with_worktree):
    """The false positive that trained everyone to set SKIP_PYTEST_HOOK=1."""
    _main_co, worktree = repo_with_worktree
    assert _run_real(monkeypatch, "git push origin HEAD:claude/feature", worktree) == 0


def test_leading_cd_into_a_worktree_is_honoured(monkeypatch, repo_with_worktree):
    """`cd <worktree> && git push` must be judged in the worktree, not the payload cwd."""
    main_co, worktree = repo_with_worktree
    command = f"cd {worktree} && git push origin HEAD:claude/feature"
    assert _run_real(monkeypatch, command, main_co) == 0


def test_genuine_main_push_with_python_changes_still_blocks(monkeypatch, repo_with_worktree):
    """The guard must keep its teeth for the case it actually exists to catch."""
    main_co, _worktree = repo_with_worktree
    assert _run_real(monkeypatch, "git push origin main", main_co) == 2


def test_empty_diff_never_claims_python_changes(monkeypatch, tmp_path):
    """An empty outgoing diff must not be reported as 'includes Python changes'."""
    origin = tmp_path / "o2"
    origin.mkdir()
    _git(origin, "init", "-b", "main")
    _git(origin, "config", "user.email", "t@t.t")
    _git(origin, "config", "user.name", "t")
    (origin / "seed.py").write_text("x = 1\n", encoding="utf-8")
    _git(origin, "add", "seed.py")
    _git(origin, "commit", "-m", "seed")
    clone = tmp_path / "c2"
    _git(tmp_path, "clone", str(origin), str(clone))
    # No commits ahead of origin/main at all.
    assert _run_real(monkeypatch, "git push origin main", clone) == 0


def test_unresolvable_cd_falls_back_instead_of_guessing(monkeypatch, repo_with_worktree):
    """`cd $VAR` is ambiguous; the guard must fall back to the payload cwd, not guess."""
    main_co, _worktree = repo_with_worktree
    assert _run_real(monkeypatch, "cd $TARGET && git push origin main", main_co) == 2


# --- Cross-family review P1s on the #5771 fix. Both were BYPASSES: they let an
# --- untested push to `main` through, which is the one thing this guard exists
# --- to stop. Absence of these tests is what let the first fix look correct.


def test_chained_cd_follows_the_last_directory_before_the_push(monkeypatch, repo_with_worktree):
    """`cd <worktree> && cd <main> && git push origin main` must still be judged as main.

    Honouring only the FIRST cd meant the guard saw a feature branch and waved the
    push through, even though it actually ran from main.
    """
    main_co, worktree = repo_with_worktree
    command = f"cd {worktree} && cd {main_co} && git push origin main"
    assert _run_real(monkeypatch, command, worktree) == 2


def test_cd_after_the_push_does_not_re_home_it(monkeypatch, repo_with_worktree):
    """Only cd's BEFORE the push count; a trailing cd must not change the verdict."""
    main_co, worktree = repo_with_worktree
    command = f"cd {main_co} && git push origin main && cd {worktree}"
    assert _run_real(monkeypatch, command, worktree) == 2


@pytest.mark.parametrize(
    "var",
    [
        "GIT_DIR",
        "GIT_OBJECT_DIRECTORY",
        "GIT_ALTERNATE_OBJECT_DIRECTORIES",
        "GIT_COMMON_DIR",
        "GIT_INDEX_FILE",
    ],
)
def test_hostile_git_env_cannot_disable_the_guard(monkeypatch, repo_with_worktree, var):
    """A broken git-discovery override must not turn a block into a pass.

    An invalid value makes `git diff` fail; an unstripped variable therefore
    yielded no changed paths, and no changed paths meant "nothing to guard".
    """
    main_co, _worktree = repo_with_worktree
    monkeypatch.setenv(var, "/nonexistent/hostile/path")
    assert _run_real(monkeypatch, "git push origin main", main_co) == 2
