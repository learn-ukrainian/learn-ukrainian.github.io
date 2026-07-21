"""Tests for the primary-checkout write guard hook (issue #4448).

Two layers:

* **Pure extraction** — ``bash_write_targets`` / ``write_tool_targets`` are
  driven directly with strings/dicts (no git), covering redirection, ``tee``,
  in-place edits, quoted false-positives, and the Write/Edit/apply_patch
  payload shapes.
* **End-to-end decision** — the hook is run as a subprocess with a JSON payload
  on stdin against a *real* git repo (primary checkout on ``main`` + a
  registered ``.worktrees/dispatch/**`` worktree + gitignored state), asserting
  the exit code and worktree-hint message. The decision itself is delegated to
  ``scripts.guardrails.worktree_containment`` (#4444); these tests prove the
  provider payloads map onto it correctly.

The hook filename has hyphens, so pure-function tests load it via importlib.
Only module-level defs run on import (``main`` is ``__main__``-guarded).
"""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
HOOK_PATH = REPO_ROOT / "agents_extensions/shared" / "hooks" / "guard-primary-checkout-write.py"

# Git env vars that would hijack the throwaway repos below (inherited under
# pre-commit / a git hook). Mirrors the module's own denylist.
_GIT_ENV = {
    "GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_OBJECT_DIRECTORY",
    "GIT_ALTERNATE_OBJECT_DIRECTORIES", "GIT_NAMESPACE", "GIT_CEILING_DIRECTORIES",
    "GIT_DISCOVERY_ACROSS_FILESYSTEM", "GIT_COMMON_DIR",
}


def _load_hook():
    spec = importlib.util.spec_from_file_location("guard_primary_checkout_write", HOOK_PATH)
    assert spec and spec.loader, f"could not load hook at {HOOK_PATH}"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


hook = _load_hook()


# ===========================================================================
# Pure extraction — Bash
# ===========================================================================


@pytest.mark.parametrize(
    "command, expected",
    [
        # Read-only preflight commands expose no write target.
        ("git status", []),
        ("git log --oneline -5", []),
        ("rg pattern scripts/", []),
        ("cat curriculum/x.md", []),
        ("git diff && git status", []),
        # Redirection variants.
        ("echo hi > out.txt", ["out.txt"]),
        ("printf x >> a.log", ["a.log"]),
        ("echo x &> both.txt", ["both.txt"]),
        ("echo x 2>err.txt", ["err.txt"]),
        ("build > /dev/null", ["/dev/null"]),
        # tee (with wrapper + append flag).
        ("cat a | tee out.txt", ["out.txt"]),
        ("cat a | tee -a log.txt", ["log.txt"]),
        ("sudo tee /etc/hosts", ["/etc/hosts"]),
        # In-place editors — script excluded, files kept.
        ('sed -i "s/x/y/" real.py', ["real.py"]),
        ('sed -i.bak -e "s/a/b/" f1 f2', ["f1", "f2"]),
        ('perl -pi -e "s/x/y/" z.txt', ["z.txt"]),
        # Leading env assignment before the command word.
        ("VAR=1 tee out2.txt", ["out2.txt"]),
    ],
)
def test_bash_write_targets(command, expected):
    assert hook.bash_write_targets(command) == expected


@pytest.mark.parametrize(
    "command",
    [
        # A redirect char inside a quoted string is NOT a redirection.
        'git commit -m "fix > thing"',
        "echo 'a > b'",
        # fd duplication is not a file write.
        "echo x 2>&1",
        # sed without an in-place flag does not write a file.
        'sed "s/x/y/" real.py',
    ],
)
def test_bash_no_false_positive_write(command):
    assert hook.bash_write_targets(command) == []


# ===========================================================================
# Pure extraction — structured write tools
# ===========================================================================


def test_write_tool_targets_file_path():
    assert hook.write_tool_targets({"file_path": "/repo/x.py", "content": "hi"}) == ["/repo/x.py"]
    assert hook.write_tool_targets({"file_path": "rel/y.md"}) == ["rel/y.md"]


def test_write_tool_targets_apply_patch():
    patch = (
        "*** Begin Patch\n"
        "*** Add File: scripts/new.py\n+print(1)\n"
        "*** Update File: docs/z.md\n"
        "*** Delete File: old/gone.txt\n"
        "*** End Patch\n"
    )
    assert hook.write_tool_targets({"input": patch}) == [
        "scripts/new.py",
        "docs/z.md",
        "old/gone.txt",
    ]


