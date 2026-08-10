#!/usr/bin/env python3
"""Generate hash-sharded VESUM form→lemma(s) JSON shards (#5882 residual).

Fable GO SHARDED-EXACT design (batch_state/atlas-driver — 2026-08-10):
build-time hash-sharded form→lemma(s) map from ``data/vesum.db``, ~4096
shards, so the paste-text deck wizard can classify a pasted word as a known
Ukrainian word FORM (VESUM-attested, no Atlas entry yet) rather than lumping
it in with genuinely unverified strings.

The shard payloads are NOT committed to git — VESUM has ~6.7M forms and the
full shard set can run 40-60MB gzipped, and this repo does not commit
generated blobs of that size (see ``docs/best-practices/git-hygiene.md``).
This script is the "generate from local VESUM" step: it writes shard files
directly to a static-hosting directory (``site/public/lexicon/vesum-forms/``
by default, gitignored — same pattern as the Atlas search shards written by
``scripts/audit/generate_search_index.py`` into ``site/public/lexicon/search/``).
The client (``site/src/lib/lexicon/vesum-form-shard.ts``) fetches ONE shard
per lookup at runtime; a fetch failure degrades that lookup rather than
failing the whole paste-text flow (never invent, lose recall not precision).

Client-side shard selection uses the SAME normalized key + hash as this
generator (``scripts/lexicon/vesum_form_key.py`` / the TypeScript twin
``site/src/lib/lexicon/vesum-form-key.ts``) — keep both in lockstep; parity
is golden-tested via ``vesum_form_key_vectors.json``.

Every shard id in ``[0, shard_count)`` is always written (even an empty
``{}``), so a missing shard file at runtime is unambiguously a publish/fetch
problem, never a legitimate "no VESUM forms hashed here".

Usage:
    .venv/bin/python -m scripts.lexicon.generate_vesum_form_shards
    .venv/bin/python -m scripts.lexicon.generate_vesum_form_shards \\
        --db-path tests/fixtures/vesum_sample.db \\
        --out-dir /tmp/vesum-form-shards --shard-count 64
"""

from __future__ import annotations

import argparse
import gzip
import json
import sqlite3
import sys
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path

