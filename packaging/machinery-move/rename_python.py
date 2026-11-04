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
MODULE_LITERAL = re.compile(r"scripts(?:\.[A-Za-z_][A-Za-z0-9_]*)+")
# A module name followed by more text, such as ``scripts.api.main:app``.
MODULE_PREFIX = re.compile(r"scripts(?:\.[A-Za-z_][A-Za-z0-9_]*)+")
# The start of a module name completed at run time: ``scripts.x.`` + name, ``scripts.%s``, ``scripts.{}``.
MODULE_HEAD = re.compile(r"scripts(?:\.[A-Za-z_][A-Za-z0-9_]*)*\.?")
# A string that begins with the package name (not a ``scripts/`` path or a longer word).
MODULE_START = re.compile(r"scripts(?![A-Za-z0-9_/\\\-])")
# A module name anywhere in a built string: ``scripts`` then dotted parts, or ``scripts`` at the end.
MODULE_ANYWHERE = re.compile(r"(?<![A-Za-z0-9_/\\.\-])scripts(?:\.[A-Za-z_][A-Za-z0-9_]*)*\.?(?![A-Za-z0-9_/\\\-])")
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

    def visit_Subscript(self, node: cst.Subscript) -> None:
        self._visit_string_expression(node)  # ``"scripts.dispatchX"[:-1]``

    def _visit_string_expression(self, node: cst.BaseExpression) -> None:
        """Classify the outermost string expression; every string inside it is then skipped."""

        if id(node) in self._skip_strings:
            return
        evaluator = Evaluator()
        expr = cst_expr(node)
        value = evaluator.value(expr)
        if not is_string(value):
            return
        self._skip_strings.update(id(member.origin) for member in evaluator.structure(expr))
        if self._import_depth or id(node) in self._docstrings or id(node) in self._loader_args:
            return
        if evaluator.failures:
            self._unresolved(
                node,
                "unevaluable_string",
                _code(node),
                f"evaluating this string failed ({evaluator.failures[0]}); it may build a module name",
            )
            return
        if evaluator.transformed:
            # A run-time pattern, template or bound may turn any literal into another name.
            loose = next((t for t in evaluator.literal_texts(expr) if LOOSE_MODULE.search(t)), None)
            if loose is not None:
                detail = f"a string containing {LOOSE_MODULE.search(loose).group(0)}… is reshaped at run time"  # type: ignore[union-attr]
                self._unresolved(node, "computed_module_string", _code(node), detail)
                return
        parts = text_parts(value)  # type: ignore[arg-type]
        self._classify_string(node, parts, rewritable=False, pieces=evaluator.search_texts(expr))

    def _classify_string(
        self, node: cst.CSTNode, parts: list[str | None], rewritable: bool, pieces: Sequence[tuple[str, bool]] = ()
    ) -> str | None:
        """Decide one string expression; return the new value when a plain literal is to be rewritten.

        ``parts`` is the value in order, with None for each piece only known at run time; ``pieces``
        are the texts to search when the value is not fully known (``Evaluator.search_texts``).
        A plain literal is ``rewritable``. A plain literal with whitespace before its first
        run-time piece is prose or a command, and rename_nonpython.py reports module names in it.
        A built string (``rewritable`` false) is always decided here, wherever the name sits.
        """

        static = "".join(itertools.takewhile(lambda part: part is not None, parts))
        computed = None in parts
        shown = _code(node)
        if rewritable and re.search(r"\s", static):
            return None
        leading = bool(MODULE_START.match(static)) and not re.search(r"\s", static)
        if leading:
            reported = len(self.unresolved)
            new_value = self._classify_leading_name(node, static, computed, rewritable, shown)
            if rewritable or len(self.unresolved) > reported:
                return new_value
        if rewritable:
            return None
        # A built string: look for a module name anywhere in its value, or, when the value is only
        # known at run time, in the texts that may hold one (``Evaluator.search_texts``).
        texts = list(pieces) if computed else [(static, False)]
        matches = [(i, text, more, m) for i, (text, more) in enumerate(texts) for m in MODULE_ANYWHERE.finditer(text)]
        for index, text, more, match in matches:
            if leading and index == 0 and match.start() == 0:
                continue  # already judged as the leading name (the first known run)
            name = match.group(0).rstrip(".")
            continues = more and match.end() == len(text)  # run-time text may extend the name
            if name == OLD_ROOT and not (match.group(0).endswith(".") or continues):
                continue  # the word "scripts" in prose
            resolved = self.ownership.resolve(name)
            if continues or match.group(0).endswith(".") or name == OLD_ROOT:
                owner = self.ownership.subtree_owner(resolved[0].name) if resolved else AMBIGUOUS
            else:
                owner = resolved[0].owner if resolved else AMBIGUOUS
            if owner != PRODUCT:
                kind = "computed_module_string" if computed else "assembled_module_string"
                self._unresolved(
                    node, kind, shown, f"a module name ({match.group(0)}) inside a string built from parts"
                )
                break
        return None

    def _classify_leading_name(
        self, node: cst.CSTNode, static: str, computed: bool, rewritable: bool, shown: str
    ) -> str | None:
        """A string whose value starts with the package name."""

        if not computed and MODULE_LITERAL.fullmatch(static):
            entry = self.ownership.resolve(static)
            assert entry is not None
            if entry[0].owner == AMBIGUOUS:
                self._unresolved(node, "ambiguous_module", shown, entry[0].note or "no single owner")
            elif entry[0].owner == MACHINERY:
                if rewritable:
                    return renamed(static)
                self._unresolved(node, "assembled_module_string", shown, "a machinery module name built from parts")
            return None
        head = MODULE_HEAD.match(static)
        assert head is not None
        text, after = head.group(0), static[head.end() : head.end() + 1]
        if after in ("", "%", "{"):
            if not computed and after == "" and not text.endswith("."):
                return None  # just ``scripts``: a word, not a module name
            # Completed at run time, or a prefix completed elsewhere (``"scripts.x."``): a trailing dot
            # fixes the parent; otherwise the last part may continue.
            base = text[:-1] if text.endswith(".") else text.rsplit(".", 1)[0] if "." in text else OLD_ROOT
            resolved = self.ownership.resolve(base)
            owner = self.ownership.subtree_owner(resolved[0].name) if resolved else None
            kind, detail = "computed_module_string", "a module name completed at run time"
            if base == OLD_ROOT and not computed:
                kind, detail = "package_name_literal", "the package name used to build or test module names"
        else:
            # A separator follows (``module:attribute``): the module part is fixed.
            resolved = self.ownership.resolve(text.rstrip("."))
            owner = resolved[0].owner if resolved and resolved[0].name != OLD_ROOT else AMBIGUOUS
            kind, detail = "module_literal_suffix", "a module name followed by other text, e.g. module:attribute"
            if text.rstrip(".") == OLD_ROOT:
                kind, detail = "package_name_literal", "the package name inside a pattern or text"
        if owner != PRODUCT:
            self._unresolved(node, kind, shown, detail)
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
            _mark_parts(arg.value, self._skip_strings)
            self._loader_args.add(id(arg.value))

    def visit_Call(self, node: cst.Call) -> None:
        if isinstance(node.func, cst.Attribute) and (
            node.func.attr.value in STR_METHODS or _cst_stringish(node.func.value)
        ):
            self._visit_string_expression(node)  # ``"scripts.{}".format(name)``, ``".".join([...])``
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
        _mark_parts(target, self._skip_strings)
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
        skipped = (self._docstrings, self._skip_strings, self._loader_args)
        if self._import_depth or any(id(original_node) in ids for ids in skipped):
            return updated_node
        value = _literal_text(original_node)
        new_value = self._classify_string(original_node, [value], rewritable=True, pieces=[value])
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


