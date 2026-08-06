#!/usr/bin/env python3
"""Text-free, fail-closed primitives for Phase 3 disposition audits.

This module deliberately validates identities, populations, and audit receipts.
It never reads source prose, makes linguistic judgments, searches for a seed,
or writes an audit result.  The assigned auditor may only commit and attest the
unique origin/main-bound seed derivation after every audit population is frozen.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import subprocess
import sys
from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from scripts.projects.open_model_data import verify_phase3_source_universe_freeze as source_freeze

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "data/projects/open_model_data"
DEFAULT_SOURCE_UNIVERSE = DATA / "evidence/source_universe_v1"
DEFAULT_COVERAGE_CONTRACT = DATA / "evidence/correction_protection_coverage_contract_v1.json"
DEFAULT_ROLE_CONTRACT = DATA / "evidence/correction_protection_role_contract_v1.json"
DISPOSITION_CODES = frozenset({
    "converted", "not_rule_bearing", "duplicate_representation", "evaluation_only",
    "rights_limited_locator_only", "superseded_or_historical", "blocked_with_reason",
})
NONCONVERTED_DECISION_CODES = frozenset({
    "agree", "disagree_should_be_converted", "disagree_wrong_code", "insufficient_locator_evidence",
})
CONVERTED_MISS_CODES = frozenset({
    "disagree_stub_conversion", "disagree_misclassified_role_or_claim",
    "disagree_unsupported_evidence", "disagree_non_actionable_rule",
})
LEXICAL_DECISION_CODES = frozenset({
    "agree", "disagree_invalid_attestation", "disagree_unsupported_semantic_range",
    "disagree_mismapped_morphology", "insufficient_locator_evidence",
})
SHA256 = re.compile(r"^[a-f0-9]{64}$")
IDENTITY = re.compile(r"^[A-Za-z0-9_.:-]{1,160}$")
ROUND_ID = re.compile(r"^audit_round_[a-z0-9_]{1,120}$")
GIT_SHA40 = re.compile(r"^[a-f0-9]{40}$")
SQUASH_SUBJECT = re.compile(r"\(#[1-9][0-9]*\)$")
ENTROPY_CONTRACT_VERSION = "phase3_common_audit_entropy_v1"
ORIGIN_MAIN_REF = "origin/main"
AUDIT_KINDS = frozenset({"source_disposition", "textbook_nonhit", "pravopys_delta"})


class AuditError(ValueError):
    """An audit artifact is malformed, stale, or fails a required gate."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AuditError(message)


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_value(value: Any) -> str:
    return sha256_bytes(canonical_json(value).encode("utf-8"))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as exc:
        raise AuditError(f"cannot read artifact: {path}") from exc
    return digest.hexdigest()


def _git(repo_root: Path, arguments: Sequence[str], *, text: bool = True) -> str | bytes:
    try:
        completed = subprocess.run(
            ["git", "-C", str(repo_root), *arguments],
            check=False,
            capture_output=True,
            text=text,
        )
    except OSError as exc:
        raise AuditError(f"cannot execute git for entropy binding: {exc}") from exc
    require(completed.returncode == 0, "cannot verify origin/main entropy binding")
    return completed.stdout


def _first_containing_squash_merge(
    population_freeze: Mapping[str, Any],
    *,
    repo_root: Path = ROOT,
    origin_ref: str = ORIGIN_MAIN_REF,
) -> str:
    """Find the earliest origin/main squash commit landing this exact freeze.

    Pickaxe narrows the first-parent history to commits changing the exact
    freeze hash.  Candidate changed blobs must parse to the supplied canonical
    population-freeze object, preventing a documentation mention or later
    reland from becoming entropy provenance.
    """
    require(origin_ref == ORIGIN_MAIN_REF, "entropy origin ref must be exact origin/main")
    freeze_hash = _sha(population_freeze.get("population_freeze_sha256"), "population freeze")
    head = str(_git(repo_root, ["rev-parse", "--verify", origin_ref])).strip()
    require(GIT_SHA40.fullmatch(head) is not None, "invalid origin/main head")
    output = str(_git(repo_root, [
        "log", "--first-parent", "--reverse", "--format=%H", f"-S{freeze_hash}", origin_ref, "--",
    ]))
    for candidate in (line.strip() for line in output.splitlines() if line.strip()):
        require(GIT_SHA40.fullmatch(candidate) is not None, "invalid entropy commit candidate")
        paths = str(_git(repo_root, ["diff-tree", "--no-commit-id", "--name-only", "--diff-filter=AMR", "-r", candidate])).splitlines()
        for path in paths:
            if not path or path.startswith("-"):
                continue
            blob = _git(repo_root, ["show", f"{candidate}:{path}"], text=False)
            try:
                landed = json.loads(bytes(blob))
            except (UnicodeDecodeError, json.JSONDecodeError):
                continue
            if isinstance(landed, Mapping) and canonical_json(landed) == canonical_json(population_freeze):
                parents = str(_git(repo_root, ["rev-list", "--parents", "-n", "1", candidate])).split()
                subject = str(_git(repo_root, ["show", "-s", "--format=%s", candidate])).strip()
                committer = str(_git(repo_root, ["show", "-s", "--format=%cn%x00%ce", candidate])).strip()
                require(
                    len(parents) == 2
                    and SQUASH_SUBJECT.search(subject) is not None
                    and committer == "GitHub\x00noreply@github.com",
                    "first population-freeze landing is not a GitHub squash-merge commit",
                )
                return candidate
    raise AuditError("population freeze is not landed by an exact first-containing squash merge on origin/main")


def entropy_tuple(
    *,
    first_containing_squash_merge_sha: str,
    audit_kind: str,
    family_id: str,
    population_kind: str,
    population_freeze_sha256: str,
    population_universe_sha256: str,
) -> list[dict[str, str]]:
    """Return the approved ordered, byte-stable common entropy tuple."""
    require(GIT_SHA40.fullmatch(first_containing_squash_merge_sha) is not None, "invalid first-containing merge SHA")
    require(audit_kind in AUDIT_KINDS, "invalid common entropy audit kind")
    _identity(family_id, "entropy family")
    _identity(population_kind, "entropy population kind")
    _sha(population_freeze_sha256, "entropy population freeze")
    _sha(population_universe_sha256, "entropy population universe")
    return [
        {"field": "version_tag", "value": ENTROPY_CONTRACT_VERSION},
        {"field": "first_containing_squash_merge_sha", "value": first_containing_squash_merge_sha},
        {"field": "audit_kind", "value": audit_kind},
        {"field": "family_id", "value": family_id},
        {"field": "population_kind", "value": population_kind},
        {"field": "population_freeze_sha256", "value": population_freeze_sha256},
        {"field": "population_universe_sha256", "value": population_universe_sha256},
    ]


def _derive_entropy_seed_from_fields(**fields: str) -> tuple[list[dict[str, str]], str]:
    frozen_tuple = entropy_tuple(**fields)
    return frozen_tuple, sha256_bytes(canonical_json(frozen_tuple).encode("utf-8"))


def derive_entropy_seed(
    population_freeze: Mapping[str, Any],
    *,
    audit_kind: str,
    family_id: str,
    population_kind: str,
    population_universe_sha256: str,
    repo_root: Path = ROOT,
) -> tuple[list[dict[str, str]], str, str]:
    """Derive the unique seed only after the exact freeze lands on origin/main."""
    first_commit = _first_containing_squash_merge(population_freeze, repo_root=repo_root)
    frozen_tuple, seed = _derive_entropy_seed_from_fields(
        first_containing_squash_merge_sha=first_commit,
        audit_kind=audit_kind,
        family_id=family_id,
        population_kind=population_kind,
        population_freeze_sha256=population_freeze["population_freeze_sha256"],
        population_universe_sha256=population_universe_sha256,
    )
    return frozen_tuple, seed, first_commit


