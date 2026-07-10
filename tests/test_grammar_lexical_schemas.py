"""Phase 0 contracts for Ukrainian grammar and lexical gate artifacts.

These tests validate schemas and data-only golden skeletons. They deliberately
do not import or implement grammar, lexical, VESUM, scoring, or judge runtime
behavior.
"""

from __future__ import annotations

import json
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
from typing import Any

import pytest
import yaml
from jsonschema import Draft202012Validator

REPO_ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_SCHEMA = json.loads(
    (REPO_ROOT / "schemas/ua-grammar-lexical-evidence.v2.schema.json").read_text(encoding="utf-8")
)
SCORE_SCHEMA = json.loads(
    (REPO_ROOT / "schemas/ua-grammar-lexical-score.v2.schema.json").read_text(encoding="utf-8")
)
GOLDEN_SKELETONS = REPO_ROOT / "tests/fixtures/grammar_lexical/golden_skeletons.yaml"
EVIDENCE_VALIDATOR = Draft202012Validator(EVIDENCE_SCHEMA)
SCORE_VALIDATOR = Draft202012Validator(SCORE_SCHEMA)


def _sha256(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()


def _schema_errors(validator: Draft202012Validator, document: dict[str, Any]) -> list[str]:
    return sorted(error.message for error in validator.iter_errors(document))


def _assert_evidence_invariants(document: dict[str, Any]) -> None:
    """Validate §8.1 and §8.4 arithmetic outside JSON Schema."""

    coverage = document["coverage"]
    assert coverage["eligible_ukrainian_words"] == (
        coverage["scored_ukrainian_words"] + coverage["coverage_missing_ukrainian_words"]
    )
    if document["result"] == "PASS":
        assert coverage["coverage_missing"] == 0
        assert coverage["coverage_missing_ukrainian_words"] == 0


def _assert_score_invariants(document: dict[str, Any]) -> None:
    """Validate the §9.2 totals that JSON Schema cannot calculate."""

    counts = document["counts"]
    assert counts["outputs_total"] == (
        counts["outputs_pass"] + counts["outputs_fail_content"] + counts["outputs_needs_audit"]
    )
    assert counts["outputs_total"] == len(set(document["output_artifact_ids"]))
    assert counts["eligible_ukrainian_words"] == (
        counts["scored_ukrainian_words"] + counts["coverage_missing_ukrainian_words"]
    )
    if document["rank_eligibility"] == "ELIGIBLE":
        assert counts["eligible_ukrainian_words"] == counts["scored_ukrainian_words"]
        assert counts["coverage_missing_ukrainian_words"] == 0
        assert counts["coverage_missing"] == 0
        assert document["rates"]["grammar_errors_per_1000"] is not None
        assert document["rates"]["lexical_errors_per_1000"] is not None


def _valid_evidence_document() -> dict[str, Any]:
    region_id = _sha256("surface-region")
    token_id = _sha256("surface-token")
    scan_unit_id = _sha256("scan-unit")
    candidate_id = _sha256("gate-candidate")
    binding_id = _sha256("evidence-binding")
    return {
        "schema_version": "ua_grammar_lexical_evidence.v2",
        "artifact_kind": "gate_result",
        "run_id": "phase-0-contract-test",
        "gate_version": "v2",
        "target": {
            "artifact_id": "fixture-34",
            "artifact_type": "eval_output",
            "content_sha256": _sha256("fixture-34-content"),
            "level_policy": "a1",
            "writer_model_id": "fixture-writer",
            "writer_family": "fixture-family",
        },
        "source_snapshots": {
            "vesum": "vesum-fixture",
            "pravopys_rules": "pravopys-fixture",
            "ua_gec": "ua-gec-fixture",
            "antonenko": "antonenko-fixture",
            "grac": "grac-fixture",
            "balla": "balla-fixture",
            "heritage": "heritage-fixture",
            "sum11": "sum11-fixture",
        },
        "surface_regions": [
            {
                "region_id": region_id,
                "raw_start": 0,
                "raw_end": 12,
                "surface_kind": "ACTIVITY_FIELD",
                "role": "UKRAINIAN_TARGET",
                "role_method": "STRUCTURED_FIELD",
                "raw_sha256": _sha256("fixture-surface"),
            }
        ],
        "tokens": [
            {
                "token_id": token_id,
                "region_id": region_id,
                "raw_start": 0,
                "raw_end": 4,
                "raw_sha256": _sha256("fixture-token"),
            }
        ],
        "scan_units": [
            {
                "scan_unit_id": scan_unit_id,
                "unit_kind": "TOKEN",
                "region_ids": [region_id],
                "token_ids": [token_id],
                "raw_start": 0,
                "raw_end": 4,
                "required_detector_ids": ["vesum-form-v2"],
            }
        ],
        "detector_runs": [
            {
                "detector_run_id": _sha256("detector-run"),
                "scan_unit_id": scan_unit_id,
                "detector_id": "vesum-form-v2",
                "detector_version": "v2",
                "applicability": "APPLICABLE",
                "outcome": "CANDIDATE",
                "candidate_ids": [candidate_id],
                "evidence_binding_ids": [binding_id],
                "failure_reason": None,
            }
        ],
        "candidates": [
            {
                "candidate_id": candidate_id,
                "candidate_class": "AGREEMENT",
                "hypothesis": {
                    "hypothesis_id": _sha256("hypothesis"),
                    "type": "LOCAL_RELATION",
                    "target_locus_spans": [{"start": 0, "end": 4}],
                    "involved_token_ids": [token_id],
                    "asserted_risk": "registered fixture risk",
                },
                "target_window": {
                    "candidate_id": "anchor-candidate",
                    "window_start": 0,
                    "window_end": 12,
                    "window_sha256": _sha256("window"),
                    "logical_unit_complete": True,
                },
                "evidence_candidate_ids": [_sha256("anchor-candidate")],
                "allowed_relations": ["ACCEPTABLE", "AGREEMENT_ERROR"],
                "canonical_rule_family": "fixture-local-agreement",
            }
        ],
        "evidence_bindings": [
            {
                "evidence_binding_id": binding_id,
                "candidate_id": _sha256("anchor-candidate"),
                "source_role": "VESUM_ANALYSIS",
                "authority_class": "NORMATIVE",
                "target_span_ids": [token_id],
                "rule_or_pair_id": None,
                "corpus_snapshot_id": "vesum-fixture",
                "ancestor_source_ids": [],
            }
        ],
        "findings": [
            {
                "finding_id": "fixture-finding",
                "issue_id": "FIXTURE_FINDING",
                "issue_class": "grammar",
                "dimension": "contact_grammar",
                "severity": "info",
                "contact_source_lang": "unknown",
                "source_lang": "unknown",
                "track_l1": "en",
                "ua_gec_tag": None,
                "confidence": "deterministic",
                "disposition": "suppressed_fp",
                "file": "tests/fixtures/grammar_lexical/golden_skeletons.yaml",
                "line": 1,
                "span": {"start": 0, "end": 4},
                "excerpt": "fixture",
                "message": "Static Phase 0 fixture finding.",
                "suggested_replacement": [],
                "detector": {
                    "adapter": "phase-0-contract-test",
                    "rule_id": "fixture-rule",
                    "pattern_id": "fixture-pattern",
                },
                "attribution": {
                    "corpus": "fixture",
                    "license": None,
                    "doc_id": None,
                    "pair_id": None,
                    "evidence": "Phase 0 contract test",
                },
            }
        ],
        "audits": [],
        "coverage": {
            "scan_units_total": 1,
            "scan_units_complete": 1,
            "coverage_missing": 0,
            "coverage_missing_by_reason": {},
            "eligible_ukrainian_words": 1,
            "scored_ukrainian_words": 1,
            "coverage_missing_ukrainian_words": 0,
        },
        "metrics": {
            "confirmed_grammar_errors": 0,
            "confirmed_lexical_errors": 0,
            "unresolved_candidates": 0,
            "target_vocab_required": 1,
            "target_vocab_realized": 1,
            "target_vocab_coverage": 1.0,
            "content_lemma_tokens": 1,
            "mattr_window": None,
            "mattr": None,
            "reference_mattr": None,
            "lexical_diversity_retention": None,
            "flattening_flag": False,
        },
        "result": "PASS",
    }


def _valid_score_document() -> dict[str, Any]:
    return {
        "schema_version": "ua_grammar_lexical_score.v2",
        "artifact_kind": "model_scorecard",
        "evaluation_set_id": "phase-0-contract-test",
        "evaluation_set_sha256": _sha256("evaluation-set"),
        "prompt_set_sha256": _sha256("prompt-set"),
        "generation_config_sha256": _sha256("generation-config"),
        "reference_set_sha256": _sha256("reference-set"),
        "model": {
            "provider": "fixture-provider",
            "model_id": "fixture-model",
            "family": "fixture-family",
            "revision": None,
        },
        "gate_version": "v2",
        "source_snapshot_ids": {"vesum": "vesum-fixture"},
        "output_artifact_ids": ["fixture-34"],
        "counts": {
            "outputs_total": 1,
            "outputs_pass": 1,
            "outputs_fail_content": 0,
            "outputs_needs_audit": 0,
            "eligible_ukrainian_words": 1,
            "scored_ukrainian_words": 1,
            "coverage_missing_ukrainian_words": 0,
            "coverage_missing": 0,
            "grammar_error_units": 0,
            "lexical_error_units": 0,
            "unresolved_candidates": 0,
            "target_vocab_required": 1,
            "target_vocab_realized": 1,
            "outputs_below_target_vocab": 0,
            "outputs_flattened": 0,
        },
        "rates": {
            "grammar_errors_per_1000": 0.0,
            "lexical_errors_per_1000": 0.0,
            "target_vocab_coverage": 1.0,
            "aggregate_mattr": None,
            "lexical_diversity_retention": None,
            "flattening_trend_delta": None,
        },
        "reproducibility": "DETERMINISTIC_NO_JUDGE",
        "rank_eligibility": "ELIGIBLE",
    }


def test_accepts_complete_valid_evidence_and_score_artifacts() -> None:
    evidence = _valid_evidence_document()
    score = _valid_score_document()

    assert _schema_errors(EVIDENCE_VALIDATOR, evidence) == []
    assert _schema_errors(SCORE_VALIDATOR, score) == []
    _assert_evidence_invariants(evidence)
    _assert_score_invariants(score)


def test_rejects_unknown_registered_enum_values() -> None:
    mutations = [
        (EVIDENCE_VALIDATOR, _valid_evidence_document(), ("surface_regions", 0, "role")),
        (EVIDENCE_VALIDATOR, _valid_evidence_document(), ("detector_runs", 0, "outcome")),
        (EVIDENCE_VALIDATOR, _valid_evidence_document(), ("candidates", 0, "allowed_relations", 0)),
        (EVIDENCE_VALIDATOR, _valid_evidence_document(), ("evidence_bindings", 0, "source_role")),
        (SCORE_VALIDATOR, _valid_score_document(), ("rank_eligibility",)),
    ]

    for validator, document, path in mutations:
        target: Any = document
        for key in path[:-1]:
            target = target[key]
        target[path[-1]] = "UNKNOWN_ENUM"
        assert _schema_errors(validator, document), f"unknown enum at {path} must be rejected"


def test_rejects_missing_required_fields_and_bad_sha256_values() -> None:
    evidence = _valid_evidence_document()
    evidence["coverage"].pop("scored_ukrainian_words")
    assert _schema_errors(EVIDENCE_VALIDATOR, evidence)

    bad_evidence = _valid_evidence_document()
    bad_evidence["target"]["content_sha256"] = "not-a-sha256"
    assert _schema_errors(EVIDENCE_VALIDATOR, bad_evidence)

    score = _valid_score_document()
    score["counts"].pop("outputs_total")
    assert _schema_errors(SCORE_VALIDATOR, score)

    bad_score = _valid_score_document()
    bad_score["reference_set_sha256"] = "g" * 64
    assert _schema_errors(SCORE_VALIDATOR, bad_score)


def test_rejects_additional_properties_at_every_contract_boundary() -> None:
    evidence = _valid_evidence_document()
    evidence["unexpected"] = True
    assert _schema_errors(EVIDENCE_VALIDATOR, evidence)

    evidence = _valid_evidence_document()
    evidence["surface_regions"][0]["unexpected"] = True
    assert _schema_errors(EVIDENCE_VALIDATOR, evidence)

    score = _valid_score_document()
    score["model"]["unexpected"] = True
    assert _schema_errors(SCORE_VALIDATOR, score)


def test_exposes_the_required_phase_zero_compatibility_registers() -> None:
    assert EVIDENCE_SCHEMA["$defs"]["layerAReason"]["enum"] == [
        "ANCHORED_CONTIGUOUS",
        "ANCHORED_ORDERED_SEGMENTS",
        "PRESENT_MULTI",
        "ABSENT",
        "FUZZY_AMBIGUOUS",
        "OUTSIDE_SCAN",
        "RAW_MAPPING_AMBIGUOUS",
        "CROSS_EVENT_STITCH_FORBIDDEN",
        "INCOMPLETE_CAPTURE",
        "INCOMPLETE_CANDIDATE_SET",
        "TOOL_ERROR",
        "INSUFFICIENT_MASS",
        "BELOW_TAU",
        "DIGIT_NOT_ALIGNED",
        "SALIENT_NOT_ALIGNED",
    ]
    assert EVIDENCE_SCHEMA["$defs"]["gateDecision"]["enum"] == [
        "ACCEPT",
        # Design §6.7: AUTHENTIC_HERITAGE_DEFENSE × {A, N} resolves ONLY the
        # form-validity candidate; the containing LEXICAL_USE still requires
        # contextual coverage (§8.1). Without this value those fusion cells
        # are unrepresentable and implementations would round to ACCEPT
        # (silently completing coverage) or AUDIT.
        "ACCEPT_FORM_ONLY",
        "REJECT",
        "DEFER",
        "UNCOVERED",
        "AUDIT",
    ]
    assert EVIDENCE_SCHEMA["$defs"]["lexicalFusedClass"]["enum"] == [
        "EXACT_ANTONENKO_REJECT",
        "EXACT_UA_GEC_REJECT",
        "EXACT_RULE_PLUS_MODERN_CONTRARY",
        "POSITIVE_EXACT_ALLOW",
        "AUTHENTIC_HERITAGE_DEFENSE",
        "HEURISTIC_OR_GRAC_ONLY",
        "BALLA_OBSERVATION",
        "NO_DECISIVE_EVIDENCE",
        "LINEAGE_OR_SOURCE_FAILURE",
    ]


def test_coverage_fields_represent_eligible_scored_and_missing_words() -> None:
    evidence = _valid_evidence_document()
    evidence["coverage"].update(
        {
            "eligible_ukrainian_words": 3,
            "scored_ukrainian_words": 2,
            "coverage_missing_ukrainian_words": 1,
            "coverage_missing": 1,
        }
    )
    evidence["result"] = "NEEDS_AUDIT"

    assert _schema_errors(EVIDENCE_VALIDATOR, evidence) == []
    _assert_evidence_invariants(evidence)

    invalid = deepcopy(evidence)
    invalid["coverage"]["eligible_ukrainian_words"] = 4
    with pytest.raises(AssertionError):
        _assert_evidence_invariants(invalid)


def test_score_output_invariants_and_flattening_ineligibility_are_representable() -> None:
    score = _valid_score_document()
    score["counts"].update(
        {
            "outputs_total": 2,
            "outputs_pass": 1,
            "outputs_needs_audit": 1,
            "eligible_ukrainian_words": 3,
            "scored_ukrainian_words": 2,
            "coverage_missing_ukrainian_words": 1,
            "coverage_missing": 1,
            "outputs_flattened": 1,
        }
    )
    score["output_artifact_ids"] = ["fixture-34", "fixture-35"]
    score["rank_eligibility"] = "INELIGIBLE_FLATTENING"
    score["rates"]["grammar_errors_per_1000"] = None
    score["rates"]["lexical_errors_per_1000"] = None

    assert _schema_errors(SCORE_VALIDATOR, score) == []
    _assert_score_invariants(score)

    invalid = deepcopy(score)
    invalid["counts"]["outputs_total"] = 3
    with pytest.raises(AssertionError):
        _assert_score_invariants(invalid)


def test_round_trips_data_only_golden_skeletons() -> None:
    skeletons = yaml.safe_load(GOLDEN_SKELETONS.read_text(encoding="utf-8"))
    round_tripped = yaml.safe_load(yaml.safe_dump(skeletons, allow_unicode=True, sort_keys=False))

    assert round_tripped == skeletons
    assert skeletons["qualification_eligible"] is False
    assert skeletons["qualification_blockers"]

    role_enum = EVIDENCE_SCHEMA["$defs"]["surfaceRegion"]["properties"]["role"]["enum"]
    outcome_enum = EVIDENCE_SCHEMA["$defs"]["detectorRun"]["properties"]["outcome"]["enum"]
    decision_enum = EVIDENCE_SCHEMA["$defs"]["gateDecision"]["enum"]
    fixture_numbers = set()
    for case in skeletons["cases"]:
        fixture_numbers.update(case["fixture_numbers"])
        assert case["input_text"]
        assert case["annotation_status"] == "SKELETON"
        assert set(case["expected_surface_roles"]).issubset(role_enum)
        assert set(case["expected_detector_outcomes"]).issubset(outcome_enum)
        assert case["expected_decision"] in {None, *decision_enum}
        assert set(case.get("allowed_decisions", [])).issubset(decision_enum)

    assert fixture_numbers == {
        16,
        17,
        18,
        19,
        20,
        21,
        22,
        24,
        25,
        *range(34, 48),
        48,
        49,
        50,
        51,
        52,
        53,
        60,
        61,
        63,
        64,
        65,
        66,
        67,
        68,
    }
