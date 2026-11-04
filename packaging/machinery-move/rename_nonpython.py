#!/usr/bin/env python3
"""Rename machinery module invocations and resource paths outside Python code.

Uses the ownership model in ``rename_python.py`` (same map, same module names).
Shell scripts, git hooks, systemd and launchd units, configuration files and
Markdown code spans are rewritten where a whole name or path matches: ``scripts.<machinery
module>`` becomes ``lu_machinery.<module>`` and ``scripts/<machinery path>``
becomes ``lu_machinery/<path>``. Python files are only inventoried: path
strings, split path components and ``-m`` argument lists are reported for
disposition because rename_python.py owns every Python rewrite.
"""

from __future__ import annotations

import argparse
import ast
import importlib.util
import re
import sys
from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from fnmatch import fnmatchcase
from pathlib import Path, PurePosixPath
from types import ModuleType


def _load_rename_python() -> ModuleType:
    name = "machinery_move_rename_python"
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, Path(__file__).resolve().with_name("rename_python.py"))
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


rp = _load_rename_python()
AMBIGUOUS, MACHINERY, PRODUCT = rp.AMBIGUOUS, rp.MACHINERY, rp.PRODUCT
OLD_ROOT, NEW_ROOT = rp.OLD_ROOT, rp.NEW_ROOT
Finding, OwnershipMap, Report = rp.Finding, rp.OwnershipMap, rp.Report

# ``scripts`` starting a dotted module name; ``-mscripts.x`` (no space) is also an invocation.
MODULE_START = re.compile(r"(?:(?<=-m)|(?<![\w.\-/$@\\]))scripts(?P<comp>(?:\.[A-Za-z_][A-Za-z0-9_]*)*)(?P<dot>\.)?")
# ``scripts/...`` (glob characters included) or a ``/scripts`` directory at the end of a path.
PATH_START = re.compile(r"(?<![\w.\-\\])scripts(?:(?P<rest>/[\w.\-*?\[\]/]*)|(?![\w.\-]))")
BACKSLASH_PATH = re.compile(r"(?<![\w.\-\\/])scripts\\[\w.\-\\]+")
BARE_WORD = re.compile(r"(?<![\w.\-/$@\\])scripts(?![\w.\-/\\])")
# Text that completes a name at run time: shell or template variables and placeholders.
DYNAMIC_NEXT = frozenset("${%<")
INVOCATION_BEFORE = re.compile(r"(?:^|[\s\"'(\[,=])-m[\s\"',\-]*$")
ENTRY_POINT_NEXT = re.compile(r":[A-Za-z_]")
PREFIX_STOP = re.compile(r"[\s\"'=(\[{<>|&;,:`!]")
# Commands and settings that change the working directory to the path that follows.
CWD_BEFORE = re.compile(
    r"(?:(?:^|[\s;&|(])(?:cd|pushd)(?:\s+-{1,2}[\w-]*)*\s+|WorkingDirectory=|(?:^|\s)-C\s*"
    r"|(?:^|\s)--(?:directory|cwd|chdir|working-directory)(?:=|\s+))[\"']?$"
)
INTERPRETER_BEFORE = re.compile(
    r"(?:^|[\s;&|(\"'])(?:\S*python[0-9.]*|\"?\$\{?PY\w*\}?\"?|bash|sh|zsh|exec|source|\.|uv\s+run(?:\s+python[0-9.]*)?)\s+[\"']?$"
)
GLOB_CHARS = frozenset("*?[")
FENCE = re.compile(r"^\s*(`{3,}|~{3,})")
INLINE_CODE = re.compile(r"(`+)(?!`)(.+?)(?<!`)\1(?!`)")

