#!/usr/bin/env python3
"""PreToolUse guard — block branch switches in the MAIN worktree.

Reads the Claude Code hook payload on stdin (JSON with `tool_name` +
`tool_input.command`) and exits with code 2 if the command would switch
branches in the main worktree. Exit 0 in all other cases.

Why Python and not bash? Distinguishing a literal `git checkout -b ...`
INVOCATION from the SAME STRING appearing inside a quoted
`git commit -m "..."` body requires shell-quote-aware tokenization.
`shlex.split` handles single quotes, double quotes, escapes, and
heredoc-like patterns (best effort) correctly; bash + grep does not.

The hook is a no-op inside an added worktree (the worktree IS the
right place to switch branches). Detection: `git rev-parse --git-dir`
returns `.git/worktrees/<name>` inside added worktrees and matches
`--git-common-dir` only in the main worktree.

Blocked in the MAIN worktree:
  - git checkout -b <name>
  - git switch -c <name>
  - git switch <non-main-branch>
  - git checkout <non-main-branch>          (when target is a branch, not a path)

Allowed in the MAIN worktree:
  - git checkout main / master / HEAD / HEAD~N
  - git checkout -- <path>                  (file-level discard / restore)
  - git status / git log / git worktree add / ...
  - non-git commands
  - git commit -m "...body mentioning git checkout -b..."
"""
from __future__ import annotations

import json
import shlex
import subprocess
import sys
from pathlib import Path

# Words that, when seen as the FIRST token after `git`, indicate a branch
# switch. Everything else is treated as a different git verb and ignored.
SWITCH_VERBS = frozenset({"checkout", "switch"})

# Branch names that are "safe" to switch to in the main worktree
# (returning to the trunk). `master` kept for older repos; we use main here.
SAFE_TARGETS = frozenset({"main", "master", "HEAD", "-", "--detach", "--orphan"})


def _read_payload() -> dict:
    try:
        return json.loads(sys.stdin.read() or "{}")
    except json.JSONDecodeError:
        return {}


def _bash_command(payload: dict) -> str:
    return ((payload.get("tool_input") or {}).get("command") or "").strip()


def _in_main_worktree(project_root: Path) -> bool:
    """True iff `project_root` is the MAIN worktree of its repo.

    `git rev-parse --git-dir` returns the repo's effective .git dir:
      - In the main worktree: the actual `.git` directory.
      - In an added worktree: `<main-git-dir>/worktrees/<name>`.
    `--git-common-dir` always returns the main `.git` regardless of which
    worktree we're in. So they match iff we're in the main worktree.
    """
    try:
        gd = subprocess.run(
            ["git", "rev-parse", "--git-dir"],
            cwd=project_root, capture_output=True, text=True, check=True,
        ).stdout.strip()
        cd = subprocess.run(
            ["git", "rev-parse", "--git-common-dir"],
            cwd=project_root, capture_output=True, text=True, check=True,
        ).stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        # Not a git repo or git missing → nothing to enforce.
        return False

    # Normalize to absolute paths so a relative `.git` matches an absolute
    # equivalent. resolve() handles `..` in the path too.
    abs_gd = (project_root / gd).resolve()
    abs_cd = (project_root / cd).resolve()
    return abs_gd == abs_cd


def _segments(command: str) -> list[list[str]]:
    """Tokenize the command line, split on shell command separators.

    Returns a list of argv-style segments. Each segment is the token list
    for one logical sub-command (everything between `&&`, `||`, `;`, `|`).
    `shlex.split` respects single/double quotes, so a `git commit -m
    "git checkout -b foo"` collapses to a single segment whose tokens
    are `['git', 'commit', '-m', 'git checkout -b foo']` — the dangerous
    substring is INSIDE a single argv element, not a separate command.
    """
    try:
        tokens = shlex.split(command, posix=True)
    except ValueError:
        # Unbalanced quotes — fall back to a degenerate split. We err on
        # the safe side: if we can't parse, allow (the user will see the
        # malformed command fail anyway).
        return []
    segments: list[list[str]] = []
    current: list[str] = []
    for tok in tokens:
        if tok in ("&&", "||", ";", "|"):
            if current:
                segments.append(current)
                current = []
        else:
            current.append(tok)
    if current:
        segments.append(current)
    return segments


