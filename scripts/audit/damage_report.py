"""Damage report: classify every module's audit state into actionable buckets.

Phase 1 of the "take Gemini off the critical path" plan. This tool is 100%
read-only, offline, and LLM-free. It walks the curriculum, runs the current
deterministic audit against every module, and classifies each into one of:

    CLEAN        — audit passes, every gate is strictly 'pass', no violations.
    MECHANICAL   — violations exist, but every one of them is the kind a
                   deterministic fixer script could repair without calling
                   an LLM (e.g. YAML schema type errors, inline-gloss
                   overflow, phase/translation formatting).
    LLM_REGEN    — at least one violation truly needs an LLM rewrite
                   (content-level issues: low naturalness, robotic prose,
                   grammar violations inside Ukrainian prose, missing UK
                   paragraphs in a phase that requires them, etc.).
    UNVERIFIED   — audit overall says 'pass' BUT at least one gate is
                   'info'/'pending'/'deferred' — meaning the check never
                   actually ran (most commonly naturalness, which depends
                   on a completed review). Treated as neither clean nor
                   broken; needs a review pass to promote to CLEAN.

Output:
    1. Stdout table — one row per module
    2. Markdown report — `docs/damage-report-{level}-{timestamp}.md`
    3. CSV report    — `docs/damage-report-{level}-{timestamp}.csv`

Usage:

    .venv/bin/python scripts/audit/damage_report.py a1
    .venv/bin/python scripts/audit/damage_report.py a2
    .venv/bin/python scripts/audit/damage_report.py a1 a2
    .venv/bin/python scripts/audit/damage_report.py a1 --fresh   # force re-audit
    .venv/bin/python scripts/audit/damage_report.py a1 --limit 5

Design choices:

1. By default we RE-RUN the audit on each module before reading its status,
   so the report always reflects the current audit engine (the salad
   detector wired on 2026-04-10 made all pre-existing status.json files
   stale). Pass `--no-fresh` to read the existing status files only.

2. The "mechanical" classification is conservative: we only mark a module
   mechanical if EVERY violation in it has a known deterministic fixer.
   One content-level violation bumps the whole module to LLM_REGEN.

3. We never modify any file. Re-running the audit is a pure function
   from (content, audit_engine) → report + status. The audit engine
   writes its own status.json as a side effect, but that's the
   existing behavior — not something this tool introduces.

4. The tool prints progress as it goes (one line per module) so a
   long walk over 140 modules is not a silent hang.
"""
from __future__ import annotations

import argparse
import contextlib
import csv
import io
import json
import re
import sys
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

# Repo layout: this file is scripts/audit/damage_report.py
_SCRIPTS_DIR = Path(__file__).resolve().parent.parent
_REPO_ROOT = _SCRIPTS_DIR.parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from audit.core import audit_module
from batch.batch_gemini_config import get_module_index

CURRICULUM_ROOT = _REPO_ROOT / "curriculum" / "l2-uk-en"


# ---------------------------------------------------------------------------
# Violation classification
# ---------------------------------------------------------------------------

# Informational tags — NOT violations, filtered out before classification.
# `[INFO]` is used by the audit engine for advisory notes (e.g. "dative case
# used at A1 but formally taught at A2") which flag nothing broken; they're
# just breadcrumbs for the writer.
INFORMATIONAL_TAGS: frozenset[str] = frozenset({
    "INFO",
    "NOTE",
    "HINT",
})

