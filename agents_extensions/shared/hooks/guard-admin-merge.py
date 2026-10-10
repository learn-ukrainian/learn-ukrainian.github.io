#!/usr/bin/env python3
"""PreToolUse guard — block `gh pr merge --admin` when a BLOCKING CI check is red (#M-0.5 / #1908).

Reads the Claude Code hook payload on stdin (JSON with `tool_input.command`) and exits
2 (block) when the command is a `gh pr merge ... --admin` whose target PR has any
*blocking* (required) check in a failing state. Exit 0 (allow) otherwise — including
`--admin` merges where ONLY *advisory* checks fail, which is the one legitimate use of
`--admin` per #M-0.5.

Why a hook (#1908): "#M-0.5 don't admin-bypass blocking CI" is advisory text in
MEMORY.md that has been violated despite being canonical. A PreToolUse guard pushes it
to the enforcement layer — the bypass is refused before the merge runs, not "the model
tries to remember."

FAIL-CLOSED: if the target PR or its check states can't be determined (gh error/timeout,
no PR number), BLOCK. An anti-bypass guard must not let an *unverifiable* bypass through;
the human can always run the merge directly if it is genuinely intended.

Blocking (required) checks per #M-0.5: pytest, ruff, frontend/vitest, schema/MDX drift,
gitleaks/secret-scan, radon/quality-gates, prompt-lint, CodeQL/Analyze. Matched by name
substring (case-insensitive); erring toward "treat as blocking" is the safe direction here.
"""

from __future__ import annotations

import importlib
import json
import os
import re
import subprocess
import sys


def _expansion_may_build_words(probe: str) -> bool:
    """Whether an expansion could assemble the guarded words at run time.

    Variables and substitutions can spell `gh`, `pr merge` or `--admin` without those
    words appearing in the raw text (`G=gh; $G pr merge 5 --$A$B`), so such commands must
    reach the parser. Plain data expansions (`printf %s "$FOO"`) stay on the fast path.
    """
    if not re.search(r"[$`]", probe):
        return False
    if re.search(r"\$\(|`", probe):  # command substitution yields arbitrary words
        return True
    if re.search(r"\beval\b|(?:^|\s)-[a-zA-Z]*c\b", probe):  # dynamic payloads are re-read
        return True
    # expansion as the command name, directly or behind a wrapper's own options (`timeout 5 $G$H`)
    if re.search(
        r"(?:^|[;&|(\n])\s*(?:(?:timeout|nice|nohup|exec|command|builtin|time|sudo|xargs|env)"
        r"(?:\s+-\S+(?:\s+[A-Za-z]+)?|\s+[\d.]+[smhd]?|\s+\w+=\S+)*\s+)?!?\s*\$",
        probe,
    ):
        return True
    names = re.findall(r"(?:^|[\s;&|(])([A-Za-z_]\w*)=", probe)
    return any(re.search(r"\$\{?" + re.escape(name) + r"\b", probe) for name in names)


def _may_guard(command: str) -> bool:
    # Include Bash dollar quoting and numeric ANSI-C escapes in the raw gate.
    # This is only a conservative prefilter; the pinned AST decides execution.
    probe = re.sub(r"\$(['\"])", r"\1", command)
    try:
        probe = re.sub(
            r"\\(x[0-9a-fA-F]{1,2}|u[0-9a-fA-F]{1,4}|U[0-9a-fA-F]{1,8}|[0-7]{1,3})",
            lambda m: chr(int(m[1][1:], 16) if m[1][0] in "xuU" else int(m[1], 8)),
            probe,
        )
    except ValueError:
        return True  # unreadable escape: let the full parser refuse it
    probe = probe.replace("\\\n", "").replace("\\", "").replace("'", "").replace('"', "")
    if _expansion_may_build_words(probe):
        return True
    return bool(
        ("git" in re.sub(r"\$git\b", "", probe) and re.search(r"\b(?:checkout|switch|branch)\b", probe))
        or (("gh" in probe or re.search(r"\bpr\s+merge\b", probe)) and "--admin" in probe)
        or re.search(r"(?:^|[\s;{])gh\s+[^;\n]*\$", probe)
        or re.search(r"(?:--pre(?:=|\s)|--config-env|\bmergetool\b|\bgit\s+worktree[^;\n]*\$|\bgh\s+alias\s)", probe)
    )


if __name__ == "__main__":
    try:
        _CLI_PAYLOAD = json.loads(sys.stdin.read() or "{}")
        _CLI_COMMAND = (_CLI_PAYLOAD.get("tool_input") or {}).get("command", "")
        if isinstance(_CLI_COMMAND, str) and not _may_guard(_CLI_COMMAND):
            sys.exit(0)
    except (ValueError, AttributeError):
        print("BLOCKED: malformed hook payload; provide a literal Bash command", file=sys.stderr)
        sys.exit(2)


sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# Don't write __pycache__ next to deployed hooks (#9108).
sys.dont_write_bytecode = True
try:
    from shell_bash import REPAIR, UNREADABLE, ShellParseError, invoked_start, read_commands
except Exception as exc:
    print(
        f"guard dependency unavailable: shell_bash ({type(exc).__name__}); "
        "repair: uv pip install --python <canonical-checkout>/.venv/bin/python "
        "--require-hashes --only-binary=:all: -r requirements-hooks.txt; "
        "npm run agents:deploy",
        file=sys.stderr,
    )
    raise SystemExit(2) from None


_merge_guard = importlib.import_module("guard-pr-merge")


# Agent harnesses export CLICOLOR_FORCE/FORCE_COLOR, which beat NO_COLOR and make
# `gh --json` emit ANSI-colorized JSON on pipes -> json.loads fails -> the guard reads
# every check state as undeterminable and fail-closes, blocking the legitimate
# advisory-only --admin merge it exists to permit (review B1, PR #5324). Every gh
# subprocess below runs with the force vars REMOVED and NO_COLOR pinned; _decolorize()
# strips any residual escapes. Kept identical to guard-pr-merge.py's copy.
_ANSI_RE = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")


def _gh_env() -> dict[str, str]:
    env = {k: v for k, v in os.environ.items() if k not in {"CLICOLOR_FORCE", "FORCE_COLOR"}}
    env["NO_COLOR"] = "1"
    env["CLICOLOR"] = "0"
    return env


def _decolorize(text: str) -> str:
    return _ANSI_RE.sub("", text)


# A check is treated as BLOCKING unless its name marks it explicitly advisory.
# Rationale (anti-bypass safe direction): an allowlist of "known required" names would
# UNDER-block — a new required check absent from the list would let an admin-bypass slip
# through. So we invert: any FAILING check blocks --admin *unless* it is explicitly
# advisory. Advisory-only failures don't even need --admin (a normal `gh pr merge` passes
# non-required checks), so a Claude --admin over a failure implies bypassing something
# required — exactly what #M-0.5 forbids. The human can still run a genuine handoff-
# authorized advisory bypass directly.
ADVISORY_NAME_MARKERS = ("advisory",)

_FAIL_BUCKETS = {"fail", "failure", "error", "cancel", "canceled", "cancelled", "timed_out", "action_required"}
_FALSE_VALUES = {"false", "f", "0"}
_VALUE_FLAGS = {
    "--subject",
    "-t",
    "--body",
    "-b",
    "--body-file",
    "-F",
    "--match-head-commit",
    "--author-email",
    "-A",
    "--repo",
    "-R",
}


def _is_advisory(name: str) -> bool:
    low = name.lower()
    return any(m in low for m in ADVISORY_NAME_MARKERS)


def _read_payload() -> dict:
    try:
        return json.loads(sys.stdin.read() or "{}")
    except json.JSONDecodeError:
        return {}


def _command(payload: dict) -> str:
    return ((payload.get("tool_input") or {}).get("command") or "").strip()


def _flag_enabled(args: list[str], name: str) -> bool:
    """Whether the last occurrence of a boolean flag enables it."""
    enabled = False
    i = 0
    while i < len(args):
        arg = args[i]
        if arg in _VALUE_FLAGS:
            i += 2
            continue
        if arg.startswith("--") and arg.split("=", 1)[0] in _VALUE_FLAGS:
            i += 1
            continue
        if arg == f"--{name}":
            enabled = True
        elif arg.startswith(f"--{name}="):
            enabled = arg.split("=", 1)[1].strip().lower() not in _FALSE_VALUES
        i += 1
    return enabled


_UNREADABLE_MARKER = UNREADABLE


def _skip_command_prefix(seg, i):
    return i + invoked_start(seg[i:])[0]


def _segments(command: str) -> list[list[str]]:
    try:
        return [row.argv for row in read_commands(command, include_payloads=False)]
    except ShellParseError:
        return [["gh", "pr", "merge", "--admin", UNREADABLE]] if _may_guard(command) else []


def _admin_merge_args(seg: list[str]) -> list[str] | None:
    """Return the args of a `gh pr merge ... --admin` segment, else None."""
    args = _merge_guard._merge_args(seg)
    return args if args is not None and _merge_guard._flag_enabled(_merge_guard._classify(args)[0], "admin") else None


def _pr_number(args: list[str]) -> str | None:
    """Explicit selector after removing value-taking options."""
    return None if UNREADABLE in args else _merge_guard._pr_selector(args)