def test_write_tool_targets_apply_patch_move():
    patch = "*** Begin Patch\n*** Move to: dst/here.py\n*** Move from: src/there.py\n*** End Patch\n"
    assert hook.write_tool_targets({"patch": patch}) == ["dst/here.py", "src/there.py"]


# ===========================================================================
# End-to-end decision against a real repo + worktree
# ===========================================================================


def _clean_env() -> dict[str, str]:
    return {k: v for k, v in os.environ.items() if k not in _GIT_ENV}


def _git(repo: Path, *args: str) -> None:
    subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True, capture_output=True, text=True, env=_clean_env(),
    )


def _python() -> str:
    venv = REPO_ROOT / ".venv" / "bin" / "python"
    return str(venv) if venv.exists() else "python3"


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """Primary checkout on ``main`` + a dispatch worktree + gitignored state."""
    main = tmp_path / "main"
    main.mkdir()
    _git(main, "init", "-q", "-b", "main")
    _git(main, "config", "user.email", "test@example.com")
    _git(main, "config", "user.name", "Test")

    (main / "curriculum").mkdir()
    (main / "curriculum" / "tracked.md").write_text("original\n", encoding="utf-8")
    (main / ".gitignore").write_text("local_state/\n*.local\n", encoding="utf-8")
    _git(main, "add", "curriculum/tracked.md", ".gitignore")
    _git(main, "commit", "-q", "-m", "init")

    _git(main, "worktree", "add", "-q",
         ".worktrees/dispatch/claude/task-1", "-b", "claude/task-1")
    return main


def _run(repo: Path, payload: dict) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [_python(), str(HOOK_PATH)],
        input=json.dumps(payload),
        cwd=repo, check=False, capture_output=True, text=True, env=_clean_env(),
    )


def _write_payload(repo: Path, tool: str, rel: str) -> dict:
    return {"tool_name": tool, "cwd": str(repo), "tool_input": {"file_path": str(repo / rel)}}


def test_tracked_primary_file_write_blocked(repo: Path):
    result = _run(repo, _write_payload(repo, "Write", "curriculum/tracked.md"))
    assert result.returncode == 2, result.stderr
    assert ".worktrees/dispatch/" in result.stderr


def test_untracked_new_primary_file_write_blocked(repo: Path):
    # A brand-new tracked-to-be file in the primary checkout also dirties it.
    result = _run(repo, _write_payload(repo, "Write", "curriculum/brand-new.md"))
    assert result.returncode == 2, result.stderr


def test_gitignored_local_state_write_allowed(repo: Path):
    result = _run(repo, _write_payload(repo, "Write", "local_state/scratch.json"))
    assert result.returncode == 0, result.stderr


def test_dispatch_worktree_write_allowed(repo: Path):
    payload = _write_payload(repo, "Edit", ".worktrees/dispatch/claude/task-1/curriculum/tracked.md")
    result = _run(repo, payload)
    assert result.returncode == 0, result.stderr


def test_read_only_bash_allowed(repo: Path):
    for command in ("git status", "cat curriculum/tracked.md", "git log --oneline"):
        payload = {"tool_name": "Bash", "cwd": str(repo), "tool_input": {"command": command}}
        result = _run(repo, payload)
        assert result.returncode == 0, f"{command!r}: {result.stderr}"


def test_write_capable_bash_redirect_blocked(repo: Path):
    payload = {
        "tool_name": "Bash", "cwd": str(repo),
        "tool_input": {"command": "echo tampered > curriculum/tracked.md"},
    }
    result = _run(repo, payload)
    assert result.returncode == 2, result.stderr
    assert ".worktrees/dispatch/" in result.stderr


def test_write_capable_bash_tee_blocked(repo: Path):
    payload = {
        "tool_name": "Bash", "cwd": str(repo),
        "tool_input": {"command": "echo x | tee curriculum/tracked.md"},
    }
    result = _run(repo, payload)
    assert result.returncode == 2, result.stderr


def test_bash_redirect_to_gitignored_allowed(repo: Path):
    payload = {
        "tool_name": "Bash", "cwd": str(repo),
        "tool_input": {"command": "echo x > local_state/out.log"},
    }
    result = _run(repo, payload)
    assert result.returncode == 0, result.stderr


def test_apply_patch_tracked_file_blocked(repo: Path):
    patch = "*** Begin Patch\n*** Update File: curriculum/tracked.md\n@@\n-original\n+tampered\n*** End Patch\n"
    payload = {"tool_name": "apply_patch", "cwd": str(repo), "tool_input": {"input": patch}}
    result = _run(repo, payload)
    assert result.returncode == 2, result.stderr
    assert ".worktrees/dispatch/" in result.stderr


