# what-is-it-like (L2-UK-EN A1/M09) — LOCKED review

- **File reviewed:** `wiki/pedagogy/a1/what-is-it-like.md`
- **Review date:** 2026-04-23
- **Reviewer:** claude-opus-4-7, effort=xhigh (adversarial self-review, post-fix)
- **Rubric:** 5-dimension wiki rubric (factual / language / decolonization / completeness / actionable), target ≥9 on each. See `docs/best-practices/wiki-plan-review-and-lock.md` for the full rubric and procedure.
- **Prior state:** No prior locked review file existed. The wiki had three substantive intake gaps: (1) no lifecycle metadata in the wiki-meta block; (2) no `Типові помилки L2` section despite adjectives being one of the highest-density Russianism interference zones in everyday Ukrainian (taste, color, character — every base attribute has a near-homophone Russian counterpart); (3) Step 5 (oblique cases) and the vocabulary block were under-bounded — a writer reading them could plausibly drift into teaching the full тверда/м'яка group declension paradigm at A1.
- **Fixes applied:** This PR — see the diff against `wiki/pedagogy/a1/what-is-it-like.md`.

## Dimension scores

| # | Dimension | Score | Evidence |
|---|-----------|-------|----------|
| 1 | Factual accuracy | **9/10** | Every claim sourced via inline `[S1]–[S6]` keyed to the sidecar `what-is-it-like.sources.yaml`. The new `Типові помилки L2` table is the heaviest factual addition; every right-column item is VESUM-verified (batch `mcp__sources__verify_words` — `смачний`, `жовтий`, `чорний`, `червоний`, `правильний`, `поганий`, `розумний`, `лінивий` all attested) and every left-column item belongs to one of four explicitly-named categories: (a) VESUM-absent (`вкусний`, `жолтий`, `черний`, `ленивий`); (b) VESUM-present but `arch`-tagged (`умний` — clarified per Codex AC-3 finding); (c) СУМ-11 розм. (`плохий`); (d) attested with different Ukrainian semantics — paronym (`красний` = «гарний, прекрасний» нар.-поет. per СУМ-11; `вірний` = «loyal/faithful»; `любий` = «дорогий, милий»). The remaining soft spot is that the `розм.` mark on `плохий` makes it a "preferred form" recommendation rather than a hard wrong-form deduction — this is intentional and stated in the table's note. |
| 2 | Ukrainian language quality | **9/10** | Zero Russianisms in instructional prose. The four-check sweep (Russianisms / Surzhyk / calques / paronyms) is now made explicit by the new table, which separates structural patterns: pure Russianism (вкусний, жолтий, черний, ленивий), colloquial drift (плохий), paronymic interference (красний, вірний, любий). The decolonization-section bullet 3 was rewritten to reference this table rather than naming only two examples. New writer-note pins `радий/рада/раді` (long-form predicative, never the short `рад` form per the dimension-2 fail-mode "short forms borrowed from Russian"). |
| 3 | Decolonization | **9/10** | The four-point decolonization section was already strong (no Russian-comparative explanations, attention to /ɣ/ in `-ого`, native-Slavic origin framing). The lock pass tightened bullet 3: instead of two example pairs, it now points to the full audited Surzhyk table — which itself names Russian explicitly as the calque source for each pair (`рос. *вкусный*`, `рос. *жёлтый*`, `рос. *чёрный*`, `рос. *красный*`, etc.) rather than masking the asymmetry. The structural choice — Ukrainian-on-its-own-terms first (Кроки 1-4, vocabulary block), prophylactic table second — matches the same pedagogical sequence at-the-cafe locked at. |
| 4 | Completeness | **9/10** | Intake gap 1 (lifecycle metadata) closed. Intake gap 2 (no L2-error table) closed via the new 9-row `Типові помилки L2` section. Intake gap 3 (under-bounded oblique-case scope) closed via the new "Межа A1 (для автора)" callout under Step 5 plus the new writer-note after Словниковий мінімум, which together pin the three permitted formats (question-answer chunk in nominative; predicative with omitted «бути»; pre-agreed adjective+noun chunk) and explicitly forbid full paradigm teaching, short adj forms, productive comparatives, and instrumental case. Step 2's soft-group treatment (синій) remains intentionally light — the plan defers full soft-group work to М10 «Кольори», and the wiki now matches that boundary. |
| 5 | Actionable guidance | **9/10** | The wiki is now directly liftable: the writer note enumerates the three permitted adj formats with model phrases (`Який стіл? — Великий стіл.` / `Стіл новий.` / `нова книга`); Step 5's "Межа A1" callout names the maximum allowed depth (2-3 illustration examples, no productive); the new exercise 5 mirrors the table 1:1 so the writer has a working drill template. Every item in the new table has a "Примітка" column identifying the exact source/diagnosis (VESUM-absent, СУМ-11 розм., or paronym with native-Ukrainian sense), so the writer is not guessing at the rationale. |

**Overall: 9/10 — LOCKED.**

## What "LOCKED" means for this artifact

