#!/usr/bin/env python3
"""Rename machinery Python modules from ``scripts`` to ``lu_machinery`` with LibCST.

The ownership map is a JSON object from repository-relative file paths to an
owner, ``machinery`` or ``product``. Every module name is derived from the map's
paths (``.py`` and a terminal ``__init__`` stripped), so a reference is renamed
only when the file Python would bind for it is machinery-owned. Product modules
keep the ``scripts`` name. A reference the map cannot settle is reported, never
guessed.

``rename_nonpython.py`` imports the ownership model from this file.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import itertools
import json
import multiprocessing
import operator
import os
import re
import string
import sys
import tempfile
from collections.abc import Callable, Iterable, Iterator, Mapping, Sequence
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath

import libcst as cst
from libcst.codemod import CodemodContext, VisitorBasedCodemodCommand
from libcst.helpers import get_full_name_for_node
from libcst.metadata import (
    ParentNodeProvider,
    PositionProvider,
    QualifiedNameProvider,
    QualifiedNameSource,
)

OLD_ROOT = "scripts"
NEW_ROOT = "lu_machinery"
MACHINERY = "machinery"
PRODUCT = "product"
AMBIGUOUS = "ambiguous"
OWNERS = frozenset({MACHINERY, PRODUCT})

EXIT_OK = 0
EXIT_UNRESOLVED = 1
EXIT_USAGE = 2

SKIPPED_DIRS = frozenset(
    {".git", ".venv", "venv", "node_modules", "__pycache__", ".mypy_cache", ".ruff_cache", ".pytest_cache"}
)
LOADERS = {
    "importlib.import_module": "name",
    "importlib.__import__": "name",
    "builtins.__import__": "name",
    "runpy.run_module": "mod_name",
}
STDLIB = frozenset(sys.stdlib_module_names)
# What an import or loader finding names, for counting the machinery part of the residue.
KIND_TARGETS = {"unprefixed_cross_owner": MACHINERY, "unknown_module": "unknown", "unmapped_importer": "unknown"}


class MapError(ValueError):
    """The ownership map is unreadable or malformed."""


@dataclass(frozen=True)
class ModuleEntry:
    """The file Python binds for one module name, and that file's owner."""

    name: str
    owner: str
    bound_file: str | None
    note: str = ""


@dataclass(frozen=True)
class Finding:
    """One rewrite or one unresolved reference, with a repository-relative location."""

    path: str
    line: int
    kind: str
    before: str
    after: str = ""
    detail: str = ""
    # For a reference left as written: what the map says it names (machinery, product, ambiguous, unknown).
    target: str = ""

    def as_dict(self) -> dict[str, object]:
        data: dict[str, object] = {"path": self.path, "line": self.line, "kind": self.kind, "before": self.before}
        if self.after:
            data["after"] = self.after
        if self.detail:
            data["detail"] = self.detail
        if self.target:
            data["target"] = self.target
        return data


@dataclass
class Report:
    """Everything one run found, in a stable order."""

    tool: str
    mode: str
    map_sha256: str
    files_scanned: int = 0
    files_changed: list[str] = field(default_factory=list)
    rewrites: list[Finding] = field(default_factory=list)
    unresolved: list[Finding] = field(default_factory=list)
    inventory: list[Finding] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def counts(self, findings: Iterable[Finding]) -> dict[str, int]:
        counts: dict[str, int] = {}
        for finding in findings:
            counts[finding.kind] = counts.get(finding.kind, 0) + 1
        return dict(sorted(counts.items()))

    def as_dict(self) -> dict[str, object]:
        return {
            "tool": self.tool,
            "mode": self.mode,
            "map_sha256": self.map_sha256,
            "files_scanned": self.files_scanned,
            "files_changed": sorted(self.files_changed),
            "rewrite_counts": self.counts(self.rewrites),
            "unresolved_counts": self.counts(self.unresolved),
            "inventory_counts": self.counts(self.inventory),
            "rewrites": [item.as_dict() for item in self.rewrites],
            "unresolved": [item.as_dict() for item in self.unresolved],
            "inventory": [item.as_dict() for item in self.inventory],
            "notes": self.notes,
        }

    def print_summary(self, stream=sys.stdout) -> None:
        print(
            f"mode={self.mode} map_sha256={self.map_sha256} files_scanned={self.files_scanned} "
            f"files_{'to_change' if self.mode == 'check' else 'changed'}={len(self.files_changed)}",
            file=stream,
        )
        for title, findings in (("rewrites", self.rewrites), ("inventory", self.inventory)):
            counts = self.counts(findings)
            rendered = ", ".join(f"{kind}={count}" for kind, count in counts.items()) or "none"
            print(f"{title}: {len(findings)} ({rendered})", file=stream)
        counts = self.counts(self.unresolved)
        rendered = ", ".join(f"{kind}={count}" for kind, count in counts.items()) or "none"
        print(f"unresolved: {len(self.unresolved)} ({rendered})", file=stream)
        for item in sorted(self.unresolved, key=lambda f: (f.path, f.line, f.kind)):
            detail = f" ({item.detail})" if item.detail else ""
            print(f"{item.path}:{item.line}: {item.kind}: {item.before}{detail}", file=stream)


class OwnershipMap:
    """File-to-owner map plus the module names Python derives from those files."""

    def __init__(self, files: Mapping[str, str], sha256: str = "") -> None:
        self.files: dict[str, str] = {}
        for raw_path, owner in files.items():
            path = _validated_map_path(raw_path)
            if owner not in OWNERS:
                raise MapError(f"{raw_path!r}: owner must be 'machinery' or 'product', got {owner!r}")
            self.files[path] = owner
        self.sha256 = sha256
        self.modules: dict[str, ModuleEntry] = {}
        self.collisions: list[str] = []
        self._derive_modules()
        self._subtree_cache: dict[str, str | None] = {}
        self._module_subtree_cache: dict[str, str | None] = {}

    @classmethod
    def from_file(cls, path: Path) -> OwnershipMap:
        try:
            raw = path.read_bytes()
        except OSError as exc:
            raise MapError(f"cannot read ownership map: {exc.strerror}") from exc
        try:
            data = json.loads(raw)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise MapError(f"ownership map is not valid JSON: {exc}") from exc
        if not isinstance(data, dict) or not data:
            raise MapError("ownership map must be a non-empty JSON object of path -> owner")
        return cls(data, hashlib.sha256(raw).hexdigest())

    # -- module derivation -------------------------------------------------

    def _derive_modules(self) -> None:
        packages: dict[str, str] = {}
        plain: dict[str, str] = {}
        directories: dict[str, set[str]] = {}
        for path in self.files:
            parts = PurePosixPath(path).parts
            if not parts or parts[0] != OLD_ROOT:
                continue
            for depth in range(1, len(parts)):
                directory = parts[:depth]
                if all(part.isidentifier() for part in directory):
                    directories.setdefault(".".join(directory), set())
            if not path.endswith(".py"):
                continue
            stem_parts = (*parts[:-1], parts[-1][: -len(".py")])
            if not all(part.isidentifier() for part in stem_parts):
                continue
            for depth in range(1, len(stem_parts)):
                directories[".".join(stem_parts[:depth])].add(path)
            if stem_parts[-1] == "__init__":
                packages[".".join(stem_parts[:-1])] = path
            else:
                plain[".".join(stem_parts)] = path
        names = set(packages) | set(plain) | {name for name, members in directories.items() if members}
        for name in sorted(names):
            if name in packages:
                bound = packages[name]
                if name in plain and self.files[plain[name]] != self.files[bound]:
                    self.collisions.append(
                        f"{name}: Python binds {bound} ({self.files[bound]}) over {plain[name]} "
                        f"({self.files[plain[name]]})"
                    )
                self.modules[name] = ModuleEntry(name, self.files[bound], bound)
            elif name in plain:
                self.modules[name] = ModuleEntry(name, self.files[plain[name]], plain[name])
            else:
                owners = {self.files[member] for member in directories[name]}
                owner = owners.pop() if len(owners) == 1 else AMBIGUOUS
                self.modules[name] = ModuleEntry(name, owner, None, "namespace package")

    # -- paths ------------------------------------------------------------

    @staticmethod
    def original_path(rel: str) -> str:
        """Map a tree path back to its map key; filter-repo may already have moved machinery."""

        if rel == NEW_ROOT or rel.startswith(NEW_ROOT + "/"):
            return OLD_ROOT + rel[len(NEW_ROOT) :]
        return rel

    def file_owner(self, rel: str) -> str | None:
        return self.files.get(self.original_path(rel))

    def path_owner(self, path: str) -> str | None:
        """Owner of a file or directory path under ``scripts/``; None when the map has nothing there."""

        path = path.rstrip("/")
        if path in self.files:
            return self.files[path]
        if path in self._subtree_cache:
            return self._subtree_cache[path]
        owners = {owner for key, owner in self.files.items() if key.startswith(path + "/")}
        result = None if not owners else owners.pop() if len(owners) == 1 else AMBIGUOUS
        self._subtree_cache[path] = result
        return result

    def name_prefixes(self) -> frozenset[str]:
        """Every leading part of every mapped path, for spelling a name out character by character."""

        cached: frozenset[str] | None = getattr(self, "_name_prefixes", None)
        if cached is None:
            cached = frozenset(key[:i] for key in self.files for i in range(1, len(key) + 1))
            self._name_prefixes = cached
        return cached

    # -- modules ----------------------------------------------------------

    def module(self, dotted: str) -> ModuleEntry | None:
        return self.modules.get(dotted)

    def resolve(self, dotted: str) -> tuple[ModuleEntry, str] | None:
        """Longest module prefix of a dotted name under ``scripts`` and the attribute rest."""

        if dotted != OLD_ROOT and not dotted.startswith(OLD_ROOT + "."):
            return None
        parts = dotted.split(".")
        for depth in range(len(parts), 0, -1):
            entry = self.modules.get(".".join(parts[:depth]))
            if entry is not None:
                return entry, ".".join(parts[depth:])
        return None

    def subtree_owner(self, dotted: str) -> str | None:
        """Single owner of a module and everything below it, or AMBIGUOUS."""

        if dotted in self._module_subtree_cache:
            return self._module_subtree_cache[dotted]
        owners = {
            entry.owner for name, entry in self.modules.items() if name == dotted or name.startswith(dotted + ".")
        }
        result = None if not owners else owners.pop() if len(owners) == 1 else AMBIGUOUS
        self._module_subtree_cache[dotted] = result
        return result


