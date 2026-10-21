"""Unit tests for Word Atlas heteronym disambiguation (scripts/lexicon/enrich_heteronyms.py)."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from scripts.lexicon import enrich_heteronyms
from scripts.lexicon.sum20_lookup import lookup_sum11_colonization_context
from tests.helpers.sum20_store import canonical_sum20_store as canonical_sum20_store


def test_colonization_context_builder_sets_explicit_citation_marker(tmp_path: Path) -> None:
    db = tmp_path / "sources.db"
    with sqlite3.connect(db) as conn:
        conn.execute("CREATE TABLE sum11 (word TEXT, definition TEXT, text TEXT, "
                     "sovietization_risk INTEGER, sovietization_keywords TEXT)")
        conn.execute("INSERT INTO sum11 VALUES (?, ?, ?, ?, ?)", ("тест", "fixture", "", 0, ""))
    context = lookup_sum11_colonization_context("тест", db)
    assert context is not None
    assert context["red_flag"] is True
    assert context["sovietization_risk"] == 0


def test_curated_heteronyms_structure():
    """Curated heteronyms must include all required fields for Word Atlas."""
    for lemma, items in enrich_heteronyms.CURATED_HETERONYMS.items():
        assert len(items) >= 2, f"Expected at least 2 heteronyms for {lemma}"
        variant_keys = [
            (
                item["headword"],
                item.get("morphology", {}).get("paradigm", {}).get("animacy"),
                item.get("short_label"),
            )
            for item in items
        ]
        assert len(set(variant_keys)) == len(variant_keys), f"Duplicate variant entries found for {lemma}"
        for item in items:
            assert "headword" in item
            assert "gloss" in item
            assert "short_label" in item
            assert "heritage_status" in item
            assert "distinction_note" in item
            assert "morphology" in item
            assert "pronunciation" in item
            assert "stress" in item


def test_gorod_disambiguation():
    """Verify город vegetable garden is distinguished from archaic город city."""
    items = enrich_heteronyms.build_heteronyms_for_lemma("город")
    assert items is not None
    assert len(items) == 2

    garden, city = items[0], items[1]

    # Sense 0: vegetable garden (A2, modern standard)
    assert garden["headword"] == "горо́д"
    assert garden["cefr"] == "A2"
    assert garden["heritage_status"]["classification"] == "standard"
    assert garden["pronunciation"]["ipa"] == "[ɦɔˈrɔd]"
    assert garden["morphology"]["paradigm"]["cases"]["родовий"]["singular"] == "горо́ду"
    assert garden["morphology"]["paradigm"]["cases"]["місцевий"]["singular"] == "на горо́ді / горо́ду"
    assert "місто" not in garden["sections"]["synonyms"]["items"]
    assert "грядка" in garden["sections"]["synonyms"]["items"]

    # Sense 1: archaic city
    assert city["headword"] == "го́род"
    assert city["heritage_status"]["classification"] == "authentic-archaism"
    assert city["heritage_status"]["warning_severity"] == "treasured"
    assert city["pronunciation"]["ipa"] == "[ˈɦɔrɔd]"
    assert "місто" in city["sections"]["synonyms"]["items"]


def test_sum11_parsing():
    """Verify regex extraction of heteronyms from multi-headword СУМ-11 text."""
    sample_text = (
        "А́ТЛАС, у, ч. Укладений за певною системою збірник карт.\n"
        "АТЛА́С, у, ч. Шовкова або напівшовкова тканина, блискуча з лиця."
    )
    parsed = enrich_heteronyms.parse_sum11_heteronyms("атлас", sample_text)
    assert len(parsed) == 2
    assert parsed[0]["head"] == "А́ТЛАС"
    assert "збірник карт" in parsed[0]["body"]
    assert parsed[1]["head"] == "АТЛА́С"
    assert "Шовкова" in parsed[1]["body"]


def test_apply_heteronyms_to_db(tmp_path: Path):
    """Verify apply_heteronyms updates SQLite database properly for all heteronym lemmas."""
    db_path = tmp_path / "test_atlas.db"
    dummy_manifest = tmp_path / "empty_manifest.json"
    dummy_manifest.write_text("{}", encoding="utf-8")

    conn = sqlite3.connect(db_path)
    conn.execute(
        """CREATE TABLE article_payloads (
            slug TEXT PRIMARY KEY,
            route_order INTEGER,
            payload_json TEXT NOT NULL,
            is_public_route INTEGER NOT NULL DEFAULT 1
        )"""
    )
    conn.execute(
        """CREATE TABLE articles (
            slug TEXT PRIMARY KEY,
            display_head TEXT NOT NULL,
            pos TEXT,
            gloss TEXT,
            heritage_classification TEXT
        )"""
    )

    initial_records = [
        ("город", "город", "vegetable garden", "authentic-archaism", {"items": ["місто"]}),
        ("замок", "замок", "castle / lock", "standard", {"items": ["палац"]}),
        ("атлас", "атлас", "atlas / satin", "standard", None),
    ]
    for slug, head, gloss, heritage, syns in initial_records:
        sec = {"synonyms": syns} if syns else {}
        p = {"lemma": slug, "url_slug": slug, "gloss": gloss, "heritage_status": {"classification": heritage}, "sections": sec}
        conn.execute("INSERT INTO article_payloads VALUES (?, 1, ?, 1)", (slug, json.dumps(p)))
        conn.execute("INSERT INTO articles VALUES (?, ?, 'noun', ?, ?)", (slug, head, gloss, heritage))
    conn.commit()
    conn.close()

    counts = enrich_heteronyms.apply_heteronyms(
        db_path=db_path, manifest_path=dummy_manifest, lemmas=["город", "замок", "атлас"]
    )
    assert counts["db_payloads"] == 3
    assert counts["db_articles"] == 3

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # Verify город
    g_row = cur.execute("SELECT payload_json FROM article_payloads WHERE slug = 'город'").fetchone()
    assert g_row is not None
    g_payload = json.loads(g_row[0])
    assert len(g_payload["heteronyms"]) == 2
    assert g_payload["heteronyms"][0]["headword"] == "горо́д"
    assert g_payload["display_head"] == "горо́д"
    assert g_payload["heritage_status"]["classification"] == "standard"
    assert g_payload["sections"]["synonyms"]["items"] == ["грядка", "городчик"]

    # Verify замок
    z_row = cur.execute("SELECT payload_json FROM article_payloads WHERE slug = 'замок'").fetchone()
    assert z_row is not None
    z_payload = json.loads(z_row[0])
    assert len(z_payload["heteronyms"]) == 2
    assert z_payload["display_head"] == "за́мок"
    assert "фортеця" in z_payload["sections"]["synonyms"]["items"]
    z_art = cur.execute("SELECT display_head, gloss FROM articles WHERE slug = 'замок'").fetchone()
    assert z_art == ("за́мок", "castle, fortress, palace")

    # Verify атлас
    a_row = cur.execute("SELECT payload_json FROM article_payloads WHERE slug = 'атлас'").fetchone()
    assert a_row is not None
    a_payload = json.loads(a_row[0])
    assert len(a_payload["heteronyms"]) == 2
    assert a_payload["display_head"] == "а́тлас"
    assert "збірник карт" in a_payload["sections"]["synonyms"]["items"]
    a_art = cur.execute("SELECT display_head, gloss FROM articles WHERE slug = 'атлас'").fetchone()
    assert a_art == ("а́тлас", "atlas (bound collection of maps)")

    conn.close()


def test_apply_heteronyms_to_manifest(tmp_path: Path):
    """Verify apply_heteronyms updates JSON manifest properly for all heteronyms."""
    manifest_path = tmp_path / "lexicon-manifest.json"
    data = {
        "entries": [
            {
                "lemma": "город",
                "url_slug": "город",
                "gloss": "vegetable garden",
                "heritage_status": {"classification": "authentic-archaism"},
            },
            {
                "lemma": "замок",
                "url_slug": "замок",
                "gloss": "castle / lock",
                "heritage_status": {"classification": "standard"},
            },
            {
                "lemma": "атлас",
                "url_slug": "атлас",
                "gloss": "atlas / satin",
                "heritage_status": {"classification": "standard"},
            },
        ]
    }
    manifest_path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

    dummy_db = tmp_path / "empty.db"
    counts = enrich_heteronyms.apply_heteronyms(
        db_path=dummy_db, manifest_path=manifest_path, lemmas=["город", "замок", "атлас"]
    )
    assert counts["manifest_entries"] == 3

    updated = json.loads(manifest_path.read_text(encoding="utf-8"))
    entries = {e["lemma"]: e for e in updated["entries"]}

    assert entries["город"]["display_head"] == "горо́д"
    assert entries["город"]["sections"]["synonyms"]["items"] == ["грядка", "городчик"]

    assert entries["замок"]["display_head"] == "за́мок"
    assert "фортеця" in entries["замок"]["sections"]["synonyms"]["items"]

    assert entries["атлас"]["display_head"] == "а́тлас"
    assert "збірник карт" in entries["атлас"]["sections"]["synonyms"]["items"]


def test_curated_heteronyms_ts_parity():
    """Verify site/src/lib/lexicon/curated-heteronyms.ts exactly matches enrich_heteronyms.CURATED_HETERONYMS."""
    ts_file = Path(__file__).resolve().parents[1] / "site" / "src" / "lib" / "lexicon" / "curated-heteronyms.ts"
    assert ts_file.is_file(), f"Expected {ts_file} to exist"
    content = ts_file.read_text(encoding="utf-8")

    prefix = "export const CURATED_HETERONYMS: Record<string, LexiconEntry[]> = "
    start_idx = content.find(prefix)
    assert start_idx != -1, f"Could not find CURATED_HETERONYMS assignment in {ts_file}"
    start_idx += len(prefix)
    end_idx = content.find(";\n\nexport function getEffectiveHeteronyms", start_idx)
    assert end_idx != -1, f"Could not find end of CURATED_HETERONYMS object in {ts_file}"
    json_literal = content[start_idx:end_idx].strip()
    ts_data = json.loads(json_literal)

    assert set(ts_data.keys()) == set(enrich_heteronyms.CURATED_HETERONYMS.keys())

    for lemma, py_items in enrich_heteronyms.CURATED_HETERONYMS.items():
        ts_items = ts_data[lemma]
        assert len(ts_items) == len(py_items)
        for i, py_item in enumerate(py_items):
            ts_item = ts_items[i]
            assert ts_item["lemma"] == lemma
            assert ts_item["url_slug"] == lemma
            ts_item_clean = {k: v for k, v in ts_item.items() if k not in ("lemma", "url_slug")}
            assert ts_item_clean == py_item, f"Drift detected for {lemma} entry #{i} ({py_item['headword']})"


def test_batch3_lemmas_not_duplicated_from_earlier_batches():
    """Verify batch 3's 32 lemmas are net-new (варення and бубон were dropped as dupes)."""
    from scripts.lexicon.curated_heteronyms_batch import CURATED_HETERONYMS_BATCH
    from scripts.lexicon.curated_heteronyms_batch2 import CURATED_HETERONYMS_BATCH_2
    from scripts.lexicon.curated_heteronyms_batch3 import CURATED_HETERONYMS_BATCH_3

    assert len(CURATED_HETERONYMS_BATCH_3) == 32
    earlier = set(CURATED_HETERONYMS_BATCH) | set(CURATED_HETERONYMS_BATCH_2)
    assert earlier & set(CURATED_HETERONYMS_BATCH_3) == set()
    assert "варення" not in CURATED_HETERONYMS_BATCH_3
    assert "бубон" not in CURATED_HETERONYMS_BATCH_3
    assert "копати" in CURATED_HETERONYMS_BATCH_3
    assert "коханий" in CURATED_HETERONYMS_BATCH_3


