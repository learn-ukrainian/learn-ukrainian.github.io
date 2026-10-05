"""Every headless Claude Code launch under ``scripts/`` goes through one chokepoint (#9750).

A print-mode run (``claude -p`` / ``--print``) ends with its final turn, so any
background work it started is lost (#9690). ``scripts/agent_runtime/adapters/claude.py``
defines the controls and ``headless_claude_launch(argv, env)``, which returns the
argv with the background tools denied and the env with background execution
disabled. Direct launchers start the child with exactly that pair.

Two layers:

1. **Behaviour (the guarantee).** For each direct launcher, a test drives the
   caller's real code path with its process boundary patched and asserts the
   argv and env the child would receive.
2. **Discovery (a tripwire).** A static scan of every Python module and shell
   script under ``scripts/`` resolves argv values (literals, local variables,
   concatenation, list mutation, ``shlex.split``, same-module builders, shell
   command strings) and flags each Claude print-mode argv that reaches a process
   launch, or is returned from its function, without being the chokepoint's argv
   accompanied by the chokepoint's env. A shell command string can never pass the
   chokepoint, so one that runs ``claude -p`` is always flagged.

Static limits, each covered by the behavioural layer rather than the scan:

- A value from another module is opaque, so a print flag imported from elsewhere
  (``["claude", *FLAGS]``) is not resolved
  (``test_static_limit_imported_print_flag_is_documented``).
- Branch conditions are not evaluated. The scan fails closed: a Claude argv
  that exists on any path must be controlled on every path that launches it.
  Where paths meet (branches, conditional expressions, ``and``/``or``, loop
  back edges, a function's several returns, the edges into ``except`` and
  ``finally`` from every state of the ``try`` body), an env stays the
  chokepoint's env only if it is that env on every path holding the
  chokepoint's argv. Loops are re-run until those facts are stable.
- ``contextlib.suppress`` is modelled as a path out of every state of its
  block; another context manager whose ``__exit__`` swallows exceptions is not.
- Dynamic dispatch (``getattr``, ``functools.partial``, ``eval``) is not followed,
  nor a launch wrapper defined in a module that neither names Claude nor
  launches a process itself.
- A module without both ``claude`` and a print-flag literal in its text is not
  scanned: it could only supply them through another module's value, which is
  opaque anyway.
- Agent-runtime plans (``InvocationPlan``) are launched by the shared runner.
  A plan-building Claude argv must live in an adapter listed in
  ``tests/agent_runtime/test_claude_no_background.py::_CLAUDE_CODE_HARNESSES``,
  whose tests drive the real runner. A shell script that runs ``claude -p`` must
  be named by a behavioural test there.
"""

from __future__ import annotations

import ast
import json
import re
import shlex
import subprocess
import textwrap
from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field
from itertools import pairwise, product
from pathlib import Path
from typing import Any

import pytest

from scripts.agent_runtime.adapters.claude import HEADLESS_BACKGROUND_TOOL_DENIES, headless_claude_launch

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = REPO_ROOT / "scripts"
ADAPTER = "scripts/agent_runtime/adapters/claude.py"
NO_BACKGROUND_TESTS = REPO_ROOT / "tests/agent_runtime/test_claude_no_background.py"
CHOKEPOINT = headless_claude_launch.__name__
PRINT_FLAGS = frozenset({"-p", "--print"})
SWITCH = "CLAUDE_CODE_DISABLE_BACKGROUND_TASKS"
DENIES = ",".join(HEADLESS_BACKGROUND_TOOL_DENIES)

# Shell scripts that run ``claude -p``, each mapped to the test in
# NO_BACKGROUND_TESTS that launches it through the real runner.
SHELL_LAUNCHERS: dict[str, str] = {
    "scripts/agent_runtime/kimicc_headless.sh": "test_kimicc_runner_launch_carries_switch_and_denies",
}

# The direct launchers. The scan must see each, controlled; each has a
# behavioural test below.
KNOWN_LAUNCHES = (
    "scripts/batch/batch_dispatcher_helpers.py::dispatch_claude_fix",
    "scripts/pipeline/dispatch.py::dispatch_claude_phase",
    "scripts/audit/code_review_benchmark.py::build_native_command",
    "scripts/audit/code_review_benchmark.py::run_native_cli",
    "scripts/audit/judge_calibration_matrix.py::build_native_command",
    "scripts/audit/judge_calibration_matrix.py::run_native_cli",
    "scripts/ai_agent_bridge/openai_proxy.py::_claude_backend",
    "scripts/eval/zno_nmt/adapters.py::run_claude",
    "scripts/review/isolation.py::build_claude_review_argv",
)


# --- Values ------------------------------------------------------------------


@dataclass(frozen=True)
class Tok:
    """One argv element: its text (``\\0`` marks unknown fragments) or the names behind it."""

    text: str | None = None
    names: frozenset[str] = frozenset()
    spread: bool = False  # an unknown number of elements


Alt = tuple[tuple[Tok, ...], int | None]  # argv elements, chokepoint call that produced them


@dataclass(frozen=True)
class Val:
    """An abstract value: as one string, as the argvs it may hold, as a fixed tuple."""

    tok: Tok | None = None
    alts: frozenset[Alt] = frozenset()
    env_marks: frozenset[int] = frozenset()  # chokepoint calls whose env this may be
    items: tuple[Val, ...] | None = None


_MAX_ALTS = 64


def _names(node: ast.AST) -> frozenset[str]:
    found: set[str] = set()
    for child in ast.walk(node):
        if isinstance(child, ast.Name):
            found.add(child.id)
        elif isinstance(child, ast.Attribute):
            found.add(child.attr)
    return frozenset(found)


def _opaque(names: frozenset[str]) -> Val:
    return Val(tok=Tok(names=names), alts=frozenset({((Tok(names=names, spread=True),), None)}))


def _prints(toks: tuple[Tok, ...]) -> bool:
    return any(tok.text in PRINT_FLAGS for tok in toks)


def _cap(alts: Iterable[Alt]) -> frozenset[Alt]:
    """Bound an argv set, keeping print-mode argvs first and, among them, unmarked ones."""
    alts = alts if isinstance(alts, (frozenset, set, list, tuple)) else list(alts)
    if len(alts) <= _MAX_ALTS:
        return frozenset(alts)
    ranked = sorted(alts, key=lambda alt: (not _prints(alt[0]), alt[1] is not None))
    return frozenset(ranked[:_MAX_ALTS])


def _as_argv(val: Val) -> frozenset[Alt]:
    if val.alts:
        return val.alts
    return frozenset({(((val.tok or Tok()),), None)})


def _as_element(val: Val) -> Tok:
    if val.tok is not None:
        return val.tok
    names = frozenset(name for toks, _ in val.alts for tok in toks for name in tok.names)
    return Tok(names=names)


def _concat(left: frozenset[Alt], right: frozenset[Alt]) -> frozenset[Alt]:
    """Concatenate argvs; only an unchanged (copied) argv keeps its chokepoint mark."""

    def combine(first: Alt, second: Alt) -> Alt:
        (a, mark_a), (b, mark_b) = first, second
        return a + b, mark_b if not a else mark_a if not b else None

    if len(left) * len(right) <= _MAX_ALTS:
        return frozenset(combine(a, b) for a, b in product(left, right))
    # Rank before combining: a combined argv prints if either part does.
    lefts = [(alt, _prints(alt[0])) for alt in left]
    rights = [(alt, _prints(alt[0])) for alt in right]
    candidates = [(combine(a, b), prints_a or prints_b) for (a, prints_a), (b, prints_b) in product(lefts, rights)]
    candidates.sort(key=lambda candidate: (not candidate[1], candidate[0][1] is not None))
    return frozenset(alt for alt, _ in candidates[:_MAX_ALTS])


def _argv_marks(val: Val) -> frozenset[int]:
    """Chokepoint calls whose argv ``val`` (or one of its items) may hold."""
    marks = frozenset(mark for _, mark in val.alts if mark is not None)
    for item in val.items or ():
        marks |= _argv_marks(item)
    return marks


def _has_env_marks(val: Val) -> bool:
    return bool(val.env_marks) or any(_has_env_marks(item) for item in val.items or ())


def _drop_env_marks(val: Val, live: frozenset[int]) -> Val:
    """``val`` joined with a path where it is not that chokepoint's env and ``live`` argvs exist."""
    if not live or not _has_env_marks(val):
        return val
    items = None if val.items is None else tuple(_drop_env_marks(item, live) for item in val.items)
    return Val(tok=val.tok, alts=val.alts, env_marks=val.env_marks - live, items=items)


def _env_signature(val: Val) -> tuple[Any, ...]:
    return (val.env_marks, tuple(_env_signature(item) for item in val.items or ()))


def _mark_signature(state: dict[str, Val]) -> dict[str, tuple[Any, ...]]:
    """What a state says about chokepoint pairs: the only facts a loop pass must stabilise.

    Argvs may keep growing (an accumulator list), but marks form a finite set, so
    passes compared on this projection converge.
    """
    signature: dict[str, tuple[Any, ...]] = {}
    for key, val in state.items():
        marks = _argv_marks(val)
        if marks or _has_env_marks(val):
            signature[key] = (marks, _env_signature(val))
    return signature


def _join(a: Val, b: Val, live_a: frozenset[int], live_b: frozenset[int]) -> Val:
    """Join the values one name holds on two paths.

    ``live_a`` / ``live_b`` are the chokepoint argvs that exist on each path. The
    join is conservative: an env stays a chokepoint's env only if, on every path
    where that chokepoint's argv exists, it is that env. A path that never held
    the argv cannot launch it, so it does not withdraw the mark.
    """
    if a == b:
        return a
    if a.tok == b.tok:
        tok = a.tok
    elif a.tok is None or b.tok is None:
        tok = a.tok or b.tok
    else:
        tok = Tok(names=a.tok.names | b.tok.names)
    items = None
    if a.items is not None and b.items is not None and len(a.items) == len(b.items):
        items = tuple(_join(x, y, live_a, live_b) for x, y in zip(a.items, b.items, strict=True))
    env_marks = frozenset(
        mark
        for mark in a.env_marks | b.env_marks
        if (mark in a.env_marks or mark not in live_a) and (mark in b.env_marks or mark not in live_b)
    )
    return Val(tok=tok, alts=_cap(a.alts | b.alts), env_marks=env_marks, items=items)


# --- Shell command lines ---------------------------------------------------------

