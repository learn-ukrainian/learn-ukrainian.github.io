"""Tests for the external chunk migration script."""

from __future__ import annotations

import json
import os
import sqlite3
import sys
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))

from wiki.migrate_external_chunks import (
    _overlap_prefix,
    _split_main_chunks,
    chunk_text,
    migrate_external_chunks,
)


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n",
        encoding="utf-8",
    )


def _init_external_db(path: Path) -> None:
    conn = sqlite3.connect(str(path))
    conn.executescript(
        """
        CREATE TABLE external_articles (
            id INTEGER PRIMARY KEY,
            chunk_id TEXT NOT NULL DEFAULT '',
            url TEXT NOT NULL DEFAULT '',
            url_normalized TEXT NOT NULL DEFAULT '',
            title TEXT NOT NULL DEFAULT '',
            text TEXT NOT NULL DEFAULT '',
            source_file TEXT NOT NULL DEFAULT '',
            domain TEXT DEFAULT '',
            char_count INTEGER DEFAULT 0
        );
        CREATE VIRTUAL TABLE external_fts USING fts5(
            title, text, content='external_articles', content_rowid='id', tokenize='unicode61'
        );
        CREATE TRIGGER external_ai AFTER INSERT ON external_articles BEGIN
            INSERT INTO external_fts(rowid, title, text) VALUES (new.id, new.title, new.text);
        END;
        """
    )
    conn.commit()
    conn.close()


@pytest.fixture()
def migration_fixture(tmp_path: Path) -> dict[str, Path]:
    data_dir = tmp_path / "external_articles"
    data_dir.mkdir()

    long_text = (
        "Перше речення про козаків та історію України. "
        "Друге речення пояснює походи, кордони та пам'ять. "
        "Третє речення додає деталі про джерела та інтерпретації. "
    ) * 20
    blog_text = "Короткий урок української мови."

    _write_jsonl(
        data_dir / "realna_istoria.jsonl",
        [
            {
                "url": "https://www.youtube.com/watch?v=abc123xyz89",
                "title": "Козаки та історія",
                "text": long_text,
                "char_count": len(long_text),
            },
            {
                "url": "https://www.youtube.com/watch?v=abc123xyz89",
                "title": "Козаки та історія",
                "text": long_text,
                "char_count": len(long_text),
            },
        ],
    )
    _write_jsonl(
        data_dir / "ulp_blogs.jsonl",
        [{
            "url": "https://www.ukrainianlessons.com/demo-post/",
            "title": "Demo post",
            "text": blog_text,
            "char_count": len(blog_text),
            "domain": "www.ukrainianlessons.com",
        }],
    )

    channels = {
        "channels": [
            {
                "id": "realna_istoria",
                "name": "Реальна Історія",
                "host": "Акім Галімов",
                "url": "https://www.youtube.com/channel/demo",
                "source_file": "realna_istoria",
                "register_tag": "interview",
                "decolonization_tag": "strong",
                "quality_tier": 1,
                "language_purity": "vetted",
                "track_affinity": {"hist": 1.0},
                "description": "Demo history source.",
            },
            {
                "id": "ulp_blogs",
                "name": "ULP Blog",
                "host": "Anna Ohoiko",
                "url": "https://www.ukrainianlessons.com/",
                "source_file": "ulp_blogs",
                "register_tag": "scripted",
                "decolonization_tag": "moderate",
                "quality_tier": 1,
                "language_purity": "vetted",
                "track_affinity": {"a1": 1.0},
                "description": "Demo pedagogy source.",
            },
        ],
    }
    channels_path = data_dir / "channels.yaml"
    channels_path.write_text(yaml.safe_dump(channels, sort_keys=False, allow_unicode=True), encoding="utf-8")

    db_path = tmp_path / "sources.db"
    _init_external_db(db_path)
    return {
        "data_dir": data_dir,
        "channels_path": channels_path,
        "db_path": db_path,
    }


def test_chunker_is_sentence_aware_and_overlapping():
    text = (
        "Перше коротке речення про мову. "
        "Друге речення достатньо довге, щоб тримати контекст і переносити сенс. "
        "Третє речення завершує перший блок.\n\n"
        "Четверте речення починає новий абзац із новими подробицями. "
        "П'яте речення знову додає деталі про українську історію та лексику. "
    ) * 6
    main_chunks = _split_main_chunks(text, target_chars=200)
    chunks = chunk_text(text, target_chars=200, overlap_chars=20)

    assert len(main_chunks) >= 2
    assert len(chunks) >= 2
    assert all(len(chunk) <= 230 for chunk in chunks)
    assert all(chunk.rstrip().endswith((".", "!", "?", "…")) for chunk in main_chunks[:-1])
    assert chunks[1].startswith(f"{_overlap_prefix(main_chunks[0], 20)}\n\n")

    tokens = [f"токен{i}" for i in range(40)]
    token_chunks = chunk_text(" ".join(tokens), target_chars=60, overlap_chars=10)
    for token in tokens:
        assert any(token in chunk.split() for chunk in token_chunks)


def test_migration_is_idempotent_and_chunk_ids_are_stable(migration_fixture: dict[str, Path]):
    stats1 = migrate_external_chunks(
        db_path=migration_fixture["db_path"],
        data_dir=migration_fixture["data_dir"],
        channels_path=migration_fixture["channels_path"],
        verify=True,
    )
    conn = sqlite3.connect(str(migration_fixture["db_path"]))
    rows1 = conn.execute(
        """SELECT chunk_id, source_file, title, text, channel_id, quality_tier, video_id
           FROM external_articles
           ORDER BY chunk_id"""
    ).fetchall()
    conn.close()

    stats2 = migrate_external_chunks(
        db_path=migration_fixture["db_path"],
        data_dir=migration_fixture["data_dir"],
        channels_path=migration_fixture["channels_path"],
        verify=True,
    )
    conn = sqlite3.connect(str(migration_fixture["db_path"]))
    rows2 = conn.execute(
        """SELECT chunk_id, source_file, title, text, channel_id, quality_tier, video_id
           FROM external_articles
           ORDER BY chunk_id"""
    ).fetchall()
    conn.close()

    assert stats1["rows_after"] == stats1["rows_inserted"]
    assert stats2["rows_after"] == stats2["rows_inserted"]
    assert stats1["items_deduped"] == 1
    assert stats1["verify_results"]["козаки"]
    assert rows1 == rows2
    assert rows1[0][0].startswith("ext-realna_istoria-abc123xyz89-")


def test_migration_preserves_ulp_blogs_as_single_chunks(migration_fixture: dict[str, Path]):
    stats = migrate_external_chunks(
        db_path=migration_fixture["db_path"],
        data_dir=migration_fixture["data_dir"],
        channels_path=migration_fixture["channels_path"],
    )
    conn = sqlite3.connect(str(migration_fixture["db_path"]))
    blog_rows = conn.execute(
        "SELECT chunk_id, text, char_count FROM external_articles WHERE source_file = 'ulp_blogs'"
    ).fetchall()
    conn.close()

    assert stats["items_failed"] == []
    assert len(blog_rows) == 1
    assert blog_rows[0][0].endswith("-000")
    assert blog_rows[0][1] == "Короткий урок української мови."
    assert blog_rows[0][2] == len("Короткий урок української мови.")
