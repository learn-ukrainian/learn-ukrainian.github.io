#!/usr/bin/env python3
"""Structural SQLite constructor boundary over scripts/ (#9609, RB-1 §9).

Every constructor reference is forbidden outside the explicit writer manifest
and the one tested reader boundary, independent of target, mode, or call shape.
Module objects may not escape into assignments/containers/calls: otherwise an
alias could hide a constructor. Dynamic imports of SQLite are refused too.
Code built from strings (exec) is out of scope. Test fixture opens are outside
this scan; a separate runtime guard must reject writable real data/*.db opens.
"""

from __future__ import annotations

import argparse
import ast
import json
import subprocess
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
READER_BOUNDARY = "scripts/lib/readonly_sqlite.py"
WRITER_MANIFEST = Path(__file__).with_name("sqlite_writer_allowlist.json")
SQLITE_MODULES = frozenset({"sqlite3", "sqlite3.dbapi2", "_sqlite3"})
CONSTRUCTORS = frozenset({"connect", "Connection"})


@dataclass(frozen=True)
class AllowedWriter:
    path: str
    target_db: str
    reason: str
    calls: tuple[str, ...]


def load_allowlist() -> tuple[AllowedWriter, ...]:
    return tuple(
        AllowedWriter(**{**row, "calls": tuple(row["calls"])}) for row in json.loads(WRITER_MANIFEST.read_text())
    )


@dataclass(frozen=True)
class Finding:
    rel_path: str
    line_no: int
    snippet: str
    kind: str = "constructor reference"


def _dotted(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return f"{_dotted(node.value)}.{node.attr}"
    return ""


def classify_source(source: str, rel_path: str) -> list[Finding]:
    """Match syntax references, never infer database paths or caller arguments."""
    tree = ast.parse(source, filename=rel_path)
    parents = {child: node for node in ast.walk(tree) for child in ast.iter_child_nodes(node)}
    modules = set(SQLITE_MODULES)
    loaders = {"__import__", "importlib.import_module"}
    findings: dict[int, Finding] = {}

    def report(node: ast.AST) -> None:
        line = node.lineno
        findings[line] = Finding(rel_path, line, source.splitlines()[line - 1].strip())

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name in SQLITE_MODULES:
                    modules.add(alias.asname or alias.name)
                if alias.name == "importlib":
                    loaders.add(f"{alias.asname or alias.name}.import_module")
                if alias.name == "builtins":
                    loaders.add(f"{alias.asname or alias.name}.__import__")
        elif isinstance(node, ast.ImportFrom):
            if node.module in SQLITE_MODULES:
                for alias in node.names:
                    if alias.name in CONSTRUCTORS or alias.name == "*":
                        report(node)
                    elif node.module == "sqlite3" and alias.name == "dbapi2":
                        modules.add(alias.asname or alias.name)
            elif node.module == "importlib":
                for alias in node.names:
                    if alias.name == "import_module":
                        loaders.add(alias.asname or alias.name)
            elif node.module == "builtins":
                for alias in node.names:
                    if alias.name == "__import__":
                        loaders.add(alias.asname or alias.name)

    has_sqlite_literal = any(
        isinstance(node, ast.Constant) and isinstance(node.value, str) and node.value in SQLITE_MODULES
        for node in ast.walk(tree)
    )
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Attribute)
            and _dotted(node.value) in modules
            and node.attr in CONSTRUCTORS | {"__dict__", "__getattribute__"}
        ):
            report(node)
        # A module object in value position is an escape, including assignment
        # aliases, arguments, return values, subscripts and reflective getattr.
        if isinstance(node, (ast.Name, ast.Attribute)) and _dotted(node) in modules:
            parent = parents.get(node)
            if not isinstance(parent, ast.Attribute) or parent.value is not node:
                report(node)
        if isinstance(node, ast.Call) and (
            _dotted(node.func) in loaders
            or any(
                isinstance(value, ast.Constant) and value.value in SQLITE_MODULES
                for value in [*node.args, *(k.value for k in node.keywords)]
            )
        ):
            # A dynamic import in a file naming SQLite fails closed. This is
            # a syntax rule, without tracing the name through assignments.
            target = node.args[0] if node.args else next((k.value for k in node.keywords if k.arg == "name"), None)
            if (isinstance(target, ast.Constant) and target.value in SQLITE_MODULES) or (
                has_sqlite_literal and not isinstance(target, ast.Constant)
            ):
                report(node)
    return sorted(findings.values(), key=lambda finding: finding.line_no)