_SHELL_PUNCT = frozenset({";", "&", "|", "&&", "||", "(", ")", ";;", "|&", "{", "}", "$"})
_SHELL_KEYWORDS = frozenset(
    {"if", "then", "else", "elif", "fi", "do", "done", "while", "until", "case", "esac", "!", "[[", "]]"}
)
_DECLARATIONS = frozenset({"local", "export", "declare", "readonly", "typeset", "alias"})
_PROGRAM_WRAPPERS = frozenset(
    {
        "builtin",
        "bunx",
        "command",
        "env",
        "eval",
        "exec",
        "ionice",
        "nice",
        "nohup",
        "npx",
        "pnpx",
        "setsid",
        "stdbuf",
        "sudo",
        "systemd-run",
        "time",
        "timeout",
        "unbuffer",
        "xvfb-run",
    }
)
_SHELLS = frozenset({"sh", "bash", "zsh", "dash", "ksh"})
_ASSIGNMENT = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)(\[[^\]]*\])?\+?=(.*)$", re.S)
_WRAPPER_ARG = re.compile(r"^(-.*|[A-Za-z_][A-Za-z0-9_]*=.*|\d+(\.\d+)?[smhd]?)$", re.S)
_HEREDOC = re.compile(r"(?<!<)<<(?!<)-?\s*['\"]?([A-Za-z_][A-Za-z0-9_]*)['\"]?")
_FUNCTION = re.compile(r"^\s*(?:function\s+)?([A-Za-z_][A-Za-z0-9_:-]*)\s*\(\s*\)|^\s*function\s+([A-Za-z_][\w:-]*)")


def _logical_shell_lines(text: str) -> Iterator[tuple[int, str]]:
    """Yield ``(line number, line)`` with continuations joined and heredoc bodies dropped."""
    lines = text.splitlines()
    index = 0
    heredoc: str | None = None
    while index < len(lines):
        start = index + 1
        line = lines[index]
        index += 1
        if heredoc is not None:
            if line.strip() == heredoc:
                heredoc = None
            continue
        while line.endswith("\\") and (len(line) - len(line.rstrip("\\"))) % 2 == 1 and index < len(lines):
            line = line[:-1] + " " + lines[index]
            index += 1
        match = _HEREDOC.search(line)
        if match:
            heredoc = match.group(1)
        yield start, line


def _shell_tokens(line: str) -> list[str]:
    prepared = line.replace("$(", " ( ").replace("`", " ; ")
    lexer = shlex.shlex(prepared, posix=True, punctuation_chars=";&|()")
    lexer.whitespace_split = True
    lexer.commenters = "#"
    try:
        return list(lexer)
    except ValueError:
        return re.findall(r"[;&|()]+|[^\s;&|()]+", prepared.split(" #", 1)[0])


def _shell_commands(tokens: list[str]) -> Iterator[list[str]]:
    current: list[str] = []
    for token in tokens:
        if token in _SHELL_PUNCT or (token and set(token) <= set(";&|()")):
            if current:
                yield current
            current = []
        else:
            current.append(token)
    if current:
        yield current


def _shell_program(command: list[str]) -> int | None:
    index = 0
    while index < len(command):
        token = command[index]
        if token in _SHELL_KEYWORDS or _ASSIGNMENT.match(token):
            index += 1
        elif token in _DECLARATIONS:
            return None
        elif Path(token.lstrip("\\")).name in _PROGRAM_WRAPPERS:
            index += 1
            while index < len(command) and _WRAPPER_ARG.match(command[index]):
                index += 1
        else:
            return index
    return None


def _shell_names_claude(token: str, aliases: set[str]) -> bool:
    name = Path(token.lstrip("\\")).name if "/" in token else token.lstrip("\\")
    variable = re.match(r"^\$\{?([A-Za-z_][A-Za-z0-9_]*)", name)
    if variable:
        return "claude" in variable.group(1).lower() or variable.group(1) in aliases
    return "claude" in name.lower() or name in aliases


def shell_claude_print_lines(text: str) -> list[int]:
    """Lines of a shell script or command string that run Claude Code in print mode."""
    commands: list[tuple[int, list[str], str | None]] = []
    assignments: list[tuple[str, list[str]]] = []
    function: str | None = None
    depth = 0
    for lineno, line in _logical_shell_lines(text):
        tokens = _shell_tokens(line)
        for index, token in enumerate(tokens):
            assignment = _ASSIGNMENT.match(token)
            if assignment is None:
                continue
            if assignment.group(3):
                assignments.append((assignment.group(1), _shell_tokens(assignment.group(3))[:1]))
            elif tokens[index + 1 : index + 2] == ["("]:
                inner = tokens[index + 2 : tokens.index(")", index) if ")" in tokens[index:] else len(tokens)]
                assignments.append((assignment.group(1), [t for t in inner if not t.startswith("-")]))
        defined = _FUNCTION.match(line)
        if defined and depth == 0:
            function = defined.group(1) or defined.group(2)
        depth = max(0, depth + tokens.count("{") - tokens.count("}"))
        for command in _shell_commands(tokens):
            commands.append((lineno, command, function if depth or defined else None))
        if depth == 0 and not defined:
            function = None

    aliases: set[str] = set()
    changed = True
    while changed:
        changed = False
        for name, values in assignments:
            if name not in aliases and any(_shell_names_claude(value, aliases) for value in values):
                aliases.add(name)
                changed = True
        for _, command, function in commands:
            program = _shell_program(command)
            if (
                function is not None
                and function not in aliases
                and program is not None
                and _shell_names_claude(command[program], aliases)
            ):
                aliases.add(function)
                changed = True

    hits: list[int] = []
    for lineno, command, _ in commands:
        program = _shell_program(command)
        if program is None:
            continue
        if _shell_names_claude(command[program], aliases) and PRINT_FLAGS & set(command[program + 1 :]):
            hits.append(lineno)
    return sorted(set(hits))


# --- Python argv classification --------------------------------------------------


def _text_names_claude(text: str) -> bool:
    return "claude" in text.replace("\0", "/").rstrip("/").rsplit("/", 1)[-1].lower()


def _tok_names_claude(tok: Tok) -> bool:
    if tok.text is not None and "\0" not in tok.text:
        return _text_names_claude(tok.text)
    if tok.text is not None and _text_names_claude(tok.text):
        return True
    return any("claude" in name.lower() for name in tok.names)


def _program_index(toks: tuple[Tok, ...]) -> int | None:
    index = 0
    while index < len(toks):
        tok = toks[index]
        if tok.text is not None and Path(tok.text).name in _PROGRAM_WRAPPERS:
            index += 1
            while index < len(toks) and toks[index].text is not None and _WRAPPER_ARG.match(toks[index].text):
                index += 1
            continue
        return index
    return None


def _alt_kind(toks: tuple[Tok, ...], scope_names_claude: bool) -> str | None:
    """``direct`` for a Claude print-mode argv, ``shell`` for one run through a shell."""
    index = _program_index(toks)
    if index is None:
        return None
    program = toks[index]
    rest = toks[index + 1 :]
    if program.text is not None and Path(program.text).name in _SHELLS:
        for flag, script in pairwise(rest):
            if flag.text == "-c" and script.text is not None and shell_claude_print_lines(script.text):
                return "shell"
        return None
    known_other = program.text is not None and "\0" not in program.text and not program.spread
    claude = _tok_names_claude(program) or (not known_other and scope_names_claude)
    if not claude:
        return None
    for tok in rest:
        if tok.text == "--":
            break
        if tok.text in PRINT_FLAGS:
            return "direct"
    return None


# --- Process launches ------------------------------------------------------------------

# Qualified callee -> (argv position, argv keyword, env position or keyword).
_LAUNCH_APIS: dict[str, tuple[int | str, str | None, int | str | None]] = {
    **{f"subprocess.{name}": (0, "args", "env") for name in ("run", "Popen", "call", "check_call", "check_output")},
    "subprocess.getoutput": (0, "cmd", None),
    "subprocess.getstatusoutput": (0, "cmd", None),
    "asyncio.create_subprocess_exec": ("all", None, "env"),
    "asyncio.create_subprocess_shell": (0, "cmd", "env"),
    "os.system": (0, "command", None),
    "os.popen": (0, "cmd", None),
    "os.execv": (1, None, None),
    "os.execvp": (1, None, None),
    "os.execve": (1, None, 2),
    "os.execvpe": (1, None, 2),
    "os.execl": ("from1", None, None),
    "os.execlp": ("from1", None, None),
    "os.execle": ("from1", None, "last"),
    "os.execlpe": ("from1", None, "last"),
    "os.spawnv": (2, None, None),
    "os.spawnvp": (2, None, None),
    "os.spawnve": (2, None, 3),
    "os.spawnvpe": (2, None, 3),
    "os.posix_spawn": (1, None, 2),
    "os.posix_spawnp": (1, None, 2),
    "pty.spawn": (0, None, None),
}


@dataclass(frozen=True)
class Invocation:
    path: str
    scope: str
    line: int
    kind: str  # launch | return | plan
    controlled: bool

    @property
    def key(self) -> str:
        return f"{self.path}::{self.scope}"


def _imports(tree: ast.AST) -> dict[str, str]:
    return _import_table(ast.walk(tree))


def _import_table(nodes: Iterable[ast.AST]) -> dict[str, str]:
    """Local name -> imported dotted name; a later import (in source order) rebinds a name."""
    table: dict[str, str] = {}
    imports = [node for node in nodes if isinstance(node, (ast.Import, ast.ImportFrom))]
    for node in sorted(imports, key=lambda node: (node.lineno, node.col_offset)):
        if isinstance(node, ast.Import):
            for alias in node.names:
                table[alias.asname or alias.name.split(".")[0]] = (
                    alias.name if alias.asname else alias.name.split(".")[0]
                )
        elif isinstance(node, ast.ImportFrom) and node.module:
            for alias in node.names:
                table[alias.asname or alias.name] = f"{node.module}.{alias.name}"
    return table


def _qualify(func: ast.AST, imports: dict[str, str]) -> str:
    if isinstance(func, ast.Name):
        return imports.get(func.id, func.id)
    if isinstance(func, ast.Attribute):
        return f"{_qualify(func.value, imports)}.{func.attr}"
    return "?"


def _launch_api(qualified: str) -> tuple[int | str, str | None, int | str | None] | None:
    parts = qualified.split(".")
    return _LAUNCH_APIS.get(qualified) or _LAUNCH_APIS.get(".".join(parts[-2:]))


