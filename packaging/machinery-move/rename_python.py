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
import os
import re
import sys
import tempfile
from collections.abc import Iterable, Iterator, Mapping, Sequence
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
LOADER_NAMES = frozenset(name.rsplit(".", 1)[1] for name in LOADERS)
MODULE_LITERAL = re.compile(r"scripts(?:\.[A-Za-z_][A-Za-z0-9_]*)+")
# A module name followed by more text, such as ``scripts.api.main:app``.
MODULE_PREFIX = re.compile(r"scripts(?:\.[A-Za-z_][A-Za-z0-9_]*)+")
# The start of a module name completed at run time: ``scripts.x.`` + name, ``scripts.%s``, ``scripts.{}``.
MODULE_HEAD = re.compile(r"scripts(?:\.[A-Za-z_][A-Za-z0-9_]*)*\.?")
STDLIB = frozenset(sys.stdlib_module_names)


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

    def as_dict(self) -> dict[str, object]:
        data: dict[str, object] = {"path": self.path, "line": self.line, "kind": self.kind, "before": self.before}
        if self.after:
            data["after"] = self.after
        if self.detail:
            data["detail"] = self.detail
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
        self.root_names = frozenset(name.split(".")[1] for name in self.modules if name.count(".") >= 1)

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
    if not body:
        return None
    first = body[0]
    if isinstance(first, cst.SimpleStatementLine) and len(first.body) == 1:
        expr = first.body[0]
        if isinstance(expr, cst.Expr) and isinstance(expr.value, (cst.SimpleString, cst.ConcatenatedString)):
            return expr.value
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
        self._import_depth = 0
        self._docstrings: set[int] = set()
        self._skip_strings: set[int] = set()
        self._loader_args: set[int] = set()
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

    def _unresolved(self, node: cst.CSTNode, kind: str, before: str, detail: str) -> None:
        self.unresolved.append(Finding(self.rel_path, self._line(node), kind, before, detail=detail))

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

    def visit_ClassDef(self, node: cst.ClassDef) -> None:
        self._mark_docstring(node.body.body if isinstance(node.body, cst.IndentedBlock) else ())

    def visit_FunctionDef(self, node: cst.FunctionDef) -> None:
        self._mark_docstring(node.body.body if isinstance(node.body, cst.IndentedBlock) else ())

    def _mark_docstring(self, body: Sequence[cst.CSTNode]) -> None:
        doc = _docstring_expr(body)
        if doc is not None:
            self._docstrings.add(id(doc))

    def visit_Import(self, node: cst.Import) -> None:
        self._import_depth += 1

    def visit_ImportFrom(self, node: cst.ImportFrom) -> None:
        self._import_depth += 1

    # -- module strings built from parts ------------------------------

    def visit_ConcatenatedString(self, node: cst.ConcatenatedString) -> None:
        self._visit_string_expression(node)

    def visit_FormattedString(self, node: cst.FormattedString) -> None:
        self._visit_string_expression(node)

    def visit_BinaryOperation(self, node: cst.BinaryOperation) -> None:
        self._visit_string_expression(node)

    def _visit_string_expression(self, node: cst.BaseExpression) -> None:
        """Classify the outermost string expression; its string parts are then skipped."""

        if id(node) in self._skip_strings:
            return
        parts = _string_parts(node)
        if parts is None:
            return
        _mark_parts(node, self._skip_strings)
        if self._import_depth or id(node) in self._docstrings or id(node) in self._loader_args:
            return
        self._classify_string(node, parts, rewritable=False)

    def _classify_string(self, node: cst.CSTNode, parts: list[str | None], rewritable: bool) -> str | None:
        """Decide one string expression; return the new value when a plain literal is to be rewritten.

        ``parts`` are the static texts, with None for each piece only known at run time.
        Strings with whitespace before the first run-time piece are prose or commands and
        belong to rename_nonpython.py, which reports module names inside them.
        """

        static = "".join(itertools.takewhile(lambda part: part is not None, parts))
        computed = None in parts
        if not static.startswith(OLD_ROOT) or re.search(r"\s", static):
            return None
        shown = _code(node)
        if not computed and MODULE_LITERAL.fullmatch(static):
            entry = self.ownership.resolve(static)
            assert entry is not None
            if entry[0].owner == AMBIGUOUS:
                self._unresolved(node, "ambiguous_module", shown, entry[0].note or "no single owner")
            elif entry[0].owner == MACHINERY:
                if rewritable:
                    return renamed(static)
                self._unresolved(node, "assembled_module_string", shown, "a machinery module name split across parts")
            return None
        head = MODULE_HEAD.match(static)
        assert head is not None
        template = static[head.end() : head.end() + 1] in ("%", "{")
        if computed or template:
            if head.end() < len(static) and not template:
                return None  # e.g. ``scriptsfoo`` + name: not a module name
            text = head.group(0)
            # Without a trailing dot the last component may continue at run time.
            base = text[:-1] if text.endswith(".") else text.rsplit(".", 1)[0] if "." in text else OLD_ROOT
            resolved = self.ownership.resolve(base)
            owner = self.ownership.subtree_owner(resolved[0].name) if resolved else None
            if owner != PRODUCT:
                self._unresolved(node, "computed_module_string", shown, "a module name completed at run time")
            return None
        prefix = MODULE_PREFIX.match(static)
        if prefix is not None:
            resolved = self.ownership.resolve(prefix.group(0))
            if resolved is not None and resolved[0].owner != PRODUCT:
                self._unresolved(
                    node, "module_literal_suffix", shown, "a module name followed by other text, e.g. module:attribute"
                )
        return None

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
        if not (isinstance(root, cst.Name) and root.value == OLD_ROOT):
            return updated_node
        qualified = self.get_metadata(QualifiedNameProvider, original_node, set())
        sources = {q.source for q in qualified}
        if not qualified or QualifiedNameSource.IMPORT not in sources:
            return updated_node  # a local variable called scripts
        dotted = get_full_name_for_node(original_node) or ""
        if sources != {QualifiedNameSource.IMPORT}:
            self._unresolved(original_node, "rebound_name", dotted, "scripts is bound by an import and by a local")
            return updated_node
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
        if any(q.source == QualifiedNameSource.IMPORT for q in qualified):
            self._unresolved(
                original_node,
                "bare_package_use",
                _code(parent) if isinstance(parent, cst.CSTNode) else OLD_ROOT,
                "uses the package object bound by `import scripts...`; what it reaches cannot be resolved",
            )
        return updated_node

    # -- pass 2: loader targets and module strings -----------------------

    def visit_Call(self, node: cst.Call) -> None:
        if isinstance(node.func, cst.Attribute) and node.func.attr.value == "format":
            self._visit_string_expression(node)  # ``"scripts.{}".format(name)``
        if not _is_dotted_name(node.func):
            return  # ``__import__("x").attr(...)`` reports the inner call's name for the outer one
        qualified = {q.name for q in self.get_metadata(QualifiedNameProvider, node.func, set())}
        loaders = [name for name in qualified if name in LOADERS]
        if not loaders:
            return
        keyword = LOADERS[loaders[0]]
        shown = _code(node)
        target = None
        starred = False
        for arg in node.args:
            if arg.keyword is not None and arg.keyword.value == keyword:
                target = arg.value
                break
            if arg.keyword is None and arg.star == "" and target is None:
                target = arg.value
                break
            if arg.star:
                starred = True
                if arg.star == "*" and target is None:
                    break
        if target is None:
            if starred:
                self._unresolved(node, "computed_loader", shown, "the loader target comes from unpacked arguments")
            return
        self._loader_args.add(id(target))
        _mark_parts(target, self._skip_strings)
        if not (isinstance(target, cst.SimpleString) and isinstance(target.evaluated_value, str)):
            self._unresolved(node, "computed_loader", shown, "the loader target is computed at run time")
            return
        value = target.evaluated_value
        if value.startswith("."):
            self._unresolved(node, "relative_loader", shown, "a relative loader target depends on its package")
            return
        resolved = self.ownership.resolve(value)
        if resolved is None:
            self._unprefixed_loader(node, target, value, shown)
            return
        entry, rest = resolved
        if rest:
            if self._missing_matters(value):
                self._unresolved(node, "unknown_module", shown, f"the map has no module {value}")
            return
        owner = entry.owner
        main = self.ownership.module(f"{value}.__main__")
        if loaders[0] == "runpy.run_module" and main is not None and main.owner != owner:
            owner = AMBIGUOUS  # run_module runs the package's __main__
        has_fromlist = any(a.keyword is not None and a.keyword.value == "fromlist" for a in node.args) or (
            len(node.args) > 3 and node.args[3].keyword is None
        )
        if loaders[0].endswith("__import__") and has_fromlist and self.ownership.subtree_owner(value) == AMBIGUOUS:
            owner = AMBIGUOUS  # the fromlist may name submodules of either owner
        if owner == AMBIGUOUS:
            self._unresolved(node, "ambiguous_module", shown, f"{value} has more than one owner for this loader")
        elif owner == MACHINERY:
            self._loader_rewrites[id(target)] = renamed(value)

    def _unprefixed_loader(self, node: cst.Call, target: cst.SimpleString, value: str, shown: str) -> None:
        verdict, candidate, detail = self._unprefixed_decision(value, None)
        if verdict == "rewrite":
            self._loader_rewrites[id(target)] = renamed(candidate)
        elif verdict not in ("external", "keep"):
            self._unresolved(node, verdict, shown, detail)

    def leave_SimpleString(self, original_node: cst.SimpleString, updated_node: cst.SimpleString) -> cst.SimpleString:
        if id(original_node) in self._loader_rewrites:
            new_value = self._loader_rewrites[id(original_node)]
            self._rewrite(original_node, "loader", str(original_node.evaluated_value), new_value)
            return _with_string_value(original_node, updated_node, new_value)
        skipped = (self._docstrings, self._skip_strings, self._loader_args)
        if self._import_depth or any(id(original_node) in ids for ids in skipped):
            return updated_node
        value = original_node.evaluated_value
        if isinstance(value, bytes):
            text = value.decode("ascii", "replace")
            resolved = self.ownership.resolve(text) if MODULE_LITERAL.fullmatch(text) else None
            if resolved is not None and resolved[0].owner != PRODUCT:
                self._unresolved(original_node, "bytes_module_string", text, "a module name in a bytes literal")
            return updated_node
        new_value = self._classify_string(original_node, [value], rewritable=True)
        if new_value is None:
            return updated_node
        self._rewrite(original_node, "module_literal", value, new_value)
        return _with_string_value(original_node, updated_node, new_value)

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


