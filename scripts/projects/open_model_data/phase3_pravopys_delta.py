#!/usr/bin/env python3
"""Text-free, fail-closed alignment and audit primitives for Pravopys editions.

This module may nominate mechanical *candidates* from frozen hierarchy locators
and normalized-text digests.  It never infers whether two rules mean the same
thing, and it never assigns a delta disposition.  Those are externally supplied
Ukrainian-review adjudications which this module only validates.
"""

from __future__ import annotations

import hashlib
import importlib
import json
import math
import re
from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, ValidationError

from scripts.projects.open_model_data import phase3_functional_roles as functional_roles

ROOT = Path(__file__).resolve().parents[3]
SCHEMA_PATH = ROOT / "data/projects/open_model_data/contracts/phase3_pravopys_delta_bundle_v1.schema.json"
SCHEMA_VERSION = "phase3_pravopys_delta_bundle_v1"
CURRENT_SOURCE_FREEZE_STATUS = "SOURCE_UNIVERSE_CURRENT_V2_1"
SOURCE_FREEZE_WRAPPER_SCHEMA_VERSION = "phase3_pravopys_source_freeze_wrapper_v2_1"
LEGACY_SOURCE_FREEZE_STATUS = "SOURCE_UNIVERSE_FROZEN_NOT_COVERAGE_READY"
EDITION_2019 = "pravopys_2019_complete"
EDITION_2026 = "pravopys_2026_complete"
EDITION_TOTALS = {EDITION_2019: 1090, EDITION_2026: 1466}
EDITION_HASHES = {
    EDITION_2019: "9adcb3e7e6b68db62719a4e8b0c34d7b1f4abde2986c694ab77662f2791ad24c",
    EDITION_2026: "e593956bfba6737d991a76fa86970db9c10a5cd7fd8895bae67f2b9a950c3a92",
}
DELTA_DISPOSITIONS = frozenset({
    "unchanged",
    "editorial_technical_only",
    "illustration_removed_or_changed",
    "stress_or_formulation_clarified",
    "new_structural_wrapper_or_alphabet_material",
    "added_rule_bearing_unit",
    "removed_rule_bearing_unit",
    "normative_conflict",
})
SEMANTIC_DISPOSITIONS = frozenset({
    "stress_or_formulation_clarified",
    "added_rule_bearing_unit",
    "removed_rule_bearing_unit",
    "normative_conflict",
})
UKRAINIAN_REVIEWER_ROLE = "ukrainian_source_reviewer"
AUDITOR_ROLE = "disposition_auditor"
REVIEW_ACTION_KIND = "pravopys_delta_ukrainian_review"
AUDIT_ACTION_KIND = "pravopys_delta_audit_results"
SOURCE_REVIEW_ACTION_KIND = "pravopys_source_freeze_ukrainian_review"
ROLE_PROVIDERS = {
    UKRAINIAN_REVIEWER_ROLE: "xai",
    AUDITOR_ROLE: "anthropic",
}


