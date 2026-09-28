"""Keep merge-queue docs test reads covered when test modules change (#9073).

This deliberately conservative source scan includes concrete tracked Markdown
references and docs subtree globs. A harmless reference may force full CI;
missing a real read can let a docs-only queue entry skip its guard.
"""

from __future__ import annotations

import ast
import re
import subprocess
from pathlib import Path

import pytest

from scripts.ci.classify_changes import (
    _QUEUE_TEST_READ_DOC_PATHS,
    _QUEUE_TEST_READ_DOC_PREFIXES,
)

pytestmark = [pytest.mark.repo_invariant, pytest.mark.repo_wide]

ROOT = Path(__file__).resolve().parents[1]
_DOC_LITERAL = re.compile(r"(?<![\w/])docs/[\w.*{}\-/]+")
_DOC_JOIN = re.compile(r"['\"]docs['\"]\s*/\s*['\"]([\w.*-]+)['\"]")
_DOC_JOIN_PART = re.compile(r"/\s*['\"]([\w.*-]+)['\"]")
_REPO_ROOT_EXPRESSION = re.compile(r"\b(?:REPO|ROOT|PROJECT_ROOT|REPO_ROOT)\b|Path\(")
# A docs/ Markdown edit does not set docs_reads_content; that marker is run
# only when a curriculum/ or wiki/ path is present.
_DOCS_LANE_MARKERS = ("repo_wide", "docs_skills")


def _is_docs_lane_marked(tree: ast.Module) -> bool:
    """Only a module marker covers every test in that module."""
    for node in tree.body:
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            if any(isinstance(target, ast.Name) and target.id == "pytestmark" for target in targets):
                value = ast.unparse(node.value)
                return any(f"pytest.mark.{marker}" in value for marker in _DOCS_LANE_MARKERS)
    return False


def _tracked_docs() -> set[str]:
    names = subprocess.check_output(
        ["git", "ls-tree", "-r", "--name-only", "HEAD"],
        cwd=ROOT,
        text=True,
        timeout=120,
    ).splitlines()
    return {name for name in names if name.startswith("docs/") and name.endswith(".md")}


def _references(source: str, tracked_docs: set[str]) -> set[str]:
    tree = ast.parse(source)
    found: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Constant) or not isinstance(node.value, str):
            continue
        for match in _DOC_LITERAL.finditer(node.value):
            path = match.group().rstrip(".,")
            if "*" in path and path.endswith(".md"):
                prefix = path.split("*", 1)[0]
                if any(doc.startswith(prefix) for doc in tracked_docs):
                    found.add(prefix)
            elif path in tracked_docs:
                found.add(path)

    # Also catch Path joins such as ROOT / "docs" / "runbooks" / "x.md".
    for match in _DOC_JOIN.finditer(source):
        line_start = source.rfind("\n", 0, match.start()) + 1
        if not _REPO_ROOT_EXPRESSION.search(source[line_start : match.start()]):
            continue
        tail = source[
            match.start() : source.find("\n", match.start()) if "\n" in source[match.start() :] else len(source)
        ]
        parts = _DOC_JOIN_PART.findall(tail)
        path = "docs/" + "/".join(parts)
        if path in tracked_docs:
            found.add(path)
        elif any(doc.startswith(path + "/") for doc in tracked_docs):
            found.add(path + "/")

    # A named docs root followed by glob/rglob reads every matching Markdown
    # file, including files added after this invariant was written.
    docs_roots: dict[str, str] = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            expression = ast.unparse(node.value)
            match = re.search(
                r"\b(?:REPO|ROOT|PROJECT_ROOT|REPO_ROOT)\s*/\s*['\"]docs['\"]"
                r"|Path\(['\"]docs['\"]\)",
                expression,
            )
            if match:
                parts = _DOC_JOIN_PART.findall(expression[match.start() :])
                docs_roots[node.targets[0].id] = "docs/" + "/".join(parts[1:] if parts else [])
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        if node.func.attr not in {"glob", "rglob"} or not node.args:
            continue
        if isinstance(node.func.value, ast.Name) and node.func.value.id in docs_roots:
            if (
                isinstance(node.args[0], ast.Constant)
                and isinstance(node.args[0].value, str)
                and ("*" in node.args[0].value or node.args[0].value.endswith(".md"))
            ):
                prefix = docs_roots[node.func.value.id].rstrip("/") + "/"
                if any(doc.startswith(prefix) for doc in tracked_docs):
                    found.add(prefix)
        elif (
            isinstance(node.func.value, ast.Call)
            and isinstance(node.func.value.func, ast.Name)
            and node.func.value.func.id == "Path"
            and node.func.value.args
            and isinstance(node.func.value.args[0], ast.Constant)
            and node.func.value.args[0].value == "docs"
            and isinstance(node.args[0], ast.Constant)
            and isinstance(node.args[0].value, str)
            and ("*" in node.args[0].value or node.args[0].value.endswith(".md"))
        ):
            found.add("docs/")
    if re.search(r"Path\(['\"]docs['\"]\)", source) and re.search(r"\.(?:rglob|glob)\(", source):
        found.add("docs/")
    return found


def _scan_doc_references() -> dict[str, set[str]]:
    tracked = _tracked_docs()
    modules = sorted((*ROOT.joinpath("tests").rglob("test_*.py"), *ROOT.joinpath("scripts").rglob("test_*.py")))
    hits: dict[str, set[str]] = {}
    for module in modules:
        source = module.read_text(encoding="utf-8")
        if "docs" not in source:
            continue
        tree = ast.parse(source)
        if _is_docs_lane_marked(tree):
            continue
        references = _references(source, tracked)
        if references:
            hits[module.relative_to(ROOT).as_posix()] = references
    return hits


def test_queue_docs_read_allowlist_covers_unmarked_test_references() -> None:
    missing = [
        f"{module}: {path}"
        for module, paths in _scan_doc_references().items()
        for path in sorted(paths)
        if path not in _QUEUE_TEST_READ_DOC_PATHS and not path.startswith(_QUEUE_TEST_READ_DOC_PREFIXES)
    ]
    assert not missing, "Uncovered docs references in test modules:\n" + "\n".join(missing)


def test_scan_catches_literal_join_and_subtree_glob() -> None:
    tracked = {"docs/runbooks/example.md", "docs/research/bio/person.md"}
    source = """
ROOT = Path(__file__).resolve().parents[1]
RUNBOOK = ROOT / "docs" / "runbooks" / "example.md"
DOCS = ROOT / "docs"
for path in DOCS.rglob("*.md"):
    path.read_text()
for path in ROOT.glob("docs/research/bio/**/*.md"):
    path.read_text()
for path in Path("docs").rglob("*.md"):
    path.read_text()
"""
    assert _references(source, tracked) == {
        "docs/runbooks/example.md",
        "docs/",
        "docs/research/bio/",
    }


def test_only_markers_run_for_plain_docs_entries_exempt_a_module() -> None:
    assert _is_docs_lane_marked(ast.parse("pytestmark = pytest.mark.repo_wide"))
    assert _is_docs_lane_marked(ast.parse("pytestmark = [pytest.mark.docs_skills]"))
    assert not _is_docs_lane_marked(ast.parse("pytestmark = pytest.mark.reads_content"))
