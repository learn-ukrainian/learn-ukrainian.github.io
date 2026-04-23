# checkpoint-first-contact (L2-UK-EN A1/M007) — LOCKED review

- **File reviewed:** `wiki/pedagogy/a1/checkpoint-first-contact.md`
- **Review date:** 2026-04-23
- **Reviewer:** claude-opus-4-7, effort=xhigh (adversarial self-review, post-fix)
- **Rubric:** 5-dimension wiki rubric (factual / language / decolonization / completeness / actionable), target ≥9 on each. See `docs/best-practices/wiki-plan-review-and-lock.md` for the full rubric and procedure.
- **Prior state:** No prior review on record (first review pass). Wiki had been compiled 2026-04-21 by `gemini-2.5-pro` but had not been adversarially reviewed for Surzhyk / calque / pragmatic defects or for alignment with its companion plan (`curriculum/l2-uk-en/plans/a1/checkpoint-first-contact.yaml`).
- **Template followed:** `at-the-cafe` (PR #1415). This review-and-lock pass follows the procedure documented in the rubric with `at-the-cafe-review-LOCKED.md` as the worked example.

## Dimension scores

| # | Dimension | Score | Evidence |
|---|-----------|-------|----------|
| 1 | Factual accuracy | **9/10** | Every claim sourced via `[Sn]` keys into `checkpoint-first-contact.sources.yaml` (S1–S10, Ukrainian school-textbook chunks). The new Step 6 ("Чекпойнт A1.1") and the "Типові помилки L2" table draw on a combination of textbook pedagogy (self-assessment pattern [S1, S5]) and dictionary authority (VESUM + СУМ-11 for each right-column token; СУМ-11's explicit "розм./заст./діал." labels for `фамілія`, and "глава католицької церкви" sole sense for `папа`). One soft spot: the Ви/ти register guidance in Step 6 is pedagogical judgement rather than a single citable reference — this is intentional and inline-justified ("учень має засвоїти як дихотомію"). |
| 2 | Ukrainian language quality | **9/10** | Zero Russianisms in instructional text after the fix. Key fix: `Мене звать...` at line 33 replaced with `Мене звати...` (standard full infinitive) + inline note explaining why the VESUM-attested short form `звать` is withheld at A1. The new "Типові помилки L2" section explicitly teaches 8 A1.1-specific Russianism / calque / borrowing pairs (`Здрастуйте → Добрий день`, `Пока → До побачення`, `Папа → Тато`, `Моє ім'я є X → Мене звати X`, `Я є студент → Я студент`, `Я маю 25 років → Мені 25 років`, `фамілія → прізвище`, plus a Ви/ти-aware residual note). Four-check rubric passed: Russianism (папа / здрастуйте / пока), Surzhyk (шо/що — not relevant at this slug), Calque (моє ім'я є X / я маю N років — explicitly flagged), Paronym (фамілія vs прізвище) all audited. |
| 3 | Decolonization | **9/10** | Existing decolonization section preserved in full: no Russian phonetic comparisons, emphasis on Ukrainian-unique letters (`І`, `Ї`, `Ґ`) with Soviet-era repression + restoration framing, historical figures presented as Ukrainian-Rus' rather than Russian-imperial (`князь Володимир`, `гетьман Богдан Хмельницький`), culturally Ukrainian example corpus (`Львів`, `Канів`, `Дніпро`, `Десна`, Shevchenko, Lesya Ukrainka, Franko). The new "Типові помилки L2" table names Russian explicitly as the source of each русизм (e.g. "рос. *здравствуйте*", "рос. *папа*") — teaching the asymmetry rather than hiding it. Residual note on `Я з Росії / я русский` explicitly declines to rehearse Russian identity as an A1.1 role-model template (the module's self-introduction scripts are scoped to the learner's own country of origin). |
| 4 | Completeness | **9/10** | Gap 1 (checkpoint framing absent) closed via new **Step 6: Чекпойнт A1.1 — інтеграція модулів №1–6** — gives integration principle, format, minimal integration monologue, self-assessment pattern, and Ви/ти register guidance. Gap 2 (no A1.1-specific Surzhyk / calque table) closed via new "Типові помилки L2 (самопрезентація)" section with 8 verified pairs. Gap 3 (integration vocabulary absent from word minimum) closed via new "Лексика інтеграції" sub-list (`знайомство`, `професія`, `національність`, `походження`, `родина`, `сім'я`) and added politeness formulas (`Вітаю`, `Дуже приємно`, `Мені теж`). Gap 4 (no textbook example of an integration checkpoint dialogue) closed by rewriting **Приклад 1** from a minimal 6-line name-exchange into a full checkpoint-integration dialogue that covers all A1.1 objectives. New **Приклад 5** drills the "Типові помилки L2" pairs in the format the writer will actually use. |
| 5 | Actionable guidance | **9/10** | Step 6 gives an explicit minimal-viable integration monologue the writer can lift directly: `— Привіт! Мене звати [ім'я]. Моє прізвище [прізвище]. Я з [країна]. Я [національність]. Я [професія]. У мене є мама, тато і [брат / сестра]. Моя мама — [професія], мій тато — [професія]. Дуже приємно познайомитися!`. The writer-note after the vocabulary list pins `Мене звати [ім'я]`, `Я з [країна]`, `Я [професія]`, `Мені [N] років` as indivisible chunks — preventing A1 over-teaching of adjective declension, instrumental of `звати`, or dative+genitive age construction. Приклад 1 is the full checkpoint-integration dialogue in ti-register; Приклад 5 is the A1.1 Surzhyk drill. Every entry in the "Типові помилки" table has a "Примітка" column naming the exact authority (VESUM form status, СУМ-11 sense label, or named calque source). |

**Overall: 9/10 — LOCKED.**

## What "LOCKED" means for this artifact

- All 5 dimensions at ≥9.
- The 4 gaps identified at intake (no checkpoint framing, no A1.1-specific Surzhyk table, no integration vocabulary, no integration dialogue example) all closed.
- Every new vocabulary item is VESUM-verified (`професія`, `національність`, `походження`, `знайомство`, `приємно`, `Вітаю`, `теж`, `тато`, `мама`, `родина`, `сім'я`, `прізвище`).
- Every left-column Russianism / calque in the "Типові помилки L2" table has a documented authority (VESUM form status + СУМ-11 sense label where applicable).
- Meta block carries `lifecycle: locked`, `last_reviewed: 2026-04-23`, `reviewed_by: claude-opus-4-7-xhigh`.
- This wiki is cleared as a clean input for A1 scale-batch module builds per `docs/best-practices/wiki-plan-review-and-lock.md`.

## Unlock triggers

This LOCKED state should be revisited if any of the following happen:

1. The module build (checkpoint-first-contact A1/M007) surfaces a gap the wiki did not anticipate — file as an issue, do a fresh review round, republish with incremented `last_reviewed` date.
2. A native-speaker reviewer (Teacher Tetiana / Teacher Alona) flags a left- or right-column item in the "Типові помилки L2" table — authoritative override of the dictionary-based verification.
3. The `culture/decolonization/surzhyk-and-russianisms` wiki — which this wiki links to — changes its framing in a way that contradicts this table (e.g. re-classifies `спасибі` as neutral, which would affect the general framing of this wiki's note set).
4. VESUM / СУМ-11 updates retire or re-label any of the cited forms, specifically `фамілія` (if the розм./заст./діал. labelling is changed) or `папа` (if the family sense is added to СУМ-11 as standard).
5. Phase A1.1 module ordering changes (e.g. the upstream modules #1–#6 are renumbered or split) — the integration step's module-reference list would need updating.

## Residual non-blockers (documented, not blocking)

- The Step 6 dialogue in Приклад 1 has a minor register-switch that a stricter reviewer could flag: Оксана introduces herself with `Я з Канади, але я українка` — at A1.1, this mixes origin (`з Канади`) with ethnicity (`українка`) in one turn. The phrasing is pedagogically intentional (checkpoint drills both at once) and is accompanied by the Step-6 Ви-vs-ти note, but a module-level review pass may want the writer to split these across two turns for cleaner input. Not a wiki defect.
- `Вітаю!` is listed both as a standalone greeting and as a replacement for `Здрастуйте!` in the Surzhyk table. In modern Ukrainian, `Вітаю!` is also the standard congratulation ("Congratulations!"). The wiki does not disambiguate this dual function — relying on context. Safe to leave as-is; a future module on congratulations can re-attend this.
- The Step 6 self-assessment question list (5 items) is a minimum set. A more ambitious module could add a reading-aloud micro-assessment mapped to Ступінь 4 (йотовані голосні). Not a wiki defect — that is a module-design choice.
- S1–S10 in `checkpoint-first-contact.sources.yaml` have `type: unknown`. This is cosmetic and consistent with the rest of the a1 sidecars; it does not affect factual scoring because the `[Sn]` keys all resolve to textbook chunks. A future sidecar-cleanup pass could enrich these without reopening the lock.
