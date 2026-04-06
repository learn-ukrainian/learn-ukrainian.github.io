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
from wiki.state import get_status_summary, log_event, read_log

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


def cmd_log(*, track: str | None = None) -> None:
    """Show build log — structured events from compilation + review.

    Usage:
        --log                   Show all recent events
        --log --track a2        Show only A2 events
    """
    entries = read_log(track=track)
    if not entries:
        print("No build log entries found.")
        return

    # Group by slug for a summary view
    by_slug: dict[str, list[dict]] = {}
    for e in entries:
        key = f"{e['track']}/{e['slug']}"
        by_slug.setdefault(key, []).append(e)

    print(f"\n📊 Build Log ({len(entries)} events, {len(by_slug)} articles)")
    if track:
        print(f"   Filtered: {track}")
    print(f"{'─' * 70}")

    for key, events in by_slug.items():
        # Find compile and final review events
        compile_evt = next((e for e in events if e["event"] == "compile"), None)
        final_evt = next((e for e in reversed(events)
                         if e["event"] in ("review_pass", "review_fail", "review_reverted")), None)
        rounds = [e for e in events if e["event"] == "review_round"]

        words = compile_evt.get("words", "?") if compile_evt else "?"
        if final_evt:
            score = final_evt.get("score", "?")
            status = "✅" if final_evt["event"] == "review_pass" else "❌"
            n_rounds = final_evt.get("rounds", len(rounds))
        else:
            score = "pending"
            status = "⏳"
            n_rounds = len(rounds)

        # Show round progression
        round_scores = " → ".join(str(r.get("score", "?")) for r in rounds)

        print(f"  {status} {key:<45} {score}/10  ({words}w, {n_rounds}r)")
        if rounds:
            print(f"     rounds: {round_scores}")

    # Summary stats
    passed = sum(1 for evts in by_slug.values()
                 if any(e["event"] == "review_pass" for e in evts))
    failed = sum(1 for evts in by_slug.values()
                 if any(e["event"] == "review_fail" for e in evts))
    pending = len(by_slug) - passed - failed
    print(f"\n{'─' * 70}")
    print(f"  ✅ Passed: {passed}  ❌ Failed: {failed}  ⏳ Pending: {pending}")


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
        word_count = len(result.read_text("utf-8").split()) if result.exists() else 0
        log_event(track, slug, "compile", words=word_count, sources=len(all_chunks))
        if review and not dry_run:
            _review_article(result, track, slug)
        return True
    return dry_run  # dry_run returns None but isn't a failure


def _parse_review_scores(review_text: str) -> dict[str, float]:
    """Parse all review scores: 5 dimensions + overall. Handles decimals.

    Returns dict like:
        {"factual": 9.0, "language": 9.0, "decolonization": 10.0,
         "completeness": 7.0, "actionable": 9.0, "overall": 8.8}

    Missing dimensions default to 0.0. Overall is parsed from the explicit
    "Overall:" line, NOT averaged from dimensions (reviewer may weight them).

    IMPORTANT: The review text contains the prompt template echo (with "X/10"
    placeholders) followed by Gemini's actual response. We use findall and
    take the LAST match for each dimension to skip the template.
    """
    import re

    scores: dict[str, float] = {}

    # Parse individual dimensions — take LAST match to skip prompt template echo
    dimension_names = {
        "factual": r"factual",
        "language": r"(?:language|ukrainian\s+language)",
        "decolonization": r"decolonization",
        "completeness": r"completeness",
        "actionable": r"actionable",
    }
    for key, pattern in dimension_names.items():
        matches = re.findall(
            rf"{pattern}\**[:\s]*\**\s*(\d+(?:\.\d+)?)\s*/\s*10",
            review_text, re.IGNORECASE,
        )
        # Last match = Gemini's actual score (first may be prompt template)
        scores[key] = float(matches[-1]) if matches else 0.0

    # Parse overall score — also take LAST match
    overall_matches = re.findall(
        r"(?:overall|score|verdict|підсумок)[:\s]*\**\s*(\d+(?:\.\d+)?)\s*/\s*10",
        review_text, re.IGNORECASE,
    )
    if overall_matches:
        scores["overall"] = float(overall_matches[-1])
    else:
        # Fallback: last X/10 in the text
        all_scores = re.findall(r"(\d+(?:\.\d+)?)\s*/\s*10", review_text)
        scores["overall"] = float(all_scores[-1]) if all_scores else 0.0

    return scores


