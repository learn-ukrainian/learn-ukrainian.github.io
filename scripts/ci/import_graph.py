"""Import-graph dependency index for PR test selection (#8750 phase B0a).

Pure library, stdlib only, no CI wiring. Given a git tree-ish (and optionally
a base tree-ish) plus the changed paths, it answers one question: which test
files can observe the change, or must the caller run everything?

Design points
-------------
* Sparse-checkout safe: the tree is enumerated with ONE ``git ls-tree -r`` per
  tree-ish and every blob is read with ONE ``git cat-file --batch`` per run.
  The working tree is never read.
* Every tracked ``.py`` is a node, wherever it lives. Edges come from a
  lexical candidate scan (``import`` / ``import_module`` / ``.py`` / quoted
  dotted-name hits) followed by exact parsing of each candidate call with
  ``ast``. A full ``ast.parse`` of all ~70 MB of first-party source measured
  20-40 s, which cannot meet the 3 s budget, so full ``ast`` validation is
  applied to the CHANGED files (a syntax error there is ``UNPARSABLE_BLOB``);
  unchanged files can only over-match (the scan also matches code embedded in
  strings, which is intended: a test that writes ``import delegate`` into a
  subprocess depends on it).
* Edge kinds (``ImportGraph.edge_kinds``): ``import`` (``import``,
  ``from ... import`` including relative, star and submodule names, literal
  ``importlib.import_module`` / ``__import__`` / ``runpy.run_module``, and
  ``pytest_plugins`` names in any module), ``init`` (ancestor ``__init__.py``
  initializers, run first by any submodule import), ``load`` (a file loaded
  through ``spec_from_file_location`` / ``runpy.run_path`` /
  ``SourceFileLoader`` by a statically evaluated path; a known directory
  joined with a computed name loads every file under it) and ``mention`` (a
  string literal naming a first-party path such as ``scripts/x.py`` or
  ``root / "scripts" / "x.py"``, a dotted module such as ``scripts.x.y`` /
  ``python -m scripts.x`` / ``monkeypatch.setattr("scripts.x.y", ...)``, or
  the literal prefix of a computed module name, which reaches every module
  whose dotted name starts with it; comments are ignored, and a non-test file
  that names a test path is not an edge).
* One file is one node under several runtime identities. ``pythonpath`` from
  ``pyproject.toml`` plus ``scripts`` are flat import roots (``import
  delegate`` and ``import scripts.delegate`` reach the same file), as are the
  import roots of in-tree installable packages (``packages/*/src``). Each
  file also resolves against its own directory, its pytest ``rootdir``
  insertion directory and every directory it puts on ``sys.path``, evaluated
  statically (``Path(__file__).resolve().parents[2] / "scripts"``, module
  constants, ``os.path.join(os.path.dirname(__file__), ...)``). Within one
  root a package directory shadows a same-named module.
* Result = reverse transitive closure of the changed files, restricted to
  test files; a changed test file selects itself. Nested conftests scope to
  their directory subtree.

Closed reason codes (``Reason``) for a FULL result:

``NO_CHANGED_PATHS``          nothing to classify.
``GIT_ERROR``                 git failed or a blob could not be read.
``NON_PYTHON_CHANGE``         a changed path is not ``*.py``.
``CHANGED_SET_INCOMPLETE``    with a base tree, the trees differ at a path that
                              is not in the changed list (e.g. one side of a
                              rename was dropped).
``UNPARSABLE_BLOB``           a changed ``.py`` or a ``pyproject.toml`` is not
                              valid.
``DELETION_UNRECOVERABLE``    a path was deleted or renamed away and the base
                              tree needed to rebuild its edges is missing or
                              unreadable.
``CONFTEST_REACHABLE``        the change is a root ``conftest.py`` or is
                              imported (transitively, including function-local
                              imports of autouse fixtures) by one.
``CONFTEST_SCOPE_UNKNOWN``    the change reaches a conftest outside ``tests/``
                              (pytest runs with ``testpaths = tests``), whose
                              collection scope is therefore not established.
``PYTEST_PLUGIN``             the change is, or is imported by, a plugin
                              registered through ``pytest_plugins`` in a
                              conftest, ``addopts -p ...``, or a ``pytest11``
                              entry point declared in a ``pyproject.toml``.
``UNBOUNDED_DYNAMIC_IMPORT``  a file pytest can run (a test, a conftest, a
                              plugin or anything they reach) loads code its
                              own evidence does not bound, so the change
                              could be the target: ``import_module`` /
                              ``__import__`` / ``run_module`` with a computed
                              name and no literal prefix naming a first-party
                              module (``dynamic="strict"``: any computed
                              name); ``spec_from_file_location`` /
                              ``run_path`` / ``SourceFileLoader`` with a path
                              that cannot be evaluated; an alias of any of
                              these loaders (``load = import_module``); a
                              ``sys.path`` change or ``pytest_plugins`` value
                              that cannot be evaluated. Bounding is per call:
                              a literal elsewhere never bounds a computed
                              name. ``dynamic="dependents"`` always selects
                              the tests that reach such a file instead
                              (FULL when a root conftest or plugin reaches
                              it).
``AMBIGUOUS_RESOLUTION``      an import that resolves to more than one distinct
                              first-party file involves a changed file.

The caller must ALWAYS also run ``-m repo_wide`` with a selected tier:
tests that walk a directory (``scan_scripts()`` over ``scripts/``, #8707)
observe files through the filesystem, not through an import edge, so this
index never selects them. The caller must treat an empty ``tests`` with
``unreached`` paths as "no test imports this change", not as "run nothing".

Known residuals (not modelled, documented for the caller):
``PYTEST_ADDOPTS`` / CLI ``-p`` flags outside ``pyproject.toml``;
``pytest.ini`` / ``tox.ini`` / ``setup.cfg`` (absent here); installed
third-party ``pytest11`` plugins; ``PYTHONPATH`` handed to a subprocess;
``exec`` / ``compile`` of source read from a file; a ``getattr(importlib,
"import_module")`` lookup; ``sys.path`` entries leaking across modules of one
process (pytest ``rootdir`` insertion, another module's ``sys.path.insert``):
an import resolves against the importing file's own roots only; a fixture of
a ``pytest_plugins`` module used by a test that does not itself (transitively)
declare that plugin, which works only by collection order.
"""

from __future__ import annotations

import ast
import bisect
import enum
import itertools
import os
import posixpath
import re
import shlex
import subprocess
import tomllib
from collections import defaultdict
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass, field
from typing import Literal

RepoPath = str | os.PathLike[str] | None
DynamicPolicy = Literal["strict", "bounded", "dependents"]
GIT_TIMEOUT_SECONDS = 120
TEST_ROOT = "tests"
_TEST_FILE_RE = re.compile(r"(?:^|/)(?:test_[^/]+\.py|[^/]+_test\.py)$")


class Reason(enum.StrEnum):
    """Closed set of FULL reason codes (see module docstring)."""

    NO_CHANGED_PATHS = "NO_CHANGED_PATHS"
    GIT_ERROR = "GIT_ERROR"
    NON_PYTHON_CHANGE = "NON_PYTHON_CHANGE"
    CHANGED_SET_INCOMPLETE = "CHANGED_SET_INCOMPLETE"
    UNPARSABLE_BLOB = "UNPARSABLE_BLOB"
    DELETION_UNRECOVERABLE = "DELETION_UNRECOVERABLE"
    CONFTEST_REACHABLE = "CONFTEST_REACHABLE"
    CONFTEST_SCOPE_UNKNOWN = "CONFTEST_SCOPE_UNKNOWN"
    PYTEST_PLUGIN = "PYTEST_PLUGIN"
    UNBOUNDED_DYNAMIC_IMPORT = "UNBOUNDED_DYNAMIC_IMPORT"
    AMBIGUOUS_RESOLUTION = "AMBIGUOUS_RESOLUTION"


@dataclass(frozen=True)
class Selection:
    """Outcome: ``full`` (with ``reason``) or the selected ``tests``."""

    full: bool
    reason: Reason | None = None
    detail: str = ""
    tests: tuple[str, ...] = ()
    # Changed .py files that no test reaches (caller decides what that means).
    unreached: tuple[str, ...] = ()


class GitError(RuntimeError):
    """A git command failed or returned malformed output."""


def is_test_file(path: str) -> bool:
    """True for ``tests/**/test_*.py`` and ``tests/**/*_test.py``."""
    return path.startswith(f"{TEST_ROOT}/") and bool(_TEST_FILE_RE.search(path))


# ---------------------------------------------------------------------------
# git access
# ---------------------------------------------------------------------------