def _key(node: ast.AST) -> str | None:
    """``a.b.c`` / ``a.b[0]`` for a name path a local binding can be tracked under."""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = _key(node.value)
        return f"{base}.{node.attr}" if base else None
    if isinstance(node, ast.Subscript) and isinstance(node.slice, ast.Constant):
        base = _key(node.value)
        return f"{base}[{node.slice.value!r}]" if base else None
    return None


def _callee_name(func: ast.AST) -> str | None:
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return None


# Wrapper name -> {(argv position, argv keyword)}: a function that forwards a
# parameter into a launch's argv.
Wrappers = dict[str, set[tuple[int | str, str]]]


FunctionCalls = tuple[ast.FunctionDef | ast.AsyncFunctionDef, bool, list[ast.Call]]


def _calls_by_function(tree: ast.AST) -> tuple[list[FunctionCalls], list[ast.Import | ast.ImportFrom]]:
    """Each function, whether it is a method, and the calls in its own body (not in nested functions).

    One pass over the tree; the module's imports are collected on the way.
    """
    found: list[FunctionCalls] = []
    imports: list[ast.Import | ast.ImportFrom] = []
    # (node, calls of the enclosing function or None at module level, directly inside a class)
    stack: list[tuple[ast.AST, list[ast.Call] | None, bool]] = [(tree, None, False)]
    while stack:
        node, calls, in_class = stack.pop()
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                own: list[ast.Call] = []
                found.append((child, in_class, own))
                stack.append((child, own, False))
            elif isinstance(child, ast.ClassDef):
                stack.append((child, calls, True))
            else:
                if calls is not None and isinstance(child, ast.Call):
                    calls.append(child)
                elif isinstance(child, (ast.Import, ast.ImportFrom)):
                    imports.append(child)
                stack.append((child, calls, in_class))
    return found, imports


def _forwarded_param(expr: ast.expr, params: dict[str, tuple[int | str, str]]) -> tuple[int | str, str] | None:
    if isinstance(expr, ast.Starred):
        expr = expr.value
    if isinstance(expr, ast.Call) and _callee_name(expr.func) in {"list", "tuple"} and expr.args:
        expr = expr.args[0]
    if isinstance(expr, ast.List) and len(expr.elts) == 1 and isinstance(expr.elts[0], ast.Starred):
        expr = expr.elts[0].value
    if isinstance(expr, ast.Name):
        return params.get(expr.id)
    return None


def _params(fn: ast.FunctionDef | ast.AsyncFunctionDef, method: bool) -> dict[str, tuple[int | str, str]]:
    positional = [*fn.args.posonlyargs, *fn.args.args]
    if method and positional and positional[0].arg in {"self", "cls"}:
        positional = positional[1:]
    params: dict[str, tuple[int | str, str]] = {arg.arg: (i, arg.arg) for i, arg in enumerate(positional)}
    params.update({arg.arg: (-1, arg.arg) for arg in fn.args.kwonlyargs})
    if fn.args.vararg:
        params[fn.args.vararg.arg] = ("all", fn.args.vararg.arg)
    return params


Param = tuple[int | str, str]


@dataclass(frozen=True)
class CallFact:
    """A call in a function body, reduced to what wrapper discovery needs (no parse tree)."""

    function: str
    launch: tuple[int | str, str | None] | None  # argv spec when the callee is a launch API
    callee: str | None
    args: tuple[Param | None, ...]  # the parameter each positional argument forwards
    keywords: tuple[tuple[str | None, Param | None], ...]

    def argv_params(self, position: int | str, keyword: str | None) -> list[Param | None]:
        if position == "all":
            return list(self.args)
        if position == "from1":
            return list(self.args[1:])
        assert isinstance(position, int)
        if 0 <= position < len(self.args):
            return [self.args[position]]
        return [param for name, param in self.keywords if name == keyword and keyword]


def call_facts(tree: ast.AST) -> list[CallFact]:
    """The calls in ``tree`` that forward a parameter of their function and so may make it a wrapper."""
    functions, import_nodes = _calls_by_function(tree)
    imports = _import_table(import_nodes)
    facts: list[CallFact] = []
    for fn, method, calls in functions:
        params = _params(fn, method)
        if not params:
            continue
        for call in calls:
            args = tuple(_forwarded_param(arg, params) for arg in call.args)
            keywords = tuple((kw.arg, _forwarded_param(kw.value, params)) for kw in call.keywords)
            if not any(args) and not any(param for _, param in keywords):
                continue
            api = _launch_api(_qualify(call.func, imports))
            callee = _callee_name(call.func)
            if api is not None or callee is not None:
                facts.append(CallFact(fn.name, (api[0], api[1]) if api else None, callee, args, keywords))
    return facts


def find_wrappers(facts: Iterable[CallFact]) -> Wrappers:
    """Functions (by name) that forward one of their parameters into a launch's argv, transitively."""
    queue: list[tuple[CallFact, tuple[int | str, str | None]]] = []
    callers: dict[str, list[CallFact]] = {}
    for fact in facts:
        if fact.launch is not None:
            queue.append((fact, fact.launch))
        elif fact.callee is not None:
            callers.setdefault(fact.callee, []).append(fact)
    wrappers: Wrappers = {}
    while queue:
        fact, (position, keyword) = queue.pop()
        for forwarded in fact.argv_params(position, keyword):
            if forwarded is not None and forwarded not in wrappers.get(fact.function, set()):
                wrappers.setdefault(fact.function, set()).add(forwarded)
                queue.extend((site, forwarded) for site in callers.get(fact.function, ()))
    return wrappers


@dataclass
class _Ctx:
    scope: str
    scope_names_claude: bool
    report: bool
    returns: list[tuple[Val, frozenset[int]]]  # returned value, chokepoint argvs live on that path
    traces: list[list[dict[str, Val]]] = field(default_factory=list)  # states an exception may leave from

    def quiet(self) -> _Ctx:
        return _Ctx(self.scope, self.scope_names_claude, False, [], self.traces)


# Passes over a loop body before its entry state is taken as stable.
_LOOP_PASSES = 3