def renamed(dotted: str) -> str:
    """``scripts.x`` -> ``lu_machinery.x``."""

    return NEW_ROOT + dotted[len(OLD_ROOT) :]


def _validated_map_path(raw: object) -> str:
    if not isinstance(raw, str) or not raw:
        raise MapError(f"map key must be a non-empty string, got {raw!r}")
    path = PurePosixPath(raw)
    if path.is_absolute() or ".." in path.parts or raw != path.as_posix():
        raise MapError(f"map key must be a normalized repository-relative path, got {raw!r}")
    return raw


# -- the LibCST pass ------------------------------------------------------


def _dotted_node(name: str) -> cst.Attribute | cst.Name:
    node = cst.parse_expression(name)
    assert isinstance(node, (cst.Attribute, cst.Name))
    return node


def _code(node: cst.CSTNode) -> str:
    return " ".join(cst.Module([]).code_for_node(node).split())


def _docstring_expr(body: Sequence[cst.CSTNode]) -> cst.CSTNode | None:
    """The docstring of a module, class or function body: its first statement, if that is a str literal.

    The first small statement counts even when others follow it on the line (``"doc"; x = 1``), and in a
    one-line suite (``def f(): "doc"``).
    """

    if not body:
        return None
    first = body[0]
    expr = first.body[0] if isinstance(first, cst.SimpleStatementLine) and first.body else first
    if not (isinstance(expr, cst.Expr) and isinstance(expr.value, (cst.SimpleString, cst.ConcatenatedString))):
        return None
    try:
        return expr.value if isinstance(static_value(expr.value), str) else None  # a bytes literal is no docstring
    except (NotStatic, StaticError):
        return None


