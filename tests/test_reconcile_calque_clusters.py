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
    a_conn.execute("CREATE TABLE articles (slug TEXT PRIMARY KEY, lemma TEXT);")
    a_conn.execute("CREATE TABLE article_payloads (slug TEXT PRIMARY KEY, payload_json TEXT);")

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

    a_conn.execute("INSERT INTO articles VALUES ('буран', 'буран');")
    a_conn.execute("INSERT INTO article_payloads VALUES ('буран', ?);", (json.dumps(buran_payload),))

    a_conn.execute("INSERT INTO articles VALUES ('заметіль', 'заметіль');")
    a_conn.execute("INSERT INTO article_payloads VALUES ('заметіль', ?);", (json.dumps(zamitil_payload),))

    a_conn.execute("INSERT INTO articles VALUES ('хуртовина', 'хуртовина');")
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