def _build_review_prompt(article_text: str, article_type: str,
                         track: str, slug: str, round_label: str) -> str:
    """Build a review prompt with the CURRENT article text."""
    return (
        f"You are a HARSH adversarial reviewer of a {article_type} for the Ukrainian "
        "language curriculum wiki. Your job is to find problems, not praise.\n\n"
        f"Track: {track}, Slug: {slug}, Round: {round_label}\n\n"
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
        "- Output a <fixes> block with specific changes. "
        "If the article is clean, output <fixes></fixes> (empty).\n"
        "- Do NOT invent problems. Fabricated issues waste rebuild cycles.\n\n"
        "## Fix syntax\n\n"
        "Two formats are available:\n\n"
        "**1. Replace existing text** (for corrections, rewording):\n"
        "Use a SHORT anchor (1-2 sentences max) for the old: text. "
        "Do NOT paste massive paragraphs — they break exact matching.\n"
        "```\n"
        "old: short exact text to find\n"
        "new: replacement text\n"
        "```\n\n"
        "**2. Insert new content** (for missing sections, added examples):\n"
        "Use INSERT AFTER with a short anchor from the article, then the new text to add.\n"
        "```\n"
        "INSERT AFTER: short anchor text that exists in the article\n"
        "NEW TEXT: the new content to insert after the anchor\n"
        "```\n\n"
        "Separate multiple fixes with `---`.\n\n"
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
        "INSERT AFTER: anchor text in article\n"
        "NEW TEXT: content to add after the anchor\n"
        "</fixes>\n\n"
        f"## Article to review\n\n{article_text[:15000]}"
    )


def _normalize_whitespace(text: str) -> str:
    """Normalize whitespace for fuzzy matching: collapse runs, strip line-trailing."""
    import re
    # Strip trailing whitespace per line
    text = "\n".join(line.rstrip() for line in text.split("\n"))
    # Collapse multiple spaces (but not newlines — those are structural)
    text = re.sub(r" {2,}", " ", text)
    return text


def _map_norm_pos_to_orig(article_text: str, norm_article: str,
                          norm_target: int) -> int:
    """Map a position in normalized text back to the corresponding position in original.

    Walks both strings in parallel: characters that match advance the normalized
    cursor; characters that were collapsed (extra spaces, trailing whitespace)
    only advance the original cursor.
    """
    orig_pos = 0
    norm_pos = 0
    while norm_pos < norm_target and orig_pos < len(article_text):
        if article_text[orig_pos] == norm_article[norm_pos]:
            norm_pos += 1
        orig_pos += 1
    return orig_pos


def _fuzzy_replace(article_text: str, old: str, new: str) -> str | None:
    """Try whitespace-normalized matching when exact match fails.

    Returns updated text on success, None on failure.
    """
    norm_article = _normalize_whitespace(article_text)
    norm_old = _normalize_whitespace(old)

    if norm_old not in norm_article:
        return None

    # Find match boundaries in normalized text
    norm_start = norm_article.index(norm_old)
    norm_end = norm_start + len(norm_old)

    # Map both boundaries back to original text independently
    orig_start = _map_norm_pos_to_orig(article_text, norm_article, norm_start)
    orig_end = _map_norm_pos_to_orig(article_text, norm_article, norm_end)

    # Replace the original span
    return article_text[:orig_start] + new + article_text[orig_end:]