- All 5 dimensions are at ≥9.
- The three intake gaps (missing lifecycle metadata, missing `Типові помилки L2`, under-bounded oblique-case + writer scope) have been closed in the wiki body itself.
- Every new vocabulary item added for the lock pass was VESUM-verified (`mcp__sources__verify_words` batch) and cross-checked against СУМ-11 / Антоненко-Давидович for calque/paronym attestation before commit.
- The wiki meta block now carries `lifecycle: locked`, `last_reviewed: 2026-04-23`, and `reviewed_by`.
- The paired plan has been brought into alignment and marked `lifecycle: locked` (see PR body, AC-2).
- This wiki is cleared as a clean input for A1 module build (a1-009) per `docs/best-practices/wiki-plan-review-and-lock.md`.

## Unlock triggers

This LOCKED state should be revisited if any of the following happen:

1. A native-speaker reviewer (Teacher Tetiana / Teacher Alona) flags a left- or right-column item in the new `Типові помилки L2` table — authoritative override of the dictionary-based verification. Especially the colloquial-vs-Russianism call on `плохий` (СУМ-11 розм.) — a teacher may prefer a stricter framing.
2. The module build (what-is-it-like A1/M09) surfaces a gap the wiki did not anticipate — file as an issue, do a fresh review round, republish with incremented `last_reviewed` date.
3. The `culture/decolonization/surzhyk-and-russianisms` wiki — to which this wiki links — changes its framing in a way that contradicts this table.
4. VESUM / СУМ-11 / Антоненко-Давидович update or re-label any of the cited forms (e.g. if `плохий` is reclassified from `розм.` to `діал.` or vice-versa).
5. A future wiki recompile silently removes the `Типові помилки L2` section, the writer note, or the "Межа A1" callout while leaving `lifecycle: locked` in metadata (ghost-lock).

## Residual non-blockers (documented, not blocking)

- The vocabulary section continues to use the legacy ★/★★/★★★ frequency tier marking inherited from the gemini-2.5-pro generation. This is a wiki-corpus convention used elsewhere (e.g. at-the-cafe vocab table style), not a defect for this slug.
- The source sidecar `wiki/pedagogy/a1/what-is-it-like.sources.yaml` still uses the generic `type: unknown` convention, like many other wiki sidecars in the repo (including the locked at-the-cafe sidecar). The new dictionary-backed claims (VESUM / СУМ-11 / Антоненко-Давидович) in the L2-error section are not separately registered in the sidecar — same trade-off accepted by the at-the-cafe lock pass. This is corpus-hygiene debt that should be addressed by a sidecar-schema upgrade across all locked wikis, not by piecemeal additions on individual slugs.
- The Step 5 oblique-case callout is intentionally minimal at A1; a more detailed treatment lives in the planned `pedagogy/a1/nominative-case` and the (future) A2 `adjective-declension` wikis. This is a scope choice, not a completeness deduction.

## Cross-agent adversarial review (Codex)

A cross-agent adversarial review was run via `ai_agent_bridge ask-codex` (task-id `what-is-it-like-adv-review`, message #425). Findings and resolutions:

- **BLOCKER:** plan drilled only 7/9 wiki Surzhyk pairs, contradicting "1:1 mirror" lock claim → **fixed** by adding `красний/червоний` and `ленивий/лінивий` rows to the plan's `activity_hints` Surzhyk drill, updating the new objective to enumerate all 9 pairs, and amending the changelog.
- **BLOCKER:** Codex flagged `М08`/`М09`/`М10` references in plan prose as #1392 D1 (Latin homoglyphs). Verification: characters were Cyrillic `М` (U+041C), not Latin homoglyphs — D1 strict reading not violated. However the underlying spirit (raw module IDs in writer-facing prose on a `lifecycle: locked` plan) was a fair signal → **fixed** by rewriting the objective and content_outline points to use natural Ukrainian phrasing ("з попереднього модуля «Речі мають рід»", "у наступному модулі «Кольори»") while keeping numeric module IDs only in the structured `connects_to` and `prerequisites` fields.
- **MEDIUM:** `умний` was loosely classified as "VESUM peripheral" in the wiki table note — Codex confirmed VESUM tags it `arch` → **fixed** in both the wiki section intro and the table row; LOCKED review dimension-1 evidence now names all four left-column categories (absent / arch / розм. / paronym) explicitly.
- **MEDIUM:** rubric doc `wiki-plan-review-and-lock.md` lacks explicit #1392 D1/D5/D7 checklist bullets — out-of-scope for this slug PR; recorded as feedback for the rubric maintainer (not modified here to avoid drift between rubric and applied template within the same PR).
- **MEDIUM:** new dictionary-backed claims not traceable in the sources sidecar — accepted as residual, identical to the at-the-cafe lock pass precedent; flagged for a corpus-wide sidecar-schema upgrade.
- **NIT:** `лінивий/ленивий` row formatting differed from other rows → **fixed** to match the standard sentence-pair format (`Ленивий учень` / `Лінивий учень`).
