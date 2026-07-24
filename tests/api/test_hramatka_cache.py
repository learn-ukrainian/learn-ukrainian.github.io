"""Unit tests for the Hramatka content-addressed generation cache."""

from __future__ import annotations

import hashlib
import sqlite3
from datetime import UTC, datetime, timedelta

from scripts.api.hramatka_cache import HramatkaGenerationCache


def test_cache_hit_miss_and_invalidation(tmp_path) -> None:
    cache = HramatkaGenerationCache(tmp_path / "generation-cache.sqlite3")
    lesson = {"title": "Відмінки", "activities": [{"type": "quiz", "items": 4}]}

    assert cache.get("missing") is None

    cache.set("lesson-key", lesson)

    assert cache.get("lesson-key") == lesson

    cache.invalidate("lesson-key")

    assert cache.get("lesson-key") is None


def test_cache_uses_wal_mode(tmp_path) -> None:
    database_path = tmp_path / "generation-cache.sqlite3"
    HramatkaGenerationCache(database_path)

    with sqlite3.connect(database_path) as connection:
        assert connection.execute("PRAGMA journal_mode").fetchone()[0].lower() == "wal"


def test_cache_key_is_sha256_of_all_generation_inputs() -> None:
    inputs = {
        "owner_id": "teacher-17",
        "anchor_hash": "anchor-a",
        "normalized_request": '{"topic":"verbs"}',
        "prompt_sha": "prompt-a",
        "schema_sha": "schema-a",
        "data_manifest_sha": "manifest-a",
        "model_id": "gemini-3.6-flash",
        "policy_version": "2026-07",
    }
    key = HramatkaGenerationCache.build_key(**inputs)
    expected = hashlib.sha256(":".join(inputs.values()).encode("utf-8")).hexdigest()

    assert key == expected

    for dimension in ("prompt_sha", "schema_sha", "data_manifest_sha", "model_id"):
        changed = inputs | {dimension: f"changed-{inputs[dimension]}"}
        assert HramatkaGenerationCache.build_key(**changed) != key


def test_cache_expires_entries_after_fourteen_days_and_cleans_them_up(tmp_path) -> None:
    now = datetime(2026, 7, 1, 12, 0, tzinfo=UTC)
    cache = HramatkaGenerationCache(tmp_path / "generation-cache.sqlite3", clock=lambda: now)
    cache.set("lesson-key", {"title": "Час"})

    now += timedelta(days=14)

    assert cache.get("lesson-key") is None
    assert cache.cleanup_expired() == 1
