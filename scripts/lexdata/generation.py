"""Read-side boundary for a lexdata generation (design r3 §6.3, §6.5, §7.1).

Readers open ``data/lexdata.db`` read-only through ``resolve_store("lexdata")``
and ``open_readonly`` and get either an ``OpenGeneration`` or an
``Unavailable`` reason. The reasons match ``PulsLookup.Withheld`` (§7.1):

- ``lexdata_unavailable``: no store, a refused path, an unreadable file, or
  malformed generation metadata;
- ``lexdata_unpublished``: ``meta.status`` is not ``published`` (or no meta);
- ``normalizer_mismatch``: the reader's normalizer digest differs from the
  generation's, so its query keys could silently miss (§6.3);
- ``lexdata_stale``: the generation schema version, or the per-source
  ``l1_transform_digests`` map, differs from what the reader's own transform
  registry computes now (§6.5). The check always runs: there is no opt-out, and
  a caller selects a registry only through ``binding``;
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
from scripts.lexdata.schema import GENERATION_SCHEMA_VERSION
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


class MetaMalformed(ValueError):
    """The ``meta`` row exists but its JSON fields do not decode to objects."""


_JSON_FIELDS = ("input_manifest", "transform_manifest", "l1_transform_digests", "normalizer_manifest",
                "store_fingerprints", "diff_receipt")


def read_meta(conn: Any) -> dict[str, Any] | None:
    """The decoded ``meta`` row; ``None`` without one; ``MetaMalformed`` when it does not decode."""
    try:
        cursor = conn.execute("SELECT * FROM meta WHERE singleton = 1")
    except Exception:  # a file without meta is simply not a generation
        return None
    row = cursor.fetchone()
    if row is None:
        return None
    meta = dict(zip([column[0] for column in cursor.description], row, strict=True))
    for name in _JSON_FIELDS:
        try:
            meta[name] = json.loads(meta[name])
        except (TypeError, ValueError):
            raise MetaMalformed(name) from None
        if not isinstance(meta[name], dict):
            raise MetaMalformed(name)
    return meta


def current_transform_digests(binding: transforms.TransformBinding) -> dict[str, str]:
    """Per-source ``l1_transform_digest`` this code would build with under ``binding``."""
    return {source_id: transforms.transform_digest(source_id, binding) for source_id in sorted(binding.sources)}


def check_meta(meta: Mapping[str, Any] | None, *, binding: transforms.TransformBinding,
               current_store_fingerprints: Mapping[str, str | None] | None = None) -> str | None:
    """Return the first unavailable reason for ``meta``, or ``None`` when usable."""
    if meta is None or meta.get("status") != "published":
        return "lexdata_unpublished"
    if meta.get("normalizer_digest") != transforms.normalizer_digest(binding):
        return "normalizer_mismatch"
    if meta.get("generation_schema_version") != GENERATION_SCHEMA_VERSION:
        return "lexdata_stale"
    if meta.get("l1_transform_digests") != current_transform_digests(binding):
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
    current_store_fingerprints: Mapping[str, str | None] | None = None,
) -> OpenGeneration | Unavailable:
    """Open the published generation read-only, or say why it is unavailable.

    ``binding`` is the transform registry the reader runs with; the generation
    must have been built under the same normalizer and per-source transform
    digests, or it is unavailable.
    """
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
    opened: OpenGeneration | None = None
    try:
        try:
            meta = read_meta(conn)
        except MetaMalformed:
            return Unavailable("lexdata_unavailable")
        reason = check_meta(meta, binding=binding, current_store_fingerprints=current_store_fingerprints)
        if reason is not None:
            return Unavailable(reason, None if meta is None else meta.get("generation"))
        assert meta is not None
        opened = OpenGeneration(resolved.path, meta["generation"], meta, conn)
        return opened
    finally:
        if opened is None:
            conn.close()
