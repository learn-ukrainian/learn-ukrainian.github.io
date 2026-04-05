#!/usr/bin/env python3
"""Wiki knowledge base compiler — CLI entry point.

Compiles source material into structured markdown wiki articles using Gemini.
Supports ALL tracks: core levels (A1-C2) and seminar tracks (FOLK, HIST, etc.).

Each track type gets a different compilation prompt:
  - A1:         Pedagogical briefs (methodology, phonetic guardrails, vocabulary boundaries)
  - A2-B2:      Grammar briefs (paradigms, frequency, L2 errors, textbook approaches)
  - C1-C2:      Academic briefs (scholarly register, stylistic nuances)
  - Seminars:   Knowledge articles (primary sources, decolonization, historiography)

Discovery files are auto-generated from plans if they don't exist.
Compiled articles are stored in wiki/{domain}/ and used by the build pipeline
as context for Gemini when writing module content (step_research).

Usage:
    # Show compilation status (all tracks)
    .venv/bin/python scripts/wiki/compile.py --status

    # List what's available for a track
    .venv/bin/python scripts/wiki/compile.py --track a1 --list
    .venv/bin/python scripts/wiki/compile.py --track folk --list

    # Compile one article (dry run — shows prompt without calling Gemini)
    .venv/bin/python scripts/wiki/compile.py --track a1 --slug sounds-letters-and-hello --dry-run

    # Compile one article
    .venv/bin/python scripts/wiki/compile.py --track a1 --slug sounds-letters-and-hello

    # Compile one article + adversarial review
    .venv/bin/python scripts/wiki/compile.py --track a1 --slug sounds-letters-and-hello --review

    # Compile all articles for a track
    .venv/bin/python scripts/wiki/compile.py --track a1 --all
    .venv/bin/python scripts/wiki/compile.py --track a2 --all --review
    .venv/bin/python scripts/wiki/compile.py --track b1 --all --limit 20

    # Compile all articles for a seminar track
    .venv/bin/python scripts/wiki/compile.py --track folk --all
    .venv/bin/python scripts/wiki/compile.py --track hist --all --review

    # Force recompilation (even if already compiled)
    .venv/bin/python scripts/wiki/compile.py --track a1 --slug sounds-letters-and-hello --force

    # Update wiki index
    .venv/bin/python scripts/wiki/compile.py --update-index

Tracks: a1, a2, b1, b2, c1, c2, folk, hist, bio, istorio, lit, lit-essay,
        lit-war, lit-hist-fic, lit-youth, lit-fantastika, lit-humor, lit-drama,
        lit-doc, lit-crimea, oes, ruth
"""

import argparse
import sys
from pathlib import Path

# Add scripts/ to path for relative imports
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from wiki.compiler import compile_article, update_index
from wiki.config import ALL_TRACKS, CURRICULUM_DIR, TRACK_DOMAINS
from wiki.enrichment import enrich_sources
from wiki.sources import (
    gather_discovery_sources,
    list_discovery_slugs,
    list_literary_sources,
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

    # Show available tracks (check plans dir, don't auto-generate discovery)
    print("\nAvailable tracks:")
    for track in ALL_TRACKS:
        plans_dir = CURRICULUM_DIR / "plans" / track
        disc_dir = CURRICULUM_DIR / track / "discovery"
        plan_count = len(list(plans_dir.glob("*.yaml"))) if plans_dir.exists() else 0
        disc_count = len(list(disc_dir.glob("*.yaml"))) if disc_dir.exists() else 0
        if plan_count or disc_count:
            status = f"{disc_count} discovery" if disc_count else f"{plan_count} plans (discovery auto-generates on compile)"
            print(f"  {track}: {status}")

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
                    dry_run: bool = False, review: bool = False) -> bool:
    """Compile a single wiki article from a discovery file."""
    print(f"\n🔨 Compiling: {track}/{slug}")

    # Get domain mapping
    domain = _get_domain(track, slug)

    # Gather sources
    sources_info = gather_discovery_sources(track, slug)
    if "error" in sources_info:
        print(f"  ❌ {sources_info['error']}")
        return False

    # Collect and enrich source chunks
    all_chunks = enrich_sources(track, slug, sources_info)

    # Build a human-readable topic from discovery keywords (Ukrainian) or slug (fallback)
    topic = _slug_to_topic(slug, track, sources_info)

    result = compile_article(
        topic=topic,
        slug=slug,
        domain=domain,
        sources=all_chunks,
        track=track,
        force=force,
        dry_run=dry_run,
    )

    if result:
        update_index()
        if review and not dry_run:
            _review_article(result, track, slug)
        return True
    return dry_run  # dry_run returns None but isn't a failure


