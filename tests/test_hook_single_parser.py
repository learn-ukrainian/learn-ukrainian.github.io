"""Fail the build when a hook grows a second shell parser or an unreviewed process start (#9807).

Parser sites. Over the whole module the check collects every binding of each
name to the ``shlex`` module or a boundary module. If a name is ever bound to
one of those modules, every use of that name may be that module. A later,
earlier, or untaken assignment does not remove that binding. A name bound to
``shlex`` may appear only as ``quote`` or ``join`` in load context. ``shlex.split``
and ``shlex.shlex`` are parser sites in every position. Imports of ``bashlex``
and ``tree_sitter_bash`` are sites. ``shlex.quote`` and ``shlex.join`` are output
quoting and are allowed. Generic regexes are not parsers.

The shared parser boundary is ``shell_shlex.py`` and ``shell_redirects.py``.
Outside it, a name bound to either module may appear only as a public export.
Aliased imports and attribute access are checked. Wildcard imports and dynamic
access to these modules fail. The observed parser sites must equal the frozen
creation set exactly. This module is a test: production hooks must not import
it, and it is not a bash oracle deployed with them.

Process starts. A process start is allowed only when both of these hold:

1. It is a direct call ``subprocess.run``, ``subprocess.call``,
   ``subprocess.check_call``, or ``subprocess.check_output``. ``Popen`` is not
   permitted. ``subprocess`` is bound only by a module-level plain
   ``import subprocess`` that is never rebound, aliased, passed, returned, or
   stored. The call has exactly one positional argument, or only an explicit
   ``args=`` keyword, and no call-level ``*args`` or ``**kwargs``. ``shell=``
   may only be the literal ``False``. ``executable=`` is forbidden.
2. That argument is a list or tuple display matching a reviewed command
   template: a literal ``git`` or ``gh``, literal subcommand words, and variable
   operands only in the template's operand positions. Config-injection forms
   (``-c``, ``--config``, and alias definitions) are violations. There is no
   general ``python`` permission.

Anything else that can start a process is a violation, reported as
``process-start: path:line`` plus a reason code. That includes other
``subprocess`` references except ``DEVNULL``, ``PIPE``, ``STDOUT``,
``TimeoutExpired``, ``CalledProcessError``, and ``CompletedProcess``;
``from subprocess import``; ``os`` process functions (``system``, ``popen``,
``exec*``, ``spawn*``, ``posix_spawn*``, ``fork*``, ``startfile``) and ``os``
module escapes; ``asyncio`` subprocess APIs and any ``subprocess_exec`` or
``subprocess_shell`` attribute, whatever the receiver is; and ``pty``,
``multiprocessing``, ``concurrent.futures.ProcessPoolExecutor``,
``psutil.Popen``, ``pexpect``, ``sh``, and ``plumbum``. A new external
capability has to be classified in this set before it is silent.

A name bound to a process-capable module (``os``, ``asyncio``,
``asyncio.subprocess``, ``psutil``, ``pty``, ``multiprocessing``,
``concurrent.futures``, ``subprocess`` other than the one plain import, and the
other modules in rule 3) is a violation when that name is used as a value:
assignment, argument, return, container, or the host of an attribute after a
rebinding. Every ``ast.Name`` and ``ast.Attribute`` is judged through the
parent map. Wildcard imports from any of those modules are violations and are
not expanded.

``subprocess`` is rebound by every binding of that name other than the one
plain import. That includes Store and Del names (assignment, walrus, ``for``,
``with``, comprehension targets), match captures, ``except`` names, parameters,
function and class names, ``global`` / ``nonlocal``, and ``import X as
subprocess`` / ``from X import Y as subprocess``.

Rule 4 exceptions. Only a call AST may be baselined. An existing call whose
argv is not a reviewed template is listed in
``tests/fixtures/hook_process_start_baseline.json``. A function that launches a
process from a computed argv is a runner helper: its own launch call is pinned,
and every call to that helper from the scanned set is pinned too (normalized
call AST, literal argv where present, multiplicity). A runner default or alias
is not baseline-eligible; the baseline pins the launch call instead. The
fixture must equal the creation set in this module. Replacing, duplicating, or
adding an entry fails unless both change together. An entry waives nothing in
rule 1 or 3: ``shell=``, ``executable=``, a rebound or aliased ``subprocess``,
and any other process API still fail when the same AST is written into the
baseline.

Trust assumptions. The check trusts that the literal names ``git`` and ``gh``
resolve to those executables, and that user or system git/gh configuration does
not define a shell alias for a reviewed subcommand. It does not read that
configuration.

Helper scope. The denominator is every hook module plus the production helpers
those hooks import. A reached helper follows import-time imports, relative
imports, and function-local absolute imports. ``scripts/ai_agent_bridge/`` and
``agents_extensions/shared/session_streams/`` are not entered. The production
helper count is 26.

The walk is a pure AST walk. It does not import or execute the modules it
scans. Iteration order is sorted, so the result does not depend on
``PYTHONHASHSEED``.

Accepted limitations (owner: claude-infra). Slice 2a does not establish the
Move 2 guarantee while the handwritten scanners remain:

- Handwritten scanners, this inventory:
  ``agents_extensions/shared/hooks/guard-secret-print.py``
  ``_strip_shell_comments``, ``_collapse_shell_line_continuations``,
  ``_decode_ansi_c_quotes``, ``_protect_parameters``, ``_substitution_spans``;
  ``agents_extensions/shared/hooks/guard-primary-checkout-write.py``
  ``_strip_shell_comments``, ``_collapse_shell_line_continuations``,
  ``_decode_ansi_c_quotes``, ``_mask_quoted_literals``,
  ``_normalize_backtick_substitutions``,
  ``_normalize_quoted_command_substitutions``.
- Execution and import machinery is not run: ``exec``, ``eval``, ``compile``,
  computed ``importlib`` / ``__import__``, and ``typing.get_type_hints``.
- Quoted (string) annotations stay source text.
- Dynamic namespace access: ``globals()``, ``vars()``, ``__dict__``, and
  ``sys.modules[...]``. A process starter reached only through that machinery,
  with no direct reference to the module or the callable, stays unresolved.
- ``Popen.__init__`` re-entry and ``type(p)`` reconstruction are not separate
  findings. Constructing ``subprocess.Popen`` is a violation; calling back into
  an object that already exists is not detected.
- Internal stdlib re-exports such as ``asyncio.base_events`` and
  ``asyncio.events`` are not followed.
"""

from __future__ import annotations

import ast
import json
import os
import subprocess
import sys
from collections import Counter, defaultdict
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = REPO_ROOT / "tests" / "fixtures" / "hook_parser_sites_baseline.json"
PROCESS_FIXTURE_PATH = REPO_ROOT / "tests" / "fixtures" / "hook_process_start_baseline.json"

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
SHLEX_MODULE_ALLOWED_ATTRS = frozenset({"quote", "join"})
DYNAMIC_MODULE_FUNCS = frozenset({"getattr", "vars", "globals", "__import__"})
# Process-capable modules. A name bound to one of these, used as a value, is a
# violation. Star-imports of these modules, and of shlex, are refused outside
# the boundary and are not expanded.
PROCESS_CAPABLE_MODULES = frozenset(
    {
        "asyncio",
        "asyncio.subprocess",
        "concurrent.futures",
        "multiprocessing",
        "os",
        "pexpect",
        "plumbum",
        "psutil",
        "pty",
        "sh",
        "subprocess",
    }
)
WILDCARD_IMPORT_MODULES = PROCESS_CAPABLE_MODULES | frozenset({"shlex"})
# May-bind is only the shlex module and the boundary modules.
_MAY_BIND_KINDS = frozenset({"shlex_module", "boundary_module"})
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

# Application packages the session-start helper chain reaches by a
# function-local absolute import. They are product code, not hook support,
# and the helper scan does not enter them. Every other project-local import,
# including a function-local absolute import that crosses a package, is followed.
UNRELATED_APPLICATION_PREFIXES = (
    "agents_extensions/shared/session_streams/",
    "scripts/ai_agent_bridge/",
)
# Count of production helpers under the scope rule above. A change to the
# rule that adds or drops a helper updates this count in the same change.
PRODUCTION_HELPER_COUNT = 26

# Reviewed command templates. ``None`` is an operand position. A call on main
# matches one of these, or it is an exception in the process-start baseline.
# There is no general python permission.
COMMAND_TEMPLATES: tuple[tuple[str, tuple[str | None, ...]], ...] = (
    ("git", ("rev-parse", "--git-common-dir")),
    ("git", ("rev-parse", "--git-dir")),
    ("git", ("rev-parse", "--path-format=absolute", "--git-common-dir")),
    ("git", ("rev-parse", "--path-format=absolute", "--show-toplevel")),
    ("git", ("symbolic-ref", "--quiet", "--short", "HEAD")),
    ("gh", ("api", None)),
    ("gh", ("pr", "checks", None, "--json", "name,bucket,state")),
)

PERMITTED_SUBPROCESS_RUNNERS = frozenset({"run", "call", "check_call", "check_output"})
SUBPROCESS_NON_LAUNCHING = frozenset(
    {"DEVNULL", "PIPE", "STDOUT", "TimeoutExpired", "CalledProcessError", "CompletedProcess"}
)
ASYNCIO_SUBPROCESS_ATTRS = frozenset({"create_subprocess_exec", "create_subprocess_shell"})
EVENT_LOOP_SUBPROCESS_ATTRS = frozenset({"subprocess_exec", "subprocess_shell"})
EXTERNAL_PROCESS_MODULES = frozenset({"pty", "multiprocessing", "pexpect", "plumbum", "sh"})
_OS_GETATTR_FUNCS = frozenset({"getattr", "hasattr", "setattr", "delattr"})
# Only call ASTs. A runner default or alias (``runner-reference``) cannot be pinned.
_ELIGIBLE_PROCESS_REASONS = frozenset({"argv-template", "runner-call"})


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
    line: int = 0

    def format(self) -> str:
        if self.kind == "process-start":
            return f"process-start: {self.path}:{self.line}::{self.enclosing_symbol}::{self.detail}"
        return f"{self.kind}: {self.path}::{self.enclosing_symbol}::{self.detail}"


@dataclass(frozen=True)
class Check:
    sites: tuple[Site, ...]
    violations: tuple[Violation, ...]
    hook_files: tuple[str, ...]
    production_helpers: tuple[str, ...]
    process_findings: tuple[ProcessFinding, ...] = ()
    process_exceptions: tuple[ProcessException, ...] = ()


@dataclass(frozen=True)
class _Binding:
    kind: str
    detail: tuple[str, ...] = ()


_UNKNOWN = _Binding("unknown")


def _binding_sort_key(binding: _Binding) -> tuple[object, ...]:
    """Stable order for a binding set. The hash seed must not change results."""
    return (binding.kind, binding.detail)


def _sorted_bindings(bindings: Iterable[_Binding]) -> list[_Binding]:
    return sorted(bindings, key=_binding_sort_key)


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


def _process_enclosing_symbol(node: ast.AST, parents: dict[ast.AST, ast.AST]) -> str:
    """Enclosing function, including a default or annotation on that function."""
    names: list[str] = []
    current: ast.AST | None = node
    while current is not None:
        parent = parents.get(current)
        if isinstance(parent, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            in_body = any(current is statement for statement in parent.body)
            in_signature = current is parent.args or current in parent.decorator_list or current is parent.returns
            if in_body or in_signature:
                names.append(parent.name)
        elif isinstance(parent, ast.Lambda) and current in {parent.body, parent.args}:
            names.append("<lambda>")
        current = parent
    if not names:
        return "<module>"
    return ".".join(reversed(names))


def _is_os_process_attr(name: str) -> bool:
    """True for the os process-start families named by the allowlist."""
    return name in {"system", "popen", "startfile"} or name.startswith(("exec", "spawn", "posix_spawn", "fork"))


def _is_config_literal(node: ast.AST) -> bool:
    """True when a displayed argv word is a git/gh config or alias injection."""
    if not isinstance(node, ast.Constant) or not isinstance(node.value, str):
        return False
    text = node.value
    if text == "-c" or text.startswith("--config"):
        return True
    if text.startswith("!"):
        return True
    return "alias." in text and "!" in text


def _module_is(module: str | None, name: str) -> bool:
    if not module:
        return False
    return module == name or module.startswith(f"{name}.")


def _is_stdlib_subprocess_module(module: str | None) -> bool:
    """True for ``subprocess`` itself, not ``asyncio.subprocess`` or another package."""
    if not module or module == "asyncio.subprocess" or module.startswith("asyncio.subprocess."):
        return False
    return module == "subprocess" or module.endswith(".subprocess")


def _string_binding_sites(node: ast.AST) -> list[tuple[str, ast.AST]]:
    """Names bound without a Store ``ast.Name``. Import aliases are separate.

    Store and Del names (assignment, walrus, ``for``, ``with``, comprehension
    targets) are visited directly. These forms bind through a string field.
    """
    if isinstance(node, (ast.Global, ast.Nonlocal)):
        return [(name, node) for name in node.names]
    if isinstance(node, ast.ExceptHandler) and node.name:
        return [(node.name, node)]
    if isinstance(node, ast.MatchAs) and node.name:
        return [(node.name, node)]
    if isinstance(node, ast.MatchStar) and node.name:
        return [(node.name, node)]
    if isinstance(node, ast.MatchMapping) and node.rest:
        return [(node.rest, node)]
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        return [(node.name, node)]
    if isinstance(node, ast.arg):
        return [(node.arg, node)]
    return []


def _subprocess_runner_attributes(expr: ast.AST) -> list[ast.Attribute]:
    """Permitted ``subprocess`` runners used as values inside ``expr``."""
    found: list[ast.Attribute] = []
    for node in ast.walk(expr):
        if (
            isinstance(node, ast.Attribute)
            and isinstance(node.value, ast.Name)
            and node.value.id == "subprocess"
            and node.attr in PERMITTED_SUBPROCESS_RUNNERS
        ):
            found.append(node)
    return found


def _iter_scope_nodes(body: list[ast.stmt]) -> Iterable[ast.AST]:
    """Nodes in ``body`` except nested function and lambda bodies.

    Class bodies are entered so a class-level alias is visible. Methods are
    skipped here and scanned as their own functions.
    """
    stack: list[ast.AST] = list(reversed(body))
    while stack:
        node = stack.pop()
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
            continue
        if isinstance(node, ast.ClassDef):
            stack.extend(reversed(node.body))
            continue
        yield node
        stack.extend(reversed(list(ast.iter_child_nodes(node))))


def _is_module_level(node: ast.AST, parents: dict[ast.AST, ast.AST]) -> bool:
    current: ast.AST | None = node
    while current is not None:
        if isinstance(current, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.ClassDef)):
            return False
        current = parents.get(current)
    return True


def _attribute_root_name(node: ast.AST) -> tuple[str, tuple[str, ...]] | None:
    chain = _attribute_chain(node)
    if chain is None:
        return None
    root, attrs = chain
    return root.id, attrs