def writer_target_violations(source: str, writer: AllowedWriter) -> list[str]:
    """Pin every writer open to its declared target expression and call options.

    These are static site contracts; caller-supplied paths remain the writer's
    API responsibility. No path-dataflow inference is used by this rule.
    """
    tree = ast.parse(source)
    calls = [ast.unparse(n) for n in ast.walk(tree) if isinstance(n, ast.Call) and _dotted(n.func) == "sqlite3.connect"]
    if Counter(calls) != Counter(writer.calls):
        return [f"{writer.path}: opens differ from declared target sites ({writer.target_db})"]
    allowed_attributes = {
        n.func for n in ast.walk(tree) if isinstance(n, ast.Call) and _dotted(n.func) == "sqlite3.connect"
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            # A writer may provide a connection factory subclass; its open
            # remains the separately inventoried sqlite3.connect call.
            allowed_attributes.update(base for base in node.bases if _dotted(base) == "sqlite3.Connection")
        annotation = getattr(node, "annotation", None)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            annotation = node.returns
        if annotation is not None:
            allowed_attributes.update(ast.walk(annotation))
    if any(
        isinstance(node, ast.Attribute)
        and _dotted(node) in {"sqlite3.connect", "sqlite3.Connection"}
        and node not in allowed_attributes
        for node in ast.walk(tree)
    ):
        return [f"{writer.path}: constructor escapes the declared writer sites"]
    # Import/reflective/aliased constructors are not writer exemptions.
    allowed_lines = {
        n.lineno
        for n in ast.walk(tree)
        if (isinstance(n, ast.Attribute) and _dotted(n) == "sqlite3.Connection")
        or (isinstance(n, ast.Call) and _dotted(n.func) == "sqlite3.connect")
    }
    unexpected = [f for f in classify_source(source, writer.path) if f.line_no not in allowed_lines]
    return [f"{f.rel_path}:{f.line_no}: undeclared {f.kind}" for f in unexpected]


def iter_scan_paths(root: Path) -> list[Path]:
    """Tracked scripts in a repository, fixture files in an injected test root."""
    if (root / ".git").exists():
        result = subprocess.run(
            ["git", "ls-files", "-z", "--", "scripts/*.py"], cwd=root, check=True, capture_output=True, timeout=30
        )
        return [root / p for p in result.stdout.decode().split("\0") if p]
    return sorted((root / "scripts").rglob("*.py"))


def find_violations(
    repo_root: Path | None = None, allowlist: tuple[AllowedWriter, ...] | None = None
) -> tuple[list[str], list[str]]:
    root = (repo_root or REPO_ROOT).resolve()
    writers = {writer.path: writer for writer in (load_allowlist() if allowlist is None else allowlist)}
    violations, unreadable = [], []
    seen = set()
    for path in iter_scan_paths(root):
        rel = path.relative_to(root).as_posix()
        seen.add(rel)
        try:
            source = path.read_text(encoding="utf-8")
            if rel == READER_BOUNDARY:
                continue
            if rel in writers:
                violations.extend(writer_target_violations(source, writers[rel]))
            else:
                violations.extend(
                    f"{f.rel_path}:{f.line_no}: {f.kind}: {f.snippet}" for f in classify_source(source, rel)
                )
        except (OSError, SyntaxError):
            unreadable.append(rel)
    violations.extend(f"{rel}: stale writer allowlist entry" for rel in sorted(writers.keys() - seen))
    return violations, unreadable


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args(argv)
    violations, unreadable = find_violations()
    if violations or unreadable:
        print("\n".join([*violations, *(f"{path}: unreadable" for path in unreadable)]), file=sys.stderr)
        return 1
    print("OK: no undeclared SQLite constructor references in scripts/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