def _git(repo: RepoPath, args: Sequence[str], stdin: bytes | None = None) -> bytes:
    try:
        proc = subprocess.run(
            ["git", *args],
            input=stdin,
            capture_output=True,
            cwd=str(repo) if repo is not None else None,
            timeout=GIT_TIMEOUT_SECONDS,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise GitError(f"git {args[0]} failed to run: {exc}") from exc
    if proc.returncode != 0:
        raise GitError(f"git {args[0]} exited {proc.returncode}: {proc.stderr.decode(errors='replace')[:300]}")
    return proc.stdout


def list_tree(repo: RepoPath, tree: str) -> dict[str, str]:
    """Map every blob path in ``tree`` to its object id (one git process)."""
    raw = _git(repo, ["ls-tree", "-r", "-z", tree])
    out: dict[str, str] = {}
    for entry in raw.split(b"\0"):
        if not entry:
            continue
        meta, _, path = entry.partition(b"\t")
        parts = meta.split()
        if len(parts) != 3 or not path:
            raise GitError(f"malformed ls-tree entry: {entry[:80]!r}")
        if parts[1] != b"blob" or parts[0] == b"120000":
            continue  # submodules and symlinks carry no readable source
        out[path.decode("utf-8", "surrogateescape")] = parts[2].decode("ascii")
    return out


def read_blobs(repo: RepoPath, oids: Sequence[str]) -> dict[str, bytes]:
    """Read every object id with ONE ``git cat-file --batch`` process."""
    unique = list(dict.fromkeys(oids))
    if not unique:
        return {}
    raw = _git(repo, ["cat-file", "--batch"], stdin=("\n".join(unique) + "\n").encode("ascii"))
    out: dict[str, bytes] = {}
    pos = 0
    for oid in unique:
        eol = raw.find(b"\n", pos)
        if eol < 0:
            raise GitError("truncated cat-file output")
        header = raw[pos:eol].split()
        if len(header) != 3 or header[0].decode("ascii") != oid or header[1] != b"blob":
            raise GitError(f"cat-file could not read {oid}: {raw[pos:eol][:80]!r}")
        size = int(header[2])
        out[oid] = raw[eol + 1 : eol + 1 + size]
        pos = eol + 1 + size + 1
    return out


# ---------------------------------------------------------------------------
# per-file fact extraction
# ---------------------------------------------------------------------------

_PREFIX_STMT_RE = re.compile(rb"""[ \t]*(?:[rRbBfFuU]{0,2}(?:\"\"\"|'''|\"|'))?[ \t]*(?:from[ \t]+([.\w]+)[ \t]+)?$""")
_INLINE_FROM_RE = re.compile(rb"(?:^|[:;])[ \t]*from[ \t]+([.\w]+)[ \t]+$")
_ITEM_RE = re.compile(r"\s*(\*|[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*)(?:\s+as\s+[A-Za-z_]\w*)?\s*")
_QUOTED_DOTTED_RE = re.compile(rb"""["']([A-Za-z_]\w*(?:\.[A-Za-z_]\w*)+)""")
_DASH_M_RE = re.compile(rb"-m[ \t]+([A-Za-z_][\w.]*)")
_PY_TOKEN_END_RE = re.compile(rb"\.py\b")
_PATH_CHAR = frozenset(b"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_./-")
# Data suffixes: "config.yaml" is not the dotted module "config" + attribute "yaml".
_DATA_SUFFIXES = frozenset(
    (
        "json",
        "yaml",
        "yml",
        "md",
        "txt",
        "db",
        "sqlite",
        "csv",
        "toml",
        "html",
        "js",
        "ts",
        "sh",
        "log",
        "cfg",
        "ini",
        "lock",
        "png",
        "svg",
        "jsonl",
        "tsv",
        "xml",
    )
)
_IGNORED_BARE_NAMES = frozenset({"__init__.py", "conftest.py", "__main__.py", "setup.py"})
_WORD_BYTES = frozenset(b"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_")
_WORD_BYTES_DOT = _WORD_BYTES | {ord(".")}
_MAX_CONTINUATION_LINES = 200


@dataclass
class FileFacts:
    """Tree-independent facts extracted from one blob."""

    # (level, module, names) for each import statement; level>0 is relative.
    imports: list[tuple[int, str, tuple[str, ...]]] = field(default_factory=list)
    dyn_literals: list[str] = field(default_factory=list)
    dyn_prefixes: list[str] = field(default_factory=list)
    unbounded: list[str] = field(default_factory=list)
    path_tokens: set[str] = field(default_factory=set)
    bare_path_tokens: set[str] = field(default_factory=set)
    dotted_tokens: set[str] = field(default_factory=set)
    plugins: list[str] = field(default_factory=list)
    # Directories put on sys.path and files loaded by path, as ``_path_values``
    # spellings (cwd-relative or anchored at the file with ``@F``).
    syspath: set[str] = field(default_factory=set)
    file_loads: set[str] = field(default_factory=set)


def _parse_import_statement(stmt: str, from_module: str | None, facts: FileFacts) -> None:
    """Lenient parse of the text after ``import``: leading names only."""
    text = re.sub(r"#[^\n]*", "", stmt).replace("\\\n", " ").replace("(", " ").replace(")", " ")
    names: list[str] = []
    for item in text.split(","):
        match = _ITEM_RE.match(item)
        if not match:
            break
        names.append(match.group(1))
        if match.end() < len(item):
            break  # trailing prose, quote or a following statement
    if not names:
        return
    if from_module is None:
        for name in names:
            facts.imports.append((0, name, ()))
        return
    level = len(from_module) - len(from_module.lstrip("."))
    facts.imports.append((level, from_module.lstrip("."), tuple(names)))


def _statement_text(data: bytes, start: int) -> str:
    """Logical-line text from ``start`` (continuations and open parens joined)."""
    end = data.find(b"\n", start)
    if end < 0:
        end = len(data)
    stmt = data[start:end]
    extra = 0
    while (
        extra < _MAX_CONTINUATION_LINES
        and end < len(data)
        and (stmt.rstrip().endswith(b"\\") or stmt.count(b"(") > stmt.count(b")"))
    ):
        nxt = data.find(b"\n", end + 1)
        if nxt < 0:
            nxt = len(data)
        stmt += b"\n" + data[end + 1 : nxt]
        end = nxt
        extra += 1
    return stmt.decode("utf-8", "replace")


def _balanced_close(data: bytes, open_paren: int) -> int | None:
    """Offset of the ``)`` matching ``data[open_paren]`` (within 2000 bytes)."""
    depth = 0
    limit = min(len(data), open_paren + 2000)
    idx = open_paren
    while idx < limit:
        close = data.find(b")", idx, limit)
        if close < 0:
            return None
        depth += data.count(b"(", idx, close) - 1
        if depth == 0:
            return close
        idx = close + 1
    return None


def _balanced_call_args(data: bytes, open_paren: int) -> str | None:
    close = _balanced_close(data, open_paren)
    return data[open_paren + 1 : close].decode("utf-8", "replace") if close is not None else None


def _dotted_prefix(node: ast.expr) -> str | None:
    """Leading constant text of an f-string or ``"a." + x`` expression."""
    if isinstance(node, ast.JoinedStr) and node.values:
        first = node.values[0]
        if isinstance(first, ast.Constant) and isinstance(first.value, str):
            return first.value
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        return _dotted_prefix(node.left) or (
            node.left.value if isinstance(node.left, ast.Constant) and isinstance(node.left.value, str) else None
        )
    return None


# A computed module name is bounded only by its own literal prefix: a dotted
# package plus an optional leading stem (``"pkg.sub."`` or ``"pkg.v4_"``).
_MODULE_PREFIX_RE = re.compile(r"[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*\.\w*|[A-Za-z_]\w*")
# name -> (kind, positional index, keyword) of the argument that names what is loaded.
_LOADERS: dict[str, tuple[str, int, str]] = {
    "import_module": ("module", 0, "name"),
    "__import__": ("module", 0, "name"),
    "run_module": ("module", 0, "mod_name"),
    "spec_from_file_location": ("file", 1, "location"),
    "run_path": ("file", 0, "path_name"),
    "SourceFileLoader": ("file", 1, "path"),
    "SourcelessFileLoader": ("file", 1, "path"),
}
# sys.path mutation -> (positional index of the path argument, argument is a sequence).
_SYSPATH_CALLS: dict[bytes, tuple[int, bool]] = {
    b"sys.path.insert": (1, False),
    b"sys.path.append": (0, False),
    b"sys.path.extend": (0, True),
    b"syspath_prepend": (0, False),
    b"site.addsitedir": (0, False),
}
_SYSPATH_ASSIGN_RE = re.compile(rb"sys\.path[ \t]*(\[[^\]\n]*\])?[ \t]*(?:\+=|=(?!=))")
_PLACEHOLDER_RE = re.compile(r"\{([^{}]*?)(?:![rsa])?(?::[^{}]*)?\}")
_FILE_ANCHOR = "@F"  # the scanned file's own path; resolved per file by the graph
_MAX_PATH_VALUES = 64
_PATH_CONSTRUCTORS = ("Path", "PurePath", "PosixPath", "PurePosixPath")
# Calls whose value is their (joined) path arguments.
_PATH_FUNCTIONS = frozenset((*_PATH_CONSTRUCTORS, "str", "fspath", "abspath", "realpath", "normpath", "join"))


def _parse_call_args(args_text: str | None) -> ast.Call | None:
    """``f(<args_text>)`` as an ``ast.Call``.

    Call text inside a code template (``f"sys.path.insert(0, {root!r})"``)
    only parses once each ``{expr!r}`` placeholder is replaced by ``expr``,
    which is evaluated in the scanned file itself.
    """
    if args_text is None:
        return None
    for text in (args_text, _PLACEHOLDER_RE.sub(r"(\1)", args_text)):
        try:
            call = ast.parse(f"f({text})", mode="eval").body
        except SyntaxError:
            continue
        if isinstance(call, ast.Call):
            return call
    return None


def _call_arg(call: ast.Call, index: int, keyword: str) -> ast.expr | None:
    for kw in call.keywords:
        if kw.arg == keyword:
            return kw.value
    if len(call.args) > index and not any(isinstance(a, ast.Starred) for a in call.args[: index + 1]):
        return call.args[index]
    return None


_SIMPLE_ASSIGN_RE = re.compile(rb"[ \t]*(?::[^=\n]*)?=(?!=)")
_BINDER_HEAD_RE = re.compile(
    rb"(?:\bas|\bdef|\bclass|\blambda\b[^:\n]*|\bfor\b(?:(?!\bin\b)[^\n])*"
    rb"|\b(?:global|nonlocal|del)\b[^;\n]*|^[ \t]*case\b[^\n]*)[ \t,(]*$"
)
_IMPORT_NAMES = rb"(?:[\w.]+(?:[ \t]+as[ \t]+\w+)?[ \t]*,[ \t]*)*(?:[\w.]+[ \t]+as[ \t]+)?"
_IMPORT_HEAD_RE = re.compile(rb"[ \t]*(?:from[ \t]+[\w.]+[ \t]+)?import[ \t]+\(?[ \t]*" + _IMPORT_NAMES)
_IMPORT_CONTINUATION_RE = re.compile(rb"[ \t]*" + _IMPORT_NAMES)
_FROM_STMT_RE = re.compile(rb"[ \t]*from[ \t]+(\.*)([\w.]*)[ \t]+import\b")
_LITERAL_FOR_RE = re.compile(rb"[ \t]+in[ \t]+(.+?):[ \t]*(?:#[^\n]*)?$")
_BINDER_WORDS_RE = re.compile(rb"\b(?:as|def|class|lambda|for|global|nonlocal|del|case|import)\b")
_STAR_IMPORT_RE = re.compile(rb"(?m)^[ \t]*from[ \t]+\S+[ \t]+import[ \t]+\*")
_DEF_RE = re.compile(rb"def[ \t]+\w+[ \t]*(?:\[[^\]\n]*\])?[ \t]*\(")
_DEF_INDENT_RE = re.compile(rb"([ \t]*)(?:async[ \t]+)?")
_TRIPLE_QUOTE_RE = re.compile(rb"\"\"\"|'''")
# A constant imported from another module: ``@I<level>|<module>|<name>@``.
_IMPORT_SPELLING_RE = re.compile(r"@I(\d+)\|([\w.]*)\|(\w+)@(.*)", re.S)


def _is_target_tail(head: bytes, tail: bytes) -> bool:
    """True when the rest of the line makes the name an assignment target.

    ``NAME := x`` anywhere; otherwise an ``=`` (or augmented ``+=``) before
    any quote or comment at the name's own bracket depth when the name is not
    inside brackets (``NAME, b = ...``, ``A = NAME = ...``, ``NAME += 1``), or
    just after the brackets close when the statement opens with one
    (``(a, NAME) = ...``). A keyword argument's name or value
    (``f(NAME=1)``, ``f(default=NAME, help="x")``) and a use such as
    ``NAME.mkdir(parents=True)`` are not targets.
    """
    if re.match(rb"[ \t]*:=", tail):
        return True
    inside = sum(head.count(c) for c in (b"(", b"[", b"{")) > sum(head.count(c) for c in (b")", b"]", b"}"))
    bracketed_target = head.lstrip()[:1] in (b"(", b"[")
    depth = lowest = 0
    for idx, ch in enumerate(tail):
        if ch in b"([{":
            depth += 1
        elif ch in b")]}":
            depth -= 1
            lowest = min(lowest, depth)
        elif ch in b"'\"#":
            return False
        elif ch == 0x3D and depth == lowest and ((depth == 0 and not inside) or (depth < 0 and bracketed_target)):
            before, after = tail[idx - 1 : idx], tail[idx + 1 : idx + 2]
            if after == b"=" or before in (b"=", b"!", b"<", b">"):
                continue
            return True
    return False


def _import_statement_start(data: bytes, start: int) -> int | None:
    """Offset of the import statement that the name at ``start`` belongs to."""
    ls = data.rfind(b"\n", 0, start) + 1
    head = data[ls:start]
    if _IMPORT_HEAD_RE.fullmatch(head):
        return ls
    if not _IMPORT_CONTINUATION_RE.fullmatch(head):
        return None
    opener = data.rfind(b"(", 0, start)
    if opener < 0 or b")" in data[opener:start]:
        return None
    ols = data.rfind(b"\n", 0, opener) + 1
    return ols if re.fullmatch(rb"\s*from\s+[\w.]+\s+import\s*", data[ols:opener]) else None


def _is_plain_import_name(data: bytes, start: int, end: int) -> bool:
    """True when ``data[start:end]`` is an un-aliased name in an import statement."""
    after = data[end : end + 40].lstrip(b" \t")
    if after[:2] == b"as" and after[2:3] in (b" ", b"\t"):
        return False
    return _import_statement_start(data, start) is not None


class _Bindings:
    """Every value a name is bound to in one blob, found lexically and by scope.

    Only the binding statements are parsed (a full ``ast.parse`` of every
    candidate file costs seconds). A simple ``NAME = value``, a statement
    ``for NAME in (<literal>, ...)`` and ``from mod import NAME`` (an
    ``@I`` spelling the graph resolves in ``mod``) contribute values. Any other
    possible binding (parameter, ``import x as NAME``, ``with`` / ``except``
    ``as``, unpacking or chained target, ``+=``, ``:=``, a loop target,
    ``global`` / ``del``, a star import in the file) poisons the name, so
    evaluating it fails and the caller treats the value as unknown; a name
    used as a keyword argument is poisoned too, which only costs precision.

    A use inside a ``def`` sees the bindings of the innermost enclosing
    ``def`` that binds the name (Python makes such a name local); otherwise
    the union of every binding in the file.
    """

    def __init__(self, data: bytes) -> None:
        self._data = data
        self._occurrences: dict[str, list[tuple[str, int, ast.expr | str | None]] | None] = {}
        self._defs: list[tuple[int, int, int, int]] | None = None  # start, indent, sig start, sig end
        self._def_ends: dict[int, int] = {}
        self._lines: tuple[list[int], list[int | None]] | None = None
        self._triple: list[tuple[int, int]] | None = None

    def alias(self, name: str) -> str:
        """Imported original of ``name`` (``from pathlib import Path as _P``)."""
        if name in _PATH_FUNCTIONS or b" as " not in self._data:
            return name
        match = re.search(rb"\b([A-Za-z_]\w*)[ \t]+as[ \t]+" + re.escape(name.encode()) + rb"\b", self._data)
        return match.group(1).decode("ascii") if match else name

    def lookup(self, name: str, pos: int) -> list[tuple[ast.expr | str, int]] | None:
        """``(value, binding offset)`` pairs visible at ``pos``; None if unknown."""
        occurrences = self._occurrences.get(name, [])
        if name not in self._occurrences:
            occurrences = self._occurrences[name] = self._scan(name)
        if occurrences is None:
            return None
        chosen = occurrences
        for start, end in self._enclosing_defs(pos):
            local = [o for o in occurrences if start <= o[1] < end]
            if local:
                chosen = local
                break
        if not chosen or any(kind == "poison" for kind, _, _ in chosen):
            return None
        return [(value, where) for _, where, value in chosen if value is not None]

    def in_def(self, pos: int) -> bool:
        return bool(self._enclosing_defs(pos))

    def in_triple_quoted_string(self, pos: int) -> bool:
        if self._triple is None:
            self._triple = []
            match = _TRIPLE_QUOTE_RE.search(self._data)
            while match:
                close = self._data.find(match.group(), match.end())
                if close < 0:
                    break
                self._triple.append((match.end(), close))
                match = _TRIPLE_QUOTE_RE.search(self._data, close + 3)
        return any(start <= pos < end for start, end in self._triple)

    def _def_spans(self) -> list[tuple[int, int, int, int]]:
        """``(start, indent, signature start, signature end)`` of every ``def``."""
        if self._defs is None:
            data = self._data
            self._defs = []
            pos = data.find(b"def")
            while pos >= 0:
                ls = data.rfind(b"\n", 0, pos) + 1
                lead = _DEF_INDENT_RE.fullmatch(data, ls, pos)
                match = _DEF_RE.match(data, pos) if lead else None
                if lead and match:
                    close = _balanced_close(data, match.end() - 1)
                    sig_end = close if close is not None else len(data)
                    self._defs.append((ls, len(lead.group(1)), match.end(), sig_end))
                pos = data.find(b"def", pos + 3)
        return self._defs

    def _def_end(self, index: int) -> int:
        """End offset of a ``def`` body: the next non-blank line indented no deeper."""
        if index not in self._def_ends:
            if self._lines is None:
                starts = [0, *(m.end() for m in re.finditer(rb"\n", self._data))]
                indents = [
                    None if not line.strip() else len(line) - len(line.lstrip(b" \t"))
                    for line in self._data.split(b"\n")
                ]
                self._lines = (starts, indents)
            starts, indents = self._lines
            _, indent, _, sig_end = self._def_spans()[index]
            end = len(self._data)
            for line in range(bisect.bisect_right(starts, sig_end), len(indents)):
                width = indents[line]
                if width is not None and width <= indent:
                    end = starts[line]
                    break
            self._def_ends[index] = end
        return self._def_ends[index]

    def _enclosing_defs(self, pos: int) -> list[tuple[int, int]]:
        if pos < 0 or b"def" not in self._data:
            return []
        spans = []
        for index, (start, _, _, _) in enumerate(self._def_spans()):
            if start > pos:
                break
            end = self._def_end(index)
            if pos < end:
                spans.append((start, end))
        return sorted(spans, reverse=True)

    def _signature_at(self, pos: int) -> bool:
        if b"def" not in self._data:
            return False
        spans = self._def_spans()  # ordered by offset; signatures never nest
        index = bisect.bisect_right(spans, (pos, len(self._data))) - 1
        return index >= 0 and spans[index][2] <= pos < spans[index][3]

    def _scan(self, name: str) -> list[tuple[str, int, ast.expr | str | None]] | None:
        data = self._data
        if b"*" in data and _STAR_IMPORT_RE.search(data):
            return None
        out: list[tuple[str, int, ast.expr | str | None]] = []
        token = name.encode()
        start = data.find(token)
        while start >= 0:
            end = start + len(token)
            nxt = data.find(token, end)
            if (start and data[start - 1] in _WORD_BYTES_DOT) or (end < len(data) and data[end] in _WORD_BYTES):
                start = nxt
                continue
            ls = data.rfind(b"\n", 0, start) + 1
            head = data[ls:start]
            le = data.find(b"\n", end)
            tail = data[end : le if le >= 0 else len(data)]
            if (
                head.strip()
                and b"=" not in tail
                and not _BINDER_WORDS_RE.search(head)
                and head.rstrip()[-1:] not in b"(,*"
            ):
                start = nxt
                continue  # a plain use: no target, binder keyword or parameter position
            self._classify(name, data, start, end, head, tail, out)
            start = nxt
        return out

    def _classify(
        self,
        name: str,
        data: bytes,
        start: int,
        end: int,
        head: bytes,
        tail: bytes,
        out: list[tuple[str, int, ast.expr | str | None]],
    ) -> None:
        """Append the binding (value, import or poison) at ``start``, if any."""
        if not head.strip():
            simple = _SIMPLE_ASSIGN_RE.match(data, end)
            if simple:
                try:
                    out.append(
                        ("value", start, ast.parse(_statement_text(data, simple.end()).strip(), mode="eval").body)
                    )
                except SyntaxError:
                    out.append(("poison", start, None))
                return
        if re.fullmatch(rb"[ \t]*(?:async[ \t]+)?for[ \t]+", head):
            loop = _LITERAL_FOR_RE.match(tail)
            try:
                iterable = ast.parse(loop.group(1).decode("utf-8", "replace"), mode="eval").body if loop else None
            except SyntaxError:
                iterable = None
            if isinstance(iterable, (ast.List, ast.Tuple, ast.Set)):
                out.extend(("value", start, element) for element in iterable.elts)
            else:
                out.append(("poison", start, None))
            return
        stmt = _import_statement_start(data, start)
        if stmt is not None:
            source = _FROM_STMT_RE.match(data, stmt)
            aliased = re.search(rb"(\w+)[ \t]+as[ \t]*$", head)
            original = aliased.group(1).decode("ascii") if aliased else name
            if source is None:
                out.append(("poison", start, None))  # ``import x as NAME``: a module object
            else:
                level, module = len(source.group(1)), source.group(2).decode("ascii")
                out.append(("import", start, f"@I{level}|{module}|{original}@"))
            return
        signature = self._signature_at(start)
        if signature:  # a parameter name binds; a default or annotation is a use
            if self._data[max(0, start - 200) : start].rstrip()[-1:] in (b"(", b",", b"*"):
                out.append(("poison", start, None))
        elif _is_target_tail(head, tail) or _BINDER_HEAD_RE.search(head):
            out.append(("poison", start, None))


def _join(left: set[str], right: set[str]) -> set[str]:
    # pathlib: an absolute right operand (an ``@`` anchor) replaces the left.
    # A trailing ``*`` (any continuation) absorbs whatever follows it.
    return {l if l.endswith("*") else r if r.startswith("@") else f"{l}/{r}" for l in left for r in right}


def _concat(left: set[str], right: set[str]) -> set[str] | None:
    # An anchor is only meaningful at the start of the string (``f"{ROOT}/x"``).
    if any(r.startswith("@") and l and not l.endswith("*") for l in left for r in right):
        return None
    return {l if l.endswith("*") else l + r for l in left for r in right}


def _path_values(
    node: ast.expr | None, env: _Bindings, pos: int, seen: frozenset[str] = frozenset(), *, wildcard: bool = False
) -> set[str] | None:
    """Static value(s) of a filesystem-path expression used at ``pos``, else ``None``.

    Values are spellings relative to the working directory (pytest runs at
    the repo root), anchored at the scanned file (``@F``, from ``__file__``)
    or at a constant imported from another module (``@I...@``, resolved by the
    graph). Covers ``Path(__file__).resolve().parents[N] / "x"``,
    ``os.path.join(os.path.dirname(__file__), "x")``, f-strings, module and
    function-local constants; anything else (a parameter, a helper call, an
    absolute or home-relative string) is unknown. With ``wildcard`` a known
    prefix followed by an unknown part (``Path(__file__).parent / name``,
    ``f"{ROOT}/tools/{name}.py"``) is ``<prefix>*``: any path under it.
    """
    out = _path_values_inner(node, env, pos, seen, wildcard) if node is not None else None
    return out if out is not None and len(out) <= _MAX_PATH_VALUES else None


def _path_values_inner(
    node: ast.expr, env: _Bindings, pos: int, seen: frozenset[str], wildcard: bool
) -> set[str] | None:
    def ev(sub: ast.expr) -> set[str] | None:
        return _path_values(sub, env, pos, seen, wildcard=wildcard)

    def open_end(prefix: set[str] | None, sep: str) -> set[str] | None:
        return {p if p.endswith("*") else f"{p}{sep}*" for p in prefix} if wildcard and prefix is not None else None

    if isinstance(node, ast.Constant):
        if not isinstance(node.value, str) or node.value.startswith(("/", "~", "\\", "@")) or ":" in node.value:
            return None
        return {node.value or "."}
    if isinstance(node, ast.Name):
        if node.id == "__file__":
            return {_FILE_ANCHOR}
        bindings = env.lookup(node.id, pos) if node.id not in seen else None
        if not bindings:
            return None
        out: set[str] = set()
        for value, where in bindings:
            got = (
                {value}
                if isinstance(value, str)
                else _path_values(value, env, where, seen | {node.id}, wildcard=wildcard)
            )
            if got is None:
                return None
            out |= got
        return out
    if isinstance(node, ast.Attribute):
        if node.attr == "parent":
            base = ev(node.value)
            return {f"{b}/.." for b in base} if base is not None and not any("*" in b for b in base) else None
        if node.attr == "sep":
            return {"/"}
        return None
    if isinstance(node, ast.Subscript):
        index = node.slice
        if (
            isinstance(node.value, ast.Attribute)
            and node.value.attr == "parents"
            and isinstance(index, ast.Constant)
            and type(index.value) is int
            and index.value >= 0
        ):
            base = ev(node.value.value)
            if base is None or any("*" in b for b in base):
                return None
            return {b + "/.." * (index.value + 1) for b in base}
        return None
    if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Div, ast.Add)):
        left, right = ev(node.left), ev(node.right)
        if left is None:
            return None
        if right is None:
            return open_end(left, "/" if isinstance(node.op, ast.Div) else "")
        return _join(left, right) if isinstance(node.op, ast.Div) else _concat(left, right)
    if isinstance(node, ast.JoinedStr):
        acc: set[str] | None = {""}
        for part in node.values:
            if isinstance(part, ast.FormattedValue):
                got = ev(part.value) if part.format_spec is None else None
            else:
                got = ev(part)
            if got is None:
                return open_end(acc, "") if acc != {""} else None
            acc = _concat(acc, got)
            if acc is None:
                return None
        return acc
    if isinstance(node, ast.IfExp):
        body, orelse = ev(node.body), ev(node.orelse)
        return body | orelse if body is not None and orelse is not None else None
    if isinstance(node, ast.Call) and not node.keywords:
        return _path_call_values(node, env, ev, open_end)
    return None


