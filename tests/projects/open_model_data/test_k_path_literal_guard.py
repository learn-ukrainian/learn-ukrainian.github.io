"""Guard production K-path literals so defaults cannot point at moved files.

A string literal under ``data/projects/open_model_data/`` that names a
classification-table K file or a K-only directory must be an argument of
``resolve_open_model_path`` (or the registry-backed helpers ``_bound_path``,
``_physical_k_path``, and ``source_asset``). Frozen logical keys from
Decisions G and H, directory-prefix queries, and packaged v4-runtime resource
names stay as the pre-migration ``data/`` string. Package resource joins must
use the runtime's ``resource_root()``; joins onto filesystem roots fail.
"""

from __future__ import annotations

import ast
import csv
import re
from pathlib import Path

import pytest

MARKER = "data/projects/open_model_data/"
REVIEW_PREFIX = "components/decolonization/reviews/"
RESOLVERS = frozenset({"resolve_open_model_path", "_bound_path", "_physical_k_path", "source_asset"})
REPO_ROOT = Path(__file__).resolve().parents[3]

FROZEN_LOGICAL_KEYS = frozenset(
    {
        "admission/phase3_p4_pilot_construction_v1.json",
        "contracts/correction_protection_coverage_contract_v1.schema.json",
        "contracts/correction_protection_evaluation_contract_v1.schema.json",
        "contracts/phase3_audit_entropy_receipt_v1.schema.json",
        "contracts/phase3_cycle_void_receipt_v1.schema.json",
        "contracts/phase3_disposition_audit_bundle_v1.schema.json",
        "contracts/phase3_evaluation_freeze_bundle_v1.schema.json",
        "contracts/phase3_evaluation_reproduction_bundle_v1.schema.json",
        "contracts/phase3_fixed_release_manifest_v1.schema.json",
        "contracts/phase3_heldout_clean_modern_label_prompt_v1.md",
        "contracts/phase3_heldout_label_transport_bundle_v1.schema.json",
        "contracts/phase3_heldout_partition_bundle_v1.schema.json",
        "contracts/phase3_heldout_semantic_gold_label_prompt_v1.md",
        "contracts/phase3_historical_document_chronology_receipt_v2.schema.json",
        "contracts/phase3_lavra_near_caves_intake_receipt_v1.schema.json",
        "contracts/phase3_p4_pilot_construction_v1.schema.json",
        "contracts/phase3_pravopys_delta_bundle_v1.schema.json",
        "contracts/phase3_rule_author_packet_bundle_v1.schema.json",
        "contracts/phase3_rule_author_run_manifest_v1.schema.json",
        "contracts/phase3_rule_author_source_rows_v1.schema.json",
        "contracts/phase3_source_author_prompt_v1.md",
        "contracts/phase3_source_disposition_input_v1.schema.json",
        "contracts/phase3_source_production_transport_v1.schema.json",
        "contracts/phase3_source_review_prompt_v1.md",
        "contracts/phase3_source_unit_materialization_receipt_v1.schema.json",
        "contracts/phase3_source_universe_freeze_v1.schema.json",
        "contracts/phase3_spas_catalog_materialization_receipt_v1.schema.json",
        "contracts/phase3_spas_glyph_adapter_receipt_v1.schema.json",
        "contracts/phase3_spas_layout_candidate_receipt_v1.schema.json",
        "contracts/phase3_spas_source_attribution_receipt_v1.schema.json",
        "contracts/phase3_textbook_nonhit_bundle_v1.schema.json",
        "contracts/phase3_v3_cooperative_control_plane_v1.schema.json",
        "dataset/v4_human_source_dataset_manifest_v1.json",
        "dataset/v4_human_source_dataset_receipt_v1.json",
        "detector/correction_protection_known_answers_v1.json",
        "evidence/correction_protection_bundle_manifest_v1.json",
        "evidence/correction_protection_evaluation_contract_v1.json",
        "evidence/correction_protection_evaluation_contract_v2_2.json",
        "evidence/correction_protection_functional_role_contract_v2_1.json",
        "evidence/correction_protection_functional_role_contract_v2_2.json",
        "evidence/correction_protection_near_duplicate_policy_v1.json",
        "evidence/correction_protection_release_receipt_v1.json",
        "evidence/phase3_cycle001_void_receipt_v1.json",
        "evidence/phase3_heldout_label_public_receipt_v1.json",
        "evidence/phase3_p1_dialect_regional_protection_amendment_v1.json",
        "evidence/phase3_p1_universe_freeze_v1.json",
        "evidence/phase3_p2_canonical_contracts_v1.json",
        "evidence/phase3_scope_circularity_firewall_v1.json",
        "evidence/phase3_university_source_policy_v1.json",
        "evidence/phase3_v2_compatibility_matrix_v1.json",
        "evidence/phase3_v3_cooperative_control_plane_v1.json",
        "extraction/v4_native_extraction_config_v1.json",
        "language/v4_language_usage_config_v1.json",
        "pilot/v4_human_source_pilot_manifest_v1.json",
        "pilot/v4_human_source_pilot_quality_assessment_v1.json",
        "splits/v4_work_grouping_split_config_v1.json",
        "splits/v4_work_grouping_split_receipt_v1.json",
        "treatments/gemma4_it_l40s_hf_jobs_probe_plan_v1.json",
        "treatments/gemma4_it_model_snapshot_manifest_v1.json",
    }
)

