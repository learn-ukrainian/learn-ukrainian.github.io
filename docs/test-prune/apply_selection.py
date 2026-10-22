"""Apply the #11226 test-prune selection to tests/ mechanically (phase B).

One-off record of how the phase A selection was applied; it is not part of the
production toolchain. Run from the repository root with the project interpreter.

    collect  --out F [PATH ...]   write {nodeid: {argname: repr(value)}} for collected tests
    apply    --before F           delete the selected tests, write the apply report
    verify   --before F --after G check that exactly the selected tests disappeared

`apply` works on the Python AST with exact line spans:

* a selected function or class method is removed together with its decorators and
  the comment lines directly above it (no blank line between);
* a selected parametrize case is removed from a literal argvalues list (and from a
  literal ``ids`` list) only when every collected case that shares that list entry
  is selected; any other case shape is skipped and reported;
* a test class left without test methods is removed when nothing else names it;
* a file whose every collected test is selected is deleted unless another file
  imports it;
* a module- or class-level helper, fixture or constant that was referenced before
  the apply and is referenced nowhere afterwards (in the file, or in another test
  file that names this module) is removed, repeated until nothing changes;
* finally ``ruff check --fix --select F401,F811,F841`` and ``--select I`` run on the
  touched files to drop the imports the deletions left unused.

A selected test that no longer exists on the current tree, is inherited rather
than defined where the selection names it, is still called or imported by kept
code, or whose removal would also remove an unselected test, is skipped and
listed in the report; no replacement is guessed.
"""

from __future__ import annotations

import argparse
import ast
import difflib
import gzip
import json
import re
import subprocess
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path

REPO = Path.cwd()
SELECTION = Path("docs/test-prune/2026-10-21-public-selection.jsonl")
DETAIL = Path("docs/test-prune/2026-10-21-public-selection-detail.jsonl.gz")
RESTORES = Path("docs/test-prune/2026-10-21-phase-b-restores.jsonl")
TEST_NAME = re.compile(r"\b(?:[A-Z]\w*::)?test_\w+")
WORD = re.compile(r"\w+")
PROTECTED_NAMES = {
    "pytestmark",
    "pytest_plugins",
    "collect_ignore",
    "collect_ignore_glob",
    "setup_module",
    "teardown_module",
    "setup_function",
    "teardown_function",
    "setup_method",
    "teardown_method",
    "setup_class",
    "teardown_class",
    "setUp",
    "tearDown",
    "setUpClass",
    "tearDownClass",
    "setUpModule",
    "tearDownModule",
    "asyncSetUp",
    "asyncTearDown",
    "load_tests",
}


# --------------------------------------------------------------------------- collect


class _Collector:
    def __init__(self) -> None:
        self.items: dict[str, dict[str, str]] = {}

    def pytest_collection_finish(self, session) -> None:  # pragma: no cover - pytest hook
        for item in session.items:
            callspec = getattr(item, "callspec", None)
            self.items[item.nodeid] = {name: repr(value) for name, value in callspec.params.items()} if callspec else {}


