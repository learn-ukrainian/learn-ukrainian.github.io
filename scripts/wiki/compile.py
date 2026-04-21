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
import time
import traceback
from datetime import datetime
from pathlib import Path

# Force line-buffered stdout so progress is visible even when piped (tee, less,
# some terminals).  Without this, `print()` can buffer for kilobytes and make
# the process look frozen.
try:
    sys.stdout.reconfigure(line_buffering=True)  # type: ignore[attr-defined]
    sys.stderr.reconfigure(line_buffering=True)  # type: ignore[attr-defined]
except AttributeError:
    pass  # Python < 3.7 fallback — not supported here anyway

# Add scripts/ to path for relative imports
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def _ts() -> str:
    """Compact HH:MM:SS timestamp for log lines."""
    return datetime.now().strftime("%H:%M:%S")

from wiki.compiler import compile_article, update_index
from wiki.config import ALL_TRACKS, CURRICULUM_DIR, TRACK_DOMAINS, WIKI_DIR
from wiki.context import strip_meta
from wiki.enrichment import enrich_sources
from wiki.sources import (
    gather_discovery_sources,
    list_discovery_slugs,
    list_discovery_slugs_readonly,
    list_literary_sources,
)
from wiki.sources_schema import (
    extract_short_citation_ids,
    load_sources_registry,
    registry_path_for,
    validate_sources_registry,
)
from wiki.state import log_event, read_log

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


def _progress_bar(done: int, total: int, width: int = 20) -> str:
    """Render a compact progress bar: [████████░░░░] 8/12."""
    if total == 0:
        return f"[{'░' * width}] 0/0"
    filled = round(width * done / total)
    bar = "█" * filled + "░" * (width - filled)
    return f"[{bar}] {done}/{total}"


