"""Hermetic tests for the comparative historical periodization freeze."""

from __future__ import annotations

import copy
import hashlib
import json

import pytest

from scripts.projects.open_model_data import phase3_historical_periodization as periodization


def _freeze() -> dict:
    return json.loads(periodization.FREEZE_PATH.read_text(encoding="utf-8"))


def _reseal(value: dict) -> dict:
    body = {key: item for key, item in value.items() if key != "receipt_sha256"}
    value["receipt_sha256"] = hashlib.sha256((periodization.canonical_json(body) + "\n").encode("utf-8")).hexdigest()
    return value


def _matches(assignment: dict, framework_id: str) -> dict[str, str]:
    framework = next(item for item in assignment["framework_matches"] if item["framework_id"] == framework_id)
    return {item["stage_id"]: item["match_status"] for item in framework["matches"]}


def test_tracked_freeze_is_exact_and_preserves_three_frameworks():
    freeze = periodization.load_freeze()

    assert periodization.sha256_file(periodization.FREEZE_PATH) == periodization.EXPECTED_FREEZE_SHA256
    assert freeze["bindings"] == periodization.EXPECTED_BINDINGS
    assert freeze["periodization_layer_ready"] is True
    assert freeze["overall_phase3_source_freeze_ready"] is False
    assert freeze["scope"]["modern_only"] is False
    assert freeze["scope"]["canonical_framework_id"] is None
    assert freeze["scope"]["frameworks_preserved_without_collapse"] is True
    assert freeze["scope"]["scalar_language_age_claim_allowed"] is False

    frameworks = {item["framework_id"]: item for item in freeze["frameworks"]}
    assert set(frameworks) == set(periodization.REQUIRED_FRAMEWORKS)
    assert {key: item["primary_stage_count"] for key, item in frameworks.items()} == (periodization.REQUIRED_FRAMEWORKS)
    assert len(frameworks["nimchuk_five_stage_with_middle_subperiods"]["stages"]) == 7


def test_five_stage_university_synthesis_is_explicit_and_not_modern_only():
    framework = next(
        item
        for item in periodization.load_freeze()["frameworks"]
        if item["framework_id"] == "university_five_stage_synthesis"
    )

    assert [item["label_uk"] for item in framework["stages"]] == [
        "Праслов’янська мова з протосхіднослов’янськими діалектами",
        "Протоукраїнська мова",
        "Староукраїнська мова",
        "Середньоукраїнська мова",
        "Нова українська мова",
    ]
    assert framework["stages"][1]["start_boundary"]["label"] == "VII ст."
    assert framework["stages"][4]["start_boundary"]["label"] == "з кінця XVIII ст."


def test_1413_assignment_keeps_three_attributed_answers():
    assignment = periodization.classify_year(1413)

    assert _matches(assignment, "university_five_stage_synthesis") == {"serednoukrainska": "definite"}
    assert _matches(assignment, "shevelov_detailed_six_period") == {"rannoserendoukrainskyi": "definite"}
    assert _matches(assignment, "nimchuk_five_stage_with_middle_subperiods") == {
        "serednoukrainska_abo_serednoukrainoruska": "possible_boundary_overlap",
        "rannia_serednoukrainska": "possible_boundary_overlap",
    }
    assert assignment["canonical_framework_id"] is None
    assert assignment["safeguards"]["historical_forms_protected"] is True
    assert assignment["safeguards"]["modern_correction_eligible"] is False


def test_boundary_uncertainty_is_not_silently_rounded_to_one_year():
    assignment = periodization.classify_year(1050)

    assert _matches(assignment, "university_five_stage_synthesis") == {"staroukrainska": "definite"}
    assert _matches(assignment, "shevelov_detailed_six_period") == {
        "protoukrainskyi": "possible_boundary_overlap",
        "davnoukrainskyi": "possible_boundary_overlap",
    }
    assert _matches(assignment, "nimchuk_five_stage_with_middle_subperiods") == {"davnorusko_ukrainska": "definite"}


def test_nimchuk_primary_text_gap_remains_explicit_and_limited():
    freeze = periodization.load_freeze()
    gap = next(item for item in freeze["remaining_gaps"] if item["gap_id"].startswith("nimchuk"))
    bibliography = next(
        item for item in freeze["evidence"] if item["evidence_id"] == "nimchuk_primary_article_bibliography"
    )

    assert bibliography["full_text_state"] == "bibliographic_only"
    assert bibliography["document_sha256"] is None
    assert "primary_source_grade_for_nimchuk_framework" in gap["blocking_for"]
    assert "qualified_source_attributed_periodization_comparison" in gap["nonblocking_for"]


def test_validator_rejects_framework_collapse_even_when_resealed():
    freeze = copy.deepcopy(_freeze())
    freeze["scope"]["canonical_framework_id"] = "shevelov_detailed_six_period"

    with pytest.raises(periodization.HistoricalPeriodizationError, match="schema violation"):
        periodization.validate_freeze(_reseal(freeze))


def test_validator_rejects_primary_text_authority_without_bytes():
    freeze = copy.deepcopy(_freeze())
    bibliography = next(
        item for item in freeze["evidence"] if item["evidence_id"] == "nimchuk_primary_article_bibliography"
    )
    bibliography["authority"] = "primary_scholarship"

    with pytest.raises(periodization.HistoricalPeriodizationError, match="bibliographic-only evidence"):
        periodization.validate_freeze(_reseal(freeze))


def test_validator_rejects_erasure_of_nimchuk_primary_text_gap():
    freeze = copy.deepcopy(_freeze())
    freeze["remaining_gaps"] = []

    with pytest.raises(periodization.HistoricalPeriodizationError, match="must remain explicit"):
        periodization.validate_freeze(_reseal(freeze))


def test_validator_rejects_receipt_drift():
    freeze = copy.deepcopy(_freeze())
    freeze["frameworks"][0]["attributed_to"] += " drift"

    with pytest.raises(periodization.HistoricalPeriodizationError, match="receipt seal mismatch"):
        periodization.validate_freeze(freeze)


def test_source_verification_checks_relative_paths_and_bytes(tmp_path):
    source_root = tmp_path / "source-root"
    source_root.mkdir()
    source_file = source_root / "periodization.jsonl"
    source_file.write_bytes(b"immutable periodization evidence\n")
    digest = periodization.sha256_file(source_file)
    freeze = {
        "evidence": [
            {
                "evidence_id": "fixture",
                "full_text_state": "locally_acquired",
                "document_sha256": digest,
                "locator": {"project_relative_path": "periodization.jsonl"},
            },
            {
                "evidence_id": "bibliography",
                "full_text_state": "bibliographic_only",
                "document_sha256": None,
                "locator": {"project_relative_path": None},
            },
        ]
    }

    receipt = periodization.validate_acquired_evidence(freeze, source_root)
    assert receipt["verified_source_count"] == 1
    assert receipt["verified_sources"][0]["document_sha256"] == digest

    source_file.write_bytes(b"drift\n")
    with pytest.raises(periodization.HistoricalPeriodizationError, match="evidence byte drift"):
        periodization.validate_acquired_evidence(freeze, source_root)
