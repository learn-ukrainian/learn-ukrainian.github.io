#!/usr/bin/env python3
"""Ratchet: writable ``sqlite3.connect`` opens of ``sources.db`` / ``vesum.db`` (#9609).

The open-model-data plan (PA2) builds only from authenticated source rows, so no
code outside the ingest layer may open the two source databases writable.  This
linter parses every tracked Python file (``git ls-files``) except ``tests/``,
``archive/`` and the ingest package ``scripts/ingest/``, finds each
``sqlite3.connect`` call, and decides two things from the AST:

* **Target.**  The database argument is resolved through the names it uses:
  assignments and parameter defaults in the enclosing functions, module-level
  assignments, ``self.<attr>`` assignments in the enclosing class and the return
  values of module-local functions (bounded depth).  The call targets a source
  database when a resolved string contains ``sources.db`` / ``vesum.db`` or a
  resolved identifier names one (``sources_db``, ``SOURCES_DB_PATH``,
  ``_resolve_sources_db``, ``vesum_db`` ...).  A function parameter is resolved
  through its default *and* the arguments of the module's own calls of that
  function (keyword and positional, through any number of call levels), because
  an explicit argument overrides the default; a parameter with neither a default
  nor a caller in the module (a public helper) counts as a source-database target
  when the module itself names a source database anywhere.
* **Mode.**  The open is read-only only when ``uri=True`` is passed literally and
  the database argument is, on every path (defaults and caller arguments alike),
  a URI that carries ``mode=ro`` or ``immutable=1`` as literal text.  An argument that is read-only on some paths
  only (``a if read_only else b``) is reported as ``conditional``.

Caller arguments are mapped to parameters by call shape: ``obj.read(p)`` and
``Cls().read(p)`` bind ``self``, ``Cls.read(obj, p)`` passes it explicitly,
``@classmethod`` binds ``cls`` either way, ``@staticmethod`` binds nothing, and
``Cls(p)`` / ``Cls.__init__(self, p)`` / ``super().__init__(p)`` reach ``__init__``.

Known limits.  This is a lint backstop; the runtime defence is that the read paths
open the databases read-only.  Not followed: calls across modules (a path handed
in from another module under a neutral name, into a module that never names a
source database), arguments forwarded through ``*args`` / ``**kwargs``, callables
wrapped in ``functools.partial``, callbacks and other first-class function
values, a class bound to another name, and subclass constructors that inherit
``__init__``.  Callers are matched by name, so unrelated same-named callables
add evidence (over-approximation, never a missed writer).

Remaining writable sites are allowlisted by ``(path, stripped snippet,
max_occurrences, reason)``; the allowlist may only shrink.  Stale entries fail.
"""

from __future__ import annotations

import argparse
import ast
import re
import subprocess
import sys
from collections import Counter
from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

# Ingest code may write the source databases; tests build their own fixtures;
# archived code is not importable product code.
EXCLUDED_PREFIXES: tuple[str, ...] = ("tests/", "archive/", "scripts/ingest/")

SOURCE_DB_TOKEN = re.compile(r"(?<![a-z0-9])(?:sources[-_.]?db|vesum)", re.IGNORECASE)
READ_ONLY_TOKEN = re.compile(r"[?&](?:mode=ro|immutable=1)(?![a-z0-9])")
_MAX_DEPTH = 6

_FunctionNode = ast.FunctionDef | ast.AsyncFunctionDef


@dataclass(frozen=True)
class AllowedSite:
    path: str
    snippet: str
    max_occurrences: int
    reason: str


