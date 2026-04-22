# my-day (L2-UK-EN A1/M25) — LOCKED review

- **File reviewed:** `wiki/pedagogy/a1/my-day.md`
- **Review date:** 2026-04-23
- **Reviewer:** claude-opus-4-7, effort=xhigh (adversarial self-review, post-fix)
- **Rubric:** 5-dimension wiki rubric (factual / language / decolonization / completeness / actionable), target ≥9 on each. See `docs/best-practices/wiki-plan-review-and-lock.md` for the full rubric and procedure.
- **Prior state:** no prior review file in `wiki/.reviews/pedagogy/a1/`. The wiki was a fresh compile (2026-04-21) with no `lifecycle` meta, no L2-error table for the daily-routine domain, and a `час`/`година` aside in the decolonization section that conflicted with the vocabulary list (which lists `час` as ★★★) without any writer-facing disambiguation.
- **Fixes applied:** this PR — see the diff on `agent/scale-my-day`.

## Dimension scores

| # | Dimension | Score | Evidence |
|---|-----------|-------|----------|
| 1 | Factual accuracy | **9/10** | Every pre-existing claim is already sourced against the S1–S10 registry in `my-day.sources.yaml` (textbooks: Grade 2 Vashulenko [S1, S2], Grade 7 verb-tense sections [S4], Grade 3 imperative exercises [S9]). The new "Типові помилки L2" table does not add textbook citations because the left-column items are ill-formed Ukrainian absent from the L1 pedagogical corpus; instead, every right-column form is VESUM-verified (see note below) and the entries appeal to either Антоненко-Давидович's documented `приймати X → брати X` rule or #1392 Phase 2 findings (`приймати ліки`, `Давайте + 1pl`). The one soft spot is the `час`/`година` writer-note which draws on native-speaker clock-time usage rather than a single textbook citation; this is intentional (routine chunks like `о сьомій годині` are not taught as grammar in L1 textbooks because L1 learners already have them). |
| 2 | Ukrainian language quality | **9/10** | Zero Russianisms in instructional prose. The new "Типові помилки L2" table *explicitly shows* 8 routine-specific Russianism / calque pairs with cited authority. All right-column forms verified in VESUM (`mcp__sources__verify_words`): `брати`, `душ`, `пити`, `ліки`, `вживати`, `прокиньмося`, `котра`, `година`, `сніданок`, `смачний`, `перекусити`, `поїсти`, `їсти`, `прокинутися`, `прокидатися`, `ходімо`, `купатися`, `вмиватися`. All left-column Russianisms confirmed absent from VESUM where expected (`вкусний`, `завтрак`, `кушати`, `покушати`) or explicitly acknowledged as a VESUM-present variant whose A1 normative form differs (`проснутися` — table note explains). The `приймати X → брати X` pair cites the generalised Антоненко-Давидович rule (same as `at-the-cafe` uses for `приймати замовлення → брати замовлення`). |
| 3 | Decolonization | **9/10** | Section explicitly forbids Russian phonetic comparisons, rejects framing Ukrainian as a "variant of Russian," and names Russian as the source of each calque in the new table (`калька російської моделі принимать душ`, `калька рос. принимать лекарства`, etc.). The new writer-note on `час`/`година` decolonises the "false friend" explicitly: it tells the writer exactly why the Russian `час` = "hour" does not map to the Ukrainian `час` = "time," rather than hiding the asymmetry behind a comparison. No "like Russian but…" framing anywhere. |
| 4 | Completeness | **9/10** | Gaps closed by this pass: (1) absence of an L2-error / Surzhyk inoculation table for daily-routine vocabulary → closed via new "Типові помилки L2" section with 8 routine-specific pairs; (2) silent contradiction between `час` in vocab list and `година (не час)` in decolonization section → closed by an explicit writer-note disambiguating the two senses with sentence-level examples; (3) missing chunk-policy guidance that would let the writer handle clock-time (`о сьомій (годині)`, `пів на восьму`, `Котра година?`) and fixed collocations (`лягати спати`, `робити зарядку`) without over-teaching locative of ordinals / imperative of reflexives at A1 → closed via the new writer-note after the vocabulary table. |
| 5 | Actionable guidance | **9/10** | The chunk-policy writer-note pins six exact indivisible phrases the writer must treat as set formulas. The Surzhyk table has a "Примітка" column identifying the source of each calque. New exercise 5 in "Приклади з підручників" is a direct drill of all 8 pairs from the new table — the writer can lift the 8-item list verbatim into a module activity. Generic "teach it well" advice is absent. |

**Overall: 9/10 — LOCKED.**

## What "LOCKED" means for this artifact

- All 5 dimensions at ≥9.
- The silent `час` vs `година` contradiction is closed.
- A routine-specific L2 error table exists and is VESUM-verified.
- Chunk policy for clock-time and fixed collocations is explicit.
- Meta block carries `lifecycle: locked` + `reviewed_by: claude-opus-4-7-xhigh` + `last_reviewed: 2026-04-23`.
- This wiki is cleared as clean input for the paired module build (a1-025 / Мій день).

## Unlock triggers

Revisit LOCKED state if any of the following happen:

1. The paired module build (a1-025) surfaces a gap the wiki did not anticipate — file as an issue, do a fresh review round, republish with incremented `last_reviewed`.
2. A native-speaker reviewer (Teacher Tetiana / Teacher Alona) flags a left- or right-column item in the "Типові помилки L2" table — authoritative override of dictionary-based verification.
3. The `culture/decolonization/surzhyk-and-russianisms` wiki changes its framing in a way that contradicts this table's pair classifications.
4. VESUM / СУМ-11 updates retire or re-label any of the cited forms (`брати душ`, `пити ліки`, `прокиньмося`, `сніданок`, `смачний`, `ходімо`).
5. A subsequent systemic audit (#1392-style) discovers a defect class that would have caught a problem here.

## Residual non-blockers (documented, not blocking)

- `проснутися` is **present in VESUM** as a legitimate Ukrainian form (colloquial / informal register), so the table's classification of "use `прокинутися` at A1 instead" is a pedagogical choice about reducing paradigm noise at A1, not a correctness verdict. The table note makes this explicit ("`Проснутися` існує як розмовний варіант… у педагогічному тексті для рівня А1 варто закріплювати саме `прокидатися`"). A B1+ wiki may decide to introduce the colloquial doublet; at A1 it stays one-form.
- `зарядка` (in `робити зарядку`) is a regular Ukrainian noun (VESUM: `зарядка(noun)`) — not a Russianism even though it is cognate with the Russian `зарядка`. The chunk-policy note includes `робити зарядку` as a standard A1 chunk and does NOT place it in the Surzhyk table. Called out here because a future reviewer may be tempted to flag it — don't; the word is fine.
- Textbook exercise 3 (imperative transformation from Grade 3 [S9]) is preserved unchanged from the prior compile. It is valuable on its own merits (imperative is the only grammar drilled in this wiki beyond time-word insertion) and the new Surzhyk drill is added as exercise 5 rather than overwriting exercise 3. This differs from the at-the-cafe pattern (where exercise 3 was rewritten) but the net effect is the same: there is a direct drill of the new table, and the pre-existing pedagogical coverage is kept.
- The writer is trusted not to introduce the full ordinal-number paradigm (`перший … дванадцятий` in locative) when using `о сьомій / о восьмій` etc. The writer-note is explicit ("should not be asked to inflect `сьомий` / `восьмий` / `перший`"), but a sufficiently ambitious writer could still over-teach. This is a content-review concern (v6 review pass), not a wiki concern.