def _segment_is_dangerous(seg: list[str]) -> str | None:
    """Return a human-readable reason string if seg is a dangerous git op,
    else None."""
    # Find `git` token; allow common leading wrappers (`sudo`, `time`, `env`).
    i = 0
    while i < len(seg) and seg[i] in {"sudo", "time", "env", "nohup"}:
        i += 1
    if i >= len(seg) or seg[i] != "git":
        return None
    # Skip over `git -C <dir>` / `git -c k=v` flag pairs and other top-level
    # git flags so we land on the verb.
    i += 1
    while i < len(seg) and seg[i].startswith("-"):
        # Verbs never start with `-`, so any `-x` here is a top-level git
        # flag. Some take a value (`-C dir`, `-c key=val`); consume one
        # extra token defensively when it doesn't look like a verb.
        if seg[i] in {"-C", "-c", "--git-dir", "--work-tree"} and i + 1 < len(seg):
            i += 2
        else:
            i += 1
    if i >= len(seg):
        return None
    verb = seg[i]
    if verb not in SWITCH_VERBS:
        return None

    # Now we're on `git ... <checkout|switch> <args...>`. Decide if this
    # would switch the branch state of the current worktree.
    args = seg[i + 1:]

    # File-level checkout: `git checkout -- <path>` or `git checkout
    # <treeish> -- <path>`. The presence of `--` means path-restoration,
    # not branch switch.
    if "--" in args:
        return None

    # Flags we treat as "definitely creates / switches to a new branch":
    if "-b" in args or "--create" in args:
        return f"git {verb} -b creates and switches to a new branch in the main worktree"
    if "-c" in args or "-C" in args:
        # `-C` is `git switch --force-create`; equally a branch creation.
        return f"git {verb} -c creates and switches to a new branch in the main worktree"

    # Bare `git checkout <target>` / `git switch <target>`. Block when
    # target is not a safe one. Find the first non-flag positional.
    target: str | None = None
    skip_next = False
    for a in args:
        if skip_next:
            skip_next = False
            continue
        if a.startswith("-"):
            # Switches like `--track`, `--detach` take no value; `-t` takes
            # one (the upstream). Defensive: treat single-letter flags
            # other than the known boolean ones as value-taking.
            if a in {"--detach", "--quiet", "-q", "--force", "-f", "--orphan",
                     "--no-track", "--guess", "--no-guess", "--progress",
                     "--no-progress", "--merge", "--theirs", "--ours",
                     "--ignore-skip-worktree-bits", "--patch", "-p",
                     "--ignore-other-worktrees", "--overlay", "--no-overlay",
                     "--recurse-submodules", "--no-recurse-submodules"}:
                continue
            # Two-arg flags: skip their value too.
            if a in {"-t", "--track", "-B", "--start-point",
                     "--conflict", "--pathspec-from-file"}:
                skip_next = True
            continue
        target = a
        break

    if target is None or target in SAFE_TARGETS:
        return None
    return f"git {verb} {target} switches branch in the main worktree"


def main() -> int:
    payload = _read_payload()
    command = _bash_command(payload)
    if not command:
        return 0

    # If we can't determine project root, fall through to allowing the
    # command — the hook is meant to be a safety net, not a chokepoint.
    project_root = Path(__file__).resolve().parents[2]
    if not (project_root / ".git").exists() and not (project_root / ".git").is_dir():
        # `.git` may also be a file in worktrees. We check the containing
        # repo regardless. If git isn't there at all, no-op.
        return 0

    if not _in_main_worktree(project_root):
        return 0

    for segment in _segments(command):
        reason = _segment_is_dangerous(segment)
        if reason:
            sys.stderr.write(
                f"BLOCKED by guard-branch-switch-in-main: {reason}.\n\n"
                f"The MAIN worktree ({project_root}) must stay on `main`. "
                "All feature work happens in added worktrees so the main\n"
                "tree is always reviewable.\n\n"
                "Use this pattern instead (from the main project dir):\n\n"
                "  git worktree add .worktrees/<purpose>/<branch-name> "
                "-b <branch-name>\n"
                "  cd .worktrees/<purpose>/<branch-name>\n"
                "  # ...edits, commits, push, PR...\n"
                "  # back in the main project dir:\n"
                "  git worktree remove .worktrees/<purpose>/<branch-name>\n\n"
                "Hook source: .claude/hooks/guard-branch-switch-in-main.py\n"
            )
            return 2

    return 0


if __name__ == "__main__":
    sys.exit(main())