def cmd_collect(args: argparse.Namespace) -> int:
    import pytest

    collector = _Collector()
    paths = args.paths or ["tests"]
    code = pytest.main(["--collect-only", "-qq", "-p", "no:cacheprovider", *paths], plugins=[collector])
    Path(args.out).write_text(json.dumps(collector.items, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    print(f"collected {len(collector.items)} items, pytest exit {int(code)}")
    return 0 if int(code) in (0, 5) else int(code)


# --------------------------------------------------------------------------- helpers


def _base(nodeid: str) -> str:
    return nodeid.split("[", 1)[0]


def _load_selection() -> list[dict]:
    return [json.loads(line) for line in SELECTION.read_text(encoding="utf-8").splitlines() if line.strip()]


def _line_offsets(data: bytes) -> list[int]:
    offsets = [0]
    for index, byte in enumerate(data):
        if byte == 0x0A:
            offsets.append(index + 1)
    return offsets


def _is_blank(line: bytes) -> bool:
    return not line.strip()


def _is_comment(line: bytes) -> bool:
    return line.lstrip().startswith(b"#")


def _decorator_name(node: ast.expr) -> str:
    target = node.func if isinstance(node, ast.Call) else node
    parts: list[str] = []
    while isinstance(target, ast.Attribute):
        parts.append(target.attr)
        target = target.value
    if isinstance(target, ast.Name):
        parts.append(target.id)
    return ".".join(reversed(parts))


def _fixture_alias(node: ast.AST) -> str | None:
    for dec in getattr(node, "decorator_list", []):
        if isinstance(dec, ast.Call) and _decorator_name(dec).split(".")[-1] == "fixture":
            for keyword in dec.keywords:
                if keyword.arg == "name" and isinstance(keyword.value, ast.Constant):
                    return str(keyword.value.value)
    return None


def _is_autouse(node: ast.AST) -> bool:
    for dec in getattr(node, "decorator_list", []):
        if isinstance(dec, ast.Call) and _decorator_name(dec).split(".")[-1] == "fixture":
            for keyword in dec.keywords:
                if keyword.arg == "autouse" and not (
                    isinstance(keyword.value, ast.Constant) and keyword.value.value is False
                ):
                    return True
    return False


def _is_test_def(node: ast.AST) -> bool:
    return isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test")


def _is_test_class(node: ast.AST) -> bool:
    return isinstance(node, ast.ClassDef) and node.name.startswith("Test")


def _start_line(node: ast.AST, lines: list[bytes]) -> int:
    """First 1-based line of the node's block: decorators and attached comments."""
    start = min([node.lineno, *(dec.lineno for dec in getattr(node, "decorator_list", []))])
    indent = b" " * node.col_offset
    while start > 1 and _is_comment(lines[start - 2]) and lines[start - 2].startswith(indent + b"#"):
        start -= 1
    return start


@dataclass
class FileReport:
    file: str
    deleted: list[str] = field(default_factory=list)
    deleted_cases: list[str] = field(default_factory=list)
    skipped: dict[str, str] = field(default_factory=dict)
    removed_classes: list[str] = field(default_factory=list)
    removed_helpers: list[str] = field(default_factory=list)
    file_deleted: bool = False
    file_kept_reason: str = ""


# --------------------------------------------------------------------------- cross-file


class TestTree:
    """Word index of the Python files under tests/ that survive the apply, for cross-file checks."""

    def __init__(self, exclude: frozenset[str] = frozenset()) -> None:
        self.words: dict[str, set[str]] = {}
        self.texts: dict[str, str] = {}
        for path in sorted((REPO / "tests").rglob("*.py")):
            rel = path.relative_to(REPO).as_posix()
            if rel in exclude:
                continue
            self.texts[rel] = path.read_text(encoding="utf-8", errors="replace")
            self.words[rel] = set(WORD.findall(self.texts[rel]))

    def files_importing_module(self, rel: str) -> list[str]:
        """Other test files that import this module (statically or as a plugin by dotted name)."""
        dotted = rel[:-3].replace("/", ".")
        parent, stem = dotted.rsplit(".", 1)
        patterns = [
            rf"\bimport\s+{re.escape(dotted)}\b",
            rf"\bfrom\s+{re.escape(dotted)}\s+import\b",
            rf"\bfrom\s+{re.escape(parent)}\s+import\s+\(?[^)]*?\b{re.escape(stem)}\b",
            rf"\bfrom\s+\.{re.escape(stem)}\s+import\b",
            rf"\bfrom\s+{re.escape(stem)}\s+import\b",
            rf"[\"']{re.escape(dotted)}[\"']",
        ]
        return [
            other
            for other in self.files_naming_module(rel)
            if any(re.search(pattern, self.texts[other]) for pattern in patterns)
        ]

    def files_naming_module(self, rel: str) -> list[str]:
        stem = Path(rel).stem
        return [other for other, words in self.words.items() if other != rel and stem in words]

    def used_elsewhere(self, rel: str, name: str) -> bool:
        return any(name in self.words[other] for other in self.files_naming_module(rel))


# --------------------------------------------------------------------------- planning


def _index_defs(tree: ast.Module) -> tuple[dict[str, list[ast.AST]], dict[str, ast.ClassDef]]:
    """Map 'name' / 'Class::name' / 'A::B::name' to the defs that carry it."""
    defs: dict[str, list[ast.AST]] = defaultdict(list)
    classes: dict[str, ast.ClassDef] = {}

    def walk(body: list[ast.stmt], prefix: str) -> None:
        for stmt in body:
            if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
                defs[prefix + stmt.name].append(stmt)
            elif isinstance(stmt, ast.ClassDef):
                qual = prefix + stmt.name
                classes[qual] = stmt
                walk(stmt.body, qual + "::")

    walk(tree.body, "")
    return defs, classes


def _subclasses_inheriting(classes: dict[str, ast.ClassDef], owner: str, method: str) -> list[str]:
    """Top-level classes in the file that inherit `method` from `owner` without overriding it."""
    top = {qual: node for qual, node in classes.items() if "::" not in qual}
    family = {owner.split("::")[-1]}
    changed = True
    while changed:
        changed = False
        for node in top.values():
            bases = {base.id for base in node.bases if isinstance(base, ast.Name)}
            if node.name not in family and bases & family:
                family.add(node.name)
                changed = True
    return [
        qual
        for qual, node in top.items()
        if node.name in family
        and qual != owner
        and not any(
            isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)) and stmt.name == method for stmt in node.body
        )
    ]


