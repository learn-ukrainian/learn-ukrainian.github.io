from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

import pytest
import yaml

from scripts.lexicon.reconcile_calque_clusters import (
    CURRENT_ENRICHMENT_VERSION,
    CalqueReconciliationEngine,
    CandidateAlternative,
    strip_accents,
)


def test_strip_accents() -> None:
    assert strip_accents("пилосо́с") == "пилосос"
    assert strip_accents("безкошто́вний") == "безкоштовний"
    assert strip_accents("чи́стий") == "чистий"
    assert strip_accents("plain") == "plain"


def test_candidate_alternative_validation() -> None:
    # 1. Valid single word with VESUM forms
    cand1 = CandidateAlternative(term="порохотяг", is_phrase=False, vesum_forms_count=14)
    assert cand1.is_valid is True

    # 2. Invalid neologism with 0 VESUM forms and no heritage attestation
    cand2 = CandidateAlternative(term="вигаданеслово", is_phrase=False, vesum_forms_count=0, heritage_attested=False)
    assert cand2.is_valid is False

    # 3. Valid heritage-attested word even with 0 VESUM forms
    cand3 = CandidateAlternative(term="архаїзм", is_phrase=False, vesum_forms_count=0, heritage_attested=True)
    assert cand3.is_valid is True

    # 4. Valid multi-word phrase
    cand4 = CandidateAlternative(term="пилососна машина", is_phrase=True, vesum_forms_count=1)
    assert cand4.is_valid is True


def test_candidate_ranking_key() -> None:
    # High textbook hits beat everything
    cand_tb = CandidateAlternative(term="пилосмок", is_phrase=False, textbook_hits=5, vesum_forms_count=10)
    # Heritage attestation beats pure VESUM when textbook hits are 0
    cand_her = CandidateAlternative(
        term="порохосмок", is_phrase=False, textbook_hits=0, heritage_attested=True, vesum_forms_count=15
    )
    # Pure VESUM with 0 textbook hits
    cand_ves = CandidateAlternative(
        term="пилотяг", is_phrase=False, textbook_hits=0, heritage_attested=False, vesum_forms_count=14
    )

    ranked = sorted([cand_ves, cand_tb, cand_her], key=lambda c: c.ranking_key, reverse=True)
    assert ranked == [cand_tb, cand_her, cand_ves]


@pytest.fixture
def mock_dbs(tmp_path: Path) -> dict[str, Path]:
    # 1. Mock sources.db
    sources_db = tmp_path / "sources.db"
    s_conn = sqlite3.connect(sources_db)
    s_conn.execute("CREATE VIRTUAL TABLE textbooks_fts USING fts5(content);")
    s_conn.execute("INSERT INTO textbooks_fts (content) VALUES ('прибирання пилосмок у класі');")
    s_conn.execute("CREATE TABLE grinchenko (word TEXT);")
    s_conn.execute("INSERT INTO grinchenko (word) VALUES ('старовиннеслово');")
    s_conn.commit()
    s_conn.close()

    # 2. Mock atlas.db
    atlas_db = tmp_path / "atlas.db"
    a_conn = sqlite3.connect(atlas_db)
    a_conn.execute(
        "CREATE TABLE articles (slug TEXT PRIMARY KEY, lemma TEXT, heritage_classification TEXT, updated_at TEXT);"
    )
    a_conn.execute("CREATE TABLE article_payloads (slug TEXT PRIMARY KEY, payload_json TEXT);")
    a_conn.execute(
        "CREATE TABLE enrichment (slug TEXT NOT NULL, section TEXT NOT NULL, payload_json TEXT NOT NULL, source TEXT, filled_at TEXT, phase TEXT, UNIQUE (slug, section));"
    )

    # Seed atlas entries:
    # 'буран' (error lemma, Russianism)
    buran_payload = {
        "slug": "буран",
        "lemma": "буран",
        "sections": {
            "synonyms": {
                "items": ["вакуум", "буря"],  # 'вакуум' is an invalid synset to be pruned
                "source": "wordnet",
            }
        },
    }
    # 'заметіль' (authentic alternative present in Atlas)
    zamitil_payload = {
        "slug": "заметіль",
        "lemma": "заметіль",
        "sections": {
            "synonyms": {
                "items": ["віхола"],
            }
        },
    }
    # 'хуртовина' (authentic alternative present in Atlas)
    khurtovyna_payload = {
        "slug": "хуртовина",
        "lemma": "хуртовина",
        "sections": {
            "synonyms": {
                "items": ["хурделиця"],
            }
        },
    }

    a_conn.execute("INSERT INTO articles (slug, lemma) VALUES ('буран', 'буран');")
    a_conn.execute("INSERT INTO article_payloads VALUES ('буран', ?);", (json.dumps(buran_payload),))

    a_conn.execute("INSERT INTO articles (slug, lemma) VALUES ('заметіль', 'заметіль');")
    a_conn.execute("INSERT INTO article_payloads VALUES ('заметіль', ?);", (json.dumps(zamitil_payload),))

    a_conn.execute("INSERT INTO articles (slug, lemma) VALUES ('хуртовина', 'хуртовина');")
    a_conn.execute("INSERT INTO article_payloads VALUES ('хуртовина', ?);", (json.dumps(khurtovyna_payload),))

    a_conn.commit()
    a_conn.close()

    # 3. Mock lt_replacements.json
    lt_path = tmp_path / "lt_replacements.json"
    lt_data = {
        "буран": {
            "suggestions": ["заметіль", "хуртовина", "завірюха"]  # 'завірюха' is NOT in Atlas
        }
    }
    lt_path.write_text(json.dumps(lt_data), encoding="utf-8")

    # 4. Mock heritage_pairs.yaml
    heritage_path = tmp_path / "heritage_pairs.yaml"
    heritage_data = {"pairs": [{"error": "буран", "correct": "заметіль"}]}
    heritage_path.write_text(yaml.dump(heritage_data), encoding="utf-8")

    overlay_path = tmp_path / "heritage_overlay.yaml"
    overlay_path.write_text(yaml.dump({"pairs": []}), encoding="utf-8")

    return {
        "sources_db": sources_db,
        "atlas_db": atlas_db,
        "lt_path": lt_path,
        "heritage_pairs": heritage_path,
        "heritage_overlay": overlay_path,
    }


