"""Fail the build when a hook grows a second shell parser (#9807).

The check is structural. Over the whole module it collects every binding of
each name to the ``shlex`` module or a boundary module: imports, assignments,
augmented and annotated assignments, unpacking, ``for`` / ``with`` /
``except`` targets, walrus expressions, function and class definitions, and
``global`` / ``nonlocal``. If a name is ever bound to one of those modules,
every use of that name may be that module. A later, earlier, or untaken
assignment does not remove that binding. Process runners are not copied
through those bindings.

A name bound to the ``shlex`` module may appear only as ``quote`` or ``join``
attribute access in load context; every other use of that name is a parser
site. ``from shlex import split`` and ``from shlex import shlex`` are always
sites. ``shlex.split`` and ``shlex.shlex`` are parser sites in every
position, including when they are not the function of a call. Imports and
references of ``bashlex`` and ``tree_sitter_bash`` are sites. A literal argv
whose program is ``bash``, ``sh``, ``dash``, or ``zsh`` (or a path ending in
one of those) and that requests a syntax check (``-n``, a short-option
cluster containing ``n``, ``--noexec``, or ``-o noexec``) is a site. A
literal shell command string beginning with one of those programs plus a
``-n``-class flag is the same site on ``os.system``, ``os.popen``,
``asyncio.create_subprocess_shell``, ``subprocess.getoutput``,
``subprocess.getstatusoutput``, and ``subprocess.*`` with ``shell=True``.
``shlex.quote`` and ``shlex.join`` are output quoting and are allowed.
Generic regexes, loops, and subprocess calls are not parsers.

In a hook module outside the boundary, a process runner may appear only as
the ``func`` of a call, or as the class of a match pattern (a call written
in a pattern). Every other use — assignment value, argument, return,
default, annotation, collection element, comprehension or loop iterable,
unpacking source, or attribute of something else — is a violation,
``runner used as a value``. The runner is not followed into the name that
received it. A direct call keeps the literal argv and literal command-string
checks over every argument, positional or keyword.

A process runner is ``subprocess.run``, ``Popen``, ``call``, ``check_call``,
``check_output``, ``getoutput``, or ``getstatusoutput``; ``os.system``,
``os.popen``, ``os.exec*``, ``os.spawn*``, ``os.posix_spawn``, or
``os.posix_spawnp``; or ``asyncio.create_subprocess_exec`` or
``asyncio.create_subprocess_shell``. The reference may be ``module.attr`` on
any import of that module, including a dotted import whose final segment is
the module, or a name brought in by ``from module import attr``.

The module objects ``subprocess``, ``os``, ``asyncio``, and ``shlex`` follow
the same shape when they are passed, assigned, or stored instead of used as
the base of an attribute (``module used as a value``). A ``shlex`` module
used that way is also a parser site. ``getattr(subprocess, 'run')`` passes
the module and is that violation; it is not a separate hole.

In a hook module outside the boundary, ``from shlex import *``,
``from subprocess import *``, ``from os import *``, ``from asyncio import *``,
and a wildcard import of either boundary module are violations by themselves.
Star-imports are not expanded.

A name keeps every module it is imported as. Each binding is checked.
Iteration over those sets is sorted.

Boundary modules are recognized by the final segment of every import form:
a plain import, an alias, a dotted import (``import package.shell_shlex``),
and a relative import. Attribute access on the resolved module must be a
public export.

Name use is not a list of statement kinds. A parent map over ``ast.walk``
inspects every name and every attribute chain, wherever it sits. External
syntax-check calls use that same walk: every ``ast.Call`` is inspected, so
the position of the call cannot hide it.

Accepted limitations (owner: claude-infra, slice 2b):

- Handwritten scanners. The quote tracker in
  ``agents_extensions/shared/hooks/guard-secret-print.py``
  (``_strip_shell_comments`` and the sibling scanners listed in the slice-2b
  residual) is outside this guarantee. Slice 2b migrates those scanners; this
  module does not.
- Execution and import machinery is not run: ``exec``, ``eval``, ``compile``,
  computed ``importlib`` / ``__import__``, and ``typing.get_type_hints`` on
  quoted annotations. A runner reached only through that machinery, with no
  direct reference to the module or the callable, stays unresolved.
- Quoted (string) annotations stay source text.
- A function-local absolute import that leaves a helper's package is not
  followed. The session-start hook reaches application modules that already
  call ``shlex.split``, and those calls are not hook parsers.
- Computed argv is not a literal command. List concatenation and starred
  elements stay unresolved. Computed command strings (string concatenation
  or formatting) and argv lists mutated after binding stay unresolved.

``shell_shlex.py`` and ``shell_redirects.py`` are the shared parser boundary.
Outside those modules a name bound to either may appear only as a public
export. This module is a test: production hooks must not import it, and it is
not a bash oracle deployed with them. There is no ``bash -n`` subprocess in
this check.
"""

from __future__ import annotations

import ast
import json
import os
import shlex
import subprocess
import sys
from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = REPO_ROOT / "tests" / "fixtures" / "hook_parser_sites_baseline.json"

# Creation count. The on-disk fixture must equal ``CREATION_SITES`` exactly.
# Shrinking a site means editing the fixture and that tuple in the same change.
# A fixture that drops a creation site, or grows one back after the tuple
# shrank, fails. Editing the constant is a policy change, not a refresh.
BASELINE_SIZE_AT_CREATION = 6

BOUNDARY_PATHS = frozenset(
    {
        "agents_extensions/shared/hooks/shell_redirects.py",
        "agents_extensions/shared/hooks/shell_shlex.py",
    }
)

# Public exports enumerated from the modules' own definitions (no ``__all__``;
# adding one is slice 2b) and checked against current hook consumers below.
PUBLIC_EXPORTS = {
    "shell_shlex": frozenset(
        {
            "ShellPreprocessLimit",
            "collapse_line_continuations",
            "preprocess_shell_command",
            "skippable_heredoc_delimiters",
            "split_operator_run",
            "split_quote_preserving",
            "strip_shell_comments",
            "strip_skippable_heredoc_bodies",
        }
    ),
    "shell_redirects": frozenset(
        {
            "command_repository_unknown",
            "preprocess_branch_command",
            "scope_events",
            "segments_with_following_operator",
            "unknown_repository_segments",
            "unmodeled_shell_offset",
        }
    ),
}

# Names hook modules import today. Definitions not in this set stay public;
# consumers must not step outside ``PUBLIC_EXPORTS``.
CONSUMER_IMPORTS = {
    "shell_shlex": frozenset(
        {
            "ShellPreprocessLimit",
            "preprocess_shell_command",
            "skippable_heredoc_delimiters",
            "split_operator_run",
            "split_quote_preserving",
            "strip_skippable_heredoc_bodies",
        }
    ),
    "shell_redirects": frozenset(
        {
            "command_repository_unknown",
            "preprocess_branch_command",
            "scope_events",
            "segments_with_following_operator",
            "unknown_repository_segments",
        }
    ),
}

# Tests of the two boundary modules may read private names. Other files may not.
WHITE_BOX_TESTS = frozenset(
    {
        "tests/test_shell_redirects.py",
        "tests/test_shell_shlex.py",
    }
)

# Closed list. A new shell-parser dependency is a new site, not a silent miss.
SHELL_PARSER_LIBRARIES = frozenset({"bashlex", "tree_sitter_bash"})
SYNTAX_CHECK_SHELLS = frozenset({"bash", "sh", "dash", "zsh"})
SHLEX_MODULE_ALLOWED_ATTRS = frozenset({"quote", "join"})
DYNAMIC_MODULE_FUNCS = frozenset({"getattr", "vars", "globals", "__import__"})
SUBPROCESS_FUNCS = frozenset({"run", "call", "check_call", "check_output", "Popen", "getoutput", "getstatusoutput"})
OS_STRING_FUNCS = frozenset({"system", "popen"})
OS_EXEC_LIST_FUNCS = frozenset({"execl", "execlp", "execle", "execlpe"})
OS_EXEC_ARGV_FUNCS = frozenset({"execv", "execvp", "execvpe", "execve"})
OS_SPAWN_LIST_FUNCS = frozenset({"spawnl", "spawnle", "spawnlp", "spawnlpe"})
OS_SPAWN_ARGV_FUNCS = frozenset({"spawnv", "spawnve", "spawnvp", "spawnvpe"})
# ``posix_spawn(path, argv, env)``: argv is the second positional, as with execv*.
OS_POSIX_SPAWN_FUNCS = frozenset({"posix_spawn", "posix_spawnp"})
OS_ARGV_SECOND_FUNCS = OS_EXEC_ARGV_FUNCS | OS_POSIX_SPAWN_FUNCS
OS_RUNNER_FUNCS = (
    OS_STRING_FUNCS
    | OS_EXEC_LIST_FUNCS
    | OS_EXEC_ARGV_FUNCS
    | OS_SPAWN_LIST_FUNCS
    | OS_SPAWN_ARGV_FUNCS
    | OS_POSIX_SPAWN_FUNCS
)
ASYNCIO_EXEC_FUNCS = frozenset({"create_subprocess_exec"})
ASYNCIO_SHELL_FUNCS = frozenset({"create_subprocess_shell"})
ASYNCIO_RUNNER_FUNCS = ASYNCIO_EXEC_FUNCS | ASYNCIO_SHELL_FUNCS
# Star-imports of these modules are refused outside the boundary. They are not expanded.
WILDCARD_IMPORT_MODULES = frozenset({"asyncio", "os", "shlex", "subprocess"})
# Runner alias tracking is gone. May-bind is only the shlex module and the
# boundary modules; a runner reference is judged where it is written.
_MAY_BIND_KINDS = frozenset({"shlex_module", "boundary_module"})
RUNNER_MODULE_FAMILIES = frozenset({"asyncio", "os", "subprocess"})
VALUE_MODULE_FAMILIES = frozenset({"asyncio", "os", "shlex", "subprocess"})
_RUNNER_FUNCS_BY_FAMILY = {
    "asyncio": ASYNCIO_RUNNER_FUNCS,
    "os": OS_RUNNER_FUNCS,
    "subprocess": SUBPROCESS_FUNCS,
}
SHLEX_EXPORTS = frozenset({"split", "shlex", "quote", "join"})
PARSER_SHLEX_ATTRS = frozenset({"split", "shlex"})

# Helpers the hook trees import today. The scan must keep reaching them, and
# the modules they import at load time, so a parser site on that chain fails
# the baseline. Extras (package ``__init__`` files loaded with those imports)
# are allowed.
REQUIRED_PRODUCTION_HELPERS = frozenset(
    {
        "scripts/common/repo_root.py",
        "scripts/guardrails/assert_primary_on_main.py",
        "scripts/guardrails/worktree_containment.py",
        "scripts/lib/session_record.py",
        "scripts/opsec/prepublish.py",
        "scripts/orchestration/thread_handoff.py",
        "scripts/publish/merge_guard.py",
    }
)


@dataclass(frozen=True)
class Site:
    path: str
    enclosing_symbol: str
    site_identity: str

    def key(self) -> tuple[str, str, str]:
        return (self.path, self.enclosing_symbol, self.site_identity)

    def format(self) -> str:
        return f"{self.path}::{self.enclosing_symbol}::{self.site_identity}"


# The six parser sites present when this check was created. The fixture must
# equal this tuple. Shrinking, replacement, and regrowth edit it on purpose.
CREATION_SITES: tuple[Site, ...] = (
    Site(
        "agents_extensions/shared/hooks/guard-primary-checkout-write.py",
        "_sibling_git_invocation",
        "shlex.split",
    ),
    Site(
        "agents_extensions/shared/hooks/guard-primary-checkout-write.py",
        "_tokenize",
        "shlex.shlex",
    ),
    Site(
        "agents_extensions/shared/hooks/guard-primary-checkout-write.py",
        "main",
        "shlex.split",
    ),
    Site(
        "agents_extensions/shared/hooks/guard-public-github-text.py",
        "invokes_gh",
        "shlex.shlex",
    ),
    Site(
        "agents_extensions/shared/hooks/guard-secret-print.py",
        "_shell_script.decode",
        "shlex.split",
    ),
    Site(
        "agents_extensions/shared/hooks/heal-core-bare.py",
        "_is_git_command",
        "shlex.split",
    ),
)


@dataclass(frozen=True)
class Violation:
    kind: str
    path: str
    enclosing_symbol: str
    detail: str

    def format(self) -> str:
        return f"{self.kind}: {self.path}::{self.enclosing_symbol}::{self.detail}"


@dataclass(frozen=True)
class Check:
    sites: tuple[Site, ...]
    violations: tuple[Violation, ...]
    hook_files: tuple[str, ...]
    production_helpers: tuple[str, ...]


@dataclass(frozen=True)
class _Binding:
    kind: str
    detail: tuple[str, ...] = ()
    argv: tuple[str | None, ...] | None = None


_UNKNOWN = _Binding("unknown")


def _binding_sort_key(binding: _Binding) -> tuple[object, ...]:
    """Stable order for a binding set. The hash seed must not change results."""
    if binding.argv is None:
        return (binding.kind, binding.detail, True, ())
    rendered = tuple("" if part is None else part for part in binding.argv)
    return (binding.kind, binding.detail, False, rendered)


def _sorted_bindings(bindings: Iterable[_Binding]) -> list[_Binding]:
    return sorted(bindings, key=_binding_sort_key)


def _first_syntax_identity(argvs: list[tuple[str | None, ...]]) -> str | None:
    for argv in argvs:
        identity = _syntax_identity(argv)
        if identity:
            return identity
    return None


