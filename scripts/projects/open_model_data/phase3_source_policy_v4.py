#!/usr/bin/env python3
"""Build and validate the complete Phase 3 30-source policy.

The policy is text-free and default-deny. It converts the reviewed university
admission gate into one machine-readable source universe while preserving the
context-only and quarantine lanes. It does not authorize live database ingest,
the complete source freeze, Phase 3 completion, or Phase 4.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
from collections import Counter
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from scripts.projects.open_model_data import (
    phase3_university_source_admission as admission,
)

SCHEMA_VERSION = "phase3_complete_source_policy_v4"
SCHEMA_PATH = ROOT / "data/projects/open_model_data/contracts/phase3_complete_source_policy_v4.schema.json"
DEFAULT_POLICY_PATH = ROOT / "data/projects/open_model_data/admission/phase3_complete_source_policy_v4.json"
DEFAULT_V3_POLICY_PATH = ROOT / "data/projects/open_model_data/admission/phase3_university_source_policy_v3.json"
EXPECTED_POLICY_SHA256 = "98e7a80f8fdc1274a190cda793699aceaa79741ebf2145669d73e4c8a2236559"

EXPECTED_INPUT_HASHES = {
    "phase3_reboot_prompt_v3_sha256": ("5f22c7fc84ce6ca6d497fcf0437d72274a0bdb3aa1cf48cfebfe196e67dbd11d"),
    "phase3_recovery_prompt_v2_sha256": ("298591094d1281629ea444707909b679d1a5368f3ad8afddf39120bc0c34532b"),
    "university_source_matrix_v3_sha256": ("e2e82934ec26b7d98002cdf87f5326b84fb2d3d7900fe675920ba99e84d190de"),
    "university_source_admission_gate_v1_sha256": ("423275e09192e593cdcc3b31b5074c860ada9e735d94a0857fc802d5dc9ef755"),
    "university_source_policy_v3_sha256": ("2cb3643cec48acc52e9163e8ad1a21360de3380584a62a1a08ad07800b1c731d"),
    "university_corpus_reconciliation_v3_sha256": ("3a4abb3883ad06db3fea1f994a5b51bc22cbdd6ab3e8d3adaf72c180bc42dd65"),
    "pr6630_drive_backup_receipt_sha256": ("f577ab1cec2b2dee99e033284f1801f723a3d741e9e7c050d32cec0494b52d81"),
}
PR6630_MERGE_COMMIT = "d117a9c5bab7f309e78607b540ac8931a6bc3b4c"

STAGED_JSONL_SPECS: dict[str, dict[str, Any]] = {
    "uni-ukrmova-corpus-linguistics-khpi-2021-part-1": {
        "source_locator": (
            "university_corpus/staging/phase3-6375-waves-b-e/wave-b/"
            "uni-ukrmova-corpus-linguistics-khpi-2021-part-1.jsonl"
        ),
        "jsonl_sha256": "00cfd4f8d6185b9116992311891a883753218e6a27b52f6e9f291f37e66366af",
        "rows_sha256": "e46aee2f63238a73a050374a02aeea9a673b10e7e3fbec9678a9e0e55f9e22f9",
        "expected_rows": 47,
        "audience_class": "A_ukrainian_university_audience",
        "subject_role": "ukrainian_linguistics",
    },
    "uni-ukrmova-corpus-linguistics-khpi-2021-part-2": {
        "source_locator": (
            "university_corpus/staging/phase3-6375-waves-b-e/wave-b/"
            "uni-ukrmova-corpus-linguistics-khpi-2021-part-2.jsonl"
        ),
        "jsonl_sha256": "5ac5d5495aee21ff756156fda362f4e2340de9021380917c0bf9c74b9440e84b",
        "rows_sha256": "c50d686392788437858fd699b0c75e1e50384e447b92a30cdeeaf68623e9013a",
        "expected_rows": 51,
        "audience_class": "A_ukrainian_university_audience",
        "subject_role": "ukrainian_linguistics",
    },
    "uni-ukrmova-morphology-volkova-maslo-2012": {
        "source_locator": (
            "university_corpus/staging/phase3-6375-waves-b-e/wave-d/uni-ukrmova-morphology-volkova-maslo-2012.jsonl"
        ),
        "jsonl_sha256": "0229ba6526f863b1500533693032d31e29b9e3f9456dd15aa7a1704f14dec54e",
        "rows_sha256": "96fe0d5f52828c9529f7e2b05f5f2050f63667ad087a70117a015c6244608db9",
        "expected_rows": 205,
        "audience_class": "A_ukrainian_university_audience",
        "subject_role": "ukrainian_linguistics",
    },
    "uni-ukrmova-text-linguistics-shevel-bilyk-2024": {
        "source_locator": (
            "university_corpus/staging/phase3-6375-wave-a/grade-00/uni-ukrmova-text-linguistics-shevel-bilyk-2024.jsonl"
        ),
        "jsonl_sha256": "26848855c02a8ac6c02b7320d2b4a1986397a897c0a6d9df9ade720c20339920",
        "rows_sha256": "10b5f59f1852b7a7f7337b52ccb855ce7d04345466f670c5161106c928646273",
        "expected_rows": 282,
        "audience_class": "A_ukrainian_university_audience",
        "subject_role": "ukrainian_linguistics",
    },
}
STAGED_IDS = frozenset(STAGED_JSONL_SPECS)
STAGED_EXPECTED_ROWS = {source_id: int(spec["expected_rows"]) for source_id, spec in STAGED_JSONL_SPECS.items()}
POST_2019_AUTHORITY_RESTRICTIONS = admission.POST_2019_AUTHORITY_RESTRICTIONS
NONCOMMERCIAL_RESTRICTION = admission.NONCOMMERCIAL_RESTRICTION
CONTEXTUAL_USE_OVERRIDES = {
    "uni-ukrmova-dialectology-torchynska-2017": {
        "supported_uses": [
            "regional_dialect_variation_context",
            "comparative_dialect_phonetics_and_vocabulary",
            "sociolinguistic_geography_reference",
        ],
        "prohibited_uses": [
            "modern_standard_normative_grammar_authority",
            "normative_orthography_or_spellcheck_authority",
        ],
    },
    "uni-ukrmova-historical-grammar-kupchynska-piletskyi-2024": {
        "supported_uses": [
            "historical_diachronic_grammar_context",
            "diachronic_sound_change_and_morphological_evolution",
        ],
        "prohibited_uses": [
            "modern_normative_grammar_authority",
            "modern_orthography_enforcement",
        ],
    },
    "uni-ukrmova-sociolinguistics-masenko-2010": {
        "supported_uses": [
            "sociolinguistic_and_language_policy_context",
            "surzhyk_and_language_contact_analysis",
        ],
        "prohibited_uses": ["modern_standard_normative_grammar_authority"],
    },
}


class CompleteSourcePolicyError(ValueError):
    """The complete Phase 3 source policy is incomplete or unsafe."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise CompleteSourcePolicyError(message)


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CompleteSourcePolicyError(f"cannot read JSON artifact: {path}") from exc
    require(isinstance(value, dict), f"JSON artifact must be an object: {path}")
    return value


