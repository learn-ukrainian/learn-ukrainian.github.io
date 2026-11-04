#!/usr/bin/env python3
"""Rename machinery module invocations and resource paths outside Python code.

Uses the ownership model in ``rename_python.py`` (same map, same module names).
Shell scripts, git hooks, systemd and launchd units, configuration files and
Markdown code spans are rewritten at token boundaries: ``scripts.<machinery
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

# ``scripts.a.b`` not glued to a longer word, path or variable.
MODULE_TOKEN = re.compile(r"(?<![\w.\-/$@])scripts(?:\.[A-Za-z_][A-Za-z0-9_]*)+")
# ``scripts/...`` or a trailing ``/scripts`` directory, not glued to a longer word.
PATH_TOKEN = re.compile(r"(?<![\w.\-])scripts(?:/[\w.\-*/]*)?(?![\w.\-])")
INVOCATION_BEFORE = re.compile(r"(?:^|[\s\"'(\[,=])-m[\s\"',]*$")
PREFIX_STOP = re.compile(r"[\s\"'=(\[{<>|&;,:`!]")
INTERPRETER_BEFORE = re.compile(
    r"(?:^|[\s;&|(\"'])(?:\S*python[0-9.]*|\"?\$\{?PY\w*\}?\"?|bash|sh|zsh|exec|source|\.|uv\s+run(?:\s+python[0-9.]*)?)\s+[\"']?$"
)
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


@dataclass(frozen=True)
class Edit:
    start: int
    end: int
    replacement: str


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
    while token and token[-1] in ".,":
        token = token[:-1]
    return token


class Scanner:
    """Resolve module and path tokens in one text against the ownership map."""

    def __init__(self, ownership: OwnershipMap, rel: str) -> None:
        self.ownership = ownership
        self.rel = rel
        self.file_owner = ownership.file_owner(rel)
        self.root_anchored = PurePosixPath(rel).name in ROOT_ANCHORED_NAMES

    def resolve_path(self, token: str) -> str | None:
        """Owner of a ``scripts/...`` path: machinery, product, AMBIGUOUS, ``root`` or None (unknown)."""

        stripped = token.rstrip("/")
        if stripped == OLD_ROOT:
            return "root"
        if "*" in stripped:
            owners = set()
            for key, owner in self.ownership.files.items():
                parents = [p.as_posix() for p in PurePosixPath(key).parents]
                if fnmatchcase(key, stripped) or any(fnmatchcase(p, stripped) for p in parents):
                    owners.add(owner)
            return None if not owners else owners.pop() if len(owners) == 1 else AMBIGUOUS
        return self.ownership.path_owner(stripped)

    def module_tokens(self, text: str) -> Iterator[tuple[int, int, str, str, str]]:
        """Yield (start, end, token, verdict, detail); verdict is rename, keep, or an unresolved kind."""

        for match in MODULE_TOKEN.finditer(text):
            token = match.group(0)
            invocation = bool(INVOCATION_BEFORE.search(text[max(0, match.start() - 40) : match.start()]))
            resolved = self.ownership.resolve(token)
            if resolved is None:
                verdict, detail = ("unknown_module", "the map has no scripts package") if invocation else ("keep", "")
            else:
                entry, rest = resolved
                owner = entry.owner
                if invocation:
                    main = self.ownership.module(f"{entry.name}.__main__")
                    if main is not None and main.owner != owner:
                        owner = AMBIGUOUS
                if entry.name == OLD_ROOT or (invocation and rest):
                    verdict, detail = (
                        ("unknown_module", f"no module {token} in the map") if invocation else ("keep", "")
                    )
                elif owner == AMBIGUOUS:
                    verdict, detail = "ambiguous_module", f"{entry.name} has more than one owner"
                elif owner == MACHINERY:
                    verdict, detail = ("module_invocation" if invocation else "module_reference"), ""
                else:
                    verdict, detail = "keep", ""
            yield match.start(), match.end(), token, verdict, detail

    def path_tokens(self, text: str) -> Iterator[tuple[int, int, str, str, str]]:
        """Yield (start, end, token, verdict, detail) for ``scripts/...`` paths."""

        for match in PATH_TOKEN.finditer(text):
            raw = match.group(0)
            if raw == OLD_ROOT and (match.start() == 0 or text[match.start() - 1] != "/"):
                continue  # the bare word "scripts"
            token = clean_path(raw)
            end = match.start() + len(token)
            owner = self.resolve_path(token)
            prefix = path_prefix(text, match.start())
            if owner == "root":
                if self.file_owner == PRODUCT:
                    continue
                verdict, detail = "root_reference", "the scripts/ root is split between both owners"
            elif owner is None:
                verdict, detail = "unknown_path", "the map has no file or directory here"
            elif owner == AMBIGUOUS:
                verdict, detail = "ambiguous_path", "the directory holds files of both owners"
            elif owner == PRODUCT:
                verdict, detail = "keep", ""
            elif not prefix_is_local(prefix, self.root_anchored):
                verdict, detail = "foreign_path", f"prefix {prefix!r} is not this repository's root"
            else:
                verdict, detail = "resource_path", ""
            yield match.start(), end, token, verdict, detail

    def is_direct_invocation(self, text: str, start: int, token: str) -> bool:
        if not token.endswith((".py", ".sh")):
            return False
        before = text[: start - len(path_prefix(text, start))]
        line_start = before.rfind("\n") + 1
        return bool(INTERPRETER_BEFORE.search(before[line_start:]))


def line_of(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def markdown_code_regions(text: str) -> list[tuple[int, int]]:
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
        elif fence is None:
            regions.extend((offset + m.start(2), offset + m.end(2)) for m in INLINE_CODE.finditer(line))
        offset += len(line)
    if fence is not None:
        regions.append((fence_start, len(text)))
    return regions


def in_regions(regions: list[tuple[int, int]], start: int, end: int) -> bool:
    return any(a <= start and end <= b for a, b in regions)


def scan_text(scanner: Scanner, text: str, kind: str, report: Report) -> list[Edit]:
    """Rewrite or report every token in a non-Python text file."""

    regions = markdown_code_regions(text) if kind == MARKDOWN else []
    edits: list[Edit] = []
    rel = scanner.rel
    tokens = [*scanner.module_tokens(text), *scanner.path_tokens(text)]
    for start, end, token, verdict, detail in sorted(tokens):
        if verdict == "keep":
            continue
        line = line_of(text, start)
        rewritable = kind == CODE or (kind == MARKDOWN and in_regions(regions, start, end))
        if kind == MARKDOWN and not rewritable:
            if verdict in (
                "module_invocation",
                "module_reference",
                "resource_path",
                "ambiguous_module",
                "ambiguous_path",
            ):
                report.inventory.append(
                    Finding(rel, line, "prose_mention", token, detail="Markdown prose is left as written")
                )
            continue
        if kind == OTHER:
            if verdict in (
                "module_invocation",
                "module_reference",
                "resource_path",
                "ambiguous_module",
                "ambiguous_path",
            ):
                report.unresolved.append(
                    Finding(rel, line, "unsupported_file_type", token, detail="no rewrite rule for this file type")
                )
            continue
        if verdict in ("module_invocation", "module_reference", "resource_path"):
            after = NEW_ROOT + token[len(OLD_ROOT) :]
            edits.append(Edit(start, start + len(OLD_ROOT), NEW_ROOT))
            report.rewrites.append(Finding(rel, line, verdict, token, after))
            if verdict == "resource_path" and scanner.is_direct_invocation(text, start, token):
                report.inventory.append(
                    Finding(rel, line, "direct_script_invocation", token, after, "runs a machinery file by path")
                )
        else:
            report.unresolved.append(Finding(rel, line, verdict, token, detail=detail))
    return edits


# -- Python files: inventory only ----------------------------------------


LOADER_NAMES = frozenset({"import_module", "run_module", "__import__"})
PATH_CALLS = frozenset({"Path", "PurePath", "PurePosixPath", "join", "joinpath"})


def _callee_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return ""


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
        if computed and owner not in (None, "root"):
            subtree = scanner.ownership.path_owner(path)
            if subtree == PRODUCT:
                return
        if owner is None and not computed:
            return
        detail = "path assembled from parts" + (" with a computed part" if computed else "")
        unresolved(node, "split_path_component", path + ("/…" if computed else ""), detail)

    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str) and id(node) not in skip:
            value = node.value
            parent = parents.get(id(node))
            if value in (OLD_ROOT, OLD_ROOT + "/"):
                components, computed = _following_components(node, parents)
                if components is not None:
                    check_split(node, components, computed)
                    continue
            if rp.MODULE_LITERAL.fullmatch(value):
                continue  # rename_python rewrites exact module strings
            if (
                isinstance(parent, ast.JoinedStr)
                and parent.values
                and parent.values[0] is node
                and re.fullmatch(r"scripts(?:\.[A-Za-z_]\w*)*\.", value)
                and scanner.ownership.subtree_owner(value.rstrip(".")) != PRODUCT
            ):
                unresolved(node, "computed_module_string", value + "{…}", "module name assembled at run time")
                continue
            for _s, _e, token, verdict, detail in [*scanner.module_tokens(value), *scanner.path_tokens(value)]:
                if verdict in ("keep", "unknown_module", "unknown_path"):
                    continue
                kind = (
                    "python_string_reference"
                    if verdict in ("module_invocation", "module_reference", "resource_path", "foreign_path")
                    else verdict
                )
                unresolved(node, kind, token, detail or "string in Python code; rename_python does not rewrite it")
        elif isinstance(node, (ast.List, ast.Tuple)):
            elts = node.elts
            for i, elt in enumerate(elts[:-1]):
                nxt = elts[i + 1]
                if isinstance(elt, ast.Constant) and elt.value == "-m" and not isinstance(nxt, ast.Constant):
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
        scanner = Scanner(ownership, rel)
        kind = classify(rel, data[:256])
        if kind == PYTHON:
            scan_python(scanner, data, report)
            continue
        edits = scan_text(scanner, text, kind, report)
        if not edits:
            continue
        report.files_changed.append(rel)
        for edit in sorted(edits, key=lambda e: e.start, reverse=True):
            text = text[: edit.start] + edit.replacement + text[edit.end :]
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
