"""Tests for DictUACrawler in scripts/lexicon/tools/dump_ulif.py."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from scripts.lexicon import ulif_raw_cache
from scripts.lexicon.tools.dump_ulif import DictUACrawler, DumpDB, import_to_sources

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


def test_import_to_sources_keeps_all_exact_http_bodies_in_cache(tmp_path: Path) -> None:
    dump_path = tmp_path / "dump.db"
    source_path = tmp_path / "sources.db"
    dump = DumpDB(dump_path)
    dump.store_entry(
        {
            "lemma": "замок",
            "canonical_headword": "за́мок",
            "status": "ok",
            "retrieved_at": "2026-09-25T00:00:00+00:00",
            "paradigm": {"rows": [["Називний", "за́мок"]]},
            "raw_responses": {"initial": "<html>register</html>", "paradigm": "<html>entry</html>"},
        },
        include_html=True,
    )
    dump.close()

    assert import_to_sources(dump_path, source_path) == 0
    with sqlite3.connect(source_path) as source:
        ref = source.execute("SELECT raw_response_ref FROM ulif_dictua_entries").fetchone()[0]
        assert source.execute("SELECT 1 FROM sqlite_master WHERE name='ulif_dictua_raw_responses'").fetchone() is None
    cache = ulif_raw_cache.cache_path(source_path)
    manifest = ulif_raw_cache.resolve_ref(ref, path=cache)
    assert manifest is not None
    refs = json.loads(manifest)
    assert set(refs) == {"initial", "paradigm"}
    assert ulif_raw_cache.resolve_ref(refs["initial"], path=cache) == b"<html>register</html>"