def _parametrize_decorators(node: ast.AST) -> list[tuple[list[str], ast.Call]]:
    found: list[tuple[list[str], ast.Call]] = []
    for dec in node.decorator_list:
        if isinstance(dec, ast.Call) and _decorator_name(dec).endswith("mark.parametrize") and dec.args:
            first = dec.args[0]
            names: list[str] = []
            if isinstance(first, ast.Constant) and isinstance(first.value, str):
                names = [part.strip() for part in first.value.split(",") if part.strip()]
            elif isinstance(first, (ast.List, ast.Tuple)):
                names = [elt.value for elt in first.elts if isinstance(elt, ast.Constant)]
            found.append((names, dec))
    return found


def _argvalues(dec: ast.Call) -> ast.expr | None:
    if len(dec.args) > 1:
        return dec.args[1]
    for keyword in dec.keywords:
        if keyword.arg == "argvalues":
            return keyword.value
    return None


def _ids(dec: ast.Call) -> ast.expr | None:
    for keyword in dec.keywords:
        if keyword.arg == "ids":
            return keyword.value
    return None


def _tidy_parametrize_separators(data: bytes) -> bytes:
    """Collapse the ", ]" / ", )" that adjacent entry removals leave on a parametrize line."""
    lines = data.decode("utf-8").splitlines(keepends=True)
    for index, line in enumerate(lines):
        if "mark.parametrize(" in line:
            lines[index] = re.sub(r",\s+\)", ",)", re.sub(r",\s+\]", "]", line))
    return "".join(lines).encode("utf-8")


def _literal_case(elt: ast.expr, names: list[str]) -> dict[str, str] | None:
    """{argname: repr(value)} for a literal parametrize entry, else None."""
    if isinstance(elt, ast.Call) and _decorator_name(elt).endswith("param"):
        if elt.keywords and any(keyword.arg not in ("id", "marks") for keyword in elt.keywords):
            return None
        parts = list(elt.args)
    elif len(names) == 1:
        parts = [elt]
    elif isinstance(elt, (ast.Tuple, ast.List)):
        parts = list(elt.elts)
    else:
        return None
    if len(parts) != len(names):
        return None
    try:
        return {name: repr(ast.literal_eval(part)) for name, part in zip(names, parts, strict=True)}
    except (ValueError, TypeError, SyntaxError, MemoryError, RecursionError):
        return None


def _element_range(elt: ast.expr, data: bytes, offsets: list[int]) -> tuple[int, int]:
    """Byte range of a list element plus its trailing comma (whole lines when it owns them)."""
    start = offsets[elt.lineno - 1] + elt.col_offset
    end = offsets[elt.end_lineno - 1] + elt.end_col_offset
    cursor = end
    while cursor < len(data) and data[cursor : cursor + 1] in (b" ", b"\t"):
        cursor += 1
    trailing_comma = data[cursor : cursor + 1] == b","
    if trailing_comma:
        end = cursor + 1
    line_start = offsets[elt.lineno - 1]
    line_end = data.find(b"\n", end)
    line_end = len(data) if line_end == -1 else line_end
    owns_lines = not data[line_start:start].strip() and (
        not data[end:line_end].strip() or data[end:line_end].strip().startswith(b"#")
    )
    if owns_lines:
        return line_start, min(line_end + 1, len(data))
    after = end
    while after < len(data) and data[after : after + 1] == b" ":
        after += 1
    if not trailing_comma or data[after : after + 1] in (b"]", b")"):
        # Last entry on its line: drop the separator before it instead of leaving ", ]".
        before = start
        while before > 0 and data[before - 1 : before] == b" ":
            before -= 1
        if data[before - 1 : before] == b",":
            return before - 1, after if trailing_comma else end
    return start, after


