# food-and-drink (L2-UK-EN A1/M36) — LOCKED review

- **File reviewed:** `wiki/pedagogy/a1/food-and-drink.md`
- **Review date:** 2026-04-23
- **Reviewer:** codex-gpt-5-food-and-drink
- **Rubric:** 5-dimension wiki rubric (factual / language / decolonization / completeness / actionable), target ≥9 on each. See `docs/best-practices/wiki-plan-review-and-lock.md`.
- **Prior state:** unlocked, no prior `food-and-drink` review file in `wiki/.reviews/pedagogy/a1/`. Main gaps on intake: no lock metadata, no food-specific L2 error block, weak writer guidance on `з + ...` / `без + ...` chunks, and textbook examples that did not directly drill the mistakes the article warns about.
- **Verification note:** The checked-in `data/vesum.db` is an empty placeholder in this worktree, so word-form verification for new right-column items was done against the raw linked VESUM corpus file `data/vesum/dict_corp_vis.txt` instead of the absent local SQLite index.

## Dimension scores

| # | Dimension | Score | Evidence |
|---|-----------|-------|----------|
| 1 | Factual accuracy | **9/10** | The article now keeps its strongest claims tied to explicit source-backed teaching patterns: meal-verb pairing, adjective agreement via food nouns, fixed etiquette formula `Смачного!`, and A1 chunk teaching for `без цукру` / `без молока`. New citations [S13]–[S18] cover the added guidance and the borscht framing. |
| 2 | Ukrainian language quality | **9/10** | The wiki now contains a dedicated food-specific L2 error table with normative replacements: `сир`, `смачний/смачна`, `смажена`, `без цукру`, `Я снідаю`, `Смачного!`. The right-column forms were checked against the raw VESUM corpus; the left-column items are explicitly marked as errors/calques, not presented as acceptable teaching targets. |
| 3 | Decolonization | **9/10** | The decolonization section already rejected Russian-centered comparison; this pass makes it more operational by telling the writer how to frame `борщ` and by explicitly preferring Ukrainian etiquette and food vocabulary over Russianized formulas. The article teaches Ukrainian food on Ukrainian terms rather than through Russian analogues. |
| 4 | Completeness | **9/10** | The prior wiki covered food categories and cultural framing, but it did not tell the writer which errors to inoculate against or which high-frequency chunks to treat as indivisible at A1. Those gaps are now closed through new Step 6, the chunk note after vocabulary, and the `Типові помилки L2` section. |
| 5 | Actionable guidance | **9/10** | The writer now has directly liftable guidance: which meal verbs to pair, which chunks to keep whole, which wrong forms can serve as distractors, and four activity models that map one-to-one to the article’s teaching claims. This is materially stronger than the prior generic textbook summaries. |

**Overall: 9/10 — LOCKED.**

## What "LOCKED" means for this artifact

- All 5 dimensions are at or above 9.
- The wiki carries `lifecycle: locked`, `last_reviewed`, and `reviewed_by` metadata.
- Food-specific L2 pitfalls are now explicit instead of implied.
- New writer-facing chunks and corrective forms are source-backed and VESUM-checked.
- The article is ready to serve as the pedagogical source of truth for the paired plan.

## Unlock triggers

1. The paired plan or built module drifts away from the wiki’s new chunk policy (`кава з молоком`, `без цукру`, `Смачного!`) or omits the food-specific L2 corrections.
2. A native-speaker reviewer objects to any right-column corrective form in the `Типові помилки L2` table.
3. A future review replaces the cited food-culture framing for `борщ` or the etiquette guidance around `Смачного!`.
4. The source registry for [S13]–[S18] changes or the linked source packet is revised in a way that weakens the evidence for these additions.

## Residual non-blockers

- The article remains broad by design: it introduces `борщ`, `вареники`, and other cultural items without turning into a cuisine-history lesson. That is appropriate for A1 and does not block lock status.
- The chunk policy intentionally previews forms like `каву` and `без цукру` before a full case lesson. This is acceptable because the article explicitly tells the writer to treat them as memorized service formulas, not as a grammar presentation.