def test_batch9_lemmas_not_duplicated_from_earlier_batches():
    """Verify batch 9's 32 lemmas are net-new and mutually disjoint with batches 1-8."""
    from scripts.lexicon.curated_heteronyms_batch import CURATED_HETERONYMS_BATCH
    from scripts.lexicon.curated_heteronyms_batch2 import CURATED_HETERONYMS_BATCH_2
    from scripts.lexicon.curated_heteronyms_batch3 import CURATED_HETERONYMS_BATCH_3
    from scripts.lexicon.curated_heteronyms_batch4 import CURATED_HETERONYMS_BATCH_4
    from scripts.lexicon.curated_heteronyms_batch5 import CURATED_HETERONYMS_BATCH_5
    from scripts.lexicon.curated_heteronyms_batch6 import CURATED_HETERONYMS_BATCH_6
    from scripts.lexicon.curated_heteronyms_batch7 import CURATED_HETERONYMS_BATCH_7
    from scripts.lexicon.curated_heteronyms_batch8 import CURATED_HETERONYMS_BATCH_8
    from scripts.lexicon.curated_heteronyms_batch9 import CURATED_HETERONYMS_BATCH_9

    assert len(CURATED_HETERONYMS_BATCH_9) == 32
    assert sum(len(v) for v in CURATED_HETERONYMS_BATCH_9.values()) == 64
    earlier = (
        set(CURATED_HETERONYMS_BATCH)
        | set(CURATED_HETERONYMS_BATCH_2)
        | set(CURATED_HETERONYMS_BATCH_3)
        | set(CURATED_HETERONYMS_BATCH_4)
        | set(CURATED_HETERONYMS_BATCH_5)
        | set(CURATED_HETERONYMS_BATCH_6)
        | set(CURATED_HETERONYMS_BATCH_7)
        | set(CURATED_HETERONYMS_BATCH_8)
    )
    assert earlier & set(CURATED_HETERONYMS_BATCH_9) == set()
    assert "лупання" in CURATED_HETERONYMS_BATCH_9
    assert "люстровий" in CURATED_HETERONYMS_BATCH_9
    assert "маячний" in CURATED_HETERONYMS_BATCH_9
    assert "набігати" in CURATED_HETERONYMS_BATCH_9
    assert "набухати" in CURATED_HETERONYMS_BATCH_9
    assert "наварний" in CURATED_HETERONYMS_BATCH_9
    assert "навозити" in CURATED_HETERONYMS_BATCH_9
    assert "назубок" in CURATED_HETERONYMS_BATCH_9
    assert "наслухати" in CURATED_HETERONYMS_BATCH_9
    assert "настильний" in CURATED_HETERONYMS_BATCH_9
    assert "невигода" in CURATED_HETERONYMS_BATCH_9
    assert "неперехідний" in CURATED_HETERONYMS_BATCH_9
    assert "неповоротний" in CURATED_HETERONYMS_BATCH_9
    assert "оббігати" in CURATED_HETERONYMS_BATCH_9
    assert "обводити" in CURATED_HETERONYMS_BATCH_9
    assert "обідець" in CURATED_HETERONYMS_BATCH_9
    assert "обрізання" in CURATED_HETERONYMS_BATCH_9
    assert "окісний" in CURATED_HETERONYMS_BATCH_9
    assert "окружний" in CURATED_HETERONYMS_BATCH_9
    assert "описка" in CURATED_HETERONYMS_BATCH_9
    assert "пахолок" in CURATED_HETERONYMS_BATCH_9
    assert "перевозити" in CURATED_HETERONYMS_BATCH_9
    assert "перекладка" in CURATED_HETERONYMS_BATCH_9
    assert "переливний" in CURATED_HETERONYMS_BATCH_9
    assert "переруб" in CURATED_HETERONYMS_BATCH_9
    assert "попадати" in CURATED_HETERONYMS_BATCH_9
    assert "посипатися" in CURATED_HETERONYMS_BATCH_9
    assert "пригар" in CURATED_HETERONYMS_BATCH_9
    assert "провозити" in CURATED_HETERONYMS_BATCH_9
    assert "розбігатися" in CURATED_HETERONYMS_BATCH_9
    assert "рябець" in CURATED_HETERONYMS_BATCH_9
    assert "травник" in CURATED_HETERONYMS_BATCH_9

    # Check pre-Soviet witnesses
    lupannya = CURATED_HETERONYMS_BATCH_9["лупання"]
    assert "Грінченко" in lupannya[0]["pre_soviet_witness"]["witness"]
    assert "Миганіе" in lupannya[0]["pre_soviet_witness"]["quote"]
    assert "Откалываніе" in lupannya[1]["pre_soviet_witness"]["quote"]

    obidets = CURATED_HETERONYMS_BATCH_9["обідець"]
    assert "Грінченко" in obidets[0]["pre_soviet_witness"]["witness"]
    assert "обід" in obidets[0]["pre_soviet_witness"]["quote"].lower()
    assert "Ободок" in obidets[1]["pre_soviet_witness"]["quote"]

    # Morphology check: лупання must be singular-only, переруб genitive must be пере́рубу, травник genitive must be травника́
    assert "plural" not in lupannya[0]["morphology"]["paradigm"]["cases"]["називний"]
    assert "plural" not in lupannya[1]["morphology"]["paradigm"]["cases"]["називний"]
    pererub = CURATED_HETERONYMS_BATCH_9["переруб"]
    assert pererub[0]["morphology"]["paradigm"]["cases"]["родовий"]["singular"] == "пере́рубу"
    travnik = CURATED_HETERONYMS_BATCH_9["травник"]
    assert travnik[1]["morphology"]["paradigm"]["cases"]["родовий"]["singular"] == "травника́"

    # Decolonization check: no normative СУМ-11 citations outside soviet_colonization_context
    for lemma, variants in CURATED_HETERONYMS_BATCH_9.items():
        for v in variants:
            assert "СУМ-11" not in v["meaning"]["source"], f"Found СУМ-11 in meaning.source for {lemma}"
            assert "СУМ-11" not in v["stress"]["source"], f"Found СУМ-11 in stress.source for {lemma}"