def _block_range(start_line: int, end_line: int, lines: list[bytes], offsets: list[int]) -> tuple[int, int]:
    """Byte range of whole lines start..end plus the blank lines that separated them."""
    first = start_line
    while first > 1 and _is_blank(lines[first - 2]):
        first -= 1
    last = end_line
    if first == start_line:
        while last < len(lines) and _is_blank(lines[last]):
            last += 1
    end = offsets[last] if last < len(offsets) else sum(len(line) for line in lines)
    return offsets[first - 1], end


def _apply_ranges(data: bytes, ranges: list[tuple[int, int]]) -> bytes:
    merged: list[tuple[int, int]] = []
    for start, end in sorted(ranges):
        if merged and start < merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))
    out = bytearray()
    cursor = 0
    for start, end in merged:
        out += data[cursor:start]
        cursor = end
    out += data[cursor:]
    return bytes(out)


def _ensure_class_bodies(data: bytes) -> bytes:
    """Insert `pass` into any class whose body the removals emptied."""
    text = data.decode("utf-8")
    while True:
        try:
            ast.parse(text)
            return text.encode("utf-8")
        except SyntaxError as error:
            if "expected an indented block" not in str(error.msg) or error.lineno is None:
                raise
            lines = text.splitlines(keepends=True)
            header = error.lineno - 2
            while header >= 0 and (not lines[header].strip() or lines[header].lstrip().startswith("#")):
                header -= 1
            indent = len(lines[header]) - len(lines[header].lstrip()) + 4
            lines.insert(header + 1, " " * indent + "pass\n")
            text = "".join(lines)


def _helper_candidates(tree: ast.Module) -> list[tuple[str, ast.AST, ast.ClassDef | None]]:
    """(name, node, owning test class or None) for removable non-test definitions."""
    found: list[tuple[str, ast.AST, ast.ClassDef | None]] = []

    def consider(stmt: ast.stmt, member: ast.ClassDef | None) -> None:
        if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            name = stmt.name
            if (
                name.startswith(("test", "Test", "pytest_", "__"))
                or name in PROTECTED_NAMES
                or _is_autouse(stmt)
                or (_is_test_class(stmt))
            ):
                return
            found.append((name, stmt, member))
        elif member is None and isinstance(stmt, (ast.Assign, ast.AnnAssign)):
            targets = stmt.targets if isinstance(stmt, ast.Assign) else [stmt.target]
            if len(targets) == 1 and isinstance(targets[0], ast.Name):
                name = targets[0].id
                if not name.startswith("__") and name not in PROTECTED_NAMES:
                    found.append((name, stmt, member))

    for stmt in tree.body:
        consider(stmt, None)
        if _is_test_class(stmt):
            for inner in stmt.body:
                consider(inner, stmt)
    return found


def _has_foreign_bases(node: ast.ClassDef) -> bool:
    return any(_decorator_name(base) not in ("object", "unittest.TestCase", "TestCase") for base in node.bases)


def _remove_unused_helpers(
    rel: str, original: str, data: bytes, report: FileReport, tests: TestTree, original_tests: TestTree
) -> bytes:
    """Remove helpers that the deletions left unreferenced, until a fixpoint.

    "Referenced before" counts this file and every other test file before the apply,
    including files the apply deletes; "referenced after" counts surviving files only.
    """
    original_tree = ast.parse(original)
    original_lines = original.encode("utf-8").splitlines(keepends=True)
    before_spans: dict[str, list[tuple[int, int]]] = defaultdict(list)
    for name, node, _owner in _helper_candidates(original_tree):
        before_spans[name].append((_start_line(node, original_lines), node.end_lineno))

    def used_before(name: str) -> bool:
        lines = original.splitlines(keepends=True)
        spans = before_spans.get(name, [])
        kept = [line for number, line in enumerate(lines, 1) if not any(a <= number <= b for a, b in spans)]
        return name in WORD.findall("".join(kept)) or original_tests.used_elsewhere(rel, name)

    used_before_cache: dict[str, bool] = {}
    while True:
        text = data.decode("utf-8")
        tree = ast.parse(text)
        lines = data.splitlines(keepends=True)
        offsets = _line_offsets(data)
        removable: list[tuple[int, int]] = []
        for name, node, member in _helper_candidates(tree):
            usage_names = [name]
            alias = _fixture_alias(node)
            if alias:
                usage_names.append(alias)
            start = _start_line(node, lines)
            body_text = "".join(
                line.decode("utf-8") for number, line in enumerate(lines, 1) if not start <= number <= node.end_lineno
            )
            words_after = set(WORD.findall(body_text))
            if any(usage in words_after for usage in usage_names):
                continue
            key = "|".join(usage_names)
            if key not in used_before_cache:
                used_before_cache[key] = any(used_before(usage) for usage in usage_names)
            if not used_before_cache[key]:
                continue  # already unused before the apply: not ours to remove
            if any(tests.used_elsewhere(rel, usage) for usage in usage_names):
                continue
            if (
                member is not None
                and _has_foreign_bases(member)
                and any(usage in words for other, words in tests.words.items() if other != rel for usage in usage_names)
            ):
                # A member of a class with imported bases may be a template-method override.
                continue
            removable.append(_block_range(start, node.end_lineno, lines, offsets))
            report.removed_helpers.append(name)
        if not removable:
            return data
        data = _ensure_class_bodies(_apply_ranges(data, removable))


