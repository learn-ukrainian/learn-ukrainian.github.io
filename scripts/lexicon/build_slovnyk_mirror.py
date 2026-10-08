#!/usr/bin/env python3
"""Foreground slovnyk.me shared-cache builder with observed outcome reporting.

Use one writer for this legacy cache. Unattended independent dictionary jobs
belong to scripts.ingest.dictionary_acquisition, with isolated durable staging.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from scripts.lexicon.enrich_manifest import (
    _SLOVNYK_LOOKUP_SLUGS,
    MANIFEST,
    _load_current_slovnyk_cache_file,
    _reusable_slovnyk_cache,
    _slovnyk_cache,
    _slovnyk_cache_path,
    _slovnyk_lookup_word,
    _valid_slovnyk_positive,
)


def _is_fully_cached(lemma: str) -> bool:
    """Only current, identity-valid positives prove reusable work; nulls do not."""
    cache = _load_current_slovnyk_cache_file(_slovnyk_cache_path(lemma))
    lookup_word = _slovnyk_lookup_word(lemma)
    return _reusable_slovnyk_cache(cache, lemma, lookup_word) and all(
        _valid_slovnyk_positive(cache["lookups"].get(slug), slug, lookup_word) for slug in _SLOVNYK_LOOKUP_SLUGS
    )


def _manifest_lemmas(manifest_path: Path) -> list[str]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    seen: set[str] = set()
    lemmas: list[str] = []
    for entry in manifest.get("entries", []):
        lemma = entry.get("lemma")
        if lemma and lemma not in seen:
            seen.add(lemma)
            lemmas.append(lemma)
    return lemmas


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Populate the foreground per-lemma shared slovnyk.me cache.\n"
        "Use one writer; use dictionary_acquisition for unattended isolated dictionary jobs.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  .venv/bin/python -m scripts.lexicon.build_slovnyk_mirror --manifest manifest.json --limit 5
  .venv/bin/python -m scripts.lexicon.build_slovnyk_mirror --manifest manifest.json
Outputs: per-lemma JSON in LEXICON_SLOVNYK_CACHE (default data/lexicon/slovnyk_cache);
lookup counts fetched/reused/misses/errors/pending partition the full manifest x dictionary-slug denominator.
Exit codes: 0 all lookups resolved this invocation; 1 unresolved/storage/access/parse failure; 2 usage error.
First access or parse stop ends the run, preserving partial results. Offline/empty lookups stay pending (exit 1).
Legacy nulls are refetched; only observed 404 proves a miss in this invocation. No durable terminal latch.
Related: scripts.ingest.dictionary_acquisition; docs/runbooks/dictionary-acquisition.md; #10003.
""",
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=MANIFEST,
        help="Atlas manifest JSON, e.g. manifest.json (default: Atlas manifest).",
    )
    parser.add_argument(
        "--limit", type=int, default=None, help="Cap lemmas attempted, e.g. 5 (default: all); remainder stays pending."
    )
    parser.add_argument(
        "--progress-every", type=int, default=25, help="Progress log cadence in lemmas (default: 25), e.g. 10."
    )
    args = parser.parse_args(argv)
    if args.progress_every < 1 or (args.limit is not None and args.limit < 0):
        parser.error("limit must be nonnegative and progress-every positive")
    try:
        lemmas = _manifest_lemmas(args.manifest)
    except (OSError, ValueError, TypeError, AttributeError):
        print("ERROR invalid or unavailable manifest", flush=True)
        return 1
    denominator = len(lemmas) * len(_SLOVNYK_LOOKUP_SLUGS)
    counts = dict.fromkeys(("fetched", "reused", "misses", "errors", "pending"), 0)
    counts["pending"] = denominator
    selected = lemmas if args.limit is None else lemmas[: args.limit]
    start = time.monotonic()
    print(f"manifest lemmas={len(lemmas)} denominator={denominator} selected={len(selected)}", flush=True)
    for index, lemma in enumerate(selected, 1):
        outcomes = {}
        try:
            _slovnyk_cache(lemma, outcomes=outcomes, slugs=_SLOVNYK_LOOKUP_SLUGS)
        except (OSError, ValueError, TypeError):
            # No exception bodies/paths: storage failure cannot attest fetched work.
            counts["errors"] += 1
            counts["pending"] -= 1
            break
        terminal = False
        for outcome in outcomes.values():
            key = {"positive": "fetched", "reused": "reused", "not_found": "misses", "pending": "pending"}.get(
                outcome.status, "errors"
            )
            if key != "pending":
                counts[key] += 1
                counts["pending"] -= 1
            if outcome.status in {"blocked", "parse_error", "error"}:
                terminal = True
                print(f"STOP {outcome.status} HTTP={outcome.http_status}", flush=True)
        if index % args.progress_every == 0 or index == len(selected) or terminal:
            print(
                f"[{index}/{len(selected)}] " + " ".join(f"{key}={value}" for key, value in counts.items()), flush=True
            )
        if terminal:
            break
    elapsed = time.monotonic() - start
    print(
        "RESULT "
        + " ".join(f"{key}={value}" for key, value in counts.items())
        + f" denominator={denominator} elapsed={elapsed:.1f}s",
        flush=True,
    )
    return 1 if counts["errors"] or counts["pending"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
