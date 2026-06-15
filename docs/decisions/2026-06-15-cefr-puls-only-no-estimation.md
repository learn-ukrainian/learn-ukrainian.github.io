# Decision: CEFR levels are PULS-only — no frequency estimation, leave uncovered blank

- **Date:** 2026-06-15
- **Decided by:** user (Krisztian)
- **Status:** active
- **Scope:** Word Atlas CEFR field (`enrichment.cefr`) in `site/src/data/lexicon-manifest.json`
- **Revisit when:** a new *validated per-word* Ukrainian CEFR source becomes available.

## Decision
Assign a CEFR level to an Atlas word **only** when it is present in the PULS corpus profile
(`puls_cefr`, served by `enrich_manifest._cefr` / `mcp__sources__query_cefr_level`). For words
not in PULS, **leave the CEFR field blank — never estimate it** (not from GRAC frequency, not
from any heuristic). A labeled "estimated" band was explicitly rejected: leave it empty until
real data backs it up.

This is already the implemented behavior — `_cefr` returns `None` when the word is absent from
`puls_cefr`. **No code change** results from this decision; it closes the long-pending
"estimate vs blank" question (was: `docs/session-state/*atlas*`).

## Why PULS is trusted *where it has the word* (the evidence)
PULS was questioned ("how can we trust that list?") and tested rather than taken on faith:

1. **Provenance:** Synchak/Starko/Burak/Svystun (UCU), eLex 2025 — 1M-word corpus from 21 UFL
   textbooks, VESUM-lemmatized, levels via "significant onset of use" + two-stage expert review.
   The published set = the 5,891 words on PULS (`puls.peremova.org`) = our `puls_cefr` (5,939 rows).
2. **Internal sanity:** level assignments spot-check as linguistically correct A1→C1
   (A1 `я/що/як/яблуко`; C1 `чигати/шинок`); distribution is A1 962 · A2 1386 · B1 2164 · B2 1194
   · C1 233 · **C2 0** → PULS covers **A1–B2 only**.
3. **External cross-check vs our own curriculum (decisive):** 1,239 words overlap between PULS and
   our `course_usage` first-appearance level. **90% agree within ±1 level**; 54% exact; mean bias
   `PULS − ours = +0.24` (PULS slightly harder). Two independently-built sources concurring 90%
   within one level is strong corroboration for an inherently fuzzy CEFR task.

## Known limits / follow-ups (NOT blockers)
- **PULS is empty above B2** — cannot level advanced vocab; that vocab stays blank by this decision.
- **Cross-check only validated A1–B1** (that's where our built content is) — re-validate as B2+ ships.
- **94 words carry multiple PULS levels** (POS/sense splits); `_cefr` currently takes the first row
  (`LIMIT 1`, arbitrary). Minor follow-up: prefer the **lowest** level (most conservative). Small,
  separate change.
- **125 words disagree by ≥2 levels** with our curriculum (`крамниця` PULS=C1 vs we-teach-A1 — our
  decolonized choice over `магазин`; `готово`/`надія` PULS-conservative). This is a free **review
  queue**, not a defect — each is a PULS quirk to override or a pedagogical choice to document.

## What this is NOT
Not a claim that PULS is an official CEFR standard — there is none. The Ukrainian State Standard
2024 (mova.gov.ua №279) is a descriptors framework with **no per-word vocabulary list** (confirmed
in the Synchak paper). PULS is the best *validated* per-word source we have; surface it labeled as
a corpus profile (`source: PULS`), not as an authority.
