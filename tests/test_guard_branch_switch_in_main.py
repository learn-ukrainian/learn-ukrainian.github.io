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
    segments = guard._segments_with_following_operator(command)
    cd_argv, operator = segments[0]
    assert operator == "&&"
    assert str(guard._cd_target(cd_argv, tmp_path)) == actual[0]
    assert ["git", *actual[1:]] in [argv for argv, _ in segments]
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
    monkeypatch.setattr(sys.modules["shell_shlex"], "_MAX_BACKTICK_DEPTH", 2)
    monkeypatch.chdir(repos["public"])
    body = "git checkout -b feature"
    for _ in range(3):
        body = "`" + body.replace("\\", "\\\\").replace("`", r"\`") + "`"
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps({"tool_input": {"command": "echo " + body}})))
    assert guard.main() == 2


def test_issue_9088_heredoc_opener_after_escaped_quote_is_found():
    assert guard._heredoc_delimiters(r'echo "a \" b" <<EOF') == [("EOF", False)]


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
    assert guard._heredoc_delimiters(f"cat {opener}") == [("EOF", opener == "<<-EOF")]
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
    assert guard._heredoc_delimiters(first) == []
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
    assert guard._heredoc_delimiters(f"cat {opener}") is None
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
    assert "guard dependency unavailable: shell_shlex" in result.stderr


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
    assert (guard._command_danger_reason(command, cwd) is not None) == (actual[0] == str(repos["public"]))


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
    rows = guard._segments_with_following_operator(command)
    assert rows[0][1] == "&&open"
    assert rows[1][1] == "close&&"


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
