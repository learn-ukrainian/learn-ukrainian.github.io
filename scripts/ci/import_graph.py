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
  f-string or concatenated dotted prefixes, which reach every module under the
  prefix), ``init`` (ancestor ``__init__.py`` initializers, run first by any
  submodule import) and ``mention`` (a string literal naming a first-party
  path such as ``scripts/x.py`` or ``root / "scripts" / "x.py"``, or a dotted
  module such as ``scripts.x.y`` / ``python -m scripts.x`` /
  ``monkeypatch.setattr("scripts.x.y", ...)``; comments are ignored, and a
  non-test file that names a test path is not an edge).
* One file is one node under several runtime identities. ``pythonpath`` from
  ``pyproject.toml`` plus ``scripts`` are flat import roots (``import
  delegate`` and ``import scripts.delegate`` reach the same file), and each
  file also resolves against its own directory, its pytest ``rootdir``
  insertion directory and any constant directory it puts on ``sys.path``.
  Within one root a package directory shadows a same-named module.
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
``UNBOUNDED_DYNAMIC_IMPORT``  a file that a test can reach calls
                              ``import_module`` / ``__import__`` /
                              ``run_module`` with a computed name and no
                              first-party module or path literal is reachable
                              from it (``dynamic="strict"``: any computed
                              name), so the change could be its target.
                              ``dynamic="dependents"`` selects the tests that
                              reach that file instead of returning FULL.
``AMBIGUOUS_RESOLUTION``      an import that resolves to more than one distinct
                              first-party file involves a changed file.