def _path_call_values(
    node: ast.Call,
    env: _Bindings,
    ev: Callable[[ast.expr], set[str] | None],
    open_end: Callable[[set[str] | None, str], set[str] | None],
) -> set[str] | None:
    func = node.func
    name = func.attr if isinstance(func, ast.Attribute) else env.alias(func.id) if isinstance(func, ast.Name) else None
    parts: list[ast.expr] = list(node.args)
    if name in ("cwd", "getcwd") and not parts:
        return {"."}
    if isinstance(func, ast.Attribute) and name in ("resolve", "absolute") and not parts:
        return ev(func.value)
    if name == "joinpath" and isinstance(func, ast.Attribute):
        parts.insert(0, func.value)
    elif name == "join" and isinstance(func, ast.Attribute) and isinstance(func.value, ast.Constant):
        return None  # "sep".join(parts)
    elif name == "dirname" and len(parts) == 1:
        base = ev(parts[0])
        return {f"{b}/.." for b in base} if base is not None and not any("*" in b for b in base) else None
    elif name in _PATH_CONSTRUCTORS and not parts:
        return {"."}
    elif name not in _PATH_FUNCTIONS:
        return None
    if not parts or any(isinstance(p, ast.Starred) for p in parts):
        return None
    acc = ev(parts[0])
    for part in parts[1:]:
        got = ev(part)
        if acc is None or got is None:
            return open_end(acc, "/")
        acc = _join(acc, got)
    return acc