def write_text_atomic(path: Path, text: str) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    require(not path.is_symlink(), f"refusing symlink output: {path}")
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temporary_path = Path(handle.name)
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, path)
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()


def load_jsonl_rows(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    try:
        with Path(path).open(encoding="utf-8") as stream:
            for line_number, line in enumerate(stream, start=1):
                if not line.strip():
                    continue
                value = json.loads(line)
                require(isinstance(value, dict), f"JSONL line {line_number} is not an object")
                rows.append(value)
    except (OSError, json.JSONDecodeError) as exc:
        raise CompleteSourcePolicyError(f"cannot read staged JSONL: {path}") from exc
    require(rows, f"staged JSONL is empty: {path}")
    return rows


def evidence_rows_sha256(rows: list[dict[str, Any]], *, page_start: int, page_end: int) -> str:
    selected: list[dict[str, Any]] = []
    for row in rows:
        row_start = row.get("page_start")
        row_end = row.get("page_end")
        if not isinstance(row_start, int) or not isinstance(row_end, int):
            continue
        if row_end < page_start or row_start > page_end:
            continue
        selected.append(
            {
                "chunk_id": row.get("chunk_id"),
                "page_start": row_start,
                "page_end": row_end,
                "text": row.get("text"),
            }
        )
    require(selected, f"evidence pages {page_start}-{page_end} contain no JSONL rows")
    return hashlib.sha256(canonical_json(selected).encode("utf-8")).hexdigest()


def _schema() -> dict[str, Any]:
    schema = read_json(SCHEMA_PATH)
    Draft202012Validator.check_schema(schema)
    return schema


def _schema_errors(value: Mapping[str, Any]) -> list[Any]:
    return sorted(
        Draft202012Validator(_schema()).iter_errors(value),
        key=lambda error: tuple(str(part) for part in error.absolute_path),
    )


def _v3_policy_sources(policy: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    require(policy.get("schema_version") == "phase3_university_source_policy_v3", "v3 policy schema drift")
    require(policy.get("status") == "ACTIVE_DEFAULT_DENY", "v3 policy is not active")
    sources = policy.get("sources")
    require(isinstance(sources, list) and len(sources) == 20, "v3 policy must contain exactly 20 sources")
    by_id: dict[str, dict[str, Any]] = {}
    for source in sources:
        require(isinstance(source, dict), "v3 policy source is not an object")
        source_id = source.get("source_file")
        require(isinstance(source_id, str) and source_id, "v3 policy source ID is absent")
        require(source_id not in by_id, f"v3 policy duplicates {source_id}")
        by_id[source_id] = dict(source)
    require(list(by_id) == sorted(by_id), "v3 policy sources are not sorted")
    return by_id


def _jsonl_evidence_from_v3(source_id: str, source: Mapping[str, Any]) -> dict[str, Any]:
    evidence = source["evidence"]
    return {
        "source_locator": f"university_corpus/jsonl/grade-00/{source_id}.jsonl",
        "audience_class": source["audience_class"],
        "subject_role": source["subject_role"],
        "evidence_kind": evidence["kind"],
        "jsonl_sha256": evidence["jsonl_sha256"],
        "page_start": evidence["page_start"],
        "page_end": evidence["page_end"],
        "rows_sha256": evidence["rows_sha256"],
    }


def _jsonl_evidence_from_staged(source_id: str) -> dict[str, Any]:
    spec = STAGED_JSONL_SPECS[source_id]
    return {
        "source_locator": spec["source_locator"],
        "audience_class": spec["audience_class"],
        "subject_role": spec["subject_role"],
        "evidence_kind": "jsonl_front_matter",
        "jsonl_sha256": spec["jsonl_sha256"],
        "page_start": 1,
        "page_end": 4,
        "rows_sha256": spec["rows_sha256"],
    }


def _normalized_custody_state(
    source_id: str,
    *,
    final_disposition: str,
    v3_source: Mapping[str, Any] | None,
    matrix_row: Mapping[str, Any],
) -> str:
    if final_disposition == "quarantine":
        return "quarantined_not_database_resident"
    if source_id in STAGED_IDS:
        return "staged_drive_backed"
    if v3_source is not None:
        return "database_resident_and_drive_backed"
    if matrix_row.get("custody_state") == "not_downloaded":
        return "locator_only"
    return "reference_drive_backed"


def _matrix_evidence_hash(matrix_row: Mapping[str, Any]) -> str:
    for key in (
        "evidence_receipt_sha256",
        "receipt_sha256",
        "quarantine_decision_sha256",
        "sha256_hash",
    ):
        value = matrix_row.get(key)
        if isinstance(value, str) and len(value) == 64:
            return value
    raise CompleteSourcePolicyError(f"{matrix_row.get('source_id')}: matrix row has no hash-bound evidence")


def _contextual_uses(source_id: str, matrix_row: Mapping[str, Any]) -> tuple[list[str], list[str]]:
    override = CONTEXTUAL_USE_OVERRIDES.get(source_id)
    if override is not None:
        return list(override["supported_uses"]), list(override["prohibited_uses"])
    return list(matrix_row["supported_uses"]), list(matrix_row["prohibited_uses"])


def validate_staged_jsonls(paths: Mapping[str, Path]) -> None:
    require(set(paths) == STAGED_IDS, "staged JSONL path set is not the exact four-source denominator")
    for source_id, spec in STAGED_JSONL_SPECS.items():
        path = Path(paths[source_id])
        require(path.is_file(), f"{source_id}: staged JSONL is missing")
        require(path.stem == source_id, f"{source_id}: staged JSONL filename drift")
        require(sha256_file(path) == spec["jsonl_sha256"], f"{source_id}: staged JSONL byte drift")
        rows = load_jsonl_rows(path)
        require(len(rows) == spec["expected_rows"], f"{source_id}: staged row-count drift")
        require(
            evidence_rows_sha256(rows, page_start=1, page_end=4) == spec["rows_sha256"],
            f"{source_id}: front-matter evidence drift",
        )


def _validate_matrix_and_gate(
    matrix: Mapping[str, Any], gate: Mapping[str, Any]
) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    source_set = admission.derive_source_set_check(matrix)
    require(source_set["total_unique_sources"] == 30, "source matrix is not the complete 30-source universe")
    require(
        all(source_set[key] for key in ("no_extras", "no_omissions", "no_duplicate_credit", "quarantines_preserved")),
        "source matrix completeness or quarantine preservation failed",
    )
    gate_schema = read_json(admission.GATE_SCHEMA_PATH)
    errors = sorted(
        Draft202012Validator(gate_schema).iter_errors(gate),
        key=lambda error: tuple(str(part) for part in error.absolute_path),
    )
    require(not errors, f"source-admission gate schema violation: {errors[0].message if errors else ''}")
    require(gate.get("policy_generation_ready") is True, "source-admission gate does not authorize policy generation")
    require(
        gate.get("database_ingest_authorized") is False, "source-admission gate unexpectedly authorizes database ingest"
    )
    require(gate.get("source_freeze_ready") is False, "source-admission gate unexpectedly closes the source freeze")
    require(gate.get("phase3_complete") is False and gate.get("phase4_blocked") is True, "phase boundary drift")

    matrix_rows = {row["source_id"]: dict(row) for row in matrix["source_dispositions"]}
    require(set(matrix_rows) == admission.FULL_SOURCE_IDS, "source matrix row set drift")
    gate_decisions = {decision["source_id"]: dict(decision) for decision in gate["decisions"]}
    require(set(gate_decisions) == set(admission.SOURCE_IDS), "source-admission decision set drift")
    for source_id, decision in gate_decisions.items():
        require(decision["final_disposition"] == "admit_scoped", f"{source_id}: source is not admitted")
        require(matrix_rows[source_id]["disposition"] == "admit_candidate", f"{source_id}: matrix disposition drift")
        if "rights_capability" in matrix_rows[source_id]:
            require(
                decision["rights_capability"] == matrix_rows[source_id]["rights_capability"],
                f"{source_id}: matrix and admission rights metadata disagree",
            )
        require(
            decision["orthography_regime"] == matrix_rows[source_id]["orthography_regime"],
            f"{source_id}: matrix and admission orthography metadata disagree",
        )
    return matrix_rows, gate_decisions


def build_policy(
    matrix: Mapping[str, Any],
    gate: Mapping[str, Any],
    v3_policy: Mapping[str, Any],
) -> dict[str, Any]:
    """Build the deterministic complete policy from reviewed, hash-bound inputs."""
    matrix_rows, gate_decisions = _validate_matrix_and_gate(matrix, gate)
    v3_sources = _v3_policy_sources(v3_policy)
    require(not set(v3_sources) & STAGED_IDS, "staged sources unexpectedly appear in the v3 policy")
    require(set(v3_sources) <= admission.FULL_SOURCE_IDS, "v3 policy contains a source outside the matrix")

    sources: list[dict[str, Any]] = []
    for source_id in sorted(admission.FULL_SOURCE_IDS):
        matrix_row = matrix_rows[source_id]
        matrix_disposition = matrix_row["disposition"]
        decision = gate_decisions.get(source_id)
        v3_source = v3_sources.get(source_id)

        if decision is not None:
            final_disposition = "admit_scoped"
            allowed_lanes = decision["allowed_lanes"]
            source_state = decision["source_state"]
            primary_roles = decision["primary_source_roles"]
            claim_types = decision["claim_types"]
            supported_uses = decision["supported_uses"]
            prohibited_uses = decision["prohibited_uses"]
            exactness_status = decision["exactness_status"]
            evidence_hashes = decision["evidence_hashes"]
            rights_capability = decision["rights_capability"]
        elif matrix_disposition == "contextual_only":
            final_disposition = "contextual_only"
            allowed_lanes = v3_source["allowed_lanes"] if v3_source is not None else ["contextual_retrieval"]
            source_state = "db_resident_contextual" if v3_source is not None else "reference_only"
            primary_roles = []
            claim_types = []
            supported_uses, prohibited_uses = _contextual_uses(source_id, matrix_row)
            exactness_status = "context_only"
            evidence_hashes = [_matrix_evidence_hash(matrix_row)]
            rights_capability = str(matrix_row.get("rights_capability") or "rights_bound_by_v3_policy")
        else:
            require(matrix_disposition == "quarantine", f"{source_id}: unsupported matrix disposition")
            final_disposition = "quarantine"
            allowed_lanes = []
            source_state = "quarantined"
            primary_roles = []
            claim_types = []
            supported_uses = matrix_row["supported_uses"]
            prohibited_uses = matrix_row["prohibited_uses"]
            exactness_status = "failed"
            evidence_hashes = [_matrix_evidence_hash(matrix_row)]
            rights_capability = str(matrix_row.get("rights_capability") or "rights_bound_by_v3_policy")

        university_jsonl = v3_source is not None or source_id in STAGED_IDS
        entry: dict[str, Any] = {
            "source_id": source_id,
            "source_kind": "university_jsonl" if university_jsonl else "external_reference",
            "final_disposition": final_disposition,
            "source_state": source_state,
            "custody_state": _normalized_custody_state(
                source_id,
                final_disposition=final_disposition,
                v3_source=v3_source,
                matrix_row=matrix_row,
            ),
            "allowed_lanes": allowed_lanes,
            "orthography_regime": matrix_row["orthography_regime"],
            "rights_capability": rights_capability,
            "primary_source_roles": primary_roles,
            "claim_types": claim_types,
            "supported_uses": supported_uses,
            "prohibited_uses": prohibited_uses,
            "exactness_status": exactness_status,
            "evidence_hashes": evidence_hashes,
        }
        if v3_source is not None:
            expected_v3_disposition = matrix_disposition
            require(
                v3_source["content_disposition"] == expected_v3_disposition,
                f"{source_id}: v3 policy and source matrix disposition disagree",
            )
            entry["jsonl_evidence"] = _jsonl_evidence_from_v3(source_id, v3_source)
        elif source_id in STAGED_IDS:
            entry["jsonl_evidence"] = _jsonl_evidence_from_staged(source_id)
        sources.append(entry)

    counts = Counter(source["final_disposition"] for source in sources)
    body: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "text_free": True,
        "status": "ACTIVE_DEFAULT_DENY",
        "default_disposition": "QUARANTINE_UNTIL_REVIEWED",
        "bindings": {**EXPECTED_INPUT_HASHES, "pr6630_merge_commit": PR6630_MERGE_COMMIT},
        "source_count": len(sources),
        "disposition_counts": {
            "admit_scoped": counts.get("admit_scoped", 0),
            "contextual_only": counts.get("contextual_only", 0),
            "quarantine": counts.get("quarantine", 0),
            "total": len(sources),
        },
        "database_ingest": {
            "eligible_source_ids": list(admission.SOURCE_IDS),
            "staged_not_ingested_source_ids": sorted(STAGED_IDS),
            "staged_expected_rows": STAGED_EXPECTED_ROWS,
            "staged_expected_row_count": sum(STAGED_EXPECTED_ROWS.values()),
            "copied_database_rehearsal_required": True,
            "live_ingest_authorized": False,
        },
        "sources": sources,
        "source_freeze_ready": False,
        "phase3_complete": False,
        "phase4_blocked": True,
    }
    policy = {
        **body,
        "receipt_sha256": hashlib.sha256((canonical_json(body) + "\n").encode("utf-8")).hexdigest(),
    }
    validate_policy_document(policy)
    return policy


def validate_policy_document(policy: Mapping[str, Any]) -> dict[str, Any]:
    """Validate schema plus the exact 30-source semantic invariants."""
    errors = _schema_errors(policy)
    require(not errors, f"complete source policy schema violation: {errors[0].message if errors else ''}")
    body = {key: value for key, value in policy.items() if key != "receipt_sha256"}
    expected_receipt = hashlib.sha256((canonical_json(body) + "\n").encode("utf-8")).hexdigest()
    require(policy["receipt_sha256"] == expected_receipt, "complete source policy receipt hash drift")
    require(
        policy["bindings"] == {**EXPECTED_INPUT_HASHES, "pr6630_merge_commit": PR6630_MERGE_COMMIT},
        "policy bindings drift",
    )

    sources = policy["sources"]
    source_ids = [source["source_id"] for source in sources]
    require(
        source_ids == sorted(admission.FULL_SOURCE_IDS), "policy source IDs are incomplete, duplicated, or unsorted"
    )
    by_disposition = {
        disposition: {source["source_id"] for source in sources if source["final_disposition"] == disposition}
        for disposition in ("admit_scoped", "contextual_only", "quarantine")
    }
    require(by_disposition["admit_scoped"] == set(admission.SOURCE_IDS), "policy admission set drift")
    require(by_disposition["contextual_only"] == admission.CONTEXTUAL_ONLY_IDS, "policy contextual set drift")
    require(by_disposition["quarantine"] == admission.QUARANTINE_IDS, "policy quarantine set drift")

    ingest = policy["database_ingest"]
    require(ingest["eligible_source_ids"] == list(admission.SOURCE_IDS), "eligible ingest set drift")
    require(ingest["staged_not_ingested_source_ids"] == sorted(STAGED_IDS), "staged ingest set drift")
    require(ingest["staged_expected_rows"] == STAGED_EXPECTED_ROWS, "staged row denominator drift")
    require(ingest["staged_expected_row_count"] == 585, "staged row total drift")
    require(ingest["live_ingest_authorized"] is False, "policy unexpectedly authorizes live ingest")

    v3_sources = _v3_policy_sources(read_json(DEFAULT_V3_POLICY_PATH))
    jsonl_ids = {source["source_id"] for source in sources if source["source_kind"] == "university_jsonl"}
    require(jsonl_ids == set(v3_sources) | STAGED_IDS, "university JSONL source set drift")
    for source in sources:
        source_id = source["source_id"]
        lanes = set(source["allowed_lanes"])
        if source_id in v3_sources:
            require(
                source["jsonl_evidence"] == _jsonl_evidence_from_v3(source_id, v3_sources[source_id]),
                f"{source_id}: v3 JSONL evidence drift",
            )
        elif source_id in STAGED_IDS:
            require(
                source["jsonl_evidence"] == _jsonl_evidence_from_staged(source_id),
                f"{source_id}: staged JSONL evidence drift",
            )
        if source["source_kind"] == "external_reference":
            require("corpus_ingest" not in lanes, f"{source_id}: external reference cannot enter corpus ingest")
        if source["final_disposition"] == "admit_scoped":
            require(source["source_kind"] == "university_jsonl", f"{source_id}: admitted source lacks JSONL identity")
            if source["orthography_regime"] == "pre_2019":
                require(
                    bool(set(source["prohibited_uses"]) & POST_2019_AUTHORITY_RESTRICTIONS),
                    f"{source_id}: pre-2019 admission lacks a post-2019 restriction",
                )
        if source["rights_capability"] == "cc_by_nc_4_0_noncommercial_only":
            require(
                NONCOMMERCIAL_RESTRICTION in source["prohibited_uses"],
                f"{source_id}: noncommercial restriction is absent",
            )
        if source["final_disposition"] == "quarantine":
            require(not lanes, f"{source_id}: quarantined source has a production lane")
    return dict(policy)


def load_policy(path: Path = DEFAULT_POLICY_PATH) -> tuple[dict[str, Any], str]:
    policy_sha256 = sha256_file(path)
    require(policy_sha256 == EXPECTED_POLICY_SHA256, "complete source policy byte drift")
    policy = read_json(path)
    return validate_policy_document(policy), policy_sha256


def validate_bound_inputs(paths: Mapping[str, Path]) -> None:
    require(set(paths) == set(EXPECTED_INPUT_HASHES), "bound input path set is incomplete")
    for key, expected_sha256 in EXPECTED_INPUT_HASHES.items():
        path = Path(paths[key])
        require(path.is_file(), f"missing bound input artifact: {key}")
        require(sha256_file(path) == expected_sha256, f"bound input artifact drift: {key}")


def _parse_staged_jsonls(values: list[str]) -> dict[str, Path]:
    parsed: dict[str, Path] = {}
    for value in values:
        source_id, separator, raw_path = value.partition("=")
        require(bool(separator and source_id and raw_path), "--staged-jsonl must be SOURCE_ID=PATH")
        require(source_id not in parsed, f"duplicate staged JSONL argument: {source_id}")
        parsed[source_id] = Path(raw_path)
    return parsed


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase3-reboot-prompt-v3", type=Path, required=True)
    parser.add_argument("--phase3-recovery-prompt-v2", type=Path, required=True)
    parser.add_argument("--university-source-matrix-v3", type=Path, required=True)
    parser.add_argument("--university-source-admission-gate-v1", type=Path, required=True)
    parser.add_argument("--university-source-policy-v3", type=Path, required=True)
    parser.add_argument("--university-corpus-reconciliation-v3", type=Path, required=True)
    parser.add_argument("--pr6630-drive-backup-receipt", type=Path, required=True)
    parser.add_argument("--staged-jsonl", action="append", default=[], metavar="SOURCE_ID=PATH")
    parser.add_argument("--output", type=Path)
    return parser


def main() -> int:
    args = _parser().parse_args()
    bound_paths = {
        "phase3_reboot_prompt_v3_sha256": args.phase3_reboot_prompt_v3,
        "phase3_recovery_prompt_v2_sha256": args.phase3_recovery_prompt_v2,
        "university_source_matrix_v3_sha256": args.university_source_matrix_v3,
        "university_source_admission_gate_v1_sha256": args.university_source_admission_gate_v1,
        "university_source_policy_v3_sha256": args.university_source_policy_v3,
        "university_corpus_reconciliation_v3_sha256": args.university_corpus_reconciliation_v3,
        "pr6630_drive_backup_receipt_sha256": args.pr6630_drive_backup_receipt,
    }
    validate_bound_inputs(bound_paths)
    validate_staged_jsonls(_parse_staged_jsonls(args.staged_jsonl))
    policy = build_policy(
        read_json(args.university_source_matrix_v3),
        read_json(args.university_source_admission_gate_v1),
        read_json(args.university_source_policy_v3),
    )
    encoded = json.dumps(policy, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output is None:
        print(encoded, end="")
    else:
        write_text_atomic(args.output, encoded)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
