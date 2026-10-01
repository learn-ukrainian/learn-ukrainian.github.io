"""Read-only git calls in the Monitor API, reporter and sweeps take no optional locks (#8874).

``git status`` (and other read-only commands that refresh the index) take
``.git/index.lock`` as an optional side effect. A reporter killed mid-call
leaves that lock behind, and every later writer in the same checkout fails
with "Unable to create .../index.lock: File exists". Read-only callers pass
``--no-optional-locks`` (``git(1)``) so they never take it.

The gate parses every ``["git", <subcommand>, ...]`` argv literal in the
scanned files. The global options before the subcommand must include
``--no-optional-locks`` unless the subcommand is in the closed
``_WRITE_VERBS`` allowlist below. A subcommand that is not a literal
(``["git", *args]`` in a helper) counts as read-only, so a shared helper must
carry the flag itself. The flag is harmless on a command that does write, so
``_READ_VERBS`` errs towards requiring it; a literal that names neither set
(``("git", "runtime")`` as a section list) is not a git invocation.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.repo_wide

_REPO_ROOT = Path(__file__).resolve().parents[1]
_FLAG = "--no-optional-locks"

# Monitor API, the project-state reporter and the reconcile sweep.
_PYTHON_ROOTS = (_REPO_ROOT / "scripts" / "api",)
_PYTHON_FILES = (
    _REPO_ROOT / "scripts" / "orchestration" / "reconcile_sweep.py",
    _REPO_ROOT / "scripts" / "orchestration" / "worktree_prep.py",
)
_SHELL_FILES = (_REPO_ROOT / "scripts" / "orchestration" / "run_project_state_reporter.sh",)

# Closed allowlist: subcommands that write repository state and so must be
# free to take the locks they need. Anything else needs the flag.
_WRITE_VERBS = frozenset(
    {
        "add",
        "am",
        "apply",
        "checkout",
        "cherry-pick",
        "clean",
        "clone",
        "commit",
        "fetch",
        "gc",
        "init",
        "merge",
        "mv",
        "pull",
        "push",
        "rebase",
        "reset",
        "restore",
        "revert",
        "rm",
        "sparse-checkout",
        "stash",
        "switch",
        "update-index",
        "update-ref",
    }
)
_READ_VERBS = frozenset(
    {
        "archive",
        "blame",
        "branch",
        "cat-file",
        "check-ignore",
        "cherry",
        "config",
        "count-objects",
        "describe",
        "diff",
        "diff-files",
        "diff-index",
        "diff-tree",
        "for-each-ref",
        "grep",
        "log",
        "ls-files",
        "ls-remote",
        "ls-tree",
        "merge-base",
        "name-rev",
        "reflog",
        "remote",
        "rev-list",
        "rev-parse",
        "shortlog",
        "show",
        "show-ref",
        "status",
        "symbolic-ref",
        "tag",
        "worktree",
    }
)
_WORKTREE_WRITE_ACTIONS = frozenset({"add", "lock", "move", "prune", "remove", "repair", "unlock"})
# Global options whose value is the next argv element.
_GLOBAL_OPTIONS_WITH_VALUE = frozenset({"-C", "-c", "--git-dir", "--work-tree", "--namespace"})


def _literal_text(node: ast.expr) -> str | None:
    """Return a string constant, or the leading literal text of an f-string."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.JoinedStr) and node.values:
        head = node.values[0]
        if isinstance(head, ast.Constant) and isinstance(head.value, str):
            return head.value
    return None


def _missing_flag(elements: list[ast.expr]) -> str | None:
    """Return the subcommand label when this git argv lacks the flag, else None."""
    globals_seen: list[str] = []
    index = 1
    while index < len(elements):
        text = _literal_text(elements[index])
        if text is None or not text.startswith("-"):
            break
        globals_seen.append(text)
        index += 2 if text in _GLOBAL_OPTIONS_WITH_VALUE else 1
    if index >= len(elements):
        return None
    verb = _literal_text(elements[index])
    dynamic = verb is None or isinstance(elements[index], ast.JoinedStr)
    if not dynamic and verb not in _READ_VERBS | _WRITE_VERBS:
        return None
    if _FLAG in globals_seen:
        return None
    if dynamic:
        return "<dynamic>"
    if verb in _WRITE_VERBS:
        return None
    if verb == "worktree" and index + 1 < len(elements):
        action = _literal_text(elements[index + 1])
        if action in _WORKTREE_WRITE_ACTIONS:
            return None
        return f"worktree {action or '<dynamic>'}"
    return verb


