"""Transform registry and content-addressed L1 transform digests (design r3 §6.1).

``l1_transform_digest[source]`` is the SHA-256 of the canonical JSON of that
source's transform manifest. Every component lists the modules that implement
it; each module enters the manifest by the SHA-256 of its source bytes, so a
changed module changes the digest even when nobody bumps its declared version.
``undeclared_imports`` scans every registered module with ``ast`` and reports a
project import that is not registered in the same manifest, so an undeclared
dependency cannot escape the digest. The build refuses to run while one exists.

Slices register here, in reviewed changes: parsers in ``PARSERS``, list
grammars in ``LIST_GRAMMARS`` and sources in ``SOURCES``. F registers none.
"""

from __future__ import annotations

import ast
import unicodedata
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from types import MappingProxyType
from typing import Any

from scripts.lexdata import case_signal, normalize, records, rights, rule_tables, schema, stress
from scripts.lexdata.canonical import sha256_canonical, sha256_file
from scripts.lexdata.derive import ROW_SHA256_FIELDS

REPO_ROOT = Path(__file__).resolve().parents[2]
PROJECT_PACKAGES = ("scripts", "tests")
TRANSFORM_MANIFEST_VERSION = "1"


class TransformRegistryError(RuntimeError):
    """The registry is incomplete: an unknown id or an undeclared dependency."""


@dataclass(frozen=True)
class ParserSpec:
    parser_id: str
    version: str
    modules: tuple[str, ...]
    repair_proposers: tuple[str, ...] = ()


@dataclass(frozen=True)
class ListGrammarSpec:
    grammar_id: str
    version: str
    modules: tuple[str, ...]


@dataclass(frozen=True)
class SourceSpec:
    """One L1 source. ``adapter`` is ``"module.path:factory"`` returning a SourceAdapter."""

    source_id: str
    parser_id: str
    rights_class: str
    rights_register_ids: tuple[str, ...] = ()
    list_grammar: str | None = None
    adapter: str | None = None
    expected_units: int | None = None


@dataclass(frozen=True)
class NormalizerBinding:
    """The normalizer a build or reader runs with (production or a test binding)."""

    impl: Callable[[str], normalize.Normalized]
    version: str
    modules: tuple[str, ...]
    vectors: str
    contents: Callable[[], Mapping[str, Any]]


PRODUCTION_NORMALIZER = NormalizerBinding(
    impl=normalize.normalize_span,
    version=normalize.NORMALIZER_VERSION,
    modules=("scripts/lexdata/normalize.py",),
    vectors="scripts/lexdata/normalization_vectors.json",
    contents=normalize.table_contents,
)

PARSERS: Mapping[str, ParserSpec] = MappingProxyType({})
LIST_GRAMMARS: Mapping[str, ListGrammarSpec] = MappingProxyType({})
SOURCES: Mapping[str, SourceSpec] = MappingProxyType({})


@dataclass(frozen=True)
class TransformBinding:
    """Everything a digest depends on. Tests bind a temp root, sources or a normalizer."""

    normalizer: NormalizerBinding = PRODUCTION_NORMALIZER
    parsers: Mapping[str, ParserSpec] = field(default_factory=lambda: PARSERS)
    list_grammars: Mapping[str, ListGrammarSpec] = field(default_factory=lambda: LIST_GRAMMARS)
    sources: Mapping[str, SourceSpec] = field(default_factory=lambda: SOURCES)
    repo_root: Path = REPO_ROOT


DEFAULT_BINDING = TransformBinding()


def _module_entry(root: Path, rel: str) -> dict[str, str]:
    path = root / rel
    try:
        return {"path": rel, "sha256": sha256_file(path)}
    except OSError as exc:
        raise TransformRegistryError(f"registered module unreadable: {rel} ({type(exc).__name__})") from exc


def _component(root: Path, version: str, modules: tuple[str, ...], contents: Mapping[str, Any] | None = None,
               data_files: tuple[str, ...] = ()) -> dict[str, Any]:
    return {
        "version": version,
        "modules": [_module_entry(root, rel) for rel in sorted(modules)],
        "data_files": [_module_entry(root, rel) for rel in sorted(data_files)],
        "contents_sha256": sha256_canonical(dict(contents or {})),
    }


def normalizer_manifest(binding: TransformBinding = DEFAULT_BINDING) -> dict[str, Any]:
    """Components that turn a query string into keys and ``case_signal`` (§6.3)."""
    root, norm = binding.repo_root, binding.normalizer
    return {
        "normalizer": _component(root, norm.version, norm.modules,
                                 {"unidata_version": unicodedata.unidata_version, **dict(norm.contents())},
                                 (norm.vectors,)),
        "case_signal": _component(root, case_signal.CASE_SIGNAL_VERSION, ("scripts/lexdata/case_signal.py",),
                                  {"values": sorted(case_signal.CASE_SIGNALS)}),
        "stress": _component(root, stress.STRESS_POLICY_VERSION, ("scripts/lexdata/stress.py",),
                             stress.policy_contents()),
    }


def normalizer_digest(binding: TransformBinding = DEFAULT_BINDING) -> str:
    return sha256_canonical(normalizer_manifest(binding))


