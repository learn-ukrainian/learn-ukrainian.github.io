from __future__ import annotations

import pytest

from scripts.audit import curriculum_qg_harness, llm_qg_store
from scripts.audit.qg_schema import (
    CONTACT_SOURCE_LANGS,
    FINDING_SCHEMA_VERSION,
    LEGACY_EVIDENCE_SCHEMA_VERSIONS,
    QGSchemaError,
    Span,
    build_deterministic_phrase_finding,
    build_semantic_false_friend_finding,
    build_ua_gec_finding,
    finding_id,
    normalize_contact_source_lang,
    ua_gec_mapping_for_tag,
    validate_finding,
)


def test_b1_27_deterministic_phrase_finding_shape() -> None:
    finding = build_deterministic_phrase_finding(
        module_id="b1/aspect-in-imperatives",
        rule_id="b1_awkward_passive_result_state",
        file="module.md",
        line=12,
        excerpt="застосунок має бути відкритий",
        span=Span(start=40, end=71),
    )

    assert finding["schema_version"] == FINDING_SCHEMA_VERSION
    assert finding["finding_id"].startswith("qg-")
    assert finding["issue_id"] == "AWKWARD_PASSIVE_RESULT_STATE"
    assert finding["rule_id"] == "b1_awkward_passive_result_state"
    assert finding["dimension"] == "ukrainian_style"
    assert finding["severity"] == "critical"
    assert finding["checker"] == "deterministic"
    assert finding["contact_source_lang"] == "ru"
    assert finding["quoted_bad_form"] == "застосунок має бути відкритий"
    assert finding["span"] == {"start": 40, "end": 71}
    assert finding["disposition"]["defect"] is True
    assert finding["disposition"]["quoted_bad_form"] is True


def test_ua_gec_f_calque_mapping_and_default_info_severity() -> None:
    finding = build_ua_gec_finding(
        module_id="b1/aspect-in-imperatives",
        ua_gec_tag="F/Calque",
        file="module.md",
        line=5,
        excerpt="таким чином",
        message="UA-GEC F/Calque suggestion for discourse marker calque.",
        error_form="таким чином",
        suggested_form="отже",
        doc_id="doc-123",
        pair_id="pair-456",
    )

    assert finding["dimension"] == "calque"
    assert finding["issue_id"] == "UA_GEC_CALQUE"
    assert finding["ua_gec_tag"] == "F/Calque"
    assert finding["severity"] == "info"
    assert finding["contact_source_lang"] == "ru"
    assert finding["attribution"] == {
        "corpus": "UA-GEC",
        "license": "CC-BY-4.0",
        "attribution": "Syvokon et al., UNLP 2023",
        "doc_id": "doc-123",
        "pair_id": "pair-456",
    }


def test_ua_gec_g_case_mapping() -> None:
    mapping = ua_gec_mapping_for_tag("G/Case")
    finding = build_ua_gec_finding(
        module_id="b1/test-module",
        ua_gec_tag="G/Case",
        file="module.md",
        line=8,
        excerpt="на столі",
        message="UA-GEC G/Case grammar correction.",
        error_form="на столі",
        suggested_form="на стіл",
    )

    assert mapping["dimension"] == "grammar"
    assert mapping["issue_id"] == "UA_GEC_GRAMMAR_CASE"
    assert finding["dimension"] == "grammar"
    assert finding["issue_id"] == "UA_GEC_GRAMMAR_CASE"
    assert finding["ua_gec_tag"] == "G/Case"
    assert finding["contact_source_lang"] == "unknown"


@pytest.mark.parametrize("lang", ["ru", "pl", "en", "unknown"])
def test_contact_source_lang_validation_accepts_supported_codes(lang: str) -> None:
    assert normalize_contact_source_lang(lang) == lang


def test_contact_source_lang_validation_rejects_invalid_code() -> None:
    with pytest.raises(QGSchemaError, match="unsupported contact_source_lang"):
        normalize_contact_source_lang("de")


