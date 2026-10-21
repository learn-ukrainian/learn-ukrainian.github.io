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


def _entry(**updates: Any) -> dict[str, Any]:
    return {
        "path": "scripts/router.py",
        "scope": "route",
        "context": "expression",
        "id": "gpt-99-test",
        "count": 1,
        "kind": "adapter_identity",
        "reason": "Provider wire identity for the synthetic adapter.",
        **updates,
    }


def _document(*entries: dict[str, Any]) -> dict[str, Any]:
    return {"schema_version": "model-literals-allowlist.v2", "entries": list(entries)}


def test_identity_inventory_includes_retired_and_wire_ids_but_not_lane_aliases() -> None:
    assert _identities(
        {
            "models": {
                "gpt-99-test": {
                    "lifecycle": "retired",
                    "aliases": ["test", "gpt-99-alias", "pool", "glm", "gemma"],
                    "runtime_model_ids": ["gpt-99-runtime", "kimi-for-coding"],
                    "routing_wire_ids": {"cursor": "gpt-99-test-high", "opencode": "provider/coding"},
                },
                "model-without-digits": {},
            }
        }
    ) == {
        "gpt-99-test",
        "test",
        "gpt-99-alias",
        "gpt-99-runtime",
        "gpt-99-test-high",
        "kimi-for-coding",
        "provider/coding",
        "model-without-digits",
    }


def test_ast_inventory_covers_embedded_ids_fstrings_nested_scopes_and_defaults(tmp_path: Path) -> None:
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    (scripts / "router.py").write_text('''# "gpt-99-test" is a comment
"""Example: --model gpt-99-test"""
@decorator("gpt-99-test")
def route(model="gpt-99-test"):
    """gpt-99-test gpt-99-test"""
    message = f"gpt-99-test {model}"
    async def nested():
        return "gpt-99-" "test"
class Adapter:
    default = "gpt-99-test-high"
    def method(self):
        return "gpt-99-testish"
''')
    assert _scan(tmp_path, {"gpt-99-test", "gpt-99-test-high"}) == Counter(
        {
            ("scripts/router.py", "<module>", "docstring", "gpt-99-test"): 1,
            ("scripts/router.py", "<module>", "expression", "gpt-99-test"): 2,
            ("scripts/router.py", "route", "docstring", "gpt-99-test"): 2,
            ("scripts/router.py", "route", "expression", "gpt-99-test"): 1,
            ("scripts/router.py", "route.nested", "expression", "gpt-99-test"): 1,
            ("scripts/router.py", "Adapter", "expression", "gpt-99-test-high"): 1,
            ("scripts/router.py", "Adapter.method", "expression", "gpt-99-testish"): 1,
        }
    )


@pytest.mark.parametrize(
    "update",
    [
        {"path": "scripts/*.py"},
        {"path": "scripts/../router.py"},
        {"path": "/scripts/router.py"},
        {"path": "scripts//router.py"},
        {"path": "scripts/router.py\n"},
        {"scope": "*"},
        {"context": "comment"},
        {"id": "unknown-model"},
        {"count": True},
        {"count": 0},
        {"count": -1},
        {"count": "1"},
        {"kind": "routing"},
        {"reason": " "},
        {"kind": "migration_debt"},
    ],
)
def test_allowlist_rejects_broad_or_invalid_exemptions(update: dict) -> None:
    with pytest.raises(AssertionError):
        _allowlist(_document(_entry(**update)), {"gpt-99-test"})


@pytest.mark.parametrize("field", sorted(FIELDS))
def test_allowlist_requires_every_field(field: str) -> None:
    entry = _entry()
    del entry[field]
    with pytest.raises(AssertionError, match="requires exactly"):
        _allowlist(_document(entry), {"gpt-99-test"})


def test_allowlist_rejects_duplicates_extra_fields_and_unknown_schema() -> None:
    for raw in (
        _document(_entry(), _entry()),
        _document(_entry(extra="ignored")),
        {**_document(), "schema_version": "unknown"},
    ):
        with pytest.raises(AssertionError):
            _allowlist(raw, {"gpt-99-test"})
    with pytest.raises(ValueError, match="duplicate YAML key"):
        yaml.load("entries: []\nentries: []", Loader=_UniqueLoader)


