"""Tests for wiki source-attribution backfills."""

from __future__ import annotations

import io
import os
import sqlite3
import sys
from pathlib import Path

import pytest

_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_project_root, "scripts"))


@pytest.fixture
def backfill_fixture(tmp_path: Path, monkeypatch) -> dict[str, Path]:
    from wiki import backfill_source_attribution, source_attribution

    db_path = tmp_path / "sources.db"
    conn = sqlite3.connect(str(db_path))
    conn.executescript(
        """
        CREATE TABLE textbook_sections (
            section_id INTEGER PRIMARY KEY,
            source_file TEXT NOT NULL,
            grade INTEGER NOT NULL,
            section_title TEXT NOT NULL,
            page_start INTEGER
        );

        CREATE TABLE textbooks (
            id INTEGER PRIMARY KEY,
            chunk_id TEXT NOT NULL DEFAULT '',
            title TEXT NOT NULL DEFAULT '',
            source_file TEXT NOT NULL DEFAULT '',
            grade TEXT DEFAULT '',
            author TEXT DEFAULT ''
        );

        CREATE TABLE literary_texts (
            id INTEGER PRIMARY KEY,
            chunk_id TEXT NOT NULL DEFAULT '',
            title TEXT NOT NULL DEFAULT '',
            source_file TEXT NOT NULL DEFAULT '',
            author TEXT DEFAULT '',
            work TEXT DEFAULT ''
        );

        CREATE TABLE external_articles (
            id INTEGER PRIMARY KEY,
            chunk_id TEXT NOT NULL DEFAULT '',
            url TEXT NOT NULL DEFAULT '',
            title TEXT NOT NULL DEFAULT '',
            source_file TEXT NOT NULL DEFAULT '',
            domain TEXT DEFAULT '',
            video_id TEXT DEFAULT '',
            chunk_start_ts INTEGER,
            chunk_end_ts INTEGER
        );

        CREATE TABLE wikipedia (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            url TEXT NOT NULL DEFAULT ''
        );

        CREATE TABLE ukrainian_wiki (
            id INTEGER PRIMARY KEY,
            passage_id TEXT NOT NULL UNIQUE,
            article_slug TEXT NOT NULL,
            article_title TEXT NOT NULL DEFAULT '',
            section_path TEXT NOT NULL DEFAULT ''
        );
        """
    )
    conn.execute(
        "INSERT INTO textbook_sections(section_id, source_file, grade, section_title, page_start) VALUES (?, ?, ?, ?, ?)",
        (77, "11-klas-ukrmova-avramenko-2019", 11, "Складне речення", 123),
    )
    conn.execute(
        """
        INSERT INTO external_articles(
            id, chunk_id, url, title, source_file, domain, video_id, chunk_start_ts, chunk_end_ts
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            1,
            "ext-blog-001",
            "https://example.com/article",
            "Article",
            "ulp_blogs",
            "example.com",
            "",
            None,
            None,
        ),
    )
    conn.commit()
    conn.close()

    wiki_dir = tmp_path / "wiki"
    article_path = wiki_dir / "pedagogy" / "a1" / "demo.md"
    article_path.parent.mkdir(parents=True)
    article_text = (
        "# Demo\n\n"
        "<!-- wiki-meta\n"
        "slug: demo\n"
        "domain: pedagogy\n"
        "tracks: [a1]\n"
        "compiled: 2026-04-23\n"
        "-->\n\n"
        "Факт один [S1]. Факт два [S2].\n"
    )
    article_path.write_text(article_text, encoding="utf-8")
    registry_path = article_path.with_suffix(".sources.yaml")
    registry_path.write_text(
        "# Source registry for wiki/pedagogy/a1/demo.md\n"
        "# Referenced inline as [S1], [S2], ...\n"
        "sources:\n"
        "- id: S1\n"
        "  file: S77\n"
        "  type: unknown\n"
        "- id: S2\n"
        "  file: ext-blog-001\n"
        "  type: unknown\n"
        "- id: S8\n"
        "  file: VESUM\n"
        "  type: morphological-dictionary\n"
        "  notes: VESUM authority\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(source_attribution, "DEFAULT_DB_PATH", db_path)
    monkeypatch.setattr(backfill_source_attribution, "WIKI_DIR", wiki_dir)
    monkeypatch.setattr(backfill_source_attribution, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(backfill_source_attribution, "LOG_DIR", tmp_path / "docs" / "data-quality")

    return {
        "tmp_path": tmp_path,
        "db_path": db_path,
        "wiki_dir": wiki_dir,
        "article_path": article_path,
        "registry_path": registry_path,
    }


def test_dry_run_emits_diff_without_writing(backfill_fixture: dict[str, Path]) -> None:
    from wiki import backfill_source_attribution

    registry_path = backfill_fixture["registry_path"]
    original_registry = registry_path.read_text(encoding="utf-8")
    stdout = io.StringIO()
    stderr = io.StringIO()

    summary = backfill_source_attribution.run_backfill(
        apply=False,
        track="a1",
        slug=None,
        stdout=stdout,
        stderr=stderr,
    )

    assert summary.files_scanned == 1
    assert summary.files_changed == 1
    assert summary.total_resolved == 2
    assert "11-klas-ukrmova-avramenko-2019_s0077" in stdout.getvalue()
    assert registry_path.read_text(encoding="utf-8") == original_registry


def test_apply_preserves_markdown_ids_and_is_idempotent(backfill_fixture: dict[str, Path]) -> None:
    from wiki import backfill_source_attribution

    article_path = backfill_fixture["article_path"]
    registry_path = backfill_fixture["registry_path"]
    original_article = article_path.read_text(encoding="utf-8")

    first_stdout = io.StringIO()
    first_stderr = io.StringIO()
    first_summary = backfill_source_attribution.run_backfill(
        apply=True,
        track=None,
        slug="demo",
        stdout=first_stdout,
        stderr=first_stderr,
    )

    updated_registry = registry_path.read_text(encoding="utf-8")
    assert first_summary.files_changed == 1
    assert "type: textbook" in updated_registry
    assert "url: https://example.com/article" in updated_registry
    assert "type: morphological-dictionary" in updated_registry
    assert "notes: VESUM authority" in updated_registry
    assert article_path.read_text(encoding="utf-8") == original_article
    assert "[S1]" in original_article and "[S2]" in original_article

    second_summary = backfill_source_attribution.run_backfill(
        apply=True,
        track=None,
        slug="demo",
        stdout=io.StringIO(),
        stderr=io.StringIO(),
    )

    assert second_summary.files_changed == 0
    assert second_summary.total_resolved == 0
    assert registry_path.read_text(encoding="utf-8") == updated_registry


def test_unresolvable_entries_are_logged_to_stderr(tmp_path: Path, monkeypatch) -> None:
    from wiki import backfill_source_attribution, source_attribution

    db_path = tmp_path / "sources.db"
    sqlite3.connect(str(db_path)).close()
    wiki_dir = tmp_path / "wiki"
    article_path = wiki_dir / "pedagogy" / "a1" / "missing.md"
    article_path.parent.mkdir(parents=True)
    article_path.write_text(
        "# Missing\n\n"
        "<!-- wiki-meta\n"
        "slug: missing\n"
        "domain: pedagogy\n"
        "tracks: [a1]\n"
        "compiled: 2026-04-23\n"
        "-->\n\n"
        "Текст [S9].\n",
        encoding="utf-8",
    )
    registry_path = article_path.with_suffix(".sources.yaml")
    registry_path.write_text(
        "# Source registry for wiki/pedagogy/a1/missing.md\n"
        "# Referenced inline as [S1], [S2], ...\n"
        "sources:\n"
        "- id: S9\n"
        "  file: S9999\n"
        "  type: unknown\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(source_attribution, "DEFAULT_DB_PATH", db_path)
    monkeypatch.setattr(backfill_source_attribution, "WIKI_DIR", wiki_dir)
    monkeypatch.setattr(backfill_source_attribution, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(backfill_source_attribution, "LOG_DIR", tmp_path / "docs" / "data-quality")

    stderr = io.StringIO()
    summary = backfill_source_attribution.run_backfill(
        apply=False,
        track="a1",
        slug=None,
        stdout=io.StringIO(),
        stderr=stderr,
    )

    assert summary.total_unresolved == 1
    assert "Unresolved source attribution" in stderr.getvalue()
    assert "S9999" in stderr.getvalue()
