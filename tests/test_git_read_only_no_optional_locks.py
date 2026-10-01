"""Read-only git calls in the Monitor API, reporter and sweeps take no optional locks (#8874).

``git status`` (and other read-only commands that refresh the index) take
``.git/index.lock`` as an optional side effect. A reporter killed mid-call
leaves that lock behind, and every later writer in the same checkout fails
with "Unable to create .../index.lock: File exists". Read-only callers pass
``--no-optional-locks`` (``git(1)``) so they never take it.

The gate fails closed. It finds every ``git`` invocation in the scanned files:
argv lists and tuples (also built by ``+`` concatenation, ``*`` unpacking or
``shlex.split``/``str.split`` of a literal), ``exec``-style calls whose first
argument is ``"git"``, shell command strings (``shell=True``, ``os.system``,
``sh -c``; f-strings and ``+`` concatenations included) and every shell-file
line. For each one it must statically prove one of two things:

* locks are off: ``--no-optional-locks`` among the global options before the
  subcommand, or ``GIT_OPTIONAL_LOCKS=0`` as the last effective assignment in
  the call's ``env=`` (or a shell env prefix); or
* the subcommand is a literal in ``_WRITE_VERBS``, which is free to take the
  locks it needs.

A literal ``_READ_VERBS`` subcommand without either is an offender, and so is
any other literal subcommand (it must be added to one of the closed sets). A
subcommand that cannot be resolved from literal elements (``["git", *args]``,
``["git", "-C", repo] + rest``, ``f"git {verb}"``), a shell command whose
command word is not a literal, and an ``env=`` the resolver cannot follow are
offenders too. The flag is harmless on a command that does write, so the
remedy is to add it. A genuinely dynamic call that cannot carry it takes a
``# lock-lint: ok <reason>`` comment on its reported line; the marker exempts
only unresolved subcommands, needs a non-empty reason, and the repository may
hold at most ``_MAX_MARKERS`` of them.
"""

from __future__ import annotations

import ast
import io
import re
import tokenize
from collections.abc import Iterator
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
# Keyword arguments whose value is data, never an argv (FastAPI ``tags=["git"]``).
_DATA_KEYWORDS = frozenset({"tags"})
_SHELL_CALLS = frozenset({"system", "popen", "getoutput", "getstatusoutput", "create_subprocess_shell"})
_SHELLS = frozenset({"sh", "bash", "dash", "zsh"})

# Verdicts for a call whose subcommand or command word is not a literal: the
# only ones a ``# lock-lint: ok <reason>`` marker may exempt.
_DYNAMIC = "<dynamic>"
_UNRESOLVED_SHELL = "<unresolved shell command>"
_MAX_MARKERS = 2
_MARKER = re.compile(r"#\s*lock-lint:\s*ok\b(?P<reason>.*)$")


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
    covered = _FLAG in globals_seen or env_disables_locks
    verb = tokens[index] if index < len(tokens) else None
    if verb is None:
        return None if covered else _DYNAMIC
    if verb in _WRITE_VERBS:
        return None
    if verb == "worktree":
        action = tokens[index + 1] if index + 1 < len(tokens) else None
        if action in _WORKTREE_WRITE_ACTIONS or covered:
            return None
        return f"worktree {action or _DYNAMIC}"
    if verb in _READ_VERBS:
        return None if covered else verb
    return f"{verb} (unknown subcommand)"


def _exemptable(verdict: str) -> bool:
    return _DYNAMIC in verdict or verdict == _UNRESOLVED_SHELL