# Violations a deterministic fixer can repair without calling an LLM.
# Every time we add a new fixer in Phase 2, add its violation tag here.
MECHANICAL_VIOLATIONS: frozenset[str] = frozenset({
    "YAML_SCHEMA_VIOLATION",
    "SALAD_EXCESSIVE_INLINE_GLOSSES",
    "SALAD_MIXED_PARAGRAPH",
    "SALAD_MIXED_SENTENCE",
    "SALAD_TOO_MANY_TRANSLATIONS",
    "SALAD_PAIRED_TRANSLATION",
    "PHASE_UK_PARAGRAPH_TOO_EARLY",
    "PHASE_TRANSLATIONS_MISSING",
    "PHASE_TRANSLATIONS_LOW",
    "PHASE_TRANSLATIONS_EXCESS",
    "INJECT_ACTIVITY_FORMAT",
    "HINT_IN_INSTRUCTION",
    "HINT_IN_ACTIVITY",             # same idea, different tag
    "ERROR_CORRECTION_HINT",
    "MALFORMED_CLOZE",
    "CLOZE_SYNTAX",
    "ERROR_CORRECTION",
    # Russicism replacement: we already have plan_autofix.fix_russianisms_in_plan.
    # The content-level fixer just needs the same word map applied to the
    # prose, which is a dictionary-replace job.
    "RUSSICISM_DETECTED",
    # Level-restricted activity types: the fixer swaps the disallowed type
    # for an allowed one from the same bucket, or drops the activity if no
    # swap is possible. No LLM call needed.
    "LEVEL_RESTRICTION",
})

# Violations that need an LLM rewrite. A single one of these on a module
# promotes it from MECHANICAL to LLM_REGEN.
LLM_VIOLATIONS: frozenset[str] = frozenset({
    "COMPLEXITY",               # too few items per activity
    "COMPLEXITY_WORD_COUNT",    # section / prose word-count out of target
    "GRAMMAR",                  # subordinate clause markers — prose rewrite
    "PHASE_NO_UK_PARAGRAPHS",   # writer must actually produce UK content
    "METALANGUAGE",             # meta-commentary in content prose
    "ROBOTIC_STRUCTURE",        # repetitive / formulaic prose
    "ROBOTIC_PROSE",
    "INLINE_ENGLISH_IN_PROSE",  # inline English where UK is required
    "TONE",
    "NATURALNESS",
    "LOW_ENGAGEMENT",
    "FACTUAL",
    "MARK_WORDS",
    "INVALID_TYPE",             # activity type not allowed for this level
    "FORBIDDEN_TYPE",
    "CONTENT_REDUNDANCY",       # duplicated sections — needs prose rewrite
    "CASE_GOV",                 # case governance — morphology rewrite
})


def classify_violation(tag: str) -> str:
    """Return 'mechanical', 'llm', 'informational', or 'unknown' for a tag."""
    if tag in INFORMATIONAL_TAGS:
        return "informational"
    if tag in MECHANICAL_VIOLATIONS:
        return "mechanical"
    if tag in LLM_VIOLATIONS:
        return "llm"
    return "unknown"


# ---------------------------------------------------------------------------
# Per-module damage record
# ---------------------------------------------------------------------------


@dataclass
class ModuleDamage:
    level: str
    num: int
    slug: str
    overall_status: str = "unknown"          # pass | fail | content-complete | unknown
    failed_gates: list[str] = field(default_factory=list)
    unverified_gates: list[str] = field(default_factory=list)
    violations: list[tuple[str, str]] = field(default_factory=list)  # (tag, message)
    review_score: float | None = None
    category: str = "UNKNOWN"                # CLEAN | MECHANICAL | LLM_REGEN | UNVERIFIED
    projected_category: str = "UNKNOWN"      # what `category` becomes after mech heal
    audit_duration_ms: float = 0.0
    notes: str = ""

    @property
    def mechanical_count(self) -> int:
        return sum(1 for tag, _ in self.violations if classify_violation(tag) == "mechanical")

    @property
    def llm_count(self) -> int:
        return sum(1 for tag, _ in self.violations if classify_violation(tag) == "llm")

    @property
    def unknown_violation_count(self) -> int:
        return sum(1 for tag, _ in self.violations if classify_violation(tag) == "unknown")


# ---------------------------------------------------------------------------
# Audit runner
# ---------------------------------------------------------------------------


_VIOLATION_RE = re.compile(r"^- \*\*\[([A-Z_]+)\]\*\* (.+?)$", re.MULTILINE)


