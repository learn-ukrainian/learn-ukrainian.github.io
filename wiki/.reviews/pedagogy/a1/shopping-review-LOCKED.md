# shopping (L2-UK-EN A1/M39) — LOCKED review

- **File reviewed:** `wiki/pedagogy/a1/shopping.md`
- **Review date:** 2026-04-23
- **Reviewer:** codex-gpt-5, effort=high (final lock pass)
- **Rubric:** 5-dimension wiki rubric (factual / language / decolonization / completeness / actionable), target ≥9 on each. See `docs/best-practices/wiki-plan-review-and-lock.md`.
- **Prior state:** no prior `shopping-review*.md` file in `wiki/.reviews/pedagogy/a1`; the wiki was effectively unscored and unlocked. The pre-lock version covered price/number basics but stopped short of checkout, had no shopping-specific L2 error block, and gave the writer too little guidance on which chunks to prioritize.
- **Fixes applied in this pass:** added lock metadata to the wiki, rewrote the teaching sequence around price → quantity → checkout, added a shopping-specific L2 error table, tightened the examples section around concrete shopping drills, and refreshed `shopping.sources.yaml` with specific textbook/external chunk IDs.

## Dimension scores

| # | Dimension | Score | Evidence |
|---|-----------|-------|----------|
| 1 | Factual accuracy | **9/10** | Core claims are now pinned to specific sources in `shopping.sources.yaml`: price/availability dialogue and checkout closure rely on `6-klas-ukrmova-avramenko-2023_s0017`; payment-method vocabulary relies on `4-klas-ukrayinska-mova-ponomarova-2021-1_s0122`; quantity-chunk guidance relies on `S1143`; clothing-shop extension relies on `S2393` and `ext-ulp_youtube-272`. The vocabulary additions used for the new writer guidance (`картка`, `готівка`, `приміряти`, `крамниця`, `продавчиня`) were VESUM-verified during this pass. |
| 2 | Ukrainian language quality | **9/10** | The revised wiki removes generic English framing and keeps instructional prose in natural Ukrainian. The new `Типові помилки L2` block directly addresses the highest-risk shopping mistakes: `коштує/коштують`, `один кілограм`, `два кілограми яблук`, `три пляшки води`, `приміряти`. No Russian-comparison teaching remains in the instructional path; the decolonization section explicitly forbids that framing. |
| 3 | Decolonization | **9/10** | The decolonization section is now shopping-specific, not boilerplate. It explicitly bans explaining `гривня` through another currency, rejects Russian-as-scaffold explanations for shopping vocabulary, and refuses to frame `крамниця` as decorative nationalism. The examples are anchored in Ukrainian retail contexts (`ринок`, `крамниця`, `каса`) rather than a generic post-Soviet setting. |
| 4 | Completeness | **9/10** | The prior version covered "what is a price?" but not the full act of buying. The locked version now covers: scene setup, availability, price, quantity chunks, decision/selection, checkout/payment, and an optional clothing-shop extension. It also includes the shopping-specific L2 error table that was previously absent, so the writer no longer has to invent likely failure points such as `коштує/коштують` or `приміряти/pоміряти`. |
| 5 | Actionable guidance | **9/10** | The writer now gets liftable material instead of generic advice: concrete chunk lists, a note on which phrases to treat as indivisible, a checkout micro-script, and four directly reusable exercise patterns. The examples section is tied to the exact weak spots named elsewhere in the wiki, so the writer can turn the pedagogical brief into activities without inventing the practice set from scratch. |

**Overall: 9/10 — LOCKED.**

## What "LOCKED" means for this artifact

- All 5 rubric dimensions are at 9 or above.
- The wiki has a complete A1 shopping spine: price, quantity, and payment all have writer-facing hooks.
- The shopping-specific L2 error block is present and aligned with the teaching sequence.
- The source registry has been refreshed to specific, traceable chunks rather than a thin placeholder mapping.
- The wiki meta block carries `lifecycle: locked`, `last_reviewed`, and `reviewed_by`.

## Unlock triggers

Re-open this wiki for review if any of the following happen:

1. The paired `curriculum/l2-uk-en/plans/a1/shopping.yaml` drifts away from the wiki's new checkout/L2-error guidance.
2. A native-speaker reviewer challenges one of the new shopping chunks or corrections, especially in the quantity table or the `приміряти` distinction.
3. The shopping module build surfaces a missing writer hook that still forces the module author to invent key learner-facing material.
4. The source registry is regenerated and drops any of the specific chunk mappings used for this lock pass.

## Residual non-blockers

- The shopping wiki still favors product/market language over non-food retail. That is intentional for A1 and does not block the lock; the clothing-shop extension is present only as a narrow, optional add-on.
- The source base is still mostly textbook-heavy. That is acceptable for this slug because the goal is writer guidance for A1, not a sociolinguistic survey of modern retail language.