def _enclosing_symbol(node: ast.AST, parents: dict[ast.AST, ast.AST]) -> str:
    """Function, class, and lambda that lexically contain ``node``.

    Decorators, defaults, annotations, and base classes are evaluated in the
    enclosing scope, matching the statement visitor. Only a body statement, or
    a lambda body, pushes a name.
    """
    names: list[str] = []
    current: ast.AST | None = node
    while current is not None:
        parent = parents.get(current)
        if isinstance(parent, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and any(
            current is statement for statement in parent.body
        ):
            names.append(parent.name)
        elif isinstance(parent, ast.Lambda) and current is parent.body:
            names.append("<lambda>")
        current = parent
    if not names:
        return "<module>"
    return ".".join(reversed(names))


@dataclass
class _Scope:
    kind: str
    parent: _Scope | None
    module: _Scope
    bindings: list[tuple[int, int, str, _Binding]] = field(default_factory=list)
    global_names: set[str] = field(default_factory=set)
    nonlocal_names: set[str] = field(default_factory=set)

    def bind(self, line: int, column: int, name: str, binding: _Binding) -> None:
        target = self
        if name in self.global_names and self.module is not self:
            target = self.module
        elif name in self.nonlocal_names and self.parent is not None:
            target = self.parent
        target.bindings.append((line, column, name, binding))

    def lookup(self, name: str, line: int, column: int, *, follow_global: bool = True) -> _Binding | None:
        if follow_global and name in self.global_names and self.module is not self:
            return self.module.lookup(name, line, column, follow_global=False)
        if follow_global and name in self.nonlocal_names and self.parent is not None:
            return self.parent.lookup(name, line, column)
        best: _Binding | None = None
        best_pos: tuple[int, int] | None = None
        for bound_line, bound_column, bound_name, binding in self.bindings:
            if bound_name != name:
                continue
            pos = (bound_line, bound_column)
            if pos <= (line, column) and (best_pos is None or pos >= best_pos):
                best = binding
                best_pos = pos
        if best is not None:
            return best
        if self.kind == "function" and any(bound_name == name for _, _, bound_name, _ in self.bindings):
            return _UNKNOWN
        if self.parent is not None:
            return self.parent.lookup(name, line, column)
        return None


def _classify_leaf(leaf: str) -> tuple[str, str] | None:
    """Closed module named by an import's final segment.

    The pair is ``(family, leaf)``. ``family`` is ``boundary``, ``shlex``,
    ``subprocess``, ``os``, or ``asyncio``.
    """
    if leaf in PUBLIC_EXPORTS:
        return ("boundary", leaf)
    if leaf == "shlex":
        return ("shlex", "shlex")
    if leaf in RUNNER_MODULE_FAMILIES:
        return (leaf, leaf)
    return None


def _attribute_chain(node: ast.AST) -> tuple[ast.Name, tuple[str, ...]] | None:
    """Root name and attribute segments of a static chain, or None."""
    attrs: list[str] = []
    current = node
    while isinstance(current, ast.Attribute):
        attrs.append(current.attr)
        current = current.value
    if not isinstance(current, ast.Name):
        return None
    attrs.reverse()
    return current, tuple(attrs)


def _parent_map(tree: ast.AST) -> dict[ast.AST, ast.AST]:
    parents: dict[ast.AST, ast.AST] = {}
    for node in ast.walk(tree):
        for child in ast.iter_child_nodes(node):
            parents[child] = node
    return parents


def _is_runner_head(node: ast.AST, parents: dict[ast.AST, ast.AST]) -> bool:
    """True when ``node`` is the callable head of a call or match pattern."""
    parent = parents.get(node)
    if isinstance(parent, ast.Call) and parent.func is node:
        return True
    return isinstance(parent, ast.MatchClass) and parent.cls is node


def _is_attribute_base(node: ast.AST, parents: dict[ast.AST, ast.AST]) -> bool:
    parent = parents.get(node)
    return isinstance(parent, ast.Attribute) and parent.value is node


def _is_hook_path(path: str) -> bool:
    parts = path.split("/")
    if path.startswith("scripts/hooks/") and path.endswith(".py") and ".." not in parts:
        return True
    return (
        len(parts) >= 4
        and parts[0] == "agents_extensions"
        and parts[2] == "hooks"
        and path.endswith(".py")
        and ".." not in parts
    )


def _boundary_module_name(module: str | None) -> str | None:
    if not module:
        return None
    leaf = module.split(".")[-1]
    if leaf in PUBLIC_EXPORTS:
        return leaf
    return None


def _is_test_module(module: str | None) -> bool:
    return module == "tests" or (module is not None and module.startswith("tests."))


def _is_parser_library(module: str | None) -> str | None:
    if not module:
        return None
    top = module.split(".")[0]
    if top in SHELL_PARSER_LIBRARIES:
        return top
    return None


def _is_deployed_oracle(path: str) -> bool:
    name = path.rsplit("/", 1)[-1]
    return _is_hook_path(path) and ("bash_oracle" in name or "shell_oracle" in name or "syntax_oracle" in name)


def _executable_name(token: str) -> str:
    return token.replace("\\", "/").rsplit("/", 1)[-1]


def _syntax_identity(argv: tuple[str | None, ...]) -> str | None:
    if not argv or argv[0] is None:
        return None
    words = list(argv)
    exe = _executable_name(words[0])
    rest = words[1:]
    if exe == "env":
        index = 0
        while index < len(rest):
            token = rest[index]
            if token is None:
                return None
            if token in SYNTAX_CHECK_SHELLS or _executable_name(token) in SYNTAX_CHECK_SHELLS:
                exe = _executable_name(token)
                rest = rest[index + 1 :]
                break
            if token in {"-i", "-"} or token.startswith("-u") or "=" in token or token.startswith("-"):
                index += 2 if token in {"-u", "-S"} else 1
                continue
            return None
        else:
            return None
    if exe not in SYNTAX_CHECK_SHELLS:
        return None
    if _argv_requests_syntax_check(rest):
        return f"syntax:{exe} -n"
    return None


def _argv_requests_syntax_check(argv: list[str | None]) -> bool:
    """True when a literal argv asks a shell not to execute.

    A short-option cluster containing ``n`` (``-n``, ``-nc``, ``-xn``),
    ``--noexec``, or ``-o noexec`` is a syntax check. This is syntactic: the
    tokens are not interpreted as a shell command line.
    """
    for index, token in enumerate(argv):
        if token is None:
            continue
        if token == "--noexec":
            return True
        if token == "-o" and index + 1 < len(argv) and argv[index + 1] == "noexec":
            return True
        if token.startswith("-") and not token.startswith("--") and "n" in token[1:]:
            return True
    return False


def _direct_alias_pairs(target: ast.AST, value: ast.AST) -> list[tuple[str, str]]:
    """Name-to-name aliases, including matching unpacks. No value flow."""
    if isinstance(target, ast.Name) and isinstance(value, ast.Name):
        return [(target.id, value.id)]
    if (
        isinstance(target, (ast.Tuple, ast.List))
        and isinstance(value, (ast.Tuple, ast.List))
        and len(target.elts) == len(value.elts)
        and not any(isinstance(elt, ast.Starred) for elt in (*target.elts, *value.elts))
    ):
        pairs: list[tuple[str, str]] = []
        for left, right in zip(target.elts, value.elts, strict=True):
            pairs.extend(_direct_alias_pairs(left, right))
        return pairs
    return []


def public_definitions(source: str) -> frozenset[str]:
    """Top-level public definitions. Imports are not exports; ``__all__`` is not consulted."""
    tree = ast.parse(source)
    names: set[str] = set()
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if not node.name.startswith("_"):
                names.add(node.name)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                names.update(_public_store_names(target))
        elif (
            isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and not node.target.id.startswith("_")
        ):
            names.add(node.target.id)
    return frozenset(names)


def _public_store_names(target: ast.AST) -> set[str]:
    if isinstance(target, ast.Name):
        return set() if target.id.startswith("_") else {target.id}
    if isinstance(target, (ast.Tuple, ast.List)):
        names: set[str] = set()
        for elt in target.elts:
            names.update(_public_store_names(elt))
        return names
    return set()


def consumer_imports(sources: dict[str, str]) -> dict[str, frozenset[str]]:
    found = {name: set() for name in PUBLIC_EXPORTS}
    for path, source in sources.items():
        if path in BOUNDARY_PATHS or not _is_hook_path(path):
            continue
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if not isinstance(node, ast.ImportFrom):
                continue
            boundary = _boundary_module_name(node.module)
            if boundary is None:
                continue
            for alias in node.names:
                if alias.name != "*":
                    found[boundary].add(alias.name)
    return {name: frozenset(values) for name, values in found.items()}


class _Analyzer:
    def __init__(self, path: str, *, record_sites: bool, enforce_exports: bool) -> None:
        self.path = path
        self.record_sites = record_sites
        self.enforce_exports = enforce_exports
        self.sites: list[Site] = []
        self.violations: list[Violation] = []
        self._symbols: list[str] = []
        self._may: dict[str, set[_Binding]] = {}
        self._shlex_module_names: set[str] = set()
        self._boundary_names: dict[str, set[str]] = {}
        self._dynamic_aliases: dict[str, str] = {}
        # Import bindings only. Assignment does not copy a runner or a module
        # object into another name; that use is an escape violation.
        self._module_aliases: dict[str, set[str]] = {}
        self._imported_runners: dict[str, set[tuple[str, str]]] = {}
        self._dotted_modules: dict[str, set[tuple[tuple[str, ...], str, str]]] = {}
        self._node_scopes: dict[int, _Scope] = {}
        self._module_scope: _Scope | None = None

    def symbol(self) -> str:
        return ".".join(self._symbols) if self._symbols else "<module>"

    def add_site(self, identity: str) -> None:
        if self.record_sites:
            self.sites.append(Site(self.path, self.symbol(), identity))

    def add_violation(self, kind: str, detail: str) -> None:
        self.violations.append(Violation(kind, self.path, self.symbol(), detail))

    def analyze(self, tree: ast.Module) -> None:
        self._prepare_closed_names(tree)
        # Name use and syntax-check calls are total walks. The statement
        # visitor binds imports, records literal values those calls read, and
        # records imported callables. It does not decide which nodes can hold
        # a module name or a call.
        self._inspect_bound_module_uses(tree)
        module = _Scope(kind="module", parent=None, module=None)  # type: ignore[arg-type]
        module.module = module
        self._module_scope = module
        self._node_scopes = {id(tree): module}
        self._hoist(tree.body, module)
        for stmt in tree.body:
            self._visit_stmt(stmt, module)
        self._inspect_syntax_check_calls(tree)
        self._inspect_runner_escape(tree)

    def _scope_for(self, node: ast.AST, parents: dict[ast.AST, ast.AST]) -> _Scope:
        """Lexical scope of ``node``.

        The statement visitor stamps every statement and expression it walks.
        A call it does not walk takes the nearest stamped ancestor: the
        assignment or match statement for a target or pattern, and the
        function definition for an annotation or a default.
        """
        current: ast.AST | None = node
        while current is not None:
            found = self._node_scopes.get(id(current))
            if found is not None:
                return found
            current = parents.get(current)
        if self._module_scope is None:
            raise RuntimeError("syntax-check walk ran before the module scope existed")
        return self._module_scope

    def _inspect_syntax_check_calls(self, tree: ast.AST) -> None:
        """Judge every call for an external syntax check, not a statement list."""
        if not self.record_sites:
            return
        parents = _parent_map(tree)
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                identity = self._call_syntax_identity(node, self._scope_for(node, parents))
            elif isinstance(node, ast.MatchClass):
                # ``case subprocess.run([...])`` is a class pattern, not an
                # ``ast.Call``. The call is still written in that position.
                identity = self._match_syntax_identity(node, self._scope_for(node, parents))
            else:
                continue
            if identity:
                self._record_site(node, identity, parents)

    def _bound_modules(self, name: str) -> list[tuple[str, str]]:
        """Every module ``name`` may be, shlex first, then boundary names in order."""
        found: list[tuple[str, str]] = []
        if name in self._shlex_module_names:
            found.append(("shlex", "shlex"))
        for module in sorted(self._boundary_names.get(name, ())):
            found.append(("boundary", module))
        return found

    def _inspect_bound_module_uses(self, tree: ast.AST) -> None:
        """Judge every bound module name from a parent map, not a node-type list."""
        if not self.record_sites and not self.enforce_exports:
            return
        parents = _parent_map(tree)
        judged: set[int] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                self._inspect_bound_name(node, parents, judged)
            elif isinstance(node, ast.Attribute):
                self._inspect_bound_attribute(node, parents, judged)
                self._inspect_dotted_attribute(node, parents, judged)
            elif isinstance(node, (ast.Global, ast.Nonlocal)):
                self._inspect_bare_name_strings(node, node.names, parents)
            elif isinstance(node, (ast.MatchAs, ast.MatchStar)) and node.name:
                self._inspect_bare_name_strings(node, (node.name,), parents)
            elif isinstance(node, ast.MatchMapping) and node.rest:
                self._inspect_bare_name_strings(node, (node.rest,), parents)

    def _inspect_bound_name(self, node: ast.Name, parents: dict[ast.AST, ast.AST], judged: set[int]) -> None:
        kinds = self._bound_modules(node.id)
        if not kinds:
            return
        parent = parents.get(node)
        if isinstance(parent, ast.Attribute) and parent.value is node:
            if id(parent) not in judged:
                judged.add(id(parent))
                for kind in kinds:
                    self._judge_bound_attribute(parent, kind, parents)
            return
        for kind in kinds:
            self._reject_bare_bound_name(node, kind, parents)

    def _inspect_bound_attribute(self, node: ast.Attribute, parents: dict[ast.AST, ast.AST], judged: set[int]) -> None:
        if id(node) in judged or not isinstance(node.value, ast.Name):
            return
        kinds = self._bound_modules(node.value.id)
        if not kinds:
            return
        judged.add(id(node))
        for kind in kinds:
            self._judge_bound_attribute(node, kind, parents)

    def _inspect_dotted_attribute(self, node: ast.Attribute, parents: dict[ast.AST, ast.AST], judged: set[int]) -> None:
        """Judge a boundary or shlex module reached by an unaliased dotted import.

        ``import package.shell_shlex`` binds the name ``package``. The chain
        ``package.shell_shlex`` is the boundary module, and the next attribute
        follows the public-export rule. A runner module on the same shape is
        left to the escape rule.
        """
        if id(node) in judged:
            return
        if isinstance(node.value, ast.Attribute):
            bases = self._dotted_exact(node.value)
            sensitive = [(family, leaf) for family, leaf in bases if family in {"shlex", "boundary"}]
            if sensitive:
                judged.add(id(node))
                for family, leaf in sensitive:
                    self._judge_bound_attribute(node, (family, leaf), parents)
                return
        modules = [(family, leaf) for family, leaf in self._dotted_exact(node) if family in {"shlex", "boundary"}]
        if not modules:
            return
        parent = parents.get(node)
        if isinstance(parent, ast.Attribute) and parent.value is node:
            return
        for family, leaf in modules:
            kind = ("shlex", "shlex") if family == "shlex" else ("boundary", leaf)
            self._reject_bare_bound_name(node, kind, parents)

    def _inspect_bare_name_strings(
        self,
        node: ast.AST,
        names: tuple[str, ...] | list[str],
        parents: dict[ast.AST, ast.AST],
    ) -> None:
        for name in names:
            for kind in self._bound_modules(name):
                self._reject_bare_bound_name(node, kind, parents)

    def _judge_bound_attribute(
        self, node: ast.Attribute, kind: tuple[str, str], parents: dict[ast.AST, ast.AST]
    ) -> None:
        family, module = kind
        if family == "shlex":
            if not self.record_sites:
                return
            if node.attr in SHLEX_MODULE_ALLOWED_ATTRS and isinstance(node.ctx, ast.Load):
                return
            self._record_site(node, f"shlex.{node.attr}", parents)
            return
        if not self.enforce_exports:
            return
        if node.attr.startswith("__") and node.attr.endswith("__"):
            self._record_violation(node, "dynamic access", f"{module}.{node.attr}", parents)
        elif node.attr not in PUBLIC_EXPORTS[module]:
            self._record_violation(node, "private attribute", f"{module}.{node.attr}", parents)

    def _reject_bare_bound_name(self, node: ast.AST, kind: tuple[str, str], parents: dict[ast.AST, ast.AST]) -> None:
        family, module = kind
        if family == "shlex":
            if self.record_sites:
                self._record_site(node, "shlex", parents)
            return
        if self.enforce_exports:
            self._record_violation(node, "dynamic access", f"module {module}", parents)

    def _record_site(self, node: ast.AST, identity: str, parents: dict[ast.AST, ast.AST]) -> None:
        self.sites.append(Site(self.path, _enclosing_symbol(node, parents), identity))

    def _record_violation(self, node: ast.AST, kind: str, detail: str, parents: dict[ast.AST, ast.AST]) -> None:
        self.violations.append(Violation(kind, self.path, _enclosing_symbol(node, parents), detail))

    def _prepare_closed_names(self, tree: ast.AST) -> None:
        """Bind shlex and boundary names for the whole file.

        Every binding of a name is collected, and a sensitive binding is kept
        wherever the name occurs. Later, earlier, or untaken rebinding does
        not remove ``shlex`` or a boundary module. Process runners are not
        part of this map: a runner reference is allowed only as a call.
        This is syntactic; it does not track which branch runs.
        """
        self._may = {}
        self._shlex_module_names = set()
        self._boundary_names = {}
        self._module_aliases = {}
        self._imported_runners = {}
        self._dotted_modules = {}
        self._dynamic_aliases = {name: name for name in DYNAMIC_MODULE_FUNCS}
        pairs: list[tuple[str, str]] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    self._remember_module_import(alias)
            elif isinstance(node, ast.ImportFrom):
                self._seed_import_from(node)
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    pairs.extend(_direct_alias_pairs(target, node.value))
            elif (isinstance(node, ast.AnnAssign) and node.value is not None) or isinstance(node, ast.NamedExpr):
                pairs.extend(_direct_alias_pairs(node.target, node.value))
        self._propagate_may_bind(tree)
        self._publish_may_bind()
        changed = True
        while changed:
            changed = False
            for new_name, source_name in pairs:
                if source_name in self._dynamic_aliases and new_name not in self._dynamic_aliases:
                    self._dynamic_aliases[new_name] = self._dynamic_aliases[source_name]
                    changed = True

    def _add_may(self, name: str, binding: _Binding) -> bool:
        if binding.kind not in _MAY_BIND_KINDS:
            return False
        found = self._may.setdefault(name, set())
        if binding in found:
            return False
        found.add(binding)
        return True

    def _remember_module_import(self, alias: ast.alias) -> None:
        """Record an ``import`` by the module's final segment.

        ``import module as name`` binds ``name`` to that module. ``import
        package.module`` binds ``package`` to the top package and the attribute
        chain to the module. A runner module is remembered only so a direct
        reference can be recognized; it is not copied through assignment.
        """
        parts = tuple(alias.name.split("."))
        leaf = parts[-1]
        root = parts[0]
        if alias.asname:
            classified = _classify_leaf(leaf)
            if classified is not None:
                family, name = classified
                self._bind_direct_module(alias.asname, family, name)
            return
        root_classified = _classify_leaf(root)
        if root_classified is not None:
            family, name = root_classified
            self._bind_direct_module(root, family, name)
        if len(parts) > 1:
            classified = _classify_leaf(leaf)
            if classified is not None:
                family, name = classified
                self._dotted_modules.setdefault(root, set()).add((parts[1:], family, name))

    def _bind_direct_module(self, name: str, family: str, leaf: str) -> None:
        if family == "shlex":
            self._add_may(name, _Binding("shlex_module"))
        elif family == "boundary":
            self._add_may(name, _Binding("boundary_module", (leaf,)))
        if family in VALUE_MODULE_FAMILIES:
            self._module_aliases.setdefault(name, set()).add(family)

    def _dotted_rows(self, root: str) -> list[tuple[tuple[str, ...], str, str]]:
        return sorted(self._dotted_modules.get(root, ()), key=lambda row: (row[0], row[1], row[2]))

    def _dotted_exact(self, node: ast.AST) -> list[tuple[str, str]]:
        """``(family, leaf)`` when ``node`` is exactly a dotted import's module."""
        chain = _attribute_chain(node)
        if chain is None:
            return []
        root, attrs = chain
        if not attrs:
            return []
        found: list[tuple[str, str]] = []
        for remaining, family, leaf in self._dotted_rows(root.id):
            if attrs == remaining:
                found.append((family, leaf))
        return found

    def _seed_import_from(self, node: ast.ImportFrom) -> None:
        module = node.module or ""
        module_leaf = module.split(".")[-1] if module else ""
        # ``from shell_shlex import name`` binds the export, not the module.
        # ``from package import shell_shlex`` binds the module.
        if module_leaf not in PUBLIC_EXPORTS:
            for alias in node.names:
                if alias.name in PUBLIC_EXPORTS:
                    self._add_may(alias.asname or alias.name, _Binding("boundary_module", (alias.name,)))
        if node.level and not module:
            for alias in node.names:
                if alias.name == "*":
                    continue
                classified = _classify_leaf(alias.name)
                if classified is None:
                    continue
                family, name = classified
                self._bind_direct_module(alias.asname or alias.name, family, name)
        if module_leaf == "subprocess":
            funcs = SUBPROCESS_FUNCS
            family = "subprocess"
        elif module_leaf == "os":
            funcs = OS_RUNNER_FUNCS
            family = "os"
        elif module_leaf == "asyncio":
            funcs = ASYNCIO_RUNNER_FUNCS
            family = "asyncio"
        else:
            return
        for alias in node.names:
            if alias.name == "*" or alias.name not in funcs:
                continue
            local = alias.asname or alias.name
            self._imported_runners.setdefault(local, set()).add((family, alias.name))

    def _propagate_may_bind(self, tree: ast.AST) -> None:
        """Copy a shlex or boundary binding through every alias of that name.

        ``for``, ``with``, ``except``, ``global``, ``nonlocal``, and function
        or class definitions are bindings. Only a value that may itself be the
        ``shlex`` module or a boundary module adds one; the other forms do
        not clear one. A process runner is not copied.
        """
        nodes = list(ast.walk(tree))
        changed = True
        while changed:
            changed = False
            for node in nodes:
                changed |= self._propagate_may_node(node)

    def _propagate_may_node(self, node: ast.AST) -> bool:
        if isinstance(node, ast.Assign):
            changed = False
            for target in node.targets:
                changed |= self._propagate_target(target, node.value)
            return changed
        if isinstance(node, ast.AnnAssign) and node.value is not None:
            return self._propagate_target(node.target, node.value)
        if isinstance(node, ast.NamedExpr):
            return self._propagate_target(node.target, node.value)
        if isinstance(node, ast.AugAssign):
            return False
        if isinstance(node, (ast.For, ast.AsyncFor)):
            return self._propagate_for(node.target, node.iter)
        if isinstance(node, (ast.With, ast.AsyncWith, ast.ExceptHandler, ast.Global, ast.Nonlocal)):
            return False
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            return False
        return False

    def _propagate_for(self, target: ast.AST, iter_expr: ast.expr) -> bool:
        if not isinstance(iter_expr, (ast.List, ast.Tuple)):
            return False
        if any(isinstance(elt, ast.Starred) for elt in iter_expr.elts):
            return False
        if isinstance(target, ast.Name):
            changed = False
            for element in iter_expr.elts:
                changed |= self._propagate_target(target, element)
            return changed
        if len(iter_expr.elts) == 1:
            return self._propagate_target(target, iter_expr.elts[0])
        return False

    def _propagate_target(self, target: ast.AST, value: ast.expr) -> bool:
        if isinstance(target, ast.Name):
            changed = False
            for binding in _sorted_bindings(self._may_values(value)):
                changed |= self._add_may(target.id, binding)
            return changed
        if (
            isinstance(target, (ast.Tuple, ast.List))
            and isinstance(value, (ast.Tuple, ast.List))
            and len(target.elts) == len(value.elts)
            and not any(isinstance(elt, ast.Starred) for elt in (*target.elts, *value.elts))
        ):
            changed = False
            for left, right in zip(target.elts, value.elts, strict=True):
                changed |= self._propagate_target(left, right)
            return changed
        return False

    def _may_values(self, expr: ast.expr) -> set[_Binding]:
        dotted: set[_Binding] = set()
        for family, leaf in self._dotted_exact(expr):
            if family == "boundary":
                dotted.add(_Binding("boundary_module", (leaf,)))
            elif family == "shlex":
                dotted.add(_Binding("shlex_module"))
        if dotted:
            return dotted
        if isinstance(expr, ast.Name):
            return set(_sorted_bindings(self._may.get(expr.id, ())))
        if isinstance(expr, ast.Attribute):
            found: set[_Binding] = set()
            for base in _sorted_bindings(self._may_values(expr.value)):
                resolved = _resolve_attribute(base, expr.attr)
                if resolved.kind in _MAY_BIND_KINDS:
                    found.add(resolved)
            return found
        if isinstance(expr, ast.IfExp):
            return set(_sorted_bindings(self._may_values(expr.body) | self._may_values(expr.orelse)))
        if isinstance(expr, ast.BoolOp):
            found: set[_Binding] = set()
            for value in expr.values:
                found.update(_sorted_bindings(self._may_values(value)))
            return found
        if isinstance(expr, ast.NamedExpr):
            return self._may_values(expr.value)
        return set()

    def _publish_may_bind(self) -> None:
        for name in sorted(self._may):
            for binding in _sorted_bindings(self._may[name]):
                if binding.kind == "shlex_module":
                    self._shlex_module_names.add(name)
                elif binding.kind == "boundary_module":
                    self._boundary_names.setdefault(name, set()).add(binding.detail[0])

    def _possible_runners(self, func: ast.expr) -> list[_Binding]:
        """Runners ``func`` names directly. An assigned alias is not a runner."""
        return [_Binding("runner", pair) for pair in self._direct_runner_bindings(func)]

    def _direct_runner_bindings(self, node: ast.AST) -> list[tuple[str, str]]:
        """``(family, func)`` for a runner written as ``module.attr`` or an import name."""
        found: set[tuple[str, str]] = set()
        if isinstance(node, ast.Name):
            found.update(self._imported_runners.get(node.id, ()))
        elif isinstance(node, ast.Attribute):
            for family in self._runner_families(node.value):
                funcs = _RUNNER_FUNCS_BY_FAMILY.get(family)
                if funcs is not None and node.attr in funcs:
                    found.add((family, node.attr))
        return sorted(found)

    def _runner_families(self, node: ast.AST) -> list[str]:
        """Runner-module families ``node`` is, from imports only."""
        found: set[str] = set()
        if isinstance(node, ast.Name):
            found.update(self._module_aliases.get(node.id, ()))
        else:
            for family, _leaf in self._dotted_exact(node):
                found.add(family)
        return sorted(family for family in found if family in RUNNER_MODULE_FAMILIES)

    def _direct_value_modules(self, node: ast.AST) -> list[str]:
        """``subprocess``, ``os``, ``asyncio``, or ``shlex`` when ``node`` is that module."""
        found: set[str] = set()
        if isinstance(node, ast.Name):
            found.update(self._module_aliases.get(node.id, ()))
        else:
            for family, _leaf in self._dotted_exact(node):
                if family in VALUE_MODULE_FAMILIES:
                    found.add(family)
        return sorted(family for family in found if family in VALUE_MODULE_FAMILIES)

    def _inspect_runner_escape(self, tree: ast.AST) -> None:
        """A runner or runner module used as a value is a violation.

        Hook modules outside the boundary only. Helpers stay on the parser
        scan; passing a runner there is not this violation. The reference
        itself is judged, and the name it is assigned to is not a runner.
        """
        if not self.enforce_exports or not _is_hook_path(self.path):
            return
        parents = _parent_map(tree)
        for node in ast.walk(tree):
            if not isinstance(node, (ast.Name, ast.Attribute)):
                continue
            runners = self._direct_runner_bindings(node)
            if runners:
                if not _is_runner_head(node, parents):
                    detail = ", ".join(f"{family}.{func}" for family, func in runners)
                    self._record_violation(node, "runner used as a value", detail, parents)
                continue
            if _is_attribute_base(node, parents):
                continue
            for module in self._direct_value_modules(node):
                self._record_violation(node, "module used as a value", module, parents)

    def _hoist(self, body: list[ast.stmt], scope: _Scope) -> None:
        for stmt in body:
            for node in _iter_imports(stmt):
                self._bind_import(node, scope)

    def _bind_at(self, scope: _Scope, line: int, column: int, name: str, binding: _Binding) -> None:
        scope.bind(line, column, name, binding)

    def _bind_import(self, node: ast.AST, scope: _Scope) -> None:
        if isinstance(node, ast.Import):
            for alias in node.names:
                self._bind_import_alias(node, scope, alias)
            return
        if isinstance(node, ast.ImportFrom):
            self._bind_import_from(node, scope)

    def _bind_import_alias(self, node: ast.Import, scope: _Scope, alias: ast.alias) -> None:
        full = alias.name
        local = alias.asname or full.split(".")[0]
        meaning = full if alias.asname else full.split(".")[0]
        if _is_test_module(full) or _is_test_module(meaning):
            self.add_violation("test-only bash oracle", f"imports {full}")
        library = _is_parser_library(full)
        if library is not None:
            self.add_site(f"import:{library}")
        self._bind_twice(scope, node, local, self._module_binding(meaning, full))

    def _module_binding(self, meaning: str, full: str) -> _Binding:
        """Binding of the name an ``import`` actually assigns.

        ``meaning`` is the module that name refers to: the full module when
        the import is aliased, and only the first segment when it is not.
        A dotted ``import package.shell_shlex`` therefore does not make
        ``package`` the boundary module. The attribute chain resolves that.
        """
        library = _is_parser_library(meaning) or _is_parser_library(full)
        boundary = _boundary_module_name(meaning)
        if boundary is not None:
            return _Binding("boundary_module", (boundary,))
        if library is not None:
            return _Binding("parser_lib", (library,))
        if meaning == "shlex" or meaning.endswith(".shlex"):
            return _Binding("shlex_module")
        if meaning == "importlib" or meaning.endswith(".importlib"):
            return _Binding("importlib_module")
        return _UNKNOWN

    def _bind_import_from(self, node: ast.ImportFrom, scope: _Scope) -> None:
        self._refuse_wildcard_import(node)
        module = node.module
        if _is_test_module(module):
            self.add_violation("test-only bash oracle", f"imports {module}")
            self._bind_unknown_aliases(node, scope)
            return
        boundary = _boundary_module_name(module)
        if boundary is not None:
            self._bind_boundary_from(node, scope, boundary)
            return
        if module == "shlex":
            self._bind_shlex_from(node, scope)
            return
        library = _is_parser_library(module)
        if library is not None:
            self.add_site(f"import:{library}")
            for alias in node.names:
                if alias.name == "*":
                    continue
                local = alias.asname or alias.name
                self._bind_twice(scope, node, local, _Binding("parser_attr", (library, alias.name)))
            return
        if module == "importlib":
            for alias in node.names:
                if alias.name == "*":
                    continue
                local = alias.asname or alias.name
                kind = "import_module" if alias.name == "import_module" else "unknown"
                binding = _Binding(kind) if kind == "import_module" else _UNKNOWN
                self._bind_twice(scope, node, local, binding)
            return
        # ``from . import shell_shlex`` and other relative forms.
        if node.level and not module:
            for alias in node.names:
                if alias.name == "*":
                    continue
                local = alias.asname or alias.name
                imported = _boundary_module_name(alias.name)
                if imported is not None:
                    self._bind_twice(scope, node, local, _Binding("boundary_module", (imported,)))
                elif _is_test_module(alias.name):
                    self.add_violation("test-only bash oracle", f"imports {alias.name}")
                    self._bind_twice(scope, node, local, _UNKNOWN)
                else:
                    self._bind_twice(scope, node, local, _UNKNOWN)
            return
        self._bind_unknown_aliases(node, scope)

    def _refuse_wildcard_import(self, node: ast.ImportFrom) -> None:
        """Star-imports of runners, shlex, and the boundary are violations.

        Hook modules outside the boundary only. The names a star would bind are
        not expanded; the import itself is the violation.
        """
        if not self.enforce_exports:
            return
        if not any(alias.name == "*" for alias in node.names):
            return
        boundary = _boundary_module_name(node.module)
        if boundary is not None:
            self.add_violation("wildcard import", boundary)
            return
        module = node.module or ""
        if node.level == 0 and module in WILDCARD_IMPORT_MODULES:
            self.add_violation("wildcard import", module)

    def _bind_boundary_from(self, node: ast.ImportFrom, scope: _Scope, boundary: str) -> None:
        for alias in node.names:
            if alias.name == "*":
                continue
            local = alias.asname or alias.name
            if self.enforce_exports and alias.name not in PUBLIC_EXPORTS[boundary]:
                self.add_violation("private import", f"{boundary}.{alias.name}")
            self._bind_twice(scope, node, local, _Binding("boundary_name", (boundary, alias.name)))

    def _bind_shlex_from(self, node: ast.ImportFrom, scope: _Scope) -> None:
        for alias in node.names:
            if alias.name == "*":
                self.add_site("shlex.*")
                continue
            local = alias.asname or alias.name
            if alias.name in SHLEX_EXPORTS:
                self._bind_twice(scope, node, local, _Binding("shlex_callable", (alias.name,)))
                if alias.name in PARSER_SHLEX_ATTRS:
                    self.add_site(f"shlex.{alias.name}")
            else:
                self._bind_twice(scope, node, local, _UNKNOWN)

    def _bind_unknown_aliases(self, node: ast.ImportFrom, scope: _Scope) -> None:
        for alias in node.names:
            if alias.name == "*":
                continue
            local = alias.asname or alias.name
            # ``from package import shell_shlex as shared`` binds the module.
            # ``from shell_shlex import name`` is handled before this method.
            if alias.name in PUBLIC_EXPORTS:
                self._bind_twice(scope, node, local, _Binding("boundary_module", (alias.name,)))
            else:
                self._bind_twice(scope, node, local, _UNKNOWN)

    def _bind_twice(self, scope: _Scope, node: ast.AST, name: str, binding: _Binding) -> None:
        # (0, 1) makes a function-local import visible to earlier uses in that
        # function for literal argv and imported callables. Module names do
        # not use this position: may-bind keeps every one.
        self._bind_at(scope, 0, 1, name, binding)
        self._bind_at(scope, getattr(node, "lineno", 0), getattr(node, "col_offset", 0), name, binding)

    def _visit_stmt(self, node: ast.stmt, scope: _Scope) -> None:
        self._node_scopes[id(node)] = scope
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            self._visit_function(node, scope)
        elif isinstance(node, ast.ClassDef):
            self._visit_class(node, scope)
        elif isinstance(
            node, (ast.Import, ast.ImportFrom, ast.Global, ast.Nonlocal, ast.Pass, ast.Break, ast.Continue)
        ):
            return
        elif isinstance(node, ast.Assign):
            self._visit_assign(node, scope)
        elif isinstance(node, ast.AnnAssign):
            if node.value is not None:
                self._visit_expr(node.value, scope)
            if isinstance(node.target, ast.Name):
                binding = self._value_binding(node.value, scope) if node.value is not None else _UNKNOWN
                scope.bind(node.lineno, node.target.col_offset, node.target.id, binding)
        elif isinstance(node, ast.AugAssign):
            self._visit_expr(node.value, scope)
            self._bind_target(node.target, _UNKNOWN, scope, node)
        elif isinstance(node, (ast.For, ast.AsyncFor)):
            self._visit_expr(node.iter, scope)
            self._bind_target(node.target, _UNKNOWN, scope, node)
            for stmt in node.body:
                self._visit_stmt(stmt, scope)
            for stmt in node.orelse:
                self._visit_stmt(stmt, scope)
        elif isinstance(node, ast.With):
            for item in node.items:
                self._visit_expr(item.context_expr, scope)
                if item.optional_vars is not None:
                    self._bind_target(item.optional_vars, _UNKNOWN, scope, item.optional_vars)
            for stmt in node.body:
                self._visit_stmt(stmt, scope)
        else:
            self._generic(node, scope)

    def _visit_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef, scope: _Scope) -> None:
        for decorator in node.decorator_list:
            self._visit_expr(decorator, scope)
        self._visit_defaults(node.args, scope)
        parent = scope.parent if scope.kind == "class" and scope.parent is not None else scope
        child = _Scope(kind="function", parent=parent, module=scope.module)
        self._bind_arguments(node.args, child, node.lineno)
        self._collect_directives(node.body, child)
        self._symbols.append(node.name)
        self._hoist(node.body, child)
        for stmt in node.body:
            self._visit_stmt(stmt, child)
        self._symbols.pop()

    def _visit_class(self, node: ast.ClassDef, scope: _Scope) -> None:
        for decorator in node.decorator_list:
            self._visit_expr(decorator, scope)
        for base in (*node.bases, *node.keywords):
            value = base.value if isinstance(base, ast.keyword) else base
            self._visit_expr(value, scope)
        child = _Scope(kind="class", parent=scope, module=scope.module)
        self._symbols.append(node.name)
        self._hoist(node.body, child)
        for stmt in node.body:
            self._visit_stmt(stmt, child)
        self._symbols.pop()

    def _visit_defaults(self, args: ast.arguments, scope: _Scope) -> None:
        for default in (*args.defaults, *args.kw_defaults):
            if default is not None:
                self._visit_expr(default, scope)

    def _bind_arguments(self, args: ast.arguments, scope: _Scope, line: int) -> None:
        names = [
            *(arg.arg for arg in (*args.posonlyargs, *args.args, *args.kwonlyargs)),
            *([args.vararg.arg] if args.vararg else []),
            *([args.kwarg.arg] if args.kwarg else []),
        ]
        for name in names:
            scope.bind(line, 0, name, _UNKNOWN)

    def _collect_directives(self, body: list[ast.stmt], scope: _Scope) -> None:
        for stmt in body:
            for node in _iter_directives(stmt):
                if isinstance(node, ast.Global):
                    scope.global_names.update(node.names)
                elif isinstance(node, ast.Nonlocal):
                    scope.nonlocal_names.update(node.names)

    def _visit_assign(self, node: ast.Assign, scope: _Scope) -> None:
        self._visit_expr(node.value, scope)
        binding = self._value_binding(node.value, scope)
        for target in node.targets:
            if isinstance(target, ast.Name):
                scope.bind(node.lineno, target.col_offset, target.id, binding)
            else:
                self._bind_target(target, _UNKNOWN, scope, node)

    def _bind_target(self, target: ast.AST, binding: _Binding, scope: _Scope, node: ast.AST) -> None:
        if isinstance(target, ast.Name):
            scope.bind(getattr(node, "lineno", 0), target.col_offset, target.id, binding)
        elif isinstance(target, (ast.Tuple, ast.List)):
            for elt in target.elts:
                self._bind_target(elt, _UNKNOWN, scope, node)
        elif isinstance(target, ast.Starred):
            self._bind_target(target.value, _UNKNOWN, scope, node)

    def _value_binding(self, node: ast.expr | None, scope: _Scope) -> _Binding:
        if node is None:
            return _UNKNOWN
        if isinstance(node, (ast.Name, ast.Attribute)):
            return self._resolve(node, scope)
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return _Binding("const_str", (node.value,))
        if isinstance(node, (ast.List, ast.Tuple)) and not any(isinstance(elt, ast.Starred) for elt in node.elts):
            return _Binding("const_argv", argv=tuple(self._element_str(elt, scope) for elt in node.elts))
        return _UNKNOWN

    def _visit_expr(
        self,
        node: ast.expr,
        scope: _Scope,
        *,
        as_call_func: bool = False,
        as_attribute_base: bool = False,
    ) -> None:
        self._node_scopes[id(node)] = scope
        if isinstance(node, ast.Call):
            self._visit_call(node, scope)
        elif isinstance(node, ast.Attribute):
            self._visit_attribute(node, scope, as_call_func=as_call_func)
        elif isinstance(node, ast.Name):
            self._visit_name(
                node,
                scope,
                as_call_func=as_call_func,
                as_attribute_base=as_attribute_base,
            )
        elif isinstance(node, ast.Lambda):
            self._visit_defaults(node.args, scope)
            child = _Scope(kind="function", parent=scope, module=scope.module)
            self._bind_arguments(node.args, child, node.lineno)
            self._symbols.append("<lambda>")
            self._visit_expr(node.body, child)
            self._symbols.pop()
        elif isinstance(node, ast.NamedExpr):
            self._visit_expr(node.value, scope)
            if isinstance(node.target, ast.Name):
                scope.bind(node.lineno, node.target.col_offset, node.target.id, self._value_binding(node.value, scope))
        elif isinstance(node, ast.Subscript):
            self._note_mapping_boundary_lookup(node, scope)
            self._generic(node, scope)
        else:
            self._generic(node, scope)

    def _visit_call(self, node: ast.Call, scope: _Scope) -> None:
        identity = self._special_call(node, scope) or self._call_identity(node, scope)
        if identity:
            self.add_site(identity)
        else:
            self._visit_expr(node.func, scope, as_call_func=True)
        for arg in node.args:
            self._visit_expr(arg, scope)
        for keyword in node.keywords:
            if keyword.value is not None:
                self._visit_expr(keyword.value, scope)

    def _visit_attribute(self, node: ast.Attribute, scope: _Scope, *, as_call_func: bool) -> None:
        # ``shlex.split`` on a bound module name is already a site from the
        # parent-map walk. Recording it again here would double the baseline.
        owned_by_name_use = isinstance(node.value, ast.Name) and node.value.id in self._shlex_module_names
        if not as_call_func and not owned_by_name_use:
            identity = _callable_identity(self._resolve(node, scope))
            if identity:
                self.add_site(identity)
        self._visit_expr(node.value, scope, as_attribute_base=True)

    def _visit_name(
        self,
        node: ast.Name,
        scope: _Scope,
        *,
        as_call_func: bool,
        as_attribute_base: bool = False,
    ) -> None:
        if as_call_func or as_attribute_base or not isinstance(node.ctx, ast.Load):
            return
        identity = _callable_identity(self._resolve(node, scope))
        if identity:
            self.add_site(identity)

    def _boundary_modules_of(self, node: ast.expr, scope: _Scope) -> list[str]:
        if isinstance(node, ast.Name):
            modules = self._boundary_names.get(node.id)
            if modules:
                return sorted(modules)
        binding = self._resolve(node, scope)
        if binding.kind == "boundary_module":
            return [binding.detail[0]]
        return []

    def _dynamic_canonical(self, node: ast.expr) -> str | None:
        if isinstance(node, ast.Name) and node.id in self._dynamic_aliases:
            return self._dynamic_aliases[node.id]
        return None

    def _argument_boundary_modules(self, node: ast.expr, scope: _Scope) -> list[str]:
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            leaf = node.value.rsplit(".", 1)[-1]
            if leaf in PUBLIC_EXPORTS:
                return [leaf]
            return []
        return self._boundary_modules_of(node, scope)

    def _note_mapping_boundary_lookup(self, node: ast.Subscript, scope: _Scope) -> None:
        """``globals()['shell_shlex']`` and ``vars()['shell_redirects']`` name the module."""
        if not self.enforce_exports or not isinstance(node.value, ast.Call):
            return
        canonical = self._dynamic_canonical(node.value.func)
        if canonical not in {"globals", "vars"}:
            return
        for module in self._argument_boundary_modules(node.slice, scope):
            self.add_violation("dynamic access", f"{canonical} {module}")

    def _note_dynamic_boundary_arguments(self, node: ast.Call, scope: _Scope, canonical: str) -> None:
        if not self.enforce_exports:
            return
        values = list(node.args)
        values.extend(keyword.value for keyword in node.keywords if keyword.value is not None)
        for value in values:
            for module in self._argument_boundary_modules(value, scope):
                self.add_violation("dynamic access", f"{canonical} {module}")

    def _special_call(self, node: ast.Call, scope: _Scope) -> str | None:
        canonical = self._dynamic_canonical(node.func)
        if canonical == "getattr" and node.args:
            target = self._resolve(node.args[0], scope)
            attr = self._const_str(node.args[1], scope) if len(node.args) > 1 else None
            if target.kind == "boundary_module" and self.enforce_exports:
                shown = attr if attr is not None else "<dynamic>"
                self.add_violation("dynamic access", f"getattr {target.detail[0]}.{shown}")
            elif target.kind == "shlex_module" and attr in PARSER_SHLEX_ATTRS:
                return f"shlex.{attr}"
            elif target.kind == "parser_lib":
                library = target.detail[0]
                return f"{library}.{attr}" if attr else f"import:{library}"
            self._note_dynamic_boundary_arguments(node, scope, "getattr")
            return None
        if canonical in {"vars", "globals", "__import__"}:
            self._note_dynamic_boundary_arguments(node, scope, canonical)
            if canonical == "__import__" and node.args:
                self._note_imported_string(self._const_str(node.args[0], scope))
            return None
        if self._is_unbound_name(node.func, scope, "__import__") and node.args:
            self._note_imported_string(self._const_str(node.args[0], scope))
            return None
        func = self._resolve(node.func, scope)
        if func.kind == "import_module" or (
            isinstance(node.func, ast.Attribute)
            and node.func.attr == "import_module"
            and self._resolve(node.func.value, scope).kind == "importlib_module"
        ):
            text = self._const_str(node.args[0], scope) if node.args else None
            self._note_imported_string(text)
        return None

    def _note_imported_string(self, text: str | None) -> None:
        if text is None:
            return
        if _is_test_module(text):
            self.add_violation("test-only bash oracle", f"imports {text}")
        elif self.enforce_exports and _boundary_module_name(text) is not None:
            self.add_violation("dynamic access", f"import_module {text}")

    def _is_unbound_name(self, node: ast.expr, scope: _Scope, name: str) -> bool:
        if not isinstance(node, ast.Name) or node.id != name:
            return False
        return scope.lookup(name, node.lineno, node.col_offset) is None

    def _call_identity(self, node: ast.Call, scope: _Scope) -> str | None:
        binding = self._resolve(node.func, scope)
        if binding.kind == "shlex_callable" and binding.detail[0] in PARSER_SHLEX_ATTRS:
            if (
                isinstance(node.func, ast.Attribute)
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id in self._shlex_module_names
            ):
                return None
            return f"shlex.{binding.detail[0]}"
        if binding.kind == "parser_attr":
            return f"{binding.detail[0]}.{binding.detail[1]}"
        if binding.kind == "parser_lib":
            return f"call:{binding.detail[0]}"
        # Runner calls are judged by the total walk, not here.
        return None

    def _call_syntax_identity(self, node: ast.Call, scope: _Scope) -> str | None:
        for binding in self._possible_runners(node.func):
            identity = _first_syntax_identity(self._runner_argvs(node, scope, binding))
            if identity:
                return identity
        return None

    def _match_syntax_identity(self, node: ast.MatchClass, scope: _Scope) -> str | None:
        for binding in self._possible_runners(node.cls):
            identity = _first_syntax_identity(self._match_runner_argvs(node, scope, binding))
            if identity:
                return identity
        return None

    def _match_command_pattern(self, node: ast.MatchClass) -> ast.pattern | None:
        for attr, pattern in zip(node.kwd_attrs, node.kwd_patterns, strict=True):
            if attr == "args":
                return pattern
        if node.patterns:
            return node.patterns[0]
        return None

    def _match_runner_argv(
        self, node: ast.MatchClass, scope: _Scope, binding: _Binding
    ) -> tuple[str | None, ...] | None:
        """Argv of a class pattern, using the same shapes as ``_runner_argv``."""
        family, func = binding.detail
        if family == "subprocess" or func in OS_STRING_FUNCS or func in ASYNCIO_SHELL_FUNCS:
            pattern = self._match_command_pattern(node)
            if pattern is None:
                return None
            return self._static_pattern(pattern, scope)
        if func in OS_ARGV_SECOND_FUNCS and len(node.patterns) >= 2:
            argv = self._static_pattern(node.patterns[1], scope)
            if argv is not None:
                return argv
            exe = self._pattern_element(node.patterns[0], scope)
            return (exe,) if exe is not None else None
        if func in OS_EXEC_LIST_FUNCS and node.patterns:
            values = tuple(self._pattern_element(pattern, scope) for pattern in node.patterns)
            if values[0] is None and all(item is None for item in values):
                return None
            return values
        if func in OS_SPAWN_ARGV_FUNCS and len(node.patterns) >= 3:
            argv = self._static_pattern(node.patterns[2], scope)
            if argv is not None:
                return argv
            exe = self._pattern_element(node.patterns[1], scope)
            return (exe,) if exe is not None else None
        if func in OS_SPAWN_LIST_FUNCS and len(node.patterns) >= 2:
            values = tuple(self._pattern_element(pattern, scope) for pattern in node.patterns[1:])
            if values[0] is None and all(item is None for item in values):
                return None
            return values
        if func in ASYNCIO_EXEC_FUNCS and node.patterns:
            values = tuple(self._pattern_element(pattern, scope) for pattern in node.patterns)
            if values[0] is None and all(item is None for item in values):
                return None
            return values
        return None

    def _static_pattern(self, pattern: ast.pattern, scope: _Scope) -> tuple[str | None, ...] | None:
        if isinstance(pattern, ast.MatchAs):
            if pattern.pattern is None:
                return None
            return self._static_pattern(pattern.pattern, scope)
        if isinstance(pattern, ast.MatchOr):
            fallback: tuple[str | None, ...] | None = None
            for alternative in pattern.patterns:
                found = self._static_pattern(alternative, scope)
                if found is None:
                    continue
                if _syntax_identity(found) is not None:
                    return found
                if fallback is None:
                    fallback = found
            return fallback
        if isinstance(pattern, ast.MatchSequence):
            if any(isinstance(part, ast.MatchStar) for part in pattern.patterns):
                return None
            return tuple(self._pattern_element(part, scope) for part in pattern.patterns)
        if isinstance(pattern, ast.MatchValue):
            return self._static_command(pattern.value, scope)
        return None

    def _pattern_element(self, pattern: ast.pattern, scope: _Scope) -> str | None:
        if isinstance(pattern, ast.MatchAs):
            if pattern.pattern is None:
                return None
            return self._pattern_element(pattern.pattern, scope)
        if not isinstance(pattern, ast.MatchValue):
            return None
        return self._const_str(pattern.value, scope)

    def _runner_argvs(self, node: ast.Call, scope: _Scope, binding: _Binding) -> list[tuple[str | None, ...]]:
        """Literal commands visible on a runner call.

        The signature-specific argv stays first so an existing positional form
        keeps its identity. Every other literal argument is then judged with
        the same rules, whatever its keyword name is.
        """
        found: list[tuple[str | None, ...]] = []
        specific = self._runner_argv(node, scope, binding)
        if specific is not None:
            found.append(specific)
        for expr in self._call_argument_exprs(node):
            argv = self._static_command(expr, scope)
            if argv is not None:
                found.append(argv)
        return found

    def _match_runner_argvs(
        self, node: ast.MatchClass, scope: _Scope, binding: _Binding
    ) -> list[tuple[str | None, ...]]:
        found: list[tuple[str | None, ...]] = []
        specific = self._match_runner_argv(node, scope, binding)
        if specific is not None:
            found.append(specific)
        for pattern in (*node.patterns, *node.kwd_patterns):
            argv = self._static_pattern(pattern, scope)
            if argv is not None:
                found.append(argv)
        return found

    def _call_argument_exprs(self, node: ast.Call) -> list[ast.expr]:
        """Positional arguments, keyword values, and visible starred literals."""
        exprs: list[ast.expr] = []
        for arg in node.args:
            if isinstance(arg, ast.Starred):
                exprs.extend(self._unpacked_literal(arg.value))
            else:
                exprs.append(arg)
        for keyword in node.keywords:
            if keyword.value is None:
                continue
            if keyword.arg is None:
                exprs.extend(self._unpacked_literal(keyword.value))
            else:
                exprs.append(keyword.value)
        return exprs

    def _unpacked_literal(self, node: ast.expr) -> list[ast.expr]:
        """Values inside a statically visible ``*`` or ``**`` literal.

        A list or tuple is itself a literal argv, and its elements are values.
        A dict exposes its values. A starred name is not a literal.
        """
        if isinstance(node, (ast.List, ast.Tuple)):
            values: list[ast.expr] = [node]
            for elt in node.elts:
                if not isinstance(elt, ast.Starred):
                    values.append(elt)
            return values
        if isinstance(node, ast.Dict):
            values = []
            for key, value in zip(node.keys, node.values, strict=True):
                if value is None:
                    continue
                if key is None:
                    values.extend(self._unpacked_literal(value))
                else:
                    values.append(value)
            return values
        return []

    def _runner_argv(self, node: ast.Call, scope: _Scope, binding: _Binding) -> tuple[str | None, ...] | None:
        family, func = binding.detail
        if family == "subprocess" or func in OS_STRING_FUNCS or func in ASYNCIO_SHELL_FUNCS:
            command = self._command_arg(node)
            if command is None:
                return None
            return self._static_command(command, scope)
        if func in OS_ARGV_SECOND_FUNCS and len(node.args) >= 2:
            argv = self._static_command(node.args[1], scope)
            if argv is not None:
                return argv
            exe = self._const_str(node.args[0], scope)
            return (exe,) if exe is not None else None
        if func in OS_EXEC_LIST_FUNCS and node.args:
            values = tuple(self._element_str(arg, scope) for arg in node.args)
            if values[0] is None and all(item is None for item in values):
                return None
            return values
        if func in OS_SPAWN_ARGV_FUNCS and len(node.args) >= 3:
            # ``spawnv(mode, path, argv)``: the mode is not the program.
            argv = self._static_command(node.args[2], scope)
            if argv is not None:
                return argv
            exe = self._const_str(node.args[1], scope)
            return (exe,) if exe is not None else None
        if func in OS_SPAWN_LIST_FUNCS and len(node.args) >= 2:
            values = tuple(self._element_str(arg, scope) for arg in node.args[1:])
            if values[0] is None and all(item is None for item in values):
                return None
            return values
        if func in ASYNCIO_EXEC_FUNCS and node.args:
            values = tuple(self._element_str(arg, scope) for arg in node.args)
            if values[0] is None and all(item is None for item in values):
                return None
            return values
        return None

    def _command_arg(self, node: ast.Call) -> ast.expr | None:
        for keyword in node.keywords:
            if keyword.arg == "args":
                return keyword.value
        if node.args:
            return node.args[0]
        return None

    def _static_command(self, node: ast.expr, scope: _Scope) -> tuple[str | None, ...] | None:
        if isinstance(node, ast.Name):
            binding = scope.lookup(node.id, node.lineno, node.col_offset)
            if binding is None:
                return None
            if binding.kind == "const_argv" and binding.argv is not None:
                return binding.argv
            if binding.kind == "const_str":
                return _split_command(binding.detail[0])
            return None
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return _split_command(node.value)
        if isinstance(node, ast.JoinedStr) and all(isinstance(part, ast.Constant) for part in node.values):
            return _split_command("".join(part.value for part in node.values if isinstance(part.value, str)))
        if isinstance(node, (ast.List, ast.Tuple)):
            if any(isinstance(elt, ast.Starred) for elt in node.elts):
                return None
            return tuple(self._element_str(elt, scope) for elt in node.elts)
        return None

    def _element_str(self, node: ast.expr, scope: _Scope) -> str | None:
        return self._const_str(node, scope)

    def _const_str(self, node: ast.expr, scope: _Scope) -> str | None:
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value
        if isinstance(node, ast.Name):
            binding = scope.lookup(node.id, node.lineno, node.col_offset)
            if binding is not None and binding.kind == "const_str":
                return binding.detail[0]
        return None

    def _resolve(self, node: ast.expr, scope: _Scope) -> _Binding:
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
            found = scope.lookup(node.id, node.lineno, node.col_offset)
            return found if found is not None else _UNKNOWN
        if isinstance(node, ast.Attribute):
            return _resolve_attribute(self._resolve(node.value, scope), node.attr)
        return _UNKNOWN

    def _generic(self, node: ast.AST, scope: _Scope) -> None:
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.stmt):
                self._visit_stmt(child, scope)
            elif isinstance(child, ast.expr):
                self._visit_expr(child, scope)
            else:
                self._generic(child, scope)


