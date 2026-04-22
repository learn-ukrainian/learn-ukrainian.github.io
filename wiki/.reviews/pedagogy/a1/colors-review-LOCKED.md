# colors (L2-UK-EN A1/M10) — LOCKED review

- **File reviewed:** `wiki/pedagogy/a1/colors.md`
- **Review date:** 2026-04-23
- **Reviewer:** codex-scale-batch-1-colors, review-and-lock pass
- **Rubric:** 5-dimension wiki rubric (factual / language / decolonization / completeness / actionable), target ≥9 on each. See `docs/best-practices/wiki-plan-review-and-lock.md`.
- **Prior state:** No prior locked review file for `colors`; wiki meta had no lifecycle markers. The current corpus gap audit still listed two blocker concepts for this article: `запитання про колір` and `різниця між синім і блакитним` (`data/corpus_audit/gap_categories.md`).
- **Fixes applied:** review-and-lock pass on 2026-04-23. Main fixes:
  1. Added lock metadata to the wiki meta block.
  2. Closed the missing `Якого кольору?` gap with a dedicated step and writer-usable Q/A pattern.
  3. Reworked the `синій` / `блакитний` section into a concrete A1 contrast built from ready contexts (`синє море`, `блакитне небо`) instead of an abstract palette discussion.
  4. Removed the false statement that `голубий` is a Russianism. Verification: `голубий` is attested in both VESUM and СУМ-11 in the main checkout dictionaries.
  5. Added fixed collocations for appearance (`карі очі`, `русяве волосся`, `сиве волосся`) so the writer does not default to literal English-style color transfer.
  6. Added a new textbook-style exercise that drills `Якого кольору?` plus those fixed collocations directly.

## Dimension scores

| # | Dimension | Score | Evidence |
|---|-----------|-------|----------|
| 1 | Factual accuracy | **9/10** | The most important factual defect in the prior state was removed: the wiki no longer mislabels `голубий` as a Russianism. The active teaching contrast remains `синій` / `блакитний`, but the review pass verified `голубий` as an attested Ukrainian word in both VESUM and СУМ-11. Existing source-backed claims remain tied to the sidecar `colors.sources.yaml`; the new writer guidance is constrained to verified pedagogical framing rather than new unsourced lexical folklore. |
| 2 | Ukrainian language quality | **9/10** | No Russianisms in the instructional prose after the fix. The revised text distinguishes agreement (`червоний/червона/червоне/червоні`), lexical contrast (`синій` / `блакитний`), collocation (`карі очі`, `русяве волосся`, `сиве волосся`), and orthography of compound colors (`світло-зелений`, `темно-синій`) cleanly. The locked version removes the false Russicism label and therefore reduces, rather than increases, lexical noise. |
| 3 | Decolonization | **9/10** | The article still explicitly forbids "explain it via Russian" framing. The revised version is stronger because it no longer invents a decolonization claim where none exists: it keeps the Ukrainian-centered A1 choice (`синій` / `блакитний`) without falsely branding another attested Ukrainian word as foreign. This is the right decolonial move: precise, evidence-based, and non-russocentric. |
| 4 | Completeness | **9/10** | The two blocker concepts named by the corpus audit are now explicitly covered: the article has a standalone `Якого кольору?` step and a concrete `синій` / `блакитний` teaching step. In addition, the new collocation step closes a writer-facing gap that previously would have forced invention when describing eyes or hair. A writer can now derive the module's sequence, key chunks, and likely L2 pitfalls from this wiki without filling in missing pedagogy on their own. |
| 5 | Actionable guidance | **9/10** | The locked wiki now gives directly liftable material: question-answer frames, ready-made context pairs, fixed collocations, and a dedicated mini-dialogue exercise. The article no longer asks the writer to infer how to turn color theory into A1 classroom language. The new Step 3 and the new exercise are especially strong here because they can be copied almost verbatim into learner-facing content. |

**Overall: 9/10 — LOCKED.**

## What "LOCKED" means for this artifact

- All 5 rubric dimensions are at 9 or above.
- The blocker concepts named for `a1/colors` in `data/corpus_audit/gap_categories.md` have been closed in the wiki itself.
- The wiki meta block now carries `lifecycle: locked`, `last_reviewed`, and `reviewed_by`.
- The paired plan has been brought into alignment and marked `lifecycle: locked`.
- This article is now a stable input for A1 scale-batch writing unless one of the unlock triggers below happens.

## Unlock triggers

1. A native-speaker content review flags one of the new fixed collocations or the `голубий` treatment as pedagogically misleading.
2. The paired plan drifts away from the wiki again, especially around `Якого кольору?`, the `синій` / `блакитний` contrast, or the appearance collocations.
3. The sources sidecar is regenerated in a way that drops support for a currently cited claim.
4. A systemic audit finds a new color-specific defect class not checked in this pass.

## Residual non-blockers

- The wiki mentions `помаранчевий` / `жовтогарячий` and `коричневий` / `брунатний` as synonym pairs, but it does not force a preference ranking between them for A1 production. That is acceptable at lock time because the module's active production load is still concentrated on the smaller core palette.
- The article deliberately avoids teaching comparative forms of color adjectives at A1. This is a curriculum-boundary choice, not a gap.
