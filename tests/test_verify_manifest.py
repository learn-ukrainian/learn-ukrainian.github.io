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
    assert "clean (eyeball the sample" in out
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


# --- §8 conformance wiring (autopsy follow-up to #3124) ---------------------
# The structural hazard scan alone is necessary but NOT sufficient: it gave a
# false-clean on the re-enrich whose kaikki suffix turned test_atlas_conformance
# RED on main. verify_manifest now runs the SAME validate() the required CI test
# runs. These tests use nonexistent curriculum/vesum paths so the suite stays
# hermetic (no 967MB vesum.db, no curriculum.yaml dependency).

_NO_DEPS = {"curriculum_path": Path("/nonexistent/none.yaml"), "vesum_path": Path("/nonexistent/none.db")}


def test_conformance_off_by_default_is_structural_only(tmp_path, capsys):
    # Synonyms-with-items-but-no-source passes the structural scan but WOULD trip
    # the §8 provenance gate. Default run_conformance=False keeps the old contract.
    entries = [{"lemma": "слово", "sections": {"synonyms": {"items": ["мова"]}}}]
    rc = verify_manifest.run(_write(tmp_path, entries), sample=0, baseline_path=None)
    out = capsys.readouterr().out
    assert rc == 0
    assert "CONFORMANCE" not in out


def test_conformance_flags_provenance_violation_structural_misses(tmp_path, capsys):
    entries = [{"lemma": "слово", "sections": {"synonyms": {"items": ["мова"]}}}]
    rc = verify_manifest.run(
        _write(tmp_path, entries), sample=0, baseline_path=None, run_conformance=True, **_NO_DEPS
    )
    out = capsys.readouterr().out
    assert rc == 2
    assert "CONFORMANCE" in out
    assert "do NOT commit" in out
    assert "conformance violation" in out


def test_conformance_clean_entry_passes(tmp_path, capsys):
    rc = verify_manifest.run(
        _write(tmp_path, [{"lemma": "слово"}]), sample=0, baseline_path=None, run_conformance=True, **_NO_DEPS
    )
    out = capsys.readouterr().out
    assert rc == 0
    assert "CLEAN — 0 violations" in out
    assert "lemma_in_vesum skipped" in out


# --- #5077 shrink gate ------------------------------------------------------
# The NONEMPTY->EMPTY hazard catches fully-stripped sections but MISSES partial
# shrinks (1,748 on the 2026-07-13 go-live). The shrink gate flags per-section
# item-count regressions vs the hydrated baseline, exempting retractions justified
# by gate-ran provenance or the curated allowlist.


def _write_named(path: Path, entries: list[dict]) -> Path:
    path.write_text(json.dumps({"entries": entries}, ensure_ascii=False), encoding="utf-8")
    return path


def _ключ_manifests(tmp_path: Path, *, cur_entry: dict) -> tuple[Path, Path]:
    base = _write_named(
        tmp_path / "base.json",
        [{"lemma": "ключ", "sections": {"synonyms": {"items": ["джерело", "живець", "замок"], "source": "s"}}}],
    )
    cur = _write_named(tmp_path / "cur.json", [cur_entry])
    return base, cur


def test_shrink_gate_catches_unexplained_regression(tmp_path, capsys):
    base, cur = _ключ_manifests(
        tmp_path,
        cur_entry={"lemma": "ключ", "sections": {"synonyms": {"items": ["замок"], "source": "s"}}},
    )
    rc = verify_manifest.run(cur, sample=0, baseline_path=base)
    out = capsys.readouterr().out
    assert rc == 2
    assert "SHRINK GATE" in out
    assert "unexplained section shrink" in out
    assert "ключ" in out


def test_shrink_gate_flags_vanished_section(tmp_path, capsys):
    base, cur = _ключ_manifests(tmp_path, cur_entry={"lemma": "ключ"})  # synonyms gone entirely
    rc = verify_manifest.run(cur, sample=0, baseline_path=base)
    out = capsys.readouterr().out
    assert rc == 2
    assert "3 -> 0" in out


def test_shrink_gate_allows_allowlisted_retraction(tmp_path, capsys):
    base, cur = _ключ_manifests(
        tmp_path,
        cur_entry={"lemma": "ключ", "sections": {"synonyms": {"items": ["замок"], "source": "s"}}},
    )
    allowlist = tmp_path / "allow.yaml"
    allowlist.write_text(
        "version: 1\nkind: atlas_shrink_allowlist\n"
        "retractions:\n  - lemma: ключ\n    section: synonyms\n    reason: WordNet junk\n",
        encoding="utf-8",
    )
    rc = verify_manifest.run(cur, sample=0, baseline_path=base, shrink_allowlist_path=allowlist)
    out = capsys.readouterr().out
    assert rc == 0
    assert "no unexplained section shrink" in out


def test_shrink_gate_allows_gate_ran_rejection_via_provenance(tmp_path, capsys):
    base, cur = _ключ_manifests(
        tmp_path,
        cur_entry={
            "lemma": "ключ",
            "sections": {"synonyms": {"items": ["замок"], "source": "s"}},
            "gate_provenance": {"synonyms": "rejected"},
        },
    )
    rc = verify_manifest.run(cur, sample=0, baseline_path=base)
    out = capsys.readouterr().out
    assert rc == 0
    assert "no unexplained section shrink" in out


def test_shrink_gate_ignores_growth_and_equal(tmp_path, capsys):
    base, cur = _ключ_manifests(
        tmp_path,
        cur_entry={
            "lemma": "ключ",
            "sections": {"synonyms": {"items": ["джерело", "живець", "замок", "шифр"], "source": "s"}},
        },
    )
    rc = verify_manifest.run(cur, sample=0, baseline_path=base)
    out = capsys.readouterr().out
    assert rc == 0
    assert "no unexplained section shrink" in out


def test_shrink_gate_off_without_baseline(tmp_path, capsys):
    cur = _write_named(
        tmp_path / "cur.json",
        [{"lemma": "ключ", "sections": {"synonyms": {"items": ["замок"], "source": "s"}}}],
    )
    rc = verify_manifest.run(cur, sample=0, baseline_path=None)
    out = capsys.readouterr().out
    assert rc == 0
    assert "SHRINK GATE" not in out  # no baseline -> gate cannot run, stays silent
