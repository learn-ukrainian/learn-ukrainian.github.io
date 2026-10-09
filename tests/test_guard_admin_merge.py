"""Unit tests for the admin-merge guard hook (#M-0.5 / #1908).

Exercises the pure decision logic in
``agents_extensions/shared/hooks/guard-admin-merge.py``:

  * `gh pr merge ... --admin` detection (incl. wrappers + a positional PR number),
  * the quote-aware tokenizer (a `--admin` inside a quoted commit body is NOT a merge),
  * advisory-vs-blocking classification,
  * the fail-CLOSED `main()` decision (block on failing required check, on unknown PR,
    and on undeterminable check states; allow on green / advisory-only).

The hook filename has hyphens, so it is loaded by path via importlib. `main()` is guarded
by `__name__ == "__main__"`, so import has no side effects. Network functions
(`_pr_number`, `_failing_blocking_checks`) are monkeypatched — no `gh`/network in tests.
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
HOOK_PATH = REPO_ROOT / "agents_extensions/shared" / "hooks" / "guard-admin-merge.py"


def _load_hook():
    spec = importlib.util.spec_from_file_location("guard_admin_merge", HOOK_PATH)
    assert spec and spec.loader, f"could not load hook at {HOOK_PATH}"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


guard = _load_hook()

REDIRECTS_9479 = ["", "2>&1", ">file", "2>/dev/null", "&>file", "<file", "| cat"]


@pytest.mark.parametrize("redirect", REDIRECTS_9479)
@pytest.mark.parametrize("shape", ["cd", "admin-before", "admin-after", "implicit"])
def test_issue_9479_redirect_denominator(monkeypatch, redirect, shape):
    args = {"cd": "5 --admin", "admin-before": "--admin 5", "admin-after": "5 --admin", "implicit": "--admin"}[shape]
    command = {
        "cd": f"cd fixture {redirect} && gh pr merge 5 --admin {redirect}",
        "admin-before": f"gh pr merge --admin {redirect} 5",
        "admin-after": f"gh pr merge 5 {redirect} --admin",
        "implicit": f"gh pr merge --admin {redirect}",
    }[shape]
    if redirect == "| cat":
        command = f"gh pr merge {args} {redirect}"
        if shape == "cd":
            command = "cd fixture && " + command
    judged = [guard._admin_merge_args(seg) for seg in guard._segments(command)]
    assert args.split() in judged
    seen = []
    monkeypatch.setattr(guard, "_failing_blocking_checks", lambda pr, cwd=None: seen.append(pr) or ["Test (pytest)"])
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps({"tool_input": {"command": command}})))
    assert guard.main() == 2
    assert seen == ([] if shape == "implicit" else ["5"])


@pytest.mark.parametrize("command", ["gh pr merge --admin 2>&1", "gh pr merge 2>&1 5 --admin"])
def test_issue_9479_reviewer_reproductions(monkeypatch, command):
    seen = []
    monkeypatch.setattr(guard, "_failing_blocking_checks", lambda pr, cwd=None: seen.append(pr) or ["Test (pytest)"])
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps({"tool_input": {"command": command}})))
    assert guard.main() == 2
    assert seen == ([] if command.endswith("2>&1") else ["5"])


@pytest.mark.parametrize("redirect", REDIRECTS_9479)
@pytest.mark.parametrize("placement", ["before-number", "after-number", "cd"])
def test_issue_9479_real_bash_argv(tmp_path, monkeypatch, redirect, placement):
    recorder = tmp_path / "gh"
    recorder.write_text('#!/bin/bash\nprintf "%s\\n" "$PWD" "$@" > "$GUARD_RECORD"\n')
    recorder.chmod(0o755)
    (tmp_path / "file").touch()
    record = tmp_path / "record"
    if placement == "before-number":
        command = f"gh pr merge --admin {redirect} 5"
        expected = ["--admin", "5"]
    else:
        command = f"gh pr merge 5 {redirect} --admin"
        expected = ["5", "--admin"]
    if redirect == "| cat":
        command = "gh pr merge " + " ".join(expected) + " | cat"
    if placement == "cd":
        command = f"cd {tmp_path} {redirect if redirect != '| cat' else ''} && " + command
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
    assert actual == [str(tmp_path), "pr", "merge", *expected]
    judged = [guard._admin_merge_args(seg) for seg in guard._segments(command)]
    assert actual[3:] in judged
    seen = []
    monkeypatch.setattr(guard, "_failing_blocking_checks", lambda pr, cwd=None: seen.append(pr) or [])
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps({"tool_input": {"command": command}})))
    assert guard.main() == 0
    assert seen == ["5"]


@pytest.mark.parametrize("redirect", [">file", "2>&1", "<file", "&>file"])
@pytest.mark.parametrize("target", ["$PR", '"$PR"', "$(cat selector)", "`cat selector`"])
def test_issue_9479_redirect_never_launders_target(monkeypatch, redirect, target):
    monkeypatch.setattr(
        guard, "_failing_blocking_checks", lambda pr, cwd=None: pytest.fail("unreadable target reached lookup")
    )
    command = f"gh pr merge --admin {target} {redirect}"
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps({"tool_input": {"command": command}})))
    assert guard.main() == 2


@pytest.mark.parametrize(
    "redirect,position",
    [
        (redirect, position)
        for redirect in ['> "$FILE"', "> $(echo file)", "> `echo file`", ">"]
        for position in ["prefix", "suffix", "cd"]
        if (redirect, position) != (">", "prefix")
    ],
)
def test_issue_9479_dynamic_redirect_refused(monkeypatch, redirect, position):
    command = {
        "prefix": f"{redirect} gh pr merge 5 --admin",
        "suffix": f"gh pr merge 5 --admin {redirect}",
        "cd": f"cd fixture {redirect} && gh pr merge 5 --admin",
    }[position]
    monkeypatch.setattr(
        guard, "_failing_blocking_checks", lambda pr, cwd=None: pytest.fail("dynamic redirect reached lookup")
    )
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps({"tool_input": {"command": command}})))
    assert guard.main() == 2


@pytest.mark.parametrize("target", ["'>'", "'2>&1'", "'file$name'", r"file\$name"])
def test_issue_9479_literal_redirect_target(monkeypatch, target):
    command = f"gh pr merge 5 --admin > {target}"
    assert guard._segments(command) == [["gh", "pr", "merge", "5", "--admin"]]
    assert _run(monkeypatch, command, failing=[]) == 0


@pytest.mark.parametrize("hook", ["guard-admin-merge.py", "guard-branch-switch-in-main.py", "guard-pr-merge.py"])
def test_issue_9479_missing_shared_helper_fails_closed(tmp_path, hook):
    hook_path = HOOK_PATH.parent / hook
    shutil.copy2(hook_path, tmp_path / hook)
    command = "git switch -c fixture" if "branch" in hook else "gh pr merge 5 --admin"
    result = subprocess.run(
        [sys.executable, str(tmp_path / hook)],
        input=json.dumps({"tool_input": {"command": command}}),
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 2
    assert "guard dependency unavailable: shell_bash" in result.stderr


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
def test_issue_9102_executable_payload_stays_visible(monkeypatch, shape):
    command = shape.replace("{payload}", "gh pr merge 5 --admin")
    assert _any_admin(command)
    assert _run(monkeypatch, command, failing=["Test (pytest)"]) == 2


def test_issue_9102_real_let_heredoc_body_is_inert():
    assert not _any_admin("let x=1<<EOF\ngh pr merge 5 --admin\nEOF")


@pytest.mark.parametrize(
    "command",
    [
        "echo $(echo foo # comment \\\ngh pr merge 5 --admin)",
        "echo `gh pr merge 5 --admin`",
        'echo "`gh pr merge 5 --admin`"',
        "echo `echo foo # comment \\\ngh pr merge 5 --admin`",
        "echo $(echo foo # comment \\\n`gh pr merge 5 --admin`)",
    ],
)
def test_issue_9115_nested_and_backtick_admin_merges_blocked(monkeypatch, command):
    assert _any_admin(command)
    assert _run(monkeypatch, command, failing=["Test (pytest)"]) == 2


def test_issue_9115_escaped_nested_backtick_admin_merge_is_visible():
    assert _any_admin(r"echo `echo \`gh pr merge 5 --admin\``")


def test_issue_9115_backtick_depth_limit_blocks_in_hook(monkeypatch):
    monkeypatch.setattr(sys.modules["shell_bash"], "MAX_DEPTH", 2)
    body = "gh pr merge 5 --admin"
    for _ in range(3):
        body = "`" + body.replace("\\", "\\\\").replace("`", r"\`") + "`"
    assert _run(monkeypatch, "echo " + body, failing=[]) == 2


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
    assert not _any_admin(f"cat {opener}\ngh pr merge 5 --admin\n{closer}")
    assert _any_admin(f"cat {opener}\nnote\n{closer}\ngh pr merge 5 --admin")


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
def test_issue_9088_here_strings_keep_admin_merge_visible(monkeypatch, first):
    command = f"{first}\ngh pr merge 5 --admin\nEOF"
    assert ["true"] in guard._segments(first)
    assert _any_admin(command)
    assert _run(monkeypatch, command, failing=["Test (pytest)"]) == 2


def test_issue_9088_crlf_closer_keeps_admin_merge_visible(monkeypatch):
    command = "cat <<EOF\r\nEOF\r\ngh pr merge 5 --admin\nEOF"
    assert _any_admin(command)
    assert _run(monkeypatch, command, failing=["Test (pytest)"]) == 2


def test_issue_9088_reviewer_heredoc_bypass_blocks(monkeypatch):
    command = 'cat <<"EO\\"F"\nnote\nEO"F\ngh pr merge 1 --admin\ngit checkout -b feature\ntee AGENTS.md\necho $GH_TOKEN\ncat .env\nEO\\"F'
    assert _any_admin(command)
    assert _run(monkeypatch, command, failing=["Test (pytest)"]) == 2


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
def test_issue_9088_exotic_heredoc_keeps_admin_merge_visible(monkeypatch, opener, closer):
    command = f"cat {opener}\ngh pr merge 5 --admin\n{closer}"
    with pytest.raises(guard.ShellParseError):
        guard.read_commands(f"cat {opener}\nfixture\n{closer}")
    assert _any_admin(command)
    assert _run(monkeypatch, command, failing=["Test (pytest)"]) == 2


def test_issue_9088_exotic_body_cannot_skip_later_safe_opener(monkeypatch):
    command = "cat <<$'EOF'\ncat <<SAFE\ngh pr merge 5 --admin\nSAFE\nEOF"
    assert _any_admin(command)
    assert _run(monkeypatch, command, failing=["Test (pytest)"]) == 2


def test_issue_9088_missing_shell_helper_blocks(tmp_path):
    guard_copy = tmp_path / HOOK_PATH.name
    shutil.copy2(HOOK_PATH, guard_copy)
    result = subprocess.run(
        [sys.executable, str(guard_copy)],
        input=json.dumps({"tool_input": {"command": "gh pr merge 1 --admin"}}),
        text=True,
        capture_output=True,
        check=False,
        timeout=30,
    )
    assert result.returncode == 2
    assert "guard dependency unavailable: shell_bash" in result.stderr


def _run(monkeypatch, command: str, *, pr: str | None = "5", failing=()) -> int:
    """Drive main() with a simulated stdin payload + monkeypatched network calls."""
    payload = json.dumps({"tool_input": {"command": command}})
    monkeypatch.setattr("sys.stdin", io.StringIO(payload))
    monkeypatch.setattr(guard, "_pr_number", lambda args: pr)
    monkeypatch.setattr(
        guard, "_failing_blocking_checks", lambda p, cwd=None: list(failing) if failing is not None else None
    )
    return guard.main()


# --- detection (pure, no network) ------------------------------------------


@pytest.mark.parametrize(
    "shell_options",
    [
        "bash -oc errexit",
        "bash -co errexit",
        "bash -Oc extglob",
        "bash -cO extglob",
        "bash -xco errexit",
        "bash -xcO extglob",
        "bash -ooc errexit nounset",
        "bash -oOc errexit extglob",
        "sh -co errexit",
        "sh -oc errexit",
    ],
)
def test_issue_9484_packed_shell_c_options_blocked(monkeypatch, shell_options):
    command = f"{shell_options} 'gh pr merge 5 --admin'"
    with pytest.raises(guard.ShellParseError, match="packed shell -c with -o/-O"):
        guard.read_commands(command)
    assert _run(monkeypatch, command, failing=["Test (pytest)"]) == 2


@pytest.mark.parametrize("option", ["-xo errexit", "+xo errexit", "-xO extglob", "+xO extglob"])
def test_issue_9484_packed_shell_options_invalidate_directory(monkeypatch, option):
    command = f"bash {option} -c 'gh pr merge 5 --admin'"
    merges = [row for row in guard.read_commands(command) if guard._admin_merge_args(row.argv) is not None]
    assert len(merges) == 1
    assert merges[0].cwd_unreadable
    assert _run(monkeypatch, command) == 2


@pytest.mark.parametrize(
    "seg,is_admin",
    [
        (["gh", "pr", "merge", "--admin"], True),
        (["gh", "pr", "merge", "123", "--admin=true"], True),
        (["gh", "pr", "merge", "123", "--admin=false"], False),
        (["gh", "pr", "merge", "123", "--subject", "--admin"], False),
        (["gh", "pr", "merge", "123", "--admin", "--squash"], True),
        (["sudo", "gh", "pr", "merge", "--admin"], True),
        (["gh", "pr", "merge", "--squash"], False),
        (["gh", "pr", "merge", "--squash", "--delete-branch"], False),
        (["gh", "pr", "view", "5"], False),
        (["git", "push"], False),
    ],
)
def test_admin_merge_detection(seg, is_admin):
    assert (guard._admin_merge_args(seg) is not None) is is_admin


def test_quoted_admin_not_detected():
    # `--admin` inside a quoted commit body must NOT be seen as a merge command.
    segs = guard._segments('git commit -m "ref: gh pr merge --admin notes"')
    assert all(guard._admin_merge_args(s) is None for s in segs)


def test_is_advisory():
    assert guard._is_advisory("pip-audit (advisory)")
    assert guard._is_advisory("npm-audit (advisory)")
    assert not guard._is_advisory("Test (pytest)")
    assert not guard._is_advisory("Lint (ruff)")
    assert not guard._is_advisory("Frontend (build + vitest)")


# --- main() decision (fail-closed) -----------------------------------------


def test_non_admin_command_is_untouched(monkeypatch):
    assert _run(monkeypatch, "gh pr merge 5 --squash --delete-branch") == 0


def test_unrelated_command_is_untouched(monkeypatch):
    assert _run(monkeypatch, "git push origin main") == 0


def test_admin_with_failing_required_check_blocked(monkeypatch):
    assert _run(monkeypatch, "gh pr merge 5 --admin", failing=["Test (pytest)"]) == 2


def test_admin_equals_true_with_failing_required_check_blocked(monkeypatch):
    assert _run(monkeypatch, "gh pr merge 5 --admin=true", failing=["Test (pytest)"]) == 2


def test_admin_with_only_green_or_advisory_allowed(monkeypatch):
    # No failing *required* checks (advisory-only or all green) → the legitimate --admin.
    assert _run(monkeypatch, "gh pr merge 5 --admin", failing=[]) == 0


def test_admin_unknown_pr_fails_closed(monkeypatch):
    assert _run(monkeypatch, "gh pr merge --admin", pr=None) == 2


def test_admin_undeterminable_checks_fails_closed(monkeypatch):
    assert _run(monkeypatch, "gh pr merge 5 --admin", failing=None) == 2


# --- _failing_blocking_checks: gh-output handling (fail-open regression) -----


def _fake_gh(monkeypatch, *, returncode: int, stdout: str):
    import types

    def fake_run(*_a, **_k):
        return types.SimpleNamespace(returncode=returncode, stdout=stdout, stderr="")

    monkeypatch.setattr(guard.subprocess, "run", fake_run)


def test_failing_checks_empty_output_with_error_rc_is_failclosed(monkeypatch):
    # Regression: bogus/non-existent PR → gh errors with EMPTY stdout. Must be None
    # (fail-closed), NOT [] — `json.loads("[]")` once silently read this as "no failing
    # checks" and let the --admin bypass through.
    _fake_gh(monkeypatch, returncode=1, stdout="")
    assert guard._failing_blocking_checks("99999") is None


def test_failing_checks_empty_output_with_ok_rc_is_no_checks(monkeypatch):
    # PR genuinely has zero checks → rc 0, empty output → [] (nothing to bypass → allow).
    _fake_gh(monkeypatch, returncode=0, stdout="")
    assert guard._failing_blocking_checks("5") == []


def test_failing_checks_reports_failing_non_advisory(monkeypatch):
    rows = '[{"name":"Test (pytest)","bucket":"fail"},{"name":"pip-audit (advisory)","bucket":"fail"}]'
    _fake_gh(monkeypatch, returncode=8, stdout=rows)
    assert guard._failing_blocking_checks("5") == ["Test (pytest)"]


def test_failing_checks_advisory_only_is_empty(monkeypatch):
    rows = '[{"name":"pip-audit (advisory)","bucket":"fail"},{"name":"Test (pytest)","bucket":"pass"}]'
    _fake_gh(monkeypatch, returncode=8, stdout=rows)
    assert guard._failing_blocking_checks("5") == []


def test_failing_checks_garbage_output_is_failclosed(monkeypatch):
    _fake_gh(monkeypatch, returncode=0, stdout="not json")
    assert guard._failing_blocking_checks("5") is None


# --- #4876: glued-operator evasion class ------------------------------------


def _any_admin(command: str) -> bool:
    return any(guard._admin_merge_args(s) is not None for s in guard._segments(command))


@pytest.mark.parametrize(
    "cmd",
    [
        "true 2>&1 | head -1; gh pr merge 5 --admin",
        "gh pr view 5 --jq '{state}'; gh pr merge 5 --admin --squash",
        "echo hi\ngh pr merge 5 --admin",
        "true;gh pr merge 5 --admin",
    ],
)
def test_glued_operator_admin_merge_detected(cmd):
    assert _any_admin(cmd)


def test_heredoc_admin_mention_not_detected():
    cmd = "cat > /tmp/n.md <<'EOF'\nrun gh pr merge 5 --admin manually\nEOF"
    assert not _any_admin(cmd)


def test_backslash_continuation_admin_detected():
    assert _any_admin("gh pr merge 5 \\\n  --admin --squash")


# --- #4877 adversarial round (grok-build msg 2334) ---


@pytest.mark.parametrize(
    "cmd",
    [
        "env FOO=1 gh pr merge 5 --admin",
        "FOO=1 gh pr merge 5 --admin",
        "{ gh pr merge 5 --admin; }",
    ],
)
def test_wrapper_assignment_brace_admin_detected(cmd):
    assert _any_admin(cmd)


@pytest.mark.parametrize(
    "cmd",
    [
        "env -i gh pr merge 5 --admin",
        "env -i FOO=1 gh pr merge 5 --admin",
        "env -u FOO gh pr merge 5 --admin",
        "sudo -u root gh pr merge 5 --admin",
        "sudo --preserve-env gh pr merge 5 --admin",
        "sudo -E gh pr merge 5 --admin",
        "time -p gh pr merge 5 --admin",
        "nice -n 10 gh pr merge 5 --admin",
        "stdbuf -oL gh pr merge 5 --admin",
    ],
)
def test_wrapper_options_do_not_hide_admin_merge_verb(cmd):
    assert _any_admin(cmd)


def test_unclosed_heredoc_does_not_hide_admin():
    assert _any_admin("cat <<'NOEND'\nnote\ngh pr merge 5 --admin")


# --- colorized gh output (review B1, PR #5324) ------------------------------
# Agent harnesses export CLICOLOR_FORCE/FORCE_COLOR (beating NO_COLOR), and gh then
# colorizes piped --json output. The bare `json.loads` here raised JSONDecodeError ->
# None -> "undeterminable" -> BLOCK, so the one legitimate use of --admin this hook
# exists to permit (advisory-only failures, #M-0.5) was refused inside every agent
# harness. Same bug class as the sibling's B1; the guard must scrub the env AND
# tolerate residual ANSI.

# Escapes sit OUTSIDE the string tokens, as gh's colorizer actually emits them.
_COLORIZED_ROWS = (
    "\x1b[1;37m[\x1b[m{\n"
    '  \x1b[1;34m"name"\x1b[m: \x1b[32m"Test (pytest)"\x1b[m,\n'
    '  \x1b[1;34m"bucket"\x1b[m: \x1b[32m"pass"\x1b[m,\n'
    '  \x1b[1;34m"state"\x1b[m: \x1b[32m"SUCCESS"\x1b[m\n'
    "}\x1b[1;37m]\x1b[m\n"
)


def _capture_gh(monkeypatch, *, returncode: int = 0, stdout: str = "[]"):
    """Like _fake_gh, but records each call's argv + kwargs so the env can be asserted."""
    import types

    calls: list[tuple] = []

    def fake_run(cmd, **kwargs):
        calls.append((cmd, kwargs))
        return types.SimpleNamespace(returncode=returncode, stdout=stdout, stderr="")

    monkeypatch.setattr(guard.subprocess, "run", fake_run)
    return calls


