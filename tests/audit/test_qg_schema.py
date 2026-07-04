from __future__ import annotations

import pytest

from scripts.audit import qg_schema
from scripts.audit.curriculum_qg_harness import EVIDENCE_SCHEMA_VERSION as CURRICULUM_QG_SCHEMA_VERSION
from scripts.audit.llm_qg_store import EVIDENCE_SCHEMA_VERSION as LLM_QG_SCHEMA_VERSION


def test_deterministic_b1_finding_uses_canonical_shape() -> None:
    finding = qg_schema.build_deterministic_curriculum_finding(
        issue_id="AWKWARD_PASSIVE_RESULT_STATE",
        rule_id="b1_awkward_passive_result_state",
        dimension="ukrainian_style",
        severity="critical",
        file="module.md",
        line=3,
        span={"start": 42, "end": 73},
        excerpt="застосунок має бути відкритий",
        message="Use active/impersonal Ukrainian instead of a literal passive state.",
    )

    qg_schema.validate_finding(finding)
    assert finding["issue_class"] == "calque"
    assert finding["contact_source_lang"] == "unknown"
    assert finding["source_lang"] == "unknown"
    assert finding["track_l1"] == "en"
    assert finding["detector"] == {
        "adapter": "curriculum_qg_harness",
        "rule_id": "b1_awkward_passive_result_state",
        "pattern_id": "b1_awkward_passive_result_state",
    }
    assert finding["finding_id"] == qg_schema.make_finding_id(finding)


def test_ua_gec_f_calque_defaults_to_info_russian_contact_with_attribution() -> None:
    finding = qg_schema.build_ua_gec_finding(
        error="являється",
        correction="є",
        tag="F/Calque",
        file="module.md",
        line=18,
        span={"start": 210, "end": 218},
        doc_id="0301",
        pair_id="ua-gec-0301-1",
        frequency=47,
    )

    assert finding["issue_id"] == "CONTACT_CALQUE_UA_GEC"
    assert finding["issue_class"] == "calque"
    assert finding["dimension"] == "contact_calque"
    assert finding["severity"] == "info"
    assert finding["confidence"] == "lookup_heuristic"
    assert finding["contact_source_lang"] == "ru"
    assert finding["ua_gec_tag"] == "F/Calque"
    assert finding["suggested_replacement"] == ["є"]
    assert finding["attribution"] == {
        "corpus": "UA-GEC v2",
        "license": "CC-BY-4.0",
        "doc_id": "0301",
        "pair_id": "ua-gec-0301-1",
        "evidence": "Syvokon et al., UNLP 2023",
    }


def test_ua_gec_g_case_can_preserve_non_russian_source_lang() -> None:
    finding = qg_schema.build_ua_gec_finding(
        error="по дорозі",
        correction="дорогою",
        tag="G/Case",
        source_lang="pl",
        file="module.md",
        line=None,
        span=None,
    )

    assert finding["issue_id"] == "UKRAINIAN_GRAMMAR_CASE"
    assert finding["issue_class"] == "grammar"
    assert finding["dimension"] == "contact_grammar"
    assert finding["contact_source_lang"] == "pl"
    assert finding["source_lang"] == "pl"


@pytest.mark.parametrize("source_lang", ["ru", "pl", "en", "unknown", "other", "russian", "english"])
def test_source_language_normalization_accepts_schema_values(source_lang: str) -> None:
    normalized = qg_schema.normalize_source_lang(source_lang)

    assert normalized in qg_schema.SOURCE_LANGS


def test_invalid_source_language_dimension_and_tag_are_rejected() -> None:
    with pytest.raises(ValueError, match="unsupported contact source language"):
        qg_schema.normalize_source_lang("de")

    finding = qg_schema.build_ua_gec_finding(
        error="являється",
        correction="є",
        tag="F/Calque",
        file="module.md",
        line=1,
        span={"start": 0, "end": 8},
    )
    finding["dimension"] = "calque"
    with pytest.raises(ValueError, match="unsupported dimension"):
        qg_schema.validate_finding(finding)

    with pytest.raises(ValueError, match="unsupported UA-GEC tag"):
        qg_schema.map_ua_gec_tag("P/Punctuation")


def test_semantic_false_friend_finding_carries_sense_context() -> None:
    finding = qg_schema.build_semantic_false_friend_finding(
        word="лук",
        russian_meaning="onion",
        ukrainian_meaning="bow (weapon)",
        replacement="цибуля",
        matched_gloss_pattern="**лук** (onion)",
        file="vocabulary.yaml",
        line=12,
        span={"start": 88, "end": 102},
        excerpt="**лук** (onion)",
    )

    assert finding["issue_id"] == "SEMANTIC_FALSE_FRIEND"
    assert finding["issue_class"] == "false_friend"
    assert finding["dimension"] == "contact_calque"
    assert finding["contact_source_lang"] == "ru"
    assert finding["suggested_replacement"] == ["цибуля"]
    assert finding["sense_context"] == {
        "word": "лук",
        "calque_sense": "onion",
        "authentic_sense": "bow (weapon)",
        "matched_gloss_pattern": "**лук** (onion)",
    }


def test_evidence_record_validates_nested_findings_and_keeps_legacy_versions() -> None:
    finding = qg_schema.build_ua_gec_finding(
        error="на протязі",
        correction="протягом",
        tag="F/Calque",
        file="module.md",
        line=5,
        span={"start": 15, "end": 25},
        doc_id="0490",
    )
    record = qg_schema.build_evidence_record(
        profile="ua_gec_eval",
        evidence_kind="fixture",
        fixture_id="ua-gec-0490",
        level_policy={"family": "b1_plus", "english_policy": "Ukrainian-led prose"},
        dimensions={
            "contact_calque": qg_schema.build_dimension(
                score=9.0,
                verdict="WARN",
                findings=[finding],
            )
        },
        checker_runs=[
            {
                "adapter": "ua_gec_lookup",
                "version": "ua_gec_lookup.v1",
                "config_hash": "abc123",
                "provider": None,
                "model": None,
                "source_lang_filter": "ru",
            }
        ],
        verdict="WARN",
        terminal_verdict="PASS",
    )

    qg_schema.validate_record(record)
    assert record["schema_version"] == "ua_contact_quality_evidence.v1"
    assert record["compatibility"] == {
        "legacy_projection_versions": ["curriculum_ua_qg_evidence.v1", "llm_qg_evidence.v1"],
        "migration_required": False,
    }
    assert CURRICULUM_QG_SCHEMA_VERSION == "curriculum_ua_qg_evidence.v1"
    assert LLM_QG_SCHEMA_VERSION == "llm_qg_evidence.v1"