def _callable_identity(binding: _Binding) -> str | None:
    if binding.kind == "shlex_callable" and binding.detail[0] in PARSER_SHLEX_ATTRS:
        return f"shlex.{binding.detail[0]}"
    if binding.kind == "parser_attr":
        return f"{binding.detail[0]}.{binding.detail[1]}"
    if binding.kind == "parser_lib":
        return f"import:{binding.detail[0]}"
    return None


def _resolve_attribute(base: _Binding, attr: str) -> _Binding:
    if base.kind == "shlex_module" and attr in SHLEX_EXPORTS:
        return _Binding("shlex_callable", (attr,))
    if base.kind == "parser_lib":
        return _Binding("parser_attr", (base.detail[0], attr))
    if base.kind == "boundary_module":
        return _Binding("boundary_attr", (base.detail[0], attr))
    if base.kind == "importlib_module" and attr == "import_module":
        return _Binding("import_module")
    return _UNKNOWN


def _split_command(command: str) -> tuple[str | None, ...] | None:
    try:
        return tuple(shlex.split(command, posix=True))
    except ValueError:
        return None


def _iter_imports(node: ast.AST) -> list[ast.AST]:
    found: list[ast.AST] = []

    def walk(current: ast.AST) -> None:
        if isinstance(current, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)):
            return
        if isinstance(current, (ast.Import, ast.ImportFrom)):
            found.append(current)
            return
        for child in ast.iter_child_nodes(current):
            walk(child)

    walk(node)
    return found