def test_homonyms_with_numeric_suffixes_and_identical_stress_not_treated_as_heteronyms(monkeypatch):
    """Separate dictionary article numbers from headword before comparing stress (#8039).

    Ensures that homonyms with identical stress but distinct article numbers (e.g. ТЕ́СТ 1 and ТЕ́СТ 2)
    are not treated as heteronyms, and that numeric suffixes are stripped from headwords.
    """
    from scripts.lexicon import sum20_lookup

    synthetic_same_stress = {
        "lemma": "синтетичнийтест",
        "modern_sum20": [
            {
                "stressed_headword": "ТЕ́СТ 1",
                "grammar": "іменник",
                "senses": [{"definition": "Перше значення тесту"}],
            },
            {
                "stressed_headword": "ТЕ́СТ 2",
                "grammar": "іменник",
                "senses": [{"definition": "Друге значення тесту"}],
            },
        ],
        "soviet_colonization_context": None,
    }

    monkeypatch.setattr(
        sum20_lookup,
        "lookup_decolonized_heteronym_evidence",
        lambda lemma: synthetic_same_stress,
    )
    result_same = enrich_heteronyms.build_heteronyms_for_lemma("синтетичнийтест")
    assert result_same is None

    synthetic_diff_stress = {
        "lemma": "синтетичнийтест",
        "modern_sum20": [
            {
                "stressed_headword": "ТЕ́СТ 1",
                "grammar": "іменник",
                "senses": [{"definition": "Перше значення тесту"}],
            },
            {
                "stressed_headword": "ТЕСТІ́ 2",
                "grammar": "іменник",
                "senses": [{"definition": "Друге значення тесту"}],
            },
        ],
        "soviet_colonization_context": None,
    }

    monkeypatch.setattr(
        sum20_lookup,
        "lookup_decolonized_heteronym_evidence",
        lambda lemma: synthetic_diff_stress,
    )
    result_diff = enrich_heteronyms.build_heteronyms_for_lemma("синтетичнийтест")
    assert result_diff is not None
    assert len(result_diff) == 2
    assert result_diff[0]["headword"] == "ТЕ́СТ"
    assert result_diff[1]["headword"] == "ТЕСТІ́"