# Writable or conditional opens outside ``scripts/ingest/``.  Every entry states
# why the open stays writable (a writer by role) or why the target is not a
# source database.
ALLOWLIST: tuple[AllowedSite, ...] = (
    AllowedSite(
        "data/projects/ua_eval_harness/releases/v0.1.1/vesum_reingest.py",
        "connection = sqlite3.connect(temporary_path)",
        1,
        "frozen v0.1.1 release copy of the VESUM shadow builder: creates a new shadow DB and refuses data/vesum.db",
    ),
    AllowedSite(
        "scripts/audit/generate_practice_deck.py",
        "conn = sqlite3.connect(path)",
        1,
        "read_atlas_db opens data/atlas.db, not a source DB",
    ),
    AllowedSite(
        "scripts/audit/sum11_sovietization_scan.py",
        "conn = sqlite3.connect(args.db)",
        1,
        "classifier backfill: UPDATE sum11 SET sovietization_risk, sovietization_keywords",
    ),
    AllowedSite(
        "scripts/audit/verbatim_overlap_gate.py",
        "self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)",
        1,
        "ShingleIndex writes its own verbatim_shingle index DB, not a source DB",
    ),
    AllowedSite(
        "scripts/ci/data_tier.py",
        "contextlib.closing(sqlite3.connect(target)) as writer,",
        1,
        "writes a backup copy into a disposable CI checkout; the primary source DB is read mode=ro",
    ),
    AllowedSite(
        "scripts/etymology/extract_cognate_forms.py",
        "conn = sqlite3.connect(db_path)",
        1,
        "etymology loader: creates and fills esum_cognate_forms in sources.db",
    ),
    AllowedSite(
        "scripts/etymology/recover_latin_cognates.py",
        "conn = sqlite3.connect(db_path)",
        1,
        "schema backfill: ALTER TABLE and UPDATE esum_cognate_forms in sources.db",
    ),
    AllowedSite(
        "scripts/lexicon/load_relation_candidates.py",
        "conn = sqlite3.connect(db_path)",
        2,
        "loader: creates relation_pairs and upserts candidate and verdict rows in sources.db",
    ),
    AllowedSite(
        "scripts/lexicon/migrate_sum11_sovietization.py",
        "conn = sqlite3.connect(args.db)",
        1,
        "migration: adds sum11.sovietization_* columns and index, writes the flags",
    ),
    AllowedSite(
        "scripts/lexicon/reconcile_calque_clusters.py",
        "self._atlas_conn = sqlite3.connect(self.atlas_db_path)",
        1,
        "atlas.db writer; sources.db is opened separately mode=ro",
    ),
    AllowedSite(
        "scripts/lexicon/runner/fetch_ulif_homonyms.py",
        "self.conn = sqlite3.connect(path)",
        1,
        "runner's own ledger.sqlite, not a source DB",
    ),
    AllowedSite(
        "scripts/lexicon/runner/generate_pr1_fixture.py",
        "conn = sqlite3.connect(path)",
        1,
        "builds a hermetic synthetic sources slice fixture, not the live sources.db",
    ),
    AllowedSite(
        "scripts/lexicon/runner/network_cache.py",
        "self._conn = sqlite3.connect(self.path, isolation_level=None)",
        1,
        "network cache DB, guarded by assert_not_sources_db just before the open",
    ),
    AllowedSite(
        "scripts/lexicon/runner/phase_relations.py",
        "conn = sqlite3.connect(output_db)",
        1,
        "recreates the run-level relations output DB, not a source DB",
    ),
    AllowedSite(
        "scripts/lexicon/runner/side_db.py",
        "out = sqlite3.connect(output)",
        3,
        "Balla, dmklinger and kaikki side-DB artifacts, freshly unlinked; not source DBs",
    ),
    AllowedSite(
        "scripts/lexicon/runner/ulif_forms.py",
        "conn = sqlite3.connect(str(target_db))",
        1,
        "derived-table builder: rewrites ulif_forms, ulif_forms_failures, ulif_forms_build in sources.db",
    ),
    AllowedSite(
        "scripts/lexicon/sum20_lookup.py",
        "conn = sqlite3.connect(target) if write else sqlite3.connect(read_only_uri, uri=True)",
        1,
        "write branch only (write=True): caches fetched СУМ-20 articles into sum20_articles; reads open mode=ro",
    ),
    AllowedSite(
        "scripts/lexicon/teacher_deck.py",
        'conn = sqlite3.connect(sources_db.resolve().as_uri() + "?mode=rw", uri=True, timeout=30)',
        1,
        "ingest: private_teacher_lessons_ingest rewrites teacher-lesson rows in textbooks/textbook_sections",
    ),
    AllowedSite(
        "scripts/lexicon/tools/dump_ulif.py",
        "self.conn = sqlite3.connect(str(self.db_path))",
        1,
        "ULIF crawler's own resumable dump DB, not a source DB",
    ),
    AllowedSite(
        "scripts/lexicon/tools/dump_ulif.py",
        "dump_conn = sqlite3.connect(str(dump_db_path))",
        1,
        "reads the ULIF crawler dump DB; sources.db writes go through store_ulif_dictua_entry",
    ),
    AllowedSite(
        "scripts/lexicon/tools/import_ulif_dump.py",
        "dump_conn = sqlite3.connect(str(args.dump_db))",
        1,
        "ULIF crawler dump DB (--dump-db), not a source DB",
    ),
    AllowedSite(
        "scripts/lexicon/tools/import_ulif_dump.py",
        "target_conn = sqlite3.connect(str(args.sources_db))",
        1,
        "importer: upserts ulif_dictua_entries and ulif_dictua_sections in sources.db",
    ),
    AllowedSite(
        "scripts/lexicon/tools/migrate_ulif_raw.py",
        "conn = sqlite3.connect(db, timeout=0)",
        2,
        "migration: WAL checkpoint, DROP of the ULIF raw table, VACUUM INTO a compacted sources.db",
    ),
    AllowedSite(
        "scripts/lexicon/tools/migrate_ulif_raw.py",
        "compact_writable = sqlite3.connect(new)",
        1,
        "migration: sets WAL on the compacted sources.db.new before the rename",
    ),
    AllowedSite(
        "scripts/migrations/2026-05-15-add-author-uk-to-textbooks.py",
        "with sqlite3.connect(str(args.db)) as conn:",
        1,
        "migration: adds and fills textbooks.author_uk",
    ),
    AllowedSite(
        "scripts/migrations/2026-07-06-add-subject-to-textbooks.py",
        "with sqlite3.connect(str(args.db)) as conn:",
        1,
        "migration: adds and fills textbooks.subject",
    ),
    AllowedSite(
        "scripts/projects/open_model_data/phase3_vspu_db_cutover.py",
        "with sqlite3.connect(source_uri, uri=True) as source_connection, sqlite3.connect(target) as target_connection:",
        1,
        "cutover/rollback: restores sources.db from a mode=ro snapshot via the SQLite backup API",
    ),
    AllowedSite(
        "scripts/rag/migrate_add_literary_source_url.py",
        "conn = sqlite3.connect(str(db_path))",
        1,
        "migration: adds and backfills literary_texts.source_url",
    ),
    AllowedSite(
        "scripts/rag/scrape_wikisource.py",
        "conn = sqlite3.connect(str(db_path))",
        1,
        "loader: rewrites literary_texts rows and rebuilds literary_fts",
    ),
    AllowedSite(
        "scripts/rag/vesum_reingest.py",
        "connection = sqlite3.connect(temporary_path)",
        1,
        "VESUM shadow builder: creates a new shadow DB and refuses data/vesum.db",
    ),
    AllowedSite(
        "scripts/wiki/build_sources_db.py",
        "connection = sqlite3.connect(str(db_path))",
        2,
        "rebuild: grade backfills on the temporary rebuild DB",
    ),
    AllowedSite(
        "scripts/wiki/build_sources_db.py",
        "conn = sqlite3.connect(str(db))",
        1,
        "rebuild finalization: declares WAL on the swapped-in sources.db",
    ),
    AllowedSite(
        "scripts/wiki/build_sources_db.py",
        "conn = sqlite3.connect(str(tmp_db))",
        1,
        "rebuild: creates the new sources.db in a temporary file before the atomic swap",
    ),
    AllowedSite(
        "scripts/wiki/diagnostics/retrieval_bakeoff_9233.py",
        "db = sqlite3.connect(destination)",
        1,
        "work-dir vector cache, not a source DB",
    ),
    AllowedSite(
        "scripts/wiki/diagnostics/retrieval_bakeoff_9233.py",
        "with sqlite3.connect(target) as conn:",
        1,
        "work-dir corpus subset copy, not a source DB; sources.db is read through _ro_connect",
    ),
    AllowedSite(
        "scripts/wiki/extract_sections.py",
        "with sqlite3.connect(str(db_path)) as conn:",
        1,
        "build step: creates and fills textbook_sections, sets textbooks.parent_section_id",
    ),
    AllowedSite(
        "scripts/wiki/fetch_wikipedia.py",
        "conn = sqlite3.connect(str(DB_PATH))",
        1,
        "fetcher: inserts wikipedia and wikipedia_negative_cache rows",
    ),
    AllowedSite(
        "scripts/wiki/migrate_external_chunks.py",
        "conn = sqlite3.connect(str(db_path))",
        1,
        "migration: external_articles columns, rows and external_fts rebuild",
    ),
    AllowedSite(
        "scripts/wiki/restore_literary_metadata.py",
        "conn = sqlite3.connect(str(db_path))",
        1,
        "schema backfill: literary_texts metadata columns and values",
    ),
    AllowedSite(
        "scripts/wiki/rollback_sections.py",
        "with sqlite3.connect(str(db_path)) as conn, conn:",
        1,
        "migration rollback: drops textbook_sections and textbooks.parent_section_id (--db sources.db)",
    ),
    AllowedSite(
        "scripts/wiki/sources_db.py",
        "conn = sqlite3.connect(str(db_path), check_same_thread=False)",
        1,
        "_open_conn write branch (read_only=False): ULIF DictUA schema creation and --migrate; lookups open mode=ro",
    ),
    AllowedSite(
        "scripts/wiki/ukrainian_wiki_corpus.py",
        "conn = sqlite3.connect(str(db_path))",
        3,
        "loader and migration: ukrainian_wiki schema and passage rows",
    ),
)