def cmd_status() -> None:
    """Show per-track compilation progress."""
    from wiki.state import load_progress

    progress = load_progress()
    articles = progress["articles"]

    # Collect per-track stats
    core_tracks = [t for t in ALL_TRACKS if t in ("a1", "a2", "b1", "b2", "c1", "c2")]
    seminar_tracks = [t for t in ALL_TRACKS if t not in core_tracks]

    total_compiled = 0
    total_available = 0
    total_words = 0

    def _track_stats(track: str) -> tuple[int, int, int]:
        """Return (compiled, total, words) for a track."""
        disc_dir = CURRICULUM_DIR / track / "discovery"
        if not disc_dir.exists():
            return 0, 0, 0
        slugs = sorted(f.stem for f in disc_dir.glob("*.yaml"))
        if not slugs:
            return 0, 0, 0
        compiled = 0
        words = 0
        for slug in slugs:
            domain = _get_domain(track, slug)
            key = f"{domain}/{slug}"
            entry = articles.get(key)
            if entry and entry.get("status") == "compiled":
                compiled += 1
                words += entry.get("word_count", 0)
        return compiled, len(slugs), words

    print("\n📊 Wiki Compilation Status")
    print(f"{'═' * 56}")

    # Core levels
    print("\n  Core levels")
    print(f"  {'─' * 52}")
    for track in core_tracks:
        compiled, total, words = _track_stats(track)
        total_compiled += compiled
        total_available += total
        total_words += words
        if total == 0:
            continue
        bar = _progress_bar(compiled, total)
        pct = f"{100 * compiled // total}%" if total else "—"
        words_str = f"{words:>8,}w" if words else ""
        label = f"  {track.upper():<6}"
        if compiled == total:
            print(f"  {label} {bar}  ✅ {pct:>4} {words_str}")
        elif compiled > 0:
            print(f"  {label} {bar}  🔶 {pct:>4} {words_str}")
        else:
            print(f"  {label} {bar}       {words_str}")

    # Seminar tracks
    print("\n  Seminar tracks")
    print(f"  {'─' * 52}")
    for track in seminar_tracks:
        compiled, total, words = _track_stats(track)
        total_compiled += compiled
        total_available += total
        total_words += words
        if total == 0:
            continue
        bar = _progress_bar(compiled, total)
        pct = f"{100 * compiled // total}%" if total else "—"
        words_str = f"{words:>8,}w" if words else ""
        label = f"  {track:<12}"
        if compiled == total:
            print(f"  {label} {bar}  ✅ {pct:>4} {words_str}")
        elif compiled > 0:
            print(f"  {label} {bar}  🔶 {pct:>4} {words_str}")
        else:
            print(f"  {label} {bar}       {words_str}")

    # Totals
    print(f"\n{'═' * 56}")
    bar = _progress_bar(total_compiled, total_available)
    pct = f"{100 * total_compiled // total_available}%" if total_available else "—"
    print(f"  Total    {bar}  {pct:>4}  {total_words:,} words")
    lit_count = len(list_literary_sources())
    print(f"  Sources  {lit_count} literary JSONL files")


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
                    dry_run: bool = False, review: bool = False,
                    dim_review: bool = False) -> bool:
    """Compile a single wiki article from a discovery file.

    ``dim_review``: run the Phase-2 dimensional review orchestrator after
    compile, in SHADOW MODE (logs findings to ``wiki/.reviews/``; never
    blocks). Independent of the legacy single-call ``review``. Safe to
    pass both during canary rollout (§8 Phase 2). See
    ``docs/design/dimensional-review.md``.
    """
    from wiki.state import is_compiled

    domain = _get_domain(track, slug)
    article_key = f"{domain}/{slug}"
    if not force and not dry_run and _compiled_article_is_ready(track, slug):
        print(f"  ⏭️  Already compiled: {article_key}")
        return True

    print(f"\n🔨 Compiling: {track}/{slug}")

    # Gather sources — can stall on cloud-backed or slow filesystem paths.
    # Codex review 2026-04-21 flagged this as the #1 silent-hang suspect.
    t_stage = time.monotonic()
    print(f"  📂 Gathering discovery sources... ({_ts()})", flush=True)
    sources_info = gather_discovery_sources(track, slug)
    print(f"    ✓ gather_discovery_sources in {time.monotonic() - t_stage:.1f}s", flush=True)
    if "error" in sources_info:
        print(f"  ❌ {sources_info['error']}")
        return False

    # Collect and enrich source chunks — dense retrieval + tokenizer encode,
    # can take 10–60s on a cold cache.
    t_stage = time.monotonic()
    print("  🔎 Enriching sources (dense retrieval + encoding)...", flush=True)
    all_chunks = enrich_sources(track, slug, sources_info)
    print(f"    ✓ enrich_sources → {len(all_chunks)} chunks in {time.monotonic() - t_stage:.1f}s", flush=True)

    # Build a human-readable topic from discovery keywords (Ukrainian) or slug (fallback)
    topic = _slug_to_topic(slug, track, sources_info)

    t_stage = time.monotonic()
    result = compile_article(
        topic=topic,
        slug=slug,
        domain=domain,
        sources=all_chunks,
        track=track,
        force=force or is_compiled(article_key),
        dry_run=dry_run,
    )
    print(f"    ✓ compile_article in {time.monotonic() - t_stage:.1f}s", flush=True)

    if result:
        if not dry_run:
            t_stage = time.monotonic()
            print("  📑 Updating index + logging event...", flush=True)
            update_index()
            word_count = len(result.read_text("utf-8").split()) if result.exists() else 0
            log_event(track, slug, "compile", words=word_count, sources=len(all_chunks))
            print(f"    ✓ post-write I/O in {time.monotonic() - t_stage:.1f}s ({word_count} words)", flush=True)
        if review and not dry_run:
            print("  📋 Review enabled — running legacy single-call review...", flush=True)
            t_stage = time.monotonic()
            _review_article(result, track, slug)
            print(f"    ✓ review in {time.monotonic() - t_stage:.1f}s", flush=True)
        if dim_review and not dry_run:
            print("  🔬 Dim-review enabled — running 4-dim shadow-mode review...", flush=True)
            t_stage = time.monotonic()
            _dim_review_article(result, track, slug)
            print(f"    ✓ dim-review in {time.monotonic() - t_stage:.1f}s", flush=True)
        return True
    return dry_run  # dry_run returns None but isn't a failure


