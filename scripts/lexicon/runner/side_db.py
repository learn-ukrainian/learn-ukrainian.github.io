"""Immutable indexed side databases replacing whole-table Python indexes (#5230 PR1).

Builders scan sources in bounded batches. Workers open with mode=ro&immutable=1,
query_only, bounded page cache, and disabled large mmap.
"""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any

from scripts.lexicon.runner.contracts import SIDE_DB_SCHEMA_VERSION, SideDbArtifact
from scripts.lexicon.runner.sqlite_ro import checkpoint_and_hash, open_immutable_ro

DEFAULT_BATCH_SIZE = 2000

BALLA_KIND = "balla_reverse"
DMKLINGER_KIND = "dmklinger"
KAIKKI_KIND = "kaikki"


def _iter_batches(
    conn: sqlite3.Connection,
    sql: str,
    *,
    batch_size: int = DEFAULT_BATCH_SIZE,
) -> Iterator[list[tuple[Any, ...]]]:
    try:
        cursor = conn.execute(sql)
    except sqlite3.OperationalError:
        return
        yield  # pragma: no cover — make this a generator
    while True:
        rows = cursor.fetchmany(batch_size)
        if not rows:
            break
        yield list(rows)


def build_balla_reverse_side_db(
    sources: sqlite3.Connection,
    output: Path,
    *,
    candidate_keys: Callable[[str], list[tuple[str, str | None]]],
    headword_fn: Callable[[object], str | None],
    segment_fn: Callable[[object], list[str]],
    token_re: Any,
    batch_size: int = DEFAULT_BATCH_SIZE,
) -> SideDbArtifact:
    """Build Balla reverse-definition lookup side DB.

    ``candidate_keys`` / ``headword_fn`` / ``segment_fn`` are injected from
    enrich_manifest so the builder preserves exact tokenization semantics
    without circular imports of the whole engine at module load.
    """
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        output.unlink()
    out = sqlite3.connect(output)
    try:
        out.execute("PRAGMA journal_mode = OFF")
        out.execute("PRAGMA synchronous = OFF")
        out.executescript(
            """
            CREATE TABLE meta (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
            CREATE TABLE balla_reverse (
                lemma_key TEXT NOT NULL,
                headword TEXT NOT NULL,
                vesum_pos TEXT,
                PRIMARY KEY (lemma_key, headword, vesum_pos)
            );
            CREATE INDEX idx_balla_lemma ON balla_reverse(lemma_key);
            """
        )
        out.execute(
            "INSERT INTO meta(key, value) VALUES (?, ?)",
            ("schema_version", SIDE_DB_SCHEMA_VERSION),
        )
        out.execute(
            "INSERT INTO meta(key, value) VALUES (?, ?)",
            ("kind", BALLA_KIND),
        )
        seen: set[tuple[str, str, str | None]] = set()
        row_count = 0
        batches = _iter_batches(
            sources,
            "SELECT word, definition FROM balla_en_uk ORDER BY word",
            batch_size=batch_size,
        )
        for batch in batches:
            for word, definition in batch:
                headword = headword_fn(word)
                if not headword:
                    continue
                for segment in segment_fn(definition):
                    tokens = token_re.findall(segment)
                    if len(tokens) != 1:
                        continue
                    for key, pos in candidate_keys(tokens[0]):
                        seen_key = (key, headword, pos)
                        if seen_key in seen:
                            continue
                        seen.add(seen_key)
                        out.execute(
                            "INSERT INTO balla_reverse(lemma_key, headword, vesum_pos) VALUES (?, ?, ?)",
                            (key, headword, pos),
                        )
                        row_count += 1
            out.commit()
        digest = checkpoint_and_hash(out, output)
        out.execute(
            "INSERT OR REPLACE INTO meta(key, value) VALUES (?, ?)",
            ("content_sha256", digest),
        )
        out.execute(
            "INSERT OR REPLACE INTO meta(key, value) VALUES (?, ?)",
            ("row_count", str(row_count)),
        )
        out.commit()
        digest = checkpoint_and_hash(out, output)
    finally:
        out.close()
    return SideDbArtifact(
        path=str(output),
        kind=BALLA_KIND,
        sha256=digest,
        row_count=row_count,
    )


def build_dmklinger_side_db(
    sources: sqlite3.Connection,
    output: Path,
    *,
    key_fn: Callable[[str], str],
    batch_size: int = DEFAULT_BATCH_SIZE,
) -> SideDbArtifact:
    """Build dmklinger headword lookup side DB (stress-stripped keys)."""
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        output.unlink()
    out = sqlite3.connect(output)
    try:
        out.execute("PRAGMA journal_mode = OFF")
        out.execute("PRAGMA synchronous = OFF")
        out.executescript(
            """
            CREATE TABLE meta (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
            CREATE TABLE dmklinger (
                lemma_key TEXT NOT NULL,
                pos TEXT,
                translations TEXT NOT NULL,
                row_ord INTEGER NOT NULL,
                PRIMARY KEY (lemma_key, row_ord)
            );
            CREATE INDEX idx_dmklinger_lemma ON dmklinger(lemma_key);
            """
        )
        out.execute(
            "INSERT INTO meta(key, value) VALUES (?, ?)",
            ("schema_version", SIDE_DB_SCHEMA_VERSION),
        )
        out.execute(
            "INSERT INTO meta(key, value) VALUES (?, ?)",
            ("kind", DMKLINGER_KIND),
        )
        row_count = 0
        ord_by_key: dict[str, int] = {}
        batches = _iter_batches(
            sources,
            "SELECT word, pos, translations FROM dmklinger_uk_en",
            batch_size=batch_size,
        )
        for batch in batches:
            for word, pos, translations in batch:
                key = key_fn(str(word or ""))
                if not key:
                    continue
                row_ord = ord_by_key.get(key, 0)
                ord_by_key[key] = row_ord + 1
                out.execute(
                    "INSERT INTO dmklinger(lemma_key, pos, translations, row_ord) VALUES (?, ?, ?, ?)",
                    (key, pos, translations if translations is not None else "", row_ord),
                )
                row_count += 1
            out.commit()
        digest = checkpoint_and_hash(out, output)
        out.execute(
            "INSERT OR REPLACE INTO meta(key, value) VALUES (?, ?)",
            ("content_sha256", digest),
        )
        out.execute(
            "INSERT OR REPLACE INTO meta(key, value) VALUES (?, ?)",
            ("row_count", str(row_count)),
        )
        out.commit()
        digest = checkpoint_and_hash(out, output)
    finally:
        out.close()
    return SideDbArtifact(
        path=str(output),
        kind=DMKLINGER_KIND,
        sha256=digest,
        row_count=row_count,
    )


