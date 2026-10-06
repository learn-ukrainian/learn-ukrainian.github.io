#!/usr/bin/env python3
"""Structural SQLite constructor boundary over scripts/ (#9609, RB-1 §9).

Every constructor reference is forbidden outside the pinned reference manifest
and the one tested reader boundary, independent of target, mode, or call shape.
Every listed file pins its reference count; readers awaiting #9662 do not gain
permission to add constructors. Reader and writer call expressions pin their target sites.
Module objects may not escape into assignments/containers/calls: otherwise an
alias could hide a constructor. Dynamic imports of SQLite are refused too.
Code built from strings (exec) and constructors recovered through type(conn)(path)
are stated residuals outside this structural scan. Test fixture opens are outside
this scan; tests/helpers/source_db_write_guard.py rejects writable real
repository data/*.db connect calls within the pytest process.
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
REFERENCE_MANIFEST = Path(__file__).with_name("sqlite_reference_allowlist.json")
SQLITE_MODULES = frozenset({"sqlite3", "sqlite3.dbapi2", "_sqlite3"})
CONSTRUCTORS = frozenset({"connect", "Connection"})


@dataclass(frozen=True)
class AllowedReference:
    path: str
    reference_count: int
    kind: str
    target_db: str | None
    reason: str
    calls: tuple[str, ...] = ()


def load_allowlist() -> tuple[AllowedReference, ...]:
    entries = tuple(
        AllowedReference(**{**row, "calls": tuple(row.get("calls", ()))})
        for row in json.loads(REFERENCE_MANIFEST.read_text())
    )
    if len({entry.path for entry in entries}) != len(entries):
        raise ValueError("duplicate SQLite allowlist path")
    for entry in entries:
        if (
            entry.kind not in {"writer", "reader_pending_migration_9662"}
            or entry.reference_count < 1
            or not entry.reason.strip()
            or not entry.path.startswith("scripts/")
            or ".." in Path(entry.path).parts
            or (entry.kind == "writer" and (not entry.target_db or not entry.calls))
            or (entry.kind != "writer" and entry.target_db is not None)
        ):
            raise ValueError(f"invalid SQLite allowlist entry: {entry.path}")
    return entries


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
    nodes = list(ast.walk(tree))
    lines = source.splitlines()
    modules = set(SQLITE_MODULES)
    loaders = {"__import__", "importlib.import_module", "pkgutil.resolve_name"}
    findings: dict[tuple[int, int], Finding] = {}
    constructors = set()

    def report(node: ast.AST) -> None:
        line = node.lineno
        findings[(line, node.col_offset)] = Finding(rel_path, line, lines[line - 1].strip())

    for node in nodes:
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name in SQLITE_MODULES:
                    modules.add(alias.asname or alias.name)
                    if alias.name == "sqlite3":
                        modules.add(f"{alias.asname or alias.name}.dbapi2")
                if alias.name == "importlib":
                    loaders.add(f"{alias.asname or alias.name}.import_module")
                if alias.name == "pkgutil":
                    loaders.add(f"{alias.asname or alias.name}.resolve_name")
                if alias.name == "builtins":
                    loaders.add(f"{alias.asname or alias.name}.__import__")
        elif isinstance(node, ast.ImportFrom):
            if node.module in SQLITE_MODULES:
                for alias in node.names:
                    if alias.name in CONSTRUCTORS or alias.name == "*":
                        report(alias)
                        if alias.name != "*":
                            constructors.add(alias.asname or alias.name)
                    elif node.module == "sqlite3" and alias.name == "dbapi2":
                        modules.add(alias.asname or alias.name)
            elif any(alias.name in SQLITE_MODULES for alias in node.names):
                for alias in node.names:
                    if alias.name in SQLITE_MODULES:
                        report(alias)
                        modules.add(alias.asname or alias.name)
            elif node.module == "pkgutil":
                for alias in node.names:
                    if alias.name == "resolve_name":
                        loaders.add(alias.asname or alias.name)
            elif node.module == "importlib":
                for alias in node.names:
                    if alias.name == "import_module":
                        loaders.add(alias.asname or alias.name)
            elif node.module == "builtins":
                for alias in node.names:
                    if alias.name == "__import__":
                        loaders.add(alias.asname or alias.name)

    parents = {child: node for node in nodes for child in ast.iter_child_nodes(node)}
    assignments = [node for node in nodes if isinstance(node, (ast.Assign, ast.AnnAssign))]

    # Propagate explicit module and constructor aliases; count their later uses.
    changed = True
    while changed:
        changed = False
        for node in assignments:
            if node.value is not None:
                value = _dotted(node.value)
                dynamic_module = False
                if isinstance(node.value, ast.Call) and _dotted(node.value.func) in loaders:
                    target = (
                        node.value.args[0]
                        if node.value.args
                        else next((k.value for k in node.value.keywords if k.arg == "name"), None)
                    )
                    dynamic_module = not isinstance(target, ast.Constant) or (
                        isinstance(target.value, str) and target.value.split(":", 1)[0] in SQLITE_MODULES
                    )
                targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                for target in targets:
                    if not isinstance(target, ast.Name):
                        continue
                    if (value in modules or dynamic_module) and target.id not in modules:
                        modules.add(target.id)
                        if value == "sqlite3" or f"{value}.dbapi2" in modules:
                            modules.add(f"{target.id}.dbapi2")
                        changed = True
                    if (
                        value in constructors or any(value == f"{m}.{c}" for m in modules for c in CONSTRUCTORS)
                    ) and target.id not in constructors:
                        constructors.add(target.id)
                        changed = True

    for node in nodes:
        # Any module can re-export sqlite3. Pin neither the exporting module's
        # identity nor an inferred caller path: the SQLite attribute is enough.
        if isinstance(node, ast.Attribute) and node.attr in SQLITE_MODULES:
            report(node)
            modules.add(_dotted(node))
        if (
            isinstance(node, ast.Subscript)
            and isinstance(node.slice, ast.Constant)
            and node.slice.value in SQLITE_MODULES
        ):
            report(node)

    for node in nodes:
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load) and node.id in constructors:
            report(node)
        if (
            isinstance(node, ast.Attribute)
            and _dotted(node.value) in modules
            and node.attr in CONSTRUCTORS | {"__dict__", "__getattribute__"}
        ):
            report(node)
        # A module object in value position is an escape, including assignment
        # aliases, arguments, return values, subscripts and reflective getattr.
        if isinstance(node, (ast.Name, ast.Attribute)) and isinstance(node.ctx, ast.Load) and _dotted(node) in modules:
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
            # A nonliteral import target might load SQLite: refuse it without
            # path/name dataflow inference. Known unrelated literal imports pass.
            target = node.args[0] if node.args else next((k.value for k in node.keywords if k.arg == "name"), None)
            if (
                isinstance(target, ast.Constant)
                and isinstance(target.value, str)
                and target.value.split(":", 1)[0] in SQLITE_MODULES
            ) or (not isinstance(target, ast.Constant)):
                report(node)
    return sorted(findings.values(), key=lambda finding: finding.line_no)


def writer_target_violations(
    source: str, writer: AllowedReference, references: list[Finding] | None = None
) -> list[str]:
    """Pin every writer open to its declared target expression and call options.

    These are static site contracts; caller-supplied paths remain the writer's
    API responsibility. No path-dataflow inference is used by this rule.
    """
    tree = ast.parse(source)
    nodes = list(ast.walk(tree))
    calls = [ast.unparse(n) for n in nodes if isinstance(n, ast.Call) and _dotted(n.func) == "sqlite3.connect"]
    if Counter(calls) != Counter(writer.calls):
        return [f"{writer.path}: opens differ from declared target sites ({writer.target_db})"]
    allowed_attributes = {n.func for n in nodes if isinstance(n, ast.Call) and _dotted(n.func) == "sqlite3.connect"}
    for node in nodes:
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
        for node in nodes
    ):
        return [f"{writer.path}: constructor escapes the declared writer sites"]
    # Import/reflective/aliased constructors are not writer exemptions.
    allowed_lines = {
        n.lineno
        for n in nodes
        if (isinstance(n, ast.Attribute) and _dotted(n) == "sqlite3.Connection")
        or (isinstance(n, ast.Call) and _dotted(n.func) == "sqlite3.connect")
    }
    unexpected = [
        f
        for f in (classify_source(source, writer.path) if references is None else references)
        if f.line_no not in allowed_lines
    ]
    return [f"{f.rel_path}:{f.line_no}: undeclared {f.kind}" for f in unexpected]


def iter_scan_paths(root: Path) -> list[Path]:
    """Tracked scripts in a repository, fixture files in an injected test root."""
    if (root / ".git").exists():
        result = subprocess.run(
            ["git", "ls-files", "-z", "--cached", "--others", "--", "scripts/*.py"],
            cwd=root,
            check=True,
            capture_output=True,
            timeout=30,
        )
        return sorted({root / p for p in result.stdout.decode().split("\0") if p})
    return sorted((root / "scripts").rglob("*.py"))


def find_violations(
    repo_root: Path | None = None, allowlist: tuple[AllowedReference, ...] | None = None
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
            references = classify_source(source, rel)
            if rel in writers:
                entry = writers[rel]
                if len(references) != entry.reference_count:
                    violations.append(f"{rel}: pinned {entry.reference_count} references, found {len(references)}")
                if entry.kind == "writer":
                    violations.extend(writer_target_violations(source, entry, references))
                else:
                    calls = [
                        ast.unparse(n)
                        for n in ast.walk(ast.parse(source))
                        if isinstance(n, ast.Call) and _dotted(n.func) == "sqlite3.connect"
                    ]
                    if Counter(calls) != Counter(entry.calls):
                        violations.append(f"{rel}: reader opens differ from pinned call expressions")
            else:
                violations.extend(f"{f.rel_path}:{f.line_no}: {f.kind}: {f.snippet}" for f in references)
        except (OSError, SyntaxError):
            unreadable.append(rel)
    violations.extend(f"{rel}: stale reference allowlist entry" for rel in sorted(writers.keys() - seen))
    return violations, unreadable


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Examples:\n  .venv/bin/python -m scripts.hygiene.lint_source_db_writable_connects\nOutputs: diagnostics only; no files or databases changed.\nExit codes: 0 = pinned inventory matches; 1 = a violation or unreadable script.\nRelated: #9609, RB-1 section 9; #9662 reader migration. Code generated by exec is outside this structural scan.",
    )
    parser.parse_args(argv)
    violations, unreadable = find_violations()
    if violations or unreadable:
        print("\n".join([*violations, *(f"{path}: unreadable" for path in unreadable)]), file=sys.stderr)
        return 1
    print("OK: no undeclared SQLite constructor references in scripts/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
