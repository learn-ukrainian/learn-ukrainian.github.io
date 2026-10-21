"""Spec-facing tests for external corpus chunking and migration idempotency."""

from __future__ import annotations

import json
import os
import sqlite3
import sys
from pathlib import Path

import yaml

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))

from wiki.migrate_external_chunks import _overlap_prefix, _split_main_chunks, chunk_text, migrate_external_chunks


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n",
        encoding="utf-8",
    )


def _seed_fixture(tmp_path: Path) -> dict[str, Path]:
    data_dir = tmp_path / "external_articles"
    data_dir.mkdir()

    transcript = (
        "Перше речення про козаків та історію України. "
        "Друге речення пояснює походи, кордони та пам'ять. "
        "Третє речення додає деталі про джерела та інтерпретації. "
    ) * 20

    _write_jsonl(
        data_dir / "realna_istoria.jsonl",
        [{
            "url": "https://www.youtube.com/watch?v=abc123xyz89",
            "title": "Козаки та історія",
            "text": transcript,
        }],
    )

    channels = {
        "channels": [{
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
        }],
    }
    channels_path = data_dir / "channels.yaml"
    channels_path.write_text(yaml.safe_dump(channels, sort_keys=False, allow_unicode=True), encoding="utf-8")

    db_path = tmp_path / "sources.db"
    sqlite3.connect(str(db_path)).close()
    return {"data_dir": data_dir, "channels_path": channels_path, "db_path": db_path}


def test_chunk_text_is_sentence_aware_and_respects_cap():
    text = (
        "Перше коротке речення про мову. "
        "Друге речення достатньо довге, щоб тримати контекст і переносити сенс. "
        "Третє речення завершує перший блок.\n\n"
        "Четверте речення починає новий абзац із новими подробицями. "
        "П'яте речення знову додає деталі про українську історію та лексику. "
    ) * 6

    main_chunks = _split_main_chunks(text, target_chars=200)
    chunks = chunk_text(text, target_chars=200, overlap_chars=20)

    assert len(chunks) >= 2
    assert all(len(chunk) <= 230 for chunk in chunks)
    assert all(chunk.rstrip().endswith((".", "!", "?", "…")) for chunk in main_chunks[:-1])
    assert chunks[1].startswith(f"{_overlap_prefix(main_chunks[0], 20)}\n\n")


def test_migration_rerun_is_a_noop_and_chunk_ids_stay_stable(tmp_path: Path):
    fixture = _seed_fixture(tmp_path)

    first = migrate_external_chunks(
        db_path=fixture["db_path"],
        data_dir=fixture["data_dir"],
        channels_path=fixture["channels_path"],
        verify=True,
    )
    second = migrate_external_chunks(
        db_path=fixture["db_path"],
        data_dir=fixture["data_dir"],
        channels_path=fixture["channels_path"],
        verify=True,
    )

    conn = sqlite3.connect(str(fixture["db_path"]))
    rows = conn.execute(
        "SELECT chunk_id, char_count FROM external_articles ORDER BY chunk_id"
    ).fetchall()
    conn.close()

    assert first["rows_inserted"] == first["rows_after"]
    assert first["rows_changed"] == first["rows_after"]
    assert second["rows_inserted"] == 0
    assert second["rows_changed"] == 0
    assert second["noop"] is True
    assert second["verify_results"]["козаки"]
    assert rows[0][0].startswith("ext-realna_istoria-abc123xyz89-")
