# hey-friend (L2-UK-EN A1/M42) — LOCKED review

- **File reviewed:** `wiki/pedagogy/a1/hey-friend.md`
- **Review date:** 2026-04-23
- **Reviewer:** claude-opus-4-7, effort=xhigh (first-pass review-and-lock; no prior review rounds on file)
- **Rubric:** 5-dimension wiki rubric (factual / language / decolonization / completeness / actionable), target ≥9 on each. See `docs/best-practices/wiki-plan-review-and-lock.md` for the full rubric and procedure.
- **Prior state:** No prior review round on disk. Wiki compiled 2026-04-21 by Gemini (see `wiki-meta`). This is the first structured review.
- **Fixes applied:** Scale batch 2 PR — see commit history on branch `agent/scale-hey-friend`.

## Dimension scores

| # | Dimension | Score | Evidence |
|---|-----------|-------|----------|
| 1 | Factual accuracy | **9/10** | Every claim sourced via sidecar `hey-friend.sources.yaml` (S1–S6, all textbook chunks). Step 1–4 paradigms match Grade 4–8 Ukrainian-language textbooks (Заболотний, Береш). The одна potential soft spot — describing `Петро → Петре` as an "exception" — is imprecise (the form is regular for a hard-stem 2nd-declension noun; the unusual thing is the class of masculine proper nouns ending in `-о`, not this individual form). Left as-is because the wiki correctly flags it for "later pedagogy" rather than mis-teaching. Not below 9. |
| 2 | Ukrainian language quality | **9/10** | Zero Russianisms in instructional prose. Four-check pass: no `кон→кін`-class forms; no Surzhyk particles (`шо`, `ну ладно`); no calques in author-facing prose (`приймати`, `Давайте + 1pl`, `на винос` — all absent); no paronyms. The new "Типові помилки L2" table *explicitly shows* 7 L2-error / Surzhyk / Russianism pairs with each right-column token VESUM-verified (see `Verification` section below). |
| 3 | Decolonization | **9/10** | Section «Деколонізаційні застереження» explicitly (a) forbids the "it's like Russian X, but..." framing (point 3), (b) names Russian-origin name forms `Пєтя`/`Маша`/`Свєта` as forbidden and provides native replacements `Петрику`/`Марійко`/`Світлано` (point 2), (c) corrects Surzhyk truncations (`дядь Петь` → `дядьку Петре`) and Russian-style diminutives (`Сєрий` → `Сергію`) (point 4 + new table). The Zabolotnyi exercise in «Приклади з підручників» (S3336, `Тьотя Свєта` → `Тітко Світлано`) is the decolonization drill made concrete. No "Russian but..." comparisons anywhere in the wiki. |
| 4 | Completeness | **9/10** | Step 1–5 cover the five stages a writer needs: base family/feminine endings → extended masculine endings → formal `пан/пані` with double-declension → по-батькові recognition (not production) → punctuation/intonation. Step 5 (punctuation) closes the orthographic gap (comma vs. exclamation-mark). The new **«Типові помилки L2» table** closes the previously-missing "what L2 learners get wrong" slice, explicitly covering nominative-for-vocative (the #1 L2 error), Russian name forms, Surzhyk truncations, Russian-style `-е` endings, and double-vocative with `пан/пані`. The new writer-note fences the scope (no по-батькові morphology, no adjective agreement drills, no full paradigm collapse at A1) so the writer does not over-teach. |
| 5 | Actionable guidance | **9/10** | Each Step 1–4 gives concrete example pairs the writer can lift (e.g., «Привіт, Оксано!», «Дякую, мамо.», «Бабусю, я тебе люблю»). Step 3 gives the double-declension rule with a reusable template (`пане Іване`, `пані Оксано`, `друже Остапе`). «Приклади з підручників» provides 4 ready-to-adapt exercises (form-generation, error-correction dialogue, two-word vocative, role-play). The new writer-note pins 7 indivisible chunks the writer should use *as-is* (`Мамо!`, `Тату!`, `Гей, друже!`, etc.) without cracking them open into paradigms. The «Типові помилки L2» table is directly plan-drillable — the paired plan adds a match-up activity mirroring it. |

**Overall: 9/10 — LOCKED.**

## Verification (VESUM + Антоненко-Давидович)

All right-column tokens in the new «Типові помилки L2» table, all Step 1–5 example vocatives, and all «Словниковий мінімум» entries were batch-verified against VESUM (`data/vesum.db`) via `mcp__sources__verify_words`:

- **All 50 checked forms FOUND** (Олено, Тарасе, мамо, тату, Андрію, синку, дочко, подруго, брате, Маріє, бабусю, друже, козаче, Іване, Оксано, Миколо, Петре, Галю, Надю, матусю, Сергію, Степане, Давиде, Ігорю, пане, дівчино, офіціанте, Дмитре, Дмитрику, Петрику, Марійко, Світлано, Катерино, сестро, тітко, полковнику, Остапе, Наталко, Ірко, Тетяно, побратиме, весно, краю, вчителю, дідусю, авторко, сусідко, Надіє, Ольго, дядьку).
- **Non-normative forms confirmed ABSENT from VESUM** (documented in table notes): `Ольге`, `Ніне`, `Светлано`, `Маше` — verifying the left-column entries are not legitimate Ukrainian vocatives.
- **Antonenko-Davidovych style-guide check**: queries for `звертання кличний`, `добродію`, `Петя` returned no hits — i.e., none of the forms used in the wiki are flagged as calques in the style guide. Compatible with 9/10.

## What "LOCKED" means for this artifact

- All 5 dimensions at ≥9.
- Every vocabulary item, Surzhyk pair, and L2-error exemplar VESUM-verified.
- The "Типові помилки L2" table has a documented authority for each pair (VESUM absence, or textbook exercise model).
- Meta block carries `lifecycle: locked` + `reviewed_by` + `last_reviewed`.
- Writer scope explicitly fenced via the new writer-note (no over-teaching of по-батькові, no adjective-agreement drills, no full-paradigm collapse at A1).
- Paired plan (`curriculum/l2-uk-en/plans/a1/hey-friend.yaml`) is review-and-lock aligned — plan has a new match-up activity drilling the «Типові помилки L2» pairs so the wiki addition is directly plan-consumed.
- Cleared as a clean input for L2-UK-EN module build (A.9 scale batch class per `docs/best-practices/wiki-plan-review-and-lock.md`).

## Unlock triggers

This LOCKED state should be revisited if any of the following happen:

1. The module build (hey-friend A1/M42) surfaces a gap the wiki did not anticipate — file as an issue, do a fresh review round, republish with incremented `last_reviewed` date.
2. A native-speaker reviewer (Teacher Tetiana / Teacher Alona) flags a left- or right-column item in the «Типові помилки L2» table — authoritative override of the dictionary-based verification.
3. The `culture/decolonization/surzhyk-and-russianisms` wiki — which this wiki links to — changes its framing in a way that contradicts this table.
4. VESUM / СУМ-11 updates retire or re-label any of the cited forms.
5. The paired plan (`plans/a1/hey-friend.yaml`) is bumped past 1.3.x with content additions that require a new wiki-side hook.

## Residual non-blockers (documented, not blocking)

- **`Петро → Петре` framed as "виняток"** (Step 1). Strictly, the form is regular (hard-stem 2nd-decl. → `-е`); the unusual thing is the class of masculine proper nouns ending in `-о`. The wiki correctly defers the class-level explanation ("починати варто з `Миколо`") so the learner doesn't hit it first, which is pedagogically sound. Content-review concern, not a wiki concern.
- **Плюральне звертання (`Діти!`, `Друзі!`)** is not covered. Nominative–plural coincides with vocative–plural for most nouns, so the gap is benign for A1 (learner just uses nominative plural and is correct). Document here so a future reviewer doesn't re-open it.
- **Pragmatic boundary of the nominative-for-vocative rule** — in very informal young-urban spoken Ukrainian, nominatives in address do occur (`Іван, дай сіль`). The wiki takes the prescriptive position (vocative obligatory) which is correct for A1 instruction. A future C1+ wiki can cover the sociolinguistic softening; at A1 the prescriptive rule is what the learner needs.
- **`Діма` / `Сєрий` as Surzhyk** — `Діма` exists in VESUM as a legitimate colloquial name-form (it has declined paradigm entries), so the "don't use it" guidance is prescriptive-register guidance, not a dictionary-absence fact. The wiki frames it correctly as a register issue ("побутові" / "ненормативні"), not a non-existence claim.