def test_not_enforced_off_protected_branch(repo: Path):
    # If the primary checkout is deliberately on a feature branch, the guard
    # stays out of the way — enforcement is scoped to protected branches.
    _git(repo, "checkout", "-q", "-b", "maintenance")
    result = _run(repo, _write_payload(repo, "Write", "curriculum/tracked.md"))
    assert result.returncode == 0, result.stderr


def test_bash_write_from_worktree_targeting_main_blocked(repo: Path):
    # An agent working in the dispatch worktree that reaches back into the
    # primary checkout via an absolute path is still blocked (containment is by
    # resolved real path, not by cwd).
    worktree = repo / ".worktrees/dispatch/claude/task-1"
    payload = {
        "tool_name": "Bash", "cwd": str(worktree),
        "tool_input": {"command": f"echo x > {repo / 'curriculum' / 'tracked.md'}"},
    }
    result = _run(repo, payload)
    assert result.returncode == 2, result.stderr


# --- #4538 / #4855: heredoc bodies carry no write targets -------------------


@pytest.mark.parametrize(
    "command, expected",
    [
        # Body text with `>N` (previously misread as a redirect to '15%').
        (
            "cat > /tmp/brief.md <<'EOF'\n"
            "... if >15% of the last 30 consecutive live passages ...\n"
            "EOF",
            ["/tmp/brief.md"],
        ),
        # Body text with markdown backtick code spans (#4855 live repro).
        (
            "cat > /tmp/brief.md <<'EOF'\n"
            "run `.venv/bin/python scripts/x.py` then check\n"
            "EOF",
            ["/tmp/brief.md"],
        ),
        # Tab-indented body with <<- and a redirect-looking line.
        (
            "cat > /tmp/t.md <<-'DOC'\n\tdata 2>&1 goes here\n\tDOC",
            ["/tmp/t.md"],
        ),
        # A real write AFTER the heredoc closes is still seen.
        (
            "cat > /tmp/a.md <<'EOF'\nbody\nEOF\necho x > out.txt",
            ["/tmp/a.md", "out.txt"],
        ),
    ],
)
def test_heredoc_body_not_write_targets(command, expected):
    assert hook.bash_write_targets(command) == expected


# --- #4877 adversarial round (grok-build msg 2334): heredoc fail-open ---------


@pytest.mark.parametrize(
    "command, expected",
    [
        # Never-closing marker: the whole buffer is inspected (fail-closed).
        # The security-critical target `curriculum/tracked.md` must NOT vanish;
        # the would-be body line `> fake` is conservatively over-reported too,
        # which is the safe direction (a malformed heredoc gets full scrutiny).
        (
            "cat <<'NOEND'\nbody > fake\necho tampered > curriculum/tracked.md",
            ["fake", "curriculum/tracked.md"],
        ),
        # Attached `<<-E` whose closer never appears → unclosed → keep the
        # trailing real write.
        (
            "cat <<-E\n\tbody\nreal > target.txt",
            ["target.txt"],
        ),
        # Attached `<<-EOF` PROPERLY closed (tab + EOF): body dropped, no FP,
        # and the opener's own redirect target is still seen.
        (
            "cat > /tmp/a.md <<-EOF\n\tbody 2>&1 here\n\tEOF",
            ["/tmp/a.md"],
        ),
    ],
)
def test_heredoc_failclosed_on_unclosed(command, expected):
    assert hook.bash_write_targets(command) == expected


# --- #5396: git-mediated primary-checkout mutations -------------------------


@pytest.mark.parametrize(
    "command, kind",
    [
        ("git apply /tmp/worker.diff", "apply"),
        ("git am /tmp/mbox", "am"),
        ("git add curriculum/tracked.md", "add"),
        ("git stash pop", "stash_apply"),
        ("git stash apply", "stash_apply"),
        ("git checkout HEAD -- curriculum/tracked.md", "path_checkout"),
        ("git restore --source=HEAD~1 -- curriculum/tracked.md", "restore_source"),
    ],
)
def test_bash_git_write_intents_blocked_kinds(command, kind):
    intents = hook.bash_git_write_intents(command)
    assert len(intents) == 1
    assert intents[0]["kind"] == kind
    assert intents[0]["allowlisted"] is False


