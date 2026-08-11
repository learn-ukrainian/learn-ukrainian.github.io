#!/usr/bin/env python3
"""Validate the reviewed Phase 3 university source-admission boundary.

The module is deliberately non-semantic.  It cannot admit a source by itself;
it checks an exact Ukrainian-reviewer result and emits a text-free gate receipt
that keeps database ingest, the complete source freeze, and Phase 4 blocked.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from collections import Counter
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "data/projects/open_model_data"
REVIEW_SCHEMA_PATH = DATA / "contracts/phase3_university_source_admission_review_v1.schema.json"
GATE_SCHEMA_PATH = DATA / "contracts/phase3_university_source_admission_gate_v1.schema.json"

SOURCE_IDS = (
    "uni-ukrmova-corpus-linguistics-khpi-2021-part-1",
    "uni-ukrmova-corpus-linguistics-khpi-2021-part-2",
    "uni-ukrmova-lexicology-filon-khomik-2010",
    "uni-ukrmova-morphology-volkova-maslo-2012",
    "uni-ukrmova-orthography-strokal-2021",
    "uni-ukrmova-phonetics-komarova-2015",
    "uni-ukrmova-prof-haluzynska-2006",
    "uni-ukrmova-punctuation-marynenko-2021",
    "uni-ukrmova-stylistics-sharapa-tytarenko-2025",
    "uni-ukrmova-syntax-herman-2021",
    "uni-ukrmova-text-linguistics-shevel-bilyk-2024",
)
DB_RESIDENT_IDS = frozenset(
    {
        "uni-ukrmova-lexicology-filon-khomik-2010",
        "uni-ukrmova-orthography-strokal-2021",
        "uni-ukrmova-phonetics-komarova-2015",
        "uni-ukrmova-prof-haluzynska-2006",
        "uni-ukrmova-punctuation-marynenko-2021",
        "uni-ukrmova-stylistics-sharapa-tytarenko-2025",
        "uni-ukrmova-syntax-herman-2021",
    }
)
STAGED_IDS = frozenset(SOURCE_IDS) - DB_RESIDENT_IDS
CONTEXTUAL_ONLY_IDS = frozenset(
    {
        "khpi-ukrainian-morphological-tagging-petrasova-et-al-2017",
        "lang-uk-tokenize-uk",
        "naukma-ukrainian-tokenization-stemming-hlybovets-tochytskyi-2017",
        "uni-istoriya-kalynichenko-olianych-2025",
        "uni-istoriya-levytska-2015",
        "uni-mystetstvo-levytska-2015",
        "uni-mystetstvo-petutina-2012",
        "uni-ukrlit-dvulychanska-2017",
        "uni-ukrlit-kalinichenko-2024",
        "uni-ukrmova-computational-linguistics-vakhovska-2023",
        "uni-ukrmova-dialectology-torchynska-2017",
        "uni-ukrmova-error-typology-minchak-2023",
        "uni-ukrmova-historical-grammar-kupchynska-piletskyi-2024",
        "uni-ukrmova-morphology-kobchenko-2025",
        "uni-ukrmova-sociolinguistics-masenko-2010",
    }
)
QUARANTINE_IDS = frozenset(
    {
        "uni-ukrmova-glukhovtseva-2021",
        "uni-ukrmova-morphology-aleksiienko-2014",
        "uni-ukrmova-syntax-didkivska-shvets-2020",
        "uni-ukrmova-vlasova-2023",
    }
)
FULL_SOURCE_IDS = frozenset(SOURCE_IDS) | CONTEXTUAL_ONLY_IDS | QUARANTINE_IDS
TOPIC_AREAS = (
    "phonetics",
    "phonology",
    "orthoepy",
    "accentology",
    "graphics",
    "orthography",
    "morphemics",
    "word formation",
    "lexicology",
    "semantics",
    "phraseology",
    "morphology",
    "syntax",
    "punctuation",
    "government/valency",
    "text linguistics",
    "discourse/pragmatics",
    "stylistics",
    "culture of language",
    "dialectology",
    "sociolinguistics",
    "language contact",
    "historical grammar",
    "history of the literary language",
    "corpus linguistics",
    "Ukrainian-specific computational linguistics/tokenization",
)
EXPECTED_INPUT_HASHES = {
    "phase3_reboot_prompt_v3_sha256": "5f22c7fc84ce6ca6d497fcf0437d72274a0bdb3aa1cf48cfebfe196e67dbd11d",
    "phase3_recovery_prompt_v2_sha256": "298591094d1281629ea444707909b679d1a5368f3ad8afddf39120bc0c34532b",
    "university_source_matrix_v3_sha256": "e2e82934ec26b7d98002cdf87f5326b84fb2d3d7900fe675920ba99e84d190de",
    "tracked_university_policy_v3_sha256": "2cb3643cec48acc52e9163e8ad1a21360de3380584a62a1a08ad07800b1c731d",
    "university_corpus_reconciliation_v3_sha256": "3a4abb3883ad06db3fea1f994a5b51bc22cbdd6ab3e8d3adaf72c180bc42dd65",
    "final_drive_backup_receipt_sha256": "0ecc5553395cdf32788f8bce1d5b071c0a90bd409f371eb44e6fded534d86a7a",
}
EXPECTED_SCOPE_INPUT_HASHES = {
    "phase3_reboot_prompt_v3_sha256": EXPECTED_INPUT_HASHES["phase3_reboot_prompt_v3_sha256"],
    "phase3_recovery_prompt_v2_sha256": EXPECTED_INPUT_HASHES["phase3_recovery_prompt_v2_sha256"],
    "university_source_matrix_v3_sha256": EXPECTED_INPUT_HASHES["university_source_matrix_v3_sha256"],
    "university_source_admission_review_sha256": "8267f65aefdd8d14d24f1255c7bda4b7b92bc06f62f4c6e234696f39bd9ad22a",
    "university_source_admission_gate_sha256": "71a22c5159a21709d0eacd777c3b1a9c33bca041ca8436defed494722a75440c",
    "university_corpus_reconciliation_v3_sha256": EXPECTED_INPUT_HASHES["university_corpus_reconciliation_v3_sha256"],
    "final_drive_backup_receipt_sha256": EXPECTED_INPUT_HASHES["final_drive_backup_receipt_sha256"],
}
DISPOSITIONS = ("admit_scoped", "contextual_only", "quarantine", "needs_more_evidence")
METADATA_ONLY_MUTATION_PREFIXES = (".agent/sessions/", ".entire/", "batch_state/api_usage/usage_")
SOURCE_ROLES = frozenset(
    {
        "explicit_rule",
        "correct_example",
        "incorrect_example",
        "corrected_example",
        "editing_exercise",
        "answer_key",
        "distractor",
        "quotation",
        "historical_or_literary_excerpt",
        "metalinguistic_mention",
        "ordinary_narration",
        "ambiguous_or_ocr",
    }
)
CLAIM_TYPES = frozenset(
    {
        "prescriptive_rule",
        "human_correction_pair",
        "style_preference",
        "acceptable_variant",
        "historical_advice",
        "attestation_only",
        "unresolved",
    }
)
POST_2019_AUTHORITY_RESTRICTIONS = frozenset(
    {
        "post_2019_orthography_rules",
        "post_2019_orthography_spelling_rules",
        "post_2019_orthography_spelling_rules_without_current_corroboration",
    }
)
NONCOMMERCIAL_RESTRICTION = "unrestricted_commercial_training"


class SourceAdmissionError(ValueError):
    """The reviewed source-admission boundary is incomplete or unsafe."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SourceAdmissionError(message)


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SourceAdmissionError(f"cannot read JSON artifact: {path}") from exc
    require(isinstance(value, dict), f"JSON artifact must be an object: {path}")
    return value


