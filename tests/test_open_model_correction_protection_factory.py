"""Phase 3 correction/protection factory and known-answer tests."""

from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator

from scripts.projects.open_model_data import correction_protection_factory as factory

ROOT = Path(__file__).resolve().parents[1]
KNOWN_ANSWERS = ROOT / "data/projects/open_model_data/detector/correction_protection_known_answers_v1.json"
THRESHOLDS = ROOT / "data/projects/open_model_data/detector/correction_protection_thresholds_v1.json"
MODEL_LANES = ROOT / "data/projects/open_model_data/evidence/correction_protection_model_lanes_v1.json"


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_known_answers_cover_all_categories_and_frozen_minima() -> None:
    known_answers = _json(KNOWN_ANSWERS)
    thresholds = _json(THRESHOLDS)
    assert tuple(known_answers["categories"]) == factory.CATEGORY_IDS
    assert tuple(thresholds["categories"]) == factory.CATEGORY_IDS
    assert sum(
        len(specification.get(role, []))
        for specification in known_answers["categories"].values()
        for role in ("positive", "acceptable_control", "protected")
    ) == 99
    gates = factory.gate_results(known_answers, thresholds, model_proposal_lanes=0, model_dissent_lanes=0)
    assert gates["russian_lexical_inflectional_intrusion"]["state"] == "passed"
    assert gates["russian_lexical_inflectional_intrusion"]["correction_release_allowed"] is True
    assert gates["contextual_calque_government_valency"]["state"] == "research_only"
    assert gates["contextual_calque_government_valency"]["correction_release_allowed"] is False
    assert gates["modern_literary_ukrainian_control"]["state"] == "passed"
    assert gates["surzhyk_contested_contact"]["state"] == "research_only"


def test_every_known_answer_has_one_immutable_surface_and_publishable_source() -> None:
    known_answers = _json(KNOWN_ANSWERS)
    config_sha256 = factory.sha256_file(KNOWN_ANSWERS)
    source_validator = factory.validators()[factory.SOURCE_SCHEMA]
    for category_id, specification in known_answers["categories"].items():
        for role in ("positive", "acceptable_control", "protected"):
            for index, item in enumerate(specification.get(role, [])):
                assert item["text"].count(item["surface"]) == 1
                source, start, end = factory.canary_source(
                    config=known_answers,
                    config_sha256=config_sha256,
                    category_id=category_id,
                    role=role,
                    index=index,
                    item=item,
                )
                assert source["context"]["context_text"] == item["text"]
                assert source["context"]["publication_capability_state"] == "permitted_with_evidence"
                assert item["text"][start:end] == item["surface"]
                assert list(source_validator.iter_errors(source)) == []
    source_versions = {
        evidence["source_version"]
        for specification in known_answers["categories"].values()
        for evidence in specification["evidence"]
    }
    assert "repository-pinned" not in source_versions
    assert "pinned-project-environment" not in source_versions


def test_phase2_source_blind_routes_are_conservative() -> None:
    base = {
        "dimensions": {"period": "modern", "genre": "prose", "register": "literary"},
        "signals": {"counts": {"russian_specific": 0}},
        "heldout_contamination": {"state": "clear"},
    }
    assert factory.phase2_route(base) == ("modern_literary_ukrainian_control", "unresolved")
    historical = {**base, "dimensions": {**base["dimensions"], "period": "middle_ukrainian"}}
    assert factory.phase2_route(historical) == ("historical_archaic_ukrainian", "protected")
    contact = {**base, "signals": {"counts": {"russian_specific": 1}}}
    assert factory.phase2_route(contact) == ("surzhyk_contested_contact", "unresolved")
    contaminated = {**base, "heldout_contamination": {"state": "matched"}}
    assert factory.phase2_route(contaminated) == ("surzhyk_contested_contact", "excluded")


def test_bundle_schema_is_strict_and_meta_valid() -> None:
    schema = _json(factory.BUNDLE_SCHEMA)
    Draft202012Validator.check_schema(schema)
    assert schema["additionalProperties"] is False


def test_model_lane_is_attributed_and_failed_lane_cannot_strengthen_gate() -> None:
    active = factory.validators()
    proposals, lane_counts = factory.load_model_proposals(MODEL_LANES, active)
    assert lane_counts == {"proposal_lanes": 1, "dissent_lanes": 1}
    assert set(proposals) == {"participate", "copula", "duration", "regarding"}
    assert {proposal["exact_model_id"] for proposal in proposals.values()} == {"grok-4.5"}
    lanes = _json(MODEL_LANES)["lanes"]
    failed = next(lane for lane in lanes if lane["parser_status"] == "failed")
    assert failed["gate_strengthening_allowed"] is False
    assert failed["proposals"] == []
    gates = factory.gate_results(
        _json(KNOWN_ANSWERS),
        _json(THRESHOLDS),
        model_proposal_lanes=lane_counts["proposal_lanes"],
        model_dissent_lanes=lane_counts["dissent_lanes"],
    )
    assert gates["contextual_calque_government_valency"]["state"] == "passed"
    assert gates["contextual_calque_government_valency"]["correction_release_allowed"] is True