def test_build_heteronyms_for_lemma_preserves_all_homonyms_when_stresses_differ(monkeypatch):
    """Verify that when multiple articles share stress but at least one differs, ALL articles are preserved."""
    from scripts.lexicon import sum20_lookup

    synthetic_three_articles = {
        "lemma": "синтетичнийтест",
        "modern_sum20": [
            {
                "stressed_headword": "ТЕ́СТ 1",
                "grammar": "іменник",
                "senses": [{"definition": "Перше значення тесту"}],
            },
            {
                "stressed_headword": "ТЕ́СТ 2",
                "grammar": "іменник",
                "senses": [{"definition": "Друге значення тесту"}],
            },
            {
                "stressed_headword": "ТЕСТІ́ 3",
                "grammar": "іменник",
                "senses": [{"definition": "Третє значення тесту"}],
            },
        ],
        "soviet_colonization_context": None,
    }

    monkeypatch.setattr(
        sum20_lookup,
        "lookup_decolonized_heteronym_evidence",
        lambda lemma: synthetic_three_articles,
    )
    result = enrich_heteronyms.build_heteronyms_for_lemma("синтетичнийтест")
    assert result is not None
    assert len(result) == 3
    assert result[0]["headword"] == "ТЕ́СТ"
    assert result[0]["gloss"] == "Перше значення тесту"
    assert result[1]["headword"] == "ТЕ́СТ"
    assert result[1]["gloss"] == "Друге значення тесту"
    assert result[2]["headword"] == "ТЕСТІ́"
    assert result[2]["gloss"] == "Третє значення тесту"


