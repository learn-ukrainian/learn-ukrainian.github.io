"""Read-only git calls in the Monitor API, reporter and sweeps take no optional locks (#8874).

``git status`` (and other read-only commands that refresh the index) take
``.git/index.lock`` as an optional side effect. A reporter killed mid-call
leaves that lock behind, and every later writer in the same checkout fails
with "Unable to create .../index.lock: File exists". Read-only callers pass
``--no-optional-locks`` (``git(1)``) so they never take it.

The gate fails closed by construction: it accepts a call only on a static
proof and treats every expression it cannot prove as an offender.

* Every process-spawning call (``subprocess.run``/``Popen``/``call``/
  ``check_call``/``check_output``/``getoutput``/``getstatusoutput``,
  ``asyncio.create_subprocess_exec``/``_shell``, ``os.system``,
  ``os.popen``, ``os.exec*``/``spawn*``/``posix_spawn*``, under any import
  alias) must prove its command. A process function used as a value
  (``partial(subprocess.run, ...)``, ``getattr(subprocess, "run")``,
  ``run = subprocess.run``) is an offender.
* A command is proven when it is a literal argv (list, tuple, ``+``, ``*``
  of literals, ``shlex.split``/``str.split`` of a literal) or literal shell
  text whose program is not ``git`` and runs no ``git`` (after ``&&``,
  ``;``, ``|``, ``$(``, backticks, quotes or ``sh -c``; a wrapper such as
  ``timeout 5 git`` included), or a ``git`` call with a literal subcommand
  that is a write verb or runs with locks off. A program word may also be a
  literal path built by ``str()``, ``Path()`` and ``/``.
* A program other than git is proven only when no argument carries ``git``
  as a word (``make --eval 'x:; git status'``), it writes no ``gh`` alias,
  and, for ``make``/``just``/``task``, every argument is a literal. A
  ``git config alias.*`` write and a ``git`` word in shell text outside a
  readable git command (``/usr/bin/git status``, ``xargs git``) are unproven.
* A name proves a command only when it is local to the function, assigned
  exactly once by a plain assignment that runs before the call, read exactly
  once (as this command) and never declared ``global``/``nonlocal``: then
  nothing can alias, mutate or rebind it. Its value must itself be a proof,
  never another name. A program word (an immutable ``str``/``Path``) may be
  read more than once.
* A parameter used as the command makes its module-level function a runner
  when the function only reads the parameter (subscripts, tests, ``len``,
  a returned call, another read-only module function): every call of the
  runner must then pass a proven command, and any other use of its name (an
  argument, an import from another scanned module, an attribute chain such
  as ``pkg.mod._run`` or ``self._run``) is an offender. Another module's
  attribute chain counts unless it resolves to a scanned module without it.
* Locks are off when ``--no-optional-locks`` is among the global options
  before the subcommand, or when ``env=`` is a dict display, ``dict(...)``
  or ``| {...}`` written in the call (or a once-assigned, once-read local
  name bound to one) whose last ``GIT_OPTIONAL_LOCKS`` entry, after every
  ``**`` unpack, is ``"0"``; or a shell ``GIT_OPTIONAL_LOCKS=0`` prefix. The
  environment proofs hold only for a git that starts its own command: a git
  reached through a wrapper program (``env``, ``timeout``, ``xargs``,
  ``sh -c``, any program with ``git`` as a later word) may run in a changed
  environment (``env -u``, ``env -i``), so only the flag covers it.

A literal read subcommand without locks off is never exempt. Any other
offender (a dynamic subcommand or command, an unresolved shell command, a
process function used as a value) may take a ``# lock-lint: ok <reason>``
comment on its reported line; the reason must be non-empty and the scanned
files may hold at most ``_MAX_MARKERS`` markers.
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
# ``git config`` forms that only read a key.
_CONFIG_READS = frozenset({"--get", "--get-all", "--get-regexp", "--list", "-l", "get", "list"})
_WORKTREE_WRITE_ACTIONS = frozenset({"add", "lock", "move", "prune", "remove", "repair", "unlock"})
# Global options whose value is the next argv element.
_GLOBAL_OPTIONS_WITH_VALUE = frozenset({"-C", "-c", "--git-dir", "--work-tree", "--namespace"})


_LOCKS_ENV = "GIT_OPTIONAL_LOCKS"
# Names bound to a data tuple that merely starts with "git" (orient section
# names), so it is not an argv. Every other "git"-led literal is checked.
_NOT_GIT_ARGV = frozenset({"LEAN_ORIENT_SECTIONS"})
# Keyword arguments whose value is data, never an argv (FastAPI ``tags=["git"]``).
_DATA_KEYWORDS = frozenset({"tags"})
_SHELLS = frozenset({"sh", "bash", "dash", "zsh"})

# Process-spawning functions and how each reads its command: an argv (its
# ``shell=`` keyword may turn it into shell text), shell text, an exec-style
# positional argv, or a program path.
_SINKS = {
    "subprocess.run": "argv",
    "subprocess.Popen": "argv",
    "subprocess.call": "argv",
    "subprocess.check_call": "argv",
    "subprocess.check_output": "argv",
    "subprocess.getoutput": "shell",
    "subprocess.getstatusoutput": "shell",
    "os.system": "shell",
    "os.popen": "shell",
    "asyncio.create_subprocess_shell": "shell",
    "asyncio.subprocess.create_subprocess_shell": "shell",
    "asyncio.create_subprocess_exec": "exec",
    "asyncio.subprocess.create_subprocess_exec": "exec",
}
_PROGRAM_SINK = re.compile(r"os\.(?:exec[lv]p?e?|spawn[lv]p?e?|posix_spawnp?)")
_SINK_MODULES = frozenset({"subprocess", "os", "asyncio", "asyncio.subprocess"})
# ``git`` as a word anywhere in a literal. A program other than git that
# carries one (``make --eval 'x:; git status'``, ``gh alias set st 'git status'``)
# may run it, so the call is not proven as a non-git call.
_GIT_WORD = re.compile(r"(?<![\w.-])git(?![\w-])")
# Programs that run commands defined elsewhere (a recipe, a task): proven only
# when every argument is a literal.
_TASK_RUNNERS = frozenset({"make", "just", "task"})

# Verdicts for a call the lint cannot prove: the only ones a
# ``# lock-lint: ok <reason>`` marker may exempt.
_DYNAMIC = "<dynamic>"
_UNRESOLVED_SHELL = "<unresolved shell command>"
_UNPROVEN = "<unproven command>"
_REFERENCE = "<process function used as a value>"
_EXEMPTABLE = frozenset({_UNRESOLVED_SHELL, _UNPROVEN, _REFERENCE})
# Fixed at the scanned files' genuinely dynamic process calls (injected runners, launch
# factories, binary-override seams); a new one must replace one, not add one.
_MAX_MARKERS = 6
_MARKER = re.compile(r"#\s*lock-lint:\s*ok\b(?P<reason>.*)$")
_MAX_DEPTH = 32


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
    rest = tokens[index + 1 :]
    if verb == "config" and any(t and t.startswith("alias.") for t in rest) and not _CONFIG_READS & set(rest):
        return _UNPROVEN  # an alias written here runs a command the lint never sees
    if verb == "worktree":
        action = tokens[index + 1] if index + 1 < len(tokens) else None
        if action in _WORKTREE_WRITE_ACTIONS or covered:
            return None
        return f"worktree {action or _DYNAMIC}"
    if verb in _READ_VERBS:
        return None if covered else verb
    return f"{verb} (unknown subcommand)"


def _exemptable(verdict: str) -> bool:
    return _DYNAMIC in verdict or verdict in _EXEMPTABLE


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


def _basename(path: str) -> str | None:
    return path.rstrip("/").rpartition("/")[2] or None


def _literal_text(item: _Item) -> str | None:
    """The literal text of an argv item, each non-literal part a NUL byte; None when it has none."""
    if item is None or isinstance(item, str):
        return item
    if isinstance(item, (ast.Constant, ast.JoinedStr)) or (
        isinstance(item, ast.BinOp) and isinstance(item.op, ast.Add)
    ):
        return _shell_text(item)
    return None


def _carries_git(items: list[_Item]) -> bool:
    return any(_GIT_WORD.search(text) for text in map(_literal_text, items) if text)


def _indirect_verdicts(program: str, items: list[_Item]) -> list[str]:
    """A ``gh`` alias write, or a task runner with a non-literal argument, runs a command the lint never sees."""
    tokens = [_item_token(item) for item in items]
    if program == "gh" and "alias" in tokens and tokens[1:3] != ["alias", "list"]:
        return [_UNPROVEN]
    if program in _TASK_RUNNERS and any(text is None or "\0" in text for text in map(_literal_text, items[1:])):
        return [_UNPROVEN]
    return []


def _is_command_argv(items: list[_Item] | None) -> bool:
    return bool(items) and _program(items[0]) in {"git", *_SHELLS}


# --- env= --------------------------------------------------------------------
# A mapping's effect on GIT_OPTIONAL_LOCKS: sets it to "0", provably leaves it
# untouched, or anything else (another value, an unknown mapping, a removal).
_ZERO, _ABSENT, _UNKNOWN = "zero", "absent", "unknown"
_SCOPES = (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.ClassDef, ast.Module)
_FUNCTIONS = (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)


def _merge(state: str, later: str) -> str:
    return state if later == _ABSENT else later


def _key_write(key: ast.expr | None, value: ast.expr | None) -> str:
    """The effect of a ``key: value`` entry on GIT_OPTIONAL_LOCKS."""
    if not (isinstance(key, ast.Constant) and isinstance(key.value, str)):
        return _UNKNOWN
    if key.value != _LOCKS_ENV:
        return _ABSENT
    return _ZERO if isinstance(value, ast.Constant) and value.value == "0" else _UNKNOWN


def _display_state(node: ast.expr) -> str:
    """GIT_OPTIONAL_LOCKS in a mapping written out in place; any other expression is unknown."""
    if isinstance(node, ast.Dict):
        state = _ABSENT
        for key, value in zip(node.keys, node.values, strict=True):
            state = _merge(state, _display_state(value) if key is None else _key_write(key, value))
        return state
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "dict":
        if len(node.args) > 1 or any(isinstance(arg, ast.Starred) for arg in node.args):
            return _UNKNOWN
        state = _display_state(node.args[0]) if node.args else _ABSENT
        for keyword in node.keywords:
            if keyword.arg is None:
                later = _display_state(keyword.value)
            elif keyword.arg == _LOCKS_ENV:
                later = _ZERO if isinstance(keyword.value, ast.Constant) and keyword.value.value == "0" else _UNKNOWN
            else:
                later = _ABSENT
            state = _merge(state, later)
        return state
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
        return _merge(_display_state(node.left), _display_state(node.right))
    return _UNKNOWN


def _parameters(args: ast.arguments) -> list[ast.arg]:
    extra = [arg for arg in (args.vararg, args.kwarg) if arg is not None]
    return [*args.posonlyargs, *args.args, *args.kwonlyargs, *extra]


def _binder_name(node: ast.AST) -> str | None:
    """The name a non-``Name`` binding node binds (import, def, class, except, match capture)."""
    if isinstance(node, ast.alias):
        return (node.asname or node.name).split(".")[0]
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        return node.name
    if isinstance(node, ast.ExceptHandler):
        return node.name
    if isinstance(node, (ast.MatchAs, ast.MatchStar)):
        return node.name
    if isinstance(node, ast.MatchMapping):
        return node.rest
    return None


def _is_hasattr_probe(call: ast.AST | None, module: ast.expr) -> bool:
    """``hasattr(os, "O_CLOEXEC")``: a feature probe reads the module and runs nothing."""
    return (
        isinstance(call, ast.Call)
        and isinstance(call.func, ast.Name)
        and call.func.id == "hasattr"
        and call.args[:1] == [module]
    )


class _Lint:
    """Offenders of one Python module."""

    def __init__(self, source: str) -> None:
        self.tree = ast.parse(source)
        self.parents = {child: parent for parent in ast.walk(self.tree) for child in ast.iter_child_nodes(parent)}
        self.aliases: dict[str, str] = {"subprocess": "subprocess", "os": "os", "asyncio": "asyncio"}
        self.offenders: list[tuple[int, str]] = []
        self.claimed: set[int] = set()
        self.runners: dict[str, ast.FunctionDef | ast.AsyncFunctionDef] = {}
        self.obligations: list[tuple[ast.FunctionDef | ast.AsyncFunctionDef, ast.arg, str, str, ast.Name]] = []
        self.functions = self._module_functions()
        # Annotations name types (``subprocess.Popen[bytes]``); they never run a process.
        self.annotations = {
            id(child)
            for node in ast.walk(self.tree)
            for annotation in (getattr(node, "annotation", None), getattr(node, "returns", None))
            if isinstance(annotation, ast.expr)
            for child in ast.walk(annotation)
        }
        for node in ast.walk(self.tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.asname:
                        self.aliases[alias.asname] = alias.name
                    else:
                        root = alias.name.split(".")[0]
                        self.aliases[root] = root
            elif isinstance(node, ast.ImportFrom) and node.module and not node.level:
                for alias in node.names:
                    if alias.name != "*":
                        self.aliases[alias.asname or alias.name] = f"{node.module}.{alias.name}"
                    elif node.module in _SINK_MODULES:
                        self.offenders.append((node.lineno, _REFERENCE))

    # --- scopes -------------------------------------------------------------
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

    def dominates(self, statement: ast.stmt, use: ast.AST, scope: ast.AST) -> bool:
        """``statement`` runs before ``use`` on every path through ``scope``."""
        path, use_path = self.stmt_path(statement, scope), self.stmt_path(use, scope)
        last = len(path) - 1
        return (
            0 <= last < len(use_path)
            and path[:last] == use_path[:last]
            and path[last][:2] == use_path[last][:2]
            and path[last][2] < use_path[last][2]
        )

    def _module_functions(self) -> dict[str, ast.FunctionDef | ast.AsyncFunctionDef]:
        """Module-level functions whose name is bound nowhere else in the module."""
        bindings: dict[str, int] = {}
        for node in ast.walk(self.tree):
            if isinstance(node, ast.Name) and not isinstance(node.ctx, ast.Load):
                name = node.id
            elif isinstance(node, (ast.Global, ast.Nonlocal)):
                for name in node.names:
                    bindings[name] = bindings.get(name, 0) + 2
                continue
            else:
                name = _binder_name(node)
            if name:
                bindings[name] = bindings.get(name, 0) + 1
        return {
            node.name: node
            for node in self.tree.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and bindings.get(node.name) == 1
        }

    def binding(self, name: ast.Name, *, single_load: bool) -> ast.expr | ast.arg | None:
        """The one value a function-local ``name`` holds where it is read, or its parameter.

        The name must be assigned exactly once in its function, by a plain
        single-target assignment that runs before the read, with no other
        store, delete, binding or ``global``/``nonlocal`` declaration anywhere
        in the function, nested scopes included; with ``single_load`` this
        read must be its only read. A parameter is returned as its ``arg``
        when nothing rebinds it.
        """
        scope = self.scope_of(name)
        if not isinstance(scope, _FUNCTIONS):
            return None
        own = {id(arg) for arg in _parameters(scope.args)}
        parameter: ast.arg | None = None
        stores: list[ast.AST] = []
        loads: list[ast.Name] = []
        for node in ast.walk(scope):
            if isinstance(node, ast.Name) and node.id == name.id:
                (loads if isinstance(node.ctx, ast.Load) else stores).append(node)
            elif isinstance(node, (ast.Global, ast.Nonlocal)) and name.id in node.names:
                return None
            elif isinstance(node, ast.arg) and node.arg == name.id:
                if id(node) not in own:
                    return None
                parameter = node
            elif node is not scope and _binder_name(node) == name.id:
                stores.append(node)
        if parameter is not None:
            return None if stores else parameter
        if len(stores) != 1 or (single_load and loads != [name]):
            return None
        store = stores[0]
        statement = self.parents.get(store)
        if (isinstance(statement, ast.Assign) and statement.targets == [store]) or (
            isinstance(statement, ast.AnnAssign) and statement.target is store and statement.value is not None
        ):
            value = statement.value
        else:
            return None
        if self.scope_of(store) is not scope or not self.dominates(statement, name, scope):
            return None
        return value

    # --- runners ------------------------------------------------------------
    def read_only(self, function: ast.AST, name: str, command: ast.AST | None, depth: int) -> bool:
        """Every use of parameter ``name`` in ``function`` only reads it (``command`` aside)."""
        if depth > _MAX_DEPTH:
            return False
        own = {id(arg) for arg in _parameters(function.args)}  # type: ignore[attr-defined]
        for node in ast.walk(function):
            if isinstance(node, (ast.Global, ast.Nonlocal)) and name in node.names:
                return False
            if isinstance(node, ast.arg) and node.arg == name and id(node) not in own:
                return False
            if node is not function and _binder_name(node) == name:
                return False
            if isinstance(node, ast.Name) and node.id == name:
                if not isinstance(node.ctx, ast.Load) or self.scope_of(node) is not function:
                    return False
                if node is not command and not self.read_position(node, depth):
                    return False
        return True

    def read_position(self, node: ast.expr, depth: int) -> bool:
        """``node`` (a list parameter) is read where it cannot be mutated, aliased or kept."""
        parent = self.parents[node]
        if isinstance(parent, ast.Subscript):
            return parent.value is node and isinstance(parent.ctx, ast.Load)
        if isinstance(parent, ast.BoolOp):  # its value may be ``node`` itself
            return self.read_position(parent, depth)
        if isinstance(parent, ast.Compare) or (isinstance(parent, ast.UnaryOp) and isinstance(parent.op, ast.Not)):
            return True
        if isinstance(parent, (ast.If, ast.While, ast.IfExp, ast.Assert)) and parent.test is node:
            return True
        call = self.parents[parent] if isinstance(parent, ast.keyword) else parent
        if not isinstance(call, ast.Call) or call.func is node:
            return False
        if isinstance(self.parents.get(call), ast.Return) or (
            isinstance(call.func, ast.Name) and call.func.id == "len"
        ):
            return True  # the function returns before any later use
        callee = self.functions.get(call.func.id) if isinstance(call.func, ast.Name) else None
        if callee is None or parent is not call or node not in call.args:
            return False
        index = call.args.index(node)
        positional = [*callee.args.posonlyargs, *callee.args.args]
        return index < len(positional) and self.read_only(callee, positional[index].arg, None, depth + 1)

    def runner(self, name: ast.Name, parameter: ast.arg, mode: str, env: str, depth: int) -> list[str]:
        """Defer a parameter command to the callers of its module-level function."""
        function = self.scope_of(name)
        if (
            not isinstance(function, (ast.FunctionDef, ast.AsyncFunctionDef))
            or self.functions.get(function.name) is not function
            or parameter in (function.args.vararg, function.args.kwarg)
            or not self.read_only(function, parameter.arg, name, depth)
        ):
            return [_UNPROVEN]
        self.runners[function.name] = function
        self.obligations.append((function, parameter, mode, env, name))
        return []

    def check_runner_calls(
        self,
        function: ast.FunctionDef | ast.AsyncFunctionDef,
        parameter: ast.arg,
        mode: str,
        env: str,
        command: ast.Name,
    ) -> None:
        """Prove the command each caller passes; a runner used as a value leaves its own call unproven."""
        positional = [*function.args.posonlyargs, *function.args.args]
        with_defaults = positional[len(positional) - len(function.args.defaults) :]
        defaults = dict(zip([arg.arg for arg in with_defaults], function.args.defaults, strict=True))
        defaults.update(
            (arg.arg, default)
            for arg, default in zip(function.args.kwonlyargs, function.args.kw_defaults, strict=True)
            if default is not None
        )
        for node in ast.walk(self.tree):
            if isinstance(node, ast.Attribute) and node.attr == function.name:
                # ``pkg.mod._run(...)`` or ``self._run(...)``: unresolved, so fail closed by name.
                self.offenders.append((node.lineno, _UNPROVEN))
                continue
            if not (isinstance(node, ast.Name) and node.id == function.name and isinstance(node.ctx, ast.Load)):
                continue
            call = self.parents.get(node)
            if not (isinstance(call, ast.Call) and call.func is node):
                self.offenders.append((command.lineno, _UNPROVEN))
                continue
            if any(isinstance(arg, ast.Starred) for arg in call.args) or any(k.arg is None for k in call.keywords):
                self.offenders.append((call.lineno, _UNPROVEN))
                continue
            argument = next((k.value for k in call.keywords if k.arg == parameter.arg), None)
            if argument is None and parameter in positional and positional.index(parameter) < len(call.args):
                argument = call.args[positional.index(parameter)]
            argument = argument or defaults.get(parameter.arg)
            if argument is None:
                self.offenders.append((call.lineno, _UNPROVEN))
                continue
            self.claim(argument)
            self.offenders.extend((argument.lineno, v) for v in self.prove(argument, mode, env, 0))

    # --- proofs -------------------------------------------------------------
    def claim(self, node: ast.AST) -> None:
        self.claimed.update(id(child) for child in ast.walk(node))

    def qualname(self, node: ast.expr) -> str | None:
        if isinstance(node, ast.Name):
            return self.aliases.get(node.id)
        if isinstance(node, ast.Attribute):
            base = self.qualname(node.value)
            return f"{base}.{node.attr}" if base else None
        return None

    def env_state(self, call: ast.Call) -> str:
        for keyword in call.keywords:
            if keyword.arg == "env":
                value = keyword.value
                if isinstance(value, ast.Name):
                    value = self.binding(value, single_load=True)
                    if not isinstance(value, ast.expr) or isinstance(value, ast.Name):
                        return _UNKNOWN
                    self.claim(value)
                return _display_state(value)
        return _UNKNOWN if any(keyword.arg is None for keyword in call.keywords) else _ABSENT

    def program(self, node: _Item, depth: int) -> str | None:
        """The basename of the program a command word names, proven from literals."""
        if depth > _MAX_DEPTH or node is None:
            return None
        if isinstance(node, str):
            return _basename(node)
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return _basename(node.value)
        if isinstance(node, ast.Name):
            value = self.binding(node, single_load=False)
            if not isinstance(value, ast.expr) or isinstance(value, ast.Name):
                return None
            return self.program(value, depth + 1)
        if isinstance(node, ast.Call) and len(node.args) == 1 and not node.keywords:
            wraps = isinstance(node.func, ast.Name) and node.func.id == "str"
            if wraps or self.qualname(node.func) in {"pathlib.Path", "pathlib.PurePath"}:
                return self.program(node.args[0], depth + 1)
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
            return self.program(node.right, depth + 1)
        return None

    def argv_verdicts(self, items: list[_Item], env: str, depth: int) -> list[str]:
        """Verdicts for one argv: its program must be proven, and any git it runs covered."""
        program = self.program(items[0], depth)
        if program is None:
            return [_UNPROVEN]
        tokens = [_item_token(item) for item in items]
        if program == "git":
            verdict = _git_verdict(["git", *tokens[1:]], env_disables_locks=env == _ZERO)
            return [verdict] if verdict is not None else []
        if program in _SHELLS:
            return _shell_argv_verdicts(items, tokens)
        # A wrapper (``timeout 5 git status``, ``env X=1 git log``) runs the git it names.
        # The program word is proven by its basename above; any argument may be a command.
        # The wrapper may change the environment first (``env -u``), so only the flag covers it.
        for index, token in enumerate(tokens[1:], start=1):
            if token is not None and _basename(token) == "git":
                if _carries_git(items[1:index]):
                    return [_UNPROVEN]
                verdict = _git_verdict(["git", *tokens[index + 1 :]])
                return [verdict] if verdict is not None else []
        if _carries_git(items[1:]):
            return [_UNPROVEN]
        return _indirect_verdicts(program, items)

    def prove(self, node: ast.expr, mode: str, env: str, depth: int) -> list[str]:
        """Verdicts for a command expression read in ``mode``; empty when proven."""
        unproven = [_UNRESOLVED_SHELL if mode == "shell" else _UNPROVEN]
        if depth > _MAX_DEPTH:
            return unproven
        if mode == "both":
            return sorted(set(self.prove(node, "argv", env, depth)) | set(self.prove(node, "shell", env, depth)))
        if isinstance(node, ast.Name):
            bound = self.binding(node, single_load=True)
            if isinstance(bound, ast.arg):
                return self.runner(node, bound, mode, env, depth)
            if bound is None or isinstance(bound, ast.Name):
                return unproven
            self.claim(bound)
            return self.prove(bound, mode, env, depth + 1)
        if mode == "shell":
            if isinstance(node, (ast.List, ast.Tuple)):  # POSIX: the first element is the shell text
                if not node.elts or isinstance(node.elts[0], ast.Starred):
                    return unproven
                node = node.elts[0]
            if (
                isinstance(node, ast.JoinedStr)
                or (isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add))
                or (isinstance(node, ast.Constant) and isinstance(node.value, str))
            ):
                return [verdict for _line, verdict in _shell_line_offenders(_shell_text(node), env_state=env)]
            return unproven
        if mode == "program":
            program = self.program(node, depth)
            return [] if program is not None and program != "git" and program not in _SHELLS else unproven
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id in {"list", "tuple"}
            and len(node.args) == 1
            and not node.keywords
            and not isinstance(node.args[0], ast.Starred)
        ):
            return self.prove(node.args[0], mode, env, depth + 1)
        items: list[_Item] | None = (
            [node] if isinstance(node, ast.Constant) and isinstance(node.value, str) else _argv_items(node)
        )
        if not items:
            return unproven
        return self.argv_verdicts(items, env, depth)

    def sink(self, call: ast.Call, name: str) -> None:
        mode = _SINKS.get(name) or "program"
        env = self.env_state(call)
        if mode == "exec":
            self.claim(call)
            if not call.args or isinstance(call.args[0], ast.Starred):
                self.offenders.append((call.lineno, _UNPROVEN))
                return
            items: list[_Item] = [None if isinstance(arg, ast.Starred) else arg for arg in call.args]
            self.offenders.extend((call.lineno, v) for v in self.argv_verdicts(items, env, 0))
            return
        index = 1 if mode == "program" and ".spawn" in name else 0
        command = call.args[index] if len(call.args) > index else None
        if command is None and mode != "program":
            command = next((k.value for k in call.keywords if k.arg in {"args", "cmd"}), None)
        if command is None or isinstance(command, ast.Starred):
            self.offenders.append((call.lineno, _UNPROVEN))
            return
        if mode == "argv":
            shell = next((k.value for k in call.keywords if k.arg == "shell"), None)
            if isinstance(shell, ast.Constant):
                mode = "shell" if shell.value else "argv"
            elif shell is not None or any(k.arg is None for k in call.keywords):
                mode = "both"
        self.claim(command)
        verdicts = self.prove(command, mode, env, 0)
        if mode == "program" and not verdicts:
            # ``os.execlp(file, arg0, *args)`` passes its argv positionally, ``os.execvp(file, argv)`` as one list.
            if re.fullmatch(r"os\.(?:exec|spawn)l.*", name):
                arguments: list[_Item] | None = [
                    None if isinstance(arg, ast.Starred) else arg for arg in call.args[index + 1 :]
                ]
            else:
                arguments = _argv_items(call.args[index + 1]) if len(call.args) > index + 1 else None
            if arguments:
                verdicts = self.argv_verdicts([command, *arguments[1:]], env, 0)
        self.offenders.extend((command.lineno, v) for v in verdicts)

    def sinks(self) -> Iterator[tuple[ast.Call, str]]:
        """Each process-spawning call; a process function or module used as a value is an offender."""
        for node in ast.walk(self.tree):
            if not (isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load) and node.id in self.aliases):
                continue
            if id(node) in self.annotations:
                continue
            top: ast.expr = node
            while isinstance(parent := self.parents.get(top), ast.Attribute) and parent.value is top:
                top = parent
            name = self.qualname(top) or ""
            spawns = name in _SINKS or _PROGRAM_SINK.fullmatch(name)
            if not spawns and name not in _SINK_MODULES:
                continue
            call = self.parents.get(top)
            if spawns and isinstance(call, ast.Call) and call.func is top:
                yield call, name
            elif not spawns and _is_hasattr_probe(call, top):
                continue
            else:
                self.offenders.append((top.lineno, _REFERENCE))

    def run(self) -> list[tuple[int, str]]:
        for node in ast.walk(self.tree):
            if isinstance(node, (ast.Assign, ast.AnnAssign)) and node.value is not None:
                targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                if any(isinstance(t, ast.Name) and t.id in _NOT_GIT_ARGV for t in targets):
                    self.claim(node.value)
            elif isinstance(node, ast.keyword) and node.arg in _DATA_KEYWORDS:
                self.claim(node.value)
        for call, name in list(self.sinks()):
            self.sink(call, name)
        seen: set[tuple[int, int, str, str]] = set()
        while self.obligations:
            function, parameter, mode, env, command = self.obligations.pop()
            key = (id(function), id(parameter), mode, env)
            if key not in seen:
                seen.add(key)
                self.check_runner_calls(function, parameter, mode, env, command)
        # Every other git argv literal, wherever it is built (breadth-first:
        # an outer argv before its parts).
        for node in ast.walk(self.tree):
            if id(node) in self.claimed or not isinstance(node, ast.expr):
                continue
            items = _argv_items(node)
            if _is_command_argv(items):
                self.claim(node)
                self.offenders.extend((node.lineno, v) for v in _literal_argv_verdicts(items, _ABSENT))
            elif isinstance(node, ast.Call) and node.args and _item_token(node.args[0]) == "git" and len(node.args) > 1:
                # exec-style: run_git("git", "status", ...)
                self.claim(node)
                exec_items: list[_Item] = [None if isinstance(a, ast.Starred) else a for a in node.args]
                self.offenders.extend((node.lineno, v) for v in _literal_argv_verdicts(exec_items, _ABSENT))
        return self.offenders


# --- shell text ------------------------------------------------------------
# A ``git`` at command position (also inside quotes, for ``sh -c 'git ...'``),
# with any ``NAME=value`` env prefix, its global options and the next two
# words (the subcommand and a worktree action).
_SHELL_GIT = re.compile(
    r"(?:^|[\s;&|(`$'\"])"
    r"(?P<env>(?:[A-Za-z_][A-Za-z0-9_]*=[^\s;&|]*\s+)*)"
    r"(?P<git>git)[\"']?"
    r"(?P<options>(?:\s+(?:-[Cc]|--git-dir|--work-tree|--namespace)\s+\S+|\s+-\S+)*)"
    r"\s+(?P<verb>[^\s;&|)`]+)"
    r"(?:\s+(?P<action>[^\s;&|)`]+))?"
)
_SHELL_WORD = re.compile(r"[a-z][\w.-]*")
# A non-literal part (rendered NUL) at command position: the command run is unknown.
_COMMAND_PLACEHOLDER = re.compile(
    r"(?:^|[;&|(`\n]|\$\()\s*"
    r"(?:[A-Za-z_][A-Za-z0-9_]*=[^\s;&|]*\s+)*"
    r"(?:(?:command|env|exec|nohup|sudo|time|xargs|then|do|else)\s+)*"
    r"[\"']?\0"
)
# A ``gh`` alias write, or a task runner with a non-literal argument, at command position.
_SHELL_INDIRECT = re.compile(
    r"(?:^|[;&|(`\n]|\$\()\s*"
    r"(?:[A-Za-z_][A-Za-z0-9_]*=[^\s;&|]*\s+)*"
    r"(?:(?:command|env|exec|nohup|sudo|time|xargs|then|do|else)\s+)*"
    r"(?:gh\s+alias\s+(?!list\b)|(?:make|just|task)\b[^;&|\n]*\0)"
)
# Where the words of the git command a match starts end.
_SHELL_COMMAND_END = re.compile(r"[;&|)`\n]")
# Text that ends where a simple command starts (a separator, a group or a reserved word).
_COMMAND_START = re.compile(r"(?:^|[;&|(`{!\n]|(?<![\w.-])(?:then|do|else|elif|if|while|until))\s*$")


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


def _lone_command(code: str, word: re.Match[str]) -> bool:
    """``word`` is the only word of its command."""
    before = code[: word.start()]
    begin = max((m.end() for m in re.finditer(r"[;&|(`\n]", before)), default=0)
    end = _SHELL_COMMAND_END.search(code, word.end())
    after = code[word.end() : end.start() if end else len(code)]
    return not before[begin:].strip(" \t\"'") and not after.strip(" \t\"'")


def _runs_directly(code: str, match: re.Match[str]) -> bool:
    """The git of ``match`` starts its simple command outside quotes, so no wrapper program
    (``env -i``, ``timeout``, ``xargs``, ``sh -c '...'``) can change its environment first."""
    head = code[: match.start("env")]
    if head.endswith(("'", '"')):
        head = head[:-1]  # a quoted program word: ``"git" status``
    if not _COMMAND_START.search(head):
        return False
    inner = re.split(r"\$\(|`", head)[-1]  # a substitution opens a new quoting context
    return inner.count("'") % 2 == 0 and inner.count('"') % 2 == 0


def _shell_line_offenders(source: str, *, env_state: str = _ABSENT, wrapped: bool = False) -> list[tuple[int, str]]:
    """Offenders of shell text; ``wrapped`` text (``sh -c <text>``) runs every git through a wrapper."""
    offenders: list[tuple[int, str]] = []
    # The call's env= counts only when the text never touches the variable itself.
    inherited = env_state if _LOCKS_ENV not in source else _UNKNOWN
    # Every character is read: no comment is stripped, since telling a comment from a quoted
    # or expanded ``#`` needs a shell parser. A git word in a real comment counts as a command.
    for lineno, code in enumerate(source.splitlines(), start=1):
        if _COMMAND_PLACEHOLDER.search(code) or _SHELL_INDIRECT.search(code):
            offenders.append((lineno, _UNRESOLVED_SHELL))
        # Each git command read below, from its ``git`` to the end of its words.
        spans = [
            (match.start("git"), (end.start() if (end := _SHELL_COMMAND_END.search(code, match.end())) else len(code)))
            for match in _SHELL_GIT.finditer(code)
        ]
        # A ``git`` word outside them (``/usr/bin/git status``, ``X=git``, ``xargs git``) runs a
        # git the lint cannot read; ``git`` alone as a whole command runs no subcommand.
        if any(
            not any(start <= word.start() < end for start, end in spans) and not _lone_command(code, word)
            for word in _GIT_WORD.finditer(code)
        ):
            offenders.append((lineno, _UNRESOLVED_SHELL))
        for match in _SHELL_GIT.finditer(code):
            if wrapped or not _runs_directly(code, match):
                effective = _ABSENT  # only the flag covers a git a wrapper runs
            else:
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
def _shell_argv_verdicts(items: list[_Item], tokens: list[str | None]) -> list[str]:
    """Verdicts for ``sh [options] -c <text>``; a script file runs no inline git.

    The shell is a wrapper: each git in its text needs the flag, whatever the environment.
    Any other element that carries a ``git`` word (``sh -c '"$@"' _ git status``) is unproven.
    """
    verdicts: list[str] = []
    text_index = None
    for index, token in enumerate(tokens[1:], start=1):
        if token is None or not token.startswith("-"):
            verdicts = [_UNRESOLVED_SHELL] if token is None else []  # a script file, or unknown options
            break
        if "c" in token.lstrip("-") and not token.startswith("--"):
            text_index = index + 1
            text = _shell_text(items[text_index]) if text_index < len(items) else "\0"
            verdicts = [verdict for _line, verdict in _shell_line_offenders(text, wrapped=True)]
            break
    if _carries_git([item for index, item in enumerate(items[1:], start=1) if index != text_index]):
        verdicts.append(_UNPROVEN)
    return verdicts


def _literal_argv_verdicts(items: list[_Item], env_state: str) -> list[str]:
    """Verdicts for a literal argv outside a process call whose program is ``git`` or a shell."""
    tokens = [_item_token(item) for item in items]
    if _program(items[0]) == "git":
        verdict = _git_verdict(tokens, env_disables_locks=env_state == _ZERO)
        return [verdict] if verdict is not None else []
    return _shell_argv_verdicts(items, tokens)


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


def _exempt(offenders: list[tuple[int, str]], source: str) -> list[tuple[int, str]]:
    markers = _python_markers(source)
    return sorted({(n, v) for n, v in offenders if not (_exemptable(v) and markers.get(n, "").strip())})


def git_calls_without_flag(source: str) -> list[tuple[int, str]]:
    """Return (lineno, verdict) for each git invocation or process call that fails the gate."""
    return _exempt(_Lint(source).run(), source)


def runner_names(source: str) -> set[str]:
    """Module-level functions whose callers the lint checks in place of their process call."""
    lint = _Lint(source)
    lint.run()
    return set(lint.runners)


def _attribute_path(node: ast.expr, modules: dict[str, str]) -> str | None:
    """The dotted module path an attribute chain's object names (``a.b.c`` for ``a.b.c.f``), via imports."""
    parts: list[str] = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if not isinstance(node, ast.Name) or node.id not in modules:
        return None
    return ".".join([modules[node.id], *reversed(parts)])