def _iter_directives(node: ast.AST) -> list[ast.AST]:
    found: list[ast.AST] = []

    def walk(current: ast.AST) -> None:
        if isinstance(current, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)):
            return
        if isinstance(current, (ast.Global, ast.Nonlocal)):
            found.append(current)
        for child in ast.iter_child_nodes(current):
            walk(child)

    walk(node)
    return found


def analyze_source(path: str, source: str) -> tuple[list[Site], list[Violation]]:
    record_sites = path not in BOUNDARY_PATHS
    enforce_exports = record_sites and path not in WHITE_BOX_TESTS
    analyzer = _Analyzer(path, record_sites=record_sites, enforce_exports=enforce_exports)
    if _is_deployed_oracle(path):
        analyzer.add_violation("test-only bash oracle", "deployed with production hooks")
    try:
        tree = ast.parse(source, filename=path)
    except SyntaxError as exc:
        analyzer.add_violation("syntax error", exc.msg or "syntax error")
        return analyzer.sites, analyzer.violations
    analyzer.analyze(tree)
    return analyzer.sites, analyzer.violations


def _module_file(module: str, exists) -> str | None:
    relative = module.replace(".", "/") + ".py"
    package = module.replace(".", "/") + "/__init__.py"
    if exists(relative):
        return relative
    if exists(package):
        return package
    return None


