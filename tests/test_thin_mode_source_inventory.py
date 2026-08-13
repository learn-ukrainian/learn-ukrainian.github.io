"""Tests for scripts.practice.thin_mode_source_inventory."""

from __future__ import annotations

import json
from pathlib import Path

import yaml

from scripts.practice.thin_mode_source_inventory import (
    SCHEMA,
    UNIQUE_LEMMA_BAR,
    build_inventory,
    format_table,
    main,
)


def _write_yaml(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, allow_unicode=True, sort_keys=False), encoding="utf-8")


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _seed_sources(base: Path) -> dict[str, Path]:
    synonym = base / "synonym_pair_verdicts.yaml"
    antonym = base / "antonym_pairs.yaml"
    paronym = base / "paronym_pairs.yaml"
    homonym = base / "homonym_pairs.yaml"
    _write_yaml(
        synonym,
        {
            "schema_version": 1,
            "approved": [
                {"a": "вода", "b": "рідина", "polarity": "synonym"},
                {"a": "вхід", "b": "вихід", "polarity": "antonym"},
                {"a": "кіт", "b": "мурчик", "polarity": "synonym"},
            ],
            "rejected": [
                {"a": "а", "b": "б", "polarity": "synonym"},
            ],
        },
    )
    _write_yaml(
        antonym,
        {
            "schema_version": 1,
            "pairs": [
                {
                    "slugA": "день",
                    "slugB": "ніч",
                    "distinction_gloss_uk": "День проти ночі.",
                },
                {
                    "slugA": "тепло",
                    "slugB": "холод",
                    "distinction_gloss_uk": "Тепло проти холоду.",
                },
            ],
        },
    )
    _write_yaml(
        paronym,
        {
            "schema_version": 1,
            "pairs": [
                {
                    "slugA": "адресант",
                    "slugB": "адресат",
                    "distinction_gloss_uk": "Адресант vs адресат.",
                },
                {
                    "slugA": "біліти",
                    "slugB": "білити",
                    "distinction_gloss_uk": "Біліти vs білити.",
                },
            ],
        },
    )
    _write_yaml(
        homonym,
        {
            "schema_version": 1,
            "pairs": [
                {
                    "slugA": "атлас",
                    "slugB": "атлас",
                    "distinction_gloss_uk": "Атлас карта vs тканина.",
                },
                {
                    "slugA": "замок",
                    "slugB": "замок",
                    "distinction_gloss_uk": "Замок будівля vs механізм.",
                },
            ],
        },
    )
    return {
        "synonym": synonym,
        "antonym": antonym,
        "paronym": paronym,
        "homonym": homonym,
    }


def _seed_shards(practice_dir: Path) -> None:
    _write_json(
        practice_dir / "practice-synonym.B1.json",
        {
            "level": "B1",
            "synonym": [
                {
                    "lemmaId": "вода",
                    "targetLemmaId": "рідина",
                    "polarity": "synonym",
                },
                {
                    "lemmaId": "вихід",
                    "targetLemmaId": "вхід",
                    "polarity": "antonym",
                },
            ],
        },
    )
    _write_json(
        practice_dir / "practice-antonym.A1.json",
        {
            "level": "A1",
            "antonym": [
                {
                    "lemmaId": "ніч",
                    "lemma": "ніч",
                    "distinction_gloss_uk": "День проти ночі.",
                }
            ],
        },
    )
    _write_json(
        practice_dir / "practice-paronym.A1.json",
        {
            "level": "A1",
            "paronym": [
                {
                    "lemmaId": "адресант",
                    "lemma": "адресант",
                    "distinction_gloss_uk": "Адресант vs адресат.",
                }
            ],
        },
    )
    _write_json(
        practice_dir / "practice-homonym.A1.json",
        {
            "level": "A1",
            "homonym": [
                {
                    "lemmaId": "атлас",
                    "lemma": "атлас",
                    "distinction_gloss_uk": "Атлас карта vs тканина.",
                }
            ],
        },
    )