# -- strings built from parts: one evaluator for both tools ----------------

# str and bytes methods that return a new string, or a list of strings, from their receiver and arguments alone.
STR_METHODS = frozenset(
    {
        "capitalize",
        "casefold",
        "center",
        "decode",
        "encode",
        "expandtabs",
        "format",
        "format_map",
        "join",
        "ljust",
        "lower",
        "lstrip",
        "removeprefix",
        "removesuffix",
        "replace",
        "partition",
        "rjust",
        "rpartition",
        "rsplit",
        "rstrip",
        "split",
        "splitlines",
        "strip",
        "swapcase",
        "title",
        "translate",
        "upper",
        "zfill",
    }
)
# A module name or its start anywhere in a literal, in any case: used when a run-time value may reshape it.
LOOSE_MODULE = re.compile(r"scripts\.", re.IGNORECASE)
# Larger counts or widths could build a huge string; such a value is left to run time.
MAX_EVAL_INT = 10_000
WIDE_FORMAT = re.compile(r"\d{5,}")
# Stand-ins for run-time pieces while a partly known string is evaluated (see Evaluator._apply).
SENTINEL = re.compile("\x00\\d+\x01*\x00")
CONVERSIONS = {None: lambda value: value, "s": str, "r": repr, "a": ascii}
# One ``%`` conversion: ``%(key)-10.3s``.
PERCENT_FIELD = re.compile(
    r"%(?:\((?P<key>[^)]*)\))?(?P<flags>[#0\- +]*)(?P<width>\*|\d+)?(?P<precision>\.(?:\*|\d+))?[hlL]?(?P<type>.)", re.S
)
# str and bytes methods that return no string (their literals cannot reach a module name).
STR_PREDICATES = frozenset(
    {"count", "endswith", "find", "hex", "index", "rfind", "rindex", "startswith"}
    | {name for name in dir(str) if name.startswith("is")}
    | {"__contains__", "__eq__", "__ge__", "__gt__", "__hash__", "__le__", "__len__", "__lt__", "__ne__", "__sizeof__"}
)
# Pure builtins over literals.
BUILTINS = {
    "ascii": ascii,
    "chr": chr,
    "format": format,
    "list": list,
    "repr": repr,
    "reversed": lambda value: list(reversed(value)),
    "sorted": sorted,
    "str": str,
    "tuple": tuple,
}


@dataclass(eq=False)
class Expr:
    """A string-building expression in a tree-neutral form, built from LibCST (``cst_expr``) or ast (``ast_expr``).

    ``kind`` is lit, fstr, field, add, mod, mul, call, builtin, index, choice, same, seq, map or unknown; ``origin`` is the
    source node. ``index`` is a subscript (receiver, then the index or the slice bounds); ``choice`` is one of
    its operands (``a if c else b``, ``a or b``).
    ``items`` are the operands in source order (for a call: the receiver, then the arguments; for a map:
    key, value, key, value). ``data`` is a literal's value, an f-string field's conversion, a call's
    (method, how each argument is passed: "", "*", "**" or "=name") or a container's (type, has unpacking).
    """

    kind: str
    origin: object
    items: tuple[Expr, ...] = ()
    data: object = None


