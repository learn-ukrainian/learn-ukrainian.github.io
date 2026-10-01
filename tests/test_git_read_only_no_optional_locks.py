"""Read-only git calls in the Monitor API, reporter and sweeps take no optional locks (#8874).

``git status`` (and other read-only commands that refresh the index) take
``.git/index.lock`` as an optional side effect. A reporter killed mid-call
leaves that lock behind, and every later writer in the same checkout fails
with "Unable to create .../index.lock: File exists". Read-only callers pass
``--no-optional-locks`` (``git(1)``) so they never take it.

The gate parses every ``["git", <subcommand>, ...]`` argv literal in the
scanned files, every shell command string handed to a shell (``shell=True``,
``os.system``; f-strings included) and every shell-file line. Each subcommand
must be in one of two closed sets: a ``_READ_VERBS`` call needs
``--no-optional-locks`` among the global options before it, or
``GIT_OPTIONAL_LOCKS=0`` in the call's literal ``env=`` (an env prefix in a
shell string); a ``_WRITE_VERBS`` call is free to take the locks it needs.
Any other subcommand fails closed and must be added to one of the sets. A
subcommand that is not a literal (``["git", *args]`` in a helper) counts as
read-only, so a shared helper must carry the flag itself. The flag is
harmless on a command that does write, so ``_READ_VERBS`` errs towards
requiring it.
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
        "check-attr",
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


_LOCKS_ENV = "GIT_OPTIONAL_LOCKS"
# Names bound to a data tuple that merely starts with "git" (orient section
# names), so it is not an argv. Every other "git"-led literal is checked.
_NOT_GIT_ARGV = frozenset({"LEAN_ORIENT_SECTIONS"})
_SHELL_CALLS = frozenset({"system", "popen", "getoutput", "getstatusoutput"})


def _git_verdict(tokens: list[str | None], *, env_disables_locks: bool = False) -> str | None:
    """Return the offending subcommand of a ``git`` argv, or None when it passes.

    ``tokens[0]`` is ``git``; a ``None`` token is not a literal.
    """
    globals_seen: list[str] = []
    index = 1
    while index < len(tokens):
        text = tokens[index]
        if text is None or not text.startswith("-"):
            break
        globals_seen.append(text)
        index += 2 if text in _GLOBAL_OPTIONS_WITH_VALUE else 1
    if index >= len(tokens):
        return None
    covered = _FLAG in globals_seen or env_disables_locks
    verb = tokens[index]
    if verb is None:
        return None if covered else "<dynamic>"
    if verb in _WRITE_VERBS:
        return None
    if verb == "worktree":
        action = tokens[index + 1] if index + 1 < len(tokens) else None
        if action in _WORKTREE_WRITE_ACTIONS or covered:
            return None
        return f"worktree {action or '<dynamic>'}"
    if verb in _READ_VERBS:
        return None if covered else verb
    return f"{verb} (unknown subcommand)"


def _argv_token(node: ast.expr) -> str | None:
    """A string constant, or the leading literal of an f-string option such as ``f"--git-dir={d}"``."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.JoinedStr) and node.values:
        head = node.values[0]
        if isinstance(head, ast.Constant) and isinstance(head.value, str) and head.value.startswith("-"):
            return head.value
    return None


