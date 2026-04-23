# special-signs (L2-UK-EN A1/M03) — LOCKED review

- **File reviewed:** `wiki/pedagogy/a1/special-signs.md`
- **Review date:** 2026-04-23
- **Reviewer:** codex, effort=high (adversarial self-review, post-fix)
- **Rubric:** 5-dimension wiki rubric (factual / language / decolonization / completeness / actionable), target ≥9 on each. See `docs/best-practices/wiki-plan-review-and-lock.md` for the full rubric and procedure.
- **Prior state:** No prior locked review file for `special-signs` in `wiki/.reviews/pedagogy/a1/`. The wiki had three substantive gaps at intake: (1) no lifecycle metadata in the wiki-meta block, (2) no `Типові помилки L2` section despite `special-signs` being one of the highest-interference phonetics/orthography slugs in A1, and (3) an under-specified rule boundary around apostrophe vs. no-apostrophe zones (`буряк` / `бур'ян` / `свято` / `цвях`), which would have forced the writer to invent the exception handling on their own.
- **Fixes applied:** This PR — see the diff against `wiki/pedagogy/a1/special-signs.md`.

## Dimension scores

| # | Dimension | Score | Evidence |
|---|-----------|-------|----------|
| 1 | Factual accuracy | **9/10** | The revised wiki no longer states the beginner apostrophe rule as an absolute law. It now explicitly marks the A1 scope boundary ("base model after `б, п, в, м, ф, р`") and names the no-apostrophe exception zone with concrete standard words: `свято`, `цвях`, `морквяний`, `буряк`. The earlier soft-sign section's misleading minimal-pair material has been replaced with VESUM-verifiable pairs (`стан/стань`, `лан/лань`, `рис/рись`) and high-frequency words (`день`, `кінь`, `сіль`, `вчитель`). Transfer examples are now textbook-shaped (`Мар'-яна`, `дере-в'яний`, `бур'-ян`, `паль-ці`) instead of a vague reminder. New vocabulary used to close the gaps (`буряк`, `бур'ян`, `свято`, `цвях`, `стань`, `лань`, `рись`, `ложка`, `Мар'яна`, `дерев'яний`, `пальці`) was verified against VESUM in the main checkout database before locking. |
| 2 | Ukrainian language quality | **9/10** | Instructional prose is clean literary Ukrainian: no Russianisms, no Surzhyk spellings, no `Давайте`, no calqued pseudo-technical language. The article now uses Ukrainian pedagogical categories consistently (`м'якість`, `йотовані літери`, `збіг приголосних`, `перенос`, `роздільна вимова`) and avoids the previous risk of teaching malformed forms such as `брать`/`куть`. The new L2-error table is phrased in Ukrainian pedagogical prose rather than English-framed learner diagnostics. |
| 3 | Decolonization | **9/10** | The decolonization section is affirmative and Ukrainian-first. It explicitly forbids teaching the apostrophe as "the Ukrainian version of Russian `ъ`" or the soft sign as "the same as in Russian", and it reframes Russian only as a possible source of interference (`св'ято`, `льожка`), not as the baseline explanatory system. The strongest improvement is operational rather than rhetorical: the core teaching contrast is now `буряк` / `бур'ян` / `свято`, i.e. Ukrainian examples with Ukrainian internal logic, not a comparative detour through Russian orthography. |
| 4 | Completeness | **9/10** | The wiki now gives the writer the full minimum package for this slug: sequencing (Кроки 1–5), scope boundary (what is in A1 vs. what is deferred), vocabulary boundaries, transfer rules, and a concrete `Типові помилки L2` section. The previously missing exception zone (`свято`, `цвях`, `морквяний`) is now taught as part of the article rather than left to writer intuition. The writer note after `Словниковий мінімум` is critical: it stops the module from expanding into prefix-apostrophe theory or general morphology. Meta block lifecycle markers are present. |
| 5 | Actionable guidance | **9/10** | The article is now directly writable. A writer can lift the three-way contrast (`буряк` / `бур'ян` / `свято`), the five-row L2-error table, and the four exercise models into a module without inventing new structure. The new exercise set is aligned to the actual defect surface: contrastive sort, fill-in of `ь`/apostrophe, find-the-no-apostrophe word, and transfer practice. The transfer block names exact line-break models rather than abstractly saying "remember the transfer rule". |

**Overall: 9/10 — LOCKED.**

## What "LOCKED" means for this artifact

- All 5 dimensions are at ≥9.
- The intake gaps (missing lifecycle metadata, missing `Типові помилки L2`, fuzzy apostrophe/no-apostrophe boundary) have been closed in the wiki body itself.
- Every new single-word vocabulary item added for the lock pass was VESUM-verified before commit.
- The wiki meta block now carries `lifecycle: locked`, `last_reviewed`, and `reviewed_by`.
- The paired plan has been brought into alignment and marked `lifecycle: locked`.

## Unlock triggers

This LOCKED state should be revisited if any of the following happen:

1. A native-speaker reviewer flags any of the contrast words or transfer models, especially `буряк` / `бур'ян` / `свято` / `цвях`.
2. The paired plan drifts again by reintroducing non-slug phonetics content or by dropping the exception-zone hooks.
3. A future wiki recompile silently removes the `Типові помилки L2` section or the writer note while leaving `lifecycle: locked` in metadata.
4. The orthography guidance for transfer or apostrophe scope changes upstream in the project's textbook corpus or review rubric.

## Residual non-blockers (documented, not blocking)

- The source sidecar `wiki/pedagogy/a1/special-signs.sources.yaml` still uses the generic `type: unknown` convention, like many other wiki sidecars in the repo. This is corpus-hygiene debt, not a blocker on the pedagogical content.
- The short mnemonic `Де ти з'їси ці лини?` remains in the wiki as a beginner memory aid, but the article now explicitly states that the author must remember the full orthographic set (`д, т, з, с, ц, л, н, р, дз`) rather than treating the short mnemonic as the whole rule. That is the correct compromise for A1: pedagogically light for the learner, factually complete for the writer.