class MachineryRenameCommand(VisitorBasedCodemodCommand):
    """Rewrite import nodes, bound names, loader targets and exact module literals."""

    DESCRIPTION = "Rename machinery modules from scripts to lu_machinery using a file ownership map."
    METADATA_DEPENDENCIES = (PositionProvider, QualifiedNameProvider, ParentNodeProvider)

    def __init__(
        self,
        context: CodemodContext,
        ownership: OwnershipMap,
        rel_path: str,
        external_names: frozenset[str] | None = None,
    ) -> None:
        super().__init__(context)
        self.ownership = ownership
        self.external_names = external_names
        self.rel_path = rel_path
        original = ownership.original_path(rel_path)
        self.importer_owner = ownership.file_owner(rel_path)
        parts = list(PurePosixPath(original).with_suffix("").parts)
        if parts and parts[-1] == "__init__":
            parts.pop()
        else:
            parts = parts[:-1]
        self.importer_package = ".".join(parts) if all(p.isidentifier() for p in parts) else ""
        self.rewrites: list[Finding] = []
        self.unresolved: list[Finding] = []
        self.inventory: list[Finding] = []
        self._import_depth = 0
        self._docstrings: set[int] = set()
        self._loader_args: set[int] = set()
        self._carrier_cache: dict[int, cst.CSTNode | None] = {}
        self._string_roots: dict[int, tuple[cst.CSTNode, list[cst.CSTNode]]] = {}
        self._string_rewrites: dict[int, str] = {}
        self._string_kinds: dict[int, type] = {}
        self._loader_rewrites: dict[int, str] = {}
        self._consumed_splits: set[int] = set()
        self._split_origin: dict[int, tuple[int, str]] = {}
        self._splits: dict[int, list[cst.ImportFrom]] = {}
        self._renamed_chain = False
        self._kept_chain = False

    # -- helpers ---------------------------------------------------------

    def _line(self, node: cst.CSTNode) -> int:
        return self.get_metadata(PositionProvider, node).start.line

    def _rewrite(self, node: cst.CSTNode, kind: str, before: str, after: str) -> None:
        self.rewrites.append(Finding(self.rel_path, self._line(node), kind, before, after))

    def _unresolved(self, node: cst.CSTNode, kind: str, before: str, detail: str, target: str = "") -> None:
        target = target or KIND_TARGETS.get(kind, AMBIGUOUS)
        self.unresolved.append(Finding(self.rel_path, self._line(node), kind, before, detail=detail, target=target))

    def _unprefixed_candidates(self, dotted: str) -> tuple[list[str], list[str]]:
        """Modules an unprefixed name can bind through sys.path (``scripts/`` or the importer's directory).

        Returns (exact, partial): names the map has in full, and names whose first part exists but
        whose full module does not (Python would fail there, so they are not import targets).
        """

        top = dotted.split(".", 1)[0]
        if not dotted or top in (OLD_ROOT, NEW_ROOT):
            return [], []
        exact: list[str] = []
        partial: list[str] = []
        for base in dict.fromkeys((OLD_ROOT, self.importer_package)):
            if (
                base
                and (base == OLD_ROOT or base.startswith(OLD_ROOT + "."))
                and self.ownership.module(f"{base}.{top}")
            ):
                name = f"{base}.{dotted}"
                (exact if self.ownership.module(name) else partial).append(name)
        return exact, partial

    def _missing_matters(self, dotted: str) -> bool:
        """A module the map lacks is worth reporting unless everything around it is product."""

        resolved = self.ownership.resolve(dotted)
        return resolved is None or self.ownership.subtree_owner(resolved[0].name) != PRODUCT

    def _unprefixed_decision(self, dotted: str, names: Sequence[str] | None) -> tuple[str, str, str]:
        """Decide an unprefixed absolute import of ``dotted`` (optionally ``from dotted import names``).

        Returns (verdict, candidate, detail). The verdict is ``external`` (not a scripts module),
        ``keep`` (the sys.path spelling keeps working on its own side), ``rewrite`` (to the qualified
        lu_machinery name of ``candidate``) or an unresolved kind with its detail.
        """

        candidates, partial = self._unprefixed_candidates(dotted)
        if not candidates:
            missing = [name for name in partial if self._missing_matters(name)]
            if missing:
                return "unknown_module", "", f"the map has no module {', '.join(missing)}"
            return "external", "", ""
        per_candidate = {c: self._owners_below(c, names) for c in candidates}
        owners = {owner for found in per_candidate.values() for owner in found}
        if AMBIGUOUS in owners:
            return "ambiguous_module", "", f"{' or '.join(candidates)} has no single owner"
        if len(candidates) > 1 and len(owners) > 1:
            return "ambiguous_module", "", f"sys.path can bind {' or '.join(candidates)}, which have different owners"
        if MACHINERY not in owners or self.importer_owner == MACHINERY:
            return "keep", "", ""
        top = dotted.split(".", 1)[0]
        if len(candidates) > 1:
            block = f"sys.path can bind {' or '.join(candidates)}"
        elif top in STDLIB or (self.external_names and top in self.external_names):
            block = f"{top!r} is also a standard-library or installed top-level name"
        elif self.importer_owner is None:
            block = "the importing file is not in the map, so its side is unknown"
        elif self.external_names is None:
            block = "pass --external-names to rule out installed packages with the same top-level name"
        else:
            return "rewrite", candidates[0], ""
        return "unprefixed_cross_owner", "", block

    def _owners_below(self, absolute: str, names: Sequence[str] | None) -> list[str]:
        """Owner per imported name: a submodule's owner, else the module's owner (an attribute)."""

        resolved = self.ownership.resolve(absolute)
        if resolved is None or resolved[1]:
            return []
        entry = resolved[0]
        if names is None:
            return [entry.owner]
        owners = []
        for name in names:
            sub = self.ownership.module(f"{absolute}.{name}")
            owners.append(sub.owner if sub is not None else entry.owner)
        return owners

    # -- docstrings and nesting -----------------------------------------

    def visit_Module(self, node: cst.Module) -> None:
        self._mark_docstring(node.body)
        self._collect_string_roots(node)

    def visit_ClassDef(self, node: cst.ClassDef) -> None:
        self._mark_docstring(node.body.body)  # an indented block's statements, or a one-line suite's

    def visit_FunctionDef(self, node: cst.FunctionDef) -> None:
        self._mark_docstring(node.body.body)

    def visit_Comment(self, node: cst.Comment) -> None:
        """Comments are never changed; a machinery or unknown name in one is listed in the inventory."""

        if WORD not in node.value.lower():
            return
        mentions = [ref for ref in text_references(self.ownership, node.value) if ref.target != PRODUCT]
        if mentions:
            shown = ", ".join(ref.text for ref in mentions)
            self.inventory.append(
                Finding(
                    self.rel_path,
                    self._line(node),
                    "comment_mention",
                    node.value[:160],
                    detail=f"left as written: {shown}",
                    target=worst_target(mentions),
                )
            )

    def _mark_docstring(self, body: Sequence[cst.CSTNode]) -> None:
        doc = _docstring_expr(body)
        if doc is not None:
            self._docstrings.add(id(doc))

    def visit_Import(self, node: cst.Import) -> None:
        self._import_depth += 1

    def visit_ImportFrom(self, node: cst.ImportFrom) -> None:
        self._import_depth += 1

    # -- string expressions -------------------------------------------

    def _parent(self, node: cst.CSTNode) -> cst.CSTNode | None:
        return self.get_metadata(ParentNodeProvider, node, None)

    def _carrier_parent(self, node: cst.CSTNode) -> cst.CSTNode | None:
        """The larger string expression this node is a part of, or None when it is a whole value.

        A literal is part of a larger expression when it is an operand (``+``, ``%``, ``*`` ...), sits in
        an f-string or an implicit concatenation, is the receiver of a method or a subscript, or is an
        argument of a str method (``.join``, ``.format``, ``.replace`` ...) or of a builtin that returns
        its text (``sorted``, ``str`` ...). Containers, ``a if c else b``, ``a or b`` and ``:=`` pass
        it on only when they are themselves such a part. Anything else (an assignment, a call of
        another function, a comparison, an index) takes the value whole.
        """

        key = id(node)
        if key in self._carrier_cache:
            return self._carrier_cache[key]
        result = self._find_carrier_parent(node)
        self._carrier_cache[key] = result
        return result

    def _find_carrier_parent(self, node: cst.CSTNode) -> cst.CSTNode | None:
        parent = self._parent(node)
        if isinstance(parent, (cst.ConcatenatedString, cst.FormattedString, cst.BinaryOperation, cst.UnaryOperation)):
            return parent
        if isinstance(parent, cst.FormattedStringExpression):
            return self._parent(parent)  # the f-string around the field (value or format spec)
        if isinstance(parent, (cst.Attribute, cst.Subscript)):
            if parent.value is not node:
                return None  # an attribute name, or an index or bound: a whole value
            outer = self._parent(parent)
            return outer if isinstance(outer, cst.Call) and outer.func is parent else parent
        if isinstance(parent, cst.Arg):
            call = self._parent(parent)
            return call if isinstance(call, cst.Call) and _shapes_arguments(call) else None
        if isinstance(parent, (cst.Element, cst.DictElement, cst.StarredDictElement)):
            container = self._parent(parent)
            return container if container is not None and self._carrier_parent(container) is not None else None
        if isinstance(parent, cst.IfExp):
            return parent if parent.test is not node and self._carrier_parent(parent) is not None else None
        if isinstance(parent, (cst.BooleanOperation, cst.NamedExpr)):
            return parent if self._carrier_parent(parent) is not None else None
        return None

    def _collect_string_roots(self, module: cst.Module) -> None:
        """Group every string literal under the outermost expression it is part of."""

        collector = _StringCollector()
        module.visit(collector)
        for leaf in collector.nodes:
            root: cst.CSTNode = leaf
            while (up := self._carrier_parent(root)) is not None:
                root = up
            entry = self._string_roots.setdefault(id(root), (root, []))
            entry[1].append(leaf)

    def on_visit(self, node: cst.CSTNode) -> bool:
        descend = super().on_visit(node)
        entry = self._string_roots.get(id(node))
        if entry is not None and not self._import_depth and id(node) not in self._loader_args:
            self._decide_string_root(node, entry[1])
        return descend

    def on_leave(self, original_node: cst.CSTNode, updated_node: cst.CSTNode) -> object:
        result = super().on_leave(original_node, updated_node)
        new_value = self._string_rewrites.get(id(original_node))
        if new_value is None:
            return result
        if isinstance(original_node, cst.SimpleString) and isinstance(result, cst.SimpleString):
            return _with_string_value(original_node, result, new_value)
        prefix = "b" if self._string_kinds.get(id(original_node)) is bytes else ""
        return cst.SimpleString(
            f'{prefix}"{new_value}"',
            lpar=original_node.lpar,
            rpar=original_node.rpar,  # type: ignore[attr-defined]
        )

    def _decide_string_root(self, node: cst.CSTNode, leaves: Sequence[cst.CSTNode]) -> None:
        texts = [text for leaf in leaves for text in _leaf_texts(leaf)]
        prose = id(node) in self._docstrings
        decision = decide_string(self.ownership, node, texts, prose=prose)
        shown = _code(node)
        if decision.action == "rewrite":
            if _has_comment(node):
                self.unresolved.append(
                    Finding(
                        self.rel_path,
                        self._line(node),
                        "assembled_module_string",
                        shown,
                        detail="a machinery module name joined across lines with comments; rewrite it by hand",
                        target=MACHINERY,
                    )
                )
                return
            value = static_value(node)
            self._string_kinds[id(node)] = type(value)
            self._string_rewrites[id(node)] = decision.new_value
            self._rewrite(node, decision.kind, _text(value), decision.new_value)  # type: ignore[arg-type]
        elif decision.action in ("unresolved", "inventory"):
            finding = Finding(
                self.rel_path, self._line(node), decision.kind, shown, detail=decision.detail, target=decision.target
            )
            (self.unresolved if decision.action == "unresolved" else self.inventory).append(finding)

    def _check_module_argument_list(self, node: cst.List | cst.Tuple) -> None:
        """``["-m", name]``: the module run is only known at run time."""

        values = [element.value for element in node.elements]
        for first, second in itertools.pairwise(values):
            if (
                isinstance(first, cst.SimpleString)
                and first.evaluated_value == "-m"
                and isinstance(second, (cst.Name, cst.Attribute, cst.Call, cst.Subscript))
            ):
                self.unresolved.append(
                    Finding(
                        self.rel_path,
                        self._line(node),
                        "computed_module_argument",
                        _code(node)[:160],
                        detail="the -m target is computed at run time",
                        target=AMBIGUOUS,
                    )
                )
                return

    def visit_List(self, node: cst.List) -> None:
        self._check_module_argument_list(node)

    def visit_Tuple(self, node: cst.Tuple) -> None:
        self._check_module_argument_list(node)

    # -- pass 1: import nodes -------------------------------------------

    def leave_Import(self, original_node: cst.Import, updated_node: cst.Import) -> cst.Import:
        self._import_depth -= 1
        names = []
        for alias in updated_node.names:
            dotted = get_full_name_for_node(alias.name) or ""
            new_alias = alias
            resolved = self.ownership.resolve(dotted)
            if resolved is not None:
                entry, rest = resolved
                if rest:
                    if self._missing_matters(dotted):
                        self._unresolved(
                            original_node, "unknown_module", f"import {dotted}", "the map has no such module"
                        )
                elif entry.owner == AMBIGUOUS:
                    self._unresolved(original_node, "ambiguous_module", f"import {dotted}", entry.note)
                elif entry.owner == MACHINERY:
                    new_alias = alias.with_changes(name=_dotted_node(renamed(dotted)))
                    self._rewrite(original_node, "import", f"import {dotted}", f"import {renamed(dotted)}")
            else:
                new_alias = self._unprefixed_import(original_node, alias, dotted)
            names.append(new_alias)
        return updated_node.with_changes(names=names)

    def _unprefixed_import(self, node: cst.Import, alias: cst.ImportAlias, dotted: str) -> cst.ImportAlias:
        shown = f"import {dotted}" + (f" as {alias.asname.name.value}" if isinstance(alias.asname, cst.AsName) else "")
        verdict, candidate, detail = self._unprefixed_decision(dotted, None)
        if verdict == "rewrite" and alias.asname is None and "." in dotted:
            verdict = "unprefixed_cross_owner"
            detail = f"`import {dotted}` binds {dotted.split('.')[0]!r}; a qualified import binds another name"
        if verdict in ("external", "keep"):
            return alias
        if verdict != "rewrite":
            self._unresolved(node, verdict, shown, detail)
            return alias
        new_name = renamed(candidate)
        asname = alias.asname if alias.asname is not None else cst.AsName(name=cst.Name(dotted))
        self._rewrite(node, "import_unprefixed", shown, f"import {new_name} as {asname.name.value}")
        return alias.with_changes(name=_dotted_node(new_name), asname=asname)

    def leave_ImportFrom(self, original_node: cst.ImportFrom, updated_node: cst.ImportFrom) -> cst.ImportFrom:
        self._import_depth -= 1
        level = len(updated_node.relative)
        module_text = get_full_name_for_node(updated_node.module) if updated_node.module is not None else ""
        shown = _code(original_node)
        if level:
            base = self.importer_package.split(".") if self.importer_package else []
            if level - 1 > len(base) or not self.importer_package:
                return updated_node
            base = base[: len(base) - (level - 1)]
            absolute = ".".join([*base, *([module_text] if module_text else [])])
            form = "relative"
        elif self.ownership.resolve(module_text or "") is not None:
            absolute = module_text or ""
            form = "qualified"
        else:
            names = (
                None
                if isinstance(updated_node.names, cst.ImportStar)
                else [get_full_name_for_node(a.name) or "" for a in updated_node.names]
            )
            verdict, candidate, detail = self._unprefixed_decision(module_text or "", names)
            if verdict in ("external", "keep"):
                return updated_node
            if verdict != "rewrite":
                self._unresolved(original_node, verdict, shown, detail)
                return updated_node
            absolute = candidate
            form = "unprefixed"

        resolved = self.ownership.resolve(absolute)
        if resolved is None:
            return updated_node  # a relative import outside scripts/
        entry, rest = resolved
        if rest:
            if self._missing_matters(absolute):
                self._unresolved(original_node, "unknown_module", shown, f"the map has no module {absolute}")
            return updated_node

        groups: dict[str, list[cst.ImportAlias]] = {}
        if isinstance(updated_node.names, cst.ImportStar):
            if self.ownership.subtree_owner(absolute) == AMBIGUOUS:
                self._unresolved(
                    original_node,
                    "ambiguous_module",
                    shown,
                    f"star import from {absolute}, whose submodules have both owners",
                )
                return updated_node
            owners = [entry.owner]
        else:
            owners = []
            for alias in updated_node.names:
                name = get_full_name_for_node(alias.name) or ""
                sub = self.ownership.module(f"{absolute}.{name}")
                owner = sub.owner if sub is not None else entry.owner
                owners.append(owner)
                groups.setdefault(owner, []).append(alias)
        if AMBIGUOUS in owners:
            self._unresolved(original_node, "ambiguous_module", shown, f"{absolute} has more than one owner below it")
            return updated_node
        if form == "relative" and self.importer_owner is None:
            self._unresolved(original_node, "unmapped_importer", shown, "relative import from a file the map lacks")
            return updated_node

        def target_text(owner: str) -> tuple[str, bool]:
            """(module text, keep the original relative spelling)."""

            new_name = renamed(absolute) if owner == MACHINERY else absolute
            if form == "qualified":
                return new_name, False
            if form == "unprefixed":
                # Product targets and same-side targets keep the sys.path spelling.
                return new_name, not (owner == MACHINERY and self.importer_owner == PRODUCT)
            importer_new = renamed(self.importer_package) if self.importer_owner == MACHINERY else self.importer_package
            base = importer_new.split(".")
            base = base[: len(base) - (level - 1)]
            still = ".".join([*base, *([module_text] if module_text else [])])
            return new_name, still == new_name

        def build(owner: str, aliases: list[cst.ImportAlias] | None) -> cst.ImportFrom:
            new_name, keep_relative = target_text(owner)
            node = updated_node
            if not keep_relative and (form != "qualified" or new_name != absolute):
                node = node.with_changes(module=_dotted_node(new_name), relative=())
            if aliases is not None:
                node = node.with_changes(**_regroup(updated_node, aliases))
            return node

        unique = list(dict.fromkeys(owners))
        if len(unique) == 1:
            new_node = build(unique[0], None)
            if new_node is not updated_node:
                kind = {"relative": "import_from_relative", "unprefixed": "import_from_unprefixed"}.get(
                    form, "import_from"
                )
                self._rewrite(original_node, kind, shown, _code(new_node))
            return new_node

        pieces = [build(owner, groups[owner]) for owner in unique]
        if all(piece.module is updated_node.module and piece.relative is updated_node.relative for piece in pieces):
            return updated_node  # every group keeps the same spelling; nothing to split
        self._splits[id(original_node)] = pieces
        self._split_origin[id(original_node)] = (self._line(original_node), shown)
        self._rewrite(original_node, "import_from_split", shown, " | ".join(_code(p) for p in pieces))
        return updated_node

    def _expand_splits(
        self, original_body: Sequence[cst.BaseSmallStatement], updated_body: Sequence[cst.BaseSmallStatement]
    ) -> list[cst.BaseSmallStatement]:
        """Replace each split import by its pieces, joined with semicolons on the same line."""

        body: list[cst.BaseSmallStatement] = []
        for original, updated in zip(original_body, updated_body, strict=True):
            pieces = self._splits.get(id(original))
            if pieces is None:
                body.append(updated)
                continue
            self._consumed_splits.add(id(original))
            last = len(pieces) - 1
            body.extend(
                piece.with_changes(semicolon=updated.semicolon if i == last else cst.MaybeSentinel.DEFAULT)
                for i, piece in enumerate(pieces)
            )
        return body

    def leave_SimpleStatementLine(
        self, original_node: cst.SimpleStatementLine, updated_node: cst.SimpleStatementLine
    ) -> cst.BaseStatement | cst.FlattenSentinel[cst.BaseStatement]:
        if not any(id(stmt) in self._splits for stmt in original_node.body):
            return updated_node
        if len(original_node.body) == 1:
            # A lone split import becomes one line per owner.
            pieces = self._splits[id(original_node.body[0])]
            self._consumed_splits.add(id(original_node.body[0]))
            return cst.FlattenSentinel(
                [
                    updated_node.with_changes(body=[piece], leading_lines=updated_node.leading_lines if i == 0 else ())
                    for i, piece in enumerate(pieces)
                ]
            )
        return updated_node.with_changes(body=self._expand_splits(original_node.body, updated_node.body))

    def leave_SimpleStatementSuite(
        self, original_node: cst.SimpleStatementSuite, updated_node: cst.SimpleStatementSuite
    ) -> cst.SimpleStatementSuite:
        """``if ready: from scripts import a, b`` keeps one line, with the pieces joined by semicolons."""

        if not any(id(stmt) in self._splits for stmt in original_node.body):
            return updated_node
        return updated_node.with_changes(body=self._expand_splits(original_node.body, updated_node.body))

    # -- bound names: ``import scripts.x`` then ``scripts.x.f`` ----------

    def leave_Attribute(self, original_node: cst.Attribute, updated_node: cst.Attribute) -> cst.Attribute:
        if self._import_depth:
            return updated_node
        parent = self.get_metadata(ParentNodeProvider, original_node, None)
        if isinstance(parent, cst.Attribute) and parent.value is original_node:
            return updated_node  # only the whole chain is resolved
        root = original_node
        while isinstance(root, cst.Attribute):
            root = root.value
        if not isinstance(root, cst.Name):
            return updated_node
        qualified = self.get_metadata(QualifiedNameProvider, original_node, set())
        imported = {q.name for q in qualified if q.source == QualifiedNameSource.IMPORT}
        ours = {name for name in imported if name == OLD_ROOT or name.startswith(OLD_ROOT + ".")}
        if not ours:
            return updated_node  # not bound to a scripts module (a local, or another package)
        dotted = get_full_name_for_node(original_node) or ""
        if len(qualified) != 1:
            detail = f"{root.value} is bound in more than one way here ({', '.join(sorted(q.name for q in qualified))})"
            self._unresolved(original_node, "rebound_name", dotted, detail)
            return updated_node
        (name,) = ours
        if not (root.value == OLD_ROOT and name == dotted):
            self._check_aliased_chain(original_node, root.value, dotted, name)
            return updated_node  # the alias keeps its name; the import that binds it is renamed on its own
        resolved = self.ownership.resolve(dotted)
        if resolved is None:
            return updated_node
        entry, _rest = resolved
        if entry.owner == AMBIGUOUS:
            self._unresolved(original_node, "ambiguous_module", dotted, entry.note)
            return updated_node
        if entry.owner != MACHINERY:
            self._kept_chain = True
            return updated_node
        self._renamed_chain = True
        self._rewrite(original_node, "bound_name", dotted, renamed(dotted))
        return _replace_root(updated_node, NEW_ROOT)

    def _check_aliased_chain(self, node: cst.Attribute, alias: str, dotted: str, qualified: str) -> None:
        """``import scripts.x as a`` or ``from scripts import x as a``, then ``a.y``.

        Renaming the import keeps ``a``, so the chain still works unless it reaches a module of the
        other owner (``a.y`` where ``scripts.x.y`` is a submodule of the other side): that is reported.
        """

        suffix = dotted[len(alias) :]
        if not qualified.endswith(suffix):
            self._unresolved(node, "rebound_name", dotted, f"{alias} is bound to {qualified}")
            return
        bound = self.ownership.resolve(qualified[: len(qualified) - len(suffix)])
        reached = self.ownership.resolve(qualified)
        if bound is None or reached is None:
            return
        if AMBIGUOUS in (bound[0].owner, reached[0].owner):
            self._unresolved(node, "ambiguous_binding", dotted, f"{qualified} has no single owner")
        elif reached[0].name != bound[0].name and reached[0].owner != bound[0].owner:
            detail = f"{alias} is {bound[0].name} ({bound[0].owner}), but {qualified} is in {reached[0].name} ({reached[0].owner})"
            self._unresolved(node, "alias_crosses_owner", dotted, detail)

    def leave_Name(self, original_node: cst.Name, updated_node: cst.Name) -> cst.Name:
        """A bare use of the package bound by ``import scripts...`` cannot be resolved statically."""

        if self._import_depth or original_node.value != OLD_ROOT:
            return updated_node
        parent = self.get_metadata(ParentNodeProvider, original_node, None)
        if isinstance(parent, cst.Attribute) and (parent.value is original_node or parent.attr is original_node):
            return updated_node  # a chain root (leave_Attribute) or an attribute name
        if isinstance(parent, cst.Arg) and parent.keyword is original_node:
            return updated_node
        qualified = self.get_metadata(QualifiedNameProvider, original_node, set())
        if any(q.source == QualifiedNameSource.IMPORT and q.name == OLD_ROOT for q in qualified):
            self._unresolved(
                original_node,
                "bare_package_use",
                _code(parent) if isinstance(parent, cst.CSTNode) else OLD_ROOT,
                "uses the package object bound by `import scripts...`; what it reaches cannot be resolved",
            )
        return updated_node

    def visit_Attribute(self, node: cst.Attribute) -> None:
        self._check_loader_value(node)

    def visit_Name(self, node: cst.Name) -> None:
        self._check_loader_value(node)

    def _check_loader_value(self, node: cst.Attribute | cst.Name) -> None:
        """A loader passed around as a value (``load = importlib.import_module``) hides every call."""

        if self._import_depth or not _is_dotted_name(node):
            return  # ``__import__("x").attr`` inherits the call's qualified name; it is not the loader
        parent = self.get_metadata(ParentNodeProvider, node, None)
        if isinstance(parent, cst.Call) and parent.func is node:
            return  # a direct call: visit_Call checks its target
        if isinstance(parent, cst.Attribute) and parent.value is node:
            return  # the inner part of a longer name
        if isinstance(parent, cst.Attribute) and parent.attr is node:
            return  # the attribute name itself; the whole Attribute is checked
        if isinstance(parent, (cst.Arg, cst.Param, cst.Decorator)) and getattr(parent, "keyword", None) is node:
            return
        qualified = {q.name for q in self.get_metadata(QualifiedNameProvider, node, set())}
        if qualified & set(LOADERS):
            self._unresolved(
                node,
                "loader_reference",
                _code(parent) if parent else _code(node),
                "a loader used as a value; its calls cannot be resolved",
            )

    # -- pass 2: loader targets and module strings -----------------------

    def _hold_loader_call(self, node: cst.Call) -> None:
        """A reported loader call stays as written: none of its string arguments is rewritten."""

        for arg in node.args:
            self._loader_args.add(id(arg.value))

    def visit_Call(self, node: cst.Call) -> None:
        if not _is_dotted_name(node.func):
            return  # ``__import__("x").attr(...)`` reports the inner call's name for the outer one
        qualified = {q.name for q in self.get_metadata(QualifiedNameProvider, node.func, set())}
        loaders = [name for name in qualified if name in LOADERS]
        if not loaders:
            return
        loader = loaders[0]
        keyword = LOADERS[loader]
        shown = _code(node)

        def report(kind: str, detail: str) -> None:
            self._hold_loader_call(node)
            self._unresolved(node, kind, shown, detail)

        # Read every argument: unpacking can hide the target, or __import__'s fromlist and level.
        positional = [arg for arg in node.args if arg.keyword is None and not arg.star]
        unpacked = [arg for arg in node.args if arg.star]
        hidden_first = (
            any(arg.star == "*" for arg in node.args[: node.args.index(positional[0])])
            if positional
            else bool(unpacked)
        )
        target = next(
            (arg.value for arg in node.args if arg.keyword is not None and arg.keyword.value == keyword), None
        )
        if target is None and positional and not hidden_first:
            target = positional[0].value
        if target is None:
            if unpacked:
                report("computed_loader", "the loader target comes from unpacked arguments")
            return
        if loader.endswith("__import__"):
            if unpacked:
                report("computed_loader", "unpacked arguments may set __import__'s fromlist or level")
                return
            level = next((a.value for a in node.args if a.keyword is not None and a.keyword.value == "level"), None)
            if level is None and len(positional) > 4:
                level = positional[4].value
            if level is not None and not (isinstance(level, cst.Integer) and level.evaluated_value == 0):
                report("relative_loader", "a non-zero or computed level makes the import relative")
                return
        self._loader_args.add(id(target))
        if not (isinstance(target, cst.SimpleString) and isinstance(target.evaluated_value, str)):
            report("computed_loader", "the loader target is computed at run time")
            return
        value = target.evaluated_value
        if value.startswith("."):
            report("relative_loader", "a relative loader target depends on its package")
            return
        resolved = self.ownership.resolve(value)
        if resolved is None:
            self._unprefixed_loader(node, target, value, shown)
            return
        entry, rest = resolved
        if rest:
            if self._missing_matters(value):
                report("unknown_module", f"the map has no module {value}")
            return
        owner = entry.owner
        main = self.ownership.module(f"{value}.__main__")
        if loader == "runpy.run_module" and main is not None and main.owner != owner:
            owner = AMBIGUOUS  # run_module runs the package's __main__
        has_fromlist = (
            any(a.keyword is not None and a.keyword.value == "fromlist" for a in node.args) or len(positional) > 3
        )
        if loader.endswith("__import__") and has_fromlist and self.ownership.subtree_owner(value) == AMBIGUOUS:
            owner = AMBIGUOUS  # the fromlist may name submodules of either owner
        if owner == AMBIGUOUS:
            report("ambiguous_module", f"{value} has more than one owner for this loader")
        elif owner == MACHINERY:
            self._loader_rewrites[id(target)] = renamed(value)

    def _unprefixed_loader(self, node: cst.Call, target: cst.SimpleString, value: str, shown: str) -> None:
        verdict, candidate, detail = self._unprefixed_decision(value, None)
        if verdict == "rewrite":
            self._loader_rewrites[id(target)] = renamed(candidate)
        elif verdict not in ("external", "keep"):
            self._hold_loader_call(node)
            self._unresolved(node, verdict, shown, detail)

    def leave_SimpleString(self, original_node: cst.SimpleString, updated_node: cst.SimpleString) -> cst.SimpleString:
        if id(original_node) in self._loader_rewrites:
            new_value = self._loader_rewrites[id(original_node)]
            self._rewrite(original_node, "loader", str(original_node.evaluated_value), new_value)
            return _with_string_value(original_node, updated_node, new_value)
        return updated_node

    # -- binding check --------------------------------------------------

    def leave_Module(self, original_node: cst.Module, updated_node: cst.Module) -> cst.Module:
        for split_id in sorted(set(self._splits) - self._consumed_splits):
            line, shown = self._split_origin[split_id]
            self.unresolved.append(
                Finding(self.rel_path, line, "split_not_applied", shown, detail="a split import was not placed")
            )
        bound = _unaliased_import_roots(updated_node)
        if self._renamed_chain and NEW_ROOT not in bound:
            self._unresolved(
                original_node,
                "binding_missing",
                f"{NEW_ROOT}.*",
                "a renamed attribute chain has no `import lu_machinery...`",
            )
        if self._kept_chain and OLD_ROOT not in bound:
            self._unresolved(
                original_node,
                "binding_missing",
                f"{OLD_ROOT}.*",
                "a product attribute chain lost its `import scripts...`",
            )
        return updated_node


