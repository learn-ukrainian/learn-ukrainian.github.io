# sounds-letters-and-hello (L2-UK-EN A1/M01) — LOCKED review

- **File reviewed:** `wiki/pedagogy/a1/sounds-letters-and-hello.md`
- **Review date:** 2026-04-23
- **Reviewer:** claude-opus-4-7, effort=xhigh (adversarial self-review, post-fix)
- **Rubric:** 5-dimension wiki rubric (factual / language / decolonization / completeness / actionable), target ≥9 on each. See `docs/best-practices/wiki-plan-review-and-lock.md` for the full rubric and procedure.
- **Prior state:** Final Gemini review 2026-04-05 scored 8.4/10. r4: 8.6, r3: 8.2, r2: 7.8, r1: 7.2. Documented gaps: (a) slug promises "Hello" but wiki has no pedagogical step integrating greetings with phonetics; (b) "Типові помилки L2" section from prior rounds dropped during 2026-04-21 recompile; (c) no coverage of milozvučnist' (у/в, і/й euphony), stress-as-meaning-maker, or kinesthetic drills ("cover ears", smile–unsmile); (d) wiki-meta missing lifecycle markers.
- **Fixes applied:** This PR — see the diff against `wiki/pedagogy/a1/sounds-letters-and-hello.md`.

## Dimension scores