def _import_facts(tree: ast.AST) -> list[tuple[str | None, tuple[str, ...], int, bool]]:
    """Imports as ``(module, names, level, inside_function)``.

    Class bodies run at import time, so they are not marked as function-local.
    """
    found: list[tuple[str | None, tuple[str, ...], int, bool]] = []

    def walk(node: ast.AST, inside_function: bool) -> None:
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
                walk(child, True)
                continue
            if isinstance(child, ast.ClassDef):
                walk(child, inside_function)
                continue
            if isinstance(child, ast.Import):
                for alias in child.names:
                    found.append((alias.name, (), 0, inside_function))
                continue
            if isinstance(child, ast.ImportFrom):
                names = tuple(alias.name for alias in child.names if alias.name != "*")
                found.append((child.module, names, child.level, inside_function))
                continue
            walk(child, inside_function)

    walk(tree, False)
    return found


def _package_directory(path: str) -> str:
    return path.rsplit("/", 1)[0] if "/" in path else ""


def _resolve_imported_module(importer: str, module: str | None, level: int) -> str | None:
    """Resolve ``module`` from ``importer``, applying a relative import level."""
    if level <= 0:
        return module
    parts = importer.split("/")[:-1]
    keep = len(parts) - level + 1
    if keep < 0:
        return None
    base = parts[:keep]
    if module:
        base.extend(module.split("."))
    if not base:
        return None
    return ".".join(base)


def _follow_helper_import(importer: str, helper: str, *, inside_function: bool, level: int) -> bool:
    """Decide whether a helper import extends the hook's parser chain.

    Hook files start a chain from every import, including imports written
    inside functions. A reached helper then follows its import-time imports
    and its relative or same-package imports, transitively and cycle-safe.
    A function-local absolute import that leaves the helper's package is not
    followed: the session-start hook reaches application modules that already
    call ``shlex.split``, and those calls are not hook parsers.
    """
    if _is_hook_path(importer):
        return True
    if not inside_function or level > 0:
        return True
    package = _package_directory(importer)
    return bool(package) and helper.startswith(package + "/")


def _helper_paths(module: str | None, names: tuple[str, ...], exists) -> list[str]:
    if module is None or _is_test_module(module):
        return []
    paths: list[str] = []
    parts = module.split(".")
    for index in range(1, len(parts) + 1):
        package = "/".join(parts[:index]) + "/__init__.py"
        if index < len(parts) and exists(package):
            paths.append(package)
    parent = _module_file(module, exists)
    if parent is not None and not _is_hook_path(parent):
        paths.append(parent)
    for name in names:
        if name == "*":
            continue
        submodule = _module_file(f"{module}.{name}", exists)
        if submodule is not None and not _is_hook_path(submodule):
            paths.append(submodule)
    return paths


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def analyze_files(sources: dict[str, str], *, root: Path | None = None) -> Check:
    """Analyze an overlay of repo-relative sources. ``root`` fills helpers that are not overlaid."""

    def exists(relative: str) -> bool:
        if ".." in relative.split("/") or relative.startswith("/"):
            return False
        if relative in sources:
            return True
        return root is not None and (root / relative).is_file()

    hook_files = tuple(sorted(path for path in sources if _is_hook_path(path)))
    helpers: set[str] = set()
    extra: list[Violation] = []
    seen = set(hook_files)
    queue = list(hook_files)
    while queue:
        path = queue.pop(0)
        source = sources.get(path)
        if source is None and root is not None and exists(path):
            try:
                source = _read(root / path)
            except (OSError, UnicodeError):
                continue
            sources[path] = source
        if source is None:
            continue
        try:
            tree = ast.parse(source, filename=path)
        except SyntaxError:
            continue
        for module, names, level, inside_function in _import_facts(tree):
            resolved = _resolve_imported_module(path, module, level)
            if resolved is None or _is_test_module(resolved):
                continue
            for helper in _helper_paths(resolved, names, exists):
                if helper in seen or helper in BOUNDARY_PATHS:
                    continue
                if not _follow_helper_import(
                    path,
                    helper,
                    inside_function=inside_function,
                    level=level,
                ):
                    continue
                seen.add(helper)
                helpers.add(helper)
                queue.append(helper)
    ordered_helpers = tuple(sorted(helpers))
    sites: list[Site] = []
    violations = list(extra)
    for path in (*hook_files, *ordered_helpers):
        if path not in sources:
            if root is None:
                continue
            try:
                sources[path] = _read(root / path)
            except (OSError, UnicodeError) as exc:
                violations.append(Violation("unreadable hook file", path, "<module>", type(exc).__name__))
                continue
        file_sites, file_violations = analyze_source(path, sources[path])
        sites.extend(file_sites)
        violations.extend(file_violations)
    return Check(tuple(sites), tuple(violations), hook_files, ordered_helpers)


def discover_hook_files(root: Path) -> tuple[str, ...]:
    found: list[str] = []
    agents = root / "agents_extensions"
    if agents.is_dir():
        for entry in sorted(agents.iterdir()):
            hooks = entry / "hooks"
            if not hooks.is_dir():
                continue
            for path in sorted(hooks.rglob("*.py")):
                if "__pycache__" in path.parts:
                    continue
                found.append(path.relative_to(root).as_posix())
    scripts_hooks = root / "scripts" / "hooks"
    if scripts_hooks.is_dir():
        for path in sorted(scripts_hooks.rglob("*.py")):
            if "__pycache__" in path.parts:
                continue
            found.append(path.relative_to(root).as_posix())
    return tuple(found)