DIRECTORY_PREFIXES = frozenset(
    {
        "adjudication",
        "admission",
        "contracts",
        "delivery",
        "examples",
        "integrations",
        "model_views",
        "silver",
        "treatments",
        "trust",
    }
)

PACKAGED_RESOURCE_PATHS = frozenset(
    {
        "admission",
        "admission/dataset_v4_a10_pilot_review_gate_receipt_v1.json",
        "admission/dataset_v4_a11_silver_release_gate_receipt_v1.json",
        "admission/dataset_v4_a12_gold_overlay_gate_receipt_v1.json",
        "admission/dataset_v4_a2_source_operation_admission_receipt_v1.json",
        "admission/dataset_v4_a3_builder_packet_receipt_v1.json",
        "admission/dataset_v4_a3_heldout_source_family_seal_receipt_v1.json",
        "admission/dataset_v4_a4_deterministic_extraction_receipt_v1.json",
        "admission/dataset_v4_a5_evidence_enrichment_receipt_v1.json",
        "admission/dataset_v4_a9_evaluation_package_receipt_v1.json",
        "admission/dataset_v4_pilot_slot_manifest_v1.json",
        "contracts",
        "contracts/dataset_v4_a3_builder_packet_receipt_v1.schema.json",
        "contracts/dataset_v4_a3_heldout_source_family_seal_receipt_v1.schema.json",
        "evidence/correction_protection_near_duplicate_policy_v1.json",
        "trust/v4_child_profile_v3.json",
        "trust/v4_review_rubric_v2.txt",
        "trust/v4_trust_policy_v2.json",
    }
)


def _classes() -> dict[str, str]:
    table = REPO_ROOT / "registry/artifacts/classification-v1.tsv"
    classes: dict[str, str] = {}
    with table.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            logical = row.get("path", "")
            if logical.startswith(MARKER) and row.get("class") in {"K", "A"}:
                classes[logical[len(MARKER) :]] = row["class"]
    return classes


def _kind(relative: str, classes: dict[str, str]) -> tuple[str, str | None]:
    relative = relative.strip("/")
    if not relative:
        return "ROOT", None
    found = classes.get(relative)
    if found is not None:
        return "FILE", found
    prefix = relative + "/"
    child_classes = {classes[item] for item in classes if item.startswith(prefix)}
    if not child_classes:
        return "UNKNOWN", None
    if child_classes == {"K"}:
        return "DIR", "K"
    if child_classes == {"A"}:
        return "DIR", "A"
    return "DIR", "MIXED"


def _call_name(node: ast.AST) -> str | None:
    func = getattr(node, "func", None)
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return None


