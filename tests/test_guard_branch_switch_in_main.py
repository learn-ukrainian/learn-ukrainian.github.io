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
import os
import subprocess
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


def _git(cwd: Path, *args: str) -> None:
    env = os.environ.copy()
    for name in (
        "GIT_DIR",
        "GIT_WORK_TREE",
        "GIT_INDEX_FILE",
        "GIT_PREFIX",
        "GIT_OBJECT_DIRECTORY",
        "GIT_ALTERNATE_OBJECT_DIRECTORIES",
    ):
        env.pop(name, None)
    subprocess.run(
        ["git", "-c", "core.hooksPath=/dev/null", *args],
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )


@pytest.fixture
def repos(tmp_path, monkeypatch):
    """Three independent primary repos plus an added public worktree."""
    public = tmp_path / "public"
    private = tmp_path / "private"
    other = tmp_path / "other"
    for root in (public, private, other):
        root.mkdir()
        _git(root, "init", "-b", "main")
        _git(root, "config", "user.name", "Guard Test")
        _git(root, "config", "user.email", "guard@example.invalid")
        _git(root, "commit", "--allow-empty", "-m", "initial")

    public_worktree = public / ".worktrees" / "topic"
    public_worktree.parent.mkdir()
    _git(public, "worktree", "add", "-b", "topic", str(public_worktree))
    monkeypatch.setattr(guard, "PROTECTED_ROOTS", [public.resolve(), private.resolve()])
    return {
        "public": public.resolve(),
        "private": private.resolve(),
        "other": other.resolve(),
        "public_worktree": public_worktree.resolve(),
    }


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


@pytest.mark.parametrize(
    "cmd",
    [
        "git checkout --detach",
        "git switch --detach",
        "git checkout --orphan tmp-orphan",
        "git checkout abcdef0",
        "git checkout 9265871162825c0c74a0b03cd2f2440d729b298f",
        "git checkout origin/main",
        "git checkout origin/feature",
        "git checkout refs/heads/feature",
    ],
)
def test_detach_and_raw_object_checkout_blocked(cmd):
    """Primary must never detach (#4857 recurrence)."""
    assert _dangerous(cmd) is not None


def test_gh_pr_checkout_blocked_in_primary(repos, monkeypatch):
    """#4857: gh pr checkout on primary is forbidden."""
    monkeypatch.chdir(repos["public"])
    reason = guard._command_danger_reason(
        "gh pr checkout 4849",
        session_cwd=repos["public"],
    )
    assert reason is not None
    assert "gh pr checkout" in reason


def test_gh_pr_checkout_allowed_in_worktree(repos, monkeypatch):
    monkeypatch.chdir(repos["public_worktree"])
    reason = guard._command_danger_reason(
        "gh pr checkout 4849",
        session_cwd=repos["public_worktree"],
    )
    assert reason is None


# --- Force-delete / force-rename (new behavior) ----------------------------


