"""Synthetic regression test for empty canonical_headword in evidence/words.py (#8431)."""

from __future__ import annotations

import sqlite3

import yaml

from scripts.curriculum.evidence import sources, words


def test_empty_canonical_headword_falls_back_to_lemma(synthetic_vesum, synthetic_sources, tmp_path):
    """When a ULIF entry has empty canonical_headword (""), words.py falls back to lemma."""
    # Set up synthetic_vesum with a single entry for lemma 'тест'
    with sqlite3.connect(synthetic_vesum) as conn:
        conn.execute("DELETE FROM forms_all")
        conn.execute(
            "INSERT INTO forms_all VALUES (1, 100, 'тест', 'тест', 'noun', 'noun:inanim:m:v_naz', '', 'src:1')"
        )

    # Insert a ULIF entry with empty canonical_headword
    with sqlite3.connect(synthetic_sources) as conn:
        conn.execute(
            """INSERT INTO ulif_dictua_entries
            (id, normalized_query, homonym_index, canonical_headword, grammatical_label, sense_gloss, homonym_checked, status, retrieved_at)
            VALUES (1, 'тест', 1, '', 'ч', 'перевірка', 1, 'present', '2026-01-01')"""
        )

    req_path = tmp_path / "req.yaml"
    req_path.write_text(
        yaml.safe_dump(
            {
                "request_schema": 1,
                "level": "a1",
                "words": [
                    {
                        "lemma": "тест",
                        "pos": "noun",
                        "want": "new",
                        "entry": {"source": "ulif", "homonym_index": 1},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    with sources.Sources(sources_db=synthetic_sources, vesum_db=synthetic_vesum) as api:
        res = words.build_words(
            "a1",
            req_path,
            evidence_dir=tmp_path,
            sources_instance=api,
            dry_run=True,
        )

    word_record = res["store"]["words"][0]
    # Verify entry key fell back to lemma "тест" rather than empty string ""
    assert word_record["entry"]["source"] == "ulif"
    assert word_record["entry"]["key"][0] == "тест", f"Expected 'тест', got {word_record['entry']['key'][0]!r}"
    assert word_record["ulif"]["key"][0] == "тест", f"Expected 'тест', got {word_record['ulif']['key'][0]!r}"
