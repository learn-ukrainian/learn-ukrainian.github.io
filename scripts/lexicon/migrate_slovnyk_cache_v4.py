#!/usr/bin/env python3
"""Purge stale slovnyk.me cache rows predating the v4 known-miss reset.

Offline replay of the #6809 zero-fill diagnosis found that ~57% of a random
40-slug sample of cached ``ukreng: null`` rows (fetched Aug 14-15) are
contradicted by a live slovnyk.me lookup today -- the page has a ``ukreng``
sense, the cache just recorded a miss. ``_slovnyk_cache()`` has no TTL or
re-attest path for a cached miss: once a lookup slug is recorded ``None`` for
a lemma, nothing ever asks slovnyk.me again for that (lemma, slug) pair. #6840
fixed two deterministic extraction bugs that fed this same zero-gloss symptom,
but that only helps *future* fetches -- it cannot retroactively un-miss a
lookup slovnyk.me was never asked to redo.

``scripts/lexicon/enrich_manifest.py`` already migrates this lazily: bumping
``_SLOVNYK_CACHE_SCHEMA_VERSION`` to 4 makes ``_slovnyk_cache()`` reset any
non-current cache file (every v1/v2/v3 row, known-miss or not) to empty
``lookups`` and refetch on its next touch -- same lever as the v3 precedent
(#6524). This script applies that same reset directly to every file on disk
right now (no network access needed -- it only drops the stale ``lookups``,
it does not refetch), so the residue is gone immediately instead of only
self-healing one lemma at a time as future runs happen to touch it.

Idempotent: a file already at the current schema version is left untouched.
Discards ``lookups`` wholesale per file, not selectively -- a v3 row carries
no marker distinguishing a false-negative ``ukreng: null`` from a genuine
miss on another slug, so this does not try to guess (no heuristics, #1).

The live refetch of the ~19k-slug corpus this reset makes retryable is a
separate, later drive step -- this script (and the schema bump) only make
existing on-disk rows retryable; running it does not hit the network.

    .venv/bin/python scripts/lexicon/migrate_slovnyk_cache_v4.py [--cache-dir PATH] [--dry-run]
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# NOTE: this pulls in `requests` (enrich_manifest is a runtime module, not the
# minimal-deps CI freshness-gate import) -- fine for a manually-run maintenance
# script; see migrate_source_labels.py's NOTE for the module this pattern avoids.
from scripts.lexicon.enrich_manifest import (
    _SLOVNYK_CACHE_SCHEMA_VERSION,
    _default_slovnyk_cache,
)


def scan(cache_dir: Path) -> Counter[str]:
    """Count cache files by migration status without modifying anything."""
    counts: Counter[str] = Counter()
    for path in sorted(cache_dir.glob("*.json")):
        counts["total"] += 1
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            counts["malformed"] += 1
            continue
        if not isinstance(payload, dict):
            counts["malformed"] += 1
            continue
        version = payload.get("schema_version")
        if version == _SLOVNYK_CACHE_SCHEMA_VERSION:
            counts["already_current"] += 1
        else:
            counts[f"stale_v{version!r}"] += 1
            counts["stale_total"] += 1
    return counts


def migrate(cache_dir: Path, *, dry_run: bool) -> Counter[str]:
    """Discard ``lookups`` in every non-current cache file; bump its schema_version.

    Preserves ``lemma``/``lookup_word``/``fetched_at`` so the file is still a valid
    (now-empty) cache entry that ``_slovnyk_cache()`` will happily refetch into on
    its next live touch. Malformed files are left alone (not this migration's job).
    """
    counts: Counter[str] = Counter()
    for path in sorted(cache_dir.glob("*.json")):
        counts["total"] += 1
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            counts["malformed"] += 1
            continue
        if not isinstance(payload, dict):
            counts["malformed"] += 1
            continue
        if payload.get("schema_version") == _SLOVNYK_CACHE_SCHEMA_VERSION:
            counts["already_current"] += 1
            continue

        counts["migrated"] += 1
        if dry_run:
            continue
        migrated: dict[str, Any] = {
            "schema_version": _SLOVNYK_CACHE_SCHEMA_VERSION,
            "lemma": payload.get("lemma", path.stem),
            "lookup_word": payload.get("lookup_word", payload.get("lemma", path.stem)),
            "fetched_at": payload.get("fetched_at", ""),
            "lookups": {},
        }
        path.write_text(json.dumps(migrated, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return counts


def _print_counts(label: str, counts: Counter[str]) -> None:
    print(f"{label}:")
    for key in sorted(counts):
        print(f"  {key}: {counts[key]}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--cache-dir",
        type=Path,
        default=None,
        help="Override the slovnyk cache directory (defaults to the resolved SLOVNYK_CACHE path).",
    )
    parser.add_argument("--dry-run", action="store_true", help="Report what would change without writing.")
    parser.add_argument(
        "--scan-only",
        action="store_true",
        help="Only print the current schema_version distribution; write nothing.",
    )
    args = parser.parse_args()

    cache_dir = args.cache_dir or _default_slovnyk_cache()
    if not cache_dir.exists():
        print(f"No cache directory at {cache_dir}; nothing to migrate.")
        return 0

    if args.scan_only:
        _print_counts(f"scan ({cache_dir})", scan(cache_dir))
        return 0

    before = scan(cache_dir)
    _print_counts(f"before ({cache_dir})", before)

    counts = migrate(cache_dir, dry_run=args.dry_run)
    _print_counts("dry-run result" if args.dry_run else "migrated", counts)

    if not args.dry_run:
        after = scan(cache_dir)
        _print_counts(f"after ({cache_dir})", after)
        if after.get("stale_total"):
            print("FAIL: stale (non-current schema_version) rows remain after migration.", file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