def foreign_runner_uses(source: str, runners: dict[str, set[str]]) -> list[tuple[int, str]]:
    """Uses of another scanned module's runner, whose callers here the lint cannot check.

    ``runners`` maps every other scanned module's stem to its runner names. An
    attribute chain ending in a runner name that does not resolve to a scanned
    module (``self._run``, ``load()._run``, an unscanned module) counts as a use.
    """
    tree = ast.parse(source)
    # Each imported name and the dotted module path it binds (``import a.b.c`` binds ``a``).
    modules: dict[str, str] = {}
    offenders: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                bound = alias.name if alias.asname else alias.name.split(".")[0]
                modules[alias.asname or bound] = bound
        elif isinstance(node, ast.ImportFrom):
            prefix = "." * node.level + (f"{node.module}." if node.module else "")
            stem = (node.module or "").rpartition(".")[2]
            for alias in node.names:
                if alias.name in runners.get(stem, set()) or (alias.name == "*" and stem in runners):
                    offenders.append((node.lineno, _REFERENCE))
                modules[alias.asname or alias.name] = prefix + alias.name
    names = set().union(*runners.values()) if runners else set()
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Attribute) and node.attr in names):
            continue
        path = _attribute_path(node.value, modules)
        stem = path.rpartition(".")[2] if path else None
        if stem not in runners or node.attr in runners[stem]:
            offenders.append((node.lineno, _REFERENCE))
    return _exempt(offenders, source)


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
    sources = {path: path.read_text(encoding="utf-8") for path in _scanned_python_files()}
    runners = {path.stem: runner_names(source) for path, source in sources.items()}
    for path, source in sources.items():
        foreign = {stem: names for stem, names in runners.items() if stem != path.stem}
        found = git_calls_without_flag(source) + foreign_runner_uses(source, foreign)
        offenders.extend(f"{path.relative_to(_REPO_ROOT)}:{lineno} git {verb}" for lineno, verb in found)
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
        # Commands the lint cannot prove fail closed (review r3, case 1 and its family).
        "subprocess.run(command)",
        "subprocess.run(shlex.split(command))",
        "subprocess.run(command.split())",
        "subprocess.run([*parts])",
        "subprocess.run(commands['status'])",
        "subprocess.run(self.command)",
        "subprocess.run(build_command())",
        "subprocess.run(prefix + ['status'])",
        "subprocess.Popen([tool, 'status'])",
        "asyncio.create_subprocess_exec(*argv)",
        "os.execvp(program, argv)",
        "os.popen(command)",
        # A wrapper or a quoted shell still runs git.
        'subprocess.run(["timeout", "5", "git", "status"])',
        'subprocess.run(["env", "LANG=C", "/usr/bin/git", "log"])',
        "subprocess.run(\"sh -c 'git status'\", shell=True)",
        'subprocess.run(["bash", "-lc", "cd x && \\"git\\" log"])',
        # A process function or module used as a value.
        "functools.partial(subprocess.run, check=True)",
        'getattr(subprocess, "run")',
        "subprocess.run",
        "loop.run_in_executor(None, subprocess.check_output, argv)",
        # Review r4, case 2: a program other than git that carries a git word, a gh
        # alias write, a task runner with a non-literal target, a git alias write.
        'subprocess.run(["make", "--eval", "probe:; git status --porcelain", "probe"])',
        'subprocess.run(["gh", "alias", "set", "--shell", "st", "git status --porcelain"])',
        'subprocess.run(["gh", "alias", "set", "st", "pr status"])',
        'subprocess.run(["gh", "alias", "import", path])',
        'subprocess.run(["timeout", "5", "make", "--eval", "x:; git status", "x"])',
        'subprocess.run(["python", "-c", "import subprocess; subprocess.run([\'git\', \'status\'])"])',
        'subprocess.run(["sh", "-c", \'"$@"\', "_", "git", "status"])',
        'subprocess.run(["env", "X=git", "git", "--no-optional-locks", "status"])',
        'subprocess.run(["make", target])',
        'subprocess.run(["just", f"probe-{name}"])',
        'subprocess.run(["task", "--dir", str(path), "probe"])',
        'subprocess.run(["git", "--no-optional-locks", "config", "alias.st", "!git status"])',
        'os.execvp("make", ["make", "--eval", "x:; git status", "x"])',
        'os.execlp("gh", "gh", "alias", "set", "st", "git status")',
        'subprocess.run("/usr/bin/git status", shell=True)',
        'subprocess.run("echo status | xargs git", shell=True)',
        "subprocess.run(\"make --eval 'x:; git status' x\", shell=True)",
        'subprocess.run(f"make {target}", shell=True)',
        "subprocess.run(\"gh alias set st 'pr status'\", shell=True)",
        "subprocess.run(\"git --no-optional-locks config alias.st '!git status'\", shell=True)",
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
        # Non-git programs with dynamic arguments, and the names a module may use.
        'subprocess.run(["du", "-sk", str(path)], capture_output=True)',
        'subprocess.run(["gh", "pr", "list", "--limit", str(limit)])',
        'subprocess.run(["/bin/launchctl", *command])',
        'subprocess.run(["git", "--no-optional-locks", *args], env=sanitized_git_env())',
        'os.system("echo ok")',
        'os.execvp("python", argv)',
        "subprocess.PIPE",
        "subprocess.CompletedProcess(args=args, returncode=0)",
        'os.environ.get("HOME")',
        "asyncio.subprocess.PIPE",
        # Literal task-runner targets, read-only gh calls and git-free arguments.
        'subprocess.run(["make", "-C", "docs", "html"])',
        'subprocess.run(["gh", "alias", "list"])',
        'subprocess.run(["gh", "api", "repos/o/r/pulls", "--jq", ".[].title"])',
        'subprocess.run(["python", "-m", "scripts.git_tool", "--help"])',
        'subprocess.run(["rg", "-l", "github", ".gitignore"])',
        'os.execvp("python", ["python", "-m", "http.server"])',
        'subprocess.run("make html", shell=True)',
        'subprocess.run("git", shell=True)',
        'subprocess.run("git --no-optional-locks config --get alias.st", shell=True)',
    ],
)
def test_lint_accepts_flagged_and_write_calls(snippet: str) -> None:
    assert git_calls_without_flag(f"cmd = {snippet}\n") == []


