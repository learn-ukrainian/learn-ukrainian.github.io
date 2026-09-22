"""Tests for the read-only Atlas thin-page report (#8313)."""

from __future__ import annotations

import hashlib
import json
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.atlas.atlas_db import SCHEMA
from scripts.lexicon.thin_page_report import (
    TIER_BARE,
    TIER_RICH,
    TIER_THIN,
    build_parser,
    build_report,
    classify_tier,
    frazeolohichnyi_idiom_keys,
    main,
    normalize_key,
    slovnyk_capabilities,
)

STRESSED_APPLE = "я\u0301блуко"  # combining acute on 'я'


def _make_atlas_db(path: Path) -> None:
    conn = sqlite3.connect(path)
    conn.executescript(SCHEMA)

    def article(slug: str, lemma: str, gloss: str | None, visibility: str = "public") -> None:
        conn.execute(
            """INSERT INTO articles
               (slug, display_head, lemma, entry_type, pos, gloss, review_state,
                visibility, cefr, heritage_classification, created_at, updated_at)
               VALUES (?, ?, ?, 'lemma', 'noun', ?, 'approved', ?, NULL, NULL, NULL, NULL)""",
            (slug, lemma, lemma, gloss, visibility),
        )

    def enrich(slug: str, section: str, payload: object) -> None:
        conn.execute(
            "INSERT INTO enrichment (slug, section, payload_json, source, filled_at, phase) "
            "VALUES (?, ?, ?, NULL, NULL, NULL)",
            (slug, section, json.dumps(payload, ensure_ascii=False)),
        )

    # thin: gloss + translation + morphology = 3 rich buckets; empty meaning row = missing
    article("iabluko", "яблуко", "apple")
    enrich("iabluko", "translation", {"en": ["apple"]})
    enrich("iabluko", "morphology", {"forms": ["яблука"]})
    enrich("iabluko", "meaning", {})  # phase-1 'uncovered' style placeholder

    # rich: 5 filled rich buckets
    article("sontse", "сонце", "sun")
    for section, payload in (
        ("meaning", {"definitions": ["зоря"]}),
        ("etymology", {"text": "прасл."}),
        ("morphology", {"forms": ["сонця"]}),
        ("synonyms", {"items": ["світило"]}),
        ("translation", {"en": ["sun"]}),
    ):
        enrich("sontse", section, payload)

    # bare: no definition layer, no translation
    article("test", "тест", None)
    enrich("test", "heritage_status", {"classification": "neutral"})

    # private entries are excluded from the denominator
    article("hidden", "прихований", "hidden", visibility="private")

    conn.commit()
    conn.close()


def _make_sources_db(path: Path) -> None:
    conn = sqlite3.connect(path)
    conn.executescript(
        """
        CREATE TABLE sum20_articles (normalized_lookup_key TEXT, definition_text TEXT);
        CREATE TABLE grinchenko (word TEXT, definition TEXT);
        CREATE TABLE dmklinger_uk_en (word TEXT, translations TEXT);
        CREATE TABLE esum_etymology_meta (lemma TEXT, etymology_text TEXT);
        CREATE TABLE puls_cefr (word TEXT, level TEXT);
        CREATE TABLE wiktionary (word TEXT, synonyms TEXT, antonyms TEXT);
        CREATE TABLE frazeolohichnyi (id INTEGER PRIMARY KEY, word TEXT, definition TEXT);
        CREATE VIRTUAL TABLE frazeolohichnyi_fts USING fts5(
            word, definition, content='frazeolohichnyi', content_rowid='id', tokenize='trigram'
        );
        """
    )
    conn.execute("INSERT INTO puls_cefr VALUES ('яблуко', 'A1')")
    conn.execute("INSERT INTO grinchenko VALUES ('тест', 'испытаніе')")
    conn.execute("INSERT INTO dmklinger_uk_en VALUES (?, 'test')", ("те\u0301ст",))  # stressed key
    conn.execute("INSERT INTO esum_etymology_meta VALUES ('яблуко', 'прасл. *ablъko')")
    conn.execute("INSERT INTO wiktionary VALUES ('тест', '[\"проба\"]', '')")
    conn.execute("INSERT INTO frazeolohichnyi (word, definition) VALUES ('яблуко розбрату', 'причина суперечки')")
    conn.execute(
        "INSERT INTO frazeolohichnyi_fts (rowid, word, definition) SELECT id, word, definition FROM frazeolohichnyi"
    )
    conn.commit()
    conn.close()