def _run_audit_fresh(content_path: Path) -> None:
    """Invoke the audit engine on content_path, suppressing its stdout.

    The audit engine prints a LOT of output. We just want the side effects
    (status.json + audit report markdown files). Silencing stdout here is
    purely cosmetic — progress is still printed by the outer loop.
    """
    # audit_module calls print() and sys.exit() in some paths; wrap both.
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
        try:
            audit_module(str(content_path), skip_activities=False, skip_review=False)
        except SystemExit:
            # Audit sometimes exits on its own when a source file is missing.
            # We catch so our tool keeps walking the rest of the modules.
            pass
        except Exception as exc:
            # Log the exception to stderr but keep going.
            print(f"[damage_report] audit raised on {content_path.name}: "
                  f"{type(exc).__name__}: {exc}", file=sys.stderr)


def _parse_audit_report(report_path: Path) -> list[tuple[str, str]]:
    """Extract (tag, message) tuples from an audit report markdown file."""
    if not report_path.exists():
        return []
    try:
        text = report_path.read_text("utf-8")
    except OSError:
        return []
    # Only look inside the PEDAGOGICAL VIOLATIONS section, which is bounded
    # by a following `## ` heading (or EOF).
    start = text.find("## PEDAGOGICAL VIOLATIONS")
    if start == -1:
        return []
    end = text.find("\n## ", start + len("## PEDAGOGICAL VIOLATIONS"))
    block = text[start:end if end != -1 else len(text)]
    out: list[tuple[str, str]] = []
    for m in _VIOLATION_RE.finditer(block):
        tag = m.group(1).strip()
        msg = m.group(2).strip()
        out.append((tag, msg))
    return out


def _load_review_score(level: str, slug: str) -> float | None:
    """Load the latest saved review score for a module, if any."""
    review_dir = CURRICULUM_ROOT / level / "review"
    primary = review_dir / f"{slug}-review.md"
    candidates = []
    if primary.exists():
        candidates.append(primary)
    if review_dir.exists():
        candidates.extend(sorted(review_dir.glob(f"{slug}-review-r*.md")))
    if not candidates:
        return None
    # Use the newest one. Parse with the same regex as v6_build.
    newest = max(candidates, key=lambda p: p.stat().st_mtime)
    try:
        text = newest.read_text("utf-8")
    except OSError:
        return None
    dimension_weights = {
        1: 0.15, 2: 0.15, 3: 0.15, 4: 0.10, 5: 0.15,
        6: 0.10, 7: 0.05, 8: 0.05, 9: 0.10,
    }
    score_pat = re.compile(r"\|\s*\d+\.\s*[^|]+\|\s*(\d+)/10\s*\|")
    scores = [int(m.group(1)) for m in score_pat.finditer(text)][:len(dimension_weights)]
    if not scores:
        return None
    available = min(len(scores), len(dimension_weights))
    weights = {k: v for k, v in dimension_weights.items() if k <= available}
    wsum = sum(weights.values())
    if wsum == 0:
        return None
    weighted = sum(scores[i] * dimension_weights.get(i + 1, 0) for i in range(available))
    return round(weighted / wsum, 1)