def _references_outside(tree: ast.Module, spans: list[tuple[int, int]]) -> set[tuple[str, str]]:
    """('name', id) loads and ('attribute', attr) accesses on lines outside the given spans."""
    found: set[tuple[str, str]] = set()
    for node in ast.walk(tree):
        line = getattr(node, "lineno", None)
        if line is None or any(start <= line <= end for start, end in spans):
            continue
        if isinstance(node, ast.Name):
            found.add(("name", node.id))
        elif isinstance(node, ast.Attribute):
            found.add(("attribute", node.attr))
    return found


def plan_and_apply(
    row: dict, before: dict[str, dict[str, int]], tests: TestTree, original_tests: TestTree
) -> FileReport:
    rel = row["file"]
    report = FileReport(rel)
    path = REPO / rel
    original = path.read_text(encoding="utf-8")
    data = original.encode("utf-8")
    tree = ast.parse(original)
    lines = data.splitlines(keepends=True)
    offsets = _line_offsets(data)
    defs, classes = _index_defs(tree)
    collected = {nodeid: indices for nodeid, indices in before.items() if nodeid.split("::", 1)[0] == rel}
    collected_bases = {_base(nodeid).split("::", 1)[1] for nodeid in collected}
    selected = set(row.get("delete", {}))
    ranges: list[tuple[int, int]] = []

    removed_nodes: set[int] = set()
    planned: dict[str, list[ast.AST]] = {}
    for name in sorted(selected):
        if name not in collected_bases:
            report.skipped[name] = "not collected on current main (moved, renamed or removed since phase A)"
            continue
        nodes = defs.get(name)
        if not nodes:
            report.skipped[name] = "not defined at that path (inherited or generated); not removed"
            continue
        if "::" in name:
            owner, method = name.rsplit("::", 1)
            inheritors = [
                sub for sub in _subclasses_inheriting(classes, owner, method) if f"{sub}::{method}" not in selected
            ]
            inheritors = [sub for sub in inheritors if f"{sub}::{method}" in collected_bases]
            if inheritors:
                report.skipped[name] = "unselected subclasses inherit it: " + ", ".join(inheritors)
                continue
        planned[name] = nodes

    # A selected test that kept code still calls (as a helper) or imports stays.
    importers = tests.files_importing_module(rel)
    changed = True
    while changed:
        changed = False
        spans = [(node.lineno, node.end_lineno) for nodes in planned.values() for node in nodes]
        live = _references_outside(tree, spans)
        for name in sorted(planned):
            short = name.rsplit("::", 1)[-1]
            kind = "attribute" if "::" in name else "name"
            if (kind, short) in live or any(short in tests.words[other] for other in importers):
                report.skipped[name] = "kept code still references it (helper call or import); not removed"
                del planned[name]
                changed = True
    for name, nodes in sorted(planned.items()):
        for node in nodes:
            ranges.append(_block_range(_start_line(node, lines), node.end_lineno, lines, offsets))
            removed_nodes.add(id(node))
        report.deleted.append(name)

    # Parametrize cases inside kept functions.
    cases_by_function: dict[str, set[str]] = defaultdict(set)
    for case in row.get("delete_cases", {}):
        cases_by_function[case.split("[", 1)[0]].add(case)
    for function, cases in sorted(cases_by_function.items()):
        if function in selected:
            continue
        nodes = defs.get(function)
        if not nodes:
            for case in cases:
                report.skipped[case] = "parametrized function not defined at that path"
            continue
        node = nodes[-1]
        function_items = {
            nodeid.split("::", 1)[1]: params
            for nodeid, params in collected.items()
            if _base(nodeid).split("::", 1)[1] == function
        }
        remaining = set(cases)
        for case in sorted(cases):
            if case not in function_items:
                report.skipped[case] = "case not collected on current main"
                remaining.discard(case)
        for names, dec in _parametrize_decorators(node):
            values = _argvalues(dec)
            if not names or not isinstance(values, (ast.List, ast.Tuple)):
                continue
            ids = _ids(dec)
            if isinstance(ids, (ast.List, ast.Tuple)) and (
                len(ids.elts) != len(values.elts) or any(isinstance(elt, ast.Starred) for elt in values.elts)
            ):
                continue
            element_values = [_literal_case(elt, names) for elt in values.elts]
            for index, element in enumerate(element_values):
                if element is None or element_values.count(element) > 1:
                    continue
                members = {
                    case_id
                    for case_id, params in function_items.items()
                    if all(params.get(name) == value for name, value in element.items())
                }
                if members and members <= remaining:
                    ranges.append(_element_range(values.elts[index], data, offsets))
                    if isinstance(ids, (ast.List, ast.Tuple)):
                        ranges.append(_element_range(ids.elts[index], data, offsets))
                    remaining -= members
                    report.deleted_cases.extend(sorted(members))
        for case in sorted(remaining):
            report.skipped[case] = (
                "case is not a removable literal parametrize entry (shared or generated); not removed"
            )

    # Test classes left without any test method.
    for qual, node in classes.items():
        if not _is_test_class(node) or "::" in qual:
            continue
        tests_left = [stmt for stmt in node.body if _is_test_def(stmt) and id(stmt) not in removed_nodes]
        had_tests = any(_is_test_def(stmt) for stmt in node.body)
        if had_tests and not tests_left:
            others = original.splitlines()
            span = range(_start_line(node, lines), node.end_lineno + 1)
            outside = "\n".join(line for number, line in enumerate(others, 1) if number not in span)
            if node.name in WORD.findall(outside) or tests.used_elsewhere(rel, node.name):
                continue
            ranges.append(_block_range(_start_line(node, lines), node.end_lineno, lines, offsets))
            report.removed_classes.append(qual)

    every_test_selected = bool(collected) and all(
        _base(nodeid).split("::", 1)[1] in report.deleted or nodeid.split("::", 1)[1] in report.deleted_cases
        for nodeid in collected
    )
    if every_test_selected:
        importers = tests.files_importing_module(rel)
        if importers:
            report.file_kept_reason = "every test deleted, but another test file imports it: " + ", ".join(importers)
        else:
            path.unlink()
            report.file_deleted = True
            return report

    if not ranges:
        return report
    data = _ensure_class_bodies(_apply_ranges(data, ranges))
    if report.deleted_cases:
        data = _tidy_parametrize_separators(data)
    data = _remove_unused_helpers(rel, original, data, report, tests, original_tests)
    data = data.rstrip() + b"\n"
    path.write_bytes(data)
    return report


