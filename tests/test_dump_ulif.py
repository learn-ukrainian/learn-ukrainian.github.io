"""Tests for DictUACrawler in scripts/lexicon/tools/dump_ulif.py."""

from __future__ import annotations

from pathlib import Path

from scripts.lexicon.tools.dump_ulif import DictUACrawler

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "ulif_dictua"


def _fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def test_parse_paradigm_noun() -> None:
    html = _fixture("privit-paradigm.html")
    res = DictUACrawler._parse_paradigm(html)
    assert res is not None
    assert "headers" in res
    assert "rows" in res
    assert res["headers"] == ["відмінок", "однина", "множина"]
    assert len(res["rows"]) == 8
    # Check that case label exists in rows
    cases = [row[0] for row in res["rows"][1:]]
    assert "називний" in cases
    assert "родовий" in cases


def test_parse_paradigm_verb() -> None:
    html = _fixture("hovoryty-paradigm.html")
    res = DictUACrawler._parse_paradigm(html)
    assert res is not None
    assert "headers" in res
    assert "rows" in res
    assert res["headers"] == ["Інфінітив", "говори́ти"]
    assert len(res["rows"]) == 27


def test_parse_paradigm_empty() -> None:
    assert DictUACrawler._parse_paradigm("") is None
    assert DictUACrawler._parse_paradigm("<html><body><p>No table</p></body></html>") is None
