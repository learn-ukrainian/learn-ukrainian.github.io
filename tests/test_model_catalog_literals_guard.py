"""Pin catalog model literals by AST scope; new routing pins fail closed (#9302).

The allowlist is a reviewed inventory, never a file or scope wildcard. Migration
debt remains explicit until the owning #9302 consumer packet removes it. Counts
include model IDs embedded in docstrings, help, commands and f-string segments.
"""

from __future__ import annotations

import ast
import re
import subprocess
from collections import Counter
from copy import deepcopy
from pathlib import Path, PurePosixPath
from typing import Any

import pytest
import yaml

pytestmark = [pytest.mark.repo_invariant, pytest.mark.repo_wide]

REPO_ROOT = Path(__file__).resolve().parents[1]
FIELDS = frozenset({"path", "scope", "id", "count", "kind", "reason"})
KINDS = frozenset({"adapter_identity", "frozen_identity", "documentation", "migration_debt"})
SCOPE = re.compile(r"(?:<module>|[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*)\Z")


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
    # Generic lane aliases (e.g. pool/glm) are not model-version identities.
    return {identity for identity in identities if re.search(r"\d", identity)}


def _pattern(identities: set[str]) -> re.Pattern[str]:
    assert identities, "catalog has no model identities"
    choices = "|".join(re.escape(identity) for identity in sorted(identities, key=lambda x: (-len(x), x)))
    return re.compile(rf"(?<![\w./:-])(?:{choices})(?![\w/:-]|\.[\w])")


def _scan(root: Path, identities: set[str]) -> Counter[tuple[str, str, str]]:
    pattern = _pattern(identities)
    counts: Counter[tuple[str, str, str]] = Counter()

    class Visitor(ast.NodeVisitor):
        def __init__(self, relative: str) -> None:
            self.relative = relative
            self.scopes: list[str] = []

        def visit_Constant(self, node: ast.Constant) -> None:
            if isinstance(node.value, str):
                scope = ".".join(self.scopes) or "<module>"
                for match in pattern.finditer(node.value):
                    counts[self.relative, scope, match.group()] += 1

        def visit_FunctionDef(self, node: ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef) -> None:
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


def _allowlist(raw: Any, identities: set[str]) -> Counter[tuple[str, str, str]]:
    assert isinstance(raw, dict) and set(raw) == {"schema_version", "entries"}, "invalid allowlist document"
    assert raw["schema_version"] == "model-literals-allowlist.v1", "unsupported allowlist schema"
    assert isinstance(raw["entries"], list), "entries must be a list"
    counts: Counter[tuple[str, str, str]] = Counter()
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
        assert entry["id"] in identities, f"unknown catalog identity: {entry['id']}"
        assert type(entry["count"]) is int and entry["count"] > 0, "count must be a positive integer"
        assert entry["kind"] in KINDS, f"unknown exemption kind: {entry['kind']}"
        if entry["kind"] == "migration_debt":
            assert "#9302" in entry["reason"], "migration debt must name its owning issue"
        key = entry["path"], entry["scope"], entry["id"]
        assert key not in counts, f"duplicate exemption: {key}"
        counts[key] = entry["count"]
    return counts


def _assert_inventory(actual: Counter, allowed: Counter) -> None:
    unexempted = actual - allowed
    stale = allowed - actual
    assert not unexempted and not stale, (
        f"unexempted model literals (path, scope, id): {dict(sorted(unexempted.items()))}\n"
        f"stale or overbroad exemptions (path, scope, id): {dict(sorted(stale.items()))}"
    )


def test_scripts_model_literals_are_exactly_allowlisted() -> None:
    catalog = yaml.load((REPO_ROOT / "scripts/config/model_catalog.yaml").read_text(), Loader=_UniqueLoader)
    identities = _identities(catalog)
    raw = yaml.load((REPO_ROOT / "scripts/config/model_literals_allowlist.yaml").read_text(), Loader=_UniqueLoader)
    _assert_inventory(_scan(REPO_ROOT, identities), _allowlist(raw, identities))