def cmd_apply(args: argparse.Namespace) -> int:
    before = json.loads(Path(args.before).read_text(encoding="utf-8"))
    restores: dict[str, set[str]] = defaultdict(set)
    whole_files: set[str] = set()
    for line in RESTORES.read_text(encoding="utf-8").splitlines():
        if line.strip():
            nodeid = json.loads(line)["nodeid"]
            if "::" in nodeid:
                file, name = nodeid.split("::", 1)
                restores[file].add(name)
            else:
                whole_files.add(nodeid)  # tooling runs the file by path: keep it whole
    rows = []
    for row in _load_selection():
        if row["file"] in whole_files:
            rows.append({"file": row["file"], "delete": {}, "delete_cases": {}})
            continue
        kept = restores.get(row["file"], set())
        rows.append({**row, "delete": {name: cls for name, cls in row.get("delete", {}).items() if name not in kept}})
    # Files whose every collected test is selected; references from them do not keep anything.
    bases_by_file: dict[str, set[str]] = defaultdict(set)
    for nodeid in before:
        file, rest = _base(nodeid).split("::", 1)
        bases_by_file[file].add(rest)
    emptied = frozenset(
        row["file"] for row in rows if bases_by_file[row["file"]] and bases_by_file[row["file"]] <= set(row["delete"])
    )
    while True:
        tests = TestTree(exclude=emptied)
        held = {file for file in emptied if tests.files_importing_module(file)}
        if not held:
            break
        emptied -= held
    original_tests = TestTree()
    reports = [plan_and_apply(row, before, tests, original_tests) for row in rows]
    touched = [report.file for report in reports if not report.file_deleted and (REPO / report.file).exists()]
    for select in ("F401,F811,F841", "I"):
        # Imports the deletions left unused, then the import order those removals disturb.
        subprocess.run(
            [sys.executable, "-m", "ruff", "check", "--quiet", "--fix", "--select", select, *touched],
            cwd=REPO,
            check=False,
            timeout=600,
        )
    for file in touched:
        # Ruff can leave blank lines at the end of a file whose last statement it removed.
        target = REPO / file
        content = target.read_bytes()
        if content.rstrip() + b"\n" != content:
            target.write_bytes(content.rstrip() + b"\n")
    payload = [report.__dict__ for report in reports]
    Path(args.report).write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    deleted = sum(len(report.deleted) for report in reports)
    cases = sum(len(report.deleted_cases) for report in reports)
    skipped = sum(len(report.skipped) for report in reports)
    print(
        f"files {len(reports)}; deleted functions {deleted}; deleted cases {cases}; skipped {skipped}; "
        f"files deleted {sum(report.file_deleted for report in reports)}; "
        f"helpers removed {sum(len(report.removed_helpers) for report in reports)}"
    )
    return 0


