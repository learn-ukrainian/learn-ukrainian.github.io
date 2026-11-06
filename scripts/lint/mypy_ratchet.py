#!/usr/bin/env python3
"""Ratchet mypy on scripts/: new errors fail, and the baseline only shrinks (#12642).

Identity is ``(path, error code, message)``. Line and column are not part of
it, so inserting a line above an existing error does not churn the baseline.
A message that mypy no longer reports is a stale baseline entry and fails.
Union member order, compact ``Literal`` member order, and TypedDict key-list
order are not part of the identity: mypy does not keep them stable. A pipe
inside a quoted literal stays part of the value. The run matches CI: wheels
the CI env does
not install are skipped, and the content ``wiki/`` tree is not a namespace
package on the module path.
Once ``origin/main`` contains the baseline, the committed multiset may only
shrink. Before that first landing, the baseline has no predecessor; it must
still equal the mypy census exactly, so entries mypy does not report fail.
Where the machinery package directory is not ``scripts`` (after the machinery
move), the module slot of two exact baseline message forms is respelled with
the pinned rename map, which that checkout must carry at
packaging/machinery-move/rename-map.json with a verified .sha256 beside it.

Examples:
  .venv/bin/python -m scripts.lint.mypy_ratchet
  .venv/bin/python -m scripts.lint.mypy_ratchet scripts/lint/mypy_ratchet.py
  .venv/bin/python -m scripts.lint.mypy_ratchet --write-baseline

Outputs: one violation per new or stale identity on stderr, or a one-line
pass message on stdout. ``--write-baseline`` rewrites the baseline JSON.
Exit codes: 0 pass or baseline written; 1 a new error, a stale entry, growth,
or mypy could not run.
Related: #12642, scripts/hygiene/lint_source_db_writable_connects.py.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
import re
import subprocess
import sys
import tomllib
from collections import Counter
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path, PurePosixPath


def _package_dir() -> Path:
    # Unresolved package directory (design-v1 amendment 1). Never __package__.
    return Path(os.path.abspath(__file__)).parents[1]


def _mp(relative: str) -> str:
    return f"{_package_dir().name}/{relative}"


REPO_ROOT = Path(__file__).resolve().parents[2]
BASELINE_PATH = Path(__file__).with_name("mypy_baseline.json")
SCHEMA = "mypy-ratchet-baseline.v1"
DEFAULT_TARGET = _package_dir().name
MYPY_TIMEOUT_SECONDS = 600
# python-ci-env installs the lock without these wheels. Skipping them makes a
# laptop venv that has them report the same errors as CI.
_CI_ABSENT_MODULES = (
    "torch",
    "torch.*",
    "torchvision",
    "torchvision.*",
    "open_clip",
    "stanza",
)
# Top-level content trees with no Python. On a full checkout mypy treats them
# as namespace packages, so `from wiki import name` (the scripts/wiki fallback)
# becomes an attr-defined error. A sparse checkout that omits them does not.
# The search root below leaves them out so both checkouts see the same census.
_CONTENT_NAMESPACE_ROOTS = frozenset({"wiki"})
_MYPY_KEYS = (
    "python_version",
    "warn_return_any",
    "warn_unused_configs",
    "ignore_missing_imports",
    "exclude",
)
_GIT_TIMEOUT_SECONDS = 30
_SHRINK_REFS = ("HEAD", "HEAD^", "origin/main")

# path:line:col: error: message  [code]  — column is optional.
_REPORT = re.compile(
    r"^(?P<path>.+?):(?P<line>\d+)(?::(?P<col>\d+))?: (?P<sev>error|note): "
    r"(?P<msg>.*?)(?:  \[(?P<code>[^\]]+)\])?\s*$"
)


@dataclass(frozen=True, order=True)
class MypyError:
    """One mypy error. Line and column are intentionally absent."""

    path: str
    code: str
    message: str

    @property
    def identity(self) -> tuple[str, str, str]:
        return (self.path, self.code, self.message)


def _sort_union_runs(text: str) -> str:
    """Sort each ``A | B`` run. A depth-0 comma ends the run (``str | None, ...``)."""

    tokens: list[tuple[str, str]] = []
    buf: list[str] = []
    stack: list[str] = []
    closing = {")": "(", "]": "[", "}": "{"}

    def flush() -> None:
        if buf:
            tokens.append(("content", "".join(buf)))
            buf.clear()

    i = 0
    quote = ""
    while i < len(text):
        ch = text[i]
        if quote:
            buf.append(ch)
            if ch == "\\" and i + 1 < len(text):
                buf.append(text[i + 1])
                i += 2
                continue
            if ch == quote:
                quote = ""
            i += 1
            continue
        if not stack and text.startswith(" | ", i):
            flush()
            tokens.append(("union", " | "))
            i += 3
            continue
        if not stack and ch == ",":
            flush()
            tokens.append(("comma", ","))
            i += 1
            continue
        buf.append(ch)
        if ch in "\"'":
            quote = ch
        elif ch in "([{":
            stack.append(ch)
        elif ch in closing and stack and stack[-1] == closing[ch]:
            stack.pop()
        i += 1
    flush()
    out: list[str] = []
    run: list[str] = []
    pending = False

    def flush_run() -> None:
        if not run:
            return
        if len(run) == 1:
            out.append(run[0])
        else:
            lead = run[0][: len(run[0]) - len(run[0].lstrip())]
            out.append(lead + " | ".join(sorted(part.strip() for part in run if part.strip())))
        run.clear()

    for kind, token in tokens:
        if kind == "comma":
            flush_run()
            pending = False
            out.append(token)
            continue
        if kind == "union":
            pending = True
            continue
        if pending:
            run.append(token)
            pending = False
        else:
            flush_run()
            run.append(token)
    flush_run()
    return "".join(out)


def _scan_quoted(text: str, start: int) -> int:
    """Return the index just past the quoted span that opens at ``start``."""

    quote = text[start]
    j = start + 1
    while j < len(text):
        if text[j] == "\\" and j + 1 < len(text):
            j += 2
            continue
        if text[j] == quote:
            return j + 1
        j += 1
    return len(text)


def _matching_bracket(text: str, start: int) -> int:
    """Return the index just past the bracket that opens at ``start``."""

    opens = {"(": ")", "[": "]", "{": "}"}
    stack = [opens[text[start]]]
    quote = ""
    j = start + 1
    while j < len(text) and stack:
        ch = text[j]
        if quote:
            if ch == "\\" and j + 1 < len(text):
                j += 2
                continue
            if ch == quote:
                quote = ""
            j += 1
            continue
        if ch in "\"'":
            quote = ch
        elif ch in opens:
            stack.append(opens[ch])
        elif ch == stack[-1]:
            stack.pop()
        j += 1
    return j


def _split_top_commas(text: str) -> list[str]:
    """Split on commas that are not inside quotes or brackets."""

    parts: list[str] = []
    buf: list[str] = []
    stack: list[str] = []
    opens = {"(": ")", "[": "]", "{": "}"}
    closing = {")": "(", "]": "[", "}": "{"}
    quote = ""
    i = 0
    while i < len(text):
        ch = text[i]
        if quote:
            buf.append(ch)
            if ch == "\\" and i + 1 < len(text):
                buf.append(text[i + 1])
                i += 2
                continue
            if ch == quote:
                quote = ""
            i += 1
            continue
        if ch in "\"'":
            quote = ch
        elif ch in opens:
            stack.append(ch)
        elif ch in closing and stack and stack[-1] == closing[ch]:
            stack.pop()
        elif ch == "," and not stack:
            parts.append("".join(buf).strip())
            buf = []
            i += 1
            continue
        buf.append(ch)
        i += 1
    tail = "".join(buf).strip()
    if tail:
        parts.append(tail)
    return parts


def _sort_literal_items(inner: str) -> str:
    """Order compact ``Literal`` members. mypy keeps source union order."""

    return ", ".join(sorted(_split_top_commas(inner)))


def _sort_unions(text: str) -> str:
    """Order ``A | B`` members. mypy does not keep that order stable.

    Single quotes are literal values (``'b | a'``) and stay byte for byte.
    Double quotes wrap a type, so unions inside them are ordered. Brackets
    are walked so ``dict[str, int | str]`` is ordered too.
    """

    rebuilt: list[str] = []
    i = 0
    while i < len(text):
        if text[i] == "'":
            j = _scan_quoted(text, i)
            rebuilt.append(text[i:j])
            i = j
            continue
        if text[i] == '"':
            j = _scan_quoted(text, i)
            rebuilt.append('"' + _sort_unions(text[i + 1 : j - 1]) + '"')
            i = j
            continue
        if text[i] in "([{":
            j = _matching_bracket(text, i)
            inner = text[i + 1 : j - 1]
            closer = text[j - 1 : j]
            prefix = "".join(rebuilt)
            literal = prefix.endswith("Literal") and (
                len(prefix) == len("Literal")
                or not (prefix[-len("Literal") - 1].isalnum() or prefix[-len("Literal") - 1] == "_")
            )
            if text[i] == "[" and literal:
                rebuilt.append("[" + _sort_literal_items(inner) + closer)
            else:
                rebuilt.append(text[i] + _sort_unions(inner) + closer)
            i = j
            continue
        rebuilt.append(text[i])
        i += 1
    return _sort_union_runs("".join(rebuilt))


# Key lists follow TypedDict declaration order. The names are data, not types.
_UNORDERED_KEYS = re.compile(
    r"(?P<prefix>Missing keys|Extra keys|Non-required keys|expected one of|TypedDict keys)"
    r" \((?P<body>[^)]*)\)"
)
_KEY_SLOT = re.compile("\ue000(\\d+)\ue001")
# mypy names the line of an earlier definition inside some messages
# ("already defined on line 12"). Lines are not part of the identity.
_LINE_REFERENCE = re.compile(r" on line \d+\b")


def _sort_name_list(body: str) -> str:
    ellipsis = body.rstrip().endswith("...")
    names = re.findall(r'"((?:[^"\\]|\\.)*)"', body)
    inner = ", ".join(f'"{name}"' for name in sorted(names))
    if ellipsis:
        return f"{inner}, ..." if inner else "..."
    return inner


def _normalize_message(message: str) -> str:
    """Drop order that mypy does not keep stable and line references, and nothing else."""

    message = _LINE_REFERENCE.sub("", message)
    slots: list[str] = []

    def protect(match: re.Match[str]) -> str:
        slots.append(f"{match.group('prefix')} ({_sort_name_list(match.group('body'))})")
        return f"\ue000{len(slots) - 1}\ue001"

    ordered = _sort_unions(_UNORDERED_KEYS.sub(protect, message))
    return _KEY_SLOT.sub(lambda slot: slots[int(slot.group(1))], ordered)


# -- Baseline spelling after the machinery move (C-4761) ---------------------
#
# The committed baseline was censused where the machinery package directory is
# ``scripts``. Once the machinery directory has another name, mypy names a moved
# module under it. Exactly two complete diagnostic forms carry such a name in a
# template slot, and only that slot of a baseline message is respelled; every
# other message, and all other text, is compared exactly. mypy output is never
# rewritten. Other mypy forms (``...; maybe "x"?``, explicit-export messages,
# ``Function``/``Module`` "is not valid as a type") stay outside on purpose.

_SOURCE_PACKAGE = "scripts"  # the census spelling, and the pinned rename's old root
_MACHINERY = "machinery"
_PRODUCT = "product"
_AMBIGUOUS = "ambiguous"
_IDENT = r"[A-Za-z_][A-Za-z0-9_]*"
_DOTTED = rf"{_IDENT}(?:\.{_IDENT})*"
# error code -> (complete message, slot kind). A module slot is a whole module;
# a variable slot is a module plus the symbol it defines, and keeps the symbol.
_SLOT_TEMPLATES: dict[str, tuple[re.Pattern[str], str]] = {
    "attr-defined": (
        re.compile(rf'Module "(?P<slot>{_DOTTED})" has no attribute "{_IDENT}"'),
        "module",
    ),
    "valid-type": (
        re.compile(rf'Variable "(?P<slot>{_DOTTED}\.{_IDENT})" is not valid as a type'),
        "variable",
    ),
}
RENAME_MAP = Path("packaging") / "machinery-move" / "rename-map.json"
_DIGEST_LINE = re.compile(rf"(?P<digest>[0-9a-f]{{64}})  {re.escape(RENAME_MAP.name)}\n")


@dataclass(frozen=True)
class _MapModule:
    name: str
    owner: str
    bound_file: str | None  # None for a namespace package


class _RenameMap:
    """The pinned rename's ownership map and its module resolution rules.

    A faithful port of ``OwnershipMap`` and ``module_target`` in the freeze's
    ``rename_python.py``: a slot is respelled only when the rename itself would
    move that module, never by file existence or a longest-prefix guess alone.
    """

    def __init__(self, files: dict[str, str]) -> None:
        self.files = files
        self.modules: dict[str, _MapModule] = {}
        self._owners: dict[str, str | None] = {}
        packages: dict[str, str] = {}
        plain: dict[str, str] = {}
        directories: dict[str, set[str]] = {}
        for path in files:
            parts = PurePosixPath(path).parts
            if not parts or parts[0] != _SOURCE_PACKAGE:
                continue
            for depth in range(1, len(parts)):
                if all(part.isidentifier() for part in parts[:depth]):
                    directories.setdefault(".".join(parts[:depth]), set())
            if not path.endswith(".py"):
                continue
            stem = (*parts[:-1], parts[-1][: -len(".py")])
            if not all(part.isidentifier() for part in stem):
                continue
            for depth in range(1, len(stem)):
                directories[".".join(stem[:depth])].add(path)
            if stem[-1] == "__init__":
                packages[".".join(stem[:-1])] = path
            else:
                plain[".".join(stem)] = path
        names = set(packages) | set(plain) | {name for name, members in directories.items() if members}
        for name in sorted(names):
            bound = packages.get(name) or plain.get(name)
            if bound is not None:
                self.modules[name] = _MapModule(name, files[bound], bound)
            else:
                owners = {files[member] for member in directories[name]}
                owner = owners.pop() if len(owners) == 1 else _AMBIGUOUS
                self.modules[name] = _MapModule(name, owner, None)

    def path_owner(self, path: str) -> str | None:
        if path in self.files:
            return self.files[path]
        if path not in self._owners:
            owners = {owner for key, owner in self.files.items() if key.startswith(path + "/")}
            self._owners[path] = None if not owners else owners.pop() if len(owners) == 1 else _AMBIGUOUS
        return self._owners[path]

    def resolve(self, dotted: str) -> tuple[_MapModule, str] | None:
        """Longest module prefix of a ``scripts`` name and the attribute rest."""

        if dotted != _SOURCE_PACKAGE and not dotted.startswith(_SOURCE_PACKAGE + "."):
            return None
        parts = dotted.split(".")
        for depth in range(len(parts), 0, -1):
            entry = self.modules.get(".".join(parts[:depth]))
            if entry is not None:
                return entry, ".".join(parts[depth:])
        return None

    def target(self, name: str, kind: str) -> str:
        """Owner of a module slot (exact module) or a variable slot (module plus symbol)."""

        resolved = self.resolve(name)
        if resolved is None:
            return "unknown"
        entry, rest = resolved
        if (kind == "module") == bool(rest):
            return "unknown"  # a module slot names no attribute; a variable slot needs one
        if entry.name == _SOURCE_PACKAGE:
            return "unknown" if rest else _AMBIGUOUS
        if rest and entry.bound_file is None:
            return "unknown"  # a namespace package has no attributes
        if not rest:
            main = self.modules.get(f"{entry.name}.__main__")
            if main is not None and main.owner != entry.owner:
                return _AMBIGUOUS
            mixed_dir = entry.bound_file is None or entry.bound_file.endswith("/__init__.py")
            if mixed_dir and self.path_owner(entry.name.replace(".", "/")) == _AMBIGUOUS:
                return _AMBIGUOUS  # a package with files of both owners
        return entry.owner


def _load_rename_map(package_dir: Path) -> _RenameMap:
    """Read and verify the rename map a renamed machinery checkout must carry.

    Contract: ``packaging/machinery-move/rename-map.json``, in the directory
    that holds the machinery package, has the exact bytes of the ownership
    map (``path -> machinery|product``) that the extraction's rename tools
    read; portcheck keeps it as
    ``runs/<sha12>-all/derive/map.json``. Those tools record the SHA-256 of
    the bytes as ``map_sha256`` in their reports (``transform/{py,np,st}.json``).
    ``rename-map.json.sha256`` beside it records that receipt value in
    ``sha256sum`` format, one line: ``<64 lowercase hex>  rename-map.json``.
    Both are installed with the first push. A missing, unreadable, malformed
    or mismatched artifact is an error, never the source layout.
    """

    path = package_dir.parent / RENAME_MAP
    digest_path = path.with_name(path.name + ".sha256")
    prefix = f"rename map {path}"
    try:
        raw = path.read_bytes()
        recorded = digest_path.read_bytes().decode("ascii")
    except (OSError, UnicodeDecodeError) as exc:
        raise ValueError(f"{prefix}: required for machinery package {package_dir.name!r}; unreadable: {exc}") from exc
    line = _DIGEST_LINE.fullmatch(recorded)
    if line is None:
        raise ValueError(f"{digest_path}: expected one line '<sha256>  {RENAME_MAP.name}'")
    actual = hashlib.sha256(raw).hexdigest()
    if actual != line.group("digest"):
        raise ValueError(f"{prefix}: sha256 {actual} does not match the recorded {line.group('digest')}")
    try:
        data = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"{prefix}: not valid JSON: {exc}") from exc
    if not isinstance(data, dict) or not data:
        raise ValueError(f"{prefix}: must be a non-empty JSON object of path -> owner")
    for key, owner in data.items():
        if (
            not key
            or PurePosixPath(key).is_absolute()
            or ".." in PurePosixPath(key).parts
            or key != PurePosixPath(key).as_posix()
        ):
            raise ValueError(f"{prefix}: key is not a normalized relative path: {key!r}")
        if owner not in (_MACHINERY, _PRODUCT):
            raise ValueError(f"{prefix}: {key!r} has owner {owner!r}")
    return _RenameMap(data)


@dataclass(frozen=True)
class _BaselineSpelling:
    """Respell a baseline message into the running layout. Identity in ``scripts``."""

    package: str
    rename_map: _RenameMap | None

    def message(self, code: str, message: str) -> str:
        template = _SLOT_TEMPLATES.get(code)
        if self.rename_map is None or template is None:
            return message
        pattern, kind = template
        match = pattern.fullmatch(message)
        if match is None or self.rename_map.target(match.group("slot"), kind) != _MACHINERY:
            return message
        start, end = match.span("slot")
        return message[:start] + self.package + message[start + len(_SOURCE_PACKAGE) : end] + message[end:]


def _baseline_spelling() -> _BaselineSpelling:
    """The running layout, from this file's unresolved location (amendment 1)."""

    package_dir = _package_dir()
    if package_dir.name == _SOURCE_PACKAGE:
        return _BaselineSpelling(_SOURCE_PACKAGE, None)
    return _BaselineSpelling(package_dir.name, _load_rename_map(package_dir))


