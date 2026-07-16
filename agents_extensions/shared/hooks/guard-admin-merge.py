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

import json
import os
import re
import shlex
import subprocess
import sys

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


# --- Command segmentation hardened against glued shell operators (#4876). ---
# Pattern lifted from guard-secret-print.py. Hooks are standalone by design,
# so the helpers are copied, not imported. Keep the three copies in
# guard-branch-switch-in-main.py, guard-admin-merge.py, and
# guard-push-pytest.py in sync.


def _strip_quotes(token: str) -> str:
    if len(token) >= 2 and token[0] == token[-1] and token[0] in {"'", '"'}:
        return token[1:-1]
    return token


def _heredoc_delimiters(line: str) -> list[tuple[str, bool]]:
    """Return (delimiter, strip_tabs) per heredoc opener; handles spaced
    ``<< EOF`` / ``<< - EOF`` and attached ``<<-EOF`` / ``<<-'EOF'`` (#4877)."""
    try:
        lexer = shlex.shlex(line, posix=False, punctuation_chars=True)
        lexer.whitespace_split = True
        lexer.commenters = ""
        tokens = list(lexer)
    except ValueError:
        return []

    delimiters: list[tuple[str, bool]] = []
    i = 0
    while i < len(tokens):
        if tokens[i] != "<<":
            i += 1
            continue
        strip_tabs = False
        j = i + 1
        delim_tok = ""
        if j < len(tokens):
            nxt = tokens[j]
            if nxt == "-":
                strip_tabs = True
                j += 1
                if j < len(tokens):
                    delim_tok = tokens[j]
            elif nxt.startswith("-") and len(nxt) > 1:
                strip_tabs = True
                delim_tok = nxt[1:]
            else:
                delim_tok = nxt
        delimiter = _strip_quotes(delim_tok)
        if delimiter:
            delimiters.append((delimiter, strip_tabs))
        i = j + 1
    return delimiters


def _strip_heredoc_bodies(command: str) -> str:
    """Drop heredoc BODY lines — document text is data, not commands.

    Fail-CLOSED on an unclosed heredoc (#4877): a never-closing / mis-parsed
    opener must not make trailing real `gh pr merge --admin` vanish. Only a
    heredoc that actually closes has its body + closer dropped.
    """
    if "<<" not in command:
        return command

    lines = command.splitlines()
    kept: list[str] = []
    i = 0
    n = len(lines)
    while i < n:
        kept.append(lines[i])
        i += 1
        pending = _heredoc_delimiters(lines[i - 1])
        if not pending:
            continue
        body_start = i
        while i < n and pending:
            delimiter, strip_tabs = pending[0]
            candidate = lines[i].lstrip("\t") if strip_tabs else lines[i]
            if candidate == delimiter:
                pending.pop(0)
            i += 1
        if pending:
            kept.extend(lines[body_start:i])
    return "\n".join(kept)


def _join_line_continuations(text: str) -> str:
    r"""Fold `\<newline>` into one logical line, as the shell does — so a
    `\`-continued `gh pr merge --admin` is not split across physical lines
    and missed. Over-folding a quoted literal `\` only merges argv text."""
    return text.replace("\\\n", "")


def _segments(command: str) -> list[list[str]]:
    """Quote-aware argv segments, robust to glued shell operators (#4876).

    A `--admin` inside a quoted commit body (`git commit -m "... --admin ..."`)
    stays one argv element — no false block. A `; gh pr merge --admin` glued
    to a preceding token (`…'; gh pr merge --admin`) is now split into its
    own segment and inspected — no evasion. Heredoc bodies are stripped
    (document text is not commands); `\\`-continuations are folded; each
    logical line parses separately.
    """
    segs: list[list[str]] = []
    for line in _join_line_continuations(_strip_heredoc_bodies(command)).splitlines():
        try:
            lexer = shlex.shlex(line, posix=True, punctuation_chars=True)
            lexer.whitespace_split = True
            tokens = list(lexer)
        except ValueError:
            continue
        cur: list[str] = []
        for tok in tokens:
            if tok and all(c in ";|&()<>" for c in tok):
                if cur:
                    segs.append(cur)
                    cur = []
            else:
                cur.append(tok)
        if cur:
            segs.append(cur)
    return segs


def _is_env_assignment(tok: str) -> bool:
    return "=" in tok and not tok.startswith("-") and tok.split("=", 1)[0].isidentifier()


def _skip_command_prefix(seg: list[str], i: int) -> int:
    """Advance past wrappers / env-assignments / brace-group open so a
    `env FOO=1 gh pr merge --admin` or `{ gh pr merge --admin; }` is not
    missed (#4877)."""
    while i < len(seg):
        tok = seg[i]
        if tok in {"sudo", "time", "env", "nohup", "command", "exec", "{"} or _is_env_assignment(
            tok
        ):
            i += 1
        else:
            break
    return i


def _admin_merge_args(seg: list[str]) -> list[str] | None:
    """Return the args of a `gh pr merge ... --admin` segment, else None."""
    i = _skip_command_prefix(seg, 0)
    if seg[i : i + 3] != ["gh", "pr", "merge"]:
        return None
    args = seg[i + 3 :]
    return args if "--admin" in args else None


def _pr_number(args: list[str]) -> str | None:
    """First numeric positional after `merge`, else the current branch's PR number."""
    for a in args:
        if not a.startswith("-") and a.isdigit():
            return a
    try:
        out = subprocess.run(
            ["gh", "pr", "view", "--json", "number", "-q", ".number"],
            capture_output=True,
            env=_gh_env(),
            text=True,
            timeout=10,
        )
        # Decolorized before use, not just before json.loads: a colorized "5" is passed
        # straight to the next gh call as the PR selector, where the escapes break it.
        return _decolorize(out.stdout or "").strip() or None
    except Exception:
        return None


def _failing_blocking_checks(pr: str) -> list[str] | None:
    """Failing non-advisory check names for the PR, or None if undeterminable (→ fail-closed)."""
    try:
        out = subprocess.run(
            ["gh", "pr", "checks", pr, "--json", "name,bucket,state"],
            capture_output=True,
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
    payload = _read_payload()
    command = _command(payload)
    # Fast path: only engage on `gh ... --admin` (leave every other command untouched).
    if not command or "--admin" not in command or "gh" not in command:
        return 0
    for seg in _segments(command):
        args = _admin_merge_args(seg)
        if args is None:
            continue
        pr = _pr_number(args)
        if not pr:
            sys.stderr.write(_block_msg("could not determine the target PR number"))
            return 2
        failing = _failing_blocking_checks(pr)
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
