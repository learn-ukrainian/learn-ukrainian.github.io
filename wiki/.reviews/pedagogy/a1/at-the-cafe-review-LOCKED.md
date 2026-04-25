# at-the-cafe (L2-UK-EN A1/M38) — LOCKED review

- **File reviewed:** `wiki/pedagogy/a1/at-the-cafe.md`
- **Review date:** 2026-04-22
- **Reviewer:** claude-opus-4-7, effort=xhigh (adversarial self-review, post-fix)
- **Rubric:** 5-dimension wiki rubric (factual / language / decolonization / completeness / actionable), target ≥9 on each. See `docs/best-practices/wiki-plan-review-and-lock.md` for the full rubric and procedure.
- **Prior state:** 8/10 (final review from 2026-04-05, `wiki/.reviews/pedagogy/a1/at-the-cafe-review-final.md`). Documented gaps: missing modern café vocab (`тут чи із собою`, sizes); Surzhyk table generic, not café-specific.
- **Fixes applied:** PR #1412 (commit `115b6989`) — see that commit for the diff.

## Dimension scores

| # | Dimension | Score | Evidence |
|---|-----------|-------|----------|
| 1 | Factual accuracy | **9/10** | Every claim sourced. Sources S1–S10 properly keyed via the sidecar `at-the-cafe.sources.yaml`. The one remaining soft spot is that Step 5 ("сучасна кав'ярня" — `тут чи із собою`, sizes) draws on native-speaker usage rather than a single textbook citation; this is intentional (the textbook corpus is L1 pedagogy and does not cover modern café pragmatics) and is acknowledged inline in the wiki text ("яких немає у шкільних підручниках"). |
| 2 | Ukrainian language quality | **9/10** | Zero Russianisms in instructional text. New "Типові помилки L2" table *explicitly shows* 8 café-specific Russianism/calque pairs with cited authority. All right-column tokens verified in VESUM (`data/vesum.db`) + cross-checked against СУМ-11. The `приймати замовлення → брати замовлення` pair cites Антоненко-Давидович's own `приймати участь → брати участь` as the generalised rule. |
| 3 | Decolonization | **9/10** | Section explicitly forbids Russian phonetic comparisons, highlights Ukrainian-specific etiquette (кличний відмінок, `пане`/`офіціанте`/`дівчино`, `Будьте ласкаві`), and the new Surzhyk table names Russian as the source of the calque in each case (e.g. "калька з рос. *на вынос*") — teaching the asymmetry explicitly rather than hiding it. |
| 4 | Completeness | **9/10** | Gap 1 (modern café vocab) closed via Step 5 + vocabulary additions. Gap 2 (café-specific Surzhyk table) closed via the new "Типові помилки L2" section. Step 5 explicitly covers format (`Вам тут чи із собою?`) + size (`велику/маленьку каву`) and gives the minimal complete ordering scenario. The only residue is that Розділ "Типові помилки L2" does not yet re-teach the `Будь ласка / Прошу` stress-distinction that the old wiki version had — this was not a documented gap, is adequately covered by other wikis, and does not count against 9/10. |
| 5 | Actionable guidance | **9/10** | Step 5 gives an explicit minimal-viable dialogue the writer can lift directly. The Surzhyk table is now directly usable: exercise 3 in "Приклади з підручників" has been rewritten to drill exactly those pairs. The writer-note after the vocabulary table pins `велику каву` / `Тут, будь ласка` / `Із собою, будь ласка` as indivisible chunks — preventing the writer from teaching adjective declension at A1. Every entry in the new table has a "Примітка" column identifying the exact source of the calque. |

**Overall: 9/10 — LOCKED.**

## What "LOCKED" means for this artifact

- All 5 dimensions at ≥9.
- Both documented gaps from the 8/10 final review have been closed.
- Every new vocabulary item is VESUM-verified.
- Every Surzhyk pair in the new table has a documented authority (VESUM, СУМ-11, or Антоненко-Давидович).
- Meta block carries `lifecycle: locked` + `reviewed_by` + `last_reviewed`.
- This wiki is cleared as a clean input for A.8 canary (L2-UK-EN module build) per `docs/architecture/a8-canary-protocol.md`.

## Unlock triggers

This LOCKED state should be revisited if any of the following happen:

1. The module build (at-the-cafe A1/M38) surfaces a gap the wiki did not anticipate — file as an issue, do a fresh review round, republish with incremented `last_reviewed` date.
2. A native-speaker reviewer (native-speaker reviewer) flags a left- or right-column item in the Surzhyk table — authoritative override of the dictionary-based verification.
3. The `culture/decolonization/surzhyk-and-russianisms` wiki — which this wiki links to — changes its framing in a way that contradicts this table.
4. VESUM / СУМ-11 updates retire or re-label any of the cited forms.

## Residual non-blockers (documented, not blocking)

- `трубочка` (in the "straw" sense) is a calque, but the same word-form exists in VESUM as a legitimate diminutive of `трубка` (and as a pastry name). The table's "Примітка" column flags this explicitly ("У значенні «трубка для пиття» — калька"). Keep as-is; confusing only if the learner is already familiar with the pastry sense.
- Writer guidance for Step 5 trusts the writer to NOT introduce the instrumental of `себе` paradigm at A1. The writer-note after the vocabulary table is explicit, but a sufficiently ambitious writer could still over-teach. This is a content-review concern (v6 review pass), not a wiki concern.