def _path_join_aliases(tree: ast.Module) -> tuple[set[str], set[str], set[str]]:
    """Resolve the imported spellings of os.path/posixpath.join in this module."""
    os_names = {"os"}
    path_names = {"posixpath"}
    join_names: set[str] = set()
    for statement in tree.body:
        if isinstance(statement, ast.Import):
            for alias in statement.names:
                if alias.name == "os":
                    os_names.add(alias.asname or "os")
                elif alias.name == "os.path":
                    if alias.asname:
                        path_names.add(alias.asname)
                    else:
                        os_names.add("os")
                elif alias.name == "posixpath":
                    path_names.add(alias.asname or "posixpath")
        elif isinstance(statement, ast.ImportFrom) and statement.module in {"os.path", "posixpath"}:
            join_names.update(alias.asname or alias.name for alias in statement.names if alias.name == "join")
        elif isinstance(statement, ast.ImportFrom) and statement.module == "os":
            path_names.update(alias.asname or alias.name for alias in statement.names if alias.name == "path")
    return os_names, path_names, join_names


def _is_join_call(func: ast.AST, aliases: tuple[set[str], set[str], set[str]]) -> bool:
    os_names, path_names, join_names = aliases
    if isinstance(func, ast.Name):
        return func.id in join_names
    if not isinstance(func, ast.Attribute) or func.attr != "join":
        return False
    value = func.value
    if isinstance(value, ast.Name):
        return value.id in path_names
    return (
        isinstance(value, ast.Attribute)
        and value.attr == "path"
        and isinstance(value.value, ast.Name)
        and value.value.id in os_names
    )


def _is_path_join(
    node: ast.AST, parents: dict[ast.AST, ast.AST], aliases: tuple[set[str], set[str], set[str]]
) -> bool:
    """Recognize joins around a literal, including a root embedded in an f-string."""
    child = node
    while child is not None:
        if isinstance(child, ast.BinOp) and isinstance(child.op, (ast.Div, ast.Add)):
            return True
        if isinstance(child, ast.Call):
            if _call_name(child) in {"Path", "PurePath"} and len(child.args) > 1:
                return True
            if _is_join_call(child.func, aliases) and len(child.args) > 1:
                return True
            if isinstance(child.func, ast.Attribute) and child.func.attr == "joinpath" and child.args:
                return True
        if isinstance(child, ast.JoinedStr):
            for index, part in enumerate(child.values):
                if not isinstance(part, ast.Constant) or not isinstance(part.value, str) or MARKER not in part.value:
                    continue
                before_marker = part.value.split(MARKER, 1)[0]
                if before_marker.endswith("/") and any(
                    isinstance(previous, ast.FormattedValue) for previous in child.values[:index]
                ):
                    return True
                if part.value.endswith("/") and any(
                    isinstance(following, ast.FormattedValue) for following in child.values[index + 1 :]
                ):
                    return True
        child = parents.get(child)
    return False


def _resource_root_names(tree: ast.Module) -> tuple[set[str], set[str]]:
    """Names bound at module scope to the package resource root."""
    imports = {
        alias.asname or alias.name
        for statement in tree.body
        if isinstance(statement, ast.ImportFrom) and statement.module == "learn_ukrainian_v4_runtime.resources"
        for alias in statement.names
        if alias.name == "resource_root"
    }
    heldout_source = REPO_ROOT / "packages/v4-runtime/src/learn_ukrainian_v4_runtime/v4_a3_heldout_family_assignment.py"
    heldout_tree = ast.parse(heldout_source.read_text(encoding="utf-8"))
    heldout_root_is_resource = any(
        isinstance(statement, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == "ROOT" for target in statement.targets)
        and isinstance(statement.value, ast.Call)
        and isinstance(statement.value.func, ast.Name)
        and statement.value.func.id == "resource_root"
        and not statement.value.args
        and not statement.value.keywords
        for statement in heldout_tree.body
    ) and any(
        isinstance(statement, ast.ImportFrom)
        and statement.module == "learn_ukrainian_v4_runtime.resources"
        and any(alias.name == "resource_root" for alias in statement.names)
        for statement in heldout_tree.body
    )
    heldout_imports = {
        alias.asname or alias.name
        for statement in tree.body
        if isinstance(statement, ast.ImportFrom) and statement.module == "learn_ukrainian_v4_runtime"
        for alias in statement.names
        if alias.name == "v4_a3_heldout_family_assignment" and heldout_root_is_resource
    }
    names: set[str] = set()
    for statement in tree.body:
        if not isinstance(statement, (ast.Assign, ast.AnnAssign)):
            continue
        value = statement.value
        if value is None:
            continue
        direct = (
            isinstance(value, ast.Call)
            and isinstance(value.func, ast.Name)
            and value.func.id in imports
            and not value.args
            and not value.keywords
        )
        alias = isinstance(value, ast.Name) and value.id in names
        # heldout.ROOT is defined by resource_root() in the packaged runtime.
        inherited = (
            isinstance(value, ast.Attribute)
            and value.attr == "ROOT"
            and isinstance(value.value, ast.Name)
            and value.value.id in heldout_imports
        )
        targets = statement.targets if isinstance(statement, ast.Assign) else [statement.target]
        for target in targets:
            if isinstance(target, ast.Name):
                if direct or alias or inherited:
                    names.add(target.id)
                else:
                    names.discard(target.id)
                imports.discard(target.id)
    return names, imports


