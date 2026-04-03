#!/usr/bin/env python3
"""Wiki knowledge base compiler — CLI entry point.

Compiles source material (literary texts, textbook chunks, discovery files)
into structured markdown wiki articles using Gemini.

Usage:
    # Show compilation status
    .venv/bin/python scripts/wiki/compile.py --status

    # List what's available for a track
    .venv/bin/python scripts/wiki/compile.py --track folk --list

    # Compile one article (dry run)
    .venv/bin/python scripts/wiki/compile.py --track folk --slug dumy-lytsarski --dry-run

    # Compile one article
    .venv/bin/python scripts/wiki/compile.py --track folk --slug dumy-lytsarski

    # Compile all articles for a track (with limit)
    .venv/bin/python scripts/wiki/compile.py --track folk --all --limit 5

    # Force recompilation
    .venv/bin/python scripts/wiki/compile.py --track folk --slug dumy-lytsarski --force

    # Update wiki index
    .venv/bin/python scripts/wiki/compile.py --update-index
"""

import argparse
import sys
from pathlib import Path

# Add scripts/ to path for relative imports
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from wiki.compiler import compile_article, update_index
from wiki.config import SEMINAR_TRACKS, TRACK_DOMAINS
from wiki.sources import (
    gather_discovery_sources,
    list_discovery_slugs,
    list_literary_sources,
    load_literary_jsonl,
)
from wiki.state import get_status_summary

# ── Domain mapping: how to group discovery slugs into wiki articles ──

# For FOLK, each discovery slug maps directly to a wiki article
# For other tracks, we may want to group multiple slugs into one article
FOLK_DOMAIN_MAP: dict[str, str] = {
    "bylyny-kyivskoho-tsyklu": "folk/genres",
    "bylyny-sotsialni": "folk/genres",
    "bohatyri-illiya-dobrynia": "folk/genres",
    "zastavy-bohatyrski": "folk/genres",
    "dumy-lytsarski": "folk/genres",
    "dumy-nevilnytski": "folk/genres",
    "dumy-sotsialno-pobutovi": "folk/genres",
    "pokhodzhennia-dum": "folk/genres",
    "charivni-kazky": "folk/genres",
    "kazky-pro-tvaryn": "folk/genres",
    "sotsialno-pobutovi-kazky": "folk/genres",
    "koliadky-shchedrivky": "folk/ritual",
    "kupalski-pisni": "folk/ritual",
    "obzhynkovi-pisni": "folk/ritual",
    "rusalni-pisni": "folk/ritual",
    "vesilni-pisni": "folk/ritual",
    "vesnianky-hayivky": "folk/ritual",
    "chumatski-burlatski-pisni": "folk/lyric",
    "rodynna-liryka-kolomyiky": "folk/lyric",
    "holosinnya": "folk/tradition",
    "kobzarstvo-fenomen": "folk/tradition",
    "narodni-anekdoty": "folk/prose",
    "narodni-balady": "folk/prose",
    "narodni-lehendy": "folk/prose",
    "istorychni-perekazy": "folk/prose",
    "prykazky-ta-pryslivia": "folk/short-forms",
    "zahadky": "folk/short-forms",
}


def cmd_status() -> None:
    """Show compilation status."""
    summary = get_status_summary()
    print("\n📊 Wiki Compilation Status")
    print(f"{'─' * 40}")
    print(f"Total compiled: {summary['total_compiled']} articles")
    print(f"Total words:    {summary['total_words']:,}")
    if summary['last_updated']:
        print(f"Last updated:   {summary['last_updated']}")

    if summary["by_domain"]:
        print("\nBy domain:")
        for domain, count in sorted(summary["by_domain"].items()):
            print(f"  {domain}: {count}")

    # Show available tracks
    print("\nAvailable tracks (with discovery files):")
    for track in SEMINAR_TRACKS:
        slugs = list_discovery_slugs(track)
        if slugs:
            print(f"  {track}: {len(slugs)} modules")

    lit_count = len(list_literary_sources())
    print(f"\nLiterary sources: {lit_count} JSONL files")


def cmd_list(track: str) -> None:
    """List available modules and their source material for a track."""
    slugs = list_discovery_slugs(track)
    if not slugs:
        print(f"No discovery files for track '{track}'")
        return

    print(f"\n📋 {track.upper()} — {len(slugs)} modules")
    print(f"Domains: {', '.join(TRACK_DOMAINS.get(track, ['unknown']))}")
    print(f"{'─' * 60}")

    for slug in slugs:
        sources = gather_discovery_sources(track, slug)
        lit = len(sources.get("literary_chunks", []))
        text = len(sources.get("textbook_chunks", []))
        files = len(sources.get("literary_files", []))
        print(f"  {slug:<40} lit:{lit} text:{text} files:{files}")