@dataclass(frozen=True)
class Finding:
    rel_path: str
    line_no: int
    snippet: str
    kind: str  # "writable" | "conditional"


@dataclass
class _Scope:
    node: ast.AST
    assignments: dict[str, list[ast.expr]] = field(default_factory=dict)
    parameters: dict[str, ast.expr | None] = field(default_factory=dict)


def _target_names(target: ast.expr) -> Iterator[str]:
    if isinstance(target, ast.Name):
        yield target.id
    elif isinstance(target, (ast.Tuple, ast.List, ast.Starred)):
        for element in target.elts if not isinstance(target, ast.Starred) else [target.value]:
            yield from _target_names(element)


def _collect_assignments(body: Iterable[ast.AST], into: dict[str, list[ast.expr]]) -> None:
    """Record ``name = value`` bindings of one scope, not of nested scopes."""
    stack = list(body)
    while stack:
        node = stack.pop()
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)):
            continue
        if isinstance(node, ast.Assign):
            for target in node.targets:
                for name in _target_names(target):
                    into.setdefault(name, []).append(node.value)
        elif isinstance(node, (ast.AnnAssign, ast.AugAssign)) and node.value is not None:
            for name in _target_names(node.target):
                into.setdefault(name, []).append(node.value)
        elif isinstance(node, ast.NamedExpr):
            into.setdefault(node.target.id, []).append(node.value)
        elif isinstance(node, (ast.With, ast.AsyncWith)):
            for item in node.items:
                if item.optional_vars is not None:
                    for name in _target_names(item.optional_vars):
                        into.setdefault(name, []).append(item.context_expr)
        elif isinstance(node, (ast.For, ast.AsyncFor, ast.comprehension)):
            for name in _target_names(node.target):
                into.setdefault(name, []).append(node.iter)
        stack.extend(ast.iter_child_nodes(node))