@dataclass(frozen=True)
class Static:
    """A value known before run time."""

    value: object


@dataclass(frozen=True)
class Partial:
    """A string with pieces known only at run time, each shown as None."""

    parts: tuple[str | bytes | None, ...]


@dataclass(frozen=True)
class Container:
    """A literal list, tuple, set or dict with some run-time values (dict: key, value, key, value)."""

    kind: str
    values: tuple[object, ...]


UNKNOWN_STRING = Partial((None,))


def is_string(value: object) -> bool:
    return isinstance(value, Partial) or (isinstance(value, Static) and isinstance(value.value, (str, bytes)))


def text_parts(value: Static | Partial) -> list[str | None]:
    """A string value in order, bytes read as Latin-1 so a module name in them is visible."""

    raw = value.parts if isinstance(value, Partial) else (value.value,)
    return [part.decode("latin-1") if isinstance(part, bytes) else part for part in raw]


def _pieces_of(value: object) -> tuple[str | bytes | None, ...]:
    if isinstance(value, Partial):
        return value.parts
    if is_string(value):
        return (value.value,)  # type: ignore[union-attr]
    return (None,)


def _joined(pieces: Iterable[str | bytes | None]) -> Static | Partial:
    """Merge neighbouring known pieces (and neighbouring unknown ones); a fully known string is Static."""

    merged: list[str | bytes | None] = []
    for piece in pieces:
        if piece == "" or piece == b"":
            continue
        last = merged[-1] if merged else ""
        if merged and piece is None and last is None:
            continue
        if merged and piece is not None and last is not None and type(piece) is type(last):
            merged[-1] = last + piece  # type: ignore[operator]
        else:
            merged.append(piece)
    if not merged:
        return Static("")
    if None not in merged and len(merged) == 1:
        return Static(merged[0])
    return Partial(tuple(merged))


def _container(kind: str, values: Sequence[object]) -> object:
    if kind == "dict":
        return dict(zip(values[0::2], values[1::2], strict=True))
    return {"list": list, "tuple": tuple, "set": set}[kind](values)


class _Opaque(Exception):
    """A run-time piece that cannot be stood in for (inside bytes)."""


def _stand_in(value: object, counter: Iterator[int], width: int) -> object:
    """A concrete object for one input, with a sentinel for each run-time piece."""

    if isinstance(value, Static):
        return value.value
    if value is None:
        return f"\x00{next(counter)}{chr(1) * width}\x00"
    if isinstance(value, Partial):
        if any(isinstance(part, bytes) for part in value.parts):
            raise _Opaque
        return "".join(part if part is not None else str(_stand_in(None, counter, width)) for part in value.parts)
    assert isinstance(value, Container)
    return _container(value.kind, [_stand_in(v, counter, width) for v in value.values])


def _split_stand_ins(text: str) -> list[str | None] | None:
    """Known text and run-time pieces of a result; None when a sentinel was cut or reshaped."""

    parts: list[str | None] = []
    position = 0
    for match in SENTINEL.finditer(text):
        parts.extend((text[position : match.start()], None))
        position = match.end()
    parts.append(text[position:])
    if any(part is not None and ("\x00" in part or "\x01" in part) for part in parts):
        return None
    return [part for part in parts if part != ""]