def _sequence_values(
    node: ast.expr | None, env: _Bindings, pos: int, seen: frozenset[str] = frozenset()
) -> set[str] | None:
    """Path values of every entry a ``sys.path`` sequence expression adds.

    A copy or slice of ``sys.path`` itself (``saved = list(sys.path)`` restored
    later) adds nothing.
    """
    if node is None:
        return None
    if _is_syspath_copy(node):
        return set()
    if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
        out: set[str] = set()
        for element in node.elts:
            got = _path_values(element, env, pos, seen)
            if got is None:
                return None
            out |= got
        return out
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        left, right = _sequence_values(node.left, env, pos, seen), _sequence_values(node.right, env, pos, seen)
        return left | right if left is not None and right is not None else None
    if isinstance(node, ast.Name) and node.id not in seen:
        bindings = env.lookup(node.id, pos)
        if not bindings:
            return None
        acc: set[str] = set()
        for value, where in bindings:
            got = None if isinstance(value, str) else _sequence_values(value, env, where, seen | {node.id})
            if got is None:
                return None
            acc |= got
        return acc
    return None


def _is_syspath_copy(node: ast.expr) -> bool:
    def is_syspath(sub: ast.expr) -> bool:
        return (
            isinstance(sub, ast.Attribute)
            and sub.attr == "path"
            and isinstance(sub.value, ast.Name)
            and sub.value.id == "sys"
        )

    if is_syspath(node):
        return True
    if isinstance(node, ast.Subscript):
        return is_syspath(node.value) and isinstance(node.slice, ast.Slice)
    if isinstance(node, ast.Call) and not node.args and isinstance(node.func, ast.Attribute):
        return node.func.attr == "copy" and is_syspath(node.func.value)
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in ("list", "tuple"):
        return len(node.args) == 1 and _is_syspath_copy(node.args[0])
    if isinstance(node, (ast.ListComp, ast.GeneratorExp)) and len(node.generators) == 1:
        # [p for p in sys.path if ...]: a filtered copy
        loop = node.generators[0]
        return (
            isinstance(node.elt, ast.Name)
            and isinstance(loop.target, ast.Name)
            and node.elt.id == loop.target.id
            and _is_syspath_copy(loop.iter)
        )
    return False