def _string_parts(node: cst.CSTNode) -> list[str | None] | None:
    """Static text pieces of a string expression, None for each run-time piece; None if not a string."""

    if isinstance(node, cst.SimpleString):
        value = node.evaluated_value
        return [value] if isinstance(value, str) else None
    if isinstance(node, cst.ConcatenatedString):
        left, right = _string_parts(node.left), _string_parts(node.right)
        return None if left is None or right is None else left + right
    if isinstance(node, cst.FormattedString):
        parts: list[str | None] = []
        for part in node.parts:
            if isinstance(part, cst.FormattedStringText):
                parts.append(part.value.replace("{{", "{").replace("}}", "}"))
            else:
                parts.append(None)
        return parts
    if isinstance(node, cst.BinaryOperation):
        left, right = _string_parts(node.left), _string_parts(node.right)
        if isinstance(node.operator, cst.Add) and (left is not None or right is not None):
            return (left if left is not None else [None]) + (right if right is not None else [None])
        if isinstance(node.operator, cst.Modulo) and left is not None:
            return [*left, None]  # ``"scripts.%s" % name``
    if isinstance(node, cst.Call) and isinstance(node.func, cst.Attribute) and node.func.attr.value == "format":
        receiver = _string_parts(node.func.value)
        return None if receiver is None else [*receiver, None]
    return None