def _extract_and_apply_fixes(review_text: str, article_text: str) -> tuple[str, int, int]:
    """Extract fixes from review and apply them to article text.

    Supports two fix types:
    - old:/new: — find and replace (with whitespace-normalized fallback)
    - INSERT AFTER:/NEW TEXT: — insert new content after an anchor

    Returns: (updated_article_text, total_fixes, applied_count)
    """
    import re

    # Strip markdown code fences before searching for <fixes> tags
    clean_review = re.sub(r"```\w*\n?", "", review_text)
    # Use findall + take LAST match — earlier matches may be from the prompt template
    fixes_matches = re.findall(r"<fixes>(.*?)</fixes>", clean_review, re.DOTALL)
    fixes_content = fixes_matches[-1].strip() if fixes_matches else ""

    if not fixes_content:
        return article_text, 0, 0

    # Parse both old:/new: pairs and INSERT AFTER:/NEW TEXT: directives
    fix_pairs = _parse_wiki_fixes(fixes_content)
    insert_directives = _parse_insert_directives(fixes_content)
    total = len(fix_pairs) + len(insert_directives)

    if total == 0:
        return article_text, 0, 0

    applied = 0

    # Apply old:/new: replacements (exact match first, then fuzzy)
    for old, new in fix_pairs:
        if old in article_text:
            article_text = article_text.replace(old, new, 1)
            applied += 1
        else:
            # Fuzzy fallback: whitespace-normalized matching
            result = _fuzzy_replace(article_text, old, new)
            if result is not None:
                article_text = result
                applied += 1

    # Apply INSERT AFTER: directives
    for anchor, new_text in insert_directives:
        if anchor in article_text:
            pos = article_text.index(anchor) + len(anchor)
            article_text = article_text[:pos] + "\n" + new_text + article_text[pos:]
            applied += 1
        else:
            # Fuzzy anchor matching
            norm_article = _normalize_whitespace(article_text)
            norm_anchor = _normalize_whitespace(anchor)
            if norm_anchor in norm_article:
                # Find original position of anchor end
                result = _fuzzy_replace(article_text, anchor, anchor + "\n" + new_text)
                if result is not None:
                    article_text = result
                    applied += 1

    return article_text, total, applied


def _parse_insert_directives(fixes_text: str) -> list[tuple[str, str]]:
    """Parse INSERT AFTER:/NEW TEXT: pairs from a <fixes> block.

    Returns list of (anchor_text, new_text) tuples.
    """
    pairs = []
    lines = fixes_text.split("\n")
    anchor_lines: list[str] = []
    new_lines: list[str] = []
    current: str | None = None

    def _flush():
        anchor = "\n".join(anchor_lines).strip()
        new = "\n".join(new_lines).strip()
        if anchor and new:
            pairs.append((anchor, new))
        anchor_lines.clear()
        new_lines.clear()

    for line in lines:
        stripped = line.strip()
        if stripped == "---":
            _flush()
            current = None
            continue
        if stripped.upper().startswith("INSERT AFTER:"):
            if anchor_lines and new_lines:
                _flush()
            current = "anchor"
            anchor_lines.append(stripped[len("INSERT AFTER:"):].strip())
        elif stripped.upper().startswith("NEW TEXT:"):
            current = "new"
            new_lines.append(stripped[len("NEW TEXT:"):].strip())
        elif current == "anchor":
            anchor_lines.append(line)
        elif current == "new":
            new_lines.append(line)

    _flush()
    return pairs


def _needs_structural_rewrite(scores: dict[str, float]) -> bool:
    """Check if any dimension is below 8 — requires targeted rewrite, not copyedit."""
    for key in ("factual", "language", "decolonization", "completeness", "actionable"):
        if scores.get(key, 0) < 8.0:
            return True
    return scores.get("overall", 0) < 8.0


def _send_review(track: str, slug: str, review_prompt: str,
                 round_label: str, project_root: str) -> str | None:
    """Send a review prompt to Gemini via agent bridge. Returns stdout or None."""
    import subprocess

    try:
        result = subprocess.run(
            [
                sys.executable, "scripts/ai_agent_bridge/__main__.py",
                "ask-gemini", "-",  # Read prompt from stdin (avoids arg length limits)
                "--task-id", f"wiki-review-{track}-{slug}-{round_label}",
                "--model", "gemini-3.1-pro-preview",
            ],
            input=review_prompt,
            capture_output=True, text=True, timeout=300,
            cwd=project_root,
        )
    except Exception as e:
        print(f"  ⚠️  Review error: {e}")
        return None

    if result.returncode != 0:
        print(f"  ⚠️  Review failed: {result.stderr[:200]}")
        return None

    return result.stdout