def _local_bindings(function: ast.FunctionDef | ast.AsyncFunctionDef) -> set[str]:
    """Names assigned in a function body, excluding bodies of nested scopes."""
    bound: set[str] = set()

    class Bindings(ast.NodeVisitor):
        def visit_Name(self, node: ast.Name) -> None:
            if isinstance(node.ctx, ast.Store):
                bound.add(node.id)

        def visit_Import(self, node: ast.Import) -> None:
            bound.update(alias.asname or alias.name.split(".", 1)[0] for alias in node.names)

        def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
            bound.update(alias.asname or alias.name for alias in node.names)

        def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
            bound.add(node.name)

        def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
            bound.add(node.name)

        def visit_ClassDef(self, node: ast.ClassDef) -> None:
            bound.add(node.name)

        def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
            if node.name:
                bound.add(node.name)
            self.generic_visit(node)

    visitor = Bindings()
    for statement in function.body:
        visitor.visit(statement)
    return bound


def _resource_root_join(
    node: ast.AST,
    parents: dict[ast.AST, ast.AST],
    names: set[str],
    imports: set[str],
    aliases: tuple[set[str], set[str], set[str]],
) -> bool:
    """Accept only a join rooted in the runtime's package resource namespace."""
    functions = [
        ancestor
        for ancestor in _ancestors(node, parents)
        if isinstance(ancestor, (ast.FunctionDef, ast.AsyncFunctionDef))
    ]
    for function in reversed(functions):
        args = function.args.posonlyargs + function.args.args
        parameters = {arg.arg for arg in args + function.args.kwonlyargs}
        if function.args.vararg:
            parameters.add(function.args.vararg.arg)
        if function.args.kwarg:
            parameters.add(function.args.kwarg.arg)
        bound = _local_bindings(function)
        inherited_defaults = {
            arg.arg
            for arg, default in zip(args[-len(function.args.defaults) :], function.args.defaults, strict=False)
            if isinstance(default, ast.Name) and default.id in names and arg.arg not in bound
        }
        names = (names - bound - parameters) | inherited_defaults
        imports = imports - bound - parameters

    def is_root(expr: ast.AST) -> bool:
        if isinstance(expr, ast.Name):
            return expr.id in names
        if isinstance(expr, ast.Call) and isinstance(expr.func, ast.Name):
            return expr.func.id in imports and not expr.args and not expr.keywords
        if isinstance(expr, ast.BinOp) and isinstance(expr.op, ast.Add):
            return is_root(expr.left) and isinstance(expr.right, ast.Constant) and expr.right.value == "/"
        return False

    child = node
    for parent in _ancestors(node, parents):
        if isinstance(parent, ast.BinOp) and isinstance(parent.op, (ast.Div, ast.Add)) and child is parent.right:
            return is_root(parent.left)
        if isinstance(parent, ast.Call) and child in parent.args[1:]:
            if _call_name(parent) in {"Path", "PurePath"} and is_root(parent.args[0]):
                return True
            if _is_join_call(parent.func, aliases) and is_root(parent.args[0]):
                return True
            if (
                isinstance(parent.func, ast.Attribute)
                and parent.func.attr == "joinpath"
                and isinstance(parent.func.value, ast.Name)
                and parent.func.value.id in {"Path", "PurePath"}
                and is_root(parent.args[0])
            ):
                return True
        if (
            isinstance(parent, ast.Call)
            and isinstance(parent.func, ast.Attribute)
            and parent.func.attr == "joinpath"
            and child in parent.args
            and is_root(parent.func.value)
        ):
            return True
        if isinstance(parent, ast.JoinedStr):
            for index, part in enumerate(parent.values):
                if part is child and index > 0 and isinstance(part, ast.Constant) and isinstance(part.value, str):
                    previous = parent.values[index - 1]
                    if part.value.startswith("/") and isinstance(previous, ast.FormattedValue):
                        return is_root(previous.value)
        child = parent
    return False


