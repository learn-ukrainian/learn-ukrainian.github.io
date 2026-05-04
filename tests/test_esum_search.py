from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

from wiki.sources_db import search_esum


def _joined_text(query: str, limit: int = 5) -> str:
    hits = search_esum(query, volume=1, limit=limit)
    return "\n".join(str(hit["etymology_text"]) for hit in hits)


def test_search_esum_berkut_returns_turkic_origin() -> None:
    hits = search_esum("беркут", volume=1, limit=3)
    assert [hit["lemma"] for hit in hits] == ["беркут"]
    assert "запозичення з тюркських мов" in hits[0]["etymology_text"]
    assert "тат. біркут" in hits[0]["etymology_text"]


def test_search_esum_bereza_returns_indo_european_cognates() -> None:
    text = _joined_text("береза")
    assert "іє." in text
    assert "дінд." in text
    assert "лит." in text


def test_search_esum_voda_returns_cross_slavic_and_proto_slavic_cognates() -> None:
    text = _joined_text("вода")
    assert "р. болг. вода" in text
    assert "стел, вода" in text
    assert "псл." in text
    assert "іє." in text


def test_search_esum_sibir_is_outside_volume_one_scope() -> None:
    # ЕСУМ vol. 1 covers А-Г only; `сибір` belongs to a later volume.
    assert search_esum("сибір", volume=1, limit=3) == []


def test_search_esum_maty_is_outside_volume_one_scope() -> None:
    # ЕСУМ vol. 1 covers А-Г only; `мати` belongs to a later volume.
    assert search_esum("мати", volume=1, limit=3) == []


def test_search_esum_nonexistent_word_returns_empty_list() -> None:
    assert search_esum("хххх", volume=1, limit=3) == []
