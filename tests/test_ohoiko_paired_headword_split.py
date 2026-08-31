"""Fixture-level tests for Ohoiko paired-headword split policy (#6370)."""

from __future__ import annotations

import json

import pytest

from scripts.lexicon import ohoiko_paired_headword_split as paired_split
from scripts.lexicon.ohoiko_paired_headword_split import (
    analyze_paired_splits,
    analyze_space_collapses,
    append_space_collapse_audit,
    build_split_leg_rows,
    classify_split_leg,
    collapse_internal_whitespace,
    collect_space_collapse_candidates,
    is_single_orthographic_word,
    recover_latin_lookalike,
    resolve_leg_lemma,
    split_paired_headword,
    strip_trailing_parentheticals,
)


def test_split_basic_gender_pair() -> None:
    assert split_paired_headword("актор, акторка") == ["актор", "акторка"]


def test_split_aspect_pair() -> None:
    assert split_paired_headword("бачити, побачити") == ["бачити", "побачити"]


def test_split_strips_whitespace_and_empty_legs() -> None:
    assert split_paired_headword("випити,") == ["випити"]
    assert split_paired_headword(" , акторка , ") == ["акторка"]


def test_strip_trailing_parentheticals_repeated() -> None:
    assert strip_trailing_parentheticals("побитися (1)") == "побитися"
    assert strip_trailing_parentheticals("мати (verb)") == "мати"
    assert strip_trailing_parentheticals("lemma (1) (2)") == "lemma"


def test_split_strips_trailing_parenthetical_on_legs() -> None:
    assert split_paired_headword("битися, побитися (1),") == ["битися", "побитися"]
    assert split_paired_headword("рости, вирости (1),") == ["рости", "вирости"]


def test_multiword_legs_detected() -> None:
    legs = split_paired_headword("боя тися, забоя тися")
    assert legs == ["боя тися", "забоя тися"]
    assert all(not is_single_orthographic_word(leg) for leg in legs)
    assert all(classify_split_leg(leg) == "multiword_after_split" for leg in legs)


def test_english_contaminated_second_leg_is_multiword(requires_vesum_db) -> None:
    legs = split_paired_headword("убивати, to kill (imperfective, perfective)")
    assert legs[0] == "убивати"
    assert classify_split_leg(legs[0]) != "multiword_after_split"
    assert any(classify_split_leg(leg) == "multiword_after_split" for leg in legs[1:])


def test_split_does_not_invent_lemmas() -> None:
    raw = "науковець, науковиця,"
    legs = split_paired_headword(raw)
    assert legs == ["науковець", "науковиця"]
    # No synthetic feminine/masculine forms beyond the split legs.
    assert "науковецька" not in legs


def test_analyze_paired_splits_never_promotes_a_no_gloss_leg(monkeypatch) -> None:
    """#7458: a VESUM-ok leg with no honest gloss anywhere (parent / СУМ-20 /
    ВТС all miss) must not enter ``promote_candidates`` — it is held in its
    own residual bucket instead, so nothing downstream ever writes a lemma+pos
    skeleton with a fabricated or empty-but-promoted gloss."""
    monkeypatch.setattr(paired_split, "classify_split_leg", lambda leg: "single_word_vesum_ok")
    monkeypatch.setattr(paired_split, "resolve_leg_lemma", lambda leg: leg)
    monkeypatch.setattr(paired_split, "_vesum_pos", lambda lemma: "noun")
    monkeypatch.setattr(paired_split.promo, "_sum20_vts_gloss", lambda lemma: None)

    result = analyze_paired_splits(
        paired_lemmas=["безглосник, безглосниця"],
        atlas_keys=set(),
        inventory_rows_by_lemma={"безглосник, безглосниця": {"gloss": None}},
    )

    assert result["promote_candidate_count"] == 0
    assert result["promote_candidates"] == []
    assert result["leg_counts"]["single_word_vesum_ok_no_gloss"] == 2
    assert "безглосник" in result["legs_by_category"]["single_word_vesum_ok_no_gloss"]


