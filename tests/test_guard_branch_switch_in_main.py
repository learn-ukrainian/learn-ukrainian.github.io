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
import io
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
HOOK_PATH = REPO_ROOT / "agents_extensions/shared" / "hooks" / "guard-branch-switch-in-main.py"


def _load_hook():
    spec = importlib.util.spec_from_file_location("guard_branch_switch_in_main", HOOK_PATH)
    assert spec and spec.loader, f"could not load hook at {HOOK_PATH}"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


guard = _load_hook()

REDIRECTS_9479 = ["", "2>&1", ">file", "2>/dev/null", "&>file", "<file", "| cat"]


@pytest.mark.parametrize("redirect", REDIRECTS_9479)
@pytest.mark.parametrize("shape", ["cd", "admin-before", "admin-after", "implicit"])
def test_issue_9479_redirect_denominator(repos, redirect, shape):
    merge = {
        "cd": "",
        "admin-before": "gh pr merge --admin 5 && ",
        "admin-after": "gh pr merge 5 --admin && ",
        "implicit": "gh pr merge --admin && ",
    }[shape]
    # Merge option placement is irrelevant to this hook; its branch switch
    # must still use the cwd and argv that Bash actually executes.
    cd_redirect = redirect if redirect != "| cat" else ""
    command = f"cd {repos['public']} {cd_redirect} && {merge}git switch -c fixture {redirect}"
    assert guard._command_danger_reason(command, repos["other"]) is not None
    assert ["git", "switch", "-c", "fixture"] in guard._segments(command)
    safe = command.replace(str(repos["public"]), str(repos["public_worktree"]))
    assert guard._command_danger_reason(safe, repos["other"]) is None


@pytest.mark.parametrize("redirect,verb", [(">/dev/null", "checkout -b"), ("2>&1", "switch -c")])
def test_issue_9479_reviewer_reproductions(repos, redirect, verb):
    command = f"cd {repos['public']} {redirect} && git {verb} fixture"
    assert guard._command_danger_reason(command, repos["other"]) is not None


@pytest.mark.parametrize("redirect", REDIRECTS_9479)
@pytest.mark.parametrize("verb", ["checkout -b", "switch -c"])
def test_issue_9479_real_bash_cwd_and_argv(repos, tmp_path, redirect, verb):
    recorder = tmp_path / "git"
    recorder.write_text('#!/bin/bash\nprintf "%s\\n" "$PWD" "$@" > "$GUARD_RECORD"\n')
    recorder.chmod(0o755)
    (tmp_path / "file").touch()
    (repos["public"] / "file").touch()
    record = tmp_path / "record"
    cd_redirect = redirect if redirect != "| cat" else ""
    command = f"cd {repos['public']} {cd_redirect} && git {verb} fixture {redirect}"
    result = subprocess.run(
        ["bash", "-c", command],
        cwd=tmp_path,
        env={**os.environ, "PATH": str(tmp_path) + os.pathsep + os.environ["PATH"], "GUARD_RECORD": str(record)},
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 0, result.stderr
    actual = record.read_text().splitlines()
    assert actual == [str(repos["public"]), *verb.split(), "fixture"]
    rows = guard.read_commands(command, cwd=str(tmp_path))
    assert any(row.argv == ["git", *actual[1:]] and row.cwd == actual[0] for row in rows)
    assert guard._command_danger_reason(command, repos["other"]) is not None


@pytest.mark.parametrize(
    "redirect,position",
    [
        (redirect, position)
        for redirect in ['> "$FILE"', "> $(echo file)", "> `echo file`", ">"]
        for position in ["prefix", "suffix", "cd"]
        if (redirect, position) != (">", "prefix")
    ],
)
def test_issue_9479_dynamic_redirect_refused(repos, redirect, position):
    switch = f"git -C {repos['public']} switch -c fixture"
    command = {
        "prefix": f"{redirect} {switch}",
        "suffix": f"{switch} {redirect}",
        "cd": f"cd {repos['public']} {redirect} && git switch -c fixture",
    }[position]
    assert guard._command_danger_reason(command, repos["other"]) is not None


@pytest.mark.parametrize("redirect", [">file", "2>&1", "<file", "&>file"])
@pytest.mark.parametrize("target", ["$BRANCH", '"$BRANCH"', "$(cat selector)", "`cat selector`"])
def test_issue_9479_redirect_never_launders_target(repos, redirect, target):
    command = f"git checkout {target} {redirect}"
    assert guard._command_danger_reason(command, repos["public"]) is not None


@pytest.mark.parametrize(
    "command",
    [
        "git status >file",
        'git status > "$FILE"',
        "echo fixture > $(echo file)",
        "echo 'git switch -c fixture' >file",
        "git log 2>&1 | cat",
    ],
)
def test_issue_9479_benign_commands_still_allowed(repos, command):
    assert guard._command_danger_reason(command, repos["public"]) is None


def test_issue_9479_quoted_redirect_stays_data():
    assert guard._segments("cd '>' 2>&1 && git status") == [["cd", ">"], ["git", "status"]]


@pytest.mark.parametrize(
    "shape",
    [
        "echo $((1 << EOF))\n{payload}\nEOF",
        "((1 << EOF))\n{payload}\nEOF",
        "echo ${x#<<EOF }\n{payload}\nEOF",
        "let 'x=1<<EOF'\n{payload}\nEOF",
        "true # <<EOF\n{payload}\nEOF",
        ": <<EOF; \\\n{payload}\nnote\nEOF",
        ": <<EOF\n$({payload})\nEOF",
        ": <<EOF\n`{payload}`\nEOF",
        "echo '\n: <<EOF\n'\n" + "{payload}" + "\nEOF",
        ": << -EOF\nnote\n-EOF\n{payload}\nEOF",
        "echo foo # comment \\\n{payload}",
        ": <<EOF\n$(echo x\n{payload}\n)\nEOF",
        ": <<EOF\n$(echo x # )\n{payload}\n)\nEOF",
        ": <<EOF\n`echo x\n{payload}\n`\nEOF",
        ": <<EOF\n$(echo ')'; {payload})\nEOF",
        "x[1 << EOF ]=1\n{payload}\nEOF",
        "echo $[1 << EOF ]\n{payload}\nEOF",
    ],
)
def test_issue_9102_executable_payload_stays_visible(repos, shape):
    command = shape.replace("{payload}", "git checkout -b feature")
    assert _dangerous(command) is not None
    assert guard._command_danger_reason(command, repos["public"]) is not None


def test_issue_9102_real_let_heredoc_body_is_inert():
    assert _dangerous("let x=1<<EOF\ngit checkout -b feature\nEOF") is None


@pytest.mark.parametrize(
    "command",
    [
        "echo $(echo foo # comment \\\ngit checkout -b feature)",
        "echo `git checkout -b feature`",
        'echo "`git checkout -b feature`"',
        "echo `echo foo # comment \\\ngit checkout -b feature`",
        "echo $(echo foo # comment \\\n`git checkout -b feature`)",
    ],
)
def test_issue_9115_nested_and_backtick_switches_blocked(repos, command):
    assert _dangerous(command) is not None
    assert guard._command_danger_reason(command, repos["public"]) is not None


def test_issue_9115_escaped_nested_backtick_switch_is_visible(repos):
    command = r"echo `echo \`git checkout -b feature\``"
    assert _dangerous(command) is not None
    assert guard._command_danger_reason(command, repos["public"]) is not None


def test_issue_9115_backtick_depth_limit_blocks_branch_hook(repos, monkeypatch):
    monkeypatch.setattr(sys.modules["shell_bash"], "MAX_DEPTH", 2)
    monkeypatch.chdir(repos["public"])
    body = "git checkout -b feature"
    for _ in range(3):
        body = "`" + body.replace("\\", "\\\\").replace("`", r"\`") + "`"
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps({"tool_input": {"command": "echo " + body}})))
    assert guard.main() == 2