def _relative(root: Path, raw: str) -> str | None:
    path = Path(raw)
    if path.is_absolute():
        try:
            path = path.relative_to(root)
        except ValueError:
            return None
    text = path.as_posix()
    if text.startswith("./"):
        text = text[2:]
    if not text or text.startswith("../"):
        return None
    return text


def parse_mypy_stdout(text: str, root: Path) -> tuple[list[MypyError], list[str]]:
    """Parse an error report. Notes are ignored. Non-error junk is returned."""

    errors: list[MypyError] = []
    unparsed: list[str] = []
    for line in text.splitlines():
        if not line.strip():
            continue
        match = _REPORT.match(line)
        if match is None:
            unparsed.append(line)
            continue
        if match.group("sev") != "error":
            continue
        rel = _relative(root, match.group("path"))
        code = match.group("code")
        if rel is None or not code:
            unparsed.append(line)
            continue
        errors.append(MypyError(rel, code, _normalize_message(match.group("msg"))))
    return errors, unparsed


def _covers(path: str, target: str) -> bool:
    return path == target or path.startswith(target.rstrip("/") + "/")


def _in_scope(path: str, targets: Sequence[str]) -> bool:
    return any(_covers(path, target) for target in targets)


def _normalize_targets(root: Path, paths: Sequence[str]) -> list[str]:
    targets: list[str] = []
    for raw in paths:
        rel = _relative(root, raw)
        if rel is None:
            raise ValueError(f"path is outside the tree: {raw}")
        targets.append(rel)
    return targets


