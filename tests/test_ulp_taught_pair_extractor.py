"""Fixture-level tests for ULP taught-pair extractor (#7550 Unit B)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from scripts.lexicon import ulp_taught_pair_extractor as extractor
from scripts.lexicon.ulp_taught_pair_extractor import (
    extract_taught_pairs_from_text,
    format_markdown_tables,
    measure_corpus_intake_ulp,
    measure_curated_ulp_lists,
)


def test_extract_basic_margin_pair() -> None:
    sample_text = (
        "Ви не уявляєте, яка я щаслива говорити до вас знову.              уявля́ти ― to imagine\n"
        "записувала нових епізодів, але я повернулася!                     умо́ви ― conditions\n"
    )
    pairs = extract_taught_pairs_from_text(sample_text, source_file="ulp-6-00-lesson-notes", season=6)
    assert len(pairs) == 2
    assert pairs[0].ukrainian_headword == "уявля́ти"
    assert pairs[0].english_gloss == "to imagine"
    assert pairs[0].season == 6
    assert pairs[1].ukrainian_headword == "умо́ви"
    assert pairs[1].english_gloss == "conditions"


def test_extract_key_vocabulary_table_pairs() -> None:
    sample_text = (
        "Key Vocabulary 1-01\n"
        "              моро́зиво                                         ice cream\n"
        "              Приві́т!                                          Hi!\n"
        "              чудо́во                                           great, wonderful (adverb)\n"
    )
    pairs = extract_taught_pairs_from_text(sample_text, source_file="ulp-1-00-lesson-notes", season=1)
    assert len(pairs) == 3
    assert pairs[0].ukrainian_headword == "моро́зиво"
    assert pairs[0].english_gloss == "ice cream"
    assert pairs[1].ukrainian_headword == "Приві́т!"
    assert pairs[1].english_gloss == "Hi!"
    assert pairs[2].ukrainian_headword == "чудо́во"
    assert pairs[2].english_gloss == "great, wonderful (adverb)"


def test_extract_inline_dash_pairs() -> None:
    sample_text = "Чудо́во! — Great! Wonderful!\nДу́же до́бре! — Very good!\nДо́бре. — Fine.\n"
    pairs = extract_taught_pairs_from_text(sample_text, source_file="ulp-1-00-lesson-notes", season=1)
    assert len(pairs) == 3
    assert pairs[0].ukrainian_headword == "Чудо́во!"
    assert pairs[0].english_gloss == "Great! Wonderful!"
    assert pairs[2].ukrainian_headword == "До́бре."
    assert pairs[2].english_gloss == "Fine."


def test_measure_curated_ulp_lists_with_dummy_files(tmp_path: Path) -> None:
    dummy_manifest = tmp_path / "manifest.json"
    dummy_manifest.write_text(
        json.dumps(
            {
                "entries": [
                    {"lemma": "морозиво"},
                    {"lemma": "привіт"},
                    {"lemma": "чудово"},
                ]
            }
        ),
        encoding="utf-8",
    )

    dummy_inv = tmp_path / "inventory.yaml"
    dummy_inv.write_text(
        yaml.safe_dump(
            {
                "sources": [
                    {
                        "id": "ohoiko-ulp-curated-2026-07-19-bulk-ulp",
                        "headwords": [
                            {"lemma": "морозиво", "locator": "ulp-1-00-lesson-notes lesson 1"},
                            {"lemma": "привіт", "locator": "ulp-1-00-lesson-notes lesson 1"},
                            {"lemma": "переключити", "locator": "ulp-4-00-lesson-notes lesson 121"},
                        ],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    res = measure_curated_ulp_lists(inventory_path=dummy_inv, manifest_path=dummy_manifest)
    assert res["total_curated_rows"] == 3
    assert res["total_in_atlas"] == 2
    assert res["total_missing"] == 1
    assert res["per_season"][1]["missing_count"] == 0
    assert res["per_season"][4]["missing_count"] == 1
    assert res["per_season"][4]["missing_lemmas"] == ["переключити"]


def test_measure_corpus_intake_ulp_with_dummy_files(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    dummy_manifest = tmp_path / "manifest.json"
    dummy_manifest.write_text(
        json.dumps(
            {
                "entries": [
                    {"lemma": "привіт"},
                ]
            }
        ),
        encoding="utf-8",
    )

    dec_dir = tmp_path / "decisions"
    dec_dir.mkdir(parents=True, exist_ok=True)
    batch_file = dec_dir / "2026-07-14-ohoiko-corpus-intake-batch-01.yaml"
    batch_file.write_text(
        yaml.safe_dump(
            {
                "decisions": [
                    {
                        "lemma": "привіт",
                        "decision": "reject",
                        "source_inventory": {
                            "source_id": "ulp-1-00-lesson-notes",
                        },
                    },
                    {
                        "lemma": "невідомеслово",
                        "decision": "needs_more_evidence",
                        "source_inventory": {
                            "source_id": "ulp-1-00-lesson-notes",
                        },
                    },
                ]
            }
        ),
        encoding="utf-8",
    )

    # Mock verify_word so test does not depend on external DB
    monkeypatch.setattr(extractor, "verify_word", lambda word: [] if word == "невідомеслово" else [{"pos": "noun"}])

    res = measure_corpus_intake_ulp(decisions_dir=dec_dir, manifest_path=dummy_manifest)
    s1 = res["per_season"][1]
    assert s1["total_rows"] == 2
    assert s1["unique_lemmas"] == 2
    assert s1["already_in_atlas"] == 1
    assert s1["missing_total"] == 1
    assert s1["vesum_unrecognized"] == 1
    assert s1["no_en_count"] == 2


def test_format_markdown_tables() -> None:
    curated = {
        "total_curated_rows": 3906,
        "total_in_atlas": 3903,
        "total_missing": 3,
        "per_season": {
            1: {"unique_lemmas": 369, "in_atlas": 369, "missing_count": 0, "missing_lemmas": []},
            4: {"unique_lemmas": 984, "in_atlas": 983, "missing_count": 1, "missing_lemmas": ["переключити"]},
        },
    }
    intake = {
        "per_season": {
            1: {
                "source_id": "ulp-1-00-lesson-notes",
                "unique_lemmas": 636,
                "already_in_atlas": 320,
                "missing_total": 316,
                "vesum_ok_missing": 114,
                "vesum_unrecognized": 202,
                "heritage_hold": 0,
            }
        }
    }
    taught = {
        "per_season": {
            1: {
                "source_file": "ulp-1-00-lesson-notes",
                "raw_taught_pairs": 98,
                "unique_uk_headwords": 92,
                "unique_single_word_lemmas": 63,
                "already_in_atlas": 58,
                "vesum_ok_missing_count": 1,
                "vesum_unrecognized_count": 4,
                "heritage_hold_count": 0,
                "multiword_phrases": 44,
            }
        }
    }
    md = format_markdown_tables(curated, intake, taught)
    assert "## Unit B — ULP Seasons 1–6 Lemma Census (#7550)" in md
    assert "0 admits" in md
    assert "переключити" in md
    assert "hold(heritage_russianism) via #7557" in md