def analyze_repository(root: Path = REPO_ROOT) -> Check:
    sources: dict[str, str] = {}
    violations: list[Violation] = []
    hook_files = discover_hook_files(root)
    for relative in hook_files:
        try:
            sources[relative] = _read(root / relative)
        except (OSError, UnicodeError) as exc:
            violations.append(Violation("unreadable hook file", relative, "<module>", type(exc).__name__))
    check = analyze_files(sources, root=root)
    return Check(check.sites, violations + list(check.violations), hook_files, check.production_helpers)


def load_baseline(path: Path = FIXTURE_PATH) -> tuple[Site, ...]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("pinned_size_at_creation") != BASELINE_SIZE_AT_CREATION:
        raise AssertionError(f"fixture pin {payload.get('pinned_size_at_creation')} != {BASELINE_SIZE_AT_CREATION}")
    if frozenset(payload.get("boundary", ())) != BOUNDARY_PATHS:
        raise AssertionError(f"fixture boundary {payload.get('boundary')} != {sorted(BOUNDARY_PATHS)}")
    sites = []
    for item in payload["sites"]:
        sites.append(Site(item["path"], item["enclosing_symbol"], item["site_identity"]))
    return tuple(sites)


def creation_set_gap(
    baseline: tuple[Site, ...] | list[Site],
    frozen: tuple[Site, ...] | list[Site],
) -> list[str]:
    """Sites ``baseline`` adds or drops relative to a frozen creation set.

    Equality is required. Dropping a frozen site is a shrink that did not edit
    the frozen set. Adding a site the frozen set no longer contains is regrowth.
    """
    creation = Counter(site.key() for site in frozen)
    found = Counter(site.key() for site in baseline)
    reasons: list[str] = []
    for key in sorted(found - creation):
        count = found[key] - creation[key]
        site = Site(*key)
        reasons.extend([f"outside creation set: {site.format()}"] * count)
    for key in sorted(creation - found):
        count = creation[key] - found[key]
        site = Site(*key)
        reasons.extend([f"shrunk creation site: {site.format()}"] * count)
    return reasons


def outside_creation_set(baseline: tuple[Site, ...] | list[Site]) -> list[str]:
    """The on-disk fixture must equal ``CREATION_SITES`` exactly."""
    return creation_set_gap(baseline, CREATION_SITES)


def compare_baseline(check: Check, baseline: tuple[Site, ...] | list[Site], *, pinned_size: int) -> list[str]:
    reasons = [violation.format() for violation in check.violations]
    if len(baseline) > pinned_size:
        reasons.append(f"baseline growth: {len(baseline)} sites exceed pinned creation size {pinned_size}")
    observed = Counter(site.key() for site in check.sites)
    expected = Counter(site.key() for site in baseline)
    for key in sorted(observed - expected):
        count = observed[key] - expected[key]
        site = Site(*key)
        reasons.extend([f"new parser site: {site.format()}"] * count)
    for key in sorted(expected - observed):
        count = expected[key] - observed[key]
        site = Site(*key)
        reasons.extend([f"stale baseline site: {site.format()}"] * count)
    return reasons


def _overlay_reasons(
    sources: dict[str, str], baseline: list[Site], *, pinned_size: int = BASELINE_SIZE_AT_CREATION
) -> list[str]:
    return compare_baseline(analyze_files(sources), baseline, pinned_size=pinned_size)


def _single(
    source: str, baseline: list[Site] | None = None, *, path: str = "agents_extensions/shared/hooks/mutant.py"
) -> list[str]:
    return _overlay_reasons({path: source}, [] if baseline is None else baseline)


def _site(path: str, symbol: str, identity: str) -> Site:
    return Site(path, symbol, identity)


def test_observed_sites_match_frozen_baseline() -> None:
    check = analyze_repository()
    baseline = load_baseline()
    reasons = compare_baseline(check, baseline, pinned_size=BASELINE_SIZE_AT_CREATION)
    reasons.extend(outside_creation_set(baseline))
    observed = "\n".join(site.format() for site in check.sites)
    assert reasons == [], "\n".join(reasons) + "\nobserved:\n" + observed
    assert len(CREATION_SITES) == BASELINE_SIZE_AT_CREATION
    assert Counter(site.key() for site in baseline) == Counter(site.key() for site in CREATION_SITES)
    assert len(baseline) == BASELINE_SIZE_AT_CREATION
    assert not any(site.path in BOUNDARY_PATHS for site in check.sites)


def test_public_exports_match_definitions_and_consumers() -> None:
    sources = {path: _read(REPO_ROOT / path) for path in BOUNDARY_PATHS}
    computed = {Path(path).stem: public_definitions(sources[path]) for path in BOUNDARY_PATHS}
    assert computed == PUBLIC_EXPORTS
    hook_sources = {relative: _read(REPO_ROOT / relative) for relative in discover_hook_files(REPO_ROOT)}
    assert consumer_imports(hook_sources) == CONSUMER_IMPORTS
    for module, names in CONSUMER_IMPORTS.items():
        assert names <= PUBLIC_EXPORTS[module]


def test_production_helpers_imported_by_hooks_are_scanned() -> None:
    check = analyze_repository()
    missing = REQUIRED_PRODUCTION_HELPERS - set(check.production_helpers)
    assert not missing, sorted(missing)
    assert all(not helper.startswith("tests/") for helper in check.production_helpers)


def test_secret_print_quote_tracker_is_not_detected() -> None:
    check = analyze_repository()
    symbols = {
        site.enclosing_symbol
        for site in check.sites
        if site.path == "agents_extensions/shared/hooks/guard-secret-print.py"
    }
    assert symbols == {"_shell_script.decode"}
    assert "_strip_shell_comments" not in symbols


def test_checker_is_not_deployed_with_hooks() -> None:
    relative = Path(__file__).resolve().relative_to(REPO_ROOT).as_posix()
    assert relative == "tests/test_hook_single_parser.py"
    assert not _is_hook_path(relative)
    check = analyze_repository()
    assert not any("test-only bash oracle" in violation.kind for violation in check.violations)


def test_direct_parser_reference_fails() -> None:
    source = "import shlex\n\ndef parse(command):\n    return shlex.split(command, posix=True)\n"
    reasons = _single(source)
    assert any(
        reason == "new parser site: agents_extensions/shared/hooks/mutant.py::parse::shlex.split" for reason in reasons
    )


def test_aliased_parser_reference_fails() -> None:
    source = (
        "import shlex as shell_lex\n"
        "from shlex import shlex as make_lexer\n"
        "from shlex import split as quote\n"
        "\n"
        "def parse(command):\n"
        "    shell_lex.split(command)\n"
        "    return make_lexer(command, posix=True)\n"
        "\n"
        "def renamed(command):\n"
        "    return quote(command)\n"
    )
    reasons = _single(source)
    assert any(reason.endswith("::parse::shlex.split") for reason in reasons)
    assert any(reason.endswith("::parse::shlex.shlex") for reason in reasons)
    assert any(reason.endswith("::renamed::shlex.split") for reason in reasons)
    joined = "\n".join(reasons)
    assert "shlex.quote" not in joined
    assert "shlex.join" not in joined


def test_quote_and_join_only_pass() -> None:
    source = (
        "import re\n"
        "import shlex\n"
        "import subprocess\n"
        "from shlex import join as join_words\n"
        "from shlex import quote as split\n"
        "\n"
        "def emit(argv):\n"
        "    quoted = []\n"
        "    for arg in argv:\n"
        "        quoted.append(split(arg))\n"
        "    pattern = re.compile(r'[^ ]+')\n"
        "    subprocess.run(['git', 'status'], check=False)\n"
        "    subprocess.run(['make', '-n', 'preview'], check=False)\n"
        "    note = 'shlex.split is only mentioned here'\n"
        "    return shlex.join(quoted) + join_words(argv) + shlex.quote(argv[0]) + note + pattern.pattern\n"
    )
    assert _single(source) == []


def test_handwritten_quote_tracker_passes() -> None:
    source = (
        "def strip_comments(command):\n"
        "    out = []\n"
        "    quote = ''\n"
        "    index = 0\n"
        "    while index < len(command):\n"
        "        char = command[index]\n"
        "        if char == \"'\" and quote != '\"':\n"
        "            quote = '' if quote == \"'\" else \"'\"\n"
        "        elif char == '\"' and quote != \"'\":\n"
        "            quote = '' if quote == '\"' else '\"'\n"
        "        elif not quote and char == '#':\n"
        "            break\n"
        "        out.append(char)\n"
        "        index += 1\n"
        "    return ''.join(out)\n"
    )
    assert _single(source) == []


def test_private_import_fails() -> None:
    source = "from shell_shlex import _tokenize as tokenize\nfrom shell_redirects import _split_scopes\n"
    reasons = _single(source)
    assert any("private import: " in reason and "shell_shlex._tokenize" in reason for reason in reasons)
    assert any("private import: " in reason and "shell_redirects._split_scopes" in reason for reason in reasons)


def test_private_attribute_access_fails() -> None:
    source = (
        "import shell_shlex as shared\n"
        "import shell_redirects as redirects\n"
        "\n"
        "def hidden():\n"
        "    return shared._MAX_BACKTICK_DEPTH\n"
        "\n"
        "def parse(line):\n"
        "    return redirects._tokenize(line)\n"
    )
    reasons = _single(source)
    assert any("private attribute: " in reason and "shell_shlex._MAX_BACKTICK_DEPTH" in reason for reason in reasons)
    assert any("private attribute: " in reason and "shell_redirects._tokenize" in reason for reason in reasons)


def test_wildcard_import_fails() -> None:
    source = "from shell_shlex import *\nfrom shell_redirects import *\n"
    reasons = _single(source)
    assert any("wildcard import: " in reason and reason.endswith("::shell_shlex") for reason in reasons)
    assert any("wildcard import: " in reason and reason.endswith("::shell_redirects") for reason in reasons)


def test_dynamic_access_fails() -> None:
    source = (
        "import importlib\n"
        "import shell_shlex\n"
        "\n"
        "def read(name):\n"
        "    return getattr(shell_shlex, name)\n"
        "\n"
        "def load():\n"
        "    return importlib.import_module('shell_redirects')\n"
    )
    reasons = _single(source)
    assert any("dynamic access: " in reason and "getattr shell_shlex" in reason for reason in reasons)
    assert any("dynamic access: " in reason and "import_module shell_redirects" in reason for reason in reasons)


def test_same_count_replacement_fails() -> None:
    path = "agents_extensions/shared/hooks/mutant.py"
    source = "import shlex\n\ndef parse(command):\n    return shlex.shlex(command, posix=True)\n"
    baseline = [_site(path, "parse", "shlex.split")]
    check = analyze_files({path: source})
    assert len(check.sites) == len(baseline)
    reasons = compare_baseline(check, baseline, pinned_size=BASELINE_SIZE_AT_CREATION)
    assert any(reason.endswith("::parse::shlex.shlex") and reason.startswith("new parser site") for reason in reasons)
    assert any(
        reason.endswith("::parse::shlex.split") and reason.startswith("stale baseline site") for reason in reasons
    )
    assert not any(reason.startswith("baseline growth") for reason in reasons)


def test_partial_baseline_shrink_fails() -> None:
    path = "agents_extensions/shared/hooks/mutant.py"
    source = (
        "import shlex\n"
        "\n"
        "def first(command):\n"
        "    return shlex.split(command)\n"
        "\n"
        "def second(command):\n"
        "    return shlex.shlex(command)\n"
    )
    baseline = [_site(path, "first", "shlex.split")]
    check = analyze_files({path: source})
    assert len(check.sites) == 2
    assert len(baseline) < len(check.sites)
    reasons = compare_baseline(check, baseline, pinned_size=BASELINE_SIZE_AT_CREATION)
    assert any(reason == f"new parser site: {path}::second::shlex.shlex" for reason in reasons)
    assert not any(reason.startswith("stale baseline site") for reason in reasons)
    assert not any(reason.startswith("baseline growth") for reason in reasons)


def test_baseline_growth_fails() -> None:
    sources: dict[str, str] = {}
    baseline: list[Site] = []
    for index in range(BASELINE_SIZE_AT_CREATION + 1):
        path = f"agents_extensions/shared/hooks/extra_{index}.py"
        sources[path] = "import shlex\n\ndef parse(command):\n    return shlex.split(command)\n"
        baseline.append(_site(path, "parse", "shlex.split"))
    check = analyze_files(sources)
    assert len(check.sites) == len(baseline) == BASELINE_SIZE_AT_CREATION + 1
    reasons = compare_baseline(check, baseline, pinned_size=BASELINE_SIZE_AT_CREATION)
    assert reasons == [
        f"baseline growth: {BASELINE_SIZE_AT_CREATION + 1} sites exceed pinned creation size {BASELINE_SIZE_AT_CREATION}"
    ]


def test_full_baseline_shrink_passes() -> None:
    path = "agents_extensions/shared/hooks/mutant.py"
    source = "import shlex\n\ndef parse(command):\n    shlex.quote(command)\n"
    assert compare_baseline(analyze_files({path: source}), [], pinned_size=BASELINE_SIZE_AT_CREATION) == []


def test_external_syntax_check_call_fails() -> None:
    source = (
        "import os\n"
        "import subprocess\n"
        "from subprocess import run\n"
        "import subprocess as sp\n"
        "\n"
        "def check(path):\n"
        "    subprocess.run(['bash', '-n', path])\n"
        "    sp.call(('sh', '-n', path))\n"
        "    run(['/usr/bin/bash', '--posix', '-n', path])\n"
        "    os.system('bash -n hook.sh')\n"
        "    argv = ['sh', '-n', 'hook.sh']\n"
        "    subprocess.run(argv)\n"
    )
    reasons = _single(source)
    assert any(reason.endswith("::check::syntax:bash -n") for reason in reasons)
    assert any(reason.endswith("::check::syntax:sh -n") for reason in reasons)
    assert sum(reason.endswith("::check::syntax:bash -n") for reason in reasons) >= 2
    assert sum(reason.endswith("::check::syntax:sh -n") for reason in reasons) >= 2


def test_unreadable_hook_file_fails(tmp_path: Path) -> None:
    target = tmp_path / "agents_extensions" / "shared" / "hooks" / "broken.py"
    target.parent.mkdir(parents=True)
    target.write_bytes(b"\xff\xfe not utf-8")
    check = analyze_repository(tmp_path)
    assert any(
        violation.kind == "unreadable hook file" and violation.path.endswith("broken.py")
        for violation in check.violations
    )


def test_syntax_error_fails() -> None:
    reasons = _single("def (\n")
    assert any(reason.startswith("syntax error:") for reason in reasons)


def test_imported_helper_parser_site_fails() -> None:
    sources = {
        "agents_extensions/shared/hooks/guard.py": "from scripts.parsing.helper import tokenize\n",
        "scripts/parsing/helper.py": "import shlex\n\ndef tokenize(command):\n    return shlex.split(command)\n",
    }
    check = analyze_files(sources)
    assert "scripts/parsing/helper.py" in check.production_helpers
    reasons = compare_baseline(check, [], pinned_size=BASELINE_SIZE_AT_CREATION)
    assert any(reason == "new parser site: scripts/parsing/helper.py::tokenize::shlex.split" for reason in reasons)


def test_quote_only_helper_is_not_a_parser_site() -> None:
    sources = {
        "agents_extensions/shared/hooks/guard.py": "from scripts.parsing.helper import emit\n",
        "scripts/parsing/helper.py": "import shlex\n\ndef emit(text):\n    return shlex.quote(text)\n",
    }
    check = analyze_files(sources)
    assert check.sites == ()
    assert compare_baseline(check, [], pinned_size=BASELINE_SIZE_AT_CREATION) == []