class Evaluator:
    """Evaluate a string expression as Python would; a piece only known at run time stays unknown.

    Literals, ``+``, ``%``, ``*``, f-strings, containers, subscripts, ``str()``, choices and the
    methods in ``STR_METHODS`` are evaluated. Anything else (names, other calls, attributes) is a
    run-time piece. An operation on known values that raises is recorded in ``failures``; the
    caller reports it.

    A run-time piece is stood in for by a sentinel only where the operation inserts it as content
    (concatenation, a format or ``%`` value, a join element or separator, a ``replace``
    replacement, the receiver of a per-character case change or of padding). There the result
    depends on the piece only through its position and length, which two runs with sentinels of
    two lengths check. Every other input controls the operation; a run-time control input makes
    the value unknown and sets ``transformed``.
    """

    def __init__(self) -> None:
        self.failures: list[str] = []
        # Set when a known piece was given up (an operation the sentinels could not follow): the
        # literals are still in the value, but where they sit is not known.
        self.lossy = False
        # Set when a run-time value controls an operation (a ``replace`` pattern, ``strip`` characters,
        # a template, a slice bound), or when the sentinels could not follow one (a run-time width or
        # precision, a type only known at run time): the literals themselves may be changed.
        self.transformed = False
        self._memo: dict[int, object] = {}

    def value(self, expr: Expr) -> object:
        """Static, Partial, Container, or None (a run-time value not known to be a string)."""

        key = id(expr)
        if key not in self._memo:
            try:
                self._memo[key] = self._value(expr)
            except Exception as exc:  # never a silent pass: the caller reports the failure
                self.failures.append(f"{type(exc).__name__}: {exc}")
                self._memo[key] = UNKNOWN_STRING
        return self._memo[key]

    def _value(self, expr: Expr) -> object:
        kind, items = expr.kind, expr.items
        if kind == "lit":
            return Static(expr.data)
        if kind in ("seq", "map"):
            container_kind, unpacked = expr.data  # type: ignore[misc]
            if unpacked:
                self.lossy = True
                return None
            values = [self.value(item) for item in items]
            if all(isinstance(v, Static) for v in values):
                return Static(_container(container_kind, [v.value for v in values]))  # type: ignore[union-attr]
            return Container(container_kind, tuple(values))
        if kind == "fstr":
            return _joined(piece for item in items for piece in _pieces_of(self.value(item)))
        if kind == "field":
            spec = self.value(items[1]) if len(items) > 1 else Static("")
            return self._field(self.value(items[0]), expr.data, spec)  # type: ignore[arg-type]
        if kind in ("add", "mul"):
            left, right = self.value(items[0]), self.value(items[1])
            if isinstance(left, Static) and isinstance(right, Static):
                return self._apply(operator.add if kind == "add" else operator.mul, [left, right])
            if not (is_string(left) or is_string(right)):
                return None
            if kind == "mul":
                self.lossy = True
                return UNKNOWN_STRING
            return _joined([*_pieces_of(left), *_pieces_of(right)])
        if kind == "mod":
            template = self.value(items[0])
            if not is_string(template):
                return None  # arithmetic
            values = self.value(items[1])
            if isinstance(template, Static) and isinstance(values, Static):
                return self._apply(operator.mod, [template, values], template=0)
            return self._percent(template, values)
        if kind == "call":
            method, passing = expr.data  # type: ignore[misc]
            receiver = self.value(items[0])
            if not is_string(receiver):
                return None
            arguments = [self.value(item) for item in items[1:]]
            if method not in STR_METHODS:
                if method in STR_PREDICATES:
                    return None  # a number or a truth value, not a string
                self.lossy = self.transformed = True  # a method the evaluator does not follow
                return UNKNOWN_STRING
            if method in ("format", "format_map") and not all(isinstance(v, Static) for v in [receiver, *arguments]):
                return self._format(receiver, method, passing, arguments)
            if method == "join" and passing == ("",) and arguments[0] is None:
                # Run-time elements: the result is run-time content; the separator literal is kept inside it.
                self.lossy = True
                return UNKNOWN_STRING

            def call(target: object, *args: object) -> object:
                positional: list[object] = []
                keywords: dict[str, object] = {}
                for how, arg in zip(passing, args, strict=True):
                    if how == "*":
                        positional.extend(arg)  # type: ignore[call-overload]
                    elif how == "**":
                        keywords.update(arg)  # type: ignore[call-overload]
                    elif how:
                        keywords[how[1:]] = arg
                    else:
                        positional.append(arg)
                return getattr(target, method)(*positional, **keywords)

            call.method = method  # type: ignore[attr-defined]
            template = 0 if method.startswith("format") else None
            return self._apply(call, [receiver, *arguments], template=template, control=_controls(method, passing))
        if kind == "index":
            receiver = self.value(items[0])
            bounds = [self.value(item) for item in items[1:]]
            if isinstance(receiver, Static) and not is_string(receiver):
                # ``"a.b".split(".")[0]``: a known list or tuple, indexed by known values.
                if not all(isinstance(b, Static) for b in bounds) or not isinstance(receiver.value, (list, tuple)):
                    return None
                key = bounds[0].value if expr.data is None else slice(*(b.value for b in bounds))  # type: ignore[union-attr]
                try:
                    return Static(receiver.value[key])  # type: ignore[index]
                except Exception:
                    return None
            if not is_string(receiver):
                return None

            def index(target: object, *values: object) -> object:
                key = values[0] if expr.data is None else slice(*values)
                return target[key]  # type: ignore[index]

            return self._apply(index, [receiver, *bounds], control=set(range(1, len(items))))
        if kind == "choice":
            options = [self.value(item) for item in items]
            if not any(is_string(option) for option in options):
                return None
            if all(isinstance(o, Static) for o in options) and len({repr(o.value) for o in options}) == 1:  # type: ignore[union-attr]
                return options[0]
            self.lossy = True  # one of several values: each literal is kept, but which one is not known
            return UNKNOWN_STRING
        if kind == "builtin":
            values = [self.value(item) for item in items]
            if all(isinstance(v, Static) for v in values):
                function = BUILTINS[expr.data]  # type: ignore[index]
                return self._apply(lambda *args: function(*args), values, control=set(range(len(values))))
            name = expr.data
            if name == "str" and len(values) == 1 and is_string(values[0]):
                return values[0]
            if (
                name in ("list", "tuple", "sorted", "reversed")
                and len(values) == 1
                and isinstance(values[0], Container)
            ):
                # Whole elements, reordered at most: each literal is kept as it is.
                elements = values[0].values if values[0].kind != "dict" else values[0].values[0::2]
                if name == "sorted":
                    self.lossy = True  # the order depends on run-time values
                kind_name = "tuple" if name == "tuple" else "list"
                return Container(kind_name, tuple(reversed(elements)) if name == "reversed" else tuple(elements))
            if name in ("repr", "ascii") and len(values) == 1 and is_string(values[0]):
                self.lossy = True  # quoted: the literals are kept, their positions move
                return UNKNOWN_STRING
            if any(is_string(v) or isinstance(v, Container) for v in values):
                self.lossy = self.transformed = True  # literals re-encoded or cut at run time
                return UNKNOWN_STRING
            return UNKNOWN_STRING if name in ("str", "repr", "ascii", "format", "chr") else None
        if kind == "same":
            return self.value(items[0])
        return None

    def _field(self, value: object, conversion: str | None, spec: object) -> object:
        """One replacement field. Run-time content stays one unknown piece: formatting it cannot
        change the text around it. A value holding literals passes through only unformatted."""

        if isinstance(value, Static) and isinstance(spec, Static):
            return self._apply(lambda v, s: format(CONVERSIONS[conversion](v), s), [value, spec], template=1)
        if not _holds_literals(value):
            return UNKNOWN_STRING
        if conversion in (None, "s") and spec == Static("") and is_string(value):
            return value
        self.lossy = self.transformed = True  # a width, precision or conversion may cut or reshape the literals
        return UNKNOWN_STRING

    def _format(self, template: object, method: str, passing: Sequence[str], arguments: list[object]) -> object:
        """``str.format`` and ``format_map`` with some run-time values, one field at a time."""

        if not (isinstance(template, Static) and isinstance(template.value, str)):
            self.lossy = self.transformed = True  # a run-time template
            return UNKNOWN_STRING
        positional: list[object] = []
        keywords: dict[str, object] = {}
        opaque = False  # unpacked run-time arguments: which value a field gets is not known
        pairs = (
            [("**", arguments[0])]
            if method == "format_map" and arguments
            else list(zip(passing, arguments, strict=True))
        )
        for how, argument in pairs:
            if how in ("*", "**"):
                entries = _entries(argument, mapping=how == "**")
                if entries is None:
                    opaque = True
                elif how == "*":
                    positional.extend(entries)  # type: ignore[arg-type]
                else:
                    keywords.update(entries)  # type: ignore[arg-type]
            elif how:
                keywords[how[1:]] = argument
            else:
                positional.append(argument)
        pieces: list[str | bytes | None] = []
        auto = 0
        try:
            fields = list(string.Formatter().parse(template.value))
        except ValueError as exc:
            self.failures.append(f"ValueError: {exc}")
            return UNKNOWN_STRING
        for literal, name, spec, conversion in fields:
            pieces.append(literal)
            if name is None:
                continue
            first = re.match(r"[^.\[]*", name).group(0)  # type: ignore[union-attr]
            key: int | str = auto if first == "" else int(first) if first.isdigit() else first
            auto += first == ""
            missing = (key >= len(positional)) if isinstance(key, int) else key not in keywords
            value = None if missing else positional[key] if isinstance(key, int) else keywords[key]
            if missing and not opaque:
                self.failures.append(f"{'IndexError' if isinstance(key, int) else 'KeyError'}: {key!r}")
                return UNKNOWN_STRING
            spec_value: object = Static(spec) if "{" not in spec else None  # a nested field: a run-time spec
            access = name[len(first) :]
            if access:
                # ``{0.attr}``, ``{0[key]}``: only a known value is looked into.
                if isinstance(value, Static) and isinstance(spec_value, Static):
                    mini = "{0" + access + (f"!{conversion}" if conversion else "") + ":" + str(spec_value.value) + "}"
                    pieces.extend(_pieces_of(self._apply(lambda v, t=mini: t.format(v), [value])))
                elif value is None or not (is_string(value) or isinstance(value, Container)):
                    pieces.append(None)
                else:
                    self.lossy = self.transformed = True
                    pieces.append(None)
                continue
            pieces.extend(_pieces_of(self._field(value, conversion, spec_value)))
        return _joined(pieces)

    def _percent(self, template: object, values: object) -> object:
        """``template % values`` with some run-time values, one conversion at a time."""

        if not (isinstance(template, Static) and isinstance(template.value, str)):
            self.lossy = self.transformed = True  # a run-time template (or bytes)
            return UNKNOWN_STRING
        text = template.value
        positional: list[object] | None = None  # None: the run-time shape decides which value a field gets
        mapping: dict[object, object] | None = None
        if isinstance(values, Static):
            positional = [Static(v) for v in values.value] if isinstance(values.value, tuple) else [values]
            if isinstance(values.value, dict):
                mapping = {k: Static(v) for k, v in values.value.items()}
        elif isinstance(values, Container):
            positional = list(values.values) if values.kind == "tuple" else [values]
            if values.kind == "dict":
                mapping = _entries(values, mapping=True)  # type: ignore[assignment]
        elif isinstance(values, Partial):
            positional = [values]  # one string
        pieces: list[str | bytes | None] = []
        position = index = 0
        for match in PERCENT_FIELD.finditer(text):
            pieces.append(text[position : match.start()])
            position = match.end()
            if match.group("type") == "%":
                pieces.append("%")
                continue
            conversion = "%" + "".join(match.group(g) or "" for g in ("flags", "width", "precision", "type"))
            if match.group("key") is not None:
                value = mapping.get(match.group("key")) if mapping is not None else None
            elif positional is not None and "*" not in conversion:
                value = positional[index] if index < len(positional) else None
                index += 1
            else:
                value, positional = None, None  # run-time shape (or a ``*`` width): later fields are unknown too
            if isinstance(value, Static):
                pieces.extend(_pieces_of(self._apply(lambda v, c=conversion: c % (v,), [value])))
            elif value is None:
                pieces.append(None)
            elif conversion == "%s" and is_string(value):
                pieces.extend(_pieces_of(value))
            else:
                self.lossy = self.transformed = True
                pieces.append(None)
        pieces.append(text[position:])
        return _joined(pieces)

    def _apply(
        self, function: object, inputs: list[object], template: int | None = None, control: Iterable[int] = ()
    ) -> object:
        """Run one operation; with run-time inputs, run it on sentinels and keep what is known for certain.

        ``control`` lists the inputs that steer the operation rather than being inserted into its result.
        """

        shown = [text_parts(v) for v in inputs if is_string(v)]  # type: ignore[arg-type]
        big = [v for v in inputs if isinstance(v, Static) and type(v.value) is int and abs(v.value) > MAX_EVAL_INT]
        if not shown:
            # No string goes in (``2 * 3``, ``[a] + [b]``): not a string being built.
            if big or not all(isinstance(v, Static) for v in inputs):
                return None
            try:
                return Static(function(*(v.value for v in inputs)))  # type: ignore[operator, union-attr]
            except Exception:
                return None
        if template is not None and is_string(inputs[template]):
            fixed = "".join(p for p in text_parts(inputs[template]) if p is not None)  # type: ignore[arg-type]
            if WIDE_FORMAT.search(fixed):
                self.lossy = self.transformed = True
                return UNKNOWN_STRING
        if big or sum(len(p or "") for parts in shown for p in parts) > 1_000_000:
            self.lossy = self.transformed = True
            return UNKNOWN_STRING
        if all(isinstance(v, Static) for v in inputs):
            try:
                return Static(function(*(v.value for v in inputs)))  # type: ignore[operator, union-attr]
            except Exception as exc:
                self.failures.append(f"{type(exc).__name__}: {exc}")
                return UNKNOWN_STRING
        if control and _one_character_pattern(function, inputs):
            control = set(control) - {0}  # a one-character pattern cannot match across a run-time piece
        if any(not isinstance(inputs[i], Static) for i in control if i < len(inputs)):
            # Two sentinels that agree prove nothing about a run-time pattern, template or bound.
            self.lossy = self.transformed = True
            return UNKNOWN_STRING
        # Run it twice with sentinels of two lengths: text that moves with a run-time piece's length
        # (padding, truncation) differs between the runs and is not taken as known.
        results = []
        for width in (0, 3):
            counter = itertools.count()
            try:
                result = function(*(_stand_in(v, counter, width) for v in inputs))  # type: ignore[operator]
            except Exception:  # e.g. ``%d`` given a run-time piece: its type is not known here
                self.lossy = self.transformed = True
                return UNKNOWN_STRING
            if not isinstance(result, str):
                self.lossy = self.transformed = True
                return UNKNOWN_STRING
            results.append(_split_stand_ins(result))
        if results[0] is None or results[0] != results[1]:
            self.lossy = self.transformed = True
            return UNKNOWN_STRING
        return _joined(results[0])

    def structure(self, expr: Expr) -> list[Expr]:
        """The expression and the parts its value is built from, in source order.

        A literal that only feeds a run-time piece (an argument of another call) is not included.
        """

        members = [expr]
        for item in expr.items:
            if item.kind in ("seq", "map", "field") or (item.kind != "unknown" and is_string(self.value(item))):
                members.extend(self.structure(item))
        return members

    def leaves(self, expr: Expr) -> list[str]:
        """Every string literal in the structure, in source order (bytes read as Latin-1)."""

        return [
            m.data.decode("latin-1") if isinstance(m.data, bytes) else m.data
            for m in self.structure(expr)
            if m.kind == "lit" and isinstance(m.data, (str, bytes))
        ]

    def search_texts(self, expr: Expr, joined: bool = True) -> list[tuple[str, bool]]:
        """Texts to search for names in a string whose value is not fully known, each with whether
        run-time text may follow it.

        These are the known runs of the value; with ``joined``, the literals joined in source order
        (``"scr" + x + "ipts.y"`` when x is empty); and, when the evaluation gave up a piece
        (``lossy``), each literal and the known parts of every evaluated sub-expression.
        """

        parts = text_parts(self.value(expr))  # type: ignore[arg-type]
        texts = static_runs(parts)
        leaves = self.leaves(expr)
        if joined:
            texts.append(("".join(leaves), parts[-1] is None))
        if self.lossy:
            texts.extend((text, True) for text in self.literal_texts(expr))
        return texts

    def literal_texts(self, expr: Expr) -> list[str]:
        """Each literal and the known parts of every evaluated sub-expression."""

        return [*self.leaves(expr)] + [
            part
            for member in self.structure(expr)
            if member.kind != "lit" and is_string(self.value(member))
            for part in text_parts(self.value(member))  # type: ignore[arg-type]
            if part
        ]