def test_gh_env_scrubs_color_forcers(monkeypatch):
    monkeypatch.setenv("CLICOLOR_FORCE", "1")
    monkeypatch.setenv("FORCE_COLOR", "1")
    env = guard._gh_env()
    assert "CLICOLOR_FORCE" not in env
    assert "FORCE_COLOR" not in env
    assert env["NO_COLOR"] == "1"
    assert env["CLICOLOR"] == "0"


def test_decolorize_recovers_parseable_json():
    assert json.loads(guard._decolorize(_COLORIZED_ROWS)) == [
        {"name": "Test (pytest)", "bucket": "pass", "state": "SUCCESS"}
    ]


def test_colorized_check_rows_still_parse(monkeypatch):
    """The B1 bug itself: colorized rows must not read as undeterminable (None), which
    would fail-close and block a green PR's --admin merge."""
    _fake_gh(monkeypatch, returncode=0, stdout=_COLORIZED_ROWS)
    assert guard._failing_blocking_checks("5") == []


def test_colorized_advisory_only_failure_still_allows(monkeypatch):
    """End-to-end verdict, the user-level consequence: an advisory-only failure is the
    ONE legitimate --admin case (#M-0.5). Colorized, it was blocked."""
    rows = (
        '\x1b[1;37m[\x1b[m{\x1b[1;34m"name"\x1b[m: \x1b[32m"pip-audit (advisory)"\x1b[m, '
        '\x1b[1;34m"bucket"\x1b[m: \x1b[31m"fail"\x1b[m}\x1b[1;37m]\x1b[m'
    )
    _fake_gh(monkeypatch, returncode=0, stdout=rows)
    monkeypatch.setattr(guard, "_pr_number", lambda args: "5")
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps({"tool_input": {"command": "gh pr merge 5 --admin"}})))
    assert guard.main() == 0


