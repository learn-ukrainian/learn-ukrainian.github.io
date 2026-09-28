"""Guard production K-path literals so defaults cannot point at moved files.

A string literal under ``data/projects/open_model_data/`` that names a
classification-table K file or a K-only directory must be an argument of
``resolve_open_model_path`` (or the registry-backed helpers ``_bound_path``,
``_physical_k_path``, and ``source_asset``). Frozen logical keys from
Decisions G and H, directory-prefix queries, and packaged v4-runtime resource
names stay as the pre-migration ``data/`` string. A script that joins such a
literal onto a filesystem root is still a failure.
"""

from __future__ import annotations

import ast
import csv
import re
from pathlib import Path

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


def _literal_hits(source: str) -> list[dict[str, object]]:
    tree = ast.parse(source)
    parents: dict[ast.AST, ast.AST] = {}
    for parent in ast.walk(tree):
        for child in ast.iter_child_nodes(parent):
            parents[child] = parent
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
        container: ast.AST = node
        parent = parents.get(container)
        if isinstance(parent, ast.JoinedStr):
            container = parent
            parent = parents.get(container)
        is_join = isinstance(parent, ast.BinOp) and isinstance(parent.op, ast.Div)
        is_path_call = isinstance(parent, ast.Call) and _call_name(parent) == "Path"
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
                        "path_call": is_path_call,
                        "key": dict_key,
                    }
                )
            index = found + len(MARKER)
    return hits


def _disposition(hit: dict[str, object], *, packaged: bool) -> str:
    if hit["via_resolver"]:
        return "resolver"
    relative = str(hit["relative"])
    review = (
        hit["kind"] == "FILE"
        and hit["key"] == "review_dossier_locator"
        and relative.startswith(REVIEW_PREFIX)
        and relative.endswith(".review.json")
        and not hit["join"]
        and not hit["path_call"]
    )
    if review:
        return "review-locator"
    if packaged and relative in PACKAGED_RESOURCE_PATHS:
        return "packaged-resource"
    if hit["kind"] == "DIR" and relative in DIRECTORY_PREFIXES and not hit["join"]:
        return "directory-prefix"
    if hit["kind"] == "FILE" and relative in FROZEN_LOGICAL_KEYS and not hit["join"]:
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