SHELL_SUFFIXES = (".sh", ".bash", ".zsh")
UNIT_SUFFIXES = (".service", ".timer", ".socket", ".path", ".target", ".mount", ".plist", ".plist.disabled")
CONFIG_SUFFIXES = (
    ".yml",
    ".yaml",
    ".toml",
    ".json",
    ".ini",
    ".cfg",
    ".conf",
    ".tsv",
    ".j2",
    ".jinja",
    ".txt",
    ".env",
    ".example",
)
# Pattern files where a leading "/" anchors at the repository root rather than the filesystem root.
ROOT_ANCHORED_NAMES = frozenset({".gitattributes", ".gitignore", ".dockerignore", ".trufflehogignore", "CODEOWNERS"})
CONFIG_NAMES = frozenset({"Makefile", "Dockerfile", "justfile", "Procfile"}) | ROOT_ANCHORED_NAMES
MARKDOWN_SUFFIXES = (".md", ".markdown", ".mdx")
MAX_BYTES = 4 * 1024 * 1024

CODE, MARKDOWN, PYTHON, OTHER = "code", "markdown", "python", "other"
REWRITE_VERDICTS = frozenset({"module_invocation", "module_reference", "resource_path"})
# Verdicts that name a machinery or mixed target (worth listing in prose and unsupported files).
MACHINERY_VERDICTS = REWRITE_VERDICTS | {"ambiguous_module", "ambiguous_path", "computed_module", "computed_path"}


@dataclass(frozen=True)
class Edit:
    start: int
    end: int
    replacement: str


@dataclass(frozen=True)
class Token:
    """One reference found in a text: where it is, what it says and what to do with it."""

    start: int
    end: int
    text: str
    verdict: str
    detail: str = ""


def is_shell_like(rel: str, head: bytes) -> bool:
    """Files whose words are shell arguments, so a bare ``scripts`` names the directory."""

    name = PurePosixPath(rel).name
    if name.endswith(SHELL_SUFFIXES) or name in ("Makefile", "Dockerfile", "justfile", "Procfile"):
        return True
    if head.startswith(b"#!"):
        return b"python" not in head.split(b"\n", 1)[0]
    parts = PurePosixPath(rel).parts
    return "." not in name and any(part in (".githooks", "hooks") for part in parts[:-1])


def classify(rel: str, head: bytes) -> str:
    name = PurePosixPath(rel).name
    if name.endswith(".py"):
        return PYTHON
    if name.endswith(MARKDOWN_SUFFIXES):
        return MARKDOWN
    if name.endswith(SHELL_SUFFIXES + UNIT_SUFFIXES + CONFIG_SUFFIXES) or name in CONFIG_NAMES:
        return CODE
    if head.startswith(b"#!"):
        first = head.split(b"\n", 1)[0]
        return PYTHON if b"python" in first else CODE
    parts = PurePosixPath(rel).parts
    if "." not in name and any(part in (".githooks", "hooks") for part in parts[:-1]):
        return CODE
    return OTHER


def path_prefix(text: str, start: int) -> str:
    """The run of path characters glued in front of a ``scripts`` token."""

    i = start
    while i > 0 and not PREFIX_STOP.match(text[i - 1]):
        i -= 1
    return text[i:start]


def prefix_is_local(prefix: str, root_anchored: bool = False) -> bool:
    if not prefix or (root_anchored and prefix == "/"):
        return True
    if re.fullmatch(r"(?:\.\.?/|\*\*?/)+", prefix):
        return True  # relative segments, or a glob that matches any root
    return prefix.endswith("/") and any(marker in prefix for marker in "$@%})")


def clean_path(token: str) -> str:
    """Drop sentence punctuation and an unbalanced closing bracket (Markdown link text)."""

    while token and (token[-1] in ".," or (token[-1] == "]" and token.count("[") < token.count("]"))):
        token = token[:-1]
    return token