def build_damage(level: str, num: int, slug: str, *, do_fresh: bool) -> ModuleDamage:
    """Build a ModuleDamage record for one module."""
    damage = ModuleDamage(level=level, num=num, slug=slug)

    content_path = CURRICULUM_ROOT / level / f"{slug}.md"
    if not content_path.exists():
        damage.category = "MISSING"
        damage.notes = "content file does not exist"
        return damage

    if do_fresh:
        t0 = time.monotonic()
        _run_audit_fresh(content_path)
        damage.audit_duration_ms = (time.monotonic() - t0) * 1000

    status_path = CURRICULUM_ROOT / level / "status" / f"{slug}.json"
    if not status_path.exists():
        damage.category = "UNKNOWN"
        damage.notes = "no status file after audit"
        return damage

    try:
        status = json.loads(status_path.read_text("utf-8"))
    except Exception as exc:
        damage.category = "UNKNOWN"
        damage.notes = f"status file unreadable: {exc}"
        return damage

    damage.overall_status = status.get("overall", {}).get("status", "unknown")
    gates = status.get("gates") or {}
    for name, g in gates.items():
        if not isinstance(g, dict):
            continue
        gstatus = g.get("status")
        if gstatus == "fail":
            damage.failed_gates.append(name)
        elif gstatus not in ("pass", "deferred"):
            damage.unverified_gates.append(name)

    report_path = CURRICULUM_ROOT / level / "audit" / f"{slug}-audit.md"
    raw_violations = _parse_audit_report(report_path)
    # Filter out informational tags ([INFO], [NOTE], [HINT]) — they're
    # advisory notes, not broken state. They should neither promote the
    # module to broken nor inflate the violation counts.
    damage.violations = [
        (tag, msg) for tag, msg in raw_violations
        if classify_violation(tag) != "informational"
    ]
    damage.review_score = _load_review_score(level, slug)

    # Classification logic.
    if damage.overall_status == "pass" and not damage.failed_gates and not damage.violations:
        if damage.unverified_gates:
            damage.category = "UNVERIFIED"
            damage.projected_category = "UNVERIFIED"
        else:
            damage.category = "CLEAN"
            damage.projected_category = "CLEAN"
        return damage

    # There are violations or failing gates. Decide LLM vs mechanical.
    if damage.violations:
        if damage.llm_count > 0 or damage.unknown_violation_count > 0:
            damage.category = "LLM_REGEN"
        else:
            damage.category = "MECHANICAL"
    elif damage.failed_gates:
        # Gates failed but no parseable violations — treat as LLM to be safe.
        damage.category = "LLM_REGEN"
    else:
        damage.category = "UNVERIFIED"

    # Project what this module would look like AFTER mechanical heal.
    # This is the signal that matters most: it tells us whether the
    # mechanical fixer (Phase 2) alone can get the module to CLEAN, or
    # whether an LLM pass is also required.
    if damage.llm_count == 0 and damage.unknown_violation_count == 0:
        # Only mechanical violations remain — heal clears all of them.
        # But the module can still be blocked by a failing gate that
        # isn't tied to a violation tag (rare); in that case we land on
        # LLM_REGEN after heal too.
        mechanical_fail_only = all(
            g in {"lesson", "activities", "meta"} for g in damage.failed_gates
        )
        if mechanical_fail_only:
            damage.projected_category = "CLEAN"
        else:
            damage.projected_category = "LLM_REGEN"
    else:
        damage.projected_category = "LLM_REGEN"

    return damage


# ---------------------------------------------------------------------------
# Report output
# ---------------------------------------------------------------------------


_CATEGORY_ORDER = ["CLEAN", "UNVERIFIED", "MECHANICAL", "LLM_REGEN", "MISSING", "UNKNOWN"]
_CATEGORY_ICON = {
    "CLEAN":      "✅",
    "UNVERIFIED": "ℹ️",
    "MECHANICAL": "🔧",
    "LLM_REGEN":  "🧠",
    "MISSING":    "⚠️",
    "UNKNOWN":    "❓",
}


def _print_progress(d: ModuleDamage) -> None:
    """One-line progress tick during the walk."""
    icon = _CATEGORY_ICON.get(d.category, "?")
    reason = ""
    if d.violations:
        top = d.violations[0][0]
        reason = f"  {top}"
        if len(d.violations) > 1:
            reason += f" (+{len(d.violations) - 1} more)"
    elif d.unverified_gates:
        reason = f"  unverified: {','.join(d.unverified_gates)}"
    elif d.failed_gates:
        reason = f"  failed: {','.join(d.failed_gates)}"
    print(f"  {icon} {d.level.upper()} M{d.num:02d} {d.slug:<40s} {d.category:<11s}{reason}")