def test_reconciliation_dry_run_vs_apply(mock_dbs: dict[str, Path], monkeypatch: pytest.MonkeyPatch) -> None:
    # Mock verify_lemma so test does not depend on full 60MB vesum.db
    def mock_verify_lemma(lemma: str, db_path: Any = None) -> list[dict[str, Any]]:
        if lemma in {"заметіль", "хуртовина", "завірюха"}:
            return [{"lemma": lemma, "pos": "noun", "tags": "inanim:f:v_naz"}]
        return []

    monkeypatch.setattr("scripts.lexicon.reconcile_calque_clusters.verify_lemma", mock_verify_lemma)

    engine = CalqueReconciliationEngine(
        sources_db_path=mock_dbs["sources_db"],
        atlas_db_path=mock_dbs["atlas_db"],
        lt_path=mock_dbs["lt_path"],
        heritage_pairs_path=mock_dbs["heritage_pairs"],
        heritage_overlay_path=mock_dbs["heritage_overlay"],
    )

    # 1. Run DRY-RUN
    dry_results = engine.run_reconciliation(dry_run=True, single_lemma="буран")
    assert dry_results["total_candidates"] == 1
    assert dry_results["reconciled_entries"] == 1
    assert dry_results["skipped_up_to_date"] == 0
    assert dry_results["inflow_queued_count"] == 1  # 'завірюха' queued

    # Verify atlas.db was NOT changed during dry run
    conn = sqlite3.connect(mock_dbs["atlas_db"])
    row = conn.execute("SELECT payload_json FROM article_payloads WHERE slug = 'буран'").fetchone()
    payload = json.loads(row[0])
    assert payload.get("enrichment_version") is None
    conn.close()

    # 2. Run APPLY
    apply_results = engine.run_reconciliation(dry_run=False, single_lemma="буран")
    assert apply_results["reconciled_entries"] == 1

    # Verify atlas.db updates
    conn = sqlite3.connect(mock_dbs["atlas_db"])

    # Check 'буран' (Russianism)
    buran_row = conn.execute("SELECT payload_json FROM article_payloads WHERE slug = 'буран'").fetchone()
    buran_p = json.loads(buran_row[0])
    assert buran_p["enrichment_version"] == CURRENT_ENRICHMENT_VERSION
    assert buran_p["is_russianism"] is True
    assert buran_p["calque_warning"]["is_calque"] is True
    assert "заметіль" in buran_p["calque_warning"]["standard_alternatives"]
    assert "хуртовина" in buran_p["calque_warning"]["standard_alternatives"]
    assert "завірюха" in buran_p["calque_warning"]["standard_alternatives"]
    # Check invalid WordNet synset 'вакуум' was pruned
    assert "вакуум" not in buran_p["sections"]["synonyms"]["items"]
    # Check authentic in-atlas alternatives added to synonyms
    assert "заметіль" in buran_p["sections"]["synonyms"]["items"]
    assert "хуртовина" in buran_p["sections"]["synonyms"]["items"]

    # Check peer authentic entries: 'заметіль' and 'хуртовина'
    zamitil_row = conn.execute("SELECT payload_json FROM article_payloads WHERE slug = 'заметіль'").fetchone()
    zamitil_p = json.loads(zamitil_row[0])
    assert zamitil_p["enrichment_version"] == CURRENT_ENRICHMENT_VERSION
    # 'заметіль' should have 'хуртовина' as peer synonym
    assert "хуртовина" in zamitil_p["sections"]["synonyms"]["items"]
    # 'заметіль' must NOT have 'буран' (the Russianism) in synonyms!
    assert "буран" not in zamitil_p["sections"]["synonyms"]["items"]

    khurt_row = conn.execute("SELECT payload_json FROM article_payloads WHERE slug = 'хуртовина'").fetchone()
    khurt_p = json.loads(khurt_row[0])
    assert khurt_p["enrichment_version"] == CURRENT_ENRICHMENT_VERSION
    assert "заметіль" in khurt_p["sections"]["synonyms"]["items"]
    assert "буран" not in khurt_p["sections"]["synonyms"]["items"]

    # Check DB sync on articles and enrichment tables
    art_row = conn.execute("SELECT heritage_classification, updated_at FROM articles WHERE slug = 'буран'").fetchone()
    assert art_row[0] == "russianism"
    assert art_row[1] == buran_p["updated_at"]

    enr_hs = conn.execute("SELECT payload_json FROM enrichment WHERE slug = 'буран' AND section = 'heritage_status'").fetchone()
    assert enr_hs is not None
    hs_data = json.loads(enr_hs[0])
    assert hs_data["classification"] == "russianism"
    assert hs_data["warning_severity"] == "russianism_red"

    enr_syn = conn.execute("SELECT payload_json FROM enrichment WHERE slug = 'буран' AND section = 'synonyms'").fetchone()
    assert enr_syn is not None

    enr_peer = conn.execute("SELECT payload_json FROM enrichment WHERE slug = 'заметіль' AND section = 'synonyms'").fetchone()
    assert enr_peer is not None
    peer_data = json.loads(enr_peer[0])
    assert "хуртовина" in peer_data["items"]
    assert "буран" not in peer_data["items"]

    # Check inflow queue: 'завірюха' was queued because it's not in Atlas
    inflow = apply_results["inflow_queue"]
    assert len(inflow) == 1
    assert inflow[0]["lemma"] == "завірюха"
    assert inflow[0]["cluster_parent"] == "буран"
    assert inflow[0]["vesum_forms"] == 1

    conn.close()


