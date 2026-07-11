#!/usr/bin/env python3
"""PreToolUse guard — keep protected primary checkouts on their main branch.

Reads the Claude Code hook payload on stdin (JSON with `tool_name` +
`tool_input.command`) and exits with code 2 if the command would switch
branches or alters the checked-out branch in a protected primary checkout.
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

Blocked in a protected PRIMARY checkout:
  - git checkout -b <name>
  - git switch -c <name>
  - git switch <non-main-branch>
  - git checkout <non-main-branch>          (when target is a branch, not a path)
  - git branch -D / -M <current-branch>     (force-delete / force-rename HEAD)
  - git branch -f <name>                    (force-move a branch ref)

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
import os
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


def _git_probe_env() -> dict[str, str]:
    """Return an environment that lets git discover the requested repo."""
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
    return env


def _public_primary_root() -> Path:
    """Find this source tree's primary checkout, even when run from a worktree."""
    source_root = Path(__file__).resolve().parents[2]
    try:
        common_dir = subprocess.run(
            ["git", "rev-parse", "--path-format=absolute", "--git-common-dir"],
            cwd=source_root,
            capture_output=True,
            text=True,
            check=True,
            env=_git_probe_env(),
        ).stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return source_root
    return Path(common_dir).resolve().parent


# This deployed public hook is also the only branch guard for the private
# infrastructure checkout. Resolve both roots so symlinked invocations compare
# the actual checkout directories, not their textual spellings.
PROTECTED_ROOTS = [
    _public_primary_root(),
    Path("~/projects/learn-ukrainian-infra-private").expanduser().resolve(),
]


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
            cwd=project_root, capture_output=True, text=True, check=True, env=_git_probe_env(),
        ).stdout.strip()
        cd = subprocess.run(
            ["git", "rev-parse", "--git-common-dir"],
            cwd=project_root, capture_output=True, text=True, check=True, env=_git_probe_env(),
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
    """Return (delimiter, strip_tabs) for each heredoc opener on `line`.

    Handles all four operator/marker forms (#4877): spaced ``<< EOF`` /
    ``<< - EOF`` and attached ``<<-EOF`` / ``<<-'EOF'`` — the attached ``-``
    means ``<<-`` (strip leading tabs on the closer), NOT part of the
    delimiter word. Getting this wrong left a real heredoc effectively
    unclosed, which (with the old strip) silently dropped everything after
    the opener.
    """
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

    Fail-CLOSED on an unclosed heredoc (#4877): if a delimiter never appears
    before EOF, the buffered lines were NOT a real heredoc body — a crafted
    or malformed opener (never-closing marker, mis-parsed ``<<-``) must not
    make trailing REAL commands/writes vanish from the parsed view. Those
    lines are kept and inspected; only a heredoc that actually closes has
    its body + closer dropped.
    """
    if "<<" not in command:
        return command

    lines = command.splitlines()
    kept: list[str] = []
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        kept.append(line)
        i += 1
        pending = _heredoc_delimiters(line)
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
            # Unclosed at EOF → not a real body; keep the lines (fail-closed).
            kept.extend(lines[body_start:i])
        # else: closed — body and closer consumed and dropped.
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


def _segments_with_following_operator(command: str) -> list[tuple[list[str], str | None]]:
    """Tokenize commands and retain the separator after each segment.

    The existing ``_segments`` helper deliberately exposes only argv lists for
    its focused parser tests. Target resolution additionally needs to know
    when ``cd <path> &&`` changes the effective cwd of the following command.
    """
    segments: list[tuple[list[str], str | None]] = []
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
                    segments.append((current, tok))
                    current = []
            else:
                current.append(tok)
        if current:
            segments.append((current, None))
    return segments


def _branch_force_reason(args: list[str], current_branch: str | None) -> str | None:
    """Reason string if a `git branch` invocation force-deletes/force-renames.

    Blocks only force operations which affect the currently checked-out branch:
      - `git branch -D <current>`     (force delete, == --delete --force)
      - `git branch -M <current> <new>` / `git branch -M <new>`
      - `git branch -f <name> <ref>`  / `--force` (force-move a ref)
      - any combined short cluster carrying D/M/f (e.g. `-Df`)

    Intentionally ALLOWED (non-destructive): `-d` (delete-if-merged),
    `-m` (rename), plain `git branch` (list), `git branch <name>` (create).
    Uppercase D/M and lowercase `f` are the force indicators; their
    lowercase counterparts `d`/`m` are the safe ops, so a simple
    character-membership test discriminates correctly.
    """
    force_delete = False
    force_rename = False
    positions: list[str] = []
    for a in args:
        if a == "--force":
            return "git branch --force rewrites/force-deletes a branch ref in the main worktree"
        # Single-dash short flag cluster (e.g. -D, -M, -f, -Df). Long flags
        # (`--`) other than --force are not force ops and fall through.
        if len(a) >= 2 and a[0] == "-" and a[1] != "-":
            flags = a[1:]
            if "f" in flags:
                return f"git branch {a} force-moves a branch ref in the main worktree"
            force_delete = force_delete or "D" in flags
            force_rename = force_rename or "M" in flags
        elif not a.startswith("-"):
            positions.append(a)

    if force_delete and current_branch and current_branch in positions:
        return "git branch -D force-deletes the checked-out branch in the main worktree"
    if force_rename and current_branch and (
        len(positions) == 1 or positions[0] == current_branch
    ):
        return "git branch -M force-renames the checked-out branch in the main worktree"
    return None


def _is_env_assignment(tok: str) -> bool:
    """`VAR=val` prefix (as before `env` or a bare command). Mirrors the
    reference idiom in guard-primary-checkout-write._command_word."""
    return "=" in tok and not tok.startswith("-") and tok.split("=", 1)[0].isidentifier()


def _skip_command_prefix(seg: list[str], i: int) -> int:
    """Advance past transparent leading tokens so we land on the real command
    word: wrappers (`sudo`/`time`/`env`/`nohup`/`command`/`exec`), env
    assignments (`FOO=1`), and a brace-group opener (`{`). Without this a
    `env FOO=1 git branch -D x` or `{ git branch -D x; }` hid the verb (#4877)."""
    while i < len(seg):
        tok = seg[i]
        if tok in {"sudo", "time", "env", "nohup", "command", "exec", "{"} or _is_env_assignment(
            tok
        ):
            i += 1
        else:
            break
    return i


def _git_invocation(
    seg: list[str], effective_cwd: Path
) -> tuple[str, list[str], Path] | None:
    """Return ``(verb, args, git_cwd)`` for a direct git invocation.

    Git applies repeated ``-C`` options from left to right, including relative
    paths. Mirroring that behaviour prevents a command aimed at another repo
    from being evaluated against the hook session's checkout.
    """
    i = _skip_command_prefix(seg, 0)
    if i >= len(seg) or seg[i] != "git":
        return None
    i += 1
    git_cwd = effective_cwd
    while i < len(seg) and seg[i].startswith("-"):
        option = seg[i]
        if option == "-C" and i + 1 < len(seg):
            directory = Path(seg[i + 1]).expanduser()
            git_cwd = (directory if directory.is_absolute() else git_cwd / directory).resolve()
            i += 2
        elif option.startswith("-C") and len(option) > 2:
            directory = Path(option[2:]).expanduser()
            git_cwd = (directory if directory.is_absolute() else git_cwd / directory).resolve()
            i += 1
        elif option in {"-c", "--git-dir", "--work-tree"} and i + 1 < len(seg):
            # These do not change the cwd. ``--git-dir``/``--work-tree``
            # override repository discovery, so do not infer a protected root
            # from them; the guard remains deliberately non-blocking there.
            if option in {"--git-dir", "--work-tree"}:
                return None
            i += 2
        else:
            i += 1
    if i >= len(seg):
        return None
    return seg[i], seg[i + 1 :], git_cwd


def _git_repo_root(git_cwd: Path) -> Path | None:
    """Resolve the root of the repo a git invocation actually targets."""
    try:
        root = subprocess.run(
            ["git", "rev-parse", "--path-format=absolute", "--show-toplevel"],
            cwd=git_cwd,
            capture_output=True,
            text=True,
            check=True,
            env=_git_probe_env(),
        ).stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    return Path(root).resolve()


def _checked_out_branch(repo_root: Path) -> str | None:
    try:
        return subprocess.run(
            ["git", "symbolic-ref", "--quiet", "--short", "HEAD"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=True,
            env=_git_probe_env(),
        ).stdout.strip() or None
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def _cd_target(seg: list[str], effective_cwd: Path) -> Path | None:
    """Return the directory from a simple leading ``cd`` command, if any."""
    i = _skip_command_prefix(seg, 0)
    if i >= len(seg) or seg[i] != "cd":
        return None
    args = seg[i + 1 :]
    if args[:1] == ["--"]:
        args = args[1:]
    if len(args) != 1 or args[0] == "-":
        return None
    directory = Path(args[0]).expanduser()
    return (directory if directory.is_absolute() else effective_cwd / directory).resolve()


def _segment_is_dangerous(
    seg: list[str], current_branch: str | None = "main"
) -> str | None:
    """Return a human-readable reason string if seg is a dangerous git op,
    else None."""
    invocation = _git_invocation(seg, Path.cwd())
    if invocation is None:
        return None
    verb, args, _ = invocation

    # `git branch -D/-M/-f` force-deletes or force-renames a branch ref —
    # destructive and irreversible in the MAIN worktree. Safe variants
    # (`-d` delete-if-merged, `-m` rename, plain list/create) are allowed.
    if verb == "branch":
        return _branch_force_reason(args, current_branch)

    if verb not in SWITCH_VERBS:
        return None

    # Now we're on `git ... <checkout|switch> <args...>`. Decide if this
    # would switch the branch state of the current worktree.

    # File-level checkout: `git checkout -- <path>`, `git checkout <treeish>
    # -- <path>`, and conflict resolution `checkout --ours/--theirs <path>`.
    if "--" in args or "--ours" in args or "--theirs" in args:
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


def _command_danger_reason(command: str, session_cwd: Path | None = None) -> str | None:
    """Return a block reason only for a command targeting a protected root."""
    effective_cwd = (session_cwd or Path.cwd()).resolve()
    protected_roots = {root.resolve() for root in PROTECTED_ROOTS}
    for segment, following_operator in _segments_with_following_operator(command):
        cd_target = _cd_target(segment, effective_cwd)
        if cd_target is not None and following_operator == "&&":
            effective_cwd = cd_target
            continue

        invocation = _git_invocation(segment, effective_cwd)
        if invocation is None:
            continue
        _, _, git_cwd = invocation
        repo_root = _git_repo_root(git_cwd)
        if repo_root is None or repo_root not in protected_roots:
            continue
        # A target under */.worktrees/* may share this repo's common git dir,
        # but it is deliberately an added worktree where branch operations are
        # allowed. Ask git rather than relying only on the path spelling.
        if not _in_main_worktree(repo_root):
            continue
        reason = _segment_is_dangerous(segment, _checked_out_branch(repo_root))
        if reason:
            return reason
    return None


def main() -> int:
    payload = _read_payload()
    command = _bash_command(payload)
    if not command:
        return 0

    reason = _command_danger_reason(command)
    if reason:
            sys.stderr.write(
                f"BLOCKED by guard-branch-switch-in-main: {reason}.\n\n"
                "A protected PRIMARY worktree must stay on `main`. "
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