def _literal_text(node: cst.SimpleString) -> str:
    """The value of a plain literal; bytes are read as Latin-1 so a module name in them is visible."""

    value = node.evaluated_value
    return value.decode("latin-1") if isinstance(value, bytes) else value


def _fstring_text(node: cst.FormattedString, raw: str) -> str:
    """Decode the escapes in one literal stretch of an f-string, as Python would."""

    if "r" not in node.start.lower():
        try:
            decoded = ast.literal_eval(f"{node.end}{raw}{node.end}")
        except (SyntaxError, ValueError):
            decoded = raw
        raw = decoded if isinstance(decoded, str) else raw
    return raw.replace("{{", "{").replace("}}", "}")


# -- strings: fail closed ----------------------------------------------------
#
# A string expression is renamed only when it is a plain literal (or literals joined by implicit
# concatenation, ``+`` or an f-string without fields) whose exact value is one machinery module name.
# Every other string expression that may hold a ``scripts`` module name or path is reported.
# There is no partial evaluation: a value is either known exactly from literals, or it is not known.

# A module name, optionally followed by attributes: ``scripts.x.y``.
MODULE_LITERAL = re.compile(r"scripts(?:\.[A-Za-z_][A-Za-z0-9_]*)+")
WORD = "scripts"
# ``scripts`` as a word: not inside a longer identifier, except right after a glued ``-m``.
WORD_AT = re.compile(r"(?:(?<![A-Za-z0-9_])|(?<=-m))scripts(?![A-Za-z0-9_])")
# ``Scripts/x.py`` in another case: the same file on a case-insensitive file system.
CASE_VARIANT = re.compile(r"(?<![A-Za-z0-9_])(?!scripts)(?i:scripts)(?=/)")
IDENT = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
PATH_CHARS = re.compile(r"[A-Za-z0-9_.\-/]*")
GLOB_CHARS = frozenset("*?[")

