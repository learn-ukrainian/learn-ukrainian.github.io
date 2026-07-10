"""Unit tests for the main-worktree branch guard hook.

Exercises the pure decision logic in
``agents_extensions/shared/hooks/guard-branch-switch-in-main.py``:

  * branch switch / create detection (pre-existing behavior),
  * the new ``git branch -D/-M/-f`` force-delete / force-rename blocking,
  * the safe-op allow-list (``-d`` / ``-m`` / list / create), and
  * the quote-aware tokenizer that prevents false positives on git verbs
    quoted inside a commit message — the reason this guard is Python and
    not a grep one-liner.

The hook filename has hyphens, so it is loaded by path via importlib.
Only module-level defs/constants run on load (``main`` is guarded by
``__name__ == "__main__"``), so importing it has no side effects.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
HOOK_PATH = REPO_ROOT / "agents_extensions/shared" / "hooks" / "guard-branch-switch-in-main.py"


def _load_hook():
    spec = importlib.util.spec_from_file_location(
        "guard_branch_switch_in_main", HOOK_PATH
    )
    assert spec and spec.loader, f"could not load hook at {HOOK_PATH}"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


guard = _load_hook()


def _dangerous(command: str) -> str | None:
    """Replicate the hook's per-segment scan; return the first reason or None."""
    for seg in guard._segments(command):
        reason = guard._segment_is_dangerous(seg)
        if reason:
            return reason
    return None


# --- Branch switches / creates (pre-existing behavior) ---------------------


@pytest.mark.parametrize(
    "cmd",
    [
        "git checkout -b feature",
        "git switch -c feature",
        "git switch some-branch",
        "git checkout some-branch",
        "git -C . checkout -b feature",
        "sudo git checkout -b feature",
        "git status && git checkout -b feature",
    ],
)
def test_branch_switch_blocked(cmd):
    assert _dangerous(cmd) is not None


@pytest.mark.parametrize(
    "cmd",
    [
        "git checkout main",
        "git checkout master",
        "git checkout HEAD",
        "git checkout -- path/to/file",
        "git status",
        "git log --oneline",
        "git worktree add .worktrees/x -b x origin/main",
        "ls -la",
    ],
)
def test_safe_ops_allowed(cmd):
    assert _dangerous(cmd) is None


# --- Force-delete / force-rename (new behavior) ----------------------------


@pytest.mark.parametrize(
    "cmd",
    [
        "git branch -D feature",
        "git branch -M old new",
        "git branch -f feature origin/main",
        "git branch --force feature origin/main",
        "git branch -d --force feature",
        "git branch --delete --force feature",
        "git branch -Df feature",
        "git -C . branch -D feature",
        "git status && git branch -D feature",
    ],
)
def test_force_branch_ops_blocked(cmd):
    reason = _dangerous(cmd)
    assert reason is not None
    assert "branch" in reason


@pytest.mark.parametrize(
    "cmd",
    [
        "git branch -d merged-feature",  # safe delete-if-merged
        "git branch -m old new",  # safe rename
        "git branch feature",  # create, does not switch
        "git branch",  # list
        "git branch -a",  # list all
        "git branch -r",  # list remotes
        "git branch -v",  # verbose list
        "git branch --list",
        "git branch -u origin/main",  # set upstream
    ],
)
def test_safe_branch_ops_allowed(cmd):
    assert _dangerous(cmd) is None


# --- Quote-aware: the key advantage over a grep-based hook -----------------


@pytest.mark.parametrize(
    "cmd",
    [
        'git commit -m "git branch -D old"',
        'git commit -m "revert: git checkout -b foo"',
        "git commit -m 'force-delete via git branch -D'",
        'git commit -m "git switch -c topic"',
    ],
)
def test_quoted_git_in_commit_message_not_blocked(cmd):
    assert _dangerous(cmd) is None


def test_branch_force_reason_unit():
    assert guard._branch_force_reason(["-D", "feature"]) is not None
    assert guard._branch_force_reason(["-M", "old", "new"]) is not None
    assert guard._branch_force_reason(["-f", "feature", "ref"]) is not None
    assert guard._branch_force_reason(["--force", "feature", "ref"]) is not None
    assert guard._branch_force_reason(["-d", "merged"]) is None
    assert guard._branch_force_reason(["-m", "old", "new"]) is None
    assert guard._branch_force_reason(["feature"]) is None
    assert guard._branch_force_reason([]) is None


# --- #4876: glued-operator evasion class ------------------------------------
# Live shapes from 2026-07-10: five `git branch -D` calls rode through the
# guard because `;`/`|`/newlines glued to neighbouring tokens never became
# separator tokens, collapsing the whole line into one segment.


@pytest.mark.parametrize(
    "cmd",
    [
        "true 2>&1 | head -1; git branch -D victim",
        "gh pr view 9 --json s --jq '{state, mergedAt}'; git branch -D victim",
        "cmd1\ngit branch -D victim",
        (
            "git worktree remove --force .worktrees/x 2>&1 | head -1; "
            "git branch -D victim 2>/dev/null | head -1"
        ),
        "true;git checkout -b feature",
        "true&&git switch -c feature",
    ],
)
def test_glued_operator_evasion_blocked(cmd):
    assert _dangerous(cmd) is not None


@pytest.mark.parametrize(
    "cmd",
    [
        # Heredoc bodies are data — a dangerous-looking line inside one must
        # not trigger…
        "cat > /tmp/x.md <<'EOF'\ngit branch -D fake\nEOF",
        # …quoting still protects commit messages…
        'git commit -m "git branch -D notreal"',
        # …and safe ops with glued separators stay allowed.
        "git branch -d merged-ok; echo done",
        # Commented-out danger is dead text.
        "echo hi # git branch -D victim",
    ],
)
def test_hardened_segments_no_false_positive(cmd):
    assert _dangerous(cmd) is None


def test_heredoc_body_does_not_mask_following_command():
    cmd = "cat > /tmp/x.md <<'EOF'\nbody text\nEOF\ngit branch -D victim"
    assert _dangerous(cmd) is not None


def test_backslash_line_continuation_still_inspected():
    # `\`-continuation is ONE logical command; the folded line must still be
    # scanned. Regression guard for the per-line refactor — the whole-command
    # tokenizer this replaced folded continuations implicitly (#4876).
    assert _dangerous("git branch -D victim \\\n  --force-ish") is not None
    assert _dangerous("git status \\\n  && git branch -D victim") is not None