def validate_common_entropy_receipt(
    receipt: Mapping[str, Any],
    population_freeze: Mapping[str, Any],
    *,
    assigned_auditor_controller_identity_id: str,
    audit_kind: str,
    family_id: str,
    population_kind: str,
    population_universe_sha256: str,
    repo_root: Path = ROOT,
    prohibited_identity_ids: Sequence[str] = (),
    prior_seed_receipt_sha256s: Sequence[str] = (),
) -> str:
    """Apply the reusable source/textbook/delta anti-grinding contract."""
    assigned = _identity(assigned_auditor_controller_identity_id, "assigned entropy auditor")
    require(receipt.get("audit_kind") == audit_kind and audit_kind in AUDIT_KINDS, "entropy audit kind mismatch")
    require(receipt.get("family_id") == family_id and receipt.get("population_kind") == population_kind, "entropy family or population mismatch")
    require(receipt.get("population_freeze_sha256") == population_freeze.get("population_freeze_sha256"), "entropy population-freeze binding mismatch")
    require(receipt.get("population_sha256") == population_universe_sha256, "entropy population universe binding mismatch")
    _sha(receipt.get("seed"), "derived audit seed")
    require(receipt.get("auditor_controller_identity_id") == assigned, "entropy identity is not the assigned auditor")
    require(receipt.get("seed_committer_controller_identity_id") == assigned, "assigned auditor must be the sole seed committer")
    require(receipt.get("seed_attestor_controller_identity_id") == assigned, "assigned auditor must be the sole seed attestor")
    require(assigned not in set(prohibited_identity_ids), "author or root identity cannot commit audit entropy")
    require(receipt.get("proposal_identity_ids") == [], "seed proposal/filter/search identities are forbidden")
    require(receipt.get("results_recorded") is False, "seed receipt was recorded after results")
    require(receipt.get("reroll_count") == 0, "seed search or reroll invalidates receipt")
    require(receipt.get("prior_sample_reused") is False, "passing sample reuse is forbidden")
    require(receipt.get("derivation_mode") == "unique_sha256_or_abort", "seed derivation must be unique or abort")
    require(receipt.get("entropy_contract_version") == ENTROPY_CONTRACT_VERSION, "entropy contract version mismatch")
    require(receipt.get("origin_main_ref") == ORIGIN_MAIN_REF, "entropy provenance is not exact origin/main")
    first_commit = _first_containing_squash_merge(population_freeze, repo_root=repo_root)
    require(receipt.get("first_containing_squash_merge_sha") == first_commit, "stale or non-first population-freeze merge binding")
    expected_tuple, expected_seed = _derive_entropy_seed_from_fields(
        first_containing_squash_merge_sha=first_commit,
        audit_kind=audit_kind,
        family_id=family_id,
        population_kind=population_kind,
        population_freeze_sha256=population_freeze["population_freeze_sha256"],
        population_universe_sha256=population_universe_sha256,
    )
    require(receipt.get("entropy_tuple") == expected_tuple, "canonical entropy tuple mismatch")
    require(receipt.get("entropy_tuple_sha256") == expected_seed, "entropy tuple hash mismatch")
    require(receipt.get("seed") == expected_seed, "seed is not the unique approved entropy derivation")
    require(receipt.get("seed_commitment_sha256") == sha256_bytes(expected_seed.encode("ascii")), "seed commitment mismatch")
    receipt_hash = sha256_value(receipt)
    require(receipt_hash not in set(prior_seed_receipt_sha256s), "seed receipt cannot be reused after a repair or passing audit")
    return receipt_hash


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AuditError(f"cannot read JSON artifact: {path}") from exc
    require(isinstance(value, dict), f"JSON artifact must be an object: {path}")
    return value


def _exact(value: Mapping[str, Any], fields: set[str], label: str) -> None:
    require(set(value) == fields, f"unexpected {label} shape")


def _sha(value: object, label: str) -> str:
    require(isinstance(value, str) and SHA256.fullmatch(value) is not None, f"invalid SHA-256: {label}")
    return value


def _identity(value: object, label: str) -> str:
    require(isinstance(value, str) and IDENTITY.fullmatch(value) is not None, f"invalid text-free identity: {label}")
    return value


def _text_free(value: object, label: str = "artifact") -> None:
    """Reject source-bearing field names and multiline values in submitted artifacts."""
    forbidden = {"text", "source_text", "content", "definition", "sentence", "excerpt", "quote"}
    if isinstance(value, Mapping):
        for key, item in value.items():
            require(isinstance(key, str) and key not in forbidden, f"source text field is forbidden: {label}")
            _text_free(item, label)
    elif isinstance(value, list):
        for item in value:
            _text_free(item, label)
    elif isinstance(value, str):
        require("\n" not in value and "\r" not in value, f"multiline value is forbidden: {label}")