# --------------------------------------------------------------------------- check-covered


def _other_delete_votes(row: dict) -> list[str]:
    votes = dict(part.split("=", 1) for part in row.get("votes", "").split(",") if "=" in part)
    return sorted({vote for vote in votes.values() if vote.startswith("D-") and vote != "D-COVERED"})


def cmd_check_covered(args: argparse.Namespace) -> int:
    """Verify every D-COVERED claim against the selection; print the restores it requires.

    A D-COVERED deletion stands when a sibling it names exists on the current tree and is
    kept, or reaches a kept test (or a deletion of another class) through other D-COVERED
    deletions. A claim whose named sibling exists nowhere is restored unless another vote
    gave the test an independent delete class. A chain of D-COVERED deletions that only
    cover each other gets one representative restored per chain (the most-named member
    without an independent delete vote).
    """
    before = json.loads(Path(args.before).read_text(encoding="utf-8"))
    names_by_file: dict[str, set[str]] = defaultdict(set)
    for nodeid in before:
        file, rest = _base(nodeid).split("::", 1)
        names_by_file[file].add(rest)
    rows = [json.loads(line) for line in gzip.decompress(DETAIL.read_bytes()).decode("utf-8").splitlines()]
    deleted = {row["nodeid"]: row for row in rows if row["scope"] == "function" and row["verdict"] == "delete"}

    def resolve(file: str, name: str) -> list[str]:
        short = name.split("::")[-1]
        local = names_by_file.get(file, set())
        exact = [f"{file}::{base}" for base in local if base == name or base.split("::")[-1] == short]
        if exact:
            return exact
        fuzzy = [
            f"{file}::{base}"
            for base in local
            if base.split("::")[-1].startswith(short)
            or difflib.SequenceMatcher(None, short, base.split("::")[-1]).ratio() >= 0.9
        ]
        if len(fuzzy) == 1:
            return fuzzy
        return [
            f"{other}::{base}"
            for other, bases in names_by_file.items()
            for base in bases
            if base.split("::")[-1] == short
        ]

    targets: dict[str, list[str]] = {}
    for nodeid, row in deleted.items():
        if row["class"] != "D-COVERED":
            continue
        named = set(TEST_NAME.findall(row["reason"])) - {nodeid.split("::")[-1]}
        targets[nodeid] = sorted({hit for name in named for hit in resolve(row["file"], name) if hit != nodeid})

    def reaches_cover(nodeid: str, seen: set[str]) -> bool:
        if nodeid not in deleted or deleted[nodeid]["class"] != "D-COVERED":
            return True
        if nodeid in seen:
            return False
        seen.add(nodeid)
        return any(reaches_cover(target, seen) for target in targets[nodeid])

    stats: Counter[str] = Counter()
    unverified: list[str] = []
    dead: list[str] = []
    for nodeid, hits in targets.items():
        if not hits:
            stats["no named sibling exists"] += 1
            unverified.append(nodeid)
        elif any(hit not in deleted for hit in hits):
            stats["named sibling kept"] += 1
        elif reaches_cover(nodeid, set()):
            stats["covered through other deletions"] += 1
        else:
            stats["chain reaches no kept test"] += 1
            dead.append(nodeid)
    restores = [
        {"nodeid": nodeid, "source": "covered-unverified", "reason": "D-COVERED names no sibling that exists on main"}
        for nodeid in sorted(unverified)
        if not _other_delete_votes(deleted[nodeid])
    ]
    restored = {row["nodeid"] for row in restores}
    adjacency: dict[str, set[str]] = defaultdict(set)
    for nodeid in dead:
        for target in targets[nodeid]:
            adjacency[nodeid].add(target)
            adjacency[target].add(nodeid)
    seen: set[str] = set()
    chains = 0
    for start in sorted(dead):
        if start in seen:
            continue
        chains += 1
        stack, chain = [start], []
        while stack:
            node = stack.pop()
            if node not in seen:
                seen.add(node)
                chain.append(node)
                stack.extend(adjacency[node])
        if restored & set(chain):
            continue
        named = Counter(target for node in chain for target in targets.get(node, []))
        for node in sorted(chain, key=lambda node: (-named[node], node)):
            if node in deleted and not _other_delete_votes(deleted[node]):
                restores.append(
                    {
                        "nodeid": node,
                        "source": "covered-dead-chain",
                        "reason": f"D-COVERED chain of {len(chain)} deletions covers no kept test; one restored",
                    }
                )
                break
    for key, value in sorted(stats.items()):
        print(f"{key}: {value}")
    print(f"dead chains: {chains}; restores: {len(restores)}")
    Path(args.out).write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in restores), encoding="utf-8")
    return 0