def _holds_literals(value: object) -> bool:
    """Whether a value carries known text that formatting could cut or reshape."""

    if isinstance(value, Static):
        return True
    if isinstance(value, Partial):
        return any(part is not None for part in value.parts)
    if isinstance(value, Container):
        return any(_holds_literals(v) for v in value.values)
    return False


def _entries(value: object, mapping: bool) -> list[object] | dict[object, object] | None:
    """The values of a literal sequence, or the entries of a literal mapping; None when not known."""

    if isinstance(value, Static) and mapping and isinstance(value.value, dict):
        return {k: Static(v) for k, v in value.value.items()}
    if isinstance(value, Static) and not mapping and isinstance(value.value, (list, tuple)):
        return [Static(v) for v in value.value]
    if isinstance(value, Container) and mapping and value.kind == "dict":
        keys = value.values[0::2]
        if not all(isinstance(k, Static) for k in keys):
            return None
        return {k.value: v for k, v in zip(keys, value.values[1::2], strict=True)}  # type: ignore[union-attr]
    if isinstance(value, Container) and not mapping and value.kind != "dict":
        return list(value.values)
    return None


def _one_character_pattern(function: object, inputs: Sequence[object]) -> bool:
    """``text.replace(old, new)`` whose known ``old`` is at most one character long."""

    if getattr(function, "method", None) != "replace" or len(inputs) < 2:
        return False
    old = inputs[1]
    return isinstance(old, Static) and isinstance(old.value, (str, bytes)) and len(old.value) <= 1


