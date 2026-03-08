#!/usr/bin/env python3
"""Fix external_resources.yaml — clean bad data, re-score assignments.

Standalone process, no module rebuild needed. After fixing:
  .venv/bin/python scripts/generate_mdx.py l2-uk-en {level} {num}

Usage:
    %(prog)s --audit                    # Report problems, no changes
    %(prog)s --clean                    # Remove bad entries (placeholders, duplicates)
    %(prog)s --reassign a1 1-30         # Re-score assignments for a range using blog DBs
    %(prog)s --reassign a1 --all        # Re-score all modules in track
    %(prog)s --regen-mdx a1 1-30        # Regenerate MDX after fixes

Issue: #751
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = SCRIPTS_DIR.parent
sys.path.insert(0, str(SCRIPTS_DIR))

import yaml
from batch_gemini_config import get_module_index

RESOURCES_PATH = PROJECT_ROOT / "docs" / "resources" / "external_resources.yaml"
BACKUP_PATH = RESOURCES_PATH.with_suffix(".yaml.bak")

# Keep in sync with pipeline_v5._GENERIC_URL_PATTERNS
_GENERIC_URL_PATTERNS = [
    re.compile(r"^https?://(www\.)?ukrainianlessons\.com/?$"),
    re.compile(r"^https?://ukrainianlessons\.com/?$"),
    re.compile(r"^https?://(www\.)?ukrainianlessons\.com/podcast/?$"),
    re.compile(r"^https?://(www\.)?ukrainianlessons\.com/the-podcast/?$"),
    re.compile(r"youtube\.com/watch\?v=example"),
    re.compile(r"^https?://sum\.in\.ua/?$"),
    re.compile(r"^https?://slovnyk\.ua/?$"),
    re.compile(r"^https?://pravopys\.net/?$"),
    re.compile(r"^https?://r2u\.org\.ua/?$"),
    re.compile(r"^https?://(www\.)?youtube\.com/@\w+/?$"),
]

# Keep in sync with pipeline_v5._GENERIC_TITLES
_GENERIC_TITLES = {
    "Ukrainian Lessons Podcast", "Ukrainian Lessons", "Ukrainian Grammar",
    "Speak Ukrainian YouTube", "Colors Guide", "Verb Practice",
}

# Max times a URL can appear across modules before it's considered generic
_MAX_URL_REUSE = 15


def load_resources() -> tuple[dict, dict]:
    """Load external_resources.yaml. Returns (full_data, resources_dict)."""
    if not RESOURCES_PATH.exists():
        print(f"ERROR: {RESOURCES_PATH} not found")
        sys.exit(1)
    with open(RESOURCES_PATH, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data, data.get("resources", {})


def save_resources(data: dict) -> None:
    """Save external_resources.yaml with backup."""
    # Backup
    if RESOURCES_PATH.exists():
        BACKUP_PATH.write_text(RESOURCES_PATH.read_text("utf-8"), "utf-8")
    with open(RESOURCES_PATH, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False, width=120)
    print(f"Saved → {RESOURCES_PATH.name} (backup → {BACKUP_PATH.name})")


def _is_generic_url(url: str) -> bool:
    return any(p.search(url) for p in _GENERIC_URL_PATTERNS)


def _is_generic_title(title: str) -> bool:
    return title.strip() in _GENERIC_TITLES


def audit(resources: dict) -> dict:
    """Audit external_resources.yaml for problems. Returns stats dict."""
    # Count URL usage across all modules
    url_counter: Counter = Counter()
    for module_key, module_data in resources.items():
        if not module_data:
            continue
        for cat in ("youtube", "articles", "websites"):
            for item in module_data.get(cat, []):
                url_counter[item.get("url", "")] += 1

    overused_urls = {u for u, c in url_counter.items() if c > _MAX_URL_REUSE and u}

    stats = {
        "total_modules": len(resources),
        "empty_modules": 0,
        "total_links": 0,
        "generic_url": 0,
        "generic_title": 0,
        "overused_url": 0,
        "placeholder_url": 0,
        "good_links": 0,
    }
    problems: list[str] = []

    for module_key, module_data in sorted(resources.items()):
        if not module_data:
            stats["empty_modules"] += 1
            continue

        for cat in ("youtube", "articles", "websites"):
            for item in module_data.get(cat, []):
                stats["total_links"] += 1
                url = item.get("url", "")
                title = item.get("title", "")

                issues = []
                if _is_generic_url(url):
                    stats["generic_url"] += 1
                    issues.append("GENERIC_URL")
                if _is_generic_title(title):
                    stats["generic_title"] += 1
                    issues.append("GENERIC_TITLE")
                if url in overused_urls:
                    stats["overused_url"] += 1
                    issues.append(f"OVERUSED({url_counter[url]}x)")
                if not url or "example" in url:
                    stats["placeholder_url"] += 1
                    issues.append("PLACEHOLDER")

                if issues:
                    problems.append(f"  {module_key} [{cat}]: {' | '.join(issues)} — {title[:50]} → {url[:60]}")
                else:
                    stats["good_links"] += 1

    bad = stats["total_links"] - stats["good_links"]
    print(f"\n{'='*70}")
    print(f"External Resources Audit")
    print(f"{'='*70}")
    print(f"Modules:     {stats['total_modules']} ({stats['empty_modules']} empty)")
    print(f"Total links: {stats['total_links']}")
    print(f"  Good:      {stats['good_links']}")
    print(f"  Bad:       {bad}")
    print(f"    Generic URL:   {stats['generic_url']}")
    print(f"    Generic title: {stats['generic_title']}")
    print(f"    Overused URL:  {stats['overused_url']}")
    print(f"    Placeholder:   {stats['placeholder_url']}")

    if problems:
        print(f"\nProblems ({len(problems)}):")
        for p in problems[:50]:
            print(p)
        if len(problems) > 50:
            print(f"  ... and {len(problems) - 50} more")
    else:
        print("\nNo problems found!")

    print(f"{'='*70}\n")
    return stats


def clean(resources: dict) -> int:
    """Remove bad entries + normalize keys. Returns total count of changes.

    1. Strips numbered keys ('a1-05-slug' → 'a1-slug') to prevent stale mappings
    2. Removes: generic URLs, generic titles, placeholder URLs
    Does NOT remove overused-but-legitimate URLs — those are flagged in audit.
    """
    normalized = _normalize_keys(resources)
    removed = 0

    for module_key in list(resources.keys()):
        module_data = resources[module_key]
        if not module_data:
            continue

        for cat in ("youtube", "articles", "websites"):
            items = module_data.get(cat, [])
            if not items:
                continue

            clean_items = []
            for item in items:
                url = item.get("url", "")
                title = item.get("title", "")
                if _is_generic_url(url) or _is_generic_title(title) or "example" in url:
                    removed += 1
                else:
                    clean_items.append(item)

            if clean_items:
                module_data[cat] = clean_items
            elif cat in module_data:
                del module_data[cat]

    total = normalized + removed
    print(f"Cleaned: {normalized} keys normalized, {removed} bad entries removed")
    return total


def _normalize_keys(resources: dict) -> int:
    """Strip numbers from keys: 'a1-05-slug' → 'a1-slug'. Merges duplicates.

    Numbers in keys go stale when curriculum reorders. Slug-only keys are stable.
    Called automatically by clean().
    """
    numbered_pattern = re.compile(r"^([a-z]\d+)-\d+-(.+)$")
    keys_to_remove = []
    fixed = 0

    for key in list(resources.keys()):
        m = numbered_pattern.match(key)
        if not m:
            continue
        slug_key = f"{m.group(1)}-{m.group(2)}"
        module_data = resources[key]

        # Merge into slug-only key
        existing = resources.get(slug_key, {}) or {}
        if module_data:
            for cat in ("youtube", "articles", "websites"):
                items = module_data.get(cat, [])
                if items:
                    existing_items = existing.get(cat, [])
                    existing_urls = {it.get("url", "") for it in existing_items}
                    for item in items:
                        if item.get("url", "") not in existing_urls:
                            existing_items.append(item)
                            existing_urls.add(item.get("url", ""))
                    existing[cat] = existing_items
            if existing:
                resources[slug_key] = existing

        keys_to_remove.append(key)
        fixed += 1

    for key in keys_to_remove:
        del resources[key]

    if fixed:
        print(f"Normalized: {fixed} numbered keys → slug-only")
    return fixed


def _verify_with_gemini(topic_title: str, slug: str, candidates: list[dict]) -> list[dict]:
    """Ask Gemini to verify which candidates are actually relevant.

    Returns only candidates that Gemini judges as relevant.
    """
    from pipeline_lib import dispatch_gemini_raw

    article_list = "\n".join(
        f"{i+1}. \"{c['title']}\" (source: {c.get('source', '?')})"
        for i, c in enumerate(candidates)
    )

    prompt = f"""You are a Ukrainian language curriculum resource matcher.