def _is_dynamic(text: str, end: int, dynamic_tail: bool, shell: bool = False) -> bool:
    """True when the name does not end where the match ends.

    A shell word continues across quotes (``scripts/x.py"${S}"``, ``'scripts/x'.bak``): after
    any run of quote characters, a variable, a placeholder, a backtick or more word characters
    mean the real name is only known at run time or is longer than the match.
    """

    i = end
    while i < len(text) and text[i] in "\"'":
        i += 1
    if i == len(text):
        return dynamic_tail
    if text.startswith("</", i):
        return False  # a closing markup tag, not a ``<placeholder>``
    if text[i] in DYNAMIC_NEXT or (shell and text[i] == "`"):
        return True  # in a shell file a backtick starts command substitution
    return i > end and (text[i].isalnum() or text[i] in "_./-`")


class Scanner:
    """Resolve module and path references in one text against the ownership map."""

    def __init__(self, ownership: OwnershipMap, rel: str, shell: bool = False) -> None:
        self.ownership = ownership
        self.rel = rel
        self.shell = shell
        self.file_owner = ownership.file_owner(rel)
        self.root_anchored = PurePosixPath(rel).name in ROOT_ANCHORED_NAMES

    def resolve_path(self, token: str) -> str | None:
        """Owner of a ``scripts/...`` path or glob: machinery, product, AMBIGUOUS, ``root`` or None (unknown)."""

        stripped = token.rstrip("/")
        if stripped == OLD_ROOT:
            return "root"
        if GLOB_CHARS & set(stripped):
            owners = set()
            for key, owner in self.ownership.files.items():
                parents = [p.as_posix() for p in PurePosixPath(key).parents]
                if fnmatchcase(key, stripped) or any(fnmatchcase(p, stripped) for p in parents):
                    owners.add(owner)
            return None if not owners else owners.pop() if len(owners) == 1 else AMBIGUOUS
        return self.ownership.path_owner(stripped)

    def module_tokens(self, text: str, dynamic_tail: bool = False) -> Iterator[Token]:
        """Dotted ``scripts.`` names; ``dynamic_tail`` means run-time text follows the end of ``text``."""

        for match in MODULE_START.finditer(text):
            start, comp, dot = match.start(), match.group("comp"), match.group("dot")
            end = match.end()
            dynamic = _is_dynamic(text, end, dynamic_tail, self.shell)
            if not dynamic and dot:
                end -= 1  # a full stop after the name
            if not comp and not dynamic:
                continue  # the word "scripts", or a path
            name = text[start:end]
            before = text[max(0, start - 40) : start]
            invocation = before.endswith("-m") or bool(INVOCATION_BEFORE.search(before))
            if dynamic:
                dotted = name.rstrip(".")
                base = dotted if name.endswith(".") else dotted.rsplit(".", 1)[0] if "." in dotted else OLD_ROOT
                resolved = self.ownership.resolve(base)
                owner = self.ownership.subtree_owner(resolved[0].name) if resolved else None
                verdict = {MACHINERY: "module_invocation" if invocation else "module_reference", PRODUCT: "keep"}.get(
                    owner or "", "computed_module"
                )
                detail = (
                    "" if verdict != "computed_module" else f"completed at run time below {base}, whose owners differ"
                )
                yield Token(start, end, name + "…", verdict, detail)
                continue
            if not invocation and ENTRY_POINT_NEXT.match(text, end):
                invocation = True  # ``module:attribute`` names a module to import
            yield Token(start, end, name, *self._module_verdict(name, invocation))

    def _module_verdict(self, name: str, invocation: bool) -> tuple[str, str]:
        resolved = self.ownership.resolve(name)
        if resolved is None:
            return ("unknown_module", "the map has no scripts package") if invocation else ("keep", "")
        entry, rest = resolved
        if invocation and rest:
            return "unknown_module", f"no module {name} in the map"
        if entry.name == OLD_ROOT:
            return "keep", ""  # e.g. ``scripts.sh``: a file name, not a module under scripts
        owner = entry.owner
        if invocation:
            main = self.ownership.module(f"{entry.name}.__main__")
            if main is not None and main.owner != owner:
                owner = AMBIGUOUS
        if owner == AMBIGUOUS:
            return "ambiguous_module", f"{entry.name} has more than one owner"
        if owner == MACHINERY:
            return ("module_invocation" if invocation else "module_reference"), ""
        return "keep", ""

    def path_tokens(self, text: str, dynamic_tail: bool = False) -> Iterator[Token]:
        """``scripts/...`` paths and globs, and a ``.../scripts`` directory at the end of a path."""

        for match in PATH_START.finditer(text):
            start = match.start()
            if match.group("rest") is None and (start == 0 or text[start - 1] != "/"):
                continue  # the bare word; see bare_words
            token = clean_path(match.group(0))
            end = start + len(token)
            prefix = path_prefix(text, start)
            if _is_dynamic(text, end, dynamic_tail, self.shell):
                # A run-time suffix can climb out of any directory (``${NAME}`` = ``../x``), so the
                # owner of the static part proves nothing: always reported, never rewritten.
                yield Token(start, end, token + "…", "computed_path", "the path is completed at run time")
                continue
            owner = self.resolve_path(token)
            if owner == "root":
                if self.file_owner != PRODUCT:
                    yield Token(start, end, token, "root_reference", "the scripts/ root is split between both owners")
            elif owner is None:
                yield Token(start, end, token, "unknown_path", "the map has no file or directory here")
            elif owner == AMBIGUOUS:
                yield Token(start, end, token, "ambiguous_path", "the path or glob covers files of both owners")
            elif owner == MACHINERY:
                if prefix_is_local(prefix, self.root_anchored):
                    yield Token(start, end, token, "resource_path")
                else:
                    yield Token(start, end, token, "foreign_path", f"prefix {prefix!r} is not this repository's root")
        for match in BACKSLASH_PATH.finditer(text):
            token = clean_path(match.group(0))
            owner = self.resolve_path(token.replace("\\", "/"))
            if owner in (MACHINERY, AMBIGUOUS):
                yield Token(match.start(), match.start() + len(token), token, "backslash_path", "Windows-style path")

    def bare_words(self, text: str) -> Iterator[Token]:
        """The word ``scripts`` as a directory argument, outside comment lines (``cd scripts``)."""

        if self.file_owner == PRODUCT:
            return  # the product tree keeps its scripts/ directory
        for match in BARE_WORD.finditer(text):
            line_start = text.rfind("\n", 0, match.start()) + 1
            if text[line_start : match.start()].lstrip().startswith(("#", "//", ";")):
                continue
            yield Token(match.start(), match.end(), OLD_ROOT, "root_reference", "the scripts/ root is split")

    def changes_directory(self, text: str, start: int) -> bool:
        before = text[: start - len(path_prefix(text, start))]
        return bool(CWD_BEFORE.search(before[before.rfind("\n") + 1 :]))

    def is_direct_invocation(self, text: str, start: int, token: str) -> bool:
        if not token.endswith((".py", ".sh")):
            return False
        before = text[: start - len(path_prefix(text, start))]
        line_start = before.rfind("\n") + 1
        return bool(INTERPRETER_BEFORE.search(before[line_start:]))


