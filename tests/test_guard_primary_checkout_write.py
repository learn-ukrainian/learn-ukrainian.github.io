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
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.reads_content

REPO_ROOT = Path(__file__).resolve().parent.parent
HOOK_PATH = REPO_ROOT / "agents_extensions/shared" / "hooks" / "guard-primary-checkout-write.py"

# Git env vars that would hijack the throwaway repos below (inherited under
# pre-commit / a git hook). Mirrors the module's own denylist.
_GIT_ENV = {
    "GIT_DIR",
    "GIT_WORK_TREE",
    "GIT_INDEX_FILE",
    "GIT_OBJECT_DIRECTORY",
    "GIT_ALTERNATE_OBJECT_DIRECTORIES",
    "GIT_NAMESPACE",
    "GIT_CEILING_DIRECTORIES",
    "GIT_DISCOVERY_ACROSS_FILESYSTEM",
    "GIT_COMMON_DIR",
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
        ("sed -i '' 's/a/b/' f", ["f"]),
        ("sed -i '' f", []),
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


def test_bash_multiline_read_only_commands_do_not_merge_editor_flags():
    command = (
        "sed -n '1,220p' agents_extensions/codex/hooks.json\n"
        "find agents_extensions/shared/hooks -maxdepth 1 -type f -print | sort\n"
        'rg -n "additionalContext|BLOCKED" agents_extensions/shared/hooks'
    )

    assert hook.bash_write_targets(command) == []


def test_bash_line_continuation_keeps_in_place_editor_target():
    command = "sed -i \\\n-e 's/old/new/' curriculum/tracked.md"

    assert hook.bash_write_targets(command) == ["curriculum/tracked.md"]


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
        check=True,
        capture_output=True,
        text=True,
        env=_clean_env(),
        timeout=10,
    )


def _python() -> str:
    return sys.executable


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

    _git(main, "worktree", "add", "-q", ".worktrees/dispatch/claude/task-1", "-b", "claude/task-1")
    return main


def _run(repo: Path, payload: dict, env_extra: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [_python(), str(HOOK_PATH)],
        input=json.dumps(payload),
        cwd=repo,
        check=False,
        capture_output=True,
        text=True,
        env={**_clean_env(), **(env_extra or {})},
        timeout=30,
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


def test_dispatch_worktree_control_hook_write_allowed(repo: Path):
    payload = _write_payload(
        repo,
        "Edit",
        ".worktrees/dispatch/claude/task-1/agents_extensions/shared/hooks/guard-pr-merge.py",
    )

    result = _run(repo, payload)

    assert result.returncode == 0, result.stderr


def test_read_only_bash_allowed(repo: Path):
    for command in ("git status", "cat curriculum/tracked.md", "git log --oneline"):
        payload = {"tool_name": "Bash", "cwd": str(repo), "tool_input": {"command": command}}
        result = _run(repo, payload)
        assert result.returncode == 0, f"{command!r}: {result.stderr}"


def test_read_only_bash_redirect_is_allowed_when_jsonschema_is_masked(repo: Path, tmp_path: Path) -> None:
    """Read-only commands do not depend on optional Python packages."""
    poison = tmp_path / "poison"
    poison.mkdir()
    (poison / "jsonschema.py").write_text("raise ImportError('jsonschema deliberately masked')\n", encoding="utf-8")
    env = _clean_env()
    env["PYTHONPATH"] = str(poison)
    payload = {
        "tool_name": "Bash",
        "cwd": str(repo),
        "tool_input": {"command": "git status 2>/dev/null"},
    }

    result = subprocess.run(
        [_python(), str(HOOK_PATH)],
        input=json.dumps(payload),
        cwd=repo,
        check=False,
        capture_output=True,
        text=True,
        env=env,
        timeout=30,
    )

    assert result.returncode == 0, result.stderr


def test_bash_tool_input_workdir_controls_relative_write_resolution(repo: Path):
    worktree = repo / ".worktrees/dispatch/claude/task-1"
    payload = {
        "tool_name": "Bash",
        "cwd": str(repo),
        "tool_input": {
            "command": "echo x > curriculum/tracked.md",
            "workdir": str(worktree),
        },
    }

    result = _run(repo, payload)

    assert result.returncode == 0, result.stderr


def test_bash_tool_input_primary_workdir_cannot_be_spoofed_by_payload_cwd(repo: Path):
    worktree = repo / ".worktrees/dispatch/claude/task-1"
    payload = {
        "tool_name": "Bash",
        "cwd": str(worktree),
        "tool_input": {
            "command": "echo x > curriculum/tracked.md",
            "workdir": str(repo),
        },
    }

    result = _run(repo, payload)

    assert result.returncode == 2, result.stderr
    assert "tracked_primary_checkout" in result.stderr


def test_bash_line_continuation_cannot_hide_primary_in_place_edit(repo: Path):
    payload = {
        "tool_name": "Bash",
        "cwd": str(repo),
        "tool_input": {
            "command": "sed -i \\\n-e 's/old/new/' curriculum/tracked.md",
        },
    }

    result = _run(repo, payload)

    assert result.returncode == 2, result.stderr
    assert "tracked_primary_checkout" in result.stderr


def test_write_capable_bash_redirect_blocked(repo: Path):
    payload = {
        "tool_name": "Bash",
        "cwd": str(repo),
        "tool_input": {"command": "echo tampered > curriculum/tracked.md"},
    }
    result = _run(repo, payload)
    assert result.returncode == 2, result.stderr
    assert ".worktrees/dispatch/" in result.stderr


def test_write_capable_bash_tee_blocked(repo: Path):
    payload = {
        "tool_name": "Bash",
        "cwd": str(repo),
        "tool_input": {"command": "echo x | tee curriculum/tracked.md"},
    }
    result = _run(repo, payload)
    assert result.returncode == 2, result.stderr


def test_bash_redirect_to_gitignored_allowed(repo: Path):
    payload = {
        "tool_name": "Bash",
        "cwd": str(repo),
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
        "tool_name": "Bash",
        "cwd": str(worktree),
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
            "cat > /tmp/brief.md <<'EOF'\n... if >15% of the last 30 consecutive live passages ...\nEOF",
            ["/tmp/brief.md"],
        ),
        # Body text with markdown backtick code spans (#4855 live repro).
        (
            "cat > /tmp/brief.md <<'EOF'\nrun `.venv/bin/python scripts/x.py` then check\nEOF",
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
    ],
)
def test_bash_git_write_intents_allowlisted_or_ignored(command):
    intents = hook.bash_git_write_intents(command)
    # No blocking intents: either empty or allowlisted-only.
    assert all(i.get("allowlisted") for i in intents)