def test_lint_reports_a_git_prefix_reused_by_unpacking() -> None:
    source = 'prefix = ["git", "-C", repo]\nsubprocess.run([*prefix, "status"])\n'
    assert git_calls_without_flag(source) == [(1, _DYNAMIC), (2, _UNPROVEN)]
    # A spliced name proves no program, flag or not.
    flagged = 'prefix = ["git", "--no-optional-locks", "-C", repo]\nsubprocess.run([*prefix, "status"])\n'
    assert git_calls_without_flag(flagged) == [(2, _UNPROVEN)]


_HEADER = "import os\nimport shlex\nimport subprocess\nfrom pathlib import Path\n\n\n"


def _in_function(body: str) -> str:
    return (
        _HEADER
        + "def run(repos, extra, cond, key, root, path, limit):\n"
        + "".join(f"    {line}\n" for line in body.splitlines())
    )


def _verdicts(source: str) -> list[str]:
    return [verdict for _line, verdict in git_calls_without_flag(source)]


@pytest.mark.parametrize(
    "body",
    [
        'env = {**os.environ, "GIT_OPTIONAL_LOCKS": "0"}\nsubprocess.run(["git", "status"], env=env)',
        'env = dict(os.environ, GIT_OPTIONAL_LOCKS="0")\nsubprocess.run(["git", "status"], env=env)',
        'env: dict[str, str] = {**os.environ, "LANG": "C", "GIT_OPTIONAL_LOCKS": "0"}\n'
        'subprocess.run(["git", "status"], env=env)',
        'env = os.environ | {"GIT_OPTIONAL_LOCKS": "0"}\nfor repo in repos:\n'
        '    subprocess.run(["git", "-C", repo, "status"], env=env)',
        'cmd = ["git", "--no-optional-locks", "status"]\nsubprocess.run(cmd, check=False)',
        'command = ["git", "-C", root, "--no-optional-locks", "archive", key]\n'
        "process = subprocess.Popen(command, stdout=subprocess.PIPE)",
        'cmd = ["git", "status"]\nsubprocess.run(cmd, env={**os.environ, "GIT_OPTIONAL_LOCKS": "0"})',
        'text = "git --no-optional-locks status"\nsubprocess.run(text, shell=True)',
        'script = root / "scripts" / "audit_module.sh"\nsubprocess.run([str(script), str(path)])',
        'tool = Path("/usr/bin/security")\nif tool.is_file():\n    subprocess.run([str(tool), "find"])',
        'cmd = ["gh", "issue", "list", "--limit", str(limit)]\nsubprocess.run(cmd)',
    ],
)
def test_lint_accepts_proven_function_locals(body: str) -> None:
    assert git_calls_without_flag(_in_function(body)) == []


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
        # Built in statements, even when every statement sets "0" (only a
        # once-assigned, once-read display is a proof).
        'env = os.environ.copy()\nenv["GIT_OPTIONAL_LOCKS"] = "0"\nsubprocess.run(["git", "status"], env=env)\n',
        'env = dict(os.environ)\nenv.update({"GIT_OPTIONAL_LOCKS": "0"})\nsubprocess.run(["git", "status"], env=env)\n',
        'env = {**os.environ}\nenv.update(GIT_OPTIONAL_LOCKS="0", LANG="C")\nsubprocess.run(["git", "status"], env=env)\n',
        'env = os.environ.copy()\nenv |= {"GIT_OPTIONAL_LOCKS": "0"}\nsubprocess.run(["git", "status"], env=env)\n',
        'base = {**os.environ, "GIT_OPTIONAL_LOCKS": "0"}\nenv = {**base, "LANG": "C"}\n'
        'subprocess.run(["git", "status"], env=env)\n',
        # Review r3, case 2: a mutated alias, at any depth.
        'env = {**os.environ, "GIT_OPTIONAL_LOCKS": "0"}\nchild_env = env\nchild_env["GIT_OPTIONAL_LOCKS"] = "1"\n'
        'subprocess.run(["git", "status"], env=env)\n',
        'env = {**os.environ, "GIT_OPTIONAL_LOCKS": "0"}\na = env\nb = a\nc = b\nc.update(extra)\n'
        'subprocess.run(["git", "status"], env=env)\n',
        # Passed to a helper that may change it, aliased, read twice or assigned twice.
        'env = {**os.environ, "GIT_OPTIONAL_LOCKS": "0"}\nharden(env)\nsubprocess.run(["git", "status"], env=env)\n',
        'env = {**os.environ, "GIT_OPTIONAL_LOCKS": "0"}\nchild_env = env\nsubprocess.run(["git", "status"], env=child_env)\n',
        'env = {**os.environ, "GIT_OPTIONAL_LOCKS": "0"}\nprint(env)\nsubprocess.run(["git", "status"], env=env)\n',
        'env = {**os.environ, "GIT_OPTIONAL_LOCKS": "0"}\nenv = {**env, "LANG": "C"}\n'
        'subprocess.run(["git", "status"], env=env)\n',
        'env = {**os.environ, "GIT_OPTIONAL_LOCKS": "0"}\n'
        "def poison():\n    nonlocal env\n    env = {}\npoison()\n"
        'subprocess.run(["git", "status"], env=env)\n',
        'for env in ({"GIT_OPTIONAL_LOCKS": "0"}, extra):\n    subprocess.run(["git", "status"], env=env)\n',
        'with make_env() as env:\n    subprocess.run(["git", "status"], env=env)\n',
    ],
)
def test_lint_flags_env_overridden_in_statements(body: str) -> None:
    assert _verdicts(_in_function(body)) == ["status"]