def test_batch13_vesum_attestation_and_witness_integrity():
    """Ensure Batch 13 has accurate vesum_attested flags and verified Grinchenko quotes."""
    from scripts.lexicon.curated_heteronyms_batch13 import CURATED_HETERONYMS_BATCH_13

    # Lemmas without base lemma entries in VESUM
    unattested = {"містовий", "навидіти", "навидітися", "світок", "совик", "типик", "гвоздик"}
    for lem in unattested:
        for v in CURATED_HETERONYMS_BATCH_13[lem]:
            assert v["heritage_status"]["vesum_attested"] is False, f"Expected {lem} to have vesum_attested=False"

    # волохи: воло́хи (ethnonym) is attested as plural of волох, but во́лохи (body hairs) is not
    assert CURATED_HETERONYMS_BATCH_13["волохи"][0]["heritage_status"]["vesum_attested"] is False
    assert CURATED_HETERONYMS_BATCH_13["волохи"][1]["heritage_status"]["vesum_attested"] is True

    # тупик: тупи́к (inanim dead end) is attested in VESUM, but ту́пик (anim puffin bird) is not
    assert CURATED_HETERONYMS_BATCH_13["тупик"][0]["heritage_status"]["vesum_attested"] is False
    assert CURATED_HETERONYMS_BATCH_13["тупик"][1]["heritage_status"]["vesum_attested"] is True