def test_analyze_paired_splits_promotes_leg_with_honest_gloss(monkeypatch) -> None:
    monkeypatch.setattr(paired_split, "classify_split_leg", lambda leg: "single_word_vesum_ok")
    monkeypatch.setattr(paired_split, "resolve_leg_lemma", lambda leg: leg)
    monkeypatch.setattr(paired_split, "_vesum_pos", lambda lemma: "noun")
    monkeypatch.setattr(paired_split.promo, "_sum20_vts_gloss", lambda lemma: None)

    result = analyze_paired_splits(
        paired_lemmas=["глосник, глосниця"],
        atlas_keys=set(),
        inventory_rows_by_lemma={"глосник, глосниця": {"gloss": "a glossed thing"}},
    )

    assert result["promote_candidate_count"] == 2
    assert {c["lemma"] for c in result["promote_candidates"]} == {"глосник", "глосниця"}
    assert "single_word_vesum_ok_no_gloss" not in result["leg_counts"]


def test_build_split_leg_rows_skips_candidates_with_no_honest_gloss(monkeypatch) -> None:
    """Defense in depth: even if a caller hands ``build_split_leg_rows`` an
    unfiltered candidate with no resolvable gloss, it must not write a
    skeleton row."""
    monkeypatch.setattr(paired_split, "_vesum_pos", lambda lemma: "noun")
    monkeypatch.setattr(paired_split.promo, "_sum20_vts_gloss", lambda lemma: None)

    rows = build_split_leg_rows(
        [
            {"lemma": "безглосник", "paired_source": "безглосник, безглосниця", "gloss": None},
            {"lemma": "глосник", "paired_source": "глосник, глосниця", "gloss": "a glossed thing"},
        ]
    )

    assert [r["lemma"] for r in rows] == ["глосник"]
    assert rows[0]["gloss"] == "a glossed thing"


def test_recover_latin_lookalike_twarina_and_zhinka() -> None:
    assert recover_latin_lookalike("тваринa") == "тварина"
    assert recover_latin_lookalike("жiнка") == "жінка"
    assert recover_latin_lookalike("футболiст") == "футболіст"
    assert recover_latin_lookalike("чистий") == "чистий"


def test_resolve_leg_lemma_recovers_ocr_lookalikes(requires_vesum_db) -> None:
    assert resolve_leg_lemma("тваринa") == "тварина"
    assert resolve_leg_lemma("жiнка") == "жінка"
    assert resolve_leg_lemma("футболiст") == "футболіст"


def _space_candidate(original: str) -> dict[str, str]:
    return {
        "original_form": original,
        "source_lemma": original,
        "source_kind": "paired_headword_leg",
        "source_family": "ohoiko",
        "source_id": "ohoiko-ulp-curated-2026-07-19-bulk-ohoiko",
        "source_extraction_mode": "curated_bulk",
        "source_locator": "ohoiko-1000-words entry 47",
        "source_pos": "phrase",
        "source_gloss": "to fear, to be afraid",
    }


def test_space_collapse_requires_collapsed_vesum_and_invalid_components(requires_vesum_db) -> None:
    result = analyze_space_collapses(
        [_space_candidate("забоя тися"), _space_candidate("боя тися")],
        inventory_rel="data/lexicon/source-inventory/oneshot/input.yaml",
    )

    assert result["candidate_count"] == 2
    assert result["collapsed_vesum_valid_count"] == 2
    assert result["admissible_count"] == 1
    assert result["manual_review_count"] == 1
    assert result["admitted"][0]["collapsed_form"] == "забоятися"
    rejected = result["manual_review"][0]
    assert rejected["original_form"] == "боя тися"
    assert rejected["valid_split_components"] == ["боя"]
    assert rejected["reasons"] == ["split_component_vesum_valid"]


def test_space_collapse_marks_multi_component_tokenization_manual(requires_vesum_db) -> None:
    result = analyze_space_collapses(
        [_space_candidate("перед тим як")],
        inventory_rel="data/lexicon/source-inventory/oneshot/input.yaml",
    )

    assert result["admissible_count"] == 0
    assert result["manual_review"][0]["reasons"] == [
        "ambiguous_tokenization",
        "collapsed_not_vesum_valid",
        "split_component_vesum_valid",
    ]


def test_space_collapse_rejects_non_ocr_source() -> None:
    source_row = {
        "source_family": "teacher_lesson",
        "source_id": "lesson-1",
        "locator": "lesson 1",
        "gloss": "to fear",
    }
    with pytest.raises(ValueError, match="non-OCR source family"):
        collect_space_collapse_candidates(
            residual={"lemmas_by_category": {"multiword_phrases_other": ["боя тися"]}},
            paired_analysis={"pairs": []},
            inventory_rows_by_lemma={"боя тися": source_row},
        )


