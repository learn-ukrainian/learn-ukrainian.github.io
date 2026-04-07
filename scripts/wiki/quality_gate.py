#!/usr/bin/env python3
"""Wiki quality gate — check compiled articles for problems.

Scans wiki articles and flags:
1. Short articles (below min word count)
2. AI noise (Gemini thinking leaked into output)
3. Fence wrapping (```markdown)
4. Missing heading (doesn't start with #)
5. Truncated (ends mid-sentence)

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
]
_AI_NOISE_RE = re.compile("|".join(AI_NOISE_PATTERNS), re.MULTILINE)


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

    # 2. AI noise
    if _AI_NOISE_RE.search(text[:500]):
        issues.append("AI_NOISE (thinking leaked)")

    # 3. Fence wrapping
    if first_line.startswith("```"):
        issues.append("FENCE_WRAPPED")

    # 4. Missing heading
    if not first_line.startswith("#"):
        issues.append(f"NO_HEADING (starts: {first_line[:40]}...)")

    # 5. Truncated
    stripped = text.rstrip()
    if stripped and stripped[-1] not in ".!?»\")]\n`|":
        last_line = stripped.split("\n")[-1].strip()
        if last_line and not last_line.startswith(("#", "|", "-", "*", ">", "```", "<!--")):
            issues.append(f"TRUNCATED (ends: ...{last_line[-30:]})")

    return issues


def scan_track(track: str) -> dict[str, list[str]]:
    """Scan all articles for a track. Returns {slug: [issues]}."""
    # Map track to wiki directory
    track_dirs = {
        "a1": WIKI_DIR / "pedagogy" / "a1",
        "a2": WIKI_DIR / "grammar" / "a2",
        "b1": WIKI_DIR / "grammar" / "b1",
        "b2": WIKI_DIR / "grammar" / "b2",
        "c1": WIKI_DIR / "academic" / "c1",
        "c2": WIKI_DIR / "mastery" / "c2",
    }
    # Seminar tracks
    for t in ("folk", "hist", "bio", "istorio", "lit", "oes", "ruth"):
        for sub in WIKI_DIR.glob(f"**/{t}"):
            if sub.is_dir():
                track_dirs[t] = sub

    wiki_dir = track_dirs.get(track)
    if not wiki_dir or not wiki_dir.exists():
        return {}

    results = {}
    for md in sorted(wiki_dir.rglob("*.md")):
        if md.name == "index.md":
            continue
        slug = md.stem
        issues = check_article(md, track)
        if issues:
            results[slug] = issues
    return results


def clear_for_recompile(track: str, slugs: list[str]) -> int:
    """Clear articles from progress DB and delete files for recompile."""
    cleared = 0
    if PROGRESS_DB.exists():
        conn = sqlite3.connect(str(PROGRESS_DB))
        for slug in slugs:
            # Find the article_key pattern
            rows = conn.execute(
                "SELECT article_key FROM compiled WHERE article_key LIKE ?",
                (f"%/{slug}",),
            ).fetchall()
            for row in rows:
                conn.execute("DELETE FROM compiled WHERE article_key = ?", (row[0],))
                cleared += 1
        conn.commit()
        conn.close()

    # Delete files
    for slug in slugs:
        for md in WIKI_DIR.rglob(f"{slug}.md"):
            if md.exists():
                md.unlink()

    return cleared


def main() -> None:
    parser = argparse.ArgumentParser(description="Wiki quality gate")
    parser.add_argument("--track", help="Check specific track")
    parser.add_argument("--fix", action="store_true", help="Auto-clear bad articles for recompile")
    args = parser.parse_args()

    tracks = [args.track] if args.track else ["a1", "a2", "b1", "b2", "c1", "c2"]

    total_issues = 0
    all_bad: dict[str, list[str]] = {}

    for track in tracks:
        issues = scan_track(track)
        if issues:
            print(f"\n{'='*50}")
            print(f"  {track.upper()}: {len(issues)} issues")
            print(f"{'='*50}")
            for slug, problems in issues.items():
                print(f"  ❌ {slug}: {', '.join(problems)}")
                all_bad[slug] = problems
            total_issues += len(issues)

    if total_issues == 0:
        print("\n✅ All articles pass quality gate")
        return

    print(f"\n📊 Total: {total_issues} articles with issues")

    if args.fix:
        slugs = list(all_bad.keys())
        cleared = clear_for_recompile(args.track or "all", slugs)
        print(f"🗑️  Cleared {cleared} articles for recompile")
        print("Run compile.py --all to rebuild them")
    else:
        print("Run with --fix to auto-clear for recompile")


if __name__ == "__main__":
    main()