def _toml(value: object) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, str):
        return json.dumps(value)
    if isinstance(value, list) and all(isinstance(item, str) for item in value):
        return "[" + ", ".join(json.dumps(item) for item in value) + "]"
    raise ValueError(f"unsupported mypy config value: {value!r}")


def ratchet_config(root: Path) -> Path | None:
    """Point mypy at the repo config plus overrides for wheels CI does not install.

    ``files`` is omitted so the paths passed on the command line are the whole
    check. An unknown ``[tool.mypy]`` key fails closed instead of being dropped.
    """

    pyproject = root / "pyproject.toml"
    if not pyproject.is_file():
        return None
    tool = tomllib.loads(pyproject.read_text(encoding="utf-8")).get("tool", {}).get("mypy", {})
    if not isinstance(tool, dict):
        raise ValueError("pyproject [tool.mypy] is not a table")
    unknown = sorted(set(tool) - set(_MYPY_KEYS) - {"files"})
    if unknown:
        raise ValueError("unhandled [tool.mypy] keys: " + ", ".join(unknown))
    lines = ["[tool.mypy]"]
    for key in _MYPY_KEYS:
        # Unused-section notes have no line number, so a partial pre-commit
        # (a file that never imports the skipped wheels) would fail closed.
        # The flag only adds notes; it does not change type errors.
        if key == "warn_unused_configs":
            lines.append("warn_unused_configs = false")
            continue
        if key in tool:
            lines.append(f"{key} = {_toml(tool[key])}")
    lines.extend([
        "",
        "[[tool.mypy.overrides]]",
        "module = " + _toml(list(_CI_ABSENT_MODULES)),
        'follow_imports = "skip"',
        "ignore_missing_imports = true",
        "",
    ])
    dest = root / ".mypy_cache" / "mypy-ratchet" / "pyproject.toml"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text("\n".join(lines), encoding="utf-8")
    return dest