def _mark_parts(node: cst.CSTNode, ids: set[int]) -> None:
    """Record a string expression and its string pieces (not the run-time expressions inside them)."""

    ids.add(id(node))
    if isinstance(node, cst.Call) and isinstance(node.func, cst.Attribute) and node.func.attr.value == "format":
        _mark_parts(node.func.value, ids)
    elif isinstance(node, cst.ConcatenatedString):
        _mark_parts(node.left, ids)
        _mark_parts(node.right, ids)
    elif isinstance(node, cst.BinaryOperation) and _string_parts(node) is not None:
        for side in (node.left, node.right):
            if _string_parts(side) is not None:
                _mark_parts(side, ids)


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


def needs_codemod(ownership: OwnershipMap, source: bytes) -> bool:
    """Cheap, conservative stdlib pre-check: False only when the LibCST pass cannot act on the file.

    LibCST metadata resolution costs about a second per thousand lines, so files whose
    imports, names, strings and calls cannot touch a non-product ``scripts`` module skip it.
    """

    try:
        tree = ast.parse(source)
    except (SyntaxError, ValueError):
        return True  # let LibCST report the parse error

    def touches(dotted: str) -> bool:
        top = dotted.split(".", 1)[0]
        if top == OLD_ROOT:
            return ownership.subtree_owner(dotted) != PRODUCT
        return top in ownership.root_names

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            if any(touches(alias.name) for alias in node.names):
                return True
        elif isinstance(node, ast.ImportFrom):
            if node.level or touches(node.module or ""):
                return True
            if any(alias.name in LOADER_NAMES for alias in node.names):
                return True
        elif isinstance(node, ast.Name):
            if node.id == OLD_ROOT or node.id in LOADER_NAMES:
                return True
        elif isinstance(node, ast.Attribute):
            if node.attr in LOADER_NAMES:
                return True
        elif isinstance(node, ast.Constant) and isinstance(node.value, (str, bytes)):
            value = node.value.decode("ascii", "replace") if isinstance(node.value, bytes) else node.value
            # Any string that starts a module name: whole, assembled from parts, or a template.
            if value.startswith(OLD_ROOT) and value[len(OLD_ROOT) : len(OLD_ROOT) + 1] in ("", ".", "{", "%"):
                return True
    return False