class PravopysDeltaError(ValueError):
    """A candidate, adjudication, freeze, or audit artifact is unsafe."""


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def sha256_json(value: Any) -> str:
    return hashlib.sha256((canonical_json(value) + "\n").encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def source_universe_sha256(source_freeze: Mapping[str, Any]) -> str:
    """Return the identity hash for one caller-supplied current source freeze."""
    return sha256_json(dict(source_freeze))


def source_freeze_input_manifest_sha256(
    input_sha256: Mapping[str, Any], ledger_sha256: Mapping[str, Any], ledger_unit_counts: Mapping[str, Any],
) -> str:
    """Hash the fixed inputs a v2.1 source-review task was given."""
    return sha256_json({
        "input_sha256": dict(input_sha256),
        "pravopys_ledgers": [
            {
                "family_id": edition,
                "ledger_sha256": ledger_sha256[edition],
                "unit_count": ledger_unit_counts[edition],
            }
            for edition in sorted(EDITION_TOTALS)
        ],
    })


def source_freeze_review_result_sha256(wrapper: Mapping[str, Any]) -> str:
    """Hash the closed, non-recursive reviewed-current-freeze result surface."""
    return sha256_json({
        field: wrapper[field]
        for field in (
            "source_status",
            "legacy_receipt_sha256",
            "source_freeze_input_manifest_sha256",
            "base_contract_sha256",
            "amendment_sha256",
            "combined_contract_sha256",
            "functional_role_contract_sha256",
            "conflict_graph_sha256",
            "evaluation_cycle_id",
            "source_review_receipt_locator",
            "source_review_receipt_sha256",
        )
    })


def _read_json(path: Path) -> Mapping[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PravopysDeltaError(f"cannot read required JSON artifact: {path}") from exc
    return _as_mapping(value, "required JSON artifact must be an object")


def _read_jsonl(path: Path) -> list[Mapping[str, Any]]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
        return [_as_mapping(json.loads(line), "frozen ledger row must be an object") for line in lines if line]
    except (OSError, json.JSONDecodeError) as exc:
        raise PravopysDeltaError(f"cannot read frozen JSONL ledger: {path}") from exc


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise PravopysDeltaError(message)


def _as_mapping(value: Any, message: str) -> Mapping[str, Any]:
    _require(isinstance(value, Mapping), message)
    return value


def _unit_view(units: Iterable[Mapping[str, Any]], edition: str) -> dict[str, Mapping[str, Any]]:
    """Validate the text-free frozen unit surface and return units by opaque ID."""
    materialized = list(units)
    _require(len(materialized) == EDITION_TOTALS[edition], f"{edition} frozen denominator must be {EDITION_TOTALS[edition]}")
    result: dict[str, Mapping[str, Any]] = {}
    for unit in materialized:
        item = _as_mapping(unit, "frozen unit must be an object")
        _require(item.get("family_id") == edition, "frozen unit edition identity drift")
        unit_id = item.get("unit_id")
        text_hash = item.get("normalized_text_sha256")
        locator = item.get("locator")
        _require(isinstance(unit_id, str) and unit_id, "frozen unit lacks opaque unit_id")
        _require(isinstance(text_hash, str) and len(text_hash) == 64, "frozen unit lacks normalized-text hash")
        _require(isinstance(locator, Mapping), "frozen unit lacks hierarchy locator")
        _require(locator.get("edition_sha256", "").lower() == EDITION_HASHES[edition], "frozen unit PDF hash drift")
        path = locator.get("section_path")
        _require(isinstance(path, list) and path and all(isinstance(token, str) and token for token in path), "frozen unit lacks section_path")
        _require(unit_id not in result, "duplicate frozen unit_id")
        result[unit_id] = item
    return result


def _path_key(unit: Mapping[str, Any]) -> tuple[str, ...]:
    return tuple(unit["locator"]["section_path"])


def _unique_index(units: Mapping[str, Mapping[str, Any]], key: str) -> dict[Any, str]:
    buckets: dict[Any, list[str]] = defaultdict(list)
    for unit_id, unit in units.items():
        value = unit["normalized_text_sha256"] if key == "normalized_text_sha256" else _path_key(unit)
        buckets[value].append(unit_id)
    return {value: values[0] for value, values in buckets.items() if len(values) == 1}


def generate_candidate_alignment(
    units_2019: Iterable[Mapping[str, Any]], units_2026: Iterable[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Make deterministic, non-semantic candidate correspondences.

    A matching hash or hierarchy path is only a review candidate.  Ambiguous
    matches remain unmatched and must be resolved by externally reviewed input.
    """
    old, new = _unit_view(units_2019, EDITION_2019), _unit_view(units_2026, EDITION_2026)
    old_hash, new_hash = _unique_index(old, "normalized_text_sha256"), _unique_index(new, "normalized_text_sha256")
    old_path, new_path = _unique_index(old, "section_path"), _unique_index(new, "section_path")
    matched_old: set[str] = set()
    matched_new: set[str] = set()
    records: list[dict[str, Any]] = []

    def add_pair(old_id: str, new_id: str, basis: str) -> None:
        matched_old.add(old_id)
        matched_new.add(new_id)
        records.append({
            "candidate_id": sha256_json({"basis": basis, "unit_ids_2019": [old_id], "unit_ids_2026": [new_id]}),
            "candidate_basis": basis,
            "candidate_kind": "candidate_pair",
            "unit_ids_2019": [old_id],
            "unit_ids_2026": [new_id],
        })

    for digest in sorted(set(old_hash) & set(new_hash)):
        add_pair(old_hash[digest], new_hash[digest], "normalized_text_sha256_exact")
    for path in sorted(set(old_path) & set(new_path)):
        old_id, new_id = old_path[path], new_path[path]
        if old_id not in matched_old and new_id not in matched_new:
            add_pair(old_id, new_id, "section_path_exact")
    for old_id in sorted(set(old) - matched_old):
        records.append({"candidate_id": sha256_json({"basis": "unmatched", "unit_ids_2019": [old_id], "unit_ids_2026": []}), "candidate_basis": "unmatched", "candidate_kind": "unmatched_2019", "unit_ids_2019": [old_id], "unit_ids_2026": []})
    for new_id in sorted(set(new) - matched_new):
        records.append({"candidate_id": sha256_json({"basis": "unmatched", "unit_ids_2019": [], "unit_ids_2026": [new_id]}), "candidate_basis": "unmatched", "candidate_kind": "unmatched_2026", "unit_ids_2019": [], "unit_ids_2026": [new_id]})
    return sorted(records, key=lambda record: record["candidate_id"])


def _validated_source_freeze(
    source_freeze: Mapping[str, Any], *, repo_root: Path = ROOT, role_contract_path: Path = functional_roles.LEDGER_PATH,
) -> tuple[Mapping[str, Any], Path, dict[str, Path]]:
    """Bind a current v2.1 wrapper to a historical receipt and its ledgers.

    The historical v1 receipt stays a byte-bound provenance payload.  Current
    source status exists only in the wrapper and is admitted only with the
    v2.1 Ukrainian source-review action receipt.
    """
    manifest = _as_mapping(source_freeze, "source-freeze manifest must be an object")
    _require(
        set(manifest) == {
            "wrapper_schema_version", "legacy_receipt_path", "legacy_receipt_sha256", "source_status",
            "input_sha256", "ledger_sha256", "ledger_unit_counts",
            "base_contract_sha256", "amendment_sha256", "combined_contract_sha256",
            "functional_role_contract_sha256", "conflict_graph_sha256", "evaluation_cycle_id",
            "source_freeze_input_manifest_sha256", "source_review_receipt_locator", "source_review_receipt_sha256",
            "source_review_result_sha256",
            "source_review_action_receipt",
        },
        "source-freeze wrapper fields drift",
    )
    _require(manifest.get("wrapper_schema_version") == SOURCE_FREEZE_WRAPPER_SCHEMA_VERSION, "wrong source-freeze wrapper schema")
    receipt_path_value = manifest.get("legacy_receipt_path")
    _require(isinstance(receipt_path_value, str) and receipt_path_value, "legacy source-freeze receipt path missing")
    receipt_path = (repo_root / receipt_path_value).resolve()
    _require(receipt_path.is_relative_to(repo_root.resolve()), "legacy source-freeze receipt escapes repository root")
    _require(receipt_path.is_file() and not receipt_path.is_symlink(), "legacy source-freeze receipt is missing")
    _require(sha256_file(receipt_path) == manifest.get("legacy_receipt_sha256"), "legacy source-freeze receipt SHA drift")
    _require(manifest.get("source_status") == CURRENT_SOURCE_FREEZE_STATUS, "invalidated or non-current source-freeze status")
    receipt = _read_json(receipt_path)
    _require(receipt.get("schema_version") == "phase3_source_universe_freeze_v1", "wrong source-freeze receipt schema")
    _require(receipt.get("text_free") is True, "source-freeze receipt is not text-free")
    _require(receipt.get("status") == LEGACY_SOURCE_FREEZE_STATUS, "legacy receipt is not historical-only provenance")
    _require(receipt.get("input_sha256") == manifest["input_sha256"], "source-freeze input binding drift")
    input_hashes = _as_mapping(manifest.get("input_sha256"), "source-freeze input hashes missing")
    _require(
        set(input_hashes) == {
            "calque_module", "pravopys_2019_pdf", "pravopys_2026_pdf", "r2u_cache", "sources_db", "vesum_db",
        }
        and all(isinstance(value, str) and re.fullmatch(r"[a-f0-9]{64}", value) for value in input_hashes.values()),
        "source-freeze input hash shape drift",
    )
    ledger_hashes = _as_mapping(manifest.get("ledger_sha256"), "source-freeze ledger hashes missing")
    _require(set(ledger_hashes) == set(EDITION_TOTALS), "source-freeze ledger family set drift")
    _require(all(isinstance(value, str) and re.fullmatch(r"[a-f0-9]{64}", value) for value in ledger_hashes.values()), "source-freeze ledger hash syntax drift")
    ledger_unit_counts = _as_mapping(manifest.get("ledger_unit_counts"), "source-freeze ledger counts missing")
    _require(ledger_unit_counts == EDITION_TOTALS, "source-freeze ledger denominator drift")
    families = {item.get("family_id"): item for item in receipt.get("families", []) if isinstance(item, Mapping)}
    payloads = {
        item.get("path"): item
        for item in _as_mapping(receipt.get("artifact_manifest"), "source-freeze manifest missing").get("payloads", [])
        if isinstance(item, Mapping)
    }
    ledger_paths: dict[str, Path] = {}
    for edition in EDITION_TOTALS:
        family = _as_mapping(families.get(edition), "source-freeze family receipt missing")
        ledger_name = f"{edition}.units.jsonl"
        path = receipt_path.parent / ledger_name
        _require(path.is_file() and not path.is_symlink(), "missing frozen Pravopys ledger")
        payload = _as_mapping(payloads.get(ledger_name), "source-freeze payload manifest missing")
        _require(
            family.get("ledger_file") == ledger_name
            and family.get("ledger_sha256") == ledger_hashes[edition]
            and family.get("unit_count") == ledger_unit_counts[edition],
            "source-freeze family receipt drift",
        )
        _require(payload.get("sha256") == ledger_hashes[edition], "source-freeze payload SHA drift")
        _require(sha256_file(path) == ledger_hashes[edition], "frozen Pravopys ledger SHA drift")
        ledger_paths[edition] = path
    role_contract, bindings = load_functional_role_bindings(path=role_contract_path)
    source_binding = bindings[UKRAINIAN_REVIEWER_ROLE]
    for field, expected in (
        ("base_contract_sha256", functional_roles.BASE_SHA256),
        ("amendment_sha256", functional_roles.AMENDMENT_SHA256),
        ("combined_contract_sha256", functional_roles.COMBINED_SHA256),
        ("functional_role_contract_sha256", source_binding["functional_role_contract_sha256"]),
        ("conflict_graph_sha256", source_binding["conflict_graph_sha256"]),
        ("evaluation_cycle_id", source_binding["evaluation_cycle_id"]),
    ):
        _require(manifest.get(field) == expected, "source-freeze v2.1 contract binding drift")
    expected_input_manifest = source_freeze_input_manifest_sha256(input_hashes, ledger_hashes, ledger_unit_counts)
    _require(
        manifest.get("source_freeze_input_manifest_sha256") == expected_input_manifest,
        "source-freeze review input manifest binding drift",
    )
    _require(
        isinstance(manifest.get("source_review_receipt_locator"), str)
        and re.fullmatch(r"immutable://[^\s]+", manifest["source_review_receipt_locator"]) is not None,
        "immutable source-review receipt locator missing",
    )
    _require(
        isinstance(manifest.get("source_review_receipt_sha256"), str)
        and re.fullmatch(r"[a-f0-9]{64}", manifest["source_review_receipt_sha256"]) is not None,
        "immutable source-review receipt hash missing",
    )
    expected_result = source_freeze_review_result_sha256(manifest)
    _require(manifest.get("source_review_result_sha256") == expected_result, "source-freeze review result binding drift")
    _action_receipt_is_valid(
        manifest.get("source_review_action_receipt"),
        role_contract=role_contract,
        binding=source_binding,
        action_kind=SOURCE_REVIEW_ACTION_KIND,
        input_manifest_sha256=expected_input_manifest,
        output_sha256=expected_result,
    )
    return receipt, receipt_path, ledger_paths


def load_frozen_pravopys_ledgers(
    source_freeze: Mapping[str, Any], *, repo_root: Path = ROOT, role_contract_path: Path = functional_roles.LEDGER_PATH,
) -> tuple[Mapping[str, Any], list[Mapping[str, Any]], list[Mapping[str, Any]]]:
    """Load current, hash-bound text-free Pravopys ledgers supplied by a manifest."""
    _, _, ledger_paths = _validated_source_freeze(
        source_freeze, repo_root=repo_root, role_contract_path=role_contract_path,
    )
    rows: dict[str, list[Mapping[str, Any]]] = {}
    for edition, path in ledger_paths.items():
        ledger = _read_jsonl(path)
        _require(len(ledger) == EDITION_TOTALS[edition], "frozen Pravopys ledger line count drift")
        rows[edition] = ledger
    _unit_view(rows[EDITION_2019], EDITION_2019)
    _unit_view(rows[EDITION_2026], EDITION_2026)
    return dict(source_freeze), rows[EDITION_2019], rows[EDITION_2026]


def _validate_candidates(candidates: Sequence[Mapping[str, Any]], old: Mapping[str, Any], new: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    by_id: dict[str, Mapping[str, Any]] = {}
    seen_old: set[str] = set()
    seen_new: set[str] = set()
    for record in candidates:
        item = _as_mapping(record, "candidate record must be an object")
        candidate_id = item.get("candidate_id")
        kind, basis = item.get("candidate_kind"), item.get("candidate_basis")
        old_ids, new_ids = item.get("unit_ids_2019"), item.get("unit_ids_2026")
        _require(isinstance(candidate_id, str) and candidate_id and candidate_id not in by_id, "duplicate candidate_id")
        _require(kind in {"candidate_pair", "unmatched_2019", "unmatched_2026"}, "invalid candidate kind")
        _require(basis in {"normalized_text_sha256_exact", "section_path_exact", "unmatched"}, "invalid candidate basis")
        _require(isinstance(old_ids, list) and isinstance(new_ids, list), "candidate memberships must be arrays")
        _require(all(isinstance(unit_id, str) and unit_id in old for unit_id in old_ids), "candidate references unknown 2019 unit")
        _require(all(isinstance(unit_id, str) and unit_id in new for unit_id in new_ids), "candidate references unknown 2026 unit")
        _require(len(old_ids) == len(set(old_ids)) and len(new_ids) == len(set(new_ids)), "candidate repeats a unit")
        _require((kind == "candidate_pair") == (len(old_ids) == len(new_ids) == 1), "candidate pair shape drift")
        _require((kind == "unmatched_2019") == (len(old_ids) == 1 and not new_ids), "2019 unmatched candidate shape drift")
        _require((kind == "unmatched_2026") == (not old_ids and len(new_ids) == 1), "2026 unmatched candidate shape drift")
        _require((basis == "unmatched") == (kind != "candidate_pair"), "candidate basis/kind drift")
        expected_candidate_id = sha256_json({"basis": basis, "unit_ids_2019": old_ids, "unit_ids_2026": new_ids})
        _require(candidate_id == expected_candidate_id, "candidate_id is not deterministic from its text-free basis")
        if basis == "normalized_text_sha256_exact":
            _require(old[old_ids[0]]["normalized_text_sha256"] == new[new_ids[0]]["normalized_text_sha256"], "candidate hash basis is false")
        if basis == "section_path_exact":
            _require(_path_key(old[old_ids[0]]) == _path_key(new[new_ids[0]]), "candidate hierarchy basis is false")
        _require(not (seen_old & set(old_ids)) and not (seen_new & set(new_ids)), "candidate coverage is not a partition")
        seen_old.update(old_ids)
        seen_new.update(new_ids)
        by_id[candidate_id] = item
    _require(seen_old == set(old) and seen_new == set(new), "candidate alignment does not cover both denominators exactly once")
    return by_id


def load_functional_role_bindings(
    *, path: Path = functional_roles.LEDGER_PATH,
) -> tuple[Mapping[str, Any], dict[str, dict[str, str]]]:
    """Verify and expose only the v2.1 review/audit task bindings."""
    _require(path.is_file() and not path.is_symlink(), "functional-role ledger is missing")
    try:
        contract = functional_roles.verify_value(functional_roles.read_json(path))
        bindings = {
            role_id: functional_roles.binding_for_role(contract, role_id)
            for role_id in (UKRAINIAN_REVIEWER_ROLE, AUDITOR_ROLE)
        }
    except functional_roles.FunctionalRoleError as exc:
        raise PravopysDeltaError(str(exc)) from exc
    return contract, {
        role_id: {
            **binding,
            "functional_role_contract_sha256": sha256_file(path),
            "conflict_graph_sha256": functional_roles.conflict_graph_sha256(contract),
            "evaluation_cycle_id": str(contract["evaluation_cycle"]["evaluation_cycle_id"]),
        }
        for role_id, binding in bindings.items()
    }


def _action_receipt_is_valid(
    action: Any,
    *,
    role_contract: Mapping[str, Any],
    binding: Mapping[str, str],
    action_kind: str,
    input_manifest_sha256: str,
    output_sha256: str,
) -> None:
    receipt = _as_mapping(action, "functional action receipt is missing")
    _require(set(receipt) == set(functional_roles.ACTION_RECEIPT_FIELDS), "functional action receipt fields drift")
    _require(
        receipt.get("role_id") == binding["role_id"] and receipt.get("task_id") == binding["task_id"],
        "functional action receipt task binding mismatch",
    )
    role = next(item for item in role_contract["functional_roles"] if item["role_id"] == binding["role_id"])
    _require(
        all(receipt.get(field) == role[field] for field in ("exact_model", "model_family", "harness")),
        "functional action receipt lane mismatch",
    )
    _require(receipt.get("provider") == ROLE_PROVIDERS[binding["role_id"]], "functional action provider binding mismatch")
    _require(receipt.get("action_kind") == action_kind, "functional action kind mismatch")
    _require(
        receipt.get("input_manifest_sha256") == input_manifest_sha256
        and receipt.get("output_sha256") == output_sha256,
        "functional action input/output binding mismatch",
    )
    _require(
        receipt.get("evaluation_cycle_id") == binding["evaluation_cycle_id"]
        and all(
            receipt.get(field) == binding[field]
            for field in (
                "functional_role_contract_sha256",
                "conflict_graph_sha256",
            )
        )
        and receipt.get("base_contract_sha256") == functional_roles.BASE_SHA256
        and receipt.get("amendment_sha256") == functional_roles.AMENDMENT_SHA256
        and receipt.get("combined_contract_sha256") == functional_roles.COMBINED_SHA256,
        "functional action contract or evaluation-cycle binding mismatch",
    )
    _require(receipt.get("status") == "completed", "functional action is not complete")
    _require(
        all(isinstance(receipt.get(field), str) and receipt[field] for field in ("receipt_id", "started_at", "completed_at")),
        "functional action metadata incomplete",
    )
    identity = {
        field: receipt[field]
        for field in ("role_id", "task_id", "input_manifest_sha256", "evaluation_cycle_id", "output_sha256", "status")
    }
    _require(
        receipt["receipt_id"]
        == "phase3_functional_action:" + hashlib.sha256(canonical_json(identity).encode("utf-8")).hexdigest(),
        "functional action receipt ID mismatch",
    )


def _review_is_valid(
    value: Any,
    *,
    semantic: bool,
    binding: Mapping[str, str],
    role_contract: Mapping[str, Any],
    review_input_manifest_sha256: str,
) -> bool:
    review = _as_mapping(value, "delta lacks external Ukrainian adjudication")
    _require(review.get("role_id") == binding["role_id"] and review.get("task_id") == binding["task_id"], "delta reviewer task binding drift")
    _require(isinstance(review.get("review_receipt_locator"), str) and re.fullmatch(r"immutable://[^\s]+", review["review_receipt_locator"]) is not None, "immutable Ukrainian review receipt locator missing")
    _require(isinstance(review.get("review_receipt_sha256"), str) and re.fullmatch(r"[a-f0-9]{64}", review["review_receipt_sha256"]) is not None, "immutable Ukrainian review receipt hash missing")
    _require(isinstance(review.get("evidence_locator"), str) and re.fullmatch(r"immutable://[^\s]+", review["evidence_locator"]) is not None, "immutable review evidence locator missing")
    _require(isinstance(review.get("evidence_sha256"), str) and re.fullmatch(r"[a-f0-9]{64}", review["evidence_sha256"]) is not None, "immutable review evidence hash missing")
    _require(review.get("adjudication_state") == "externally_reviewed", "delta is not externally reviewed")
    _action_receipt_is_valid(
        review.get("action_receipt"),
        role_contract=role_contract,
        binding=binding,
        action_kind=REVIEW_ACTION_KIND,
        input_manifest_sha256=review_input_manifest_sha256,
        output_sha256=str(review["review_receipt_sha256"]),
    )
    if semantic:
        _require(review.get("semantic_review") is True, "semantic delta lacks Ukrainian semantic review")
    return True


def _delta_review_input_manifest_sha256(
    source_freeze: Mapping[str, Any], row: Mapping[str, Any],
) -> str:
    """Hash the fixed non-review delta inputs that the reviewer was given."""
    return sha256_json({
        "source_freeze": dict(source_freeze),
        "delta": {
            field: row[field]
            for field in (
                "delta_id",
                "delta_disposition",
                "candidate_ids",
                "unit_ids_2019",
                "unit_ids_2026",
                "edition_section_identity",
            )
        },
    })


def validate_delta_ledger(
    ledger: Sequence[Mapping[str, Any]], candidates: Sequence[Mapping[str, Any]],
    units_2019: Iterable[Mapping[str, Any]], units_2026: Iterable[Mapping[str, Any]],
    *,
    source_freeze: Mapping[str, Any],
    role_contract: Mapping[str, Any],
    reviewer_binding: Mapping[str, str],
) -> dict[str, Any]:
    """Validate externally adjudicated delta rows against both frozen denominators."""
    old, new = _unit_view(units_2019, EDITION_2019), _unit_view(units_2026, EDITION_2026)
    try:
        verified_contract = functional_roles.verify_value(role_contract)
        expected_binding = functional_roles.binding_for_role(verified_contract, UKRAINIAN_REVIEWER_ROLE)
    except functional_roles.FunctionalRoleError as exc:
        raise PravopysDeltaError(str(exc)) from exc
    _require(
        reviewer_binding["role_id"] == expected_binding["role_id"]
        and reviewer_binding["task_id"] == expected_binding["task_id"],
        "Ukrainian reviewer functional binding drift",
    )
    _require(
        list(candidates) == generate_candidate_alignment(old.values(), new.values()),
        "candidate alignment differs from the deterministic mechanical generator",
    )
    candidates_by_id = _validate_candidates(candidates, old, new)
    _require(bool(ledger), "delta population must be nonempty")
    seen_candidates: set[str] = set()
    seen_old: set[str] = set()
    seen_new: set[str] = set()
    delta_ids: set[str] = set()
    normalized: list[dict[str, Any]] = []
    for row in ledger:
        item = _as_mapping(row, "delta row must be an object")
        delta_id, disposition = item.get("delta_id"), item.get("delta_disposition")
        candidate_ids = item.get("candidate_ids")
        _require(isinstance(delta_id, str) and delta_id and delta_id not in delta_ids, "duplicate delta_id")
        _require(disposition in DELTA_DISPOSITIONS, "invalid delta disposition")
        _require(isinstance(candidate_ids, list) and candidate_ids and len(candidate_ids) == len(set(candidate_ids)), "delta must reference unique candidates")
        _require(all(isinstance(candidate_id, str) and candidate_id in candidates_by_id for candidate_id in candidate_ids), "delta references unknown candidate")
        _require(not (seen_candidates & set(candidate_ids)), "candidate appears in more than one delta row")
        expected_old = sorted(unit_id for candidate_id in candidate_ids for unit_id in candidates_by_id[candidate_id]["unit_ids_2019"])
        expected_new = sorted(unit_id for candidate_id in candidate_ids for unit_id in candidates_by_id[candidate_id]["unit_ids_2026"])
        _require(item.get("unit_ids_2019") == expected_old and item.get("unit_ids_2026") == expected_new, "delta membership differs from candidate partition")
        _require(isinstance(item.get("edition_section_identity"), str) and item["edition_section_identity"], "delta lacks edition_section_identity")
        _review_is_valid(
            item.get("ukrainian_review"),
            semantic=disposition in SEMANTIC_DISPOSITIONS,
            binding=reviewer_binding,
            role_contract=verified_contract,
            review_input_manifest_sha256=_delta_review_input_manifest_sha256(source_freeze, item),
        )
        if disposition in {
            "unchanged",
            "editorial_technical_only",
            "illustration_removed_or_changed",
            "stress_or_formulation_clarified",
            "normative_conflict",
        }:
            _require(bool(expected_old) and bool(expected_new), f"{disposition} delta must cover both editions")
        if disposition in {"new_structural_wrapper_or_alphabet_material", "added_rule_bearing_unit"}:
            _require(not expected_old and bool(expected_new), f"{disposition} delta must be 2026-only")
        if disposition == "removed_rule_bearing_unit":
            _require(bool(expected_old) and not expected_new, "removed rule-bearing delta must be 2019-only")
        seen_candidates.update(candidate_ids)
        seen_old.update(expected_old)
        seen_new.update(expected_new)
        delta_ids.add(delta_id)
        normalized.append(dict(item))
    _require(seen_candidates == set(candidates_by_id), "delta ledger does not classify every candidate")
    _require(seen_old == set(old) and seen_new == set(new), "delta ledger does not cover both frozen denominators exactly once")
    return {
        "delta_total": len(normalized),
        "delta_population_sha256": sha256_json(sorted(normalized, key=lambda row: row["delta_id"])),
        "edition_totals": {EDITION_2019: len(old), EDITION_2026: len(new)},
    }


def audit_sample_size(delta_total: int) -> int:
    _require(delta_total > 0, "delta population must be nonempty")
    return min(delta_total, max(100, math.ceil(0.02 * delta_total)))


def hamilton_allocation(strata_sizes: Mapping[tuple[str, str], int], sample_size: int) -> dict[tuple[str, str], int]:
    """Allocate the fixed sample deterministically by Hamilton's method."""
    _require(bool(strata_sizes) and all(size > 0 for size in strata_sizes.values()), "invalid empty audit stratum")
    total = sum(strata_sizes.values())
    _require(0 < sample_size <= total, "audit sample size is out of range")
    floors = {key: (sample_size * size) // total for key, size in strata_sizes.items()}
    remaining = sample_size - sum(floors.values())
    rankings = sorted(strata_sizes, key=lambda key: (-(sample_size * strata_sizes[key] % total), key))
    for key in rankings[:remaining]:
        floors[key] += 1
    return floors


def freeze_population(ledger: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    _require(bool(ledger), "delta population must be nonempty")
    rows = sorted((dict(row) for row in ledger), key=lambda row: row["delta_id"])
    _require(len({row["delta_id"] for row in rows}) == len(rows), "population has duplicate delta_id")
    return {"population_frozen": True, "delta_total": len(rows), "population_sha256": sha256_json(rows), "sample_size": audit_sample_size(len(rows))}


def validate_auditor_seed(
    seed_record: Mapping[str, Any], population: Mapping[str, Any], *, source_freeze: Mapping[str, Any],
) -> None:
    """Validate only the anti-grinding attestation fields, never derive entropy."""
    _require(population.get("population_frozen") is True, "auditor seed precedes population freeze")
    _require(seed_record.get("population_sha256") == population.get("population_sha256"), "auditor seed is not bound to population freeze")
    _require(seed_record.get("seed_owner_role_id") == AUDITOR_ROLE, "auditor seed owner is not independent disposition auditor")
    _require(seed_record.get("auditor_attests_only") is True, "auditor must only attest/commit common entropy")
    _require(seed_record.get("author_or_root_choices") is False and seed_record.get("reroll_count") == 0, "author/root choices or rerolls invalidate audit")
    _require(seed_record.get("audit_id") == "pravopys_delta", "wrong common-entropy audit identity")
    _require(seed_record.get("family_id") == "pravopys_2019_2026_delta", "wrong common-entropy family identity")
    _require(isinstance(seed_record.get("first_containing_origin_main_squash_merge_sha"), str) and len(seed_record["first_containing_origin_main_squash_merge_sha"]) == 40, "first-containing origin/main squash-merge SHA missing")
    _require(seed_record.get("universe_sha256") == source_universe_sha256(source_freeze), "common-entropy source-universe binding drift")
    receipt = _as_mapping(seed_record.get("entropy_receipt"), "approved common entropy receipt is missing")
    _require(
        receipt.get("first_containing_merge_sha") == seed_record.get("first_containing_origin_main_squash_merge_sha"),
        "common entropy first-containing binding drift",
    )


def _approved_entropy_bytes(
    approved_common_entropy_contract: Any | None,
    *,
    seed_record: Mapping[str, Any],
    population: Mapping[str, Any],
    source_freeze: Mapping[str, Any],
    repo_root: Path,
) -> tuple[bytes, dict[str, str]]:
    """Use the approved receipt verifier; injection is test-only plumbing.

    Production always imports the common verifier.  A supplied verifier may be
    used by hermetic tests, but it receives the exact production arguments and
    cannot switch back to a caller-derived entropy protocol.
    """
    if approved_common_entropy_contract is None:
        module = importlib.import_module("scripts.projects.open_model_data.phase3_audit_entropy")
        verifier = getattr(module, "verify_entropy_receipt", None)
    else:
        verifier = (
            approved_common_entropy_contract
            if callable(approved_common_entropy_contract)
            else getattr(approved_common_entropy_contract, "verify_entropy_receipt", None)
        )
    _require(callable(verifier), "approved common entropy verifier is unavailable")
    try:
        result = verifier(
            seed_record["entropy_receipt"],
            purpose="pravopys_delta",
            frozen_bundle_sha256=source_universe_sha256(source_freeze),
            frozen_population_sha256=str(population["population_sha256"]),
            auditor_role_id=AUDITOR_ROLE,
            auditor_task_id=functional_roles.ROLE_TASKS[AUDITOR_ROLE],
            repo_root=repo_root,
        )
    except Exception as exc:
        raise PravopysDeltaError("approved common entropy receipt is invalid") from exc
    _require(isinstance(result, Mapping), "approved common entropy verifier returned invalid result")
    required = {"derived_seed", "entropy_receipt_sha256", "first_containing_merge_sha", "canonical_tuple_sha256"}
    _require(set(result) == required and all(isinstance(result[key], str) for key in required), "approved common entropy verifier result shape drift")
    _require(all(re.fullmatch(r"[a-f0-9]{64}", str(result[key])) for key in required - {"first_containing_merge_sha"}), "approved common entropy verifier returned invalid hashes")
    _require(re.fullmatch(r"[a-f0-9]{40}", str(result["first_containing_merge_sha"])) is not None, "approved common entropy verifier returned invalid merge SHA")
    return bytes.fromhex(str(result["derived_seed"])), {key: str(result[key]) for key in required}


def draw_audit_sample(
    ledger: Sequence[Mapping[str, Any]],
    population: Mapping[str, Any],
    seed_record: Mapping[str, Any],
    *,
    source_freeze: Mapping[str, Any],
    approved_common_entropy_contract: Any | None = None,
    repo_root: Path = ROOT,
) -> dict[str, Any]:
    """Draw the independent, no-replacement Hamilton-stratified audit sample."""
    validate_auditor_seed(seed_record, population, source_freeze=source_freeze)
    entropy, entropy_identity = _approved_entropy_bytes(
        approved_common_entropy_contract,
        seed_record=seed_record,
        population=population,
        source_freeze=source_freeze,
        repo_root=repo_root,
    )
    rows = sorted((dict(row) for row in ledger), key=lambda row: row["delta_id"])
    _require(population.get("population_sha256") == sha256_json(rows), "audit population changed after freeze")
    strata: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        strata[(row["delta_disposition"], row["edition_section_identity"])].append(row)
    allocation = hamilton_allocation({key: len(value) for key, value in strata.items()}, int(population["sample_size"]))
    sample: list[dict[str, Any]] = []
    for key in sorted(strata):
        def rank(row: Mapping[str, Any], stratum: tuple[str, str] = key) -> tuple[str, str]:
            message = f"{population['population_sha256']}|{stratum[0]}|{stratum[1]}|{row['delta_id']}"
            return hashlib.sha256(entropy + message.encode()).hexdigest(), str(row["delta_id"])

        ranked = sorted(strata[key], key=rank)
        sample.extend(ranked[:allocation[key]])
    sample_ids = sorted(row["delta_id"] for row in sample)
    _require(len(sample_ids) == len(set(sample_ids)) == int(population["sample_size"]), "audit sample violates no-replacement size")
    return {
        "population_sha256": population["population_sha256"],
        "sample_size": len(sample_ids),
        "sample_delta_ids": sample_ids,
        "stratum_allocation": [{"delta_disposition": key[0], "edition_section_identity": key[1], "sample_count": allocation[key]} for key in sorted(allocation)],
        "entropy_receipt_sha256": entropy_identity["entropy_receipt_sha256"],
        "first_containing_merge_sha": entropy_identity["first_containing_merge_sha"],
        "canonical_tuple_sha256": entropy_identity["canonical_tuple_sha256"],
        "derived_seed_sha256": sha256_json({"derived_seed": entropy_identity["derived_seed"]}),
    }


def validate_audit_results(
    sample: Mapping[str, Any],
    results: Sequence[Mapping[str, Any]],
    population: Mapping[str, Any],
    *,
    role_contract: Mapping[str, Any],
    auditor_binding: Mapping[str, str],
    audit_action_receipt: Mapping[str, Any],
) -> None:
    _require(sample.get("population_sha256") == population.get("population_sha256"), "audit sample population binding drift")
    expected = set(sample.get("sample_delta_ids", []))
    _require(len(expected) == sample.get("sample_size") == population.get("sample_size"), "audit sample identity/count mismatch")
    result_by_id: dict[str, Mapping[str, Any]] = {}
    for result in results:
        item = _as_mapping(result, "audit result must be an object")
        delta_id = item.get("delta_id")
        _require(isinstance(delta_id, str) and delta_id in expected and delta_id not in result_by_id, "audit results do not exactly match sample")
        _require(item.get("decision") == "agree", "zero non-agree is required; repair, re-freeze, and re-sample")
        _require(item.get("repair_applied") is False, "repair invalidates freeze and sample")
        result_by_id[delta_id] = item
    _require(set(result_by_id) == expected, "audit results do not cover every sampled delta")
    _action_receipt_is_valid(
        audit_action_receipt,
        role_contract=role_contract,
        binding=auditor_binding,
        action_kind=AUDIT_ACTION_KIND,
        input_manifest_sha256=sha256_json(dict(sample)),
        output_sha256=sha256_json(list(results)),
    )


def validate_bundle(
    bundle: Mapping[str, Any],
    *,
    schema_path: Path = SCHEMA_PATH,
    role_contract_path: Path = functional_roles.LEDGER_PATH,
    repo_root: Path = ROOT,
    approved_common_entropy_contract: Any | None = None,
) -> dict[str, Any]:
    """Validate a complete, closed Pravopys delta bundle and all cross-record invariants."""
    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        Draft202012Validator(schema).validate(bundle)
    except (OSError, json.JSONDecodeError, ValidationError) as exc:
        raise PravopysDeltaError(f"delta bundle schema violation: {exc}") from exc
    _require(bundle.get("schema_version") == SCHEMA_VERSION and bundle.get("text_free") is True, "wrong text-free delta bundle")
    source_freeze = _as_mapping(bundle["source_freeze"], "source-freeze bundle binding must be an object")
    _, frozen_2019, frozen_2026 = load_frozen_pravopys_ledgers(
        source_freeze, repo_root=repo_root, role_contract_path=role_contract_path,
    )
    role_contract, bindings = load_functional_role_bindings(path=role_contract_path)
    old = _unit_view(bundle["units_2019"], EDITION_2019)
    new = _unit_view(bundle["units_2026"], EDITION_2026)
    _require(list(old.values()) == frozen_2019 and list(new.values()) == frozen_2026, "bundle unit ledgers are not the exact source-freeze ledgers")
    coverage = validate_delta_ledger(
        bundle["delta_ledger"],
        bundle["candidate_alignment"],
        old.values(),
        new.values(),
        source_freeze=source_freeze,
        role_contract=role_contract,
        reviewer_binding=bindings[UKRAINIAN_REVIEWER_ROLE],
    )
    population = _as_mapping(bundle["population_freeze"], "population freeze must be an object")
    expected_population = freeze_population(bundle["delta_ledger"])
    _require(dict(population) == expected_population, "population freeze drift")
    validate_auditor_seed(
        _as_mapping(bundle["auditor_seed"], "auditor seed must be an object"),
        population,
        source_freeze=source_freeze,
    )
    sample = draw_audit_sample(
        bundle["delta_ledger"],
        population,
        bundle["auditor_seed"],
        source_freeze=source_freeze,
        approved_common_entropy_contract=approved_common_entropy_contract,
        repo_root=repo_root,
    )
    _require(bundle["audit_sample"] == sample, "audit sample is not deterministic from independent seed")
    validate_audit_results(
        bundle["audit_sample"],
        bundle["audit_results"],
        population,
        role_contract=role_contract,
        auditor_binding=bindings[AUDITOR_ROLE],
        audit_action_receipt=_as_mapping(bundle["audit_action_receipt"], "audit action receipt must be an object"),
    )
    _require(coverage["delta_population_sha256"] == population["population_sha256"], "ledger/population digest mismatch")
    return {"ok": True, **coverage, "audit_sample_size": population["sample_size"]}