def _argv_token(node: ast.expr) -> str | None:
    """A string constant, or the leading literal of an f-string option such as ``f"--git-dir={d}"``."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.JoinedStr) and node.values:
        head = node.values[0]
        if isinstance(head, ast.Constant) and isinstance(head.value, str) and head.value.startswith("-"):
            return head.value
    return None


def _shell_text(node: ast.expr | str | None) -> str:
    """Render a shell command with each non-literal part as a NUL byte."""
    if isinstance(node, str):
        return node
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.JoinedStr):
        return "".join(
            part.value if isinstance(part, ast.Constant) and isinstance(part.value, str) else "\0"
            for part in node.values
        )
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        return _shell_text(node.left) + _shell_text(node.right)
    return "\0"


# An argv item: an element node, a word split from a literal, or None for a
# span of unknown length (``*args``, ``+ rest``).
_Item = ast.expr | str | None


def _split_call_text(node: ast.expr) -> str | None:
    """The literal text of ``shlex.split(<text>)`` or ``<text>.split()``."""
    if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute) or node.func.attr != "split":
        return None
    if isinstance(node.func.value, ast.Name) and node.func.value.id == "shlex" and node.args:
        source = node.args[0]
    elif not node.args:
        source = node.func.value
    else:
        return None
    if isinstance(source, (ast.Constant, ast.JoinedStr)) or (
        isinstance(source, ast.BinOp) and isinstance(source.op, ast.Add)
    ):
        text = _shell_text(source)
        return text if text != "\0" else None
    return None


def _argv_items(node: ast.expr) -> list[_Item] | None:
    """Flatten an argv expression; None when ``node`` is not argv-shaped."""
    if isinstance(node, (ast.List, ast.Tuple)):
        items: list[_Item] = []
        for element in node.elts:
            if isinstance(element, ast.Starred):
                items.extend(_argv_items(element.value) or [None])
            else:
                items.append(element)
        return items
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        left, right = _argv_items(node.left), _argv_items(node.right)
        if left is None and right is None:
            return None
        return (left or [None]) + (right or [None])
    text = _split_call_text(node)
    if text is not None:
        return [None if "\0" in word else word for word in text.split()]
    return None


def _item_token(item: _Item) -> str | None:
    if item is None or isinstance(item, str):
        return item
    return _argv_token(item)


def _program(item: _Item) -> str | None:
    """The program a token names: a bare name or a path in a ``bin`` directory (``/usr/bin/git``)."""
    token = _item_token(item)
    if token is None:
        return None
    directory, slash, name = token.rpartition("/")
    return name if not slash or directory.endswith("/bin") or directory == "bin" else None


def _is_command_argv(items: list[_Item] | None) -> bool:
    return bool(items) and _program(items[0]) in {"git", *_SHELLS}


# --- env= resolution -------------------------------------------------------
# A mapping's effect on GIT_OPTIONAL_LOCKS: sets it to "0", provably leaves it
# untouched, or anything else (another value, an unknown mapping, a removal).
_ZERO, _ABSENT, _UNKNOWN = "zero", "absent", "unknown"
_SCOPES = (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.ClassDef, ast.Module)
_LOOPS = (ast.For, ast.AsyncFor, ast.While)
_MUTATORS = frozenset({"update", "setdefault", "pop", "popitem", "clear", "__setitem__", "__delitem__", "__ior__"})
_MAX_DEPTH = 32


def _merge(state: str, later: str) -> str:
    return state if later == _ABSENT else later


def _key_write(key: ast.expr | None, value: ast.expr | None) -> str:
    """The effect of ``mapping[key] = value`` (``value`` None: a deletion or an in-place operator)."""
    if not (isinstance(key, ast.Constant) and isinstance(key.value, str)):
        return _UNKNOWN
    if key.value != _LOCKS_ENV:
        return _ABSENT
    return _ZERO if isinstance(value, ast.Constant) and value.value == "0" else _UNKNOWN


def _declares(node: ast.AST, name: str) -> bool:
    """A parameter, import or definition binding ``name`` to a value the resolver does not follow."""
    if isinstance(node, ast.arg):
        return node.arg == name
    if isinstance(node, ast.alias):
        return (node.asname or node.name).split(".")[0] == name
    return isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and node.name == name


def _store_event(node: ast.Name, parent: ast.AST | None) -> tuple:
    """The effect of a store to ``node``: a new mapping, an in-place ``|=``, or an unfollowed binding."""
    if isinstance(parent, ast.Assign) and any(target is node for target in parent.targets):
        return ("set", parent.value)
    if isinstance(parent, (ast.AnnAssign, ast.NamedExpr)) and parent.target is node and parent.value is not None:
        return ("set", parent.value)
    if isinstance(parent, ast.AugAssign) and isinstance(parent.op, ast.BitOr):
        return ("merge", parent.value)
    return ("unknown",)


class _Module:
    def __init__(self, tree: ast.Module) -> None:
        self.tree = tree
        self.parents = {child: parent for parent in ast.walk(tree) for child in ast.iter_child_nodes(parent)}

    def ancestors(self, node: ast.AST) -> Iterator[ast.AST]:
        while node in self.parents:
            node = self.parents[node]
            yield node

    def scope_of(self, node: ast.AST) -> ast.AST:
        return next(a for a in self.ancestors(node) if isinstance(a, _SCOPES))

    def stmt_path(self, node: ast.AST, scope: ast.AST) -> list[tuple[int, str, int]]:
        """(container, field, index) of each statement enclosing ``node``, from ``scope`` down."""
        path: list[tuple[int, str, int]] = []
        current = node
        while current is not scope:
            parent = self.parents[current]
            if isinstance(current, ast.stmt):
                for field, value in ast.iter_fields(parent):
                    if isinstance(value, list) and any(item is current for item in value):
                        path.append((id(parent), field, next(i for i, s in enumerate(value) if s is current)))
                        break
            current = parent
        return path[::-1]

    def mapping_state(self, node: ast.expr, depth: int = 0) -> str:
        if depth > _MAX_DEPTH:
            return _UNKNOWN
        if isinstance(node, ast.Dict):
            state = _ABSENT
            for key, value in zip(node.keys, node.values, strict=True):
                later = self.mapping_state(value, depth + 1) if key is None else _key_write(key, value)
                state = _merge(state, later)
            return state
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "dict":
            return self.call_state(node, _ABSENT, depth)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "copy":
            return self.mapping_state(node.func.value, depth + 1) if not node.args and not node.keywords else _UNKNOWN
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
            return _merge(self.mapping_state(node.left, depth + 1), self.mapping_state(node.right, depth + 1))
        if isinstance(node, ast.Name):
            return self.name_state(node, depth + 1)
        return _UNKNOWN

    def call_state(self, call: ast.Call, state: str, depth: int) -> str:
        """Apply ``dict(...)`` or ``mapping.update(...)`` arguments on top of ``state``."""
        if len(call.args) > 1 or any(isinstance(arg, ast.Starred) for arg in call.args):
            return _UNKNOWN
        for arg in call.args:
            state = _merge(state, self.mapping_state(arg, depth + 1))
        for keyword in call.keywords:
            if keyword.arg is None:
                later = self.mapping_state(keyword.value, depth + 1)
            elif keyword.arg == _LOCKS_ENV:
                later = _ZERO if isinstance(keyword.value, ast.Constant) and keyword.value.value == "0" else _UNKNOWN
            else:
                later = _ABSENT
            state = _merge(state, later)
        return state

    def apply(self, state: str, event: tuple, depth: int) -> str:
        kind = event[0]
        if kind == "set":
            return self.mapping_state(event[1], depth + 1)
        if kind == "merge":
            return _merge(state, self.mapping_state(event[1], depth + 1))
        if kind == "key":
            return _merge(state, _key_write(event[1], event[2]))
        if kind == "method":
            call: ast.Call = event[1]
            method = call.func.attr  # type: ignore[attr-defined]
            key = call.args[0] if call.args else None
            if method == "update":
                return self.call_state(call, state, depth)
            if method == "__ior__":
                return _merge(state, self.mapping_state(key, depth + 1)) if key is not None else _UNKNOWN
            if method == "__setitem__":
                return _merge(state, _key_write(key, call.args[1] if len(call.args) > 1 else None))
            if method == "setdefault":
                if _key_write(key, None) == _ABSENT or state == _ZERO:
                    return state
                return _key_write(key, call.args[1] if len(call.args) > 1 else None) if state == _ABSENT else _UNKNOWN
            if method in {"pop", "__delitem__"} and _key_write(key, None) == _ABSENT:
                return state
        return _UNKNOWN

    def events(self, scope: ast.AST, name: str) -> list[tuple[ast.AST, tuple]]:
        """Each binding or mutation of ``name`` directly in ``scope`` (nested scopes excluded)."""
        found: list[tuple[ast.AST, tuple]] = []
        stack = list(ast.iter_child_nodes(scope))
        while stack:
            node = stack.pop()
            if not isinstance(node, _SCOPES):
                stack.extend(ast.iter_child_nodes(node))
            parent = self.parents.get(node)
            if isinstance(node, (ast.Global, ast.Nonlocal)) and name in node.names:
                found.append((node, ("global",)))
            elif _declares(node, name):
                found.append((node, ("unknown",)))
            elif isinstance(node, ast.Name) and node.id == name and not isinstance(node.ctx, ast.Load):
                found.append((node, _store_event(node, parent)))
            elif (
                isinstance(node, ast.Subscript)
                and isinstance(node.value, ast.Name)
                and node.value.id == name
                and not isinstance(node.ctx, ast.Load)
            ):
                value = parent.value if isinstance(parent, ast.Assign) else None
                found.append((node, ("key", node.slice, value)))
            elif (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id == name
                and node.func.attr in _MUTATORS
            ):
                found.append((node, ("method", node)))
        return sorted(found, key=lambda pair: (getattr(pair[0], "lineno", 0), getattr(pair[0], "col_offset", 0)))

    def flow_state(self, scope: ast.AST, use: ast.AST, events: list[tuple[ast.AST, tuple]], depth: int) -> str:
        """Apply, in order, the events that run before ``use`` on every path; any other may-write is unknown."""
        use_path = self.stmt_path(use, scope)
        use_pos = (getattr(use, "lineno", 0), getattr(use, "col_offset", 0))
        use_loops = {id(a) for a in self.ancestors(use) if isinstance(a, _LOOPS)}
        state = _UNKNOWN
        for node, event in events:
            path = self.stmt_path(node, scope)
            pos = (getattr(node, "lineno", 0), getattr(node, "col_offset", 0))
            if pos >= use_pos:
                if use_loops & {id(a) for a in self.ancestors(node) if isinstance(a, _LOOPS)}:
                    return _UNKNOWN
                continue
            depth_index = len(path) - 1
            dominates = (
                depth_index >= 0
                and depth_index < len(use_path)
                and path[:depth_index] == use_path[:depth_index]
                and path[depth_index][:2] == use_path[depth_index][:2]
                and path[depth_index][2] < use_path[depth_index][2]
            )
            state = self.apply(state, event, depth) if dominates else _UNKNOWN
        return state

    def name_state(self, name: ast.Name, depth: int) -> str:
        scope = self.scope_of(name)
        while True:
            events = self.events(scope, name.id)
            if any(event[0] == "global" for _node, event in events):
                return _UNKNOWN
            if isinstance(scope, ast.Module):
                return self.module_name_state(name, events, depth)
            if any(event[0] in {"set", "merge", "unknown"} for _node, event in events):
                return self.flow_state(scope, name, events, depth)
            if events:  # mutates a name it never binds: a closure or module object
                return _UNKNOWN
            scope = self.scope_of(scope)
            while isinstance(scope, ast.ClassDef):
                scope = self.scope_of(scope)
            if not isinstance(scope, ast.Module):
                return _UNKNOWN  # closure over an enclosing function

    def module_name_state(self, name: ast.Name, events: list[tuple[ast.AST, tuple]], depth: int) -> str:
        for node in ast.walk(self.tree):
            if isinstance(node, _SCOPES) and node is not self.tree and self.events(node, name.id):
                nested = self.events(node, name.id)
                binds = any(event[0] in {"set", "merge", "unknown"} for _n, event in nested)
                if any(event[0] == "global" for _n, event in nested) or not binds:
                    return _UNKNOWN
        if self.scope_of(name) is self.tree:
            return self.flow_state(self.tree, name, events, depth)
        state = _UNKNOWN
        for node, event in events:
            if len(self.stmt_path(node, self.tree)) != 1:
                return _UNKNOWN
            state = self.apply(state, event, depth)
        return state

    def env_state(self, call: ast.Call) -> str:
        for keyword in call.keywords:
            if keyword.arg == "env":
                return self.mapping_state(keyword.value)
            if keyword.arg is None:
                return _UNKNOWN  # ``**kwargs`` may carry env=
        return _ABSENT


# --- shell text ------------------------------------------------------------
# A ``git`` at command position, with any ``NAME=value`` env prefix, its global
# options and the next two words (the subcommand and a worktree action).
_SHELL_GIT = re.compile(
    r"(?:^|[\s;&|(`$])"
    r"(?P<env>(?:[A-Za-z_][A-Za-z0-9_]*=[^\s;&|]*\s+)*)"
    r"git"
    r"(?P<options>(?:\s+(?:-[Cc]|--git-dir|--work-tree|--namespace)\s+\S+|\s+-\S+)*)"
    r"\s+(?P<verb>[^\s;&|)`]+)"
    r"(?:\s+(?P<action>[^\s;&|)`]+))?"
)
_SHELL_WORD = re.compile(r"[a-z][a-z-]*")
# A non-literal part (rendered NUL) at command position: the command run is unknown.
_COMMAND_PLACEHOLDER = re.compile(
    r"(?:^|[;&|(`\n]|\$\()\s*"
    r"(?:[A-Za-z_][A-Za-z0-9_]*=[^\s;&|]*\s+)*"
    r"(?:(?:command|env|exec|nohup|sudo|time|xargs|then|do|else)\s+)*"
    r"[\"']?\0"
)


def _shell_word(word: str | None) -> str | None:
    if word is None:
        return None
    word = word.strip("\"'")
    return word if _SHELL_WORD.fullmatch(word) else None


def _prefix_state(env: str) -> str:
    """The last ``GIT_OPTIONAL_LOCKS=`` assignment in a shell env prefix."""
    state = _ABSENT
    for assignment in env.split():
        key, _, value = assignment.partition("=")
        if key == _LOCKS_ENV:
            state = _ZERO if value.strip("\"'") == "0" else _UNKNOWN
    return state


def _shell_line_offenders(source: str, *, env_state: str = _ABSENT) -> list[tuple[int, str]]:
    offenders: list[tuple[int, str]] = []
    # The call's env= counts only when the text never touches the variable itself.
    inherited = env_state if _LOCKS_ENV not in source else _UNKNOWN
    for lineno, line in enumerate(source.splitlines(), start=1):
        code = line.split("#", 1)[0]
        if _COMMAND_PLACEHOLDER.search(code):
            offenders.append((lineno, _UNRESOLVED_SHELL))
        for match in _SHELL_GIT.finditer(code):
            prefix = _prefix_state(match.group("env"))
            effective = inherited if prefix == _ABSENT else prefix
            options = [option.strip("\"'") for option in match.group("options").split()]
            tokens = ["git", *options, _shell_word(match.group("verb")), _shell_word(match.group("action"))]
            verdict = _git_verdict(tokens, env_disables_locks=effective == _ZERO)
            if verdict is not None:
                offenders.append((lineno, verdict))
    return offenders


def shell_git_calls_without_flag(source: str) -> list[tuple[int, str]]:
    markers = _shell_markers(source)
    return [
        (lineno, verdict)
        for lineno, verdict in _shell_line_offenders(source)
        if not (_exemptable(verdict) and markers.get(lineno, "").strip())
    ]


# --- Python source ---------------------------------------------------------
def _runs_in_shell(call: ast.Call) -> bool:
    func = call.func
    name = func.attr if isinstance(func, ast.Attribute) else func.id if isinstance(func, ast.Name) else None
    if name in _SHELL_CALLS:
        return True
    return any(
        keyword.arg == "shell" and not (isinstance(keyword.value, ast.Constant) and not keyword.value.value)
        for keyword in call.keywords
    )


def _argv_verdicts(items: list[_Item], env_state: str) -> list[str]:
    """Verdicts for one argv whose program is ``git`` or a shell."""
    tokens = [_item_token(item) for item in items]
    if _program(items[0]) == "git":
        verdict = _git_verdict(tokens, env_disables_locks=env_state == _ZERO)
        return [verdict] if verdict is not None else []
    for index, token in enumerate(tokens[1:], start=1):
        if token is None or not token.startswith("-"):
            return [_UNRESOLVED_SHELL] if token is None else []  # a script file, or unknown options
        if "c" in token.lstrip("-") and not token.startswith("--"):
            text = _shell_text(items[index + 1]) if index + 1 < len(items) else "\0"
            return [verdict for _line, verdict in _shell_line_offenders(text, env_state=env_state)]
    return []


def _python_markers(source: str) -> dict[int, str]:
    markers: dict[int, str] = {}
    for token in tokenize.generate_tokens(io.StringIO(source).readline):
        if token.type == tokenize.COMMENT and (match := _MARKER.search(token.string)):
            markers[token.start[0]] = match.group("reason")
    return markers


def _shell_markers(source: str) -> dict[int, str]:
    markers: dict[int, str] = {}
    for lineno, line in enumerate(source.splitlines(), start=1):
        if "#" in line and (match := _MARKER.search(line[line.index("#") :])):
            markers[lineno] = match.group("reason")
    return markers


def _python_offenders(source: str) -> list[tuple[int, str]]:
    tree = ast.parse(source)
    module = _Module(tree)
    offenders: list[tuple[int, str]] = []
    seen: set[int] = set()

    def claim(node: ast.AST) -> None:
        seen.update(id(child) for child in ast.walk(node))

    for node in ast.walk(tree):
        if isinstance(node, (ast.Assign, ast.AnnAssign)) and node.value is not None:
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            if any(isinstance(t, ast.Name) and t.id in _NOT_GIT_ARGV for t in targets):
                claim(node.value)
        elif isinstance(node, ast.keyword) and node.arg in _DATA_KEYWORDS:
            claim(node.value)
    # Breadth-first: a call before its argv, an outer argv before its parts.
    for node in ast.walk(tree):
        if id(node) in seen:
            continue
        if isinstance(node, ast.Call):
            command = node.args[0] if node.args else next((k.value for k in node.keywords if k.arg == "args"), None)
            if command is not None and not isinstance(command, ast.Starred):
                items = _argv_items(command)
                if _runs_in_shell(node) and not _is_command_argv(items):
                    claim(command)
                    text = _shell_text(command)
                    for _line, verdict in _shell_line_offenders(text, env_state=module.env_state(node)):
                        offenders.append((command.lineno, verdict))
                elif _is_command_argv(items):
                    claim(command)
                    offenders.extend((command.lineno, v) for v in _argv_verdicts(items, module.env_state(node)))
                elif _item_token(command) == "git" and len(node.args) > 1:
                    # exec-style: create_subprocess_exec("git", "status", ...)
                    for arg in node.args:
                        claim(arg)
                    exec_items: list[_Item] = [None if isinstance(a, ast.Starred) else a for a in node.args]
                    offenders.extend((node.lineno, v) for v in _argv_verdicts(exec_items, module.env_state(node)))
        # The call itself may be an argv (``shlex.split("git status")``).
        if isinstance(node, ast.expr) and id(node) not in seen:
            items = _argv_items(node)
            if _is_command_argv(items):
                claim(node)
                offenders.extend((node.lineno, v) for v in _argv_verdicts(items, _ABSENT))
    return offenders


def git_calls_without_flag(source: str) -> list[tuple[int, str]]:
    """Return (lineno, verdict) for each git invocation that fails the gate."""
    markers = _python_markers(source)
    return sorted(
        (lineno, verdict)
        for lineno, verdict in _python_offenders(source)
        if not (_exemptable(verdict) and markers.get(lineno, "").strip())
    )


def marker_budget_violation(markers: list[str]) -> str | None:
    """None while the ``# lock-lint: ok`` escape hatch stays within its fixed budget."""
    if len(markers) <= _MAX_MARKERS:
        return None
    return f"{len(markers)} lock-lint markers exceed the budget of {_MAX_MARKERS}:\n" + "\n".join(markers)


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