def test_enrichment_versioning_skips_up_to_date(mock_dbs: dict[str, Path], monkeypatch: pytest.MonkeyPatch) -> None:
    def mock_verify_lemma(lemma: str, db_path: Any = None) -> list[dict[str, Any]]:
        return [{"lemma": lemma, "pos": "noun", "tags": "inanim:f:v_naz"}]

    monkeypatch.setattr("scripts.lexicon.reconcile_calque_clusters.verify_lemma", mock_verify_lemma)

    engine = CalqueReconciliationEngine(
        sources_db_path=mock_dbs["sources_db"],
        atlas_db_path=mock_dbs["atlas_db"],
        lt_path=mock_dbs["lt_path"],
        heritage_pairs_path=mock_dbs["heritage_pairs"],
        heritage_overlay_path=mock_dbs["heritage_overlay"],
    )

    # First pass: applies version 2
    engine.run_reconciliation(dry_run=False, single_lemma="буран")

    # Second pass without force: should be skipped
    res_skip = engine.run_reconciliation(dry_run=True, single_lemma="буран", force=False)
    assert res_skip["skipped_up_to_date"] == 1
    assert res_skip["reconciled_entries"] == 0

    # Third pass with force=True: re-processes entry
    res_force = engine.run_reconciliation(dry_run=True, single_lemma="буран", force=True)
    assert res_force["skipped_up_to_date"] == 0
    assert res_force["reconciled_entries"] == 1


def test_normalize_text() -> None:
    from scripts.lexicon.reconcile_calque_clusters import normalize_text

    assert normalize_text("«порохотяг»") == "порохотяг"
    assert normalize_text('"дармовис",') == "дармовис"
    assert normalize_text("  корабельня…  ") == "корабельня"
    assert normalize_text("добрий лад") == "добрий лад"