from scripts.lexicon.vesum_form_key import (
    VESUM_FORM_SHARD_COUNT,
    vesum_form_key,
    vesum_shard_id,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB_PATH = PROJECT_ROOT / "data" / "vesum.db"
DEFAULT_OUT_DIR = PROJECT_ROOT / "site" / "public" / "lexicon" / "vesum-forms"
DEFAULT_MANIFEST_OUT = DEFAULT_OUT_DIR / "_manifest.json"

MANIFEST_SCHEMA = "atlas-vesum-form-shards"
MANIFEST_SCHEMA_VERSION = 1

# Size budget (binding design point 8) — fail loud, never silently ship an
# oversized deploy artifact past the gate.
MAX_TOTAL_GZ_BYTES = 60 * 1024 * 1024
MAX_SHARD_P95_GZ_BYTES = 25 * 1024


class ShardSizeBudgetError(RuntimeError):
    """Raised when the generated shard set exceeds the committed size budget."""


def _read_forms(db_path: Path) -> dict[str, set[str]]:
    """``form_key -> {lemma, ...}`` from the VESUM ``forms`` table."""
    if not db_path.exists():
        raise FileNotFoundError(f"VESUM database not found at {db_path}")
    conn = sqlite3.connect(str(db_path))
    try:
        by_key: dict[str, set[str]] = defaultdict(set)
        for word_form, lemma in conn.execute("SELECT word_form, lemma FROM forms"):
            if not word_form or not lemma:
                continue
            key = vesum_form_key(word_form)
            if not key:
                continue
            by_key[key].add(lemma.strip())
        return by_key
    finally:
        conn.close()


def _shard_payloads(by_key: dict[str, set[str]], shard_count: int) -> dict[str, dict[str, list[str]]]:
    shards: dict[str, dict[str, list[str]]] = {format(i, "03x"): {} for i in range(shard_count)}
    for form_key, lemmas in by_key.items():
        shard = vesum_shard_id(form_key, shard_count)
        shards[shard][form_key] = sorted(lemmas)
    return shards


def _percentile(values: list[int], pct: float) -> int:
    if not values:
        return 0
    ordered = sorted(values)
    index = min(len(ordered) - 1, round(pct * (len(ordered) - 1)))
    return ordered[index]


def generate(
    db_path: Path = DEFAULT_DB_PATH,
    out_dir: Path = DEFAULT_OUT_DIR,
    manifest_out: Path = DEFAULT_MANIFEST_OUT,
    shard_count: int = VESUM_FORM_SHARD_COUNT,
    enforce_budget: bool = True,
) -> dict:
    by_key = _read_forms(db_path)
    shards = _shard_payloads(by_key, shard_count)

    out_dir.mkdir(parents=True, exist_ok=True)
    gz_sizes: list[int] = []
    total_gz_bytes = 0
    for shard_id, payload in shards.items():
        body = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
        (out_dir / f"{shard_id}.json").write_text(body, encoding="utf-8")
        gz_size = len(gzip.compress(body.encode("utf-8"), compresslevel=9))
        gz_sizes.append(gz_size)
        total_gz_bytes += gz_size

    shard_p95_gz_bytes = _percentile(gz_sizes, 0.95)
    non_empty_shards = sum(1 for payload in shards.values() if payload)

    if enforce_budget:
        problems = []
        if total_gz_bytes > MAX_TOTAL_GZ_BYTES:
            problems.append(f"total shard set {total_gz_bytes} gz bytes exceeds budget {MAX_TOTAL_GZ_BYTES}")
        if shard_p95_gz_bytes > MAX_SHARD_P95_GZ_BYTES:
            problems.append(f"shard p95 size {shard_p95_gz_bytes} gz bytes exceeds budget {MAX_SHARD_P95_GZ_BYTES}")
        if problems:
            raise ShardSizeBudgetError("; ".join(problems))

    manifest = {
        "schema": MANIFEST_SCHEMA,
        "schemaVersion": MANIFEST_SCHEMA_VERSION,
        "generatedAt": datetime.now(UTC).isoformat(),
        "hashAlgorithm": "fnv1a32",
        "shardCount": shard_count,
        "shardsWritten": len(shards),
        "nonEmptyShards": non_empty_shards,
        "totalForms": len(by_key),
        "sizeBudget": {
            "totalGzBytes": total_gz_bytes,
            "shardP95GzBytes": shard_p95_gz_bytes,
            "maxTotalGzBytes": MAX_TOTAL_GZ_BYTES,
            "maxShardP95GzBytes": MAX_SHARD_P95_GZ_BYTES,
            "enforced": enforce_budget,
        },
    }
    manifest_out.parent.mkdir(parents=True, exist_ok=True)
    manifest_out.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db-path", type=Path, default=DEFAULT_DB_PATH)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--manifest-out", type=Path, default=None)
    parser.add_argument("--shard-count", type=int, default=VESUM_FORM_SHARD_COUNT)
    parser.add_argument(
        "--no-enforce-budget",
        action="store_true",
        help="Skip the size-budget gate (debugging only; never use for a real publish).",
    )
    args = parser.parse_args()
    manifest_out = args.manifest_out or (args.out_dir / "_manifest.json")

    try:
        manifest = generate(
            db_path=args.db_path,
            out_dir=args.out_dir,
            manifest_out=manifest_out,
            shard_count=args.shard_count,
            enforce_budget=not args.no_enforce_budget,
        )
    except ShardSizeBudgetError as exc:
        print(f"FAIL: VESUM form shard size budget exceeded: {exc}", file=sys.stderr)
        sys.exit(1)

    budget = manifest["sizeBudget"]
    print(
        f"✓ wrote {manifest['nonEmptyShards']}/{manifest['shardsWritten']} non-empty "
        f"VESUM form shards ({manifest['totalForms']} forms, "
        f"{budget['totalGzBytes'] / (1024 * 1024):.1f} MB gz total, "
        f"p95 shard {budget['shardP95GzBytes'] / 1024:.1f} KB gz) under {args.out_dir}"
    )


if __name__ == "__main__":
    main()