def git_calls_without_flag(source: str) -> list[tuple[int, str]]:
    """Return (lineno, subcommand) for each read-only git argv literal missing the flag."""
    offenders: list[tuple[int, str]] = []
    for node in ast.walk(ast.parse(source)):
        if not isinstance(node, (ast.List, ast.Tuple)) or not node.elts:
            continue
        first = node.elts[0]
        if not (isinstance(first, ast.Constant) and first.value == "git"):
            continue
        verb = _missing_flag(list(node.elts))
        if verb is not None:
            offenders.append((node.lineno, verb))
    return sorted(offenders)


_SHELL_GIT = re.compile(r"(?:^|[\s;&|(`$])git((?:\s+-[Cc]\s+\S+|\s+-\S+)*)\s+([a-z][a-z-]*)")


def shell_git_calls_without_flag(source: str) -> list[tuple[int, str]]:
    offenders: list[tuple[int, str]] = []
    for lineno, line in enumerate(source.splitlines(), start=1):
        code = line.split("#", 1)[0]
        for match in _SHELL_GIT.finditer(code):
            options, verb = match.group(1).split(), match.group(2)
            if _FLAG not in options and verb not in _WRITE_VERBS:
                offenders.append((lineno, verb))
    return offenders


def _scanned_python_files() -> list[Path]:
    files = {path for root in _PYTHON_ROOTS for path in root.rglob("*.py")}
    files.update(_PYTHON_FILES)
    return sorted(files)


def test_verb_sets_are_disjoint_and_cover_the_read_only_commands() -> None:
    assert not _READ_VERBS & _WRITE_VERBS
    assert {"status", "diff", "log", "rev-parse", "ls-files", "for-each-ref", "worktree"} <= _READ_VERBS


def test_scanned_files_exist() -> None:
    for path in (*_PYTHON_FILES, *_SHELL_FILES):
        assert path.is_file(), f"scanned file moved: {path.relative_to(_REPO_ROOT)}"
    assert len(_scanned_python_files()) > len(_PYTHON_FILES)


def test_read_only_git_calls_pass_no_optional_locks() -> None:
    offenders: list[str] = []
    for path in _scanned_python_files():
        for lineno, verb in git_calls_without_flag(path.read_text(encoding="utf-8")):
            offenders.append(f"{path.relative_to(_REPO_ROOT)}:{lineno} git {verb}")
    for path in _SHELL_FILES:
        for lineno, verb in shell_git_calls_without_flag(path.read_text(encoding="utf-8")):
            offenders.append(f"{path.relative_to(_REPO_ROOT)}:{lineno} git {verb}")
    assert not offenders, f"read-only git calls missing {_FLAG}:\n" + "\n".join(offenders)


def test_reporter_disables_optional_locks_for_every_child() -> None:
    source = _SHELL_FILES[0].read_text(encoding="utf-8")
    assert re.search(r"(?m)^export GIT_OPTIONAL_LOCKS=0$", source)


@pytest.mark.parametrize(
    "snippet",
    [
        '["git", "status", "--porcelain"]',
        '["git", "-C", repo, "diff", "HEAD"]',
        '("git", "log", "-1")',
        '["git", "rev-parse", "HEAD"]',
        '["git", "ls-files", "-z"]',
        '["git", "for-each-ref", "refs/heads"]',
        '["git", "worktree", "list", "--porcelain"]',
        '["git", *args]',
        '["git", f"--git-dir={d}", f"--work-tree={w}", *args]',
        '["git", "-c", "core.quotepath=off", "status"]',
    ],
)
def test_lint_flags_read_only_calls_without_flag(snippet: str) -> None:
    assert len(git_calls_without_flag(f"cmd = {snippet}\n")) == 1


@pytest.mark.parametrize(
    "snippet",
    [
        '["git", "--no-optional-locks", "status", "--porcelain"]',
        '["git", "-C", repo, "--no-optional-locks", "diff", "HEAD"]',
        '["git", "--no-optional-locks", *args]',
        '["git", "--no-optional-locks", f"--git-dir={d}", f"--work-tree={w}", *args]',
        '["git", "worktree", "add", path]',
        '["git", "push", "-u", "origin", branch]',
        '["git", "fetch", "origin"]',
        '["python", "status"]',
        '["git"]',
        '("git", "runtime", "delegate")',
    ],
)
def test_lint_accepts_flagged_and_write_calls(snippet: str) -> None:
    assert git_calls_without_flag(f"cmd = {snippet}\n") == []


def test_shell_lint_flags_read_only_calls_without_flag() -> None:
    source = 'git status --porcelain\ngit --no-optional-locks diff\nhead="$(git -C "$R" rev-parse HEAD)"\ngit push\n'
    assert shell_git_calls_without_flag(source) == [(1, "status"), (3, "rev-parse")]