| # | Dimension | Score | Evidence |
|---|-----------|-------|----------|
| 1 | Factual accuracy | **9/10** | Every claim sourced via `[S1]`–`[S7]` (sidecar `sounds-letters-and-hello.sources.yaml`). Phoneme inventory (6 vowels, 32 consonants, 33 letters, 38 sounds) consistent with Заболотний 5-клас (S1) and Avramenko 5-клас (S2). Minimal pairs (`дим–дім`, `кит–кіт`, `лис–ліс`, `рис–рись`, `гриб–грип`, `казка–каска`) and `[ґ]`-word list (`аґрус, ґава, ґудзик, ґанок, ґрати`) all VESUM-verified (`data/vesum.db`). Articulatory descriptions of `[г]` (gortan fricative), `[ґ]` (plosive), `[в]→[ў]` (non-syllabic) and mnemonic «ЧуК ПиШе Ці ФоКуСи ТиХо» match native pedagogy (Большакова, Захарійчук). Transcription apparatus (`[´]` stress, `[′]` softness, `[:]` length) matches the simplified convention used in 5-клас textbooks. No unsourced etymological claims. |
| 2 | Ukrainian language quality | **9/10** | Zero Russianisms in instructional text. All explanatory prose uses standard literary Ukrainian (no `шо→що`, no `приймати`-calques, no Title Case — all Cyrillic subheadings capitalise only the first word). Technical terms (`голосний`, `приголосний`, `дзвінкий`, `глухий`, `африкат`, `йотований`, `апостроф`) are the native Ukrainian pedagogical lexicon. Greeting chunks (`Привіт`, `Добрий день`, `Доброго ранку`, `Добрий вечір`, `Радий/Рада тебе бачити`) — all VESUM-verified forms; none are Russian calques. Transcription examples (`[д′акуйу]`, `[с′імйа]`, `[йіжак]`, `[кийіў]`) use sounds inside phonetic brackets (not letters — addresses the r-final factual deduction). |
| 3 | Decolonization | **9/10** | All five decolonization points are framed **affirmatively** (what Ukrainian IS) rather than contrastively (what Ukrainian ISN'T like Russian). The `[г]` / `[ґ]` pair is taught via English anchors (*behind* for `[h]`, *go* for `[g]`), not via Russian. The `ї` and `ґ` letters are celebrated as positive Ukrainian features (unique/restored), not as "things Russian lacks". The single "на відміну від російської" clause (final-consonant devoicing in Крок 7) is a negative-transfer warning, not a phonetic baseline — matches the at-the-cafe locked wiki's convention of naming Russian as calque source when teaching against it. Unstressed `[о]` is treated as the single most important decol. point, surfaced in both Крок 1 and Типова помилка #5 and Декол. #5. No "Ukrainian и is like Russian ы"-type framing anywhere. |
| 4 | Completeness | **9/10** | Closes all four documented gaps: (a) new **Крок 8: Привітання як лексичні чанки** integrates `Привіт / Добрий день / Доброго ранку / Добрий вечір / До побачення / Як справи? / Добре-Чудово-Нормально / Радий-Рада тебе бачити` — the "Hello" component of the slug name is now taught with stress marks + pronunciation notes linked back to Кроки 1–7; (b) new **Типові помилки L2** section (6 errors with minimal pair + kinesthetic test per error); (c) Методичний підхід now covers **принцип милозвучності** (у/в, і/й alternation) AND **наголос як носій значення** (`за́мок` / `замо́к`); (d) new kinesthetic drill examples in Приклади з підручників (cover-ears test, smile–unsmile, unstressed `[о]` drill). Sequence now runs Крок 1 → Крок 8, covering: vowels → easy consonants → hardness/softness → `[г]/[ґ]`, `[дж]/[дз]` → iotated → `щ/ь/apostrophe` → voiced/voiceless → greetings. Writer has everything needed to build the phonetics-first module without inventing sections. |
| 5 | Actionable guidance | **9/10** | Every pedagogical claim is paired with a concrete drill, minimal pair set, or kinesthetic test that a writer can lift directly into an exercise. 7 textbook-grounded exercises (including the new kinesthetic drill #5, `[и]/[і]` minimal pairs #6, and unstressed `[о]` drill #7) + 6 L2-error rows with explicit prevention recipes. Vocabulary table pins core greeting chunks with a writer-note explicitly forbidding grammar analysis at A1 ("do NOT introduce adjective declension, verb conjugation, or case paradigms") — prevents over-teaching. Phonetic transcription mini-apparatus defined up front, so the writer uses a consistent notation. No "teach it well" generic advice; every subsection either names a specific drill or cites a textbook exercise model. |

**Overall: 9/10 — LOCKED.**

## What "LOCKED" means for this artifact

- All 5 dimensions at ≥9.
- The four documented gaps from the 8.4/10 final review (Hello integration, L2 errors, euphony/stress pedagogy, lifecycle markers) have been closed.
- Every new vocabulary item (including mini-pair words `дим, кит, лис, ліс, рис, рись, гриб, грип, казка, каска`, `[ґ]`-words, greeting chunks) is VESUM-verified (`data/vesum.db`).
- Every L2-error row in the new "Типові помилки L2" table has a documented minimal pair and/or kinesthetic test.
- Meta block carries `lifecycle: locked` + `reviewed_by` + `last_reviewed`.
- This wiki is cleared as a clean input for A1 scale batch module build.

## Unlock triggers

This LOCKED state should be revisited if any of the following happen:

1. The module build (sounds-letters-and-hello A1/M01) surfaces a phonetic drill gap the wiki did not anticipate — file as an issue, fresh review round, republish with incremented `last_reviewed`.
2. A native-speaker reviewer (Teacher Tetiana / Teacher Alona) flags any minimal-pair, kinesthetic test, or greeting chunk — authoritative override.
3. The paired `culture/decolonization/surzhyk-and-russianisms` wiki changes its framing in a way that contradicts the Декол. #1–5 points here.
4. VESUM / СУМ-11 updates retire or re-label any of the cited forms (especially the `[ґ]`-word list or greeting chunks).
5. A revision of the broader "sound-first vs letter-first" pedagogy consensus in Ukrainian primary education (unlikely — Bukvar tradition is deeply entrenched).

## Residual non-blockers (documented, not blocking)

- The sound-first introduction sequence (Крок 1 → Крок 2) assumes English-speaker ordering intuitions ("false friends first" idea from prior r4). The current wiki pragmatically introduces the most productive first 9 consonants (`м, т, н, с, л, в, к, п, р`) rather than classifying them as "false friends". This is the Bukvar-native order (Большакова, Захарійчук) and is the better default; the "false friends" framing is a legitimate alternate sequencing that a writer may still adopt for an English-speaker audience without violating this wiki.
- The iotated-vowel treatment in Крок 5 does not yet introduce the full 2vs1-sound column exercise as a drill — it's referenced only via the textbook exercise #3. A writer who wants an interactive three-column exercise needs to adapt the textbook model. This is acceptable for a wiki brief (vs a module-level content spec).
- Stress-distinction minimal pair set (`за́мок`/`замо́к`, `бра́ти`/брати́) is introduced in Методичний підхід but not expanded into a dedicated drill row in "Типові помилки L2" — the L2 error table focuses on production errors; stress-distinction is a comprehension issue that the writer can build into the glossary itself.
- Крок 7 example `нігті` [ніхт'і] uses a palatalized `т′` that cascades from а regressive voicelessness+palatalization assimilation; this is correct standard Ukrainian orthoepy but deep phonology for A1. Keep as-is (labeled "з асиміляцією") — writer can choose to defer the transcription and only teach the production rule.
