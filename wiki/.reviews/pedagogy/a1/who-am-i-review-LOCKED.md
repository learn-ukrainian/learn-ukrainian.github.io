# who-am-i (L2-UK-EN A1/M05) — LOCKED review

- **File reviewed:** `wiki/pedagogy/a1/who-am-i.md`
- **Review date:** 2026-04-23
- **Reviewer:** claude-opus-4-7, effort=xhigh (review-and-lock per `docs/best-practices/wiki-plan-review-and-lock.md`)
- **Rubric:** 5-dimension wiki rubric (factual / language / decolonization / completeness / actionable), target ≥9 on each. Template applied: `at-the-cafe` (PR #1412, `wiki/.reviews/pedagogy/a1/at-the-cafe-review-LOCKED.md`).
- **Prior state:** No formal wiki review existed (wiki last compiled 2026-04-21). Fresh review + lock in one round, plus one Codex adversarial-review round that surfaced a BLOCKER on sources-sidecar traceability (fixed) and two MEDIUMs on plan grammar↔objectives mapping and Exercise 5 item count (fixed).
- **Fixes applied:** see branch `claude/scale-who-am-i-review-and-lock` and the associated PR.

## Gaps identified on intake (vs. the locked at-the-cafe template)

1. **No Surzhyk / calque table** (`Типові помилки L2`). The topic "introductions + self-presentation" is one of the most Russianism-prone slices at A1 (the Russian `меня зовут`, `очень приятно`, `папа`, `жена`, `врач` calques + non-feminitive professions). The wiki had zero learner-facing defenses for this.
2. **Vocabulary not in table format.** The locked peer (at-the-cafe) uses a `Українською | Англійською | Рівень` table so the module writer gets glosses. who-am-i only had a Ukrainian-only bulleted list with star frequencies — writer had to translate each item.
3. **Chunk guidance missing.** The locked peer pins `велику каву`, `Тут, будь ласка`, etc. as indivisible chunks, preventing premature grammar teaching. who-am-i had no equivalent note, creating risk that the writer would over-teach `звати` conjugation, genitive after `з/зі`, or the full accusative pronoun paradigm at A1.
4. **Echo-question pattern (`А тебе?` / `А вас?`) missing.** The paired plan uses `А тебе?` in Dialogue 1, but the wiki did not teach this pattern nor warn against the `А у тебе?` trap (#1392 Defect 2 pattern: context-blind reciprocal that drags in unwanted genitive grammar).
5. **Feminitives not addressed as a decolonization line.** Professions (`лікарка`, `вчителька`, `інженерка`, `програмістка`, `авторка`) are one of the most visible markers of "Ukrainian on its own terms" — Russian has no productive feminitive pattern for professions. The old decolonization section did not name this.
6. **Missing `lifecycle` / `last_reviewed` / `reviewed_by` in wiki-meta.**

## Fixes applied

1. Added new **Типові помилки L2 (Common L2 Errors — introductions-specific Surzhyk)** section with seven pairs, fully VESUM-verified [S8] and (where semantic trap matters) СУМ-11-verified [S9]:
   - `папа` (father) → `тато` — СУМ-11 confirms `папа` = "pope" only.
   - `жена` → `дружина` — `жена` absent from VESUM.
   - `врач` → `лікар` / `лікарка` — `врач` absent from VESUM.
   - `ізвиніть` → `вибачте` / `пробачте` — `ізвиніть` absent from VESUM.
   - `спасібо` → `спасибі` / `дякую` — `спасібо` absent from VESUM.
   - `тоже` → `теж` / `також` — `тоже` absent from VESUM.
   - Masculine generic for female person → feminitive (`інженерка`, etc.) — decolonization framing.
2. Converted vocabulary section to the `Українською | Англійською | Рівень | Джерело` table format, 28 entries + writer-note pinning 5 indivisible chunks (`Мене звати + Ім'я`, `Як тебе/вас звати?`, `Я з + country`, `Дуже приємно`, `А тебе? / А вас?`).
3. Added echo-question pattern to **Крок 1**, explicitly warning against the `А у тебе?` reciprocal (#1392 Defect 2: genitive-after-preposition should not surface at A1).
4. Added feminitives writer-instruction to **Крок 6** and new decolonization point **#5**.
5. Added new **Exercise 5** in "Приклади з підручників" that drills all seven Surzhyk pairs in the minimal context of self-introduction (mirrors at-the-cafe's Exercise 3).
6. Added `last_reviewed: 2026-04-23`, `lifecycle: locked`, `reviewed_by: claude-opus-4-7-xhigh` to wiki-meta block.
7. Extended `wiki/pedagogy/a1/who-am-i.sources.yaml` with dictionary authorities **S8 (VESUM)** and **S9 (СУМ-11)**, cited inline at every claim site in Крок 6, Декол. #5, the "Типові помилки L2" table, and Exercise 5. Sidecar now supports the LOCKED review's "every claim sourced" language (fixed the Codex-flagged BLOCKER on sidecar traceability).
8. Added two `grammar:` items to the plan to mirror the two new objectives introduced by this pass (echo-reciprocal chunk + normative-contrast pattern), so `grammar` ↔ `objectives` remain bidirectionally mapped.

## Dimension scores

| # | Dimension | Score | Evidence |
|---|-----------|-------|----------|
| 1 | Factual accuracy | **9/10** | Every S1–S7 textbook citation preserved; every new claim backed by VESUM (`mcp__sources__verify_word` / `verify_words`) and СУМ-11 (`mcp__sources__search_definitions`). `папа`-as-pope-only was verified via СУМ-11 directly. The one soft spot is that the feminitive callout draws on VESUM lexical evidence rather than a single textbook citation (the L1 textbook corpus is silent on feminitive ideology), and this is acknowledged inline — the claim is "these forms exist in VESUM and Russian has no productive feminitive pattern," both of which are verifiable. |
| 2 | Ukrainian language quality | **9/10** | Zero Russianisms in instructional text. The new "Типові помилки L2" table *explicitly shows* seven introductions-specific Russianism/calque pairs with cited authority. All right-column tokens (and their requested inflected forms `папу`, `тата`, `інженерка`, etc.) verified in VESUM. All left-column tokens confirmed absent from VESUM or flagged semantically via СУМ-11. Echo pattern `А тебе?` preferred over `А у тебе?` prevents the #1392 Defect 2 genitive-drag pattern. |
| 3 | Decolonization | **9/10** | Old section (4 points) preserved; new point #5 addresses feminitives explicitly as a distinctly-Ukrainian feature (Russian lacks productive feminitive morphology for professions). Surzhyk table frames each Russianism with *which* Russian word it calques — teaching the asymmetry rather than hiding it. The `А у тебе?` avoidance note inside Крок 1 doubles as decolonization (it's a direct Ukrainian idiom vs. a Russian-model reciprocal). |
| 4 | Completeness | **9/10** | Gap 1 (Surzhyk table) closed via new section + Exercise 5. Gap 2 (vocabulary table) closed via table rewrite + writer-note. Gap 3 (chunk guidance) closed via writer-note pinning 5 A1 chunks. Gap 4 (echo pattern) closed in Крок 1. Gap 5 (feminitives) closed via Крок 6 addition + decolonization #5. A writer using this wiki now has explicit guidance on: chunk boundaries, reciprocal echo pattern, feminitives as primary form for a female learner, and café-equivalent Surzhyk drill. |
| 5 | Actionable guidance | **9/10** | Every example is now directly liftable: four original exercises from the 5-class textbook corpus, plus a new Exercise 5 that drills all seven Surzhyk pairs from the new table. Writer-note inside "Словниковий мінімум" enumerates five indivisible chunks (no adjective declension, no `з+gen` analysis, no full accusative pronoun paradigm) so the writer cannot over-teach. Крок 1's echo-pattern note is a literal sentence the writer can paste into dialogue. |

**Overall: 9/10 — LOCKED.**

## What "LOCKED" means for this artifact

- All 5 dimensions at ≥9.
- All six intake gaps are closed.
- Every new vocabulary item and Surzhyk right-column token is VESUM-verified (see `mcp__sources__verify_words` evidence in the PR body).
- Every Surzhyk pair in the new table has a documented authority (VESUM absence proof, СУМ-11 semantics, or feminitive-morphology argument).
- Meta block carries `lifecycle: locked` + `reviewed_by` + `last_reviewed`.
- This wiki is cleared as a clean input for the module build of L2-UK-EN A1/M05.

## Unlock triggers

This LOCKED state should be revisited if any of the following happen:

1. The module build (`a1-005`) surfaces a gap the wiki did not anticipate — file as an issue, do a fresh review round, republish with incremented `last_reviewed`.
2. A native-speaker reviewer (Teacher Tetiana / Teacher Alona) flags a left- or right-column item in the new Surzhyk table — authoritative override of dictionary-based verification.
3. The `culture/decolonization/surzhyk-and-russianisms` wiki (once created) re-frames the feminitive question or the `папа` / `жена` / `врач` calques in a way that contradicts this table.
4. VESUM / СУМ-11 updates retire or re-label any cited form.
5. The wiki-plan drift check flags a new mismatch between this wiki's content and the locked plan (`curriculum/l2-uk-en/plans/a1/who-am-i.yaml`).

## Residual non-blockers (documented, not blocking)

- `німеччина` and proper nouns like `Штати`, `Україна` return no hit in case-sensitive VESUM verification — this is a VESUM proper-noun handling artifact, not evidence of absence. The inflection `зі Штатів` is used in the paired plan without issue.
- The wiki explicitly does NOT teach `Мене звуть` (alternative 3pl-like form — VESUM confirms `звуть` / `зовуть` both exist as valid `звати` forms). Decision: A1 teaches the single canonical chunk `Мене звати` to avoid variant overload; `Мене звуть` is a content-review concern for higher CEFR levels, not a wiki gap at A1.
- Dialogue situation "Орієнтаційний день в університеті" (plan-side) mixes formal `Ви` for professor/group address with informal `ти` for peer chitchat — this is acceptable setting realism but will be watched in the module-build v6 review pass; not a wiki concern.
- Plan word-count sum is 1250 vs `word_target: 1200` — within +5 % tolerance, not a contradiction for the purposes of AC-2 check #4 but flagged here for precision (Codex adversarial-review NIT).