def _clean_rewrite_response(response: str) -> str | None:
    """Extract a clean article from Gemini's rewrite response.

    Handles common issues:
    1. Prompt echo: Gemini echoes back parts of the rewrite prompt
       (instructions, critique, old article) before producing the new article.
    2. Duplicate titles: Old article title appears first, then the rewrite
       starts with the same title again — take the LAST top-level heading.
    3. Truncation: Response cuts off mid-word/mid-sentence.
    4. Code fences: Gemini wraps response in ```markdown ... ```.
    5. Agent bridge metadata: stdout diagnostics mixed into response.

    Returns cleaned markdown string, or None if response is unusable.
    """
    import re

    if not response or len(response) < 100:
        return None

    # Strip agent bridge metadata that leaks into stdout
    lines = response.split("\n")
    clean_lines = [
        line for line in lines
        if not re.match(
            r"^\s*(✓|✅|ℹ️|Auto-acknowledged|────|📎 Attached|🤖 Processing|"
            r"\[gemini\]|Dimension scores:|<fixes>|</fixes>)",
            line,
        )
    ]
    response = "\n".join(clean_lines).strip()

    if len(response) < 100:
        return None

    # Strip markdown code fences wrapping the entire response
    # Gemini sometimes wraps: ```markdown\n# Title\n...\n```
    fence_match = re.match(r"^```\w*\n(.*)\n```\s*$", response, re.DOTALL)
    if fence_match:
        response = fence_match.group(1)

    # Strip prompt fragments that Gemini sometimes echoes back
    prompt_fragments = [
        "## Instructions\n",
        "## Reviewer critique\n",
        "## Current article\n",
        "## Weak dimensions:",
    ]
    for frag in prompt_fragments:
        if frag in response:
            idx = response.rfind(frag)
            # Find next heading (H1 or H2) AFTER the prompt fragment line
            after_frag = idx + len(frag)
            next_heading = re.search(r"^#{1,2}\s+", response[after_frag:], re.MULTILINE)
            if next_heading:
                response = response[after_frag + next_heading.start():]
                break

    # Find the LAST top-level heading (# Title) — Gemini may echo the old
    # article title first, then produce the actual rewrite starting with
    # the same title again. We want the LAST occurrence.
    title_matches = list(re.finditer(r"^(#\s+[^#\n].+)", response, re.MULTILINE))
    if title_matches:
        last_title = title_matches[-1]
        if len(title_matches) > 1:
            print(f"  ℹ️  Found {len(title_matches)} top-level headings, "
                  "taking from last (stripping prompt echo)")
        response = response[last_title.start():]
    elif re.search(r"^##\s+", response, re.MULTILINE):
        pass  # No top-level heading but has section headings — accept as-is
    else:
        return None

    # Truncation detection: reject if response ends mid-word or mid-sentence
    # Allow common terminal characters: punctuation, quotes, brackets, pipes
    stripped = response.rstrip()
    if stripped and stripped[-1] not in '.!?»"\')]\n`|':
        last_line = stripped.split("\n")[-1].strip()
        # Allow: headings, table rows, list items, code blocks, HTML comments
        if (last_line and not last_line.startswith(("#", "|", "-", "*", ">", "```", "<!--"))
                and len(last_line) > 20):
            print(f"  ⚠️  Rewrite appears truncated (ends with: "
                  f"...{last_line[-40:]!r})")
            return None

    return response


def _targeted_rewrite(article_path: Path, article_text: str,
                      article_type: str,
                      track: str, slug: str, review_text: str,
                      scores: dict[str, float],
                      project_root: str) -> bool:
    """Send article + critique to Gemini for targeted section rewrite.

    Does NOT recompile from scratch — preserves existing high-quality text.
    Returns True if rewrite succeeded.
    """
    import subprocess

    # Identify weak dimensions for the rewrite directive
    weak = [k for k in ("factual", "language", "decolonization", "completeness", "actionable")
            if scores.get(k, 0) < 8.0]
    weak_str = ", ".join(weak) if weak else "overall quality"

    rewrite_prompt = (
        f"You are rewriting specific sections of a {article_type} for the Ukrainian "
        "language curriculum wiki. This is NOT a full rewrite — preserve all existing "
        "high-quality text. Only rewrite the sections that need improvement.\n\n"
        f"Track: {track}, Slug: {slug}\n\n"
        f"## Weak dimensions: {weak_str}\n\n"
        "## Reviewer critique\n\n"
        f"{review_text[:5000]}\n\n"
        "## Instructions\n"
        "1. Read the critique carefully.\n"
        "2. Identify which SPECIFIC sections need rewriting to address the critique.\n"
        "3. Output the COMPLETE article with those sections rewritten.\n"
        "4. Do NOT remove or degrade sections that scored well.\n"
        "5. Do NOT add commentary — output ONLY the article markdown.\n"
        "6. CRITICAL: Start your response DIRECTLY with `# Title`. Do NOT echo these "
        "instructions, the critique, or any preamble. The very first line of your "
        "output must be the `# Title` heading of the article.\n\n"
        f"## Current article\n\n{article_text[:15000]}"
    )

    try:
        result = subprocess.run(
            [
                sys.executable, "scripts/ai_agent_bridge/__main__.py",
                "ask-gemini", "-",  # Read prompt from stdin
                "--task-id", f"wiki-rewrite-{track}-{slug}",
                "--model", "gemini-3.1-pro-preview",
            ],
            input=rewrite_prompt,
            capture_output=True, text=True, timeout=600,
            cwd=project_root,
        )
    except Exception as e:
        print(f"  ⚠️  Rewrite error: {e}")
        return False

    if result.returncode != 0:
        print(f"  ⚠️  Rewrite failed: {result.stderr[:200]}")
        return False

    response = result.stdout.strip()

    # Validate: response should be markdown starting with #, and not dramatically shorter
    if not response or len(response) < 100:
        print("  ⚠️  Rewrite returned empty/short response — keeping original")
        return False

    # Clean the response: strip prompt echo, find article, detect truncation
    cleaned = _clean_rewrite_response(response)
    if cleaned is None:
        print("  ⚠️  Could not extract clean article from rewrite response — keeping original")
        return False
    response = cleaned

    # Safety: don't accept if new article is <70% of original length (regression guard)
    if len(response) < len(article_text) * 0.7:
        print(f"  ⚠️  Rewrite too short ({len(response)} vs {len(article_text)} chars)"
              " — keeping original")
        return False

    article_path.write_text(response + "\n", "utf-8")
    new_words = len(response.split())
    log_event(track, slug, "rewrite", words=new_words,
              weak_dimensions=weak_str)
    print(f"  ✏️  Rewrite applied ({new_words} words)")
    return True