def test_colorized_blocking_failure_still_blocks(monkeypatch):
    """Verdict unflipped in the anti-bypass direction: decolorizing must not lose the
    `fail` bucket and let a red blocking check through."""
    rows = (
        '\x1b[1;37m[\x1b[m{\x1b[1;34m"name"\x1b[m: \x1b[32m"Test (pytest)"\x1b[m, '
        '\x1b[1;34m"bucket"\x1b[m: \x1b[31m"fail"\x1b[m}\x1b[1;37m]\x1b[m'
    )
    _fake_gh(monkeypatch, returncode=0, stdout=rows)
    assert guard._failing_blocking_checks("5") == ["Test (pytest)"]


def test_pr_number_requires_explicit_numeric_selector():
    assert guard._pr_number(["--admin"]) is None
    assert guard._pr_number(["5", "--admin"]) == "5"


def test_gh_check_lookup_runs_with_scrubbed_env(monkeypatch):
    monkeypatch.setenv("CLICOLOR_FORCE", "1")
    monkeypatch.setenv("FORCE_COLOR", "1")
    calls = _capture_gh(monkeypatch, returncode=0, stdout="[]")
    guard._failing_blocking_checks("5")
    assert len(calls) == 1
    for cmd, kwargs in calls:
        env = kwargs.get("env")
        assert env is not None, f"{cmd} ran without a scrubbed env"
        assert "CLICOLOR_FORCE" not in env and "FORCE_COLOR" not in env
        assert env["NO_COLOR"] == "1" and env["CLICOLOR"] == "0"


