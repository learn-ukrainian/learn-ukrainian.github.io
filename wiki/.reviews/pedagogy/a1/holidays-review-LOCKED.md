# holidays (L2-UK-EN A1/M46) — LOCKED review

- **File reviewed:** `wiki/pedagogy/a1/holidays.md`
- **Review date:** 2026-04-23
- **Reviewer:** codex-scale-batch-2-holidays, review-and-lock pass
- **Rubric:** 5-dimension wiki rubric (factual / language / decolonization / completeness / actionable), target ≥9 on each. See `docs/best-practices/wiki-plan-review-and-lock.md`.
- **Prior state:** No prior locked review file for `holidays`; the wiki meta block had no lifecycle markers. The article also had three substantive problems: (1) no writer-facing L2 error section after the Phase 2C strip, (2) a weak expansion around `День подяки` that was not needed for A1 and diluted the module's core holiday set, and (3) under-specified holiday sequencing that left winter holidays and state holidays too easy to blur together.
- **Fixes applied:** review-and-lock pass on 2026-04-23. Main fixes:
  1. Added lock metadata to the wiki meta block.
  2. Rebuilt the teaching sequence around greeting formulas, holiday actions, a clear Christmas / New Year / `Щедрий вечір` split, Easter basics, and a lean state-holiday block.
  3. Removed the `День подяки` expansion and replaced it with concrete A1 content the paired plan can actually carry.
  4. Restored a holiday-specific `Типові помилки L2` section centered on real writer-facing risks: `з + орудний` greetings, `святкувати + знахідний`, and `колядки` vs `щедрівки`.
  5. Reworked the example activities so they can be lifted directly into learner-facing tasks.
  6. Replaced the vague source registry entries with concrete textbook chunk references in `holidays.sources.yaml`.

## Dimension scores

| # | Dimension | Score | Evidence |
|---|-----------|-------|----------|
| 1 | Factual accuracy | **9/10** | The locked version is materially safer than the prior one. It removes the soft, weakly grounded `День подяки` expansion and anchors the article in concrete textbook-backed holiday material: New Year greeting-card work ([S1]), `щедрівки` / `Щедрий вечір` ([S2]), Christmas carols and `Святвечір` ([S3], [S4]), Easter traditions ([S5]), and the state-holiday dates for Independence and Unity ([S6], [S7]). The article no longer claims or implies that A1 must cover speculative or marginal holiday content. |
| 2 | Ukrainian language quality | **9/10** | No Russianisms appear in the instructional prose. The review pass improves grammatical precision by explicitly distinguishing `Вітаю з Новим роком` / `З Різдвом` from nominative-form learner errors, and by separating `святкувати День Незалежності` from time phrases like `на Різдво`. The `колядки` / `щедрівки` split is also linguistically cleaner than the prior blended winter-holiday treatment. |
| 3 | Decolonization | **9/10** | The article now states clearly that the module should not be built through Russian comparisons, Soviet-calendar defaults, or long 7-January-centered framing. It recenters modern Ukrainian production on `25 грудня — Різдво Христове`, `24 серпня — День Незалежності України`, and `22 січня — День Соборності України`, while also warning against decorative state-holiday stereotypes that flatten Ukrainian civic culture into spectacle. |
| 4 | Completeness | **9/10** | A writer can now derive the full A1 holiday module from the wiki without inventing missing pedagogy: greeting formulas, `Що ви робите на...?`, winter-holiday distinctions, Easter basics, a minimal state-holiday block, and a dedicated L2-errors section are all present. The locked version closes the biggest prior completeness gap: it no longer forces the writer to infer how to teach `святкувати + знахідний` or how to keep `колядки` and `щедрівки` apart. |
| 5 | Actionable guidance | **9/10** | The rewrite is much more liftable. It gives ready-made chunks (`З Новим роком!`, `Що ви робите на...?`), a minimum viable dialogue, specific contrast pairs for the winter block, and five textbook-style activity models. The new `Типові помилки L2` table is especially actionable because it converts abstract review concerns into exact writer-facing fixes. |

**Overall: 9/10 — LOCKED.**

## Plan review (AC-2 checklist)

The paired plan `curriculum/l2-uk-en/plans/a1/holidays.yaml` was reviewed during the same pass against the 6-point AC-2 checklist from `docs/best-practices/wiki-plan-review-and-lock.md`.

1. **Pragmatic precision:** fixed the old drift where one `dialogue_situations[]` setting did not actually motivate the content-outline dialogues. The locked plan now uses three concrete scenarios that match the dialogue goals (greeting card, family holiday talk, state-holiday date talk).
2. **Russianisms in prose:** no Russianisms remained after the rewrite. The prior decorative `салют` direction was removed from the state-holiday block.
3. **Calques in vocabulary / hints:** reviewed the active holiday lexicon and kept only straightforward, attested items (`колядка`, `щедрівка`, `святвечір`, `паска`, `писанка`, etc.). New additions were VESUM-verified during the pass.
4. **Plan-internal contradictions:** closed the earlier mismatch between dialogue setting, objectives, grammar, and activities. The locked plan now explicitly teaches the contrast `святкувати + назва свята` vs `на + свято` and mirrors the wiki's winter-holiday split.
5. **References present and specific:** the plan already had external references and now also includes a back-reference to the locked wiki.
6. **Alignment with locked wiki:** every new wiki hook now has a plan-side hook: greeting formulas, winter-holiday distinction (`колядки` / `щедрівки`), Easter basics, lean state-holiday block, and the error drill around `з + орудний` greetings plus `святкувати` vs `на + свято`.

## What "LOCKED" means for this artifact

- All 5 rubric dimensions are at 9 or above.
- The wiki meta block now carries `lifecycle: locked`, `last_reviewed`, and `reviewed_by`.
- The source sidecar now points to concrete textbook chunks rather than placeholder-style unknown source ids.
- The article has explicit plan hooks for greeting formulas, holiday actions, winter-holiday distinctions, Easter basics, and the holiday-error drill.
- The paired plan has been reviewed against the same lock rubric and brought into alignment.

## Unlock triggers

1. A native-speaker review flags the `колядки` / `щедрівки` teaching split or the A1 handling of Easter greetings as misleading.
2. The paired plan drifts away from the wiki again, especially around the `святкувати + знахідний` contrast or the winter-holiday block.
3. The sources sidecar is regenerated in a way that drops one of the currently cited textbook supports.
4. A systemic audit identifies a holiday-specific defect class not checked in this pass.

## Residual non-blockers

- The locked version deliberately keeps `День Соборності України` lighter than `День Незалежності України`; it is present as an important state-holiday anchor, but not loaded with extra historical exposition at A1.
- `Христос воскрес! — Воістину воскрес!` is treated as culturally important but not forced as the only active Easter production pattern. That is an intentional pedagogy choice, not a gap.