def test_bash_git_write_intents_honors_dash_c():
    intents = hook.bash_git_write_intents("git -C .worktrees/dispatch/claude/task-1 apply /tmp/x.diff")
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
    """Pinned residual: pathless worktree applies are checked by CI/merge diff layers."""
    worktree = repo / ".worktrees/dispatch/claude/task-1"
    payload = {
        "tool_name": "Bash",
        "cwd": str(worktree),
        "tool_input": {"command": "git apply /tmp/worker.diff"},
    }
    result = _run(repo, payload)
    assert result.returncode == 0, result.stderr


def test_git_add_control_path_in_worktree_allowed(repo: Path):
    worktree = repo / ".worktrees/dispatch/claude/task-1"
    payload = {
        "tool_name": "Bash",
        "cwd": str(worktree),
        "tool_input": {
            "command": "git add agents_extensions/shared/hooks/guard-pr-merge.py",
        },
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
        timeout=30,
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
        "tool_input": {"command": f"git -C {worktree} mv curriculum/tracked.md curriculum/renamed.md"},
    }
    result = _run(repo, payload)
    assert result.returncode == 0, result.stderr


def test_git_checkout_branch_only_blocked_by_effective_cwd_guard(repo: Path):
    """The write guard owns branch mutations after effective-cwd resolution."""
    payload = {
        "tool_name": "Bash",
        "cwd": str(repo),
        "tool_input": {"command": "git checkout -b feature-x"},
    }
    result = _run(repo, payload)
    assert result.returncode == 2, result.stderr


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


def test_bash_redirect_to_gitignored_claude_archive_is_allowed(repo: Path):
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


def test_bash_shell_var_reassignment_not_expanded(repo: Path):
    """#5404 CF F001: multi-assign $A must not expand to last (benign) value."""
    payload = {
        "tool_name": "Bash",
        "cwd": str(repo),
        "tool_input": {
            "command": ("A=curriculum/tracked.md; echo x > $A; A=local_state/ok.log"),
        },
    }
    result = _run(repo, payload)
    # Must not allow (would dirty tracked file under bash's true binding).
    assert result.returncode == 2, result.stderr
    assert "unresolved_shell_variable" in result.stderr or "tracked_primary" in result.stderr


# ===========================================================================
# #8500: same-command $VAR paths are expanded before the containment check
# ===========================================================================


@pytest.mark.parametrize(
    "command, text, unresolved_at",
    [
        ("S=/tmp/x; cat > $S/a.md", "/tmp/x/a.md", None),
        ('S=/tmp/x && echo hi > "$S/b.txt"', "/tmp/x/b.txt", None),
        ("export S=/tmp/y; echo x > ${S}/f", "/tmp/y/f", None),
        ("A=/tmp; B=$A/b; echo x > $B/f", "/tmp/b/f", None),
        # Quoted / escaped expansion characters stay literal.
        ("echo x > '$HOME/f'", "$HOME/f", None),
        ('echo x > "~/f"', "~/f", None),
        # Unknown values: never assigned, $(...), backticks, subshell- or
        # pipeline-scoped, prefix-only, re-bound, or after source/eval.
        ("echo x > $UNSET/f", "$UNSET/f", 0),
        ("S=$(pwd); echo x > $S/f", "$S/f", 0),
        ("S=`pwd`; echo x > $S/f", "$S/f", 0),
        ("(S=/tmp/x); echo x > $S/f", "$S/f", 0),
        ("S=/tmp/x | cat; echo x > $S/f", "$S/f", 0),
        ("S=/tmp/x cmd > $S/f", "$S/f", 0),
        ("S=/tmp/x; for S in a; do echo x > $S/f; done", "$S/f", 0),
        ("S=/tmp/x; source env.sh; echo x > $S/f", "$S/f", 0),
        ("echo x > /tmp/$X/y", "/tmp/$X/y", 5),
    ],
)
def test_bash_write_targets_expand_same_command_variables(command, text, unresolved_at):
    (target,) = hook.bash_write_targets(command)
    assert target == text
    assert target.unresolved_at == unresolved_at