def _argv_matches_template(argv: ast.AST) -> bool:
    """True when ``argv`` is a list or tuple display of one reviewed template."""
    if not isinstance(argv, (ast.List, ast.Tuple)):
        return False
    elements = argv.elts
    if not elements or any(isinstance(elt, ast.Starred) for elt in elements):
        return False
    executable = elements[0]
    if not isinstance(executable, ast.Constant) or not isinstance(executable.value, str):
        return False
    rest = elements[1:]
    for name, parts in COMMAND_TEMPLATES:
        if executable.value != name or len(rest) != len(parts):
            continue
        if all(_template_part_matches(elt, part) for elt, part in zip(rest, parts, strict=True)):
            return True
    return False


def _template_part_matches(elt: ast.AST, part: str | None) -> bool:
    if isinstance(elt, ast.Starred) or _is_config_literal(elt):
        return False
    if part is None:
        return True
    return isinstance(elt, ast.Constant) and elt.value == part


def _displayed_argv_has_config_injection(argv: ast.AST) -> bool:
    if not isinstance(argv, (ast.List, ast.Tuple)):
        return False
    return any(_is_config_literal(elt) for elt in argv.elts)


def _call_shape_reason(call: ast.Call) -> str | None:
    """Rule 1 call-shape failure, or None when the call may be templated."""
    if any(isinstance(arg, ast.Starred) for arg in call.args):
        return "call-shape:starred-args"
    for keyword in call.keywords:
        if keyword.arg is not None:
            continue
        if _starred_keywords_name(keyword.value, "executable"):
            return "call-shape:executable"
        if _starred_keywords_name(keyword.value, "shell"):
            return "call-shape:shell"
        return "call-shape:starred-kwargs"
    has_args = any(keyword.arg == "args" for keyword in call.keywords)
    if has_args and call.args:
        return "call-shape:positional-and-args"
    if not has_args and len(call.args) != 1:
        return "call-shape:positional-count"
    for keyword in call.keywords:
        if keyword.arg == "executable":
            return "call-shape:executable"
        if keyword.arg == "shell" and not (isinstance(keyword.value, ast.Constant) and keyword.value.value is False):
            return "call-shape:shell"
    return None


def _starred_keywords_name(node: ast.expr, name: str) -> bool:
    if not isinstance(node, ast.Dict):
        return False
    return any(isinstance(key, ast.Constant) and key.value == name for key in node.keys)


def _call_argv_expr(call: ast.Call) -> ast.expr | None:
    for keyword in call.keywords:
        if keyword.arg == "args":
            return keyword.value
    if len(call.args) == 1:
        return call.args[0]
    return None


def _exception_root(node: ast.AST, parents: dict[ast.AST, ast.AST]) -> ast.AST:
    """Largest expression that is the stored runner or the non-template call."""
    current = node
    while True:
        parent = parents.get(current)
        if isinstance(parent, ast.BoolOp):
            current = parent
            continue
        if isinstance(parent, ast.IfExp) and current in {parent.body, parent.orelse}:
            current = parent
            continue
        if isinstance(parent, ast.NamedExpr) and parent.value is current:
            current = parent
            continue
        return current


def _normalized_ast(node: ast.AST) -> str:
    return ast.dump(node, include_attributes=False)


@dataclass(frozen=True)
class ProcessFinding:
    """One allowlist miss. Eligible misses can match the shrink-only baseline."""

    path: str
    line: int
    column: int
    enclosing_symbol: str
    reason: str
    normalized_ast: str

    @property
    def eligible(self) -> bool:
        return self.reason in _ELIGIBLE_PROCESS_REASONS

    def key(self) -> tuple[str, str, str]:
        return (self.path, self.enclosing_symbol, self.normalized_ast)

    def as_violation(self) -> Violation:
        return Violation("process-start", self.path, self.enclosing_symbol, self.reason, self.line)


@dataclass(frozen=True)
class ProcessException:
    """One pinned call. A runner default or alias is not a baseline row."""

    path: str
    enclosing_symbol: str
    multiplicity: int
    normalized_ast: str
    explanation: str

    def key(self) -> tuple[str, str, str]:
        return (self.path, self.enclosing_symbol, self.normalized_ast)


PROCESS_EXCEPTION_COUNT = 50