def test_lock_lint_markers_stay_within_budget() -> None:
    markers: list[str] = []
    for path in _scanned_python_files():
        found = _python_markers(path.read_text(encoding="utf-8"))
        markers.extend(f"{path.relative_to(_REPO_ROOT)}:{lineno}" for lineno in found)
    for path in _SHELL_FILES:
        found = _shell_markers(path.read_text(encoding="utf-8"))
        markers.extend(f"{path.relative_to(_REPO_ROOT)}:{lineno}" for lineno in found)
    assert marker_budget_violation(markers) is None, marker_budget_violation(markers)


def test_marker_budget_fails_above_the_fixed_number() -> None:
    assert marker_budget_violation([f"f.py:{n}" for n in range(_MAX_MARKERS)]) is None
    violation = marker_budget_violation([f"f.py:{n}" for n in range(_MAX_MARKERS + 1)])
    assert violation is not None and f"{_MAX_MARKERS + 1} lock-lint markers" in violation


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
        # A later key or unpack overrides an earlier "0" (review r2, case 1).
        'subprocess.run(["git", "status"], env={"GIT_OPTIONAL_LOCKS": "0", **os.environ})',
        'subprocess.run(["git", "status"], env={**base, "GIT_OPTIONAL_LOCKS": "0", **extra})',
        'subprocess.run(["git", "status"], env={"GIT_OPTIONAL_LOCKS": "0", "GIT_OPTIONAL_LOCKS": "1"})',
        'subprocess.run(["git", "status"], env={**a, **b})',
        'subprocess.run(["git", "status"], env=dict(os.environ, GIT_OPTIONAL_LOCKS="1"))',
        'subprocess.run(["git", "status"], env=dict({"GIT_OPTIONAL_LOCKS": "0"}, **extra))',
        'subprocess.run(["git", "status"], env={"GIT_OPTIONAL_LOCKS": "0"} | os.environ)',
        'subprocess.run(["git", "status"], env=os.environ)',
        'subprocess.run(["git", "status"], env=None)',
        'subprocess.run(["git", "status"], env=make_env())',
        'subprocess.run(["git", "status"], **kwargs)',
        # Concatenation in either order; the prefix ends before the subcommand (review r2, case 2).
        'subprocess.run(["git", "-C", repo] + ["status", "--porcelain"])',
        '["git"] + ["-C", repo, "status"]',
        '("git", "-C", repo) + ("status",)',
        '["git", "-C", repo] + args',
        '["git"] + list(args)',
        '["git", "-C", repo]',
        '["git"]',
        # Tuple and * unpacking.
        '[*("git", "-C", repo), "status"]',
        '["git", *prefix, "status"]',
        '("git", *("-C", repo), "log")',
        '["git", *opts, "--no-optional-locks", "status"]',
        # Other argv shapes and programs.
        'shlex.split("git status --porcelain")',
        '"git log -1".split()',
        '["/usr/bin/git", "status"]',
        'run(command=["git", "status"], tag="git")',
        'asyncio.create_subprocess_exec("git", "status")',
        'subprocess.run(["bash", "-c", "git status"])',
        'subprocess.run(["sh", "-ec", f"cd {repo} && git log -1"])',
        'subprocess.run(["bash", "-c", command])',
        # Shell commands the lint cannot read, and env prefixes overridden later.
        'subprocess.run("git " + verb, shell=True)',
        'subprocess.run("cd x && " + command, shell=True)',
        "subprocess.run(command, shell=True)",
        'subprocess.run(f"{git_bin} status", shell=True)',
        'subprocess.run("GIT_OPTIONAL_LOCKS=0 GIT_OPTIONAL_LOCKS=1 git status", shell=True)',
        'subprocess.run("GIT_OPTIONAL_LOCKS=1 git status", shell=True, env={"GIT_OPTIONAL_LOCKS": "0"})',
        'subprocess.run("export GIT_OPTIONAL_LOCKS=1; git status", shell=True, env={"GIT_OPTIONAL_LOCKS": "0"})',
        'subprocess.run("git status", shell=use_shell)',
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
        'subprocess.run(["git", "status"], env={**os.environ, "GIT_OPTIONAL_LOCKS": "0"})',
        'subprocess.run(["git", "-C", repo, "diff"], env=dict(os.environ, GIT_OPTIONAL_LOCKS="0"))',
        'subprocess.run(["git", "status"], env={**a, **b, "GIT_OPTIONAL_LOCKS": "0"})',
        'subprocess.run(["git", "status"], env=os.environ | {"GIT_OPTIONAL_LOCKS": "0"})',
        'subprocess.run(["git", "status"], env=dict(os.environ, **{"GIT_OPTIONAL_LOCKS": "0"}))',
        'subprocess.run(["git", "-C", repo] + ["status"], env={**os.environ, "GIT_OPTIONAL_LOCKS": "0"})',
        'subprocess.run("git --no-optional-locks status", shell=True)',
        'subprocess.run(f"git -C {repo} --no-optional-locks log -1", shell=True)',
        'subprocess.run("GIT_OPTIONAL_LOCKS=0 git status", shell=True)',
        'subprocess.run("GIT_OPTIONAL_LOCKS=1 GIT_OPTIONAL_LOCKS=0 git status", shell=True)',
        'subprocess.run("git status", shell=True, env={"GIT_OPTIONAL_LOCKS": "0"})',
        'subprocess.run(f"git -C {repo} worktree add {path}", shell=True)',
        'subprocess.run("git push origin HEAD", shell=True)',
        'subprocess.run("echo git status")',
        'subprocess.run("git status", shell=False)',
        'subprocess.run(f"cd {repo} && git --no-optional-locks status", shell=True)',
        '["git", "--no-optional-locks", "-C", repo] + ["status"]',
        '["git", "--no-optional-locks"] + args',
        '["git", "-C", repo] + ["push", "origin"]',
        '[*("git", "-C", repo), "fetch"]',
        '("git", "--no-optional-locks") + tuple(args)',
        'shlex.split("git --no-optional-locks status")',
        'asyncio.create_subprocess_exec("git", "--no-optional-locks", "status")',
        'subprocess.run(["bash", "-c", "git --no-optional-locks status"])',
        'subprocess.run(["bash", "script.sh"])',
        'shutil.which("git")',
        'APIRouter(tags=["git"])',
        'RouteContract("/api/git", "prefix", "http")',
        'cmd[0] == "git"',
    ],
)
def test_lint_accepts_flagged_and_write_calls(snippet: str) -> None:
    assert git_calls_without_flag(f"cmd = {snippet}\n") == []


