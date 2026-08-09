---
name: seminar-content-review
description: Fact-check BUILT seminar content (FOLK, HIST, BIO, ISTORIO, LIT and subtracks, OES, RUTH) against Wikipedia + Literary RAG + heritage dictionaries. Verifies every factual claim, catches ghost facts / ghost sources / confident fabrication, and runs decolonization + russicism checks. For built module CONTENT — not plans (use plan-review-seminar for plans, content-review for core levels).
argument-hint: "<track/slug | path to a content file>"
effort: xhigh
---

# Seminar Content Review: $ARGUMENTS

**Scope: BUILT seminar CONTENT** (FOLK, HIST, BIO, ISTORIO, LIT + subtracks, OES, RUTH). For seminar PLANS use `/plan-review-seminar`; for core-level content use `/content-review`.

**Why this exists (the gap it closes):** seminar quality = **factual accuracy + decolonization + source grounding** — none of which the deterministic linguistic gates (VESUM validity, russicism rate, immersion policy) can measure. A model that *sounds* scholarly can be **confidently fabricating** — and the linguistic gates pass it just the same. This reviewer verifies **every factual claim against real sources** so "sounds authoritative" is never mistaken for "is accurate." (Origin: the 2026-07-04 UK-writing bakeoff ranked a writer #1 for seminars on scholarly *tone* before any fact-check — `audit/2026-07-04-uk-writing-probe/REPORT.md`.)

## Parse arguments

- Path ending in `.md` / `.mdx` / `.txt` → a single content file (review it directly).
- `{track}/{slug}` or a bare `{slug}` → the built module at `curriculum/l2-uk-en/{track}/{slug}/module.md` (+ its `vocabulary.yaml`).
- `{track}` alone → every built module in that track.

**Valid tracks:** folk, hist, bio, istorio, lit, lit-drama, lit-essay, lit-doc, lit-crimea, lit-fantastika, lit-hist-fic, lit-humor, lit-war, lit-youth, oes, ruth.

## Execute

1. **Deterministic backbone FIRST — stdout-only in a read-only review** (cheap, cite it): for a built module run `.venv/bin/python -m scripts.build.verify_shippable <track> <slug>` **without `--astro-build`**; for review coverage run `.venv/bin/python scripts/audit/module_quality_audit.py --level <track> --format json` with no `--output`; for a raw text sample run `.venv/bin/python -m scripts.audit.probe_uk_writing_score <file>`. These commands report to stdout and must not create repository artifacts in this review mode. This is NECESSARY but NOT SUFFICIENT — it cannot check facts.
2. **Then the factual + decolonization layer** — the reviewer's real job. Read and follow [seminar-content-review-prompt.md](seminar-content-review-prompt.md): claim extraction → per-claim source verification (Wikipedia + Literary RAG + heritage) → ghost-source / fabrication catch → decolonization scan → output format.

**Read-only output and gate rules:** return the report in the task response (stdout); do **not** create `status/`, `audit/`, `review/`, `.cache/`, telemetry, or any other checkout artifact. Never invoke the legacy `scripts/audit_module.py` / `scripts.audit.audit_module` from a read-only seminar review: it writes status and audit artifacts. `module_quality_audit` is advisory coverage evidence only; it cannot create a new promotion/release blocker. Promotion decisions remain governed by the active `verify_shippable` result and the current quality-gate contract. **REPORT ONLY — do not fix.** Reference issues #729 and #4840.
