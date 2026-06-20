#!/usr/bin/env python3
"""DB-free gate: block shipping a thin/un-enriched Atlas lexicon manifest (#3658).

Root-cause prevention for the #3631 empty-atlas regression class. A manifest built
via ``build_data_manifest`` WITHOUT a subsequent ``enrich_manifest`` pass ships with
``enrichment_generated`` False and ~0 enriched entries — which renders an empty Word
Atlas even though every CI fingerprint/freshness check stays green (the fingerprint
covers lexicon *code*, not manifest *content*). #3631 did exactly this: enrichment
dropped from ~2499/4148 to 0 and the regression reached main; #3654 restored it.

This gate inspects the committed ``site/src/data/lexicon-manifest.json`` and FAILS
when it is thin, so the empty-atlas class can never reach main again. It is DB-free
and reads only the committed JSON, so it runs in CI (unlike the DB-dependent
``scripts/audit/validate_atlas_conformance.py``).

NOTE: deliberately NOT placed under ``scripts/lexicon/`` — that dir is hashed by the
manifest code-fingerprint (``LEXICON_CODE_GLOB``), so a check-only file there would
spuriously force a ``make atlas`` regen on every edit.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MANIFEST = ROOT / "site" / "src" / "data" / "lexicon-manifest.json"

# The #3631 regression was a cliff: ~85% enriched -> 0%. Healthy manifests have
# historically run 60-85% enriched. A 0.40 floor decisively separates a thin
# manifest (0%) from any legitimate state while leaving wide margin against false
# positives as the lexicon grows. Tune via --min-ratio if enrichment coverage
# legitimately shifts.
MIN_ENRICHED_RATIO = 0.40


def check_enrichment(
    *,
    manifest_path: Path = DEFAULT_MANIFEST,
    min_ratio: float = MIN_ENRICHED_RATIO,
) -> int:
    """Return 0 when the manifest is adequately enriched, non-zero otherwise."""
    if not manifest_path.exists():
        print(f"::error::Atlas manifest missing at {manifest_path}; run `make atlas`.")
        return 2

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"::error::Atlas manifest unreadable ({exc}); run `make atlas`.")
        return 2

    entries = manifest.get("entries") or []
    total = len(entries)
    if total == 0:
        print("::error::Atlas manifest has 0 entries — thin/empty manifest; run `make atlas`.")
        return 2

    enriched = sum(1 for e in entries if isinstance(e, dict) and e.get("enrichment"))
    ratio = enriched / total
    flag = manifest.get("enrichment_generated")

    problems: list[str] = []
    if flag is not True:
        problems.append(f"enrichment_generated={flag!r} (expected True)")
    if ratio < min_ratio:
        problems.append(
            f"enriched ratio {ratio:.1%} ({enriched}/{total}) below floor {min_ratio:.0%}"
        )

    if problems:
        print(
            "::error::Atlas manifest is thin/un-enriched — refusing to ship "
            "(empty-atlas regression class #3631/#3658): " + "; ".join(problems)
        )
        print(
            "Fix: re-run enrichment (`make atlas`, or enrich_manifest against the warm "
            "slovnyk cache) and recommit site/src/data/lexicon-manifest.json."
        )
        return 2

    print(
        f"Atlas manifest enrichment OK: {enriched}/{total} entries enriched "
        f"({ratio:.1%}); enrichment_generated=True."
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Block shipping a thin/un-enriched Atlas lexicon manifest (#3658)."
    )
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST, help="Manifest JSON path.")
    parser.add_argument(
        "--min-ratio",
        type=float,
        default=MIN_ENRICHED_RATIO,
        help="Minimum fraction of entries that must carry enrichment.",
    )
    args = parser.parse_args()
    manifest = args.manifest
    if not manifest.is_absolute():
        manifest = ROOT / manifest
    return check_enrichment(manifest_path=manifest, min_ratio=args.min_ratio)


if __name__ == "__main__":
    raise SystemExit(main())