@pytest.mark.parametrize(
    "command",
    [
        "git checkout -- curriculum/tracked.md",
        "git restore curriculum/tracked.md",
        "git status",
        "git log --oneline",
        "git stash list",
        "git checkout -b feature",
    ],
)
def test_bash_git_write_intents_allowlisted_or_ignored(command):
    intents = hook.bash_git_write_intents(command)
    # No blocking intents: either empty or allowlisted-only.
    assert all(i.get("allowlisted") for i in intents)


def test_bash_git_write_intents_honors_dash_c():
    intents = hook.bash_git_write_intents(
        "git -C .worktrees/dispatch/claude/task-1 apply /tmp/x.diff"
    )
    assert len(intents) == 1
    assert intents[0]["c_path"] == ".worktrees/dispatch/claude/task-1"
    assert intents[0]["kind"] == "apply"


def test_git_apply_on_primary_blocked(repo: Path):
    payload = {
        "tool_name": "Bash",
        "cwd": str(repo),
        "tool_input": {"command": "git apply /tmp/worker.diff"},
    }
    result = _run(repo, payload)
    assert result.returncode == 2, result.stderr
    assert "#5396" in result.stderr
    assert "git apply" in result.stderr


def test_git_stash_pop_on_primary_blocked(repo: Path):
    payload = {
        "tool_name": "Bash",
        "cwd": str(repo),
        "tool_input": {"command": "git stash pop"},
    }
    result = _run(repo, payload)
    assert result.returncode == 2, result.stderr


def test_git_add_tracked_on_primary_blocked(repo: Path):
    payload = {
        "tool_name": "Bash",
        "cwd": str(repo),
        "tool_input": {"command": "git add curriculum/tracked.md"},
    }
    result = _run(repo, payload)
    assert result.returncode == 2, result.stderr


def test_git_checkout_ref_path_on_primary_blocked(repo: Path):
    payload = {
        "tool_name": "Bash",
        "cwd": str(repo),
        "tool_input": {"command": "git checkout HEAD -- curriculum/tracked.md"},
    }
    result = _run(repo, payload)
    assert result.returncode == 2, result.stderr


def test_git_checkout_clean_on_primary_allowed(repo: Path):
    """Rescue pattern: discard dirt without a tree-ish."""
    payload = {
        "tool_name": "Bash",
        "cwd": str(repo),
        "tool_input": {"command": "git checkout -- curriculum/tracked.md"},
    }
    result = _run(repo, payload)
    assert result.returncode == 0, result.stderr


def test_git_apply_via_dash_c_worktree_allowed(repo: Path):
    worktree = repo / ".worktrees/dispatch/claude/task-1"
    payload = {
        "tool_name": "Bash",
        "cwd": str(repo),
        "tool_input": {"command": f"git -C {worktree} apply /tmp/worker.diff"},
    }
    result = _run(repo, payload)
    assert result.returncode == 0, result.stderr


def test_git_apply_from_worktree_cwd_allowed(repo: Path):
    worktree = repo / ".worktrees/dispatch/claude/task-1"
    payload = {
        "tool_name": "Bash",
        "cwd": str(worktree),
        "tool_input": {"command": "git apply /tmp/worker.diff"},
    }
    result = _run(repo, payload)
    assert result.returncode == 0, result.stderr


def test_git_apply_dash_c_primary_from_worktree_blocked(repo: Path):
    worktree = repo / ".worktrees/dispatch/claude/task-1"
    payload = {
        "tool_name": "Bash",
        "cwd": str(worktree),
        "tool_input": {"command": f"git -C {repo} apply /tmp/worker.diff"},
    }
    result = _run(repo, payload)
    assert result.returncode == 2, result.stderr


