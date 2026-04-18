"""Tests for textbook reference resolution from wiki source registries."""

from __future__ import annotations

import os
import sqlite3
import sys

_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_project_root, "scripts"))


def test_get_textbook_links_prefers_sibling_registry(tmp_path, monkeypatch) -> None:
    from scripts.build import textbook_refs

    db_path = tmp_path / "sources.db"
    conn = sqlite3.connect(str(db_path))
    conn.execute(
        "CREATE TABLE textbooks (chunk_id TEXT, source_file TEXT, title TEXT)"
    )
    conn.execute(
        "INSERT INTO textbooks (chunk_id, source_file, title) VALUES (?, ?, ?)",
        (
            "11-klas-ukrmova-avramenko-2019_s0256",
            "11-klas-ukrmova-avramenko-2019",
            "Сторінка 73",
        ),
    )
    conn.commit()
    conn.close()

    wiki_dir = tmp_path / "wiki"
    article_dir = wiki_dir / "grammar" / "a2"
    article_dir.mkdir(parents=True)
    (article_dir / "demo.md").write_text("# Demo\n", encoding="utf-8")
    (article_dir / "demo.sources.yaml").write_text(
        "sources:\n"
        "  - id: S1\n"
        "    file: 11-klas-ukrmova-avramenko-2019_s0256\n"
        "    type: textbook\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(textbook_refs, "SOURCES_DB", db_path)
    monkeypatch.setattr(textbook_refs, "WIKI_DIR", wiki_dir)
    monkeypatch.setattr("wiki.config.TRACK_WRITE_DOMAIN", {"a2": "grammar/a2"})

    links = textbook_refs.get_textbook_links("a2", "demo")

    assert len(links) == 1
    assert links[0]["page"] == 73
    assert "11-klas-ukrmova-avramenko-2019.pdf#page=73" in links[0]["url"]