def _review_article(article_path: Path, track: str, slug: str,
                    max_rounds: int = 4) -> None:
    """Review a wiki article and auto-fix issues. Up to max_rounds of review+fix.

    Flow: Gemini reviews → Gemini fixes (with review as guide) → re-review.
    Stops when score ≥ 8 or max_rounds reached.
    """
    import subprocess

    from wiki.config import DEFAULT_PROMPT, TRACK_PROMPT, WIKI_DIR

    print(f"  🔍 Reviewing: {track}/{slug}")

    article_text = article_path.read_text("utf-8")
    if len(article_text) < 100:
        print("  ⚠️  Article too short to review")
        return

    prompt_type = TRACK_PROMPT.get(track, DEFAULT_PROMPT)
    article_type = {
        "compile_pedagogy_brief.md": "A1 pedagogical brief",
        "compile_grammar_brief.md": "grammar brief",
        "compile_academic.md": "academic brief",
        "compile_article.md": "seminar knowledge article",
    }.get(prompt_type, "wiki article")

    review_dir = WIKI_DIR / ".reviews" / str(article_path.parent.relative_to(WIKI_DIR))
    review_dir.mkdir(parents=True, exist_ok=True)
    project_root = str(Path(__file__).resolve().parents[2])

    score = 0
    review_text = ""
    applied = 0

    for round_num in range(1, max_rounds + 1):
        # Step 1: Review
        article_text = article_path.read_text("utf-8")
        review_prompt = (
            f"You are a HARSH adversarial reviewer of a {article_type} for the Ukrainian "
            "language curriculum wiki. Your job is to find problems, not praise.\n\n"
            f"Track: {track}, Slug: {slug}, Round: {round_num}\n\n"
            "## Review Rubric (score EACH dimension 1-10, then average)\n\n"
            "1. **Factual accuracy** — every claim must have evidence from sources. "
            "Vague or unsourced claims → deduct points.\n"
            "2. **Ukrainian language quality** — check for Russianisms (кон→кін), "
            "surzhyk (шо→що), calques (приймати душ→брати душ). Even ONE Russianism = max 7/10.\n"
            "3. **Decolonization** — is Ukrainian presented on its own terms? Any "
            "'like Russian but...' framing = max 6/10.\n"
            "4. **Completeness** — does it cover ALL aspects a module writer needs? "
            "Missing sections or shallow treatment → deduct.\n"
            "5. **Actionable guidance** — can a writer actually USE this? Generic advice "
            "like 'teach it well' = max 5/10. Must have specific examples, sequences, exercises.\n\n"
            "## Rules\n"
            "- Score each dimension separately, then give weighted average.\n"
            "- Be honest. If the article is excellent, say so. 10/10 IS possible.\n"
            "- 9/10 = excellent with minor issues. 8/10 = good. 7/10 = needs work.\n"
            "- Output a <fixes> block ONLY if there are real issues to fix. "
            "If the article is clean, output <fixes></fixes> (empty) and the review stops.\n"
            "- Do NOT invent problems. Fabricated issues waste rebuild cycles.\n\n"
            "## Output format\n\n"
            "Dimension scores:\n"
            "1. Factual: X/10 — [evidence]\n"
            "2. Language: X/10 — [evidence]\n"
            "3. Decolonization: X/10 — [evidence]\n"
            "4. Completeness: X/10 — [evidence]\n"
            "5. Actionable: X/10 — [evidence]\n\n"
            "**Overall: X/10**\n\n"
            "<fixes>\n"
            "old: exact text to find in the article\n"
            "new: replacement text\n"
            "---\n"
            "old: another exact find\n"
            "new: another replacement\n"
            "</fixes>\n\n"
            f"## Article to review\n\n{article_text[:15000]}"
        )

        try:
            result = subprocess.run(
                [
                    sys.executable, "scripts/ai_agent_bridge/__main__.py",
                    "ask-gemini", review_prompt,
                    "--task-id", f"wiki-review-{track}-{slug}-r{round_num}",
                    "--model", "gemini-3.1-pro-preview",
                ],
                capture_output=True, text=True, timeout=300,
                cwd=project_root,
            )
        except Exception as e:
            print(f"  ⚠️  Review error: {e}")
            return

        if result.returncode != 0:
            print(f"  ⚠️  Review failed: {result.stderr[:200]}")
            return

        review_text = result.stdout
        review_path = review_dir / f"{slug}-review-r{round_num}.md"
        review_path.write_text(review_text, "utf-8")

        # Parse score — find the OVERALL score, not per-dimension scores
        import re
        # Look for "Overall: X/10" or "Score: X/10" (the final verdict)
        overall_match = re.search(
            r"(?:overall|score|verdict|підсумок)[:\s]*\**\s*(\d+)\s*/\s*10",
            review_text, re.IGNORECASE,
        )
        if overall_match:
            score = int(overall_match.group(1))
        else:
            # Fallback: take the LAST X/10 in the text (usually the overall)
            all_scores = re.findall(r"(\d+)\s*/\s*10", review_text)
            score = int(all_scores[-1]) if all_scores else 0
        print(f"  📋 Round {round_num}: {score}/10")

        # Step 2: Extract and apply fixes (always — even if score >= 9)
        # Strip markdown code fences before searching for <fixes> tags
        clean_review = re.sub(r"```\w*\n?", "", review_text)
        fixes_match = re.search(r"<fixes>(.*?)</fixes>", clean_review, re.DOTALL)
        fix_pairs = _parse_wiki_fixes(fixes_match.group(1).strip()) if fixes_match else []

        if fix_pairs:
            applied = 0
            for old, new in fix_pairs:
                if old in article_text:
                    article_text = article_text.replace(old, new, 1)
                    applied += 1
            if applied:
                article_path.write_text(article_text, "utf-8")
                print(f"  🔧 Applied {applied}/{len(fix_pairs)} fixes")
        else:
            print("  ✅ No fixes needed — article is clean")

        # Step 3: Check if we're done
        if not fix_pairs or score >= 9:
            print(f"  ✅ Review PASSED ({score}/10)")
            final_path = review_dir / f"{slug}-review.md"
            final_path.write_text(review_text, "utf-8")
            return

        if not fix_pairs:
            print("  ⚠️  No fixes to apply — cannot improve further")
            break

        if fix_pairs and applied == 0:
            print(f"  ⚠️  0/{len(fix_pairs)} fixes matched — stopping")
            break

        print("  🔄 Re-reviewing after fixes...")

    # Exhausted rounds — save final review
    final_path = review_dir / f"{slug}-review.md"
    final_path.write_text(review_text, "utf-8")
    print(f"  📝 Final score: {score}/10 after {max_rounds} round(s)")