def _render_markdown(damages: list[ModuleDamage]) -> str:
    buckets: dict[str, list[ModuleDamage]] = {k: [] for k in _CATEGORY_ORDER}
    for d in damages:
        buckets.setdefault(d.category, []).append(d)

    lines: list[str] = []
    lines.append(f"# Damage report — {datetime.now(UTC).strftime('%Y-%m-%d %H:%M UTC')}")
    lines.append("")
    levels_seen = sorted({d.level for d in damages})
    lines.append(f"**Levels scanned:** {', '.join(l.upper() for l in levels_seen)}")
    lines.append(f"**Modules scanned:** {len(damages)}")
    lines.append("")

    # Summary table — current state + projected state after mech heal
    lines.append("## Summary")
    lines.append("")
    lines.append("| Category | Current | After mechanical heal |")
    lines.append("|---|---:|---:|")
    total = max(len(damages), 1)
    projected_counts: dict[str, int] = {}
    for d in damages:
        pc = d.projected_category
        projected_counts[pc] = projected_counts.get(pc, 0) + 1
    for cat in _CATEGORY_ORDER:
        n_now = len(buckets.get(cat, []))
        n_proj = projected_counts.get(cat, 0)
        arrow = ""
        if n_now != n_proj:
            arrow = f" ({'+' if n_proj > n_now else ''}{n_proj - n_now})"
        lines.append(f"| {_CATEGORY_ICON[cat]} {cat} | {n_now} ({n_now * 100 // total}%) | {n_proj} ({n_proj * 100 // total}%){arrow} |")
    lines.append("")
    lines.append("_\"After mechanical heal\" = hypothetical state if every mechanical "
                 "violation were fixed by the Phase 2 deterministic fixers, without "
                 "touching the LLM._")
    lines.append("")

    # Per-bucket details
    for cat in _CATEGORY_ORDER:
        items = buckets.get(cat, [])
        if not items:
            continue
        lines.append(f"## {_CATEGORY_ICON[cat]} {cat} ({len(items)})")
        lines.append("")
        if cat == "CLEAN":
            lines.append("Modules fully passing the audit (and review, if available).")
            lines.append("")
            for d in items:
                review = f" · review {d.review_score}/10" if d.review_score is not None else ""
                lines.append(f"- {d.level.upper()} M{d.num:02d} `{d.slug}`{review}")
            lines.append("")
            continue
        if cat == "UNVERIFIED":
            lines.append("Modules whose audit overall is pass but at least one gate "
                         "is in `info`/`pending` state. Most commonly naturalness — "
                         "which only gets scored after a review pass. Running "
                         "`--step review --resume` on these should promote them to CLEAN.")
            lines.append("")
            for d in items:
                lines.append(f"- {d.level.upper()} M{d.num:02d} `{d.slug}` — unverified: {', '.join(d.unverified_gates)}")
            lines.append("")
            continue

        lines.append("| Module | Slug | Gates | Violations | Review |")
        lines.append("|---|---|---|---|---|")
        for d in items:
            gates = ",".join(d.failed_gates) if d.failed_gates else "-"
            vtags: list[str] = []
            for tag, _ in d.violations:
                mark = "" if classify_violation(tag) == "mechanical" else "*"
                vtags.append(f"{tag}{mark}")
            vstr = ", ".join(vtags) if vtags else "-"
            review = f"{d.review_score}/10" if d.review_score is not None else "-"
            lines.append(f"| M{d.num:02d} | `{d.slug}` | {gates} | {vstr} | {review} |")
        lines.append("")
        lines.append("`*` next to a tag = LLM-required violation "
                     "(bumps the module to LLM_REGEN).")
        lines.append("")

    # Violation tally
    lines.append("## Violation tally")
    lines.append("")
    tally: dict[str, int] = {}
    for d in damages:
        for tag, _ in d.violations:
            tally[tag] = tally.get(tag, 0) + 1
    if tally:
        lines.append("| Violation | Count | Fix path |")
        lines.append("|---|---:|---|")
        for tag, n in sorted(tally.items(), key=lambda x: (-x[1], x[0])):
            cls = classify_violation(tag)
            fix = {
                "mechanical": "deterministic fixer (Phase 2)",
                "llm": "LLM rewrite (Phase 4)",
                "unknown": "needs triage",
            }[cls]
            lines.append(f"| `{tag}` | {n} | {fix} |")
    else:
        lines.append("_No violations parsed._")
    lines.append("")

    return "\n".join(lines)