def test_white_box_tests_may_import_private_names() -> None:
    source = "from shell_shlex import _expose_backtick_bodies\n"
    allowed_sites, allowed_violations = analyze_source("tests/test_shell_shlex.py", source)
    denied_sites, denied_violations = analyze_source("agents_extensions/shared/hooks/guard.py", source)
    assert allowed_sites == []
    assert allowed_violations == []
    assert any(violation.kind == "private import" for violation in denied_violations)
    assert denied_sites == []


def test_test_only_oracle_import_fails() -> None:
    source = "from tests.bash_oracle import check\nimport tests.shell_oracle as oracle\n"
    reasons = _single(source)
    assert any("test-only bash oracle: " in reason and "tests.bash_oracle" in reason for reason in reasons)
    assert any("test-only bash oracle: " in reason and "tests.shell_oracle" in reason for reason in reasons)


def test_deployed_oracle_filename_fails() -> None:
    path = "agents_extensions/shared/hooks/bash_oracle.py"
    reasons = _overlay_reasons({path: "def check(path):\n    return path\n"}, [])
    assert any("test-only bash oracle: " in reason and "deployed with production hooks" in reason for reason in reasons)


def test_assignment_alias_of_split_fails_and_quote_alias_passes() -> None:
    failing = "import shlex\n\ndef parse(command):\n    splitter = shlex.split\n    return splitter(command)\n"
    passing = "import shlex\n\ndef emit(text):\n    quote = shlex.quote\n    return quote(text)\n"
    assert any("shlex.split" in reason for reason in _single(failing))
    assert _single(passing) == []


@pytest.mark.parametrize(
    "source",
    [
        "import bashlex\n\ndef parse(command):\n    return bashlex.parse(command)\n",
        "import tree_sitter_bash as bash\n\ndef parse(command):\n    return bash.parse(command)\n",
    ],
)
def test_shell_parser_library_reference_fails(source: str) -> None:
    reasons = _single(source)
    assert any(reason.startswith("new parser site:") for reason in reasons)


def test_shlex_module_used_before_assignment_fails() -> None:
    source = "import shlex\n\ndef parse(command):\n    return lexer.split(command)\n\nlexer = shlex\n"
    reasons = _single(source)
    assert any(reason.endswith("::parse::shlex.split") for reason in reasons)


def test_unpacked_shlex_module_fails() -> None:
    source = "import shlex\n\nlexer, = (shlex,)\n\ndef parse(command):\n    return lexer.split(command)\n"
    reasons = _single(source)
    assert any(reason.endswith("::parse::shlex.split") for reason in reasons)


def test_conditional_rebinding_of_shlex_module_fails() -> None:
    source = (
        "import shlex\n"
        "\n"
        "def parse(command):\n"
        "    lexer = shlex\n"
        "    if command is None:\n"
        "        lexer = None\n"
        "    else:\n"
        "        return lexer.split(command)\n"
    )
    reasons = _single(source)
    assert any(reason.endswith("::parse::shlex.split") for reason in reasons)


def test_relative_production_helper_parser_site_fails() -> None:
    sources = {
        "scripts/hooks/guard.py": "from ..parsing.review_helper import parse\n",
        "scripts/parsing/review_helper.py": ("import shlex\n\ndef parse(command):\n    return shlex.split(command)\n"),
    }
    check = analyze_files(sources)
    assert "scripts/parsing/review_helper.py" in check.production_helpers
    reasons = compare_baseline(check, [], pinned_size=BASELINE_SIZE_AT_CREATION)
    assert any(reason == "new parser site: scripts/parsing/review_helper.py::parse::shlex.split" for reason in reasons)


def test_transitive_helper_wrapper_parser_site_fails() -> None:
    sources = {
        "scripts/hooks/guard.py": "from ..parsing.wrapper import parse\n",
        "scripts/parsing/wrapper.py": "from scripts.parsing.review_helper import parse\n",
        "scripts/parsing/review_helper.py": ("import shlex\n\ndef parse(command):\n    return shlex.split(command)\n"),
    }
    check = analyze_files(sources)
    assert "scripts/parsing/wrapper.py" in check.production_helpers
    assert "scripts/parsing/review_helper.py" in check.production_helpers
    reasons = compare_baseline(check, [], pinned_size=BASELINE_SIZE_AT_CREATION)
    assert any(reason == "new parser site: scripts/parsing/review_helper.py::parse::shlex.split" for reason in reasons)


def test_package_import_of_boundary_module_private_attribute_fails() -> None:
    source = (
        "from agents_extensions.shared.hooks import shell_shlex as shared\n"
        "\n"
        "def hidden(command):\n"
        "    return shared._expose_backtick_bodies(command)\n"
    )
    reasons = _single(source)
    assert any(
        "private attribute: " in reason and "shell_shlex._expose_backtick_bodies" in reason for reason in reasons
    )


def test_vars_of_boundary_module_fails() -> None:
    source = (
        "from agents_extensions.shared.hooks import shell_shlex as shared\n"
        "\n"
        "def hidden(command):\n"
        "    return vars(shared)['_expose_backtick_bodies'](command)\n"
    )
    reasons = _single(source)
    assert any("dynamic access: " in reason and "shell_shlex" in reason for reason in reasons)
    assert any(
        "_expose_backtick_bodies" in reason or "vars shell_shlex" in reason or "module shell_shlex" in reason
        for reason in reasons
    )


def test_getattr_alias_of_boundary_module_fails() -> None:
    source = (
        "from agents_extensions.shared.hooks import shell_shlex as shared\n"
        "\n"
        "lookup = getattr\n"
        "\n"
        "def hidden(command):\n"
        "    return lookup(shared, '_expose_backtick_bodies')(command)\n"
    )
    reasons = _single(source)
    assert any("dynamic access: " in reason and "shell_shlex" in reason for reason in reasons)
    assert any("_expose_backtick_bodies" in reason or "getattr shell_shlex" in reason for reason in reasons)


def test_combined_short_option_syntax_check_fails() -> None:
    source = (
        "import subprocess\n"
        "\n"
        "def check(command):\n"
        "    subprocess.run(['bash', '-nc', command])\n"
        "    subprocess.run(['sh', '-nc', command])\n"
        "    subprocess.run(['/usr/bin/bash', '-xn', command])\n"
        "    subprocess.run(['dash', '--noexec', command])\n"
        "    subprocess.run(['zsh', '-o', 'noexec', command])\n"
    )
    reasons = _single(source)
    assert any(reason.endswith("::check::syntax:bash -n") for reason in reasons)
    assert any(reason.endswith("::check::syntax:sh -n") for reason in reasons)
    assert sum(reason.endswith("::check::syntax:bash -n") for reason in reasons) >= 2
    assert any(reason.endswith("::check::syntax:dash -n") for reason in reasons)
    assert any(reason.endswith("::check::syntax:zsh -n") for reason in reasons)


def test_globals_subscript_names_boundary_module_fails() -> None:
    source = (
        "read = globals\n"
        "\n"
        "def hidden():\n"
        "    return read()['shell_shlex']._tokenize('a')\n"
        "\n"
        "def other():\n"
        "    return vars()['shell_redirects']\n"
    )
    reasons = _single(source)
    assert any("dynamic access: " in reason and "globals shell_shlex" in reason for reason in reasons)
    assert any("dynamic access: " in reason and "vars shell_redirects" in reason for reason in reasons)


def test_function_local_same_package_helper_parser_site_fails() -> None:
    sources = {
        "scripts/hooks/guard.py": "from ..parsing.wrapper import parse\n",
        "scripts/parsing/wrapper.py": ("def load():\n    from .review_helper import parse\n    return parse\n"),
        "scripts/parsing/review_helper.py": ("import shlex\n\ndef parse(command):\n    return shlex.split(command)\n"),
    }
    check = analyze_files(sources)
    assert "scripts/parsing/review_helper.py" in check.production_helpers
    reasons = compare_baseline(check, [], pinned_size=BASELINE_SIZE_AT_CREATION)
    assert any(reason == "new parser site: scripts/parsing/review_helper.py::parse::shlex.split" for reason in reasons)


def test_bash_command_string_is_not_a_syntax_check() -> None:
    source = "import subprocess\n\ndef run(command):\n    subprocess.run(['bash', '-c', command])\n"
    assert _single(source) == []


def test_self_rebinding_runner_call_fails() -> None:
    source = "import subprocess\nsubprocess = subprocess.run(['bash', '-n', '-c', 'true'])\n"
    reasons = _single(source)
    assert any(reason.endswith("::<module>::syntax:bash -n") for reason in reasons)


def test_false_branch_runner_rebinding_fails() -> None:
    source = (
        "import subprocess\n"
        "\n"
        "def check():\n"
        "    if False:\n"
        "        subprocess = None\n"
        "    subprocess.run(['bash', '-n', '-c', 'true'])\n"
    )
    reasons = _single(source)
    assert any(reason.endswith("::check::syntax:bash -n") for reason in reasons)


def test_runner_alias_after_function_definition_fails() -> None:
    """Assigning a runner is an escape violation, which replaces the old alias site.

    The call through ``runner`` is not a syntax site: the checker does not
    follow the assignment. The assignment fails on its own.
    """
    source = "import subprocess\n\ndef check():\n    runner(['bash', '-n', '-c', 'true'])\n\nrunner = subprocess.run\n"
    reasons = _single(source)
    assert reasons == [_mutant_violation("runner used as a value", "subprocess.run")]
    assert not any("syntax:" in reason for reason in reasons)


def test_syntax_check_hidden_positions_fail() -> None:
    source = (
        "import subprocess\n"
        "\n"
        "def annotated(path: subprocess.run(['bash', '-n', path])):\n"
        "    pass\n"
        "\n"
        "def returned() -> subprocess.run(['sh', '-n', 'hook.sh']):\n"
        "    pass\n"
        "\n"
        "def defaulted(path=subprocess.run(['dash', '--noexec', path])):\n"
        "    pass\n"
        "\n"
        "holder = {}\n"
        "holder[subprocess.run(['zsh', '-o', 'noexec', 'hook.sh'])] = None\n"
        "\n"
        "def matched(command):\n"
        "    match command:\n"
        "        case subprocess.run(['bash', '-nc', command]):\n"
        "            return command\n"
    )
    reasons = _single(source)
    assert any(reason.endswith("::<module>::syntax:bash -n") for reason in reasons)
    assert any(reason.endswith("::<module>::syntax:sh -n") for reason in reasons)
    assert any(reason.endswith("::<module>::syntax:dash -n") for reason in reasons)
    assert any(reason.endswith("::<module>::syntax:zsh -n") for reason in reasons)
    assert any(reason.endswith("::matched::syntax:bash -n") for reason in reasons)
    assert sum(reason.endswith("::syntax:bash -n") for reason in reasons) == 2


def test_match_or_syntax_check_fails() -> None:
    source = (
        "import subprocess\n"
        "\n"
        "def matched(command):\n"
        "    match command:\n"
        "        case subprocess.run(['true'] | ['bash', '-n', 'hook.sh']):\n"
        "            return command\n"
    )
    reasons = _single(source)
    assert any(reason.endswith("::matched::syntax:bash -n") for reason in reasons)


def test_quoted_annotation_stays_unevaluated() -> None:
    shlex_annotation = "import shlex\n\ndef f(v: 'shlex.split'):\n    pass\n"
    syntax_annotation = "import subprocess\n\ndef f(v: \"subprocess.run(['bash', '-n', 'a'])\"):\n    pass\n"
    assert _single(shlex_annotation) == []
    assert _single(syntax_annotation) == []


def test_fixture_replacement_outside_creation_set_fails() -> None:
    rewritten = list(CREATION_SITES)
    rewritten[0] = _site("agents_extensions/shared/hooks/other.py", "parse", "shlex.split")
    assert len(rewritten) == BASELINE_SIZE_AT_CREATION
    reasons = outside_creation_set(rewritten)
    assert any(reason.startswith("outside creation set:") for reason in reasons)
    assert any(reason.startswith("shrunk creation site:") for reason in reasons)
    assert not any(reason.startswith("baseline growth") for reason in reasons)


def test_round2_annotation_and_subscript_probes_fail() -> None:
    source = (
        "import shlex\n"
        "import shell_shlex as shared\n"
        "\n"
        'def f(v: shlex.split("a b")):\n'
        "    pass\n"
        "\n"
        "def g(v: shared._expose_backtick_bodies):\n"
        "    pass\n"
        "\n"
        "holder = {}\n"
        'holder[shlex.split("a b")[0]] = None\n'
    )
    reasons = _single(source)
    split_sites = [reason for reason in reasons if reason.endswith("::<module>::shlex.split")]
    assert len(split_sites) == 2
    assert any(
        "private attribute: " in reason and "shell_shlex._expose_backtick_bodies" in reason for reason in reasons
    )
    assert _single("import shell_shlex as shared\n\ndef g(v: shared.preprocess_shell_command):\n    pass\n") == []


def test_annotation_only_shlex_attribute_fails_and_quote_passes() -> None:
    failing = "import shlex\n\ndef f(v: shlex.split):\n    pass\n"
    passing = "import shlex\n\ndef f(v: shlex.quote):\n    pass\n"
    assert any(reason.endswith("::<module>::shlex.split") for reason in _single(failing))
    assert _single(passing) == []


def test_return_annotation_shlex_attribute_fails() -> None:
    source = "import shlex\n\ndef f() -> shlex.split:\n    pass\n"
    passing = "import shlex\n\ndef f() -> shlex.join:\n    pass\n"
    assert any(reason.endswith("::<module>::shlex.split") for reason in _single(source))
    assert _single(passing) == []


def test_fstring_shlex_split_fails_and_quote_passes() -> None:
    failing = 'import shlex\n\ndef f(command):\n    return f"{shlex.split(command)}"\n'
    passing = 'import shlex\n\ndef f(command):\n    return f"{shlex.quote(command)}"\n'
    assert any(reason.endswith("::f::shlex.split") for reason in _single(failing))
    assert _single(passing) == []


def test_decorator_argument_shlex_split_fails_and_quote_passes() -> None:
    failing = "import shlex\n\n@wrap(shlex.split)\ndef f():\n    pass\n"
    passing = "import shlex\n\n@wrap(shlex.quote)\ndef f():\n    pass\n"
    assert any(reason.endswith("::<module>::shlex.split") for reason in _single(failing))
    assert _single(passing) == []


def test_match_statement_shlex_split_fails_and_quote_passes() -> None:
    failing = (
        "import shlex\n\ndef f(command):\n    match command:\n        case shlex.split:\n            return command\n"
    )
    passing = (
        "import shlex\n\ndef f(command):\n    match command:\n        case shlex.quote:\n            return command\n"
    )
    capture = "import shlex\n\ndef f(command):\n    match command:\n        case shlex:\n            return command\n"
    assert any(reason.endswith("::f::shlex.split") for reason in _single(failing))
    assert _single(passing) == []
    assert any(reason.endswith("::f::shlex") for reason in _single(capture))


def test_global_and_nonlocal_bound_names_fail() -> None:
    source = (
        "import shlex\n"
        "\n"
        "def f():\n"
        "    global shlex\n"
        "    return shlex.quote('a')\n"
        "\n"
        "def outer():\n"
        "    lexer = shlex\n"
        "\n"
        "    def inner():\n"
        "        nonlocal lexer\n"
        "        return lexer.quote('b')\n"
        "\n"
        "    return inner\n"
    )
    reasons = _single(source)
    assert any(reason.endswith("::f::shlex") for reason in reasons)
    assert any(reason.endswith("::outer.inner::shlex") for reason in reasons)
    assert not any("shlex.quote" in reason for reason in reasons)