def _handle_module_load(kind: str, arg: ast.expr | None, facts: FileFacts, where: str) -> None:
    """Classify one ``import_module`` / ``__import__`` / ``run_module`` call."""
    if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
        facts.dyn_literals.append(arg.value)
        return
    prefix = _dotted_prefix(arg) if arg is not None else None
    if prefix and _MODULE_PREFIX_RE.fullmatch(prefix):
        facts.dyn_prefixes.append(prefix)
        return
    facts.unbounded.append(f"{kind}@{where}")


def _line_of(data: bytes, pos: int) -> int:
    return data.count(b"\n", 0, pos) + 1


def _scan_loaders(data: bytes, facts: FileFacts, env: _Bindings) -> None:
    """Every call of (and reference to) a module or file loader.

    A module-name call is a literal edge, a literal-prefix edge or unbounded.
    A file-path call is resolved with ``_path_values`` or is unbounded. A bare
    reference that is not a plain ``from importlib import import_module``, a
    ``def``, a quoted string or prose inside a triple-quoted string is an
    alias (``load = importlib.import_module``) whose later calls are
    invisible, so it is unbounded as well. Calls are matched in strings too:
    a code template run in a subprocess loads code just the same.
    """
    hits = []
    for name in _LOADERS:
        token = name.encode()
        start = data.find(token)
        while start >= 0:
            end = start + len(token)
            if not (start and data[start - 1] in _WORD_BYTES) and not (end < len(data) and data[end] in _WORD_BYTES):
                hits.append((start, end, name))
            start = data.find(token, end)
    for start, end, name in sorted(hits):
        kind, index, keyword = _LOADERS[name]
        after = end
        while data[after : after + 1] in (b" ", b"\t"):
            after += 1
        if data[start - 4 : start] == b"def ":
            continue
        if data[after : after + 1] != b"(":
            if data[start - 1 : start] in (b'"', b"'") or data[end : end + 1] in (b'"', b"'"):
                continue
            if not _is_plain_import_name(data, start, end) and not env.in_triple_quoted_string(start):
                facts.unbounded.append(f"{name}-alias@{_line_of(data, start)}")
            continue
        call = _parse_call_args(_balanced_call_args(data, after))
        arg = _call_arg(call, index, keyword) if call is not None else None
        if kind == "module":
            _handle_module_load(name, arg, facts, str(_line_of(data, start)))
            continue
        values = _path_values(arg, env, start, wildcard=True)
        if values is None:
            facts.unbounded.append(f"{name}@{_line_of(data, start)}")
        else:
            facts.file_loads |= values


def extract_facts(data: bytes) -> FileFacts:
    """Extract every edge-relevant fact from one blob (see module docstring)."""
    facts = FileFacts()
    find = data.find
    pos = 0
    while True:
        idx = find(b"import", pos)
        if idx < 0:
            break
        pos = idx + 6
        prev = data[idx - 1 : idx] if idx else b"\n"
        nxt = data[idx + 6 : idx + 7]
        if nxt not in (b" ", b"\t", b"\\", b"(") or (prev and prev[0] in _WORD_BYTES):
            continue
        ls = data.rfind(b"\n", 0, idx) + 1
        prefix = data[ls:idx]
        from_module: str | None = None
        if prefix.strip():
            if b"#" in prefix:
                continue
            m_from = _INLINE_FROM_RE.search(prefix)
            m_open = _PREFIX_STMT_RE.match(prefix)
            if m_from:
                from_module = m_from.group(1).decode("ascii")
            elif m_open:
                if m_open.group(1):
                    from_module = m_open.group(1).decode("ascii")
            elif prefix.rstrip()[-1:] in (b":", b";", b'"', b"'"):
                pass
            else:
                continue
        _parse_import_statement(_statement_text(data, idx + 6), from_module, facts)
    env = _Bindings(data)
    _scan_loaders(data, facts, env)
    _scan_syspath(data, facts, env)
    _scan_mentions(data, facts)
    _scan_pytest_plugins(data, facts, env)
    return facts


def _scan_syspath(data: bytes, facts: FileFacts, env: _Bindings) -> None:
    """Directories put on ``sys.path``; a value that cannot be evaluated is unbounded.

    Covers ``insert`` / ``append`` / ``extend``, ``monkeypatch.syspath_prepend``,
    ``site.addsitedir``, ``sys.path += ...`` and ``sys.path[...] = ...``.
    """
    if b"sys.path" not in data and b"syspath_prepend" not in data and b"addsitedir" not in data:
        return
    for token, (index, is_sequence) in _SYSPATH_CALLS.items():
        pos = data.find(token)
        while pos >= 0:
            after = pos + len(token)
            if data[after : after + 1] == b"(" and (pos == 0 or data[pos - 1] not in _WORD_BYTES):
                call = _parse_call_args(_balanced_call_args(data, after))
                arg = call.args[index] if call is not None and len(call.args) > index else None
                values = _sequence_values(arg, env, pos) if is_sequence else _path_values(arg, env, pos)
                if values is None:
                    facts.unbounded.append(f"sys.path@{_line_of(data, pos)}")
                else:
                    facts.syspath |= values
            pos = data.find(token, after)
    if b"sys.path" not in data:
        return
    pos = data.find(b"sys.path")
    while pos >= 0:
        match = _SYSPATH_ASSIGN_RE.match(data, pos) if pos == 0 or data[pos - 1] not in _WORD_BYTES_DOT else None
        pos = data.find(b"sys.path", pos + 8)
        if match is None:
            continue
        try:
            node: ast.expr | None = ast.parse(_statement_text(data, match.end()).strip(), mode="eval").body
        except SyntaxError:
            node = None
        index = match.group(1)
        is_item = index is not None and b":" not in index
        values = _path_values(node, env, match.start()) if is_item else _sequence_values(node, env, match.start())
        if values is None:
            facts.unbounded.append(f"sys.path@{_line_of(data, match.start())}")
        else:
            facts.syspath |= values


def _path_context(data: bytes, start: int) -> tuple[list[str], bool] | None:
    """Quoted path segments joined by ``/`` or ``,`` before ``start``.

    Returns ``(segments, via_operator)`` when a quote directly precedes the
    token, else ``None``. ``via_operator`` marks ``<expr> / "x.py"``.
    """
    if data[start - 1 : start] not in (b'"', b"'"):
        return None
    segments: list[str] = []
    via_operator = False
    pos = start - 1  # index of the opening quote of the current segment
    for _ in range(12):
        i = pos
        while i > 0 and data[i - 1] in b" \t":
            i -= 1
        if i == 0 or data[i - 1] not in b"/,":
            break
        via_operator = via_operator or data[i - 1] == 0x2F
        i -= 1
        while i > 0 and data[i - 1] in b" \t":
            i -= 1
        if i == 0 or data[i - 1] not in b"\"'":
            break  # left operand is not a string literal
        opener = data.rfind(data[i - 1 : i], max(0, i - 300), i - 1)
        if opener < 0:
            break
        seg = data[opener + 1 : i - 1]
        if not seg or any(c not in _PATH_CHAR for c in seg):
            break
        segments.insert(0, seg.decode("ascii"))
        pos = opener
    return segments, via_operator


def _in_comment(data: bytes, pos: int) -> bool:
    """True when a ``#`` precedes ``pos`` on its line (comments never execute)."""
    return b"#" in data[data.rfind(b"\n", 0, pos) + 1 : pos]


def _scan_mentions(data: bytes, facts: FileFacts) -> None:
    """Path tokens (``scripts/x.py``) and quoted dotted names (``scripts.x.y``)."""
    for match in _PY_TOKEN_END_RE.finditer(data):
        end = match.end()
        start = match.start()
        while start > 0 and data[start - 1] in _PATH_CHAR:
            start -= 1
        token = data[start:end].decode("ascii", "ignore")
        if len(token) <= 3 or _in_comment(data, start):
            continue
        context = _path_context(data, start)
        segments, via_operator = context if context else ([], False)
        token = token[2:] if token.startswith("./") else token.lstrip("/")
        if segments:
            # ``,`` may separate list items rather than join path parts, so
            # every trailing run of segments is a candidate spelling.
            for cut in range(len(segments)):
                facts.path_tokens.add("/".join([*segments[cut:], token]))
        if "/" in token:
            facts.path_tokens.add(token)
        elif (
            not segments
            and context is not None
            and (via_operator or data[end : end + 1] in (b'"', b"'"))
            and token not in _IGNORED_BARE_NAMES
        ):
            facts.bare_path_tokens.add(token)
    for match in _QUOTED_DOTTED_RE.finditer(data):
        token = match.group(1).decode("ascii")
        if token.rsplit(".", 1)[-1] in _DATA_SUFFIXES or token.endswith(".py") or _in_comment(data, match.start()):
            continue
        facts.dotted_tokens.add(token)
    for match in _DASH_M_RE.finditer(data):
        if not _in_comment(data, match.start()):
            facts.dotted_tokens.add(match.group(1).decode("ascii").rstrip("."))


