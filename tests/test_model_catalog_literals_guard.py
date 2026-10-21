"""Pin catalog model literals by AST scope; new routing pins fail closed (#9302).

The allowlist is a reviewed inventory, never a file or scope wildcard. Migration
debt remains explicit until the owning #9302 consumer packet removes it. Counts
include model-shaped tokens embedded in docstrings, help, commands and f-string
segments. Exact context and spelling prevent documentation/variant exemptions
from covering executable routing pins. Comments are not string literals.
"""

from __future__ import annotations

import ast
import re
from collections import Counter
from pathlib import Path, PurePosixPath
from typing import Any

import pytest
import yaml

from scripts.review.model_catalog import canonical_model_id

pytestmark = [pytest.mark.repo_invariant, pytest.mark.repo_wide]

REPO_ROOT = Path(__file__).resolve().parents[1]
FIELDS = frozenset({"path", "scope", "context", "id", "count", "kind", "reason"})
KINDS = frozenset(
    {
        "adapter_identity",
        "frozen_identity",
        "documentation",
        "migration_debt",
        "uncatalogued_identity",
        "non_model_label",
    }
)
CONTEXTS = frozenset({"docstring", "expression"})
# Broad shapes catch future/retired IDs independently of the current catalog.
MODEL_SHAPE = (
    r"(?:gpt|claude|gemini|grok|glm|gemma|laguna|kimi|composer|deepseek|qwen|llama|mistral)"
    r"(?:-[a-z0-9]|[0-9])(?:[a-z0-9.\-]*[a-z0-9])?"
)
SCOPE = re.compile(r"(?:<module>|[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*)\Z")
GENERIC_LANE_ALIASES = frozenset({"pool", "glm", "gemma"})


class _UniqueLoader(yaml.SafeLoader):
    """Reject duplicate YAML keys rather than silently overwriting an exemption."""


def _unique_mapping(loader: _UniqueLoader, node: yaml.MappingNode) -> dict:
    result = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node)
        if not isinstance(key, str) or key in result:
            raise ValueError(f"non-string or duplicate YAML key: {key!r}")
        result[key] = loader.construct_object(value_node)
    return result


_UniqueLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _unique_mapping)


def _identities(catalog: dict[str, Any]) -> set[str]:
    identities = set(catalog["models"])
    for model in catalog["models"].values():
        identities.update(model.get("aliases", []))
        identities.update(model.get("runtime_model_ids", []))
        identities.update(model.get("routing_wire_ids", {}).values())
    return identities - GENERIC_LANE_ALIASES


def _pattern(identities: set[str]) -> re.Pattern[str]:
    assert identities, "catalog has no model identities"
    choices = "|".join(re.escape(identity) for identity in sorted(identities, key=lambda x: (-len(x), x)))
    # Preserve complete catalog wire IDs before scanning slash-delimited shapes.
    return re.compile(
        rf"(?<![\w.-])(?:{choices}|{MODEL_SHAPE})(?![\w-]|\.[\w])",
        re.IGNORECASE,
    )


def _scan(root: Path, identities: set[str]) -> Counter[tuple[str, str, str, str]]:
    pattern = _pattern(identities)
    counts: Counter[tuple[str, str, str, str]] = Counter()

    class Visitor(ast.NodeVisitor):
        def __init__(self, relative: str) -> None:
            self.relative = relative
            self.scopes: list[str] = []
            self.docstrings: set[int] = set()

        def mark_docstring(self, node: ast.Module | ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef) -> None:
            if node.body and isinstance(node.body[0], ast.Expr):
                value = node.body[0].value
                if isinstance(value, ast.Constant) and isinstance(value.value, str):
                    self.docstrings.add(id(value))

        def visit_Module(self, node: ast.Module) -> None:
            self.mark_docstring(node)
            self.generic_visit(node)

        def visit_Constant(self, node: ast.Constant) -> None:
            if isinstance(node.value, str):
                scope = ".".join(self.scopes) or "<module>"
                for match in pattern.finditer(node.value):
                    context = "docstring" if id(node) in self.docstrings else "expression"
                    counts[self.relative, scope, context, match.group()] += 1

        def visit_FunctionDef(self, node: ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef) -> None:
            self.mark_docstring(node)
            # Decorators, annotations and defaults execute in the enclosing scope.
            for field, value in ast.iter_fields(node):
                if field != "body":
                    for child in value if isinstance(value, list) else [value]:
                        if isinstance(child, ast.AST):
                            self.visit(child)
            self.scopes.append(node.name)
            for child in node.body:
                self.visit(child)
            self.scopes.pop()

        visit_AsyncFunctionDef = visit_FunctionDef
        visit_ClassDef = visit_FunctionDef

    scripts = root / "scripts"
    assert scripts.is_dir() and not scripts.is_symlink(), "scripts source tree is missing or symlinked"
    paths = sorted(scripts.rglob("*.py"))
    assert paths, "scripts source tree contains no Python files"
    for path in paths:
        assert not path.is_symlink(), f"cannot inventory symlink: {path.relative_to(root)}"
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        Visitor(path.relative_to(root).as_posix()).visit(tree)
    return counts


