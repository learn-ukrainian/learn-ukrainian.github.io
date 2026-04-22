# my-family (L2-UK-EN A1/M06) — LOCKED review

- **File reviewed:** `wiki/pedagogy/a1/my-family.md`
- **Review date:** 2026-04-23
- **Reviewer:** claude-opus-4-7, effort=xhigh (adversarial self-review, post-fix)
- **Rubric:** 5-dimension wiki rubric (factual / language / decolonization / completeness / actionable), target ≥9 on each. See `docs/best-practices/wiki-plan-review-and-lock.md` for the full rubric and procedure.
- **Prior state:** 9.2/10 on the 2026-04-06 pre-recompile version (`my-family-review-r4.md`, Gemini adversarial). The current (2026-04-21) recompile regenerated a cleaner but **shorter** version of the wiki and silently dropped several items that the r4 round had explicitly added (`кіт`/`собака` in vocab, patronymics sequence step, dedicated L2-error section, `свій` writer-note, married-form guidance). This recompile-drift is exactly the risk the rubric's "AC-1 checklist step 1" warns about.
- **Fixes applied:** see the PR diff (branch `agent/scale-my-family`). Summary below under "Gaps closed".

## Dimension scores

| # | Dimension | Score | Evidence |
|---|-----------|-------|----------|
| 1 | Factual accuracy | **9/10** | Every claim in the new sections (Крок 6 patronymics, "Типові помилки L2" table, writer-note) is traceable. Patronymic suffix inventory `-ович/-йович/-івна/-ївна` verified against VESUM (`Іванович`, `Сергійович`, `Петрівна`, `Сергіївна` all present). The seven Surzhyk/calque pairs in the table are each annotated with a VESUM-derived verification note — the right-hand lemma verified present; the left-hand form verified **absent from VESUM** OR marked `slang`/restricted (`дєдушка: slang`, `муж`: single `v_naz` form without full paradigm). The `папа`/`тато` pair is deliberately **excluded** from the error table (it would be a defect by the rubric's evidence rule since VESUM lists `папа` untagged) and instead handled in a separate writer-note as a register-preference issue — not dictionary-wrong, only pedagogically dispreferred. One soft spot: Крок 6's sociolinguistic claim about "always `ім'я + по батькові + Ви` at work/school/state offices" is general cultural knowledge, not tied to a specific S-source — this is intentional and acknowledged in the same prose. |
| 2 | Ukrainian language quality | **9/10** | Zero Russianisms in instructional text. Every right-column token in the 7-row "Типові помилки L2" table verified in VESUM (`data/vesum.db`); every left-column token verified **absent** from VESUM, OR present only with `slang`/archaic tagging. The framing of `папа`/`тато` as a register-preference writer-note (not a table row) is the correct rubric-aligned treatment — putting a VESUM-untagged form under «НЕПРАВИЛЬНО (Суржик / калька)» would overreach and falsely frame a pedagogy/register preference as a dictionary-backed error. Four separate checks per rule #2 of `ukrainian-linguistics.md`: no Russianisms in prose, no Surzhyk (shown as the *object* of prevention, not embedded in the text), no untagged calques, no paronym confusion. |
| 3 | Decolonization | **9/10** | The existing four decolonization principles (no Russian comparison, `ти`/`Ви` on Ukrainian terms, shared-origin words not framed as "like Russian", phonetic independence) remain in force. Крок 6 strengthens decolonization by explicitly naming `-івна/-ївна` as systematically distinct from Russian `-овна` ("принципово" + "систематична, а не випадкова відмінність"). The new Surzhyk table names the Russian source of each calque explicitly in the "Примітка" column, teaching the asymmetry rather than hiding it — aligned with the at-the-cafe template. |
| 4 | Completeness | **9/10** | All documented gaps from r3/r4 now closed: pets (`кіт`, `собака`) added to vocab per r3 fix; patronymics `-ович/-йович/-івна/-ївна` fully specified per r3 fix; dedicated "Типові помилки L2" section with 8 family-specific pairs (absent in the r4 recompile) added per the at-the-cafe template; `свій` writer-awareness note added (r4 guidance). A writer working from this wiki now has: sequence (6 kroky), vocab list with pets + name/surname/patronymic, L2 error table with diagnostic pairs, per-module drill example. The one residual gap — `чоловік` has the double sense "man / husband" with no disambiguation note — is a minor grammar point that belongs in a dedicated `grammar/a1/noun-semantics` wiki, not here. |
| 5 | Actionable guidance | **9/10** | The writer can lift directly: Крок 6's three-bullet breakdown (формування → коли вживається → А1-очікування) gives a ready-made outline for a single learning objective; the "Типові помилки L2" table is directly drilled by new exercise 5 in "Приклади з підручників" (exactly mirroring the at-the-cafe exercise-3 pattern: 7 items matching the 7 transferable pairs from the table); exercise 6 gives a recognition-only drill for patronymics that respects the A1 scope; the post-vocabulary writer-note pins the chunk-level treatment of `у мене є` / `Це моя...` / patronymics, preventing the writer from over-teaching genitive pronoun declension at A1. |

**Overall: 9/10 — LOCKED.**

## What "LOCKED" means for this artifact

- All 5 dimensions at ≥9.
- All documented gaps from r3 (2026-04-05) and r4 (2026-04-05, post-fix) have been closed or explicitly addressed.
- Every new vocabulary item is VESUM-verified. Every Surzhyk pair has its left-column token checked against VESUM for absence or restrictive tagging.
- Meta block carries `lifecycle: locked` + `reviewed_by` + `last_reviewed`.
- The wiki is aligned with the at-the-cafe (#1412) template: same section order, same writer-note placement, same Surzhyk-table convention with "Примітка" column, same per-slug drill exercise.

## Unlock triggers

This LOCKED state should be revisited if any of the following happen:

1. The module build (my-family A1/M06) surfaces a gap the wiki did not anticipate — file as an issue, do a fresh review round, republish with incremented `last_reviewed` date.
2. A native-speaker reviewer (Teacher Tetiana / Teacher Alona) flags a left- or right-column item in the Surzhyk table — authoritative override of the dictionary-based verification.
3. The `culture/decolonization/surzhyk-and-russianisms` wiki — which this wiki links to — changes its framing in a way that contradicts this table.
4. VESUM / СУМ-11 updates retire or re-label any of the cited forms (particularly: `папа` status, `дядьо` as lemma for `дядя`).
5. A future recompile silently drops the new sections — the wiki compiler's idempotency vs. the review-locked state is the same recompile-drift risk documented in this file's "Prior state" paragraph. If the meta block's `lifecycle: locked` is preserved but the body shrinks, the wiki is no longer locked in fact even if it claims to be.

## Residual non-blockers (documented, not blocking)

- `папа` vs `тато` is **not** in the 7-row error table — it is only a writer-note about register preference. This was an explicit fix after the AC-3 cross-agent adversarial pass (Codex, 2026-04-23) flagged the earlier 8-row version as overreach: VESUM lists `папа` without restrictive tags, so framing it as literary-wrong violated the rubric's evidence rule. The current treatment says "use `тато` in teaching materials, but do not mark `папа` as incorrect" — aligned with what the rubric asks for.
- `дядя` / `тьотя` are not included in the table even though they were considered. Reason: VESUM treats `дядя` as a valid word-form (lemma `дядьо`) and `тьотя` as a valid lemma, both without restrictive tags. Framing them as Russianisms without a style-guide flag would contradict the rubric's "do NOT add if not verifiable in VESUM + СУМ-11" rule applied in reverse. Writer should steer toward `дядько` / `тітка` through positive modeling, not through a pair entry here.
- The wiki does not yet cover the reflexive possessive `свій` with a worked example — only a single writer-note sentence. This is deliberate: `свій` production is a B1-level skill per PULS CEFR, and at A1 the writer should not drill it. If a future module-build at A1 needs more guidance, this wiki can add a dedicated section in a re-lock pass.