def _parameter_list(node: _FunctionNode | ast.Lambda) -> list[tuple[str, ast.expr | None, bool]]:
    """``(name, default, positional)`` for every parameter, in declaration order."""
    args = node.args
    positional = [*args.posonlyargs, *args.args]
    defaults: list[ast.expr | None] = [None] * (len(positional) - len(args.defaults)) + list(args.defaults)
    params = [(arg.arg, default, True) for arg, default in zip(positional, defaults, strict=True)]
    params += [(arg.arg, default, False) for arg, default in zip(args.kwonlyargs, args.kw_defaults, strict=True)]
    for arg in (args.vararg, args.kwarg):
        if arg is not None:
            params.append((arg.arg, None, False))
    return params


def _function_scope(node: _FunctionNode | ast.Lambda) -> _Scope:
    scope = _Scope(node)
    for name, default, _positional in _parameter_list(node):
        scope.parameters[name] = default
    _collect_assignments([node.body] if isinstance(node, ast.Lambda) else node.body, scope.assignments)
    return scope


@dataclass
class _Evidence:
    strings: list[str] = field(default_factory=list)
    identifiers: set[str] = field(default_factory=set)
    open_parameter: bool = False  # a default-less parameter with no caller in the module

    def mentions_source_db(self) -> bool:
        return any(SOURCE_DB_TOKEN.search(text) for text in (*self.strings, *self.identifiers))