def _controls(method: str, passing: Sequence[str]) -> set[int]:
    """Inputs (0 = the receiver, then the arguments) that steer a method rather than being inserted."""

    arguments = set(range(1, len(passing) + 1))
    if method in ("format", "format_map"):
        return {0}  # the template; the values are inserted
    if method == "join":
        return set()  # the separator and the elements are inserted
    if method in ("lower", "upper", "casefold", "swapcase"):
        return arguments  # per character: the receiver is content
    if method in ("center", "ljust", "rjust"):
        return arguments  # padding depends only on the receiver's length
    if method == "replace":
        positional = [i + 1 for i, how in enumerate(passing) if how == ""]
        new = positional[1] if len(positional) > 1 and passing[: positional[1]].count("*") == 0 else None
        return {0} | {i for i in arguments if i != new}  # only the replacement is inserted; see _apply
    return {0} | arguments


def static_runs(parts: Sequence[str | None]) -> list[tuple[str, bool]]:
    """Consecutive known texts of a string, each with whether run-time text follows it."""

    runs: list[tuple[str, bool]] = []
    for index, part in enumerate(parts):
        if part is not None:
            runs.append((part, index + 1 < len(parts)))  # ``_joined`` keeps known and run-time pieces apart
    return runs


def cst_expr(node: cst.CSTNode) -> Expr:
    """The tree-neutral form of a LibCST expression."""

    if isinstance(node, (cst.SimpleString, cst.Integer, cst.Float)):
        return Expr("lit", node, data=node.evaluated_value)
    if isinstance(node, cst.ConcatenatedString):
        return Expr("add", node, (cst_expr(node.left), cst_expr(node.right)))
    if isinstance(node, cst.FormattedString):
        return Expr("fstr", node, tuple(_cst_fstring_items(node, node.parts)))
    if isinstance(node, cst.BinaryOperation):
        kind = {cst.Add: "add", cst.Modulo: "mod", cst.Multiply: "mul"}.get(type(node.operator))
        if kind is not None:
            return Expr(kind, node, (cst_expr(node.left), cst_expr(node.right)))
    if (
        isinstance(node, cst.Call)
        and isinstance(node.func, cst.Attribute)
        and (node.func.attr.value in STR_METHODS or _cst_stringish(node.func.value))
    ):
        items = (cst_expr(node.func.value), *(cst_expr(arg.value) for arg in node.args))
        passing = tuple(f"={arg.keyword.value}" if arg.keyword is not None else str(arg.star) for arg in node.args)
        return Expr("call", node, items, (node.func.attr.value, passing))
    if isinstance(node, cst.Subscript) and len(node.slice) == 1:
        element = node.slice[0].slice
        if isinstance(element, cst.Index) and element.star is None:
            return Expr("index", node, (cst_expr(node.value), cst_expr(element.value)))
        if isinstance(element, cst.Slice):
            bounds = (element.lower, element.upper, element.step)
            items = tuple(cst_expr(b) if b is not None else Expr("lit", node, data=None) for b in bounds)
            return Expr("index", node, (cst_expr(node.value), *items), "slice")
    if isinstance(node, cst.IfExp):
        return Expr("choice", node, (cst_expr(node.body), cst_expr(node.orelse)))
    if isinstance(node, cst.BooleanOperation):
        return Expr("choice", node, (cst_expr(node.left), cst_expr(node.right)))
    if isinstance(node, cst.NamedExpr):
        return Expr("same", node, (cst_expr(node.value),))
    if (
        isinstance(node, cst.Call)
        and isinstance(node.func, cst.Name)
        and node.func.value in BUILTINS
        and node.args
        and all(arg.keyword is None and not arg.star for arg in node.args)
    ):
        return Expr("builtin", node, tuple(cst_expr(arg.value) for arg in node.args), node.func.value)
    if isinstance(node, (cst.List, cst.Tuple, cst.Set)):
        kind = {cst.List: "list", cst.Tuple: "tuple", cst.Set: "set"}[type(node)]
        unpacked = any(isinstance(e, cst.StarredElement) for e in node.elements)
        return Expr("seq", node, tuple(cst_expr(e.value) for e in node.elements), (kind, unpacked))
    if isinstance(node, cst.Dict):
        pairs = [e for e in node.elements if isinstance(e, cst.DictElement)]
        items = tuple(x for e in pairs for x in (cst_expr(e.key), cst_expr(e.value)))
        return Expr("map", node, items, ("dict", len(pairs) != len(node.elements)))
    return Expr("unknown", node)


