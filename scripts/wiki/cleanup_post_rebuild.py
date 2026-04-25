#!/usr/bin/env python3
"""Cleanup pass after the #1553 chunk-policy re-encode (step 8).

Runs after step 6 (re-encode) and step 7 (wiki rebuild) have committed
the new manifest state. Drops orphan shards (no live units pointing at
them), VACUUMs the manifest database to reclaim space, and prints a
before/after disk-usage summary.

Idempotent — safe to run multiple times. Will not touch shards that
still have live units in the manifest.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from wiki.embedding_manifest import EmbeddingManifest


def directory_size_bytes(path: Path) -> int:
    if not path.exists():
        return 0
    total = 0
    for entry in path.rglob("*"):
        if entry.is_file():
            try:
                total += entry.stat().st_size
            except OSError:
                continue
    return total


def human_bytes(n: int) -> str:
    size = float(n)
    for unit in ("B", "KiB", "MiB", "GiB"):
        if size < 1024:
            return f"{size:,.1f} {unit}"
        size = size / 1024
    return f"{size:,.1f} TiB"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Drop orphan embedding shards and VACUUM the manifest DB "
            "after #1553 step 6/7. Idempotent and safe to re-run."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  .venv/bin/python scripts/wiki/cleanup_post_rebuild.py\n"
            "  .venv/bin/python scripts/wiki/cleanup_post_rebuild.py --dry-run\n"
            "\n"
            "Outputs:\n"
            "  Stdout: shards removed + VACUUM size delta.\n"
            "\n"
            "Exit codes:\n"
            "  0  always (no-op if nothing to clean).\n"
            "\n"
            "Related:\n"
            "  Issue: #1553 step 8.\n"
            "  Pre-requisites: steps 6 (re-encode) and 7 (wiki rebuild)\n"
            "  must have completed first.\n"
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report what would be removed without modifying anything.",
    )
    args = parser.parse_args(argv)

    manifest = EmbeddingManifest()
    embeddings_dir = manifest.embeddings_dir
    manifest_db_path = embeddings_dir / "manifest.db"

    pre_total_bytes = directory_size_bytes(embeddings_dir)
    pre_manifest_bytes = manifest_db_path.stat().st_size if manifest_db_path.exists() else 0

    if args.dry_run:
        orphan_rows = manifest._conn.execute(
            """
            SELECT COUNT(*) FROM embedding_shards
            WHERE rows = 0
               OR NOT EXISTS (
                    SELECT 1 FROM embedding_units
                    WHERE embedding_units.shard_id = embedding_shards.shard_id
                      AND embedding_units.deleted = 0
               )
            """
        ).fetchone()
        orphan_count = int(orphan_rows[0]) if orphan_rows else 0
        print(f"[dry-run] Would drop {orphan_count} orphan shards.")
        print(f"[dry-run] Would VACUUM manifest.db ({human_bytes(pre_manifest_bytes)} pre-vacuum).")
        manifest.close()
        return 0

    removed = manifest.vacuum_orphaned_shards()
    print(f"Dropped {removed} orphan shard{'s' if removed != 1 else ''}.")

    # Reclaim freed pages — needs to run outside any open transaction.
    manifest._conn.execute("VACUUM")
    manifest._conn.commit()
    manifest.close()

    post_total_bytes = directory_size_bytes(embeddings_dir)
    post_manifest_bytes = manifest_db_path.stat().st_size if manifest_db_path.exists() else 0

    print(
        f"data/embeddings/: {human_bytes(pre_total_bytes)} -> "
        f"{human_bytes(post_total_bytes)} "
        f"(delta {human_bytes(pre_total_bytes - post_total_bytes)})"
    )
    print(
        f"manifest.db: {human_bytes(pre_manifest_bytes)} -> "
        f"{human_bytes(post_manifest_bytes)} "
        f"(delta {human_bytes(pre_manifest_bytes - post_manifest_bytes)})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
