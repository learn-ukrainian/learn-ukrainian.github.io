"""Tests for the Atlas manifest verify-before-promote gate (#M-11)."""

from __future__ import annotations

import json
from pathlib import Path

from scripts.lexicon import verify_manifest


def _write(tmp_path: Path, entries: list[dict], **top) -> Path:
    p = tmp_path / "manifest.json"
    p.write_text(json.dumps({"entries": entries, **top}, ensure_ascii=False), encoding="utf-8")
    return p


def test_clean_manifest_passes(tmp_path, capsys):
    entries = [
        {"lemma": "шлях", "sections": {"synonyms": {"items": ["дорога", "кам'яниця"]}},
         "enrichment": {"etymology": {"text": "x"}}, "wiki_reference": {"wikipedia": {}}},
        {"lemma": "гарний", "sections": {"synonyms": {"items": ["красивий"]}}},
    ]
    rc = verify_manifest.run(_write(tmp_path, entries), sample=0, baseline_path=None)
    out = capsys.readouterr().out
    assert rc == 0
    assert "no structural hazards" in out
    # dialectal synonym must NOT be flagged (the кам'яниця lesson)
    assert "кам'яниця" not in out or "HAZARD" not in out


def test_junk_synonym_is_a_hazard(tmp_path, capsys):
    entries = [{"lemma": "варити", "sections": {"synonyms": {"items": ["готувати", "фальсифікувати"]}}}]
    rc = verify_manifest.run(_write(tmp_path, entries), sample=0, baseline_path=None)
    out = capsys.readouterr().out
    assert rc == 2
    assert "HAZARD" in out
    assert "фальсифікувати" in out


def test_html_entity_leak_is_a_hazard(tmp_path, capsys):
    entries = [{"lemma": "тест", "gloss": "a &amp; b"}]
    rc = verify_manifest.run(_write(tmp_path, entries), sample=0, baseline_path=None)
    assert rc == 2
    assert "amp" in capsys.readouterr().out


def test_gloss_chunk_leak_is_a_hazard(tmp_path, capsys):
    entries = [{"lemma": "тест", "gloss": "leaked from 7-klas-ukrmova_s0108"}]
    rc = verify_manifest.run(_write(tmp_path, entries), sample=0, baseline_path=None)
    assert rc == 2


def test_empty_section_is_a_hazard(tmp_path, capsys):
    entries = [{"lemma": "тест", "sections": {"synonyms": {"items": []}}}]
    rc = verify_manifest.run(_write(tmp_path, entries), sample=0, baseline_path=None)
    assert rc == 2
    assert "empty_sections" in capsys.readouterr().out


def test_coverage_and_baseline_delta(tmp_path, capsys):
    base = _write(tmp_path, [{"lemma": "a"}, {"lemma": "b"}])
    cur_entries = [
        {"lemma": "a", "sections": {"synonyms": {"items": ["x"]}}},
        {"lemma": "b"},
    ]
    cur = tmp_path / "cur.json"
    cur.write_text(json.dumps({"entries": cur_entries}, ensure_ascii=False), encoding="utf-8")
    rc = verify_manifest.run(cur, sample=0, baseline_path=base)
    out = capsys.readouterr().out
    assert rc == 0
    assert "synonyms" in out
    assert "was 0" in out  # baseline delta shown


def test_dialectal_synonym_not_in_junk_list():
    # Regression guard for the блискучий/кам'яниця lesson: authoritative dialectal
    # terms must never be hardcoded as junk.
    for term in ("кам'яниця", "звір", "гостинець", "путівець", "вуйко"):
        assert term not in verify_manifest.JUNK_SYNONYMS