Known residuals (not modelled, documented for the caller):
``PYTEST_ADDOPTS`` / CLI ``-p`` flags outside ``pyproject.toml``;
``pytest.ini`` / ``tox.ini`` / ``setup.cfg`` (absent here); installed
third-party ``pytest11`` plugins; a module named only inside a non-Python data
file and loaded through a computed name (the data file changing is FULL, the
loaded ``.py`` changing is covered only by the unbounded-dynamic rule);
runtime-supplied file paths (``spec_from_file_location`` / ``runpy.run_path``
with a non-literal path are data, not imports); an aliased loader
(``load = importlib.import_module; load(name)``); ``pytest_plugins`` declared
in a non-conftest test module is an ordinary import edge (the plugin is
registered exactly when that module is collected). The caller must treat an
empty ``tests`` with ``unreached`` paths as "no test imports this change",
not as "run nothing".
"""

from __future__ import annotations

import ast
import enum
import os
import re
import shlex
import subprocess
import tomllib
from collections import defaultdict
from collections.abc import Iterable, Sequence
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

_PREFIX_STMT_RE = re.compile(
    rb"""[ \t]*(?:[rRbBfFuU]{0,2}(?:\"\"\"|'''|\"|'))?[ \t]*(?:from[ \t]+([.\w]+)[ \t]+)?$"""
)
_INLINE_FROM_RE = re.compile(rb"(?:^|[:;])[ \t]*from[ \t]+([.\w]+)[ \t]+$")
_ITEM_RE = re.compile(r"\s*(\*|[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*)(?:\s+as\s+[A-Za-z_]\w*)?\s*")
_QUOTED_DOTTED_RE = re.compile(rb"""["']([A-Za-z_]\w*(?:\.[A-Za-z_]\w*)+)""")
_DASH_M_RE = re.compile(rb"-m[ \t]+([A-Za-z_][\w.]*)")
_PY_TOKEN_END_RE = re.compile(rb"\.py\b")
_PATH_CHAR = frozenset(b"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_./-")
# Data suffixes: "config.yaml" is not the dotted module "config" + attribute "yaml".
_DATA_SUFFIXES = frozenset(
    ("json", "yaml", "yml", "md", "txt", "db", "sqlite", "csv", "toml", "html", "js", "ts", "sh", "log", "cfg", "ini",
     "lock", "png", "svg", "jsonl", "tsv", "xml")
)
_IGNORED_BARE_NAMES = frozenset({"__init__.py", "conftest.py", "__main__.py", "setup.py"})
_WORD_BYTES = frozenset(b"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_")
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
    # Directory spellings passed to sys.path.insert/append/syspath_prepend.
    syspath: set[str] = field(default_factory=set)


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
    while extra < _MAX_CONTINUATION_LINES and end < len(data) and (
        stmt.rstrip().endswith(b"\\") or stmt.count(b"(") > stmt.count(b")")
    ):
        nxt = data.find(b"\n", end + 1)
        if nxt < 0:
            nxt = len(data)
        stmt += b"\n" + data[end + 1 : nxt]
        end = nxt
        extra += 1
    return stmt.decode("utf-8", "replace")


def _balanced_call_args(data: bytes, open_paren: int) -> str | None:
    depth = 0
    limit = min(len(data), open_paren + 2000)
    for idx in range(open_paren, limit):
        ch = data[idx]
        if ch == 0x28:  # (
            depth += 1
        elif ch == 0x29:  # )
            depth -= 1
            if depth == 0:
                return data[open_paren + 1 : idx].decode("utf-8", "replace")
    return None


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


def _handle_dynamic(kind: str, args_text: str | None, facts: FileFacts, line: int) -> None:
    """Classify one dynamic-import call as literal, prefix-bounded or unbounded.

    Loading a *file* (``spec_from_file_location``, ``runpy.run_path``) is not
    scanned: a first-party path is an edge only when spelled as a literal (the
    path-token rule) and a runtime-supplied path is data, not an import.
    """
    if args_text is None:
        facts.unbounded.append(f"{kind}@{line}")
        return
    try:
        call = ast.parse(f"f({args_text})", mode="eval").body
    except SyntaxError:
        facts.unbounded.append(f"{kind}@{line}")
        return
    arg = call.args[0] if isinstance(call, ast.Call) and call.args else None
    if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
        facts.dyn_literals.append(arg.value)
        return
    prefix = _dotted_prefix(arg) if arg is not None else None
    if prefix and re.fullmatch(r"[A-Za-z_][\w.]*\.", prefix):
        facts.dyn_prefixes.append(prefix)
        return
    facts.unbounded.append(f"{kind}@{line}")


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
        line = data.count(b"\n", 0, idx) + 1 if (nxt == b"_" or prev == b"_") else 0
        if nxt == b"_" and data[idx : idx + 13] == b"import_module" and prev[0] not in _WORD_BYTES:
            _dynamic_hit(data, idx + 13, "import_module", facts, line)
            continue
        if prev == b"_" and data[idx - 2 : idx] == b"__" and data[idx + 6 : idx + 8] == b"__":
            _dynamic_hit(data, idx + 8, "__import__", facts, line)
            continue
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
    pos = 0
    while True:  # runpy.run_module("pkg.mod") names a module like import_module
        idx = find(b"run_module", pos)
        if idx < 0:
            break
        pos = idx + 10
        if data[pos : pos + 1] == b"(" and data[idx - 1 : idx] in (b".", b" ", b"\t", b"("):
            _handle_dynamic("run_module", _balanced_call_args(data, pos), facts, data.count(b"\n", 0, idx) + 1)
    _scan_syspath(data, facts)
    _scan_mentions(data, facts)
    _scan_pytest_plugins(data, facts)
    return facts


def _scan_syspath(data: bytes, facts: FileFacts) -> None:
    """Constant directory spellings inside ``sys.path`` insertions (flat identity)."""
    for token in (b"sys.path.insert", b"sys.path.append", b"syspath_prepend"):
        pos = data.find(token)
        while pos >= 0:
            after = pos + len(token)
            if data[after : after + 1] == b"(":
                text = _balanced_call_args(data, after)
                if text is not None:
                    try:
                        call = ast.parse(f"f({text})", mode="eval").body
                    except SyntaxError:
                        call = None
                    consts = [
                        n.value
                        for n in ast.walk(call)
                        if isinstance(n, ast.Constant) and isinstance(n.value, str)
                    ] if call is not None else []
                    facts.syspath.update(c.strip("/") for c in consts if c.strip("/"))
                    if len(consts) > 1:
                        facts.syspath.add("/".join(c.strip("/") for c in consts))
            pos = data.find(token, after)


def _dynamic_hit(data: bytes, after: int, kind: str, facts: FileFacts, line: int) -> None:
    """Handle a ``import_module`` / ``__import__`` call.

    A bare reference (``builtins.__import__``, ``from importlib import
    import_module``, a quoted mention) is not a call; aliasing the loader and
    calling it later is an accepted residual.
    """
    if data[after : after + 1] == b"(":
        _handle_dynamic(kind, _balanced_call_args(data, after), facts, line)


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


def _scan_pytest_plugins(data: bytes, facts: FileFacts) -> None:
    idx = data.find(b"pytest_plugins")
    while idx >= 0:
        ls = data.rfind(b"\n", 0, idx) + 1
        if data[ls:idx].strip() == b"":
            end = data.find(b"\n", idx)
            stmt = data[idx : end if end >= 0 else len(data)]
            eq = stmt.find(b"=")
            if eq > 0:
                text = _statement_text(data, idx)
                for name in re.findall(r"""["']([A-Za-z_][\w.]*)["']""", text.partition("=")[2]):
                    facts.plugins.append(name)
        idx = data.find(b"pytest_plugins", idx + 14)


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
        self.roots: tuple[str, ...] = tuple(dict.fromkeys(["", *DEFAULT_FLAT_ROOTS, *config.pythonpath]))
        self.facts: dict[str, FileFacts] = {p: extract_facts(blobs[files[p]]) for p in sorted(self.py)}
        self.edges: dict[str, set[str]] = {p: set() for p in self.py}
        self.rev: dict[str, set[str]] = {p: set() for p in self.py}
        self.ambiguities: list[Ambiguity] = []
        self.unbounded: dict[str, list[str]] = {}
        self.scope_rev: dict[str, set[str]] = defaultdict(set)
        self.mention_edges: dict[str, int] = defaultdict(int)
        self.edge_kinds: dict[tuple[str, str], set[str]] = defaultdict(set)
        self.conftests = sorted(p for p in self.py if p.rsplit("/", 1)[-1] == "conftest.py")
        self.plugin_modules: dict[str, set[str]] = {"conftest": set(), "config": set()}
        self._build()

    # -- resolution --------------------------------------------------------

    def _roots_for(self, path: str) -> tuple[str, ...]:
        directory = _dir_of(path)
        basedir = directory
        while basedir and f"{basedir}/__init__.py" in self.py:
            basedir = _dir_of(basedir)
        extra = []
        for spelling in self.facts[path].syspath:
            if spelling in self.dirs:
                extra.append(spelling)
        return tuple(dict.fromkeys([*self.roots, directory, basedir, *extra]))

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
        """Add ``source -> target`` edges of ``kind`` (import, init or mention)."""
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
                if kind == "mention":
                    self.mention_edges[source] += 1

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
            for level, module, names in facts.imports:
                self._resolve_import(path, level, module, names)
            for name in facts.dyn_literals:
                level = len(name) - len(name.lstrip("."))
                self._resolve_import(path, level, name.lstrip("."), ())
                self.mention_edges[path] += 1
            for prefix in facts.dyn_prefixes:
                self._resolve_prefix(path, prefix)
            for token in facts.dotted_tokens:
                self._resolve_dotted_prefix_tokens(path, token)
            for token in facts.path_tokens:
                self._resolve_path_token(path, token, bare=False)
            for token in facts.bare_path_tokens:
                self._resolve_path_token(path, token, bare=True)
            if facts.unbounded:
                self.unbounded[path] = list(facts.unbounded)
        self._collect_plugins()
        self._link_conftests()

    def _resolve_prefix(self, path: str, prefix: str) -> None:
        rel = prefix.rstrip(".").replace(".", "/")
        for root in self._roots_for(path):
            base = f"{root}/{rel}/" if root else f"{rel}/"
            self._link(path, (c for c in self.py if c.startswith(base)), "mention")
            files, inits, _ = self._module_files(prefix.rstrip("."), [root])
            self._link(path, files | inits, "mention")

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
    ``pytest11`` entry points from any of them.
    """
    pythonpath: list[str] = []
    plugins: list[str] = []
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
        entry_points = data.get("project", {}).get("entry-points", {}).get("pytest11", {})
        plugins += [str(value).partition(":")[0] for value in entry_points.values()]
    return PytestConfig(tuple(dict.fromkeys(pythonpath)), tuple(dict.fromkeys(plugins)))


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
    """Files a test can reach that import a computed name nothing bounds."""
    tested = graph.forward_closure(graph.tests())
    out = []
    for importer in sorted(graph.unbounded):
        if importer not in tested:
            continue
        bounded = any(graph.mention_edges.get(n, 0) for n in graph.forward_closure([importer]))
        if dynamic == "strict" or not bounded:
            out.append(importer)
    return out


def _global_trigger(graph: ImportGraph, nodes: set[str], dynamic: DynamicPolicy) -> Selection | None:
    """FULL reasons that do not depend on which tests import the change."""
    root_conftests = [c for c in graph.conftests if c in ("conftest.py", f"{TEST_ROOT}/conftest.py")]
    hit = nodes & graph.forward_closure(root_conftests)
    if hit:
        return _full(Reason.CONFTEST_REACHABLE, _first(hit))
    foreign = [c for c in graph.conftests if c not in root_conftests and not c.startswith(f"{TEST_ROOT}/")]
    hit = nodes & graph.forward_closure(foreign)
    if hit:
        return _full(Reason.CONFTEST_SCOPE_UNKNOWN, _first(hit))
    plugins = graph.plugin_modules["conftest"] | graph.plugin_modules["config"]
    hit = nodes & graph.forward_closure(plugins)
    if hit:
        return _full(Reason.PYTEST_PLUGIN, _first(hit))
    if dynamic != "dependents":
        unbounded = _unbounded_importers(graph, dynamic)
        if unbounded:
            return _full(Reason.UNBOUNDED_DYNAMIC_IMPORT, f"{unbounded[0]}: {graph.unbounded[unbounded[0]][0]}")
    tested = graph.forward_closure(graph.tests())
    for amb in graph.ambiguities:
        if amb.importer in tested and nodes & set(amb.candidates):
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

    ``dynamic`` sets how a computed ``import_module`` / ``__import__`` /
    ``run_module`` name is treated in a file a test can reach:

    * ``"bounded"`` (default): bounded when some file reachable from it carries
      first-party module/path literals (registry tables, candidate tuples;
      those literals are already edges), otherwise ``UNBOUNDED_DYNAMIC_IMPORT``.
    * ``"strict"``: every such computed name is ``UNBOUNDED_DYNAMIC_IMPORT``.
    * ``"dependents"``: like ``"bounded"``, but a name nothing bounds selects
      every test that reaches the importing file (they alone can load the
      unknown target) instead of returning FULL.
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