def test_git_apply_override_env_allows(repo: Path, monkeypatch: pytest.MonkeyPatch):
    env = _clean_env()
    env["LEARN_UK_ALLOW_PRIMARY_GIT_WRITE"] = "1"
    payload = {
        "tool_name": "Bash",
        "cwd": str(repo),
        "tool_input": {"command": "git apply /tmp/worker.diff"},
    }
    result = subprocess.run(
        [_python(), str(HOOK_PATH)],
        input=json.dumps(payload),
        cwd=repo,
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 0, result.stderr


# --- #5517: checkout without -- ; git mv / git rm -------------------------


def test_bash_git_write_intents_checkout_no_dashdash():
    intents = hook.bash_git_write_intents("git checkout HEAD~1 curriculum/tracked.md")
    assert len(intents) == 1
    assert intents[0]["kind"] == "path_checkout"
    assert intents[0]["allowlisted"] is False
    assert intents[0]["paths"] == ["curriculum/tracked.md"]


def test_bash_git_write_intents_mv_rm():
    mv = hook.bash_git_write_intents("git mv a.py b.py")
    assert len(mv) == 1 and mv[0]["kind"] == "mv" and mv[0]["paths"] == ["a.py", "b.py"]
    rm = hook.bash_git_write_intents("git rm -f curriculum/tracked.md")
    assert len(rm) == 1 and rm[0]["kind"] == "rm" and rm[0]["paths"] == ["curriculum/tracked.md"]


def test_git_checkout_treeish_path_no_dashdash_blocked(repo: Path):
    payload = {
        "tool_name": "Bash",
        "cwd": str(repo),
        "tool_input": {"command": "git checkout HEAD~1 curriculum/tracked.md"},
    }
    result = _run(repo, payload)
    assert result.returncode == 2, result.stderr


def test_git_mv_on_primary_blocked(repo: Path):
    payload = {
        "tool_name": "Bash",
        "cwd": str(repo),
        "tool_input": {"command": "git mv curriculum/tracked.md curriculum/renamed.md"},
    }
    result = _run(repo, payload)
    assert result.returncode == 2, result.stderr


def test_git_rm_on_primary_blocked(repo: Path):
    payload = {
        "tool_name": "Bash",
        "cwd": str(repo),
        "tool_input": {"command": "git rm curriculum/tracked.md"},
    }
    result = _run(repo, payload)
    assert result.returncode == 2, result.stderr


def test_git_mv_via_dash_c_worktree_allowed(repo: Path):
    worktree = repo / ".worktrees/dispatch/claude/task-1"
    payload = {
        "tool_name": "Bash",
        "cwd": str(repo),
        "tool_input": {
            "command": f"git -C {worktree} mv curriculum/tracked.md curriculum/renamed.md"
        },
    }
    result = _run(repo, payload)
    assert result.returncode == 0, result.stderr


def test_git_checkout_branch_only_not_blocked_by_git_guard(repo: Path):
    """Branch switch has no pathspecs — left to the branch-switch guard."""
    payload = {
        "tool_name": "Bash",
        "cwd": str(repo),
        "tool_input": {"command": "git checkout -b feature-x"},
    }
    result = _run(repo, payload)
    # No git-mediated path intent → this hook allows (other hooks may still fire).
    assert result.returncode == 0, result.stderr


def test_bash_shell_var_to_gitignored_allowed(repo: Path):
    """#5404: A=gitignored/path; echo x > $A must be allowed after expansion."""
    payload = {
        "tool_name": "Bash",
        "cwd": str(repo),
        "tool_input": {
            "command": "A=local_state/from_var.log; echo x > $A",
        },
    }
    result = _run(repo, payload)
    assert result.returncode == 0, result.stderr


def test_bash_unresolved_shell_var_blocked_with_distinct_reason(repo: Path):
    """#5404: bare $A without assignment is not treated as a path under primary."""
    payload = {
        "tool_name": "Bash",
        "cwd": str(repo),
        "tool_input": {"command": "echo x > $A"},
    }
    result = _run(repo, payload)
    assert result.returncode == 2, result.stderr
    assert "unresolved_shell_variable" in result.stderr


def test_bash_redirect_to_claude_epic_archive_from_subdir_allowed(repo: Path):
    """#5404: cwd inside gitignored epic dir + relative archive path allowed."""
    epic = repo / ".claude" / "atlas-epic"
    epic.mkdir(parents=True, exist_ok=True)
    (epic / "archive").mkdir(exist_ok=True)
    # Ensure .claude is ignored like production (fixture may already ignore local_state only)
    gitignore = repo / ".gitignore"
    gi = gitignore.read_text(encoding="utf-8") if gitignore.is_file() else ""
    if ".claude/" not in gi:
        gitignore.write_text(gi.rstrip() + "\n.claude/\n", encoding="utf-8")
    payload = {
        "tool_name": "Bash",
        "cwd": str(epic),
        "tool_input": {"command": "echo x > archive/t.md"},
    }
    result = _run(repo, payload)
    assert result.returncode == 0, result.stderr


def test_bash_untracked_non_ignored_still_blocked(repo: Path):
    (repo / "docs").mkdir(exist_ok=True)
    payload = {
        "tool_name": "Bash",
        "cwd": str(repo),
        "tool_input": {"command": "echo x > docs/brand-new-untracked.md"},
    }
    result = _run(repo, payload)
    assert result.returncode == 2, result.stderr
    assert "untracked_primary_checkout" in result.stderr