def test_issue_9088_heredoc_opener_after_escaped_quote_is_found():
    assert ["echo", 'a " b'] in guard._segments(r'echo "a \" b" <<EOF' + "\nfixture\nEOF")


@pytest.mark.parametrize(
    "opener,closer",
    [
        ("<<'EOF'", "EOF"),
        ('<<"EOF"', "EOF"),
        ("<<EOF", "EOF"),
        ("<<-EOF", "\tEOF"),
    ],
)
def test_issue_9088_standard_heredoc_delimiters(opener, closer):
    assert ["cat"] in guard._segments(f"cat {opener}\nfixture\n{closer}")
    assert _dangerous(f"cat {opener}\ngit checkout -b feature\n{closer}") is None
    assert _dangerous(f"cat {opener}\nnote\n{closer}\ngit checkout -b feature") is not None


@pytest.mark.parametrize(
    "first",
    [
        "true <<<EOF",
        "true <<< EOF",
        "true <<<'EOF'",
        'true <<<"EOF"',
        "true<<<EOF",
    ],
)
def test_issue_9088_here_strings_keep_branch_switch_visible(repos, first):
    command = f"{first}\ngit checkout -b feature\nEOF"
    assert ["true"] in guard._segments(first)
    assert _dangerous(command) is not None
    assert guard._command_danger_reason(command, repos["public"]) is not None


def test_issue_9088_crlf_closer_keeps_branch_switch_visible(repos):
    command = "cat <<EOF\r\nEOF\r\ngit checkout -b feature\nEOF"
    assert _dangerous(command) is not None
    assert guard._command_danger_reason(command, repos["public"]) is not None


def test_issue_9088_reviewer_heredoc_bypass_blocks(repos, monkeypatch):
    command = 'cat <<"EO\\"F"\nnote\nEO"F\ngh pr merge 1 --admin\ngit checkout -b feature\ntee AGENTS.md\necho $GH_TOKEN\ncat .env\nEO\\"F'
    assert _dangerous(command) is not None
    assert guard._command_danger_reason(command, repos["public"]) is not None
    monkeypatch.chdir(repos["public"])
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps({"tool_input": {"command": command}})))
    assert guard.main() == 2


@pytest.mark.parametrize(
    "opener,closer",
    [
        (r'<<"EO\"F"', 'EO"F'),
        (r"<<$'EOF'", "EOF"),
        ('<<$"EOF"', "EOF"),
        (r"<<$'EO\x22F'", 'EO"F'),
        (r"<<EO$'F'", "EOF"),
        (r"<<E\OF", "EOF"),
        (r"<<-$'EOF'", "\tEOF"),
        (r"<<$'EOF' <<SAFE", "EOF\nSAFE"),
        (r"<<SAFE <<$'EOF'", "SAFE\nEOF"),
    ],
)
def test_issue_9088_exotic_heredoc_keeps_branch_switch_visible(repos, opener, closer):
    command = f"cat {opener}\ngit checkout -b x\n{closer}"
    with pytest.raises(guard.ShellParseError):
        guard.read_commands(f"cat {opener}\nfixture\n{closer}")
    assert _dangerous(command) is not None
    assert guard._command_danger_reason(command, repos["public"]) is not None


def test_issue_9088_exotic_body_cannot_skip_later_safe_opener(repos):
    command = "cat <<$'EOF'\ncat <<SAFE\ngit checkout -b x\nSAFE\nEOF"
    assert _dangerous(command) is not None
    assert guard._command_danger_reason(command, repos["public"]) is not None


def test_issue_9088_missing_shell_helper_blocks(tmp_path):
    guard_copy = tmp_path / HOOK_PATH.name
    shutil.copy2(HOOK_PATH, guard_copy)
    result = subprocess.run(
        [sys.executable, str(guard_copy)],
        input=json.dumps({"tool_input": {"command": "git checkout -b feature"}}),
        text=True,
        capture_output=True,
        check=False,
        timeout=30,
    )
    assert result.returncode == 2
    assert "guard dependency unavailable: shell_bash" in result.stderr


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
        timeout=30,
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
        ("git worktree remove --force .worktrees/x 2>&1 | head -1; git branch -D main 2>/dev/null | head -1"),
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


@pytest.mark.parametrize(
    "cmd",
    [
        "env -i git branch -D main",
        "env -i FOO=1 git branch -D main",
        "env -u FOO git branch -D main",
        "sudo -u root git branch -D main",
        "sudo --preserve-env git branch -D main",
        "sudo -E git branch -D main",
        "time -p git branch -D main",
        "nice -n 10 git branch -D main",
        "stdbuf -oL git branch -D main",
    ],
)
def test_wrapper_options_do_not_hide_branch_verb(cmd):
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