# --------------------------------------------------------------------------- verify


def _params_key(params: dict[str, str]) -> str:
    return json.dumps(params, sort_keys=True, ensure_ascii=False)


def cmd_verify(args: argparse.Namespace) -> int:
    before = json.loads(Path(args.before).read_text(encoding="utf-8"))
    after = json.loads(Path(args.after).read_text(encoding="utf-8"))
    reports = json.loads(Path(args.report).read_text(encoding="utf-8"))
    deleted = {f"{report['file']}::{name}" for report in reports for name in report["deleted"]}
    deleted_cases = {f"{report['file']}::{case}" for report in reports for case in report["deleted_cases"]}
    case_functions = {_base(nodeid) for nodeid in deleted_cases}

    def bucket(items: dict[str, dict[str, int]]) -> dict[str, set[str]]:
        grouped: dict[str, set[str]] = defaultdict(set)
        for nodeid in items:
            grouped[_base(nodeid)].add(nodeid)
        return grouped

    before_groups, after_groups = bucket(before), bucket(after)
    problems: list[str] = []
    for base in sorted(set(before_groups) | set(after_groups)):
        old, new = before_groups.get(base, set()), after_groups.get(base, set())
        if base in deleted:
            if new:
                problems.append(f"still collected: {base}")
        elif base in case_functions:
            # Generated ids (value0, value1, ...) renumber after a removal, so compare the
            # multiset of collected parameter values: before minus the selected cases.
            wanted = Counter(_params_key(before[nodeid]) for nodeid in old if nodeid not in deleted_cases)
            kept = Counter(_params_key(after[nodeid]) for nodeid in new)
            if kept != wanted:
                problems.append(
                    f"case parameters {base}: missing {sorted((wanted - kept).elements())[:3]}, "
                    f"unexpected {sorted((kept - wanted).elements())[:3]}"
                )
        elif old != new:
            problems.append(f"unselected change {base}: -{sorted(old - new)[:3]} +{sorted(new - old)[:3]}")
    removed = len(before) - len(after)
    print(f"before {len(before)} items, after {len(after)} items, removed {removed}; problems {len(problems)}")
    for problem in problems[:200]:
        print("  " + problem)
    return 1 if problems else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    collect = sub.add_parser("collect", help="collect node ids and parametrize values (repr) to JSON")
    collect.add_argument("--out", required=True)
    collect.add_argument("paths", nargs="*")
    apply = sub.add_parser("apply", help="delete the selected tests in place")
    apply.add_argument("--before", required=True, help="collect output for the tree before the apply")
    apply.add_argument("--report", required=True)
    covered = sub.add_parser("check-covered", help="verify D-COVERED claims and write the restores they need")
    covered.add_argument("--before", required=True)
    covered.add_argument("--out", required=True)
    verify = sub.add_parser("verify", help="check that exactly the selected tests disappeared")
    verify.add_argument("--before", required=True)
    verify.add_argument("--after", required=True)
    verify.add_argument("--report", required=True)
    args = parser.parse_args(argv)
    return {"collect": cmd_collect, "apply": cmd_apply, "check-covered": cmd_check_covered, "verify": cmd_verify}[
        args.command
    ](args)


if __name__ == "__main__":
    sys.exit(main())
