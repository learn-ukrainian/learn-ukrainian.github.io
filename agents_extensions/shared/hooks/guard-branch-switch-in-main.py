#!/usr/bin/env python3
"""PreToolUse guard — keep protected primary checkouts on their main branch.

Reads the Claude Code hook payload on stdin (JSON with `tool_name` +
`tool_input.command`) and exits with code 2 if the command would switch
branches or alters the checked-out branch in a protected primary checkout.
Exit 0 in all other cases.

Why Python and not bash? Distinguishing a literal `git checkout -b ...`
INVOCATION from the SAME STRING appearing inside a quoted
`git commit -m "..."` body requires shell-quote-aware tokenization.
The shared pinned Bash AST reader keeps quoted data separate from executed
commands and carries possible working directories through nested scopes.

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

import importlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path


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
    return bool(
        ("gh" in probe and re.search(r"\bpr\s+checkout\b", probe))
        or (
            re.search(r"\b(?:checkout|switch|branch)\b|\bworktree\s+add\b", probe)
            and ("git" in probe or "$" in probe)
        )
        or (
            "gh" in probe
            and re.search(r"\bpr\s+merge\b", probe)
            and re.search(r"(?:^|[\s;])(?:source|\.)\s", probe)
        )
        or re.search(
            r"--pre(?:=|\s)|--config-env|\bmergetool\b|\bgh\s+alias\s", probe
        )
        or re.search(r"(?:^|[\s;{])gh\s+[^;\n]*\$", probe)
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


# Words that, when seen as the FIRST token after `git`, indicate a branch
# switch. Everything else is treated as a different git verb and ignored.
SWITCH_VERBS = frozenset({"checkout", "switch"})

# Branch names that are "safe" to switch to in the main worktree
# (returning to the trunk). `master` kept for older repos; we use main here.
# NEVER list ``--detach`` / ``--orphan`` here — bare ``git checkout --detach``
# leaves target=None and was previously allowed (#4857 recurrence class).
SAFE_TARGETS = frozenset({"main", "master", "HEAD", "-"})

# Full-length or abbreviated object names (SHA-1/SHA-256 hex) that would
# detach HEAD when used as ``git checkout <sha>``.
_HEX_OBJECT_RE = re.compile(r"^(?:[0-9a-f]{7,40}|[0-9a-f]{64})$")


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
            cwd=project_root,
            capture_output=True,
            text=True,
            check=True,
            env=_git_probe_env(),
        ).stdout.strip()
        cd = subprocess.run(
            ["git", "rev-parse", "--git-common-dir"],
            cwd=project_root,
            capture_output=True,
            text=True,
            check=True,
            env=_git_probe_env(),
        ).stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        raise RuntimeError("repository worktree probe unavailable") from None

    if not gd or not cd:
        raise RuntimeError("repository worktree probe returned no state")
    # Normalize to absolute paths so a relative `.git` matches an absolute
    # equivalent. resolve() handles `..` in the path too.
    abs_gd = (project_root / gd).resolve()
    abs_cd = (project_root / cd).resolve()
    return abs_gd == abs_cd


_UNREADABLE_MARKER = UNREADABLE


def _skip_command_prefix(seg, i):
    return i + invoked_start(seg[i:])[0]


def _segments(command: str) -> list[list[str]]:
    try:
        return [row.argv for row in read_commands(command, include_payloads=False)]
    except ShellParseError:
        return [["git", "checkout", UNREADABLE]] if _may_guard(command) else []


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

    if current_branch is None and (force_delete or force_rename):
        return "checked-out branch unknown for force-delete or force-rename"
    if force_delete and current_branch and current_branch in positions:
        return "git branch -D force-deletes the checked-out branch in the main worktree"
    if force_rename and current_branch and (len(positions) == 1 or positions[0] == current_branch):
        return "git branch -M force-renames the checked-out branch in the main worktree"
    return None


def _git_invocation(seg: list[str], effective_cwd: Path | None) -> tuple[str, list[str], Path | None] | None:
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
            if seg[i + 1] == UNREADABLE:
                git_cwd = None
                i += 2
                continue
            directory = Path(seg[i + 1]).expanduser()
            git_cwd = (
                directory.resolve()
                if directory.is_absolute()
                else (git_cwd / directory).resolve()
                if git_cwd is not None
                else None
            )
            i += 2
        elif option.startswith(("--git-dir=", "--work-tree=")):
            git_cwd = None
            i += 1
        elif option.startswith("-C") and len(option) > 2:
            directory = Path(option[2:]).expanduser()
            git_cwd = (
                directory.resolve()
                if directory.is_absolute()
                else (git_cwd / directory).resolve()
                if git_cwd is not None
                else None
            )
            i += 1
        elif option in {"-c", "--git-dir", "--work-tree"} and i + 1 < len(seg):
            # These do not change the cwd. ``--git-dir``/``--work-tree``
            # override repository discovery, so do not infer a protected root
            # from them; the repository becomes unknown for guarded branch operations.
            if option in {"--git-dir", "--work-tree"}:
                git_cwd = None
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
    return Path(root).resolve() if root else None


def _checked_out_branch(repo_root: Path) -> str | None:
    try:
        return (
            subprocess.run(
                ["git", "symbolic-ref", "--quiet", "--short", "HEAD"],
                cwd=repo_root,
                capture_output=True,
                text=True,
                check=True,
                env=_git_probe_env(),
            ).stdout.strip()
            or None
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def _segment_is_dangerous(seg: list[str], current_branch: str | None = "main") -> str | None:
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

    if UNREADABLE in args:
        return "branch-switch target cannot be read"

    # File-level checkout: `git checkout -- <path>`, `git checkout <treeish>
    # -- <path>`, and conflict resolution `checkout --ours/--theirs <path>`.
    if "--" in args or "--ours" in args or "--theirs" in args:
        return None

    # Detach / orphan always forbidden on primary (#4857 recurrence: agents
    # leave the tree on a raw SHA and every service silently reads wrong code).
    if "--detach" in args or any(a == "--orphan" or a.startswith("--orphan=") for a in args):
        return f"git {verb} --detach/--orphan detaches HEAD in the main worktree (primary must stay attached to main)"

    # Flags we treat as "definitely creates / switches to a new branch":
    if any(a.startswith(("-b", "-B")) or a == "--create" or a.startswith("--create=") for a in args):
        return f"git {verb} -b creates and switches to a new branch in the main worktree"
    if any(a.startswith(("-c", "-C")) or a == "--force-create" or a.startswith("--force-create=") for a in args):
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
            # Both --track[=direct|inherit] and -t leave the branch positional intact.
            # ``--detach`` / ``--orphan`` already blocked above.
            if a in {
                "--quiet",
                "-q",
                "--force",
                "-f",
                "--no-track",
                "--track",
                "-t",
                "--guess",
                "--no-guess",
                "--progress",
                "--no-progress",
                "--merge",
                "--theirs",
                "--ours",
                "--ignore-skip-worktree-bits",
                "--patch",
                "-p",
                "--ignore-other-worktrees",
                "--overlay",
                "--no-overlay",
                "--recurse-submodules",
                "--no-recurse-submodules",
            }:
                continue
            # Two-arg flags: skip their value too.
            if a in {"--start-point", "--conflict", "--pathspec-from-file"}:
                skip_next = True
            continue
        target = a
        break

    if target is None:
        # e.g. bare `git checkout` (no-op / path help) — allow
        return None
    if target in SAFE_TARGETS:
        return None
    if _HEX_OBJECT_RE.fullmatch(target.lower()):
        return (
            f"git {verb} {target} detaches HEAD onto a raw object in the main "
            "worktree (use a worktree; primary must stay on main)"
        )
    # origin/main is a remote-tracking ref → detaches when checked out bare
    if target.startswith("origin/") or target.startswith("refs/"):
        return f"git {verb} {target} switches/detaches the main worktree (stay on main; use worktrees for feature refs)"
    return f"git {verb} {target} switches branch in the main worktree"


def _gh_pr_checkout_reason(seg: list[str], effective_cwd: Path | None) -> str | None:
    """Block ``gh pr checkout`` in the protected primary (#4857).

    That command moves the primary HEAD onto a PR branch (often ``pr-N``),
    which is how read-only reviews silently poisoned every local service.
    """
    i = _skip_command_prefix(seg, 0)
    if i >= len(seg) or seg[i] != "gh":
        return None
    # ``gh pr checkout <n>`` (with optional global flags before subcommand)
    rest = seg[i + 1 :]
    # Skip global gh flags that take a value
    j = 0
    while j < len(rest) and rest[j].startswith("-"):
        flag = rest[j]
        if flag in {"-R", "--repo", "-h", "--hostname", "--help"} and j + 1 < len(rest):
            j += 2
        else:
            j += 1
    if j + 1 < len(rest) and rest[j] == "pr" and rest[j + 1] == "checkout":
        if effective_cwd is None:
            return "branch-switch target could not be parsed safely"
        repo_root = _git_repo_root(effective_cwd)
        if repo_root is None:
            return "repository state unknown; repair Git discovery before branch checkout"
        protected_roots = {root.resolve() for root in PROTECTED_ROOTS}
        if repo_root.resolve() not in protected_roots:
            return None
        if not _in_main_worktree(repo_root):
            return None
        return "gh pr checkout moves the primary checkout off main (use a dispatch worktree or gh pr diff instead)"
    return None


def _check_consumer(argv: list[str], source: str, guarded_source: bool) -> None:
    """Use the same data-reader boundary for visible branch operations."""
    merge_guard = importlib.import_module("guard-pr-merge")
    # The consumer policy is operation-neutral except its candidate prefilter
    # and the Git/GH command allowlists.
    utility = Path(argv[0]).name
    if utility == "git":
        invocation = _git_invocation(argv, Path.cwd())
        if UNREADABLE in argv or (invocation is not None and invocation[0] in {"checkout", "switch", "branch"}):
            return
    if utility == "gh" and argv[1:3] == ["pr", "checkout"]:
        return
    merge_guard._check_consumer(argv, source, guarded_source, candidate=_may_guard)


def _command_danger_reason(command: str, session_cwd: Path | None = None) -> str | None:
    """Return a block reason only for a command targeting a protected root."""
    if not _may_guard(command):
        return None
    protected_roots = {root.resolve() for root in PROTECTED_ROOTS}
    try:
        initial_root = (
            _git_repo_root(session_cwd or Path.cwd())
            if re.search(r"\b[A-Za-z_][A-Za-z_0-9]*\s*\(\)\s*\{", command)
            else None
        )
        rows = read_commands(
            command,
            cwd=str(session_cwd or Path.cwd()),
            consumer_check=_check_consumer,
            allow_dynamic_git_arguments=True,
            follow_directory_functions=initial_root is not None and initial_root.resolve() not in protected_roots,
        )
    except Exception as exc:
        if isinstance(exc, ShellParseError) and str(exc) == "dynamic command name" and session_cwd is not None:
            root = _git_repo_root(session_cwd)
            if (
                root is not None
                and root.resolve() not in protected_roots
                and re.fullmatch(
                    r"(?:[A-Za-z_][A-Za-z_0-9]*=[A-Za-z_0-9]+;\s*)?(?:\$[A-Za-z_][A-Za-z_0-9]*|\$\{[A-Za-z_][A-Za-z_0-9]*\}[A-Za-z]*)\s+(?:checkout|switch|branch)\s+[-A-Za-z_0-9 ]+",
                    command,
                )
            ):
                return None
        return f"shell command cannot be read: {str(exc) if isinstance(exc, ShellParseError) else type(exc).__name__}; repair: {REPAIR}"
    for row in rows:
        segment = row.argv
        effective_cwd = None if row.cwd_unreadable else Path(row.cwd)
        gh_reason = _gh_pr_checkout_reason(segment, effective_cwd)
        if gh_reason:
            return gh_reason
        if row.branch_scope_refusal and (_segment_is_dangerous(segment) or _gh_pr_checkout_reason(segment, None)):
            return "branch-switch target could not be parsed safely (conservative case/parameter scope policy); use a literal command"
        if row.repository_unknown and _segment_is_dangerous(segment):
            return "repository environment cannot be read; use default Git repository discovery"
        invocation = _git_invocation(segment, effective_cwd)
        if invocation is None:
            selected = segment[invoked_start(segment)[0] :]
            if selected[:1] == ["git"] and UNREADABLE in selected:
                return "branch operation arguments cannot be read"
            continue
        _, _, git_cwd = invocation
        selected = segment[invoked_start(segment)[0] :]
        dynamic_args = UNREADABLE in segment and (
            invocation[0] in SWITCH_VERBS | {"branch", "worktree"} or selected[1:2] == [UNREADABLE]
        )
        reason = _segment_is_dangerous(segment, None if git_cwd is None else "main")
        if dynamic_args:
            reason = "branch operation arguments cannot be read"
        if git_cwd is None:
            if reason:
                return "branch-switch target cannot be read; use a literal directory and repository"
            continue
        repo_root = _git_repo_root(git_cwd)
        if repo_root is None:
            if reason or invocation[0] in SWITCH_VERBS | {"branch"}:
                return "repository state unknown; repair Git discovery before branch operations"
            continue
        if repo_root.resolve() not in protected_roots or not _in_main_worktree(repo_root):
            continue
        current_branch = _checked_out_branch(repo_root)
        if current_branch is None and invocation[0] == "branch":
            return "checked-out branch unknown; repair Git discovery before branch operations"
        reason = (
            "branch operation arguments cannot be read"
            if dynamic_args
            else _segment_is_dangerous(segment, current_branch)
        )
        if reason:
            return reason
    return None


def main() -> int:
    payload = _CLI_PAYLOAD if __name__ == "__main__" else _read_payload()
    command = _bash_command(payload)
    if not command:
        return 0

    try:
        supplied_cwd = payload.get("cwd")
        reason = _command_danger_reason(command, Path(supplied_cwd) if isinstance(supplied_cwd, str) else None)
    except Exception:
        reason = "nested shell command could not be parsed safely"
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