def _compiled_article_is_ready(track: str, slug: str) -> bool:
    """Return True when an article is fully compiled and safe to skip.

    "Compiled" here means more than a progress-db row: the markdown must
    exist, and if the article cites sources then its sibling
    ``.sources.yaml`` must exist and validate cleanly.
    """
    from wiki.state import is_compiled

    domain = _get_domain(track, slug)
    article_key = f"{domain}/{slug}"
    if not is_compiled(article_key):
        return False

    article_path = WIKI_DIR / domain / f"{slug}.md"
    try:
        article_text = article_path.read_text(encoding="utf-8")
    except OSError:
        return False

    registry_path = registry_path_for(article_path)
    citation_ids = extract_short_citation_ids(article_text)
    if not registry_path.exists():
        return not citation_ids

    try:
        registry = load_sources_registry(registry_path)
    except Exception:
        return False

    return not validate_sources_registry(article_text, registry)


def _dim_review_article(article_path: Path, track: str, slug: str) -> None:
    """Phase-2 dimensional review, shadow mode. See `scripts/wiki/review.py`.

    Runs the 4 LLM dim reviewers + deterministic fix-merger in shadow
    mode — the article file on disk is NOT modified by review, and no
    non-zero exit is raised even if dims fail. The report lands in
    ``wiki/.reviews/<domain>/<slug>.json`` for later calibration.

    Failures here (agent unavailable, rate-limited, prompt errors) are
    logged but do NOT break the compile pipeline — this is canary
    rollout (§8 Phase 2), not a hard gate.
    """
    import traceback as _tb

    from wiki.review import review_article, write_report

    try:
        report, _ = review_article(article_path, shadow_mode=True)
        out = write_report(report, article_path)
        print(
            f"  🔬 Dim-review: {report.final_verdict} "
            f"(failing: {report.failing_dims or 'none'}) → {out.name}"
        )
        log_event(
            track, slug, "dim_review",
            verdict=report.final_verdict,
            failing_dims=report.failing_dims,
            rounds=len(report.rounds),
            report=str(out),
            shadow=True,
        )
    except Exception as exc:  # defensive: shadow mode must never block
        print(f"  ⚠️  Dim-review failed (shadow mode — non-fatal): {type(exc).__name__}: {exc}")
        log_event(
            track, slug, "dim_review_error",
            error=f"{type(exc).__name__}: {exc}",
            traceback=_tb.format_exc(),
            shadow=True,
        )


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
    """Build a review prompt with the CURRENT article text.

    Strips the `<!-- wiki-meta ... -->` block before sending — reviewer should
    only score prose content, not machine-readable metadata (slug, domain,
    tracks, source filenames). Otherwise Gemini wastes attention on metadata
    and may flag legitimate source-filename strings as low-quality prose.
    """
    article_text = strip_meta(article_text)
    sources_registry = ""
    registry_path = registry_path_for(WIKI_DIR / _get_domain(track, slug) / f"{slug}.md")
    if registry_path.exists():
        sources_registry = f"\n\n## Sources registry\n\n{registry_path.read_text(encoding='utf-8').strip()}"
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
        f"## Article to review\n\n{article_text}{sources_registry}"
    )


def _extract_review_summary(review_text: str) -> str:
    """Extract a short human-readable summary from the first scored review."""
    import re

    score_line = re.compile(
        r"^\s*(?:\d+\.\s*)?\*{0,2}"
        r"(?:Factual|Language|Decolonization|Completeness|Actionable)"
        r"\*{0,2}\s*:\s*\d+(?:\.\d+)?\s*/\s*10\s*[—-]\s*(.+?)\s*$",
        re.IGNORECASE,
    )

    for line in review_text.splitlines():
        match = score_line.match(line.strip())
        if match:
            return " ".join(match.group(1).split())[:300]

    for line in review_text.splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith(("<fixes>", "</fixes>", "```")):
            return " ".join(stripped.split())[:300]

    return "No summary extracted from review."


