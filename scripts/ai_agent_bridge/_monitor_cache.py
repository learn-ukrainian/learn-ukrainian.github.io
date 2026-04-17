"""Persistent on-disk cache for Monitor API manifest components.

Why this exists (GH #1309): the Monitor API exposes
``/api/state/manifest`` with content hashes for rules + session. An
agent can check the manifest (< 2 KB) and only re-fetch components
whose hash changed since last boot. Without a persistent cache the
manifest hash is useless — every session downloads everything anyway.
This module is the cache.

Design notes:
- Cache lives under ``.agent/cache/monitor/``. Each component is one
  file named by a stable key (``rules.md``, ``session.md``, ...)
  plus a sibling ``*.meta.json`` holding ``{hash, fetched_at, url}``.
- Readers call ``get(key, expected_hash)`` — returns cached body if
  ``expected_hash`` matches, else ``None``. Callers then hit the
  network and call ``put(key, body, hash, url)``.
- No TTL — the MANIFEST hash is the only staleness signal. If the
  hash still matches after 6 months, the cached bytes are still
  authoritative (because the upstream file is unchanged).
- Pure-stdlib. No locking — single-agent per cache dir is fine; the
  network round-trip on miss dwarfs any race-window. If two processes
  write the same key concurrently the "last writer wins" is OK,
  both are fetching the same bytes.
"""

from __future__ import annotations

import contextlib
import json
import os
import tempfile
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CACHE_DIR = _PROJECT_ROOT / ".agent" / "cache" / "monitor"

# Allow environment override for tests / alternate checkouts. Respects
# the XDG-ish pattern but keeps the default repo-relative so a fresh
# clone works without any setup.
_ENV_VAR = "MONITOR_CACHE_DIR"


def cache_dir() -> Path:
    """Resolve the active cache directory. Created on demand by ``put``."""
    override = os.environ.get(_ENV_VAR)
    if override:
        return Path(override).expanduser()
    return DEFAULT_CACHE_DIR


@dataclass(frozen=True)
class CacheEntry:
    """One cached manifest component + provenance."""

    key: str
    body: str
    hash: str
    url: str
    fetched_at: str


def _paths(key: str) -> tuple[Path, Path]:
    base = cache_dir()
    # Key is a simple identifier like 'rules' or 'session'. No path
    # separators allowed — anchor the file name and nothing else.
    safe = key.replace("/", "_").replace("\\", "_")
    return base / f"{safe}.body", base / f"{safe}.meta.json"


def get(key: str, expected_hash: str) -> str | None:
    """Return cached body if the stored hash matches ``expected_hash``.

    ``expected_hash`` comes from the manifest. If it doesn't match
    what we have on disk (or we have nothing), return ``None`` — the
    caller should fetch fresh and call ``put``. Empty ``expected_hash``
    is treated as "cannot validate" and always returns ``None``.
    """
    if not expected_hash:
        return None
    body_path, meta_path = _paths(key)
    if not body_path.is_file() or not meta_path.is_file():
        return None
    try:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if meta.get("hash") != expected_hash:
        return None
    try:
        return body_path.read_text(encoding="utf-8")
    except OSError:
        return None


def put(key: str, body: str, *, body_hash: str, url: str) -> CacheEntry:
    """Write ``body`` to the cache with its associated hash + URL.

    Uses atomic replace so a crash mid-write can't leave a half-file
    visible to the next reader.
    """
    base = cache_dir()
    base.mkdir(parents=True, exist_ok=True)
    body_path, meta_path = _paths(key)

    fetched_at = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    meta = {"hash": body_hash, "fetched_at": fetched_at, "url": url}

    _atomic_write(body_path, body)
    _atomic_write(meta_path, json.dumps(meta, indent=2, sort_keys=True) + "\n")

    return CacheEntry(key=key, body=body, hash=body_hash, url=url, fetched_at=fetched_at)


def _atomic_write(path: Path, text: str) -> None:
    """Write + fsync + rename. Same-dir temp so rename is atomic on POSIX."""
    directory = path.parent
    directory.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=f".{path.name}.", dir=directory)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(text)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, path)
    except Exception:
        # Best-effort cleanup; don't mask the original exception.
        with contextlib.suppress(OSError):
            os.unlink(tmp)
        raise


def invalidate(key: str | None = None) -> int:
    """Drop one cached component or the whole cache.

    ``key=None`` (default) clears every ``*.body`` / ``*.meta.json``
    pair in the cache dir. Returns the number of pairs removed.
    """
    base = cache_dir()
    if not base.is_dir():
        return 0

    pairs_removed = 0
    if key is None:
        targets = list(base.glob("*.body"))
    else:
        body_path, _ = _paths(key)
        targets = [body_path] if body_path.exists() else []

    for body_path in targets:
        meta_path = body_path.with_suffix(".meta.json").with_name(
            body_path.stem + ".meta.json"
        )
        for victim in (body_path, meta_path):
            try:
                victim.unlink()
            except OSError:
                continue
        pairs_removed += 1
    return pairs_removed
