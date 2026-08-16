"""Tests for scripts/lexicon/migrate_slovnyk_cache_v4.py (#6809)."""

from __future__ import annotations

import json
from pathlib import Path

from scripts.lexicon import enrich_manifest as enrich_manifest_module
from scripts.lexicon.migrate_slovnyk_cache_v4 import migrate, scan


def _write_cache(path: Path, *, schema_version: int, lookups: dict) -> None:
    path.write_text(
        json.dumps(
            {
                "schema_version": schema_version,
                "lemma": path.stem,
                "lookup_word": path.stem,
                "fetched_at": "2026-08-15T00:00:00+00:00",
                "lookups": lookups,
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )


def test_scan_counts_stale_v3_known_miss_rows_separately(tmp_path: Path) -> None:
    current = enrich_manifest_module._SLOVNYK_CACHE_SCHEMA_VERSION
    assert current == 4, "test assumes v4 is current -- update if the schema bumps again"

    _write_cache(tmp_path / "аршин.json", schema_version=3, lookups={"ukreng": None})
    _write_cache(tmp_path / "слово.json", schema_version=current, lookups={"ukreng": {"text": "word"}})

    counts = scan(tmp_path)

    assert counts["total"] == 2
    assert counts["already_current"] == 1
    assert counts["stale_v3"] == 1
    assert counts["stale_total"] == 1


def test_migrate_discards_v3_ukreng_null_rows_and_leaves_current_files_alone(tmp_path: Path) -> None:
    """#6809: a v3 row with a cached ``ukreng: null`` known-miss must be discarded
    (empty ``lookups``, bumped to the current schema version) so the lemma's next
    live touch refetches it -- it must not be treated as a confirmed absence."""
    current = enrich_manifest_module._SLOVNYK_CACHE_SCHEMA_VERSION

    stale_path = tmp_path / "аршин.json"
    _write_cache(stale_path, schema_version=3, lookups={"ukreng": None})

    current_path = tmp_path / "слово.json"
    _write_cache(current_path, schema_version=current, lookups={"ukreng": {"text": "word"}})

    counts = migrate(tmp_path, dry_run=False)

    assert counts["migrated"] == 1
    assert counts["already_current"] == 1

    migrated_payload = json.loads(stale_path.read_text(encoding="utf-8"))
    assert migrated_payload["schema_version"] == current
    assert migrated_payload["lookups"] == {}
    assert migrated_payload["lemma"] == "аршин"

    untouched_payload = json.loads(current_path.read_text(encoding="utf-8"))
    assert untouched_payload["lookups"] == {"ukreng": {"text": "word"}}

    assert scan(tmp_path)["stale_total"] == 0


def test_migrate_dry_run_writes_nothing(tmp_path: Path) -> None:
    stale_path = tmp_path / "аршин.json"
    _write_cache(stale_path, schema_version=3, lookups={"ukreng": None})
    before_bytes = stale_path.read_bytes()

    counts = migrate(tmp_path, dry_run=True)

    assert counts["migrated"] == 1
    assert stale_path.read_bytes() == before_bytes


def test_migrate_leaves_malformed_files_untouched(tmp_path: Path) -> None:
    malformed_path = tmp_path / "broken.json"
    malformed_path.write_text("not json", encoding="utf-8")

    scan_counts = scan(tmp_path)
    migrate_counts = migrate(tmp_path, dry_run=False)

    assert scan_counts["malformed"] == 1
    assert migrate_counts["malformed"] == 1
    assert malformed_path.read_text(encoding="utf-8") == "not json"
