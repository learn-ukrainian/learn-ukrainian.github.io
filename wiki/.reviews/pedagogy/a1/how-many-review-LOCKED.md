# how-many (L2-UK-EN A1/M11) — LOCKED review

- **File reviewed:** `wiki/pedagogy/a1/how-many.md`
- **Review date:** 2026-04-23
- **Reviewer:** claude-opus-4-7-xhigh (scale batch 1, review-and-lock pass)
- **Rubric:** 5-dimension wiki rubric (factual / language / decolonization / completeness / actionable), target ≥9 on each. See `docs/best-practices/wiki-plan-review-and-lock.md`.
- **Prior state:** No prior review file for `how-many`. Wiki meta had no lifecycle markers. The wiki covered sequence (1–100), the «скільки?» / «котрий?» split, time (`пів на шосту`), and the 1 / 2–4 / 5+ agreement model — but three practical A1 use cases that the paired plan teaches (age, prices in `гривні`, phone numbers) had **no writer-facing coverage in the wiki**; there was also no numerals-specific L2-errors table.
- **Fixes applied (this PR):**
  1. Added lock metadata to the wiki meta block (`last_reviewed`, `lifecycle: locked`, `reviewed_by`).
  2. Added **Крок 7: Практичні контексти — вік, ціни, номер телефону** to close the gap between what the wiki covered and what the plan requires the writer to teach.
  3. Extended Step 6 with an explicit warning against the calque `пол-шо́стого` (rus. *пол-шестого*), with the normative `пів на шосту` explained structurally (`пів` + `на` + accusative ordinal).
  4. Added **Типові помилки L2 (Common L2 Errors — numerals)** — a 10-row Surzhyk / calque / structural-error table targeted at L2 learners. Every right-column form is VESUM-verified; every left-column Russianism (`шесть`, `пять`, `семь`, `сємнадцять`, `девять`, `пятдесят`, `девяносто`, `пол`) is confirmed absent from VESUM.
  5. Added a **writer-note chunk policy** after the vocabulary table pinning `Мені + число + рік/роки/років`, `число + гривня/гривні/гривень`, and `пів на [порядкове]` as multi-word chunks (prevents the writer from over-teaching dative/genitive-plural as grammar categories at A1).
  6. Extended the "Приклади з підручників" block with **Приклад 5** — a choice-of-form drill that exercises exactly the new L2-errors table entries plus the 1 / 2–4 / 5+ agreement model on the two highest-frequency A1 nouns (`рік`, `гривня`).
  7. Extended vocabulary minimum with `гривня/гривні/гривень`, `копійка/копійки/копійок`, `коштує/коштують`, `телефон`, and a **passive-recognition** note on collective numerals (`двоє, троє, четверо, п'ятеро`) so the writer knows when to introduce vs. suppress them at A1.

## Dimension scores

