"""Curated-source auto-approve policy + ULP windowing."""

from __future__ import annotations

from scripts.lexicon.atlas_intake_core import (
    classify_resolved_candidate,
)


def _heritage_standard(_lemma: str) -> dict:
    return {
        "classification": "standard",
        "is_russianism": False,
        "russian_shadow": False,
        "sovietization_risk": 0,
    }


def _heritage_unknown(_lemma: str) -> dict:
    return {
        "classification": "unknown",
        "is_russianism": False,
        "russian_shadow": False,
        "sovietization_risk": 0,
    }


def test_curated_ohoiko_auto_approves_without_strict_heritage() -> None:
    classification, reasons, _heritage = classify_resolved_candidate(
        lemma="банк",
        pos="noun",
        gloss="bank",
        metadata_reasons=(),
        atlas_keys=set(),
        ledger_keys=set(),
        heritage_lookup=_heritage_unknown,
        source_family="ohoiko",
    )
    assert classification == "auto_approve"
    assert "curated_source_trust" in reasons


def test_non_curated_still_requires_standard_heritage() -> None:
    classification, reasons, _heritage = classify_resolved_candidate(
        lemma="банк",
        pos="noun",
        gloss="bank",
        metadata_reasons=(),
        atlas_keys=set(),
        ledger_keys=set(),
        heritage_lookup=_heritage_unknown,
        source_family="curriculum",
    )
    assert classification == "review_queue"
    assert "heritage_nonstandard_classification" in reasons


def test_curated_still_rejects_russianism() -> None:
    def heritage(_lemma: str) -> dict:
        return {
            "classification": "russianism",
            "is_russianism": True,
            "russian_shadow": False,
            "sovietization_risk": 0,
        }

    classification, reasons, _heritage = classify_resolved_candidate(
        lemma="область",
        pos="noun",
        gloss="region",
        metadata_reasons=(),
        atlas_keys=set(),
        ledger_keys=set(),
        heritage_lookup=heritage,
        source_family="ulp",
    )
    assert classification == "reject"
    assert "heritage_russianism" in reasons