@pytest.mark.parametrize(
    "tail",
    [
        "(git switch -c fixture)",
        "( git checkout -b fixture )",
        "(git switch -c fixture) && echo ok",
        ">file git switch -c fixture",
        "git switch -c fixture {fd}>file",
    ],
)
def test_issue_9479_r2_bash_cwd(repos, tmp_path, tail):
    recorder = tmp_path / "git"
    recorder.write_text('#!/bin/bash\nprintf "%s\\n" "$PWD" "$@" > "$GUARD_RECORD"\n')
    recorder.chmod(0o755)
    record = tmp_path / "record"
    command = f"cd {repos['public']} &&{tail}"
    result = subprocess.run(
        ["bash", "-c", command],
        cwd=tmp_path,
        env={**os.environ, "PATH": str(tmp_path) + os.pathsep + os.environ["PATH"], "GUARD_RECORD": str(record)},
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 0, result.stderr
    assert record.read_text().splitlines() == [
        str(repos["public"]),
        *(["checkout", "-b", "fixture"] if "checkout" in tail else ["switch", "-c", "fixture"]),
    ]
    assert guard._command_danger_reason(command, repos["other"]) is not None
    safe = command.replace(str(repos["public"]), str(repos["public_worktree"]))
    assert guard._command_danger_reason(safe, repos["other"]) is None


def test_issue_9479_r2_subshell_cd_stays_local(repos):
    command = f"(cd {repos['public']}) && git switch -c fixture"
    assert guard._command_danger_reason(command, repos["public_worktree"]) is None
    command = f"(cd {repos['public_worktree']}) && git switch -c fixture"
    assert guard._command_danger_reason(command, repos["public"]) is not None


def _assert_r3_bash_decision(repos, tmp_path, command, cwd, verb, expected_cwd):
    recorder = tmp_path / "git"
    recorder.write_text('#!/bin/bash\nprintf "%s\\n" "$PWD" "$@" > "$GUARD_RECORD"\n')
    recorder.chmod(0o755)
    record = tmp_path / "record"
    result = subprocess.run(
        ["bash", "-c", command],
        cwd=cwd,
        env={
            **os.environ,
            "PATH": str(tmp_path) + os.pathsep + os.environ["PATH"],
            "GUARD_RECORD": str(record),
            "TMPDIR": str(tmp_path),
        },
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 0, result.stderr
    actual = record.read_text().splitlines()
    assert actual == [str(expected_cwd), *verb.split(), "fixture"]
    reason = guard._command_danger_reason(command, cwd)
    if "&& $(cd " in command:
        assert reason is not None and "dynamic command name" in reason
    else:
        assert (reason is not None) == (actual[0] == str(repos["public"]))


@pytest.mark.parametrize("parentheses", ["({body})", "( {body} )"])
@pytest.mark.parametrize("target", [".worktrees/topic", "./.worktrees/topic", "absolute"])
@pytest.mark.parametrize("verb", ["switch -c", "checkout -b", "checkout", "switch"])
def test_issue_9479_r3_closed_subshell_cd(repos, tmp_path, parentheses, target, verb):
    target = str(repos["public_worktree"]) if target == "absolute" else target
    body = f"cd {target} >$(echo /dev/null)"
    command = f"{parentheses.format(body=body)} && git {verb} fixture"
    _assert_r3_bash_decision(repos, tmp_path, command, repos["public"], verb, repos["public"])


@pytest.mark.parametrize("verb", ["switch -c", "checkout -b", "checkout", "switch"])
def test_issue_9479_r3_pending_cd_before_new_subshell(repos, tmp_path, verb):
    command = f"cd ../.. >$(echo /dev/null) &&(git {verb} fixture)"
    _assert_r3_bash_decision(repos, tmp_path, command, repos["public_worktree"], verb, repos["public"])


@pytest.mark.parametrize("verb", ["switch -c", "checkout -b", "checkout", "switch"])
@pytest.mark.parametrize(
    "shape,start,target,expected",
    [
        ("(cd {target}) && git {verb} fixture", "public", "public_worktree", "public"),
        ("(cd {target}) && git {verb} fixture", "public_worktree", "public", "public_worktree"),
        ("cd {target} >$(echo /dev/null) && git {verb} fixture", "public_worktree", "public", "public"),
        ("cd {target} >$(echo /dev/null) && git {verb} fixture", "public", "public_worktree", "public_worktree"),
        ('cd {target} 2>"$(mktemp)" && git {verb} fixture', "public_worktree", "public", "public"),
        ('cd {target} 2>"$(mktemp)" && git {verb} fixture', "public", "public_worktree", "public_worktree"),
        ('(cd {target} 2>"$(mktemp)") && git {verb} fixture', "public", "public_worktree", "public"),
        ('(cd {target} 2>"$(mktemp)") && git {verb} fixture', "public_worktree", "public", "public_worktree"),
    ],
)
def test_issue_9479_r3_scope_controls(repos, tmp_path, verb, shape, start, target, expected):
    command = shape.format(target=repos[target], verb=verb)
    _assert_r3_bash_decision(repos, tmp_path, command, repos[start], verb, repos[expected])


@pytest.mark.parametrize(
    "command",
    [
        "git checkout -b feat && echo $(git rev-parse HEAD)",
        "git switch -c feat-$(date +%s)",
        "cd $(git rev-parse --show-toplevel) && git checkout -b x",
        'git checkout -b feat >"$LOG" 2>&1',
        "git checkout -b feat && echo `git rev-parse HEAD`",
        "git checkout -b feat && cat <(echo fixture)",
        'echo fixture >"$LOG" && git checkout -b feat',
    ],
)
@pytest.mark.parametrize("location", ["public_worktree", "non_repo", "public"])
def test_issue_9479_r2_unreadable_respects_repository(repos, tmp_path, command, location):
    cwd = tmp_path / "non-repo" if location == "non_repo" else repos[location]
    cwd.mkdir(exist_ok=True)
    # An unreadable cd can change the repository even from an unprotected cwd.
    expected_block = location == "public" or command.startswith("cd $(")
    assert (guard._command_danger_reason(command, cwd) is not None) == expected_block


@pytest.mark.parametrize(
    "tail",
    [
        "git checkout -b feat && echo $(git rev-parse HEAD)",
        "git switch -c feat-$(date +%s)",
        "cd $(git rev-parse --show-toplevel) && git checkout -b x",
        'git checkout -b feat >"$LOG" 2>&1',
    ],
)
@pytest.mark.parametrize("cd_target", ["primary", "unreadable"])
def test_issue_9479_r2_unreadable_cd_blocks(repos, tail, cd_target):
    target = str(repos["public"]) if cd_target == "primary" else '"$ROOT"'
    assert guard._command_danger_reason(f"cd {target} && {tail}", repos["public_worktree"]) is not None


@pytest.mark.parametrize("target", ["public", "public_worktree"])
def test_issue_9479_r2_named_fd_cd(repos, target):
    command = f"cd {repos[target]} {{fd}}>file && git switch -c fixture"
    assert (guard._command_danger_reason(command, repos["other"]) is not None) == (target == "public")


@pytest.mark.parametrize("redirect", ['>"$LOG"', ">$(echo file)", ">`echo file`"])
@pytest.mark.parametrize("target", ["public", "public_worktree"])
def test_issue_9479_r2_literal_cd_dynamic_redirect(repos, redirect, target):
    command = f"cd {repos[target]} {redirect} && git switch -c fixture"
    assert (guard._command_danger_reason(command, repos["public_worktree"]) is not None) == (target == "public")


def test_issue_9479_r2_redirect_substitution_runs_before_cd(repos):
    command = f"cd {repos['public']} >$(git switch -c fixture) && echo ok"
    assert guard._command_danger_reason(command, repos["public_worktree"]) is None
    command = f"cd {repos['public_worktree']} >$(git switch -c fixture) && echo ok"
    assert guard._command_danger_reason(command, repos["public"]) is not None


def test_issue_9479_r2_operator_boundaries(repos):
    command = f"cd {repos['public']} &&(git switch -c fixture) && echo ok"
    rows = guard.read_commands(command, cwd=str(repos["other"]))
    assert next(row for row in rows if row.argv[0] == "git").cwd == str(repos["public"])
    assert rows[-1].cwd == str(repos["public"])


@pytest.mark.parametrize("start", ["public", "public_worktree"])
@pytest.mark.parametrize("separator", [" && ", "; ", "\n", " || "])
@pytest.mark.parametrize("redirect", ["", "2>/dev/null", ">$(echo /dev/null)", ">`echo /dev/null`"])
@pytest.mark.parametrize(
    "shape",
    [
        "WT=$(cd {target} {redirect} && pwd)",
        "x=$(cd {target} {redirect} && pwd)",
        "(cd {target} {redirect} && git status)",
        "(cd {target} {redirect} && true)",
        "WT=`cd {target} {redirect} && pwd`",
        "echo $(cd {target} {redirect} && pwd)",
        "echo `cd {target} {redirect} && pwd`",
        "[ -d $(cd {target} {redirect} && pwd) ]",
        "cat <(cd {target} {redirect} && pwd)",
        "true >(cd {target} {redirect} && pwd)",
        "( ( cd {target} {redirect} ) )",
        # The inner pwd expands to a command name: ':' runs successfully.
        "x=$(cd {target} {redirect} && $(cd {other} && echo :))",
        "x=$(cd {target} {redirect} && $(cd {other} && pwd)); true",
        "(cd {target} {redirect} && false || pwd)",
        "(cd {target} {redirect} && pwd; true)",
        "(cd {target} {redirect} && pwd\ntrue)",
    ],
)
def test_issue_9479_r4_scope_stack_bash(repos, tmp_path, start, separator, redirect, shape):
    target = "public_worktree" if start == "public" else "public"
    if shape.count("`") == 2:
        redirect = redirect.replace("`", "\\`")
    directory = ".worktrees/topic" if target == "public_worktree" else "../.."
    body = shape.format(target=directory, redirect=redirect, other=repos[start])
    # All bodies succeed; make the OR-list run its branch operation too.
    if separator == " || ":
        body += " && false"
    command = body + separator + "git checkout -b fixture"
    _assert_r3_bash_decision(repos, tmp_path, command, repos[start], "checkout -b", repos[start])


@pytest.mark.parametrize("start", ["public", "public_worktree"])
@pytest.mark.parametrize("target", ["public", "public_worktree"])
def test_issue_9479_r4_session_cd_bash(repos, tmp_path, start, target):
    command = f"cd {repos[target]} && git switch -c fixture"
    _assert_r3_bash_decision(repos, tmp_path, command, repos[start], "switch -c", repos[target])


@pytest.mark.parametrize("shape", ["({body})", "x=$({body})", "x=`{body}`", "cat <({body})"])
def test_issue_9479_r4_unreadable_cd_is_scoped(repos, tmp_path, shape):
    body = 'cd "$ROOT" && git switch -c fixture'
    command = shape.format(body=body)
    # Bash executes a real primary cd, but the guard cannot read its target.
    # Check the invocation with the same recording oracle used by the controls.
    with pytest.MonkeyPatch.context() as patch:
        patch.setenv("ROOT", str(repos["public"]))
        _assert_r3_bash_decision(repos, tmp_path, command, repos["public_worktree"], "switch -c", repos["public"])
    closed = shape.format(body='cd "$ROOT" && true') + " && git switch -c fixture"
    with pytest.MonkeyPatch.context() as patch:
        patch.setenv("ROOT", str(repos["public"]))
        _assert_r3_bash_decision(
            repos, tmp_path, closed, repos["public_worktree"], "switch -c", repos["public_worktree"]
        )


def test_issue_9479_r4_unmatched_close_fails_closed(repos, tmp_path):
    # A case arm is legal Bash but has no opening scope in this bounded reader.
    command = "case fixture in fixture) git switch -c fixture ;; esac"
    recorder = tmp_path / "git"
    recorder.write_text('#!/bin/bash\nprintf "%s\\n" "$PWD" "$@" > "$GUARD_RECORD"\n')
    recorder.chmod(0o755)
    record = tmp_path / "record"
    result = subprocess.run(
        ["bash", "-c", command],
        cwd=repos["public_worktree"],
        env={**os.environ, "PATH": str(tmp_path) + os.pathsep + os.environ["PATH"], "GUARD_RECORD": str(record)},
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 0, result.stderr
    assert record.read_text().splitlines() == [str(repos["public_worktree"]), "switch", "-c", "fixture"]
    assert guard._command_danger_reason(command, repos["public_worktree"]) is not None


@pytest.mark.parametrize("option", ["-C ", "-C"])
@pytest.mark.parametrize("target", ["public", "public_worktree", "relative"])
def test_issue_9479_r2_absolute_git_cwd_resolves_unreadable_cd(repos, option, target):
    directory = "relative" if target == "relative" else str(repos[target])
    command = f'cd "$ROOT" && git {option}{directory} switch -c fixture'
    assert (guard._command_danger_reason(command, repos["other"]) is not None) == (target != "public_worktree")


def _assert_r5_bash_record(tmp_path, command, cwd, expected_cwd):
    recorder = tmp_path / "git"
    recorder.write_text('#!/bin/bash\nprintf "%s\\n" "$PWD" "$@" > "$GUARD_RECORD"\n')
    recorder.chmod(0o755)
    record = tmp_path / "record"
    result = subprocess.run(
        ["bash", "-c", command],
        cwd=cwd,
        env={**os.environ, "PATH": str(tmp_path) + os.pathsep + os.environ["PATH"], "GUARD_RECORD": str(record)},
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 0, result.stderr
    assert record.read_text().splitlines() == [str(expected_cwd), "checkout", "-b", "fixture"]


@pytest.mark.parametrize("start", ["public", "public_worktree"])
@pytest.mark.parametrize(
    "shape",
    [
        "(cd {target} && case x in x) git checkout -b fixture;; esac)",
        "x=$(cd {target} && case y in y) git checkout -b fixture;; esac)",
        "echo ${{x:-(}} && cd {target} && echo ${{x:-)}} && git checkout -b fixture",
        "echo ${{x//[(]/}} && cd {target} && echo ${{x//[)]/}} && git checkout -b fixture",
    ],
)
def test_issue_9479_r5_reviewer_reproductions_real_bash(repos, tmp_path, start, shape):
    target = "../.." if start == "public_worktree" else "."
    command = shape.format(target=target)
    _assert_r5_bash_record(tmp_path, command, repos[start], repos["public"])
    assert guard._command_danger_reason(command, repos[start]) is not None


@pytest.mark.parametrize("start", ["public", "public_worktree"])
def test_issue_9479_r6_branch_before_case_deliberately_overblocks_worktree(repos, tmp_path, start):
    command = "git checkout -b fixture; case x in x) true;; esac"
    _assert_r5_bash_record(tmp_path, command, repos[start], repos[start])
    assert (guard._command_danger_reason(command, repos[start]) is not None) is True


@pytest.mark.parametrize(
    "shape", ["case x in x) true;; esac", "(case x in x) true;; esac)", "x=$(case x in x) true;; esac)"]
)
def test_issue_9479_r5_case_without_cd_deliberately_overblocks_worktree(repos, tmp_path, shape):
    command = shape + "; git checkout -b fixture"
    _assert_r5_bash_record(tmp_path, command, repos["public_worktree"], repos["public_worktree"])
    assert guard._command_danger_reason(command, repos["public_worktree"]) is not None


@pytest.mark.parametrize(
    "body",
    [
        "echo case",
        "echo ${x:-word}",
        "echo '${x:-(}'",
        'git commit -m "case x"',
        "case=1",
        "cat <<'EOF'\ncase x in x) ${x:-(}\nEOF\ntrue",
    ],
)
def test_issue_9479_r5_literal_case_and_parameter_controls_allowed(repos, body):
    assert guard._command_danger_reason(body + " && git switch -c fixture", repos["public_worktree"]) is None


@pytest.mark.parametrize(
    "body",
    [
        "echo ${x:-(}",
        'echo "${x:-(}"',
        "echo ${x:-${y:-(}}",
        "(echo ${x:-(})",
        "true; then case x in x) true;; esac",
        "true; do case x in x) true;; esac",
        "else case x in x) true;; esac",
        "! case x in x) true;; esac",
        "time case x in x) true;; esac",
    ],
)
def test_issue_9479_r5_unmodeled_syntax_is_sticky(repos, body):
    assert guard._command_danger_reason(body + "; git switch -c fixture", repos["public_worktree"]) is not None
    assert guard._command_danger_reason(body + "; git status", repos["public_worktree"]) is None


def test_issue_9479_r5_parentheses_in_branch_argument_refuse_current_command(repos):
    assert guard._command_danger_reason("git switch -c ${x:-(}", repos["public_worktree"]) is not None


def test_issue_9479_r6_safe_parameter_does_not_override_later_case(repos, tmp_path):
    command = 'echo ${x:-"${y:-word}"} && git checkout -b fixture; case x in x) true;; esac'
    _assert_r5_bash_record(tmp_path, command, repos["public_worktree"], repos["public_worktree"])
    assert guard._command_danger_reason(command, repos["public_worktree"]) is not None


def test_issue_9479_r5_nested_close_restores_nearest_not_outermost_frame(repos, tmp_path):
    command = "(cd ../.. && (true) && git checkout -b fixture)"
    _assert_r5_bash_record(tmp_path, command, repos["public_worktree"], repos["public"])
    assert guard._command_danger_reason(command, repos["public_worktree"]) is not None


R6_REPRODUCTIONS = [
    'git checkout -b fixture && echo "$(case x in x) echo;; esac)"',
    'echo "$(case x in x) echo;; esac)" && git checkout -b fixture',
    'echo "$(echo ${x:-(})" && git checkout -b fixture',
    'git checkout -b "fixture$(case x in x) echo y;; esac)"',
    'echo "a $(echo ${x//[)]/})"; git switch -c fixture',
    'git checkout -b fixture; echo "x$(echo ${y#(})"',
    "(cd {target} && case x in\nx) true;; esac\ngit checkout -b fixture)",
    "x=$(cd {target} && case y in\ny) git checkout -b fixture;; esac)",
    "(cd {target} && case x in x) git checkout -b fixture;;\nesac)",
    "(cd {target} && echo\n${x:-)}\ngit checkout -b fixture)",
]


def _r6_bash_record(tmp_path, command, cwd, expected_cwd):
    recorder = tmp_path / "git"
    recorder.write_text('#!/bin/bash\nprintf "%s\\n" "$PWD" "$@" > "$GUARD_RECORD"\n')
    recorder.chmod(0o755)
    record = tmp_path / "record"
    result = subprocess.run(
        ["bash", "-c", command],
        cwd=cwd,
        env={**os.environ, "PATH": str(tmp_path) + os.pathsep + os.environ["PATH"], "GUARD_RECORD": str(record)},
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 0, result.stderr
    assert record.exists(), (command, result.stderr)
    actual = record.read_text().splitlines()
    assert actual[0] == str(expected_cwd)
    assert actual[1:3] in (["checkout", "-b"], ["switch", "-c"])
    assert actual[3].startswith("fixture")


@pytest.mark.parametrize("start", ["public", "public_worktree"])
@pytest.mark.parametrize("shape", R6_REPRODUCTIONS)
def test_issue_9479_r6_whole_command_reproductions_real_bash(repos, tmp_path, start, shape):
    target = "../.." if start == "public_worktree" else "."
    command = shape.replace("{target}", target)
    expected_cwd = repos["public"] if "{target}" in shape else repos[start]
    _r6_bash_record(tmp_path, command, repos[start], expected_cwd)
    assert guard._command_danger_reason(command, repos[start]) is not None


@pytest.mark.parametrize("start", ["public", "public_worktree"])
@pytest.mark.parametrize("separator", [";", "&&", "||", "\n"])
@pytest.mark.parametrize("multiline", [False, True])
@pytest.mark.parametrize("position", ["before", "after", "inside"])
@pytest.mark.parametrize(
    "wrapper",
    ["{body}", "x=$({body})", 'echo "$({body})"', "echo `{body}`", "cat <({body})"],
)
def test_issue_9479_r6_case_anywhere_deliberately_overblocks_worktree(
    repos, tmp_path, start, separator, multiline, position, wrapper
):
    branch = "git checkout -b fixture"
    case = "case x in\nx) true;;\nesac" if multiline else "case x in x) true;; esac"
    if position == "inside":
        body = case.replace("true", branch)
        command = wrapper.format(body=body)
    else:
        body = wrapper.format(body=case)
        if separator == "||" and position == "after":
            body = "{ " + body + "; false; }"
        command = f"{branch}{separator}{body}" if position == "before" else f"{body}{separator}{branch}"
    _r6_bash_record(tmp_path, command, repos[start], repos[start])
    assert guard._command_danger_reason(command, repos[start]) is not None


@pytest.mark.parametrize(
    "body",
    ["echo case", 'git commit -m "case study"', 'grep -r "case " .', "echo ${x:-default}", "echo ${#arr[@]}"],
)
def test_issue_9479_r6_common_worktree_controls_allowed(repos, body):
    assert guard._command_danger_reason(body + " && git switch -c fixture", repos["public_worktree"]) is None


@pytest.mark.parametrize("body", ["case x in x) true;; esac", "echo ${x:-(}", 'echo "$(case x in x) echo;; esac)"'])
@pytest.mark.parametrize("start", ["public", "public_worktree"])
def test_issue_9479_r6_unmodeled_without_branch_is_unaffected(repos, body, start):
    assert guard._command_danger_reason(body, repos[start]) is None
    reason = guard._command_danger_reason(body + '; echo "git switch -c literal"', repos[start])
    if body == "echo ${x:-(}":
        assert reason is not None and "Bash parse error" in reason
    else:
        assert reason is None


@pytest.mark.parametrize("target", ["public", "public_worktree"])
def test_issue_9479_r6_absolute_git_cwd_cannot_resolve_whole_command_uncertainty(repos, target):
    command = f"case x in x) true;; esac; git -C {repos[target]} switch -c fixture"
    assert guard._command_danger_reason(command, repos["public_worktree"]) is not None


@pytest.mark.parametrize("failure", ["detector", "scope"])
def test_issue_9479_r6_helper_exception_exits_two(monkeypatch, failure):
    def broken(*args, **kwargs):
        raise RuntimeError("synthetic helper failure")

    if failure == "detector":
        monkeypatch.setattr(guard, "read_commands", broken)
    else:
        monkeypatch.setattr(sys.modules["shell_bash"], "Parser", broken)
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps({"tool_input": {"command": "git switch -c fixture"}})))
    assert guard.main() == 2


@pytest.mark.parametrize(
    "command",
    [
        'echo "$(case x in x) (true);; esac)" && git checkout -b fixture',
        'echo "$(if true; then case x in x) git checkout -b fixture;; esac; fi)"',
        "echo ${x:-$(git checkout -b fixture)}",
        'echo "${x:-$(git checkout -b fixture)}"',
        "case x in x) true;; esac; gh -R owner/repo pr checkout 5",
        'git checkout -b fixture; echo "unterminated',
        "git checkout -b fixture; cat <<EOF\nnever closed",
    ],
)
@pytest.mark.parametrize("start", ["public", "public_worktree"])
def test_issue_9479_r6_unknown_repository_branch_variants(repos, command, start):
    assert guard._command_danger_reason(command, repos[start]) is not None


@pytest.mark.parametrize("start", ["public", "public_worktree"])
@pytest.mark.parametrize("separator", [";", "&&", "||", "\n"])
@pytest.mark.parametrize("multiline", [False, True])
@pytest.mark.parametrize("position", ["before", "after", "inside"])
@pytest.mark.parametrize("parenthesis", ["(", ")"])
@pytest.mark.parametrize("wrapper", ["{body}", "x=$({body})", 'echo "$({body})"', "echo `{body}`", "cat <({body})"])
def test_issue_9479_r6_parameter_anywhere_deliberately_overblocks_worktree(
    repos, tmp_path, start, separator, multiline, position, parenthesis, wrapper
):
    branch = "git checkout -b fixture"
    body = "echo ${x:-" + parenthesis + "}"
    if multiline:
        body += "\ntrue"
    if position == "inside":
        command = wrapper.format(body=body + "; " + branch)
    else:
        body = wrapper.format(body=body)
        if separator == "||" and position == "after":
            body = "{ " + body + "; false; }"
        command = f"{branch}{separator}{body}" if position == "before" else f"{body}{separator}{branch}"
    _r6_bash_record(tmp_path, command, repos[start], repos[start])
    assert guard._command_danger_reason(command, repos[start]) is not None


R7_BODIES = [
    "fix: don't drop the cache",
    "case study of fixture",
    "${y:-(z)}",
    "a single quote: ' and a double quote: \"",
    "`printf fixture` and (parentheses)",
    "EOF trailing text\nIt's fixed",
]
R7_SHAPES = [
    'git commit -m "$(cat {opener}\n{body}\n{closer}\n)"',
    'git add -A && git commit -m "$(cat {opener}\n{body}\n{closer}\n)"',
    'git push -u origin fixture && gh pr create --body "$(cat {opener}\n{body}\n{closer}\n)"',
    'git commit -m "$(printf %s "$(cat {opener}\n{body}\n{closer}\n)")"',
]


def _r7_bash_records(tmp_path, command, cwd):
    """Execute real Bash; record every synthetic git/gh invocation and argv."""
    recorder = (
        '#!/bin/bash\nprintf "%s\\0" "${0##*/}" "$PWD" "$@" >> "$GUARD_RECORD"\nprintf "\\n" >> "$GUARD_RECORD"\n'
    )
    for name in ("git", "gh"):
        path = tmp_path / name
        path.write_text(recorder)
        path.chmod(0o755)
    record = tmp_path / "record-r7"
    record.write_bytes(b"")
    result = subprocess.run(
        ["bash", "-c", command],
        cwd=cwd,
        env={**os.environ, "PATH": str(tmp_path) + os.pathsep + os.environ["PATH"], "GUARD_RECORD": str(record)},
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 0, result.stderr
    return [row.rstrip(b"\0").decode().split("\0") for row in record.read_bytes().split(b"\0\n") if row]


@pytest.mark.parametrize("start", ["public", "public_worktree"])
@pytest.mark.parametrize("separator", [" && ", "\n"])
@pytest.mark.parametrize("opener", ["<<'EOF'", '<<"EOF"', r"<<\EOF", "<<-'EOF'", "<<EOF", "<<-EOF"])
@pytest.mark.parametrize("body", R7_BODIES)
@pytest.mark.parametrize("shape", R7_SHAPES)
def test_issue_9479_r7_commit_and_pr_heredoc_bash(repos, tmp_path, start, separator, opener, body, shape):
    closer = "\tEOF" if opener.startswith("<<-") else "EOF"
    command = "git switch -c fixture" + separator + shape.format(opener=opener, body=body, closer=closer)
    records = _r7_bash_records(tmp_path, command, repos[start])
    assert records[0] == ["git", str(repos[start]), "switch", "-c", "fixture"]
    assert records[-1][0] == ("gh" if "gh pr create" in shape else "git")
    assert records[-1][2:4] == (["pr", "create"] if "gh pr create" in shape else ["commit", "-m"])
    quoted = "'" in opener or '"' in opener or "\\" in opener
    if quoted:
        assert records[-1][-1] == body
    # Parameter parentheses in an unquoted body remain active expansions.
    expansion_tripwire = not quoted and body == "${y:-(z)}"
    # Round 8 preprocesses every heredoc before scope reading. Tighten the
    # primary expectation: plain bodies must not hide the real switch either.
    expected = expansion_tripwire or start == "public"
    assert (guard._command_danger_reason(command, repos[start]) is not None) == expected


@pytest.mark.parametrize("start", ["public", "public_worktree"])
@pytest.mark.parametrize(
    "tail",
    [
        "cat <<'ONE' <<\\TWO\nIt's fixed\nONE\ncase study ${y:-(z)}\nTWO",
        'cat <(cat <<"EOF"\nIt\'s fixed\nEOF\n)',
        "echo `cat <<'EOF'\nIt's fixed\nEOF\n`",
        "cat <<EOF\n'case study' and \"quotes\"\nEOF",
        "cat <<EOF\n'$(printf fixture)'\nEOF",
        "echo '<<EOF'",
        'cat <<<"It\'s fixed"',
    ],
)
def test_issue_9479_r7_other_heredoc_contexts_bash(repos, tmp_path, start, tail):
    command = "git checkout -b fixture\n" + tail
    assert _r7_bash_records(tmp_path, command, repos[start])[0] == [
        "git",
        str(repos[start]),
        "checkout",
        "-b",
        "fixture",
    ]
    assert (guard._command_danger_reason(command, repos[start]) is not None) == (start == "public")


@pytest.mark.parametrize("start", ["public", "public_worktree"])
@pytest.mark.parametrize(
    "tail",
    [
        "git commit -m \"$(cat <<EOF\n'$(case x in x) printf fixture;; esac)'\nEOF\n)\"",
        'git commit -m "$(cat <<EOF\n`case x in x) printf fixture;; esac`\nEOF\n)"',
        "cat <<'EOF'\nIt's fixed\nEOF\ncase x in x) true;; esac",
        'git commit -m "$(cat <<EOF\n${y:-(z)}\nEOF\n)"',
    ],
)
def test_issue_9479_r7_real_expansions_and_later_case_stay_blocked(repos, tmp_path, start, tail):
    command = "git switch -c fixture && " + tail
    assert _r7_bash_records(tmp_path, command, repos[start])[0][2:] == ["switch", "-c", "fixture"]
    assert guard._command_danger_reason(command, repos[start]) is not None


@pytest.mark.parametrize("start", ["public", "public_worktree"])
@pytest.mark.parametrize("opener", ["<<EOF", "<<'EOF'", r"<<\EOF", "<<-EOF"])
def test_issue_9479_r7_missing_terminator_fails_closed(repos, start, opener):
    command = f'git switch -c fixture && git commit -m "$(cat {opener}\nIt\'s fixed\nEOF trailing\n)"'
    with pytest.raises(guard.ShellParseError, match="Bash parse error"):
        guard.read_commands(command, str(repos[start]))
    assert guard._command_danger_reason(command, repos[start]) is not None


def test_issue_9479_r7_primary_apostrophe_is_still_blocked(repos, tmp_path):
    command = "git switch -c fixture && git commit -m \"$(cat <<'EOF\n"  # replace with a closed delimiter below
    command = "git switch -c fixture && git commit -m \"$(cat <<'EOF'\nfix: don't drop the cache\nEOF\n)\""
    assert _r7_bash_records(tmp_path, command, repos["public"])[0][2:] == ["switch", "-c", "fixture"]
    assert guard._command_danger_reason(command, repos["public"]) is not None
    assert guard._command_danger_reason(command, repos["public_worktree"]) is None


R8_BODIES = [
    "uses `git checkout -b x` in text",
    "git checkout -b x",
    "## Summary\n- run `git switch main` then `git checkout -b feat`",
    "Use `gh pr checkout 12` to test",
    "`git branch -D old`",
    "a literal $(git checkout -b x)",
    "git switch main",
]
R8_SHAPES = [
    ('git commit -m "$(cat {opener}\n{body}\n{closer}\n)"', ["git", "commit", "-m"]),
    ('gh pr create --body "$(cat {opener}\n{body}\n{closer}\n)"', ["gh", "pr", "create", "--body"]),
    ("git commit -F - {opener}\n{body}\n{closer}", ["git", "commit", "-F"]),
    ("gh pr create --body-file - {opener}\n{body}\n{closer}", ["gh", "pr", "create", "--body-file"]),
]


R9_WRAPPERS = [
    ('git commit -m "$(', ')"'),
    ('echo "$(', ')"'),
    ('gh pr create --body "$(', ')"'),
    ("echo `", "`"),
    ("(", ")"),
    ("cat <(", ")"),
    ("x=$(", ")"),
]
R9_OPERATIONS = ["git checkout -b fixture", "git switch -c fixture", "git branch -D main", "gh pr checkout 12"]


@pytest.mark.parametrize("start", ["public", "public_worktree"])
@pytest.mark.parametrize("operation", [*R9_OPERATIONS, "git status"])
@pytest.mark.parametrize("same_line_closer", [False, True])
@pytest.mark.parametrize("opener", ["<<EOF", "<<'EOF'", '<<"EOF"', "<<-EOF", "<<-'EOF'", r"<<\EOF"])
@pytest.mark.parametrize("prefix,suffix", R9_WRAPPERS)
def test_issue_9479_r9_later_line_after_heredoc_bash(
    repos, tmp_path, monkeypatch, start, operation, same_line_closer, opener, prefix, suffix
):
    # The assignment reproduces the reviewer's true-with-a-heredoc shape.
    reader = "true" if prefix == "x=$(" else "cat"
    closer = "\tEOF" if opener.startswith("<<-") else "EOF"
    command = f"{prefix}{reader} {opener}\nfix: x\n{closer}\n{operation}"
    command += ("" if same_line_closer else "\n") + suffix
    records = _r7_bash_records(tmp_path, command, repos[start])
    executable, *argv = operation.split()
    assert records[0] == [executable, str(repos[start]), *argv]
    assert len(records) == (2 if prefix.startswith(("git commit", "gh pr create")) else 1)
    # Heredoc removal must preserve precisely the decision for the executed
    # operation, including worktree admission and benign later commands.
    expected = guard._command_danger_reason(operation, repos[start]) is not None
    assert (guard._command_danger_reason(command, repos[start]) is not None) == expected
    monkeypatch.chdir(repos[start])
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps({"tool_input": {"command": command}})))
    assert guard.main() == (2 if expected else 0)


@pytest.mark.parametrize("start", ["public", "public_worktree"])
@pytest.mark.parametrize("queued", [False, True])
@pytest.mark.parametrize("operation", [*R9_OPERATIONS, "git status", ""])
@pytest.mark.parametrize("prefix,suffix", R9_WRAPPERS)
def test_issue_9479_r9_multiple_heredocs_bash(repos, tmp_path, start, queued, operation, prefix, suffix):
    bodies = (
        "cat <<'ONE' <<-TWO\nfirst\nONE\n\tsecond\n\tTWO\n"
        if queued
        else "cat <<'ONE'\nfirst\nONE\ncat <<-TWO\n\tsecond\n\tTWO\n"
    )
    command = prefix + bodies + operation + ("\n" if operation else "") + suffix
    records = _r7_bash_records(tmp_path, command, repos[start])
    if operation:
        executable, *argv = operation.split()
        assert records[0] == [executable, str(repos[start]), *argv]
    else:
        assert len(records) == (1 if prefix.startswith(("git commit", "gh pr create")) else 0)
    expected = guard._command_danger_reason(operation, repos[start]) is not None
    assert (guard._command_danger_reason(command, repos[start]) is not None) == expected


@pytest.mark.parametrize("start", ["public", "public_worktree"])
@pytest.mark.parametrize("prefix", ["", "git switch -c fixture && "])
@pytest.mark.parametrize("opener", ["<<'EOF'", '<<"EOF"', r"<<\EOF", "<<-'EOF'"])
@pytest.mark.parametrize("apostrophe", [False, True])
@pytest.mark.parametrize("body", R8_BODIES)
@pytest.mark.parametrize("shape,argv", R8_SHAPES)
def test_issue_9479_r8_quoted_branch_prose_is_data_bash(
    repos, tmp_path, start, prefix, opener, apostrophe, body, shape, argv
):
    if apostrophe:
        body += "\nIt's documented"
    closer = "\tEOF" if opener.startswith("<<-") else "EOF"
    command = prefix + shape.format(opener=opener, body=body, closer=closer)
    records = _r7_bash_records(tmp_path, command, repos[start])
    # Exact argv and call count prove that backticks, $(), and branch-looking
    # lines inside a quoted body execute no extra git or gh invocation.
    expected = [[argv[0], str(repos[start]), *argv[1:], "-" if " - " in shape else body]]
    if prefix:
        expected.insert(0, ["git", str(repos[start]), "switch", "-c", "fixture"])
    assert records == expected
    assert (guard._command_danger_reason(command, repos[start]) is not None) == (bool(prefix) and start == "public")


@pytest.mark.parametrize("start", ["public", "public_worktree"])
@pytest.mark.parametrize("opener", ["<<EOF", "<<-EOF"])
@pytest.mark.parametrize("apostrophe", [False, True])
@pytest.mark.parametrize("expansion", ["$(git checkout -b evil)", "`git checkout -b evil`"])
def test_issue_9479_r8_unquoted_branch_expansion_executes_bash(repos, tmp_path, start, opener, apostrophe, expansion):
    body = ("It's active: " if apostrophe else "active: ") + expansion
    closer = "\tEOF" if opener.startswith("<<-") else "EOF"
    command = f'git commit -m "$(cat {opener}\n{body}\n{closer}\n)"'
    records = _r7_bash_records(tmp_path, command, repos[start])
    assert records == [
        ["git", str(repos[start]), "checkout", "-b", "evil"],
        ["git", str(repos[start]), "commit", "-m", "It's active: " if apostrophe else "active: "],
    ]
    assert (guard._command_danger_reason(command, repos[start]) is not None) == (start == "public")