PROCESS_CREATION_EXCEPTIONS: tuple[ProcessException, ...] = (
    ProcessException(
        'agents_extensions/shared/hooks/guard-pr-merge.py',
        '_check_states',
        1,
        (
            "Call(func=Attribute(value=Name(id='subprocess', ctx=Load()), attr='run', ctx=Load()), args=[List"
            "(elts=[Constant(value='gh'), Constant(value='pr'), Constant(value='checks'), Name(id='pr', ctx=L"
            "oad()), Starred(value=Call(func=Name(id='_repo_args', ctx=Load()), args=[Name(id='repo', ctx=Loa"
            "d())], keywords=[]), ctx=Load()), Constant(value='--json'), Constant(value='name,bucket,state')]"
            ", ctx=Load())], keywords=[keyword(arg='capture_output', value=Constant(value=True)), keyword(arg"
            "='env', value=Call(func=Name(id='_gh_env', ctx=Load()), args=[], keywords=[])), keyword(arg='cwd"
            "', value=Name(id='cwd', ctx=Load())), keyword(arg='text', value=Constant(value=True)), keyword(a"
            "rg='timeout', value=Constant(value=8))])"
        ),
        'Spreads _repo_args(repo) before --json name,bucket,state.',
    ),
    ProcessException(
        'agents_extensions/shared/hooks/guard-pr-merge.py',
        '_check_states_from_status_rollup',
        1,
        (
            "Call(func=Attribute(value=Name(id='subprocess', ctx=Load()), attr='run', ctx=Load()), args=[List"
            "(elts=[Constant(value='gh'), Constant(value='pr'), Constant(value='view'), Name(id='pr', ctx=Loa"
            "d()), Starred(value=Call(func=Name(id='_repo_args', ctx=Load()), args=[Name(id='repo', ctx=Load("
            "))], keywords=[]), ctx=Load()), Constant(value='--json'), Constant(value='statusCheckRollup')], "
            "ctx=Load())], keywords=[keyword(arg='capture_output', value=Constant(value=True)), keyword(arg='"
            "env', value=Call(func=Name(id='_gh_env', ctx=Load()), args=[], keywords=[])), keyword(arg='cwd',"
            " value=Name(id='cwd', ctx=Load())), keyword(arg='text', value=Constant(value=True)), keyword(arg"
            "='timeout', value=Constant(value=8))])"
        ),
        'Spreads _repo_args(repo) before --json statusCheckRollup.',
    ),
    ProcessException(
        'agents_extensions/shared/hooks/guard-pr-merge.py',
        '_pr_meta',
        1,
        (
            "Call(func=Attribute(value=Name(id='subprocess', ctx=Load()), attr='run', ctx=Load()), args=[List"
            "(elts=[Constant(value='gh'), Constant(value='pr'), Constant(value='view'), Name(id='pr', ctx=Loa"
            "d()), Starred(value=Call(func=Name(id='_repo_args', ctx=Load()), args=[Name(id='repo', ctx=Load("
            "))], keywords=[]), ctx=Load()), Constant(value='--json'), Constant(value='isDraft,baseRefName,bo"
            "dy,headRefOid,number,url')], ctx=Load())], keywords=[keyword(arg='capture_output', value=Constan"
            "t(value=True)), keyword(arg='env', value=Call(func=Name(id='_gh_env', ctx=Load()), args=[], keyw"
            "ords=[])), keyword(arg='cwd', value=Name(id='cwd', ctx=Load())), keyword(arg='text', value=Const"
            "ant(value=True)), keyword(arg='timeout', value=Constant(value=8))])"
        ),
        'Spreads _repo_args(repo) between the PR selector and --json.',
    ),
    ProcessException(
        'agents_extensions/shared/hooks/heal-core-bare.py',
        'main',
        1,
        (
            "Call(func=Attribute(value=Name(id='subprocess', ctx=Load()), attr='run', ctx=Load()), args=[List"
            "(elts=[Call(func=Name(id='str', ctx=Load()), args=[Name(id='python_bin', ctx=Load())], keywords="
            "[]), Call(func=Name(id='str', ctx=Load()), args=[Name(id='script', ctx=Load())], keywords=[]), C"
            "onstant(value='--repo'), Call(func=Name(id='str', ctx=Load()), args=[Name(id='project_dir', ctx="
            "Load())], keywords=[]), Constant(value='--fix'), Constant(value='-q')], ctx=Load())], keywords=["
            "keyword(arg='check', value=Constant(value=False)), keyword(arg='stdout', value=Attribute(value=N"
            "ame(id='subprocess', ctx=Load()), attr='DEVNULL', ctx=Load())), keyword(arg='stderr', value=Attr"
            "ibute(value=Name(id='subprocess', ctx=Load()), attr='DEVNULL', ctx=Load()))])"
        ),
        'Executable is project_interpreter(); script is scripts/audit/check_core_bare.py.',
    ),
    ProcessException(
        'scripts/guardrails/assert_primary_on_main.py',
        '_git',
        1,
        (
            "Call(func=Attribute(value=Name(id='subprocess', ctx=Load()), attr='run', ctx=Load()), args=[Name"
            "(id='argv', ctx=Load())], keywords=[keyword(arg='cwd', value=Call(func=Name(id='str', ctx=Load()"
            "), args=[Name(id='cwd', ctx=Load())], keywords=[])), keyword(arg='capture_output', value=Constan"
            "t(value=True)), keyword(arg='text', value=Constant(value=True)), keyword(arg='env', value=Name(i"
            "d='env', ctx=Load())), keyword(arg='check', value=Constant(value=False)), keyword(arg='timeout',"
            " value=Name(id='_GIT_TIMEOUT_S', ctx=Load()))])"
        ),
        "argv is ['git', *args] from the caller's git arguments, not a fixed template.",
    ),
    ProcessException(
        'scripts/guardrails/worktree_containment.py',
        '_run_git',
        1,
        (
            "Call(func=Attribute(value=Name(id='subprocess', ctx=Load()), attr='run', ctx=Load()), args=[Name"
            "(id='argv', ctx=Load())], keywords=[keyword(arg='capture_output', value=Constant(value=True)), k"
            "eyword(arg='text', value=Constant(value=True)), keyword(arg='check', value=Constant(value=False)"
            "), keyword(arg='env', value=Call(func=Name(id='sanitized_git_env', ctx=Load()), args=[], keyword"
            "s=[])), keyword(arg='timeout', value=Name(id='_GIT_TIMEOUT_S', ctx=Load()))])"
        ),
        "argv is ['git', '-C', cwd, *args] from the caller's git arguments.",
    ),
    ProcessException(
        'scripts/hooks/hook_timing.py',
        'run_wrapped',
        1,
        (
            "Call(func=Attribute(value=Name(id='subprocess', ctx=Load()), attr='run', ctx=Load()), args=[Name"
            "(id='argv', ctx=Load())], keywords=[keyword(arg='input', value=Name(id='stdin', ctx=Load())), ke"
            "yword(arg='capture_output', value=Constant(value=True)), keyword(arg='timeout', value=Name(id='_"
            "HOOK_TIMEOUT_SECONDS', ctx=Load()))])"
        ),
        'argv is the hook command passed into run_wrapped, not a displayed list.',
    ),
    ProcessException(
        'scripts/hooks/measure_hook_stack.py',
        '_time_one',
        1,
        (
            "Call(func=Attribute(value=Name(id='subprocess', ctx=Load()), attr='run', ctx=Load()), args=[Name"
            "(id='argv', ctx=Load())], keywords=[keyword(arg='input', value=Name(id='stdin', ctx=Load())), ke"
            "yword(arg='capture_output', value=Constant(value=True)), keyword(arg='env', value=Name(id='env',"
            " ctx=Load())), keyword(arg='cwd', value=Name(id='ROOT', ctx=Load())), keyword(arg='timeout', val"
            "ue=Name(id='_HOOK_TIMEOUT_SECONDS', ctx=Load()))])"
        ),
        'argv is the hook command passed into _time_one, not a displayed list.',
    ),
    ProcessException(
        'scripts/lib/session_record.py',
        'canonical_state_root',
        1,
        (
            "Call(func=Attribute(value=Name(id='subprocess', ctx=Load()), attr='run', ctx=Load()), args=[Name"
            "(id='command', ctx=Load())], keywords=[keyword(arg='check', value=Constant(value=False)), keywor"
            "d(arg='capture_output', value=Constant(value=True)), keyword(arg='text', value=Constant(value=Tr"
            "ue)), keyword(arg='env', value=Name(id='env', ctx=Load())), keyword(arg='timeout', value=Name(id"
            "='_GIT_TIMEOUT_SECONDS', ctx=Load()))])"
        ),
        'command is the git -C rev-parse list built above and passed by name.',
    ),
    ProcessException(
        'scripts/orchestration/thread_handoff.py',
        'run_command',
        1,
        (
            "Call(func=Attribute(value=Name(id='subprocess', ctx=Load()), attr='run', ctx=Load()), args=[Name"
            "(id='args', ctx=Load())], keywords=[keyword(arg='cwd', value=Call(func=Name(id='str', ctx=Load()"
            "), args=[Name(id='cwd', ctx=Load())], keywords=[])), keyword(arg='capture_output', value=Constan"
            "t(value=True)), keyword(arg='text', value=Constant(value=True)), keyword(arg='timeout', value=Na"
            "me(id='timeout_s', ctx=Load())), keyword(arg='check', value=Constant(value=False)), keyword(arg="
            "'env', value=Name(id='env', ctx=Load()))])"
        ),
        'args is caller-supplied; callers pass git, gh, ps, and the project interpreter.',
    ),
    ProcessException(
        'agents_extensions/shared/hooks/guard-pr-merge.py',
        '_check_states',
        1,
        (
            "Call(func=Name(id='_check_states_from_status_rollup', ctx=Load()), args=[Name(id='pr', ctx=Load("
            ")), Name(id='repo', ctx=Load()), Name(id='cwd', ctx=Load())], keywords=[])"
        ),
        'Calls _check_states_from_status_rollup, whose gh pr view argv is pinned separately.',
    ),
    ProcessException(
        'agents_extensions/shared/hooks/heal-core-bare.py',
        '<module>',
        1,
        (
            "Call(func=Name(id='main', ctx=Load()), args=[], keywords=[])"
        ),
        'Module-level main() launches the pinned project-interpreter call.',
    ),
    ProcessException(
        'scripts/guardrails/assert_primary_on_main.py',
        'primary_head_state',
        1,
        (
            "Call(func=Name(id='_git', ctx=Load()), args=[Name(id='main_root', ctx=Load()), Constant(value='s"
            "ymbolic-ref'), Constant(value='--quiet'), Constant(value='--short'), Constant(value='HEAD')], ke"
            'ywords=[])'
        ),
        'Passes git symbolic-ref --quiet --short HEAD through the pinned _git runner.',
    ),
    ProcessException(
        'scripts/guardrails/assert_primary_on_main.py',
        'primary_head_state',
        1,
        (
            "Call(func=Name(id='_git', ctx=Load()), args=[Name(id='main_root', ctx=Load()), Constant(value='r"
            "ev-parse'), Constant(value='--short'), Constant(value='HEAD')], keywords=[])"
        ),
        'Passes git rev-parse --short HEAD through the pinned _git runner.',
    ),
    ProcessException(
        'scripts/guardrails/assert_primary_on_main.py',
        'heal_primary_to_main',
        1,
        (
            "Call(func=Name(id='_git', ctx=Load()), args=[Name(id='main_root', ctx=Load()), Constant(value='s"
            "how-ref'), Constant(value='--verify'), Constant(value='--quiet'), Constant(value='refs/heads/mai"
            "n')], keywords=[])"
        ),
        'Passes git show-ref --verify --quiet refs/heads/main through the pinned _git runner.',
    ),
    ProcessException(
        'scripts/guardrails/assert_primary_on_main.py',
        'heal_primary_to_main',
        1,
        (
            "Call(func=Name(id='_git', ctx=Load()), args=[Name(id='main_root', ctx=Load()), Constant(value='f"
            "etch'), Constant(value='origin'), Constant(value='main')], keywords=[])"
        ),
        'Passes git fetch origin main through the pinned _git runner.',
    ),
    ProcessException(
        'scripts/guardrails/assert_primary_on_main.py',
        'heal_primary_to_main',
        1,
        (
            "Call(func=Name(id='_git', ctx=Load()), args=[Name(id='main_root', ctx=Load()), Constant(value='c"
            "heckout'), Constant(value='-B'), Constant(value='main'), Constant(value='origin/main')], keyword"
            's=[])'
        ),
        'Passes git checkout -B main origin/main through the pinned _git runner.',
    ),
    ProcessException(
        'scripts/guardrails/assert_primary_on_main.py',
        'heal_primary_to_main',
        1,
        (
            "Call(func=Name(id='_git', ctx=Load()), args=[Name(id='main_root', ctx=Load()), Constant(value='c"
            "heckout'), Constant(value='main')], keywords=[])"
        ),
        'Passes git checkout main through the pinned _git runner.',
    ),
    ProcessException(
        'scripts/guardrails/assert_primary_on_main.py',
        'heal_primary_to_main',
        1,
        (
            "Call(func=Name(id='_git', ctx=Load()), args=[Name(id='main_root', ctx=Load()), Constant(value='p"
            "ull'), Constant(value='--ff-only'), Constant(value='origin'), Constant(value='main')], keywords="
            '[])'
        ),
        'Passes git pull --ff-only origin main through the pinned _git runner.',
    ),
    ProcessException(
        'scripts/guardrails/worktree_containment.py',
        '_resolve_main_root_or_none',
        1,
        (
            "Call(func=Name(id='_run_git', ctx=Load()), args=[Name(id='start_dir', ctx=Load()), Constant(valu"
            "e='rev-parse'), Constant(value='--path-format=absolute'), Constant(value='--git-common-dir')], k"
            'eywords=[])'
        ),
        'Passes git rev-parse --path-format=absolute --git-common-dir through the pinned _run_git runner.',
    ),
    ProcessException(
        'scripts/guardrails/worktree_containment.py',
        '_resolve_main_root_or_none',
        1,
        (
            "Call(func=Name(id='_run_git', ctx=Load()), args=[Name(id='start_dir', ctx=Load()), Constant(valu"
            "e='rev-parse'), Constant(value='--show-toplevel')], keywords=[])"
        ),
        'Passes git rev-parse --show-toplevel through the pinned _run_git runner.',
    ),
    ProcessException(
        'scripts/guardrails/worktree_containment.py',
        'registered_worktrees',
        1,
        (
            "Call(func=Name(id='_run_git', ctx=Load()), args=[Name(id='main_root', ctx=Load()), Constant(valu"
            "e='worktree'), Constant(value='list'), Constant(value='--porcelain')], keywords=[])"
        ),
        'Passes git worktree list --porcelain through the pinned _run_git runner.',
    ),
    ProcessException(
        'scripts/guardrails/worktree_containment.py',
        'is_tracked',
        1,
        (
            "Call(func=Name(id='_run_git', ctx=Load()), args=[Name(id='root', ctx=Load()), Constant(value='ls"
            "-files'), Constant(value='--error-unmatch'), Constant(value='--'), Name(id='rel', ctx=Load())], "
            'keywords=[])'
        ),
        'Passes git ls-files --error-unmatch and a relative path through the pinned _run_git runner.',
    ),
    ProcessException(
        'scripts/guardrails/worktree_containment.py',
        'is_ignored',
        1,
        (
            "Call(func=Name(id='_run_git', ctx=Load()), args=[Name(id='root', ctx=Load()), Constant(value='ch"
            "eck-ignore'), Constant(value='-q'), Constant(value='--'), Name(id='rel', ctx=Load())], keywords="
            '[])'
        ),
        'Passes git check-ignore -q and a relative path through the pinned _run_git runner.',
    ),
    ProcessException(
        'scripts/guardrails/worktree_containment.py',
        'current_branch',
        1,
        (
            "Call(func=Name(id='_run_git', ctx=Load()), args=[Name(id='start', ctx=Load()), Constant(value='s"
            "ymbolic-ref'), Constant(value='--quiet'), Constant(value='--short'), Constant(value='HEAD')], ke"
            'ywords=[])'
        ),
        'Passes git symbolic-ref --quiet --short HEAD through the pinned _run_git runner.',
    ),
    ProcessException(
        'scripts/guardrails/worktree_containment.py',
        'heal_primary_bare_if_needed',
        1,
        (
            "Call(func=Name(id='_run_git', ctx=Load()), args=[Name(id='main_root', ctx=Load()), Constant(valu"
            "e='rev-parse'), Constant(value='--is-bare-repository')], keywords=[])"
        ),
        'Passes git rev-parse --is-bare-repository through the pinned _run_git runner.',
    ),
    ProcessException(
        'scripts/guardrails/worktree_containment.py',
        'heal_primary_bare_if_needed',
        1,
        (
            "Call(func=Name(id='_run_git', ctx=Load()), args=[Name(id='main_root', ctx=Load()), Constant(valu"
            "e='config'), Constant(value='--get'), Constant(value='core.bare')], keywords=[])"
        ),
        'Passes git config --get core.bare through the pinned _run_git runner.',
    ),
    ProcessException(
        'scripts/guardrails/worktree_containment.py',
        'heal_primary_bare_if_needed',
        1,
        (
            "Call(func=Name(id='_run_git', ctx=Load()), args=[Name(id='main_root', ctx=Load()), Constant(valu"
            "e='config'), Constant(value='core.bare'), Constant(value='false')], keywords=[])"
        ),
        'Passes git config core.bare false through the pinned _run_git runner.',
    ),
    ProcessException(
        'scripts/guardrails/worktree_containment.py',
        'heal_primary_bare_if_needed',
        1,
        (
            "Call(func=Name(id='_run_git', ctx=Load()), args=[Name(id='main_root', ctx=Load()), Constant(valu"
            "e='config'), Constant(value='extensions.worktreeConfig'), Constant(value='true')], keywords=[])"
        ),
        'Passes git config extensions.worktreeConfig true through the pinned _run_git runner.',
    ),
    ProcessException(
        'scripts/guardrails/worktree_containment.py',
        'primary_checkout_dirty_status',
        1,
        (
            "Call(func=Name(id='_run_git', ctx=Load()), args=[Name(id='main_root', ctx=Load()), Constant(valu"
            "e='rev-parse'), Constant(value='HEAD')], keywords=[])"
        ),
        'Passes git rev-parse HEAD through the pinned _run_git runner.',
    ),
    ProcessException(
        'scripts/guardrails/worktree_containment.py',
        'primary_checkout_dirty_status',
        1,
        (
            "Call(func=Name(id='_run_git', ctx=Load()), args=[Name(id='main_root', ctx=Load()), Starred(value"
            "=Subscript(value=Name(id='command', ctx=Load()), slice=Slice(lower=Constant(value=1)), ctx=Load("
            ')), ctx=Load())], keywords=[])'
        ),
        'Spreads command[1:] through the pinned _run_git runner.',
    ),
    ProcessException(
        'scripts/hooks/hook_timing.py',
        'main',
        1,
        (
            "Call(func=Name(id='run_wrapped', ctx=Load()), args=[Name(id='cmd', ctx=Load())], keywords=[])"
        ),
        'Passes the hook command in cmd through the pinned run_wrapped runner.',
    ),
    ProcessException(
        'scripts/hooks/measure_hook_stack.py',
        'main',
        1,
        (
            "Call(func=Name(id='_time_one', ctx=Load()), args=[Name(id='name', ctx=Load()), Name(id='argv', c"
            "tx=Load()), Name(id='stdin', ctx=Load()), Name(id='env_extra', ctx=Load())], keywords=[keyword(a"
            "rg='repeats', value=Attribute(value=Name(id='args', ctx=Load()), attr='repeats', ctx=Load()))])"
        ),
        'Passes the hook argv into the pinned _time_one runner.',
    ),
    ProcessException(
        'scripts/lib/session_record.py',
        'sessions_dir',
        1,
        (
            "Call(func=Name(id='canonical_state_root', ctx=Load()), args=[], keywords=[])"
        ),
        'sessions_dir calls canonical_state_root, whose git rev-parse command is pinned separately.',
    ),
    ProcessException(
        'scripts/lib/session_record.py',
        '_resolved_state_root',
        1,
        (
            "Call(func=Name(id='canonical_state_root', ctx=Load()), args=[], keywords=[])"
        ),
        '_resolved_state_root calls canonical_state_root, whose git rev-parse command is pinned separately.',
    ),
    ProcessException(
        'scripts/opsec/gh_snapshot.py',
        'repository',
        1,
        (
            "Call(func=Name(id='reader', ctx=Load()), args=[List(elts=[Constant(value='git'), Constant(value="
            "'remote'), Constant(value='get-url'), Constant(value='origin')], ctx=Load())], keywords=[keyword"
            "(arg='cwd', value=Name(id='cwd', ctx=Load())), keyword(arg='env', value=Call(func=Name(id='inter"
            "nal_environment', ctx=Load()), args=[Name(id='environment', ctx=Load())], keywords=[])), keyword"
            "(arg='capture_output', value=Constant(value=True)), keyword(arg='text', value=Constant(value=Tru"
            "e)), keyword(arg='check', value=Constant(value=False)), keyword(arg='timeout', value=Constant(va"
            'lue=5))])'
        ),
        'reader launches git remote get-url origin; the default reader is subprocess.run.',
    ),
    ProcessException(
        'scripts/opsec/gh_snapshot.py',
        'admit',
        1,
        (
            "Call(func=Name(id='repository', ctx=Load()), args=[Name(id='cwd', ctx=Load()), Name(id='origin_e"
            "nv', ctx=Load())], keywords=[keyword(arg='reader', value=Name(id='reader', ctx=Load()))])"
        ),
        'Forwards reader into repository, whose git remote get-url call is pinned separately.',
    ),
    ProcessException(
        'scripts/opsec/gh_snapshot.py',
        'admit',
        1,
        (
            "Call(func=Name(id='reader', ctx=Load()), args=[List(elts=[Constant(value='git'), Constant(value="
            "'rev-parse'), Constant(value='--show-toplevel')], ctx=Load())], keywords=[keyword(arg='cwd', val"
            "ue=Name(id='cwd', ctx=Load())), keyword(arg='env', value=Call(func=Name(id='internal_environment"
            "', ctx=Load()), args=[Name(id='environment', ctx=Load())], keywords=[])), keyword(arg='text', va"
            "lue=Constant(value=True)), keyword(arg='capture_output', value=Constant(value=True)), keyword(ar"
            "g='check', value=Constant(value=False)), keyword(arg='timeout', value=Constant(value=5))])"
        ),
        'reader launches git rev-parse --show-toplevel; the default reader is subprocess.run.',
    ),
    ProcessException(
        'scripts/opsec/gh_snapshot.py',
        'admit',
        1,
        (
            "Call(func=Name(id='repository', ctx=Load()), args=[Name(id='cwd', ctx=Load()), Name(id='environm"
            "ent', ctx=Load()), IfExp(test=Name(id='selectors', ctx=Load()), body=Subscript(value=Name(id='se"
            "lectors', ctx=Load()), slice=UnaryOp(op=USub(), operand=Constant(value=1)), ctx=Load()), orelse="
            "Constant(value=None)), Name(id='reader', ctx=Load())], keywords=[])"
        ),
        'Forwards reader into repository with the last selector; the git remote call is pinned separately.',
    ),
    ProcessException(
        'scripts/opsec/prepublish.py',
        'checked_run',
        1,
        (
            "Call(func=Name(id='runner', ctx=Load()), args=[Name(id='args', ctx=Load())], keywords=[keyword(v"
            "alue=Name(id='kwargs', ctx=Load()))])"
        ),
        "Fallback runner(args) launches the caller's argv; the default runner is subprocess.run.",
    ),
    ProcessException(
        'scripts/opsec/prepublish.py',
        'checked_run',
        1,
        (
            "Call(func=Name(id='admit', ctx=Load()), args=[Call(func=Name(id='list', ctx=Load()), args=[Subsc"
            "ript(value=Name(id='args', ctx=Load()), slice=Slice(lower=Constant(value=1)), ctx=Load())], keyw"
            "ords=[])], keywords=[keyword(arg='cwd', value=Call(func=Name(id='Path', ctx=Load()), args=[BoolO"
            "p(op=Or(), values=[Call(func=Attribute(value=Name(id='kwargs', ctx=Load()), attr='get', ctx=Load"
            "()), args=[Constant(value='cwd')], keywords=[]), Call(func=Attribute(value=Name(id='Path', ctx=L"
            "oad()), attr='cwd', ctx=Load()), args=[], keywords=[])])], keywords=[])), keyword(arg='environme"
            "nt', value=Name(id='environment', ctx=Load())), keyword(arg='reader', value=Name(id='runner', ct"
            'x=Load()))])'
        ),
        'Forwards runner into admit, whose git calls are pinned in gh_snapshot.',
    ),
    ProcessException(
        'scripts/opsec/prepublish.py',
        'checked_run',
        1,
        (
            "Call(func=Name(id='runner', ctx=Load()), args=[List(elts=[Subscript(value=Name(id='args', ctx=Lo"
            "ad()), slice=Constant(value=0), ctx=Load()), Starred(value=Attribute(value=Name(id='frozen', ctx"
            "=Load()), attr='argv', ctx=Load()), ctx=Load())], ctx=Load())], keywords=[keyword(value=Name(id="
            "'kwargs', ctx=Load()))])"
        ),
        'runner launches gh plus the frozen argv from admit; the default runner is subprocess.run.',
    ),
    ProcessException(
        'scripts/orchestration/thread_handoff.py',
        'canonical_state_root',
        1,
        (
            "Call(func=Name(id='run_command', ctx=Load()), args=[List(elts=[Constant(value='git'), Constant(v"
            "alue='rev-parse'), Constant(value='--path-format=absolute'), Constant(value='--git-common-dir')]"
            ", ctx=Load())], keywords=[keyword(arg='cwd', value=Name(id='repo_root', ctx=Load())), keyword(ar"
            "g='env', value=Call(func=Name(id='git_environment', ctx=Load()), args=[], keywords=[]))])"
        ),
        'run_command launches git rev-parse --path-format=absolute --git-common-dir.',
    ),
    ProcessException(
        'scripts/orchestration/thread_handoff.py',
        'git_output',
        1,
        (
            "Call(func=Name(id='run_command', ctx=Load()), args=[List(elts=[Constant(value='git'), Starred(va"
            "lue=Name(id='args', ctx=Load()), ctx=Load())], ctx=Load())], keywords=[keyword(arg='cwd', value="
            "Name(id='repo_root', ctx=Load())), keyword(arg='timeout_s', value=Name(id='timeout_s', ctx=Load("
            "))), keyword(arg='env', value=Call(func=Name(id='git_environment', ctx=Load()), args=[], keyword"
            's=[]))])'
        ),
        "run_command launches git plus the caller's args.",
    ),
    ProcessException(
        'scripts/orchestration/thread_handoff.py',
        'gh_json',
        1,
        (
            "Call(func=Name(id='run_command', ctx=Load()), args=[List(elts=[Constant(value='gh'), Starred(val"
            "ue=Name(id='args', ctx=Load()), ctx=Load())], ctx=Load())], keywords=[keyword(arg='cwd', value=N"
            "ame(id='repo_root', ctx=Load())), keyword(arg='timeout_s', value=Name(id='timeout_s', ctx=Load()"
            '))])'
        ),
        "run_command launches gh plus the caller's args.",
    ),
    ProcessException(
        'scripts/orchestration/thread_handoff.py',
        'require_checkout_continuity.is_ancestor',
        1,
        (
            "Call(func=Name(id='run_command', ctx=Load()), args=[List(elts=[Constant(value='git'), Constant(v"
            "alue='merge-base'), Constant(value='--is-ancestor'), Name(id='expected_head', ctx=Load()), Name("
            "id='current_head', ctx=Load())], ctx=Load())], keywords=[keyword(arg='cwd', value=Name(id='repo_"
            "root', ctx=Load())), keyword(arg='env', value=Call(func=Name(id='git_environment', ctx=Load()), "
            'args=[], keywords=[]))])'
        ),
        'run_command launches git merge-base --is-ancestor with the two heads.',
    ),
    ProcessException(
        'scripts/orchestration/thread_handoff.py',
        '_default_process_snapshot',
        1,
        (
            "Call(func=Name(id='run_command', ctx=Load()), args=[List(elts=[Constant(value='ps'), Constant(va"
            "lue='-o'), Constant(value='ppid=,comm=,lstart='), Constant(value='-p'), Call(func=Name(id='str',"
            " ctx=Load()), args=[Name(id='pid', ctx=Load())], keywords=[])], ctx=Load())], keywords=[keyword("
            "arg='cwd', value=Call(func=Attribute(value=Name(id='Path', ctx=Load()), attr='cwd', ctx=Load()),"
            " args=[], keywords=[])), keyword(arg='env', value=Name(id='env', ctx=Load()))])"
        ),
        'run_command launches ps -o ppid=,comm=,lstart= for one pid.',
    ),
    ProcessException(
        'scripts/orchestration/thread_handoff.py',
        '_default_machine_id',
        1,
        (
            "Call(func=Name(id='run_command', ctx=Load()), args=[List(elts=[Constant(value='ioreg'), Constant"
            "(value='-rd1'), Constant(value='-c'), Constant(value='IOPlatformExpertDevice')], ctx=Load())], k"
            "eywords=[keyword(arg='cwd', value=Call(func=Attribute(value=Name(id='Path', ctx=Load()), attr='c"
            "wd', ctx=Load()), args=[], keywords=[])), keyword(arg='env', value=Call(func=Name(id='git_enviro"
            "nment', ctx=Load()), args=[], keywords=[]))])"
        ),
        'run_command launches ioreg -rd1 -c IOPlatformExpertDevice.',
    ),
    ProcessException(
        'scripts/orchestration/thread_handoff.py',
        '_process_is_zombie',
        1,
        (
            "Call(func=Name(id='run_command', ctx=Load()), args=[List(elts=[Constant(value='ps'), Constant(va"
            "lue='-o'), Constant(value='stat='), Constant(value='-p'), Call(func=Name(id='str', ctx=Load()), "
            "args=[Name(id='pid', ctx=Load())], keywords=[])], ctx=Load())], keywords=[keyword(arg='cwd', val"
            "ue=Call(func=Attribute(value=Name(id='Path', ctx=Load()), attr='cwd', ctx=Load()), args=[], keyw"
            "ords=[])), keyword(arg='env', value=Name(id='env', ctx=Load()))])"
        ),
        'run_command launches ps -o stat= for one pid.',
    ),
    ProcessException(
        'scripts/orchestration/thread_handoff.py',
        'request_claudex_rollover',
        1,
        (
            "Call(func=Name(id='run_command', ctx=Load()), args=[List(elts=[Call(func=Attribute(value=Name(id"
            "='os', ctx=Load()), attr='fspath', ctx=Load()), args=[Call(func=Name(id='project_interpreter', c"
            "tx=Load()), args=[Name(id='repo_root', ctx=Load())], keywords=[])], keywords=[]), Call(func=Attr"
            "ibute(value=Name(id='os', ctx=Load()), attr='fspath', ctx=Load()), args=[Name(id='supervisor_scr"
            "ipt', ctx=Load())], keywords=[]), Constant(value='request-rollover'), Constant(value='--state-ro"
            "ot'), Call(func=Attribute(value=Name(id='os', ctx=Load()), attr='fspath', ctx=Load()), args=[Nam"
            "e(id='state_root', ctx=Load())], keywords=[]), Constant(value='--run-id'), Name(id='run_id', ctx"
            "=Load()), Constant(value='--launch-generation'), Call(func=Name(id='str', ctx=Load()), args=[Nam"
            "e(id='launch_generation', ctx=Load())], keywords=[]), Constant(value='--session-id'), Name(id='s"
            "ession_id', ctx=Load()), Constant(value='--lineage-id'), Name(id='lineage_id', ctx=Load()), Cons"
            "tant(value='--rollover-generation'), Call(func=Name(id='str', ctx=Load()), args=[Name(id='rollov"
            "er_generation', ctx=Load())], keywords=[]), Constant(value='--rollover-id'), Name(id='rollover_i"
            "d', ctx=Load())], ctx=Load())], keywords=[keyword(arg='cwd', value=Name(id='repo_root', ctx=Load"
            '()))])'
        ),
        'run_command launches the project interpreter on claudex_supervisor.py request-rollover.',
    ),
)