@pytest.mark.parametrize(
    "cmd",
    [
        "git branch -D main",
        "git branch -M main new",
        "git branch -M new",
        "git branch -f feature origin/main",
        "git branch --force feature origin/main",
        "git branch -d --force main",
        "git branch --delete --force main",
        "git branch -Df main",
        "git -C . branch -D main",
        "git status && git branch -D main",
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
    assert guard._branch_force_reason(["-D", "feature"], "feature") is not None
    assert guard._branch_force_reason(["-D", "feature"], "main") is None
    assert guard._branch_force_reason(["-M", "old", "new"], "old") is not None
    assert guard._branch_force_reason(["-M", "new"], "main") is not None
    assert guard._branch_force_reason(["-f", "feature", "ref"], "main") is not None
    assert guard._branch_force_reason(["--force", "feature", "ref"], "main") is not None
    assert guard._branch_force_reason(["-d", "merged"], "main") is None
    assert guard._branch_force_reason(["-m", "old", "new"], "main") is None
    assert guard._branch_force_reason(["feature"], "main") is None
    assert guard._branch_force_reason([], "main") is None


# --- #4876: glued-operator evasion class ------------------------------------
# Live shapes from 2026-07-10: five `git branch -D` calls rode through the
# guard because `;`/`|`/newlines glued to neighbouring tokens never became
# separator tokens, collapsing the whole line into one segment.


@pytest.mark.parametrize(
    "cmd",
    [
        "true 2>&1 | head -1; git branch -D main",
        "gh pr view 9 --json s --jq '{state, mergedAt}'; git branch -D main",
        "cmd1\ngit branch -D main",
        (
            "git worktree remove --force .worktrees/x 2>&1 | head -1; "
            "git branch -D main 2>/dev/null | head -1"
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
    cmd = "cat > /tmp/x.md <<'EOF'\nbody text\nEOF\ngit branch -D main"
    assert _dangerous(cmd) is not None


def test_backslash_line_continuation_still_inspected():
    # `\`-continuation is ONE logical command; the folded line must still be
    # scanned. Regression guard for the per-line refactor — the whole-command
    # tokenizer this replaced folded continuations implicitly (#4876).
    assert _dangerous("git branch -D main \\\n  --force-ish") is not None
    assert _dangerous("git status \\\n  && git branch -D main") is not None


# --- #4877 adversarial round (grok-build msg 2334): env/brace/heredoc holes ---


@pytest.mark.parametrize(
    "cmd",
    [
        "env FOO=1 git branch -D main",  # env + assignment before verb
        "FOO=1 git branch -D main",  # bare leading assignment
        "{ git branch -D main; }",  # compact brace group
        "{ git branch -D main",  # unterminated brace group
        "command git branch -D main",  # `command` wrapper
    ],
)
def test_wrapper_and_assignment_prefixes_still_inspected(cmd):
    assert _dangerous(cmd) is not None


def test_unclosed_heredoc_does_not_hide_trailing_danger():
    # A never-closing marker must NOT drop the real command after it (#4877
    # fail-open): the buffered lines were not a real heredoc body.
    assert _dangerous("cat <<'NOEND'\nbody > fake\ngit branch -D main") is not None


def test_attached_dash_heredoc_closes_and_body_dropped():
    # `<<-EOF` with a tab-indented closer is a REAL heredoc: body dropped
    # (no false positive on body content), trailing command still scanned.
    cmd = "cat <<-EOF\n\tgit branch -D fake\n\tEOF\ngit branch -D main"
    assert _dangerous(cmd) is not None  # the trailing real one
    # body-only (properly closed) must not trip:
    assert _dangerous("cat <<-EOF\n\tgit branch -D fake\n\tEOF") is None


# --- #4899: target-repo-aware protected-root matching ----------------------


@pytest.mark.parametrize(
    "command",
    [
        "git checkout --ours conflicted.py",
        "git checkout --theirs conflicted.py",
        "git checkout -- conflicted.py",
        "git restore conflicted.py",
    ],
)
def test_pathspec_and_restore_are_allowed_in_protected_primary(repos, command):
    assert guard._command_danger_reason(command, repos["public"]) is None


def test_issue_4899_other_repo_git_c_is_allowed(repos):
    command = f"git -C {repos['other']} branch -D stale-branch"
    assert guard._command_danger_reason(command, repos["public"]) is None


def test_issue_4899_other_repo_cd_prefix_is_allowed(repos):
    command = f"cd {repos['other']} && git branch -D stale-branch"
    assert guard._command_danger_reason(command, repos["public"]) is None


@pytest.mark.parametrize("root_key", ["public", "private"])
@pytest.mark.parametrize(
    "operation",
    ["switch topic", "checkout topic", "checkout -b topic"],
)
def test_protected_primary_switches_block_for_both_roots(repos, root_key, operation):
    root = repos[root_key]
    assert guard._command_danger_reason(f"git -C {root} {operation}", repos["other"]) is not None


@pytest.mark.parametrize("root_key", ["public", "private"])
@pytest.mark.parametrize(
    "operation",
    ["branch -D main", "branch -M main renamed-main"],
)
def test_protected_primary_current_branch_force_ops_block(repos, root_key, operation):
    root = repos[root_key]
    assert guard._command_danger_reason(f"git -C {root} {operation}", repos["other"]) is not None


def test_private_non_current_branch_pruning_is_allowed(repos):
    command = f"git -C {repos['private']} branch -D merged-feature"
    assert guard._command_danger_reason(command, repos["public"]) is None


def test_operations_inside_added_worktrees_are_allowed(repos):
    command = f"git -C {repos['public_worktree']} switch another-topic"
    assert guard._command_danger_reason(command, repos["public"]) is None


@pytest.mark.parametrize(
    "cmd",
    [
        'bash -c "git branch -D x"',
        'sh -c "git branch -D x"',
        'eval "git branch -D x"',
        "x=`git branch -D x`",  # backtick command substitution
    ],
)
def test_known_boundary_verb_inside_string_or_backticks(cmd):
    """DOCUMENTED LIMITATION (#4877, grok msg 2334): a verb hidden inside a
    quoted string arg (`bash -c "…"`, `eval "…"`) or backticks is NOT
    inspected — a segment guard cannot see it without becoming a recursive
    shell parser (which would add false positives). The old whole-command
    guard had the same blind spot. These guards are an honest-mistake safety
    net, not an adversarial sandbox: an agent does not accidentally wrap a
    destructive command in `bash -c`. This test PINS the boundary so any
    future change to it is visible and deliberate. (Note: `$(…)` substitution
    IS caught — see the dangerous-cases tests — because it leaks bare verb
    tokens into a segment; only string-args and backticks are blind.)
    """
    assert _dangerous(cmd) is None