def _shared_components(binding: TransformBinding) -> dict[str, Any]:
    root = binding.repo_root
    return {
        **normalizer_manifest(binding),
        "rule_tables": _component(root, rule_tables.RULE_TABLES_VERSION, ("scripts/lexdata/rule_tables.py",),
                                  rule_tables.table_contents()),
        "schema": _component(root, schema.L1_SCHEMA_VERSION, ("scripts/lexdata/schema.py",),
                             schema.schema_contents()),
        "records": _component(root, records.RECORDS_INTERFACE_VERSION, ("scripts/lexdata/records.py",)),
        "derivation": _component(root, TRANSFORM_MANIFEST_VERSION,
                                 ("scripts/lexdata/derive.py", "scripts/lexdata/canonical.py",
                                  "scripts/lexdata/rights.py"),
                                 {"row_sha256_fields": list(ROW_SHA256_FIELDS)}),
    }


def source_spec(source_id: str, binding: TransformBinding = DEFAULT_BINDING) -> SourceSpec:
    try:
        return binding.sources[source_id]
    except KeyError:
        raise TransformRegistryError(f"source {source_id!r} is not registered in transforms.SOURCES") from None


def transform_manifest(source_id: str, binding: TransformBinding = DEFAULT_BINDING) -> dict[str, Any]:
    spec = source_spec(source_id, binding)
    try:
        parser = binding.parsers[spec.parser_id]
    except KeyError:
        raise TransformRegistryError(f"parser {spec.parser_id!r} is not registered") from None
    root = binding.repo_root
    grammar: dict[str, Any] | None = None
    if spec.list_grammar is not None:
        try:
            grammar_spec = binding.list_grammars[spec.list_grammar]
        except KeyError:
            raise TransformRegistryError(f"list grammar {spec.list_grammar!r} is not registered") from None
        grammar = {"grammar_id": grammar_spec.grammar_id,
                   **_component(root, grammar_spec.version, grammar_spec.modules)}
    return {
        "manifest_version": TRANSFORM_MANIFEST_VERSION,
        "source_id": source_id,
        **_shared_components(binding),
        "parser": {"parser_id": parser.parser_id,
                   **_component(root, parser.version, parser.modules + parser.repair_proposers)},
        "list_grammar": grammar,
        "rights": _component(root, "1", (), rights.rights_contents(root, spec.rights_class,
                                                                    spec.rights_register_ids)),
    }


def transform_digest(source_id: str, binding: TransformBinding = DEFAULT_BINDING) -> str:
    return sha256_canonical(transform_manifest(source_id, binding))


def _manifest_modules(manifest: Mapping[str, Any]) -> set[str]:
    found: set[str] = set()
    for value in manifest.values():
        if isinstance(value, Mapping):
            found.update(entry["path"] for entry in value.get("modules", ()))
    return found


def _resolve_import(root: Path, name: str) -> str | None:
    parts = name.split(".")
    if parts[0] not in PROJECT_PACKAGES:
        return None
    base = root.joinpath(*parts)
    for candidate in (base.with_suffix(".py"), base / "__init__.py"):
        if candidate.is_file():
            return candidate.relative_to(root).as_posix()
    return None


def module_imports(root: Path, rel: str) -> set[str]:
    """Project modules imported by one module (absolute and relative imports)."""
    tree = ast.parse((root / rel).read_text(encoding="utf-8"), filename=rel)
    package = rel.rsplit("/", 1)[0].replace("/", ".")
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.update(path for alias in node.names if (path := _resolve_import(root, alias.name)))
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                anchor = package.split(".")[: len(package.split(".")) - (node.level - 1)]
                module = ".".join([*anchor, *([node.module] if node.module else [])])
            else:
                module = node.module or ""
            for alias in node.names:
                # ``from pkg import name``: the submodule when one exists, else the package.
                path = _resolve_import(root, f"{module}.{alias.name}") or _resolve_import(root, module)
                if path:
                    found.add(path)
    found.discard(rel)
    # A package __init__ that holds only a docstring carries no transform code.
    return {path for path in found if not path.endswith("__init__.py") or _is_code(root / path)}


def _is_code(path: Path) -> bool:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return any(not (isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant)) for node in tree.body)


def undeclared_imports(binding: TransformBinding = DEFAULT_BINDING) -> dict[str, list[str]]:
    """Per manifest (``shared`` and each source), registered modules' unregistered imports."""
    manifests: dict[str, Mapping[str, Any]] = {"shared": _shared_components(binding)}
    for source_id in binding.sources:
        manifests[source_id] = transform_manifest(source_id, binding)
    problems: dict[str, list[str]] = {}
    for name, manifest in manifests.items():
        declared = _manifest_modules(manifest)
        missing = sorted({f"{module} imports {dep}" for module in declared
                          for dep in module_imports(binding.repo_root, module) if dep not in declared})
        if missing:
            problems[name] = missing
    return problems


def assert_registry_closed(binding: TransformBinding = DEFAULT_BINDING) -> None:
    problems = undeclared_imports(binding)
    if problems:
        raise TransformRegistryError(f"undeclared transform dependencies: {problems}")