def _finding(
    path: str,
    node: ast.AST,
    parents: dict[ast.AST, ast.AST],
    reason: str,
    normalized: ast.AST | None = None,
) -> ProcessFinding:
    return ProcessFinding(
        path,
        getattr(node, "lineno", 0),
        getattr(node, "col_offset", 0),
        _process_enclosing_symbol(node, parents),
        reason,
        _normalized_ast(normalized if normalized is not None else node),
    )


def _benign_os_getattr(name: ast.Name, parents: dict[ast.AST, ast.AST]) -> bool:
    """``getattr(os, "O_DIRECTORY", 0)`` reads a literal non-process attribute."""
    parent = parents.get(name)
    if not isinstance(parent, ast.Call) or not parent.args or parent.args[0] is not name:
        return False
    func = parent.func
    if not isinstance(func, ast.Name) or func.id not in _OS_GETATTR_FUNCS or len(parent.args) < 2:
        return False
    attr = parent.args[1]
    return isinstance(attr, ast.Constant) and isinstance(attr.value, str) and not _is_os_process_attr(attr.value)


class _ProcessAllowlist:
    """Positive allowlist over one module. The walk does not execute the module."""

    def __init__(self, path: str, tree: ast.AST) -> None:
        self.path = path
        self.tree = tree
        self.parents = _parent_map(tree)
        self.findings: list[ProcessFinding] = []
        self._subprocess_names: set[str] = set()
        self._subprocess_clean = False
        self._os_names: set[str] = set()
        self._asyncio_names: set[str] = set()
        self._asyncio_subprocess_names: set[str] = set()
        self._psutil_names: set[str] = set()
        self._module_names: dict[str, set[str]] = {}
        self._rebound_modules: set[str] = set()
        self._suppressed_runner_ids: set[int] = set()

    def collect(self) -> list[ProcessFinding]:
        self._collect_imports()
        self._propagate_process_modules()
        self._sync_process_name_sets()
        self._collect_binding_escapes()
        self._taint_subprocess_values()
        self._collect_alias_launches()
        self._collect_references()
        self.findings.sort(key=lambda item: (item.line, item.column, item.reason, item.normalized_ast))
        return self.findings

    def _add(self, node: ast.AST, reason: str, normalized: ast.AST | None = None) -> None:
        self.findings.append(_finding(self.path, node, self.parents, reason, normalized))

    def _collect_imports(self) -> None:
        plain_subprocess = False
        tainted_subprocess = False
        for node in ast.walk(self.tree):
            if isinstance(node, ast.Import):
                plain_subprocess, tainted_subprocess = self._collect_import(node, plain_subprocess, tainted_subprocess)
            elif isinstance(node, ast.ImportFrom):
                tainted_subprocess = self._collect_import_from(node) or tainted_subprocess
        self._subprocess_clean = plain_subprocess and not tainted_subprocess

    def _collect_import(
        self, node: ast.Import, plain_subprocess: bool, tainted_subprocess: bool
    ) -> tuple[bool, bool]:
        module_level = _is_module_level(node, self.parents)
        for alias in node.names:
            root = alias.name.split(".", 1)[0]
            local = alias.asname or root
            if alias.name == "subprocess" or alias.name.startswith("subprocess."):
                if alias.asname or not module_level or root != "subprocess":
                    self._add(node, "binding:function-local-import" if not module_level else "binding:aliased-import")
                    tainted_subprocess = True
                    self._subprocess_names.add(local)
                else:
                    plain_subprocess = True
                    self._subprocess_names.add("subprocess")
            elif local == "subprocess":
                # ``import os as subprocess`` binds the subprocess name to another module.
                self._add(alias, "binding:rebound")
                tainted_subprocess = True
                self._subprocess_names.add("subprocess")
            if root == "os" and alias.asname is None:
                self._os_names.add("os")
            elif alias.name == "os" and alias.asname:
                self._os_names.add(alias.asname)
            if alias.name == "asyncio" or alias.name.startswith("asyncio."):
                self._remember_asyncio_import(node, alias)
            if root == "psutil":
                self._psutil_names.add(alias.asname or "psutil")
            if root in EXTERNAL_PROCESS_MODULES and alias.name.split(".", 1)[0] == root:
                self._add(node, f"external-capability:{root}")
            self._note_process_import(alias)
        return plain_subprocess, tainted_subprocess

    def _note_process_import(self, alias: ast.alias) -> None:
        """Record the module object an ``import`` actually binds."""
        full = alias.name
        if alias.asname:
            if full in PROCESS_CAPABLE_MODULES:
                self._bind_process_module(alias.asname, full, imported=True)
            return
        root = full.split(".", 1)[0]
        if root in PROCESS_CAPABLE_MODULES:
            self._bind_process_module(root, root, imported=True)

    def _bind_process_module(self, local: str, module: str, *, imported: bool) -> None:
        if module not in PROCESS_CAPABLE_MODULES:
            return
        self._module_names.setdefault(local, set()).add(module)
        if not imported:
            self._rebound_modules.add(local)

    def _add_rebound_modules(self, name: str, modules: set[str]) -> bool:
        changed = False
        bucket = self._module_names.setdefault(name, set())
        for module in modules:
            if module not in bucket:
                bucket.add(module)
                changed = True
        if name not in self._rebound_modules:
            self._rebound_modules.add(name)
            changed = True
        return changed

    def _remember_asyncio_import(self, node: ast.Import, alias: ast.alias) -> None:
        if alias.name == "asyncio.subprocess" or alias.name.startswith("asyncio.subprocess."):
            self._add(node, "asyncio-subprocess")
            if alias.asname:
                self._asyncio_subprocess_names.add(alias.asname)
            else:
                self._asyncio_names.add("asyncio")
            return
        local = alias.asname or "asyncio"
        if alias.name == "asyncio" or (alias.asname is None and alias.name.startswith("asyncio.")):
            self._asyncio_names.add(local if alias.asname or alias.name == "asyncio" else "asyncio")

    def _collect_import_from(self, node: ast.ImportFrom) -> bool:
        module = node.module or ""
        tainted = False
        if any(alias.name == "*" for alias in node.names):
            # Wildcard imports are refused by the parser walk. They are not expanded.
            return tainted
        if _is_stdlib_subprocess_module(module):
            self._add(node, "binding:from-import")
            tainted = True
        else:
            for alias in node.names:
                local = alias.asname or alias.name
                if local == "subprocess":
                    self._add(alias, "binding:rebound")
                    tainted = True
                    self._subprocess_names.add("subprocess")
        if module == "asyncio":
            for alias in node.names:
                if alias.name == "subprocess":
                    self._bind_process_module(alias.asname or alias.name, "asyncio.subprocess", imported=True)
        if _module_is(module, "os"):
            for alias in node.names:
                if _is_os_process_attr(alias.name):
                    self._add(alias, f"os-process:{alias.name}")
        if module == "asyncio.subprocess" or module.startswith("asyncio.subprocess."):
            self._add(node, "asyncio-subprocess")
        elif module == "asyncio":
            self._collect_asyncio_from(node)
        if module == "psutil" or module.startswith("psutil."):
            for alias in node.names:
                if alias.name == "Popen":
                    self._add(alias, "external-capability:psutil.Popen")
        if module == "concurrent.futures" or module.startswith("concurrent.futures."):
            for alias in node.names:
                if alias.name == "ProcessPoolExecutor":
                    self._add(alias, "external-capability:ProcessPoolExecutor")
        root = module.split(".", 1)[0]
        if root in EXTERNAL_PROCESS_MODULES:
            self._add(node, f"external-capability:{root}")
        return tainted

    def _collect_asyncio_from(self, node: ast.ImportFrom) -> None:
        for alias in node.names:
            local = alias.asname or alias.name
            if alias.name in ASYNCIO_SUBPROCESS_ATTRS or alias.name == "subprocess":
                self._add(alias, "asyncio-subprocess")
                if alias.name == "subprocess":
                    self._asyncio_subprocess_names.add(local)
            elif alias.name == "subprocess_exec" or alias.name == "subprocess_shell":
                self._add(alias, "event-loop-subprocess")

    def _collect_binding_escapes(self) -> None:
        """Every binding of the name ``subprocess`` except the plain import.

        Store and Del names cover assignment, walrus, loops, ``with``, and
        comprehensions. String fields cover match, ``except``, parameters,
        definitions, and ``global`` / ``nonlocal``. Nothing is skipped because
        of the statement it sits in.
        """
        seen: set[int] = set()
        for node in ast.walk(self.tree):
            sites: list[ast.AST] = []
            if isinstance(node, ast.Name) and isinstance(node.ctx, (ast.Store, ast.Del)) and node.id == "subprocess":
                sites.append(node)
            sites.extend(site for name, site in _string_binding_sites(node) if name == "subprocess")
            for site in sites:
                if id(site) in seen:
                    continue
                seen.add(id(site))
                self._add(site, "binding:rebound")
                self._subprocess_clean = False

    def _expr_process_modules(self, expr: ast.AST) -> set[str]:
        if isinstance(expr, ast.Name):
            return set(self._module_names.get(expr.id, ()))
        if isinstance(expr, ast.Attribute):
            base = self._expr_process_modules(expr.value)
            found: set[str] = set()
            if expr.attr == "subprocess" and "asyncio" in base:
                found.add("asyncio.subprocess")
            if expr.attr == "futures" and "concurrent" in base:
                found.add("concurrent.futures")
            return found
        if isinstance(expr, ast.BoolOp):
            found = set()
            for value in expr.values:
                found |= self._expr_process_modules(value)
            return found
        if isinstance(expr, ast.IfExp):
            return self._expr_process_modules(expr.body) | self._expr_process_modules(expr.orelse)
        if isinstance(expr, ast.NamedExpr):
            return self._expr_process_modules(expr.value)
        return set()

    def _propagate_process_modules(self) -> None:
        """Copy a process-module binding through assignments. Flow-insensitive."""
        changed = True
        while changed:
            changed = False
            for node in ast.walk(self.tree):
                changed |= self._propagate_process_node(node)

    def _propagate_process_node(self, node: ast.AST) -> bool:
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if (
                isinstance(target, (ast.Tuple, ast.List))
                and isinstance(node.value, (ast.Tuple, ast.List))
                and len(target.elts) == len(node.value.elts)
                and not any(isinstance(elt, ast.Starred) for elt in (*target.elts, *node.value.elts))
            ):
                changed = False
                for left, right in zip(target.elts, node.value.elts, strict=True):
                    modules = self._expr_process_modules(right)
                    if modules and isinstance(left, ast.Name):
                        changed |= self._add_rebound_modules(left.id, modules)
                return changed
        value: ast.expr | None = None
        targets: list[ast.AST] = []
        if isinstance(node, ast.Assign):
            value = node.value
            targets = list(node.targets)
        elif isinstance(node, (ast.AnnAssign, ast.NamedExpr)) and node.value is not None:
            value = node.value
            targets = [node.target]
        if value is None:
            return False
        modules = self._expr_process_modules(value)
        if not modules:
            return False
        changed = False
        for target in targets:
            if isinstance(target, ast.Name):
                changed |= self._add_rebound_modules(target.id, modules)
        return changed

    def _sync_process_name_sets(self) -> None:
        for name in sorted(self._module_names):
            modules = self._module_names[name]
            if "os" in modules:
                self._os_names.add(name)
            if "asyncio" in modules:
                self._asyncio_names.add(name)
            if "asyncio.subprocess" in modules:
                self._asyncio_subprocess_names.add(name)
            if "psutil" in modules:
                self._psutil_names.add(name)
            if "subprocess" in modules:
                self._subprocess_names.add(name)

    def _name_is_attribute_host(self, node: ast.Name) -> bool:
        parent = self.parents.get(node)
        return isinstance(parent, ast.Attribute) and parent.value is node

    def _process_name_is_value_use(self, node: ast.Name) -> bool:
        """True when ``node`` uses a process-capable module as a value.

        The original import name hosting an attribute (``os.path``, ``asyncio.sleep``)
        is not a value use. A name that was assigned the module, then used as
        the host of an attribute, is.
        """
        if node.id not in self._module_names:
            return False
        if self._name_is_attribute_host(node) and node.id not in self._rebound_modules:
            return False
        modules = self._module_names[node.id]
        return not ("os" in modules and _benign_os_getattr(node, self.parents))

    def _taint_subprocess_values(self) -> None:
        """A subprocess module used as a value makes every later runner untrusted.

        This runs before call judgment so breadth-first walk order cannot see
        the call first.
        """
        for node in ast.walk(self.tree):
            if not isinstance(node, ast.Name) or not isinstance(node.ctx, ast.Load):
                continue
            if "subprocess" not in self._module_names.get(node.id, ()):
                continue
            if self._process_name_is_value_use(node):
                self._subprocess_clean = False
                return

    def _module_value_reason(self, name: str) -> str:
        if self._module_names.get(name) == {"os"}:
            return "os-escape"
        return "binding:module-value"

    def _note_runner_assignment(self, node: ast.AST, established: dict[str, list[ast.Attribute]]) -> None:
        value: ast.expr | None = None
        targets: list[ast.AST] = []
        if isinstance(node, ast.Assign):
            value = node.value
            targets = list(node.targets)
        elif isinstance(node, (ast.AnnAssign, ast.NamedExpr)) and node.value is not None:
            value = node.value
            targets = [node.target]
        if value is None:
            return
        attributes = _subprocess_runner_attributes(value)
        if not attributes:
            return
        for target in targets:
            if isinstance(target, ast.Name):
                established.setdefault(target.id, []).extend(attributes)

    def _scan_runner_scope(self, body: list[ast.stmt], established: dict[str, list[ast.Attribute]]) -> None:
        for node in _iter_scope_nodes(body):
            self._note_runner_assignment(node, established)
        called: set[str] = set()
        calls: list[ast.Call] = []
        for node in _iter_scope_nodes(body):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in established:
                called.add(node.func.id)
                calls.append(node)
        for name in sorted(called):
            for attribute in established[name]:
                self._suppressed_runner_ids.add(id(attribute))
        for call in calls:
            self._add(call, "runner-call", call)

    def _collect_alias_launches(self) -> None:
        """A call through a name bound to ``subprocess.run`` is the launch.

        The default or alias that established the name is not a separate
        baseline row. ``subprocess.run`` stored and not called stays a
        ``runner-reference``.
        """
        module_established: dict[str, list[ast.Attribute]] = {}
        self._scan_runner_scope(self.tree.body, module_established)
        for node in ast.walk(self.tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            established: dict[str, list[ast.Attribute]] = {
                name: list(attributes) for name, attributes in module_established.items()
            }
            positional = node.args.posonlyargs + node.args.args
            pad = len(positional) - len(node.args.defaults)
            for arg, default in zip(positional, [None] * pad + list(node.args.defaults), strict=True):
                if default is None:
                    continue
                attributes = _subprocess_runner_attributes(default)
                if attributes:
                    established.setdefault(arg.arg, []).extend(attributes)
            for arg, default in zip(node.args.kwonlyargs, node.args.kw_defaults, strict=True):
                if default is None:
                    continue
                attributes = _subprocess_runner_attributes(default)
                if attributes:
                    established.setdefault(arg.arg, []).extend(attributes)
            self._scan_runner_scope(node.body, established)

    def _attribute_process_modules(self, node: ast.Attribute) -> set[str]:
        """Modules this attribute expression denotes, when it is the module object."""
        return self._expr_process_modules(node)

    def _collect_references(self) -> None:
        for node in ast.walk(self.tree):
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                self._on_name(node)
            elif isinstance(node, ast.Attribute) and isinstance(node.ctx, ast.Load):
                self._on_attribute(node)

    def _on_name(self, node: ast.Name) -> None:
        if node.id == "ProcessPoolExecutor" and not self._name_is_attribute_host(node):
            self._add(node, "external-capability:ProcessPoolExecutor")
        if not self._process_name_is_value_use(node):
            return
        self._add(node, self._module_value_reason(node.id))
        if "subprocess" in self._module_names.get(node.id, ()):
            self._subprocess_clean = False

    def _on_attribute(self, node: ast.Attribute) -> None:
        modules = self._attribute_process_modules(node)
        parent = self.parents.get(node)
        if modules and not (isinstance(parent, ast.Attribute) and parent.value is node):
            self._add(node, "binding:module-value")
        if node.attr == "ProcessPoolExecutor":
            self._add(node, "external-capability:ProcessPoolExecutor")
        if node.attr in EVENT_LOOP_SUBPROCESS_ATTRS:
            self._add(node, "event-loop-subprocess")
        root = _attribute_root_name(node)
        if root is None:
            self._on_unrooted_attribute(node)
            return
        name, attrs = root
        if not attrs:
            return
        if name in self._os_names and _is_os_process_attr(attrs[-1]) and node.attr == attrs[-1]:
            self._add(node, f"os-process:{node.attr}")
        if name in self._psutil_names and node.attr == "Popen":
            self._add(node, "external-capability:psutil.Popen")
        if name in self._asyncio_names or name in self._asyncio_subprocess_names:
            self._on_asyncio_attribute(node, name, attrs)
        if name in self._subprocess_names and node.attr == attrs[-1] and self._name_is_subprocess(name, attrs[:-1]):
            self._on_subprocess_attribute(node)

    def _name_is_subprocess(self, name: str, leading: tuple[str, ...]) -> bool:
        if leading:
            return False
        return name == "subprocess" or name in self._subprocess_names

    def _on_unrooted_attribute(self, node: ast.Attribute) -> None:
        """``something.subprocess_exec`` is already recorded. Asyncio calls on a call result too."""
        if node.attr in ASYNCIO_SUBPROCESS_ATTRS and self._receiver_is_asyncio(node.value):
            self._add(node, "asyncio-subprocess")

    def _receiver_is_asyncio(self, node: ast.AST) -> bool:
        if isinstance(node, ast.Name):
            return node.id in self._asyncio_names or node.id in self._asyncio_subprocess_names
        if isinstance(node, ast.Attribute) and node.attr == "subprocess":
            return self._receiver_is_asyncio(node.value)
        return False

    def _on_asyncio_attribute(self, node: ast.Attribute, name: str, attrs: tuple[str, ...]) -> None:
        if node.attr in ASYNCIO_SUBPROCESS_ATTRS and (
            name in self._asyncio_subprocess_names or (len(attrs) >= 2 and attrs[-2] == "subprocess")
        ):
            self._add(node, "asyncio-subprocess")
            return
        if node.attr in ASYNCIO_SUBPROCESS_ATTRS and name in self._asyncio_names and attrs == (node.attr,):
            self._add(node, "asyncio-subprocess")
            return
        if (
            node.attr == "subprocess"
            and name in self._asyncio_names
            and not self._asyncio_subprocess_attribute_is_non_launching(node)
        ):
            parent = self.parents.get(node)
            child_is_launcher = (
                isinstance(parent, ast.Attribute)
                and parent.value is node
                and parent.attr in ASYNCIO_SUBPROCESS_ATTRS
            )
            if not child_is_launcher:
                self._add(node, "asyncio-subprocess")

    def _asyncio_subprocess_attribute_is_non_launching(self, node: ast.Attribute) -> bool:
        parent = self.parents.get(node)
        return isinstance(parent, ast.Attribute) and parent.value is node and parent.attr in SUBPROCESS_NON_LAUNCHING

    def _on_subprocess_attribute(self, node: ast.Attribute) -> None:
        parent = self.parents.get(node)
        base_is_plain = isinstance(node.value, ast.Name) and node.value.id == "subprocess"
        if node.attr in SUBPROCESS_NON_LAUNCHING:
            return
        if node.attr.startswith("__") and node.attr.endswith("__"):
            # Dynamic namespace access is a named residual, not a process-start finding.
            return
        if node.attr not in PERMITTED_SUBPROCESS_RUNNERS:
            self._add(node, f"subprocess-attribute:{node.attr}")
            return
        direct_call = isinstance(parent, ast.Call) and parent.func is node and base_is_plain
        if not direct_call or not self._subprocess_clean or not base_is_plain:
            if direct_call and base_is_plain and not self._subprocess_clean:
                self._add(node, "binding:untrusted", parent)
                return
            reason = "runner-reference" if self._subprocess_clean and base_is_plain else "binding:untrusted"
            if reason == "runner-reference" and id(node) in self._suppressed_runner_ids:
                return
            root = _exception_root(node, self.parents) if reason == "runner-reference" else node
            self._add(node, reason, root)
            return
        assert isinstance(parent, ast.Call)
        shape = _call_shape_reason(parent)
        if shape is not None:
            self._add(parent, shape, parent)
            return
        argv = _call_argv_expr(parent)
        if argv is not None and _displayed_argv_has_config_injection(argv):
            self._add(parent, "config-injection", parent)
            return
        if argv is not None and _argv_matches_template(argv):
            return
        self._add(parent, "argv-template", parent)


def collect_process_findings(path: str, tree: ast.AST) -> list[ProcessFinding]:
    """Allowlist findings for one parsed module. Pure AST; nothing is executed."""
    return _ProcessAllowlist(path, tree).collect()


def reconcile_process_findings(
    findings: Iterable[ProcessFinding],
    baseline: Iterable[ProcessException],
) -> tuple[list[Violation], list[str]]:
    """Match eligible findings to the baseline. Rule 1 and rule 3 misses stay violations.

    A baseline row does not waive ``shell=``, ``executable=``, a rebound import,
    or another process API: those reasons are not eligible, so a row with the
    same AST still leaves the violation in place.
    """
    expected: dict[tuple[str, str, str], int] = {}
    for entry in baseline:
        expected[entry.key()] = expected.get(entry.key(), 0) + entry.multiplicity
    grouped: dict[tuple[str, str, str], list[ProcessFinding]] = defaultdict(list)
    violations: list[Violation] = []
    for finding in findings:
        if not finding.eligible:
            violations.append(finding.as_violation())
            continue
        grouped[finding.key()].append(finding)
    for key in sorted(grouped):
        group = sorted(grouped[key], key=lambda item: (item.line, item.column, item.reason))
        allowed = expected.get(key, 0)
        violations.extend(item.as_violation() for item in group[allowed:])
    stale: list[str] = []
    for key in sorted(expected):
        seen = len(grouped.get(key, ()))
        missing = expected[key] - seen
        if missing > 0:
            path, symbol, normalized = key
            stale.extend([f"stale process exception: {path}::{symbol}::{normalized}"] * missing)
    violations.sort(key=lambda item: (item.path, item.line, item.enclosing_symbol, item.detail))
    return violations, stale


def _stale_process_violation(item: str) -> Violation:
    """Turn one reconcile stale row into a single violation.

    ``item`` is ``stale process exception: path::symbol::normalized``. The
    violation kind supplies that prefix once.
    """
    prefix = "stale process exception: "
    body = item.removeprefix(prefix)
    path, symbol, normalized = body.split("::", 2)
    return Violation("stale process exception", path, symbol, normalized)


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


def _is_asyncio_subprocess_module(module: str) -> bool:
    """True for ``asyncio.subprocess``. Its final segment is not ``subprocess``."""
    return module.split(".")[-2:] == ["asyncio", "subprocess"]


def _classify_leaf(leaf: str) -> tuple[str, str] | None:
    """Closed module named by an import's final segment.

    The pair is ``(family, leaf)``. ``family`` is ``boundary`` or ``shlex``.
    """
    if leaf in PUBLIC_EXPORTS:
        return ("boundary", leaf)
    if leaf == "shlex":
        return ("shlex", "shlex")
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
    def __init__(
        self,
        path: str,
        *,
        record_sites: bool,
        enforce_exports: bool,
    ) -> None:
        self.path = path
        self.record_sites = record_sites
        self.enforce_exports = enforce_exports
        self.sites: list[Site] = []
        self.violations: list[Violation] = []
        self.process_findings: list[ProcessFinding] = []
        self._symbols: list[str] = []
        self._may: dict[str, set[_Binding]] = {}
        self._shlex_module_names: set[str] = set()
        self._boundary_names: dict[str, set[str]] = {}
        self._dynamic_aliases: dict[str, str] = {}
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
        # Name use is a total walk. The statement visitor binds imports and
        # records imported callables. It does not decide which nodes can hold
        # a module name.
        self._inspect_bound_module_uses(tree)
        module = _Scope(kind="module", parent=None, module=None)  # type: ignore[arg-type]
        module.module = module
        self._module_scope = module
        self._node_scopes = {id(tree): module}
        self._hoist(tree.body, module)
        for stmt in tree.body:
            self._visit_stmt(stmt, module)
        self.process_findings.extend(collect_process_findings(self.path, tree))


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
        """Record an import whose final segment is shlex or a boundary module.

        ``import module as name`` binds ``name``. ``import package.module``
        binds the root name, and the attribute chain names the module.
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
        """May-bind a boundary module or shlex reached by ``from``."""
        module = node.module or ""
        module_leaf = module.split(".")[-1] if module else ""
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
        """Star-imports of shlex, subprocess, os, asyncio, and the boundary fail.

        Hook modules outside the boundary only. The names a star would bind are
        not expanded.
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
        if node.level == 0 and (module in WILDCARD_IMPORT_MODULES or _is_asyncio_subprocess_module(module)):
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
        # function. Module names do not use this position: may-bind keeps every one.
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


    def _once_literal(self, scope: _Scope, name: str, line: int, column: int) -> _Binding | None:
        """The literal bound to ``name`` when that scope binds the name once.

        A second assignment in the same scope leaves the name unresolved.
        ``global`` and ``nonlocal`` use the scope that holds the binding.
        """
        if name in scope.global_names and scope.module is not scope:
            return self._once_literal(scope.module, name, line, column)
        if name in scope.nonlocal_names and scope.parent is not None:
            return self._once_literal(scope.parent, name, line, column)
        own = [binding for _, _, bound_name, binding in scope.bindings if bound_name == name]
        if own:
            if len(own) != 1:
                return None
            for bound_line, bound_column, bound_name, binding in scope.bindings:
                if bound_name == name and (bound_line, bound_column) <= (line, column):
                    return binding
            # The scope binds the name later. It is local, so an outer binding
            # is not the value of this use.
            return None
        if scope.parent is not None:
            return self._once_literal(scope.parent, name, line, column)
        return None


    def _const_str(self, node: ast.expr, scope: _Scope) -> str | None:
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value
        if isinstance(node, ast.Name):
            binding = self._once_literal(scope, node.id, node.lineno, node.col_offset)
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


def analyze_source(
    path: str,
    source: str,
) -> tuple[list[Site], list[Violation], list[ProcessFinding]]:
    record_sites = path not in BOUNDARY_PATHS
    enforce_exports = record_sites and path not in WHITE_BOX_TESTS
    analyzer = _Analyzer(path, record_sites=record_sites, enforce_exports=enforce_exports)
    if _is_deployed_oracle(path):
        analyzer.add_violation("test-only bash oracle", "deployed with production hooks")
    try:
        tree = ast.parse(source, filename=path)
    except SyntaxError as exc:
        analyzer.add_violation("syntax error", exc.msg or "syntax error")
        return analyzer.sites, analyzer.violations, analyzer.process_findings
    analyzer.analyze(tree)
    return analyzer.sites, analyzer.violations, analyzer.process_findings


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


def _is_unrelated_application(path: str) -> bool:
    """True when ``path`` is an application package outside the helper denominator."""
    return any(path.startswith(prefix) for prefix in UNRELATED_APPLICATION_PREFIXES)


def _follow_helper_import(importer: str, helper: str, *, inside_function: bool, level: int) -> bool:
    """Decide whether a helper import extends the hook's parser chain.

    Hook files and reached helpers follow import-time imports, relative
    imports, and function-local absolute imports, including absolute imports
    that cross a package boundary. Unrelated application packages are not
    entered: the session-start chain reaches them, and their parsers are not
    hook parsers. ``inside_function`` and ``level`` stay in the signature so
    the call records the import form; the package boundary is not the rule.
    """
    del importer, inside_function, level
    return not _is_unrelated_application(helper)


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


def _dotted_module_name(path: str) -> str:
    """Dotted module name of a repo-relative Python path."""
    if path.endswith("/__init__.py"):
        stem = path[: -len("/__init__.py")]
    elif path.endswith(".py"):
        stem = path[:-3]
    else:
        stem = path
    return stem.replace("/", ".")


def _remember_helper_module(
    module_names: dict[str, set[tuple[str, tuple[str, ...]]]],
    local: str,
    dotted: str,
    prefix: tuple[str, ...],
) -> None:
    module_names.setdefault(local, set()).add((dotted, prefix))


def _helper_bindings(
    path: str,
    tree: ast.AST,
    helpers: set[tuple[str, str]],
    by_module: dict[str, dict[str, str]],
) -> tuple[dict[str, set[tuple[str, str]]], dict[str, set[tuple[str, tuple[str, ...]]]]]:
    """Local names that may call a runner helper, and names that may be its module.

    A module binding is ``(dotted module, attribute prefix)``. The prefix is
    empty when the local name is the module, and the remaining dotted segments
    when the import bound only the root package.
    """
    func_names: dict[str, set[tuple[str, str]]] = {}
    module_names: dict[str, set[tuple[str, tuple[str, ...]]]] = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and (path, node.name) in helpers:
            func_names.setdefault(node.name, set()).add((path, node.name))
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            resolved = _resolve_imported_module(path, node.module, node.level)
            if not resolved:
                continue
            funcs = by_module.get(resolved, {})
            for alias in node.names:
                if alias.name == "*":
                    continue
                local = alias.asname or alias.name
                if alias.name in funcs:
                    func_names.setdefault(local, set()).add((funcs[alias.name], alias.name))
                submodule = f"{resolved}.{alias.name}"
                if submodule in by_module:
                    _remember_helper_module(module_names, local, submodule, ())
            continue
        if not isinstance(node, ast.Import):
            continue
        for alias in node.names:
            parts = tuple(alias.name.split("."))
            local = alias.asname or parts[0]
            modules = [alias.name] if alias.name in by_module else []
            if not modules:
                modules = [module for module in by_module if module.startswith(alias.name + ".")]
            for module in modules:
                module_parts = tuple(module.split("."))
                if alias.asname:
                    prefix: tuple[str, ...] = ()
                else:
                    prefix = module_parts[len(parts) :] if module != alias.name else parts[1:]
                _remember_helper_module(module_names, local, module, prefix)
    return func_names, module_names


def _matching_helpers(
    root: str,
    attrs: tuple[str, ...],
    func_names: dict[str, set[tuple[str, str]]],
    module_names: dict[str, set[tuple[str, tuple[str, ...]]]],
    by_module: dict[str, dict[str, str]],
) -> set[tuple[str, str]]:
    if not attrs:
        return set(func_names.get(root, ()))
    func_name = attrs[-1]
    prefix = attrs[:-1]
    found: set[tuple[str, str]] = set()
    for dotted, stored_prefix in module_names.get(root, ()):
        helper_path = by_module.get(dotted, {}).get(func_name)
        if stored_prefix == prefix and helper_path is not None:
            found.add((helper_path, func_name))
    return found


def _expr_helper_bindings(
    expr: ast.expr,
    func_names: dict[str, set[tuple[str, str]]],
    module_names: dict[str, set[tuple[str, tuple[str, ...]]]],
    by_module: dict[str, dict[str, str]],
) -> tuple[set[tuple[str, str]], set[tuple[str, tuple[str, ...]]]]:
    if isinstance(expr, ast.Name):
        return set(func_names.get(expr.id, ())), set(module_names.get(expr.id, ()))
    chain = _attribute_chain(expr)
    if chain is None:
        return set(), set()
    root, attrs = chain
    return _matching_helpers(root.id, attrs, func_names, module_names, by_module), set()


def _propagate_helper_aliases(
    tree: ast.AST,
    func_names: dict[str, set[tuple[str, str]]],
    module_names: dict[str, set[tuple[str, tuple[str, ...]]]],
    by_module: dict[str, dict[str, str]],
) -> None:
    """``cmd = run_command`` and ``alias = module`` keep the helper binding."""
    changed = True
    while changed:
        changed = False
        for node in ast.walk(tree):
            value: ast.expr | None = None
            targets: list[ast.AST] = []
            if isinstance(node, ast.Assign):
                value = node.value
                targets = list(node.targets)
            elif isinstance(node, (ast.AnnAssign, ast.NamedExpr)) and node.value is not None:
                value = node.value
                targets = [node.target]
            if value is None:
                continue
            funcs, modules = _expr_helper_bindings(value, func_names, module_names, by_module)
            for target in targets:
                if not isinstance(target, ast.Name):
                    continue
                if funcs:
                    bucket = func_names.setdefault(target.id, set())
                    before = len(bucket)
                    bucket.update(funcs)
                    changed = changed or len(bucket) != before
                if modules:
                    bucket = module_names.setdefault(target.id, set())
                    before = len(bucket)
                    bucket.update(modules)
                    changed = changed or len(bucket) != before


def _call_targets_helper(
    node: ast.Call,
    func_names: dict[str, set[tuple[str, str]]],
    module_names: dict[str, set[tuple[str, tuple[str, ...]]]],
    by_module: dict[str, dict[str, str]],
) -> bool:
    func = node.func
    if isinstance(func, ast.Name):
        return bool(func_names.get(func.id))
    chain = _attribute_chain(func)
    if chain is None:
        return False
    root, attrs = chain
    if not attrs:
        return False
    return bool(_matching_helpers(root.id, attrs, func_names, module_names, by_module))


def _append_runner_helper_calls(sources: dict[str, str], findings: list[ProcessFinding]) -> None:
    """Pin every scanned call to a function that launches a computed argv.

    The helper's own launch is already a finding. Calls are pinned too, so a
    new argv or an extra call does not hide behind the launch.
    """
    trees: dict[str, ast.Module] = {}
    for path in sorted(sources):
        try:
            trees[path] = ast.parse(sources[path])
        except SyntaxError:
            continue
    launched: dict[str, set[str]] = defaultdict(set)
    for finding in findings:
        if finding.reason in {"argv-template", "runner-call"} and "." not in finding.enclosing_symbol:
            launched[finding.path].add(finding.enclosing_symbol)
    helpers: set[tuple[str, str]] = set()
    for path, tree in trees.items():
        names = launched.get(path, ())
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in names:
                helpers.add((path, node.name))
    if not helpers:
        return
    by_module: dict[str, dict[str, str]] = defaultdict(dict)
    for path, name in sorted(helpers):
        by_module[_dotted_module_name(path)][name] = path
    for path in sorted(trees):
        tree = trees[path]
        parents = _parent_map(tree)
        func_names, module_names = _helper_bindings(path, tree, helpers, by_module)
        _propagate_helper_aliases(tree, func_names, module_names, by_module)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            if not _call_targets_helper(node, func_names, module_names, by_module):
                continue
            findings.append(_finding(path, node, parents, "runner-call", node))


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
    findings: list[ProcessFinding] = []
    for path in (*hook_files, *ordered_helpers):
        if path not in sources:
            if root is None:
                continue
            try:
                sources[path] = _read(root / path)
            except (OSError, UnicodeError) as exc:
                violations.append(Violation("unreadable hook file", path, "<module>", type(exc).__name__))
                continue
        file_sites, file_violations, file_findings = analyze_source(path, sources[path])
        sites.extend(file_sites)
        violations.extend(file_violations)
        findings.extend(file_findings)
    _append_runner_helper_calls(
        {path: sources[path] for path in (*hook_files, *ordered_helpers) if path in sources},
        findings,
    )
    findings.sort(key=lambda item: (item.path, item.line, item.column, item.reason, item.normalized_ast))
    process_violations, stale = reconcile_process_findings(findings, ())
    violations.extend(process_violations)
    violations.extend(_stale_process_violation(item) for item in stale)
    return Check(tuple(sites), tuple(violations), hook_files, ordered_helpers, tuple(findings), ())


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


def _without_process_violations(violations: Iterable[Violation]) -> list[Violation]:
    return [item for item in violations if item.kind not in {"process-start", "stale process exception"}]


def apply_process_baseline(check: Check, baseline: Iterable[ProcessException]) -> Check:
    """Replace unbaselined process violations with the result of ``baseline``."""
    violations = _without_process_violations(check.violations)
    process_violations, stale = reconcile_process_findings(check.process_findings, baseline)
    violations.extend(process_violations)
    violations.extend(_stale_process_violation(item) for item in stale)
    return Check(
        check.sites,
        tuple(violations),
        check.hook_files,
        check.production_helpers,
        check.process_findings,
        tuple(baseline),
    )


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
    combined = Check(
        check.sites,
        tuple(violations) + check.violations,
        hook_files,
        check.production_helpers,
        check.process_findings,
        check.process_exceptions,
    )
    return apply_process_baseline(combined, load_process_baseline())


def load_process_baseline(path: Path = PROCESS_FIXTURE_PATH) -> tuple[ProcessException, ...]:
    """Pinned non-template calls. Missing fixture is an empty baseline, which fails the repo scan."""
    if not path.is_file():
        return ()
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("pinned_count_at_creation") != PROCESS_EXCEPTION_COUNT:
        raise AssertionError(
            f"process fixture pin {payload.get('pinned_count_at_creation')} != {PROCESS_EXCEPTION_COUNT}"
        )
    entries = []
    for item in payload["exceptions"]:
        normalized = item["normalized_ast"]
        if not str(normalized).startswith("Call("):
            raise AssertionError(f"process baseline entry is not a call: {item['path']}::{item['enclosing_symbol']}")
        entries.append(
            ProcessException(
                item["path"],
                item["enclosing_symbol"],
                item["multiplicity"],
                normalized,
                item["explanation"],
            )
        )
    return tuple(entries)


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
    assert len(check.production_helpers) == PRODUCTION_HELPER_COUNT
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
        "    subprocess.run(['git', 'rev-parse', '--git-dir'], check=False)\n"
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
    allowed_sites, allowed_violations, _allowed_findings = analyze_source("tests/test_shell_shlex.py", source)
    denied_sites, denied_violations, _denied_findings = analyze_source("agents_extensions/shared/hooks/guard.py", source)
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


_MUTANT = "agents_extensions/shared/hooks/mutant.py"


def _mutant_site(symbol: str, identity: str) -> str:
    return f"new parser site: {_MUTANT}::{symbol}::{identity}"


def _mutant_violation(kind: str, detail: str, symbol: str = "<module>") -> str:
    return f"{kind}: {_MUTANT}::{symbol}::{detail}"


@pytest.mark.parametrize(
    "module",
    [
        "shlex",
        "subprocess",
        "os",
        "asyncio",
        "asyncio.subprocess",
        "concurrent.futures",
        "multiprocessing",
        "psutil",
        "pty",
        "pexpect",
        "sh",
        "plumbum",
        "shell_shlex",
        "shell_redirects",
    ],
)
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


def test_qualified_boundary_import_private_attribute_fails() -> None:
    source = (
        "import agents_extensions.shared.hooks.shell_shlex\n"
        "agents_extensions.shared.hooks.shell_shlex.shlex.split(\"echo 'a b'\")\n"
    )
    reasons = _single(source)
    assert _mutant_violation("private attribute", "shell_shlex.shlex") in reasons


def test_dynamic_namespace_runner_stays_unresolved() -> None:
    """``globals()``, ``vars()``, ``__dict__``, and ``sys.modules`` do not name a runner."""
    sources = [
        "import subprocess\n\ndef check():\n    return globals()['subprocess'].run(['bash', '-n', 'hook.sh'])\n",
        "import subprocess\n\ndef check():\n    return vars()['subprocess'].run(['bash', '-n', 'hook.sh'])\n",
        "import subprocess\n\ndef check():\n    return subprocess.__dict__['run'](['bash', '-n', 'hook.sh'])\n",
        "import sys\n\ndef check():\n    return sys.modules['subprocess'].run(['bash', '-n', 'hook.sh'])\n",
    ]
    assert all(_single(source) == [] for source in sources)


def test_internal_stdlib_reexport_stays_unresolved() -> None:
    """``asyncio.base_events`` and ``asyncio.events`` are internal re-exports."""
    sources = [
        "from asyncio.base_events import subprocess as sp\n"
        "runner = sp.run\n"
        "result = runner(['bash', '-n', '-c', 'true'])\n",
        "import asyncio.events as events\nevents.subprocess.run(['bash', '-n', '-c', 'true'])\n",
    ]
    assert all(_single(source) == [] for source in sources)


def test_function_local_cross_package_helper_parser_site_fails() -> None:
    helper = "scripts/other/review_helper.py"
    reasons = _overlay_reasons(
        {
            "scripts/hooks/guard.py": "from scripts.parsing.wrapper import load\n",
            "scripts/parsing/wrapper.py": (
                "def load():\n    from scripts.other.review_helper import parse\n    return parse\n"
            ),
            helper: "import shlex\n\ndef parse(command):\n    return shlex.split(command)\n",
        },
        [],
    )
    assert (
        helper
        in analyze_files(
            {
                "scripts/hooks/guard.py": "from scripts.parsing.wrapper import load\n",
                "scripts/parsing/wrapper.py": (
                    "def load():\n    from scripts.other.review_helper import parse\n    return parse\n"
                ),
                helper: "import shlex\n\ndef parse(command):\n    return shlex.split(command)\n",
            }
        ).production_helpers
    )
    assert any(reason == f"new parser site: {helper}::parse::shlex.split" for reason in reasons)


def test_unrelated_application_import_is_not_scanned() -> None:
    """The scope rule keeps application packages out of the helper denominator."""
    sources = {
        "scripts/hooks/guard.py": "from scripts.parsing.helper import load\n",
        "scripts/parsing/helper.py": (
            "def load():\n"
            "    from scripts.ai_agent_bridge.monitor_client import split\n"
            "    from agents_extensions.shared.session_streams.store import split as other\n"
            "    return split, other\n"
        ),
        "scripts/ai_agent_bridge/monitor_client.py": (
            "import shlex\n\ndef split(command):\n    return shlex.split(command)\n"
        ),
        "agents_extensions/shared/session_streams/store.py": (
            "import shlex\n\ndef split(command):\n    return shlex.split(command)\n"
        ),
    }
    check = analyze_files(sources)
    assert "scripts/parsing/helper.py" in check.production_helpers
    assert "scripts/ai_agent_bridge/monitor_client.py" not in check.production_helpers
    assert "agents_extensions/shared/session_streams/store.py" not in check.production_helpers
    assert check.sites == ()
    assert compare_baseline(check, [], pinned_size=BASELINE_SIZE_AT_CREATION) == []


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
    seeded = [_seeded_scan(script, probe, seed) for seed in ("0", "1", "2", "777")]
    assert all(item == seeded[0] for item in seeded[1:])
    assert seeded[0]["violations"] == []
    assert len(seeded[0]["sites"]) == BASELINE_SIZE_AT_CREATION
    assert seeded[0]["probe"] == [_mutant_violation("private attribute", "shell_redirects.preprocess_shell_command")]


_MUTANT_PROCESS = "agents_extensions/shared/hooks/mutant.py"


def _process(line: int, symbol: str, detail: str, path: str = _MUTANT_PROCESS) -> str:
    return f"process-start: {path}:{line}::{symbol}::{detail}"


def test_command_templates_are_pinned() -> None:
    """Silent widening of a reviewed command is a test change, not a refresh."""
    assert COMMAND_TEMPLATES == (
        ("git", ("rev-parse", "--git-common-dir")),
        ("git", ("rev-parse", "--git-dir")),
        ("git", ("rev-parse", "--path-format=absolute", "--git-common-dir")),
        ("git", ("rev-parse", "--path-format=absolute", "--show-toplevel")),
        ("git", ("symbolic-ref", "--quiet", "--short", "HEAD")),
        ("gh", ("api", None)),
        ("gh", ("pr", "checks", None, "--json", "name,bucket,state")),
    )


def test_each_command_template_matches_a_call_on_main() -> None:
    """Every pinned template is a conforming call in the scanned set."""
    seen = [False] * len(COMMAND_TEMPLATES)
    paths = discover_hook_files(REPO_ROOT)
    check = analyze_files({path: _read(REPO_ROOT / path) for path in paths}, root=REPO_ROOT)
    for relative in (*check.hook_files, *check.production_helpers):
        tree = ast.parse(_read(REPO_ROOT / relative), filename=relative)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            argv = _call_argv_expr(node)
            if not isinstance(argv, (ast.List, ast.Tuple)) or not argv.elts:
                continue
            if any(isinstance(elt, ast.Starred) for elt in argv.elts):
                continue
            executable = argv.elts[0]
            if not isinstance(executable, ast.Constant) or not isinstance(executable.value, str):
                continue
            rest = argv.elts[1:]
            for index, (name, parts) in enumerate(COMMAND_TEMPLATES):
                if executable.value != name or len(rest) != len(parts):
                    continue
                if all(_template_part_matches(elt, part) for elt, part in zip(rest, parts, strict=True)):
                    seen[index] = True
    missing = [COMMAND_TEMPLATES[index] for index, found in enumerate(seen) if not found]
    assert missing == []


@pytest.mark.parametrize(
    "argv",
    [
        "['git', 'rev-parse', '--git-common-dir']",
        "['git', 'rev-parse', '--git-dir']",
        "['git', 'rev-parse', '--path-format=absolute', '--git-common-dir']",
        "['git', 'rev-parse', '--path-format=absolute', '--show-toplevel']",
        "['git', 'symbolic-ref', '--quiet', '--short', 'HEAD']",
        "['gh', 'api', f'/repos/{name}']",
        "['gh', 'pr', 'checks', pr, '--json', 'name,bucket,state']",
    ],
)
def test_reviewed_command_template_passes(argv: str) -> None:
    source = f"import subprocess\nname = 'origin'\npr = '1'\nsubprocess.run({argv}, check=False)\n"
    assert _single(source) == []


def test_process_exceptions_match_fixture() -> None:
    loaded = load_process_baseline()
    assert loaded == PROCESS_CREATION_EXCEPTIONS
    assert sum(item.multiplicity for item in loaded) == PROCESS_EXCEPTION_COUNT == 50
    assert len({item.path for item in loaded}) == 10
    hooks = {path: _read(REPO_ROOT / path) for path in discover_hook_files(REPO_ROOT)}
    bare = analyze_files(hooks, root=REPO_ROOT)
    process = [item for item in bare.violations if item.kind == "process-start"]
    assert len(process) == PROCESS_EXCEPTION_COUNT
    assert Counter((item.path, item.enclosing_symbol) for item in process) == Counter(
        (item.path, item.enclosing_symbol) for item in PROCESS_CREATION_EXCEPTIONS
    )
    assert [item.format() for item in analyze_repository().violations] == []


def test_process_exception_replacement_fails() -> None:
    findings = analyze_repository().process_findings
    replaced = list(PROCESS_CREATION_EXCEPTIONS)
    original = replaced[0]
    replaced[0] = ProcessException(
        original.path,
        original.enclosing_symbol,
        original.multiplicity,
        original.normalized_ast + " ",
        original.explanation,
    )
    violations, stale = reconcile_process_findings(findings, replaced)
    assert any(item.path == original.path and item.detail == "argv-template" for item in violations)
    assert any(item.startswith("stale process exception:") and original.path in item for item in stale)


def test_process_exception_duplication_fails() -> None:
    source = (
        "import subprocess\n"
        "\n"
        "def check():\n"
        "    subprocess.run(['git', 'status'])\n"
        "    subprocess.run(['git', 'status'])\n"
    )
    check = analyze_files({_MUTANT_PROCESS: source})
    assert len(check.process_findings) == 2
    finding = check.process_findings[0]
    once = ProcessException(_MUTANT_PROCESS, finding.enclosing_symbol, 1, finding.normalized_ast, "one call")
    violations, stale = reconcile_process_findings(check.process_findings, (once,))
    assert [item.detail for item in violations] == ["argv-template"]
    assert stale == []
    duplicated = (once, once)
    violations, stale = reconcile_process_findings(check.process_findings[:1], duplicated)
    assert violations == []
    assert len(stale) == 1
    assert stale[0].startswith("stale process exception:")


def test_process_exception_regrowth_fails() -> None:
    source = "import subprocess\nsubprocess.run(['git', 'status'])\n"
    assert _single(source) == [_process(2, "<module>", "argv-template")]
    extra = ProcessException("agents_extensions/shared/hooks/other.py", "main", 1, "Call()", "added")
    violations, stale = reconcile_process_findings(
        analyze_repository().process_findings,
        (*PROCESS_CREATION_EXCEPTIONS, extra),
    )
    assert violations == []
    assert any(item.startswith("stale process exception:") and "other.py::main::" in item for item in stale)


def test_process_exception_does_not_waive_rule_one_or_three() -> None:
    samples = [
        "import subprocess\nsubprocess.run(['git', 'rev-parse', '--git-dir'], shell=True)\n",
        "import subprocess\nsubprocess.Popen(['git', 'rev-parse', '--git-dir'])\n",
        "import os\nos.system('true')\n",
        "import subprocess\nsubprocess.run(['git', '-c', 'alias.x=!bash', 'status'])\n",
        "import subprocess as sp\nsp.run(['git', 'rev-parse', '--git-dir'])\n",
        "import subprocess\nrunners = {'run': subprocess.run}\n",
    ]
    for source in samples:
        check = analyze_files({_MUTANT_PROCESS: source})
        assert check.process_findings
        for finding in check.process_findings:
            assert not finding.eligible
            baseline = (
                ProcessException(
                    finding.path,
                    finding.enclosing_symbol,
                    1,
                    finding.normalized_ast,
                    "same ast must not waive this",
                ),
            )
            violations, stale = reconcile_process_findings((finding,), baseline)
            assert [item.detail for item in violations] == [finding.reason]
            assert stale


@pytest.mark.parametrize(
    ("source", "reasons"),
    [
        pytest.param(
            "import os\n\ndef check():\n    os.system('bash' + ' -n hook.sh')\n",
            [_process(4, "check", "os-process:system")],
            id="concatenation",
        ),
        pytest.param(
            'import os\n\ndef check(name):\n    os.system(f"bash -n {name}")\n',
            [_process(4, "check", "os-process:system")],
            id="f-string",
        ),
        pytest.param(
            "import os\n\ndef check(name):\n    os.system('bash -n {}'.format(name))\n",
            [_process(4, "check", "os-process:system")],
            id="format",
        ),
        pytest.param(
            "import subprocess\n"
            "\n"
            "def check():\n"
            "    argv = ['true']\n"
            "    argv = ['bash', '-n', 'hook.sh']\n"
            "    subprocess.run(argv)\n",
            [_process(6, "check", "argv-template")],
            id="rebinding",
        ),
        pytest.param(
            "import subprocess\n"
            "\n"
            "def check():\n"
            "    argv = ['bash', '-c', 'true']\n"
            "    argv.append('-n')\n"
            "    subprocess.run(argv)\n",
            [_process(6, "check", "argv-template")],
            id="argv-name",
        ),
        pytest.param(
            "import asyncio\n"
            "\n"
            "async def check():\n"
            "    await asyncio.create_subprocess_exec('bash', *['-n', 'hook.sh'])\n",
            [_process(4, "check", "asyncio-subprocess")],
            id="starred-create-subprocess-exec",
        ),
        pytest.param(
            "import asyncio\n"
            "\n"
            "def check():\n"
            "    asyncio.get_running_loop().subprocess_exec(None, 'bash', *['-n', 'hook.sh'])\n",
            [_process(4, "check", "event-loop-subprocess")],
            id="starred-loop-subprocess-exec",
        ),
        pytest.param(
            "import asyncio\n"
            "\n"
            "def check(loop: asyncio.AbstractEventLoop):\n"
            "    loop.subprocess_exec(None, 'bash', '-n', 'hook.sh')\n",
            [_process(4, "check", "event-loop-subprocess")],
            id="typed-loop",
        ),
        pytest.param(
            "import asyncio\n"
            "\n"
            "def check(loop=asyncio.new_event_loop()):\n"
            "    loop.subprocess_exec(None, 'bash', '-n', 'hook.sh')\n",
            [_process(4, "check", "event-loop-subprocess")],
            id="defaulted-loop",
        ),
        pytest.param(
            "def check():\n    import subprocess as sp\n    sp.run(['git', 'rev-parse', '--git-dir'])\n",
            [
                _process(2, "check", "binding:function-local-import"),
                _process(3, "check", "binding:untrusted"),
            ],
            id="function-local-module-alias",
        ),
        pytest.param(
            "import subprocess\nsubprocess.Popen(['true'], -1, 'bash')\n",
            [_process(2, "<module>", "subprocess-attribute:Popen")],
            id="popen-positional-executable",
        ),
        pytest.param(
            'import subprocess\nsubprocess.run(["git", "rev-parse", "--git-dir"], **{"executable": "bash"})\n',
            [_process(2, "<module>", "call-shape:executable")],
            id="starred-executable",
        ),
        pytest.param(
            "import subprocess\nsubprocess.run(['git', '-c', 'alias.x=!bash -n hook.sh', 'status'])\n",
            [_process(2, "<module>", "config-injection")],
            id="git-config-alias",
        ),
        pytest.param(
            "from concurrent.futures import ProcessPoolExecutor\nProcessPoolExecutor()\n",
            [
                _process(1, "<module>", "external-capability:ProcessPoolExecutor"),
                _process(2, "<module>", "external-capability:ProcessPoolExecutor"),
            ],
            id="process-pool",
        ),
        pytest.param(
            "import psutil\npsutil.Popen(['true'])\n",
            [_process(2, "<module>", "external-capability:psutil.Popen")],
            id="psutil-popen",
        ),
        pytest.param(
            "import os\nos.startfile('hook.sh')\n",
            [_process(2, "<module>", "os-process:startfile")],
            id="os-startfile",
        ),
    ],
)
def test_held_out_process_start_probes_fail(source: str, reasons: list[str]) -> None:
    assert _single(source) == reasons


def test_helper_aliases_and_reexports_fail_at_the_definition() -> None:
    """A called runner alias is pinned at the call. An import re-export fails at the binding."""
    helper = "scripts/parsing/review_helper.py"
    cases = [
        (
            {
                "scripts/hooks/guard.py": "from ..parsing.review_helper import parse\n",
                helper: (
                    "import subprocess\n"
                    "\n"
                    "def parse(command):\n"
                    "    runner = subprocess.run\n"
                    "    return runner(['bash', '-n', '-c', 'true'])\n"
                ),
            },
            [_process(5, "parse", "runner-call", helper)],
        ),
        (
            {
                "agents_extensions/shared/hooks/guard.py": (
                    "from scripts.parsing.review_helper import run_command\n"
                    "run_command(['bash', '-n', '-c', 'true'])\n"
                ),
                helper: "from subprocess import run as run_command\n",
            },
            [_process(1, "<module>", "binding:from-import", helper)],
        ),
        (
            {
                "agents_extensions/shared/hooks/guard.py": "from scripts.parsing.review_helper import sp\n",
                helper: "import subprocess as sp\n",
            },
            [_process(1, "<module>", "binding:aliased-import", helper)],
        ),
        (
            {
                "scripts/hooks/guard.py": "from scripts.parsing.wrapper import go\ngo(['bash', '-n', '-c', 'true'])\n",
                "scripts/parsing/wrapper.py": "from scripts.parsing.base import run_command as go\n",
                "scripts/parsing/base.py": "from subprocess import run as run_command\n",
            },
            [_process(1, "<module>", "binding:from-import", "scripts/parsing/base.py")],
        ),
    ]
    for sources, expected in cases:
        assert _overlay_reasons(sources, []) == expected


def test_conditional_runner_reexport_fails_at_both_arms() -> None:
    helper = "scripts/parsing/review_helper.py"
    reasons = _overlay_reasons(
        {
            "agents_extensions/shared/hooks/guard.py": "from scripts.parsing.review_helper import pick\n",
            helper: (
                "import subprocess\n"
                "\n"
                "def pick(flag):\n"
                "    go = subprocess.run if flag else subprocess.call\n"
                "    return go\n"
            ),
        },
        [],
    )
    assert reasons == [
        _process(4, "pick", "runner-reference", helper),
        _process(4, "pick", "runner-reference", helper),
    ]


def test_false_branch_subprocess_rebind_fails() -> None:
    source = (
        "import subprocess\n"
        "\n"
        "def check():\n"
        "    if False:\n"
        "        subprocess = None\n"
        "    subprocess.run(['git', 'rev-parse', '--git-dir'])\n"
    )
    assert _single(source) == [
        _process(5, "check", "binding:rebound"),
        _process(6, "check", "binding:untrusted"),
    ]


def test_runner_stored_or_passed_fails_without_following_the_name() -> None:
    """A stored or passed runner stays a reference. A default that is called is the launch."""
    stored = "import subprocess\nrunners = {'run': subprocess.run}\n"
    passed = "import subprocess\ncall(subprocess.run)\n"
    defaulted = "import subprocess\n\ndef check(runner=subprocess.run):\n    return runner(['bash', '-n', 'hook.sh'])\n"
    assert _single(stored) == [_process(2, "<module>", "runner-reference")]
    assert _single(passed) == [_process(2, "<module>", "runner-reference")]
    assert _single(defaulted) == [_process(4, "check", "runner-call")]


def test_process_apis_fail_without_a_syntax_flag() -> None:
    """The allowlist is not a bash -n detector. Any unlisted process start fails."""
    cases = [
        (
            "import os\n\ndef check():\n    os.system('true')\n",
            [_process(4, "check", "os-process:system")],
        ),
        (
            "import os\nos.posix_spawn('/bin/bash', ['bash', '-c', 'true'], {})\n",
            [_process(2, "<module>", "os-process:posix_spawn")],
        ),
        (
            "import subprocess\nsubprocess.getoutput('echo hi')\n",
            [_process(2, "<module>", "subprocess-attribute:getoutput")],
        ),
        (
            "import subprocess\nsubprocess.run(['make', '-n', 'preview'])\n",
            [_process(2, "<module>", "argv-template")],
        ),
        (
            "import subprocess\nsubprocess.run('true', shell=True)\n",
            [_process(2, "<module>", "call-shape:shell")],
        ),
        (
            "import asyncio\n\nasync def check():\n    await asyncio.create_subprocess_shell('true')\n",
            [_process(4, "check", "asyncio-subprocess")],
        ),
        (
            "import asyncio\n\ndef check():\n    asyncio.subprocess_exec(None, 'true')\n",
            [_process(4, "check", "event-loop-subprocess")],
        ),
        (
            "def check(loop):\n    loop.subprocess_exec(None, 'true')\n    loop.subprocess_shell(None, 'true')\n",
            [
                _process(2, "check", "event-loop-subprocess"),
                _process(3, "check", "event-loop-subprocess"),
            ],
        ),
    ]
    for source, expected in cases:
        assert _single(source) == expected


def test_non_launching_and_unresolved_forms_pass() -> None:
    sources = [
        "import subprocess\nsubprocess.run(['git', 'rev-parse', '--git-dir'], shell=False, stdout=subprocess.DEVNULL)\n",
        "import subprocess\n\ndef annotate(done: subprocess.CompletedProcess[str]):\n    return done\n",
        "import psutil\npsutil.Process(1)\n",
        "import concurrent.futures\nconcurrent.futures.ThreadPoolExecutor()\n",
        "import asyncio\nasyncio.subprocess.PIPE\n",
        "import os\ngetattr(os, 'O_DIRECTORY', 0)\n",
        "import subprocess\n\ndef check():\n    return globals()['subprocess'].run(['bash', '-n', 'hook.sh'])\n",
        "import subprocess\nsubprocess.__dict__['run'](['bash', '-n', 'hook.sh'])\n",
        "import sys\n\ndef check():\n    return sys.modules['subprocess'].run(['bash', '-n', 'hook.sh'])\n",
        "from asyncio.base_events import subprocess as sp\nrunner = sp.run\n",
        "import asyncio.events as events\nevents.subprocess.run(['bash', '-n', 'hook.sh'])\n",
        'import subprocess\n\ndef f(v: "subprocess.run([\'bash\', \'-n\', \'a\'])"):\n    pass\n',
    ]
    assert all(_single(source) == [] for source in sources)


def test_popen_reentry_reports_only_the_constructor() -> None:
    source = (
        "import subprocess\n"
        "p = subprocess.Popen(['true'])\n"
        "p.__init__(['bash', '-n', '-c', 'true'])\n"
        "type(p)(['bash', '-n', '-c', 'true'])\n"
    )
    assert _single(source) == [_process(2, "<module>", "subprocess-attribute:Popen")]


def test_star_import_is_not_expanded_into_a_process_start() -> None:
    subprocess_star = "from subprocess import *\nrun(['bash', '-n', '-c', 'true'])\n"
    asyncio_star = (
        "from asyncio.subprocess import *\n"
        "\n"
        "async def check():\n"
        "    await create_subprocess_exec('bash', '-n', '-c', 'true')\n"
    )
    assert _single(subprocess_star) == [_mutant_violation("wildcard import", "subprocess")]
    assert _single(asyncio_star) == [_mutant_violation("wildcard import", "asyncio.subprocess")]


def test_module_object_and_os_escape_fail() -> None:
    assert _single("import subprocess\ngetattr(subprocess, 'run')\n") == [
        _process(2, "<module>", "binding:module-value")
    ]
    assert _single("import os as operating_system\nstored = operating_system\n") == [
        _process(2, "<module>", "os-escape")
    ]
    assert _single("import os\ngetattr(os, 'system')\n") == [_process(2, "<module>", "os-escape")]


def test_reviewer_module_value_probes_fail() -> None:
    """A process-capable module used as a value is a violation, including after rebinding."""
    cases = [
        (
            "import asyncio\n"
            "api = asyncio\n"
            "\n"
            "async def check():\n"
            "    await api.create_subprocess_exec('bash', '-n', stdin=-1)\n",
            [
                _process(2, "<module>", "binding:module-value"),
                _process(5, "check", "asyncio-subprocess"),
                _process(5, "check", "binding:module-value"),
            ],
        ),
        (
            "import psutil\n"
            "api = psutil\n"
            "api.Popen(['bash', '-n'], stdin=-1)\n",
            [
                _process(2, "<module>", "binding:module-value"),
                _process(3, "<module>", "binding:module-value"),
                _process(3, "<module>", "external-capability:psutil.Popen"),
            ],
        ),
        (
            "from psutil import *\nPopen(['bash', '-n'], stdin=-1)\n",
            [_mutant_violation("wildcard import", "psutil")],
        ),
        (
            "import asyncio\ndef check():\n    return asyncio\n",
            [_process(3, "check", "binding:module-value")],
        ),
        (
            "import asyncio\nstored = [asyncio]\n",
            [_process(2, "<module>", "binding:module-value")],
        ),
        (
            "import psutil\ncall(psutil)\n",
            [_process(2, "<module>", "binding:module-value")],
        ),
        (
            "import os\napi = os\napi.system('true')\n",
            [
                _process(2, "<module>", "os-escape"),
                _process(3, "<module>", "os-escape"),
                _process(3, "<module>", "os-process:system"),
            ],
        ),
        (
            "import asyncio\nsub = asyncio.subprocess\n",
            [
                _process(2, "<module>", "asyncio-subprocess"),
                _process(2, "<module>", "binding:module-value"),
            ],
        ),
    ]
    for source, expected in cases:
        assert _single(source) == expected


def test_reviewer_subprocess_rebinding_probes_fail() -> None:
    """Every binding of the name subprocess, then a permitted template, is untrusted."""
    template = "subprocess.run(['git', 'rev-parse', '--git-dir'])\n"
    cases = [
        (
            "import subprocess\nitems = [None]\nvalues = [None for subprocess in items]\n" + template,
            [
                _process(3, "<module>", "binding:rebound"),
                _process(4, "<module>", "binding:untrusted"),
            ],
        ),
        (
            "import subprocess\nvalue = None\nmatch value:\n    case subprocess:\n        pass\n" + template,
            [
                _process(4, "<module>", "binding:rebound"),
                _process(6, "<module>", "binding:untrusted"),
            ],
        ),
        (
            "import os as subprocess\n" + template,
            [
                _process(1, "<module>", "binding:rebound"),
                _process(2, "<module>", "binding:untrusted"),
            ],
        ),
        (
            "from os import path as subprocess\n" + template,
            [
                _process(1, "<module>", "binding:rebound"),
                _process(2, "<module>", "binding:untrusted"),
            ],
        ),
        (
            "import subprocess\nif (subprocess := None):\n    pass\n" + template,
            [
                _process(2, "<module>", "binding:rebound"),
                _process(4, "<module>", "binding:untrusted"),
            ],
        ),
        (
            "import subprocess\nfor subprocess in (None,):\n    pass\n" + template,
            [
                _process(2, "<module>", "binding:rebound"),
                _process(4, "<module>", "binding:untrusted"),
            ],
        ),
        (
            "import subprocess\n"
            "class CM:\n"
            "    def __enter__(self):\n"
            "        return None\n"
            "    def __exit__(self, *args):\n"
            "        return False\n"
            "with CM() as subprocess:\n"
            "    pass\n"
            + template,
            [
                _process(7, "<module>", "binding:rebound"),
                _process(9, "<module>", "binding:untrusted"),
            ],
        ),
        (
            "import subprocess\ntry:\n    pass\nexcept Exception as subprocess:\n    pass\n" + template,
            [
                _process(4, "<module>", "binding:rebound"),
                _process(6, "<module>", "binding:untrusted"),
            ],
        ),
        (
            "import subprocess\ndef check():\n    global subprocess\n    " + template,
            [
                _process(3, "check", "binding:rebound"),
                _process(4, "check", "binding:untrusted"),
            ],
        ),
        (
            "import subprocess\n"
            "def outer():\n"
            "    subprocess = None\n"
            "    def inner():\n"
            "        nonlocal subprocess\n"
            "        " + template +
            "    return inner\n",
            [
                _process(3, "outer", "binding:rebound"),
                _process(5, "outer.inner", "binding:rebound"),
                _process(6, "outer.inner", "binding:untrusted"),
            ],
        ),
    ]
    for source, expected in cases:
        assert _single(source) == expected


def _overlaid_violation_text(path: str, source: str) -> list[str]:
    sources = {item: _read(REPO_ROOT / item) for item in discover_hook_files(REPO_ROOT)}
    sources[path] = source
    check = analyze_files(sources, root=REPO_ROOT)
    applied = apply_process_baseline(check, load_process_baseline())
    return [item.format() for item in applied.violations]


def test_reviewer_runner_overlays_are_not_covered_by_the_baseline() -> None:
    """Replacing or adding a runner call fails without editing the pinned calls."""
    snapshot = "scripts/opsec/gh_snapshot.py"
    snapshot_text = _read(REPO_ROOT / snapshot)
    origin = '["git", "remote", "get-url", "origin"]'
    assert snapshot_text.count(origin) == 1
    snapshot_reasons = _overlaid_violation_text(snapshot, snapshot_text.replace(origin, '["bash", "-n", "probe"]', 1))
    process = [item for item in snapshot_reasons if item.startswith("process-start:")]
    stale = [item for item in snapshot_reasons if item.startswith("stale process exception:")]
    assert process == [f"process-start: {snapshot}:471::repository::runner-call"]
    assert len(stale) == 1
    assert stale[0].startswith(f"stale process exception: {snapshot}::repository::Call(")
    assert "Constant(value='get-url')" in stale[0]
    assert "probe" not in stale[0]
    assert len(snapshot_reasons) == 2

    prepublish = "scripts/opsec/prepublish.py"
    prepublish_text = _read(REPO_ROOT / prepublish)
    fallback = "        return runner(args, **kwargs)\n"
    assert prepublish_text.count(fallback) == 1
    inserted = fallback + '    runner(["bash", "-n", "probe"])\n'
    prepublish_reasons = _overlaid_violation_text(prepublish, prepublish_text.replace(fallback, inserted, 1))
    assert prepublish_reasons == [f"process-start: {prepublish}:503::checked_run::runner-call"]

    hook = "agents_extensions/shared/hooks/probe_runner.py"
    hook_reasons = _overlaid_violation_text(
        hook,
        "from scripts.orchestration.thread_handoff import run_command\n" 'run_command(["bash", "-nc", "if"])\n',
    )
    assert hook_reasons == [f"process-start: {hook}:2::<module>::runner-call"]


def test_process_baseline_rejects_a_non_call(tmp_path: Path) -> None:
    fixture = tmp_path / "baseline.json"
    fixture.write_text(
        json.dumps(
            {
                "pinned_count_at_creation": PROCESS_EXCEPTION_COUNT,
                "exceptions": [
                    {
                        "path": "scripts/opsec/gh_snapshot.py",
                        "enclosing_symbol": "repository",
                        "multiplicity": 1,
                        "normalized_ast": (
                            "Attribute(value=Name(id='subprocess', ctx=Load()), attr='run', ctx=Load())"
                        ),
                        "explanation": "reader default",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(AssertionError, match="process baseline entry is not a call"):
        load_process_baseline(fixture)


def test_syntax_check_tracker_is_gone() -> None:
    """Slice 2a does not keep a bash -n, runner-alias, or computed-command tracker."""
    source = Path(__file__).read_text(encoding="utf-8")
    markers = (
        "SYNTAX_CHECK_" + "SHELLS =",
        "def _syntax_" + "identity",
        "def _inspect_syntax_" + "check_calls",
        "def _inspect_runner_" + "escape",
        "def _collect_runner_" + "reexports",
        "def _split_" + "command",
    )
    for marker in markers:
        assert marker not in source