# Methods whose arguments become part of the result or shape it; their arguments are part of
# the string being built. Dunder methods (``"a".__add__(b)``) count too.
STR_METHODS = frozenset(
    {
        "capitalize", "casefold", "center", "decode", "encode", "expandtabs", "format", "format_map",
        "join", "ljust", "lower", "lstrip", "maketrans", "partition", "removeprefix", "removesuffix",
        "replace", "rjust", "rpartition", "rsplit", "rstrip", "split", "splitlines", "strip", "swapcase",
        "title", "translate", "upper", "zfill",
    }
)  # fmt: skip
# Builtins that return their arguments' text, reordered, re-encoded or cut.
TRANSFORM_BUILTINS = frozenset(
    {
        "ascii", "bytearray", "bytes", "chr", "dict", "enumerate", "filter", "format", "frozenset", "iter",
        "list", "map", "max", "min", "next", "repr", "reversed", "set", "sorted", "str", "tuple", "zip",
    }
)  # fmt: skip
# Builtins the exact evaluator runs on known values (assumed not shadowed).
SAFE_BUILTINS = {
    "ascii": ascii,
    "chr": chr,
    "format": format,
    "len": len,
    "list": list,
    "max": max,
    "min": min,
    "ord": ord,
    "repr": repr,
    "reversed": lambda value: list(reversed(value)),
    "sorted": sorted,
    "str": str,
    "tuple": tuple,
}
SAFE_OPERATORS = {
    cst.Add: operator.add,
    cst.Subtract: operator.sub,
    cst.Multiply: operator.mul,
    cst.Modulo: operator.mod,
    cst.FloorDivide: operator.floordiv,
    cst.Divide: operator.truediv,
}
# Larger numbers or widths could build a huge value; such an expression is treated as not known.
MAX_EVAL_INT = 10_000
MAX_EVAL_LEN = 1_000_000
WIDE_FIELD = re.compile(r"\d{5,}")
CONVERSIONS: dict[str | None, Callable[[object], object]] = {None: lambda value: value, "s": str, "r": repr, "a": ascii}


class NotStatic(Exception):
    """The expression has a run-time piece or an operation the exact evaluator does not run."""


class StaticError(Exception):
    """Python itself would raise on these known values."""


def _guard(value: object) -> object:
    if isinstance(value, int) and not isinstance(value, bool) and abs(value) > MAX_EVAL_INT:
        raise NotStatic
    if isinstance(value, (str, bytes, list, tuple)) and len(value) > MAX_EVAL_LEN:
        raise NotStatic
    return value


def _size(value: object) -> int:
    """An upper bound on the text a value can put into a result."""

    if isinstance(value, (str, bytes)):
        return len(value)
    if isinstance(value, dict):
        return sum(_size(k) + _size(v) + 4 for k, v in value.items()) + 2
    if isinstance(value, (list, tuple, set, frozenset)):
        return sum(_size(v) + 2 for v in value) + 2
    return len(repr(value))


def _result_bound(function: object, args: Sequence[object], kwargs: Mapping[str, object]) -> int:
    """An upper bound on the size of an operation's result, computed before running it."""

    inputs = sum(_size(v) for v in (*args, *kwargs.values()))
    method = getattr(function, "__name__", "")
    receiver = getattr(function, "__self__", None)
    if function in (operator.add, operator.getitem):
        return inputs
    if function is operator.mul:
        sizes = [_size(a) if isinstance(a, (str, bytes, list, tuple)) else a for a in args]
        return abs(sizes[0] * sizes[1]) if all(isinstance(n, int) for n in sizes) else inputs  # type: ignore[operator]
    if function is operator.mod and args and isinstance(args[0], (str, bytes)):
        template = _text(args[0])
        return len(template) + 6 * inputs + MAX_EVAL_INT * template.count("%")
    if not isinstance(receiver, (str, bytes)):
        return 6 * inputs + MAX_EVAL_INT  # an operator or builtin over guarded inputs
    size = len(receiver)
    values = [*args, *kwargs.values()]
    if method == "replace":
        new = args[1] if len(args) > 1 else kwargs.get("new", "")
        return size + (size + 1) * _size(new)
    if method == "join":
        items = args[0] if args else ()
        count = len(items) if isinstance(items, (str, bytes, list, tuple, set, frozenset, dict)) else MAX_EVAL_LEN
        return inputs + size * count
    if method == "translate":
        table = args[0] if args else {}
        widest = max((_size(v) for v in table.values()), default=1) if isinstance(table, dict) else MAX_EVAL_LEN
        return size * max(widest, 1)
    if method == "expandtabs":
        tab = values[0] if values else 8
        return size * max(tab if isinstance(tab, int) else MAX_EVAL_LEN, 1)
    if method in ("format", "format_map"):
        fields = _text(receiver).count("{")
        return size + inputs * (fields + 1) + MAX_EVAL_INT * fields
    return 4 * (size + inputs) + MAX_EVAL_INT  # padding, case changes, encodings, splits