def build_kaikki_side_db(
    kaikki_json: Path,
    output: Path,
    *,
    batch_size: int = DEFAULT_BATCH_SIZE,
) -> SideDbArtifact:
    """Convert the kaikki JSON lookup into an immutable SQLite side DB.

    Workers query by key instead of reparsing the global JSON file.
    """
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        output.unlink()
    try:
        raw = json.loads(kaikki_json.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        raw = {}
    if not isinstance(raw, dict):
        raw = {}

    out = sqlite3.connect(output)
    try:
        out.execute("PRAGMA journal_mode = OFF")
        out.execute("PRAGMA synchronous = OFF")
        out.executescript(
            """
            CREATE TABLE meta (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
            CREATE TABLE kaikki (
                lemma_key TEXT PRIMARY KEY,
                payload TEXT NOT NULL
            );
            """
        )
        out.execute(
            "INSERT INTO meta(key, value) VALUES (?, ?)",
            ("schema_version", SIDE_DB_SCHEMA_VERSION),
        )
        out.execute(
            "INSERT INTO meta(key, value) VALUES (?, ?)",
            ("kind", KAIKKI_KIND),
        )
        items = sorted(raw.items(), key=lambda item: str(item[0]))
        row_count = 0
        for start in range(0, len(items), batch_size):
            batch = items[start : start + batch_size]
            for key, value in batch:
                if not isinstance(value, dict):
                    continue
                out.execute(
                    "INSERT INTO kaikki(lemma_key, payload) VALUES (?, ?)",
                    (str(key), json.dumps(value, ensure_ascii=False, sort_keys=True)),
                )
                row_count += 1
            out.commit()
        digest = checkpoint_and_hash(out, output)
        out.execute(
            "INSERT OR REPLACE INTO meta(key, value) VALUES (?, ?)",
            ("content_sha256", digest),
        )
        out.execute(
            "INSERT OR REPLACE INTO meta(key, value) VALUES (?, ?)",
            ("row_count", str(row_count)),
        )
        out.commit()
        digest = checkpoint_and_hash(out, output)
    finally:
        out.close()
    return SideDbArtifact(
        path=str(output),
        kind=KAIKKI_KIND,
        sha256=digest,
        row_count=row_count,
    )


class BallaReverseSideDb:
    """Worker-facing Balla reverse lookup (no whole-table Python dict)."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self._conn = open_immutable_ro(path)

    def close(self) -> None:
        self._conn.close()

    def lookup(self, lemma_key: str) -> list[tuple[str, str | None]]:
        # Bounded per-key lookup (not a whole-table load).
        rows = self._conn.execute(
            "SELECT headword, vesum_pos FROM balla_reverse WHERE lemma_key = ? ORDER BY headword, vesum_pos",
            (lemma_key,),
        ).fetchmany(10_000)
        return [(str(r[0]), None if r[1] is None else str(r[1])) for r in rows]


class DmklingerSideDb:
    """Worker-facing dmklinger lookup."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self._conn = open_immutable_ro(path)

    def close(self) -> None:
        self._conn.close()

    def lookup(self, lemma_key: str) -> list[tuple[str, str]]:
        # Bounded per-key lookup (not a whole-table load).
        rows = self._conn.execute(
            "SELECT pos, translations FROM dmklinger WHERE lemma_key = ? ORDER BY row_ord",
            (lemma_key,),
        ).fetchmany(10_000)
        return [(str(r[0] or ""), str(r[1] or "")) for r in rows]


class KaikkiSideDb:
    """Worker-facing kaikki lookup (replaces global JSON load)."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self._conn = open_immutable_ro(path)

    def close(self) -> None:
        self._conn.close()

    def get(self, lemma_key: str) -> dict[str, Any] | None:
        row = self._conn.execute(
            "SELECT payload FROM kaikki WHERE lemma_key = ?",
            (lemma_key,),
        ).fetchone()
        if not row:
            return None
        try:
            data = json.loads(str(row[0]))
        except (TypeError, ValueError):
            return None
        return data if isinstance(data, dict) else None

    def as_mapping_proxy(self) -> _KaikkiMappingProxy:
        return _KaikkiMappingProxy(self)


class _KaikkiMappingProxy:
    """Minimal mapping surface expected by enrich_manifest kaikki helpers."""

    def __init__(self, side: KaikkiSideDb) -> None:
        self._side = side

    def get(self, key: str, default: Any = None) -> Any:
        row = self._side.get(key)
        return default if row is None else row

    def __bool__(self) -> bool:
        return True