def search_root(root: Path) -> Path:
    """A cwd whose top level is the repo minus content namespace trees.

    mypy always puts the cwd on the module path and turns a directory without
    ``__init__.py`` into a namespace package. Symlinks keep the cache and the
    sources where they are; ``--cache-dir`` stays the repo ``.mypy_cache``.
    """

    dest = root / ".mypy_cache" / "mypy-ratchet" / "search"
    dest.mkdir(parents=True, exist_ok=True)
    wanted: dict[str, Path] = {}
    for child in root.iterdir():
        if child.name.startswith(".") or child.name in _CONTENT_NAMESPACE_ROOTS:
            continue
        wanted[child.name] = child.resolve()
    for existing in list(dest.iterdir()):
        target = wanted.get(existing.name)
        try:
            current = existing.resolve() if existing.is_symlink() else None
        except OSError:
            current = None
        if target is not None and current == target:
            wanted.pop(existing.name)
            continue
        if existing.is_symlink() or existing.is_file():
            existing.unlink()
    for name, target in wanted.items():
        (dest / name).symlink_to(target)
    return dest


def mypy_command(
    targets: Sequence[str],
    *,
    config_file: Path | None,
    cache_dir: Path,
    incremental: bool,
) -> list[str]:
    """The production mypy invocation. Flags that change the error set stay at
    the existing ``[tool.mypy]`` defaults; ``--platform linux`` matches CI.
    """

    command = [
        sys.executable,
        "-m",
        "mypy",
        "--platform",
        "linux",
        "--show-error-codes",
        "--no-error-summary",
        "--no-color-output",
        "--hide-error-context",
        "--no-pretty",
        "--hide-absolute-path",
        "--follow-imports",
        "normal",
        "--cache-dir",
        str(cache_dir),
    ]
    if config_file is not None:
        command.extend(["--config-file", str(config_file)])
    if incremental:
        command.append("--incremental")
    else:
        command.append("--no-incremental")
    command.extend(targets)
    return command