def _render_csv(damages: list[ModuleDamage]) -> str:
    out = io.StringIO()
    w = csv.writer(out)
    w.writerow([
        "level", "num", "slug", "category", "overall_status",
        "failed_gates", "unverified_gates",
        "violation_count", "mechanical_count", "llm_count",
        "review_score", "violations",
    ])
    for d in damages:
        w.writerow([
            d.level, d.num, d.slug, d.category, d.overall_status,
            "|".join(d.failed_gates),
            "|".join(d.unverified_gates),
            len(d.violations),
            d.mechanical_count,
            d.llm_count,
            d.review_score if d.review_score is not None else "",
            "|".join(tag for tag, _ in d.violations),
        ])
    return out.getvalue()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Classify every module's audit state into CLEAN / UNVERIFIED / "
                    "MECHANICAL / LLM_REGEN. Read-only, no LLM calls.",
    )
    parser.add_argument("levels", nargs="+", help="Levels to scan (e.g. a1 a2)")
    parser.add_argument("--no-fresh", action="store_true",
                        help="Skip re-running the audit; read existing status.json only. "
                             "Faster but may show stale results if the audit engine "
                             "has changed since the last run.")
    parser.add_argument("--limit", type=int, default=None,
                        help="Only scan the first N modules per level (for quick smoke tests).")
    parser.add_argument("--out-dir", default="docs",
                        help="Directory for the markdown + CSV reports (default: docs/).")
    args = parser.parse_args()

    do_fresh = not args.no_fresh

    all_damages: list[ModuleDamage] = []
    for level in args.levels:
        try:
            idx = get_module_index(level)
        except ValueError as exc:
            print(f"❌ {exc}", file=sys.stderr)
            return 2
        nums = sorted(idx["num_to_slug"].keys())
        if args.limit is not None:
            nums = nums[: args.limit]

        print(f"\n═══ {level.upper()} — scanning {len(nums)} module(s) "
              f"({'fresh audit' if do_fresh else 'cached status only'}) ═══")
        for n in nums:
            slug = idx["num_to_slug"][n]
            d = build_damage(level, n, slug, do_fresh=do_fresh)
            _print_progress(d)
            all_damages.append(d)

    # Summary — current vs projected (post-mechanical-heal) state
    print("\n═══ Summary ═══")
    by_cat: dict[str, int] = {}
    by_proj: dict[str, int] = {}
    for d in all_damages:
        by_cat[d.category] = by_cat.get(d.category, 0) + 1
        by_proj[d.projected_category] = by_proj.get(d.projected_category, 0) + 1
    print(f"  {'Category':<12s}  current   after mech heal")
    for cat in _CATEGORY_ORDER:
        n_now = by_cat.get(cat, 0)
        n_proj = by_proj.get(cat, 0)
        if n_now or n_proj:
            arrow = ""
            if n_now != n_proj:
                delta = n_proj - n_now
                arrow = f"  ({'+' if delta > 0 else ''}{delta})"
            print(f"  {_CATEGORY_ICON[cat]} {cat:<11s}    {n_now:>3d}     {n_proj:>3d}{arrow}")

    # Bottom line: how many modules DON'T need Gemini at all?
    clean_after = by_proj.get("CLEAN", 0)
    unverified_after = by_proj.get("UNVERIFIED", 0)
    llm_after = by_proj.get("LLM_REGEN", 0)
    total = len(all_damages)
    print()
    print(f"  Bottom line: mechanical heal alone clears "
          f"{clean_after}/{total} modules ({clean_after * 100 // max(total, 1)}%).")
    if unverified_after:
        print(f"  Additional {unverified_after} need only a review pass (no content rewrite).")
    print(f"  {llm_after} module(s) still require an LLM rewrite after mechanical heal.")

    # Write reports
    out_dir = _REPO_ROOT / args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    level_tag = "-".join(args.levels)
    md_path = out_dir / f"damage-report-{level_tag}-{stamp}.md"
    csv_path = out_dir / f"damage-report-{level_tag}-{stamp}.csv"
    md_path.write_text(_render_markdown(all_damages), "utf-8")
    csv_path.write_text(_render_csv(all_damages), "utf-8")
    print(f"\n📄 Markdown report: {md_path.relative_to(_REPO_ROOT)}")
    print(f"📄 CSV report:      {csv_path.relative_to(_REPO_ROOT)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
