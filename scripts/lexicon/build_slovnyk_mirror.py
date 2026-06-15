#!/usr/bin/env python3
"""Build-time slovnyk.me mirror for the Word Atlas (#3097).

Politely pre-populates the per-lemma slovnyk.me cache (`data/lexicon/slovnyk_cache/`,
gitignored) for every manifest lemma, so a later `enrich_manifest` run reads cache hits
instead of live-fetching. This converts the ~96-min-every-run live-fetch tax into a
one-time, resumable scrape.

Why this exists: slovnyk.me is Cloudflare-fronted and 429-rate-limits bursts. The old
0.12s delay tripped it, and `_SlovnykTransientError` results were never cached, so every
enrich re-fetched ~1000 lemmas. This builder reuses the now-429-friendly
`enrich_manifest._fetch_slovnyk_entry` (Retry-After + exponential backoff) at a polite,
configurable rate.

Resumable: fully-cached lemmas are skipped; a partially-cached lemma fetches only its
missing dictionary slugs. Safe to Ctrl-C and re-run — each lemma's cache is written as it
completes.

Usage:
    .venv/bin/python -m scripts.lexicon.build_slovnyk_mirror              # full run
    .venv/bin/python -m scripts.lexicon.build_slovnyk_mirror --limit 5    # small test batch
    LEXICON_SLOVNYK_DELAY=0.5 .venv/bin/python -m scripts.lexicon.build_slovnyk_mirror
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from scripts.lexicon.enrich_manifest import (
    _SLOVNYK_LOOKUP_SLUGS,
    MANIFEST,
    _load_slovnyk_cache_file,
    _slovnyk_cache,
    _slovnyk_cache_path,
    _slovnyk_lookup_word,
)


def _is_fully_cached(lemma: str) -> bool:
    """True if every dictionary slug for ``lemma`` is already cached (any value, incl. miss)."""
    cache = _load_slovnyk_cache_file(_slovnyk_cache_path(lemma))
    if not cache or cache.get("lookup_word") != _slovnyk_lookup_word(lemma):
        return False
    lookups = cache.get("lookups")
    if not isinstance(lookups, dict):
        return False
    return all(slug in lookups for slug in _SLOVNYK_LOOKUP_SLUGS)


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
    parser = argparse.ArgumentParser(description="Build-time slovnyk.me mirror (#3097).")
    parser.add_argument("--manifest", type=Path, default=MANIFEST, help="Atlas manifest JSON.")
    parser.add_argument("--limit", type=int, default=None, help="Cap lemmas processed (testing).")
    parser.add_argument("--progress-every", type=int, default=25, help="Progress log cadence.")
    args = parser.parse_args(argv)

    lemmas = _manifest_lemmas(args.manifest)
    todo = [lemma for lemma in lemmas if not _is_fully_cached(lemma)]
    print(
        f"manifest lemmas={len(lemmas)} already-cached={len(lemmas) - len(todo)} "
        f"to-fetch={len(todo)} slugs/lemma={len(_SLOVNYK_LOOKUP_SLUGS)}",
        flush=True,
    )
    if args.limit is not None:
        todo = todo[: args.limit]
        print(f"--limit {args.limit}: processing {len(todo)} lemma(s)", flush=True)

    fetched = errors = 0
    start = time.monotonic()
    for i, lemma in enumerate(todo, 1):
        try:
            _slovnyk_cache(lemma)
            fetched += 1
        except Exception as exc:  # log and continue; builder must be resumable
            errors += 1
            print(f"  ERROR {lemma!r}: {type(exc).__name__}: {exc}", flush=True)
        if i % args.progress_every == 0 or i == len(todo):
            elapsed = time.monotonic() - start
            rate = i / elapsed if elapsed else 0.0
            eta_min = (len(todo) - i) / rate / 60 if rate else 0.0
            print(
                f"  [{i}/{len(todo)}] fetched={fetched} errors={errors} "
                f"{rate:.2f} lemma/s ETA {eta_min:.1f}m",
                flush=True,
            )

    elapsed_min = (time.monotonic() - start) / 60
    print(f"DONE fetched={fetched} errors={errors} of {len(todo)} in {elapsed_min:.1f}m", flush=True)
    print(
        "Re-run any time to fill gaps (resumable). A subsequent `make atlas` enrich now "
        "reads cache hits instead of live-fetching.",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