def rename_source(
    ownership: OwnershipMap, rel_path: str, source: bytes, external_names: frozenset[str] | None = None
) -> tuple[bytes, list[Finding], list[Finding]]:
    """Run the codemod over one file's bytes; return (new bytes, rewrites, unresolved)."""

    if not needs_codemod(ownership, source):
        return source, [], []
    try:
        tree = cst.parse_module(source)
    except cst.ParserSyntaxError as exc:
        return source, [], [Finding(rel_path, exc.raw_line, "parse_error", rel_path, detail=exc.message)]
    command = MachineryRenameCommand(CodemodContext(filename=rel_path), ownership, rel_path, external_names)
    new_source = command.transform_module(tree).bytes
    unresolved = list(command.unresolved)
    if new_source != source or command.rewrites:
        # Post-condition: the output parses and is a fixed point. A rewrite that was reported
        # but not placed shows up again on the second pass.
        try:
            second = MachineryRenameCommand(CodemodContext(filename=rel_path), ownership, rel_path, external_names)
            second.transform_module(cst.parse_module(new_source))
        except cst.ParserSyntaxError as exc:
            detail = f"the rewritten file does not parse ({exc.message}); left unchanged"
            return source, [], [*unresolved, Finding(rel_path, exc.raw_line, "invalid_output", rel_path, detail=detail)]
        unresolved.extend(
            Finding(rel_path, f.line, "rewrite_not_applied", f.before, detail="still pending after the rewrite")
            for f in second.rewrites
        )
    return new_source, command.rewrites, unresolved


_WORKER_STATE: tuple[OwnershipMap, frozenset[str] | None] | None = None


def _worker_init(ownership: OwnershipMap, external_names: frozenset[str] | None) -> None:
    global _WORKER_STATE
    _WORKER_STATE = (ownership, external_names)


def _worker(item: tuple[str, bytes]) -> tuple[bytes, list[Finding], list[Finding]]:
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
    for (path, rel), (_rel, source), (new_source, rewrites, unresolved) in zip(files, sources, results, strict=True):
        report.files_scanned += 1
        original = ownership.original_path(rel)
        if original.startswith(OLD_ROOT + "/") and original not in ownership.files:
            report.unresolved.append(
                Finding(rel, 1, "map_gap", rel, detail="file is under scripts/ but not in the map")
            )
        report.rewrites.extend(rewrites)
        report.unresolved.extend(unresolved)
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