def _failing_blocking_checks(pr: str, cwd: str | None = None, repo: str | None = None) -> list[str] | None:
    """Failing non-advisory check names for the PR, or None if undeterminable (→ fail-closed)."""
    try:
        out = subprocess.run(
            ["gh", "pr", "checks", pr, *_merge_guard._repo_args(repo), "--json", "name,bucket,state"],
            capture_output=True,
            cwd=cwd,
            env=_gh_env(),
            text=True,
            timeout=8,
        )
    except Exception:
        return None
    text = (out.stdout or "").strip()
    if not text:
        # Empty output is ambiguous: a PR with zero checks (rc 0 → allow, nothing to
        # bypass) vs a gh error / non-existent PR (rc != 0 → fail-CLOSED block). Without
        # the returncode check, `json.loads("[]")` silently reads an *error* as "no
        # failing checks" and lets the bypass through — the fail-open bug this closes.
        return [] if out.returncode == 0 else None
    try:
        rows = json.loads(_decolorize(text))
    except json.JSONDecodeError:
        return None
    if not isinstance(rows, list):
        return None
    failing: list[str] = []
    for r in rows:
        bucket = str(r.get("bucket") or r.get("state") or "").lower()
        if bucket in _FAIL_BUCKETS:
            name = str(r.get("name") or "")
            if not _is_advisory(name):
                failing.append(name)
    return failing


def _block_msg(reason: str) -> str:
    return (
        f"BLOCKED by guard-admin-merge (#M-0.5): {reason}.\n\n"
        "`gh pr merge --admin` bypasses branch protection INCLUDING required CI "
        "(pytest, ruff, frontend, schema/MDX drift, gitleaks, radon, prompt-lint, CodeQL).\n"
        "Per #M-0.5, --admin is ONLY for explicitly-advisory failures. If a blocking check is\n"
        "red: STOP, report, and ask — do NOT bypass. If this is a genuine advisory-only case,\n"
        "fix the failing checks first, or the human runs the merge directly.\n\n"
        "Hook source: .claude/hooks/guard-admin-merge.py\n"
    )


def main() -> int:
    payload = _CLI_PAYLOAD if __name__ == "__main__" else _read_payload()
    command = _command(payload)
    # Fast path: only engage on `gh ... --admin` (leave every other command untouched).
    if not command or not _may_guard(command):
        return 0
    try:
        rows = read_commands(
            command,
            cwd=payload.get("cwd") or os.getcwd(),
            consumer_check=lambda *args: _merge_guard._check_consumer(
                *args, eval_guarded=bool(_merge_guard._may_merge(command, include_branch=False))
            ),
        )
        segments = [row.argv for row in rows]
    except Exception as exc:
        if (
            isinstance(exc, ShellParseError)
            and str(exc) in {"Bash parse error", "ambiguous heredoc delimiter", "reserved word parsed as an argument"}
            and not _merge_guard._may_merge(command, include_branch=False)
        ):
            # Unrelated malformed branch syntax is the branch guard's scope.
            return 0
        sys.stderr.write(
            _block_msg(
                f"shell command cannot be read: {str(exc) if isinstance(exc, ShellParseError) else type(exc).__name__}; repair: {REPAIR}"
            )
        )
        return 2
    redirect_unreadable = any(row.redirect_unknown for row in rows) or any(
        _UNREADABLE_MARKER in seg for seg in segments
    )
    for row in rows:
        args = _admin_merge_args(row.argv)
        if args is None:
            continue
        if row.environment_repo is not None and not _merge_guard._repo_option(args):
            args = [*args, "--repo", row.environment_repo]
        if _merge_guard._target_conflict(args):
            sys.stderr.write(_block_msg("conflicting merge repositories"))
            return 2
        if row.cwd_unreadable:
            sys.stderr.write(
                _block_msg(f"merge working directory cannot be read; use a literal directory; repair: {REPAIR}")
            )
            return 2
        pr = None if redirect_unreadable else _pr_number(args)
        if not pr:
            sys.stderr.write(_block_msg("could not determine the target PR number"))
            return 2
        repo = _merge_guard._repo_option(args)
        failing = _failing_blocking_checks(pr, cwd=row.cwd, **({"repo": repo} if repo else {}))
        if failing is None:
            sys.stderr.write(_block_msg(f"could not verify PR #{pr} check states (gh error/timeout)"))
            return 2
        if failing:
            sys.stderr.write(_block_msg(f"PR #{pr} has FAILING blocking checks: {', '.join(failing)}"))
            return 2
        # All blocking checks green (only advisory failures, if any) → allow the
        # legitimate --admin use.
    return 0


if __name__ == "__main__":
    sys.exit(main())
