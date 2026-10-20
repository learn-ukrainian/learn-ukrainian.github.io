"""Read-side boundary for a lexdata generation (design r3 §6.3, §6.5, §7.1).

Readers open ``data/lexdata.db`` read-only through ``resolve_store("lexdata")``
and ``open_readonly`` and get either an ``OpenGeneration`` or an
``Unavailable`` reason. The reasons match ``PulsLookup.Withheld`` (§7.1):

- ``lexdata_unavailable``: no store, a refused path, or an unreadable file;
- ``lexdata_unpublished``: ``meta.status`` is not ``published`` (or no meta);
- ``normalizer_mismatch``: the reader's normalizer digest differs from the
  generation's, so its query keys could silently miss (§6.3);
- ``lexdata_stale``: an expected transform digest differs;
- ``identity_store_unavailable`` / ``identity_store_stale``: an identity-store
  fingerprint the generation was built against cannot be computed now, or
  differs (§7.1).

Every resolver and migrated caller must open through ``open_generation``.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from scripts.lexdata import transforms
from scripts.lib.readonly_sqlite import open_readonly
from scripts.storage import topology

UNAVAILABLE_REASONS = frozenset({
    "lexdata_unavailable", "lexdata_unpublished", "normalizer_mismatch", "lexdata_stale",
    "identity_store_unavailable", "identity_store_stale",
})


@dataclass(frozen=True)
class Unavailable:
    reason: str
    generation: str | None = None


@dataclass
class OpenGeneration:
    """A published generation; the caller closes ``conn`` (the inode stays held)."""

    path: Path
    generation: str
    meta: dict[str, Any]
    conn: Any

    def close(self) -> None:
        self.conn.close()


def read_meta(conn: Any) -> dict[str, Any] | None:
    try:
        cursor = conn.execute("SELECT * FROM meta WHERE singleton = 1")
    except Exception:  # a file without meta is simply not a generation
        return None
    row = cursor.fetchone()
    if row is None:
        return None
    meta = dict(zip([column[0] for column in cursor.description], row, strict=True))
    for name in ("input_manifest", "transform_manifest", "l1_transform_digests", "normalizer_manifest",
                 "store_fingerprints", "diff_receipt"):
        meta[name] = json.loads(meta[name])
    return meta


def check_meta(meta: Mapping[str, Any] | None, *, binding: transforms.TransformBinding,
               expected_transform_digests: Mapping[str, str] | None = None,
               current_store_fingerprints: Mapping[str, str | None] | None = None) -> str | None:
    """Return the first unavailable reason for ``meta``, or ``None`` when usable."""
    if meta is None or meta.get("status") != "published":
        return "lexdata_unpublished"
    if meta.get("normalizer_digest") != transforms.normalizer_digest(binding):
        return "normalizer_mismatch"
    if expected_transform_digests is not None:
        built = meta.get("l1_transform_digests", {})
        if any(built.get(source) != digest for source, digest in expected_transform_digests.items()):
            return "lexdata_stale"
    built_stores = meta.get("store_fingerprints", {})
    if built_stores:
        current = current_store_fingerprints or {}
        for store, fingerprint in built_stores.items():
            now = current.get(store)
            if now is None:
                return "identity_store_unavailable"
            if now != fingerprint:
                return "identity_store_stale"
    return None


def open_generation(
    path: Path | None = None,
    *,
    binding: transforms.TransformBinding = transforms.DEFAULT_BINDING,
    repository_root: Path | None = None,
    env: Mapping[str, str] | None = None,
    expected_transform_digests: Mapping[str, str] | None = None,
    current_store_fingerprints: Mapping[str, str | None] | None = None,
) -> OpenGeneration | Unavailable:
    """Open the published generation read-only, or say why it is unavailable."""
    if path is None:
        resolved = topology.resolve_store("lexdata", repository_root, env=env)
    else:
        resolved = topology.resolve_store(
            "lexdata", repository_root, binding=topology.StoreBinding("lexdata", path), env=env)
    if isinstance(resolved, topology.StoreRefusal):
        return Unavailable("lexdata_unavailable")
    try:
        conn = open_readonly(resolved.path)
    except Exception:  # any open failure is unavailability, never a fallback
        return Unavailable("lexdata_unavailable")
    meta = read_meta(conn)
    reason = check_meta(meta, binding=binding, expected_transform_digests=expected_transform_digests,
                        current_store_fingerprints=current_store_fingerprints)
    if reason is not None:
        conn.close()
        return Unavailable(reason, None if meta is None else meta.get("generation"))
    assert meta is not None
    return OpenGeneration(resolved.path, meta["generation"], meta, conn)
