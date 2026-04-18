#!/usr/bin/env python3
"""Wiki quality gate — check compiled articles for deterministic problems.

Scans wiki articles and flags:
1. Short articles (below min word count)
2. AI noise (Gemini thinking leaked into output)
3. Fence wrapping (```markdown)
4. Missing heading (doesn't start with #)
5. Truncated (ends mid-sentence)
6. Placeholder text (TODO, [Insert, etc.)
7. Unclosed code blocks (odd number of ``` fences)
8. Forbidden `## Джерела` bibliography sections in prose
9. Citation registry mismatches between inline `[S#]` refs and sibling `.sources.yaml`
10. Malformed sibling source registries

Can auto-clear flagged articles from progress DB for recompile.

Usage:
    # Check all levels
    .venv/bin/python scripts/wiki/quality_gate.py

    # Check specific level
    .venv/bin/python scripts/wiki/quality_gate.py --track a2

    # Auto-clear bad articles for recompile
    .venv/bin/python scripts/wiki/quality_gate.py --fix
"""

import argparse
import re
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from wiki.compile import _get_domain
from wiki.config import ALL_TRACKS
from wiki.sources import list_discovery_slugs_readonly
from wiki.sources_schema import extract_short_citation_ids, load_sources_registry, registry_path_for

PROJECT_ROOT = Path(__file__).resolve().parents[2]
WIKI_DIR = PROJECT_ROOT / "wiki"
PROGRESS_DB = WIKI_DIR / ".state" / "progress.db"

MIN_WORDS = {
    "a1": 1000,
    "a2": 1200,
    "b1": 1200,
    "b2": 1200,
    "c1": 1500,
    "c2": 1500,
    "folk": 1000,
    "hist": 1500,
    "bio": 1500,
    "istorio": 1500,
    "lit": 1500,
    "oes": 1500,
    "ruth": 1500,
}

AI_NOISE_PATTERNS = [
    # English thinking
    r"^I am now ",
    r"^My plan is to ",
    r"^I will address ",
    r"^First, I will ",
    r"^Let me structure ",
    r"^I need to ",
    r"^Okay, I ",
    r"^Here is my ",
    r"^Let me now ",
    r"^Now I will ",
    r"^Let me know if ",
    r"^Here is the compiled ",
    # Ukrainian thinking
    r"^Ось мій план",
    r"^Зараз я ",
    r"^По-перше, я ",
    r"^Мені потрібно ",
]
_AI_NOISE_RE = re.compile("|".join(AI_NOISE_PATTERNS), re.MULTILINE)
_SOURCES_SECTION_RE = re.compile(r"^## Джерела", re.MULTILINE)
_SOURCES_SECTION_BLOCK_RE = re.compile(r"^## Джерела.*?(?=^## |\Z)", re.MULTILINE | re.DOTALL)


def _citation_sort_key(citation_id: str) -> int:
    return int(citation_id[1:])


def _strip_sources_section(text: str) -> str:
    """Remove forbidden bibliography blocks before parsing inline citations."""
    return _SOURCES_SECTION_BLOCK_RE.sub("", text)


def _check_citation_registry(path: Path, text: str) -> list[str]:
    """Validate inline short citations against the sibling source registry."""
    issues: list[str] = []
    citation_ids = set(extract_short_citation_ids(_strip_sources_section(text)))
    registry_path = registry_path_for(path)

    if not registry_path.exists():
        if citation_ids:
            issues.append(f"MISSING_SOURCES_YAML ({registry_path.name})")
        return issues

    try:
        registry = load_sources_registry(registry_path)
    except Exception as exc:
        issues.append(f"MALFORMED_SOURCES_YAML ({registry_path.name}: {exc})")
        return issues

    registry_ids = {entry.id for entry in registry.sources}

    for citation_id in sorted(citation_ids - registry_ids, key=_citation_sort_key):
        issues.append(f"ORPHAN_INLINE_REF ({citation_id})")

    for source_id in sorted(registry_ids - citation_ids, key=_citation_sort_key):
        issues.append(f"UNUSED_SOURCE ({source_id})")

    return issues


def _iter_track_articles(track: str):
    """Yield compiled article paths owned by a single track."""
    seen: set[Path] = set()
    for slug in list_discovery_slugs_readonly(track):
        article_path = WIKI_DIR / _get_domain(track, slug) / f"{slug}.md"
        if not article_path.exists() or article_path in seen:
            continue
        seen.add(article_path)
        yield article_path