def cmd_compile_one(track: str, slug: str, *, force: bool = False,
                    dry_run: bool = False) -> bool:
    """Compile a single wiki article from a discovery file."""
    print(f"\n🔨 Compiling: {track}/{slug}")

    # Get domain mapping
    domain = _get_domain(track, slug)

    # Gather sources
    sources_info = gather_discovery_sources(track, slug)
    if "error" in sources_info:
        print(f"  ❌ {sources_info['error']}")
        return False

    # Collect all available source chunks
    all_chunks = []
    all_chunks.extend(sources_info.get("literary_chunks", []))
    all_chunks.extend(sources_info.get("textbook_chunks", []))

    # If discovery has few inline chunks, try loading full literary files
    if len(all_chunks) < 5 and sources_info.get("literary_files"):
        print(f"  📚 Loading additional sources from {len(sources_info['literary_files'])} files...")
        for lit_path in sources_info["literary_files"][:3]:  # Cap at 3 files
            chunks = load_literary_jsonl(lit_path)
            # Take first 20 chunks (don't overwhelm the prompt)
            all_chunks.extend(chunks[:20])
            print(f"     + {lit_path.name}: {len(chunks)} chunks (using first 20)")

    if not all_chunks:
        print(f"  ⚠️  No source material found for {track}/{slug}")
        # Still compile — Gemini can use its knowledge + we'll supplement later
        all_chunks = [{"text": f"Topic: {slug.replace('-', ' ')}", "chunk_id": "no-source"}]

    # Build a human-readable topic from the slug
    topic = _slug_to_topic(slug, track)

    result = compile_article(
        topic=topic,
        slug=slug,
        domain=domain,
        sources=all_chunks,
        force=force,
        dry_run=dry_run,
    )

    if result:
        update_index()
        return True
    return dry_run  # dry_run returns None but isn't a failure


def cmd_compile_all(track: str, *, limit: int | None = None,
                    force: bool = False, dry_run: bool = False) -> None:
    """Compile all articles for a track."""
    slugs = list_discovery_slugs(track)
    if not slugs:
        print(f"No discovery files for track '{track}'")
        return

    if limit:
        slugs = slugs[:limit]

    print(f"\n🔨 Compiling {len(slugs)} articles for {track.upper()}")
    print(f"{'═' * 60}")

    success = 0
    failed = 0
    skipped = 0

    for i, slug in enumerate(slugs, 1):
        print(f"\n[{i}/{len(slugs)}] {slug}")
        result = cmd_compile_one(track, slug, force=force, dry_run=dry_run)
        if result:
            success += 1
        else:
            # Check if it was skipped (already compiled)
            from wiki.state import is_compiled
            domain = _get_domain(track, slug)
            if is_compiled(f"{domain}/{slug}"):
                skipped += 1
            else:
                failed += 1

    print(f"\n{'═' * 60}")
    print(f"✅ Compiled: {success} | ⏭️  Skipped: {skipped} | ❌ Failed: {failed}")


def _get_domain(track: str, slug: str) -> str:
    """Get the wiki domain path for a module slug."""
    # Check track-specific mappings first
    if track == "folk":
        return FOLK_DOMAIN_MAP.get(slug, "folk")

    # Default: use track name as domain
    domain_map = {
        "hist": "periods",
        "bio": "figures",
        "istorio": "historiography",
        "lit": "literature/works",
        "lit-essay": "literature/works",
        "lit-war": "literature/works",
        "lit-hist-fic": "literature/works",
        "lit-youth": "literature/works",
        "lit-fantastika": "literature/works",
        "lit-humor": "literature/works",
        "lit-drama": "literature/works",
        "lit-doc": "literature/works",
        "lit-crimea": "literature/works",
        "oes": "linguistics/oes",
        "ruth": "linguistics/ruthenian",
    }
    return domain_map.get(track, track)


def _slug_to_topic(slug: str, track: str) -> str:
    """Convert a URL slug to a human-readable topic name.

    Uses Ukrainian where possible.
    """
    # Replace hyphens with spaces, title case
    topic = slug.replace("-", " ").title()

    # Add track context
    track_labels = {
        "folk": "Український фольклор",
        "hist": "Історія України",
        "bio": "Біографія",
        "istorio": "Історіографія",
        "lit": "Українська література",
        "oes": "Давньоруська мова",
        "ruth": "Руська (староукраїнська) мова",
    }
    label = track_labels.get(track, track.upper())
    return f"{label}: {topic}"


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Wiki knowledge base compiler",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument("--status", action="store_true",
                        help="Show compilation status")
    parser.add_argument("--update-index", action="store_true",
                        help="Regenerate wiki/index.md")

    # Track selection
    parser.add_argument("--track", choices=SEMINAR_TRACKS,
                        help="Seminar track to compile")
    parser.add_argument("--slug", help="Specific module slug to compile")
    parser.add_argument("--all", action="store_true", dest="compile_all",
                        help="Compile all modules in the track")
    parser.add_argument("--list", action="store_true",
                        help="List available modules for a track")

    # Options
    parser.add_argument("--limit", type=int,
                        help="Max articles to compile (with --all)")
    parser.add_argument("--force", action="store_true",
                        help="Recompile even if already done")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print prompt without calling Gemini")

    args = parser.parse_args()

    # Route commands
    if args.status:
        cmd_status()
        return

    if args.update_index:
        update_index()
        return

    if not args.track:
        parser.error("--track is required (or use --status)")

    if args.list:
        cmd_list(args.track)
        return

    if args.slug:
        success = cmd_compile_one(
            args.track, args.slug,
            force=args.force, dry_run=args.dry_run,
        )
        sys.exit(0 if success else 1)

    if args.compile_all:
        cmd_compile_all(
            args.track,
            limit=args.limit, force=args.force, dry_run=args.dry_run,
        )
        return

    parser.error("Specify --slug, --all, or --list")


if __name__ == "__main__":
    main()
