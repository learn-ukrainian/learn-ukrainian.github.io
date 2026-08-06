#!/usr/bin/env python3
"""Text-free, fail-closed alignment and audit primitives for Pravopys editions.

This module may nominate mechanical *candidates* from frozen hierarchy locators
and normalized-text digests.  It never infers whether two rules mean the same
thing, and it never assigns a delta disposition.  Those are externally supplied
Ukrainian-review adjudications which this module only validates.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any, Protocol

from jsonschema import Draft202012Validator, ValidationError

ROOT = Path(__file__).resolve().parents[3]
SCHEMA_PATH = ROOT / "data/projects/open_model_data/contracts/phase3_pravopys_delta_bundle_v1.schema.json"
SOURCE_UNIVERSE_DIR = ROOT / "data/projects/open_model_data/evidence/source_universe_v1"
SOURCE_FREEZE_RECEIPT_PATH = SOURCE_UNIVERSE_DIR / "source-universe-freeze-receipt.json"
ROLE_CONTRACT_PATH = ROOT / "data/projects/open_model_data/evidence/correction_protection_role_contract_v1.json"
SOURCE_FREEZE_RECEIPT_SHA256 = "39061cc9c76d3cc510497dfb1df19639c07f76eb933599a3930137bf60ee31a0"
ROLE_CONTRACT_SHA256 = "05679fb356fd29fb9a14102a87020b8d06940edd43b3538a05d811bf845260cf"
SCHEMA_VERSION = "phase3_pravopys_delta_bundle_v1"
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
UKRAINIAN_REVIEWER_TASK_ID = "review-phase3-recovery-contract-domain-v8"
UKRAINIAN_REVIEWER_CONTROLLER_ID = "controller_phase3_ukrainian_reviewer_01"
SOURCE_LEDGER_SHA256 = {
    EDITION_2019: "fdb02b99bd284813e035687ae64ad41693f9d995b0e1d6666d5b5dfbf1dc9080",
    EDITION_2026: "dbf53af0f5f1c70790bad4e8e5943f700ea8f0a5d4b1311723cc1ce0fbb22006",
}
SOURCE_LEDGER_PATHS = {edition: SOURCE_UNIVERSE_DIR / f"{edition}.units.jsonl" for edition in EDITION_TOTALS}


class PravopysDeltaError(ValueError):
    """A candidate, adjudication, freeze, or audit artifact is unsafe."""


class ApprovedCommonEntropyContract(Protocol):
    """Narrow post-#6388 integration point; no local entropy implementation."""

    def derive_audit_entropy(self, context: Mapping[str, str]) -> bytes:
        """Verify the approved tuple and return its common-contract entropy."""


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


