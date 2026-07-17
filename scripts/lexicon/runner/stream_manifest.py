"""Streaming manifest input and candidate output (no full-manifest Python dict)."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from collections.abc import Iterator
from pathlib import Path
from typing import Any


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def stream_manifest_entries_json(path: Path) -> Iterator[dict[str, Any]]:
    """Yield manifest entries without building a full entries list in memory.

    Supports standard Atlas manifests (``{"entries":[...]}``) via ijson when
    available; falls back to a streaming JSONL file (one entry object per line)
    or a staged SQLite table produced by :func:`stage_manifest_to_sqlite`.
    """
    suffix = path.suffix.casefold()
    if suffix in {".sqlite", ".db"}:
        yield from stream_manifest_entries_sqlite(path)
        return
    if suffix == ".jsonl":
        with path.open(encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                obj = json.loads(line)
                if isinstance(obj, dict):
                    yield obj
        return

    # Prefer ijson for large JSON manifests; fall back to full load only for
    # small fixtures (tests). Production runners should stage to SQLite/JSONL.
    try:
        import ijson  # type: ignore[import-untyped]
    except ModuleNotFoundError:
        ijson = None  # type: ignore[assignment]
    if ijson is None:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError(f"{path} must contain a JSON object")
        entries = data.get("entries")
        if not isinstance(entries, list):
            raise ValueError(f"{path} missing entries list")
        for entry in entries:
            if isinstance(entry, dict):
                yield entry
        return

    with path.open("rb") as handle:
        for entry in ijson.items(handle, "entries.item"):
            if isinstance(entry, dict):
                yield entry


def stage_manifest_to_sqlite(
    source: Path,
    dest: Path,
    *,
    batch_size: int = 500,
) -> dict[str, Any]:
    """Stream manifest entries into ordered SQLite rows. Returns cohort digest meta."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        dest.unlink()
    conn = sqlite3.connect(dest)
    try:
        conn.execute("PRAGMA journal_mode = OFF")
        conn.executescript(
            """
            CREATE TABLE meta (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
            CREATE TABLE entries (
                ord INTEGER PRIMARY KEY,
                lemma_id TEXT NOT NULL UNIQUE,
                lemma TEXT NOT NULL,
                payload TEXT NOT NULL
            );
            """
        )
        digest = hashlib.sha256()
        count = 0
        batch: list[tuple[int, str, str, str]] = []
        for entry in stream_manifest_entries_json(source):
            lemma = str(entry.get("lemma") or "")
            lemma_id = str(entry.get("url_slug") or lemma)
            payload = json.dumps(entry, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            digest.update(payload.encode("utf-8"))
            digest.update(b"\n")
            batch.append((count, lemma_id, lemma, payload))
            count += 1
            if len(batch) >= batch_size:
                conn.executemany(
                    "INSERT INTO entries(ord, lemma_id, lemma, payload) VALUES (?, ?, ?, ?)",
                    batch,
                )
                conn.commit()
                batch.clear()
        if batch:
            conn.executemany(
                "INSERT INTO entries(ord, lemma_id, lemma, payload) VALUES (?, ?, ?, ?)",
                batch,
            )
        cohort = digest.hexdigest()
        conn.execute(
            "INSERT INTO meta(key, value) VALUES (?, ?)",
            ("cohort_digest", cohort),
        )
        conn.execute(
            "INSERT INTO meta(key, value) VALUES (?, ?)",
            ("entry_count", str(count)),
        )
        conn.commit()
        return {"cohort_digest": cohort, "entry_count": count, "path": str(dest)}
    finally:
        conn.close()


def stream_manifest_entries_sqlite(path: Path) -> Iterator[dict[str, Any]]:
    conn = sqlite3.connect(f"file:{path.resolve().as_posix()}?mode=ro", uri=True)
    try:
        for (payload,) in conn.execute("SELECT payload FROM entries ORDER BY ord"):
            obj = json.loads(str(payload))
            if isinstance(obj, dict):
                yield obj
    finally:
        conn.close()


def iter_staged_lemma_ids(path: Path) -> Iterator[tuple[str, str]]:
    """Yield (lemma_id, lemma) in deterministic order from a staged SQLite manifest."""
    conn = sqlite3.connect(f"file:{path.resolve().as_posix()}?mode=ro", uri=True)
    try:
        for lemma_id, lemma in conn.execute("SELECT lemma_id, lemma FROM entries ORDER BY ord"):
            yield str(lemma_id), str(lemma)
    finally:
        conn.close()


class StreamingCandidateWriter:
    """Emit candidate manifest incrementally — never accumulate all results."""

    def __init__(self, path: Path, *, meta: dict[str, Any] | None = None) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._tmp = path.with_name(f"{path.name}.tmp")
        self._handle = self._tmp.open("w", encoding="utf-8")
        self._meta = dict(meta or {})
        self._count = 0
        self._first = True
        # Write opening brace + meta keys, then entries array.
        self._handle.write("{\n")
        for key, value in self._meta.items():
            self._handle.write(
                f"  {json.dumps(key, ensure_ascii=False)}: "
                f"{json.dumps(value, ensure_ascii=False)},\n"
            )
        self._handle.write('  "entries": [\n')

    def write_entry(self, entry: dict[str, Any]) -> None:
        if not self._first:
            self._handle.write(",\n")
        self._first = False
        payload = json.dumps(entry, ensure_ascii=False, indent=2)
        indented = "\n".join("    " + line if line else line for line in payload.splitlines())
        self._handle.write(indented)
        self._count += 1

    def close(self) -> str:
        self._handle.write("\n  ]\n}\n")
        self._handle.flush()
        self._handle.close()
        self._tmp.replace(self.path)
        return _sha256_text(self.path.read_text(encoding="utf-8"))

    def __enter__(self) -> StreamingCandidateWriter:
        return self

    def __exit__(self, *exc: object) -> None:
        if not self._handle.closed:
            self.close()
