#!/usr/bin/env python3
"""PreToolUse guard - require recent pytest before direct pushes from main.

Reads the hook payload on stdin (JSON with ``tool_input.command``) and exits 2
only when a real ``git push`` is about to run from ``main``, the outgoing diff
contains pytest-triggering paths, and the branch's pytest stamp is absent or
stale. All repository/probe errors fail open: this hook is a discipline net, not
a security boundary.
"""

from __future__ import annotations

import json
import os
import shlex
import subprocess
import sys
import time
from pathlib import Path

MARKER_MAX_AGE_SECONDS = 10 * 60
TRIGGER_PREFIXES = (
    "tests/",
    "scripts/",
    "curriculum/",
    "agents_extensions/shared/rules/",
    ".dagger/",
)
WRAPPERS = {"sudo", "time", "env", "nohup"}


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
            if nxt == "-":  # spaced: << - DELIM
                strip_tabs = True
                j += 1
                if j < len(tokens):
                    delim_tok = tokens[j]
            elif nxt.startswith("-") and len(nxt) > 1:  # attached: <<-DELIM
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
    opener must not make a trailing real `git push` vanish. Only a heredoc
    that actually closes has its body + closer dropped.
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
    `\`-continued `git push` is not split across physical lines and missed.
    Over-folding a quoted literal `\` only merges argv text."""
    return text.replace("\\\n", "")


def _segments(command: str) -> list[list[str]]:
    """Quote-aware argv segments, robust to glued shell operators (#4876).

    Operator runs (`;`, `|`, `&`, `(`, `)`, `<`, `>`) become their own
    tokens even when glued to a neighbour, `\\`-continuations are folded,
    logical lines parse separately, and heredoc bodies are stripped before
    parsing.
    """
    segments: list[list[str]] = []
    for line in _join_line_continuations(_strip_heredoc_bodies(command)).splitlines():
        try:
            lexer = shlex.shlex(line, posix=True, punctuation_chars=True)
            lexer.whitespace_split = True
            tokens = list(lexer)
        except ValueError:
            continue
        current: list[str] = []
        for tok in tokens:
            if tok and all(c in ";|&()<>" for c in tok):
                if current:
                    segments.append(current)
                    current = []
            else:
                current.append(tok)
        if current:
            segments.append(current)
    return segments


def _skip_git_global_flags(seg: list[str], i: int) -> int:
    """Return the index of the git verb after top-level git flags."""
    while i < len(seg) and seg[i].startswith("-"):
        if seg[i] in {"-C", "-c", "--git-dir", "--work-tree"} and i + 1 < len(seg):
            i += 2
        else:
            i += 1
    return i


def _push_is_dry_run(args: list[str]) -> bool:
    for arg in args:
        if arg == "--":
            return False
        if arg == "--dry-run":
            return True
        if len(arg) > 1 and arg.startswith("-") and not arg.startswith("--") and "n" in arg[1:]:
            return True
    return False


def _push_is_help(args: list[str]) -> bool:
    return any(arg in {"-h", "--help"} for arg in args)


def _is_env_assignment(tok: str) -> bool:
    return "=" in tok and not tok.startswith("-") and tok.split("=", 1)[0].isidentifier()


def _git_push_args(seg: list[str]) -> list[str] | None:
    """Return args for a real ``git push`` segment, else None."""
    # Skip wrappers / env-assignments / brace-group open so `env X=1 git push`
    # and `{ git push; }` are not missed (#4877).
    i = 0
    while i < len(seg) and (
        seg[i] in WRAPPERS or seg[i] in {"command", "exec", "{"} or _is_env_assignment(seg[i])
    ):
        i += 1
    if i >= len(seg) or seg[i] != "git":
        return None
    i = _skip_git_global_flags(seg, i + 1)
    if i >= len(seg) or seg[i] != "push":
        return None
    args = seg[i + 1 :]
    if _push_is_dry_run(args) or _push_is_help(args):
        return None
    return args


def _contains_git_push(command: str) -> bool:
    return any(_git_push_args(seg) is not None for seg in _segments(command))


def _has_inline_skip(command: str) -> bool:
    """Check if the command includes inline SKIP_PYTEST_HOOK=1 override before a git push."""
    for seg in _segments(command):
        if _git_push_args(seg) is not None:
            for tok in seg:
                if tok == "git":
                    break
                if tok in {"SKIP_PYTEST_HOOK=1", "SKIP_PYTEST_HOOK=\"1\"", "SKIP_PYTEST_HOOK=\x271\x27"}:
                    return True
    return False


def _current_branch() -> str | None:
    try:
        out = subprocess.run(
            ["git", "branch", "--show-current"],
            capture_output=True,
            text=True,
            timeout=5,
        )
    except Exception:
        return None
    if out.returncode != 0:
        return None
    branch = out.stdout.strip()
    return branch or None


def _changed_paths() -> list[str] | None:
    try:
        out = subprocess.run(
            ["git", "diff", "--name-only", "origin/main..HEAD"],
            capture_output=True,
            text=True,
            timeout=20,
        )
    except Exception:
        return None
    if out.returncode != 0:
        return None
    return [line.strip() for line in out.stdout.splitlines() if line.strip()]


def _is_trigger_path(path: str) -> bool:
    return path.endswith(".py") or any(path == prefix.rstrip("/") or path.startswith(prefix) for prefix in TRIGGER_PREFIXES)


def _has_trigger_path(paths: list[str]) -> bool:
    return any(_is_trigger_path(path) for path in paths)


def _marker_path(branch: str) -> Path:
    return Path(os.environ.get("TMPDIR") or "/tmp") / f"learn-uk-pytest.{branch}.stamp"


def _marker_is_fresh(path: Path) -> bool | None:
    try:
        stat = path.stat()
    except FileNotFoundError:
        return False
    except Exception:
        return None
    try:
        return time.time() - stat.st_mtime <= MARKER_MAX_AGE_SECONDS
    except Exception:
        return None


def _block_msg(branch: str, marker: Path) -> str:
    return (
        f"BLOCKED by guard-push-pytest (#M-7): direct push from `{branch}` includes "
        "Python/test-trigger changes, but no recent local pytest stamp was found.\n\n"
        f"Marker path: {marker}\n"
        "Run `.venv/bin/python -m pytest ...` locally, then push again within "
        "10 minutes. To override deliberately, rerun with `SKIP_PYTEST_HOOK=1`.\n\n"
        "Hook source: .claude/hooks/guard-push-pytest.py\n"
    )


def main() -> int:
    if os.environ.get("SKIP_PYTEST_HOOK") == "1":
        return 0

    payload = _read_payload()
    command = _command(payload)
    if not command or not _contains_git_push(command):
        return 0

    if _has_inline_skip(command):
        return 0

    branch = _current_branch()
    if branch != "main":
        return 0

    paths = _changed_paths()
    if paths is None or not _has_trigger_path(paths):
        return 0

    marker = _marker_path(branch)
    fresh = _marker_is_fresh(marker)
    if fresh is None or fresh:
        return 0

    sys.stderr.write(_block_msg(branch, marker))
    return 2


if __name__ == "__main__":
    sys.exit(main())