Module: "{topic_title}" (slug: {slug})

Candidate external resources:
{article_list}

For each candidate, judge: is this article/podcast SPECIFICALLY relevant to the module topic "{topic_title}"?

Rules:
- RELEVANT: The article directly teaches or practices the same grammar, vocabulary, or skill as the module
- NOT RELEVANT: The article is about a different topic, even if it's about Ukrainian language in general
- "Grammar" or "verbs" alone is NOT enough — the specific grammar point must match
- Podcast episodes about daily life topics (market, restaurant, travel) are only relevant to vocabulary modules about those topics, NOT to grammar modules

Reply with ONLY the numbers of relevant articles, comma-separated. If none are relevant, reply "NONE".
Example: 1, 3, 5"""

    ok, output = dispatch_gemini_raw(
        prompt, task_id=f"verify-{slug}",
        model="gemini-3-flash-preview",
        stdout_only=True, timeout=120,
    )

    if not ok:
        # On failure, return all candidates (don't block)
        return candidates

    output = output.strip()
    if "NONE" in output.upper():
        return []

    # Parse numbers
    try:
        nums = [int(x.strip()) for x in output.replace("\n", ",").split(",") if x.strip().isdigit()]
        return [candidates[n - 1] for n in nums if 1 <= n <= len(candidates)]
    except (ValueError, IndexError):
        return candidates


def reassign(resources: dict, track: str, start: int, end: int, use_llm: bool = False) -> int:
    """Re-score resource assignments using blog/podcast DBs + discovery data.

    For each module, searches the blog DBs for relevant articles and updates
    the external_resources entry. Preserves good existing entries.

    If use_llm=True, candidates are verified by Gemini before assignment.
    """
    from video_discovery import search_blogs
    idx = get_module_index(track)
    updated = 0

    for n in range(start, end + 1):
        slug = idx["num_to_slug"].get(n)
        if not slug:
            continue

        # Build module key (try both formats)
        numbered_key = f"{track}-{n:02d}-{slug}"
        plain_key = f"{track}-{slug}"
        module_key = numbered_key if numbered_key in resources else plain_key

        # Build keywords from multiple lightweight sources
        topic_title = slug.replace("-", " ").title()
        keywords = [topic_title]
        base_dir = PROJECT_ROOT / "curriculum" / "l2-uk-en" / track

        # Source 1: Plan YAML (title, objectives, vocab hints)
        plan_path = PROJECT_ROOT / "curriculum" / "l2-uk-en" / "plans" / track / f"{slug}.yaml"
        if plan_path.exists():
            try:
                plan = yaml.safe_load(plan_path.read_text("utf-8"))
                if plan:
                    topic_title = plan.get("title", topic_title)
                    for obj in plan.get("objectives", []):
                        if isinstance(obj, str) and len(obj.split()) <= 6:
                            keywords.append(obj)
                    vh = plan.get("vocabulary_hints", {})
                    if isinstance(vh, dict):
                        for v in vh.get("required", [])[:5]:
                            if isinstance(v, str):
                                keywords.append(v)
            except Exception:
                pass

        # Source 2: Meta YAML (content_outline section names + points)
        meta_path = base_dir / "meta" / f"{slug}.yaml"
        if meta_path.exists():
            try:
                meta = yaml.safe_load(meta_path.read_text("utf-8"))
                if meta:
                    for sec in meta.get("content_outline", []):
                        if isinstance(sec, dict):
                            # Section name (e.g. "Velar Mutations")
                            sec_name = sec.get("section", "")
                            if sec_name and len(sec_name.split()) <= 6:
                                keywords.append(sec_name)
                            # Key points (rich with grammar terms)
                            for pt in sec.get("points", [])[:3]:
                                if isinstance(pt, str):
                                    # Extract short noun phrases (grammar terms)
                                    for phrase in re.findall(r'[A-Z][a-z]+(?: [A-Za-z]+){0,2}', pt):
                                        if len(phrase.split()) <= 3:
                                            keywords.append(phrase)
            except Exception:
                pass

        # Source 3: Content headings (if module is built)
        content_path = base_dir / f"{slug}.md"
        if content_path.exists():
            try:
                for line in content_path.read_text("utf-8").splitlines()[:100]:
                    if line.startswith("## ") or line.startswith("### "):
                        heading = line.lstrip("#").strip()
                        # Skip generic Ukrainian section names
                        if heading and not heading.startswith("Вступ") and not heading.startswith("Практика"):
                            keywords.append(heading)
            except Exception:
                pass

        # Clear stale articles before searching (prevents circular Layer 0 feedback)
        existing = resources.get(module_key, {}) or {}
        existing.pop("articles", None)
        if module_key in resources:
            resources[module_key] = existing
        # Invalidate curated cache so search_blogs doesn't return stale data
        import video_discovery as _vd
        _vd._curated_cache = None

        # Search blog DBs
        results = search_blogs(
            module_slug=slug,
            level=track,
            topic_title=topic_title,
            keywords=keywords,
            max_results=5,
        )

        if not results:
            continue

        # Preserve existing youtube/websites URLs to avoid duplicates
        existing_urls = set()
        for cat in ("youtube", "websites"):
            for item in existing.get(cat, []):
                existing_urls.add(item.get("url", ""))

        # Filter candidates — only keep those with relevance_score >= 0.5
        candidates = [
            r for r in results
            if r["url"] not in existing_urls and r.get("relevance_score", 0) >= 0.5
        ]

        if not candidates:
            continue

        # LLM verification — ask Gemini to judge actual relevance
        if use_llm:
            before = len(candidates)
            candidates = _verify_with_gemini(topic_title, slug, candidates)
            rejected = before - len(candidates)
            if rejected:
                print(f"    verify: {rejected}/{before} rejected by Gemini")

        # Build fresh articles list
        new_articles: list[dict] = []
        for r in candidates:
            new_articles.append({
                "title": r["title"],
                "url": r["url"],
                "relevance": "high" if r.get("relevance_score", 0) >= 0.7 else "medium",
                "source": r.get("source", "blog DB match"),
            })

        if new_articles:
            if module_key not in resources:
                resources[module_key] = {}
            resources[module_key]["articles"] = new_articles
            updated += 1
            print(f"  {module_key}: {len(new_articles)} articles")

    print(f"Updated: {updated} modules")
    return updated


def regen_mdx(track: str, start: int, end: int) -> None:
    """Regenerate MDX for a range of modules."""
    for n in range(start, end + 1):
        print(f"  Generating MDX: {track} #{n}...", end=" ", flush=True)
        result = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "generate_mdx.py"), "l2-uk-en", track, str(n)],
            capture_output=True, text=True, timeout=60,
        )
        if result.returncode == 0:
            print("OK")
        else:
            print(f"FAIL (rc={result.returncode})")


def parse_range(range_str: str, track: str) -> tuple[int, int]:
    """Parse '1-30' or '--all' into (start, end)."""
    if range_str == "all":
        idx = get_module_index(track)
        return 1, idx["total"]
    m = re.match(r"^(\d+)-(\d+)$", range_str)
    if m:
        return int(m.group(1)), int(m.group(2))
    # Single number
    if range_str.isdigit():
        n = int(range_str)
        return n, n
    print(f"ERROR: Invalid range '{range_str}' (expected N-M or 'all')")
    sys.exit(1)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Fix external_resources.yaml — standalone, no module rebuild.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--audit", action="store_true", help="Report problems, no changes")
    parser.add_argument("--clean", action="store_true", help="Remove bad entries (placeholders, overused, generic)")
    parser.add_argument("--reassign", nargs=2, metavar=("TRACK", "RANGE"),
                        help="Re-score assignments for a range (e.g. a1 1-30, a1 all)")
    parser.add_argument("--verify", action="store_true",
                        help="Use Gemini to verify relevance during --reassign (slower, more accurate)")
    parser.add_argument("--regen-mdx", nargs=2, metavar=("TRACK", "RANGE"),
                        help="Regenerate MDX after fixes (e.g. a1 1-30)")

    args = parser.parse_args()

    if not any([args.audit, args.clean, args.reassign, args.regen_mdx]):
        parser.print_help()
        return 0

    data, resources = load_resources()

    if args.audit:
        audit(resources)

    if args.clean:
        n_removed = clean(resources)
        if n_removed > 0:
            save_resources(data)
            # Re-audit after clean
            audit(resources)

    if args.reassign:
        track, range_str = args.reassign
        start, end = parse_range(range_str, track)
        n_updated = reassign(resources, track, start, end, use_llm=args.verify)
        if n_updated > 0:
            save_resources(data)

    if args.regen_mdx:
        track, range_str = args.regen_mdx
        start, end = parse_range(range_str, track)
        regen_mdx(track, start, end)

    return 0


if __name__ == "__main__":
    sys.exit(main())