@pytest.mark.parametrize(
    "body",
    [
        # Review r3, case 1.
        'cmd = "git status --porcelain"\nsubprocess.run(shlex.split(cmd))',
        'cmd = "git status --porcelain"\nsubprocess.run(cmd.split())',
        'cmd = "git status"\nparts = cmd.split()\nsubprocess.run([*parts])',
        'commands = {"status": "git status"}\nsubprocess.run(shlex.split(commands["status"]))',
        "subprocess.run(build_command(root))",
        "subprocess.run(extra.command)",
        # A command list mutated through an alias, at any depth, or reassigned.
        'cmd = ["git", "push"]\nalias = cmd\nalias[1] = "status"\nsubprocess.run(cmd)',
        'cmd = ["git", "push"]\na = cmd\nb = a\nc = b\nc.insert(1, "status")\nsubprocess.run(cmd)',
        'cmd = ["git", "--no-optional-locks", "status"]\nalias = cmd\nsubprocess.run(alias)',
        'cmd = ["git", "push"]\ncmd.append("--dry-run")\nsubprocess.run(cmd)',
        'cmd = ["git", "push"]\nprepare(cmd)\nsubprocess.run(cmd)',
        'for cmd in (["git", "push"], extra):\n    subprocess.run(cmd)',
        'cmd = ["git", "push"]\nif cond:\n    cmd = extra\nsubprocess.run(cmd)',
        'if cond:\n    cmd = ["git", "push"]\nsubprocess.run(cmd)',
        # A program word the lint cannot prove.
        'lsof = os.environ.get("SVC_LSOF_BIN", "lsof")\nsubprocess.run([lsof, "-p", key])',
        "subprocess.run([root, 'status'])",
        "subprocess.run([str(path), 'status'])",
    ],
)
def test_lint_flags_unproven_commands(body: str) -> None:
    assert _UNPROVEN in _verdicts(_in_function(body))


