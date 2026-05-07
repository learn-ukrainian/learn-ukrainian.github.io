#!/usr/bin/env python3
"""Discover YouTube videos by channel title regex patterns.

Usage:
    .venv/bin/python scripts/crawl/discover_yt_by_pattern.py \
        --channel "@UkrainianLessons" \
        --pattern-set ulp_grammar_guide
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from wiki.fetch_external_sources import (
    YOUTUBE_CHANNELS,
    YOUTUBE_DISCOVERY_DIR,
    YouTubeRequestLimiter,
    discover_by_title_patterns,
    load_title_pattern_set,
    make_ad_hoc_channel,
    normalize_channel_url,
)


def _normalize_channel_arg(channel: str) -> str:
    value = channel.strip()
    if not value:
        raise ValueError("--channel cannot be empty")
    if value.startswith("@"):
        return f"https://www.youtube.com/{value}"
    if value.startswith("http://") or value.startswith("https://"):
        return value
    return f"https://www.youtube.com/@{value.lstrip('@')}"


def _resolve_channel(channel: str):
    normalized = normalize_channel_url(_normalize_channel_arg(channel))
    for registered in YOUTUBE_CHANNELS.values():
        if normalize_channel_url(registered.url) == normalized:
            return registered
    return make_ad_hoc_channel(normalized, output_name=None)


def main() -> int:
    parser = argparse.ArgumentParser(description="Discover YouTube videos by title regex pattern set")
    parser.add_argument("--channel", required=True, help='YouTube channel handle or URL, e.g. "@UkrainianLessons"')
    parser.add_argument("--pattern-set", required=True, help="Pattern set key from data/youtube_discovery/patterns.yaml")
    parser.add_argument(
        "--output",
        type=Path,
        help="Output JSONL path (default: data/youtube_discovery/<pattern-set>.jsonl)",
    )
    parser.add_argument("--max-videos", type=int, default=500, help="Maximum channel videos to inspect")
    args = parser.parse_args()

    try:
        patterns = load_title_pattern_set(args.pattern_set)
        channel = _resolve_channel(args.channel)
    except ValueError as exc:
        parser.error(str(exc))

    output_file = args.output or (YOUTUBE_DISCOVERY_DIR / f"{args.pattern_set}.jsonl")
    limiter = YouTubeRequestLimiter()
    discover_by_title_patterns(
        channel=channel,
        patterns=patterns,
        output_file=output_file,
        limiter=limiter,
        max_videos=args.max_videos,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
