"""Synthetic canonical SUM-20 bindings for enrichment consumer tests."""

import sqlite3
import sys
from pathlib import Path

import pytest

from scripts.lexicon import sum20_lookup
from scripts.wiki.sum20_official import ensure_sum20_official_schema, normalize_sum20_lookup


def seed_sum20_rows(tmp_path: Path, documents: dict) -> None:
    """Ingest existing synthetic mirror documents into the test's canonical DB."""
    with sqlite3.connect(tmp_path) as conn:
        for index, (lemma, document) in enumerate(documents.items(), 1):
            row = document.get("lookups", {}).get("newsum")
            if not row or not row.get("text"):
                continue
            conn.execute("""
                INSERT OR REPLACE INTO sum20_articles (
                    wordid, normalized_lookup_key, headword, stressed_headword, article_html,
                    article_text, definition_text, official_url, fetched_at, content_sha256, parser_version
                ) VALUES (?, ?, ?, ?, '', ?, ?, ?, 'fixture', 'fixture', 'fixture')
            """, (index, normalize_sum20_lookup(lemma), row.get("word", lemma), row.get("word", lemma),
                  row["text"], row["text"], row.get("source_url", "")))


def bind_empty_sum20_store(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    """Bind an empty official store without consulting worktree data links."""
    path = tmp_path / "canonical_sum20.sqlite"
    with sqlite3.connect(path) as conn:
        ensure_sum20_official_schema(conn)
    monkeypatch.setattr(sum20_lookup, "REPO_ROOT", tmp_path)
    for name in ("scripts.wiki.sources_db", "wiki.sources_db"):
        module = sys.modules.get(name)
        if module is not None:
            monkeypatch.setattr(module, "PROJECT_ROOT", tmp_path)
    monkeypatch.setenv("LU_SOURCES_DB", str(path))
    monkeypatch.delenv("LEXDATA_DB_PATH", raising=False)
    monkeypatch.delenv("LU_LEXDATA_DB", raising=False)
    return path


@pytest.fixture(autouse=True)
def canonical_sum20_store(monkeypatch, tmp_path):
    """Give unrelated consumer tests an explicit empty canonical inventory."""
    return bind_empty_sum20_store(monkeypatch, tmp_path)