def test_validate_finding_rejects_invalid_dimension() -> None:
    with pytest.raises(QGSchemaError, match="unsupported dimension"):
        validate_finding(
            {
                "schema_version": FINDING_SCHEMA_VERSION,
                "issue_id": "BAD",
                "rule_id": "bad_rule",
                "dimension": "not_a_dimension",
                "severity": "warning",
                "checker": "deterministic",
                "contact_source_lang": "ru",
                "file": "module.md",
                "excerpt": "test",
            }
        )


def test_validate_finding_rejects_invalid_ua_gec_tag() -> None:
    with pytest.raises(QGSchemaError, match="unsupported ua_gec_tag"):
        validate_finding(
            {
                "schema_version": FINDING_SCHEMA_VERSION,
                "issue_id": "UA_GEC_CALQUE",
                "rule_id": "ua_gec_f_style",
                "dimension": "calque",
                "severity": "info",
                "checker": "ua_gec",
                "contact_source_lang": "ru",
                "ua_gec_tag": "F/Style",
                "file": "module.md",
                "excerpt": "test",
            }
        )


def test_semantic_false_friend_fields_and_sense_context() -> None:
    finding = build_semantic_false_friend_finding(
        module_id="a1/onion-bow",
        file="module.md",
        line=3,
        excerpt="**лук** (onion)",
        word="лук",
        contact_meaning="onion",
        ukrainian_meaning="bow (weapon)",
        replacement="цибуля",
        replacement_translation="onion",
        sense_context="vocabulary gloss pairs лук with the Russian onion sense",
        span=Span(start=0, end=14),
    )

    assert finding["issue_id"] == "SEMANTIC_FALSE_FRIEND"
    assert finding["checker"] == "semantic_false_friend"
    assert finding["sense_context"] == "vocabulary gloss pairs лук with the Russian onion sense"
    assert finding["false_friend"] == {
        "word": "лук",
        "contact_meaning": "onion",
        "ukrainian_meaning": "bow (weapon)",
        "replacement": "цибуля",
        "replacement_translation": "onion",
        "sense_context": "vocabulary gloss pairs лук with the Russian onion sense",
    }
    assert finding["suggested_form"] == "цибуля"


def test_finding_id_is_stable_for_same_inputs() -> None:
    first = finding_id(
        module_id="b1/aspect-in-imperatives",
        rule_id="b1_kitchen_locative_context",
        file="module.md",
        excerpt="У кухні",
        line=20,
    )
    second = finding_id(
        module_id="b1/aspect-in-imperatives",
        rule_id="b1_kitchen_locative_context",
        file="module.md",
        excerpt="У кухні",
        line=20,
    )

    assert first == second
    assert first.startswith("qg-")


def test_legacy_evidence_schema_constants_are_not_overwritten() -> None:
    assert "llm_qg_evidence.v1" in LEGACY_EVIDENCE_SCHEMA_VERSIONS
    assert "curriculum_ua_qg_evidence.v1" in LEGACY_EVIDENCE_SCHEMA_VERSIONS
    assert llm_qg_store.EVIDENCE_SCHEMA_VERSION == "llm_qg_evidence.v1"
    assert curriculum_qg_harness.EVIDENCE_SCHEMA_VERSION == "curriculum_ua_qg_evidence.v1"
    assert FINDING_SCHEMA_VERSION not in LEGACY_EVIDENCE_SCHEMA_VERSIONS


def test_ua_gec_severity_can_be_escalated_by_caller() -> None:
    finding = build_ua_gec_finding(
        module_id="b1/test-module",
        ua_gec_tag="F/Calque",
        file="module.md",
        line=1,
        excerpt="так як",
        message="Escalated calque hit.",
        error_form="так як",
        suggested_form="оскільки",
        severity="warning",
    )

    assert finding["severity"] == "warning"


def test_contact_source_langs_include_future_polish_and_english() -> None:
    assert {"ru", "pl", "en", "unknown"} <= CONTACT_SOURCE_LANGS