def test_review_r3_reproductions_are_flagged() -> None:
    split = 'import shlex\nimport subprocess\n\ncmd = "git status --porcelain"\nsubprocess.run(shlex.split(cmd))\n'
    assert git_calls_without_flag(split) == [(5, _UNPROVEN)]
    alias = (
        "import os\nimport subprocess\n\n"
        'env = {**os.environ, "GIT_OPTIONAL_LOCKS": "0"}\n'
        "child_env = env\n"
        'child_env["GIT_OPTIONAL_LOCKS"] = "1"\n'
        'subprocess.run(["git", "status"], env=env)\n'
    )
    assert git_calls_without_flag(alias) == [(7, "status")]


_LOCKS_OFF = 'env=dict(os.environ, GIT_OPTIONAL_LOCKS="0")'


@pytest.mark.parametrize(
    "argv",
    [
        # Review r5: the wrapper changes the environment the call's env= proved.
        '["env", "GIT_OPTIONAL_LOCKS=1", "git", "status", "--porcelain"]',
        '["env", "-u", "GIT_OPTIONAL_LOCKS", "git", "status", "--porcelain"]',
        '["env", "GIT_OPTIONAL_LOCKS=0", "git", "status"]',
        '["env", "-i", "git", "status"]',
        '["timeout", "5", "git", "status"]',
        '["nice", "git", "status"]',
        '["xargs", "git", "status"]',
        '["sh", "-c", "git status"]',
        '["sh", "-c", "GIT_OPTIONAL_LOCKS=0 git status"]',
        '["bash", "-c", "cd x && git log -1"]',
        '"env -u GIT_OPTIONAL_LOCKS git status"',
        '"env -i git status"',
        '"timeout 5 git status"',
        '"nice git status"',
        '"echo HEAD | xargs git rev-parse"',
        "\"sh -c 'git status'\"",
        "\"cd x && bash -c 'cd y && git status'\"",
    ],
)
def test_review_r5_wrapper_programs_need_the_flag(argv: str) -> None:
    shell = ", shell=True" if argv.startswith('"') else ""
    assert len(git_calls_without_flag(f"cmd = subprocess.run({argv}, {_LOCKS_OFF}{shell})\n")) == 1
    flagged = argv.replace("git ", "git --no-optional-locks ").replace('"git", ', '"git", "--no-optional-locks", ')
    assert git_calls_without_flag(f"cmd = subprocess.run({flagged}, {_LOCKS_OFF}{shell})\n") == []


