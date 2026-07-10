#!/usr/bin/env python3
"""PreToolUse guard — block branch switches / force-deletes in the MAIN worktree.

Reads the Claude Code hook payload on stdin (JSON with `tool_name` +
`tool_input.command`) and exits with code 2 if the command would switch
branches or force-delete/force-rename a branch in the main worktree.
Exit 0 in all other cases.

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
  - git branch -D / -M / -f <name>          (force-delete / force-rename a branch)

Allowed in the MAIN worktree:
  - git checkout main / master / HEAD / HEAD~N
  - git checkout -- <path>                  (file-level discard / restore)
  - git branch -d / -m <name>               (safe delete-if-merged / rename)
  - git branch <name>                       (create; does not switch)
  - git status / git log / git worktree add / ...
  - non-git commands
  - git commit -m "...body mentioning git checkout -b... / git branch -D..."
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


# --- Command segmentation hardened against glued shell operators (#4876). ---
# Pattern lifted from guard-secret-print.py (the reference parser among the
# Bash guards). Hooks are standalone by design, so the helpers are copied,
# not imported. Keep the three copies in guard-branch-switch-in-main.py,
# guard-admin-merge.py, and guard-push-pytest.py in sync.


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
        if j < len(tokens) and tokens[j] == "-":
            strip_tabs = True
            j += 1
        if j < len(tokens):
            delimiter = _strip_quotes(tokens[j])
            if delimiter:
                delimiters.append((delimiter, strip_tabs))
        i = j + 1
    return delimiters


def _strip_heredoc_bodies(command: str) -> str:
    """Drop heredoc BODY lines — document text is data, not commands."""
    if "<<" not in command:
        return command

    kept: list[str] = []
    pending: list[tuple[str, bool]] = []
    for line in command.splitlines():
        if pending:
            delimiter, strip_tabs = pending[0]
            candidate = line.lstrip("\t") if strip_tabs else line
            if candidate == delimiter:
                pending.pop(0)
            continue
        kept.append(line)
        pending.extend(_heredoc_delimiters(line))
    return "\n".join(kept)


def _join_line_continuations(text: str) -> str:
    r"""Fold `\<newline>` into a single logical line, as the shell does.

    Without this, per-line parsing splits `git branch -D x \<newline>--extra`
    into two physical lines; the first fails to tokenize (trailing escape)
    and the dangerous verb rides through. The whole-command tokenizer this
    replaced folded the continuation implicitly — preserve that. Over-folding
    a literal `\` inside a quoted string can only merge argv text, never
    create a false block (the guard matches specific verbs, not free text).
    """
    return text.replace("\\\n", "")


def _segments(command: str) -> list[list[str]]:
    """Tokenize the command, split on shell command separators.

    Returns argv-style segments (one per logical sub-command). Robust to
    the #4876 evasion class: `punctuation_chars` makes shlex emit operator
    runs (`;`, `|`, `&`, `(`, `)`, `<`, `>`) as their OWN tokens even when
    glued to a neighbour (`head -1; git …` no longer hides the `;` inside
    the `-1;` token), each logical line is parsed separately (a newline
    separates commands; `\\`-continuations are folded first), and heredoc
    bodies are stripped first (document text must not be parsed as
    commands). Quoting still collapses `git commit -m "git checkout -b
    foo"` into a single argv element — no false block. Default shlex
    comment handling drops `# …` trailers, matching shell semantics:
    commented-out text can neither trigger nor hide a verb.
    """
    segments: list[list[str]] = []
    for line in _join_line_continuations(_strip_heredoc_bodies(command)).splitlines():
        try:
            lexer = shlex.shlex(line, posix=True, punctuation_chars=True)
            lexer.whitespace_split = True
            tokens = list(lexer)
        except ValueError:
            # Unparseable line (unbalanced quotes) — skip just this line;
            # the shell will fail the malformed command anyway. Other
            # lines in the same command are still inspected.
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


def _branch_force_reason(args: list[str]) -> str | None:
    """Reason string if a `git branch` invocation force-deletes/force-renames.

    Blocks only the irreversible variants in the main worktree:
      - `git branch -D <name>`        (force delete, == --delete --force)
      - `git branch -M <old> <new>`   (force rename/move)
      - `git branch -f <name> <ref>`  / `--force` (force-move a ref)
      - any combined short cluster carrying D/M/f (e.g. `-Df`)

    Intentionally ALLOWED (non-destructive): `-d` (delete-if-merged),
    `-m` (rename), plain `git branch` (list), `git branch <name>` (create).
    Uppercase D/M and lowercase `f` are the force indicators; their
    lowercase counterparts `d`/`m` are the safe ops, so a simple
    character-membership test discriminates correctly.
    """
    for a in args:
        if a == "--force":
            return "git branch --force rewrites/force-deletes a branch ref in the main worktree"
        # Single-dash short flag cluster (e.g. -D, -M, -f, -Df). Long flags
        # (`--`) other than --force are not force ops and fall through.
        if len(a) >= 2 and a[0] == "-" and a[1] != "-" and any(c in a[1:] for c in ("D", "M", "f")):
            return f"git branch {a} force-deletes/force-renames a branch in the main worktree"
    return None


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
    args = seg[i + 1:]

    # `git branch -D/-M/-f` force-deletes or force-renames a branch ref —
    # destructive and irreversible in the MAIN worktree. Safe variants
    # (`-d` delete-if-merged, `-m` rename, plain list/create) are allowed.
    if verb == "branch":
        return _branch_force_reason(args)

    if verb not in SWITCH_VERBS:
        return None

    # Now we're on `git ... <checkout|switch> <args...>`. Decide if this
    # would switch the branch state of the current worktree.

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
