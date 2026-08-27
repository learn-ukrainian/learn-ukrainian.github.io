#!/usr/bin/env python3
"""Fill slovnyk.me СУМ-20 (newsum) cache entries using curl.

Bypasses Cloudflare automated client challenges by using curl with a polite
Atlas User-Agent and rate limiting (~0.3s delay).
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import subprocess
import sys
import time
import urllib.parse
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.lexicon.enrich_manifest import (
    _SLOVNYK_CACHE_SCHEMA_VERSION,
    _load_slovnyk_cache_file,
    _parse_slovnyk_entry,
    _slovnyk_cache_path,
    _slovnyk_lookup_word,
)

USER_AGENT = "learn-ukrainian-word-atlas/1.0"


def fetch_newsum_curl(
    word: str,
    *,
    user_agent: str = USER_AGENT,
    timeout: int = 15,
) -> tuple[int, str]:
    url = f"https://slovnyk.me/dict/newsum/{urllib.parse.quote(word)}"
    cmd = [
        "curl",
        "-s",
        "-w",
        "\n%{http_code}",
        "-A",
        user_agent,
        "--max-time",
        str(timeout),
        url,
    ]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout + 5)
    except subprocess.TimeoutExpired:
        return 0, ""
    if res.returncode != 0:
        return 0, ""
    parts = res.stdout.rsplit("\n", 1)
    if len(parts) == 2:
        body, code_str = parts
        try:
            return int(code_str.strip()), body
        except ValueError:
            return 0, body
    return 0, ""


def fill_slovnyk_newsum_cache(
    slugs: list[str],
    *,
    work_dir: Path | None = None,
    sleep_seconds: float = 0.3,
    consecutive_403_limit: int = 20,
    checkpoint_interval: int = 50,
    force: bool = False,
) -> dict[str, Any]:
    if work_dir is not None:
        work_dir.mkdir(parents=True, exist_ok=True)

    stats = {
        "total": len(slugs),
        "already_cached": 0,
        "fetched_ok": 0,
        "not_found_404": 0,
        "cf_challenge_403": 0,
        "other_error": 0,
    }

    consecutive_403 = 0

    for idx, slug in enumerate(slugs, 1):
        path = _slovnyk_cache_path(slug)
        existing_cache = _load_slovnyk_cache_file(path)
        lookup_word = _slovnyk_lookup_word(slug)

        if not force and existing_cache and existing_cache.get("schema_version") == _SLOVNYK_CACHE_SCHEMA_VERSION:
            lookups = existing_cache.get("lookups")
            if isinstance(lookups, dict):
                newsum = lookups.get("newsum")
                if isinstance(newsum, dict) and newsum.get("text"):
                    stats["already_cached"] += 1
                    if idx % checkpoint_interval == 0 or idx == len(slugs):
                        print(
                            f"[{idx}/{len(slugs)}] Progress: cached={stats['already_cached']}, "
                            f"fetched_ok={stats['fetched_ok']}, 404={stats['not_found_404']}, "
                            f"403={stats['cf_challenge_403']}"
                        )
                    continue

        url = f"https://slovnyk.me/dict/newsum/{urllib.parse.quote(lookup_word)}"
        code, body = fetch_newsum_curl(lookup_word)

        if code == 403 or "Just a moment..." in body or "<title>Just a moment...</title>" in body:
            consecutive_403 += 1
            stats["cf_challenge_403"] += 1
            if consecutive_403 >= consecutive_403_limit:
                blocked_msg = (
                    f"# Blocked: slovnyk.me returned 403 on {consecutive_403} consecutive requests.\n"
                    f"Last requested lemma: {slug} ({lookup_word})\n"
                    f"Timestamp: {dt.datetime.now(dt.UTC).isoformat()}\n"
                )
                if work_dir is not None:
                    (work_dir / "blocked.md").write_text(blocked_msg, encoding="utf-8")
                print(f"ABORT: 403 circuit breaker triggered ({consecutive_403} consecutive 403s)", file=sys.stderr)
                break
        elif code == 200:
            consecutive_403 = 0
            row = _parse_slovnyk_entry(body, lemma=slug, lookup_word=lookup_word, slug="newsum", url=url)
            if row and row.get("text"):
                if not existing_cache or existing_cache.get("schema_version") != _SLOVNYK_CACHE_SCHEMA_VERSION:
                    cache_entry = {
                        "schema_version": _SLOVNYK_CACHE_SCHEMA_VERSION,
                        "lemma": slug,
                        "lookup_word": lookup_word,
                        "fetched_at": dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat(),
                        "lookups": {"newsum": row},
                    }
                else:
                    cache_entry = existing_cache
                    lookups = cache_entry.setdefault("lookups", {})
                    if not isinstance(lookups, dict):
                        lookups = {}
                        cache_entry["lookups"] = lookups
                    lookups["newsum"] = row
                    cache_entry["fetched_at"] = dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat()

                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(json.dumps(cache_entry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                stats["fetched_ok"] += 1
            else:
                stats["other_error"] += 1
        elif code == 404:
            consecutive_403 = 0
            stats["not_found_404"] += 1
            if not existing_cache or existing_cache.get("schema_version") != _SLOVNYK_CACHE_SCHEMA_VERSION:
                cache_entry = {
                    "schema_version": _SLOVNYK_CACHE_SCHEMA_VERSION,
                    "lemma": slug,
                    "lookup_word": lookup_word,
                    "fetched_at": dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat(),
                    "lookups": {"newsum": None},
                }
            else:
                cache_entry = existing_cache
                lookups = cache_entry.setdefault("lookups", {})
                if not isinstance(lookups, dict):
                    lookups = {}
                    cache_entry["lookups"] = lookups
                lookups["newsum"] = None
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(cache_entry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        else:
            consecutive_403 = 0
            stats["other_error"] += 1

        if idx % checkpoint_interval == 0 or idx == len(slugs):
            print(
                f"[{idx}/{len(slugs)}] Progress: cached={stats['already_cached']}, "
                f"fetched_ok={stats['fetched_ok']}, 404={stats['not_found_404']}, "
                f"403={stats['cf_challenge_403']}"
            )

        if sleep_seconds > 0:
            time.sleep(sleep_seconds)

    return stats


def main() -> int:
    parser = argparse.ArgumentParser(description="Populate slovnyk.me СУМ-20 cache using curl.")
    parser.add_argument(
        "--slugs-file",
        type=Path,
        default=PROJECT_ROOT / "batch_state" / "atlas-encyclopedia-easy-vs-dig" / "easy-slugs.json",
        help="JSON file containing array of slugs or audit dump.",
    )
    parser.add_argument(
        "--work-dir",
        type=Path,
        default=PROJECT_ROOT / ".runtime" / "slovnyk-curl",
        help="Directory to save runtime state/blocked.md if tripped.",
    )
    parser.add_argument("--sleep", type=float, default=0.3, help="Polite sleep between requests (seconds).")
    parser.add_argument("--consecutive-403-limit", type=int, default=20, help="Abort on N consecutive 403s.")
    parser.add_argument("--checkpoint-interval", type=int, default=50, help="Log progress every N entries.")
    parser.add_argument("--force", action="store_true", help="Re-fetch even if already cached.")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of slugs to process.")

    args = parser.parse_args()

    slugs_raw = json.loads(args.slugs_file.read_text(encoding="utf-8"))
    if isinstance(slugs_raw, list):
        slugs = [str(s) for s in slugs_raw]
    elif isinstance(slugs_raw, dict) and "class_b_detail" in slugs_raw:
        slugs = [str(e.get("url_slug") or e.get("lemma")) for e in slugs_raw["class_b_detail"]]
    else:
        raise ValueError(f"unrecognized slugs file format: {args.slugs_file}")

    if args.limit is not None:
        slugs = slugs[: args.limit]

    print(f"Starting СУМ-20 curl cache fill for {len(slugs)} slugs...")
    stats = fill_slovnyk_newsum_cache(
        slugs,
        work_dir=args.work_dir,
        sleep_seconds=args.sleep,
        consecutive_403_limit=args.consecutive_403_limit,
        checkpoint_interval=args.checkpoint_interval,
        force=args.force,
    )
    print(f"Finished. Summary: {stats}")
    if stats["cf_challenge_403"] >= args.consecutive_403_limit:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