def _parse_wiki_fixes(fixes_text: str) -> list[tuple[str, str]]:
    """Parse old:/new: pairs from a <fixes> block.

    Handles both formats:
    - Separated by --- between pairs
    - Consecutive old:/new: pairs without separators
    """
    pairs = []
    lines = fixes_text.split("\n")
    old_lines: list[str] = []
    new_lines: list[str] = []
    current: str | None = None

    def _flush():
        old = "\n".join(old_lines).strip()
        new = "\n".join(new_lines).strip()
        if old and old != new:
            pairs.append((old, new))
        old_lines.clear()
        new_lines.clear()

    for line in lines:
        stripped = line.strip()
        if stripped == "---":
            _flush()
            current = None
            continue
        if stripped.startswith("old:"):
            if old_lines and new_lines:
                _flush()  # New pair starting — flush previous
            current = "old"
            old_lines.append(stripped[4:].strip())
        elif stripped.startswith("new:"):
            current = "new"
            new_lines.append(stripped[4:].strip())
        elif current == "old":
            old_lines.append(line)
        elif current == "new":
            new_lines.append(line)

    _flush()  # Don't forget last pair
    return pairs


def cmd_review_existing(track: str, *, slug: str | None = None,
                        limit: int | None = None) -> None:
    """Review already-compiled wiki articles without recompiling."""
    from wiki.config import WIKI_DIR

    # Find articles for this track
    domains = TRACK_DOMAINS.get(track, [])
    articles = []
    for domain in domains:
        domain_dir = WIKI_DIR / domain
        if not domain_dir.exists():
            continue
        for md_file in sorted(domain_dir.rglob("*.md")):
            if md_file.name == "index.md":
                continue
            if slug and md_file.stem != slug:
                continue
            articles.append(md_file)

    if not articles:
        print(f"No compiled articles found for {track}")
        return

    if limit:
        articles = articles[:limit]

    print(f"\n🔍 Reviewing {len(articles)} existing articles for {track.upper()}")
    print(f"{'═' * 60}")

    for i, article_path in enumerate(articles, 1):
        article_slug = article_path.stem
        print(f"\n[{i}/{len(articles)}] {article_slug}")
        _review_article(article_path, track, article_slug)

    print(f"\n{'═' * 60}")
    print(f"  Reviewed: {len(articles)} articles")