def _shell_text(node: ast.expr) -> str | None:
    """A string constant, or an f-string with each placeholder rendered as a NUL byte."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.JoinedStr):
        return "".join(
            part.value if isinstance(part, ast.Constant) and isinstance(part.value, str) else "\0"
            for part in node.values
        )
    return None


def _is_git_argv(node: ast.expr) -> bool:
    if not isinstance(node, (ast.List, ast.Tuple)) or not node.elts:
        return False
    first = node.elts[0]
    return isinstance(first, ast.Constant) and first.value == "git"


def _env_disables_locks(call: ast.Call) -> bool:
    """True when the call's ``env=`` is a literal mapping that sets ``GIT_OPTIONAL_LOCKS=0``."""
    for keyword in call.keywords:
        if keyword.arg != "env":
            continue
        value = keyword.value
        if isinstance(value, ast.Dict):
            pairs = zip(value.keys, value.values, strict=True)
            return any(
                isinstance(key, ast.Constant)
                and key.value == _LOCKS_ENV
                and isinstance(item, ast.Constant)
                and item.value == "0"
                for key, item in pairs
            )
        if isinstance(value, ast.Call) and isinstance(value.func, ast.Name) and value.func.id == "dict":
            return any(
                item.arg == _LOCKS_ENV and isinstance(item.value, ast.Constant) and item.value.value == "0"
                for item in value.keywords
            )
    return False


def _runs_in_shell(call: ast.Call) -> bool:
    func = call.func
    name = func.attr if isinstance(func, ast.Attribute) else func.id if isinstance(func, ast.Name) else None
    if name in _SHELL_CALLS:
        return True
    return any(
        keyword.arg == "shell" and isinstance(keyword.value, ast.Constant) and keyword.value.value is True
        for keyword in call.keywords
    )


def git_calls_without_flag(source: str) -> list[tuple[int, str]]:
    """Return (lineno, subcommand) for each git argv or shell string that fails the gate."""
    offenders: list[tuple[int, str]] = []
    tree = ast.parse(source)
    seen: set[int] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not node.args:
            continue
        command = node.args[0]
        env_off = _env_disables_locks(node)
        if _is_git_argv(command):
            seen.add(id(command))
            verdict = _git_verdict([_argv_token(element) for element in command.elts], env_disables_locks=env_off)
            if verdict is not None:
                offenders.append((command.lineno, verdict))
        elif _runs_in_shell(node) and (text := _shell_text(command)) is not None:
            for _lineno, verdict in _shell_line_offenders(text, env_disables_locks=env_off):
                offenders.append((command.lineno, verdict))
    for node in ast.walk(tree):
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            if node.value is not None and any(isinstance(t, ast.Name) and t.id in _NOT_GIT_ARGV for t in targets):
                seen.add(id(node.value))
    for node in ast.walk(tree):
        if _is_git_argv(node) and id(node) not in seen:
            verdict = _git_verdict([_argv_token(element) for element in node.elts])
            if verdict is not None:
                offenders.append((node.lineno, verdict))
    return sorted(offenders)


# A ``git`` at command position, with any ``NAME=value`` env prefix, its global
# options and the next two words (the subcommand and a worktree action).
_SHELL_GIT = re.compile(
    r"(?:^|[\s;&|(`$])"
    r"(?P<env>(?:[A-Za-z_][A-Za-z0-9_]*=\S*\s+)*)"
    r"git"
    r"(?P<options>(?:\s+(?:-[Cc]|--git-dir|--work-tree|--namespace)\s+\S+|\s+-\S+)*)"
    r"\s+(?P<verb>[^\s;&|)`]+)"
    r"(?:\s+(?P<action>[^\s;&|)`]+))?"
)
_SHELL_WORD = re.compile(r"[a-z][a-z-]*")


def _shell_word(word: str | None) -> str | None:
    if word is None:
        return None
    word = word.strip("\"'")
    return word if _SHELL_WORD.fullmatch(word) else None


def _shell_line_offenders(source: str, *, env_disables_locks: bool = False) -> list[tuple[int, str]]:
    offenders: list[tuple[int, str]] = []
    for lineno, line in enumerate(source.splitlines(), start=1):
        code = line.split("#", 1)[0]
        for match in _SHELL_GIT.finditer(code):
            env_off = env_disables_locks or f"{_LOCKS_ENV}=0" in match.group("env").split()
            options = [option.strip("\"'") for option in match.group("options").split()]
            tokens = ["git", *options, _shell_word(match.group("verb")), _shell_word(match.group("action"))]
            verdict = _git_verdict(tokens, env_disables_locks=env_off)
            if verdict is not None:
                offenders.append((lineno, verdict))
    return offenders


