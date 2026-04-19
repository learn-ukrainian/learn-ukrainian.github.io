#!/usr/bin/env python3
"""Cold-encode retrieval corpora into manifest-backed embedding shards."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from wiki.dense_rerank import (
        DEFAULT_DB_PATH,
        DEFAULT_MANIFEST_DB,
        SUPPORTED_CORPORA,
        cold_encode_corpus,
        load_corpus_units,
    )
    from wiki.embedding_manifest import EmbeddingManifest, filter_new_or_changed
else:
    from .dense_rerank import (
        DEFAULT_DB_PATH,
        DEFAULT_MANIFEST_DB,
        SUPPORTED_CORPORA,
        cold_encode_corpus,
        load_corpus_units,
    )
    from .embedding_manifest import EmbeddingManifest, filter_new_or_changed


def _emit(event: dict) -> None:
    print(json.dumps(event, ensure_ascii=False), flush=True)


def _parse_corpora(args: argparse.Namespace) -> list[str]:
    if args.all_corpora:
        return list(SUPPORTED_CORPORA)
    assert args.corpora
    return [corpus.strip() for corpus in args.corpora.split(",") if corpus.strip()]


def _dry_run_summary(corpus: str, *, db_path: Path, manifest_db: Path) -> dict:
    units = load_corpus_units(corpus, db_path=db_path)
    manifest = EmbeddingManifest(manifest_db)
    try:
        new_keys, stale_keys = filter_new_or_changed(
            manifest,
            corpus=corpus,
            candidates=[(unit.unit_key, unit.text_sha256) for unit in units],
        )
        return {
            "event": "dry_run",
            "corpus": corpus,
            "total_units": len(units),
            "new_units": len(new_keys),
            "stale_units": len(stale_keys),
            "up_to_date": not new_keys and not stale_keys,
        }
    finally:
        manifest.close()


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Cold-encode wiki retrieval corpora into manifest-backed shards.",
    )
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument(
        "--all-corpora",
        action="store_true",
        help="Encode all supported corpora in sequence.",
    )
    target.add_argument(
        "--corpora",
        help="Comma-separated corpus list, e.g. textbook_sections,modern_literary.",
    )
    parser.add_argument("--resume", action="store_true", help="Skip already-encoded units using the manifest.")
    parser.add_argument("--dry-run", action="store_true", help="Inspect pending work without writing shards.")
    parser.add_argument("--db-path", type=Path, default=DEFAULT_DB_PATH, help="Override sources.db path.")
    parser.add_argument(
        "--manifest-db",
        type=Path,
        default=DEFAULT_MANIFEST_DB,
        help="Override embedding manifest path.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    corpora = _parse_corpora(args)

    if args.dry_run:
        for corpus in corpora:
            _emit(_dry_run_summary(corpus, db_path=args.db_path, manifest_db=args.manifest_db))
        return 0

    if "MEMORY_FRACTION_OVERRIDE" in os.environ:
        _emit(
            {
                "event": "memory_fraction_override",
                "value": os.environ["MEMORY_FRACTION_OVERRIDE"],
            }
        )

    for corpus in corpora:
        summary = cold_encode_corpus(
            corpus,
            db_path=args.db_path,
            manifest_db=args.manifest_db,
            resume=args.resume,
            progress_callback=_emit,
        )
        if summary.get("status") == "up_to_date":
            _emit({"event": "up_to_date", **summary})

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