def _cst_stringish(node: cst.CSTNode) -> bool:
    """Syntax that may evaluate to a string the evaluator can see into (not a name or attribute)."""

    return isinstance(
        node,
        (cst.SimpleString, cst.ConcatenatedString, cst.FormattedString, cst.BinaryOperation, cst.Subscript, cst.Call),
    )


def _ast_stringish(node: ast.AST) -> bool:
    return isinstance(node, (ast.Constant, ast.JoinedStr, ast.BinOp, ast.Subscript, ast.Call))


def _cst_fstring_items(node: cst.FormattedString, parts: Sequence[cst.BaseFormattedStringContent]) -> Iterator[Expr]:
    for part in parts:
        if isinstance(part, cst.FormattedStringText):
            yield Expr("lit", part, data=_fstring_text(node, part.value))
        elif isinstance(part, cst.FormattedStringExpression) and part.equal is None:
            items = [cst_expr(part.expression)]
            if part.format_spec is not None:
                items.append(Expr("fstr", part, tuple(_cst_fstring_items(node, part.format_spec))))
            yield Expr("field", part, tuple(items), part.conversion)
        else:
            yield Expr("unknown", part)  # ``f"{x=}"`` and future forms


def ast_expr(node: ast.AST) -> Expr:
    """The tree-neutral form of an ast expression (rename_nonpython.py reads Python files with ast)."""

    if isinstance(node, ast.Constant) and type(node.value) in (str, bytes, int, float):
        return Expr("lit", node, data=node.value)
    if isinstance(node, ast.JoinedStr):
        return Expr("fstr", node, tuple(_ast_fstring_items(node.values)))
    if isinstance(node, ast.BinOp):
        kind = {ast.Add: "add", ast.Mod: "mod", ast.Mult: "mul"}.get(type(node.op))
        if kind is not None:
            return Expr(kind, node, (ast_expr(node.left), ast_expr(node.right)))
    if (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and (node.func.attr in STR_METHODS or _ast_stringish(node.func.value))
    ):
        args = [(a.value, "*") if isinstance(a, ast.Starred) else (a, "") for a in node.args]
        args += [(k.value, "**" if k.arg is None else f"={k.arg}") for k in node.keywords]
        items = (ast_expr(node.func.value), *(ast_expr(value) for value, _ in args))
        return Expr("call", node, items, (node.func.attr, tuple(how for _, how in args)))
    if isinstance(node, ast.Subscript):
        if isinstance(node.slice, ast.Slice):
            bounds = (node.slice.lower, node.slice.upper, node.slice.step)
            items = tuple(ast_expr(b) if b is not None else Expr("lit", node, data=None) for b in bounds)
            return Expr("index", node, (ast_expr(node.value), *items), "slice")
        return Expr("index", node, (ast_expr(node.value), ast_expr(node.slice)))
    if isinstance(node, ast.IfExp):
        return Expr("choice", node, (ast_expr(node.body), ast_expr(node.orelse)))
    if isinstance(node, ast.BoolOp):
        return Expr("choice", node, tuple(ast_expr(value) for value in node.values))
    if isinstance(node, ast.NamedExpr):
        return Expr("same", node, (ast_expr(node.value),))
    if (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id in BUILTINS
        and node.args
        and not node.keywords
        and not any(isinstance(arg, ast.Starred) for arg in node.args)
    ):
        return Expr("builtin", node, tuple(ast_expr(arg) for arg in node.args), node.func.id)
    if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
        kind = {ast.List: "list", ast.Tuple: "tuple", ast.Set: "set"}[type(node)]
        unpacked = any(isinstance(e, ast.Starred) for e in node.elts)
        return Expr("seq", node, tuple(ast_expr(e) for e in node.elts), (kind, unpacked))
    if isinstance(node, ast.Dict):
        pairs = [(k, v) for k, v in zip(node.keys, node.values, strict=True) if k is not None]
        items = tuple(x for k, v in pairs for x in (ast_expr(k), ast_expr(v)))
        return Expr("map", node, items, ("dict", len(pairs) != len(node.keys)))
    return Expr("unknown", node)