_PLUGINS_ASSIGN_RE = re.compile(rb"(?m)^[ \t]*pytest_plugins[ \t]*(?::[^=\n]*)?\+?=(?!=)")


def _scan_pytest_plugins(data: bytes, facts: FileFacts, env: _Bindings) -> None:
    """Names registered through ``pytest_plugins``; a computed module-level value is unbounded.

    pytest reads the module attribute, so a computed local variable of that
    name inside a ``def`` registers nothing.
    """
    if b"pytest_plugins" not in data:
        return
    for match in _PLUGINS_ASSIGN_RE.finditer(data):
        try:
            node: ast.expr | None = ast.parse(_statement_text(data, match.end()).strip(), mode="eval").body
        except SyntaxError:
            node = None
        elements = node.elts if isinstance(node, (ast.List, ast.Tuple, ast.Set)) else [node]
        names = [e.value for e in elements if isinstance(e, ast.Constant) and isinstance(e.value, str)]
        if len(names) == len(elements):
            facts.plugins.extend(names)
        elif not env.in_def(match.start()):
            facts.unbounded.append(f"pytest_plugins@{_line_of(data, match.start())}")


# ---------------------------------------------------------------------------
# graph construction
# ---------------------------------------------------------------------------

DEFAULT_FLAT_ROOTS = ("scripts",)


@dataclass(frozen=True)
class Ambiguity:
    importer: str
    name: str
    candidates: tuple[str, ...]


@dataclass
class PytestConfig:
    pythonpath: tuple[str, ...] = ()
    plugin_names: tuple[str, ...] = ()  # addopts ``-p`` and pytest11 entry points
    # Import roots of in-tree packages that get installed (``pip install ./pkg``).
    package_roots: tuple[str, ...] = ()


def _dir_of(path: str) -> str:
    return path.rpartition("/")[0]


def _ancestor_inits(directory: str, py: frozenset[str] | set[str]) -> set[str]:
    """``__init__.py`` files of every directory from the repo root to ``directory``."""
    out: set[str] = set()
    parts = directory.split("/") if directory else []
    for depth in range(1, len(parts) + 1):
        init = "/".join(parts[:depth]) + "/__init__.py"
        if init in py:
            out.add(init)
    if "__init__.py" in py:
        out.add("__init__.py")
    return out


