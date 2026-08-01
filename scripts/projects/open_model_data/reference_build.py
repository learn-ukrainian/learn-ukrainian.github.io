#!/usr/bin/env python3
"""Validate the Ukrainian Data Foundry interfaces in one reproducible build.

The reference build is deliberately non-operational: it uses one synthetic
Russian-interference fixture, creates five local consumer views and five
non-authorizing recipe manifests, reproduces the complete corpus profile, and
re-scores saved benchmark outputs. It never calls a model or starts training.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import resource
import shutil
import sys
import tempfile
import time
from itertools import combinations
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.projects.open_model_data import correction_factory, profile_corpus
from scripts.projects.open_model_data import model_view_exporter as exporter
from scripts.projects.open_model_data import validate_source_records as source_contract
from scripts.projects.ua_eval_harness import evaluate_model

CONTRACTS = ROOT / "data/projects/open_model_data/contracts"
DEFAULT_CONFIG = ROOT / "data/projects/open_model_data/reference/reference_build_config_v1.json"
CONFIG_SCHEMA = CONTRACTS / "reference_build_config_v1.schema.json"
MANIFEST_SCHEMA = CONTRACTS / "reference_build_manifest_v1.schema.json"
OBSERVATION_SCHEMA = CONTRACTS / "reference_build_observation_v1.schema.json"
REVIEW_CANDIDATE_SCHEMA = CONTRACTS / "review_candidate_v1.schema.json"
SOURCE_EXAMPLE = CONTRACTS / "source_record_v1.example.json"

VIEW_ORDER = (
    "continued_pretraining",
    "correction_instruction",
    "preference",
    "quality_filter",
    "heldout_evaluation",
)
VIEW_DESTINATIONS = {
    "continued_pretraining": "continued_pretraining",
    "correction_instruction": "supervised_correction",
    "preference": "pairwise_preference",
    "quality_filter": "quality_filter",
    "heldout_evaluation": "heldout_evaluation",
}
FORBIDDEN_GOLD_FIELDS = frozenset({"target", "targets", "reference", "references", "edit", "edits"})


class ReferenceBuildError(ValueError):
    """A reference input or reproduced artifact violated the frozen contract."""


def canonical_json(value: Any) -> str:
    """Return the repository's canonical JSON representation."""
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ReferenceBuildError(message)


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ReferenceBuildError(f"cannot read JSON {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ReferenceBuildError(f"expected JSON object: {path}")
    return value


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise ReferenceBuildError(f"cannot read JSONL {path}: {exc}") from exc
    for line_number, line in enumerate(lines, 1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ReferenceBuildError(f"invalid JSONL {path}:{line_number}: {exc}") from exc
        if not isinstance(value, dict):
            raise ReferenceBuildError(f"expected JSON object at {path}:{line_number}")
        rows.append(value)
    require(bool(rows), f"empty JSONL artifact: {path}")
    return rows


def jsonl_bytes(rows: list[dict[str, Any]]) -> bytes:
    return "".join(canonical_json(row) + "\n" for row in rows).encode("utf-8")


def write_bytes_atomic(path: Path, value: bytes) -> None:
    exporter.write_json_atomic(path, value)


def write_json(path: Path, value: dict[str, Any]) -> None:
    write_bytes_atomic(path, (canonical_json(value) + "\n").encode("utf-8"))


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    write_bytes_atomic(path, jsonl_bytes(rows))


def logical_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return "local-runtime-artifact"


def validate_schema(value: Any, schema_path: Path, *, label: str) -> None:
    schema = read_json(schema_path)
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors = sorted(validator.iter_errors(value), key=lambda item: list(item.path))
    if errors:
        first = errors[0]
        location = ".".join(str(part) for part in first.path) or "<root>"
        raise ReferenceBuildError(f"{label} schema violation at {location}: {first.message}")


def resolve_path(value: str) -> Path:
    path = Path(value)
    require(not path.is_absolute(), f"reference config path must be relative: {value}")
    resolved = (ROOT / path).resolve()
    require(ROOT.resolve() in resolved.parents, f"reference config path escapes repository: {value}")
    require(resolved.is_file(), f"reference input is missing: {value}")
    return resolved


def load_config(path: Path) -> dict[str, Any]:
    config = read_json(path)
    validate_schema(config, CONFIG_SCHEMA, label="reference build config")
    fixture = config["fixture"]
    require(
        fixture["source_text"].count(fixture["incorrect_span"]) == 1,
        "fixture incorrect span must occur exactly once",
    )
    require(
        fixture["incorrect_span"] != fixture["accepted_correction"],
        "fixture correction must change the source span",
    )
    for value in config["full_corpus_profile"].values():
        resolve_path(value)
    for key, value in config["baseline"].items():
        if key.endswith("_path"):
            resolve_path(value)
    require(not any(config["run_policy"].values()), "reference run policy must deny every external action")
    return config


def artifact(path: Path, *, records: int) -> dict[str, Any]:
    return {
        "bytes": path.stat().st_size,
        "records": records,
        "sha256": sha256_file(path),
    }


def _source_record(text: str) -> dict[str, Any]:
    record = read_json(SOURCE_EXAMPLE)
    record["contract_schema_sha256"] = source_contract.load_schema()[1]
    record["record_id"] = "record.reference-zvuchyt-001"
    record["source_id"] = "source.reference-zvuchyt-001"
    record["work_id"] = "work.reference-zvuchyt-001"
    record["content"]["sha256"] = sha256_text(text)
    return record


def _source_payload(text: str, incorrect_span: str) -> dict[str, Any]:
    start = text.index(incorrect_span)
    end = start + len(incorrect_span)
    spans = [
        {
            "discourse_role": "narration",
            "end": start,
            "language_identity": "ukrainian",
            "modern_loss_action": "retain",
            "reason": "other_reviewed",
            "representation": "standard_orthography",
            "start": 0,
        },
        {
            "discourse_role": "narration",
            "end": end,
            "language_identity": "russian",
            "modern_loss_action": "mask_from_loss",
            "reason": "russian_or_mixed_language",
            "representation": "standard_orthography",
            "start": start,
        },
        {
            "discourse_role": "narration",
            "end": len(text),
            "language_identity": "ukrainian",
            "modern_loss_action": "retain",
            "reason": "other_reviewed",
            "representation": "standard_orthography",
            "start": end,
        },
    ]
    return {
        "derivation": {
            "kind": "full_source",
            "receipt_sha256": sha256_text("reference-full-source-derivation-v1"),
            "source_end_char": None,
            "source_start_char": None,
        },
        "language_span_review": {
            "character_spans": spans,
            "receipt_sha256": sha256_text("reference-language-span-fixture-v1"),
            "reviewer_qualification": "Synthetic structural fixture; not qualified human evidence",
            "status": "complete",
        },
        "normalization": {
            "receipt_sha256": sha256_text("reference-normalization-fixture-v1"),
            "status": "complete",
            "version": "reference-normalization-v1",
        },
        "origin": "machine_generated",
        "origin_evidence": {
            "method": "committed synthetic fixture",
            "receipt_sha256": sha256_text("reference-origin-fixture-v1"),
            "status": "verified",
        },
        "payload_id": "payload.reference-zvuchyt-001",
        "private_data": "clear",
        "private_data_review": {
            "method": "literal committed fixture contains no private data",
            "receipt_sha256": sha256_text("reference-private-data-fixture-v1"),
            "status": "complete",
        },
        "schema_version": "foundry_source_payload_v1",
        "source_content_sha256": sha256_text(text),
        "source_record_id": "record.reference-zvuchyt-001",
        "test_fixture": True,
        "text": text,
        "text_sha256": sha256_text(text),
    }


def _review_candidate(incorrect_span: str) -> dict[str, Any]:
    return {
        "automatic_error_label": False,
        "candidate_category": "non_ukrainian_form_candidate",
        "confidence": "medium",
        "evidence_status": "vesum_unknown_context_required",
        "locator": "sqlite:reference-fixture.db#records/record.reference-zvuchyt-001",
        "normalized_form": incorrect_span.casefold(),
        "origin": "machine_generated",
        "period": "modern",
        "register": "neutral",
        "review_disposition": "unresolved",
        "schema_version": "review_candidate_v1",
        "source_family": "reference_fixture",
        "source_record_id": "record.reference-zvuchyt-001",
        "surface_form": incorrect_span,
        "token_count_in_record": 1,
        "vesum_evidence": {
            "analyses": [],
            "attested": False,
            "lookup_form": incorrect_span.casefold(),
        },
    }


def _evidence(
    source: str,
    query: str,
    *,
    status: str,
    evidence_type: str,
    supports: str,
    source_identity: str,
) -> dict[str, Any]:
    locator = (
        f"https://slovnyk.me/dict/{source_identity}/{query}"
        if source == "slovnyk_me"
        else f"fixture:{source}/{source_identity}/{query}"
    )
    return {
        "content_sha256": sha256_text(f"{source}:{source_identity}:{query}:{status}"),
        "evidence_type": evidence_type,
        "locator": locator,
        "official_url": None,
        "parser_status": "not_found" if status == "not_found" else "ok",
        "parser_version": f"{source}-reference-fixture-v1",
        "period": "modern_or_source_specific",
        "query": query,
        "raw_payload_export_allowed": False,
        "register": "source_specific",
        "rights_posture": "bounded_internal_reference",
        "sense_groups": [],
        "source": source,
        "source_identity": source_identity,
        "status": status,
        "supports": supports,
    }


def _candidate(
    text: str,
    incorrect_span: str,
    upstream: dict[str, Any],
) -> dict[str, Any]:
    registry = correction_factory.load_evaluation_registry()
    contamination = correction_factory.contamination_states(text, registry)
    contamination["registry_artifact_sha256"] = {
        "v0_1_1_manifest": registry.v011_manifest_sha256,
        "v0_2_packet": registry.v02_packet_sha256,
    }
    start = text.index(incorrect_span)
    evidence = [
        _evidence(
            "vesum",
            incorrect_span,
            status="not_found",
            evidence_type="form",
            supports="no_conclusion",
            source_identity="dict-uk-v6.8.0-e33803783ac1",
        ),
        _evidence(
            "russian_morphology",
            incorrect_span,
            status="attested",
            evidence_type="morphology",
            supports="russian_attestation",
            source_identity="pymorphy3-russian-dictionary",
        ),
        _evidence(
            "r2u",
            incorrect_span,
            status="attested",
            evidence_type="translation_equivalent",
            supports="russian_attestation",
            source_identity="r2u.org.ua",
        ),
        _evidence(
            "ulif_dictua",
            incorrect_span,
            status="not_found",
            evidence_type="form",
            supports="no_conclusion",
            source_identity="ulif-dictua",
        ),
        _evidence(
            "heritage_dictionary",
            incorrect_span,
            status="not_found",
            evidence_type="form",
            supports="no_conclusion",
            source_identity="heritage-reference-set",
        ),
        _evidence(
            "slovnyk_me",
            incorrect_span,
            status="not_found",
            evidence_type="form",
            supports="no_conclusion",
            source_identity="sum20",
        ),
        _evidence(
            "ukrainian_corpus",
            incorrect_span,
            status="attested",
            evidence_type="corpus_context",
            supports="context_only",
            source_identity="foundry-reference-fixture",
        ),
    ]
    return {
        "candidate_id": "candidate.reference-zvuchyt-001",
        "candidate_layers": ["grammar", "russian_interference"],
        "detector": {
            "automatic_error_label": False,
            "kind": "combined",
            "model_output_used_as_gold": False,
            "producer": "foundry-reference-fixture-v1",
        },
        "evidence": evidence,
        "reconstructions": [],
        "review_state": "unresolved",
        "safety": {
            "contamination": contamination,
            "origin": "verified_synthetic",
            "permitted_use": "correction_eligible",
            "private_data": "clear",
            "provenance": "complete",
            "rights": "granted",
        },
        "schema_version": "correction_candidate_v1",
        "source": {
            "content_sha256": sha256_text(text),
            "context": {
                "end": len(text),
                "sha256": sha256_text(text),
                "start": 0,
                "text": text,
            },
            "genre": "synthetic_reference_fixture",
            "locator": "fixture:reference-zvuchyt-001",
            "origin": "machine_generated",
            "period": "modern",
            "record_id": "row.reference-zvuchyt-001",
            "region": "synthetic",
            "register": "neutral",
            "source_family": "reference_fixture",
            "source_record_id": "record.reference-zvuchyt-001",
        },
        "span": {
            "discourse_role": "narration",
            "downstream_disposition": "correction_candidate",
            "end": start + len(incorrect_span),
            "language_identity": "russian",
            "representation": "standard_orthography",
            "start": start,
            "text": incorrect_span,
        },
        "uncertainty": ["synthetic_fixture_requires_real_qualified_review_before_use"],
        "upstream": {
            "candidate_schema_version": "review_candidate_v1",
            "candidate_sha256": sha256_text(canonical_json(upstream)),
            "profile_id": "foundry-reference-fixture-v1",
        },
        "views": {
            "correction": "candidate",
            "evaluation": "excluded_from_non_evaluation_views",
            "faithful_literary": "retain_original",
            "modern_literary_ukrainian": "mask_span_from_loss",
            "preference": "candidate",
        },
    }


def _decision(candidate: dict[str, Any], correction: str) -> dict[str, Any]:
    projection = {
        "acceptable_alternatives": [],
        "accepted_correction": correction,
        "citations": [
            {
                "content_sha256": sha256_text("reference-fixture-review-citation-v1"),
                "locator": "fixture:combined-evidence/vesum-r2u-russian-morphology",
                "source_identity": "reference-fixture-evidence-bundle",
                "source_kind": "dictionary",
                "supports": "Synthetic fixture projection only; not qualified human correction evidence.",
            }
        ],
        "decision": "correction",
        "discourse_role": "narration",
        "language_identity": "russian",
        "rationale": "Synthetic contract fixture models a Russian finite form in Ukrainian narration.",
        "representation": "standard_orthography",
        "uncertainty": ["fixture_review_not_real_gold"],
        "views": {
            "correction": "eligible_intake",
            "evaluation": "excluded_from_non_evaluation_views",
            "faithful_literary": "retain_original",
            "modern_literary_ukrainian": "mask_span_from_loss",
            "preference": "eligible_intake",
        },
    }

    def review(reviewer_id: str) -> dict[str, Any]:
        return {
            "projection": copy.deepcopy(projection),
            "reviewer": {
                "human": True,
                "independence_attested": True,
                "qualification_evidence": "Synthetic test fixture; never valid as real qualification evidence.",
                "reviewer_id": reviewer_id,
                "test_fixture": True,
                "ukrainian_qualification": "qualified_ukrainian_language_reviewer",
            },
        }

    return {
        "candidate_id": candidate["candidate_id"],
        "candidate_sha256": sha256_text(canonical_json(candidate)),
        "final": projection,
        "final_resolution": {"kind": "first_pass_agreement"},
        "first_pass_reviews": [
            review("fixture-reviewer.reference-a"),
            review("fixture-reviewer.reference-b"),
        ],
        "review_state": "adjudicated",
        "schema_version": "correction_reviewer_decision_v1",
    }


def build_fixture_chain(output_dir: Path, config: dict[str, Any]) -> dict[str, Any]:
    fixture_dir = output_dir / "fixture"
    fixture = config["fixture"]
    text = fixture["source_text"]
    incorrect = fixture["incorrect_span"]
    source = _source_record(text)
    payload = _source_payload(text, incorrect)
    upstream = _review_candidate(incorrect)
    validate_schema(upstream, REVIEW_CANDIDATE_SCHEMA, label="reference review candidate")
    candidate = _candidate(text, incorrect, upstream)
    decision = _decision(candidate, fixture["accepted_correction"])
    correction = correction_factory.build_correction_record(candidate, decision)

    paths = {
        "source_records": fixture_dir / "source_records.jsonl",
        "source_payloads": fixture_dir / "source_payloads.jsonl",
        "review_candidates": fixture_dir / "review_candidates.jsonl",
        "correction_candidates": fixture_dir / "correction_candidates.jsonl",
        "reviewer_decisions": fixture_dir / "reviewer_decisions.jsonl",
        "correction_records": fixture_dir / "correction_records.jsonl",
    }
    values = {
        "source_records": source,
        "source_payloads": payload,
        "review_candidates": upstream,
        "correction_candidates": candidate,
        "reviewer_decisions": decision,
        "correction_records": correction,
    }
    for name, path in paths.items():
        write_jsonl(path, [values[name]])

    admission = source_contract.validate_path(paths["source_records"])
    require(admission["admitted_records"] == 1, "synthetic reference source did not pass source contract")
    return {"paths": paths, "values": values, "admission": admission}


def _recipe_config(view_kind: str, config: dict[str, Any]) -> dict[str, Any]:
    evaluation = view_kind == "heldout_evaluation"
    templates = {
        "continued_pretraining": "{{text}}",
        "correction_instruction": "{{input_text}}\n{{target_text}}",
        "preference": "{{prompt}}\n{{chosen}}\n{{rejected}}",
        "quality_filter": "{{text}}\n{{label}}",
        "heldout_evaluation": "{{source}}",
    }
    template = templates[view_kind]
    fixture = config["recipe_fixture"]
    return {
        "base_model": fixture["base_model"],
        "data_preparation": {
            "rendering_template": template,
            "rendering_template_sha256": sha256_text(template),
            "split": {
                "modulus": None if evaluation else 10_000,
                "namespace": f"foundry-reference-v1:{view_kind}",
                "strategy": "preserve_evaluation_release" if evaluation else "sha256_record_id_modulo",
                "validation_buckets": None if evaluation else 100,
            },
            "target_loss_policy": exporter.TARGET_LOSS_POLICIES[view_kind],
        },
        "hyperparameters": fixture["hyperparameters"],
        "implementation": fixture["implementation"],
        "objective": exporter.OBJECTIVES[view_kind],
        "recipe_id": f"recipe.foundry-reference-v1:{view_kind}",
        "run_policy": {"execution_state": "not_run", "training_authorized": False},
        "schema_version": "training_recipe_config_v1",
        "tokenizer": fixture["tokenizer"],
        "view_kind": view_kind,
    }


def build_views_and_recipes(
    output_dir: Path,
    config: dict[str, Any],
    chain: dict[str, Any],
) -> dict[str, Any]:
    views_dir = output_dir / "views"
    recipes_dir = output_dir / "recipes"
    source_path = chain["paths"]["source_records"]
    correction_path = chain["paths"]["correction_records"]
    results: dict[str, Any] = {}

    for view_kind in VIEW_ORDER:
        view_path = views_dir / f"{view_kind}.jsonl"
        receipt_path = views_dir / f"{view_kind}.receipt.json"
        if view_kind == "continued_pretraining":
            receipt = exporter.export_pretraining(
                source_records_path=source_path,
                payloads_path=chain["paths"]["source_payloads"],
                origin="machine_generated",
                representation_view="modern_literary_ukrainian",
                output=view_path,
                receipt_output=receipt_path,
                allow_test_fixtures=True,
                v011_manifest=exporter.DEFAULT_V011_MANIFEST,
                v02_packet=exporter.DEFAULT_V02_PACKET,
                extra_evaluation_artifacts=(),
            )
        elif view_kind == "heldout_evaluation":
            receipt = exporter.export_evaluation(
                release="all",
                output=view_path,
                receipt_output=receipt_path,
                v011_manifest=exporter.DEFAULT_V011_MANIFEST,
                v02_packet=exporter.DEFAULT_V02_PACKET,
                extra_evaluation_artifacts=(),
            )
        else:
            receipt = exporter.export_correction_family(
                view_kind=view_kind,
                source_records_path=source_path,
                correction_records_path=correction_path,
                origin="machine_generated",
                output=view_path,
                receipt_output=receipt_path,
                allow_test_fixtures=True,
                v011_manifest=exporter.DEFAULT_V011_MANIFEST,
                v02_packet=exporter.DEFAULT_V02_PACKET,
                extra_evaluation_artifacts=(),
            )
        rows = read_jsonl(view_path)
        require(receipt["counts"]["exported_records"] == len(rows), f"{view_kind} receipt count drift")
        require(
            {row["permitted_destination"] for row in rows} == {VIEW_DESTINATIONS[view_kind]},
            f"{view_kind} destination mismatch",
        )
        recipe_config = _recipe_config(view_kind, config)
        recipe_config_path = recipes_dir / f"{view_kind}.config.json"
        recipe_manifest_path = recipes_dir / f"{view_kind}.manifest.json"
        write_json(recipe_config_path, recipe_config)
        recipe_manifest = exporter.build_recipe_manifest(
            config_path=recipe_config_path,
            view_path=view_path,
            view_receipt_path=receipt_path,
            output=recipe_manifest_path,
            allow_test_fixtures=True,
        )
        require(not recipe_manifest["execution"]["training_authorized"], "recipe authorized training")
        require(not recipe_manifest["execution"]["training_performed"], "recipe performed training")
        require(not recipe_manifest["execution"]["model_call_performed"], "recipe performed model call")
        results[view_kind] = {
            "paths": {
                "artifact": view_path,
                "receipt": receipt_path,
                "recipe_config": recipe_config_path,
                "recipe_manifest": recipe_manifest_path,
            },
            "receipt": receipt,
            "recipe_manifest": recipe_manifest,
            "rows": rows,
        }
    return results


def view_text_fields(view_kind: str, row: dict[str, Any]) -> list[str]:
    payload = row["payload"]
    if view_kind == "continued_pretraining":
        return [payload["text"]]
    if view_kind == "correction_instruction":
        return [
            payload["input_text"],
            payload["target_text"],
            payload["original_span"],
            payload["accepted_correction"],
            *payload["acceptable_alternatives"],
        ]
    if view_kind == "preference":
        return [
            payload["prompt"],
            payload["chosen"],
            payload["rejected"],
            *payload["acceptable_alternatives"],
        ]
    if view_kind == "quality_filter":
        return [payload["text"]]
    return []


def validate_separation(views: dict[str, Any]) -> dict[str, Any]:
    record_ids = {name: {row["record_id"] for row in result["rows"]} for name, result in views.items()}
    overlaps = []
    for left, right in combinations(VIEW_ORDER, 2):
        shared = sorted(record_ids[left] & record_ids[right])
        if shared:
            overlaps.append({"left": left, "right": right, "record_ids": shared})
    require(not overlaps, "view record IDs overlap")

    registry = exporter.build_exclusion_registry(
        v011_manifest=exporter.DEFAULT_V011_MANIFEST,
        v02_packet=exporter.DEFAULT_V02_PACKET,
        extra_artifacts=(),
    )
    checked_text_fields = 0
    contamination_matches = 0
    for view_kind in VIEW_ORDER[:-1]:
        schemas = {row["schema_version"] for row in views[view_kind]["rows"]}
        require(len(schemas) == 1, f"{view_kind} is not schema-homogeneous")
        for row in views[view_kind]["rows"]:
            texts = view_text_fields(view_kind, row)
            checked_text_fields += len(texts)
            contamination_matches += int(exporter.any_contamination(texts, registry).matched)
            require(row["eligibility"]["test_fixture"], f"{view_kind} fixture marker is missing")
            require(
                not row["eligibility"]["model_training_eligible"],
                f"{view_kind} fixture became training eligible",
            )
    require(contamination_matches == 0, "non-evaluation output contains evaluation contamination")
    evaluation_schemas = {row["schema_version"] for row in views["heldout_evaluation"]["rows"]}
    require(evaluation_schemas == {"heldout_evaluation_view_v1"}, "evaluation view is not homogeneous")
    artifact_hashes = [sha256_file(views[name]["paths"]["artifact"]) for name in VIEW_ORDER]
    require(len(set(artifact_hashes)) == len(artifact_hashes), "view artifacts are not pairwise distinct")
    return {
        "evaluation_contamination_matches": contamination_matches,
        "evaluation_gold_in_non_evaluation_views": False,
        "exact_and_near_evaluation_checks_applied": True,
        "non_evaluation_text_fields_checked": checked_text_fields,
        "record_id_overlap_count": 0,
        "record_ids_pairwise_disjoint": True,
        "schema_homogeneous_views": len(VIEW_ORDER),
        "view_artifact_hashes_pairwise_distinct": True,
    }


def reproduce_profile(
    output_dir: Path,
    config: dict[str, Any],
    *,
    profile_evidence: str,
    input_root: Path | None,
) -> tuple[dict[str, Any], str]:
    profile_config = resolve_path(config["full_corpus_profile"]["config_path"])
    committed_path = resolve_path(config["full_corpus_profile"]["committed_receipt_path"])
    committed = read_json(committed_path)
    validate_schema(committed, profile_corpus.RECEIPT_SCHEMA_PATH, label="committed corpus profile")
    profile_configuration = read_json(profile_config)
    require(committed["profile_id"] == profile_configuration["profile_id"], "profile ID drift")
    require(
        committed["source_snapshot_id"] == profile_configuration["source_snapshot_id"],
        "profile source snapshot drift",
    )
    require(
        committed["coverage"]["expected_rows"]
        == sum(source["expected"]["rows"] for source in profile_configuration["sources"]),
        "profile expected-row denominator drift",
    )
    require(
        committed["coverage"]["expected_lexical_words"]
        == sum(source["expected"]["lexical_words"] for source in profile_configuration["sources"]),
        "profile expected-word denominator drift",
    )
    output_path = output_dir / "profile/full_corpus_profile_v1.json"
    temporary_candidate_state = "not_generated_committed_receipt_mode"
    if profile_evidence == "fresh":
        require(input_root is not None, "fresh profile evidence requires --input-root")
        with tempfile.TemporaryDirectory(prefix="foundry-reference-candidates-", dir=output_dir) as temporary:
            candidate_path = Path(temporary) / "full-corpus-review-candidates-v1.jsonl"
            result = profile_corpus.profile_corpus(
                config_path=profile_config,
                input_root=input_root,
                summary_output=output_path,
                candidates_output=candidate_path,
            )
            require(result.complete, "fresh full-corpus profile is incomplete")
            require(result.summary == committed, "fresh full-corpus profile differs from committed receipt")
            require(candidate_path.is_file(), "fresh profile candidate artifact was not created")
            require(
                sha256_file(candidate_path) == committed["outputs"]["review_candidates"]["sha256"],
                "fresh profile candidate hash differs from committed receipt",
            )
        require(not candidate_path.exists(), "temporary full-corpus candidate artifact was not deleted")
        temporary_candidate_state = "deleted_after_verification"
    else:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(committed_path, output_path)
    require(output_path.read_bytes() == committed_path.read_bytes(), "profile receipt bytes did not reproduce")
    return committed, temporary_candidate_state


def _normalized_score(
    responses_path: Path,
    *,
    logical_response_path: str,
) -> dict[str, Any]:
    report = evaluate_model.score_saved_run(responses_path)
    report["saved_run"]["path"] = logical_response_path
    return report


def reproduce_baseline(output_dir: Path, config: dict[str, Any]) -> dict[str, Any]:
    baseline = config["baseline"]
    paths = {key: resolve_path(value) for key, value in baseline.items() if key.endswith("_path")}
    baseline_dir = output_dir / "baseline"

    request_rows = evaluate_model.prepare_requests()
    request_output = baseline_dir / "generation_requests.jsonl"
    write_jsonl(request_output, request_rows)
    require(
        request_output.read_bytes() == paths["generation_requests_path"].read_bytes(),
        "source-only generation request packet did not reproduce",
    )
    header = request_rows[0]
    require(header["gold_fields_supplied"] == [], "generation request header contains gold")
    require(not (FORBIDDEN_GOLD_FIELDS & set(header["input_fields"])), "generation input fields contain gold")
    for row in request_rows[1:]:
        require(not (FORBIDDEN_GOLD_FIELDS & set(row)), "generation request row contains gold fields")

    identity_rows = evaluate_model.generate_baseline("identity")
    committed_identity_rows = read_jsonl(paths["identity_responses_path"])
    require(
        identity_rows[1:] == committed_identity_rows[1:],
        "identity response bodies did not reproduce",
    )
    current_header = copy.deepcopy(identity_rows[0])
    current_header["runner_version"] = committed_identity_rows[0]["runner_version"]
    require(
        current_header == committed_identity_rows[0],
        "identity response header drift exceeds the frozen runner source hash",
    )
    identity_rows[0] = committed_identity_rows[0]
    identity_output = baseline_dir / "identity.responses.jsonl"
    write_jsonl(identity_output, identity_rows)
    require(
        identity_output.read_bytes() == paths["identity_responses_path"].read_bytes(),
        "identity saved responses did not reproduce",
    )

    model_rows = evaluate_model.import_model_responses(
        requests_path=request_output,
        model_output_path=paths["model_output_path"],
        metadata_path=paths["model_metadata_path"],
    )
    model_output = baseline_dir / "gemma-4-31b-it.responses.jsonl"
    write_jsonl(model_output, model_rows)
    require(
        model_output.read_bytes() == paths["model_responses_path"].read_bytes(),
        "saved Gemma responses did not reproduce from source-only outputs",
    )

    identity_report = _normalized_score(
        paths["identity_responses_path"],
        logical_response_path=baseline["identity_responses_path"],
    )
    model_report = _normalized_score(
        paths["model_responses_path"],
        logical_response_path=baseline["model_responses_path"],
    )
    require(identity_report == read_json(paths["identity_report_path"]), "identity score report did not reproduce")
    require(model_report == read_json(paths["model_report_path"]), "Gemma score report did not reproduce")
    identity_report_output = baseline_dir / "identity.report.json"
    model_report_output = baseline_dir / "gemma-4-31b-it.report.json"
    shutil.copyfile(paths["identity_report_path"], identity_report_output)
    shutil.copyfile(paths["model_report_path"], model_report_output)

    def metrics(report: dict[str, Any]) -> dict[str, Any]:
        return {
            "edit_f0_5": report["edit_correction"]["f0_5"],
            "edit_precision": report["edit_correction"]["precision"],
            "edit_recall": report["edit_correction"]["recall"],
            "exact_sentence_accuracy": report["exact_sentence"]["accuracy"],
            "headline_calque_recall": report["headline_calque"]["recall"],
        }

    before = metrics(identity_report)
    after = metrics(model_report)
    deltas = {key: after[key] - before[key] for key in before}
    decision_passed = all(
        after[key] > before[key] for key in ("edit_f0_5", "headline_calque_recall", "exact_sentence_accuracy")
    )
    require(decision_passed, "frozen model did not satisfy the predeclared measurement decision")
    return {
        "artifacts": {
            "generation_requests": artifact(request_output, records=len(request_rows)),
            "generation_prompt": artifact(evaluate_model.DEFAULT_PROMPT, records=1),
            "heldout_manifest": artifact(evaluate_model.DEFAULT_MANIFEST, records=1),
            "identity_responses": artifact(identity_output, records=len(identity_rows)),
            "identity_report": artifact(identity_report_output, records=1),
            "model_metadata": artifact(paths["model_metadata_path"], records=1),
            "model_outputs": artifact(paths["model_output_path"], records=len(read_jsonl(paths["model_output_path"]))),
            "model_responses": artifact(model_output, records=len(model_rows)),
            "model_report": artifact(model_report_output, records=1),
            "scoring_dispositions": artifact(evaluate_model.DEFAULT_DISPOSITIONS, records=1),
        },
        "decision": "measurement_interface_validated",
        "decision_passed": decision_passed,
        "decision_rule": baseline["decision_rule"],
        "deltas": deltas,
        "gold_firewall": {
            "forbidden_gold_fields_detected": [],
            "gold_fields_supplied": [],
            "input_fields": header["input_fields"],
            "model_generation_performed": False,
            "source_only_request_count": header["request_count"],
        },
        "identity": before,
        "model": after,
        "reproduction": {
            "generation_requests_byte_identical": True,
            "identity_frozen_header_provenance_preserved": True,
            "identity_responses_byte_identical": True,
            "identity_score_exact": True,
            "model_responses_byte_identical": True,
            "model_score_exact": True,
        },
        "research_question": baseline["research_question"],
    }


def interface_hashes() -> dict[str, str]:
    paths = {
        *exporter.ALL_SCHEMA_PATHS,
        profile_corpus.CONFIG_SCHEMA_PATH,
        profile_corpus.CANDIDATE_SCHEMA_PATH,
        profile_corpus.RECEIPT_SCHEMA_PATH,
        CONFIG_SCHEMA,
        MANIFEST_SCHEMA,
        OBSERVATION_SCHEMA,
    }
    return {path.name: sha256_file(path) for path in sorted(paths, key=lambda item: item.name)}


def build_manifest(
    *,
    config_path: Path,
    config: dict[str, Any],
    chain: dict[str, Any],
    views: dict[str, Any],
    separation: dict[str, Any],
    profile: dict[str, Any],
    baseline: dict[str, Any],
) -> dict[str, Any]:
    chain_values = chain["values"]
    source_payload = chain_values["source_payloads"]
    source_artifacts = {name: artifact(path, records=1) for name, path in sorted(chain["paths"].items())}
    view_manifest: dict[str, Any] = {}
    for name in VIEW_ORDER:
        result = views[name]
        recipe = result["recipe_manifest"]
        view_manifest[name] = {
            "artifact": artifact(result["paths"]["artifact"], records=len(result["rows"])),
            "model_training_eligible_records": recipe["preparation"]["model_training_eligible_records"],
            "permitted_destination": VIEW_DESTINATIONS[name],
            "receipt": artifact(result["paths"]["receipt"], records=1),
            "recipe_config": artifact(result["paths"]["recipe_config"], records=1),
            "recipe_manifest": artifact(result["paths"]["recipe_manifest"], records=1),
            "schema_version": result["rows"][0]["schema_version"],
            "test_fixture_records": recipe["preparation"]["test_fixture_records"],
        }
    profile_receipt_path = resolve_path(config["full_corpus_profile"]["committed_receipt_path"])
    manifest = {
        "baseline": baseline,
        "build_id": config["build_id"],
        "commands": {
            "fresh": (
                ".venv/bin/python -m scripts.projects.open_model_data.reference_build "
                "--profile-evidence fresh --input-root <repository-with-source-databases> "
                "--output-dir <local-output-directory> --manifest-output <manifest.json> "
                "--observation-output <observation.json>"
            ),
            "receipt_validation": (
                ".venv/bin/python -m scripts.projects.open_model_data.reference_build "
                "--profile-evidence committed --output-dir <local-output-directory> "
                "--manifest-output <manifest.json>"
            ),
        },
        "config": {
            "logical_path": logical_path(config_path),
            "sha256": sha256_file(config_path),
        },
        "determinism": {
            "serialization": "UTF-8 canonical JSON with sorted keys and LF",
            "timestamps_omitted": True,
            "view_order": list(VIEW_ORDER),
        },
        "interfaces": {
            "implementation_hashes": {
                "evaluate_model.py": sha256_file(Path(evaluate_model.__file__)),
                "reference_build.py": sha256_file(Path(__file__)),
            },
            "schema_hashes": interface_hashes(),
        },
        "limitations": [
            "The correction and reviewer decisions are synthetic structural fixtures, not qualified Ukrainian-human adjudication or training gold.",
            "The complete corpus result is morphology and inventory evidence, not sentence-level grammaticality or naturalness judgment.",
            "The 677-item benchmark is a targeted grammar-and-calque set; it is not broad Ukrainian proficiency or a general model leaderboard.",
            "Gemma versus identity validates the frozen measurement interface; it is not a before/after Foundry-data treatment and supports no causal training claim.",
            "Tokenizer diagnostics remain not run because no separately approved pinned tokenizer interface exists for this reference build.",
            "Gemma outputs are previously saved evidence; this build performs no model generation.",
        ],
        "profile": {
            "admission": profile["admission_safety"],
            "candidate_artifact": profile["outputs"]["review_candidates"],
            "config": artifact(
                resolve_path(config["full_corpus_profile"]["config_path"]),
                records=1,
            ),
            "coverage": {
                "complete": profile["coverage"]["complete"],
                "expected_lexical_words": profile["coverage"]["expected_lexical_words"],
                "expected_rows": profile["coverage"]["expected_rows"],
                "inaccessible_sources": profile["coverage"]["inaccessible_sources"],
                "processed_lexical_words": profile["coverage"]["processed_lexical_words"],
                "processed_rows": profile["coverage"]["processed_rows"],
            },
            "morphology": {
                "distinct_lemmas_observed": profile["vesum"]["distinct_lemmas_observed"],
                "interface": profile["vesum"]["interface"],
                "snapshot_id": profile["vesum"]["snapshot_id"],
                "tokens_attested": profile["vesum"]["tokens_attested"],
                "tokens_unknown": profile["vesum"]["tokens_unknown"],
                "unknown_distinct_normalized_forms": profile["unknown_forms"]["distinct_normalized_forms"],
            },
            "receipt": artifact(profile_receipt_path, records=1),
            "receipt_byte_identical": True,
            "tokenizer_diagnostics": profile["measurement_contract"]["tokenizer_diagnostics"],
        },
        "safety": {
            **config["run_policy"],
            "dataset_redistribution_performed": False,
            "model_call_performed": False,
            "training_performed": False,
        },
        "schema_version": "reference_build_manifest_v1",
        "separation": separation,
        "source_to_view_lineage": {
            "artifacts": source_artifacts,
            "evidence_sources": sorted(item["source"] for item in chain_values["correction_candidates"]["evidence"]),
            "fixture": {
                "accepted_correction_sha256": sha256_text(config["fixture"]["accepted_correction"]),
                "candidate_id": chain_values["correction_candidates"]["candidate_id"],
                "correction_record_id": chain_values["correction_records"]["record_id"],
                "incorrect_span_sha256": sha256_text(config["fixture"]["incorrect_span"]),
                "language_span_partition_complete": True,
                "masked_character_spans": [
                    {"end": span["end"], "reason": span["reason"], "start": span["start"]}
                    for span in source_payload["language_span_review"]["character_spans"]
                    if span["modern_loss_action"] == "mask_from_loss"
                ],
                "payload_id": source_payload["payload_id"],
                "source_record_id": chain_values["source_records"]["record_id"],
                "source_text_sha256": sha256_text(config["fixture"]["source_text"]),
                "test_fixture": True,
            },
            "source_contract_admitted_records": chain["admission"]["admitted_records"],
            "views": view_manifest,
        },
    }
    validate_schema(manifest, MANIFEST_SCHEMA, label="reference build manifest")
    return manifest


def build_reference(
    *,
    config_path: Path,
    output_dir: Path,
    profile_evidence: str,
    input_root: Path | None,
) -> tuple[dict[str, Any], str]:
    config = load_config(config_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    chain = build_fixture_chain(output_dir, config)
    views = build_views_and_recipes(output_dir, config, chain)
    separation = validate_separation(views)
    profile, temporary_candidate_state = reproduce_profile(
        output_dir,
        config,
        profile_evidence=profile_evidence,
        input_root=input_root,
    )
    baseline = reproduce_baseline(output_dir, config)
    manifest = build_manifest(
        config_path=config_path,
        config=config,
        chain=chain,
        views=views,
        separation=separation,
        profile=profile,
        baseline=baseline,
    )
    return manifest, temporary_candidate_state


def maximum_rss_bytes() -> int:
    maximum = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    return maximum if sys.platform == "darwin" else maximum * 1024


def observation(
    *,
    manifest_path: Path,
    manifest: dict[str, Any],
    profile_evidence: str,
    temporary_candidate_state: str,
    wall_seconds: float,
) -> dict[str, Any]:
    value = {
        "build_id": manifest["build_id"],
        "execution": {
            "completed": True,
            "exit_code": 0,
            "maximum_rss_bytes": maximum_rss_bytes(),
            "profile_evidence": profile_evidence,
            "temporary_candidate_state": temporary_candidate_state,
            "wall_seconds": round(wall_seconds, 6),
        },
        "manifest": artifact(manifest_path, records=1),
        "safety": manifest["safety"],
        "schema_version": "reference_build_observation_v1",
    }
    validate_schema(value, OBSERVATION_SCHEMA, label="reference build observation")
    return value


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--manifest-output", type=Path, required=True)
    parser.add_argument("--observation-output", type=Path)
    parser.add_argument("--profile-evidence", choices=("committed", "fresh"), required=True)
    parser.add_argument("--input-root", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.profile_evidence == "fresh" and args.input_root is None:
        parser.error("--input-root is required with --profile-evidence fresh")
    started = time.perf_counter()
    try:
        manifest, candidate_state = build_reference(
            config_path=args.config,
            output_dir=args.output_dir,
            profile_evidence=args.profile_evidence,
            input_root=args.input_root,
        )
        write_json(args.manifest_output, manifest)
        if args.observation_output is not None:
            receipt = observation(
                manifest_path=args.manifest_output,
                manifest=manifest,
                profile_evidence=args.profile_evidence,
                temporary_candidate_state=candidate_state,
                wall_seconds=time.perf_counter() - started,
            )
            write_json(args.observation_output, receipt)
        print(canonical_json(manifest))
        return 0
    except (ReferenceBuildError, correction_factory.FactoryError, exporter.ExportError) as exc:
        parser.exit(2, f"error: {exc}\n")


if __name__ == "__main__":
    raise SystemExit(main())