@pytest.mark.parametrize(
    "command",
    [
        '["git", "status"]',
        '"git status"',
        '"cd x && git status"',
        '"if git diff --quiet; then :; fi"',
        '"head=\\"$(git rev-parse HEAD)\\""',
        '"echo \\"a b\\" && \\"git\\" status"',
    ],
)
def test_lint_accepts_env_for_a_git_that_starts_its_command(command: str) -> None:
    shell = ", shell=True" if command.startswith('"') else ""
    assert git_calls_without_flag(f"cmd = subprocess.run({command}, {_LOCKS_OFF}{shell})\n") == []


@pytest.mark.parametrize(
    "imports,call",
    [
        ("import subprocess as sp", 'sp.run(["git", "status"])'),
        ("from subprocess import run", 'run(["git", "status"])'),
        ("from subprocess import check_output as out", "out(command)"),
        ("from os import system", "system(command)"),
        ("from asyncio import subprocess as aio", "aio.create_subprocess_exec(*argv)"),
        ("import asyncio.subprocess", "asyncio.subprocess.create_subprocess_shell(command)"),
        ("from subprocess import *", 'print("x")'),
        ("from subprocess import run", "spawn = run"),
    ],
)
def test_lint_follows_import_aliases(imports: str, call: str) -> None:
    # ``command`` and ``argv`` are module names here, so nothing proves them.
    assert len(git_calls_without_flag(f"{imports}\n\ndef f():\n    {call}\n")) == 1