def line_of(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def markdown_code_regions(text: str, fenced_only: bool = False) -> list[tuple[int, int]]:
    """Character ranges of fenced blocks and (unless ``fenced_only``) inline code spans."""

    regions: list[tuple[int, int]] = []
    offset = 0
    fence: str | None = None
    fence_start = 0
    for line in text.splitlines(keepends=True):
        match = FENCE.match(line)
        if fence is None and match:
            fence, fence_start = match.group(1), offset + len(line)
        elif fence is not None and match and match.group(1)[0] == fence[0] and len(match.group(1)) >= len(fence):
            regions.append((fence_start, offset))
            fence = None
        elif fence is None and not fenced_only:
            regions.extend((offset + m.start(2), offset + m.end(2)) for m in INLINE_CODE.finditer(line))
        offset += len(line)
    if fence is not None:
        regions.append((fence_start, len(text)))
    return regions


def in_regions(regions: list[tuple[int, int]], start: int, end: int) -> bool:
    return any(a <= start and end <= b for a, b in regions)


def scan_text(scanner: Scanner, text: str, kind: str, report: Report, shell_like: bool = False) -> list[Edit]:
    """Rewrite or report every reference in a non-Python text file."""

    regions = markdown_code_regions(text) if kind == MARKDOWN else []
    edits: list[Edit] = []
    rel = scanner.rel
    tokens = [*scanner.module_tokens(text), *scanner.path_tokens(text)]
    if kind == CODE and shell_like:
        tokens.extend(scanner.bare_words(text))
    elif kind == MARKDOWN:
        fenced = markdown_code_regions(text, fenced_only=True)
        tokens.extend(t for t in scanner.bare_words(text) if in_regions(fenced, t.start, t.end))
    for token in sorted(tokens, key=lambda t: (t.start, t.end)):
        if token.verdict == "keep":
            continue
        line = line_of(text, token.start)
        if kind == MARKDOWN and not in_regions(regions, token.start, token.end):
            if token.verdict in MACHINERY_VERDICTS:
                report.inventory.append(
                    Finding(rel, line, "prose_mention", token.text, detail="Markdown prose is left as written")
                )
            continue
        if kind == OTHER:
            if token.verdict in MACHINERY_VERDICTS:
                report.unresolved.append(
                    Finding(rel, line, "unsupported_file_type", token.text, detail="no rewrite rule for this file type")
                )
            continue
        if token.verdict == "resource_path" and scanner.changes_directory(text, token.start):
            # Relative paths after a directory change depend on the old layout: left as written.
            report.unresolved.append(
                Finding(rel, line, "cwd_into_machinery", token.text, detail="a working-directory change into machinery")
            )
            continue
        if token.verdict in REWRITE_VERDICTS:
            after = NEW_ROOT + token.text[len(OLD_ROOT) :]
            edits.append(Edit(token.start, token.start + len(OLD_ROOT), NEW_ROOT))
            report.rewrites.append(Finding(rel, line, token.verdict, token.text, after))
            if token.verdict == "resource_path" and scanner.is_direct_invocation(text, token.start, token.text):
                report.inventory.append(
                    Finding(rel, line, "direct_script_invocation", token.text, after, "runs a machinery file by path")
                )
        else:
            report.unresolved.append(Finding(rel, line, token.verdict, token.text, detail=token.detail))
    return edits


def apply_edits(text: str, edits: list[Edit]) -> str:
    for edit in sorted(edits, key=lambda e: e.start, reverse=True):
        text = text[: edit.start] + edit.replacement + text[edit.end :]
    return text


def check_fixed_point(scanner: Scanner, new_text: str, kind: str, report: Report, shell_like: bool = False) -> None:
    """Post-condition: scanning the rewritten text finds nothing more to rewrite."""

    second = Report("rename_nonpython", "check", "")
    scan_text(scanner, new_text, kind, second, shell_like)
    report.unresolved.extend(
        Finding(scanner.rel, f.line, "rewrite_not_applied", f.before, detail="still pending after the rewrite")
        for f in second.rewrites
    )


# -- Python files: inventory only ----------------------------------------


LOADER_NAMES = frozenset({"import_module", "run_module", "__import__"})
PATH_CALLS = frozenset({"Path", "PurePath", "PurePosixPath", "join", "joinpath"})


def _callee_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return ""


BUILDER_METHODS = frozenset({"format", "format_map", "join", "replace"})


def _ast_parts(node: ast.AST) -> list[str | None] | None:
    """Static texts of a string expression in order, None for run-time pieces; None if not a string."""

    if isinstance(node, ast.Constant) and isinstance(node.value, (str, bytes)):
        return [node.value.decode("latin-1") if isinstance(node.value, bytes) else node.value]
    if isinstance(node, ast.JoinedStr):
        return [v.value if isinstance(v, ast.Constant) and isinstance(v.value, str) else None for v in node.values]
    if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Mod)):
        left, right = _ast_parts(node.left), _ast_parts(node.right)
        if isinstance(node.op, ast.Mod):
            return None if left is None else [*left, None]
        if left is not None or right is not None:
            return (left if left is not None else [None]) + (right if right is not None else [None])
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr in BUILDER_METHODS:
        receiver = _ast_parts(node.func.value)
        return None if receiver is None else [*receiver, None]
    return None