def test_calque_gate_counts_declared_non_model_channels_and_lanes() -> None:
    known_answers = _json(KNOWN_ANSWERS)
    thresholds = _json(THRESHOLDS)
    known_answers["categories"]["contextual_calque_government_valency"]["evidence"] = known_answers[
        "categories"
    ]["contextual_calque_government_valency"]["evidence"][:1]
    gates = factory.gate_results(
        known_answers,
        thresholds,
        model_proposal_lanes=1,
        model_dissent_lanes=1,
    )
    calque = gates["contextual_calque_government_valency"]
    assert calque["state"] == "research_only"
    assert calque["correction_release_allowed"] is False
    assert any("non-model evidence channels=1" in reason for reason in calque["reasons"])

    known_answers = _json(KNOWN_ANSWERS)
    gates = factory.gate_results(
        known_answers,
        thresholds,
        model_proposal_lanes=1,
        model_dissent_lanes=0,
    )
    assert any(
        "attributed dissent lanes=0" in reason
        for reason in gates["contextual_calque_government_valency"]["reasons"]
    )


def test_zvuchyt_narration_and_protected_mutations_are_frozen() -> None:
    known_answers = _json(KNOWN_ANSWERS)
    category = known_answers["categories"]["russian_lexical_inflectional_intrusion"]
    assert category["positive"][0] == {
        "text": "Фраза звучит значно вишуканіше.",
        "surface": "звучит",
        "replacement": "звучить",
        "canary_ids": ["zvuchyt-modern-ukrainian-narration"],
    }
    assert len(category["protected"]) == 5
    assert all(item["surface"] == "звучит" for item in category["protected"])


def test_frozen_canaries_and_false_correction_caps_fail_closed() -> None:
    known_answers = _json(KNOWN_ANSWERS)
    thresholds = _json(THRESHOLDS)
    category_id = "russian_lexical_inflectional_intrusion"

    known_answers["categories"][category_id]["positive"][0]["canary_ids"] = []
    gates = factory.gate_results(
        known_answers,
        thresholds,
        model_proposal_lanes=1,
        model_dissent_lanes=1,
    )
    assert gates[category_id]["state"] == "research_only"
    assert any("zvuchyt-modern-ukrainian-narration" in reason for reason in gates[category_id]["reasons"])

    poisoned = _json(KNOWN_ANSWERS)
    poisoned["categories"][category_id]["acceptable_control"][0]["text"] = (
        "Неправильна контрольна фраза звучит поза цитатою."
    )
    gates = factory.gate_results(
        poisoned,
        thresholds,
        model_proposal_lanes=1,
        model_dissent_lanes=1,
    )
    assert gates[category_id]["state"] == "research_only"
    assert gates[category_id]["control_false_corrections"] == 1
    assert any("maximum_control_false_corrections=0" in reason for reason in gates[category_id]["reasons"])

    poisoned = _json(KNOWN_ANSWERS)
    poisoned["categories"][category_id]["protected"][0]["text"] = (
        "Неправильно незахищена фраза звучит поза цитатою."
    )
    gates = factory.gate_results(
        poisoned,
        thresholds,
        model_proposal_lanes=1,
        model_dissent_lanes=1,
    )
    assert gates[category_id]["state"] == "research_only"
    assert gates[category_id]["protected_false_corrections"] == 1
    assert any(
        "maximum_protected_false_corrections=0" in reason
        for reason in gates[category_id]["reasons"]
    )


def test_actual_matcher_protects_zvuchyt_quote_and_lexical_boundary() -> None:
    rules = factory.known_answer_correction_rules(_json(KNOWN_ANSWERS))
    quoted = list(factory.iter_rule_matches("Автор навів: «Фраза звучит природно».", rules))
    assert len(quoted) == 1
    assert quoted[0].rule["surface"] == "звучит"
    assert quoted[0].protected is True
    assert list(factory.iter_rule_matches("Фраза звучить природно.", rules)) == []


def test_known_answer_dispositions_obey_category_policy() -> None:
    thresholds = _json(THRESHOLDS)
    default_allowed = {"correct", "correction", "protected", "excluded", "unresolved"}
    for category_id, rule in thresholds["categories"].items():
        allowed = set(rule.get("allowed_dispositions", default_allowed))
        for role in ("positive", "acceptable_control", "protected"):
            disposition = factory.known_answer_disposition(
                role=role,
                category_id=category_id,
                rule=rule,
                correction_release_allowed=True,
            )
            assert disposition in allowed
    quotation_rule = thresholds["categories"]["marked_russian_quotation_code_switch"]
    assert factory.known_answer_disposition(
        role="acceptable_control",
        category_id="marked_russian_quotation_code_switch",
        rule=quotation_rule,
        correction_release_allowed=False,
    ) == "protected"
