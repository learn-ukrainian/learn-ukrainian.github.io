#!/usr/bin/env python3
"""RAG coverage recheck: identify modules with unverified quotes.

Scans completed modules in a track, extracts quotes from markdown content,
searches each against the literary RAG collection, and reports which modules
have unverified quotes (candidates for Phase D re-review).

Usage:
    .venv/bin/python scripts/check_rag_coverage.py c1-bio
    .venv/bin/python scripts/check_rag_coverage.py c1-bio --json
    .venv/bin/python scripts/check_rag_coverage.py --all-seminar
    .venv/bin/python scripts/check_rag_coverage.py c1-bio --threshold 0.4
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPTS_DIR.parent
CURRICULUM_DIR = PROJECT_ROOT / "curriculum" / "l2-uk-en"

sys.path.insert(0, str(SCRIPTS_DIR))

from batch_gemini_config import SEMINAR_TRACKS

# Default similarity threshold for considering a quote "verified"
DEFAULT_THRESHOLD = 0.5


def extract_quotes(content_path: Path) -> list[str]:
    """Extract quoted passages from module markdown.

    Looks for:
    - Text in «» (Ukrainian guillemets), 10-200 chars
    - Blockquote lines starting with > (skip callout markers)
    """
    if not content_path.exists():
        return []

    text = content_path.read_text("utf-8")
    quotes: list[str] = []

    # Ukrainian guillemets «...»
    for match in re.finditer(r"«([^»]{10,200})»", text):
        quotes.append(match.group(1).strip())

    # Blockquote lines (> text) — skip metadata/callout markers
    for match in re.finditer(r"^>\s+(.{10,200})", text, re.MULTILINE):
        line = match.group(1).strip()
        if line.startswith("[!") or line.startswith("**"):
            continue
        quotes.append(line)

    return quotes


def check_module(md_path: Path, threshold: float, search_fn) -> dict:
    """Check a single module's quote verification status.

    Returns dict with: slug, quotes, verified, unverified, action, details
    """
    slug = md_path.stem
    quotes = extract_quotes(md_path)

    if not quotes:
        return {
            "slug": slug,
            "quotes": 0,
            "verified": 0,
            "unverified": 0,
            "action": "OK",
            "details": [],
        }

    verified = 0
    unverified = 0
    details = []

    for quote in quotes:
        try:
            hits = search_fn(quote, limit=1)
        except Exception as e:
            details.append({"quote": quote[:80], "status": "ERROR", "error": str(e)})
            unverified += 1
            continue

        if hits and hits[0].get("score", 0) >= threshold:
            verified += 1
            details.append({
                "quote": quote[:80],
                "status": "VERIFIED",
                "score": hits[0]["score"],
                "work": hits[0].get("work", ""),
            })
        else:
            unverified += 1
            best_score = hits[0]["score"] if hits else 0
            details.append({
                "quote": quote[:80],
                "status": "UNVERIFIED",
                "best_score": best_score,
            })

    # Determine action
    if unverified == 0:
        action = "OK"
    elif verified > 0:
        # Some matched, some didn't — likely RAG has relevant works
        action = "RECHECK"
    else:
        # Nothing matched — RAG probably lacks relevant works for this module
        action = "AWAIT"

    return {
        "slug": slug,
        "quotes": len(quotes),
        "verified": verified,
        "unverified": unverified,
        "action": action,
        "details": details,
    }


def check_track(track: str, threshold: float, search_fn) -> list[dict]:
    """Check all modules in a track."""
    track_dir = CURRICULUM_DIR / track
    if not track_dir.is_dir():
        print(f"Error: track directory not found: {track_dir}", file=sys.stderr)
        return []

    md_files = sorted(track_dir.glob("*.md"))
    if not md_files:
        print(f"Warning: no .md files found in {track_dir}", file=sys.stderr)
        return []

    results = []
    for md_path in md_files:
        result = check_module(md_path, threshold, search_fn)
        results.append(result)

    return results


def print_report(track: str, results: list[dict]) -> None:
    """Print formatted table to stdout."""
    print(f"\n=== RAG Coverage Report: {track} ===\n")

    # Column widths
    slug_w = max((len(r["slug"]) for r in results), default=20)
    slug_w = max(slug_w, 20)

    header = (
        f"| {'Module':<{slug_w}} | Quotes | Verified | Unverified | Action   |"
    )
    sep = (
        f"|{'-' * (slug_w + 2)}|--------|----------|------------|----------|"
    )

    print(header)
    print(sep)

    for r in results:
        print(
            f"| {r['slug']:<{slug_w}} | {r['quotes']:>6} | {r['verified']:>8} | "
            f"{r['unverified']:>10} | {r['action']:<8} |"
        )

    # Summary
    total = len(results)
    recheck = sum(1 for r in results if r["action"] == "RECHECK")
    await_count = sum(1 for r in results if r["action"] == "AWAIT")
    ok = sum(1 for r in results if r["action"] == "OK")
    print(f"\nSummary: {total} modules, {recheck} RECHECK, {await_count} AWAIT, {ok} OK")


def main():
    parser = argparse.ArgumentParser(
        description="Check RAG coverage for module quotes"
    )
    parser.add_argument(
        "track",
        nargs="?",
        help="Track slug (e.g., c1-bio, hist). Required unless --all-seminar.",
    )
    parser.add_argument(
        "--all-seminar",
        action="store_true",
        help="Check all seminar tracks",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output machine-readable JSON",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=DEFAULT_THRESHOLD,
        help=f"Similarity score threshold for 'verified' (default: {DEFAULT_THRESHOLD})",
    )

    args = parser.parse_args()

    if not args.track and not args.all_seminar:
        parser.error("Provide a track name or use --all-seminar")

    # Lazy-import RAG — gracefully degrade if Qdrant is down
    try:
        from rag.query import search_literary
    except ImportError as e:
        print(f"Error: RAG module not available: {e}", file=sys.stderr)
        print("Install qdrant-client and ensure Qdrant is running.", file=sys.stderr)
        sys.exit(1)

    tracks = list(SEMINAR_TRACKS) if args.all_seminar else [args.track]
    # Filter to tracks that actually have directories
    tracks = [t for t in sorted(tracks) if (CURRICULUM_DIR / t).is_dir()]

    all_results: dict[str, list[dict]] = {}
    for track in tracks:
        print(f"Checking {track}...", file=sys.stderr)
        results = check_track(track, args.threshold, search_literary)
        all_results[track] = results

    if args.json:
        # Strip verbose details for compact output, keep action
        compact = {}
        for track, results in all_results.items():
            compact[track] = [
                {k: v for k, v in r.items() if k != "details"} for r in results
            ]
        print(json.dumps(compact, indent=2, ensure_ascii=False))
    else:
        for track, results in all_results.items():
            print_report(track, results)


if __name__ == "__main__":
    main()