| # | Dimension | Score | Evidence |
|---|-----------|-------|----------|
| 1 | Factual accuracy | **9/10** | Existing source-keyed claims ([S1]–[S7] via the `how-many.sources.yaml` sidecar) were left intact. The new Step 7 (age / prices / phone) and the L2-errors table do not introduce new unsourced lexical claims — every right-column form was checked in VESUM (batch verification log included in PR #XXXX body); every left-column Russianism is named as such and its absence from VESUM stated inline in the table's introductory paragraph. The `год` entry cites СУМ-11's own label "розм., рідко" verbatim. The one soft spot is that Step 7's phone-number pronunciation convention is native-speaker usage rather than a textbook cite — this is intentional and mirrors the at-the-cafe precedent for modern pragmatics that the L1 textbook corpus does not cover. |
| 2 | Ukrainian language quality | **9/10** | Zero Russianisms in the instructional prose. The new L2-errors table **explicitly catalogues** 10 Russianism / calque / structural-error pairs with normative replacements. Four-check coverage: (a) Russianisms (`шесть → шість`, `пять → п'ять`, `семь → сім`), (b) orthographic Surzhyk (`пятдесят → п'ятдесят` — м'який знак), (c) calques (`пол-шостого → пів на шосту`, `Я маю 20 років → Мені 20 років`), (d) structural errors (`двадцять один роки → двадцять один рік` — last-word agreement). All right-column forms attested in VESUM; left-column forms verified absent. |
| 3 | Decolonization | **9/10** | The existing decolonization section already forbade Russian phonetic comparisons and correctly flagged `дев'ятдесят` as dialectal (non-normative). The new L2-errors table strengthens this by **naming Russian explicitly** as the source of each calque rather than hiding the asymmetry. Step 7 explicitly separates age construction (`Мені X років` — dative-based) from both the English calque (`I have X years` → `Я маю...`) and the English predicate calque (`I am X years old` → `Я є...`) — decolonizing both from Russian *and* from L2-English interference. |
| 4 | Completeness | **9/10** | The three gaps closed by this pass: (gap a) wiki had no writer-facing coverage of age-expression (`Мені X років`), even though the plan's Діалог 2 and Section "Підсумок" teach it as core A1 content; (gap b) wiki had no `гривня / гривні / гривень` agreement pattern, even though the plan's Діалог 1 and Section "Ціни" teach it as core A1 content; (gap c) wiki had no numerals-specific L2-errors table, so the writer had no explicit list of Russianisms to inoculate against. All three are now explicit. Steps 1–7 give a complete sequence from cardinal 1–10 to practical A1 application in age / price / phone / time. |
| 5 | Actionable guidance | **9/10** | Step 7 gives directly liftable patterns: three numbered contexts with ready-made Q/A frames, the agreement-model applied in each. The chunk-policy writer-note prevents the common writer mistake of over-teaching declension. Приклад 5 is **directly drillable** — a writer can lift the 8 items verbatim into a fill-in-the-blank activity. The L2-errors table entries all have a "Примітка" column identifying the exact source of the error (Russian origin, English calque, Polish calque, structural mistake) so the writer can frame each one correctly. |

**Overall: 9/10 — LOCKED.**

## What "LOCKED" means for this artifact

- All 5 dimensions at ≥9.
- The three gaps between wiki coverage and plan-side A1 teaching targets (age, prices, phone numbers) are closed in the wiki.
- Every new vocabulary item (`гривня/гривні/гривень`, `копійка/копійки/копійок`, `коштує`, `телефон`, collective numerals) is VESUM-verified.
- Every Russianism / calque / structural-error pair in the new table has documented authority (VESUM absence, СУМ-11 label, or Правопис reference).
- Meta block carries `lifecycle: locked` + `reviewed_by` + `last_reviewed`.
- The paired plan (`curriculum/l2-uk-en/plans/a1/how-many.yaml`) is brought into alignment by the same PR.
- This wiki is cleared as a clean input for A.8/A.9 scale batch writing.

## Unlock triggers

This LOCKED state should be revisited if any of the following happen:

1. The built module (how-many A1/M11) surfaces a gap the wiki did not anticipate — file as an issue, do a fresh review round, republish with incremented `last_reviewed` date.
2. A native-speaker reviewer (Teacher Tetiana / Teacher Alona) flags a left- or right-column item in the L2-errors table — authoritative override of dictionary verification.
3. The `culture/decolonization/surzhyk-and-russianisms` wiki — referenced from the L2-errors table — changes its framing in a way that contradicts the table's typology.
4. VESUM / СУМ-11 updates retire or re-label any of the cited forms (esp. `дев'ятдесят` or `год` classifications, which were load-bearing for two table rows).
5. The paired plan drifts away from this wiki's new Step 7 content — e.g. if `гривня` agreement or age expression is subtracted from the plan without a paired wiki update.

## Residual non-blockers (documented, not blocking)

- **`кі́лько`** is attested in VESUM as a numeral and is flagged in the L2-errors table as a Western-Ukrainian dialectism / Polish-influence regionalism. A learner who hears it from a Western-Ukrainian speaker is not hearing "bad Ukrainian" — they are hearing a regional variant. The table note is accurate on this; framing is the writer's problem at module build time, not a wiki defect.
- **`год`** is attested in СУМ-11 with the label "розм., рідко" (colloquial, rare) and is genuinely Ukrainian in a narrow register. The table flags it **for the age-question context only** (where normative Ukrainian is `років`). A writer who encounters `год` in a literary citation should not treat it as a Russianism.
- **Collective numerals** (`двоє, троє, четверо, п'ятеро`) are introduced as passive-recognition only. This is a boundary choice aligned with the plan's A1 scope — productive use belongs to A2 (alongside `двоє дітей` as a `pluralia tantum`-only pattern).
- **Source sidecar `type: unknown`** fields were left unchanged — matches the precedent set by at-the-cafe-LOCKED / food-and-drink-LOCKED. Normalising source types is a separate cross-cutting cleanup, not a per-slug lock concern.