def _ast_part_constants(node: ast.AST) -> list[ast.Constant]:
    """The literals that make up the value in ``_ast_parts`` (not format arguments or nested keys)."""

    if isinstance(node, ast.Constant):
        return [node]
    if isinstance(node, ast.JoinedStr):
        return [v for v in node.values if isinstance(v, ast.Constant)]
    if isinstance(node, ast.BinOp):
        sides = (node.left,) if isinstance(node.op, ast.Mod) else (node.left, node.right)
        return [c for side in sides if _ast_parts(side) is not None for c in _ast_part_constants(side)]
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
        return _ast_part_constants(node.func.value)
    return []


def _builder_runs(parts: list[str | None]) -> list[tuple[str, bool]]:
    """Consecutive static texts of a built string, each with whether run-time text follows it."""

    runs: list[tuple[str, bool]] = []
    current: list[str] = []
    for part in [*parts, None]:
        if part is None:
            if current:
                runs.append(("".join(current), True))
            current = []
        else:
            current.append(part)
    if runs and parts and parts[-1] is not None:
        runs[-1] = (runs[-1][0], False)
    return runs


def _owned_by_rename_python(value: str) -> bool:
    """Strings that start with a module name and contain no whitespace are rename_python.py's."""

    return value.startswith(OLD_ROOT + ".") and not re.search(r"\s", value)