def shell_git_calls_without_flag(source: str) -> list[tuple[int, str]]:
    return _shell_line_offenders(source)


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
        '["git", "check-attr", "-a", path]',
        '["git", "--no-optional-locks", "frobnicate"]',
        '("git", "runtime", "delegate")',
        'subprocess.run(["git", "status"], env={"GIT_OPTIONAL_LOCKS": "1"})',
        'subprocess.run(["git", "status"], env=env)',
        'subprocess.run("git status", shell=True)',
        'subprocess.run(f"git -C {repo} status --porcelain", shell=True)',
        'subprocess.check_output(f"cd {repo} && git {verb}", shell=True)',
        'os.system("git rev-parse HEAD")',
        'subprocess.run("git check-attr -a x", shell=True)',
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
        'subprocess.run(["git", "status"], env={**os.environ, "GIT_OPTIONAL_LOCKS": "0"})',
        'subprocess.run(["git", "-C", repo, "diff"], env=dict(os.environ, GIT_OPTIONAL_LOCKS="0"))',
        'subprocess.run("git --no-optional-locks status", shell=True)',
        'subprocess.run(f"git -C {repo} --no-optional-locks log -1", shell=True)',
        'subprocess.run("GIT_OPTIONAL_LOCKS=0 git status", shell=True)',
        'subprocess.run("git status", shell=True, env={"GIT_OPTIONAL_LOCKS": "0"})',
        'subprocess.run(f"git -C {repo} worktree add {path}", shell=True)',
        'subprocess.run("git push origin HEAD", shell=True)',
        'subprocess.run("echo git status")',
    ],
)
def test_lint_accepts_flagged_and_write_calls(snippet: str) -> None:
    assert git_calls_without_flag(f"cmd = {snippet}\n") == []


def test_shell_lint_flags_read_only_calls_without_flag() -> None:
    source = 'git status --porcelain\ngit --no-optional-locks diff\nhead="$(git -C "$R" rev-parse HEAD)"\ngit push\n'
    assert shell_git_calls_without_flag(source) == [(1, "status"), (3, "rev-parse")]


def test_lint_reports_each_shell_string_offender_on_its_call_line() -> None:
    source = 'import subprocess\n\nsubprocess.run(\n    "git status && git push && git log -1",\n    shell=True,\n)\n'
    assert git_calls_without_flag(source) == [(4, "log"), (4, "status")]


def test_lint_skips_only_named_data_tuples() -> None:
    assert git_calls_without_flag('LEAN_ORIENT_SECTIONS = ("git", "runtime", "delegate")\n') == []
    assert git_calls_without_flag('LEAN_ORIENT_SECTIONS: tuple[str, ...] = ("git", "runtime")\n') == []
    assert git_calls_without_flag('OTHER_SECTIONS = ("git", "runtime", "delegate")\n') == [
        (1, "runtime (unknown subcommand)")
    ]


@pytest.mark.parametrize(
    "line,expected",
    [
        ('git worktree add "$path" "$branch"', []),
        ('git -C "$R" worktree remove --force "$path"', []),
        ("git worktree list --porcelain", [(1, "worktree list")]),
        ("GIT_OPTIONAL_LOCKS=0 git status", []),
        ("FOO=1 git status", [(1, "status")]),
        ("git check-attr -a x", [(1, "check-attr")]),
        ("git frobnicate", [(1, "frobnicate (unknown subcommand)")]),
        ('git "$@"', [(1, "<dynamic>")]),
        ('git --no-optional-locks "$@"', []),
        ("out=$(git rev-parse HEAD)", [(1, "rev-parse")]),
        ("git commit -m x # git status in a comment", []),
    ],
)
def test_shell_lint_cases(line: str, expected: list[tuple[int, str]]) -> None:
    assert shell_git_calls_without_flag(line + "\n") == expected