def _call_static(function: Callable[..., object], *args: object, **kwargs: object) -> object:
    for value in (*args, *kwargs.values()):
        _guard(value)
    if _result_bound(function, args, kwargs) > MAX_EVAL_LEN:
        raise NotStatic  # the result could be too large to build
    try:
        return _guard(function(*args, **kwargs))
    except NotStatic:
        raise
    except Exception as exc:
        raise StaticError(f"{type(exc).__name__}: {exc}") from exc


def static_value(node: cst.CSTNode) -> object:
    """The exact value of an expression made only of literals and the operations below.

    Raises ``NotStatic`` for anything else (names, attributes, other calls, ``f"{x=}"``) and
    ``StaticError`` when Python itself would raise on these values.
    """

    if isinstance(node, (cst.SimpleString, cst.Integer, cst.Float, cst.Imaginary)):
        return _guard(node.evaluated_value)
    if isinstance(node, cst.Name) and node.value in ("True", "False", "None"):
        return {"True": True, "False": False, "None": None}[node.value]
    if isinstance(node, cst.ConcatenatedString):
        return _call_static(operator.add, static_value(node.left), static_value(node.right))
    if isinstance(node, cst.FormattedString):
        return "".join(_static_fstring_parts(node, node.parts))
    if isinstance(node, cst.BinaryOperation):
        function = SAFE_OPERATORS.get(type(node.operator))
        if function is None:
            raise NotStatic
        left, right = static_value(node.left), static_value(node.right)
        if function is operator.mod and isinstance(left, (str, bytes)) and WIDE_FIELD.search(_text(left)):
            raise NotStatic
        return _call_static(function, left, right)
    if isinstance(node, cst.UnaryOperation):
        value = static_value(node.expression)
        unary = {
            cst.Minus: operator.neg,
            cst.Plus: operator.pos,
            cst.Not: operator.not_,
            cst.BitInvert: operator.invert,
        }
        return _call_static(unary[type(node.operator)], value)
    if isinstance(node, cst.Subscript):
        receiver = static_value(node.value)
        if len(node.slice) != 1:
            raise NotStatic
        element = node.slice[0].slice
        if isinstance(element, cst.Index) and element.star is None:
            key: object = static_value(element.value)
        elif isinstance(element, cst.Slice):
            key = slice(*(None if b is None else static_value(b) for b in (element.lower, element.upper, element.step)))
        else:
            raise NotStatic
        return _call_static(operator.getitem, receiver, key)
    if isinstance(node, cst.Call):
        return _static_call(node)
    if isinstance(node, cst.IfExp):
        return static_value(node.body) if static_value(node.test) else static_value(node.orelse)
    if isinstance(node, cst.BooleanOperation):
        left = static_value(node.left)
        if isinstance(node.operator, cst.And):
            return static_value(node.right) if left else left
        return left if left else static_value(node.right)
    if isinstance(node, cst.NamedExpr):
        return static_value(node.value)
    if isinstance(node, (cst.List, cst.Tuple, cst.Set)):
        values: list[object] = []
        for element in node.elements:
            if isinstance(element, cst.StarredElement):
                values.extend(_call_static(list, static_value(element.value)))  # type: ignore[arg-type]
            else:
                values.append(static_value(element.value))
        kind = {cst.List: list, cst.Tuple: tuple, cst.Set: set}[type(node)]
        return _call_static(kind, values)
    if isinstance(node, cst.Dict):
        result: dict[object, object] = {}
        for element in node.elements:
            if isinstance(element, cst.DictElement):
                result[static_value(element.key)] = static_value(element.value)  # type: ignore[index]
            else:
                result.update(_call_static(dict, static_value(element.value)))  # type: ignore[arg-type]
        return result
    raise NotStatic


def _static_fstring_parts(node: cst.FormattedString, parts: Sequence[cst.BaseFormattedStringContent]) -> Iterator[str]:
    total = 0
    for part in parts:
        if total > MAX_EVAL_LEN:
            raise NotStatic
        if isinstance(part, cst.FormattedStringText):
            text = _fstring_text(node, part.value)
            total += len(text)
            yield text
            continue
        if not isinstance(part, cst.FormattedStringExpression) or part.equal is not None:
            raise NotStatic
        value = static_value(part.expression)
        spec = "".join(_static_fstring_parts(node, part.format_spec)) if part.format_spec else ""
        if WIDE_FIELD.search(spec):
            raise NotStatic
        converted = _call_static(CONVERSIONS[part.conversion], value)
        text = str(_call_static(format, converted, spec))
        total += len(text)
        yield text


def _static_call(node: cst.Call) -> object:
    args: list[object] = []
    kwargs: dict[str, object] = {}
    for arg in node.args:
        value = static_value(arg.value)
        if arg.star == "*":
            args.extend(_call_static(list, value))  # type: ignore[arg-type]
        elif arg.star == "**":
            kwargs.update(_call_static(dict, value))  # type: ignore[arg-type]
        elif arg.keyword is not None:
            kwargs[arg.keyword.value] = value
        else:
            args.append(value)
    if isinstance(node.func, cst.Name) and node.func.value in SAFE_BUILTINS:
        if node.func.value == "format" and any(isinstance(a, str) and WIDE_FIELD.search(a) for a in args[1:]):
            raise NotStatic
        return _call_static(SAFE_BUILTINS[node.func.value], *args, **kwargs)
    if not isinstance(node.func, cst.Attribute):
        raise NotStatic
    receiver = static_value(node.func.value)
    method = node.func.attr.value
    if not isinstance(receiver, (str, bytes)) or method.startswith("_") or not hasattr(type(receiver), method):
        raise NotStatic
    if method in ("format", "format_map"):
        template = receiver if isinstance(receiver, str) else ""
        for _literal, field_name, spec, _conversion in _call_static(
            lambda t: list(string.Formatter().parse(t)), template
        ):  # type: ignore[attr-defined]
            if (field_name and re.search(r"[.\[]", field_name)) or (spec and ("{" in spec or WIDE_FIELD.search(spec))):
                raise NotStatic  # attribute or index access inside a field, or a nested spec
    return _call_static(getattr(receiver, method), *args, **kwargs)


def _text(value: str | bytes) -> str:
    return value.decode("latin-1") if isinstance(value, bytes) else value


def _strings_in(value: object) -> Iterator[str]:
    """Every string in a known value (bytes read as Latin-1), containers included."""

    if isinstance(value, (str, bytes)):
        yield _text(value)
    elif isinstance(value, dict):
        for key, item in value.items():
            yield from _strings_in(key)
            yield from _strings_in(item)
    elif isinstance(value, (list, tuple, set, frozenset)):
        for item in value:
            yield from _strings_in(item)


def is_plain_concatenation(node: cst.CSTNode) -> bool:
    """Literals joined by implicit concatenation, ``+`` or an f-string without fields."""

    if isinstance(node, cst.SimpleString):
        return True
    if isinstance(node, cst.ConcatenatedString):
        return is_plain_concatenation(node.left) and is_plain_concatenation(node.right)
    if isinstance(node, cst.FormattedString):
        return all(isinstance(part, cst.FormattedStringText) for part in node.parts)
    if isinstance(node, cst.BinaryOperation) and isinstance(node.operator, cst.Add):
        return is_plain_concatenation(node.left) and is_plain_concatenation(node.right)
    return False


def spells_word(texts: Sequence[str], word: str = WORD) -> bool:
    """Whether ``word`` (case-insensitive) is in one text, or is spelled by joining the end of one
    text, zero or more whole texts and the start of another, in any order (so run-time pieces
    between them, or a reordering, may join them)."""

    lowered = [t.lower() for t in texts if t]
    if any(word in t for t in lowered):
        return True

    def extend(position: int, used: frozenset[int]) -> bool:
        rest = word[position:]
        for index, text in enumerate(lowered):
            if index in used:
                continue
            if rest.startswith(text) and len(text) < len(rest) and extend(position + len(text), used | {index}):
                return True  # a whole text in the middle
            if text.startswith(rest):
                return True  # the start of a text ends the word
        return False

    for index, text in enumerate(lowered):
        for cut in range(1, len(word)):
            if text.endswith(word[:cut]) and extend(cut, frozenset({index})):
                return True
    return False


@dataclass(frozen=True)
class Reference:
    """One ``scripts`` module name or path found in a known text, and what the map says about it."""

    text: str
    form: str  # module, module_prefix, path, glob, root
    target: str  # machinery, product, ambiguous, unknown


def text_references(ownership: OwnershipMap, text: str) -> list[Reference]:
    """Every ``scripts`` module name or path in a known text.

    A bare word ``scripts`` is the root (``root``) when it is the whole text, optionally with a final
    ``.`` or ``/``. Inside longer text (``cd scripts``, a regular expression, or the English word) it is
    ``root_in_text``: it may name the shared root, so it is reported too.
    """

    found: list[Reference] = []
    stripped = text.strip()
    for match in WORD_AT.finditer(text):
        start, end = match.start(), match.end()
        following = text[end : end + 1]
        if following == "." and IDENT.match(text, end + 1):
            dotted = MODULE_LITERAL.match(text, start)
            assert dotted is not None
            name = dotted.group(0)
            after = text[dotted.end() : dotted.end() + 1]
            if after == "." and not IDENT.match(text, dotted.end() + 1):
                found.append(Reference(name + ".", "module_prefix", _subtree_target(ownership, name)))
            else:
                found.append(Reference(name, "module", module_target(ownership, name)))
        elif following == "/":
            core = PATH_CHARS.match(text, end).group(0)  # type: ignore[union-attr]
            name = WORD + core
            rest = text[end + len(core) : end + len(core) + 1]
            if rest and rest in GLOB_CHARS:
                found.append(Reference(name + "…", "glob", "unknown"))
            else:
                found.append(
                    Reference(name, "path" if name.rstrip("/") != WORD else "root", path_target(ownership, name))
                )
        elif stripped in (WORD, WORD + ".", WORD + "/"):
            found.append(Reference(stripped, "root", AMBIGUOUS))
        else:
            found.append(Reference(WORD, "root_in_text", AMBIGUOUS))
    for match in CASE_VARIANT.finditer(text):
        core = PATH_CHARS.match(text, match.end()).group(0)  # type: ignore[union-attr]
        found.append(Reference(match.group(0) + core, "case_variant", path_target(ownership, WORD + core)))
    return found