class ImportGraph:
    """Forward/reverse import edges over every first-party ``.py`` in one tree."""

    def __init__(self, files: dict[str, str], blobs: dict[str, bytes], config: PytestConfig):
        self.py = frozenset(p for p in files if p.endswith(".py"))
        self.files = files
        self.blobs = blobs
        self.config = config
        self.dirs: set[str] = set()
        self.by_base: dict[str, list[str]] = defaultdict(list)
        for path in self.py:
            directory = _dir_of(path)
            while directory and directory not in self.dirs:
                self.dirs.add(directory)
                directory = _dir_of(directory)
            self.by_base[path.rpartition("/")[2]].append(path)
        self.roots: tuple[str, ...] = tuple(
            dict.fromkeys(["", *DEFAULT_FLAT_ROOTS, *config.pythonpath, *config.package_roots])
        )
        self.facts: dict[str, FileFacts] = {p: extract_facts(blobs[files[p]]) for p in sorted(self.py)}
        self.edges: dict[str, set[str]] = {p: set() for p in self.py}
        self.rev: dict[str, set[str]] = {p: set() for p in self.py}
        self.ambiguities: list[Ambiguity] = []
        # Files whose own evidence cannot bound what they load (computed module
        # name or file path, loader alias, computed sys.path or pytest_plugins).
        self.unbounded: dict[str, list[str]] = {}
        # Files with a literal-prefix computed module name (bounded; ``strict`` counts them).
        self.prefix_importers: set[str] = set()
        self.scope_rev: dict[str, set[str]] = defaultdict(set)
        self.edge_kinds: dict[tuple[str, str], set[str]] = defaultdict(set)
        self.conftests = sorted(p for p in self.py if p.rsplit("/", 1)[-1] == "conftest.py")
        self.plugin_modules: dict[str, set[str]] = {"conftest": set(), "config": set()}
        self._sorted_py = sorted(self.py)
        self._roots_cache: dict[str, tuple[str, ...]] = {}
        self._syspath_dirs: dict[str, list[str]] = {}
        self._bindings: dict[str, _Bindings] = {}
        self._executed: set[str] | None = None
        self._build()

    # -- resolution --------------------------------------------------------

    def _base_roots(self, path: str) -> tuple[str, ...]:
        """Flat roots, the file's own directory and its pytest rootdir insertion."""
        directory = _dir_of(path)
        basedir = directory
        while basedir and f"{basedir}/__init__.py" in self.py:
            basedir = _dir_of(basedir)
        return tuple(dict.fromkeys([*self.roots, directory, basedir]))

    def _roots_for(self, path: str) -> tuple[str, ...]:
        cached = self._roots_cache.get(path)
        if cached is None:
            cached = tuple(dict.fromkeys([*self._base_roots(path), *self._syspath_dirs.get(path, ())]))
            self._roots_cache[path] = cached
        return cached

    def resolve_spelling(self, path: str, spelling: str, depth: int = 0) -> set[str] | None:
        """Repo-relative paths a ``_path_values`` spelling seen in ``path`` names.

        ``None`` when unknown (an imported constant that cannot be evaluated);
        a path outside the repository is dropped (no first-party file there).
        """
        if spelling.startswith(_FILE_ANCHOR):
            bases, rest = {path}, spelling[len(_FILE_ANCHOR) :]
        elif spelling.startswith("@I"):
            match = _IMPORT_SPELLING_RE.fullmatch(spelling)
            if match is None or depth > 4:
                return None
            level, module, name, rest = int(match.group(1)), match.group(2), match.group(3), match.group(4)
            bases = set()
            targets = self._constant_modules(path, level, module)
            for target in targets:
                env = self._bindings.setdefault(target, _Bindings(self.blobs[self.files[target]]))
                values = _path_values(ast.Name(id=name), env, -1)
                resolved = [self.resolve_spelling(target, v, depth + 1) for v in values or ()]
                if values is None or any(r is None for r in resolved):
                    return None
                bases |= {b or "." for r in resolved for b in r}  # type: ignore[union-attr]
            if not targets:
                return None
        else:
            bases, rest = {"."}, "/" + spelling
        out: set[str] = set()
        for base in bases:
            text, star, _ = (base + rest).partition("*")
            directory, _, stem = text.rpartition("/") if star else (text, "", "")
            normal = posixpath.normpath(directory or ".")
            if normal == ".." or normal.startswith(("../", "/")):
                continue  # outside the repository
            normal = "" if normal == "." else normal
            out.add(f"{normal}/{stem}*" if star and normal else f"{stem}*" if star else normal)
        return out

    def _constant_modules(self, path: str, level: int, module: str) -> list[str]:
        """Files that define ``module`` for ``from <level dots><module> import NAME`` in ``path``."""
        if level == 0:
            files, _, _ = self._module_files(module, self._base_roots(path))
            return sorted(files)
        base = _dir_of(path)
        for _ in range(level - 1):
            base = _dir_of(base)
        rel = "/".join(p for p in (base, module.replace(".", "/")) if p)
        return self._first_present(rel)

    def _module_files(self, name: str, roots: Iterable[str]) -> tuple[set[str], set[str], bool]:
        """(files, package inits, namespace-or-file found) for a dotted name."""
        rel = name.replace(".", "/")
        files: set[str] = set()
        inits: set[str] = set()
        found = False
        for root in roots:
            base = f"{root}/{rel}" if root else rel
            hit = False
            # Within one sys.path entry a package directory shadows a module.
            for cand in (f"{base}/__init__.py", f"{base}.py"):
                if cand in self.py:
                    files.add(cand)
                    hit = True
                    break
            if hit or base in self.dirs:
                found = True
                parts = rel.split("/")
                for depth in range(1, len(parts)):
                    init = "/".join(([root] if root else []) + parts[:depth]) + "/__init__.py"
                    if init in self.py:
                        inits.add(init)
        return files, inits, found

    def _link(self, source: str, targets: Iterable[str], kind: str) -> None:
        """Add ``source -> target`` edges of ``kind`` (import, init, mention or load)."""
        source_is_test = is_test_file(source)
        for target in targets:
            # A production file naming a test path (docstring, run hint) does
            # not execute that test.
            if kind == "mention" and not source_is_test and is_test_file(target):
                continue
            if target != source:
                self.edges[source].add(target)
                self.rev[target].add(source)
                self.edge_kinds[(source, target)].add(kind)

    def _record_ambiguity(self, importer: str, name: str, files: set[str]) -> None:
        if len(files) > 1:
            self.ambiguities.append(Ambiguity(importer, name, tuple(sorted(files))))

    def _resolve_import(self, path: str, level: int, module: str, names: tuple[str, ...]) -> None:
        if level == 0:
            roots = self._roots_for(path)
            files, inits, found = self._module_files(module, roots)
            if not found:
                return
            self._record_ambiguity(path, module, files)
            self._link(path, files, "import")
            self._link(path, inits, "init")
            for name in names:
                if name == "*":
                    continue
                sub_files, sub_inits, _ = self._module_files(f"{module}.{name}", roots)
                self._record_ambiguity(path, f"{module}.{name}", sub_files)
                self._link(path, sub_files, "import")
                self._link(path, sub_inits, "init")
            return
        base = _dir_of(path)
        for _ in range(level - 1):
            base = _dir_of(base)
        targets: set[str] = set()
        prefix = f"{base}/" if base else ""
        if module:
            rel = prefix + module.replace(".", "/")
            targets.update(self._first_present(rel))
            sub_base = rel
        else:
            init = f"{prefix}__init__.py"
            if init in self.py:
                targets.add(init)
            sub_base = base
        for name in names:
            if name == "*":
                continue
            sub = f"{sub_base}/{name}" if sub_base else name
            targets.update(self._first_present(sub))
        self._link(path, targets, "import")

    def _first_present(self, base: str) -> list[str]:
        for cand in (f"{base}/__init__.py", f"{base}.py"):
            if cand in self.py:
                return [cand]
        return []

    def _resolve_dotted_prefix_tokens(self, path: str, token: str) -> None:
        parts = token.split(".")
        roots = self._roots_for(path)
        for length in range(len(parts), 0, -1):
            name = ".".join(parts[:length])
            files, inits, _ = self._module_files(name, roots)
            if files and (length > 1 or any(not f.endswith("/__init__.py") for f in files)):
                self._link(path, files | inits, "mention")
                return

    def _resolve_path_token(self, path: str, token: str, *, bare: bool) -> None:
        if bare:
            self._link(path, self.by_base.get(token, ()), "mention")
            return
        parts = token.split("/")
        # Drop leading noise ("$ROOT/scripts/x.py", "./scripts/x.py") until the
        # remainder is a tracked path; else fall back to a path-suffix match.
        for start in range(len(parts) - 1):
            spelled = "/".join(parts[start:])
            if spelled in self.py:
                self._link(path, [spelled], "mention")
                return
        suffix = "/" + token
        self._link(path, [c for c in self.by_base.get(parts[-1], ()) if c.endswith(suffix)], "mention")

    def _build(self) -> None:
        for path in sorted(self.py):
            facts = self.facts[path]
            self._link(path, _ancestor_inits(_dir_of(path), self.py), "init")
            unbounded = list(facts.unbounded)
            # sys.path entries first: every name this file imports resolves against them.
            dirs: list[str] = []
            for spelling in sorted(facts.syspath):
                resolved = self.resolve_spelling(path, spelling)
                if resolved is None:
                    unbounded.append(f"sys.path value {spelling} does not resolve")
                else:
                    dirs += [d for d in sorted(resolved) if d == "" or d in self.dirs]
            self._syspath_dirs[path] = dirs
            for level, module, names in facts.imports:
                self._resolve_import(path, level, module, names)
            # A literal dynamic name and a pytest_plugins name load like an import.
            for name in [*facts.dyn_literals, *facts.plugins]:
                level = len(name) - len(name.lstrip("."))
                self._resolve_import(path, level, name.lstrip("."), ())
            for prefix in facts.dyn_prefixes:
                self.prefix_importers.add(path)
                if not self._resolve_prefix(path, prefix):
                    unbounded.append(f"prefix {prefix!r} names no first-party module")
            for spelling in sorted(facts.file_loads):
                if not self._resolve_file_load(path, spelling):
                    unbounded.append(f"loaded path {spelling} does not resolve")
            for token in facts.dotted_tokens:
                self._resolve_dotted_prefix_tokens(path, token)
            for token in facts.path_tokens:
                self._resolve_path_token(path, token, bare=False)
            for token in facts.bare_path_tokens:
                self._resolve_path_token(path, token, bare=True)
            if unbounded:
                self.unbounded[path] = unbounded
        self._collect_plugins()
        self._link_conftests()

    def _resolve_prefix(self, path: str, prefix: str) -> bool:
        """Link every module whose dotted name starts with ``prefix``; False if none."""
        package = prefix.rpartition(".")[0]
        found = False
        for root in self._roots_for(path):
            base = (f"{root}/" if root else "") + prefix.replace(".", "/")
            hits = self._files_under(base)
            if package:
                files, inits, _ = self._module_files(package, [root])
                hits += [*files, *inits]
            found = found or bool(hits)
            self._link(path, hits, "mention")
        return found

    def _resolve_file_load(self, path: str, spelling: str) -> bool:
        """Edge to a file loaded by path (``spec_from_file_location`` / ``run_path``)."""
        resolved = self.resolve_spelling(path, spelling)
        if resolved is None:
            return False
        for target in resolved:  # an untracked path holds no first-party file
            if target.endswith("*"):
                self._link(path, self._files_under(target[:-1]), "load")
                continue
            main = f"{target}/__main__.py" if target else "__main__.py"
            self._link(path, [c for c in (target, main) if c in self.py], "load")
        return True

    def _files_under(self, prefix: str) -> list[str]:
        """Every tracked ``.py`` whose path starts with ``prefix``."""
        start = bisect.bisect_left(self._sorted_py, prefix)
        return list(itertools.takewhile(lambda c: c.startswith(prefix), itertools.islice(self._sorted_py, start, None)))

    def _collect_plugins(self) -> None:
        for conftest in self.conftests:
            for name in self.facts[conftest].plugins:
                files, inits, _ = self._module_files(name, self._roots_for(conftest))
                self.plugin_modules["conftest"].update(files | inits)
        for name in self.config.plugin_names:
            files, inits, _ = self._module_files(name, self.roots)
            self.plugin_modules["config"].update(files | inits)

    def _link_conftests(self) -> None:
        """Every test collects the conftests on its directory chain.

        Kept out of ``rev`` so ``reverse_closure`` reports import relations only
        unless ``scoped=True`` asks for the collection scope as well.
        """
        scoped = [c for c in self.conftests if c.startswith(f"{TEST_ROOT}/") or c == "conftest.py"]
        for test in (p for p in self.py if is_test_file(p)):
            chain = _dir_of(test)
            for conftest in scoped:
                cdir = _dir_of(conftest)
                if not cdir or chain == cdir or chain.startswith(cdir + "/"):
                    self.scope_rev[conftest].add(test)

    # -- queries -----------------------------------------------------------

    def forward_closure(self, roots: Iterable[str]) -> set[str]:
        seen: set[str] = set()
        stack = [r for r in roots if r in self.edges]
        while stack:
            node = stack.pop()
            if node in seen:
                continue
            seen.add(node)
            stack.extend(self.edges[node] - seen)
        return seen

    def reverse_closure(self, roots: Iterable[str], *, scoped: bool = False) -> set[str]:
        """Files that (transitively) depend on ``roots``, roots included.

        ``scoped=True`` also follows conftest collection scope (a conftest
        affects every test under its directory).
        """
        seen: set[str] = set()
        stack = [r for r in roots if r in self.rev]
        while stack:
            node = stack.pop()
            if node in seen:
                continue
            seen.add(node)
            stack.extend(self.rev[node] - seen)
            if scoped and node in self.scope_rev:
                stack.extend(self.scope_rev[node] - seen)
        return seen

    def tests(self) -> set[str]:
        return {p for p in self.py if is_test_file(p)}

    def executed(self) -> set[str]:
        """Every file pytest can run: tests, conftests, plugins and what they reach."""
        if self._executed is None:
            roots = self.tests() | set(self.conftests)
            roots |= self.plugin_modules["conftest"] | self.plugin_modules["config"]
            self._executed = self.forward_closure(roots)
        return self._executed

    def explain(self, source: str, target: str) -> list[tuple[str, str, tuple[str, ...]]] | None:
        """Shortest ``source -> target`` chain as ``(from, to, edge kinds)`` hops."""
        prev: dict[str, str | None] = {source: None}
        queue = [source]
        for node in queue:
            if node == target:
                break
            for nxt in sorted(self.edges.get(node, ())):
                if nxt not in prev:
                    prev[nxt] = node
                    queue.append(nxt)
        if target not in prev:
            return None
        hops: list[tuple[str, str, tuple[str, ...]]] = []
        node = target
        while prev[node] is not None:
            parent = prev[node]
            hops.append((parent, node, tuple(sorted(self.edge_kinds[(parent, node)]))))
            node = parent
        return hops[::-1]


# ---------------------------------------------------------------------------
# pytest configuration
# ---------------------------------------------------------------------------


class UnparsableBlob(ValueError):
    """A blob whose contents the index needs but cannot parse."""


def _addopts_plugins(addopts: str | list[str]) -> list[str]:
    tokens = shlex.split(addopts) if isinstance(addopts, str) else [str(t) for t in addopts]
    names: list[str] = []
    for idx, token in enumerate(tokens):
        if token == "-p" and idx + 1 < len(tokens):
            names.append(tokens[idx + 1])
        elif token.startswith("-p") and len(token) > 2 and not token.startswith("--"):
            names.append(token[2:])
    return [n for n in names if not n.startswith("no:")]


