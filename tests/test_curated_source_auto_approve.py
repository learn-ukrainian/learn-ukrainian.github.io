"""Curated-source auto-approve policy + ULP windowing."""

from __future__ import annotations

from scripts.ingest.ulp_to_jsonl import window_text
from scripts.lexicon.atlas_intake_core import (
    CURATED_SOURCE_FAMILIES,
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


def test_curated_families_include_ohoiko_ulp_textbook_teacher() -> None:
    assert {"ohoiko", "ulp", "textbook", "teacher_lesson"} <= CURATED_SOURCE_FAMILIES


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


def test_window_text_splits_long_lesson() -> None:
    lines = [f"рядок номер {i} " + ("слово " * 20) for i in range(80)]
    text = "\n".join(lines)
    windows = window_text(text, target=800, overlap=80)
    assert len(windows) >= 3
    assert all(len(w) <= 1200 for w in windows)
    # overlap means consecutive windows share content
    assert any(tok in windows[1] for tok in windows[0].split()[-5:])