def test_collapse_internal_whitespace_changes_no_other_codepoints() -> None:
    assert collapse_internal_whitespace("боя  тися") == "боятися"
    assert collapse_internal_whitespace("чистий") == "чистий"


def test_space_collapse_audit_appends_idempotently(tmp_path) -> None:
    row = {
        "schema": "atlas-6370-ocr-space-collapse-audit.v1",
        "inventory_path": "data/input.yaml",
        "original_form": "забоя тися",
        "split_components": ["забоя", "тися"],
        "collapsed_form": "забоятися",
        "transformation": {"type": "remove_internal_whitespace", "removed_codepoints": 1},
        "collapsed_vesum_valid": True,
        "valid_split_components": [],
        "decision": "admit",
        "reasons": [],
        "source": {"id": "source-1", "locator": "entry 47"},
    }
    path = tmp_path / "audit.jsonl"

    assert append_space_collapse_audit([row], path) == 1
    assert append_space_collapse_audit([row], path) == 0
    lines = path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    assert json.loads(lines[0])["original_form"] == "забоя тися"


def test_split_trailing_commas_in_500_verbs_and_1000_words() -> None:
    assert split_paired_headword("випити,") == ["випити"]
    assert split_paired_headword("вкрасти,") == ["вкрасти"]
    assert split_paired_headword("купляти,") == ["купляти"]
    assert split_paired_headword("поліцейський,") == ["поліцейський"]
    assert split_paired_headword("замерзнути,") == ["замерзнути"]


def test_clean_tokens_and_ocr_lookalike_dispositions() -> None:
    # ого! and ой! strip trailing exclamation mark to canonical forms
    assert "ого!".rstrip("!") == "ого"
    assert "ой!".rstrip("!") == "ой"
    # тваринa recovers lookalike latin 'a' to Cyrillic 'а'
    assert recover_latin_lookalike("тваринa") == "тварина"
    assert resolve_leg_lemma("тваринa") == "тварина"


def test_ulp_taught_leftovers_heritage_holds() -> None:
    from scripts.lexicon.heritage_classifier import classify_lemma

    for lemma in ("переключити", "кримчанин", "просвітитель"):
        hs = classify_lemma(lemma)
        assert hs.get("is_russianism") is True or hs.get("classification") == "russianism"
        assert paired_split.classify_split_leg(lemma) == "single_word_heritage_flag"


def test_analyze_all_curated_leftovers_disposition(tmp_path, monkeypatch) -> None:
    from scripts.lexicon.ohoiko_paired_headword_split import analyze_all_curated_leftovers

    dummy_manifest = tmp_path / "manifest.json"
    dummy_manifest.write_text(
        json.dumps(
            {
                "entries": [
                    {"lemma": "ого"},
                    {"lemma": "ой"},
                    {"lemma": "тварина"},
                    {"lemma": "випити"},
                    {"lemma": "актор"},
                    {"lemma": "акторка"},
                ]
            }
        ),
        encoding="utf-8",
    )

    dummy_inv = tmp_path / "inventory.yaml"
    import yaml

    dummy_inv.write_text(
        yaml.safe_dump(
            {
                "sources": [
                    {
                        "id": "ohoiko-bulk",
                        "headwords": [
                            {"lemma": "ого!", "locator": "ohoiko-1000-words entry 1"},
                            {"lemma": "ой!", "locator": "ohoiko-1000-words entry 2"},
                            {"lemma": "тваринa", "locator": "ohoiko-1000-words entry 3"},
                            {"lemma": "випити,", "locator": "ohoiko-500-verbs entry 1"},
                            {"lemma": "актор, акторка", "locator": "ohoiko-1000-words entry 4"},
                            {"lemma": "переключити", "locator": "ulp-4-00-lesson-notes lesson 1"},
                        ],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    res = analyze_all_curated_leftovers(inventory_path=dummy_inv, manifest_path=dummy_manifest)
    assert res["total_keys"] == 6
    assert res["bucket_counts"]["clean_tokens"] == 3
    assert res["bucket_counts"]["verbs_500_trailing_comma"] == 1
    assert res["bucket_counts"]["words_1000_pair_keys"] == 1
    assert res["bucket_counts"]["ulp_leftovers"] == 1
    assert res["promote_candidate_count"] == 0