class _ModuleScan:
    """Evaluate one module's functions in statement order and check every launch."""

    def __init__(self, tree: ast.Module, path: str, wrappers: Wrappers) -> None:
        self.tree = tree
        self.path = path
        self.wrappers = wrappers
        self.imports = _imports(tree)
        self.functions: dict[str, list[ast.FunctionDef | ast.AsyncFunctionDef]] = {}
        self.scopes: dict[ast.AST, tuple[str, ...]] = {}
        self._index(tree, ())
        self.module_env: dict[str, Val] = {}
        self.module_marks: frozenset[int] = frozenset()  # chokepoint argvs every path can reach
        self.return_cache: dict[ast.AST, Val] = {}
        self.in_progress: set[ast.AST] = set()
        # (scope, line, kind) -> controlled; a site seen on several passes is controlled only if it always was.
        self.found: dict[tuple[str, int, str], bool] = {}

    def _index(self, node: ast.AST, scope: tuple[str, ...]) -> None:
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self.functions.setdefault(child.name, []).append(child)
                self.scopes[child] = (*scope, child.name)
                self._index(child, (*scope, child.name))
            elif isinstance(child, ast.ClassDef):
                self._index(child, (*scope, child.name))
            else:
                self._index(child, scope)

    def run(self) -> list[Invocation]:
        # Module-level names first (without reporting), then every scope.
        self.module_env, _ = self._walk(self.tree.body, {}, _Ctx("<module>", False, False, []))
        self.module_marks = self._live(self.module_env)
        self.return_cache.clear()
        self._walk(self.tree.body, dict(self.module_env), _Ctx("<module>", False, True, []))
        for fn, scope in self.scopes.items():
            env = self._params(fn)
            claude_scope = any("claude" in name.lower() for name in scope)
            self._walk(fn.body, env, _Ctx(".".join(scope), claude_scope, True, []))
        return [Invocation(self.path, scope, line, kind, ok) for (scope, line, kind), ok in self.found.items()]

    def _params(self, fn: ast.FunctionDef | ast.AsyncFunctionDef) -> dict[str, Val]:
        args = fn.args
        every = [*args.posonlyargs, *args.args, *args.kwonlyargs, args.vararg, args.kwarg]
        return {arg.arg: _opaque(frozenset({arg.arg})) for arg in every if arg is not None}

    def _returns(self, fn: ast.FunctionDef | ast.AsyncFunctionDef) -> Val:
        if fn in self.return_cache:
            return self.return_cache[fn]
        if fn in self.in_progress:
            return _opaque(frozenset({fn.name}))
        self.in_progress.add(fn)
        ctx = _Ctx(fn.name, False, False, [])
        self._walk(fn.body, self._params(fn), ctx)
        self.in_progress.discard(fn)
        out = self._join_paths(ctx.returns) if ctx.returns else Val()
        self.return_cache[fn] = out
        return out

    # Joins -----------------------------------------------------------------------

    def _live(self, state: dict[str, Val], *vals: Val) -> frozenset[int]:
        """Chokepoint argvs that exist on a path: in its names, the module's, or ``vals``."""
        marks = self.module_marks
        for val in (*state.values(), *vals):
            marks |= _argv_marks(val)
        return marks

    def _join_paths(self, paths: list[tuple[Val, frozenset[int]]]) -> Val:
        out, live = paths[0]
        for val, other in paths[1:]:
            out, live = _join(out, val, live, other), live | other
        return out

    def _join_states(self, states: list[dict[str, Val]]) -> dict[str, Val]:
        """The state after several paths meet, each name joined conservatively (see ``_join``)."""
        if len(states) == 1:
            return dict(states[0])
        lives: list[frozenset[int] | None] = [None] * len(states)

        def live(index: int) -> frozenset[int]:
            if lives[index] is None:
                lives[index] = self._live(states[index])
            return lives[index]  # type: ignore[return-value]

        joined: dict[str, Val] = {}
        for key in set().union(*states):
            held = [(i, state.get(key, self.module_env.get(key))) for i, state in enumerate(states)]
            present = [(i, val) for i, val in held if val is not None]
            if all(val == present[0][1] for _, val in present) and len(present) == len(held):
                joined[key] = present[0][1]
                continue
            marked = any(_has_env_marks(val) for _, val in present)
            paths = [(val, live(i) if marked else frozenset()) for i, val in present]
            out = self._join_paths(paths)
            if marked:
                for i, val in held:
                    if val is None:  # unbound on this path: never that chokepoint's env
                        out = _drop_env_marks(out, live(i))
            joined[key] = out
        return joined

    # Statements ------------------------------------------------------------------

    def _walk(self, body: list[ast.stmt], env: dict[str, Val], ctx: _Ctx) -> tuple[dict[str, Val], bool]:
        for stmt in body:
            env, done = self._stmt(stmt, env, ctx)
            for trace in ctx.traces:
                trace.append(dict(env))
            if done:
                return env, True
        return env, False

    def _branches(self, bodies: list[list[ast.stmt]], env: dict[str, Val], ctx: _Ctx) -> tuple[dict[str, Val], bool]:
        live = []
        for body in bodies:
            out, done = self._walk(body, dict(env), ctx)
            if not done:
                live.append(out)
        return (self._join_states(live), False) if live else (env, True)

    def _loop(self, stmt: ast.For | ast.AsyncFor | ast.While, env: dict[str, Val], ctx: _Ctx) -> dict[str, Val]:
        """The state after a loop: the body is re-run until every iteration's entry state is stable on its marks.

        Every pass reports; a later pass starts from a joined (wider) state, so a
        site keeps the verdict of the pass that saw it least controlled.
        """

        def iterate(entry: dict[str, Val], run_ctx: _Ctx) -> dict[str, Val]:
            state = dict(entry)
            if isinstance(stmt, ast.While):
                self._eval(stmt.test, state, run_ctx)  # evaluated again before every iteration
            else:
                self._bind(stmt.target, _opaque(_names(stmt.target)), state)
            looped, _ = self._walk(stmt.body, state, run_ctx)
            return self._join_states([entry, looped])

        entry = env
        for _ in range(_LOOP_PASSES):
            following = iterate(entry, ctx)
            if _mark_signature(following) == _mark_signature(entry):
                return following
            entry = following
        return iterate(entry, ctx)

    def _try(self, stmt: ast.Try, env: dict[str, Val], ctx: _Ctx) -> tuple[dict[str, Val], bool]:
        """A handler (and ``finally``) may start from any state the body passed through."""
        body_trace: list[dict[str, Val]] = [dict(env)]
        escape_trace: list[dict[str, Val]] = []  # states an exception may carry into ``finally``
        ctx.traces.append(escape_trace)
        try:
            ctx.traces.append(body_trace)
            try:
                tried, tried_done = self._walk(stmt.body, dict(env), ctx)
            finally:
                ctx.traces.pop()
            outcomes = [] if tried_done else [self._walk(stmt.orelse, tried, ctx)]
            raised = self._join_states(body_trace)
            outcomes += [self._walk(handler.body, dict(raised), ctx) for handler in stmt.handlers]
        finally:
            ctx.traces.pop()
        live = [out for out, done in outcomes if not done]
        if not stmt.finalbody:
            return (self._join_states(live), False) if live else (env, True)
        # Launches in ``finally`` are checked from every state that can reach it;
        # the code after the statement continues from the normal exits only.
        self._walk(stmt.finalbody, self._join_states(live + body_trace + escape_trace), ctx)
        if not live:
            return env, True
        return self._walk(stmt.finalbody, self._join_states(live), ctx.quiet())

    def _stmt(self, stmt: ast.stmt, env: dict[str, Val], ctx: _Ctx) -> tuple[dict[str, Val], bool]:
        if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            return env, False
        if isinstance(stmt, ast.Assign):
            val = self._eval(stmt.value, env, ctx)
            for target in stmt.targets:
                self._bind(target, val, env)
        elif isinstance(stmt, ast.AnnAssign) and stmt.value is not None:
            self._bind(stmt.target, self._eval(stmt.value, env, ctx), env)
        elif isinstance(stmt, ast.AugAssign):
            right = self._eval(stmt.value, env, ctx)
            left = self._eval(stmt.target, env, ctx)
            self._bind(
                stmt.target, self._add(left, right) if isinstance(stmt.op, ast.Add) else _opaque(_names(stmt)), env
            )
        elif isinstance(stmt, ast.Expr):
            self._eval(stmt.value, env, ctx)
        elif isinstance(stmt, ast.Return):
            val = self._eval(stmt.value, env, ctx) if stmt.value is not None else Val()
            if ctx.report:
                self._check_return(stmt, val, ctx)
            # The caller sees only the returned value (and module names) of this path.
            ctx.returns.append((val, self._live({}, val)))
            return env, True
        elif isinstance(stmt, ast.Raise):
            if stmt.exc is not None:
                self._eval(stmt.exc, env, ctx)
            return env, True
        elif isinstance(stmt, ast.If):
            self._eval(stmt.test, env, ctx)
            return self._branches([stmt.body, stmt.orelse], env, ctx)
        elif isinstance(stmt, (ast.For, ast.AsyncFor, ast.While)):
            if not isinstance(stmt, ast.While):
                self._eval(stmt.iter, env, ctx)
            return self._walk(stmt.orelse, self._loop(stmt, env, ctx), ctx)
        elif isinstance(stmt, (ast.With, ast.AsyncWith)):
            for item in stmt.items:
                val = self._eval(item.context_expr, env, ctx)
                if item.optional_vars is not None:
                    self._bind(item.optional_vars, _opaque(_names(item.optional_vars)) if not val.alts else val, env)
            suppressing = any(
                isinstance(item.context_expr, ast.Call)
                and _qualify(item.context_expr.func, self.imports).rsplit(".", 1)[-1] == "suppress"
                for item in stmt.items
            )
            if not suppressing:
                return self._walk(stmt.body, env, ctx)
            # A suppressed exception continues after the block from any state the body passed through.
            trace = [dict(env)]
            ctx.traces.append(trace)
            try:
                self._walk(stmt.body, env, ctx)
            finally:
                ctx.traces.pop()
            return self._join_states(trace), False
        elif isinstance(stmt, (ast.Try, getattr(ast, "TryStar", ast.Try))):
            return self._try(stmt, env, ctx)
        elif isinstance(stmt, ast.Match):
            self._eval(stmt.subject, env, ctx)
            return self._branches([case.body for case in stmt.cases] + [[]], env, ctx)
        else:
            for child in ast.iter_child_nodes(stmt):
                if isinstance(child, ast.expr):
                    self._eval(child, env, ctx)
        return env, False

    def _bind(self, target: ast.AST, val: Val, env: dict[str, Val]) -> None:
        if isinstance(target, ast.Name):
            env[target.id] = val
        elif isinstance(target, (ast.Attribute, ast.Subscript)):
            if (key := _key(target)) is not None:
                env[key] = val
            base = _key(target.value) if isinstance(target, ast.Subscript) else None
            current = self._lookup(base, env) if base is not None else None
            if base is not None and current is not None and current.env_marks:
                env[base] = Val()  # a changed env may no longer carry the switch
        elif isinstance(target, (ast.Tuple, ast.List)):
            plain = not any(isinstance(elt, ast.Starred) for elt in target.elts)
            if plain and val.items is not None and len(val.items) == len(target.elts):
                for elt, item in zip(target.elts, val.items, strict=True):
                    self._bind(elt, item, env)
            else:
                for elt in target.elts:
                    inner = elt.value if isinstance(elt, ast.Starred) else elt
                    self._bind(inner, _opaque(_names(inner)), env)

    # Expressions ----------------------------------------------------------------

    def _lookup(self, key: str | None, env: dict[str, Val]) -> Val | None:
        if key is None:
            return None
        return env.get(key, self.module_env.get(key))

    def _add(self, left: Val, right: Val) -> Val:
        listish = (left.alts and left.tok is None) or (right.alts and right.tok is None)
        if listish:
            return Val(alts=_concat(_as_argv(left), _as_argv(right)))
        if left.tok is not None and right.tok is not None:
            text = (left.tok.text if left.tok.text is not None else "\0") + (
                right.tok.text if right.tok.text is not None else "\0"
            )
            return Val(tok=Tok(text=text, names=left.tok.names | right.tok.names))
        return _opaque(_as_element(left).names | _as_element(right).names)

    def _sequence(self, elts: list[ast.expr], env: dict[str, Val], ctx: _Ctx) -> Val:
        parts: list[frozenset[Alt]] = []
        items: list[Val] = []
        for elt in elts:
            if isinstance(elt, ast.Starred):
                parts.append(_as_argv(self._eval(elt.value, env, ctx)))
            else:
                val = self._eval(elt, env, ctx)
                items.append(val)
                parts.append(frozenset({((_as_element(val),), None)}))
        alts: frozenset[Alt] = frozenset({((), None)})
        for part in parts:
            alts = _concat(alts, part)
        plain = not any(isinstance(elt, ast.Starred) for elt in elts)
        return Val(alts=alts, items=tuple(items) if plain else None)

    def _eval(self, node: ast.expr | None, env: dict[str, Val], ctx: _Ctx) -> Val:
        if node is None:
            return Val()
        if isinstance(node, ast.Constant):
            return Val(tok=Tok(text=node.value)) if isinstance(node.value, str) else Val()
        if isinstance(node, ast.JoinedStr):
            text, names = "", set()
            for part in node.values:
                if isinstance(part, ast.Constant):
                    text += str(part.value)
                else:
                    self._eval(part, env, ctx)
                    text += "\0"
                    names |= _names(part)
            return Val(tok=Tok(text=text, names=frozenset(names)))
        if isinstance(node, ast.FormattedValue):
            return self._eval(node.value, env, ctx)
        if isinstance(node, ast.Name):
            found = self._lookup(node.id, env)
            return found if found is not None else _opaque(frozenset({node.id}))
        if isinstance(node, ast.Attribute):
            found = self._lookup(_key(node), env)
            if found is None:
                self._eval(node.value, env, ctx)
            return found if found is not None else _opaque(_names(node))
        if isinstance(node, (ast.List, ast.Tuple)):
            return self._sequence(node.elts, env, ctx)
        if isinstance(node, ast.BinOp):
            left, right = self._eval(node.left, env, ctx), self._eval(node.right, env, ctx)
            return self._add(left, right) if isinstance(node.op, ast.Add) else _opaque(_names(node))
        if isinstance(node, (ast.IfExp, ast.BoolOp)):
            if isinstance(node, ast.IfExp):
                self._eval(node.test, env, ctx)
                vals = [self._eval(node.body, env, ctx), self._eval(node.orelse, env, ctx)]
            else:
                vals = [self._eval(value, env, ctx) for value in node.values]
            # Every operand shares this path, so every argv on it is live for each.
            live = self._live(env, *vals) if any(map(_has_env_marks, vals)) else frozenset()
            return self._join_paths([(val, live) for val in vals])
        if isinstance(node, (ast.Starred, ast.Await)):
            return self._eval(node.value, env, ctx)
        if isinstance(node, ast.NamedExpr):
            val = self._eval(node.value, env, ctx)
            self._bind(node.target, val, env)
            return val
        if isinstance(node, ast.Subscript):
            base = self._eval(node.value, env, ctx)
            self._eval(node.slice, env, ctx)
            key = node.slice
            if (
                isinstance(key, ast.Constant)
                and isinstance(key.value, int)
                and base.items is not None
                and -len(base.items) <= key.value < len(base.items)
            ):
                return base.items[key.value]
            found = self._lookup(_key(node), env)
            if found is not None:
                return found
            if isinstance(key, ast.Slice) and base.alts:
                return Val(alts=frozenset((toks, None) for toks, _ in base.alts))
            return _opaque(_names(node))
        if isinstance(node, ast.Call):
            return self._call(node, env, ctx)
        if isinstance(node, (ast.Lambda, ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)):
            return _opaque(_names(node))
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.expr):
                self._eval(child, env, ctx)
        return _opaque(_names(node))

    def _mutate(self, node: ast.Call, env: dict[str, Val], ctx: _Ctx) -> Val | None:
        func = node.func
        if not isinstance(func, ast.Attribute) or func.attr not in {"append", "extend", "insert"}:
            return None
        key = _key(func.value)
        current = self._lookup(key, env)
        if key is None or current is None or not current.alts or current.tok is not None:
            return None
        args = [self._eval(arg, env, ctx) for arg in node.args]
        if func.attr == "append" and len(args) == 1:
            added = frozenset({((_as_element(args[0]),), None)})
            env[key] = Val(alts=_concat(current.alts, added))
        elif func.attr == "extend" and len(args) == 1:
            env[key] = Val(alts=_concat(current.alts, _as_argv(args[0])))
        elif func.attr == "insert" and len(args) == 2:
            at = node.args[0].value if isinstance(node.args[0], ast.Constant) else None
            element = _as_element(args[1])
            alts = set()
            for toks, _ in current.alts:
                position = at if isinstance(at, int) else len(toks)
                alts.add(((*toks[:position], element, *toks[position:]), None))
            env[key] = Val(alts=_cap(alts))
        else:
            return None
        return Val()

    def _call(self, node: ast.Call, env: dict[str, Val], ctx: _Ctx) -> Val:
        mutated = self._mutate(node, env, ctx)
        if mutated is not None:
            return mutated
        if isinstance(node.func, ast.Attribute) and node.func.attr in {"pop", "update", "clear", "popitem"}:
            key = _key(node.func.value)
            current = self._lookup(key, env)
            if key is not None and current is not None and current.env_marks:
                env[key] = Val()  # a changed env may no longer carry the switch
        name = _callee_name(node.func)
        qualified = _qualify(node.func, self.imports)
        receiver = self._eval(node.func.value, env, ctx) if isinstance(node.func, ast.Attribute) else Val()
        args = [self._eval(arg, env, ctx) for arg in node.args]
        kwargs = {kw.arg: self._eval(kw.value, env, ctx) for kw in node.keywords}

        if name == CHOKEPOINT:
            mark = id(node)
            argv = args[0] if args else kwargs.get("argv", Val())
            out = Val(alts=frozenset((toks, mark) for toks, _ in _as_argv(argv)))
            return Val(items=(out, Val(env_marks=frozenset({mark}))))

        api = _launch_api(qualified)
        specs: list[tuple[int | str, str | None, int | str | None]] = []
        if api is not None:
            specs.append(api)
        else:
            specs.extend((position, keyword, "env") for position, keyword in self.wrappers.get(name or "", ()))
        if specs:
            if ctx.report:
                for spec in specs:
                    self._launch(node, spec, args, kwargs, ctx)
            return _opaque(frozenset({name or "?"}))
        if name == "InvocationPlan":
            if ctx.report:
                cmd = kwargs.get("cmd", args[0] if args else Val())
                kinds = [_alt_kind(toks, ctx.scope_names_claude) for toks, _ in cmd.alts]
                if any(kinds):
                    self._record(ctx, node, "plan", False)
            return _opaque(frozenset({name}))

        if qualified in {"shlex.split"} and args:
            tok = args[0].tok
            if tok is not None and tok.text is not None:
                try:
                    parts = shlex.split(tok.text)
                except ValueError:
                    parts = tok.text.split()
                return Val(
                    alts=frozenset(
                        {(tuple(Tok(text=p, names=tok.names if "\0" in p else frozenset()) for p in parts), None)}
                    )
                )
            return _opaque(_names(node))
        if name in {"str", "fspath", "Path", "PurePath", "which", "expanduser", "resolve"}:
            source = args[0] if args else receiver
            return Val(tok=_as_element(source)) if source.tok is not None or source.alts else _opaque(_names(node))
        if name in {"list", "tuple"} and args:
            return Val(alts=_as_argv(args[0]), items=args[0].items)
        if name == "copy" and isinstance(node.func, ast.Attribute):
            return receiver
        if name == "join" and isinstance(node.func, ast.Attribute) and args:
            separator = receiver.tok.text if receiver.tok is not None else None
            if separator is not None and args[0].alts:
                toks = max(args[0].alts, key=lambda alt: any(t.text in PRINT_FLAGS for t in alt[0]))[0]
                text = separator.join(tok.text if tok.text is not None else "\0" for tok in toks)
                return Val(tok=Tok(text=text, names=frozenset(n for tok in toks for n in tok.names)))
        if qualified == "shlex.join" and args and args[0].alts:
            toks = max(args[0].alts, key=lambda alt: any(t.text in PRINT_FLAGS for t in alt[0]))[0]
            return Val(tok=Tok(text=" ".join(tok.text if tok.text is not None else "\0" for tok in toks)))
        if name in self.functions and (
            isinstance(node.func, ast.Name)
            or (isinstance(node.func.value, ast.Name) and node.func.value.id in {"self", "cls"})
        ):
            returned = [self._returns(fn) for fn in self.functions[name]]
            return self._join_paths([(val, self._live({}, val)) for val in returned])
        return _opaque(_names(node.func))

    def _launch(
        self,
        node: ast.Call,
        spec: tuple[int | str, str | None, int | str | None],
        args: list[Val],
        kwargs: dict[str | None, Val],
        ctx: _Ctx,
    ) -> None:
        position, keyword, env_spec = spec
        if position in {"all", "from1"}:
            start = 0 if position == "all" else 1
            argv = Val(alts=frozenset({((), None)}))
            for arg_node, val in zip(node.args[start:], args[start:], strict=True):
                part = _as_argv(val) if isinstance(arg_node, ast.Starred) else frozenset({((_as_element(val),), None)})
                argv = Val(alts=_concat(argv.alts, part))
        elif isinstance(position, int) and 0 <= position < len(args):
            argv = args[position]
        else:
            argv = kwargs.get(keyword, Val()) if keyword else Val()
        if isinstance(env_spec, int):
            env = args[env_spec] if env_spec < len(args) else kwargs.get("env", Val())
        elif env_spec == "last":
            env = args[-1] if args else Val()
        elif env_spec is not None:
            env = kwargs.get(env_spec, Val())
        else:
            env = Val()
        self._check(node, [(argv, env)], ctx, "launch")

    def _check_return(self, node: ast.AST, val: Val, ctx: _Ctx) -> None:
        """A returned argv must be the chokepoint's, returned with the chokepoint's env."""
        pairs = [(val, Val())]
        if val.items is not None and len(val.items) == 2:
            pairs.append((val.items[0], val.items[1]))
        elif val.items:
            pairs.extend((item, Val()) for item in val.items)
        self._check(node, pairs, ctx, "return")

    def _check(self, node: ast.AST, pairs: list[tuple[Val, Val]], ctx: _Ctx, kind: str) -> None:
        for argv, env in pairs:
            direct = []
            shell = False
            for toks, mark in argv.alts:
                alt = _alt_kind(toks, ctx.scope_names_claude)
                if alt == "direct":
                    direct.append(mark)
                elif alt == "shell":
                    shell = True
            if argv.tok is not None and argv.tok.text is not None and shell_claude_print_lines(argv.tok.text):
                shell = True
            if not direct and not shell:
                continue
            controlled = not shell and all(mark is not None and mark in env.env_marks for mark in direct)
            self._record(ctx, node, kind, controlled)

    def _record(self, ctx: _Ctx, node: ast.AST, kind: str, controlled: bool) -> None:
        key = (ctx.scope, getattr(node, "lineno", 0), kind)
        self.found[key] = self.found.get(key, True) and controlled