def scan_python(scanner: Scanner, source: bytes, report: Report) -> None:
    rel = scanner.rel
    try:
        tree = ast.parse(source)
    except (SyntaxError, ValueError) as exc:
        report.unresolved.append(Finding(rel, getattr(exc, "lineno", 1) or 1, "parse_error", rel, detail=str(exc)))
        return
    parents: dict[int, ast.AST] = {}
    skip: set[int] = set()
    for node in ast.walk(tree):
        for child in ast.iter_child_nodes(node):
            parents[id(child)] = node
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)) and node.body:
            first = node.body[0]
            if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant):
                skip.add(id(first.value))
        if isinstance(node, ast.Call) and _callee_name(node.func) in LOADER_NAMES and node.args:
            skip.add(id(node.args[0]))  # rename_python owns loader targets

    def unresolved(node: ast.AST, kind: str, text: str, detail: str) -> None:
        report.unresolved.append(Finding(rel, getattr(node, "lineno", 1), kind, text, detail=detail))

    def check_split(node: ast.AST, components: list[str], computed: bool) -> None:
        path = "/".join([OLD_ROOT, *components])
        owner = scanner.resolve_path(path)
        if owner == "root" and not computed and scanner.file_owner == PRODUCT:
            return
        if owner == PRODUCT and not computed:
            return
        if computed and owner not in (None, "root") and scanner.ownership.path_owner(path) == PRODUCT:
            return
        if owner is None and not computed:
            return
        detail = "path assembled from parts" + (" with a computed part" if computed else "")
        unresolved(node, "split_path_component", path + ("/…" if computed else ""), detail)

    # Built strings (``"scripts/" + "lib/" + name``, f-strings, % and str methods) are read whole:
    # their paths are scanned with the run-time tail they really have; their module names are
    # rename_python.py's.
    for node in ast.walk(tree):
        parts = None if isinstance(node, ast.Constant) else _ast_parts(node)
        if parts is None or _ast_parts(parents.get(id(node))) is not None:
            continue  # not a built string, or not the outermost one
        skip.update(id(c) for c in _ast_part_constants(node))
        for run, tail in _builder_runs(parts):
            for token in scanner.path_tokens(run, dynamic_tail=tail):
                if token.verdict in ("keep", "unknown_path"):
                    continue
                kind = (
                    "python_string_reference" if token.verdict in REWRITE_VERDICTS | {"foreign_path"} else token.verdict
                )
                unresolved(node, kind, token.text, token.detail or "path in a string built in Python code")

    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str) and id(node) not in skip:
            value = node.value
            parent = parents.get(id(node))
            concatenated = isinstance(parent, (ast.JoinedStr, ast.BinOp)) and not isinstance(
                getattr(parent, "op", None), ast.Div
            )
            if value in (OLD_ROOT, OLD_ROOT + "/") and not concatenated:
                components, computed = _following_components(node, parents)
                if components is not None:
                    check_split(node, components, computed)
                elif scanner.file_owner != PRODUCT:
                    unresolved(node, "root_reference", value, "the scripts/ root is split between both owners")
                continue
            if _owned_by_rename_python(value):
                continue
            dynamic_tail = False
            if isinstance(parent, ast.JoinedStr):
                index = next(i for i, part in enumerate(parent.values) if part is node)
                dynamic_tail = index + 1 < len(parent.values)
            elif isinstance(parent, ast.BinOp) and isinstance(parent.op, ast.Add) and parent.left is node:
                dynamic_tail = not isinstance(parent.right, ast.Constant)  # ``"scripts/" + name``
            for token in [*scanner.module_tokens(value, dynamic_tail), *scanner.path_tokens(value, dynamic_tail)]:
                if token.verdict in ("keep", "unknown_module", "unknown_path"):
                    continue
                kind = (
                    "python_string_reference" if token.verdict in REWRITE_VERDICTS | {"foreign_path"} else token.verdict
                )
                unresolved(
                    node, kind, token.text, token.detail or "string in Python code; rename_python does not rewrite it"
                )
        elif isinstance(node, (ast.List, ast.Tuple)):
            elts = node.elts
            for i, elt in enumerate(elts[:-1]):
                nxt = elts[i + 1]
                if not (isinstance(elt, ast.Constant) and elt.value == "-m") or isinstance(nxt, ast.Constant):
                    continue
                first = nxt.values[0] if isinstance(nxt, ast.JoinedStr) and nxt.values else None
                if isinstance(first, ast.Constant) and _owned_by_rename_python(str(first.value)):
                    continue  # rename_python reports the computed module string
                unresolved(
                    node, "subprocess_computed_module", ast.unparse(node)[:160], "-m target computed at run time"
                )