def _ancestors(node: ast.AST, parents: dict[ast.AST, ast.AST]):
    while node in parents:
        node = parents[node]
        yield node


def _literal_hits(source: str) -> list[dict[str, object]]:
    tree = ast.parse(source)
    parents: dict[ast.AST, ast.AST] = {}
    for parent in ast.walk(tree):
        for child in ast.iter_child_nodes(parent):
            parents[child] = parent
    resource_names, resource_imports = _resource_root_names(tree)
    join_aliases = _path_join_aliases(tree)
    classes = _classes()
    hits: list[dict[str, object]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            if isinstance(parents.get(node), ast.JoinedStr):
                continue
            chunk = node.value
        elif isinstance(node, ast.JoinedStr):
            chunk = "".join(
                part.value for part in node.values if isinstance(part, ast.Constant) and isinstance(part.value, str)
            )
        else:
            continue
        if MARKER not in chunk:
            continue
        ancestor = parents.get(node)
        via_resolver = False
        seen: set[int] = set()
        while ancestor is not None and id(ancestor) not in seen:
            seen.add(id(ancestor))
            if isinstance(ancestor, ast.Call) and _call_name(ancestor) in RESOLVERS:
                via_resolver = True
                break
            ancestor = parents.get(ancestor)
        is_join = _is_path_join(node, parents, join_aliases)
        resource_join = is_join and _resource_root_join(node, parents, resource_names, resource_imports, join_aliases)
        dict_key = None
        dict_parent = parents.get(node)
        if isinstance(dict_parent, ast.Dict):
            for key, value in zip(dict_parent.keys, dict_parent.values, strict=False):
                if value is node and isinstance(key, ast.Constant) and isinstance(key.value, str):
                    dict_key = key.value
        index = 0
        while True:
            found = chunk.find(MARKER, index)
            if found < 0:
                break
            match = re.match(r"[A-Za-z0-9_.+/-]*", chunk[found + len(MARKER) :])
            relative = (match.group(0) if match else "").strip("/")
            kind, klass = _kind(relative, classes)
            if klass == "K":
                hits.append(
                    {
                        "line": node.lineno,
                        "kind": kind,
                        "relative": relative,
                        "via_resolver": via_resolver,
                        "join": is_join,
                        "resource_join": resource_join,
                        "key": dict_key,
                    }
                )
            index = found + len(MARKER)
    return hits


def _disposition(hit: dict[str, object], *, packaged: bool) -> str:
    relative = str(hit["relative"])
    if hit["join"] and not (packaged and hit["resource_join"] and relative in PACKAGED_RESOURCE_PATHS):
        return "violation"
    if hit["via_resolver"]:
        return "resolver"
    review = (
        hit["kind"] == "FILE"
        and hit["key"] == "review_dossier_locator"
        and relative.startswith(REVIEW_PREFIX)
        and relative.endswith(".review.json")
    )
    if review:
        return "review-locator"
    if packaged and relative in PACKAGED_RESOURCE_PATHS:
        return "packaged-resource"
    if hit["kind"] == "DIR" and relative in DIRECTORY_PREFIXES:
        return "directory-prefix"
    if hit["kind"] == "FILE" and relative in FROZEN_LOGICAL_KEYS:
        return "frozen-logical-key"
    return "violation"


def _production_sources() -> list[Path]:
    found: list[Path] = []
    for base in ("scripts", "packages"):
        for path in (REPO_ROOT / base).rglob("*.py"):
            if any(
                part in {".venv", "node_modules", "__pycache__", ".pytest-tmp", "build", "tests"} for part in path.parts
            ):
                continue
            found.append(path)
    return found


@pytest.mark.repo_wide
def test_k_path_literals_are_resolved_or_allowlisted() -> None:
    """Production K literals go through the resolver, or an explicit allowlist."""
    violations: list[str] = []
    observed_frozen: set[str] = set()
    observed_directories: set[str] = set()
    observed_packaged: set[str] = set()
    review_hits = 0
    for path in _production_sources():
        text = path.read_text(encoding="utf-8")
        if MARKER not in text:
            continue
        packaged = "packages" in path.relative_to(REPO_ROOT).parts
        for hit in _literal_hits(text):
            disposition = _disposition(hit, packaged=packaged)
            relative = str(hit["relative"])
            if disposition == "violation":
                violations.append(f"{path.relative_to(REPO_ROOT)}:{hit['line']} {hit['kind']} {relative}")
            elif disposition == "frozen-logical-key":
                observed_frozen.add(relative)
            elif disposition == "directory-prefix":
                observed_directories.add(relative)
            elif disposition == "packaged-resource":
                observed_packaged.add(relative)
            elif disposition == "review-locator":
                review_hits += 1
    assert violations == []
    assert observed_frozen == set(FROZEN_LOGICAL_KEYS)
    assert observed_directories == set(DIRECTORY_PREFIXES)
    assert observed_packaged == set(PACKAGED_RESOURCE_PATHS)
    assert review_hits >= 1


def test_guard_rejects_eager_join_and_accepts_resolver() -> None:
    """The allowlist does not excuse a script that joins a K literal onto a root."""
    logical = "data/projects/open_model_data/inventory/existing_asset_inventory_v1.schema.json"
    joined = _disposition(
        _literal_hits(f'ROOT / "{logical}"\n')[0],
        packaged=False,
    )
    resolved = _disposition(
        _literal_hits(f'resolve_open_model_path("{logical}")\n')[0],
        packaged=False,
    )
    assert joined == "violation"
    assert resolved == "resolver"


def test_guard_keeps_review_locator_and_rejects_other_uses() -> None:
    logical = "data/projects/open_model_data/components/decolonization/reviews/decol_lex_001.review.json"
    locator = _disposition(
        _literal_hits('{"review_dossier_locator": "' + logical + '"}\n')[0],
        packaged=False,
    )
    bare = _disposition(_literal_hits(f'PATH = "{logical}"\n')[0], packaged=False)
    assert locator == "review-locator"
    assert bare == "violation"


@pytest.mark.parametrize(
    ("allowed", "logical", "packaged"),
    [
        (
            "review-locator",
            "data/projects/open_model_data/components/decolonization/reviews/decol_lex_001.review.json",
            False,
        ),
        (
            "packaged-resource",
            "data/projects/open_model_data/admission/dataset_v4_a10_pilot_review_gate_receipt_v1.json",
            True,
        ),
        ("directory-prefix", "data/projects/open_model_data/admission", False),
        (
            "frozen-logical-key",
            "data/projects/open_model_data/contracts/phase3_audit_entropy_receipt_v1.schema.json",
            False,
        ),
    ],
)
@pytest.mark.parametrize("idiom", ["slash", "path_call", "pure_path_call", "os_join", "add", "f_string"])
def test_allowlisted_k_literal_join_is_a_violation(allowed: str, logical: str, packaged: bool, idiom: str) -> None:
    expressions = {
        "slash": f'ROOT / "{logical}"',
        "path_call": f'Path(ROOT, "{logical}")',
        "pure_path_call": f'PurePath(ROOT, "{logical}")',
        "os_join": f'os.path.join(ROOT, "{logical}")',
        "add": f'ROOT + "/" + "{logical}"',
        "f_string": f'Path(f"{{ROOT}}/{logical}")',
    }
    bare = f'{{"review_dossier_locator": "{logical}"}}' if allowed == "review-locator" else f'"{logical}"'
    assert _disposition(_literal_hits(bare)[0], packaged=packaged) == allowed

    hit = _literal_hits(expressions[idiom])[0]
    assert hit["join"] is True
    assert _disposition(hit, packaged=packaged) == "violation"


def test_logical_key_resolver_and_log_message_stay_allowed() -> None:
    logical = "data/projects/open_model_data/contracts/phase3_audit_entropy_receipt_v1.schema.json"
    resolved = _literal_hits(f'resolve_open_model_path("{logical}")')[0]
    logged = _literal_hits(f'logger.info("{logical}")')[0]
    assert _disposition(resolved, packaged=False) == "resolver"
    assert _disposition(logged, packaged=False) == "frozen-logical-key"


@pytest.mark.parametrize(
    "expression",
    [
        'resource_root() / "{logical}"',
        'ROOT / "{logical}"',
        'def load(root: Path = ROOT):\n    return root / "{logical}"',
    ],
)
def test_packaged_resource_join_uses_package_root(expression: str) -> None:
    logical = "data/projects/open_model_data/trust/v4_child_profile_v3.json"
    source = (
        "from learn_ukrainian_v4_runtime.resources import resource_root\n"
        "ROOT = resource_root()\n" + expression.format(logical=logical)
    )
    hit = _literal_hits(source)[0]
    assert hit["join"] is True
    assert hit["resource_join"] is True
    assert _disposition(hit, packaged=True) == "packaged-resource"


@pytest.mark.parametrize(
    "root_assignment",
    [
        "REPO_ROOT = Path(__file__).resolve().parents[3]",
        'REPO_ROOT = Path(".")',
        'REPO_ROOT = Path(os.environ["REPO_ROOT"])',
    ],
)
def test_packaged_resource_join_on_other_root_is_a_violation(root_assignment: str) -> None:
    logical = "data/projects/open_model_data/trust/v4_child_profile_v3.json"
    source = (
        "from learn_ukrainian_v4_runtime.resources import resource_root\n"
        "ROOT = resource_root()\n"
        f'{root_assignment}\nREPO_ROOT / "{logical}"'
    )
    hit = _literal_hits(source)[0]
    assert hit["join"] is True
    assert hit["resource_join"] is False
    assert _disposition(hit, packaged=True) == "violation"


def test_packaged_resource_join_rejects_rebound_and_parameter_roots() -> None:
    logical = "data/projects/open_model_data/trust/v4_child_profile_v3.json"
    source = (
        "from learn_ukrainian_v4_runtime.resources import resource_root\n"
        "ROOT = resource_root()\n"
        'ROOT = Path(".")\n'
        f'ROOT / "{logical}"\n'
        f'def load(root: Path = Path(".")):\n    return root / "{logical}"'
    )
    for hit in _literal_hits(source):
        assert hit["resource_join"] is False
        assert _disposition(hit, packaged=True) == "violation"


@pytest.mark.parametrize(
    ("import_line", "expression"),
    [
        ("import os.path as p", "p.join(REPO_ROOT, '{logical}')"),
        ("from os.path import join", "join(REPO_ROOT, '{logical}')"),
        ("import os as o", "o.path.join(REPO_ROOT, '{logical}')"),
        ("import posixpath", "posixpath.join(REPO_ROOT, '{logical}')"),
        ("import posixpath as p", "p.join(REPO_ROOT, '{logical}')"),
        ("from posixpath import join as path_join", "path_join(REPO_ROOT, '{logical}')"),
        ("from os import path as p", "p.join(REPO_ROOT, '{logical}')"),
        ("from pathlib import Path", "REPO_ROOT.joinpath('{logical}')"),
        ("from pathlib import Path", "Path(REPO_ROOT).joinpath('{logical}')"),
        ("from pathlib import PurePath", "PurePath(REPO_ROOT).joinpath('{logical}')"),
        ("from pathlib import Path", "Path.joinpath(REPO_ROOT, '{logical}')"),
        ("from pathlib import PurePath", "PurePath.joinpath(REPO_ROOT, '{logical}')"),
    ],
)
def test_packaged_resource_alias_joins_on_other_root_are_violations(import_line: str, expression: str) -> None:
    logical = "data/projects/open_model_data/trust/v4_child_profile_v3.json"
    source = f"{import_line}\n" + expression.format(logical=logical)
    hit = _literal_hits(source)[0]
    assert hit["join"] is True
    assert hit["resource_join"] is False
    assert _disposition(hit, packaged=True) == "violation"


@pytest.mark.parametrize(
    ("import_line", "expression"),
    [
        ("import os.path as p", "p.join(ROOT, '{logical}')"),
        ("from os.path import join", "join(ROOT, '{logical}')"),
        ("import os as o", "o.path.join(ROOT, '{logical}')"),
        ("import posixpath", "posixpath.join(ROOT, '{logical}')"),
    ],
)
def test_packaged_resource_alias_joins_accept_package_root(import_line: str, expression: str) -> None:
    logical = "data/projects/open_model_data/trust/v4_child_profile_v3.json"
    source = (
        "from learn_ukrainian_v4_runtime.resources import resource_root\n"
        "ROOT = resource_root()\n"
        f"{import_line}\n" + expression.format(logical=logical)
    )
    hit = _literal_hits(source)[0]
    assert hit["join"] is True
    assert hit["resource_join"] is True
    assert _disposition(hit, packaged=True) == "packaged-resource"


@pytest.mark.parametrize(
    "function",
    [
        'def load():\n    ROOT = Path(".")\n    return ROOT / "{logical}"',
        'def load(ROOT):\n    return ROOT / "{logical}"',
        'def load(ROOT: Path = Path(".")):\n    return ROOT / "{logical}"',
        'def load():\n    ROOT = Path(".")\n    return ROOT.joinpath("{logical}")',
    ],
)
def test_packaged_resource_join_rejects_function_local_shadow(function: str) -> None:
    logical = "data/projects/open_model_data/trust/v4_child_profile_v3.json"
    source = (
        "from learn_ukrainian_v4_runtime.resources import resource_root\n"
        "ROOT = resource_root()\n" + function.format(logical=logical)
    )
    hit = _literal_hits(source)[0]
    assert hit["join"] is True
    assert hit["resource_join"] is False
    assert _disposition(hit, packaged=True) == "violation"


@pytest.mark.parametrize(
    "expression",
    [
        "ROOT.joinpath('{logical}')",
        "resource_root().joinpath('{logical}')",
        "Path.joinpath(ROOT, '{logical}')",
    ],
)
def test_packaged_resource_joinpath_accepts_package_root(expression: str) -> None:
    logical = "data/projects/open_model_data/trust/v4_child_profile_v3.json"
    source = (
        "from learn_ukrainian_v4_runtime.resources import resource_root\n"
        "ROOT = resource_root()\n" + expression.format(logical=logical)
    )
    hit = _literal_hits(source)[0]
    assert hit["join"] is True
    assert hit["resource_join"] is True
    assert _disposition(hit, packaged=True) == "packaged-resource"


@pytest.mark.parametrize(
    ("logical", "allowed"),
    [
        ("data/projects/open_model_data/components/decolonization/reviews/decol_lex_001.review.json", "review-locator"),
        ("data/projects/open_model_data/examples", "directory-prefix"),
        ("data/projects/open_model_data/contracts/phase3_audit_entropy_receipt_v1.schema.json", "frozen-logical-key"),
    ],
)
def test_resource_root_join_does_not_allow_other_classes(logical: str, allowed: str) -> None:
    source = f'from learn_ukrainian_v4_runtime.resources import resource_root\nresource_root() / "{logical}"'
    bare = f'{{"review_dossier_locator": "{logical}"}}' if allowed == "review-locator" else f'"{logical}"'
    assert _disposition(_literal_hits(bare)[0], packaged=True) == allowed
    hit = _literal_hits(source)[0]
    assert hit["resource_join"] is True
    assert _disposition(hit, packaged=True) == "violation"