def test_lint_rejects_module_level_env() -> None:
    covered = '_ENV = {**os.environ, "GIT_OPTIONAL_LOCKS": "0"}\n\ndef run():\n    subprocess.run(["git", "status"], env=_ENV)\n'
    assert git_calls_without_flag(covered) == [(4, "status")]
    mutated = covered + '\ndef poison():\n    _ENV["GIT_OPTIONAL_LOCKS"] = "1"\n'
    assert git_calls_without_flag(mutated) == [(4, "status")]
    rebound = covered + "\ndef rebind():\n    global _ENV\n    _ENV = {}\n"
    assert git_calls_without_flag(rebound) == [(4, "status")]


_RUNNER = (
    "import asyncio\nimport shlex\nimport subprocess\n\n\n"
    "def _cwd(cmd):\n"
    '    return "repo" if cmd and cmd[0] == "git" else "project"\n\n\n'
    "def _run(cmd, *, timeout=2.0):\n"
    "    if not len(cmd):\n"
    "        return subprocess.CompletedProcess(args=cmd, returncode=2)\n"
    "    try:\n"
    "        return subprocess.run(cmd, cwd=_cwd(cmd), timeout=timeout)\n"
    "    except OSError:\n"
    "        return subprocess.CompletedProcess(args=cmd, returncode=127)\n\n\n"
)
_CALLER_LINE = _RUNNER.count("\n") + 2
_SINK_LINE = _RUNNER.splitlines().index("        return subprocess.run(cmd, cwd=_cwd(cmd), timeout=timeout)") + 1


@pytest.mark.parametrize(
    "caller,expected",
    [
        ('_run(["git", "--no-optional-locks", "status"])', []),
        ('_run(cmd=["gh", "pr", "list"], timeout=5.0)', []),
        ('_run(["git", "status"])', [(_CALLER_LINE, "status")]),
        ('_run(["git", "push", "origin"])', []),
        ("_run(shlex.split(text))", [(_CALLER_LINE, _UNPROVEN)]),
        ("_run(*argv)", [(_CALLER_LINE, _UNPROVEN)]),
        # A runner used as a value runs commands the lint never sees.
        ('asyncio.to_thread(_run, ["git", "--no-optional-locks", "status"])', [(_SINK_LINE, _UNPROVEN)]),
        ("handlers = {'run': _run}", [(_SINK_LINE, _UNPROVEN)]),
    ],
)
def test_lint_checks_every_runner_caller(caller: str, expected: list[tuple[int, str]]) -> None:
    source = _RUNNER + f"def caller(text, argv):\n    {caller}\n"
    assert git_calls_without_flag(source) == expected
    assert runner_names(source) == {"_run"}