def collect_errors(
    root: Path,
    targets: Sequence[str],
    *,
    config_file: Path | None = None,
    incremental: bool = True,
) -> tuple[list[MypyError], list[str]]:
    """Run mypy. Fatal runner failures come back as violation strings."""

    existing = [target for target in targets if (root / target).exists()]
    if not existing:
        return [], []
    if config_file is None:
        config_file = ratchet_config(root)
    command = mypy_command(
        existing,
        config_file=config_file,
        cache_dir=root / ".mypy_cache",
        incremental=incremental,
    )
    env = {**os.environ, "MYPY_FORCE_COLOR": "0"}
    # A checkout path or MYPYPATH must not put the content tree back on the path.
    env.pop("PYTHONPATH", None)
    env.pop("MYPYPATH", None)
    try:
        result = subprocess.run(
            command,
            cwd=search_root(root),
            capture_output=True,
            text=True,
            timeout=MYPY_TIMEOUT_SECONDS,
            env=env,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return [], [f"mypy timed out after {MYPY_TIMEOUT_SECONDS}s"]
    if result.returncode not in (0, 1):
        detail = (result.stderr or result.stdout).strip()
        return [], [f"mypy failed ({result.returncode}): {detail}"]
    errors, unparsed = parse_mypy_stdout(result.stdout, root)
    if unparsed:
        return [], [f"mypy report was not parseable: {unparsed[0]}"]
    return [error for error in errors if _in_scope(error.path, targets)], []


def _counts(errors: Iterable[MypyError]) -> Counter[tuple[str, str, str]]:
    return Counter(error.identity for error in errors)


def compare(current: Sequence[MypyError], baseline: Sequence[MypyError]) -> list[str]:
    """New identities fail, and baseline identities mypy no longer reports fail."""

    current_counts = _counts(current)
    baseline_counts = _counts(baseline)
    violations: list[str] = []
    for identity in sorted(set(current_counts) | set(baseline_counts)):
        path, code, message = identity
        extra = current_counts[identity] - baseline_counts[identity]
        if extra > 0:
            suffix = f" x{extra}" if extra > 1 else ""
            violations.append(f"{path}: new {code}{suffix}: {message}")
        missing = baseline_counts[identity] - current_counts[identity]
        if missing > 0:
            suffix = f" x{missing}" if missing > 1 else ""
            violations.append(f"{path}: stale baseline {code}{suffix}: {message}")
    return violations


def _entries_from_rows(rows: object, where: str) -> list[MypyError]:
    if not isinstance(rows, list):
        raise ValueError(f"{where}: entries must be a list")
    spelling = _baseline_spelling()
    entries: list[MypyError] = []
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError(f"{where}: an entry is not an object")
        rel = row.get("path")
        code = row.get("code")
        message = row.get("message")
        if (
            not isinstance(rel, str)
            or not rel
            or not isinstance(code, str)
            or not code
            or not isinstance(message, str)
            or not message
        ):
            raise ValueError(f"{where}: an entry needs path, code, and message")
        if rel.startswith(("/", "\\")) or ".." in Path(rel).parts:
            raise ValueError(f"{where}: entry path is not relative: {rel}")
        entries.append(MypyError(rel, code, _normalize_message(spelling.message(code, message))))
    return entries


def _payload_entries(payload: object, where: str) -> list[MypyError]:
    if not isinstance(payload, dict) or payload.get("schema") != SCHEMA:
        raise ValueError(f"{where}: schema must be {SCHEMA}")
    return _entries_from_rows(payload.get("entries"), where)


def load_entries(path: Path) -> list[MypyError]:
    return _payload_entries(json.loads(path.read_text(encoding="utf-8")), str(path))


def write_baseline(path: Path, entries: Sequence[MypyError]) -> None:
    payload = {
        "schema": SCHEMA,
        "mypy": importlib.metadata.version("mypy"),
        "entries": [
            {"path": error.path, "code": error.code, "message": error.message}
            for error in sorted(entries)
        ],
    }
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _baseline_at(root: Path, ref: str, rel: str) -> list[MypyError] | None:
    result = subprocess.run(
        ["git", "show", f"{ref}:{rel}"],
        cwd=root,
        capture_output=True,
        text=True,
        timeout=_GIT_TIMEOUT_SECONDS,
        check=False,
    )
    if result.returncode != 0:
        return None
    return _payload_entries(json.loads(result.stdout), f"{ref}:{rel}")


def _is_subset(current: Sequence[MypyError], previous: Sequence[MypyError]) -> bool:
    current_counts = _counts(current)
    previous_counts = _counts(previous)
    return all(current_counts[identity] <= previous_counts[identity] for identity in current_counts)


def shrink_violations(root: Path, baseline: Path, entries: Sequence[MypyError]) -> list[str]:
    """Reject growth against a baseline that has already landed on origin/main.

    A missing ``.git`` (fixture trees) and a baseline not yet on the default
    branch have no predecessor to shrink. A ``git show`` miss skips that ref.
    """

    if not (root / ".git").exists():
        return []
    try:
        rel = baseline.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return []
    if _baseline_at(root, "origin/main", rel) is None:
        return []
    violations: list[str] = []
    for ref in _SHRINK_REFS:
        try:
            previous = _baseline_at(root, ref, rel)
        except (json.JSONDecodeError, ValueError) as exc:
            return [f"{rel}: baseline at {ref} is unreadable: {exc}"]
        if previous is None:
            continue
        if not _is_subset(entries, previous):
            violations.append(f"{rel}: baseline may only shrink; freeze/growth differs from {ref}")
    return violations


def evaluate(
    root: Path,
    baseline: Path,
    targets: Sequence[str],
    *,
    config_file: Path | None = None,
    incremental: bool = True,
) -> list[str]:
    """Return violation strings. An empty list is a pass."""

    selected = _normalize_targets(root, targets)
    py_targets = [target for target in selected if target.endswith(".py") or (root / target).is_dir()]
    # A baseline-only path (no Python) rechecks the whole scripts tree.
    scoped = py_targets or [DEFAULT_TARGET]
    current, fatal = collect_errors(
        root, scoped, config_file=config_file, incremental=incremental
    )
    if fatal:
        return fatal
    entries = load_entries(baseline)
    # A file list compares only those files. The full scripts/ census also
    # rejects a baseline entry that names something outside scripts/.
    relevant = [entry for entry in entries if _in_scope(entry.path, scoped)]
    violations: list[str] = []
    if DEFAULT_TARGET in scoped:
        violations.extend(
            f"{entry.path}: stale baseline {entry.code}: {entry.message}"
            for entry in entries
            if not _in_scope(entry.path, (DEFAULT_TARGET,))
        )
    violations.extend(compare(current, relevant))
    violations.extend(shrink_violations(root, baseline, entries))
    return violations


def _python_targets(paths: Sequence[str], root: Path) -> list[str]:
    if not paths:
        return [DEFAULT_TARGET]
    selected = _normalize_targets(root, paths)
    python = [target for target in selected if target.endswith(".py")]
    return python or [DEFAULT_TARGET]


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "paths",
        nargs="*",
        help=f"Python files to check (default: {DEFAULT_TARGET}/). Other paths recheck {DEFAULT_TARGET}/.",
    )
    parser.add_argument(
        "--baseline",
        type=Path,
        default=BASELINE_PATH,
        help=f"Baseline JSON (default: {_mp('lint/mypy_baseline.json')}).",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=REPO_ROOT,
        help="Tree mypy runs in (default: repository root).",
    )
    parser.add_argument(
        "--write-baseline",
        action="store_true",
        help="Rewrite the baseline from the current mypy census and exit.",
    )
    parser.add_argument(
        "--no-incremental",
        action="store_true",
        help="Ignore the mypy cache. Tests use this; CI keeps the cache.",
    )
    args = parser.parse_args(argv)
    root = args.root.resolve()
    baseline = args.baseline if args.baseline.is_absolute() else root / args.baseline
    try:
        targets = [DEFAULT_TARGET] if args.write_baseline else _python_targets(args.paths, root)
        if args.write_baseline:
            current, fatal = collect_errors(
                root, targets, incremental=not args.no_incremental
            )
            if fatal:
                print("\n".join(fatal), file=sys.stderr)
                return 1
            write_baseline(baseline, current)
            print(f"Wrote {len(current)} mypy errors to {baseline.relative_to(root)}")
            return 0
        violations = evaluate(
            root, baseline, targets, incremental=not args.no_incremental
        )
    except (OSError, ValueError, json.JSONDecodeError, subprocess.SubprocessError) as exc:
        print(f"mypy ratchet could not run: {exc}", file=sys.stderr)
        return 1
    if violations:
        print("\n".join(violations), file=sys.stderr)
        return 1
    print("OK: mypy ratchet matches the baseline")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