@pytest.mark.parametrize("mutation", ["new_file", "new_scope", "increase", "remove"])
def test_planted_literal_and_stale_exemptions_fail(tmp_path: Path, mutation: str) -> None:
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    router = scripts / "router.py"
    original = 'def route():\n    return "gpt-99-test"\n'
    router.write_text(original)
    identities = {"gpt-99-test"}
    allowed = _allowlist(_document(_entry()), identities)
    _assert_inventory(_scan(tmp_path, identities), allowed)
    if mutation == "new_file":
        (scripts / "other.py").write_text(original)
    elif mutation == "new_scope":
        router.write_text(original.replace("route", "other"))
    elif mutation == "increase":
        router.write_text(original + '    extra = "gpt-99-test"\n')
    else:
        router.write_text("def route():\n    return None\n")
    with pytest.raises(AssertionError, match="unexempted model literals"):
        _assert_inventory(_scan(tmp_path, identities), allowed)


def test_inventory_rejects_syntax_errors_and_symlinked_sources(tmp_path: Path) -> None:
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    source = scripts / "broken.py"
    source.write_text("def broken(\n")
    with pytest.raises(SyntaxError):
        _scan(tmp_path, {"gpt-99-test"})
    source.write_text("pass\n")
    (scripts / "link.py").symlink_to(source)
    with pytest.raises(AssertionError, match="symlink"):
        _scan(tmp_path, {"gpt-99-test"})


def test_empty_source_tree_cannot_silently_pass(tmp_path: Path) -> None:
    with pytest.raises(AssertionError, match="missing"):
        _scan(tmp_path, {"gpt-99-test"})
    (tmp_path / "scripts").mkdir()
    with pytest.raises(AssertionError, match="no Python files"):
        _scan(tmp_path, {"gpt-99-test"})


def test_model_boundaries_distinguish_versions_from_sentence_punctuation() -> None:
    pattern = _pattern({"gpt-99-test", "gpt-99-test-high"})
    assert pattern.findall("gpt-99-test. 'gpt-99-test-high' --model=gpt-99-test[1m]") == [
        "gpt-99-test",
        "gpt-99-test-high",
        "gpt-99-test",
    ]
    assert pattern.findall("gpt-99-testing gpt-99-test-extra prefix-gpt-99-test gpt-99-test.json") == [
        "gpt-99-testing",
        "gpt-99-test-extra",
        "gpt-99-test.json",
    ]


@pytest.mark.parametrize(
    "literal,identity",
    [
        ("codex:gpt-6.1-sol", "gpt-6.1-sol"),
        ("xai/grok-4.7", "grok-4.7"),
        ("opencode:provider/coding", "provider/coding"),
        ("kimi-code/k3", "kimi-code/k3"),
        ("zai-coding-plan/glm-5.3", "zai-coding-plan/glm-5.3"),
    ],
)
def test_prefixed_model_ids_are_inventoried(tmp_path: Path, literal: str, identity: str) -> None:
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    (scripts / "router.py").write_text(f"MODEL = {literal!r}\n")
    actual = _scan(tmp_path, {identity, identity.split("/")[-1]})
    assert actual == Counter({("scripts/router.py", "<module>", "expression", identity): 1})
    with pytest.raises(AssertionError, match="unexempted model literals"):
        _assert_inventory(actual, Counter())


@pytest.mark.parametrize("literal", ["qwen3-max", "gpt5-codex", "gemma4", "glm54", "llama3.1", "gpt55"])
@pytest.mark.parametrize("suffix", ["", ":", "/", ":route", "/route"])
def test_digit_family_model_ids_fail_closed(tmp_path: Path, literal: str, suffix: str) -> None:
    (tmp_path / "scripts").mkdir()
    (tmp_path / "scripts/router.py").write_text(f"MODEL = {literal + suffix!r}\n")
    actual = _scan(tmp_path, {"gpt-99-test"})
    assert actual == Counter({("scripts/router.py", "<module>", "expression", literal): 1})
    with pytest.raises(AssertionError, match="unexempted model literals"):
        _assert_inventory(actual, Counter())


@pytest.mark.parametrize("suffix", [":", "/", ":route", "/route"])
def test_model_ids_before_colon_or_slash_fail_closed(tmp_path: Path, suffix: str) -> None:
    (tmp_path / "scripts").mkdir()
    (tmp_path / "scripts/router.py").write_text(f"MODEL = {'gpt-99-test' + suffix!r}\n")
    actual = _scan(tmp_path, {"gpt-99-test"})
    assert actual == Counter({("scripts/router.py", "<module>", "expression", "gpt-99-test"): 1})
    with pytest.raises(AssertionError, match="unexempted model literals"):
        _assert_inventory(actual, Counter())