def _review_article(article_path: Path, track: str, slug: str,
                    max_rounds: int = 4) -> None:
    """Review a wiki article with split-path fix strategy.

    Flow:
    1. Review → parse dimension scores
    2. If all dimensions ≥ 8: COPYEDIT path (old:/new: + INSERT AFTER:)
    3. If any dimension < 8: TARGETED REWRITE path (Gemini rewrites weak sections)
    4. If no fixes and score < 9: route to rewrite (lazy reviewer = structural problem)
    5. After last round, final scoring pass with fix application

    Max 4 rounds total (copyedit + rewrite combined).
    """
    from wiki.config import DEFAULT_PROMPT, TRACK_PROMPT, WIKI_DIR

    print(f"  🔍 Reviewing: {track}/{slug}")

    if not article_path.exists() or article_path.stat().st_size < 100:
        print("  ⚠️  Article missing or too short to review")
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

    score = 0.0
    scores: dict[str, float] = {}
    review_text = ""
    last_applied = 0
    rewrite_used = False  # Only allow ONE structural rewrite per article
    best_score = 0.0
    best_article = ""  # Snapshot of article text at peak score

    for round_num in range(1, max_rounds + 1):
        # Step 1: Build prompt with FRESH article text every round
        article_text = article_path.read_text("utf-8")
        review_prompt = _build_review_prompt(
            article_text, article_type, track, slug, str(round_num),
        )

        # Step 2: Send to Gemini for review
        new_review = _send_review(
            track, slug, review_prompt, f"r{round_num}", project_root,
        )
        if not new_review:
            break  # Preserve review_text from last successful round
        review_text = new_review

        review_path = review_dir / f"{slug}-review-r{round_num}.md"
        review_path.write_text(review_text, "utf-8")

        # Step 3: Parse ALL dimension scores
        scores = _parse_review_scores(review_text)
        score = scores["overall"]
        dim_summary = " | ".join(
            f"{k[:4]}:{v}" for k, v in scores.items() if k != "overall"
        )
        print(f"  📋 Round {round_num}: {score}/10 [{dim_summary}]")
        log_event(track, slug, "review_round", round=round_num,
                  score=score, **{k: v for k, v in scores.items() if k != "overall"})

        # Step 4: Track peak score — if we regress, revert to best version
        if score > best_score:
            best_score = score
            best_article = article_text
        elif score < best_score - 0.5 and round_num > 2:
            # Score dropped significantly — revert to peak and stop
            print(f"  ⚠️  Score regressed ({best_score} → {score}) — reverting to peak")
            article_path.write_text(best_article, "utf-8")
            score = best_score
            last_applied = 0  # Don't trigger final review — peak is the final state
            if review_text:
                final_path = review_dir / f"{slug}-review.md"
                final_path.write_text(review_text, "utf-8")
            log_event(track, slug, "review_reverted", score=score,
                      peak_score=best_score)
            print(f"  📝 Final score: {score}/10 (peak from round {round_num - 1})")
            return

        # Step 5: Check if we're done
        if score >= 9.0:
            log_event(track, slug, "review_pass", score=score, rounds=round_num)
            print(f"  ✅ Review PASSED ({score}/10)")
            final_path = review_dir / f"{slug}-review.md"
            final_path.write_text(review_text, "utf-8")
            return

        # Step 6: Route — copyedit or structural rewrite?
        # Structural rewrite allowed ONCE. Multiple rewrites cause oscillation
        # (fix one dimension, break another — observed: 8.4→7.4→7.8→7.0→6.2).
        needs_rewrite = _needs_structural_rewrite(scores) and not rewrite_used

        if needs_rewrite:
            # STRUCTURAL REWRITE PATH: any dimension < 8 (first time only)
            weak = [k for k in ("factual", "language", "decolonization",
                                "completeness", "actionable")
                    if scores.get(k, 0) < 8.0]
            print(f"  🔨 Structural rewrite (weak: {', '.join(weak) or 'overall'})")
            success = _targeted_rewrite(
                article_path, article_text, article_type, track, slug,
                review_text, scores, project_root,
            )
            rewrite_used = True
            if success:
                last_applied = 1
                print("  🔄 Re-reviewing after rewrite...")
                continue
            else:
                print("  ⚠️  Rewrite failed — stopping")
                break
        else:
            # COPYEDIT PATH: localized fixes (also used after rewrite is exhausted)
            if _needs_structural_rewrite(scores) and rewrite_used:
                print("  ℹ️  Structural issues remain — rewrite exhausted, trying copyedit")

            article_text, total_fixes, last_applied = _extract_and_apply_fixes(
                review_text, article_text,
            )

            if last_applied > 0:
                article_path.write_text(article_text, "utf-8")
                print(f"  🔧 Applied {last_applied}/{total_fixes} fixes")
            elif total_fixes > 0:
                print(f"  ⚠️  0/{total_fixes} fixes matched — stopping")
                break
            elif not rewrite_used:
                # No fixes + score < 9 + no rewrite yet = try rewrite once
                print(f"  🔨 No fixes but score {score}/10 — routing to rewrite")
                success = _targeted_rewrite(
                    article_path, article_text, article_type, track, slug,
                    review_text, scores, project_root,
                )
                rewrite_used = True
                if success:
                    last_applied = 1
                    print("  🔄 Re-reviewing after rewrite...")
                    continue
                else:
                    print("  ⚠️  Rewrite failed — stopping")
                    break
            else:
                print(f"  ⚠️  No fixes, rewrite exhausted — stopping at {score}/10")
                break

        print("  🔄 Re-reviewing after fixes...")

    # After the loop: if we changed the article in the last round, do a final
    # scoring review on the CURRENT article to get an accurate final score
    if last_applied > 0:
        print("  🔄 Final scoring review on fixed article...")
        article_text = article_path.read_text("utf-8")
        review_prompt = _build_review_prompt(
            article_text, article_type, track, slug, "final",
        )

        final_review = _send_review(
            track, slug, review_prompt, "final", project_root,
        )
        if final_review:
            review_text = final_review  # Only update if API succeeded
            scores = _parse_review_scores(review_text)
            score = scores["overall"]
            print(f"  📋 Final: {score}/10")

            # Apply any remaining fixes from the final review too
            article_text, total_fixes, final_applied = _extract_and_apply_fixes(
                review_text, article_text,
            )
            if final_applied > 0:
                article_path.write_text(article_text, "utf-8")
                print(f"  🔧 Applied {final_applied}/{total_fixes} final fixes")

            review_path = review_dir / f"{slug}-review-final.md"
            review_path.write_text(review_text, "utf-8")

    # Save final review (from last successful round — never empty)
    if review_text:
        final_path = review_dir / f"{slug}-review.md"
        final_path.write_text(review_text, "utf-8")
    # If we reached here, we exhausted max_rounds without hitting 9.0
    # (the >= 9.0 case returns early above)
    log_event(track, slug, "review_fail", score=score, rounds=max_rounds)
    print(f"  📝 Final score: {score}/10 after review loop")


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
    parser.add_argument("--log", action="store_true",
                        help="Show build log (filter with --track)")

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

    if args.log:
        cmd_log(track=args.track)
        return

    if not args.track:
        parser.error("--track is required (or use --status/--log)")

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
