"""Alona v5 admission uses public Atlas facts rather than invented CEFR."""

from __future__ import annotations

import json
from pathlib import Path

from scripts.lexicon import alona_v5_atlas_admission as admission


def _manifest(path: Path, entries: list[dict[str, object]]) -> Path:
    path.write_text(json.dumps({"entries": entries}, ensure_ascii=False), encoding="utf-8")
    return path


def test_candidates_keep_explicit_verb_expression_type(tmp_path: Path, monkeypatch) -> None:
    manifest = _manifest(
        tmp_path / "manifest.json",
        [{"lemma": "відомий", "url_slug": "відомий", "pos": "adj"}],
    )
    monkeypatch.setattr(admission, "_vesum_pos", lambda word: "verb" if word == "виходити" else None)

    candidates = admission.candidates_for_manifest(
        [{"lemma": "виходити з ладу", "gloss": "to break down"}], manifest
    )

    assert candidates["auto_merge"] == [
        {
            "lemma": "виходити з ладу",
            "gloss": "to break down",
            "pos": None,
            "entry_type": "expression",
            "primary_source": "alona_v5_curated_seed",
        }
    ]


def test_candidates_do_not_duplicate_an_existing_apostrophe_variant_route(tmp_path: Path) -> None:
    manifest = _manifest(
        tmp_path / "manifest.json",
        [{"lemma": "з'ясувати", "url_slug": "з-ясувати", "pos": "verb"}],
    )

    candidates = admission.candidates_for_manifest(
        [{"lemma": "з’ясувати", "gloss": "to find out", "slug": "з-ясувати"}], manifest
    )

    assert candidates == {"auto_merge": [], "needs_review": []}


def test_normalize_rows_projects_private_v5_input_to_replayable_schema() -> None:
    rows = admission.normalize_rows(
        [
            {
                "row": 7,
                "ua": "Вийти з ладу",
                "en": "to break down",
                "sentence": "Пристрій вийшов з ладу.",
                "sentence_status": "ok",
                "provenance": {"source_file": "ukrlib-example", "credit": "Автор"},
                "private_source_path": ".claude/atlas-epic/plans/alona-truth/private.jsonl",
            }
        ]
    )

    assert rows == [
        {
            "seedRow": 7,
            "lemma": "вийти з ладу",
            "gloss": "to break down",
            "slug": "вийти-з-ладу",
            "sentenceStatus": "ok",
            "example": "Пристрій вийшов з ладу.",
            "provenance": {"source_file": "ukrlib-example", "credit": "Автор"},
        }
    ]


def test_practice_seed_reports_no_hit_and_retains_duplicate_attestations(tmp_path: Path) -> None:
    manifest = _manifest(
        tmp_path / "manifest.json",
        [
            {"lemma": "відомий", "url_slug": "відомий", "pos": "adj", "enrichment": {"cefr": {"level": "A2", "source": "PULS"}}},
            {"lemma": "рідкісний", "url_slug": "рідкісний", "pos": "adj", "enrichment": {"cefr": {"level": "B2", "source": "PULS"}}},
            {"lemma": "неоцінений", "url_slug": "неоцінений", "pos": "adj"},
        ],
    )
    provenance = {"source_file": "ukrlib-example", "credit": "Автор"}
    rows = [
        {"seedRow": 1, "lemma": "відомий", "sentenceStatus": "ok", "example": "Відомий приклад.", "provenance": provenance},
        {"seedRow": 2, "lemma": "відомий", "sentenceStatus": "ok", "example": "Другий приклад.", "provenance": provenance},
        {"seedRow": 3, "lemma": "рідкісний", "sentenceStatus": "no_hit"},
        {"seedRow": 4, "lemma": "неоцінений", "sentenceStatus": "ok", "example": "Неоцінений приклад.", "provenance": provenance},
    ]

    seed, report = admission.prepare_practice_seed(rows, manifest)

    assert len(seed["entries"]) == 2
    assert report["counts"] == {
        "active_seed_rows": 4,
        "unique_seed_lemmas": 3,
        "public_atlas_rows": 4,
        "atlas_failures": 0,
        "sentence_status": {"no_hit": 1, "ok": 3},
        "practice_admitted_rows": 2,
        "practice_skipped_no_cefr": 1,
        "practice_cefr_sources": {"PULS": 2},
    }
    assert report["practice_skipped_no_cefr"] == [{"seedRow": 4, "lemma": "неоцінений"}]