def test_lint_reports_a_git_prefix_reused_by_unpacking() -> None:
    source = 'prefix = ["git", "-C", repo]\nsubprocess.run([*prefix, "status"])\n'
    assert git_calls_without_flag(source) == [(1, _DYNAMIC)]
    flagged = 'prefix = ["git", "--no-optional-locks", "-C", repo]\nsubprocess.run([*prefix, "status"])\n'
    assert git_calls_without_flag(flagged) == []


@pytest.mark.parametrize(
    "body",
    [
        'env = os.environ.copy()\nenv["GIT_OPTIONAL_LOCKS"] = "0"\nsubprocess.run(["git", "status"], env=env)\n',
        'env = dict(os.environ)\nenv.update({"GIT_OPTIONAL_LOCKS": "0"})\nsubprocess.run(["git", "status"], env=env)\n',
        'env = {**os.environ}\nenv.update(GIT_OPTIONAL_LOCKS="0", LANG="C")\nsubprocess.run(["git", "status"], env=env)\n',
        'env = os.environ.copy()\nenv |= {"GIT_OPTIONAL_LOCKS": "0"}\nsubprocess.run(["git", "status"], env=env)\n',
        'env = os.environ.copy()\nenv["GIT_OPTIONAL_LOCKS"] = "0"\nenv["LANG"] = "C"\nenv.pop("PAGER", None)\n'
        'subprocess.run(["git", "status"], env=env)\n',
        'base = {**os.environ, "GIT_OPTIONAL_LOCKS": "0"}\nenv = {**base, "LANG": "C"}\n'
        'subprocess.run(["git", "status"], env=env)\n',
        'env = os.environ.copy()\nenv["GIT_OPTIONAL_LOCKS"] = "0"\nfor repo in repos:\n'
        '    subprocess.run(["git", "-C", repo, "status"], env=env)\n',
    ],
)
def test_lint_accepts_env_built_in_statements(body: str) -> None:
    source = "def run(repos, extra, cond):\n" + "".join(f"    {line}\n" for line in body.splitlines())
    assert git_calls_without_flag(source) == []