def test_bash_write_targets_expand_home_and_tilde(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("HOME", "/home/someone")
    assert hook.bash_write_targets("echo x > ~/f; echo y > $HOME/g") == [
        "/home/someone/f",
        "/home/someone/g",
    ]


def test_bash_git_write_intents_expand_dash_c_variable():
    (intent,) = hook.bash_git_write_intents("W=/r/.worktrees/dispatch/a/b; git -C $W add f")
    assert intent["c_path"] == "/r/.worktrees/dispatch/a/b"


def _bash(
    repo: Path,
    command: str,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    payload = {
        "tool_name": "Bash",
        "cwd": str(cwd or repo),
        "tool_input": {"command": command},
    }
    return _run(repo, payload, env)


@pytest.mark.parametrize(
    "command",
    [
        "S=/tmp/x; cat > $S/a.md",
        'S=/tmp/x && echo hi > "$S/b.txt"',
        "S=/tmp/x; echo hi | tee $S/c.txt",
        "echo x > ~/scratch-8500.txt",
        # First element of a ``||`` chain always runs, so it binds (like ``&&``).
        "S=/tmp/x || true; echo x > $S/f",
        "S=/tmp/x; if true; then echo x > $S/f; fi",
    ],
)
def test_bash_expanded_variable_write_outside_primary_allowed(repo: Path, command: str):
    result = _bash(repo, command)
    assert result.returncode == 0, result.stderr


def test_bash_expanded_variable_git_dash_c_worktree_allowed(repo: Path):
    worktree = repo / ".worktrees/dispatch/claude/task-1"
    result = _bash(repo, f"W={worktree}; git -C $W add f")
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize(
    "command, reason",
    [
        ("S={repo}; echo x > $S/f", "untracked_primary_checkout"),
        ("S={repo}; echo x > $S/curriculum/tracked.md", "tracked_primary_checkout"),
        ("echo x > $UNSET/f", "unresolved_shell_variable"),
        ("S=$(pwd); echo x > $S/f", "unresolved_shell_variable"),
        ("(S=/tmp/x); echo x > $S/f", "unresolved_shell_variable"),
        ("echo x > '$HOME/f'", "untracked_primary_checkout"),
        # A literal prefix that is the primary root or one of its ancestors
        # can still reach the primary through the unknown component.
        ("echo x > {repo}/$X/f", "unresolved_shell_variable"),
        ("echo x > {parent}/$X/f", "unresolved_shell_variable"),
        # An unknown component may be absolute, empty or hold ``..``: no literal
        # prefix proves the path stays out of the primary.
        ("echo x > /nonexistent-8500/$X/f", "unresolved_shell_variable"),
        ("echo x > local_state/$X.log", "unresolved_shell_variable"),
        ("echo x > /tmp/$X/AGENTS.md", "unresolved_shell_variable"),
        ("X=$(echo ../{parent_rel}); echo x > /tmp/$X/AGENTS.md", "unresolved_shell_variable"),
        # A literal value holding ``..`` resolves lexically into the primary.
        ("X=../{repo_rel}; echo x > /tmp/$X/AGENTS.md", "untracked_primary_checkout"),
        # Only unconditional top-level literal assignments are trusted (#8500 r2).
        ("false && S=/tmp; echo x > $S/AGENTS.md", "unresolved_shell_variable"),
        ("true || S=/tmp; echo x > $S/AGENTS.md", "unresolved_shell_variable"),
        ("false &&\nS=/tmp\necho x > $S/AGENTS.md", "unresolved_shell_variable"),
        ("S={repo}; true && S=/tmp; echo x > $S/AGENTS.md", "unresolved_shell_variable"),
        ("if true; then S=/tmp; fi; echo > $S/f", "unresolved_shell_variable"),
        ("for i in 1; do S=/tmp; done; echo > $S/f", "unresolved_shell_variable"),
        ("case x in x) S=/tmp;; esac; echo > $S/f", "unresolved_shell_variable"),
        ("{ S=/tmp; }; echo > $S/f", "unresolved_shell_variable"),
        ("f() { S=/tmp; }; f; echo > $S/f", "unresolved_shell_variable"),
        ("(S=/tmp); echo > $S/f", "unresolved_shell_variable"),
        ("S=/tmp; ((S = 5)); echo > $S/f", "unresolved_shell_variable"),
        ("S=/tmp | cat; echo > $S/f", "unresolved_shell_variable"),
        ("S=/tmp &\necho > $S/f", "unresolved_shell_variable"),
        # Deferred / repeated bodies must not see a stale value.
        ("S=/tmp; f() { echo > $S/f; }; S={repo}; f", "unresolved_shell_variable"),
        ("S=/tmp; while true; do echo > $S/f; S={repo}; done", "unresolved_shell_variable"),
        ("S=/tmp; declare -n R=S; R={repo}; echo > $S/f", "unresolved_shell_variable"),
        ("S=/tmp; eval 'S=x'; echo > $S/f", "unresolved_shell_variable"),
        ("S=/tmp; trap 'S=x' DEBUG; echo > $S/f", "unresolved_shell_variable"),
        ("S=/tmp; echo ${S:=x}; echo > $S/f", "unresolved_shell_variable"),
        ("S='/tmp /x'; tee $S/f", "unresolved_shell_variable"),
        ("IFS=/; S=/tmp/x; tee $S/f", "unresolved_shell_variable"),
        ("S=/tmp; read S; echo > $S/f", "unresolved_shell_variable"),
        ("S=/tmp; unset S; echo > $S/f", "unresolved_shell_variable"),
        ("S=/tmp; printf -v S %s x; echo > $S/f", "unresolved_shell_variable"),
        ("S=/tmp; let S=5; echo > $S/f", "unresolved_shell_variable"),
    ],
)
def test_bash_variable_write_into_primary_still_blocked(repo: Path, command: str, reason: str):
    for placeholder, value in (
        ("{repo_rel}", str(repo).lstrip("/")),
        ("{parent_rel}", str(repo.parent).lstrip("/")),
        ("{repo}", str(repo)),
        ("{parent}", str(repo.parent)),
    ):
        command = command.replace(placeholder, value)
    result = _bash(repo, command)
    assert result.returncode == 2, result.stderr
    assert reason in result.stderr


@pytest.mark.parametrize(
    "command",
    [
        "W={repo}; git -C $W add curriculum/tracked.md",
        "git -C $UNSET add curriculum/tracked.md",
        "W=$(pwd); git -C $W apply /tmp/worker.diff",
    ],
)
def test_bash_variable_git_dash_c_primary_still_blocked(repo: Path, command: str):
    worktree = repo / ".worktrees/dispatch/claude/task-1"
    result = _bash(repo, command.format(repo=repo), cwd=worktree)
    assert result.returncode == 2, result.stderr
    assert "#5396" in result.stderr


def test_bash_read_home_shadows_inherited_home(repo: Path):
    """#8500 r2: ``read HOME`` must not fall back to the incoming ``$HOME``."""
    command = f"read HOME <<< '{repo}'; echo x > \"$HOME/AGENTS.md\""
    result = _bash(repo, command, env={"HOME": "/tmp"})
    assert result.returncode == 2, result.stderr
    assert "unresolved_shell_variable" in result.stderr


@pytest.mark.parametrize(
    "template, reason",
    [
        ("echo x > {primary_parent}/mai?/curriculum/tracked.md", "undecidable_glob_write_target"),
        ("echo x > {primary}/curriculum/{{tracked,new}}.md", "undecidable_glob_write_target"),
        ("cd {primary}; echo x > curriculum/tracked.md", "tracked"),
        ("command -p tee {primary}/curriculum/tracked.md", "tracked"),
        ("builtin tee {primary}/curriculum/tracked.md", "tracked"),
        ("exec tee {primary}/curriculum/tracked.md", "tracked"),
        ("cat <<EOF\n$(echo x > {primary}/curriculum/tracked.md)\nEOF", "tracked"),
        ("echo {primary}/curriculum/tracked.md | xargs tee", "undecidable_xargs_stdin_target"),
        ("find /tmp -maxdepth 0 -exec tee {primary}/curriculum/tracked.md \\;", "tracked"),
        ("$(cd {primary} && tee curriculum/tracked.md)", "tracked"),
        ("pushd {primary}; tee curriculum/tracked.md", "tracked"),
        ("find /tmp -exec sh -c 'echo x > {primary}/curriculum/tracked.md' \\;", "tracked"),
        ("env -i tee {primary}/curriculum/tracked.md", "tracked"),
        (
            "env -u HOME nice -n 2 timeout -s TERM 2 stdbuf -oL nohup sudo -u root tee {primary}/curriculum/tracked.md",
            "tracked",
        ),
        ("cat <<EOF\n`echo x > {primary}/curriculum/tracked.md`\nEOF", "tracked"),
        ("find {primary} -execdir tee relative.md \\;", "undecidable_find_execdir_target"),
        ("cd $UNKNOWN; echo x > relative.md", "undecidable_write_target_after_cd"),
    ],
)
def test_issue_8785_primary_bypasses_block(repo: Path, template: str, reason: str):
    worktree = repo / ".worktrees/dispatch/claude/task-1"
    command = template.format(primary=repo, primary_parent=repo.parent)
    result = _run(repo, {"tool_name": "Bash", "cwd": str(worktree), "tool_input": {"command": command}})
    assert result.returncode == 2, result.stderr
    assert reason in result.stderr


def test_issue_8785_quoted_heredoc_body_is_inert(repo: Path):
    worktree = repo / ".worktrees/dispatch/claude/task-1"
    command = f"cat <<'EOF'\n$(echo x > {repo}/curriculum/tracked.md)\nEOF"
    result = _run(repo, {"tool_name": "Bash", "cwd": str(worktree), "tool_input": {"command": command}})
    assert result.returncode == 0, result.stderr


def test_issue_8785_mixed_heredocs_keep_quoted_body_inert(repo: Path):
    worktree = repo / ".worktrees/dispatch/claude/task-1"
    command = f"cat <<'INERT' <<ACTIVE\n$(echo x > {repo}/curriculum/tracked.md)\nINERT\nplain text\nACTIVE"
    result = _run(repo, {"tool_name": "Bash", "cwd": str(worktree), "tool_input": {"command": command}})
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize("body", ["`cd {primary}`", "$((1 > {primary}/curriculum/tracked.md))"])
def test_issue_8785_heredoc_nonwriting_expansion_does_not_change_parent_cwd(repo: Path, body: str):
    worktree = repo / ".worktrees/dispatch/claude/task-1"
    command = "cat <<EOF\n" + body.format(primary=repo) + "\nEOF\ntee safe.txt"
    result = _run(repo, {"tool_name": "Bash", "cwd": str(worktree), "tool_input": {"command": command}})
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize("target", ["local_state/out-?.log", ".worktrees/dispatch/claude/task-1/out-?.log"])
def test_issue_8785_safe_globs_remain_allowed(repo: Path, target: str):
    worktree = repo / ".worktrees/dispatch/claude/task-1"
    command = f"echo x > {repo / target}"
    result = _run(repo, {"tool_name": "Bash", "cwd": str(worktree), "tool_input": {"command": command}})
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize(
    "template, blocked",
    [
        ("/tmp/out-?.txt", False),
        ("{primary}/out-?.txt", True),
        ("{grandparent}/*/main/AGENTS.md", True),
        ("{primary}/{{a,b}}.md", True),
        ("/tmp/{{a,b}}.txt", False),
        ("{parent}/**/AGENTS.md", True),
    ],
)
def test_issue_8785_glob_reach_depends_on_component(repo: Path, template: str, blocked: bool):
    worktree = repo / ".worktrees/dispatch/claude/task-1"
    command = f"echo x > {template.format(primary=repo, parent=repo.parent, grandparent=repo.parent.parent)}"
    result = _bash(repo, command, cwd=worktree)
    assert result.returncode == (2 if blocked else 0), result.stderr
    if blocked:
        assert "undecidable_glob_write_target" in result.stderr


@pytest.mark.parametrize(
    "template",
    [
        "cp /tmp/payload {parent}/m*",
        "cp /tmp/payload {parent}/mai?",
        "cp -t {parent}/m* /tmp/payload",
        "cp /tmp/payload {parent}/{{main,other}}",
        "rm -rf {parent}/m*",
        "chmod 700 {parent}/m*",
        "mv {parent}/m* /tmp/x",
        "ln -s /tmp/payload {parent}/m*",
        "rsync -a /tmp/payload {parent}/m*",
        "cd {parent}; rm -rf m*",
        "cd {parent}; cp /tmp/payload m*",
    ],
)
def test_issue_8785_final_component_can_match_primary(repo: Path, template: str):
    worktree = repo / ".worktrees/dispatch/claude/task-1"
    command = template.format(parent=repo.parent)
    result = _bash(repo, command, cwd=worktree)
    assert result.returncode == 2, (command, result.stderr)
    assert "undecidable_glob_write_target" in result.stderr


@pytest.mark.parametrize("pattern", ["*", "m*", "mai?", "{main,other}", "{other,ma*}", "{main,{other}}", "{other,{main,sibling}}"])
def test_issue_8785_parent_pattern_matching_primary_blocks(repo: Path, pattern: str):
    worktree = repo / ".worktrees/dispatch/claude/task-1"
    result = _bash(repo, f"rm -rf {repo.parent}/{pattern}", cwd=worktree)
    assert result.returncode == 2, result.stderr
    assert "undecidable_glob_write_target" in result.stderr


@pytest.mark.parametrize("pattern", ["other*", "{other,sibling}", "out-?.txt", "{a,b}.txt"])
def test_issue_8785_parent_pattern_matching_siblings_allowed(repo: Path, pattern: str):
    worktree = repo / ".worktrees/dispatch/claude/task-1"
    result = _bash(repo, f"rm -rf {repo.parent}/{pattern}", cwd=worktree)
    assert result.returncode == 0, result.stderr


def test_issue_8785_hidden_component_glob_semantics():
    assert not hook._final_component_matches("*", ".main")
    assert not hook._final_component_matches("[.]main", ".main")
    assert hook._final_component_matches(".m*", ".main")
    assert hook._final_component_matches("{other,.m*}", ".main")
    assert hook._final_component_matches("{other,{.main,sibling}}", ".main")


@pytest.mark.parametrize(
    "command",
    [
        "cat /tmp/read-only",
        "grep needle /tmp/read-only",
        "find /tmp -maxdepth 0",
        "git log -1",
        "cd /tmp; tee scratch.txt",
        "tee /tmp/scratch.txt",
        "echo /tmp/scratch.txt | xargs tee",
        "echo x > /tmp/out-?.txt",
    ],
)
def test_issue_8785_safe_commands_remain_allowed(repo: Path, command: str):
    worktree = repo / ".worktrees/dispatch/claude/task-1"
    result = _run(repo, {"tool_name": "Bash", "cwd": str(worktree), "tool_input": {"command": command}})
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize(
    "template, reason",
    [
        ("cd {primary}; git add curriculum/tracked.md", "tracked"),
        ("pushd {primary}; git apply /tmp/change.diff", "git_mediated_primary_worktree"),
        ("cd $UNKNOWN; git add file.txt", "undecidable_git_cwd_after_cd"),
    ],
)
def test_issue_8785_git_writer_uses_effective_cwd(repo: Path, template: str, reason: str):
    worktree = repo / ".worktrees/dispatch/claude/task-1"
    command = template.format(primary=repo)
    result = _run(repo, {"tool_name": "Bash", "cwd": str(worktree), "tool_input": {"command": command}})
    assert result.returncode == 2, result.stderr
    assert reason in result.stderr


@pytest.mark.parametrize(
    "command",
    [
        "eval 'HOME=/x'; echo x > ~/f",
        "HOME=/x cmd; echo x > ~/f",
        "f() { echo x > ~/f; }; HOME=/tmp; f",
    ],
)
def test_bash_home_clobbered_or_deferred_is_unknown(repo: Path, command: str):
    result = _bash(repo, command, env={"HOME": "/tmp"})
    assert result.returncode == 2, result.stderr
    assert "unresolved_shell_variable" in result.stderr


def test_bash_home_assigned_literal_still_expands(repo: Path):
    result = _bash(repo, "HOME=/tmp/h; echo x > ~/f", env={"HOME": str(repo)})
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize(
    "command, name, value",
    [
        ("S=/tmp/x || true; echo x > $S/f", "S", "/tmp/x/f"),
        ("S=/tmp/x && echo x > $S/f", "S", "/tmp/x/f"),
        ("echo a; S=/tmp/x\necho x > $S/f", "S", "/tmp/x/f"),
        ("if true; then :; fi; S=/tmp/x; echo x > $S/f", "S", "/tmp/x/f"),
    ],
)
def test_unconditional_top_level_assignment_is_known(command, name, value):
    (target,) = hook.bash_write_targets(command)
    assert target == value and target.unresolved_at is None


def test_bash_write_targets_see_through_compound_keywords():
    assert hook.bash_write_targets("if true; then echo x > /tmp/a; fi > /tmp/b") == [
        "/tmp/a",
        "/tmp/b",
    ]
    assert hook.bash_write_targets("for i in 1; do echo x | tee /tmp/a; done") == ["/tmp/a"]


@pytest.mark.parametrize(
    "template, reason",
    [
        ("CDPATH={primary} cd agents_extensions; echo x > HOOKS.md", "undecidable_write_target_after_cd"),
        ("env -C {primary} tee AGENTS.md", "AGENTS.md"),
        ("env --chdir={primary} tee AGENTS.md", "AGENTS.md"),
        ("sudo env -C {primary} tee AGENTS.md", "AGENTS.md"),
        ("echo x >& {primary}/AGENTS.md", "AGENTS.md"),
        ("echo x &>> {primary}/AGENTS.md", "AGENTS.md"),
        ("echo x <> {primary}/AGENTS.md", "AGENTS.md"),
        ("cp /tmp/source {primary}/AGENTS.md", "AGENTS.md"),
        ("mv /tmp/source {primary}/AGENTS.md", "AGENTS.md"),
        ("install -m 644 /tmp/source {primary}/AGENTS.md", "AGENTS.md"),
        ("ln -s /tmp/source {primary}/AGENTS.md", "AGENTS.md"),
        ("rsync -a /tmp/source {primary}/AGENTS.md", "AGENTS.md"),
        ("cp -t {primary} /tmp/source", "primary"),
        ("cp -at {primary} /tmp/source", "primary"),
        ("cp -at{primary} /tmp/source", "primary"),
        ("mv -ft {primary} /tmp/source", "primary"),
        ("ln -sft {primary} /tmp/source", "primary"),
        ("cp -S .bak -t {primary} /tmp/source", "primary"),
        ("cp --suffix=.bak --target-directory={primary} -- /tmp/source", "primary"),
        ("mv --suffix=.bak --target-directory={primary} /tmp/source", "primary"),
        ("mv -- {primary}/AGENTS.md /tmp/stolen.md", "AGENTS.md"),
        ("install -m 644 -t {primary} /tmp/source", "primary"),
        ("install -d {primary}/newdir", "newdir"),
        ("install -dv {primary}/newdir", "newdir"),
        ("mv --target-directory={primary} /tmp/source", "primary"),
        ("mv {primary}/AGENTS.md /tmp/stolen.md", "AGENTS.md"),
        ("mv -T {primary}/AGENTS.md /tmp/stolen.md", "AGENTS.md"),
        ("rsync --remove-source-files {primary}/AGENTS.md /tmp/stolen.md", "AGENTS.md"),
        ("dd if=/tmp/source of={primary}/AGENTS.md", "AGENTS.md"),
        ("eval 'echo x > {primary}/AGENTS.md'", "AGENTS.md"),
        ("CMD='echo x > {primary}/AGENTS.md'; eval \"$CMD\"", "AGENTS.md"),
        ('eval "$COMMAND {primary}/AGENTS.md"', "undecidable_eval_primary_target"),
        ("eval 'git -C {primary} apply /tmp/change.diff'", "git_mediated_primary_worktree"),
        ("echo {primary}/AGENTS.md | parallel tee", "undecidable_xargs_stdin_target"),
        ("parallel -j 2 tee ::: {primary}/AGENTS.md", "undecidable_xargs_stdin_target"),
        ("parallel cp /tmp/source ::: {primary}/AGENTS.md", "undecidable_xargs_stdin_target"),
        ("cd {primary}; parallel tee ::: AGENTS.md", "undecidable_xargs_stdin_target"),
        ("cd {primary}; echo AGENTS.md | xargs tee", "undecidable_xargs_stdin_target"),
        ("cd {primary}; find . -exec tee {{}} \\;", "tracked_primary_checkout"),
        ("cd {primary}; tee AGENTS.md", "AGENTS.md"),
        ('cd {primary}; eval "$COMMAND"', "undecidable_eval_primary_target"),
        ("rm {primary}/AGENTS.md", "AGENTS.md"),
        ("unlink {primary}/AGENTS.md", "AGENTS.md"),
        ("rmdir {primary}/newdir", "newdir"),
        ("truncate -s 0 {primary}/AGENTS.md", "AGENTS.md"),
        ("shred -u {primary}/AGENTS.md", "AGENTS.md"),
        ("chmod 600 {primary}/AGENTS.md", "AGENTS.md"),
        ("chown root:root {primary}/AGENTS.md", "AGENTS.md"),
        ("touch {primary}/AGENTS.md", "AGENTS.md"),
        ("sed -i 's/a/b/' {primary}/AGENTS.md", "AGENTS.md"),
        ("perl -pi -e 's/a/b/' {primary}/AGENTS.md", "AGENTS.md"),
        ("find {primary} -delete", "primary"),
        ("cd {primary}; find . -delete", "primary"),
        ("find {primary} -name AGENTS.md -delete", "primary"),
        ("find -- {primary} -delete", "primary"),
        ("pushd -n /tmp; rm -rf ../../../../AGENTS.md", "AGENTS.md"),
        ("pushd -n /tmp; popd -n; rm -rf ../../../../AGENTS.md", "AGENTS.md"),
        ("rsync -a --backup-dir={primary} /tmp/src /tmp/dest", "primary"),
        ("rsync -a --log-file={primary}/AGENTS.md /tmp/a /tmp/b", "AGENTS.md"),
        ("rsync --write-batch={primary}/AGENTS.md /tmp/a /tmp/b", "AGENTS.md"),
        ("rsync --only-write-batch {primary}/AGENTS.md /tmp/a /tmp/b", "AGENTS.md"),
        ("rsync --partial-dir={primary} /tmp/a /tmp/b", "primary"),
        ("rsync --temp-dir {primary} /tmp/a /tmp/b", "primary"),
        ("sort -o {primary}/AGENTS.md /tmp/a", "AGENTS.md"),
        ("sort --output={primary}/AGENTS.md /tmp/a", "AGENTS.md"),
        ("sort -o{primary}/AGENTS.md /tmp/a", "AGENTS.md"),
        ("tar -cf {primary}/AGENTS.md /tmp/a", "AGENTS.md"),
        ("tar --create --file={primary}/AGENTS.md /tmp/a", "AGENTS.md"),
        ("curl -o {primary}/AGENTS.md https://example.test/a", "AGENTS.md"),
        ("curl --output={primary}/AGENTS.md https://example.test/a", "AGENTS.md"),
        ("cd {primary}; curl -O https://example.test/AGENTS.md", "AGENTS.md"),
        ("wget -O {primary}/AGENTS.md https://example.test/a", "AGENTS.md"),
        ("wget -P {primary} https://example.test/a", "primary"),
        ("git -C {primary} archive -o AGENTS.md HEAD", "AGENTS.md"),
        ("sqlite3 {primary}/AGENTS.md 'select 1'", "AGENTS.md"),
        ("sqlite3 /tmp/a.db '.output {primary}/AGENTS.md'", "AGENTS.md"),
        ("sqlite3 /tmp/a.db '.backup {primary}/AGENTS.md'", "AGENTS.md"),
        ("git -C {primary} clean -fdx", "git_mediated_primary_worktree"),
        ("git -C {primary} clean -e -n -fdx", "git_mediated_primary_worktree"),
        ("git -C {primary} reset --hard", "git_mediated_primary_worktree"),
        ("git -C {primary} reset --merge", "git_mediated_primary_worktree"),
        ("git -C {primary} reset --keep", "git_mediated_primary_worktree"),
        ("git -C {primary} checkout -f HEAD", "git_mediated_primary_worktree"),
        ("git -C {primary} read-tree -u HEAD", "git_mediated_primary_worktree"),
        ('eval "$CMD"', "undecidable_eval_primary_target"),
    ],
)
def test_issue_8785_review_writers_block(repo: Path, template: str, reason: str):
    worktree = repo / ".worktrees/dispatch/claude/task-1"
    command = template.format(primary=repo)
    result = _run(repo, {"tool_name": "Bash", "cwd": str(worktree), "tool_input": {"command": command}})
    assert result.returncode == 2, result.stderr
    assert reason in result.stderr


@pytest.mark.parametrize(
    "template",
    [
        "find {primary} -exec rm {{}} \\;",
        "find {primary} -exec rm -rf {{}} +",
        "find {primary} -exec tee {{}} \\;",
        "find -D exec {primary} -delete",
        "find -D exec -O2 {primary} -delete",
        "find -files0-from {primary}/list -delete",
        "find /tmp -fprintf {primary}/AGENTS.md '%p'",
        "find /tmp -fprint {primary}/AGENTS.md",
        "find /tmp -fprint0 {primary}/AGENTS.md",
        "find /tmp -fls {primary}/AGENTS.md",
        "curl --output-dir {primary} -O https://example.test/a",
        "curl --output-dir={primary} -o AGENTS.md https://example.test/a",
        "curl -D {primary}/AGENTS.md https://example.test/a",
        "curl -c {primary}/AGENTS.md https://example.test/a",
        "wget -o {primary}/AGENTS.md https://example.test/a",
        "sort -T {primary} -o /tmp/out /tmp/in",
        "sort {primary}/AGENTS.md -o /tmp/out",  # accepted long-tail input false positive
        "xargs sort -o {primary}/AGENTS.md",
        "parallel sort -o {primary}/AGENTS.md ::: /tmp/a",
        "sqlite3 /tmp/a.db '.save {primary}/AGENTS.md'",
        'sh -c "$CMD"',
        'bash -c "$CMD"',
        'zsh -c "$CMD"',
        'dash -c "$CMD"',
        "git -C {primary} switch -f other",
        "git -C {primary} checkout other",
        "git -C {primary} merge other",
        "git -C {primary} pull",
        "git -C {primary} rebase other",
        "git -C {primary} cherry-pick HEAD~1",
        "git -C {primary} revert HEAD",
        "git -C {primary} am /tmp/a.patch",
        "git -C {primary} apply /tmp/a.patch",
        "git -C {primary} stash pop",
        "git -C {primary} stash apply",
        "git -C {primary} read-tree -u HEAD",
        "sh -c 'git -C {primary} merge other'",
        "git worktree remove {primary}",
        "tar -xf /tmp/x.tar -C {primary}",
        "unzip /tmp/x.zip -d {primary}",
        "patch -d {primary} -i /tmp/x.patch",
        "ffmpeg -i /tmp/in.mp4 {primary}/out.mp4",
        "convert /tmp/in.png {primary}/out.png",
    ],
)
def test_issue_8785_principle_blocks_review_escapes(repo: Path, template: str):
    worktree = repo / ".worktrees/dispatch/claude/task-1"
    result = _run(
        repo, {"tool_name": "Bash", "cwd": str(worktree), "tool_input": {"command": template.format(primary=repo)}}
    )
    assert result.returncode == 2, (template, result.stderr)


@pytest.mark.parametrize(
    "command",
    [
        "sort -o../../../../AGENTS.md /tmp/in",
        "curl -o../../../../AGENTS.md https://example.test/a",
        "tar -cf../../../../AGENTS.md /tmp/a",
        "wget -O../../../../AGENTS.md https://example.test/a",
        "unzip /tmp/x.zip -d../../../../",
        "patch -o../../../../AGENTS.md -i /tmp/x.patch",
        "cd {primary}; sort -oAGENTS.md /tmp/in",
        "cd {primary}; curl -oAGENTS.md https://example.test/a",
        "ruff format {primary}/AGENTS.md",
        "ruff check --fix {primary}/AGENTS.md",
        "ruff check --fix-only {primary}/AGENTS.md",
        "ruff check --fix --unsafe-fixes {primary}/AGENTS.md",
        "black {primary}/AGENTS.md",
        "isort {primary}/AGENTS.md",
        "prettier --write {primary}/AGENTS.md",
        "prettier -w {primary}/AGENTS.md",
        "eslint --fix {primary}/AGENTS.md",
        "clang-format -i {primary}/AGENTS.md",
        "gofmt -w {primary}/AGENTS.md",
        "gofmt -l -w {primary}/AGENTS.md",
        "gofmt -lw {primary}/AGENTS.md",
        "rustfmt {primary}/AGENTS.md",
        "shfmt -w {primary}/AGENTS.md",
        "markdownlint --fix {primary}/AGENTS.md",
        "markdownlint-cli2 --fix {primary}/AGENTS.md",
        "bash -lc 'echo x > {primary}/AGENTS.md'",
        "bash -ec 'echo x > {primary}/AGENTS.md'",
        "zsh -lc 'echo x > {primary}/AGENTS.md'",
        "dash -ec 'echo x > {primary}/AGENTS.md'",
        "sh -lc 'echo x > {primary}/AGENTS.md'",
        "bash -o pipefail -lc 'echo x > {primary}/AGENTS.md'",
        "bash +O extglob -lc 'echo x > {primary}/AGENTS.md'",
        "bash -lc -- 'echo x > {primary}/AGENTS.md'",
        "bash --noprofile --norc -lc 'echo x > {primary}/AGENTS.md'",
        "bash --login --rcfile /tmp/bashrc -lc 'echo x > {primary}/AGENTS.md'",
        "bash --init-file=/tmp/bashrc -lc 'echo x > {primary}/AGENTS.md'",
    ],
)
def test_issue_8785_final_review_writers_block(repo: Path, command: str):
    worktree = repo / ".worktrees/dispatch/claude/task-1"
    result = _bash(repo, command.format(primary=repo), cwd=worktree)
    assert result.returncode == 2, (command, result.stderr)


@pytest.mark.parametrize(
    "command",
    [
        "ruff check {primary}/AGENTS.md",
        "ruff format --check {primary}/AGENTS.md",
        "prettier --check {primary}/AGENTS.md",
        "black --check {primary}/AGENTS.md",
        "isort --check-only {primary}/AGENTS.md",
        "rustfmt --check {primary}/AGENTS.md",
        "ruff check --unsafe-fixes {primary}/AGENTS.md",
        "bash -- -c 'echo x > {primary}/AGENTS.md'",
        "cd {primary}; sort -o/tmp/safe-output /tmp/in",
        "cd {primary}; tar -cf/tmp/safe-archive /tmp/in",
        "find -files0-from /tmp/list -delete",
        "cat /tmp/list | xargs -I{{}} sh -c 'echo x > {{}}'",
        "sort -X../../../../AGENTS.md /tmp/in",
    ],
)
def test_issue_8785_final_review_allowed(repo: Path, command: str):
    worktree = repo / ".worktrees/dispatch/claude/task-1"
    result = _bash(repo, command.format(primary=repo), cwd=worktree)
    assert result.returncode == 0, (command, result.stderr)


@pytest.mark.parametrize(
    "shell",
    [
        "bash -lc",
        "bash -o pipefail -lc",
        "bash +O extglob -lc",
        "bash --noprofile --norc -lc",
        "bash --login --rcfile /tmp/bashrc -lc",
        "bash --init-file=/tmp/bashrc -lc",
        "sh -lc",
        "dash -ec",
        "zsh -lc",
    ],
)
@pytest.mark.parametrize("target_primary", [True, False])
def test_issue_8785_shell_git_cluster_uses_same_extractor(repo: Path, shell: str, target_primary: bool):
    worktree = repo / ".worktrees/dispatch/claude/task-1"
    target = repo if target_primary else worktree
    command = f"{shell} 'cd {target} && git add AGENTS.md'"
    result = _bash(repo, command, cwd=repo)
    assert result.returncode == (2 if target_primary else 0), (command, result.stderr)


@pytest.mark.parametrize(
    "template",
    [
        "curl -fsSL URL -o /tmp/x",
        "wget -O{worktree}/out https://example.test/AGENTS.md",
        "wget -P{worktree} https://example.test/AGENTS.md",
        "sort -k1,1 /tmp/in -o /tmp/out",
        "shfmt -i 2 -w {worktree}/f.sh",
        "shfmt -ln bash -p -w {worktree}/f.sh",
        "bash -lc 'cat AGENTS.md'",
        "git -C {worktree} status",
        "curl -K {primary}/AGENTS.md -o /tmp/x URL",
        "curl -T {primary}/AGENTS.md -o /tmp/x URL",
        "patch -i {primary}/AGENTS.md -o /tmp/x",
        "split -l 2 /tmp/in {worktree}/part",
    ],
)
def test_issue_8785_primary_cwd_has_no_phantom_write_target(repo: Path, template: str):
    worktree = repo / ".worktrees/dispatch/claude/task-1"
    command = template.format(primary=repo, worktree=worktree)
    result = _bash(repo, command, cwd=repo)
    assert result.returncode == 0, (command, result.stderr)


def test_issue_8785_clustered_curl_remote_name_writes_in_primary_cwd(repo: Path):
    result = _bash(repo, "curl -fsSLO https://example.test/AGENTS.md", cwd=repo)
    assert result.returncode == 2, result.stderr


@pytest.mark.parametrize(
    "template",
    [
        "curl -o{target}/AGENTS.md URL",
        "wget -a{target}/AGENTS.md URL",
        "sort -o{target}/AGENTS.md /tmp/in",
        "tar -cf{target}/AGENTS.md /tmp/in",
        "unzip /tmp/in.zip -d{target}",
        "patch -o{target}/AGENTS.md -i /tmp/in.patch",
        "split /tmp/in {target}/part",
        "gofmt -lw {target}/AGENTS.md",
        "ruff check --fix-only {target}/AGENTS.md",
        "ruff check --fix --unsafe-fixes {target}/AGENTS.md",
    ],
)
@pytest.mark.parametrize("target_primary", [True, False])
def test_issue_8785_option_destinations_follow_target_worktree(repo: Path, template: str, target_primary: bool):
    worktree = repo / ".worktrees/dispatch/claude/task-1"
    target = repo if target_primary else worktree
    command = template.format(target=target)
    result = _bash(repo, command, cwd=worktree)
    assert result.returncode == (2 if target_primary else 0), (command, result.stderr)


@pytest.mark.parametrize(
    "command",
    [
        "curl --proto=https https://example.test/a -o /tmp/x",
        "sort --parallel=2 /tmp/in -o /tmp/out",
        "tar --exclude=AGENTS.md -cf /tmp/out /tmp/in",
        "tar --exclude='*.pyc' -cf /tmp/out /tmp/in",
    ],
)
def test_issue_8785_unknown_long_values_do_not_write_primary(repo: Path, command: str):
    result = _bash(repo, command, cwd=repo)
    assert result.returncode == 0, (command, result.stderr)


@pytest.mark.parametrize(
    "template",
    [
        "curl --output={target}/AGENTS.md URL",
        "wget --output-document={target}/AGENTS.md URL",
        "sort --output={target}/AGENTS.md /tmp/in",
        "tar --file={target}/AGENTS.md -c /tmp/in",
        "patch --output={target}/AGENTS.md -i /tmp/in.patch",
    ],
)
@pytest.mark.parametrize("target_primary", [True, False])
def test_issue_8785_known_long_values_follow_target(repo: Path, template: str, target_primary: bool):
    worktree = repo / ".worktrees/dispatch/claude/task-1"
    target = repo if target_primary else worktree
    command = template.format(target=target)
    result = _bash(repo, command, cwd=repo)
    assert result.returncode == (2 if target_primary else 0), (command, result.stderr)


@pytest.mark.parametrize("flags", ["-oc", "-oce"])
@pytest.mark.parametrize("target_primary", [True, False])
def test_issue_8785_bash_cluster_option_value_precedes_script(repo: Path, flags: str, target_primary: bool):
    worktree = repo / ".worktrees/dispatch/claude/task-1"
    target = repo if target_primary else worktree
    command = f"bash {flags} pipefail 'echo x > {target}/AGENTS.md'"
    result = _bash(repo, command, cwd=repo)
    assert result.returncode == (2 if target_primary else 0), (command, result.stderr)


@pytest.mark.parametrize("flag", ["-l", "-e", "-r 'a -> b'"])
@pytest.mark.parametrize("target_primary", [True, False])
def test_issue_8785_gofmt_flag_values_follow_target(repo: Path, flag: str, target_primary: bool):
    worktree = repo / ".worktrees/dispatch/claude/task-1"
    target = repo if target_primary else worktree
    command = f"gofmt -w {flag} {target}/f.go"
    result = _bash(repo, command, cwd=repo)
    assert result.returncode == (2 if target_primary else 0), (command, result.stderr)


def test_issue_8785_inherited_cdpath_makes_bare_relative_cd_unknown(repo: Path):
    worktree = repo / ".worktrees/dispatch/claude/task-1"
    result = _run(
        repo,
        {
            "tool_name": "Bash",
            "cwd": str(worktree),
            "tool_input": {"command": "cd agents_extensions; echo x > HOOKS.md"},
        },
        {"CDPATH": str(repo)},
    )
    assert result.returncode == 2, result.stderr
    assert "undecidable_write_target_after_cd" in result.stderr


@pytest.mark.parametrize(
    "command",
    [
        "cd {primary} & echo x > guard-probe.txt",
        "env -C {primary} echo x > guard-probe.txt",
        "cd {primary} | cat; echo x > guard-probe.txt",
        "echo x | cd {primary}; echo x > guard-probe.txt",
        "cat {primary}/AGENTS.md",
        "git -C {primary} log -1",
        "git -C {primary} status",
        "git -C {primary} diff",
        "git -C {primary} clean -nfdx",
        "git -C {primary} clean --dry-run -fdx",
        "git -C {primary} checkout -- AGENTS.md",
        "git -C {primary} restore AGENTS.md",
        "git -C {primary} stash drop",
        "git -C {primary} stash clear",
        "echo x > /tmp/guard-probe.txt",
        "find . -exec grep needle {{}} \\;",
        "echo {primary}/AGENTS.md | xargs grep needle",
        "cat <<'EOF'\necho x > {primary}/AGENTS.md\nEOF",
        "cp /tmp/source {worktree}/copy.txt",
        "cp -at {worktree} /tmp/source",
        "mv -ft {worktree} /tmp/source",
        "ln -sft {worktree} /tmp/source",
        "ln -s {primary}/AGENTS.md /tmp/primary-link",
        "ln -s -T {primary}/AGENTS.md /tmp/primary-link",
        "mv {worktree}/copy.txt /tmp/moved-copy.txt",
        "rsync --remove-source-files {worktree}/copy.txt /tmp/moved-copy.txt",
        "CMD='echo x > /tmp/guard-probe.txt'; eval \"$CMD\"",
        "CMD='echo x > {worktree}/copy.txt'; eval \"$CMD\"",
        "find /tmp -delete",
        "rm /tmp/guard-probe.txt",
        "mv /tmp/a /tmp/b",
        "rsync --compare-dest={primary} /tmp/a /tmp/b",
        "rsync --link-dest={primary} /tmp/a /tmp/b",
        "cp /tmp/a {worktree}/copy.txt",
        "cp --backup=numbered --suffix=.bak /tmp/a {worktree}/copy.txt",
        "rsync -a /tmp/source {worktree}/copy.txt",
        "CDPATH=; cd ./local_state; echo x > scratch.json",
        "CDPATH=; cd agents_extensions; echo x > scratch.json",
        "echo x >&1",
        "echo x >&-",
    ],
)
def test_issue_8785_review_allowed_cases(repo: Path, command: str):
    worktree = repo / ".worktrees/dispatch/claude/task-1"
    result = _run(
        repo,
        {
            "tool_name": "Bash",
            "cwd": str(worktree),
            "tool_input": {"command": command.format(primary=repo, worktree=worktree)},
        },
    )
    assert result.returncode == 0, result.stderr