def _contract_families(coverage: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    require(coverage.get("text_free") is True, "coverage contract is not text-free")
    families = coverage.get("mandatory_families")
    require(isinstance(families, list), "coverage contract lacks mandatory families")
    result: dict[str, Mapping[str, Any]] = {}
    for family in families:
        require(isinstance(family, Mapping) and isinstance(family.get("family_id"), str), "invalid coverage family")
        family_id = family["family_id"]
        require(family_id not in result, f"duplicate coverage family: {family_id}")
        result[family_id] = family
    return result


def _validate_source_audit(family: Mapping[str, Any]) -> None:
    """Keep the coverage-contract sample rules exact rather than merely similar."""
    audit = family.get("audit")
    require(isinstance(audit, Mapping), f"source audit missing: {family.get('family_id')}")
    require(audit.get("auditor_role_id") == "disposition_auditor", "source audit owner changed")
    require(audit.get("seed_owner_role_id") == "disposition_auditor", "source seed owner changed")
    require(audit.get("nonconverted_formula") == "min(nonconverted_total,max(100,ceil(0.02*family_unit_total)))", "nonconverted formula changed")
    require(audit.get("converted_formula") == "min(converted_total,max(100,ceil(0.02*family_unit_total)))", "converted formula changed")
    require(audit.get("nonconverted_stratification") == ["disposition_code", "document_or_edition_identity"], "nonconverted strata changed")
    require(audit.get("converted_stratification") == ["source_role", "claim_type", "document_or_edition_identity"], "converted strata changed")
    require(audit.get("sampling_without_replacement") is True, "sampling-with-replacement is forbidden")
    require(set(audit.get("nonconverted_decision_codes", ())) == NONCONVERTED_DECISION_CODES and len(audit.get("nonconverted_decision_codes", ())) == len(NONCONVERTED_DECISION_CODES), "nonconverted decision codes changed")
    require(set(audit.get("converted_miss_codes", ())) == CONVERTED_MISS_CODES and len(audit.get("converted_miss_codes", ())) == len(CONVERTED_MISS_CODES), "converted miss codes changed")
    require(audit.get("repair_invalidates_both_samples") is True and audit.get("passing_sample_reuse_forbidden") is True, "repair/reuse gate changed")


def _source_receipt(source_universe_dir: Path) -> tuple[dict[str, Any], str, dict[str, list[dict[str, str]]]]:
    """Verify the merged source freeze and return only opaque source identifiers."""
    source_freeze.validate(source_universe_dir, repo_root=ROOT)
    receipt_path = source_universe_dir / source_freeze.RECEIPT_FILE
    receipt = read_json(receipt_path)
    records: dict[str, list[dict[str, str]]] = {}
    for family in receipt["families"]:
        if "ledger_file" not in family:
            continue
        family_id = family["family_id"]
        ledger_path = source_universe_dir / family["ledger_file"]
        units: list[dict[str, str]] = []
        for line in ledger_path.read_text(encoding="utf-8").splitlines():
            item = json.loads(line)
            units.append({
                "unit_id": item["unit_id"], "unit_sha256": item["unit_sha256"],
                "unit_locator_sha256": sha256_value(item["locator"]),
            })
        unit_ids = [unit["unit_id"] for unit in units]
        require(len(units) == family["unit_count"] and len(set(unit_ids)) == len(units), f"invalid frozen unit ids: {family_id}")
        records[family_id] = sorted(units, key=lambda unit: unit["unit_id"])
    return receipt, sha256_file(receipt_path), records


def source_family_universe_sha256(units: Sequence[str] | Sequence[Mapping[str, str]]) -> str:
    """Hash canonical unit-id + unit-hash membership, never source text."""
    normalized: list[dict[str, str]] = []
    for unit in units:
        if isinstance(unit, str):
            normalized.append({"unit_id": unit, "unit_sha256": sha256_value({"unit_id": unit})})
        else:
            normalized.append({"unit_id": unit["unit_id"], "unit_sha256": unit["unit_sha256"]})
    require(len(normalized) == len({unit["unit_id"] for unit in normalized}), "duplicate source unit id")
    return sha256_value(sorted(normalized, key=lambda unit: unit["unit_id"]))


def _ledger_hash(ledger: Mapping[str, Any]) -> str:
    return sha256_value(ledger)


def validate_disposition_ledger(
    ledger: Mapping[str, Any],
    *,
    source_universe_dir: Path = DEFAULT_SOURCE_UNIVERSE,
    coverage_contract: Mapping[str, Any] | None = None,
    role_contract: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Validate a full, opaque source disposition ledger against the freeze."""
    coverage = coverage_contract or read_json(DEFAULT_COVERAGE_CONTRACT)
    roles = role_contract or read_json(DEFAULT_ROLE_CONTRACT)
    _text_free(ledger, "disposition ledger")
    _exact(ledger, {
        "schema_version", "text_free", "source_universe_receipt_sha256",
        "source_universe_payload_manifest_sha256", "coverage_contract_sha256",
        "role_contract_sha256", "repair_generation", "families",
    }, "disposition ledger")
    require(ledger["schema_version"] == "phase3_disposition_ledger_v1" and ledger["text_free"] is True, "invalid disposition ledger header")
    require(isinstance(ledger["repair_generation"], int) and ledger["repair_generation"] >= 0, "invalid repair generation")
    receipt, receipt_hash, source_units = _source_receipt(source_universe_dir)
    require(ledger["source_universe_receipt_sha256"] == receipt_hash, "stale source-universe receipt binding")
    require(ledger["source_universe_payload_manifest_sha256"] == receipt["artifact_manifest"]["payload_manifest_sha256"], "stale source-universe manifest binding")
    require(ledger["coverage_contract_sha256"] == sha256_value(coverage), "stale coverage contract binding")
    require(ledger["role_contract_sha256"] == sha256_value(roles), "stale role contract binding")
    coverage_families = _contract_families(coverage)
    families = ledger["families"]
    require(isinstance(families, list), "disposition ledger families must be a list")
    observed: dict[str, dict[str, Any]] = {}
    for family in families:
        require(isinstance(family, Mapping), "disposition family must be an object")
        _exact(family, {
            "family_id", "frozen_input_identity_total", "family_unit_total", "ledger_input_total",
            "disposition_row_sum", "ledger_universe_sha256", "audit_universe_sha256", "rows",
        }, "disposition family")
        family_id = family["family_id"]
        require(isinstance(family_id, str) and family_id in source_units, f"unknown or lexical disposition family: {family_id}")
        require(family_id in coverage_families and not family_id.startswith("lexical_"), f"family cannot use source disposition audit: {family_id}")
        _validate_source_audit(coverage_families[family_id])
        require(family_id not in observed, f"duplicate disposition family: {family_id}")
        frozen_units = source_units[family_id]
        frozen_by_id = {unit["unit_id"]: unit for unit in frozen_units}
        expected_total = len(frozen_units)
        for name in ("frozen_input_identity_total", "family_unit_total", "ledger_input_total", "disposition_row_sum"):
            require(family[name] == expected_total, f"ledger identity total mismatch: {family_id}:{name}")
        expected_hash = source_family_universe_sha256(frozen_units)
        require(family["ledger_universe_sha256"] == expected_hash, f"ledger universe hash mismatch: {family_id}")
        require(family["audit_universe_sha256"] == expected_hash, f"audit universe hash mismatch: {family_id}")
        rows = family["rows"]
        require(isinstance(rows, list) and len(rows) == expected_total, f"disposition row count mismatch: {family_id}")
        row_ids: set[str] = set()
        normalized_rows: list[dict[str, Any]] = []
        for row in rows:
            require(isinstance(row, Mapping), "disposition row must be an object")
            _exact(row, {
                "unit_id", "unit_sha256", "unit_locator_sha256", "disposition_code", "document_or_edition_identity",
                "source_role", "claim_type", "canonical_content_identity", "evidence_artifact_locators", "consumer_view_ids",
                "conversion_predicate_locator", "reason_locator", "repeated_reason_count", "predicate_or_rationale_locator",
            }, "disposition row")
            unit_id = row["unit_id"]
            require(isinstance(unit_id, str) and unit_id in frozen_by_id and unit_id not in row_ids, f"duplicate or missing frozen unit id: {family_id}")
            row_ids.add(unit_id)
            require(row["unit_sha256"] == frozen_by_id[unit_id]["unit_sha256"], f"frozen unit hash mismatch: {family_id}")
            require(row["unit_locator_sha256"] == frozen_by_id[unit_id]["unit_locator_sha256"], f"frozen unit locator mismatch: {family_id}")
            _sha(row["unit_sha256"], "unit hash")
            _sha(row["unit_locator_sha256"], "unit locator")
            require(row["disposition_code"] in DISPOSITION_CODES, f"invalid disposition code: {family_id}")
            _identity(row["document_or_edition_identity"], "document identity")
            if row["disposition_code"] == "converted":
                _identity(row["source_role"], "converted source role")
                _identity(row["claim_type"], "converted claim type")
                _identity(row["canonical_content_identity"], "canonical converted content identity")
                require(isinstance(row["evidence_artifact_locators"], list) and row["evidence_artifact_locators"], "converted row lacks immutable evidence artifact locator")
                require(isinstance(row["consumer_view_ids"], list) and row["consumer_view_ids"], "converted row lacks consumer view")
                for locator in row["evidence_artifact_locators"]:
                    _identity(locator, "conversion evidence locator")
                for view_id in row["consumer_view_ids"]:
                    _identity(view_id, "consumer view identity")
                _identity(row["conversion_predicate_locator"], "conversion predicate locator")
                require(row["reason_locator"] is None and row["repeated_reason_count"] is None and row["predicate_or_rationale_locator"] is None, "converted row has nonconverted reason fields")
            else:
                require(row["source_role"] is None and row["claim_type"] is None and row["canonical_content_identity"] is None, "nonconverted row has converted strata")
                require(row["evidence_artifact_locators"] == [] and row["consumer_view_ids"] == [] and row["conversion_predicate_locator"] is None, "nonconverted row has conversion artifacts")
                _identity(row["reason_locator"], "nonconverted reason locator")
                require(isinstance(row["repeated_reason_count"], int) and row["repeated_reason_count"] >= 1, "invalid repeated reason count")
            normalized_rows.append(dict(row))
        require(row_ids == set(frozen_by_id), f"missing frozen unit id: {family_id}")
        reason_counts = Counter(
            row["reason_locator"] for row in normalized_rows
            if row["disposition_code"] != "converted"
        )
        for row in normalized_rows:
            if row["disposition_code"] == "converted":
                continue
            computed_count = reason_counts[row["reason_locator"]]
            require(row["repeated_reason_count"] == computed_count, "declared repeated reason count differs from family population")
            if computed_count >= 10:
                _identity(row["predicate_or_rationale_locator"], "repeated-reason predicate locator")
            else:
                require(row["predicate_or_rationale_locator"] is None, "unexpected nonconverted predicate locator")
        observed[family_id] = {**dict(family), "rows": sorted(normalized_rows, key=lambda item: item["unit_id"])}
    require(set(observed) == set(source_units), "disposition ledger must cover every nonlexical frozen family")
    return {
        "ok": True,
        "source_universe_receipt_sha256": receipt_hash,
        "source_universe_payload_manifest_sha256": receipt["artifact_manifest"]["payload_manifest_sha256"],
        "disposition_ledger_sha256": _ledger_hash(ledger),
        "repair_generation": ledger["repair_generation"],
        "families": [observed[family_id] for family_id in sorted(observed)],
    }


def sample_size(population_total: int, family_unit_total: int) -> int:
    """The contract formula: min(population_total, max(100, ceil(2% family)))."""
    require(isinstance(population_total, int) and population_total >= 0, "invalid population total")
    require(isinstance(family_unit_total, int) and family_unit_total >= 0, "invalid family unit total")
    return min(population_total, max(100, math.ceil(0.02 * family_unit_total)))


def _population_hash(records: Sequence[Mapping[str, Any]]) -> str:
    return sha256_value(list(records))


def _strata_allocation(records: Sequence[Mapping[str, Any]], size: int, kind: str) -> list[dict[str, Any]]:
    """Publish Hamilton (largest-remainder) proportional allocations before the seed."""
    grouped: dict[tuple[str, ...], int] = Counter(_stratum_key(record, kind) for record in records)
    total = len(records)
    allocations = {key: (size * count) // total if total else 0 for key, count in grouped.items()}
    remaining = size - sum(allocations.values())
    fractions = {key: (size * count) % total if total else 0 for key, count in grouped.items()}
    for key in sorted(grouped, key=lambda item: (-fractions[item], item))[:remaining]:
        allocations[key] += 1
    return [
        {"stratum": list(key), "population_total": grouped[key], "sample_allocation": allocations[key]}
        for key in sorted(grouped)
    ]


def freeze_audit_populations(
    ledger: Mapping[str, Any],
    *,
    source_universe_dir: Path = DEFAULT_SOURCE_UNIVERSE,
    coverage_contract: Mapping[str, Any] | None = None,
    role_contract: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Freeze the two required source populations and their exact strata before a seed."""
    coverage = coverage_contract or read_json(DEFAULT_COVERAGE_CONTRACT)
    roles = role_contract or read_json(DEFAULT_ROLE_CONTRACT)
    validated = validate_disposition_ledger(ledger, source_universe_dir=source_universe_dir, coverage_contract=coverage, role_contract=roles)
    population_families: list[dict[str, Any]] = []
    for family in validated["families"]:
        nonconverted: list[dict[str, Any]] = []
        converted: list[dict[str, Any]] = []
        for row in family["rows"]:
            if row["disposition_code"] == "converted":
                converted.append({
                    "unit_id": row["unit_id"], "source_role": row["source_role"], "claim_type": row["claim_type"],
                    "document_or_edition_identity": row["document_or_edition_identity"],
                })
            else:
                nonconverted.append({
                    "unit_id": row["unit_id"], "disposition_code": row["disposition_code"],
                    "document_or_edition_identity": row["document_or_edition_identity"],
                })
        nonconverted.sort(key=lambda row: row["unit_id"])
        converted.sort(key=lambda row: row["unit_id"])
        nonconverted_size = sample_size(len(nonconverted), family["family_unit_total"])
        converted_size = sample_size(len(converted), family["family_unit_total"])
        population_families.append({
            "family_id": family["family_id"], "family_unit_total": family["family_unit_total"],
            "nonconverted": {"total": len(nonconverted), "sample_size": nonconverted_size, "records": nonconverted, "strata": _strata_allocation(nonconverted, nonconverted_size, "nonconverted")},
            "converted": {"total": len(converted), "sample_size": converted_size, "records": converted, "strata": _strata_allocation(converted, converted_size, "converted")},
            "blocked_with_reason_total": sum(row["disposition_code"] == "blocked_with_reason" for row in family["rows"]),
        })
    base = {
        "schema_version": "phase3_disposition_population_freeze_v1", "text_free": True,
        "source_universe_receipt_sha256": validated["source_universe_receipt_sha256"],
        "source_universe_payload_manifest_sha256": validated["source_universe_payload_manifest_sha256"],
        "disposition_ledger_sha256": validated["disposition_ledger_sha256"],
        "coverage_contract_sha256": sha256_value(coverage), "role_contract_sha256": sha256_value(roles),
        "repair_generation": validated["repair_generation"], "families": population_families,
    }
    return {**base, "population_freeze_sha256": sha256_value(base)}


def _assigned_disposition_auditor(role_contract: Mapping[str, Any]) -> str:
    seats = role_contract.get("seats")
    require(isinstance(seats, list), "role contract lacks seats")
    matches = [seat for seat in seats if isinstance(seat, Mapping) and seat.get("role_id") == "disposition_auditor"]
    require(len(matches) == 1, "role contract must have one disposition auditor")
    seat = matches[0]
    require(seat.get("assignment_state") == "assigned_verified" and seat.get("controller_identity_attested") is True, "disposition auditor is not assigned and attested")
    identity = _identity(seat.get("controller_identity_id"), "assigned disposition auditor identity")
    root = role_contract.get("root")
    require(isinstance(root, Mapping), "role contract lacks root identity")
    require(identity != _identity(root.get("controller_identity_id"), "root identity"), "root identity cannot be the disposition auditor")
    return identity


def validate_seed_receipt(
    receipt: Mapping[str, Any], population_freeze: Mapping[str, Any], *, role_contract: Mapping[str, Any],
    family_id: str, population_kind: str, audit_kind: str = "source_disposition",
    repo_root: Path = ROOT, prohibited_identity_ids: Sequence[str] = (), prior_seed_receipt_sha256s: Sequence[str] = (),
) -> dict[str, Any]:
    """Validate the auditor-attested unique entropy derivation or fail closed."""
    _text_free(receipt, "seed receipt")
    _exact(receipt, {
        "schema_version", "text_free", "audit_round_id", "seed", "seed_commitment_sha256", "seed_owner_role_id",
        "auditor_controller_identity_id", "source_universe_receipt_sha256", "disposition_ledger_sha256",
        "population_freeze_sha256", "coverage_contract_sha256", "role_contract_sha256", "repair_generation",
        "results_recorded", "reroll_count", "prior_sample_reused", "proposal_identity_ids", "family_id", "population_kind",
        "population_sha256", "strata_allocation_sha256", "entropy_contract_version", "origin_main_ref",
        "first_containing_squash_merge_sha", "audit_kind", "entropy_tuple", "entropy_tuple_sha256",
        "seed_committer_controller_identity_id", "seed_attestor_controller_identity_id", "derivation_mode",
    }, "seed receipt")
    require(receipt["schema_version"] == "phase3_disposition_audit_seed_receipt_v1" and receipt["text_free"] is True, "invalid seed receipt header")
    require(isinstance(receipt["audit_round_id"], str) and ROUND_ID.fullmatch(receipt["audit_round_id"]) is not None, "invalid audit round id")
    _sha(receipt["seed"], "derived audit seed")
    require(receipt["seed_owner_role_id"] == "disposition_auditor", "wrong seed owner role")
    require(receipt["family_id"] == family_id and receipt["population_kind"] == population_kind, "seed receipt is for a different family or population")
    require(receipt["audit_kind"] == audit_kind and audit_kind in AUDIT_KINDS, "seed receipt audit kind mismatch")
    populations = {item["family_id"]: item for item in population_freeze["families"]}
    require(family_id in populations and population_kind in {"nonconverted", "converted"}, "unknown audit population")
    population = populations[family_id][population_kind]
    require(receipt["population_sha256"] == _population_hash(population["records"]), "stale seed population binding")
    require(receipt["strata_allocation_sha256"] == sha256_value(population["strata"]), "stale seed strata binding")
    assigned = _assigned_disposition_auditor(role_contract)
    for name in ("source_universe_receipt_sha256", "disposition_ledger_sha256", "population_freeze_sha256", "coverage_contract_sha256", "role_contract_sha256"):
        _sha(receipt[name], name)
        require(receipt[name] == population_freeze[name], f"stale seed receipt binding: {name}")
    require(receipt["repair_generation"] == population_freeze["repair_generation"], "stale seed receipt repair generation")
    receipt_hash = validate_common_entropy_receipt(
        receipt,
        population_freeze,
        assigned_auditor_controller_identity_id=assigned,
        audit_kind=audit_kind,
        family_id=family_id,
        population_kind=population_kind,
        population_universe_sha256=receipt["population_sha256"],
        repo_root=repo_root,
        prohibited_identity_ids=prohibited_identity_ids,
        prior_seed_receipt_sha256s=prior_seed_receipt_sha256s,
    )
    return {"ok": True, "seed_receipt_sha256": receipt_hash, "auditor_controller_identity_id": assigned, "family_id": family_id, "population_kind": population_kind}


def _rank(seed: str, domain: str, value: str) -> str:
    return sha256_bytes(f"{seed}\x00{domain}\x00{value}".encode("ascii"))


def _stratum_key(record: Mapping[str, Any], kind: str) -> tuple[str, ...]:
    if kind == "nonconverted":
        return (record["disposition_code"], record["document_or_edition_identity"])
    return (record["source_role"], record["claim_type"], record["document_or_edition_identity"])


def _stratified_ids(records: Sequence[Mapping[str, Any]], total: int, seed: str, family_id: str, kind: str, published_strata: Sequence[Mapping[str, Any]] | None = None) -> list[str]:
    require(len({record["unit_id"] for record in records}) == len(records), "population contains duplicate unit ids")
    grouped: dict[tuple[str, ...], list[Mapping[str, Any]]] = defaultdict(list)
    for record in records:
        grouped[_stratum_key(record, kind)].append(record)
    keys = sorted(grouped)
    if total == 0:
        return []
    require(total <= len(records), "sample exceeds population")
    expected_strata = _strata_allocation(records, total, kind)
    if published_strata is not None:
        require(list(published_strata) == expected_strata, "published strata/allocation table mismatch")
    allocations = {tuple(item["stratum"]): item["sample_allocation"] for item in expected_strata}
    selected: list[str] = []
    for key in keys:
        ranked = sorted(grouped[key], key=lambda row: _rank(seed, f"{family_id}:{kind}:unit", row["unit_id"]))
        selected.extend(row["unit_id"] for row in ranked[:allocations[key]])
    require(len(selected) == total and len(set(selected)) == total, "sampling without replacement failed")
    return sorted(selected)


def emit_samples(
    population_freeze: Mapping[str, Any], seed_receipts: Sequence[Mapping[str, Any]], *, ledger: Mapping[str, Any],
    role_contract: Mapping[str, Any], coverage_contract: Mapping[str, Any] | None = None,
    source_universe_dir: Path = DEFAULT_SOURCE_UNIVERSE, audit_kind: str = "source_disposition",
    repo_root: Path = ROOT, prohibited_identity_ids: Sequence[str] = (), prior_seed_receipt_sha256s: Sequence[str] = (),
) -> dict[str, Any]:
    """Deterministically select the frozen samples from an already supplied auditor seed."""
    _text_free(population_freeze, "population freeze")
    _exact(population_freeze, {
        "schema_version", "text_free", "source_universe_receipt_sha256", "source_universe_payload_manifest_sha256",
        "disposition_ledger_sha256", "coverage_contract_sha256", "role_contract_sha256", "repair_generation", "families", "population_freeze_sha256",
    }, "population freeze")
    base = {key: value for key, value in population_freeze.items() if key != "population_freeze_sha256"}
    require(population_freeze["schema_version"] == "phase3_disposition_population_freeze_v1" and population_freeze["text_free"] is True, "invalid population freeze header")
    require(population_freeze["population_freeze_sha256"] == sha256_value(base), "population freeze hash mismatch")
    coverage = coverage_contract or read_json(DEFAULT_COVERAGE_CONTRACT)
    recomputed_freeze = freeze_audit_populations(
        ledger,
        source_universe_dir=source_universe_dir,
        coverage_contract=coverage,
        role_contract=role_contract,
    )
    require(canonical_json(population_freeze) == canonical_json(recomputed_freeze), "population freeze differs from freshly derived disposition ledger population")
    require(isinstance(seed_receipts, Sequence) and not isinstance(seed_receipts, (str, bytes)), "per-population seed receipts must be a list")
    receipt_by_population: dict[tuple[str, str], Mapping[str, Any]] = {}
    for seed_receipt in seed_receipts:
        require(isinstance(seed_receipt, Mapping), "seed receipt must be an object")
        key = (seed_receipt.get("family_id"), seed_receipt.get("population_kind"))
        require(all(isinstance(item, str) for item in key) and key not in receipt_by_population, "duplicate or invalid per-population seed receipt")
        receipt_by_population[key] = seed_receipt
    samples: list[dict[str, Any]] = []
    for family in population_freeze["families"]:
        require(isinstance(family, Mapping), "population family must be an object")
        _exact(family, {"family_id", "family_unit_total", "nonconverted", "converted", "blocked_with_reason_total"}, "population family")
        for kind in ("nonconverted", "converted"):
            population = family[kind]
            require(isinstance(population, Mapping), "population must be an object")
            _exact(population, {"total", "sample_size", "records", "strata"}, "population")
            records = population["records"]
            require(isinstance(records, list) and population["total"] == len(records), "population total mismatch")
            expected_size = sample_size(population["total"], family["family_unit_total"])
            require(population["sample_size"] == expected_size, "sample formula mismatch")
            receipt = receipt_by_population.get((family["family_id"], kind))
            require(receipt is not None, "missing per-population seed receipt")
            seed = validate_seed_receipt(receipt, population_freeze, role_contract=role_contract, family_id=family["family_id"], population_kind=kind, audit_kind=audit_kind, repo_root=repo_root, prohibited_identity_ids=prohibited_identity_ids, prior_seed_receipt_sha256s=prior_seed_receipt_sha256s)
            ids = _stratified_ids(records, expected_size, receipt["seed"], family["family_id"], kind, population["strata"])
            samples.append({"family_id": family["family_id"], "sample_kind": kind, "sample_size": expected_size, "unit_ids": ids, "population_sha256": _population_hash(records), "strata_allocation_sha256": sha256_value(population["strata"]), "seed_receipt_sha256": seed["seed_receipt_sha256"], "auditor_controller_identity_id": seed["auditor_controller_identity_id"], "blocked_with_reason_total": family["blocked_with_reason_total"]})
    require(set(receipt_by_population) == {(item["family_id"], kind) for item in population_freeze["families"] for kind in ("nonconverted", "converted")}, "extra seed receipt or missing audit population")
    base_manifest = {
        "schema_version": "phase3_disposition_sample_manifest_v1", "text_free": True,
        "source_universe_receipt_sha256": population_freeze["source_universe_receipt_sha256"],
        "disposition_ledger_sha256": population_freeze["disposition_ledger_sha256"],
        "population_freeze_sha256": population_freeze["population_freeze_sha256"],
        "repair_generation": population_freeze["repair_generation"],
        "samples": sorted(samples, key=lambda item: (item["family_id"], item["sample_kind"])),
    }
    return {**base_manifest, "sample_manifest_sha256": sha256_value(base_manifest)}


def validate_audit_results(
    results: Mapping[str, Any],
    sample_manifest: Mapping[str, Any],
    *,
    ledger: Mapping[str, Any],
    population_freeze: Mapping[str, Any],
    seed_receipts: Sequence[Mapping[str, Any]],
    coverage_contract: Mapping[str, Any],
    role_contract: Mapping[str, Any],
    source_universe_dir: Path = DEFAULT_SOURCE_UNIVERSE,
    audit_kind: str = "source_disposition",
    repo_root: Path = ROOT,
    prohibited_identity_ids: Sequence[str] = (),
    prior_seed_receipt_sha256s: Sequence[str] = (),
) -> dict[str, Any]:
    """Require exact sample coverage, valid result codes, and both zero-miss gates."""
    _text_free(results, "audit results")
    _exact(results, {"schema_version", "text_free", "sample_manifest_sha256", "population_freeze_sha256", "repair_generation", "results"}, "audit results")
    require(results["schema_version"] == "phase3_disposition_audit_results_v1" and results["text_free"] is True, "invalid audit results header")
    recomputed_manifest = emit_samples(
        population_freeze,
        seed_receipts,
        ledger=ledger,
        role_contract=role_contract,
        coverage_contract=coverage_contract,
        source_universe_dir=source_universe_dir,
        audit_kind=audit_kind,
        repo_root=repo_root,
        prohibited_identity_ids=prohibited_identity_ids,
        prior_seed_receipt_sha256s=prior_seed_receipt_sha256s,
    )
    require(canonical_json(sample_manifest) == canonical_json(recomputed_manifest), "sample manifest differs from deterministic population-freeze selection")
    manifest_base = {key: value for key, value in sample_manifest.items() if key != "sample_manifest_sha256"}
    require(sample_manifest.get("sample_manifest_sha256") == sha256_value(manifest_base), "sample manifest integrity mismatch")
    for field in ("sample_manifest_sha256", "population_freeze_sha256"):
        require(results[field] == sample_manifest[field], f"stale audit result binding: {field}")
    require(results["repair_generation"] == sample_manifest["repair_generation"], "stale audit results repair generation")
    expected: dict[tuple[str, str, str], tuple[set[str], str]] = {}
    pairs: set[tuple[str, str]] = set()
    for sample in sample_manifest["samples"]:
        require(isinstance(sample, Mapping), "sample manifest entry must be an object")
        _exact(sample, {"family_id", "sample_kind", "sample_size", "unit_ids", "population_sha256", "strata_allocation_sha256", "seed_receipt_sha256", "auditor_controller_identity_id", "blocked_with_reason_total"}, "sample manifest entry")
        pair = (sample["family_id"], sample["sample_kind"])
        require(pair not in pairs, "duplicate population sample")
        pairs.add(pair)
        require(sample["sample_size"] == len(sample["unit_ids"]) == len(set(sample["unit_ids"])), "sample manifest without-replacement integrity failure")
        allowed = NONCONVERTED_DECISION_CODES if sample["sample_kind"] == "nonconverted" else CONVERTED_MISS_CODES | {"agree"}
        for unit_id in sample["unit_ids"]:
            expected[(sample["family_id"], sample["sample_kind"], unit_id)] = (allowed, sample["auditor_controller_identity_id"])
    families = {family_id for family_id, _ in pairs}
    require(pairs == {(family_id, kind) for family_id in families for kind in ("nonconverted", "converted")}, "paired nonconverted/converted population acceptance is incomplete")
    observed: set[tuple[str, str, str]] = set()
    for result in results["results"]:
        require(isinstance(result, Mapping), "audit result must be an object")
        _exact(result, {"family_id", "sample_kind", "unit_id", "decision_code", "auditor_controller_identity_id", "evidence_artifact_locators"}, "audit result")
        key = (result["family_id"], result["sample_kind"], result["unit_id"])
        require(key in expected and key not in observed, "duplicate, missing, or unsampled audit result")
        require(result["decision_code"] in expected[key][0], "invalid audit decision code")
        require(result["auditor_controller_identity_id"] == expected[key][1] == _assigned_disposition_auditor(role_contract), "result identity is not the assigned disposition auditor")
        require(isinstance(result["evidence_artifact_locators"], list) and result["evidence_artifact_locators"], "audit result lacks evidence references")
        for locator in result["evidence_artifact_locators"]:
            _identity(locator, "audit evidence reference")
        observed.add(key)
    require(observed == set(expected), "audit results do not cover exact sample")
    require(all(sample.get("blocked_with_reason_total") == 0 for sample in sample_manifest["samples"]), "blocked_with_reason cannot be accepted for source coverage")
    nonagree = [key for key in observed if next(item["decision_code"] for item in results["results"] if (item["family_id"], item["sample_kind"], item["unit_id"]) == key) != "agree"]
    require(not nonagree, "zero-nonagree/zero-miss gate failed; repair, new freeze, and fresh samples are required")
    return {"ok": True, "sample_manifest_sha256": sample_manifest["sample_manifest_sha256"], "result_count": len(observed), "zero_miss": True}


def validate_bundle(
    bundle: Mapping[str, Any],
    *,
    ledger: Mapping[str, Any],
    population_freeze: Mapping[str, Any],
    seed_receipts: Sequence[Mapping[str, Any]],
    sample_manifest: Mapping[str, Any],
    results: Mapping[str, Any],
    coverage_contract: Mapping[str, Any],
    role_contract: Mapping[str, Any],
    source_universe_dir: Path = DEFAULT_SOURCE_UNIVERSE,
    repo_root: Path = ROOT,
) -> dict[str, Any]:
    """Recompute every disposition-audit bundle binding from supplied artifacts."""
    _text_free(bundle, "audit bundle")
    _exact(bundle, {
        "schema_version", "text_free", "source_universe_receipt_sha256", "coverage_contract_sha256",
        "role_contract_sha256", "disposition_ledger_sha256", "population_freeze_sha256",
        "seed_receipt_sha256s", "sample_manifest_sha256", "audit_results_sha256",
    }, "audit bundle")
    require(bundle["schema_version"] == "phase3_disposition_audit_bundle_v1" and bundle["text_free"] is True, "invalid audit bundle header")
    result = validate_audit_results(
        results,
        sample_manifest,
        ledger=ledger,
        population_freeze=population_freeze,
        seed_receipts=seed_receipts,
        coverage_contract=coverage_contract,
        role_contract=role_contract,
        source_universe_dir=source_universe_dir,
        repo_root=repo_root,
    )
    expected = {
        "source_universe_receipt_sha256": population_freeze["source_universe_receipt_sha256"],
        "coverage_contract_sha256": sha256_value(coverage_contract),
        "role_contract_sha256": sha256_value(role_contract),
        "disposition_ledger_sha256": sha256_value(ledger),
        "population_freeze_sha256": population_freeze["population_freeze_sha256"],
        "seed_receipt_sha256s": sorted(sha256_value(receipt) for receipt in seed_receipts),
        "sample_manifest_sha256": sample_manifest["sample_manifest_sha256"],
        "audit_results_sha256": sha256_value(results),
    }
    for field, value in expected.items():
        require(bundle[field] == value, f"audit bundle binding mismatch: {field}")
    return {
        "ok": True,
        "bundle_verified": True,
        "population_freeze_sha256": population_freeze["population_freeze_sha256"],
        "sample_manifest_sha256": result["sample_manifest_sha256"],
        "result_count": result["result_count"],
    }


def validate_lexical_complete_census(census: Mapping[str, Any], *, source_universe_dir: Path = DEFAULT_SOURCE_UNIVERSE, coverage_contract: Mapping[str, Any] | None = None, role_contract: Mapping[str, Any] | None = None, population_freeze: Mapping[str, Any] | None = None, prohibited_identity_ids: Sequence[str] = ()) -> dict[str, Any]:
    """Validate a complete lexical used-subset census; it intentionally has no seed path."""
    coverage = coverage_contract or read_json(DEFAULT_COVERAGE_CONTRACT)
    roles = role_contract or read_json(DEFAULT_ROLE_CONTRACT)
    # V2 is the closed-manifest implementation.  Keep V1 verification only for
    # historical receipts; V1 cannot claim current coverage readiness.
    if census.get("schema_version") == "phase3_lexical_complete_census_v2":
        require(population_freeze is not None, "closed lexical census requires its population freeze")
        from scripts.projects.open_model_data import phase3_lexical_coverage as lexical

        try:
            return lexical.validate_complete_census(
                census,
                population_freeze,
                role_contract=roles,
                prohibited_identity_ids=prohibited_identity_ids,
            )
        except lexical.LexicalCoverageError as exc:
            raise AuditError(str(exc)) from exc
    _text_free(census, "lexical census")
    _exact(census, {"schema_version", "text_free", "source_universe_receipt_sha256", "coverage_contract_sha256", "role_contract_sha256", "release_artifact_manifest_sha256", "used_subset_extraction_artifact_sha256", "auditor_controller_identity_id", "families"}, "lexical census")
    require(census["schema_version"] == "phase3_lexical_complete_census_v1" and census["text_free"] is True, "invalid lexical census header")
    _, receipt_hash, _ = _source_receipt(source_universe_dir)
    require(census["source_universe_receipt_sha256"] == receipt_hash, "stale lexical census source binding")
    require(census["coverage_contract_sha256"] == sha256_value(coverage) and census["role_contract_sha256"] == sha256_value(roles), "stale lexical census contract binding")
    require(census["auditor_controller_identity_id"] == _assigned_disposition_auditor(roles), "lexical census identity is not the assigned disposition auditor")
    _sha(census["release_artifact_manifest_sha256"], "release artifact manifest")
    _sha(census["used_subset_extraction_artifact_sha256"], "used-subset extraction artifact")
    structural = read_json(source_universe_dir / source_freeze.STRUCTURAL_FILE)
    expected = {item["family_id"]: item["ordered_rolling_sha256"] for item in structural["families"]}
    seen: set[str] = set()
    for family in census["families"]:
        require(isinstance(family, Mapping), "lexical census family must be an object")
        _exact(family, {"family_id", "structural_universe_sha256", "used_subset_census_sha256", "used_subset_total", "rows"}, "lexical census family")
        family_id = family["family_id"]
        require(family_id in expected and family_id not in seen, "unknown or duplicate lexical census family")
        seen.add(family_id)
        require(family["structural_universe_sha256"] == expected[family_id], "lexical structural identity mismatch")
        _sha(family["used_subset_census_sha256"], "lexical used subset census")
        rows = family["rows"]
        require(isinstance(rows, list) and len(rows) == family["used_subset_total"], "lexical used-subset total mismatch")
        ids: set[str] = set()
        for row in rows:
            require(isinstance(row, Mapping), "lexical census row must be an object")
            _exact(row, {"used_subset_unit_id", "used_subset_unit_sha256", "decision_code", "evidence_artifact_locators"}, "lexical census row")
            unit_id = _identity(row["used_subset_unit_id"], "used-subset unit identity")
            require(unit_id not in ids, "duplicate lexical used-subset unit")
            ids.add(unit_id)
            _sha(row["used_subset_unit_sha256"], "used-subset unit hash")
            require(row["decision_code"] in LEXICAL_DECISION_CODES, "invalid lexical decision code")
            require(isinstance(row["evidence_artifact_locators"], list) and row["evidence_artifact_locators"], "lexical census row lacks extraction evidence")
            for locator in row["evidence_artifact_locators"]:
                _identity(locator, "lexical extraction evidence")
        require(family["used_subset_census_sha256"] == sha256_value(sorted(rows, key=lambda item: item["used_subset_unit_id"])), "lexical census row hash mismatch")
        require(all(row["decision_code"] == "agree" for row in rows), "lexical complete-census zero-nonagree gate failed")
    require(seen == set(expected), "lexical census must cover every lexical frozen family")
    return {"ok": True, "family_count": len(seen), "complete_census": True, "seed_required": False}


def validate_lexical_structural_audit(
    receipt: Mapping[str, Any], *, source_universe_dir: Path = DEFAULT_SOURCE_UNIVERSE,
    coverage_contract: Mapping[str, Any] | None = None, role_contract: Mapping[str, Any] | None = None,
    sources_db: Path, vesum_db: Path, r2u_cache: Path,
) -> dict[str, Any]:
    """Expose the independent complete structural lexical audit primitive."""
    from scripts.projects.open_model_data import phase3_lexical_coverage as lexical

    try:
        return lexical.validate_structural_audit(
            receipt,
            source_universe_dir=source_universe_dir,
            coverage_contract=coverage_contract or read_json(DEFAULT_COVERAGE_CONTRACT),
            role_contract=role_contract or read_json(DEFAULT_ROLE_CONTRACT),
            sources_db=sources_db,
            vesum_db=vesum_db,
            r2u_cache=r2u_cache,
        )
    except lexical.LexicalCoverageError as exc:
        raise AuditError(str(exc)) from exc


def freeze_lexical_used_subset_population(
    release_manifest: Mapping[str, Any], *, release_root: Path,
    source_universe_dir: Path = DEFAULT_SOURCE_UNIVERSE, coverage_contract: Mapping[str, Any] | None = None,
    role_contract: Mapping[str, Any] | None = None, sources_db: Path, vesum_db: Path, r2u_cache: Path,
    repair_generation: int,
) -> dict[str, Any]:
    """Freeze exact typed release references before the lexical census starts."""
    from scripts.projects.open_model_data import phase3_lexical_coverage as lexical

    try:
        return lexical.freeze_used_subset_population(
            release_manifest,
            release_root=release_root,
            source_universe_dir=source_universe_dir,
            coverage_contract=coverage_contract or read_json(DEFAULT_COVERAGE_CONTRACT),
            role_contract=role_contract or read_json(DEFAULT_ROLE_CONTRACT),
            sources_db=sources_db,
            vesum_db=vesum_db,
            r2u_cache=r2u_cache,
            repair_generation=repair_generation,
        )
    except lexical.LexicalCoverageError as exc:
        raise AuditError(str(exc)) from exc


def _print(value: Mapping[str, Any]) -> None:
    sys.stdout.write(canonical_json(value) + "\n")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-universe", type=Path, default=DEFAULT_SOURCE_UNIVERSE)
    parser.add_argument("--coverage-contract", type=Path, default=DEFAULT_COVERAGE_CONTRACT)
    parser.add_argument("--role-contract", type=Path, default=DEFAULT_ROLE_CONTRACT)
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("validate-ledger", "freeze-populations"):
        item = commands.add_parser(name)
        item.add_argument("--ledger", type=Path, required=True)
    item = commands.add_parser("emit-samples")
    item.add_argument("--ledger", type=Path, required=True)
    item.add_argument("--population-freeze", type=Path, required=True)
    item.add_argument("--seed-receipt", type=Path, action="append", required=True)
    item.add_argument("--prohibited-identity", action="append", default=[])
    item.add_argument("--prior-seed-receipt-sha256", action="append", default=[])
    item.add_argument("--audit-kind", choices=sorted(AUDIT_KINDS), default="source_disposition")
    item = commands.add_parser("validate-results")
    item.add_argument("--ledger", type=Path, required=True)
    item.add_argument("--sample-manifest", type=Path, required=True)
    item.add_argument("--population-freeze", type=Path, required=True)
    item.add_argument("--seed-receipt", type=Path, action="append", required=True)
    item.add_argument("--prohibited-identity", action="append", default=[])
    item.add_argument("--prior-seed-receipt-sha256", action="append", default=[])
    item.add_argument("--audit-kind", choices=sorted(AUDIT_KINDS), default="source_disposition")
    item.add_argument("--results", type=Path, required=True)
    item = commands.add_parser("validate-bundle")
    item.add_argument("--bundle", type=Path, required=True)
    item.add_argument("--ledger", type=Path, required=True)
    item.add_argument("--population-freeze", type=Path, required=True)
    item.add_argument("--seed-receipt", type=Path, action="append", required=True)
    item.add_argument("--sample-manifest", type=Path, required=True)
    item.add_argument("--results", type=Path, required=True)
    item = commands.add_parser("validate-lexical-census")
    item.add_argument("--census", type=Path, required=True)
    item = commands.add_parser("validate-lexical-structural-audit")
    item.add_argument("--receipt", type=Path, required=True)
    item.add_argument("--sources-db", type=Path, required=True)
    item.add_argument("--vesum-db", type=Path, required=True)
    item.add_argument("--r2u-cache", type=Path, required=True)
    item = commands.add_parser("freeze-lexical-used-subset")
    item.add_argument("--release-manifest", type=Path, required=True)
    item.add_argument("--release-root", type=Path, required=True)
    item.add_argument("--sources-db", type=Path, required=True)
    item.add_argument("--vesum-db", type=Path, required=True)
    item.add_argument("--r2u-cache", type=Path, required=True)
    item.add_argument("--repair-generation", type=int, required=True)
    item = commands.add_parser("validate-lexical-census-v2")
    item.add_argument("--census", type=Path, required=True)
    item.add_argument("--population-freeze", type=Path, required=True)
    item.add_argument("--prohibited-identity", action="append", default=[])
    item = commands.add_parser("validate-lexical-bundle")
    item.add_argument("--bundle", type=Path, required=True)
    item.add_argument("--structural-audit", type=Path, required=True)
    item.add_argument("--population-freeze", type=Path, required=True)
    item.add_argument("--census", type=Path, required=True)
    item.add_argument("--sources-db", type=Path, required=True)
    item.add_argument("--vesum-db", type=Path, required=True)
    item.add_argument("--r2u-cache", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        coverage, roles = read_json(args.coverage_contract), read_json(args.role_contract)
        if args.command == "validate-ledger":
            _print(validate_disposition_ledger(read_json(args.ledger), source_universe_dir=args.source_universe, coverage_contract=coverage, role_contract=roles))
        elif args.command == "freeze-populations":
            _print(freeze_audit_populations(read_json(args.ledger), source_universe_dir=args.source_universe, coverage_contract=coverage, role_contract=roles))
        elif args.command == "emit-samples":
            _print(emit_samples(read_json(args.population_freeze), [read_json(path) for path in args.seed_receipt], ledger=read_json(args.ledger), role_contract=roles, coverage_contract=coverage, source_universe_dir=args.source_universe, audit_kind=args.audit_kind, prohibited_identity_ids=args.prohibited_identity, prior_seed_receipt_sha256s=args.prior_seed_receipt_sha256))
        elif args.command == "validate-results":
            _print(validate_audit_results(read_json(args.results), read_json(args.sample_manifest), ledger=read_json(args.ledger), population_freeze=read_json(args.population_freeze), seed_receipts=[read_json(path) for path in args.seed_receipt], coverage_contract=coverage, role_contract=roles, source_universe_dir=args.source_universe, audit_kind=args.audit_kind, prohibited_identity_ids=args.prohibited_identity, prior_seed_receipt_sha256s=args.prior_seed_receipt_sha256))
        elif args.command == "validate-bundle":
            _print(validate_bundle(read_json(args.bundle), ledger=read_json(args.ledger), population_freeze=read_json(args.population_freeze), seed_receipts=[read_json(path) for path in args.seed_receipt], sample_manifest=read_json(args.sample_manifest), results=read_json(args.results), coverage_contract=coverage, role_contract=roles, source_universe_dir=args.source_universe))
        elif args.command == "validate-lexical-census":
            _print(validate_lexical_complete_census(read_json(args.census), source_universe_dir=args.source_universe, coverage_contract=coverage, role_contract=roles))
        elif args.command == "validate-lexical-structural-audit":
            _print(validate_lexical_structural_audit(read_json(args.receipt), source_universe_dir=args.source_universe, coverage_contract=coverage, role_contract=roles, sources_db=args.sources_db, vesum_db=args.vesum_db, r2u_cache=args.r2u_cache))
        elif args.command == "freeze-lexical-used-subset":
            _print(freeze_lexical_used_subset_population(read_json(args.release_manifest), release_root=args.release_root, source_universe_dir=args.source_universe, coverage_contract=coverage, role_contract=roles, sources_db=args.sources_db, vesum_db=args.vesum_db, r2u_cache=args.r2u_cache, repair_generation=args.repair_generation))
        else:
            from scripts.projects.open_model_data import phase3_lexical_coverage as lexical

            if args.command == "validate-lexical-census-v2":
                _print(validate_lexical_complete_census(read_json(args.census), population_freeze=read_json(args.population_freeze), coverage_contract=coverage, role_contract=roles, prohibited_identity_ids=args.prohibited_identity))
            else:
                _print(lexical.validate_lexical_bundle(read_json(args.bundle), structural_audit=read_json(args.structural_audit), population_freeze=read_json(args.population_freeze), census=read_json(args.census), role_contract=roles, coverage_contract=coverage, sources_db=args.sources_db, vesum_db=args.vesum_db, r2u_cache=args.r2u_cache, source_universe_dir=args.source_universe))
    except ValueError as exc:
        parser.error(str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