@pytest.mark.parametrize(
    "body",
    [
        # env.update(...) after the assignment may set it again.
        'env = os.environ.copy()\nenv["GIT_OPTIONAL_LOCKS"] = "0"\nenv.update(extra)\n'
        'subprocess.run(["git", "status"], env=env)\n',
        'env = os.environ.copy()\nenv["GIT_OPTIONAL_LOCKS"] = "0"\nenv.update(GIT_OPTIONAL_LOCKS="1")\n'
        'subprocess.run(["git", "status"], env=env)\n',
        'env = os.environ.copy()\nenv["GIT_OPTIONAL_LOCKS"] = "0"\nenv |= extra\nsubprocess.run(["git", "status"], env=env)\n',
        'env = os.environ.copy()\nenv["GIT_OPTIONAL_LOCKS"] = "0"\nenv[key] = "1"\nsubprocess.run(["git", "status"], env=env)\n',
        'env = os.environ.copy()\nenv["GIT_OPTIONAL_LOCKS"] = "0"\ndel env["GIT_OPTIONAL_LOCKS"]\n'
        'subprocess.run(["git", "status"], env=env)\n',
        'env = os.environ.copy()\nenv["GIT_OPTIONAL_LOCKS"] = "0"\nenv.pop("GIT_OPTIONAL_LOCKS")\n'
        'subprocess.run(["git", "status"], env=env)\n',
        'env = os.environ.copy()\nsubprocess.run(["git", "status"], env=env)\n',
        # A write on only one path does not cover the call.
        'env = os.environ.copy()\nif cond:\n    env["GIT_OPTIONAL_LOCKS"] = "0"\nsubprocess.run(["git", "status"], env=env)\n',
        'env = {"GIT_OPTIONAL_LOCKS": "0"}\nif cond:\n    env = os.environ.copy()\nsubprocess.run(["git", "status"], env=env)\n',
        # A write after the call reaches it on the next loop iteration.
        'env = {"GIT_OPTIONAL_LOCKS": "0"}\nfor repo in repos:\n    subprocess.run(["git", "-C", repo, "status"], env=env)\n'
        "    env.update(extra)\n",
        # Parameters and closures are not statically known.
        'subprocess.run(["git", "status"], env=extra)\n',
    ],
)
def test_lint_flags_env_overridden_in_statements(body: str) -> None:
    source = "def run(repos, extra, cond, key):\n" + "".join(f"    {line}\n" for line in body.splitlines())
    assert [verdict for _line, verdict in git_calls_without_flag(source)] == ["status"]