def _load_config(files: dict[str, str], blobs: dict[str, bytes]) -> PytestConfig:
    """``pythonpath`` and plugin names from every ``pyproject.toml`` in the tree.

    Only ``pyproject.toml`` is read (this repo has no pytest.ini / tox.ini /
    setup.cfg). ``pythonpath`` and ``addopts`` come from the root file;
    ``pytest11`` entry points from any of them. Every other ``pyproject.toml``
    is an installable package: its ``packages.find`` ``where`` (else ``src``
    when present, else its own directory) is an import root, because CI
    installs such packages from the checkout.
    """
    pythonpath: list[str] = []
    plugins: list[str] = []
    package_roots: list[str] = []
    for path in sorted(files):
        if path.rpartition("/")[2] != "pyproject.toml":
            continue
        try:
            data = tomllib.loads(blobs[files[path]].decode("utf-8"))
        except (tomllib.TOMLDecodeError, UnicodeDecodeError) as exc:
            raise UnparsableBlob(path) from exc
        if path == "pyproject.toml":
            ini = data.get("tool", {}).get("pytest", {}).get("ini_options", {})
            raw_path = ini.get("pythonpath", [])
            pythonpath += [raw_path] if isinstance(raw_path, str) else [str(x) for x in raw_path]
            plugins += _addopts_plugins(ini.get("addopts", ""))
        else:
            package_roots += _package_roots(path.rpartition("/")[0], data, files)
        entry_points = data.get("project", {}).get("entry-points", {}).get("pytest11", {})
        plugins += [str(value).partition(":")[0] for value in entry_points.values()]
    return PytestConfig(
        tuple(dict.fromkeys(pythonpath)), tuple(dict.fromkeys(plugins)), tuple(dict.fromkeys(package_roots))
    )


def _package_roots(directory: str, data: dict[str, object], files: dict[str, str]) -> list[str]:
    setuptools = data.get("tool", {}).get("setuptools", {})  # type: ignore[union-attr]
    find = setuptools.get("packages", {}) if isinstance(setuptools, dict) else {}
    where = find.get("find", {}).get("where") if isinstance(find, dict) else None
    if isinstance(where, str):
        where = [where]
    if not where:
        package_dir = setuptools.get("package-dir", {}) if isinstance(setuptools, dict) else {}
        where = [package_dir[""]] if isinstance(package_dir, dict) and "" in package_dir else None
    if not where:
        src = f"{directory}/src/"
        where = ["src"] if any(p.startswith(src) for p in files) else ["."]
    return [posixpath.normpath(f"{directory}/{w}") for w in where]


# ---------------------------------------------------------------------------
# public API
# ---------------------------------------------------------------------------


def _load_tree(repo: RepoPath, tree: str) -> tuple[dict[str, str], dict[str, bytes]]:
    files = list_tree(repo, tree)
    wanted = [oid for path, oid in files.items() if path.endswith(".py") or path.rpartition("/")[2] == "pyproject.toml"]
    return files, read_blobs(repo, wanted)


def build_index(repo: RepoPath, tree: str) -> ImportGraph:
    """Build the import graph of ``tree`` (one ``ls-tree``, one ``cat-file``)."""
    files, blobs = _load_tree(repo, tree)
    return ImportGraph(files, blobs, _load_config(files, blobs))


def _norm(path: str) -> str:
    text = path.strip().replace("\\", "/")
    while text.startswith("./"):
        text = text[2:]
    return text


def _full(reason: Reason, detail: str) -> Selection:
    return Selection(full=True, reason=reason, detail=detail)


def _first(paths: Iterable[str], limit: int = 3) -> str:
    return ", ".join(sorted(paths)[:limit])


def _unbounded_importers(graph: ImportGraph, dynamic: DynamicPolicy) -> list[str]:
    """Files pytest can run whose own evidence does not bound what they load.

    Bounding is per call: an unrelated literal elsewhere in the file or in
    anything it imports never bounds a computed name. ``strict`` also counts
    literal-prefix names.
    """
    executed = graph.executed()
    candidates = set(graph.unbounded) | (graph.prefix_importers if dynamic == "strict" else set())
    return sorted(candidates & executed)


def _unbounded_detail(graph: ImportGraph, importer: str) -> str:
    return f"{importer}: {(graph.unbounded.get(importer) or ['literal-prefix module name (strict)'])[0]}"


def _global_trigger(graph: ImportGraph, nodes: set[str], dynamic: DynamicPolicy) -> Selection | None:
    """FULL reasons that do not depend on which tests import the change."""
    root_conftests = [c for c in graph.conftests if c in ("conftest.py", f"{TEST_ROOT}/conftest.py")]
    foreign = [c for c in graph.conftests if c not in root_conftests and not c.startswith(f"{TEST_ROOT}/")]
    plugins = graph.plugin_modules["conftest"] | graph.plugin_modules["config"]
    for reason, roots in (
        (Reason.CONFTEST_REACHABLE, root_conftests),
        (Reason.CONFTEST_SCOPE_UNKNOWN, foreign),
        (Reason.PYTEST_PLUGIN, plugins),
    ):
        hit = nodes & graph.forward_closure(roots)
        if hit:
            return _full(reason, _first(hit))
    unbounded = _unbounded_importers(graph, dynamic)
    if dynamic == "dependents":
        # An unbounded importer every test runs (root conftest or plugin reach)
        # has every test as a dependent.
        unbounded = sorted(set(unbounded) & graph.forward_closure([*root_conftests, *foreign, *plugins]))
    if unbounded:
        return _full(Reason.UNBOUNDED_DYNAMIC_IMPORT, _unbounded_detail(graph, unbounded[0]))
    executed = graph.executed()
    for amb in graph.ambiguities:
        if amb.importer in executed and nodes & set(amb.candidates):
            return _full(Reason.AMBIGUOUS_RESOLUTION, f"{amb.importer} imports {amb.name}: {', '.join(amb.candidates)}")
    return None


def select_tests(
    repo: RepoPath,
    head: str,
    changed: Iterable[str],
    base: str | None = None,
    *,
    dynamic: DynamicPolicy = "bounded",
) -> Selection:
    """Select the test files that can observe ``changed`` at ``head``.

    ``base`` is the tree the changed list was computed against; it is required
    to rebuild edges of deleted or renamed-away files and, when given, is used
    to prove the changed list is complete. Pass BOTH sides of a rename (for
    example ``git diff --name-only --no-renames``).

    ``dynamic`` sets how an unbounded file (see ``UNBOUNDED_DYNAMIC_IMPORT``)
    that pytest can run is treated:

    * ``"bounded"`` (default): ``UNBOUNDED_DYNAMIC_IMPORT`` for every change. A
      computed module name is bounded only by its own literal prefix
      (``f"pkg.plugins.{name}"``), which links every module under it.
    * ``"strict"``: literal-prefix names count as unbounded as well.
    * ``"dependents"``: every test that reaches an unbounded file is always
      selected (only those tests can load its unknown target) instead of
      returning FULL; FULL when every test reaches it (root conftest or
      plugin reach).
    """
    changed_paths = sorted({_norm(p) for p in changed if _norm(p)})
    if not changed_paths:
        return _full(Reason.NO_CHANGED_PATHS, "empty changed list")
    non_py = [p for p in changed_paths if not p.endswith(".py")]
    if non_py:
        return _full(Reason.NON_PYTHON_CHANGE, _first(non_py))
    try:
        return _select(repo, head, changed_paths, base, dynamic)
    except GitError as exc:
        return _full(Reason.GIT_ERROR, str(exc))
    except UnparsableBlob as exc:
        return _full(Reason.UNPARSABLE_BLOB, str(exc))


def _select(repo: RepoPath, head: str, changed: list[str], base: str | None, dynamic: DynamicPolicy) -> Selection:
    files, blobs = _load_tree(repo, head)
    base_files: dict[str, str] = list_tree(repo, base) if base is not None else {}
    if base is not None:
        differing = {p for p in files.keys() | base_files.keys() if files.get(p) != base_files.get(p)}
        missing = differing - set(changed)
        if missing:
            return _full(Reason.CHANGED_SET_INCOMPLETE, _first(missing))
    present = [p for p in changed if p in files]
    deleted = [p for p in changed if p not in files]
    for path in present:
        try:
            ast.parse(blobs[files[path]])
        except (SyntaxError, ValueError, RecursionError, MemoryError):
            return _full(Reason.UNPARSABLE_BLOB, path)
    if deleted and (base is None or any(p not in base_files for p in deleted)):
        return _full(Reason.DELETION_UNRECOVERABLE, _first(deleted))

    graph = ImportGraph(files, blobs, _load_config(files, blobs))
    trigger = _global_trigger(graph, set(present), dynamic)
    if trigger is not None:
        return trigger
    selected = {p for p in present if is_test_file(p)}
    reach = graph.reverse_closure(present, scoped=True)
    selected |= reach & graph.tests()
    if dynamic == "dependents":
        for importer in _unbounded_importers(graph, dynamic):
            selected |= graph.reverse_closure([importer], scoped=True) & graph.tests()
    reached_by: dict[str, bool] = {}
    for path in present:
        others = graph.reverse_closure([path]) - {path}
        reached_by[path] = is_test_file(path) or bool(others & graph.tests())

    if deleted:
        assert base is not None
        try:
            base_graph = build_index(repo, base)
        except (GitError, UnparsableBlob) as exc:
            return _full(Reason.DELETION_UNRECOVERABLE, str(exc))
        trigger = _global_trigger(base_graph, set(deleted), dynamic)
        if trigger is not None:
            return trigger
        old_reach = base_graph.reverse_closure(deleted, scoped=True) & base_graph.tests()
        selected |= {t for t in old_reach if t in files}
        for path in deleted:
            others = base_graph.reverse_closure([path]) - {path}
            reached_by[path] = bool(others & base_graph.tests())
    unreached = tuple(sorted(p for p, ok in reached_by.items() if not ok))
    return Selection(full=False, tests=tuple(sorted(selected)), unreached=unreached)