def write_text_atomic(path: Path, text: str) -> None:
    """Publish one complete UTF-8 receipt without exposing a partial file."""
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


def read_review_result(path: Path) -> tuple[dict[str, Any], str, str, str]:
    """Read direct JSON or strip one non-JSON commentary prefix losslessly."""
    path = Path(path)
    try:
        raw_bytes = path.read_bytes()
        raw_text = raw_bytes.decode("utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise SourceAdmissionError(f"cannot read UTF-8 review result: {path}") from exc
    raw_sha256 = hashlib.sha256(raw_bytes).hexdigest()
    try:
        value = json.loads(raw_text)
    except json.JSONDecodeError:
        start = raw_text.find("{")
        require(start > 0, f"review result has no recoverable JSON object: {path}")
        try:
            value, consumed = json.JSONDecoder().raw_decode(raw_text[start:])
        except json.JSONDecodeError as exc:
            raise SourceAdmissionError(f"review result JSON payload is malformed: {path}") from exc
        require(not raw_text[start + consumed :].strip(), f"review result has non-whitespace trailing content: {path}")
        semantic_text = raw_text[start : start + consumed]
        normalization = "stripped_non_json_prefix"
    else:
        semantic_text = raw_text
        normalization = "direct_json"
    require(isinstance(value, dict), f"review result must contain one JSON object: {path}")
    semantic_sha256 = hashlib.sha256(semantic_text.encode("utf-8")).hexdigest()
    return value, raw_sha256, semantic_sha256, normalization


def _validate_schema(value: Mapping[str, Any], schema_path: Path, label: str) -> None:
    schema = read_json(schema_path)
    Draft202012Validator.check_schema(schema)
    errors = sorted(
        Draft202012Validator(schema).iter_errors(value),
        key=lambda error: tuple(str(part) for part in error.absolute_path),
    )
    require(not errors, f"{label} schema violation: {errors[0].message if errors else ''}")


def validate_review(review: Mapping[str, Any]) -> dict[str, Any]:
    """Validate one exact 11-source Ukrainian-reviewer response."""
    _validate_schema(review, REVIEW_SCHEMA_PATH, "source-admission review")
    verified_inputs = dict(review["verified_inputs"])
    prior_reviews_verified = verified_inputs.pop("prior_reviews_verified")
    require(prior_reviews_verified is True, "prior university reviews were not verified")
    require(verified_inputs == EXPECTED_INPUT_HASHES, "review input hashes do not match the frozen audit inputs")
    require(review["denominator"] == list(SOURCE_IDS), "review denominator is not the exact sorted 11-source set")

    decisions = review["decisions"]
    decision_ids = [decision["source_id"] for decision in decisions]
    require(decision_ids == list(SOURCE_IDS), "review decisions are missing, duplicated, or out of canonical order")
    for decision in decisions:
        source_id = decision["source_id"]
        expected_state = "db_resident" if source_id in DB_RESIDENT_IDS else "staged_not_ingested"
        require(decision["source_state"] == expected_state, f"{source_id}: source-state drift")
        require(set(decision["primary_source_roles"]) <= SOURCE_ROLES, f"{source_id}: unsupported primary role")
        require(set(decision["claim_types"]) <= CLAIM_TYPES, f"{source_id}: unsupported claim type")
        require(
            decision["allowed_lanes"] == sorted(set(decision["allowed_lanes"])),
            f"{source_id}: allowed lanes must be sorted and unique",
        )

        disposition = decision["final_disposition"]
        lanes = set(decision["allowed_lanes"])
        if disposition == "admit_scoped":
            require(
                {"contextual_retrieval", "corpus_ingest"} <= lanes,
                f"{source_id}: scoped admission must include contextual retrieval and corpus ingest",
            )
            require(
                decision["exactness_status"] == "verified_for_scoped_use", f"{source_id}: admission lacks exactness"
            )
            require(not decision["missing_evidence"], f"{source_id}: admitted source still names missing evidence")
        elif disposition == "contextual_only":
            require(
                lanes == {"contextual_retrieval", "corpus_ingest"},
                f"{source_id}: contextual-only lane set is not closed",
            )
            require(decision["exactness_status"] == "context_only", f"{source_id}: contextual exactness mismatch")
        else:
            require(not lanes, f"{source_id}: blocked source cannot enter a production lane")
            expected_exactness = "failed" if disposition == "quarantine" else "insufficient"
            require(decision["exactness_status"] == expected_exactness, f"{source_id}: blocked exactness mismatch")
            require(decision["missing_evidence"], f"{source_id}: blocked source must name concrete missing evidence")

        if "linguistic_rule_evidence" in lanes:
            require(disposition == "admit_scoped", f"{source_id}: only scoped admission may support rules")
            require(
                "explicit_rule" in decision["primary_source_roles"], f"{source_id}: rule lane lacks explicit-rule role"
            )
        if decision["orthography_regime"] == "pre_2019" and disposition == "admit_scoped":
            require(
                bool(set(decision["prohibited_uses"]) & POST_2019_AUTHORITY_RESTRICTIONS),
                f"{source_id}: pre-2019 admission lacks a post-2019 authority restriction",
            )
        if decision["rights_capability"] == "cc_by_nc_4_0_noncommercial_only":
            require(
                NONCOMMERCIAL_RESTRICTION in decision["prohibited_uses"],
                f"{source_id}: non-commercial rights restriction is not preserved",
            )

    approve = review["review_disposition"] == "APPROVE_POLICY_GENERATION"
    require(review["policy_generation_authorized"] is approve, "review disposition and policy authorization disagree")
    return dict(review)


def validate_input_artifacts(paths: Mapping[str, Path]) -> None:
    """Verify exact bytes for every externally supplied audit input."""
    require(set(paths) == set(EXPECTED_INPUT_HASHES), "input artifact path set is incomplete")
    for key, expected_sha256 in EXPECTED_INPUT_HASHES.items():
        path = Path(paths[key])
        require(path.is_file(), f"missing bound input artifact: {key}")
        require(sha256_file(path) == expected_sha256, f"bound input artifact drift: {key}")


def validate_dispatch_transport(
    state: Mapping[str, Any],
    *,
    expected_task_id: str,
    result_path: Path,
    raw_result_sha256: str,
    semantic_result_sha256: str,
    normalization: str,
) -> dict[str, Any]:
    """Normalize a clean review dispatch or the known ignored-metadata leak."""
    require(state.get("task_id") == expected_task_id, "review dispatch task identity drift")
    require(state.get("exit_code") == 0, f"{expected_task_id}: reviewer subprocess did not exit successfully")
    recorded_result = state.get("result_file")
    require(isinstance(recorded_result, str), f"{expected_task_id}: dispatch result path is absent")
    require(
        Path(recorded_result).resolve() == Path(result_path).resolve(),
        f"{expected_task_id}: dispatch result path drift",
    )
    mutation_paths = sorted(state.get("read_only_mutation_paths") or [])
    status = state.get("status")
    if status == "done":
        require(not mutation_paths, f"{expected_task_id}: done dispatch still reports checkout mutation")
        normalized_status = "done"
    else:
        require(status == "failed", f"{expected_task_id}: dispatch is not terminal")
        require(mutation_paths, f"{expected_task_id}: failed dispatch lacks an attributable mutation")
        require(
            all(path.startswith(METADATA_ONLY_MUTATION_PREFIXES) for path in mutation_paths),
            f"{expected_task_id}: failed dispatch mutated a non-metadata path",
        )
        require(
            str(state.get("last_error", "")).startswith("read-only checkout mutation detected:"),
            f"{expected_task_id}: failure was not the known read-only metadata leak",
        )
        normalized_status = "failed_metadata_only"
    return {
        "task_id": expected_task_id,
        "normalized_status": normalized_status,
        "exit_code": 0,
        "raw_result_sha256": raw_result_sha256,
        "semantic_result_sha256": semantic_result_sha256,
        "normalization": normalization,
        "metadata_only_mutation_paths": mutation_paths,
    }


def derive_source_set_check(source_matrix: Mapping[str, Any]) -> dict[str, Any]:
    """Derive the scope critic's source-set facts from matrix rows."""
    require(
        source_matrix.get("schema_version") == "phase3-university-source-matrix-consolidated.v3",
        "university source matrix schema-version drift",
    )
    require(source_matrix.get("text_free") is True, "university source matrix is not text-free")
    rows = source_matrix.get("source_dispositions")
    require(isinstance(rows, list), "university source matrix has no source-disposition rows")
    source_ids: list[str] = []
    by_disposition: dict[str, set[str]] = {
        "admit_candidate": set(),
        "contextual_only": set(),
        "quarantine": set(),
    }
    for row in rows:
        require(isinstance(row, Mapping), "university source matrix row is not an object")
        source_id = row.get("source_id")
        disposition = row.get("disposition")
        require(isinstance(source_id, str) and source_id, "university source matrix row has no source ID")
        require(disposition in by_disposition, f"{source_id}: unsupported matrix disposition")
        source_ids.append(source_id)
        by_disposition[disposition].add(source_id)

    unique_source_ids = set(source_ids)
    derived_counts = {
        "admit_candidate": len(by_disposition["admit_candidate"]),
        "contextual_only": len(by_disposition["contextual_only"]),
        "quarantine": len(by_disposition["quarantine"]),
        "total_unique_sources": len(unique_source_ids),
    }
    require(
        source_matrix.get("source_disposition_counts") == derived_counts,
        "university source matrix disposition counts do not match its rows",
    )
    return {
        "total_unique_sources": len(unique_source_ids),
        "admit_scoped_count": len(by_disposition["admit_candidate"]),
        "contextual_only_count": len(by_disposition["contextual_only"]),
        "quarantine_count": len(by_disposition["quarantine"]),
        "no_extras": unique_source_ids <= FULL_SOURCE_IDS,
        "no_omissions": unique_source_ids >= FULL_SOURCE_IDS,
        "no_duplicate_credit": len(source_ids) == len(unique_source_ids),
        "quarantines_preserved": by_disposition["quarantine"] == QUARANTINE_IDS,
    }


def validate_scope_review(review: Mapping[str, Any], source_matrix: Mapping[str, Any]) -> dict[str, Any]:
    """Validate the independent complete-matrix scope review."""
    scope_schema_path = DATA / "contracts/phase3_university_source_scope_review_v1.schema.json"
    _validate_schema(review, scope_schema_path, "source scope review")
    require(
        review["verified_inputs"] == EXPECTED_SCOPE_INPUT_HASHES,
        "scope-review input hashes do not match the frozen audit inputs",
    )
    derived_source_set_check = derive_source_set_check(source_matrix)
    require(
        review["source_set_check"] == derived_source_set_check,
        "scope-review source-set facts do not match the matrix rows",
    )
    topic_matrix = review["topic_matrix"]
    require(
        [row["area"] for row in topic_matrix] == list(TOPIC_AREAS),
        "scope review does not cover the exact ordered 26-area matrix",
    )
    for row in topic_matrix:
        support = set(row["supporting_source_ids"])
        require(support <= FULL_SOURCE_IDS, f"{row['area']}: supporting source falls outside the 30-source universe")
        require(not support & QUARANTINE_IDS, f"{row['area']}: quarantined source received coverage credit")
        if row["status"] == "missing":
            require(not support, f"{row['area']}: missing area cannot claim supporting sources")
        else:
            require(support, f"{row['area']}: non-missing area lacks supporting sources")
    counts = Counter(row["status"] for row in topic_matrix)
    require(
        review["topic_counts"]
        == {
            "sufficient": counts.get("sufficient", 0),
            "partial": counts.get("partial", 0),
            "missing": counts.get("missing", 0),
            "total": len(TOPIC_AREAS),
        },
        "scope-review topic counts do not match its 26 rows",
    )
    approved = review["matrix_disposition"] == "APPROVE_ADMISSION_MATRIX"
    require(review["source_admission_matrix_ready"] is approved, "scope disposition and readiness disagree")
    if approved:
        require(
            all(
                derived_source_set_check[key]
                for key in ("no_extras", "no_omissions", "no_duplicate_credit", "quarantines_preserved")
            ),
            "approved scope review has an incomplete, duplicated, or misclassified source set",
        )
        rows_by_disposition = {
            disposition: {
                row["source_id"] for row in source_matrix["source_dispositions"] if row["disposition"] == disposition
            }
            for disposition in ("admit_candidate", "contextual_only", "quarantine")
        }
        require(
            rows_by_disposition["admit_candidate"] == set(SOURCE_IDS)
            and rows_by_disposition["contextual_only"] == CONTEXTUAL_ONLY_IDS
            and rows_by_disposition["quarantine"] == QUARANTINE_IDS,
            "approved scope review has a source in the wrong disposition group",
        )
        require(not review["source_disposition_corrections"], "approved matrix still changes source dispositions")
    return dict(review)


def build_gate(
    review: Mapping[str, Any],
    scope_review: Mapping[str, Any],
    source_matrix: Mapping[str, Any],
    *,
    review_sha256: str,
    scope_review_sha256: str,
    transport: Mapping[str, Any],
) -> dict[str, Any]:
    """Build the text-free policy-generation gate from a valid review."""
    validated = validate_review(review)
    require(validated["policy_generation_authorized"] is True, "review does not authorize policy generation")
    require(
        review_sha256 == EXPECTED_SCOPE_INPUT_HASHES["university_source_admission_review_sha256"],
        "review bytes differ from the review checked by the scope critic",
    )
    validated_scope = validate_scope_review(scope_review, source_matrix)
    require(validated_scope["source_admission_matrix_ready"] is True, "scope review does not approve the matrix")
    require(set(transport) == {"ukrainian_review", "scope_review"}, "review transport receipt set is incomplete")
    require(
        transport["ukrainian_review"]["semantic_result_sha256"] == review_sha256,
        "Ukrainian-review transport receipt hash drift",
    )
    require(
        transport["scope_review"]["semantic_result_sha256"] == scope_review_sha256,
        "scope-review transport receipt hash drift",
    )
    decisions = []
    for decision in validated["decisions"]:
        decisions.append(
            {
                key: decision[key]
                for key in (
                    "source_id",
                    "final_disposition",
                    "source_state",
                    "allowed_lanes",
                    "orthography_regime",
                    "rights_capability",
                    "primary_source_roles",
                    "claim_types",
                    "supported_uses",
                    "prohibited_uses",
                    "exactness_status",
                    "evidence_hashes",
                    "missing_evidence",
                )
            }
        )
    counts = Counter(decision["final_disposition"] for decision in decisions)
    finding_counts = Counter(finding["severity"] for finding in validated_scope["findings"])
    body: dict[str, Any] = {
        "schema_version": "phase3_university_source_admission_gate_v1",
        "text_free": True,
        "bindings": {
            **EXPECTED_INPUT_HASHES,
            "review_sha256": review_sha256,
            "scope_review_sha256": scope_review_sha256,
        },
        "transport": dict(transport),
        "denominator_count": len(SOURCE_IDS),
        "denominator": list(SOURCE_IDS),
        "disposition_counts": {disposition: counts.get(disposition, 0) for disposition in DISPOSITIONS},
        "topic_counts": validated_scope["topic_counts"],
        "scope_review_finding_counts": {
            "material": finding_counts.get("material", 0),
            "minor": finding_counts.get("minor", 0),
        },
        "rights_and_exactness_residual_count": len(validated_scope["rights_and_exactness_residuals"]),
        "complete_residual_count": len(validated_scope["complete_residuals"]),
        "decisions": decisions,
        "scope_review_ready": True,
        "policy_generation_ready": True,
        "database_ingest_authorized": False,
        "source_freeze_ready": False,
        "phase3_complete": False,
        "phase4_blocked": True,
    }
    gate = {
        **body,
        "receipt_sha256": hashlib.sha256((canonical_json(body) + "\n").encode("utf-8")).hexdigest(),
    }
    _validate_schema(gate, GATE_SCHEMA_PATH, "source-admission gate")
    return gate


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--review", type=Path, required=True)
    parser.add_argument("--review-state", type=Path, required=True)
    parser.add_argument("--scope-review", type=Path, required=True)
    parser.add_argument("--scope-review-state", type=Path, required=True)
    parser.add_argument("--phase3-reboot-prompt-v3", type=Path, required=True)
    parser.add_argument("--phase3-recovery-prompt-v2", type=Path, required=True)
    parser.add_argument("--university-source-matrix-v3", type=Path, required=True)
    parser.add_argument("--tracked-university-policy-v3", type=Path, required=True)
    parser.add_argument("--university-corpus-reconciliation-v3", type=Path, required=True)
    parser.add_argument("--final-drive-backup-receipt", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    return parser


def main() -> int:
    args = _parser().parse_args()
    input_paths = {
        "phase3_reboot_prompt_v3_sha256": args.phase3_reboot_prompt_v3,
        "phase3_recovery_prompt_v2_sha256": args.phase3_recovery_prompt_v2,
        "university_source_matrix_v3_sha256": args.university_source_matrix_v3,
        "tracked_university_policy_v3_sha256": args.tracked_university_policy_v3,
        "university_corpus_reconciliation_v3_sha256": args.university_corpus_reconciliation_v3,
        "final_drive_backup_receipt_sha256": args.final_drive_backup_receipt,
    }
    validate_input_artifacts(input_paths)
    review, review_raw_sha256, review_sha256, review_normalization = read_review_result(args.review)
    scope_review, scope_raw_sha256, scope_review_sha256, scope_normalization = read_review_result(args.scope_review)
    transport = {
        "ukrainian_review": validate_dispatch_transport(
            read_json(args.review_state),
            expected_task_id="phase3-v3-final-source-admission-review-20-correction",
            result_path=args.review,
            raw_result_sha256=review_raw_sha256,
            semantic_result_sha256=review_sha256,
            normalization=review_normalization,
        ),
        "scope_review": validate_dispatch_transport(
            read_json(args.scope_review_state),
            expected_task_id="phase3-v3-university-source-scope-review-21",
            result_path=args.scope_review,
            raw_result_sha256=scope_raw_sha256,
            semantic_result_sha256=scope_review_sha256,
            normalization=scope_normalization,
        ),
    }
    gate = build_gate(
        review,
        scope_review,
        read_json(args.university_source_matrix_v3),
        review_sha256=review_sha256,
        scope_review_sha256=scope_review_sha256,
        transport=transport,
    )
    encoded = json.dumps(gate, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output is None:
        print(encoded, end="")
    else:
        write_text_atomic(args.output, encoded)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