def _send_review(track: str, slug: str, review_prompt: str,
                 round_label: str, project_root: str) -> str | None:
    """Send a review prompt to Gemini via agent bridge. Returns Gemini's response body.

    Uses --stdout-only so Gemini's actual response reaches stdout. Without this
    flag, ask-gemini only prints send confirmations ("✅ Message sent (ID: N)"),
    and the real response stays in the bridge message store — the parser then
    sees only the confirmation and defaults every dimension to 0.0.
    """
    import subprocess

    try:
        result = subprocess.run(
            [
                ".venv/bin/python", "scripts/ai_agent_bridge/__main__.py",
                "ask-gemini", "-",  # Read prompt from stdin (avoids arg length limits)
                "--task-id", f"wiki-review-{track}-{slug}-{round_label}",
                "--model", "gemini-3.1-pro-preview",
                "--stdout-only",  # Route Gemini's response body to subprocess stdout
            ],
            input=review_prompt,
            capture_output=True, text=True, timeout=900,
            cwd=project_root,
        )
    except Exception as e:
        print(f"  ⚠️  Review error: {e}")
        return None

    if result.returncode != 0:
        print(f"  ⚠️  Review failed: {result.stderr[:200]}")
        return None

    return result.stdout


def _review_article(article_path: Path, track: str, slug: str) -> None:
    """Review a wiki article with a single scoring-only pass."""
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

    # Skip if a PASSING final review already exists (use --force to re-review).
    # Failed reviews (score < 9) are retried on next run.
    final_review = review_dir / f"{slug}-review-final.md"
    if final_review.exists() and final_review.stat().st_size > 100:
        print(f"  ⏭️  Already reviewed (passed): {track}/{slug}")
        return

    project_root = str(Path(__file__).resolve().parents[2])

    article_text = article_path.read_text("utf-8")
    review_prompt = _build_review_prompt(
        article_text, article_type, track, slug, "r1",
    )
    review_text = _send_review(
        track, slug, review_prompt, "r1", project_root,
    )
    if not review_text:
        return

    review_path = review_dir / f"{slug}-review-r1.md"
    review_path.write_text(review_text, "utf-8")
    (review_dir / f"{slug}-review.md").write_text(review_text, "utf-8")

    scores = _parse_review_scores(review_text)
    score = scores["overall"]
    dim_summary = " | ".join(
        f"{k[:4]}:{v}" for k, v in scores.items() if k != "overall"
    )
    print(f"  📋 Round 1: {score}/10 [{dim_summary}]")
    log_event(track, slug, "review_round", round=1,
              score=score, **{k: v for k, v in scores.items() if k != "overall"})

    # Pass criteria: every individual dimension ≥ 8.0 AND overall ≥ 8.0.
    # The per-dimension floor catches the "one bad dimension hidden by a
    # strong total" failure mode (Codex's A1 macro-report finding).
    # Overall ≥ 8.0 is a lower bound — if every dim is ≥ 8.0 the overall
    # is always ≥ 8.0 by construction, so the overall gate mostly guards
    # against parse failures where the reviewer reports a sub-8 overall
    # while emitting inflated dim scores. Matches the project's documented
    # 8.0 minimum pass (docs/.../non-negotiable-rules.md §2).
    DIMENSION_FLOOR = 8.0
    OVERALL_PASS = 8.0
    DIMENSIONS = ("factual", "language", "decolonization", "completeness", "actionable")
    failing_dims = [d for d in DIMENSIONS if scores.get(d, 0) < DIMENSION_FLOOR]
    overall_ok = score >= OVERALL_PASS

    if overall_ok and not failing_dims:
        log_event(track, slug, "review_pass", score=score, rounds=1)
        print(f"  ✅ Review PASSED ({score}/10)")
        (review_dir / f"{slug}-review-final.md").write_text(review_text, "utf-8")
        return

    # Build failure reason for logs + user visibility.
    fail_reasons = []
    if not overall_ok:
        fail_reasons.append(f"overall {score} < {OVERALL_PASS}")
    for d in failing_dims:
        fail_reasons.append(f"{d} {scores.get(d, 0)} < {DIMENSION_FLOOR}")
    fail_reason = "; ".join(fail_reasons)

    review_summary = _extract_review_summary(review_text)
    force_cmd = (
        f".venv/bin/python scripts/wiki/compile.py --track {track} "
        f"--slug {slug} --force"
    )
    log_event(
        track, slug, "review_fail", score=score, rounds=1,
        article_path=str(article_path), review_summary=review_summary,
        rerun_force_cmd=force_cmd, fail_reason=fail_reason,
        failing_dimensions=failing_dims,
    )
    print(f"  ❌ Review failed: {fail_reason}")
    print(f"     path: {article_path}")
    print(f"     final score: {score}/10")
    print(f"     first review summary: {review_summary}")
    print(f"     rerun: {force_cmd}")