def test_build_inventory_counts_unused_pairs(tmp_path: Path) -> None:
    sources = _seed_sources(tmp_path / "sources")
    practice_dir = tmp_path / "lexicon"
    _seed_shards(practice_dir)

    report = build_inventory(
        practice_dir=practice_dir,
        synonym_verdicts=sources["synonym"],
        antonym_pairs=sources["antonym"],
        paronym_pairs=sources["paronym"],
        homonym_pairs=sources["homonym"],
    )

    assert report["schema"] == SCHEMA
    assert report["unique_lemma_bar"] == UNIQUE_LEMMA_BAR

    synonym = report["modes"]["synonym"]
    assert synonym["attested_pair_count"] == 3
    assert synonym["unique_lemmas_if_all_emitted"] == 6  # вода рідина вхід вихід кіт мурчик
    assert synonym["unique_lemmas_in_shards"] == 4  # вода/рідина + вихід/вхід
    assert synonym["unused_attested_pairs"] == 1  # кіт/мурчик
    assert synonym["possible_ge_1000_from_attested"] is False

    antonym = report["modes"]["antonym"]
    assert antonym["attested_pair_count"] == 2
    assert antonym["unique_lemmas_if_all_emitted"] == 4
    assert antonym["unique_lemmas_in_shards"] == 1
    assert antonym["unused_attested_pairs"] == 1
    assert antonym["possible_ge_1000_from_attested"] is False

    paronym = report["modes"]["paronym"]
    assert paronym["attested_pair_count"] == 2
    assert paronym["unique_lemmas_if_all_emitted"] == 4
    assert paronym["unused_attested_pairs"] == 1

    homonym = report["modes"]["homonym"]
    assert homonym["attested_pair_count"] == 2
    assert homonym["unique_lemmas_if_all_emitted"] == 2
    assert homonym["unused_attested_pairs"] == 1


def test_index_fallback_for_lemma_counts(tmp_path: Path) -> None:
    sources = _seed_sources(tmp_path / "sources")
    practice_dir = tmp_path / "lexicon"
    _write_json(
        practice_dir / "practice-index.A1.json",
        {
            "level": "A1",
            "items": [
                {"lemmaId": "день", "modes": ["antonym", "flashcards"]},
                {"lemmaId": "ніч", "modes": ["antonym"]},
                {"lemmaId": "атлас", "modes": ["homonym"]},
            ],
        },
    )

    report = build_inventory(
        practice_dir=practice_dir,
        synonym_verdicts=sources["synonym"],
        antonym_pairs=sources["antonym"],
        paronym_pairs=sources["paronym"],
        homonym_pairs=sources["homonym"],
        prefer_index=True,
    )

    assert report["modes"]["antonym"]["unique_lemmas_in_shards"] == 2
    assert report["modes"]["homonym"]["unique_lemmas_in_shards"] == 1
    # Without mode shards, gloss matching finds no used pairs.
    assert report["modes"]["antonym"]["unused_attested_pairs"] == 2
    assert report["modes"]["antonym"]["lemma_source"] == "practice-index"


def test_cli_prints_unused_table(tmp_path: Path, capsys) -> None:
    sources = _seed_sources(tmp_path / "sources")
    practice_dir = tmp_path / "lexicon"
    _seed_shards(practice_dir)
    out = tmp_path / "inventory.json"

    rc = main(
        [
            "--practice-dir",
            str(practice_dir),
            "--synonym-verdicts",
            str(sources["synonym"]),
            "--antonym-pairs",
            str(sources["antonym"]),
            "--paronym-pairs",
            str(sources["paronym"]),
            "--homonym-pairs",
            str(sources["homonym"]),
            "--json-out",
            str(out),
        ]
    )
    assert rc == 0
    captured = capsys.readouterr()
    assert "Unused" in captured.out
    assert "synonym" in captured.out
    assert "antonym" in captured.out
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["modes"]["synonym"]["unused_attested_pairs"] == 1
    assert "synonym" in format_table(payload)