def test_gh_timeouts_stay_within_hook_budget(monkeypatch):
    """The only admin lookup must fit the aggregate merge-guard budget."""
    calls = _capture_gh(monkeypatch, returncode=0, stdout="[]")
    guard._failing_blocking_checks("5")
    timeouts = [kwargs["timeout"] for _cmd, kwargs in calls]
    assert all(t > 0 for t in timeouts)
    assert sum(timeouts) < 20


@pytest.mark.parametrize("shape", ["cd {cwd} &&>file gh pr merge 5 --admin", "{fd}>file gh pr merge 5 --admin"])
def test_issue_9479_r2_redirect_bash_argv(tmp_path, monkeypatch, shape):
    command = shape.replace("{cwd}", str(tmp_path))
    recorder = tmp_path / "gh"
    recorder.write_text('#!/bin/bash\nprintf "%s\\n" "$@" > "$GUARD_RECORD"\n')
    recorder.chmod(0o755)
    record = tmp_path / "record"
    result = subprocess.run(
        ["bash", "-c", command],
        cwd=tmp_path,
        env={**os.environ, "PATH": str(tmp_path) + os.pathsep + os.environ["PATH"], "GUARD_RECORD": str(record)},
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 0, result.stderr
    assert record.read_text().splitlines() == ["pr", "merge", "5", "--admin"]
    assert ["5", "--admin"] in [guard._admin_merge_args(seg) for seg in guard._segments(command)]
    seen = []
    monkeypatch.setattr(guard, "_failing_blocking_checks", lambda pr, cwd=None: seen.append(pr) or ["CI Gate"])
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps({"tool_input": {"command": command}})))
    assert guard.main() == 2
    assert seen == ["5"]


def test_admin_checks_follow_literal_cd(monkeypatch, tmp_path):
    target = tmp_path / "a"
    target.mkdir()
    calls = _capture_gh(monkeypatch, returncode=0, stdout='[{"name":"CI Gate","bucket":"fail"}]')
    payload = {"cwd": str(tmp_path), "tool_input": {"command": "cd a; gh pr merge 5 --admin"}}
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(payload)))
    assert guard.main() == 2
    assert calls[0][1]["cwd"] == str(target)


def test_admin_unknown_cd_cannot_reach_checks(monkeypatch):
    monkeypatch.setattr(
        guard, "_failing_blocking_checks", lambda *args, **kwargs: pytest.fail("unknown repository reached checks")
    )
    monkeypatch.setattr(
        sys, "stdin", io.StringIO(json.dumps({"tool_input": {"command": 'cd "$P"; gh pr merge 5 --admin'}}))
    )
    assert guard.main() == 2