def _entry(**updates: Any) -> dict[str, Any]:
    return {
        "path": "scripts/router.py",
        "scope": "route",
        "id": "gpt-99-test",
        "count": 1,
        "kind": "adapter_identity",
        "reason": "Provider wire identity for the synthetic adapter.",
        **updates,
    }


def _document(*entries: dict[str, Any]) -> dict[str, Any]:
    return {"schema_version": "model-literals-allowlist.v1", "entries": list(entries)}


def test_identity_inventory_includes_retired_and_wire_ids_but_not_lane_aliases() -> None:
    assert _identities(
        {
            "models": {
                "gpt-99-test": {
                    "lifecycle": "retired",
                    "aliases": ["test", "gpt-99-alias"],
                    "runtime_model_ids": ["gpt-99-runtime"],
                    "routing_wire_ids": {"cursor": "gpt-99-test-high"},
                }
            }
        }
    ) == {"gpt-99-test", "gpt-99-alias", "gpt-99-runtime", "gpt-99-test-high"}


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
            ("scripts/router.py", "<module>", "gpt-99-test"): 3,
            ("scripts/router.py", "route", "gpt-99-test"): 3,
            ("scripts/router.py", "route.nested", "gpt-99-test"): 1,
            ("scripts/router.py", "Adapter", "gpt-99-test-high"): 1,
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
    assert not pattern.findall("gpt-99-testing gpt-99-test-extra prefix/gpt-99-test gpt-99-test.json")


@pytest.mark.parametrize(
    "role,transport",
    [
        ("launcher_codex_default", "native_codex"),
        ("launcher_claude_default", "native_claude"),
        ("launcher_claude_driver_default", "native_claude"),
        ("launcher_grok_default", "native_grok"),
        ("launcher_cursor_default", "cursor"),
        ("launcher_gemini_default", "agy"),
    ],
)
def test_shell_launcher_defaults_resolve_active_catalog_holders(role: str, transport: str) -> None:
    from scripts.review.model_catalog import load_model_catalog, resolve_role

    catalog = load_model_catalog()
    rows = [
        row
        for row in resolve_role(role, catalog=catalog, purpose="inspect", transport=transport).candidates
        if not row.exclusion_reasons
    ]
    assert len(rows) == 1 and catalog["models"][rows[0].model_id]["lifecycle"] == "active"
    result = subprocess.run(
        [
            "bash",
            "-c",
            'source scripts/lib/launcher_roles.sh; launcher_role_model "$@"',
            "launcher-test",
            str(REPO_ROOT),
            role,
            transport,
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == rows[0].wire_id


@pytest.mark.parametrize(
    "args",
    [
        [],
        ["unknown_role"],
        ["designated_authorities"],
        ["launcher_codex_default", "cursor"],
        ["role", "transport", "extra"],
    ],
)
def test_shell_launcher_default_errors_fail_closed(args: list[str]) -> None:
    result = subprocess.run(
        [
            "bash",
            "-c",
            'source scripts/lib/launcher_roles.sh; launcher_role_model "$@"',
            "launcher-test",
            *([str(REPO_ROOT), *args] if args else []),
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        timeout=30,
    )
    assert result.returncode == 2 and not result.stdout and result.stderr


def test_launcher_role_follows_holder_rotation_without_changing_the_default() -> None:
    from scripts.review.model_catalog import CATALOG_PATH, resolve_role

    catalog = yaml.safe_load(CATALOG_PATH.read_text())
    old = catalog["seats"]["openai_frontier"]["model_id"]
    replacement = deepcopy(catalog["models"][old])
    replacement["aliases"] = []
    replacement["runtime_model_ids"] = ["gpt-99-test"]
    replacement["routing_wire_ids"] = {"native_codex": "gpt-99-test"}
    catalog["models"]["gpt-99-test"] = replacement
    catalog["seats"]["openai_frontier"]["model_id"] = "gpt-99-test"
    result = resolve_role("launcher_codex_default", catalog=catalog, purpose="inspect")
    assert [row.wire_id for row in result.candidates] == ["gpt-99-test"]