def _make_ulif_db(path: Path) -> None:
    conn = sqlite3.connect(path)
    conn.execute(
        """CREATE TABLE ulif_entries (
            lemma TEXT, canonical_headword TEXT, status TEXT, retrieved_at TEXT,
            paradigm_json TEXT, synonyms_json TEXT, phraseology_json TEXT,
            antonyms_json TEXT, raw_html_json TEXT)"""
    )
    conn.execute(
        "INSERT INTO ulif_entries VALUES (?, ?, 'ok', NULL, ?, NULL, NULL, NULL, NULL)",
        ("яблуко", STRESSED_APPLE, '{"headers": ["відмінок"]}'),
    )
    conn.execute(
        "INSERT INTO ulif_entries VALUES (?, ?, 'ok', NULL, ?, ?, NULL, NULL, NULL)",
        ("тест", "тест", '{"headers": ["відмінок"]}', '["проба"]'),
    )
    conn.execute("INSERT INTO ulif_entries VALUES ('мертвий', NULL, 'not_found', NULL, NULL, NULL, NULL, NULL, NULL)")
    conn.commit()
    conn.close()


def _make_slovnyk_cache(directory: Path) -> None:
    directory.mkdir()
    row = {"dictionary_slug": "newsum", "text": "означення"}
    (directory / "тест.json").write_text(
        json.dumps(
            {
                "schema_version": 4,
                "lemma": "тест",
                "lookup_word": "тест",
                "lookups": {"newsum": row, "ukreng": row, "proverbs": None},
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


@pytest.fixture
def fixture_paths(tmp_path: Path) -> dict[str, Path]:
    atlas = tmp_path / "atlas.db"
    sources = tmp_path / "sources.db"
    ulif = tmp_path / "ulif.db"
    cache = tmp_path / "slovnyk_cache"
    _make_atlas_db(atlas)
    _make_sources_db(sources)
    _make_ulif_db(ulif)
    _make_slovnyk_cache(cache)
    return {"atlas": atlas, "sources": sources, "ulif": ulif, "cache": cache}


def _build(paths: dict[str, Path], **kwargs) -> dict:
    return build_report(
        atlas_db=paths["atlas"],
        sources_db=paths["sources"],
        ulif_db=paths["ulif"],
        slovnyk_cache=paths["cache"],
        **kwargs,
    )


def test_normalize_key_strips_stress_and_apostrophes() -> None:
    assert normalize_key(STRESSED_APPLE) == "яблуко"
    assert normalize_key("  М’ЯТА ") == "м'ята"


def test_classify_tier_rule() -> None:
    assert classify_tier(set(), None)[0] == TIER_BARE
    assert classify_tier({"translation"}, None)[0] == TIER_THIN
    assert classify_tier(set(), "a gloss")[0] == TIER_THIN
    rich = {"meaning", "etymology", "morphology", "synonyms", "translation"}
    assert classify_tier(rich, None) == (TIER_RICH, 5)


def test_totals_tiers_and_missing_sections(fixture_paths: dict[str, Path]) -> None:
    report = _build(fixture_paths)
    totals = report["totals"]
    assert totals["public_entries"] == 3  # the private entry is excluded
    assert totals["tiers"] == {TIER_BARE: 1, TIER_THIN: 1, TIER_RICH: 1}
    assert totals["thin_or_bare"] == 2
    # the empty meaning payload row counts as missing
    assert report["missing_by_section"]["meaning"] == 2
    assert report["missing_by_section"]["translation"] == 1
    assert report["missing_by_section"]["cefr"] == 3
    by_slug = {entry["slug"]: entry for entry in report["entries"]}
    assert by_slug["iabluko"]["tier"] == TIER_THIN
    assert "meaning" in by_slug["iabluko"]["missing"]
    assert "translation" not in by_slug["iabluko"]["missing"]
    assert by_slug["test"]["tier"] == TIER_BARE


def test_fillable_counts_per_section_and_source(fixture_paths: dict[str, Path]) -> None:
    fillable = _build(fixture_paths)["fillable"]
    assert fillable["cefr"]["sources.db:puls_cefr"] == 1  # яблуко only
    assert fillable["definition_cards"]["sources.db:grinchenko"] == 1  # тест
    assert fillable["translation"]["sources.db:dmklinger_uk_en"] == 1  # stressed key matched тест
    assert fillable["etymology"]["sources.db:esum_etymology"] == 1  # яблуко
    assert fillable["synonyms"]["sources.db:wiktionary_synonyms"] == 1  # тест
    assert fillable["idioms"]["sources.db:frazeolohichnyi"] == 1  # яблуко розбрату
    # ULIF: only яблуко has a stressed headword; тест is missing morphology+synonyms
    assert fillable["stress"]["ulif_dump"] == 1
    assert fillable["morphology"]["ulif_dump"] == 1
    assert fillable["synonyms"]["ulif_dump"] == 1
    # slovnyk cache covers тест: meaning, definition_cards, translation
    assert fillable["meaning"]["slovnyk_cache"] == 1
    assert fillable["definition_cards"]["slovnyk_cache"] == 1
    assert fillable["translation"]["slovnyk_cache"] == 1
    # null lookups grant nothing: proverbs stays absent for slovnyk_cache
    assert "slovnyk_cache" not in fillable.get("proverbs", {})


def test_report_never_writes_to_the_databases(fixture_paths: dict[str, Path]) -> None:
    before = {
        name: hashlib.sha256(path.read_bytes()).hexdigest() for name, path in fixture_paths.items() if path.is_file()
    }
    _build(fixture_paths)
    after = {
        name: hashlib.sha256(path.read_bytes()).hexdigest() for name, path in fixture_paths.items() if path.is_file()
    }
    assert before == after


def test_missing_optional_sources_are_reported_not_fatal(fixture_paths: dict[str, Path], tmp_path: Path) -> None:
    report = build_report(
        atlas_db=fixture_paths["atlas"],
        sources_db=tmp_path / "absent-sources.db",
        ulif_db=tmp_path / "absent-ulif.db",
        slovnyk_cache=tmp_path / "absent-cache",
    )
    assert report["sources"]["ulif_dump"] == {"available": False, "path": str(tmp_path / "absent-ulif.db")}
    assert report["sources"]["slovnyk_cache"]["available"] is False
    assert report["fillable"] == {}
    assert report["totals"]["public_entries"] == 3


def test_cli_writes_json_and_respects_no_entries(fixture_paths: dict[str, Path], tmp_path: Path, capsys) -> None:
    out = tmp_path / "thin.json"
    code = main(
        [
            "--atlas",
            str(fixture_paths["atlas"]),
            "--sources-db",
            str(fixture_paths["sources"]),
            "--ulif-db",
            str(fixture_paths["ulif"]),
            "--slovnyk-cache",
            str(fixture_paths["cache"]),
            "--json",
            str(out),
            "--no-entries",
        ]
    )
    assert code == 0
    stdout = capsys.readouterr().out
    assert "Thin-page report" in stdout
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["totals"]["tiers"] == {TIER_BARE: 1, TIER_THIN: 1, TIER_RICH: 1}
    assert "entries" not in payload


def test_cli_missing_atlas_is_exit_2(tmp_path: Path, capsys) -> None:
    code = main(["--atlas", str(tmp_path / "absent-atlas.db")])
    assert code == 2
    assert "error:" in capsys.readouterr().err


def test_help_meets_cli_standard() -> None:
    help_text = build_parser().format_help()
    for marker in ("Examples:", "Outputs:", "Exit codes:", "Related:", "read-only", "--json"):
        assert marker in help_text


def test_module_help_via_python_dash_m() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "scripts.lexicon.thin_page_report", "--help"],
        capture_output=True,
        text=True,
        cwd=Path(__file__).resolve().parents[1],
        check=True,
        timeout=30,
    )
    assert "thin" in result.stdout


def test_frazeolohichnyi_definition_mention_without_phrase_match_does_not_count(
    fixture_paths: dict[str, Path], tmp_path: Path
) -> None:
    db = tmp_path / "sources_mention_only.db"
    conn = sqlite3.connect(db)
    conn.executescript(
        """
        CREATE TABLE frazeolohichnyi (id INTEGER PRIMARY KEY, word TEXT, definition TEXT);
        CREATE VIRTUAL TABLE frazeolohichnyi_fts USING fts5(
            word, definition, content='frazeolohichnyi', content_rowid='id', tokenize='trigram'
        );
        """
    )
    # Definition mentions "яблуко", but the extracted phrase is "водити за ніс"
    conn.execute(
        "INSERT INTO frazeolohichnyi (id, word, definition) VALUES "
        "(1, 'водити за ніс', 'водити за ніс. Обдурювати когось; згадка про яблуко.')"
    )
    conn.execute(
        "INSERT INTO frazeolohichnyi_fts (rowid, word, definition) "
        "SELECT id, word, definition FROM frazeolohichnyi"
    )
    conn.commit()
    conn.close()

    assert frazeolohichnyi_idiom_keys(db, ["яблуко"]) == set()

    report = build_report(
        atlas_db=fixture_paths["atlas"],
        sources_db=db,
        ulif_db=fixture_paths["ulif"],
        slovnyk_cache=fixture_paths["cache"],
    )
    assert "sources.db:frazeolohichnyi" not in report["fillable"].get("idioms", {})


def test_frazeolohichnyi_six_fts_hits_with_sixth_phrase_match_counts(
    fixture_paths: dict[str, Path], tmp_path: Path
) -> None:
    db = tmp_path / "sources_six_hits.db"
    conn = sqlite3.connect(db)
    conn.executescript(
        """
        CREATE TABLE frazeolohichnyi (id INTEGER PRIMARY KEY, word TEXT, definition TEXT);
        CREATE VIRTUAL TABLE frazeolohichnyi_fts USING fts5(
            word, definition, content='frazeolohichnyi', content_rowid='id', tokenize='trigram'
        );
        """
    )
    # 5 rows mention "яблуко" in definition text only (phrase does not contain it)
    for i in range(1, 6):
        conn.execute(
            "INSERT INTO frazeolohichnyi (id, word, definition) VALUES (?, ?, ?)",
            (i, f"фраза {i}", f"фраза {i}. Тлумачення із яблуко {i}."),
        )
    # 6th row: extracted phrase actually contains "яблуко"
    conn.execute(
        "INSERT INTO frazeolohichnyi (id, word, definition) VALUES (6, ?, ?)",
        ("яблуко розбрату", "яблуко розбрату. Причина незгоди."),
    )
    conn.execute(
        "INSERT INTO frazeolohichnyi_fts (rowid, word, definition) "
        "SELECT id, word, definition FROM frazeolohichnyi"
    )
    conn.commit()
    conn.close()

    assert frazeolohichnyi_idiom_keys(db, ["яблуко"]) == {"яблуко"}

    report = build_report(
        atlas_db=fixture_paths["atlas"],
        sources_db=db,
        ulif_db=fixture_paths["ulif"],
        slovnyk_cache=fixture_paths["cache"],
    )
    assert report["fillable"]["idioms"]["sources.db:frazeolohichnyi"] == 1


def test_slovnyk_cache_schema_version_2_contributes_no_meaning_or_definition(
    fixture_paths: dict[str, Path], tmp_path: Path
) -> None:
    cache_dir = tmp_path / "v2_slovnyk_cache"
    cache_dir.mkdir()
    row = {"dictionary_slug": "newsum", "text": "старе означення"}
    (cache_dir / "тест.json").write_text(
        json.dumps(
            {
                "schema_version": 2,
                "lemma": "тест",
                "lookup_word": "тест",
                "lookups": {
                    "newsum": row,
                    "vts": row,
                    "ukreng": row,
                },
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    caps = slovnyk_capabilities(cache_dir)
    assert caps == {}
    assert "meaning" not in caps.get("тест", set())
    assert "definition_cards" not in caps.get("тест", set())

    report = build_report(
        atlas_db=fixture_paths["atlas"],
        sources_db=fixture_paths["sources"],
        ulif_db=fixture_paths["ulif"],
        slovnyk_cache=cache_dir,
    )
    fillable = report["fillable"]
    assert "slovnyk_cache" not in fillable.get("meaning", {})
    assert "slovnyk_cache" not in fillable.get("definition_cards", {})