def test_provider_prefix_label_cannot_hide_model_identity(tmp_path: Path) -> None:
    (tmp_path / "scripts").mkdir()
    (tmp_path / "scripts/router.py").write_text('MODEL = "kimi-code/kimi-for-coding"\n')
    identities = {"kimi-for-coding"}
    actual = _scan(tmp_path, identities)
    allowed = _allowlist(
        _document(_entry(scope="<module>", id="kimi-code", kind="non_model_label", reason="Provider prefix.")),
        identities,
    )
    assert actual == Counter(
        {
            ("scripts/router.py", "<module>", "expression", "kimi-code"): 1,
            ("scripts/router.py", "<module>", "expression", "kimi-for-coding"): 1,
        }
    )
    with pytest.raises(AssertionError, match="unexempted model literals"):
        _assert_inventory(actual, allowed)


@pytest.mark.parametrize(
    "literal,canonical",
    [
        ("claude-opus-5-6", "claude-opus-5"),
        ("gpt-7-sol", None),
        ("gemini-2.5-flash", None),
        ("GPT-6.1-Sol", "gpt-6.1-sol"),
        ("grok-4.6-tools", "grok-4.6"),
        ("glm-99-flash", "glm-5.3"),
        ("gemma-99-31b-it", "google-ais/gemma-4-31b-it"),
        ("laguna-xs-99", "poolside/laguna-xs-2.1"),
        ("kimi-k99", None),
        ("composer-99", None),
        ("deepseek-v99-pro", None),
        ("qwen-99-plus", None),
        ("llama-99-instruct", None),
        ("mistral-99-large", None),
    ],
)
def test_unknown_case_and_suffix_literals_fail_closed(tmp_path: Path, literal: str, canonical: str | None) -> None:
    catalog = yaml.safe_load((REPO_ROOT / "scripts/config/model_catalog.yaml").read_text())
    identities = _identities(catalog)
    (tmp_path / "scripts").mkdir()
    (tmp_path / "scripts/router.py").write_text(f"MODEL = {literal!r}\n")
    actual = _scan(tmp_path, identities)
    assert actual == Counter({("scripts/router.py", "<module>", "expression", literal): 1})
    assert canonical_model_id(literal, catalog) == canonical
    # Broad aliases can resolve uncatalogued tokens; exact spelling must still fail.
    # Even a known canonical ID's exemption cannot cover a different spelling.
    allowed = Counter({("scripts/router.py", "<module>", "expression", canonical): 1}) if canonical else Counter()
    with pytest.raises(AssertionError, match="unexempted model literals"):
        _assert_inventory(actual, allowed)


@pytest.mark.parametrize("scope", ["<module>", "route", "Adapter"])
def test_docstring_exemption_cannot_mask_expression(tmp_path: Path, scope: str) -> None:
    (tmp_path / "scripts").mkdir()
    source = tmp_path / "scripts/router.py"
    wrapper = {"<module>": "", "route": "def route():\n", "Adapter": "class Adapter:\n"}[scope]
    indent = "    " if wrapper else ""
    source.write_text(wrapper + indent + '"""gpt-99-test"""\n')
    identities = {"gpt-99-test"}
    allowed = _allowlist(_document(_entry(scope=scope, context="docstring", kind="documentation")), identities)
    _assert_inventory(_scan(tmp_path, identities), allowed)
    source.write_text(wrapper + indent + 'MODEL = "gpt-99-test"\n')
    with pytest.raises(AssertionError, match="unexempted model literals"):
        _assert_inventory(_scan(tmp_path, identities), allowed)


def test_variants_resolve_but_allowlist_keeps_exact_spelling() -> None:
    catalog = yaml.safe_load((REPO_ROOT / "scripts/config/model_catalog.yaml").read_text())
    for literal in ("GPT-6.1-Sol", "grok-4.6-tools"):
        allowed = _allowlist(_document(_entry(id=literal)), _identities(catalog), catalog)
        assert allowed == Counter({("scripts/router.py", "route", "expression", literal): 1})


@pytest.mark.parametrize("kind", ["uncatalogued_identity", "documentation", "non_model_label"])
def test_uncatalogued_tokens_require_precise_kinds(kind: str) -> None:
    allowed = _allowlist(_document(_entry(id="claude-future-label", kind=kind)), {"gpt-99-test"})
    assert allowed == Counter({("scripts/router.py", "route", "expression", "claude-future-label"): 1})
    with pytest.raises(AssertionError, match="precise exemption kind"):
        _allowlist(_document(_entry(id="claude-future-label")), {"gpt-99-test"})