def cmd_compile_all(track: str, *, limit: int | None = None,
                    force: bool = False, dry_run: bool = False,
                    review: bool = False) -> None:
    """Compile all articles for a track."""
    slugs = list_discovery_slugs(track)
    if not slugs:
        print(f"No discovery files for track '{track}'")
        return

    if limit:
        slugs = slugs[:limit]

    print(f"\n🔨 Compiling {len(slugs)} articles for {track.upper()}")
    if review:
        print("  📋 Review enabled — each article will be reviewed after compilation")
    print(f"{'═' * 60}")

    success = 0
    failed = 0
    skipped = 0

    for i, slug in enumerate(slugs, 1):
        print(f"\n[{i}/{len(slugs)}] {slug}")
        result = cmd_compile_one(track, slug, force=force, dry_run=dry_run, review=review)
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
    from wiki.config import TRACK_WRITE_DOMAIN

    # Core levels have a direct mapping
    if track in TRACK_WRITE_DOMAIN:
        return TRACK_WRITE_DOMAIN[track]

    # FOLK has per-slug subdomain mapping
    if track == "folk":
        return FOLK_DOMAIN_MAP.get(slug, "folk")

    # Seminar tracks
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


def _slug_to_topic(slug: str, track: str, sources_info: dict | None = None) -> str:
    """Build a topic name, preferring Ukrainian from discovery keywords.

    Falls back to Latin slug title-case if no discovery data available.
    """
    track_labels = {
        "a1": "Педагогіка A1",
        "a2": "Граматика A2",
        "b1": "Граматика B1",
        "b2": "Граматика B2",
        "c1": "Академічна C1",
        "c2": "Майстерність C2",
        "folk": "Український фольклор",
        "hist": "Історія України",
        "bio": "Біографія",
        "istorio": "Історіографія",
        "lit": "Українська література",
        "lit-essay": "Українська есеїстика",
        "lit-war": "Воєнна проза",
        "lit-hist-fic": "Історична проза",
        "lit-fantastika": "Українська фантастика",
        "lit-humor": "Гумор і сатира",
        "lit-youth": "Література для молоді",
        "lit-drama": "Українська драматургія",
        # lit-doc, lit-crimea: not in curriculum.yaml yet
        "oes": "Давньоруська мова",
        "ruth": "Руська (староукраїнська) мова",
    }
    label = track_labels.get(track, track.upper())

    # Try to get Ukrainian topic from discovery keywords (first keyword is usually the title)
    if sources_info:
        discovery = sources_info.get("discovery", {})
        keywords = discovery.get("query_keywords", [])
        if keywords:
            # First keyword is usually the topic title in Ukrainian
            first_kw = keywords[0]
            # Check if it has Cyrillic (Ukrainian)
            if any("\u0400" <= c <= "\u04FF" for c in first_kw):
                return f"{label}: {first_kw}"

    # Fallback: Latin slug
    topic = slug.replace("-", " ").title()
    return f"{label}: {topic}"


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description=(
            "Wiki knowledge base compiler. Compiles curated articles from textbook "
            "sources and RAG data using Gemini. Articles are used as context for "
            "module content generation.\n\n"
            "Prompt per track type:\n"
            "  A1:         Pedagogical briefs (methodology, phonetics, vocab boundaries)\n"
            "  A2-B2:      Grammar briefs (paradigms, frequency, L2 errors)\n"
            "  C1-C2:      Academic briefs (scholarly register, stylistics)\n"
            "  Seminars:   Knowledge articles (primary sources, historiography)"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument("--status", action="store_true",
                        help="Show compilation status for all tracks")
    parser.add_argument("--update-index", action="store_true",
                        help="Regenerate wiki/index.md from all compiled articles")

    # Track selection
    parser.add_argument("--track", choices=ALL_TRACKS,
                        help="Track to compile (a1-c2 for core, folk/hist/etc for seminars)")
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
    parser.add_argument("--review", action="store_true",
                        help="Review articles after compilation")
    parser.add_argument("--review-only", action="store_true",
                        help="Review existing articles without recompiling")

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

    if args.review_only:
        cmd_review_existing(args.track, slug=args.slug, limit=args.limit)
        return

    if args.slug:
        success = cmd_compile_one(
            args.track, args.slug,
            force=args.force, dry_run=args.dry_run,
            review=args.review,
        )
        sys.exit(0 if success else 1)

    if args.compile_all:
        cmd_compile_all(
            args.track,
            limit=args.limit, force=args.force, dry_run=args.dry_run,
            review=args.review,
        )
        return

    parser.error("Specify --slug, --all, or --list")


if __name__ == "__main__":
    main()