def module_target(ownership: OwnershipMap, name: str, exact: bool = False) -> str:
    """Owner of a dotted name: its longest module, whose attributes the rest names (none with ``exact``).

    A package whose ``__main__`` has the other owner is ambiguous: ``-m`` or ``run_module`` runs that file.
    """

    resolved = ownership.resolve(name)
    if resolved is None:
        return "unknown"
    entry, rest = resolved
    if entry.name == OLD_ROOT:
        return "unknown" if rest else AMBIGUOUS
    if rest and (exact or entry.bound_file is None):
        return "unknown"  # a namespace package has no attributes, only submodules the map lacks
    main = ownership.module(f"{entry.name}.__main__")
    if not rest and main is not None and main.owner != entry.owner:
        return AMBIGUOUS
    return entry.owner


def _subtree_target(ownership: OwnershipMap, name: str) -> str:
    resolved = ownership.resolve(name)
    if resolved is None or resolved[1]:
        return "unknown"
    return ownership.subtree_owner(resolved[0].name) or "unknown"


def path_target(ownership: OwnershipMap, path: str) -> str:
    """Owner of a ``scripts/...`` file or directory path; ``..`` and empty segments are unknown."""

    stripped = path.rstrip("/")
    if stripped == OLD_ROOT:
        return AMBIGUOUS
    if any(part in ("", ".", "..") for part in stripped.split("/")):
        return "unknown"
    return ownership.path_owner(stripped) or "unknown"


def _likely_target(ownership: OwnershipMap, leaves: Sequence[str]) -> str:
    """For counting only: what a string built at run time most likely names (its literals joined)."""

    texts = ["/".join(leaves), "".join(leaves), *leaves]
    references = [ref for text in texts for ref in text_references(ownership, text) if ref.form != "root"]
    return worst_target(references) if references else AMBIGUOUS


def worst_target(references: Iterable[Reference]) -> str:
    targets = {ref.target for ref in references}
    for target in (MACHINERY, AMBIGUOUS, "unknown", PRODUCT):
        if target in targets:
            return target
    return PRODUCT


@dataclass
class StringDecision:
    """What to do with one string expression: rewrite it, report it, list it, or nothing."""

    action: str  # rewrite, unresolved, inventory, none
    kind: str = ""
    detail: str = ""
    new_value: str = ""
    target: str = ""


def decide_string(
    ownership: OwnershipMap, node: cst.CSTNode, leaves: Sequence[str], prose: bool = False
) -> StringDecision:
    """Decide one string expression (``node``) whose literal texts are ``leaves``.

    ``prose`` marks a docstring: never rewritten; machinery mentions go to the inventory.
    """

    try:
        value = static_value(node)
    except (NotStatic, StaticError) as exc:
        if not spells_word(leaves):
            return StringDecision("none")
        target = _likely_target(ownership, leaves)
        if prose:
            return StringDecision("inventory", "docstring_mention", "left as written", target=target)
        if isinstance(exc, StaticError):
            return StringDecision("unresolved", "unevaluable_string", f"Python would raise here ({exc})", target=target)
        detail = "built at run time from literals that may spell a scripts module or path"
        return StringDecision("unresolved", "computed_string", detail, target=target)
    texts = list(_strings_in(value))
    references = [ref for text in texts for ref in text_references(ownership, text)]
    plain = is_plain_concatenation(node)
    if prose:
        mentions = [ref for ref in references if ref.target != PRODUCT]
        if mentions:
            shown = ", ".join(ref.text for ref in mentions)
            return StringDecision(
                "inventory", "docstring_mention", f"left as written: {shown}", target=worst_target(mentions)
            )
        return StringDecision("none")
    if plain and isinstance(value, (str, bytes)) and MODULE_LITERAL.fullmatch(_text(value)):
        name = _text(value)
        target = module_target(ownership, name)
        if target == MACHINERY:
            return StringDecision("rewrite", "module_literal", new_value=renamed(name), target=MACHINERY)
        if target == PRODUCT:
            return StringDecision("none")
        detail = "no single owner" if target == AMBIGUOUS else "the map has no such module"
        return StringDecision(
            "unresolved", "ambiguous_module" if target == AMBIGUOUS else "unknown_module", detail, target=target
        )
    if not references:
        return StringDecision("none")
    if all(ref.target == PRODUCT for ref in references):
        return StringDecision("none")
    shown = ", ".join(ref.text for ref in references if ref.target != PRODUCT)
    target = worst_target(references)
    if not plain:
        return StringDecision(
            "unresolved", "static_expression", f"its value names {shown}; rewrite it by hand", target=target
        )
    forms = {ref.form for ref in references if ref.target != PRODUCT}
    single = len(references) == 1 and texts == [references[0].text]
    if forms <= {"path", "glob", "case_variant"}:
        kind = "path_string" if single else "path_in_text"
    elif forms <= {"root", "root_in_text"}:
        kind = "root_reference" if "root" in forms else "root_in_text"
    elif forms == {"module_prefix"}:
        kind = "module_prefix"
    else:
        kind = "module_in_text"
    return StringDecision("unresolved", kind, f"names {shown}", target=target)


def _shapes_arguments(call: cst.Call) -> bool:
    """A call whose arguments become part of its string result: a str method or a text builtin."""

    if isinstance(call.func, cst.Attribute):
        name = call.func.attr.value
        return name in STR_METHODS or (name.startswith("__") and name.endswith("__"))
    return isinstance(call.func, cst.Name) and call.func.value in TRANSFORM_BUILTINS


class _StringCollector(cst.CSTVisitor):
    """Every string literal and f-string in a module, in source order."""

    def __init__(self) -> None:
        self.nodes: list[cst.CSTNode] = []

    def visit_SimpleString(self, node: cst.SimpleString) -> None:
        self.nodes.append(node)

    def visit_FormattedString(self, node: cst.FormattedString) -> None:
        self.nodes.append(node)


def _leaf_texts(leaf: cst.CSTNode) -> list[str]:
    if isinstance(leaf, cst.SimpleString):
        return [_literal_text(leaf)]
    assert isinstance(leaf, cst.FormattedString)
    return [_fstring_text(leaf, part.value) for part in leaf.parts if isinstance(part, cst.FormattedStringText)]


def _has_comment(node: cst.CSTNode) -> bool:
    found: list[cst.Comment] = []

    class Finder(cst.CSTVisitor):
        def visit_Comment(self, comment: cst.Comment) -> None:
            found.append(comment)

    node.visit(Finder())
    return bool(found)


def _is_dotted_name(node: cst.BaseExpression) -> bool:
    while isinstance(node, cst.Attribute):
        node = node.value
    return isinstance(node, cst.Name)


def _with_string_value(original: cst.SimpleString, updated: cst.SimpleString, value: str) -> cst.SimpleString:
    """Same prefix and quotes, new contents (module names need no escaping)."""

    return updated.with_changes(value=f"{original.prefix}{original.quote}{value}{original.quote}")


def _replace_root(node: cst.BaseExpression, new_root: str) -> cst.BaseExpression:
    if isinstance(node, cst.Attribute):
        return node.with_changes(value=_replace_root(node.value, new_root))
    assert isinstance(node, cst.Name)
    return node.with_changes(value=new_root)


def _regroup(original: cst.ImportFrom, aliases: list[cst.ImportAlias]) -> dict[str, object]:
    """Changes that give one owner group its own statement.

    Each alias keeps its comma and the comment after it. Only the group's last alias is
    adjusted: without parentheses it loses its comma; inside parentheses it ends on the
    original closing indentation, so ``)`` lands where it did before.
    """

    assert not isinstance(original.names, cst.ImportStar)
    last_original = original.names[-1]
    result = list(aliases)
    tail = result[-1]
    changes: dict[str, object] = {"names": result}
    if original.lpar is None or original.rpar is None:
        result[-1] = tail.with_changes(comma=cst.MaybeSentinel.DEFAULT)
        return changes
    if tail is last_original:
        return changes
    closing = last_original.comma.whitespace_after if isinstance(last_original.comma, cst.Comma) else None
    if closing is None:
        closing = original.rpar.whitespace_before
    if not isinstance(tail.comma, cst.Comma):
        return changes
    tail_ws = tail.comma.whitespace_after
    if isinstance(tail_ws, cst.ParenthesizedWhitespace) and isinstance(closing, cst.ParenthesizedWhitespace):
        tail_ws = tail_ws.with_changes(indent=closing.indent, last_line=closing.last_line)
        result[-1] = tail.with_changes(comma=tail.comma.with_changes(whitespace_after=tail_ws))
        changes["rpar"] = original.rpar.with_changes(whitespace_before=cst.SimpleWhitespace(""))
    elif isinstance(tail_ws, cst.SimpleWhitespace):
        result[-1] = tail.with_changes(comma=cst.MaybeSentinel.DEFAULT)
    return changes


def _unaliased_import_roots(module: cst.Module) -> set[str]:
    roots: set[str] = set()

    class Collector(cst.CSTVisitor):
        def visit_Import(self, node: cst.Import) -> None:
            for alias in node.names:
                if alias.asname is None:
                    roots.add((get_full_name_for_node(alias.name) or "").split(".", 1)[0])

    module.visit(Collector())
    return roots


# -- driving the pass over a tree -----------------------------------------


def iter_files(root: Path, targets: Sequence[str], suffixes: tuple[str, ...] | None) -> Iterator[tuple[Path, str]]:
    """Yield (absolute path, root-relative posix path) for regular files, sorted, never following symlinks."""

    root = root.resolve()
    starts = [root] if not targets else []
    for target in targets:
        candidate = Path(target)
        candidate = (candidate if candidate.is_absolute() else root / candidate).resolve()
        if candidate != root and root not in candidate.parents:
            raise MapError(f"path {target!r} is outside --root")
        starts.append(candidate)
    seen: set[Path] = set()
    for start in starts:
        walk = [(start.parent, [], [start.name])] if start.is_file() else os.walk(start)
        for directory, dirnames, filenames in walk:
            dirnames[:] = sorted(d for d in dirnames if d not in SKIPPED_DIRS)
            for name in sorted(filenames):
                path = Path(directory) / name
                if path in seen or path.is_symlink() or not path.is_file():
                    continue
                if suffixes is not None and not name.endswith(suffixes):
                    continue
                seen.add(path)
                yield path, path.relative_to(root).as_posix()


