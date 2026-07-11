"""Synthetic tests for the Grinchyshyn paronym candidate extractor."""

from __future__ import annotations

from pathlib import Path

from scripts.lexicon.extract_grinchyshyn_paronym_candidates import extract_candidates


def _vesum(word: str) -> list[dict]:
    if word == "невідоме":
        return []
    if word == "форма":
        return [{"lemma": "форм", "pos": "noun", "tags": ""}]
    return [{"lemma": word, "pos": "noun", "tags": ""}]


def test_expands_groups_and_accepts_wrapped_slash_lines(tmp_path: Path) -> None:
    source = tmp_path / "source.txt"
    source.write_text(
        "ПЕРЕДМОВА\n"
        "ПАРОНІМИ\n"
        "АБОНЕМЕНТ / АБОНЕНТ\n"
        "ТРИ // ДВА //\n"
        "ОДИН\n"
        "ВИМАРАНЕ / НЕВІДОМЕ\n"
        "ІНШЕ / ФОРМА\n"
        "АВАНТЮРИСТИЧНИЙ (АЛЬТЕРНАТИВА) / АВАНТЮРНИЙ\n"
        "визначення / не headword\n",
        encoding="utf-8",
    )

    result = extract_candidates(source, vesum_lookup=_vesum)

    assert result.groups_found == 4
    assert result.pairs_found == 6
    assert len(result.rows) == 4
    assert result.rows[0]["word_a"] == "абонемент"
    assert result.rows[0]["word_b"] == "абонент"
    assert {drop.missing_words for drop in result.drops} == {("невідоме",), ("форма",)}
    assert result.malformed_groups == 1
