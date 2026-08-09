#!/usr/bin/env python3
"""Migrate deferred decision ledger keys and scrub personal identifier paths.

Deterministically recomputes `source_inventory.key` for scrubbed inventory paths,
scrubs personal identifier tokens from metadata and notes, and emits sharded
decision ledger files.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

# Ensure project root is in sys.path when executed directly
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_SCRIPT_DIR = str(Path(__file__).resolve().parent)
if _SCRIPT_DIR in sys.path:
    sys.path.remove(_SCRIPT_DIR)
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

import yaml

from scripts.audit.source_inventory_review_decisions import source_inventory_key
from scripts.lexicon.content_lexicon_reconciler import PROJECT_ROOT

DEFAULT_SOURCE_LEDGER = (
    PROJECT_ROOT / "data/lexicon/source-inventory-review-decisions" / "2026-07-23-alona-full-document-intake.yaml"
)
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "data/lexicon/source-inventory-review-decisions"
DEFAULT_SCRUBBED_PATH = "data/lexicon/source-inventory/oneshot/private-teacher-lesson-vocabulary-full.yaml"
DEFAULT_NUM_SHARDS = 10


def scrub_decision_row(row: dict[str, Any], scrubbed_inventory_path: str) -> dict[str, Any]:
    """Return a new decision row with updated inventory path and recomputed key.

    Preserves all non-key fields and row structure byte-identical.
    """
    new_row = dict(row)
    source_inv = dict(row["source_inventory"])
    locator = source_inv["locator"]
    lemma = row["lemma"]

    source_inv["path"] = scrubbed_inventory_path
    source_inv["key"] = source_inventory_key(
        lemma=lemma,
        inventory_path=scrubbed_inventory_path,
        locator=locator,
    )
    new_row["source_inventory"] = source_inv
    if "sense_note" in new_row and isinstance(new_row["sense_note"], str):
        new_row["sense_note"] = new_row["sense_note"].replace("Alona document", "full document")
    return new_row


def generate_scrubbed_shards(
    payload: dict[str, Any],
    num_shards: int = DEFAULT_NUM_SHARDS,
    scrubbed_inventory_path: str = DEFAULT_SCRUBBED_PATH,
) -> list[dict[str, Any]]:
    """Split and scrub decision payload into N shard payloads."""
    decisions = payload.get("decisions", [])
    total_rows = len(decisions)
    if num_shards <= 0:
        raise ValueError("num_shards must be positive")

    chunk_size = (total_rows + num_shards - 1) // num_shards
    shards: list[dict[str, Any]] = []

    for i in range(num_shards):
        start = i * chunk_size
        end = min((i + 1) * chunk_size, total_rows)
        chunk = decisions[start:end]

        scrubbed_chunk = [scrub_decision_row(row, scrubbed_inventory_path) for row in chunk]

        batch_id = f"source-inventory-teacher-lesson-full-document-2026-07-23-batch-{i + 1:02d}"
        batch_label = f"Teacher-lesson full document intake (batch {i + 1:02d} of {num_shards:02d})"

        shard_payload = {
            "version": payload.get("version", 1),
            "kind": payload.get("kind", "atlas_source_inventory_review_decisions"),
            "batch_id": batch_id,
            "batch_label": batch_label,
            "reviewer": "operator-teacher-lesson-document-trust",
            "reviewed_at": payload.get("reviewed_at", "2026-07-23"),
            "source_queue": {
                "workflow": "source_inventory_publish_review_queue.v1",
                "total_queue_rows": total_rows,
                "approved_in_queue": len(scrubbed_chunk),
                "promotion_batch_size": len(scrubbed_chunk),
            },
            "production_outputs_updated": payload.get("production_outputs_updated", []),
            "decisions": scrubbed_chunk,
        }
        shards.append(shard_payload)

    return shards


def migrate_ledger_to_shards(
    source_ledger_path: Path = DEFAULT_SOURCE_LEDGER,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    num_shards: int = DEFAULT_NUM_SHARDS,
    scrubbed_inventory_path: str = DEFAULT_SCRUBBED_PATH,
    dry_run: bool = False,
) -> list[Path]:
    """Read source ledger, generate scrubbed shard payloads, and write YAML files to output_dir."""
    raw_text = source_ledger_path.read_text(encoding="utf-8")
    payload = yaml.safe_load(raw_text)

    shard_payloads = generate_scrubbed_shards(
        payload=payload,
        num_shards=num_shards,
        scrubbed_inventory_path=scrubbed_inventory_path,
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    written_paths: list[Path] = []

    for i, shard_payload in enumerate(shard_payloads, start=1):
        filename = f"2026-07-23-teacher-lesson-full-document-intake-batch-{i:02d}.yaml"
        target_path = output_dir / filename
        written_paths.append(target_path)

        if not dry_run:
            yaml_text = yaml.dump(shard_payload, sort_keys=False, allow_unicode=True)
            target_path.write_text(yaml_text, encoding="utf-8")

    return written_paths


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Migrate source inventory review decisions to scrubbed sharded files.")
    parser.add_argument(
        "--source-ledger",
        type=Path,
        default=DEFAULT_SOURCE_LEDGER,
        help="Path to unscrubbed input decision ledger YAML",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory to write scrubbed shard YAML files into",
    )
    parser.add_argument(
        "--num-shards",
        type=int,
        default=DEFAULT_NUM_SHARDS,
        help="Number of shard files to divide decisions into",
    )
    parser.add_argument(
        "--scrubbed-path",
        type=str,
        default=DEFAULT_SCRUBBED_PATH,
        help="Scrubbed source inventory relative path string",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Compute and report shard metrics without writing files to disk",
    )
    args = parser.parse_args(argv)

    if not args.source_ledger.is_file():
        print(f"Error: source ledger not found at {args.source_ledger}", file=sys.stderr)
        return 1

    written = migrate_ledger_to_shards(
        source_ledger_path=args.source_ledger,
        output_dir=args.output_dir,
        num_shards=args.num_shards,
        scrubbed_inventory_path=args.scrubbed_path,
        dry_run=args.dry_run,
    )

    action_str = "Would write" if args.dry_run else "Wrote"
    print(f"✅ {action_str} {len(written)} scrubbed shard file(s) to {args.output_dir}:")
    for path in written:
        print(f"  - {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