def cmd_review_existing(track: str, *, slug: str | None = None,
                        limit: int | None = None) -> None:
    """Review already-compiled wiki articles without recompiling."""
    articles = _existing_article_paths(track, slug=slug)

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
                    review: bool = False, dim_review: bool = False) -> None:
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
    if dim_review:
        print("  🔬 Dimensional review enabled (shadow mode — never blocks)")
    print(f"  🕐 Batch started at {_ts()}")
    print(f"{'═' * 60}")

    success = 0
    failed = 0
    skipped = 0
    batch_start = time.time()

    from wiki.state import is_compiled

    for i, slug in enumerate(slugs, 1):
        slug_start = time.time()
        print(f"\n[{i}/{len(slugs)}] {slug}  ({_ts()})")
        if not force and not dry_run and _compiled_article_is_ready(track, slug):
            domain = _get_domain(track, slug)
            skipped += 1
            elapsed = time.time() - slug_start
            print(f"  ⏭️  Already compiled: {domain}/{slug}")
            print(f"  ⏭️  Skipped (already compiled) in {elapsed:.1f}s")
            continue
        try:
            result = cmd_compile_one(
                track, slug,
                force=force, dry_run=dry_run,
                review=review, dim_review=dim_review,
            )
        except KeyboardInterrupt:
            # Explicit interrupt — stop the whole batch but leave state clean
            print(f"\n⚠️  Interrupted by user at [{i}/{len(slugs)}] {slug}")
            print(f"  Progress so far: ✅ {success}  ⏭️  {skipped}  ❌ {failed}")
            raise
        except Exception:
            # Catch-all so one broken slug doesn't kill the whole batch.
            # Without this, an unhandled exception in any per-slug step
            # silently terminates the outer loop and the user sees "no more
            # output" with no indication of what broke.
            elapsed = time.time() - slug_start
            print(f"  💥 Unhandled exception after {elapsed:.1f}s compiling {slug}:")
            traceback.print_exc()
            print("  → Treating as FAILED, continuing to next slug")
            failed += 1
            continue

        elapsed = time.time() - slug_start
        if result:
            success += 1
            print(f"  ✅ Done in {elapsed:.1f}s")
        else:
            domain = _get_domain(track, slug)
            if is_compiled(f"{domain}/{slug}"):
                skipped += 1
                print(f"  ⏭️  Skipped (already compiled) in {elapsed:.1f}s")
            else:
                failed += 1
                print(f"  ❌ Failed after {elapsed:.1f}s")

    total_elapsed = time.time() - batch_start
    print(f"\n{'═' * 60}")
    print(f"✅ Compiled: {success} | ⏭️  Skipped: {skipped} | ❌ Failed: {failed}")
    print(f"  🕐 Batch finished at {_ts()} (total {total_elapsed:.0f}s)")


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


def _existing_article_paths(track: str, *, slug: str | None = None) -> list[Path]:
    """Return compiled article paths owned by one track."""
    from wiki.config import WIKI_DIR

    seen: set[Path] = set()
    articles = []
    slugs = [slug] if slug else list_discovery_slugs_readonly(track)
    for article_slug in slugs:
        article_path = WIKI_DIR / _get_domain(track, article_slug) / f"{article_slug}.md"
        if not article_path.exists() or article_path in seen:
            continue
        seen.add(article_path)
        articles.append(article_path)
    return sorted(articles)


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
                        help="Review articles after compilation (legacy single-call)")
    parser.add_argument("--review-only", action="store_true",
                        help="Review existing articles without recompiling")
    parser.add_argument("--dim-review", action="store_true",
                        help="Run Phase-2 dimensional review in SHADOW MODE "
                             "after compile (logs findings, never blocks). "
                             "See docs/design/dimensional-review.md.")

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
            review=args.review, dim_review=args.dim_review,
        )
        sys.exit(0 if success else 1)

    if args.compile_all:
        cmd_compile_all(
            args.track,
            limit=args.limit, force=args.force, dry_run=args.dry_run,
            review=args.review, dim_review=args.dim_review,
        )
        return

    parser.error("Specify --slug, --all, or --list")


if __name__ == "__main__":
    main()