def test_lint_follows_runner_chains_and_shell_runners() -> None:
    chained = _RUNNER + 'def _gh(args):\n    return _run(args)\n\n\n_gh(["git", "log"])\n_gh(["gh", "pr", "list"])\n'
    assert _verdicts(chained) == ["log"]
    assert runner_names(chained) == {"_run", "_gh"}
    shell = "import subprocess\n\n\ndef sh(text):\n    return subprocess.run(text, shell=True)\n\n\nsh('git status')\nsh('ls')\n"
    assert git_calls_without_flag(shell) == [(8, "status")]


@pytest.mark.parametrize(
    "runner",
    [
        # The runner changes, keeps or rebinds the command it is given.
        "def _run(cmd):\n    cmd[1] = 'status'\n    return subprocess.run(cmd)\n",
        "def _run(cmd):\n    cmd.insert(1, 'status')\n    return subprocess.run(cmd)\n",
        "def _run(cmd):\n    _prep(cmd)\n    return subprocess.run(cmd)\n\n\ndef _prep(cmd):\n    cmd.append('x')\n",
        "def _run(cmd):\n    alias = cmd\n    return subprocess.run(cmd)\n",
        "def _run(cmd):\n    cmd = cmd + ['status']\n    return subprocess.run(cmd)\n",
        "def _run(cmd):\n    hook(cmd)\n    return subprocess.run(cmd)\n",
        "def _run(*cmd):\n    return subprocess.run(cmd)\n",
        # A method or nested function's callers cannot be resolved statically.
        "class Runner:\n    def run(self, cmd):\n        return subprocess.run(cmd)\n",
        "def outer():\n    def _run(cmd):\n        return subprocess.run(cmd)\n    return _run\n",
        # A function name bound twice is not one function.
        "def _run(cmd):\n    return subprocess.run(cmd)\n\n\n_run = wrap(_run)\n",
    ],
)
def test_lint_flags_runners_that_do_not_only_read_the_command(runner: str) -> None:
    source = f"import subprocess\n\n\n{runner}\n\n_run(['git', 'push'])\n"
    assert _verdicts(source) == [_UNPROVEN]


def test_foreign_runner_uses_are_flagged() -> None:
    runners = {"site_router": {"_run"}}
    assert foreign_runner_uses("from .site_router import _run\n", runners) == [(1, _REFERENCE)]
    assert foreign_runner_uses("from scripts.api.site_router import _run as run\n", runners) == [(1, _REFERENCE)]
    assert foreign_runner_uses("from . import site_router as sr\nsr._run(cmd)\n", runners) == [(2, _REFERENCE)]
    assert foreign_runner_uses("import scripts.api.site_router as sr\nsr._run(cmd)\n", runners) == [(2, _REFERENCE)]
    assert foreign_runner_uses("from .site_router import *\n", runners) == [(1, _REFERENCE)]
    assert foreign_runner_uses("from .other import _run\nself.run(cmd)\n", runners) == []


def test_review_r4_dotted_import_runner_call_is_flagged() -> None:
    runners = {"site_router": {"_run"}}
    reproduction = (
        "import scripts.api.site_router\nimport shlex\n"
        'text = "git status --porcelain"\n'
        "scripts.api.site_router._run(shlex.split(text))\n"
    )
    assert foreign_runner_uses(reproduction, runners) == [(4, _REFERENCE)]


@pytest.mark.parametrize(
    "source",
    [
        "import scripts.api\nscripts.api.site_router._run(cmd)\n",
        "from scripts import api\napi.site_router._run(cmd)\n",
        "import scripts.api.site_router as sr\nrun = sr._run\n",
        # An attribute chain that resolves to no scanned module fails closed by name.
        'import importlib\nimportlib.import_module("scripts.api.site_router")._run(cmd)\n',
        "from .other import _run\nself._run(cmd)\n",
        "import scripts.api.unscanned\nscripts.api.unscanned._run(cmd)\n",
    ],
)
def test_dotted_and_unresolved_runner_chains_are_flagged(source: str) -> None:
    runners = {"site_router": {"_run"}, "other": set()}
    assert foreign_runner_uses(source, runners) == [(2, _REFERENCE)]


def test_runner_chain_resolved_to_a_module_without_it_is_not_flagged() -> None:
    runners = {"site_router": {"_run"}, "other": set()}
    assert foreign_runner_uses("import scripts.api.other\nscripts.api.other._run(cmd)\n", runners) == []
    assert foreign_runner_uses("from scripts.api import other\nother._run(cmd)\n", runners) == []


@pytest.mark.parametrize(
    "caller",
    [
        'self._run(["git", "--no-optional-locks", "status"])',
        'scripts.api.site_router._run(["git", "--no-optional-locks", "status"])',
    ],
)
def test_lint_flags_runner_calls_through_attribute_chains_in_its_own_module(caller: str) -> None:
    source = _RUNNER + f"def caller(self):\n    {caller}\n"
    assert git_calls_without_flag(source) == [(_CALLER_LINE, _UNPROVEN)]


def test_marker_exempts_only_unresolved_subcommands_with_a_reason() -> None:
    dynamic = 'cmd = ["git", *args]  # lock-lint: ok callers pass only write verbs\n'
    assert git_calls_without_flag(dynamic) == []
    assert git_calls_without_flag('cmd = ["git", *args]  # lock-lint: ok\n') == [(1, _DYNAMIC)]
    assert git_calls_without_flag('cmd = ["git", "status"]  # lock-lint: ok reason\n') == [(1, "status")]
    shell = "subprocess.run(command, shell=True)  # lock-lint: ok command is a fixed constant\n"
    assert git_calls_without_flag(shell) == []
    unproven = "subprocess.run([tool, 'x'])  # lock-lint: ok tool is a test seam for lsof\n"
    assert git_calls_without_flag(unproven) == []
    assert git_calls_without_flag("subprocess.run([tool, 'x'])  # lock-lint: ok\n") == [(1, _UNPROVEN)]
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
        # A wrapper program runs git: only the flag covers it.
        ("env GIT_OPTIONAL_LOCKS=0 git status", [(1, "status")]),
        ("timeout 5 env GIT_OPTIONAL_LOCKS=0 git status", [(1, "status")]),
        ("env -u FOO git --no-optional-locks status", []),
        ("if GIT_OPTIONAL_LOCKS=0 git diff --quiet; then :; fi", []),
        ("x && GIT_OPTIONAL_LOCKS=0 git status", []),
        ("git check-attr -a x", [(1, "check-attr")]),
        ("git frobnicate", [(1, "frobnicate (unknown subcommand)")]),
        ('git "$@"', [(1, "<dynamic>")]),
        ('git --no-optional-locks "$@"', []),
        ('git -C "$R"', [(1, "<dynamic>")]),
        ("out=$(git rev-parse HEAD)", [(1, "rev-parse")]),
        ("sh -c 'git status'", [(1, "status")]),
        ('bash -c "git log -1"', [(1, "log")]),
    ],
)
def test_shell_lint_cases(line: str, expected: list[tuple[int, str]]) -> None:
    assert shell_git_calls_without_flag(line + "\n") == expected


@pytest.mark.parametrize(
    "text,expected",
    [
        # Review r6: a ``#`` that starts no comment hides none of the code after it.
        ('echo "# Working tree"; git status --porcelain', [(1, "status")]),
        ("echo '# Working tree'; git status --porcelain", [(1, "status")]),
        (r"echo \# Working tree; git status --porcelain", [(1, "status")]),
        ('echo "args: $#"; git status --porcelain', [(1, "status")]),
        ("n=${#files}; git status --porcelain", [(1, "status")]),
        ("cat <<EOF\nItem #1: $(git status --porcelain)\nEOF", [(2, "status")]),
        # A real comment is read too: the code before it, and a git word inside it.
        ("git status --porcelain  # refresh", [(1, "status")]),
        ("git commit -m x  # git status in a comment", [(1, "status")]),
        ("# git status", [(1, "status")]),
        ("# Git status, reworded", []),
    ],
)
def test_shell_lint_reads_text_after_a_hash(text: str, expected: list[tuple[int, str]]) -> None:
    assert shell_git_calls_without_flag(text + "\n") == expected


def test_lint_reads_shell_text_after_a_quoted_hash() -> None:
    source = "import subprocess\n\nsubprocess.run('echo \"# Working tree\"; git status --porcelain', shell=True)\n"
    assert git_calls_without_flag(source) == [(3, "status")]