def _ast_fstring_items(values: Sequence[ast.expr]) -> Iterator[Expr]:
    for value in values:
        if isinstance(value, ast.Constant):
            yield Expr("lit", value, data=value.value)
        elif isinstance(value, ast.FormattedValue):
            items = [ast_expr(value.value)]
            if value.format_spec is not None:
                items.append(ast_expr(value.format_spec))
            yield Expr("field", value, tuple(items), None if value.conversion == -1 else chr(value.conversion))
        else:
            yield Expr("unknown", value)


def _mark_parts(node: cst.CSTNode, ids: set[int]) -> None:
    """Record a string expression and every string in its structure; the outermost one decides."""

    ids.update(id(member.origin) for member in Evaluator().structure(cst_expr(node)))


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


def rename_source(
    ownership: OwnershipMap, rel_path: str, source: bytes, external_names: frozenset[str] | None = None
) -> tuple[bytes, list[Finding], list[Finding]]:
    """Run the codemod over one file's bytes; return (new bytes, rewrites, unresolved).

    Any exception inside the pass is reported for this file, which is then left unchanged.
    """

    try:
        return _rename_source(ownership, rel_path, source, external_names)
    except Exception as exc:  # one unexpected input must not stop the run or half-write a file
        detail = f"the rename pass failed ({type(exc).__name__}: {exc}); file left unchanged"
        return source, [], [Finding(rel_path, 1, "tool_error", rel_path, detail=detail)]


def _rename_source(
    ownership: OwnershipMap, rel_path: str, source: bytes, external_names: frozenset[str] | None
) -> tuple[bytes, list[Finding], list[Finding]]:
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