def test_regrowth_after_shrink_fails() -> None:
    removed = CREATION_SITES[0]
    shrunk = list(CREATION_SITES[1:])
    shrink_reasons = outside_creation_set(shrunk)
    assert any(reason.startswith("shrunk creation site:") and removed.format() in reason for reason in shrink_reasons)
    regrown = [*shrunk, removed]
    regrowth_reasons = creation_set_gap(regrown, shrunk)
    assert any(reason.startswith("outside creation set:") and removed.format() in reason for reason in regrowth_reasons)
    assert creation_set_gap(shrunk, shrunk) == []


@pytest.mark.parametrize(
    ("source", "ending"),
    [
        pytest.param(
            "import os\n\ndef check():\n    os.posix_spawn('/usr/bin/bash', ['bash', '-n', 'hook.sh'], {})\n",
            "::check::syntax:bash -n",
            id="posix_spawn",
        ),
        pytest.param(
            "import os\n\ndef check():\n    os.posix_spawnp('sh', ['sh', '-nc', 'hook.sh'], {})\n",
            "::check::syntax:sh -n",
            id="posix_spawnp",
        ),
        pytest.param(
            "from os import posix_spawn\n"
            "\n"
            "def check():\n"
            "    posix_spawn('/bin/bash', ['bash', '-xn', 'hook.sh'], {})\n",
            "::check::syntax:bash -n",
            id="from-posix_spawn",
        ),
        pytest.param(
            "from os import posix_spawnp\n"
            "\n"
            "def check():\n"
            "    posix_spawnp('dash', ['dash', '--noexec', 'hook.sh'], {})\n",
            "::check::syntax:dash -n",
            id="from-posix_spawnp",
        ),
        pytest.param(
            "import os\n"
            "\n"
            "def matched(command):\n"
            "    match command:\n"
            "        case os.posix_spawn('/bin/bash', ['bash', '-n', 'hook.sh'], {}):\n"
            "            return command\n",
            "::matched::syntax:bash -n",
            id="match-posix_spawn",
        ),
        pytest.param(
            "import asyncio\n"
            "\n"
            "async def check():\n"
            "    await asyncio.create_subprocess_shell('dash --noexec hook.sh')\n",
            "::check::syntax:dash -n",
            id="create_subprocess_shell",
        ),
        pytest.param(
            "from asyncio import create_subprocess_shell\n"
            "\n"
            "async def check():\n"
            "    await create_subprocess_shell('bash -n hook.sh')\n",
            "::check::syntax:bash -n",
            id="from-create_subprocess_shell",
        ),
        pytest.param(
            "import asyncio\n"
            "\n"
            "def matched(command):\n"
            "    match command:\n"
            "        case asyncio.create_subprocess_shell('zsh -o noexec hook.sh'):\n"
            "            return command\n",
            "::matched::syntax:zsh -n",
            id="match-create_subprocess_shell",
        ),
        pytest.param(
            "import subprocess\n\ndef check():\n    subprocess.getoutput('bash -n hook.sh')\n",
            "::check::syntax:bash -n",
            id="getoutput",
        ),
        pytest.param(
            "import subprocess\n\ndef check():\n    subprocess.getstatusoutput('zsh -o noexec hook.sh')\n",
            "::check::syntax:zsh -n",
            id="getstatusoutput",
        ),
        pytest.param(
            "from subprocess import getoutput\n\ndef check():\n    getoutput('sh -nc hook.sh')\n",
            "::check::syntax:sh -n",
            id="from-getoutput",
        ),
        pytest.param(
            "from subprocess import getstatusoutput\n\ndef check():\n    getstatusoutput('dash --noexec hook.sh')\n",
            "::check::syntax:dash -n",
            id="from-getstatusoutput",
        ),
        pytest.param(
            "import os\n\ndef check():\n    os.popen('sh -n hook.sh')\n",
            "::check::syntax:sh -n",
            id="popen",
        ),
        pytest.param(
            "from os import popen\n\ndef check():\n    popen('bash -xn hook.sh')\n",
            "::check::syntax:bash -n",
            id="from-popen",
        ),
        pytest.param(
            "import os\n\ndef check():\n    os.system('bash -n hook.sh')\n",
            "::check::syntax:bash -n",
            id="system",
        ),
        pytest.param(
            "import subprocess\n\ndef check():\n    subprocess.run('bash -n hook.sh', shell=True)\n",
            "::check::syntax:bash -n",
            id="run-shell",
        ),
        pytest.param(
            "import subprocess\n\ndef check():\n    subprocess.call('sh -nc hook.sh', shell=True)\n",
            "::check::syntax:sh -n",
            id="call-shell",
        ),
        pytest.param(
            "import subprocess\n\ndef check():\n    subprocess.check_call('dash --noexec hook.sh', shell=True)\n",
            "::check::syntax:dash -n",
            id="check_call-shell",
        ),
        pytest.param(
            "import subprocess\n\ndef check():\n    subprocess.check_output('zsh -o noexec hook.sh', shell=True)\n",
            "::check::syntax:zsh -n",
            id="check_output-shell",
        ),
        pytest.param(
            "import subprocess\n\ndef check():\n    subprocess.Popen(args='bash -xn hook.sh', shell=True)\n",
            "::check::syntax:bash -n",
            id="Popen-shell",
        ),
    ],
)
def test_literal_syntax_check_runners_fail(source: str, ending: str) -> None:
    reasons = _single(source)
    assert any(reason.endswith(ending) for reason in reasons)


def test_runner_without_syntax_flag_passes() -> None:
    sources = [
        "import os\n\ndef check():\n    os.posix_spawn('/bin/bash', ['bash', '-c', 'true'], {})\n",
        "import os\n\ndef check():\n    os.posix_spawnp('sh', ['sh', '-c', 'true'], {})\n",
        "import asyncio\n\nasync def check():\n    await asyncio.create_subprocess_shell('bash -c true')\n",
        "import subprocess\n\ndef check():\n    subprocess.getoutput('bash -c true')\n",
        "import subprocess\n\ndef check():\n    subprocess.getstatusoutput('echo hi')\n",
        "import os\n\ndef check():\n    os.popen('bash -c true')\n",
        "import os\n\ndef check():\n    os.system('bash -c true')\n",
        "import subprocess\n\ndef check():\n    subprocess.run('bash -c true', shell=True)\n",
    ]
    assert all(_single(source) == [] for source in sources)


def test_computed_command_string_and_mutated_argv_stay_unresolved() -> None:
    sources = [
        "import os\n\ndef check():\n    os.system('bash' + ' -n hook.sh')\n",
        "import os\n\ndef check():\n    os.system('bash -n {}'.format('hook.sh'))\n",
        "import os\n\ndef check():\n    os.system('bash -n %s' % 'hook.sh')\n",
        'import os\n\ndef check(name):\n    os.system(f"bash -n {name}")\n',
        "import subprocess\n"
        "\n"
        "def check():\n"
        "    argv = ['bash', '-c', 'true']\n"
        "    argv.append('-n')\n"
        "    subprocess.run(argv)\n",
        "import subprocess\n\ndef check():\n    argv = ['bash', '-n', 'hook.sh']\n    subprocess.run(*argv)\n",
    ]
    assert all(_single(source) == [] for source in sources)


_MUTANT = "agents_extensions/shared/hooks/mutant.py"


def _mutant_site(symbol: str, identity: str) -> str:
    return f"new parser site: {_MUTANT}::{symbol}::{identity}"


def _mutant_violation(kind: str, detail: str, symbol: str = "<module>") -> str:
    return f"{kind}: {_MUTANT}::{symbol}::{detail}"


@pytest.mark.parametrize(
    ("source", "reason"),
    [
        pytest.param(
            "import subprocess\nsubprocess.getstatusoutput(cmd='bash -n -c true')\n",
            _mutant_site("<module>", "syntax:bash -n"),
            id="getstatusoutput-cmd",
        ),
        pytest.param(
            "import os\nos.spawnv(mode=os.P_WAIT, file='/bin/bash', args=['bash', '-n', '-c', 'true'])\n",
            _mutant_site("<module>", "syntax:bash -n"),
            id="spawnv-keywords",
        ),
        pytest.param(
            "import asyncio\n\nasync def check():\n    await asyncio.create_subprocess_shell(cmd='bash -n -c true')\n",
            _mutant_site("check", "syntax:bash -n"),
            id="create_subprocess_shell-cmd",
        ),
        pytest.param(
            "import subprocess\nsubprocess.run(['git', 'status'], cwd='bash -n hook.sh')\n",
            _mutant_site("<module>", "syntax:bash -n"),
            id="any-keyword-name",
        ),
        pytest.param(
            "import subprocess\nsubprocess.run(*['bash', '-n', '-c', 'true'])\n",
            _mutant_site("<module>", "syntax:bash -n"),
            id="starred-literal",
        ),
        pytest.param(
            "import subprocess\nsubprocess.getstatusoutput(**{'cmd': 'bash -n -c true'})\n",
            _mutant_site("<module>", "syntax:bash -n"),
            id="double-starred-literal",
        ),
    ],
)
def test_every_runner_argument_is_a_syntax_site(source: str, reason: str) -> None:
    assert _single(source) == [reason]


def test_keyword_without_syntax_flag_passes() -> None:
    sources = [
        "import subprocess\nsubprocess.getstatusoutput(cmd='echo hi')\n",
        "import os\nos.spawnv(mode=os.P_WAIT, file='/bin/true', args=['true'])\n",
        "import asyncio\n\nasync def check():\n    await asyncio.create_subprocess_shell(cmd='bash -c true')\n",
    ]
    assert all(_single(source) == [] for source in sources)


@pytest.mark.parametrize("module", ["shlex", "subprocess", "os", "asyncio", "shell_shlex", "shell_redirects"])
def test_wildcard_runner_and_boundary_imports_fail(module: str) -> None:
    reasons = _single(f"from {module} import *\n")
    assert _mutant_violation("wildcard import", module) in reasons
    if module == "shlex":
        assert _mutant_site("<module>", "shlex.*") in reasons


def test_subprocess_wildcard_call_is_a_violation() -> None:
    source = "from subprocess import *\nrun(['bash', '-n', '-c', 'true'])\n"
    assert _single(source) == [_mutant_violation("wildcard import", "subprocess")]


def test_multi_bound_boundary_name_checks_every_module() -> None:
    expected = [_mutant_violation("private attribute", "shell_redirects.preprocess_shell_command")]
    orders = (
        "import shell_shlex as shared\nimport shell_redirects as shared\n",
        "import shell_redirects as shared\nimport shell_shlex as shared\n",
    )
    for header in orders:
        assert _single(header + "shared.preprocess_shell_command('echo ok')\n") == expected


def test_multi_bound_runner_name_checks_every_runner() -> None:
    source = (
        "import subprocess as shared\n"
        "import os as shared\n"
        "shared.getstatusoutput(cmd='bash -n -c true')\n"
        "shared.system('sh -n hook.sh')\n"
    )
    reasons = _single(source)
    assert reasons == [
        _mutant_site("<module>", "syntax:bash -n"),
        _mutant_site("<module>", "syntax:sh -n"),
    ]


def test_comprehension_runner_is_an_escape_violation() -> None:
    source = "import subprocess\n[runner(['bash', '-n', '-c', 'true']) for runner in [subprocess.run]]\n"
    reasons = _single(source)
    assert reasons == [_mutant_violation("runner used as a value", "subprocess.run")]


def test_unpacked_loop_runner_is_an_escape_violation() -> None:
    source = (
        "import subprocess\n"
        "for runner, ignored in [(subprocess.run, 0), (subprocess.run, 1)]:\n"
        "    runner(['bash', '-n', '-c', 'true'])\n"
    )
    reasons = _single(source)
    assert reasons == [
        _mutant_violation("runner used as a value", "subprocess.run"),
        _mutant_violation("runner used as a value", "subprocess.run"),
    ]


def test_defaulted_runner_parameter_is_an_escape_violation() -> None:
    source = "import subprocess\ndef check(runner=subprocess.run):\n    return runner(['bash', '-n', '-c', 'true'])\n"
    reasons = _single(source)
    assert reasons == [_mutant_violation("runner used as a value", "subprocess.run")]


def test_qualified_boundary_import_private_attribute_fails() -> None:
    source = (
        "import agents_extensions.shared.hooks.shell_shlex\n"
        "agents_extensions.shared.hooks.shell_shlex.shlex.split(\"echo 'a b'\")\n"
    )
    reasons = _single(source)
    assert _mutant_violation("private attribute", "shell_shlex.shlex") in reasons


def test_runner_passed_as_argument_is_an_escape_violation() -> None:
    source = "import subprocess\nfrom subprocess import run\ncall(subprocess.run)\ncall(run)\n"
    reasons = _single(source)
    assert reasons == [
        _mutant_violation("runner used as a value", "subprocess.run"),
        _mutant_violation("runner used as a value", "subprocess.run"),
    ]


def test_dotted_from_import_runner_is_a_direct_call() -> None:
    source = "from lib.subprocess import run as go\ngo(['bash', '-n', '-c', 'true'])\ncall(go)\n"
    assert _single(source) == [
        _mutant_violation("runner used as a value", "subprocess.run"),
        _mutant_site("<module>", "syntax:bash -n"),
    ]


def test_runner_stored_in_dict_is_an_escape_violation() -> None:
    source = "import subprocess\nrunners = {'run': subprocess.run}\n"
    assert _single(source) == [_mutant_violation("runner used as a value", "subprocess.run")]


def test_runner_module_used_as_a_value_fails() -> None:
    passed = _single("import subprocess\ngetattr(subprocess, 'run')\n")
    stored = _single("import os as operating_system\nstored = operating_system\n")
    shlex_module = _single("import shlex\nstored = shlex\n")
    assert _mutant_violation("module used as a value", "subprocess") in passed
    assert _mutant_violation("module used as a value", "os") in stored
    assert _mutant_violation("module used as a value", "shlex") in shlex_module
    assert any(reason.endswith("::<module>::shlex") for reason in shlex_module)
    assert _single("import subprocess\nsubprocess.run(['git', 'status'])\n") == []


def _seeded_scan(script: str, probe: str, seed: str) -> dict[str, object]:
    env = os.environ.copy()
    env["PYTHONHASHSEED"] = seed
    completed = subprocess.run(
        [sys.executable, "-c", script],
        cwd=REPO_ROOT,
        env=env,
        input=probe,
        text=True,
        capture_output=True,
        check=False,
        timeout=120,
    )
    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout)
    assert isinstance(payload, dict)
    return payload


def test_repository_scan_and_multi_binding_probe_match_across_hash_seeds() -> None:
    script = (
        "import json, sys\n"
        "from tests.test_hook_single_parser import _single, analyze_repository\n"
        "probe = sys.stdin.read()\n"
        "check = analyze_repository()\n"
        "json.dump({\n"
        "    'sites': [site.format() for site in check.sites],\n"
        "    'violations': [item.format() for item in check.violations],\n"
        "    'probe': _single(probe),\n"
        "}, sys.stdout)\n"
    )
    probe = (
        "import shell_shlex as shared\nimport shell_redirects as shared\nshared.preprocess_shell_command('echo ok')\n"
    )
    seeded = [_seeded_scan(script, probe, seed) for seed in ("0", "1")]
    assert seeded[0] == seeded[1]
    assert seeded[0]["violations"] == []
    assert len(seeded[0]["sites"]) == BASELINE_SIZE_AT_CREATION
    assert seeded[0]["probe"] == [_mutant_violation("private attribute", "shell_redirects.preprocess_shell_command")]
