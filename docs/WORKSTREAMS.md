# Workstreams — V6 Pipeline Era

> Epics: [#982](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/982) (V6 Pipeline) | [#981](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/981) (A1 Rebuild)
> Last updated: 2026-03-21

---

## Three Quality Pillars

Every shippable module must pass all three:

| Pillar | What | How |
|--------|------|-----|
| **Content** | Pedagogy, tone, accuracy, Ukrainian quality | Gemini adversarial review (10-dimension rubric, #991) |
| **Structural** | Word count, activities, vocab, engagement | Deterministic audit gates (`audit_module.py`) |
| **Visual** | Tabs render, exercises work, no broken MDX | Chrome-based QA (#1008) |

---

## Priority Queue

Work items in execution order. Each must unblock the next.

### P0 — Unblock the pipeline

| # | Title | Why first |
|---|-------|-----------|
| [#1007](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/1007) | Monitor API migration | V6 builds invisible to dashboard/API — nothing tracks progress |
| [#996](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/996) | Exercise placeholder filler | Stray quotes, missing fill-in context — exercises broken |
| [#997](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/997) | DSL to MDX converter | Exercises must render correctly in Starlight |
| [#1006](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/1006) | Quick verify + retry loop | Structural checks catch errors before review |
| [#991](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/991) | Review prompt calibration | Gemini review is the content quality gate |

### P1 — Ship M01, prove the pipeline end-to-end

| # | Title | Why now |
|---|-------|---------|
| [#1009](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/1009) | ENRICH — словник, videos, tabs, dialogue formatting | M01 missing vocabulary table, Anna's videos, resource tabs |
| — | M01 quality pass | Rebuild M01 through full V6, target 9+/10 from Gemini |
| [#1008](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/1008) | Visual QA (Chrome) | Verify M01 renders correctly before scaling |

### P2 — Scale

| # | Title | Scope |
|---|-------|-------|
| — | Scale A1.1 (M02-M07) | First 7 modules through V6 pipeline |
| [#1011](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/1011) | A2 plan writing | 60 modules from V3 design into plan YAMLs |
| [#1010](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/1010) | Rewrite WORKSTREAMS.md | This file (close after merge) |

### P3 — Pipeline hardening (open, not blocking)

| # | Title | Notes |
|---|-------|-------|
| [#999](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/999) | Tutor prompt principles | Integrate into writing prompt |
| [#998](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/998) | Chunking for long modules | Needed when scaling to B1+ (4,000+ words) |
| [#989](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/989) | Validation false positives | Reduce noise in verify step |
| [#985](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/985) | Preflight auto-fixes | Auto-correct plan issues before build |
| [#984](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/984) | Automated plan review | LLM adversarial review of plans |

### Completed V6 components

| # | Title |
|---|-------|
| [#994](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/994) | Research knowledge packet |
| [#995](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/995) | Writing prompt design |
| [#988](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/988) | Stress annotation |

---

## V6 Pipeline Architecture

```
Plan (YAML) → Research packet (RAG) → Write (Claude) → Quick verify → Exercises (DSL fill)
  → Stress annotation → ENRICH (словник/videos/tabs) → Validate → Review (Gemini) → MDX
```

- **Writer:** Claude (won comparison #1001 — 8.55 vs 8.35)
- **Reviewer:** Gemini (adversarial, 10-dimension rubric)
- **Retry:** Max 2 attempts, whole-module regen, model switch on failure
- **Orchestrator:** `scripts/build/v6_build.py`

---

## Content Status

### A1 — 55 plans, 0 shipped modules

- All 55 plans written, Gemini-reviewed, pass `check_plan.py`
- M01 built by both Claude and Gemini (comparison complete)
- Next: fix pipeline blockers, then ship M01, then scale A1.1

### A2 — design complete, no plans

- 60 modules across 8 phases designed in `docs/l2-uk-en/A2-CURRICULUM-V3.md`
- Gemini-reviewed, State Standard coverage verified
- Plan writing tracked in #1011

### B1-C2 — design phase

| # | Title | Status |
|---|-------|--------|
| [#1002](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/1002) | B1 design | Open |
| [#1003](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/1003) | B2 design | Open |
| [#1004](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/1004) | C1 design | Open, deferred |
| [#1005](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/1005) | C2 design | Open, deferred |

---

## Deferred Work

All labeled `priority:later`. Will revisit after A1-B2 core tracks ship.

### Seminar tracks
| # | Title |
|---|-------|
| [#706](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/706) | Seminar depth review |
| [#499](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/499) | Chronicle quotes for C1-BIO |
| [#675](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/675) | Textbook image enrichment |

### STEM domain tracks (#859 epic + children)
All STEM work (IT, MED, BUS, LAW, etc.) is deferred. Issues #859-#870 remain open but not prioritized until core A1-B2 tracks are complete.

### Advanced tracks
| # | Title |
|---|-------|
| [#303](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/303) | C2 implementation (100 modules) |
| [#497](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/497) | OES + RUTH tracks (200 modules) |
| [#658](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/658) | Literature Matrix Phase B |
| [#676](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/676) | Monolingual toggle (C1+) |
| [#429](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/429) | PRO tracks activity framework |
| [#705](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/705) | Vocabulary progression audit |

### RAG & infrastructure
| # | Title |
|---|-------|
| [#715](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/715) | ZNO exam dataset integration |
| [#854](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/854) | Expand RAG sources for weak areas |
| [#634](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/634) | Monolingual lexicon builder |
