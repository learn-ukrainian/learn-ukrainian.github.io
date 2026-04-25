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

from wiki.compiler import WRITER_CHOICES, compile_article, update_index
from wiki.config import ALL_TRACKS, CURRICULUM_DIR, TRACK_DOMAINS, WIKI_DIR
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
                    writer: str = "gemini") -> bool:
    """Compile a single wiki article from a discovery file.

    ``review``: run the per-dim review orchestrator (independent model
    calls per dim, strict persona, MIN aggregation) after compile. The
    PASS floor is :data:`scripts.common.thresholds.REVIEW_PASS_FLOOR` —
    a single dim below the floor fails the whole review with the
    failing dim named in the report.
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
        writer=writer,
    )
    print(f"    ✓ compile_article in {time.monotonic() - t_stage:.1f}s", flush=True)

    if result:
        if not dry_run:
            # Mechanical discipline pass — runs BEFORE index update so that
            # invented citations and forbidden canonical-anchor forms never
            # reach the index or the reader. Strip-and-flag pattern:
            # citations > source_count are stripped (they're just noise);
            # anchor hits get a <!-- VERIFY --> marker inserted so reviewer
            # and downstream audits see them. See scripts/wiki/discipline.py.
            t_stage = time.monotonic()
            print("  🔒 Running mechanical discipline checks...", flush=True)
            _run_discipline_checks_and_repair(
                article_path=result,
                track=track,
                slug=slug,
                source_count=len(all_chunks),
            )
            print(f"    ✓ discipline in {time.monotonic() - t_stage:.1f}s", flush=True)

            t_stage = time.monotonic()
            print("  📑 Updating index + logging event...", flush=True)
            update_index()
            word_count = len(result.read_text("utf-8").split()) if result.exists() else 0
            log_event(track, slug, "compile", words=word_count, sources=len(all_chunks))
            print(f"    ✓ post-write I/O in {time.monotonic() - t_stage:.1f}s ({word_count} words)", flush=True)
        if review and not dry_run:
            print("  📋 Review enabled — running per-dim + MIN review...", flush=True)
            t_stage = time.monotonic()
            _review_article(result, track, slug)
            print(f"    ✓ review in {time.monotonic() - t_stage:.1f}s", flush=True)
        return True
    return dry_run  # dry_run returns None but isn't a failure


def _run_discipline_checks_and_repair(
    *, article_path: Path, track: str, slug: str, source_count: int
) -> None:
    """Post-compile mechanical-discipline pass.

    Checks two things without spending an LLM call:

    1. Invented citations — `[SX]` where X > source_count. These get
       stripped from the article body. They cannot resolve to any real
       corpus chunk (see #1434 / #1435 — a bare-ID leak at the compiler
       level was one layer; this catches the writer-level hallucination
       that *produces* the bare IDs in the first place).

    2. Canonical anchors — forbidden decolonization-harmful forms like
       «блакитно-жовтий» for the Ukrainian flag. These get a trailing
       `<!-- VERIFY: ... -->` marker; we do NOT auto-strip because the
       surrounding sentence may collapse. Reviewer + human-audit will
       see the marker.

    Emits a structured `discipline_result` log event with the count of
    violations and stripped IDs, so build-logs can surface the issue
    even if no human is watching live.

    Non-fatal. If the registry is missing or regex fails, logs the
    error and returns — the compile proceeds.
    """
    from wiki.discipline import (
        flag_anchor_violations,
        run_discipline_checks,
        strip_invented_citations,
    )

    try:
        original = article_path.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"    ⚠️  Could not read {article_path} for discipline check: {exc}")
        return

    try:
        report = run_discipline_checks(original, source_count)
    except Exception as exc:
        print(f"    ⚠️  Discipline check failed (non-fatal): {exc}")
        log_event(
            track, slug, "discipline_error",
            error=f"{type(exc).__name__}: {exc}",
        )
        return

    if report.clean:
        print("    ✓ discipline clean (0 citation, 0 anchor violations)")
        log_event(track, slug, "discipline_pass", sources=source_count)
        return

    # Repair pass.
    repaired = original
    stripped_ids: list[str] = []
    if report.citations:
        repaired, stripped_ids = strip_invented_citations(repaired, source_count)
        unique_stripped = sorted(set(stripped_ids))
        print(
            f"    🧹 Stripped {len(stripped_ids)} invented citation(s): "
            f"{', '.join(unique_stripped)}"
        )
        for violation in report.citations[:3]:  # cap log noise
            print(f"       · [{violation.cited_id}] context: «{violation.context}»")

    if report.anchors:
        repaired = flag_anchor_violations(repaired, report.anchors)
        print(
            f"    🚩 Flagged {len(report.anchors)} canonical-anchor violation(s) "
            "with <!-- VERIFY --> markers"
        )
        for violation in report.anchors[:3]:
            print(
                f"       · {violation.anchor_id} — «{violation.matched_text}» "
                f"(expected «{violation.correct_form}»)"
            )

    if repaired != original:
        article_path.write_text(repaired, encoding="utf-8")

    log_event(
        track, slug, "discipline_repair",
        citation_violations=len(report.citations),
        anchor_violations=len(report.anchors),
        stripped_ids=stripped_ids,
        sources=source_count,
    )


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


def _review_article(article_path: Path, track: str, slug: str) -> None:
    """Run the per-dim + MIN review orchestrator on a compiled wiki article.

    Replaces the legacy weighted-average single-call review. Each wiki
    dim (source_grounding, factual_accuracy, ukrainian_perspective,
    register) runs as an INDEPENDENT model call with the strict persona;
    the aggregator takes ``min(dim_scores)`` (see
    ``scripts.wiki.review.aggregate_min``) and fails the review if the
    driving dim is below :data:`scripts.common.thresholds.REVIEW_PASS_FLOOR`.

    The orchestrator applies surgical fixes round-by-round to an
    in-memory copy of the article; when the final verdict is ``PASS``
    and the text changed, the updated text is written back to disk.
    Failures here are non-fatal to the outer compile pipeline: the
    review report is persisted to ``wiki/.reviews/...`` and a
    ``review_fail`` event is logged so failing wikis are visible in
    downstream audits.
    """
    import traceback as _tb

    from wiki.review import review_article, write_report

    print(f"  🔍 Reviewing: {track}/{slug}")

    if not article_path.exists() or article_path.stat().st_size < 100:
        print("  ⚠️  Article missing or too short to review")
        return

    try:
        report, final_text = review_article(article_path, shadow_mode=False)
    except Exception as exc:
        print(f"  ⚠️  Review orchestrator failed: {type(exc).__name__}: {exc}")
        log_event(
            track, slug, "review_error",
            error=f"{type(exc).__name__}: {exc}",
            traceback=_tb.format_exc(),
        )
        return

    out_path = write_report(report, article_path)
    min_score = report.min_score
    failing_dim = report.failing_dim
    verdict = report.final_verdict

    dim_summary = " | ".join(
        f"{dim}:{dr.score}" for dim, dr in report.rounds[-1].dim_results.items()
    )
    print(f"  📋 MIN {min_score}/10 [{dim_summary}]")
    for round_result in report.rounds:
        round_scores = {
            dim: float(dr.score) for dim, dr in round_result.dim_results.items()
        }
        log_event(
            track, slug, "review_round",
            round=round_result.round_num,
            score=min(round_scores.values()) if round_scores else 0.0,
            **round_scores,
        )

    if verdict == "PASS":
        if not report.shadow_mode and final_text and final_text != article_path.read_text("utf-8"):
            article_path.write_text(final_text, encoding="utf-8")
        log_event(
            track, slug, "review_pass",
            score=min_score,
            rounds=len(report.rounds),
            report=str(out_path),
        )
        print(f"  ✅ Review PASSED (MIN {min_score}/10)")
        return

    force_cmd = (
        f".venv/bin/python scripts/wiki/compile.py --track {track} "
        f"--slug {slug} --force --review"
    )
    log_event(
        track, slug, "review_fail",
        score=min_score,
        rounds=len(report.rounds),
        article_path=str(article_path),
        failing_dim=failing_dim,
        failing_dims=report.failing_dims,
        verdict=verdict,
        rerun_force_cmd=force_cmd,
        report=str(out_path),
    )
    print(f"  ❌ Review failed: {verdict} — MIN {min_score}/10 driven by {failing_dim}")
    print(f"     failing dims: {report.failing_dims}")
    print(f"     report: {out_path}")
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
                    review: bool = False, writer: str = "gemini") -> None:
    """Compile all articles for a track."""
    slugs = list_discovery_slugs(track)
    if not slugs:
        print(f"No discovery files for track '{track}'")
        return

    if limit:
        slugs = slugs[:limit]

    print(f"\n🔨 Compiling {len(slugs)} articles for {track.upper()}")
    if review:
        print("  📋 Per-dim + MIN review enabled — each article gated after compile")
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
                review=review, writer=writer,
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
            "sources and RAG data using Gemini.\n"
            "Use it for wiki article compile/review/index workflows; do not use it "
            "for module generation itself.\n\n"
            "Prompt per track type:\n"
            "  A1:         Pedagogical briefs (methodology, phonetics, vocab boundaries)\n"
            "  A2-B2:      Grammar briefs (paradigms, frequency, L2 errors)\n"
            "  C1-C2:      Academic briefs (scholarly register, stylistics)\n"
            "  Seminars:   Knowledge articles (primary sources, historiography)"
        ),
        epilog=(
            "Examples:\n"
            "  .venv/bin/python scripts/wiki/compile.py --track a2 --slug genitive-intro --dry-run\n"
            "  .venv/bin/python scripts/wiki/compile.py --track a2 --all --limit 5 --review\n"
            "  .venv/bin/python scripts/wiki/compile.py --track folk --review-only\n\n"
            "Outputs:\n"
            "  Writes wiki/<domain>/<slug>.md plus sibling .sources.yaml registries,\n"
            "  updates wiki/index.md, and appends build events under wiki/.state/.\n\n"
            "Exit codes:\n"
            "  0 on success; 1 on invalid CLI usage or single-slug compile failure.\n\n"
            "Related:\n"
            "  Prompts: scripts/wiki/prompts/\n"
            "  Design: docs/design/dimensional-review.md\n"
            "  Issue: #1379\n"
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
    parser.add_argument("--slug", help="Specific module slug to compile, e.g. genitive-intro")
    parser.add_argument("--all", action="store_true", dest="compile_all",
                        help="Compile every discovery slug in the selected --track")
    parser.add_argument("--list", action="store_true",
                        help="List available module slugs for the selected --track")

    # Options
    parser.add_argument("--limit", type=int,
                        help="Max articles to compile with --all, e.g. --limit 20")
    parser.add_argument("--force", action="store_true",
                        help="Recompile even if article + valid sidecar already exist")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print the assembled prompt without calling the writer")
    parser.add_argument(
        "--writer",
        choices=WRITER_CHOICES,
        default="gemini",
        help=(
            "Writer agent to use for compilation. Default: gemini (subscription, "
            "unlimited budget). Use 'claude' for cultural/decolonization-sensitive "
            "tracks (literature, figures, periods, historiography, folk). Use "
            "'gpt-5.5' for mechanical/structural content (grammar, academic, "
            "pedagogy)."
        ),
    )
    parser.add_argument("--review", action="store_true",
                        help="Run per-dim + MIN review after compile "
                             "(strict persona, independent model calls, "
                             "aggregated via min(dim_scores)).")
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
            review=args.review, writer=args.writer,
        )
        sys.exit(0 if success else 1)

    if args.compile_all:
        cmd_compile_all(
            args.track,
            limit=args.limit, force=args.force, dry_run=args.dry_run,
            review=args.review, writer=args.writer,
        )
        return

    parser.error("Specify --slug, --all, or --list")


if __name__ == "__main__":
    main()