def test_lint_follows_module_level_env() -> None:
    covered = '_ENV = {**os.environ, "GIT_OPTIONAL_LOCKS": "0"}\n\ndef run():\n    subprocess.run(["git", "status"], env=_ENV)\n'
    assert git_calls_without_flag(covered) == []
    mutated = covered + '\ndef poison():\n    _ENV["GIT_OPTIONAL_LOCKS"] = "1"\n'
    assert git_calls_without_flag(mutated) == [(4, "status")]
    rebound = covered + "\ndef rebind():\n    global _ENV\n    _ENV = {}\n"
    assert git_calls_without_flag(rebound) == [(4, "status")]


def test_marker_exempts_only_unresolved_subcommands_with_a_reason() -> None:
    dynamic = 'cmd = ["git", *args]  # lock-lint: ok callers pass only write verbs\n'
    assert git_calls_without_flag(dynamic) == []
    assert git_calls_without_flag('cmd = ["git", *args]  # lock-lint: ok\n') == [(1, _DYNAMIC)]
    assert git_calls_without_flag('cmd = ["git", "status"]  # lock-lint: ok reason\n') == [(1, "status")]
    shell = "subprocess.run(command, shell=True)  # lock-lint: ok command is a fixed constant\n"
    assert git_calls_without_flag(shell) == []
    in_string = 'cmd = ["git", *args, "# lock-lint: ok not a comment"]\n'
    assert git_calls_without_flag(in_string) == [(1, _DYNAMIC)]
    assert _python_markers(dynamic + in_string) == {1: " callers pass only write verbs"}
    assert shell_git_calls_without_flag('git "$@"  # lock-lint: ok wrapper of write verbs\n') == []


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
        ("GIT_OPTIONAL_LOCKS=0 GIT_OPTIONAL_LOCKS=1 git status", [(1, "status")]),
        ("env GIT_OPTIONAL_LOCKS=0 git status", []),
        ("git check-attr -a x", [(1, "check-attr")]),
        ("git frobnicate", [(1, "frobnicate (unknown subcommand)")]),
        ('git "$@"', [(1, "<dynamic>")]),
        ('git --no-optional-locks "$@"', []),
        ('git -C "$R"', [(1, "<dynamic>")]),
        ("out=$(git rev-parse HEAD)", [(1, "rev-parse")]),
        ("git commit -m x # git status in a comment", []),
    ],
)
def test_shell_lint_cases(line: str, expected: list[tuple[int, str]]) -> None:
    assert shell_git_calls_without_flag(line + "\n") == expected