def source_universe_sha256() -> str:
    """Return the identity hash for the two sealed Pravopys source ledgers."""
    return sha256_json({
        "source_freeze_receipt_sha256": SOURCE_FREEZE_RECEIPT_SHA256,
        "ledger_sha256": SOURCE_LEDGER_SHA256,
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


def load_frozen_pravopys_ledgers(
    *,
    receipt_path: Path = SOURCE_FREEZE_RECEIPT_PATH,
    ledger_paths: Mapping[str, Path] = SOURCE_LEDGER_PATHS,
) -> tuple[Mapping[str, Any], list[Mapping[str, Any]], list[Mapping[str, Any]]]:
    """Load only the two exact, current text-free Pravopys freeze ledgers.

    The receipt, receipt manifest, family receipts, and on-disk JSONL bytes are
    all checked before a caller can use a unit.  This is intentionally not a
    generic loader: another receipt requires a separately reviewed contract.
    """
    _require(receipt_path == SOURCE_FREEZE_RECEIPT_PATH, "unapproved source-freeze receipt path")
    _require(sha256_file(receipt_path) == SOURCE_FREEZE_RECEIPT_SHA256, "source-freeze receipt SHA drift")
    receipt = _read_json(receipt_path)
    _require(receipt.get("schema_version") == "phase3_source_universe_freeze_v1", "wrong source-freeze receipt schema")
    _require(receipt.get("text_free") is True, "source-freeze receipt is not text-free")
    _require(receipt.get("status") == "SOURCE_UNIVERSE_FROZEN_NOT_COVERAGE_READY", "source-freeze receipt status drift")
    _require(_as_mapping(receipt.get("input_sha256"), "source-freeze input hashes missing") == {
        "calque_module": "d1af3c47b47916c90f7e9fa6fa1e2a9e29283ffda14e430415a97848f91556c5",
        "pravopys_2019_pdf": EDITION_HASHES[EDITION_2019],
        "pravopys_2026_pdf": EDITION_HASHES[EDITION_2026],
        "r2u_cache": "182e8685b420d982ff753f38e8a4b1043191f10925d2802cb30252c4f7b6e2e7",
        "sources_db": "eb5e0c3745020def62d5d5cdfb5190bc8a91d6c3dc04b05f5f98f259b3696c4d",
        "vesum_db": "3ed0fda490c576046c67c65b1b463ab9c7d2948749cc28768f4e83559b541462",
    }, "source-freeze acquired PDF provenance drift")
    families = {item.get("family_id"): item for item in receipt.get("families", []) if isinstance(item, Mapping)}
    payloads = {item.get("path"): item for item in _as_mapping(receipt.get("artifact_manifest"), "source-freeze manifest missing").get("payloads", []) if isinstance(item, Mapping)}
    rows: dict[str, list[Mapping[str, Any]]] = {}
    for edition in EDITION_TOTALS:
        path = ledger_paths.get(edition)
        _require(path == SOURCE_LEDGER_PATHS[edition], "unapproved source-freeze ledger path")
        _require(path.is_file(), "missing frozen Pravopys ledger")
        family = _as_mapping(families.get(edition), "source-freeze family receipt missing")
        payload = _as_mapping(payloads.get(path.name), "source-freeze payload manifest missing")
        _require(family == {
            "family_id": edition,
            "ledger_file": path.name,
            "ledger_sha256": SOURCE_LEDGER_SHA256[edition],
            "unit_count": EDITION_TOTALS[edition],
        }, "source-freeze family receipt drift")
        _require(payload.get("sha256") == SOURCE_LEDGER_SHA256[edition], "source-freeze payload SHA drift")
        _require(sha256_file(path) == SOURCE_LEDGER_SHA256[edition], "frozen Pravopys ledger SHA drift")
        ledger = _read_jsonl(path)
        _require(len(ledger) == EDITION_TOTALS[edition], "frozen Pravopys ledger line count drift")
        rows[edition] = ledger
    _unit_view(rows[EDITION_2019], EDITION_2019)
    _unit_view(rows[EDITION_2026], EDITION_2026)
    return receipt, rows[EDITION_2019], rows[EDITION_2026]


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


def load_ukrainian_reviewer_binding(*, path: Path = ROLE_CONTRACT_PATH) -> Mapping[str, str]:
    """Return the exact assigned Ukrainian-reviewer seat/task binding."""
    _require(path == ROLE_CONTRACT_PATH, "unapproved reviewer role-contract path")
    _require(sha256_file(path) == ROLE_CONTRACT_SHA256, "reviewer role-contract SHA drift")
    contract = _read_json(path)
    _require(contract.get("schema_version") == "correction_protection_role_contract_v1", "wrong reviewer role-contract schema")
    seats = [item for item in contract.get("seats", []) if isinstance(item, Mapping) and item.get("seat_id") == "seat_ukrainian_source_reviewer"]
    bindings = [item for item in contract.get("task_bindings", []) if isinstance(item, Mapping) and item.get("role_id") == UKRAINIAN_REVIEWER_ROLE]
    _require(len(seats) == len(bindings) == 1, "reviewer seat/task binding is missing or ambiguous")
    _require(seats[0] == {
        "seat_id": "seat_ukrainian_source_reviewer",
        "role_id": UKRAINIAN_REVIEWER_ROLE,
        "assignment_state": "assigned_verified",
        "controller_identity_id": UKRAINIAN_REVIEWER_CONTROLLER_ID,
        "controller_identity_attested": True,
        "ukrainian_capable_required": True,
        "may_decide": ["source_span_roles", "ukrainian_claims", "source_conflicts", "normative_scope"],
        "must_not": ["extract_rules_reviewed", "seal_heldout", "score"],
    }, "Ukrainian reviewer seat drift")
    _require(bindings[0] == {
        "role_id": UKRAINIAN_REVIEWER_ROLE,
        "reserved_task_id": UKRAINIAN_REVIEWER_TASK_ID,
        "controller_identity_id": UKRAINIAN_REVIEWER_CONTROLLER_ID,
        "status": "combined_contract_text_approved_pre_artifact",
        "artifact_approval_claimed": False,
        "program_completion_claimed": False,
    }, "Ukrainian reviewer task binding drift")
    return {
        "role_contract_sha256": ROLE_CONTRACT_SHA256,
        "seat_id": "seat_ukrainian_source_reviewer",
        "role_id": UKRAINIAN_REVIEWER_ROLE,
        "review_task_id": UKRAINIAN_REVIEWER_TASK_ID,
        "reviewer_controller_identity": UKRAINIAN_REVIEWER_CONTROLLER_ID,
    }


def _review_is_valid(value: Any, *, semantic: bool, binding: Mapping[str, str]) -> bool:
    review = _as_mapping(value, "delta lacks external Ukrainian adjudication")
    _require(review.get("role_contract_sha256") == binding["role_contract_sha256"], "review lacks exact role-contract SHA")
    _require(review.get("seat_id") == binding["seat_id"] and review.get("role_id") == binding["role_id"], "delta reviewer seat/role drift")
    _require(review.get("review_task_id") == binding["review_task_id"], "delta review task identity drift")
    _require(review.get("reviewer_controller_identity") == binding["reviewer_controller_identity"], "delta reviewer identity drift")
    _require(isinstance(review.get("review_receipt_locator"), str) and re.fullmatch(r"immutable://[^\s]+", review["review_receipt_locator"]) is not None, "immutable Ukrainian review receipt locator missing")
    _require(isinstance(review.get("review_receipt_sha256"), str) and re.fullmatch(r"[a-f0-9]{64}", review["review_receipt_sha256"]) is not None, "immutable Ukrainian review receipt hash missing")
    _require(isinstance(review.get("evidence_locator"), str) and re.fullmatch(r"immutable://[^\s]+", review["evidence_locator"]) is not None, "immutable review evidence locator missing")
    _require(isinstance(review.get("evidence_sha256"), str) and re.fullmatch(r"[a-f0-9]{64}", review["evidence_sha256"]) is not None, "immutable review evidence hash missing")
    _require(review.get("adjudication_state") == "externally_reviewed", "delta is not externally reviewed")
    if semantic:
        _require(review.get("semantic_review") is True, "semantic delta lacks Ukrainian semantic review")
    return True


def validate_delta_ledger(
    ledger: Sequence[Mapping[str, Any]], candidates: Sequence[Mapping[str, Any]],
    units_2019: Iterable[Mapping[str, Any]], units_2026: Iterable[Mapping[str, Any]],
    *, reviewer_binding: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Validate externally adjudicated delta rows against both frozen denominators."""
    old, new = _unit_view(units_2019, EDITION_2019), _unit_view(units_2026, EDITION_2026)
    binding = reviewer_binding or load_ukrainian_reviewer_binding()
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
            binding=binding,
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


def validate_auditor_seed(seed_record: Mapping[str, Any], population: Mapping[str, Any]) -> None:
    """Validate only the anti-grinding attestation fields, never derive entropy."""
    _require(population.get("population_frozen") is True, "auditor seed precedes population freeze")
    _require(seed_record.get("population_sha256") == population.get("population_sha256"), "auditor seed is not bound to population freeze")
    _require(seed_record.get("seed_owner_role_id") == AUDITOR_ROLE, "auditor seed owner is not independent disposition auditor")
    _require(seed_record.get("auditor_attests_only") is True, "auditor must only attest/commit common entropy")
    _require(seed_record.get("author_or_root_choices") is False and seed_record.get("reroll_count") == 0, "author/root choices or rerolls invalidate audit")
    _require(seed_record.get("audit_id") == "pravopys_delta", "wrong common-entropy audit identity")
    _require(seed_record.get("family_id") == "pravopys_2019_2026_delta", "wrong common-entropy family identity")
    _require(isinstance(seed_record.get("first_containing_origin_main_squash_merge_sha"), str) and len(seed_record["first_containing_origin_main_squash_merge_sha"]) == 40, "first-containing origin/main squash-merge SHA missing")
    _require(seed_record.get("universe_sha256") == source_universe_sha256(), "common-entropy source-universe binding drift")


def _approved_entropy_bytes(
    approved_common_entropy_contract: ApprovedCommonEntropyContract | None,
    *,
    seed_record: Mapping[str, Any],
    population: Mapping[str, Any],
) -> bytes:
    """Delegate entropy derivation to the approved common contract after #6388.

    This deliberately provides no fallback, salt, PR lookup, or entropy
    derivation.  The injected contract alone owns the byte-stable tuple and
    first-containing-origin/main verification.
    """
    _require(approved_common_entropy_contract is not None, "approved-common-entropy-contract-required")
    derive = getattr(approved_common_entropy_contract, "derive_audit_entropy", None)
    _require(callable(derive), "approved-common-entropy-contract-required")
    context = {
        "audit_id": str(seed_record["audit_id"]),
        "family_id": str(seed_record["family_id"]),
        "first_containing_origin_main_squash_merge_sha": str(seed_record["first_containing_origin_main_squash_merge_sha"]),
        "population_freeze_sha256": str(population["population_sha256"]),
        "population_sha256": str(seed_record["population_sha256"]),
        "universe_sha256": str(seed_record["universe_sha256"]),
    }
    entropy = derive(context)
    _require(isinstance(entropy, bytes) and entropy, "approved common entropy contract returned no entropy")
    return entropy


def draw_audit_sample(
    ledger: Sequence[Mapping[str, Any]],
    population: Mapping[str, Any],
    seed_record: Mapping[str, Any],
    *,
    approved_common_entropy_contract: ApprovedCommonEntropyContract | None = None,
) -> dict[str, Any]:
    """Draw the independent, no-replacement Hamilton-stratified audit sample."""
    validate_auditor_seed(seed_record, population)
    entropy = _approved_entropy_bytes(
        approved_common_entropy_contract,
        seed_record=seed_record,
        population=population,
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
    return {"population_sha256": population["population_sha256"], "sample_size": len(sample_ids), "sample_delta_ids": sample_ids, "stratum_allocation": [{"delta_disposition": key[0], "edition_section_identity": key[1], "sample_count": allocation[key]} for key in sorted(allocation)]}


def validate_audit_results(sample: Mapping[str, Any], results: Sequence[Mapping[str, Any]], population: Mapping[str, Any]) -> None:
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


def validate_bundle(
    bundle: Mapping[str, Any],
    *,
    schema_path: Path = SCHEMA_PATH,
    approved_common_entropy_contract: ApprovedCommonEntropyContract | None = None,
) -> dict[str, Any]:
    """Validate a complete, closed Pravopys delta bundle and all cross-record invariants."""
    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        Draft202012Validator(schema).validate(bundle)
    except (OSError, json.JSONDecodeError, ValidationError) as exc:
        raise PravopysDeltaError(f"delta bundle schema violation: {exc}") from exc
    _require(bundle.get("schema_version") == SCHEMA_VERSION and bundle.get("text_free") is True, "wrong text-free delta bundle")
    _, frozen_2019, frozen_2026 = load_frozen_pravopys_ledgers()
    _require(bundle["source_freeze"] == {
        "receipt_path": "data/projects/open_model_data/evidence/source_universe_v1/source-universe-freeze-receipt.json",
        "receipt_sha256": SOURCE_FREEZE_RECEIPT_SHA256,
        "ledger_sha256": SOURCE_LEDGER_SHA256,
    }, "source-freeze bundle binding drift")
    binding = load_ukrainian_reviewer_binding()
    old = _unit_view(bundle["units_2019"], EDITION_2019)
    new = _unit_view(bundle["units_2026"], EDITION_2026)
    _require(list(old.values()) == frozen_2019 and list(new.values()) == frozen_2026, "bundle unit ledgers are not the exact source-freeze ledgers")
    coverage = validate_delta_ledger(
        bundle["delta_ledger"],
        bundle["candidate_alignment"],
        old.values(),
        new.values(),
        reviewer_binding=binding,
    )
    population = _as_mapping(bundle["population_freeze"], "population freeze must be an object")
    expected_population = freeze_population(bundle["delta_ledger"])
    _require(dict(population) == expected_population, "population freeze drift")
    validate_auditor_seed(_as_mapping(bundle["auditor_seed"], "auditor seed must be an object"), population)
    sample = draw_audit_sample(
        bundle["delta_ledger"],
        population,
        bundle["auditor_seed"],
        approved_common_entropy_contract=approved_common_entropy_contract,
    )
    _require(bundle["audit_sample"] == sample, "audit sample is not deterministic from independent seed")
    validate_audit_results(bundle["audit_sample"], bundle["audit_results"], population)
    _require(coverage["delta_population_sha256"] == population["population_sha256"], "ledger/population digest mismatch")
    return {"ok": True, **coverage, "audit_sample_size": population["sample_size"]}