def test_phrase_candidates_and_inflow_queue_file(
    mock_dbs: dict[str, Path], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def mock_verify_lemma(lemma: str, db_path: Any = None) -> list[dict[str, Any]]:
        if lemma in {"заметіль", "хуртовина", "завірюха"}:
            return [{"lemma": lemma, "pos": "noun", "tags": "inanim:f:v_naz"}]
        return []

    monkeypatch.setattr("scripts.lexicon.reconcile_calque_clusters.verify_lemma", mock_verify_lemma)

    queue_out = tmp_path / "queue_out.json"

    engine = CalqueReconciliationEngine(
        sources_db_path=mock_dbs["sources_db"],
        atlas_db_path=mock_dbs["atlas_db"],
        lt_path=mock_dbs["lt_path"],
        heritage_pairs_path=mock_dbs["heritage_pairs"],
        heritage_overlay_path=mock_dbs["heritage_overlay"],
    )

    results = engine.run_reconciliation(dry_run=False, single_lemma="буран")
    assert results["inflow_queued_count"] == 1

    # Emulate queue writing in main
    with open(queue_out, "w", encoding="utf-8") as f:
        json.dump(results["inflow_queue"], f, ensure_ascii=False, indent=2)

    assert queue_out.exists()
    data = json.loads(queue_out.read_text(encoding="utf-8"))
    assert len(data) == 1
    assert data[0]["lemma"] == "завірюха"


def test_heritage_pairs_real_schema(tmp_path: Path) -> None:
    """Verify parser extracts from real production heritage_pairs.yaml schema."""
    real_schema_yaml = tmp_path / "heritage_real.yaml"
    content = {
        "pairs": [
            {
                "calqueLabel": "бажаючий",
                "nativeLemma": "охочий",
                "corrections": ["охочий"],
            },
            {
                "calqueLabel": "благополучний",
                "nativeLemma": "щасливий",
                "corrections": ["щасливий", "успішний"],
            },
            {
                "error": "старий_варіант",
                "correct": "новий_варіант",
            },
        ]
    }
    real_schema_yaml.write_text(yaml.dump(content), encoding="utf-8")

    dummy_file = tmp_path / "dummy.json"
    dummy_file.write_text("{}", encoding="utf-8")

    engine = CalqueReconciliationEngine(
        sources_db_path=tmp_path / "dummy.db",
        atlas_db_path=tmp_path / "dummy.db",
        lt_path=dummy_file,
        heritage_pairs_path=real_schema_yaml,
        heritage_overlay_path=tmp_path / "empty.yaml",
    )

    raw = engine.load_raw_replacements()
    assert "бажаючий" in raw
    assert raw["бажаючий"]["heritage_pairs"] == ["охочий"]

    assert "благополучний" in raw
    assert raw["благополучний"]["heritage_pairs"] == ["щасливий", "успішний"]

    assert "старий_варіант" in raw
    assert raw["старий_варіант"]["heritage_pairs"] == ["новий_варіант"]


def test_phrase_validation_clean_vs_garbage(mock_dbs: dict[str, Path], monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify phrase validation accepts authentic Ukrainian tokens and rejects garbage."""

    def mock_verify_lemma(lemma: str, db_path: Any = None) -> list[dict[str, Any]]:
        return []

    monkeypatch.setattr("scripts.lexicon.reconcile_calque_clusters.verify_lemma", mock_verify_lemma)

    engine = CalqueReconciliationEngine(
        sources_db_path=mock_dbs["sources_db"],
        atlas_db_path=mock_dbs["atlas_db"],
        lt_path=mock_dbs["lt_path"],
        heritage_pairs_path=mock_dbs["heritage_pairs"],
        heritage_overlay_path=mock_dbs["heritage_overlay"],
    )

    # Valid Ukrainian phrases
    valid_cand1 = engine.validate_candidate("добрий лад")
    assert valid_cand1.is_phrase is True
    assert valid_cand1.vesum_forms_count == 1
    assert valid_cand1.is_valid is True

    valid_cand2 = engine.validate_candidate("пилососна машина")
    assert valid_cand2.is_phrase is True
    assert valid_cand2.vesum_forms_count == 1
    assert valid_cand2.is_valid is True

    # Invalid phrases with digits / symbols / Latin
    garbage1 = engine.validate_candidate("пилосос 123$$$")
    assert garbage1.is_phrase is True
    assert garbage1.vesum_forms_count == 0
    assert garbage1.is_valid is False

    garbage2 = engine.validate_candidate("robot auto")
    assert garbage2.is_phrase is True
    assert garbage2.vesum_forms_count == 0
    assert garbage2.is_valid is False

    garbage3 = engine.validate_candidate("прилад-@!")
    assert garbage3.is_phrase is False  # single token with symbols
    assert garbage3.vesum_forms_count == 0
    assert garbage3.is_valid is False


def test_lexicalised_safe_and_polysemes_skipped(mock_dbs: dict[str, Path], monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify lexicalised adjectives and polysemes are skipped and never blanket-flagged."""

    def mock_verify_lemma(lemma: str, db_path: Any = None) -> list[dict[str, Any]]:
        return []

    monkeypatch.setattr("scripts.lexicon.reconcile_calque_clusters.verify_lemma", mock_verify_lemma)

    conn = sqlite3.connect(mock_dbs["atlas_db"])
    # Seed 'блискучий' (LEXICALISED_SAFE) and 'вірний' (SENSE_RESTRICTED_CALQUES)
    conn.execute("INSERT INTO articles (slug, lemma) VALUES ('блискучий', 'блискучий');")
    conn.execute(
        "INSERT INTO article_payloads VALUES ('блискучий', ?);",
        (json.dumps({"slug": "блискучий", "lemma": "блискучий", "sections": {}}),),
    )
    conn.execute("INSERT INTO articles (slug, lemma) VALUES ('вірний', 'вірний');")
    conn.execute(
        "INSERT INTO article_payloads VALUES ('вірний', ?);",
        (json.dumps({"slug": "вірний", "lemma": "вірний", "sections": {}}),),
    )
    conn.commit()
    conn.close()

    # Add lt_replacements for them
    lt_data = {
        "блискучий": {"suggestions": ["яскравіший"]},
        "вірний": {"suggestions": ["правильний"]},
    }
    mock_dbs["lt_path"].write_text(json.dumps(lt_data), encoding="utf-8")

    engine = CalqueReconciliationEngine(
        sources_db_path=mock_dbs["sources_db"],
        atlas_db_path=mock_dbs["atlas_db"],
        lt_path=mock_dbs["lt_path"],
        heritage_pairs_path=mock_dbs["heritage_pairs"],
        heritage_overlay_path=mock_dbs["heritage_overlay"],
    )

    res = engine.run_reconciliation(dry_run=False)
    # Neither should be modified
    assert "блискучий" not in res["entries"]
    assert "вірний" not in res["entries"]

    conn = sqlite3.connect(mock_dbs["atlas_db"])
    row = conn.execute("SELECT payload_json FROM article_payloads WHERE slug = 'блискучий'").fetchone()
    assert "is_russianism" not in json.loads(row[0])
    row_v = conn.execute("SELECT payload_json FROM article_payloads WHERE slug = 'вірний'").fetchone()
    assert "is_russianism" not in json.loads(row_v[0])
    conn.close()


def test_severity_classification_curated_vs_pure_lt(mock_dbs: dict[str, Path], monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify curated calques get red severity while pure LT replacements get orange."""

    def mock_verify_lemma(lemma: str, db_path: Any = None) -> list[dict[str, Any]]:
        return [{"lemma": lemma, "pos": "noun", "tags": "inanim:f:v_naz"}]

    monkeypatch.setattr("scripts.lexicon.reconcile_calque_clusters.verify_lemma", mock_verify_lemma)

    conn = sqlite3.connect(mock_dbs["atlas_db"])
    # 1. Pure LT replacement: 'антипаста' -> 'антипасто'
    conn.execute("INSERT INTO articles (slug, lemma) VALUES ('антипаста', 'антипаста');")
    conn.execute(
        "INSERT INTO article_payloads VALUES ('антипаста', ?);",
        (json.dumps({"slug": "антипаста", "lemma": "антипаста", "sections": {}}),),
    )
    # 2. Curated calque via heritage_pairs: 'бажаючий' -> 'охочий'
    conn.execute("INSERT INTO articles (slug, lemma) VALUES ('бажаючий', 'бажаючий');")
    conn.execute(
        "INSERT INTO article_payloads VALUES ('бажаючий', ?);",
        (json.dumps({"slug": "бажаючий", "lemma": "бажаючий", "sections": {}}),),
    )
    # 3. Curated convergence calque via heritage_pairs: 'мисль' -> 'думка'
    conn.execute("INSERT INTO articles (slug, lemma) VALUES ('мисль', 'мисль');")
    conn.execute(
        "INSERT INTO article_payloads VALUES ('мисль', ?);",
        (json.dumps({"slug": "мисль", "lemma": "мисль", "sections": {}}),),
    )
    conn.commit()
    conn.close()

    # Seed lt_replacements
    lt_data = {
        "антипаста": {"suggestions": ["антипасто"]},
        "бажаючий": {"suggestions": ["охочий"]},
        "мисль": {"suggestions": ["думка"]},
    }
    mock_dbs["lt_path"].write_text(json.dumps(lt_data), encoding="utf-8")

    # Seed heritage_pairs with бажаючий and мисль
    heritage_data = {
        "pairs": [
            {
                "calqueLabel": "бажаючий",
                "nativeLemma": "охочий",
                "corrections": ["охочий"],
            },
            {
                "calqueLabel": "мисль",
                "nativeLemma": "думка",
                "corrections": ["думка"],
                "kind": "lexical",
                "severity": "calque_yellow",
                "note": "У сучасній стандартній українській мові нейтральним відповідником є «думка».",
                "noteUk": "У сучасній українській літературній мові нормативним і нейтральним відповідником є «думка».",
            },
        ]
    }
    mock_dbs["heritage_pairs"].write_text(yaml.dump(heritage_data), encoding="utf-8")

    engine = CalqueReconciliationEngine(
        sources_db_path=mock_dbs["sources_db"],
        atlas_db_path=mock_dbs["atlas_db"],
        lt_path=mock_dbs["lt_path"],
        heritage_pairs_path=mock_dbs["heritage_pairs"],
        heritage_overlay_path=mock_dbs["heritage_overlay"],
    )

    engine.run_reconciliation(dry_run=False, single_lemma="антипаста")
    engine.run_reconciliation(dry_run=False, single_lemma="бажаючий")
    engine.run_reconciliation(dry_run=False, single_lemma="мисль")

    conn = sqlite3.connect(mock_dbs["atlas_db"])

    # 'антипаста' (pure LT): orange severity, is_russianism = False, warning_severity = calque_yellow
    row_lt = conn.execute("SELECT payload_json FROM article_payloads WHERE slug = 'антипаста'").fetchone()
    p_lt = json.loads(row_lt[0])
    assert p_lt["is_russianism"] is False
    assert p_lt["calque_warning"]["severity"] == "orange"
    assert p_lt["heritage_status"]["warning_severity"] == "calque_yellow"
    assert "Нерекомендоване або ненормативне слововживання" in p_lt["calque_warning"]["warning_text"]

    row_art_lt = conn.execute("SELECT heritage_classification FROM articles WHERE slug = 'антипаста'").fetchone()
    assert row_art_lt[0] == "calque"

    # 'бажаючий' (curated calque): red severity, is_russianism = True, warning_severity = russianism_red
    row_her = conn.execute("SELECT payload_json FROM article_payloads WHERE slug = 'бажаючий'").fetchone()
    p_her = json.loads(row_her[0])
    assert p_her["is_russianism"] is True
    assert p_her["calque_warning"]["severity"] == "red"
    assert p_her["heritage_status"]["warning_severity"] == "russianism_red"
    assert "Калька / росіянізм" in p_her["calque_warning"]["warning_text"]

    row_art_her = conn.execute("SELECT heritage_classification FROM articles WHERE slug = 'бажаючий'").fetchone()
    assert row_art_her[0] == "russianism"

    # 'мисль' (curated convergence calque): orange severity, is_russianism = False, warning_severity = calque_yellow
    row_mysl = conn.execute("SELECT payload_json FROM article_payloads WHERE slug = 'мисль'").fetchone()
    p_mysl = json.loads(row_mysl[0])
    assert p_mysl["is_russianism"] is False
    assert p_mysl["calque_warning"]["severity"] == "orange"
    assert p_mysl["heritage_status"]["warning_severity"] == "calque_yellow"
    assert p_mysl["heritage_status"]["classification"] == "calque"
    assert "думка" in p_mysl["calque_warning"]["standard_alternatives"]
    assert "думка" in p_mysl["calque_warning"]["warning_text"]
    assert p_mysl["calque_warning"].get("noteUk") is not None

    row_art_mysl = conn.execute("SELECT heritage_classification FROM articles WHERE slug = 'мисль'").fetchone()
    assert row_art_mysl[0] == "calque"

    conn.close()


def test_fts5_hyphenated_lemma(mock_dbs: dict[str, Path], monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify candidate validation handles hyphenated compound words safely in FTS5."""

    def mock_verify_lemma(lemma: str, db_path: Any = None) -> list[dict[str, Any]]:
        return [{"lemma": lemma, "pos": "adj", "tags": "m:v_naz"}]

    monkeypatch.setattr("scripts.lexicon.reconcile_calque_clusters.verify_lemma", mock_verify_lemma)

    # Seed a row with hyphenated word in textbooks_fts to test match hit count
    s_conn = sqlite3.connect(mock_dbs["sources_db"])
    s_conn.execute("INSERT INTO textbooks_fts (content) VALUES ('підручник з алма-атинський край');")
    s_conn.commit()
    s_conn.close()

    engine = CalqueReconciliationEngine(
        sources_db_path=mock_dbs["sources_db"],
        atlas_db_path=mock_dbs["atlas_db"],
        lt_path=mock_dbs["lt_path"],
        heritage_pairs_path=mock_dbs["heritage_pairs"],
        heritage_overlay_path=mock_dbs["heritage_overlay"],
    )

    # Should not raise OperationalError and safely match hyphenated term in FTS5
    cand = engine.validate_candidate("алма-атинський")
    assert cand.term == "алма-атинський"
    assert cand.is_phrase is False
    assert cand.is_valid is True
    assert cand.textbook_hits == 1


def test_peer_synonyms_exclude_russianisms_in_atlas(mock_dbs: dict[str, Path], monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify that alternatives flagged as Russianisms in Atlas are excluded from peer synonyms."""

    def mock_verify_lemma(lemma: str, db_path: Any = None) -> list[dict[str, Any]]:
        return [{"lemma": lemma, "pos": "noun", "tags": "inanim:m:v_naz"}]

    monkeypatch.setattr("scripts.lexicon.reconcile_calque_clusters.verify_lemma", mock_verify_lemma)

    conn = sqlite3.connect(mock_dbs["atlas_db"])
    # Error lemma: 'тест_помилка'
    # Alt 1: 'автентичне_слово'
    # Alt 2: 'інший_росіянізм' (already flagged as is_russianism: true in Atlas)
    conn.execute("INSERT INTO articles (slug, lemma) VALUES ('тест_помилка', 'тест_помилка');")
    conn.execute(
        "INSERT INTO article_payloads VALUES ('тест_помилка', ?);",
        (json.dumps({"slug": "тест_помилка", "lemma": "тест_помилка", "sections": {}}),),
    )
    conn.execute("INSERT INTO articles (slug, lemma) VALUES ('автентичне_слово', 'автентичне_слово');")
    conn.execute(
        "INSERT INTO article_payloads VALUES ('автентичне_слово', ?);",
        (
            json.dumps(
                {"slug": "автентичне_слово", "lemma": "автентичне_слово", "sections": {"synonyms": {"items": []}}}
            ),
        ),
    )
    conn.execute("INSERT INTO articles (slug, lemma) VALUES ('інший_росіянізм', 'інший_росіянізм');")
    conn.execute(
        "INSERT INTO article_payloads VALUES ('інший_росіянізм', ?);",
        (json.dumps({"slug": "інший_росіянізм", "lemma": "інший_росіянізм", "is_russianism": True, "sections": {}}),),
    )
    conn.commit()
    conn.close()

    lt_data = {"тест_помилка": {"suggestions": ["автентичне_слово", "інший_росіянізм"]}}
    mock_dbs["lt_path"].write_text(json.dumps(lt_data), encoding="utf-8")

    engine = CalqueReconciliationEngine(
        sources_db_path=mock_dbs["sources_db"],
        atlas_db_path=mock_dbs["atlas_db"],
        lt_path=mock_dbs["lt_path"],
        heritage_pairs_path=mock_dbs["heritage_pairs"],
        heritage_overlay_path=mock_dbs["heritage_overlay"],
    )

    engine.run_reconciliation(dry_run=False, single_lemma="тест_помилка")

    conn = sqlite3.connect(mock_dbs["atlas_db"])
    row = conn.execute("SELECT payload_json FROM article_payloads WHERE slug = 'автентичне_слово'").fetchone()
    p = json.loads(row[0])
    # 'інший_росіянізм' must NOT leak into 'автентичне_слово' peer synonyms
    assert "інший_росіянізм" not in p["sections"]["synonyms"]["items"]
    # And 'тест_помилка' must also not be there
    assert "тест_помилка" not in p["sections"]["synonyms"]["items"]
    conn.close()


def test_warning_text_refresh_on_force(mock_dbs: dict[str, Path], monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify warning_text is refreshed dynamically on --force reprocessing."""

    def mock_verify_lemma(lemma: str, db_path: Any = None) -> list[dict[str, Any]]:
        return [{"lemma": lemma, "pos": "noun", "tags": "inanim:m:v_naz"}]

    monkeypatch.setattr("scripts.lexicon.reconcile_calque_clusters.verify_lemma", mock_verify_lemma)

    conn = sqlite3.connect(mock_dbs["atlas_db"])
    stale_payload = {
        "slug": "старий_запис",
        "lemma": "старий_запис",
        "is_russianism": True,
        "enrichment_version": 2,
        "calque_warning": {
            "is_calque": True,
            "severity": "red",
            "standard_alternatives": ["стара_альтернатива"],
            "warning_text": "Застарілий текст попередження",
        },
        "sections": {},
    }
    conn.execute("INSERT INTO articles (slug, lemma) VALUES ('старий_запис', 'старий_запис');")
    conn.execute(
        "INSERT INTO article_payloads VALUES ('старий_запис', ?);",
        (json.dumps(stale_payload),),
    )
    conn.commit()
    conn.close()

    lt_data = {"старий_запис": {"suggestions": ["нова_альтернатива"]}}
    mock_dbs["lt_path"].write_text(json.dumps(lt_data), encoding="utf-8")

    heritage_data = {
        "pairs": [
            {
                "calqueLabel": "старий_запис",
                "corrections": ["нова_альтернатива"],
            }
        ]
    }
    mock_dbs["heritage_pairs"].write_text(yaml.dump(heritage_data), encoding="utf-8")

    engine = CalqueReconciliationEngine(
        sources_db_path=mock_dbs["sources_db"],
        atlas_db_path=mock_dbs["atlas_db"],
        lt_path=mock_dbs["lt_path"],
        heritage_pairs_path=mock_dbs["heritage_pairs"],
        heritage_overlay_path=mock_dbs["heritage_overlay"],
    )

    # Run with force=True
    engine.run_reconciliation(dry_run=False, single_lemma="старий_запис", force=True)

    conn = sqlite3.connect(mock_dbs["atlas_db"])
    row = conn.execute("SELECT payload_json FROM article_payloads WHERE slug = 'старий_запис'").fetchone()
    p = json.loads(row[0])
    assert p["calque_warning"]["warning_text"] != "Застарілий текст попередження"
    assert "нова_альтернатива" in p["calque_warning"]["warning_text"]
    conn.close()


def test_manifest_sync_in_place(mock_dbs: dict[str, Path], tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def mock_verify_lemma(lemma: str, db_path: Any = None) -> list[dict[str, Any]]:
        if lemma in {"заметіль", "хуртовина", "завірюха"}:
            return [{"lemma": lemma, "pos": "noun", "tags": "inanim:f:v_naz"}]
        return []

    monkeypatch.setattr("scripts.lexicon.reconcile_calque_clusters.verify_lemma", mock_verify_lemma)

    manifest_file = tmp_path / "mock-lexicon-manifest.json"
    manifest_content = {
        "entries": [
            {
                "url_slug": "буран",
                "lemma": "буран",
                "sections": {"synonyms": {"items": ["вакуум", "буря"]}},
            },
            {
                "url_slug": "заметіль",
                "lemma": "заметіль",
                "sections": {"synonyms": {"items": ["віхола"]}},
            },
        ]
    }
    manifest_file.write_text(json.dumps(manifest_content, ensure_ascii=False), encoding="utf-8")

    engine = CalqueReconciliationEngine(
        sources_db_path=mock_dbs["sources_db"],
        atlas_db_path=mock_dbs["atlas_db"],
        lt_path=mock_dbs["lt_path"],
        heritage_pairs_path=mock_dbs["heritage_pairs"],
        heritage_overlay_path=mock_dbs["heritage_overlay"],
        manifest_path=manifest_file,
    )

    # 1. Dry run: manifest file should not change
    engine.run_reconciliation(dry_run=True, single_lemma="буран")
    unchanged_data = json.loads(manifest_file.read_text(encoding="utf-8"))
    assert unchanged_data["entries"][0].get("enrichment_version") is None

    # 2. Apply run: manifest file is updated in place
    engine.run_reconciliation(dry_run=False, single_lemma="буран")
    updated_data = json.loads(manifest_file.read_text(encoding="utf-8"))

    buran_entry = updated_data["entries"][0]
    assert buran_entry["enrichment_version"] == CURRENT_ENRICHMENT_VERSION
    assert buran_entry["is_russianism"] is True
    assert buran_entry["heritage_status"]["is_russianism"] is True
    assert buran_entry["heritage_status"]["warning_severity"] == "russianism_red"
    assert "заметіль" in buran_entry["calque_warning"]["standard_alternatives"]
    assert "вакуум" not in buran_entry["sections"]["synonyms"]["items"]
    assert "заметіль" in buran_entry["sections"]["synonyms"]["items"]

    zamitil_entry = updated_data["entries"][1]
    assert zamitil_entry["enrichment_version"] == CURRENT_ENRICHMENT_VERSION
    assert "хуртовина" in zamitil_entry["sections"]["synonyms"]["items"]
    assert "буран" not in zamitil_entry["sections"]["synonyms"]["items"]

    # Verify DB sync alongside manifest sync
    conn = sqlite3.connect(mock_dbs["atlas_db"])
    art_row = conn.execute("SELECT heritage_classification FROM articles WHERE slug = 'буран'").fetchone()
    assert art_row[0] == "russianism"
    enr_rows = conn.execute("SELECT section FROM enrichment WHERE slug = 'буран' ORDER BY section").fetchall()
    assert [r[0] for r in enr_rows] == ["heritage_status", "synonyms"]
    conn.close()