def scan_source(source: str, path: str, wrappers: Wrappers | None = None) -> list[Invocation]:
    """Return every Claude print-mode launch, builder return and plan in ``source``."""
    tree = ast.parse(source, filename=path)
    if wrappers is None:
        wrappers = find_wrappers(call_facts(tree))
    return _ModuleScan(tree, path, wrappers).run()


def _python_sources() -> Iterator[tuple[str, str]]:
    for path in sorted(SCRIPTS.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        yield path.relative_to(REPO_ROOT).as_posix(), path.read_text(encoding="utf-8")


def scan_repository(sources: Iterable[tuple[str, str]]) -> list[Invocation]:
    """Scan every module that names Claude; wrappers come from those and every module that launches.

    Each parse tree is dropped once its facts are extracted, so the scan holds
    one tree at a time (hundreds of modules launch processes).
    """
    facts: list[CallFact] = []
    claude: dict[str, str] = {}
    for rel, source in sources:
        names_claude = "claude" in source.lower() and _PRINT_TEXT.search(source) is not None
        if names_claude:
            claude[rel] = source
        if names_claude or _LAUNCH_TEXT.search(source):
            facts.extend(call_facts(ast.parse(source, filename=rel)))
    wrappers = find_wrappers(facts)
    found: list[Invocation] = []
    for rel, source in claude.items():
        found.extend(_ModuleScan(ast.parse(source, filename=rel), rel, wrappers).run())
    return found


_PRINT_TEXT = re.compile(r"-p\b|--print\b")
_LAUNCH_TEXT = re.compile(
    r"\b(subprocess|create_subprocess_\w+|os\.(system|popen|exec\w*|spawn\w*|posix_spawnp?)|pty\.spawn)\b"
)


@pytest.fixture(scope="module")
def repo_invocations() -> list[Invocation]:
    return scan_repository(_python_sources())


def _harness_table() -> set[str]:
    """Keys of ``_CLAUDE_CODE_HARNESSES`` in NO_BACKGROUND_TESTS (adapter files it drives)."""
    tree = ast.parse(NO_BACKGROUND_TESTS.read_text(encoding="utf-8"))
    for node in tree.body:
        targets = node.targets if isinstance(node, ast.Assign) else []
        if any(isinstance(t, ast.Name) and t.id == "_CLAUDE_CODE_HARNESSES" for t in targets):
            assert isinstance(node.value, ast.Dict)
            return {key.value for key in node.value.keys if isinstance(key, ast.Constant)}
    raise AssertionError("_CLAUDE_CODE_HARNESSES not found")


# --- Repository invariants -------------------------------------------------------------


@pytest.mark.repo_wide
def test_every_headless_claude_launch_goes_through_the_chokepoint(repo_invocations: list[Invocation]) -> None:
    """No Claude print-mode argv under scripts/ is launched or returned without the chokepoint's pair."""
    uncontrolled = sorted(
        f"{inv.key}:{inv.line} ({inv.kind})" for inv in repo_invocations if inv.kind != "plan" and not inv.controlled
    )
    assert not uncontrolled, (
        f"headless claude -p not started with the argv and env from {CHOKEPOINT}() in {ADAPTER}: {uncontrolled}"
    )


@pytest.mark.repo_wide
@pytest.mark.parametrize("key", KNOWN_LAUNCHES)
def test_scanner_sees_each_known_launch_controlled(repo_invocations: list[Invocation], key: str) -> None:
    """The tripwire is wired: it detects each direct launcher, and each is controlled."""
    matches = [inv for inv in repo_invocations if inv.key == key and inv.kind != "plan"]
    assert matches, f"scanner no longer detects {key}"
    assert all(inv.controlled for inv in matches)


@pytest.mark.repo_wide
def test_claude_plans_are_built_only_by_runner_tested_adapters(repo_invocations: list[Invocation]) -> None:
    """A Claude print-mode InvocationPlan is built only by an adapter the runner tests drive."""
    plans = {inv.path for inv in repo_invocations if inv.kind == "plan"}
    assert ADAPTER in plans, "scanner no longer detects the Claude adapter's plan"
    covered = {f"scripts/agent_runtime/{key}" for key in _harness_table()}
    assert plans <= covered, f"Claude plan built outside the runner-tested adapters: {sorted(plans - covered)}"


def _shell_launcher_errors(launching: set[str], mapping: dict[str, str], tests_source: str) -> list[str]:
    errors = [f"unmapped shell launcher: {path}" for path in sorted(launching - set(mapping))]
    errors += [f"mapped script no longer launches claude -p: {path}" for path in sorted(set(mapping) - launching)]
    functions = {
        node.name: ast.get_source_segment(tests_source, node) or ""
        for node in ast.parse(tests_source).body
        if isinstance(node, ast.FunctionDef)
    }
    for script, test_name in mapping.items():
        if Path(script).name not in functions.get(test_name, ""):
            errors.append(f"{test_name} does not launch {Path(script).name}")
    return errors


@pytest.mark.repo_wide
def test_shell_launchers_are_proven_by_a_runner_test() -> None:
    """Each shell script running claude -p is named by a test that launches it through the real runner."""
    launching = {
        path.relative_to(REPO_ROOT).as_posix()
        for path in SCRIPTS.rglob("*.sh")
        if shell_claude_print_lines(path.read_text(encoding="utf-8"))
    }
    errors = _shell_launcher_errors(launching, SHELL_LAUNCHERS, NO_BACKGROUND_TESTS.read_text(encoding="utf-8"))
    assert not errors


@pytest.mark.repo_wide
def test_controls_have_a_single_source() -> None:
    """Only the adapter defines the controls or the chokepoint; callers import them from it."""
    owned = {"HEADLESS_BACKGROUND_ENV", "HEADLESS_BACKGROUND_TOOL_DENIES", CHOKEPOINT}
    for rel, source in _python_sources():
        if rel == ADAPTER or not any(name in source for name in owned):
            continue
        tree = ast.parse(source, filename=rel)
        for node in ast.walk(tree):
            if isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
                targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                bound = {name for target in targets for name in _names(target)}
                assert not bound & owned, f"{rel}:{node.lineno} redefines a #9690 control"
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                assert node.name != CHOKEPOINT, f"{rel}:{node.lineno} redefines the chokepoint"
            if isinstance(node, ast.ImportFrom) and {alias.name for alias in node.names} & owned:
                assert (node.module or "").endswith("adapters.claude") or (node.level and node.module == "claude"), (
                    f"{rel}:{node.lineno} imports a #9690 control from {node.module!r}"
                )


# --- The chokepoint ------------------------------------------------------------------


def test_chokepoint_adds_denies_before_the_end_of_options_marker() -> None:
    argv, env = headless_claude_launch(["claude", "-p", "--model", "m", "--", "prompt"], {"PATH": "/bin"})
    assert argv == ["claude", "-p", "--model", "m", "--disallowedTools", DENIES, "--", "prompt"]
    assert env == {"PATH": "/bin", SWITCH: "1"}


def test_chokepoint_appends_denies_without_a_marker_and_overrides_the_switch() -> None:
    argv, env = headless_claude_launch(("claude", "-p", "prompt"), {SWITCH: "0"})
    assert argv == ["claude", "-p", "prompt", "--disallowedTools", DENIES]
    assert env == {SWITCH: "1"}


@pytest.mark.parametrize("flag", ["--disallowedTools", "--disallowed-tools"])
def test_chokepoint_merges_into_a_stricter_existing_list(flag: str) -> None:
    base = ["claude", "-p", flag, "Edit,Bash(git push *),Monitor", "--", "a --disallowedTools b"]
    argv, _ = headless_claude_launch(base, {})
    assert argv == [
        "claude",
        "-p",
        flag,
        "Edit,Bash(git push *),Monitor,ScheduleWakeup,CronCreate,Workflow",
        "--",
        "a --disallowedTools b",
    ]


def test_chokepoint_merges_the_equals_form_and_leaves_its_inputs_unchanged() -> None:
    base = ["claude", "-p", "--disallowedTools=Edit"]
    env = {"A": "1"}
    argv, out = headless_claude_launch(base, env)
    assert argv == ["claude", "-p", f"--disallowedTools=Edit,{DENIES}"]
    assert base == ["claude", "-p", "--disallowedTools=Edit"] and env == {"A": "1"}
    assert out == {"A": "1", SWITCH: "1"}


# --- Behaviour: each direct launcher hands the child both controls ------------------------


@pytest.fixture
def ambient_switch_off(monkeypatch: pytest.MonkeyPatch) -> None:
    """The test process's own env has background tasks *enabled*.

    A parent that already carries the switch (a Claude session running the
    suite) would otherwise let a caller that forwards ``os.environ`` instead of
    the chokepoint's env pass.
    """
    monkeypatch.setenv(SWITCH, "0")


def _assert_child_controlled(argv: list[str], env: dict[str, str]) -> None:
    flag = argv.index("--disallowedTools")
    assert set(HEADLESS_BACKGROUND_TOOL_DENIES) <= set(argv[flag + 1].split(","))
    if "--" in argv:
        assert flag < argv.index("--")
    assert env[SWITCH] == "1"


@pytest.mark.usefixtures("ambient_switch_off")
def test_batch_rebuild_child_is_controlled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.syspath_prepend(str(SCRIPTS))
    from batch import batch_dispatcher_helpers as helpers

    seen: dict[str, Any] = {}

    def fake_run(cmd: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        seen.update(argv=cmd, env=kwargs["env"])
        return subprocess.CompletedProcess(cmd, 0, stdout="done", stderr="")

    monkeypatch.setattr(helpers.subprocess, "run", fake_run)
    monkeypatch.setattr(helpers, "supports_exclude_dynamic_system_prompt_sections", lambda _bin: False)
    monkeypatch.setenv("LU_PROBE", "kept")

    assert helpers.dispatch_claude_fix("a1", "greetings", 1)["success"] is True
    _assert_child_controlled(seen["argv"], seen["env"])
    assert seen["env"]["LU_PROBE"] == "kept"
    assert seen["argv"][seen["argv"].index("--permission-mode") + 1] == "bypassPermissions"


@pytest.mark.usefixtures("ambient_switch_off")
def test_pipeline_phase_child_is_controlled(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    from scripts.pipeline import dispatch

    seen: dict[str, Any] = {}

    def fake_run(cmd: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        seen.update(argv=cmd, env=kwargs["env"], input=kwargs["input"])
        return subprocess.CompletedProcess(cmd, 0, stdout="===CONTENT_START===\nx\n===CONTENT_END===", stderr="")

    monkeypatch.setattr(dispatch.subprocess, "run", fake_run)
    monkeypatch.setattr(dispatch, "supports_exclude_dynamic_system_prompt_sections", lambda _bin: False)
    monkeypatch.setenv("CLAUDECODE", "1")
    prompt_file = tmp_path / "phase.md"
    prompt_file.write_text("write the content", encoding="utf-8")

    ok, _ = dispatch.dispatch_claude_phase(prompt_file, "B content")

    assert ok
    _assert_child_controlled(seen["argv"], seen["env"])
    assert "CLAUDECODE" not in seen["env"]
    assert seen["input"] == "write the content"


@pytest.mark.usefixtures("ambient_switch_off")
@pytest.mark.parametrize("module_name", ["code_review_benchmark", "judge_calibration_matrix"])
def test_native_claude_benchmark_child_is_controlled(monkeypatch: pytest.MonkeyPatch, module_name: str) -> None:
    import importlib

    module = importlib.import_module(f"scripts.audit.{module_name}")
    seen: dict[str, Any] = {}

    def fake_run(cmd: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        seen.update(argv=cmd, env=kwargs["env"])
        return subprocess.CompletedProcess(cmd, 0, stdout="verdict", stderr="")

    monkeypatch.setattr(module.subprocess, "run", fake_run)
    cell = module.Cell("anthropic", "claude-opus-5-5", "native_cli", "high", "no_mcp")

    call = module.run_native_cli(cell, "prompt")

    assert call.ok
    _assert_child_controlled(seen["argv"], seen["env"])
    assert seen["argv"][-2:] == ["--", "prompt"]


@pytest.mark.usefixtures("ambient_switch_off")
def test_openai_proxy_claude_child_is_controlled(monkeypatch: pytest.MonkeyPatch) -> None:
    from scripts.ai_agent_bridge import openai_proxy as proxy

    seen: dict[str, Any] = {}

    def fake_run(cmd: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        seen.update(argv=cmd, env=kwargs["env"], input=kwargs["input"])
        return subprocess.CompletedProcess(cmd, 0, stdout="reply", stderr="")

    monkeypatch.setattr(proxy.subprocess, "run", fake_run)

    response = proxy._claude_backend("claude-opus-5-5", [proxy.Message(role="user", content="hello")])

    assert response.content == "reply"
    _assert_child_controlled(seen["argv"], seen["env"])
    assert "hello" in seen["input"]


@pytest.mark.usefixtures("ambient_switch_off")
def test_zno_eval_claude_child_is_controlled(monkeypatch: pytest.MonkeyPatch) -> None:
    from scripts.eval.zno_nmt import adapters

    seen: dict[str, Any] = {}
    stdout = "\n".join(
        [
            json.dumps({"type": "system", "subtype": "init", "model": "local-test-model", "tools": []}),
            json.dumps({"type": "result", "result": json.dumps({"responses": {"opaque-1": "A"}})}),
        ]
    )

    class FakePopen:
        def __init__(self, argv: list[str], **kwargs: Any) -> None:
            seen.update(argv=argv, env=kwargs["env"])
            self.pid = 0
            self.returncode = 0

        def communicate(self, prompt: str | None = None, timeout: float | None = None) -> tuple[str, str]:
            seen["input"] = prompt
            return stdout, ""

    monkeypatch.setattr(adapters, "_claude_capabilities", lambda *_args, **_kwargs: ("claude-fixture", "2.1.fixture"))
    monkeypatch.setattr(adapters.subprocess, "Popen", FakePopen)
    config = {
        "schema": "zno-nmt.config.v1",
        "adapter": "claude",
        "model": "local-test-model",
        "effort": None,
        "timeout_seconds": 15,
        "max_output_tokens": 100,
        "max_tool_calls": 2,
        "repeats": 1,
        "tools": ["verify_word"],
        "corpus_id": "fixture-corpus",
        "claude_bin": "claude-fixture",
    }
    packet = {
        "schema": "zno-nmt.questions.v1",
        "packet_sha256": "a" * 64,
        "items": [
            {"id": "opaque-1", "kind": "single", "question": "Q", "options": [{"id": "A", "text": "A"}], "rows": []}
        ],
    }

    result = adapters.run_claude(packet, config, "closed-book", sources_url=None, prompt="exam")

    assert result["responses"] == {"opaque-1": "A"}
    _assert_child_controlled(seen["argv"], seen["env"])
    assert seen["argv"][seen["argv"].index("--tools") + 1] == ""
    assert seen["env"]["CLAUDE_CODE_MAX_OUTPUT_TOKENS"] == "100"
    assert seen["input"] == "exam"


@pytest.mark.usefixtures("ambient_switch_off")
def test_isolated_claude_review_launch_is_controlled(tmp_path: Path) -> None:
    from scripts.review.isolation import build_claude_review_argv

    binary = tmp_path / "claude"
    binary.write_text("#!/bin/sh\n", encoding="utf-8")

    argv, env = build_claude_review_argv(
        binary, prompt="review", json_schema={"type": "object"}, env={"HOME": "/h", SWITCH: "0"}
    )

    _assert_child_controlled(argv, env)
    assert argv[argv.index("--tools") + 1] == "Read,Grep,Glob"
    assert argv[-2:] == ["--", "review"]
    assert env["HOME"] == "/h"


# --- The scanner: discovery and invocation-specific control ---------------------------------

_IMPORT = (
    "import os, shlex, subprocess, asyncio\nfrom scripts.agent_runtime.adapters.claude import headless_claude_launch\n"
)


def _scan(body: str) -> list[Invocation]:
    return scan_source(_IMPORT + textwrap.dedent(body), "scripts/fixture.py")


# Each launches claude -p without the chokepoint; several escaped the round-1 scanner.
_UNCONTROLLED = {
    "literal": 'def run(p):\n    subprocess.run(["claude", "-p", p])\n',
    "absolute-path": 'def run(p):\n    subprocess.run(["/usr/local/bin/claude", "--print", "--", p])\n',
    "named-binary": "def run(p):\n    subprocess.run([CLAUDE_BIN, '-p', p], env=os.environ)\n",
    "spread-command": 'def run(p):\n    subprocess.run([*CLAUDE_CMD, "--print", "--bare"], input=p)\n',
    "shlex-split": 'def run(prompt):\n    subprocess.run(shlex.split("claude --print") + [prompt])\n',
    "shell-string": 'def run():\n    subprocess.run("claude -p hello", shell=True)\n',
    "shell-fstring": 'def run(p):\n    subprocess.run(f"cd /tmp && claude --model m -p {p}", shell=True)\n',
    "os-system": 'def run():\n    os.system("env A=1 claude -p hi")\n',
    "bash-c": 'def run():\n    subprocess.run(["bash", "-c", "claude -p hi"])\n',
    "exe-variable": 'def run(prompt):\n    exe = "claude"\n    subprocess.run([exe, "-p", prompt])\n',
    "flag-variable": 'def run(prompt):\n    flag = "-p"\n    subprocess.run(["claude", flag, prompt])\n',
    "args-concat": 'def run(prompt):\n    args = ["-p", prompt]\n    subprocess.run(["claude"] + args)\n',
    "module-constant": 'FLAGS = ("--print",)\ndef run(p):\n    subprocess.run(["claude", *FLAGS, p])\n',
    "options-first": 'def run(p):\n    subprocess.run(["claude", "--model", "m", "-p", p])\n',
    "wrapped": 'def run(p):\n    subprocess.run(["timeout", "60", "claude", "-p", p])\n',
    "append": 'def build_claude_argv(binary):\n    cmd = [str(binary)]\n    cmd.append("-p")\n    return cmd\n',
    "popen-kw": 'def run(p):\n    subprocess.Popen(args=["claude", "-p", p])\n',
    "asyncio": 'async def run(p):\n    await asyncio.create_subprocess_exec("claude", "-p", p)\n',
    "execvp": 'def run(p):\n    os.execvp("claude", ["claude", "-p", p])\n',
    "local-wrapper": (
        "def _go(argv, env=None):\n    return subprocess.run(argv, env=env)\n"
        'def run(p):\n    return _go(["claude", "-p", p])\n'
    ),
    # Round-1 false "controlled" forms.
    "constants-unused": (
        "from scripts.agent_runtime.adapters.claude import HEADLESS_BACKGROUND_ENV, HEADLESS_BACKGROUND_TOOL_DENIES\n"
        "def run(p):\n    unused = (HEADLESS_BACKGROUND_ENV, HEADLESS_BACKGROUND_TOOL_DENIES)\n"
        '    subprocess.run(["claude", "-p", p])\n'
    ),
    "chokepoint-discarded": (
        'def run(p):\n    cmd = ["claude", "-p", p]\n    headless_claude_launch(cmd, os.environ)\n'
        "    subprocess.run(cmd)\n"
    ),
    "env-replaced": (
        'def run(p):\n    cmd, env = headless_claude_launch(["claude", "-p", p], os.environ)\n'
        "    subprocess.run(cmd, env=os.environ)\n"
    ),
    "env-missing": 'def run(p):\n    cmd, env = headless_claude_launch(["claude", "-p", p], os.environ)\n    subprocess.run(cmd)\n',
    "argv-mutated-after": (
        'def run(p):\n    cmd, env = headless_claude_launch(["claude", "-p"], os.environ)\n'
        '    cmd.append("--disallowedTools=")\n    subprocess.run(cmd, env=env)\n'
    ),
    "env-from-another-call": (
        'def run(p):\n    cmd, _ = headless_claude_launch(["claude", "-p", p], {})\n'
        '    _, env = headless_claude_launch(["claude", "-p"], {})\n    subprocess.run(cmd, env=env)\n'
    ),
    "env-changed-after": (
        'def run(p):\n    cmd, env = headless_claude_launch(["claude", "-p", p], os.environ)\n'
        '    env.pop("CLAUDE_CODE_DISABLE_BACKGROUND_TASKS")\n    subprocess.run(cmd, env=env)\n'
    ),
    "builder-returns-argv-only": (
        'def build(p):\n    return headless_claude_launch(["claude", "-p", p], os.environ)[0]\n'
    ),
    "one-branch-only": (
        'def run(p, claude):\n    cmd, env = ["claude", "-p", p], None\n'
        "    if claude:\n        cmd, env = headless_claude_launch(cmd, os.environ)\n"
        "    subprocess.run(cmd, env=env)\n"
    ),
    # Round-2 false "controlled" forms: a join must not keep a control that one path lost.
    "env-replaced-on-a-branch": (
        'def run(p, discard_env):\n    cmd, env = headless_claude_launch(["claude", "-p", p], os.environ)\n'
        "    if discard_env:\n        env = os.environ\n    subprocess.run(cmd, env=env)\n"
    ),
    "switch-removed-on-a-branch": (
        'def run(p, raw):\n    cmd, env = headless_claude_launch(["claude", "-p", p], os.environ)\n'
        '    if raw:\n        env.pop("CLAUDE_CODE_DISABLE_BACKGROUND_TASKS")\n    subprocess.run(cmd, env=env)\n'
    ),
    "env-chosen-by-conditional-expression": (
        'def run(p, keep):\n    cmd, env = headless_claude_launch(["claude", "-p", p], os.environ)\n'
        "    subprocess.run(cmd, env=env if keep else os.environ)\n"
    ),
    "env-chosen-by-or": (
        'def run(p, override):\n    cmd, env = headless_claude_launch(["claude", "-p", p], os.environ)\n'
        "    subprocess.run(cmd, env=override or env)\n"
    ),
    "argv-replaced-on-a-branch": (
        'def run(p, plain):\n    cmd, env = headless_claude_launch(["claude", "-p", p], os.environ)\n'
        '    if plain:\n        cmd = ["claude", "-p", p]\n    subprocess.run(cmd, env=env)\n'
    ),
    "argv-mutated-on-a-branch": (
        'def run(p, open_tools):\n    cmd, env = headless_claude_launch(["claude", "-p", p], os.environ)\n'
        '    if open_tools:\n        cmd.append("--disallowedTools=")\n    subprocess.run(cmd, env=env)\n'
    ),
    "argv-truncated-on-a-branch": (
        'def run(p, short):\n    cmd, env = headless_claude_launch(["claude", "-p", p], os.environ)\n'
        "    if short:\n        cmd = cmd[:3]\n    subprocess.run(cmd, env=env)\n"
    ),
    "loop-reassigns-after-the-launch": (
        'def run(p):\n    cmd, env = headless_claude_launch(["claude", "-p", p], os.environ)\n'
        "    for _attempt in range(3):\n        subprocess.run(cmd, env=env)\n        env = dict(os.environ)\n"
    ),
    "loop-may-reassign-before-the-launch": (
        'def run(p, keys):\n    cmd, env = headless_claude_launch(["claude", "-p", p], os.environ)\n'
        '    for key in keys:\n        if key == "raw":\n            env = os.environ\n'
        "    subprocess.run(cmd, env=env)\n"
    ),
    "while-loop-reassigns": (
        'def run(p):\n    cmd, env = headless_claude_launch(["claude", "-p", p], os.environ)\n'
        "    while subprocess.run(cmd, env=env).returncode:\n        env = os.environ\n"
    ),
    "handler-sees-a-replaced-env": (
        'def run(p):\n    cmd, env = headless_claude_launch(["claude", "-p", p], os.environ)\n'
        "    saved = env\n    try:\n        env = os.environ\n        prepare()\n        env = saved\n"
        "    except OSError:\n        subprocess.run(cmd, env=env)\n"
    ),
    "finally-sees-a-replaced-env": (
        'def run(p):\n    cmd, env = headless_claude_launch(["claude", "-p", p], os.environ)\n'
        "    saved = env\n    try:\n        env = os.environ\n        prepare()\n        env = saved\n"
        "    finally:\n        subprocess.run(cmd, env=env)\n"
    ),
    "suppress-skips-the-restore": (
        "from contextlib import suppress\n"
        'def run(p):\n    cmd, env = headless_claude_launch(["claude", "-p", p], os.environ)\n'
        "    saved = env\n    with suppress(OSError):\n        env = os.environ\n        prepare()\n        env = saved\n"
        "    subprocess.run(cmd, env=env)\n"
    ),
    "builder-may-return-another-env": (
        'def build(p, raw):\n    cmd, env = headless_claude_launch(["claude", "-p", p], os.environ)\n'
        "    if raw:\n        env = os.environ\n    return cmd, env\n"
    ),
}


@pytest.mark.parametrize("body", list(_UNCONTROLLED.values()), ids=list(_UNCONTROLLED))
def test_scanner_flags_uncontrolled_launch(body: str) -> None:
    found = _scan(body)
    assert found, "launch not discovered"
    assert not all(inv.controlled for inv in found)


def test_scanner_flags_only_the_unprotected_invocation_in_a_function() -> None:
    found = _scan(
        """
        def run(p):
            cmd, env = headless_claude_launch(["claude", "-p", p], os.environ)
            subprocess.run(cmd, env=env)
            subprocess.run(["claude", "-p", p])
        """
    )
    assert [(inv.line, inv.controlled) for inv in found] == [(6, True), (7, False)]


def test_scanner_flags_the_unprotected_caller_of_a_shared_builder() -> None:
    found = _scan(
        """
        def build(p):
            return ["claude", "-p", p]

        def protected(p):
            cmd, env = headless_claude_launch(build(p), os.environ)
            return subprocess.run(cmd, env=env)

        def unprotected(p):
            return subprocess.run(build(p))
        """
    )
    status = {(inv.scope, inv.kind): inv.controlled for inv in found}
    assert status == {("build", "return"): False, ("protected", "launch"): True, ("unprotected", "launch"): False}


def test_scanner_flags_the_caller_of_a_builder_that_may_return_another_env() -> None:
    """Joining a builder's returns keeps the env controlled only if every return pairs it with the argv."""
    found = _scan(
        """
        def build(p, raw):
            cmd, env = headless_claude_launch(["claude", "-p", p], os.environ)
            if raw:
                return cmd, os.environ
            return cmd, env

        def run(p, raw):
            cmd, env = build(p, raw)
            return subprocess.run(cmd, env=env)
        """
    )
    status = {(inv.scope, inv.line): inv.controlled for inv in found}
    assert status == {("build", 7): False, ("build", 8): True, ("run", 12): False}


def test_scanner_accepts_launches_that_use_the_chokepoint_pair() -> None:
    found = _scan(
        """
        def direct(p):
            cmd, env = headless_claude_launch(["claude", "-p", p], os.environ)
            return subprocess.run(cmd, env=env)

        def builder(cell, p):
            if cell == "claude":
                cmd = [CLAUDE_BIN, "-p", "--", p]
                return headless_claude_launch(cmd, os.environ)
            return ["codex", "exec", p], None

        def caller(cell, p):
            cmd, env = builder(cell, p)
            return _runner(cmd, env=env)

        def _runner(cmd, *, env):
            return subprocess.run(cmd, env=env)

        async def later(p):
            cmd, env = headless_claude_launch(["claude", "-p", p], os.environ)
            return await asyncio.create_subprocess_exec(*cmd, env=env)

        def either(p, short):
            if short:
                cmd, env = headless_claude_launch(["claude", "-p", p], os.environ)
            else:
                cmd, env = headless_claude_launch(["claude", "--print", "--", p], {})
            return subprocess.run(cmd, env=env)

        def each(prompts):
            for p in prompts:
                cmd, env = headless_claude_launch(["claude", "-p", p], os.environ)
                subprocess.run(cmd, env=env)

        def retried(p):
            cmd, env = headless_claude_launch(["claude", "-p", p], os.environ)
            try:
                subprocess.run(cmd, env=env)
            except OSError:
                subprocess.run(cmd, env=env)
            finally:
                cleanup()
            return subprocess.run(cmd, env=env)

        def tolerant(p):
            cmd, env = headless_claude_launch(["claude", "-p", p], os.environ)
            with contextlib.suppress(OSError):
                subprocess.run(cmd, env=env)
            return subprocess.run(cmd, env=env)
        """
    )
    scopes = {"direct", "builder", "caller", "later", "either", "each", "retried", "tolerant"}
    assert {inv.scope for inv in found} == scopes
    assert all(inv.controlled for inv in found)


@pytest.mark.parametrize(
    "body",
    [
        'def run(p):\n    subprocess.run(["gemini", "-p", p])\n',
        'def run(p):\n    subprocess.run(["gh", "release", "download", "v1", "-p", "x"])\n',
        'def run(p):\n    subprocess.run([GROK_BIN, "-p", p])\n',
        'def run(p):\n    subprocess.run(["cursor-agent", "--model", "claude-opus-5-5", "-p", p])\n',
        'def run(p):\n    subprocess.run(["claude", "mcp", "list"])\n',
        'def run(p):\n    subprocess.run(["claude", "--", "-p"])\n',
        'def run():\n    subprocess.run("mkdir -p ~/.claude/x", shell=True)\n',
        '_FLAGS = ("--print", "--model")\n',
    ],
)
def test_scanner_ignores_other_programs(body: str) -> None:
    assert _scan(body) == []


def test_static_limit_imported_print_flag_is_documented() -> None:
    """A print flag imported from another module is opaque to the scan (documented static limit).

    The guarantee for such a launcher is its behavioural test, as for the
    direct launchers above.
    """
    found = _scan('from elsewhere import FLAGS\ndef run(p):\n    subprocess.run(["claude", *FLAGS, p])\n')
    assert found == []


def test_scanner_flags_a_new_uncontrolled_module_on_disk(tmp_path: Path) -> None:
    module = tmp_path / "late_launcher.py"
    module.write_text(
        'import subprocess\n\ndef go(p):\n    return subprocess.run(["claude", "-p", p])\n', encoding="utf-8"
    )
    found = scan_source(module.read_text(encoding="utf-8"), "scripts/late_launcher.py")
    assert [(inv.key, inv.controlled) for inv in found] == [("scripts/late_launcher.py::go", False)]


def test_scanner_reports_a_plan_built_outside_the_adapters() -> None:
    found = _scan('def plan(p):\n    return InvocationPlan(cmd=["claude", "-p", p], cwd=".")\n')
    assert [(inv.kind, inv.scope) for inv in found] == [("plan", "plan")]


# --- Shell discovery ----------------------------------------------------------------------


@pytest.mark.parametrize(
    "script",
    [
        "claude -p hello\n",
        'claude --model "$M" -p hello\n',
        "claude --model m \\\n  --output-format text \\\n  -p hello\n",
        "alias cc='claude --model m'\ncc -p hello\n",
        'CLAUDE_BIN="${KIMICC_CLAUDE_BIN:-claude}"\nCMD=("$CLAUDE_BIN" -p --bare)\nexec "${CMD[@]}"\n',
        'BIN=$(command -v claude)\n"$BIN" --print hi\n',
        'out=$(timeout 60 claude -p "$prompt")\n',
        'run_cc() {\n  claude "$@"\n}\nrun_cc -p hi\n',
        "if true; then env A=1 /opt/bin/claude -p x; fi\n",
    ],
)
def test_shell_scan_finds_print_mode_claude(script: str) -> None:
    assert shell_claude_print_lines(script)


@pytest.mark.parametrize(
    "script",
    [
        'mkdir -p "$HOME/.claude/hooks"\n',
        "# claude -p is how headless runs start\n",
        'echo "run claude -p yourself"\n',
        "cat <<EOF\nclaude -p hello\nEOF\n",
        'exec claude --model "$M" "$@"\n',
        '"$CLAUDE_DIR/hooks/guard.sh" -p\n',
    ],
)
def test_shell_scan_ignores_other_commands(script: str) -> None:
    assert shell_claude_print_lines(script) == []


def test_shell_launcher_check_requires_a_runner_test_naming_the_script() -> None:
    """Imported-but-unused constants or an unrelated test cannot vouch for a shell launcher."""
    tests_source = (
        "from x import HEADLESS_BACKGROUND_ENV, HEADLESS_BACKGROUND_TOOL_DENIES\n"
        "def test_unrelated():\n    assert HEADLESS_BACKGROUND_ENV and HEADLESS_BACKGROUND_TOOL_DENIES\n"
        "def test_runs_new():\n    launch('new_headless.sh')\n"
    )
    launching = {"scripts/new_headless.sh"}
    assert _shell_launcher_errors(launching, {}, tests_source) == ["unmapped shell launcher: scripts/new_headless.sh"]
    assert _shell_launcher_errors(launching, {"scripts/new_headless.sh": "test_unrelated"}, tests_source) == [
        "test_unrelated does not launch new_headless.sh"
    ]
    assert _shell_launcher_errors(launching, {"scripts/new_headless.sh": "test_runs_new"}, tests_source) == []