def write_atomically(path: Path, data: bytes) -> None:
    mode = path.stat().st_mode
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
        os.chmod(tmp, mode & 0o7777)
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


Result = tuple[bytes, list[Finding], list[Finding], list[Finding]]
# Findings that make the other rewrites in the same file unsafe: the file is left unchanged.
HOLDING_KINDS = frozenset(
    {
        "alias_crosses_owner",
        "ambiguous_binding",
        "bare_package_use",
        "binding_missing",
        "rebound_name",
        "split_not_applied",
    }
)


def rename_source(
    ownership: OwnershipMap, rel_path: str, source: bytes, external_names: frozenset[str] | None = None
) -> Result:
    """Run the codemod over one file's bytes; return (new bytes, rewrites, unresolved, inventory).

    Any exception inside the pass is reported for this file, which is then left unchanged.
    """

    try:
        return _rename_source(ownership, rel_path, source, external_names)
    except Exception as exc:  # one unexpected input must not stop the run or half-write a file
        detail = f"the rename pass failed ({type(exc).__name__}: {exc}); file left unchanged"
        return source, [], [Finding(rel_path, 1, "tool_error", rel_path, detail=detail)], []


def _rename_source(
    ownership: OwnershipMap, rel_path: str, source: bytes, external_names: frozenset[str] | None
) -> Result:
    try:
        tree = cst.parse_module(source)
    except cst.ParserSyntaxError as exc:
        return source, [], [Finding(rel_path, exc.raw_line, "parse_error", rel_path, detail=exc.message)], []
    command = MachineryRenameCommand(CodemodContext(filename=rel_path), ownership, rel_path, external_names)
    new_source = command.transform_module(tree).bytes
    unresolved = list(command.unresolved)
    holds = sorted({f.kind for f in unresolved if f.kind in HOLDING_KINDS})
    if holds and command.rewrites:
        # The rewrites in this file depend on one another through the ``scripts`` binding: apply none of them.
        detail = f"not applied: this file also has {', '.join(holds)}; rename it by hand"
        held = [
            Finding(rel_path, f.line, "held_rewrite", f.before, f.after, detail, MACHINERY) for f in command.rewrites
        ]
        return source, [], [*unresolved, *held], command.inventory
    if new_source != source or command.rewrites:
        # Post-condition: the output parses and is a fixed point. A rewrite that was reported
        # but not placed shows up again on the second pass.
        try:
            second = MachineryRenameCommand(CodemodContext(filename=rel_path), ownership, rel_path, external_names)
            second.transform_module(cst.parse_module(new_source))
        except cst.ParserSyntaxError as exc:
            detail = f"the rewritten file does not parse ({exc.message}); left unchanged"
            return (
                source,
                [],
                [*unresolved, Finding(rel_path, exc.raw_line, "invalid_output", rel_path, detail=detail)],
                command.inventory,
            )
        unresolved.extend(
            Finding(rel_path, f.line, "rewrite_not_applied", f.before, detail="still pending after the rewrite")
            for f in second.rewrites
        )
    return new_source, command.rewrites, unresolved, command.inventory


_WORKER_STATE: tuple[OwnershipMap, frozenset[str] | None] | None = None


def _worker_init(ownership: OwnershipMap, external_names: frozenset[str] | None) -> None:
    global _WORKER_STATE
    _WORKER_STATE = (ownership, external_names)


def _worker(item: tuple[str, bytes]) -> Result:
    assert _WORKER_STATE is not None
    return rename_source(_WORKER_STATE[0], item[0], item[1], _WORKER_STATE[1])


def load_external_names(path: Path | None) -> frozenset[str] | None:
    if path is None:
        return None
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError) as exc:
        raise MapError(f"cannot read --external-names: {exc}") from exc
    # Entries that are not identifiers (extension build artefacts) can never collide with an import.
    return frozenset(name for name in (line.strip() for line in lines) if name.isidentifier())


def run(
    ownership: OwnershipMap,
    root: Path,
    targets: Sequence[str],
    apply: bool,
    jobs: int = 1,
    external_names: frozenset[str] | None = None,
) -> Report:
    report = Report("rename_python", "apply" if apply else "check", ownership.sha256)
    report.notes.extend(f"module/package collision: {note}" for note in ownership.collisions)
    files = list(iter_files(root, targets, (".py",)))
    sources = [(rel, path.read_bytes()) for path, rel in files]
    if jobs > 1 and len(sources) > 1 and "fork" in multiprocessing.get_all_start_methods():
        context = multiprocessing.get_context("fork")
        with ProcessPoolExecutor(
            jobs, mp_context=context, initializer=_worker_init, initargs=(ownership, external_names)
        ) as pool:
            results = list(pool.map(_worker, sources, chunksize=8))
    else:
        results = [rename_source(ownership, rel, source, external_names) for rel, source in sources]
    for (path, rel), (_rel, source), (new_source, rewrites, unresolved, inventory) in zip(
        files, sources, results, strict=True
    ):
        report.files_scanned += 1
        original = ownership.original_path(rel)
        if original.startswith(OLD_ROOT + "/") and original not in ownership.files:
            report.unresolved.append(
                Finding(rel, 1, "map_gap", rel, detail="file is under scripts/ but not in the map")
            )
        report.rewrites.extend(rewrites)
        report.unresolved.extend(unresolved)
        report.inventory.extend(inventory)
        if new_source != source:
            report.files_changed.append(rel)
            if apply:
                write_atomically(path, new_source)
    return report


def emit(report: Report, report_path: Path | None) -> int:
    if report_path is not None:
        report_path.write_text(json.dumps(report.as_dict(), indent=2, sort_keys=False) + "\n", encoding="utf-8")
    report.print_summary()
    return EXIT_UNRESOLVED if report.unresolved else EXIT_OK


def add_common_arguments(parser: argparse.ArgumentParser) -> None:
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--check", action="store_true", help="Report what would change and what is unresolved; write nothing."
    )
    mode.add_argument(
        "--apply",
        action="store_true",
        help="Write every resolved rewrite in place; unresolved references are left as they are.",
    )
    parser.add_argument(
        "--map",
        required=True,
        type=Path,
        metavar="MAP.json",
        help='Ownership map: JSON object of repository-relative file path -> "machinery" or "product", '
        'e.g. {"scripts/dispatch.py": "machinery", "scripts/audit/__init__.py": "product"}. Required.',
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path.cwd(),
        help="Repository root the map's paths are relative to (default: the current directory). "
        "Files already moved to lu_machinery/ are looked up as scripts/.",
    )
    parser.add_argument(
        "--report",
        type=Path,
        metavar="OUT.json",
        help="Also write the full JSON report (every rewrite and unresolved reference) here. Default: none.",
    )
    parser.add_argument(
        "paths",
        nargs="*",
        metavar="PATH",
        help="Files or directories under --root to process (default: the whole root). "
        "Skips .git, virtualenvs, node_modules, caches and symlinks.",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="rename_python.py",
        description=(
            "Rename machinery Python modules from scripts to lu_machinery in import statements, bound names,\n"
            "import_module/run_module/__import__ targets and exact module-name strings, using a file ownership map.\n"
            "Use it on a disposable clone during the machinery move; never on the live product tree. "
            "Non-Python files belong to rename_nonpython.py."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
Examples:
  python packaging/machinery-move/rename_python.py --map ownership.json --root "$CLONE" --check
  python packaging/machinery-move/rename_python.py --map ownership.json --root "$CLONE" --apply --jobs 16 \
      --external-names external-names.txt --report py.json
  python packaging/machinery-move/rename_python.py --map ownership.json --check tests/fixtures/sample.py

Rules:
  A reference is renamed only when the file Python binds for it is machinery in the map; module names come
  from the map's paths (.py and a terminal __init__ stripped; a package beats a same-named module).
  Comments and docstrings are never changed. A mixed `from scripts import a, b` is split by owner.
  A relative import that would cross owners becomes absolute. An unprefixed import (`from lib.x import y`,
  resolved through scripts/ on sys.path) is rewritten only when a mapped product file imports exactly one
  machinery module whose top-level name is not also a standard-library or --external-names module.
  Computed or relative loader targets, ambiguous owners, unknown modules and map gaps are reported.

Outputs:
  stdout: a summary line, rewrite and unresolved counts by kind, then every unresolved reference as
  path:line: kind: text (detail). --apply rewrites files in place (atomic replace, mode kept).
  --report writes the same data as JSON with every rewrite.

Exit codes:
  0  no unresolved references (with --check, rewrites may still be pending: see the summary)
  1  at least one unresolved reference; --apply still wrote every resolved rewrite
  2  usage error, or an unreadable or malformed ownership map

Related:
  packaging/machinery-move/README.md, rename_nonpython.py, machinery move contract v3 step 6 (rename items 1-2).
  Requires libcst==1.8.6 from an isolated, hash-locked environment (see the README).
""",
    )
    add_common_arguments(parser)
    parser.add_argument(
        "--jobs",
        type=int,
        default=1,
        help="Worker processes for the LibCST pass (default: 1). Use the CPU count for a whole repository; "
        "results and their order do not depend on it.",
    )
    parser.add_argument(
        "--external-names",
        type=Path,
        metavar="NAMES.txt",
        help="Top-level module names importable in the project environment, one per line (see the README for "
        "the one-line generator). Needed to rewrite an unprefixed import (`from lib.x import y`) whose target "
        "changes sides; without it such imports are reported. Default: none.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.jobs < 1:
        print("error: --jobs must be at least 1", file=sys.stderr)
        return EXIT_USAGE
    try:
        ownership = OwnershipMap.from_file(args.map)
        external_names = load_external_names(args.external_names)
        report = run(ownership, args.root, args.paths, apply=args.apply, jobs=args.jobs, external_names=external_names)
    except MapError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_USAGE
    return emit(report, args.report)


if __name__ == "__main__":
    sys.exit(main())