def _allowlist(
    raw: Any, identities: set[str], catalog: dict[str, Any] | None = None
) -> Counter[tuple[str, str, str, str]]:
    assert isinstance(raw, dict) and set(raw) == {"schema_version", "entries"}, "invalid allowlist document"
    assert raw["schema_version"] == "model-literals-allowlist.v2", "unsupported allowlist schema"
    assert isinstance(raw["entries"], list), "entries must be a list"
    counts: Counter[tuple[str, str, str, str]] = Counter()
    pattern = _pattern(identities)
    source = catalog if catalog is not None else {"models": {model: {} for model in identities}}
    for entry in raw["entries"]:
        assert isinstance(entry, dict) and set(entry) == FIELDS, f"entry requires exactly {sorted(FIELDS)}: {entry!r}"
        for field in FIELDS - {"count"}:
            assert isinstance(entry[field], str) and entry[field].strip() == entry[field] and entry[field], (
                f"invalid {field}"
            )
        path = PurePosixPath(entry["path"])
        assert (
            path.as_posix() == entry["path"]
            and not path.is_absolute()
            and len(path.parts) >= 2
            and path.parts[0] == "scripts"
            and path.suffix == ".py"
            and all(part not in {".", ".."} for part in path.parts)
            and not any(char in entry["path"] for char in "*?[]\\")
            and all(char.isprintable() for char in entry["path"])
        ), f"path must name one scripts Python file: {entry['path']!r}"
        assert SCOPE.fullmatch(entry["scope"]), "scope must be an exact AST scope"
        assert entry["context"] in CONTEXTS, "context must be docstring or expression"
        assert pattern.fullmatch(entry["id"]), f"invalid model token: {entry['id']}"
        canonical = canonical_model_id(entry["id"], source)
        if entry["id"] not in identities and canonical is None:
            assert entry["kind"] in {"uncatalogued_identity", "documentation", "non_model_label"}, (
                f"uncatalogued token requires a precise exemption kind: {entry['id']}"
            )
        assert type(entry["count"]) is int and entry["count"] > 0, "count must be a positive integer"
        assert entry["kind"] in KINDS, f"unknown exemption kind: {entry['kind']}"
        if entry["kind"] == "migration_debt":
            assert "#9302" in entry["reason"], "migration debt must name its owning issue"
        key = entry["path"], entry["scope"], entry["context"], entry["id"]
        assert key not in counts, f"duplicate exemption: {key}"
        counts[key] = entry["count"]
    return counts


def _assert_inventory(actual: Counter, allowed: Counter) -> None:
    unexempted = actual - allowed
    stale = allowed - actual
    assert not unexempted and not stale, (
        f"unexempted model literals (path, scope, context, id): {dict(sorted(unexempted.items()))}\n"
        f"stale or overbroad exemptions (path, scope, context, id): {dict(sorted(stale.items()))}"
    )


def test_scripts_model_literals_are_exactly_allowlisted() -> None:
    catalog = yaml.load((REPO_ROOT / "scripts/config/model_catalog.yaml").read_text(), Loader=_UniqueLoader)
    identities = _identities(catalog)
    raw = yaml.load((REPO_ROOT / "scripts/config/model_literals_allowlist.yaml").read_text(), Loader=_UniqueLoader)
    _assert_inventory(_scan(REPO_ROOT, identities), _allowlist(raw, identities, catalog))