def check_article(path: Path, track: str) -> list[str]:
    """Check a single article. Returns list of issues (empty = clean)."""
    issues = []
    text = path.read_text("utf-8")
    words = len(text.split())
    first_line = text.strip().split("\n")[0] if text.strip() else ""

    # 1. Short
    min_w = MIN_WORDS.get(track, 1000)
    if words < min_w:
        issues.append(f"SHORT ({words}w < {min_w})")

    # 2. AI noise — scan full text, not just first 500 chars
    if _AI_NOISE_RE.search(text):
        issues.append("AI_NOISE (thinking leaked)")

    # 3. Fence wrapping (also covers NO_HEADING — don't double-flag)
    if first_line.startswith("```"):
        issues.append("FENCE_WRAPPED")
    elif not first_line.startswith("#"):
        # 4. Missing heading (only if not fence-wrapped)
        issues.append(f"NO_HEADING (starts: {first_line[:40]}...)")

    # 5. Truncated — check last non-whitespace char
    stripped = text.rstrip()
    if stripped and stripped[-1] not in '.!?»")\']`|…"':
        last_line = stripped.split("\n")[-1].strip()
        if last_line and not last_line.startswith(("#", "|", "-", "*", ">", "```", "<!--")):
            issues.append(f"TRUNCATED (ends: ...{last_line[-30:]})")

    # 6. Placeholder text
    if re.search(r"\[Insert|\bTODO\b|\[Your text here\]|<text>", text):
        issues.append("PLACEHOLDER_TEXT")

    # 7. Unclosed code blocks (odd fence count)
    fence_count = len(re.findall(r"^```", text, re.MULTILINE))
    if fence_count % 2 == 1:
        issues.append("UNCLOSED_CODE_BLOCK")

    # 8. Forbidden sources section in prose
    if _SOURCES_SECTION_RE.search(text):
        issues.append("SOURCES_SECTION_PRESENT")

    # 9-10. Inline citation / registry consistency
    issues.extend(_check_citation_registry(path, text))

    return issues


def scan_track(track: str) -> dict[str, list[str]]:
    """Scan all articles for a track. Returns {path_relative: [issues]}."""
    results = {}
    for md in sorted(_iter_track_articles(track)):
        # Use relative path as key to avoid slug collisions across tracks
        rel_key = str(md.relative_to(WIKI_DIR))
        issues = check_article(md, track)
        if issues:
            results[rel_key] = issues
    return results


def clear_for_recompile(bad_paths: list[str]) -> int:
    """Clear articles from progress DB and delete files.

    Args:
        bad_paths: list of paths relative to wiki/ (e.g. "grammar/a2/genitive-intro.md")
    """
    cleared = 0
    if PROGRESS_DB.exists():
        with sqlite3.connect(str(PROGRESS_DB)) as conn:
            for rel_path in bad_paths:
                # article_key in DB is path without .md extension
                article_key = rel_path.replace(".md", "")
                deleted = conn.execute(
                    "DELETE FROM compiled WHERE article_key = ?",
                    (article_key,),
                ).rowcount
                cleared += deleted
            conn.commit()

    # Delete files
    for rel_path in bad_paths:
        md = WIKI_DIR / rel_path
        if md.exists():
            md.unlink()

    return cleared


def main() -> None:
    parser = argparse.ArgumentParser(description="Wiki quality gate")
    parser.add_argument("--track", help="Check specific track")
    parser.add_argument("--fix", action="store_true", help="Auto-clear bad articles for recompile")
    args = parser.parse_args()

    tracks = [args.track] if args.track else ALL_TRACKS

    total_issues = 0
    all_bad: dict[str, list[str]] = {}

    for track in tracks:
        issues = scan_track(track)
        if issues:
            print(f"\n{'='*50}")
            print(f"  {track.upper()}: {len(issues)} issues")
            print(f"{'='*50}")
            for rel_path, problems in issues.items():
                print(f"  ❌ {rel_path}: {', '.join(problems)}")
                all_bad[rel_path] = problems
            total_issues += len(issues)

    if total_issues == 0:
        print("\n✅ All articles pass quality gate")
        return

    print(f"\n📊 Total: {total_issues} articles with issues")

    if args.fix:
        paths = list(all_bad.keys())
        cleared = clear_for_recompile(paths)
        print(f"🗑️  Cleared {cleared} entries + deleted {len(paths)} files")
        print("Run compile.py --all to rebuild them")
    else:
        print("Run with --fix to auto-clear for recompile")


if __name__ == "__main__":
    main()
