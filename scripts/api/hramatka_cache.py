"""Content-addressed cache for deterministic Hramatka lesson generations."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from pathlib import Path

DEFAULT_TTL_DAYS = 14


class HramatkaGenerationCache:
    """Persist generated lessons until their content-addressed inputs change.

    The caller supplies a database path so deployment configuration, rather than
    this library, decides where mutable cache state belongs.  Connections are
    intentionally short lived: SQLite WAL permits concurrent readers while a
    bounded busy timeout serializes brief writes from the lesson service.
    """

    def __init__(
        self,
        database_path: str | Path,
        *,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self.database_path = Path(database_path)
        self._clock = clock or (lambda: datetime.now(UTC))
        self.database_path.parent.mkdir(parents=True, exist_ok=True)

        with self._connect() as connection:
            connection.execute("PRAGMA journal_mode=WAL")
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS hramatka_generation_cache (
                    cache_key TEXT PRIMARY KEY,
                    lesson_json TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    expires_at REAL NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_hramatka_generation_cache_expiry
                ON hramatka_generation_cache (expires_at)
                """
            )
            self._delete_expired(connection, now=self._timestamp())

    @staticmethod
    def build_key(
        owner_id: str,
        anchor_hash: str,
        normalized_request: str,
        prompt_sha: str,
        schema_sha: str,
        data_manifest_sha: str,
        model_id: str,
        policy_version: str,
    ) -> str:
        """Return the required SHA-256 cache key for one generation request."""
        parts = (
            owner_id,
            anchor_hash,
            normalized_request,
            prompt_sha,
            schema_sha,
            data_manifest_sha,
            model_id,
            policy_version,
        )
        return hashlib.sha256(":".join(parts).encode("utf-8")).hexdigest()

    make_key = build_key

    def get(self, key: str) -> dict | None:
        """Return a cached lesson, or ``None`` when it is missing or expired."""
        now = self._timestamp()
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT lesson_json FROM hramatka_generation_cache
                WHERE cache_key = ? AND expires_at > ?
                """,
                (key, now.timestamp()),
            ).fetchone()
        if row is None:
            return None
        lesson_data = json.loads(row["lesson_json"])
        if not isinstance(lesson_data, dict):
            raise ValueError(f"cached lesson for key {key!r} is not a JSON object")
        return lesson_data

    def set(self, key: str, lesson_data: dict, ttl_days: int = DEFAULT_TTL_DAYS) -> None:
        """Store ``lesson_data`` under ``key`` for the requested positive TTL."""
        if isinstance(ttl_days, bool) or ttl_days <= 0:
            raise ValueError("ttl_days must be a positive integer")

        now = self._timestamp()
        expires_at = now + timedelta(days=ttl_days)
        payload = json.dumps(
            lesson_data,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
        with self._write_connection() as connection:
            self._delete_expired(connection, now=now)
            connection.execute(
                """
                INSERT INTO hramatka_generation_cache (
                    cache_key, lesson_json, created_at, expires_at
                ) VALUES (?, ?, ?, ?)
                ON CONFLICT(cache_key) DO UPDATE SET
                    lesson_json = excluded.lesson_json,
                    created_at = excluded.created_at,
                    expires_at = excluded.expires_at
                """,
                (key, payload, now.timestamp(), expires_at.timestamp()),
            )

    def invalidate(self, key: str) -> None:
        """Remove the cached generation for ``key`` if it exists."""
        with self._write_connection() as connection:
            self._delete_expired(connection, now=self._timestamp())
            connection.execute(
                "DELETE FROM hramatka_generation_cache WHERE cache_key = ?",
                (key,),
            )

    def cleanup_expired(self) -> int:
        """Delete expired entries and return how many rows were removed."""
        with self._write_connection() as connection:
            return self._delete_expired(connection, now=self._timestamp())

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(
            str(self.database_path),
            isolation_level=None,
            timeout=5.0,
        )
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA busy_timeout=5000")
        try:
            yield connection
        finally:
            connection.close()

    @contextmanager
    def _write_connection(self) -> Iterator[sqlite3.Connection]:
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                yield connection
            except BaseException:
                connection.rollback()
                raise
            else:
                connection.commit()

    def _timestamp(self) -> datetime:
        now = self._clock()
        if now.tzinfo is None or now.utcoffset() is None:
            raise ValueError("clock must return a timezone-aware datetime")
        return now.astimezone(UTC)

    @staticmethod
    def _delete_expired(connection: sqlite3.Connection, *, now: datetime) -> int:
        cursor = connection.execute(
            "DELETE FROM hramatka_generation_cache WHERE expires_at <= ?",
            (now.timestamp(),),
        )
        return cursor.rowcount