class _ModuleAnalysis:
    def __init__(self, tree: ast.Module, source: str) -> None:
        self.tree = tree
        self.module_scope = _Scope(tree)
        _collect_assignments(tree.body, self.module_scope.assignments)
        self.module_names_source_db = bool(SOURCE_DB_TOKEN.search(source))
        self.functions: dict[str, list[_FunctionNode]] = {}
        self.classes: dict[str, ast.ClassDef] = {}
        self.class_attributes: dict[ast.ClassDef, dict[str, list[ast.expr]]] = {}
        self.parents: dict[ast.AST, ast.AST] = {}
        self.calls: list[ast.Call] = []
        self.connect_names: set[str] = set()
        self.sqlite_aliases: set[str] = set()
        self._scope_cache: dict[ast.AST, _Scope] = {}
        self._caller_cache: dict[tuple[ast.AST, str], list[ast.expr]] = {}
        for parent in ast.walk(tree):
            for child in ast.iter_child_nodes(parent):
                self.parents[child] = parent
            if isinstance(parent, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self.functions.setdefault(parent.name, []).append(parent)
            elif isinstance(parent, ast.ClassDef):
                self.classes[parent.name] = parent
                self.class_attributes[parent] = self._self_attributes(parent)
            elif isinstance(parent, ast.Call):
                self.calls.append(parent)
            elif isinstance(parent, ast.Import):
                for alias in parent.names:
                    if alias.name == "sqlite3":
                        self.sqlite_aliases.add(alias.asname or "sqlite3")
            elif isinstance(parent, ast.ImportFrom) and parent.module == "sqlite3":
                for alias in parent.names:
                    if alias.name == "connect":
                        self.connect_names.add(alias.asname or "connect")
        self.cli_options = self._cli_options()

    def _cli_options(self) -> dict[str, list[ast.expr]]:
        """``dest`` → option strings, ``default`` and ``help`` of each ``add_argument`` call."""
        options: dict[str, list[ast.expr]] = {}
        for call in self.calls:
            if not (isinstance(call.func, ast.Attribute) and call.func.attr == "add_argument"):
                continue
            flags = [arg.value for arg in call.args if isinstance(arg, ast.Constant) and isinstance(arg.value, str)]
            keywords = {keyword.arg: keyword.value for keyword in call.keywords if keyword.arg}
            dest_node = keywords.get("dest")
            if isinstance(dest_node, ast.Constant) and isinstance(dest_node.value, str):
                dest = dest_node.value
            else:
                long_flags = [flag for flag in flags if flag.startswith("--")]
                chosen = long_flags[0] if long_flags else flags[0] if flags else ""
                dest = chosen.lstrip("-").replace("-", "_")
            if not dest:
                continue
            values: list[ast.expr] = [arg for arg in call.args if isinstance(arg, ast.Constant)]
            values += [keywords[name] for name in ("default", "help") if name in keywords]
            options.setdefault(dest, []).extend(values)
        return options

    @staticmethod
    def _self_attributes(cls: ast.ClassDef) -> dict[str, list[ast.expr]]:
        found: dict[str, list[ast.expr]] = {}
        for node in ast.walk(cls):
            pairs: list[tuple[ast.expr, ast.expr]] = []
            if isinstance(node, ast.Assign):
                pairs = [(target, node.value) for target in node.targets]
            elif isinstance(node, ast.AnnAssign) and node.value is not None:
                pairs = [(node.target, node.value)]
            for target, value in pairs:
                if (
                    isinstance(target, ast.Attribute)
                    and isinstance(target.value, ast.Name)
                    and target.value.id in {"self", "cls"}
                ):
                    found.setdefault(target.attr, []).append(value)
        return found

    def is_connect_call(self, node: ast.Call) -> bool:
        func = node.func
        if isinstance(func, ast.Attribute) and func.attr == "connect":
            return isinstance(func.value, ast.Name) and func.value.id in (self.sqlite_aliases or {"sqlite3"})
        return isinstance(func, ast.Name) and func.id in self.connect_names

    def scope_of(self, node: ast.AST) -> _Scope:
        if node not in self._scope_cache:
            self._scope_cache[node] = _function_scope(node)  # type: ignore[arg-type]
        return self._scope_cache[node]

    def context(self, node: ast.AST) -> tuple[list[_Scope], ast.ClassDef | None]:
        """Enclosing scopes (innermost first, module last) and the enclosing class."""
        scopes: list[_Scope] = []
        cls: ast.ClassDef | None = None
        current = self.parents.get(node)
        while current is not None:
            if isinstance(current, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
                scopes.append(self.scope_of(current))
            elif isinstance(current, ast.ClassDef) and cls is None:
                cls = current
            current = self.parents.get(current)
        scopes.append(self.module_scope)
        return scopes, cls

    def lookup(self, name: str, scopes: list[_Scope]) -> tuple[_Scope, list[ast.expr]] | None:
        for scope in scopes:
            if name in scope.parameters:
                # A parameter is bound by its default, by reassignments in the body
                # and by whatever the module's own callers pass; the default alone
                # never decides, because an explicit argument overrides it.
                values = list(scope.assignments.get(name, []))
                default = scope.parameters[name]
                if default is not None:
                    values.append(default)
                if isinstance(scope.node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    values.extend(self.caller_arguments(scope.node, name))
                return scope, values
            if name in scope.assignments:
                return scope, scope.assignments[name]
        return None

    def caller_arguments(self, function: _FunctionNode, parameter: str) -> list[ast.expr]:
        """Arguments passed for ``parameter`` by the module's own calls of ``function``."""
        key = (function, parameter)
        if key not in self._caller_cache:
            self._caller_cache[key] = self._find_caller_arguments(function, parameter)
        return self._caller_cache[key]

    def _implicit_arguments(self, function: _FunctionNode, call: ast.Call) -> int:
        """Leading positional parameters ``call`` binds implicitly (``self`` / ``cls``)."""
        owner = self.parents.get(function)
        if not isinstance(owner, ast.ClassDef):
            return 0
        decorators = {d.id for d in function.decorator_list if isinstance(d, ast.Name)}
        if "staticmethod" in decorators:
            return 0
        if "classmethod" in decorators:
            return 1  # ``cls`` is bound through the class and through an instance alike
        func = call.func
        if isinstance(func, ast.Attribute):
            # ``Reader.read(Reader(), path)`` passes ``self`` explicitly; ``obj.read(path)`` binds it.
            through_class = isinstance(func.value, ast.Name) and func.value.id in self.classes
            return 0 if through_class else 1
        return 1 if function.name == "__init__" else 0

    def _find_caller_arguments(self, function: _FunctionNode, parameter: str) -> list[ast.expr]:
        params = _parameter_list(function)
        positional = [name for name, _default, is_positional in params if is_positional]
        callee_names = {function.name}
        owner = self.parents.get(function)
        if function.name == "__init__" and isinstance(owner, ast.ClassDef):
            callee_names = {owner.name, "__init__"}  # ``Reader(path)`` and ``super().__init__(path)``
        found: list[ast.expr] = []
        for call in self.calls:
            func = call.func
            called = func.id if isinstance(func, ast.Name) else func.attr if isinstance(func, ast.Attribute) else None
            if called not in callee_names:
                continue
            for keyword in call.keywords:
                if keyword.arg == parameter:
                    found.append(keyword.value)
            if parameter in positional:
                position = positional.index(parameter) - self._implicit_arguments(function, call)
                if 0 <= position < len(call.args) and not any(
                    isinstance(a, ast.Starred) for a in call.args[: position + 1]
                ):
                    found.append(call.args[position])
        return found


class _Walker:
    """Collects target evidence and decides read-only mode for one expression."""

    def __init__(self, analysis: _ModuleAnalysis) -> None:
        self.analysis = analysis
        self.evidence = _Evidence()
        self._seen: set[tuple[int, str]] = set()

    # -- target evidence -------------------------------------------------
    def collect(self, node: ast.AST | None, scopes: list[_Scope], cls: ast.ClassDef | None, depth: int = 0) -> None:
        if node is None or depth > _MAX_DEPTH:
            return
        if isinstance(node, ast.Constant):
            if isinstance(node.value, str):
                self.evidence.strings.append(node.value)
            return
        if isinstance(node, ast.Name):
            self._collect_name(node.id, scopes, depth)
            return
        if isinstance(node, ast.Attribute):
            self.evidence.identifiers.add(node.attr)
            if isinstance(node.value, ast.Name) and node.value.id in {"self", "cls"} and cls is not None:
                key = (id(cls), node.attr)
                if key not in self._seen:
                    self._seen.add(key)
                    for value in self.analysis.class_attributes.get(cls, {}).get(node.attr, []):
                        self.collect(value, *self.analysis.context(value), depth + 1)
                return
            for option in self.analysis.cli_options.get(node.attr, []):
                self.collect(option, *self.analysis.context(option), depth + 1)
            self.collect(node.value, scopes, cls, depth)
            return
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                self.evidence.identifiers.add(func.id)
                for definition in self.analysis.functions.get(func.id, []):
                    for value in self._returns(definition):
                        self.collect(
                            value, [self.analysis.scope_of(definition), self.analysis.module_scope], None, depth + 1
                        )
            else:
                self.collect(func, scopes, cls, depth)
        for child in ast.iter_child_nodes(node):
            if child is not getattr(node, "func", None):
                self.collect(child, scopes, cls, depth)

    def _returns(self, definition: _FunctionNode) -> list[ast.expr]:
        key = (id(definition), "<return>")
        if key in self._seen:
            return []
        self._seen.add(key)
        return [
            inner.value for inner in ast.walk(definition) if isinstance(inner, ast.Return) and inner.value is not None
        ]

    def _collect_name(self, name: str, scopes: list[_Scope], depth: int) -> None:
        self.evidence.identifiers.add(name)
        found = self.analysis.lookup(name, scopes)
        if found is None:
            return
        scope, values = found
        key = (id(scope.node), name)
        if key in self._seen:
            return
        self._seen.add(key)
        for value in values:
            self.collect(value, *self.analysis.context(value), depth + 1)
        if not values and name in scope.parameters and isinstance(scope.node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            self.evidence.open_parameter = True

    # -- read-only mode --------------------------------------------------
    def read_only(self, node: ast.AST | None, scopes: list[_Scope], depth: int = 0) -> bool:
        """True when ``node`` is, on every path, a URI with a literal read-only flag."""
        if node is None or depth > _MAX_DEPTH:
            return False
        if isinstance(node, ast.Constant):
            return isinstance(node.value, str) and bool(READ_ONLY_TOKEN.search(node.value))
        if isinstance(node, ast.JoinedStr):
            return any(self.read_only(value, scopes, depth) for value in node.values if isinstance(value, ast.Constant))
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
            return self.read_only(node.left, scopes, depth) or self.read_only(node.right, scopes, depth)
        if isinstance(node, ast.IfExp):
            return self.read_only(node.body, scopes, depth) and self.read_only(node.orelse, scopes, depth)
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Attribute) and func.attr == "format":
                return self.read_only(func.value, scopes, depth)
            if isinstance(func, ast.Name) and func.id in self.analysis.functions:
                returns = [
                    inner.value
                    for definition in self.analysis.functions[func.id]
                    for inner in ast.walk(definition)
                    if isinstance(inner, ast.Return) and inner.value is not None
                ]
                return bool(returns) and all(self.read_only(value, scopes, depth + 1) for value in returns)
            return False
        if isinstance(node, ast.Name):
            found = self.analysis.lookup(node.id, scopes)
            if found is None:
                return False
            _scope, values = found
            return bool(values) and all(
                self.read_only(value, self.analysis.context(value)[0], depth + 1) for value in values
            )
        return False


def _database_argument(node: ast.Call) -> ast.expr | None:
    if node.args:
        return node.args[0]
    for keyword in node.keywords:
        if keyword.arg == "database":
            return keyword.value
    return None


def _uri_literal_true(node: ast.Call) -> bool:
    return any(
        keyword.arg == "uri" and isinstance(keyword.value, ast.Constant) and keyword.value.value is True
        for keyword in node.keywords
    )


def classify_source(source: str, rel_path: str) -> list[Finding]:
    """Return writable/conditional source-database opens in one module's source."""
    try:
        tree = ast.parse(source, filename=rel_path)
    except SyntaxError:
        return []
    analysis = _ModuleAnalysis(tree, source)
    lines = source.splitlines()
    findings: list[Finding] = []
    for node in analysis.calls:
        if not analysis.is_connect_call(node):
            continue
        scopes, cls = analysis.context(node)
        argument = _database_argument(node)
        walker = _Walker(analysis)
        walker.collect(argument, scopes, cls)
        evidence = walker.evidence
        if not (evidence.mentions_source_db() or (evidence.open_parameter and analysis.module_names_source_db)):
            continue
        if _uri_literal_true(node) and walker.read_only(argument, scopes):
            continue
        partly_read_only = any(READ_ONLY_TOKEN.search(text) for text in evidence.strings)
        snippet = lines[node.lineno - 1].strip() if node.lineno - 1 < len(lines) else ""
        findings.append(Finding(rel_path, node.lineno, snippet, "conditional" if partly_read_only else "writable"))
    return sorted(findings, key=lambda finding: finding.line_no)


def _is_excluded(rel_path: str) -> bool:
    return any(rel_path.startswith(prefix) for prefix in EXCLUDED_PREFIXES)


def iter_python_files(repo_root: Path) -> list[str]:
    """Tracked ``*.py`` files (repo-relative), or every ``*.py`` outside a git checkout."""
    try:
        listed = subprocess.run(
            ["git", "ls-files", "-z", "--", "*.py"],
            cwd=repo_root,
            check=True,
            capture_output=True,
            timeout=120,
        ).stdout.decode("utf-8")
        paths = [path for path in listed.split("\0") if path]
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        paths = [path.relative_to(repo_root).as_posix() for path in repo_root.rglob("*.py")]
    return sorted(path for path in paths if not _is_excluded(path))


def find_source_db_writable_connects(repo_root: Path | None = None) -> tuple[list[Finding], list[str]]:
    """Return ``(findings, unreadable)``; ``unreadable`` lists tracked files absent on disk."""
    root = (repo_root or REPO_ROOT).resolve()
    findings: list[Finding] = []
    unreadable: list[str] = []
    for rel_path in iter_python_files(root):
        try:
            source = (root / rel_path).read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            unreadable.append(rel_path)
            continue
        findings.extend(classify_source(source, rel_path))
    return findings, unreadable


def find_violations(
    repo_root: Path | None = None, allowlist: tuple[AllowedSite, ...] = ALLOWLIST
) -> tuple[list[str], list[str]]:
    """``(violations, unreadable)``: unallowlisted findings and stale allowlist entries.

    Files that are tracked but absent (a sparse checkout) are returned as
    ``unreadable``; their allowlist entries are not called stale.
    """
    findings, unreadable = find_source_db_writable_connects(repo_root)
    allowed = {(site.path, site.snippet): site.max_occurrences for site in allowlist}
    usage: Counter[tuple[str, str]] = Counter()
    violations: list[str] = []
    for finding in findings:
        key = (finding.rel_path, finding.snippet)
        usage[key] += 1
        if key in allowed and usage[key] <= allowed[key]:
            continue
        violations.append(f"{finding.rel_path}:{finding.line_no}: {finding.kind} open: {finding.snippet}")
    for site in allowlist:
        if site.path not in unreadable and usage[(site.path, site.snippet)] < site.max_occurrences:
            violations.append(
                f"{site.path}: stale allowlist entry ({usage[(site.path, site.snippet)]} of "
                f"{site.max_occurrences} found): {site.snippet}"
            )
    return violations, unreadable


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--list", action="store_true", help="print every finding, allowlisted or not")
    args = parser.parse_args(argv)
    if args.list:
        findings, unreadable = find_source_db_writable_connects()
        for finding in findings:
            print(f"{finding.rel_path}:{finding.line_no}\t{finding.kind}\t{finding.snippet}")
        for rel_path in unreadable:
            print(f"{rel_path}\tunreadable", file=sys.stderr)
        return 0
    violations, unreadable = find_violations()
    if not violations and not unreadable:
        print("OK: no unallowlisted writable sqlite3.connect to sources.db/vesum.db")
        return 0
    if violations:
        print("Writable sqlite3.connect to sources.db/vesum.db outside ingest code:", file=sys.stderr)
        for line in violations:
            print(f"  {line}", file=sys.stderr)
    if unreadable:
        print("Tracked files not scanned (absent on disk; `git sparse-checkout add` them):", file=sys.stderr)
        for rel_path in unreadable:
            print(f"  {rel_path}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
