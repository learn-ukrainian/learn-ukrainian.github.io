#!/usr/bin/env python3
"""Structural SQLite boundary and store-access ratchet over scripts/ and tests/.

Use for local/CI boundary checks and commit-blob census; not for caller migration.

Every constructor reference is forbidden outside the pinned reference manifest
and the one tested reader boundary, independent of target, mode, or call shape.
Every listed file pins its reference count; readers awaiting #9662 do not gain
permission to add constructors. Reader and writer call expressions pin their target sites.
Module objects may not escape into assignments/containers/calls: otherwise an
alias could hide a constructor. Dynamic imports of SQLite are refused too.
Code built from strings (exec) and constructors recovered through type(conn)(path)
are stated residuals outside this structural scan. Test fixture opens are allowed on fixture paths; store construction, raw
store constructors and collection-time test access are baseline-ratcheted.
The census reads commit blobs, including skip-worktree files; tests/helpers/source_db_write_guard.py rejects writable real
repository data/*.db connect calls within the pytest process.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
import subprocess
import sys
from collections import Counter
from dataclasses import dataclass
from functools import cached_property, lru_cache
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
    functions: tuple[str, ...] = ()


def load_allowlist() -> tuple[AllowedReference, ...]:
    entries = tuple(
        AllowedReference(**{**row, "calls": tuple(row.get("calls", ())), "functions": tuple(row.get("functions", ()))})
        for row in json.loads(REFERENCE_MANIFEST.read_text())
    )
    if len({entry.path for entry in entries}) != len(entries):
        raise ValueError("duplicate SQLite allowlist path")
    for entry in entries:
        common_invalid = ".." in Path(entry.path).parts or not entry.reason.strip()
        if entry.kind == "store_resolver":
            invalid = (entry.path != "scripts/storage/topology.py" or entry.reference_count != 0
                       or entry.target_db is not None or bool(entry.calls) or not entry.functions
                       or not set(entry.functions) <= {"resolve_store", "resolve_active_sources_db"})
        elif entry.kind == "fixture_factory":
            invalid = (not entry.path.startswith("tests/") or entry.reference_count < 1
                       or entry.target_db is not None or not entry.calls or bool(entry.functions))
        else:
            invalid = (entry.kind not in {"writer", "reader_pending_migration_9662"}
                       or entry.reference_count < 1 or not entry.path.startswith("scripts/")
                       or bool(entry.functions)
                       or (entry.kind == "writer" and (not entry.target_db or not entry.calls))
                       or (entry.kind != "writer" and entry.target_db is not None))
        if common_invalid or invalid:
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


class _Syntax:
    """One parse and child inventory per input, shared by all boundary classes."""

    def __init__(self, source: str, rel_path: str):
        self.tree = ast.parse(source, filename=rel_path)
        self.nodes = [self.tree]
        self.children = {}
        for node in self.nodes:
            # Context/operator markers have no string fragments, roots or sites.
            # Keep them on the original AST for fingerprints and ctx/op checks,
            # but omit them from the analysis inventory and child traversal.
            if isinstance(node, (ast.Constant, ast.alias, ast.Name)) or not node._fields:
                children = ()
            elif isinstance(node, ast.Attribute):
                children = (node.value,)
            elif isinstance(node, ast.BinOp):
                children = (node.left, node.right)
            else:
                children = tuple(child for child in ast.iter_child_nodes(node) if not isinstance(
                    child, (ast.expr_context, ast.operator, ast.unaryop, ast.boolop, ast.cmpop)))
            self.children[node] = children
            self.nodes.extend(children)

    @cached_property
    def parents(self):
        return {child: node for node in self.nodes for child in self.children[node]}


def classify_source(source: str, rel_path: str, *, syntax: _Syntax | None = None) -> list[Finding]:
    """Match syntax references, never infer database paths or caller arguments."""
    syntax = syntax if syntax is not None else _Syntax(source, rel_path)
    nodes = syntax.nodes
    # Every reference/loader branch below needs one of these AST anchors.
    # Check syntax rather than source text, retaining aliased and dynamic imports.
    anchors = SQLITE_MODULES | {"__import__", "importlib", "pkgutil", "builtins",
                                "import_module", "resolve_name"}
    if not any(
        (isinstance(n, ast.Name) and n.id in anchors)
        or (isinstance(n, ast.Attribute) and n.attr in anchors)
        or (isinstance(n, ast.alias) and n.name in anchors)
        or (isinstance(n, ast.ImportFrom) and n.module in anchors)
        or (isinstance(n, ast.Constant) and isinstance(n.value, str) and n.value in SQLITE_MODULES)
        for n in nodes
    ):
        return []
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

    parents = syntax.parents
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
    source: str, writer: AllowedReference, references: list[Finding] | None = None,
    *, syntax: _Syntax | None = None,
) -> list[str]:
    """Pin every writer open to its declared target expression and call options.

    These are static site contracts; caller-supplied paths remain the writer's
    API responsibility. No path-dataflow inference is used by this rule.
    """
    syntax = syntax if syntax is not None else _Syntax(source, writer.path)
    nodes = syntax.nodes
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
        for f in (classify_source(source, writer.path, syntax=syntax) if references is None else references)
        if f.line_no not in allowed_lines
    ]
    return [f"{f.rel_path}:{f.line_no}: undeclared {f.kind}" for f in unexpected]


BASELINE = Path(__file__).with_name("store_access_baseline.json")
STORE_CLASSES = ("store_path", "raw_store_constructor", "test_import_access")
STORE_NAME = re.compile(r"(?:sources|vesum|vesum_shadow_[^/]*?)\.db(?:$|[?#/])")


def _may_fold_store(nodes: list[ast.AST]) -> bool:
    """Necessary condition for a folded name, allowing arbitrary literal order.

    Fragments below only concatenate whole string constants (including those
    looked up through names). Recognize a filename stem or environment key in
    that language before doing scope/dataflow work. The first and last literal
    may contain extra text; intermediate pieces must be whole literals. This
    deliberately overapproximates actual expressions, never filters source text.
    """
    literals = {n.value for n in nodes if isinstance(n, ast.Constant) and isinstance(n.value, str)}
    for needle in ("sources.db", "vesum.db", "vesum_shadow_", "LU_SOURCES_DB", "LU_VESUM_DB"):
        if any(needle in value for value in literals):
            return True
        prefixes = tuple(needle[:i] for i in range(1, len(needle)))
        endings = [value for value in literals if value.endswith(prefixes)]
        reachable = {i for i, prefix in enumerate(prefixes, 1)
                     if any(value.endswith(prefix) for value in endings)}
        for start in range(1, len(needle)):
            if start not in reachable:
                continue
            if any(value.startswith(needle[start:]) for value in literals):
                return True
            reachable.update(end for end in range(start + 1, len(needle))
                             if needle[start:end] in literals)
    return False


@dataclass(frozen=True)
class StoreFinding:
    """Identity survives line movement; duplicate expressions remain distinct."""

    path: str
    kind: str
    scope: str
    fingerprint: str
    occurrence: int


def classify_store_source(source: str, rel_path: str, *, syntax: _Syntax | None = None) -> list[StoreFinding]:
    """Conservative same-module AST census; fixture roots are not repository roots."""
    syntax = syntax if syntax is not None else _Syntax(source, rel_path)
    tree, nodes = syntax.tree, syntax.nodes
    access_names = SQLITE_MODULES | CONSTRUCTORS | {
        "open_readonly", "resolve_store", "resolve_active_sources_db", "require_local_active_sources_db"}
    possible_import_access = rel_path.startswith("tests/") and any(
        (isinstance(n, ast.Name) and n.id in access_names)
        or (isinstance(n, ast.Attribute) and n.attr in access_names)
        or (isinstance(n, ast.alias) and n.name in access_names)
        or (isinstance(n, ast.ImportFrom) and n.module in SQLITE_MODULES)
        for n in nodes)
    may_store = _may_fold_store(nodes)
    if not may_store and not possible_import_access:
        return []
    parents = syntax.parents
    aliases = {}
    for node in nodes:
        if isinstance(node, ast.Import):
            for alias in node.names:
                aliases[alias.asname or alias.name] = alias.name
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                aliases[alias.asname or alias.name] = f"{node.module}.{alias.name}"

    def name(node):
        dotted = _dotted(node)
        head, _, tail = dotted.partition(".")
        return aliases.get(head, head) + ("." + tail if tail else "")

    @lru_cache(None)
    def scope(node):
        parent = parents.get(node)
        if parent is None:
            return "<module>"
        enclosing = scope(parent)
        if isinstance(parent, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            return parent.name if enclosing == "<module>" else f"{enclosing}.{parent.name}"
        return enclosing

    facts = {}
    string_constants = {(scope(n), target.id): n.value.value for n in nodes if isinstance(n, ast.Assign)
                        and isinstance(n.value, ast.Constant) and isinstance(n.value.value, str)
                        for target in n.targets if isinstance(target, ast.Name)}
    fixture_parameters = set()
    if rel_path.startswith("tests/"):
        for function in nodes:
            if isinstance(function, (ast.FunctionDef, ast.AsyncFunctionDef)) and (
                function.name.startswith("test_") or any(
                    name(d.func if isinstance(d, ast.Call) else d).endswith(".fixture")
                    for d in function.decorator_list)):
                function_scope = ".".join(p for p in (scope(function), function.name) if p != "<module>")
                fixture_parameters.update((function_scope, arg.arg) for arg in
                    [*function.args.posonlyargs, *function.args.args, *function.args.kwonlyargs])


    def literal_name(node):
        return string_constants.get((scope(node), node.id), string_constants.get(("<module>", node.id), ""))

    @lru_cache(None)
    def fragments(node):
        if isinstance(node, ast.Name):
            return literal_name(node)
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value
        return "".join(fragments(child) for child in syntax.children[node])

    @lru_cache(None)
    def is_store(node):
        text = fragments(node)
        return bool(text and STORE_NAME.search(text))

    # Use the same constant-folded expressions as the census itself. Source
    # substring filters can miss split strings or interpolated variable stems.
    possible_store = may_store and any(is_store(n) or fragments(n) in {"LU_SOURCES_DB", "LU_VESUM_DB"}
                                      for n in nodes if isinstance(n, ast.expr))
    if not possible_store and not possible_import_access:
        # Break recursive cache cells so the whole file AST is released now,
        # rather than retained until a later generational garbage collection.
        scope = fragments = is_store = None
        return []

    @lru_cache(None)
    def fact(node):
        if isinstance(node, ast.Name):
            if (scope(node), node.id) in fixture_parameters:
                return ("fixture", False)
            for key in ( (scope(node), node.id), ("<module>", node.id)):
                if key in facts:
                    return facts[key]
            if node.id in {"tmp_path", "tmp_path_factory", "tmpdir", "tmpdir_factory"}:
                return ("fixture", False)
            if node.id == "__file__" or node.id in {"ROOT", "REPO", "REPO_ROOT", "PROJECT_ROOT", "BASE_DIR"}:
                return ("repo", False)
            return (None, False)
        if isinstance(node, ast.Attribute) and node.attr in {"ROOT", "REPO_ROOT", "PROJECT_ROOT"}:
            return ("repo", False)
        children = [fact(child) for child in syntax.children[node]]
        roots = {root for root, _ in children if root}
        target = is_store(node) or any(store for _, store in children)
        if isinstance(node, ast.Call) and name(node.func).split(".")[-1] in {
            "default_repository_root", "main_checkout_root", "resolve_repo_root"}:
            roots.add("repo")
        if isinstance(node, ast.Constant) and isinstance(node.value, str) and re.match(
            r"^(?:\./)?data(?:/|$)", node.value):
            roots.add("relative")
        # Absolute repository provenance cannot be hidden by a fixture sibling.
        # A relative data fragment, however, can be joined to a fixture root.
        return ("repo" if "repo" in roots else "fixture" if "fixture" in roots
                else "relative" if "relative" in roots else None, target)

    assignments = [n for n in nodes if isinstance(n, (ast.Assign, ast.AnnAssign, ast.NamedExpr))]
    for _ in range(len(assignments) + 1 if possible_store else 0):
        fact.cache_clear()
        updated = False
        for node in assignments:
            if node.value is None:
                continue
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            names = [child for target in targets for child in (
                ast.walk(target) if isinstance(target, (ast.Tuple, ast.List)) else [target])
                if isinstance(child, ast.Name)]
            for target in names:
                if isinstance(target, ast.Name):
                    key, value = (scope(node), target.id), fact(node.value)
                    old = facts.get(key, (None, False))
                    roots = {old[0], value[0]}
                    value = ("repo" if "repo" in roots else "fixture" if "fixture" in roots
                             else "relative" if "relative" in roots else None, old[1] or value[1])
                    if facts.get(key) != value:
                        facts[key] = value
                        updated = True
        if not updated:
            break

    fact.cache_clear()

    constructor_names = {f"{module}.{ctor}" for module in SQLITE_MODULES for ctor in CONSTRUCTORS}

    def constructor(node):
        return isinstance(node, ast.Call) and name(node.func) in constructor_names

    # Follow module, constructor and reader aliases to a fixed point.
    for _ in range(len(assignments) + 1):
        changed = False
        for node in assignments:
            if isinstance(node.value, (ast.Name, ast.Attribute)):
                value = name(node.value)
                if value in SQLITE_MODULES or value in constructor_names or value.split(".")[-1] in {
                    "open_readonly", "resolve_store", "resolve_active_sources_db", "require_local_active_sources_db"}:
                    targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                    for target in targets:
                        if isinstance(target, ast.Name) and aliases.get(target.id) != value:
                            aliases[target.id] = value
                            changed = True
        if not changed:
            break

    found = []
    path_nodes = set()
    for node in nodes if possible_store else ():
        env_key = None
        if isinstance(node, ast.Subscript):
            env_key = node.slice
            env_reader = name(node.value).split(".")[-1] in {"environ", "env", "environ_map"}
        elif isinstance(node, ast.Call):
            env_key = node.args[0] if node.args else None
            env_reader = name(node.func) in {"os.getenv", "os.environ.get", "env.get", "environ.get"}
        else:
            env_reader = False
        key_value = fragments(env_key) if env_key is not None else None
        if env_reader and key_value in {"LU_SOURCES_DB", "LU_VESUM_DB"}:
            path_nodes.add(node)
        if isinstance(node, (ast.BinOp, ast.Call, ast.JoinedStr, ast.Constant)):
            root, target = fact(node)
            # Accessors are consumers, not builders; record their arguments.
            builder = isinstance(node, ast.JoinedStr) or (
                isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Div, ast.Add, ast.Mod)))
            if isinstance(node, ast.Call):
                builder = name(node.func).split(".")[-1] in {
                    "Path", "PurePath", "join", "joinpath", "resolve", "absolute", "expanduser",
                    "with_name", "with_suffix", "format"}
                # Unknown helpers taking data + a store filename are builders,
                # even when their anchor cannot be resolved in this module.
                arguments = [fragments(arg) for arg in [*node.args, *(k.value for k in node.keywords)]]
                builder |= any(re.search(r"(?:^|/)data/?(?:sources|vesum|vesum_shadow_[^/]*?)\.db(?:$|[?#/])",
                                         separator.join(arguments)) for separator in ("", "/"))
            if root != "fixture" and target and (
                builder or (root in {"repo", "relative"} and not isinstance(node, ast.Call))
            ):
                path_nodes.add(node)
        if constructor(node):
            arg = node.args[0] if node.args else next((k.value for k in node.keywords if k.arg == "database"), None)
            if arg is not None and (is_store(arg) or fact(arg)[1]) and fact(arg)[0] != "fixture":
                found.append(("raw_store_constructor", node))
    # Keep outermost construction, rather than its overlapping subexpressions.
    for node in path_nodes:
        parent = parents.get(node)
        container = parent
        fixture = False
        while container is not None and not isinstance(container, ast.stmt):
            if fact(container)[0] == "fixture":
                fixture = True
                break
            container = parents.get(container)
        if fixture:
            continue
        while parent is not None and parent not in path_nodes:
            if isinstance(parent, ast.stmt):
                break
            parent = parents.get(parent)
        if parent not in path_nodes:
            found.append(("store_path", node))

    def accessor(node):
        return isinstance(node, ast.Call) and (constructor(node) or name(node.func).split(".")[-1] in {
            "open_readonly", "resolve_store", "resolve_active_sources_db", "require_local_active_sources_db"})

    helpers = {n.name: n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}

    def execution_nodes(node):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            # Decorators and defaults execute at collection; function bodies do not.
            for expr in [*node.decorator_list, *node.args.defaults,
                         *(d for d in node.args.kw_defaults if d is not None)]:
                yield from ast.walk(expr)
            return
        yield node
        for child in syntax.children[node]:
            yield from execution_nodes(child)

    if rel_path.startswith("tests/"):
        for node in execution_nodes(tree):
            if accessor(node):
                found.append(("test_import_access", node))
            elif isinstance(node, ast.Call) and _dotted(node.func) in helpers:
                helper = helpers[_dotted(node.func)]
                for statement in helper.body:
                    for child in execution_nodes(statement):
                        if accessor(child):
                            found.append(("test_import_access", child))
    counts = Counter()
    result = []
    for kind, node in sorted(found, key=lambda pair: (pair[1].lineno, pair[1].col_offset, pair[0])):
        fingerprint = hashlib.sha256(ast.dump(node, include_attributes=False).encode()).hexdigest()
        key = (kind, scope(node), fingerprint)
        occurrence = counts[key]
        counts[key] += 1
        result.append(StoreFinding(rel_path, *key, occurrence))
    scope = fragments = is_store = fact = execution_nodes = None
    return result


def census(commit: str, root: Path = REPO_ROOT) -> dict:
    """Read the complete committed tree, independent of checkout sparsity."""
    sha = subprocess.check_output(["git", "rev-parse", f"{commit}^{{commit}}"], cwd=root, text=True, timeout=30).strip()
    paths = subprocess.check_output(["git", "ls-tree", "-r", "--name-only", "-z", sha, "--", "scripts", "tests"], cwd=root, timeout=30)
    names = [p for p in paths.decode().split("\0") if p.endswith(".py")]
    requests = "".join(f"{sha}:{p}\n" for p in names).encode()
    blobs = subprocess.check_output(["git", "cat-file", "--batch"], cwd=root, input=requests, timeout=30)
    entries = []
    offset = 0
    for path in names:
        end = blobs.index(b"\n", offset)
        header = blobs[offset:end].split()
        if len(header) != 3 or header[1] != b"blob":
            raise ValueError(f"census input is not a blob: {path}")
        size = int(header[2])
        source = blobs[end + 1:end + 1 + size].decode()
        offset = end + 2 + size
        entries.extend(classify_store_source(source, path))
    return {"schema": "store-access-baseline.v1", "base_commit": sha,
            "counts": {kind: sum(e.kind == kind for e in entries) for kind in STORE_CLASSES},
            "file_counts": dict(sorted(Counter(e.path for e in entries).items())),
            "entries": [e.__dict__ for e in entries]}



def base_blob_ids(root: Path, commit: str) -> dict[str, str]:
    """Complete immutable base inputs, including files absent from checkout."""
    if not (root / ".git").exists():
        return {}
    available = subprocess.run(["git", "cat-file", "-e", f"{commit}^{{commit}}"],
                               cwd=root, capture_output=True, timeout=30)
    if available.returncode:
        # Shallow checkouts lack the frozen base: classify every current file.
        return {}
    result = subprocess.check_output(["git", "ls-tree", "-r", "-z", commit, "--", "scripts", "tests"],
                                     cwd=root, timeout=30)
    blobs = {}
    for row in result.split(b"\0"):
        if row:
            metadata, path = row.split(b"\t", 1)
            _mode, kind, oid = metadata.split()
            if kind == b"blob" and path.endswith(b".py"):
                blobs[path.decode()] = oid.decode()
    return blobs


def source_blob_id(source: str, algorithm: str = "sha1") -> str:
    """Use Git's object framing to compare exact file bytes, never timestamps."""
    raw = source.encode("utf-8")
    return hashlib.new(algorithm, b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()

def baseline_entries() -> set[StoreFinding]:
    return {StoreFinding(**entry) for entry in json.loads(BASELINE.read_text())["entries"]}



def baseline_policy_violations(root: Path) -> list[str]:
    """Reject growth or a changed freeze against existing committed baselines.

    The initial slice has no predecessor baseline; its census is independently
    reproduced at review. Corrections to that unlanded initial census must
    exactly reproduce the same base. After landing, working-tree, branch and
    CI changes may only shrink available committed versions.
    """
    if not (root / ".git").exists():
        return []
    current = json.loads(BASELINE.read_text())
    current_entries = {StoreFinding(**row) for row in current["entries"]}
    rel = BASELINE.relative_to(REPO_ROOT).as_posix()
    initial_correction = None
    for ref in ("HEAD", "HEAD^", "origin/main"):
        result = subprocess.run(["git", "show", f"{ref}:{rel}"], cwd=root,
                                capture_output=True, text=True, timeout=30)
        if result.returncode:
            continue
        previous = json.loads(result.stdout)
        prior_entries = {StoreFinding(**row) for row in previous["entries"]}
        if (previous["base_commit"] != current["base_commit"] or not current_entries <= prior_entries
                or previous.get("file_counts", {}) != current.get("file_counts", {})):
            if initial_correction is None:
                # The first baseline is still in review: allow only an exact
                # recensus, never growth of a baseline already frozen on main.
                landed = subprocess.run(["git", "ls-tree", "origin/main", "--", rel],
                                        cwd=root, capture_output=True, text=True, timeout=30)
                initial_correction = (landed.returncode == 0 and not landed.stdout
                                      and current == census(current["base_commit"], root))
            if initial_correction and previous["base_commit"] == current["base_commit"]:
                continue
            return [f"{rel}: baseline may only shrink; freeze/growth differs from {ref}"]
    return []

def iter_scan_paths(root: Path) -> list[Path]:
    """Tracked scripts in a repository, fixture files in an injected test root."""
    if (root / ".git").exists():
        result = subprocess.run(
            ["git", "ls-files", "-z", "--cached", "--others", "--", "scripts/*.py", "tests/*.py"],
            cwd=root,
            check=True,
            capture_output=True,
            timeout=30,
        )
        return sorted({root / p for p in result.stdout.decode().split("\0") if p})
    return sorted([*(root / "scripts").rglob("*.py"), *(root / "tests").rglob("*.py")])


def find_violations(
    repo_root: Path | None = None, allowlist: tuple[AllowedReference, ...] | None = None
) -> tuple[list[str], list[str]]:
    root = (repo_root or REPO_ROOT).resolve()
    writers = {writer.path: writer for writer in (load_allowlist() if allowlist is None else allowlist)}
    violations, unreadable = [], []
    seen = set()
    baseline = baseline_entries() if root == REPO_ROOT.resolve() else set()
    payload = json.loads(BASELINE.read_text()) if root == REPO_ROOT.resolve() else {}
    base_blobs = base_blob_ids(root, payload["base_commit"]) if "base_commit" in payload else {}
    by_path = {}
    for finding in baseline:
        by_path.setdefault(finding.path, []).append(finding)
    current = set()
    if root == REPO_ROOT.resolve():
        violations.extend(baseline_policy_violations(root))
    for path in iter_scan_paths(root):
        rel = path.relative_to(root).as_posix()
        seen.add(rel)
        try:
            # Preserve bytes (including CRLF) when comparing Git object IDs.
            source = path.read_bytes().decode("utf-8")
            syntax = None
            entry = writers.get(rel)
            pinned = by_path.get(rel, [])
            oid = base_blobs.get(rel)
            unchanged = oid is not None and source_blob_id(source, "sha256" if len(oid) == 64 else "sha1") == oid
            if unchanged and len(pinned) == payload.get("file_counts", {}).get(rel, 0):
                store_findings = pinned
            else:
                syntax = _Syntax(source, rel)
                store_findings = classify_store_source(source, rel, syntax=syntax)
            current.update(store_findings)
            for finding in store_findings:
                sanctioned = (entry is not None and entry.kind == "store_resolver"
                              and finding.kind == "store_path" and finding.scope in entry.functions)
                if finding not in baseline and not sanctioned:
                    violations.append(f"{rel}: {finding.kind} in {finding.scope} ({finding.fingerprint})")
            if rel.startswith("tests/") and (entry is None or entry.kind != "fixture_factory"):
                continue
            if entry is not None and entry.kind == "store_resolver":
                # This kind never exempts constructor references.
                entry = None
            if rel == READER_BOUNDARY:
                continue
            syntax = syntax if syntax is not None else _Syntax(source, rel)
            references = classify_source(source, rel, syntax=syntax)
            if entry is not None:
                if len(references) != entry.reference_count:
                    violations.append(f"{rel}: pinned {entry.reference_count} references, found {len(references)}")
                if entry.kind == "writer":
                    violations.extend(writer_target_violations(source, entry, references, syntax=syntax))
                else:
                    calls = [
                        ast.unparse(n)
                        for n in syntax.nodes
                        if isinstance(n, ast.Call) and _dotted(n.func) == "sqlite3.connect"
                    ]
                    if Counter(calls) != Counter(entry.calls):
                        violations.append(f"{rel}: reader opens differ from pinned call expressions")
            else:
                violations.extend(f"{f.rel_path}:{f.line_no}: {f.kind}: {f.snippet}" for f in references)
        except (OSError, SyntaxError):
            unreadable.append(rel)
    violations.extend(f"{f.path}: stale baseline {f.kind} in {f.scope} ({f.fingerprint})"
                      for f in sorted(baseline - current, key=lambda f: (f.path, f.kind, f.scope, f.fingerprint, f.occurrence)))
    violations.extend(f"{rel}: stale reference allowlist entry" for rel in sorted(writers.keys() - seen))
    return violations, unreadable


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Examples:\n  .venv/bin/python -m scripts.hygiene.lint_source_db_writable_connects\n  .venv/bin/python -m scripts.hygiene.lint_source_db_writable_connects --census origin/main\nOutputs: diagnostics or deterministic census JSON on stdout; no files or databases changed.\nExit codes: 0 = census emitted or pinned inventory matches; 1 = a violation or unreadable input.\nRelated: #9945, #9937, #9609; #9662 reader migration. Code generated by exec is outside this structural scan.",
    )
    parser.add_argument("--census", metavar="COMMIT", help="Emit deterministic JSON census of tracked scripts/ and tests/ at COMMIT (e.g. origin/main); default: lint working tree.")
    args = parser.parse_args(argv)
    if args.census:
        print(json.dumps(census(args.census), indent=2) + "")
        return 0
    violations, unreadable = find_violations()
    if violations or unreadable:
        print("\n".join([*violations, *(f"{path}: unreadable" for path in unreadable)]), file=sys.stderr)
        return 1
    print("OK: SQLite reference boundary and store-access ratchet pass in scripts/ and tests/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
