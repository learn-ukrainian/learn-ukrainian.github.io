"""Regression tests for named antonym/homonym residual reporting (#6338)."""

from __future__ import annotations

from scripts.audit import relation_residual_audit as residual


def test_leg_statuses_keep_atlas_and_selection_failures_distinct() -> None:
    entries = [
        {
            "url_slug": "selected",
            "lemma": "selected",
            "gloss": "selected",
            "enrichment": {"cefr": {"level": "A2"}},
        },
        {"url_slug": "not-lexeme", "lemma": "not-lexeme", "pos": "grammar term"},
        {
            "url_slug": "not-selected",
            "lemma": "not-selected",
            "gloss": "not selected",
            "enrichment": {"cefr": {"level": "A2"}},
        },
    ]
    entry_by_key, entry_by_plain = residual._entry_lookup(entries)
    selected = {"selected": {"lemma": "selected", "cefr": "A2"}}

    missing, _ = residual._leg_status(
        "missing", entry_by_key, entry_by_plain, selected, selected
    )
    not_lexeme, _ = residual._leg_status(
        "not-lexeme", entry_by_key, entry_by_plain, selected, selected
    )
    not_selected, _ = residual._leg_status(
        "not-selected", entry_by_key, entry_by_plain, selected, selected
    )
    selected_leg, selected_lexeme = residual._leg_status(
        "selected", entry_by_key, entry_by_plain, selected, selected
    )

    assert missing == {"slug": "missing", "status": "missing_from_atlas"}
    assert not_lexeme == {"slug": "not-lexeme", "status": "not_lexeme_entry"}
    assert not_selected == {"slug": "not-selected", "status": "eligible_not_selected"}
    assert selected_leg == {
        "slug": "selected",
        "status": "selected",
        "cefr": "A2",
        "cefr_status": "anchored",
    }
    assert selected_lexeme == selected["selected"]


def test_summarize_reports_named_frame_and_cefr_residuals() -> None:
    summary = residual.summarize(
        [
            {"outcome": "missing_leg", "legA": {"status": "missing_from_atlas"}},
            {
                "outcome": "frame_answer_unresolved",
                "legA": {"status": "selected", "cefr_status": "uses_b1_fallback"},
                "legB": {"status": "ineligible", "reason": "missing_curriculum_anchor"},
            },
            {"outcome": "no_valid_frames"},
        ]
    )

    assert summary == {
        "pairs_total": 3,
        "outcome_counts": {
            "frame_answer_unresolved": 1,
            "missing_leg": 1,
            "no_valid_frames": 1,
        },
        "leg_status_counts": {
            "ineligible": 1,
            "missing_from_atlas": 1,
            "selected": 1,
        },
        "ineligible_by_reason": {"missing_curriculum_anchor": 1},
        "selected_cefr_status_counts": {"uses_b1_fallback": 1},
    }