def _following_components(node: ast.Constant, parents: dict[int, ast.AST]) -> tuple[list[str] | None, bool]:
    """Path parts after a literal ``"scripts"`` joined with ``/`` or a path call; None if not a split path."""

    parent = parents.get(id(node))
    components: list[str] = []
    if isinstance(parent, ast.BinOp) and isinstance(parent.op, ast.Div) and parent.right is node:
        current: ast.AST = parent
        while True:
            up = parents.get(id(current))
            if not (isinstance(up, ast.BinOp) and isinstance(up.op, ast.Div) and up.left is current):
                return components, False
            if isinstance(up.right, ast.Constant) and isinstance(up.right.value, str):
                components.extend(p for p in up.right.value.split("/") if p)
                current = up
            else:
                return components, True
    if isinstance(parent, ast.Call) and _callee_name(parent.func) in PATH_CALLS and node in parent.args:
        for arg in parent.args[parent.args.index(node) + 1 :]:
            if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                components.extend(p for p in arg.value.split("/") if p)
            else:
                return components, True
        return components, False
    return None, False


# -- driving ---------------------------------------------------------------


def run(ownership: OwnershipMap, root: Path, targets: Sequence[str], apply: bool) -> Report:
    report = Report("rename_nonpython", "apply" if apply else "check", ownership.sha256)
    skipped_binary = skipped_large = 0
    for path, rel in rp.iter_files(root, targets, None):
        size = path.stat().st_size
        if size > MAX_BYTES:
            with path.open("rb") as handle:
                if OLD_ROOT.encode() in handle.read():
                    report.unresolved.append(
                        Finding(rel, 1, "skipped_large_file", rel, detail=f"{size} bytes; inspect by hand")
                    )
            skipped_large += 1
            continue
        data = path.read_bytes()
        if OLD_ROOT.encode() not in data:
            continue
        if b"\0" in data:
            skipped_binary += 1
            continue
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            skipped_binary += 1
            continue
        report.files_scanned += 1
        kind = classify(rel, data[:256])
        shell_like = is_shell_like(rel, data[:256])
        scanner = Scanner(ownership, rel, shell=shell_like)
        if kind == PYTHON:
            scan_python(scanner, data, report)
            continue
        edits = scan_text(scanner, text, kind, report, shell_like)
        if not edits:
            continue
        report.files_changed.append(rel)
        text = apply_edits(text, edits)
        check_fixed_point(scanner, text, kind, report, shell_like)
        if apply:
            rp.write_atomically(path, text.encode("utf-8"))
    report.notes.append(f"skipped binary files containing 'scripts': {skipped_binary}")
    report.notes.append(f"skipped files over {MAX_BYTES} bytes: {skipped_large}")
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="rename_nonpython.py",
        description=(
            "Rename `-m scripts.<machinery module>` invocations and `scripts/<machinery path>` resource paths to\n"
            "lu_machinery in shell, hooks, systemd/launchd units, config files and Markdown code spans, and report\n"
            "unresolved references (including Python path strings and subprocess argument lists). Use it on a\n"
            "disposable clone during the machinery move, after rename_python.py; never on the live product tree."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
Examples:
  python packaging/machinery-move/rename_nonpython.py --map ownership.json --root "$CLONE" --check
  python packaging/machinery-move/rename_nonpython.py --map ownership.json --root "$CLONE" --apply --report np.json
  python packaging/machinery-move/rename_nonpython.py --map ownership.json --check .githooks packaging/systemd

Rules:
  Rewritten (token boundaries, whole file): *.sh/.bash/.zsh, extensionless hooks, shebang scripts,
  systemd units, launchd plists, YAML/TOML/JSON/INI/CFG/TSV/TXT/Jinja, Makefile/Dockerfile.
  Markdown: only fenced blocks and inline code spans are rewritten; machinery mentions in prose are
  inventoried, not changed. Python files: report only (rename_python.py owns Python rewrites).
  Other file types: machinery references are reported, not changed. A path whose prefix is a literal
  absolute directory (not a variable such as $ROOT/ or @REPO_ROOT@/) is reported.

Outputs:
  stdout: a summary line, rewrite/inventory/unresolved counts by kind, then every unresolved reference as
  path:line: kind: text (detail). --apply rewrites files in place (atomic replace, mode kept).
  --report writes the same data as JSON with every rewrite and inventory entry.

Exit codes:
  0  no unresolved references (with --check, rewrites may still be pending: see the summary)
  1  at least one unresolved reference; --apply still wrote every resolved rewrite
  2  usage error, or an unreadable or malformed ownership map

Related:
  packaging/machinery-move/README.md, rename_python.py, machinery move contract v3 step 6 (rename items 3-4).
""",
    )
    rp.add_common_arguments(parser)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        ownership = OwnershipMap.from_file(args.map)
        report = run(ownership, args.root, args.paths, apply=args.apply)
    except rp.MapError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return rp.EXIT_USAGE
    return rp.emit(report, args.report)


if __name__ == "__main__":
    sys.exit(main())
