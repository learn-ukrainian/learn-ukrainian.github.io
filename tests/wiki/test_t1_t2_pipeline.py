from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.reads_content

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from wiki import sources_db
from wiki.query_builder import build_query_buckets

DISCOVERY_PATH = (
    Path(__file__).resolve().parents[2]
    / "curriculum"
    / "l2-uk-en"
    / "a1-v1"
    / "discovery"
    / "sounds-letters-and-hello.yaml"
)

CONCEPT_PATTERNS = {
    "milozvuchnist": r"милозвучн",
    "hard_soft": r"тверд|м['’]як",
    "stress": r"наголос",
    "alternation": r"чергуван",
    "apostrophe": r"апостроф",
    "vowel_consonant_definition": r"голосні звуки утворюються|приголосні звуки утворюються|голос і шум",
    "yi_letter_two_sounds": r"буква ї|два звуки|\[йі\]",
    "syllable_rule": r"склад(ів|и)|скільки голосних",
    "alphabet_count": r"33 букв|33 літер|38 зву",
    "g_history": r"літеру ґ|букв[аи] ґ",
    "iotated": r"букви я, ю, є|я, ю, є",
}


def test_t1_t2_pipeline_surfaces_section_level_a1_evidence(monkeypatch, requires_sources_db):
    # build_query_buckets tolerates a missing discovery file, so a moved
    # fixture would otherwise degrade silently into a weaker query.
    assert DISCOVERY_PATH.is_file(), DISCOVERY_PATH
    bucket_a, bucket_b = build_query_buckets(DISCOVERY_PATH, "a1")
    assert bucket_a
    assert bucket_b

    def fake_rerank(_query: str, sections: list[dict], limit: int = 10) -> list[dict]:
        def concept_score(section: dict) -> tuple[int, int]:
            text = section.get("full_text", "").lower()
            hits = sum(
                1 for pattern in CONCEPT_PATTERNS.values()
                if re.search(pattern, text)
            )
            return hits, int(section.get("section_score", 0))

        ranked = sorted(sections, key=concept_score, reverse=True)
        return ranked[:limit]

    monkeypatch.setattr(sources_db, "rerank_sections", fake_rerank)

    sections = sources_db.search_sources(
        DISCOVERY_PATH,
        track="a1",
        strategy="modern_dense_section",
        limit=10,
    )

    assert len(sections) >= 5
    assert all(section.get("full_text") for section in sections)
    textbook_sections = [section for section in sections if section.get("corpus") == "textbook_sections"]
    assert textbook_sections
    # #1340 (2026-04-20): grade filter removed — CEFR L2 levels do not
    # map onto Ukrainian L1 school grades, and dense rerank handles
    # topic relevance natively. We no longer assert a grade ceiling on
    # retrieved sections; instead we assert that the concept-coverage
    # check below stays satisfied (the real outcome we care about).
    assert all(section.get("grade") is not None for section in textbook_sections), \
        "every textbook section row should still carry a grade (metadata only, no longer a gate)"

    corpus = "\n\n".join(section["full_text"] for section in sections).lower()
    matched = [
        name for name, pattern in CONCEPT_PATTERNS.items()
        if re.search(pattern, corpus)
    ]
    assert len(matched) >= 5, matched


def _keyword_unit(corpus: str, index: int, fts_score: float) -> dict:
    return {
        "corpus": corpus,
        "unit_key": f"{corpus}:{index}",
        "full_text": f"{corpus} unit {index}",
        "fts_score": fts_score,
        "dense_score": 0.0,
        "final_score": 0.0,
    }


@pytest.mark.parametrize("textbook_rank", [0, 7, 12, 40])
def test_modern_dense_section_returns_a_textbook_section_within_limit(monkeypatch, textbook_rank):
    # Keyword-only search scores every unit 0.0, so a textbook section can sort
    # behind `limit` other units; the returned slice must still carry one.
    units = [_keyword_unit("ukrainian_wiki", index, float(index)) for index in range(40)]
    units.insert(textbook_rank, _keyword_unit("textbook_sections", 0, float(textbook_rank) - 0.5))

    def dispatch(corpus: str, **_kwargs) -> list[dict]:
        return [unit for unit in units if unit["corpus"] == corpus]

    monkeypatch.setattr(sources_db, "_prepare_query", lambda query, track: (["q"], {"q"}, "q"))
    monkeypatch.setattr(sources_db, "_dispatch_corpus_search", dispatch)
    monkeypatch.setattr(sources_db, "_expand_neighbor_context", lambda match: match)

    results = sources_db.search_sources("q", track="a1", strategy="modern_dense_section", limit=10)

    assert len(results) == 10
    assert [unit["unit_key"] for unit in results].count("textbook_sections:0") == 1
    ranked = sorted(units, key=lambda unit: unit["fts_score"])
    if textbook_rank < 10:
        assert [unit["unit_key"] for unit in results] == [unit["unit_key"] for unit in ranked[:10]]
    else:
        assert results[0]["unit_key"] == "textbook_sections:0"
        assert [unit["unit_key"] for unit in results[1:]] == [unit["unit_key"] for unit in ranked[:9]]


def test_unified_dense_does_not_force_a_textbook_section(monkeypatch):
    units = [_keyword_unit("ukrainian_wiki", index, float(index)) for index in range(20)]
    units.append(_keyword_unit("textbook_sections", 0, 99.0))

    def dispatch(corpus: str, **_kwargs) -> list[dict]:
        return [unit for unit in units if unit["corpus"] == corpus]

    monkeypatch.setattr(sources_db, "_prepare_query", lambda query, track: (["q"], {"q"}, "q"))
    monkeypatch.setattr(sources_db, "_dispatch_corpus_search", dispatch)
    monkeypatch.setattr(sources_db, "_expand_neighbor_context", lambda match: match)

    results = sources_db.search_sources("q", track="a1", strategy="unified_dense", limit=10)

    assert all(unit["corpus"] == "ukrainian_wiki" for unit in results)
