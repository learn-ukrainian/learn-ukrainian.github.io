"""Fixture-level tests for Ohoiko paired-headword split policy (#6370)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

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


def test_clean_tokens_and_ocr_lookalike_dispositions(requires_vesum_db) -> None:
    # ого! and ой! strip trailing exclamation mark to canonical forms
    assert "ого!".rstrip("!") == "ого"
    assert "ой!".rstrip("!") == "ой"
    # тваринa recovers lookalike latin 'a' to Cyrillic 'а'
    assert recover_latin_lookalike("тваринa") == "тварина"
    assert resolve_leg_lemma("тваринa") == "тварина"


def test_ulp_taught_leftovers_heritage_holds(requires_vesum_db, requires_sources_db) -> None:
    from scripts.lexicon.heritage_classifier import classify_lemma

    for lemma in ("переключити", "кримчанин", "просвітитель"):
        hs = classify_lemma(lemma)
        assert hs.get("is_russianism") is True or hs.get("classification") == "russianism"
        assert paired_split.classify_split_leg(lemma) == "single_word_heritage_flag"


def test_analyze_all_curated_leftovers_disposition(
    tmp_path, monkeypatch, requires_vesum_db, requires_sources_db
) -> None:
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


def test_live_curated_unit_a_leftovers_census_invariants(requires_vesum_db) -> None:
    manifest_path = paired_split.DEFAULT_MANIFEST
    inventory_path = paired_split.DEFAULT_INVENTORY
    atlas_db_path = paired_split.DEFAULT_ATLAS_DB
    if not manifest_path.exists() or not inventory_path.exists():
        pytest.skip("requires live manifest and inventory")

    res = paired_split.analyze_all_curated_leftovers(
        inventory_path=inventory_path,
        manifest_path=manifest_path,
        atlas_db_path=atlas_db_path,
    )
    assert res["total_keys"] == 250
    assert res["bucket_counts"]["words_1000_pair_keys"] == 213
    assert res["bucket_counts"]["verbs_500_trailing_comma"] == 31
    assert res["bucket_counts"]["clean_tokens"] == 3
    assert res["bucket_counts"]["ulp_leftovers"] == 3
    assert res["promote_candidate_count"] == 0
    assert res["leg_disposition_counts"]["already_in_atlas"] == 406
    assert res["leg_disposition_counts"]["multiword_after_split"] == 15
    assert res["leg_disposition_counts"]["single_word_vesum_absent"] == 1
    assert res["leg_disposition_counts"]["hold(trailing_comma_canonical_in_atlas)"] == 31
    assert res["leg_disposition_counts"]["hold(heritage_russianism)"] == 3
    if atlas_db_path and atlas_db_path.exists():
        assert res["atlas_db_articles"] == 19785


def test_classify_taught_candidate(requires_vesum_db) -> None:
    atlas_keys = {"актор", "акторка", "випити", "ого", "ой", "тварина", "поліцейська"}
    categories = paired_split.TAUGHT_CLASSIFIER_CATEGORIES

    # already_in_atlas (trailing comma and clean interjections)
    r_comma = paired_split.classify_taught_candidate("випити,", atlas_keys=atlas_keys)
    assert r_comma["category"] == "already_in_atlas"
    assert r_comma["canonical_lemma"] == "випити"
    assert r_comma["category"] in categories

    r_interj = paired_split.classify_taught_candidate("ого!", atlas_keys=atlas_keys)
    assert r_interj["category"] == "already_in_atlas"
    assert r_interj["canonical_lemma"] == "ого"
    assert r_interj["category"] in categories

    # ocr (latin lookalike)
    r_ocr = paired_split.classify_taught_candidate("тваринa", atlas_keys=atlas_keys)
    assert r_ocr["category"] == "ocr"
    assert r_ocr["canonical_lemma"] == "тварина"
    assert r_ocr["category"] in categories

    # pair_key
    r_pair = paired_split.classify_taught_candidate("актор, акторка", atlas_keys=atlas_keys)
    assert r_pair["category"] == "pair_key"
    assert r_pair["in_atlas"] is True
    assert len(r_pair["legs"]) == 2
    assert r_pair["category"] in categories

    # heritage_hold
    for held_word in ("переключити", "кримчанин", "просвітитель"):
        r_hold = paired_split.classify_taught_candidate(held_word, atlas_keys=set())
        assert r_hold["category"] == "heritage_hold"
        assert "russianism" in r_hold["disposition"]
        assert r_hold["category"] in categories

    # vesum_unrecognized
    r_unrec = paired_split.classify_taught_candidate("поліцейський", atlas_keys=set())
    assert r_unrec["category"] == "vesum_unrecognized"
    assert r_unrec["category"] in categories


def test_live_taught_residual_census_invariants(requires_vesum_db) -> None:
    manifest_path = paired_split.DEFAULT_MANIFEST
    inventory_path = paired_split.DEFAULT_INVENTORY
    atlas_db_path = paired_split.DEFAULT_ATLAS_DB
    if not manifest_path.exists() or not inventory_path.exists():
        pytest.skip("requires live manifest and inventory")

    census = paired_split.analyze_taught_residual_census(
        inventory_path=inventory_path,
        manifest_path=manifest_path,
        atlas_db_path=atlas_db_path,
    )
    assert census["schema"] == "atlas-7550-taught-residual-census.v1"
    summary = census["summary"]
    source_units = census["taught_source_units"]

    # Live computation invariants from extractors (#7572 and Ohoiko lists)
    assert summary["total_taught_records"] == sum(u["records"] for u in source_units.values())
    assert summary["total_taught_records"] == 5938
    assert summary["total_taught_unique_keys"] == 5934
    assert summary["taught_present_in_atlas"] == 5684
    assert summary["residual_missing_candidates"] == 250
    assert summary["p1_admit_count"] == 0
    assert summary["p1_admit_candidates"] == []

    # Source unit breakdowns computed live
    assert source_units["ohoiko-1000-words"]["records"] == 1073
    assert source_units["ohoiko-1000-words"]["unique"] == 1072
    assert source_units["ohoiko-1000-words"]["in_atlas"] == 856
    assert source_units["ohoiko-1000-words"]["missing"] == 216
    assert source_units["ohoiko-1000-words"]["category_breakdown"] == {
        "pair_key": 213,
        "already_in_atlas": 2,
        "ocr": 1,
    }

    assert source_units["ohoiko-500-verbs"]["records"] == 959
    assert source_units["ohoiko-500-verbs"]["unique"] == 959
    assert source_units["ohoiko-500-verbs"]["in_atlas"] == 928
    assert source_units["ohoiko-500-verbs"]["missing"] == 31
    assert source_units["ohoiko-500-verbs"]["category_breakdown"] == {
        "already_in_atlas": 31,
    }

    assert source_units["ulp-seasons-1-6"]["records"] == 3906
    assert source_units["ulp-seasons-1-6"]["unique"] == 3906
    assert source_units["ulp-seasons-1-6"]["in_atlas"] == 3903
    assert source_units["ulp-seasons-1-6"]["missing"] == 3
    assert source_units["ulp-seasons-1-6"]["category_breakdown"] == {
        "heritage_hold": 3,
    }

    # 6 standard categories for the 250 candidates
    cand_cats = summary["candidate_category_counts"]
    assert cand_cats["already_in_atlas"] == 33
    assert cand_cats["pair_key"] == 213
    assert cand_cats["ocr"] == 1
    assert cand_cats["heritage_hold"] == 3
    assert cand_cats["vesum_unrecognized"] == 0
    assert cand_cats["p1_admit"] == 0
    assert sum(cand_cats.values()) == 250

    # Leg-level counts for the 213 pair keys (423 total legs)
    leg_cats = summary["pair_key_leg_counts"]
    assert leg_cats["already_in_atlas"] == 406
    assert leg_cats["ocr"] == 16
    assert leg_cats["vesum_unrecognized"] == 1
    assert leg_cats["heritage_hold"] == 0
    assert leg_cats["p1_admit"] == 0
    assert sum(leg_cats.values()) == 423

    # Documented heritage holds
    held_lemmas = {h["lemma"] for h in summary["heritage_holds"]}
    assert held_lemmas == {"переключити", "кримчанин", "просвітитель"}

    # Manifest and DB invariants
    assert census["manifest_entries"] == 20121
    if atlas_db_path and atlas_db_path.exists():
        assert census["atlas_db_articles"] == 19785


def test_measure_curated_ohoiko_lists_with_dummy_files(tmp_path: Path) -> None:
    dummy_manifest = tmp_path / "manifest.json"
    dummy_manifest.write_text(
        json.dumps({
            "entries": [
                {"lemma": "актор"},
                {"lemma": "акторка"},
                {"lemma": "випити"},
            ]
        }),
        encoding="utf-8",
    )

    dummy_inv = tmp_path / "inventory.yaml"
    dummy_inv.write_text(
        yaml.safe_dump({
            "sources": [
                {
                    "id": "ohoiko-ulp-curated-2026-07-19-bulk-ohoiko",
                    "source_family": "ohoiko",
                    "headwords": [
                        {"lemma": "актор", "locator": "ohoiko-1000-words entry 1"},
                        {"lemma": "акторка", "locator": "ohoiko-1000-words entry 2"},
                        {"lemma": "випити,", "locator": "ohoiko-500-verbs entry 1"},
                    ],
                }
            ]
        }),
        encoding="utf-8",
    )

    measured = paired_split.measure_curated_ohoiko_lists(
        inventory_path=dummy_inv,
        manifest_path=dummy_manifest,
    )
    assert "ohoiko-1000-words" in measured
    assert "ohoiko-500-verbs" in measured
    assert measured["ohoiko-1000-words"]["records"] == 2
    assert measured["ohoiko-1000-words"]["unique"] == 2
    assert measured["ohoiko-1000-words"]["in_atlas"] == 2
    assert measured["ohoiko-1000-words"]["missing"] == 0
    assert measured["ohoiko-500-verbs"]["records"] == 1
    assert measured["ohoiko-500-verbs"]["unique"] == 1
    assert measured["ohoiko-500-verbs"]["missing"] == 1


def test_taught_residual_census_fails_if_source_files_change(tmp_path: Path) -> None:
    """Census totals must be computed live from source files, not hardcoded literals."""
    dummy_manifest = tmp_path / "manifest.json"
    dummy_manifest.write_text(
        json.dumps({
            "entries": [
                {"lemma": "актор"},
                {"lemma": "випити"},
            ]
        }),
        encoding="utf-8",
    )

    # Modified inventory with only 3 records and omitting 500-verbs
    dummy_inv = tmp_path / "inventory.yaml"
    dummy_inv.write_text(
        yaml.safe_dump({
            "sources": [
                {
                    "id": "ohoiko-ulp-curated-2026-07-19-bulk-ohoiko",
                    "source_family": "ohoiko",
                    "headwords": [
                        {"lemma": "актор", "locator": "ohoiko-1000-words entry 1"},
                        {"lemma": "невідомеслово", "locator": "ohoiko-1000-words entry 2"},
                    ],
                },
                {
                    "id": "ohoiko-ulp-curated-2026-07-19-bulk-ulp",
                    "source_family": "ulp",
                    "headwords": [
                        {"lemma": "актор", "locator": "ulp-1-00-lesson-notes lesson 1"},
                    ],
                },
            ]
        }),
        encoding="utf-8",
    )

    census = paired_split.analyze_taught_residual_census(
        inventory_path=dummy_inv,
        manifest_path=dummy_manifest,
        atlas_db_path=None,
    )
    summary = census["summary"]
    source_units = census["taught_source_units"]

    # 500-verbs was not in the file, so it MUST be omitted honestly
    assert "ohoiko-500-verbs" not in source_units
    assert "ohoiko-1000-words" in source_units
    assert "ulp-seasons-1-6" in source_units

    # Totals MUST reflect the 3 records in the file, proving non-hardcoded behavior
    assert summary["total_taught_records"] == 3
    assert summary["total_taught_records"] != 5938
    assert summary["total_taught_unique_keys"] == 2


def test_taught_residual_census_artifact_file_integrity() -> None:
    artifact_path = paired_split.PROJECT_ROOT / "data/lexicon/recovery-audit/2026-09-06-anna-taught-residual-census.json"
    if not artifact_path.exists():
        pytest.skip("census artifact not yet created")

    data = json.loads(artifact_path.read_text(encoding="utf-8"))
    assert data["schema"] == "atlas-7550-taught-residual-census.v1"
    summary = data["summary"]
    source_units = data["taught_source_units"]
    assert summary["total_taught_records"] == 5938
    assert summary["total_taught_unique_keys"] == 5934
    assert summary["taught_present_in_atlas"] == 5684
    assert summary["residual_missing_candidates"] == 250
    assert summary["p1_admit_count"] == 0
    assert summary["candidate_category_counts"]["already_in_atlas"] == 33
    assert summary["candidate_category_counts"]["pair_key"] == 213
    assert summary["candidate_category_counts"]["ocr"] == 1
    assert summary["candidate_category_counts"]["heritage_hold"] == 3
    assert summary["candidate_category_counts"]["vesum_unrecognized"] == 0
    assert summary["candidate_category_counts"]["p1_admit"] == 0
    assert source_units["ohoiko-1000-words"]["records"] == 1073
    assert source_units["ohoiko-500-verbs"]["records"] == 959
    assert source_units["ulp-seasons-1-6"]["records"] == 3906
    assert len(data["table_rows"]) == 250
    assert len(summary["heritage_holds"]) == 3
    assert {h["lemma"] for h in summary["heritage_holds"]} == {"переключити", "кримчанин", "просвітитель"}


def test_format_taught_residual_markdown() -> None:
    dummy_census = {
        "manifest_entries": 20121,
        "manifest_pointer": "dc1d73a434e2f136a81ece811bc346f38f4bd057e208bae88998bfce925419ec",
        "taught_source_units": {
            "ohoiko-1000-words": {
                "records": 1073,
                "unique": 1072,
                "in_atlas": 856,
                "missing": 216,
                "category_breakdown": {
                    "pair_key": 213,
                    "already_in_atlas": 2,
                    "ocr": 1,
                },
            },
            "ohoiko-500-verbs": {
                "records": 959,
                "unique": 959,
                "in_atlas": 928,
                "missing": 31,
                "category_breakdown": {
                    "already_in_atlas": 31,
                },
            },
            "ulp-seasons-1-6": {
                "records": 3906,
                "unique": 3906,
                "in_atlas": 3903,
                "missing": 3,
                "category_breakdown": {
                    "heritage_hold": 3,
                },
            },
        },
        "summary": {
            "total_taught_records": 5938,
            "total_taught_unique_keys": 5934,
            "taught_present_in_atlas": 5684,
            "residual_missing_candidates": 250,
            "candidate_category_counts": {
                "already_in_atlas": 33,
                "pair_key": 213,
                "ocr": 1,
                "heritage_hold": 3,
                "vesum_unrecognized": 0,
                "p1_admit": 0,
            },
            "pair_key_leg_counts": {
                "already_in_atlas": 406,
                "ocr": 16,
                "vesum_unrecognized": 1,
                "heritage_hold": 0,
                "p1_admit": 0,
            },
            "p1_admit_count": 0,
            "heritage_holds": [
                {"lemma": "переключити", "source": "ulp-4", "classification": "russianism", "disposition": "hold(heritage_russianism)"},
                {"lemma": "кримчанин", "source": "ulp-6", "classification": "russianism", "disposition": "hold(heritage_russianism)"},
                {"lemma": "просвітитель", "source": "ulp-6", "classification": "russianism", "disposition": "hold(heritage_russianism)"},
            ],
        },
    }
    md = paired_split.format_taught_residual_markdown(dummy_census)
    assert "## Census: Measured Taught-List Residual vs Live Atlas (#7550)" in md
    assert "`ohoiko-1000-words` | 1,072 | 856 | **216** |" in md
    assert "`ohoiko-500-verbs` | 959 | 928 | **31** |" in md
    assert "`ulp-seasons-1-6` | 3,906 | 3,903 | **3** |" in md
    assert "**250** | **0 admits** |" in md
    assert "`переключити`" in md
    assert "`кримчанин`" in md
    assert "`просвітитель`" in md
    assert "0 P1-eligible admits" in md
    assert "agy/7782-live-totals" in md
