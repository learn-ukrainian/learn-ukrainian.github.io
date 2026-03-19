<!-- content-hash: 62c39d3aa910 -->
# Рецензія: Likes and Preferences

**Level:** A1 | **Module:** 19
**Overall Score:** 3.7/10
**Status:** FAIL
**Reviewed:** 2026-03-19
**Reviewed-By:** claude-sonnet-4-20250514

## Plan Verification

```
Plan-Content Alignment: FAIL (CATASTROPHIC)
- Sections: 5/5 H2 headers present, BUT Section "Мені подобається (I like)" content does not match its title
- Vocabulary: 6/8 required words in prose (подобатися MISSING from prose entirely, піти MISSING from prose)
- Grammar scope: FAIL — Dative construction (primary grammar point) completely absent from prose
- Objectives: 1/4 met (only "Express wants using Я хочу" partially covered)
```

### Plan Adherence Checklist

**Section "Мені подобається (I like)":**
- Давальна конструкція «Мені подобається + іменник/інфінітив»: **MISSING** — The section title says "Мені подобається" but the content teaches "Я люблю" instead. Zero instances of the подобається construction appear in the prose. Line 3 begins: 「When expressing that something appeals to you in Ukrainian, you can use the verb **люби́ти** (to like/love).」 — this is the WRONG verb for this section.
- Давальний відмінок займенників (мені/тобі/йому/їй/нам/вам/їм): **MISSING** — No Dative pronoun forms taught anywhere in the content.
- Узгодження подобається (sing.) vs подобаються (plur.): **MISSING**

**Section "Я люблю (I love)":**
- Конструкція «Люблю + Знахідний відмінок»: **PARTIAL** — The conjugation table is correct (lines 50-57), but the example sentences systematically use Nominative instead of Accusative: 「Я люблю́ ця кни́га.」 (line 61) instead of "Я люблю цю книгу."
- Різниця між подобається та люблю: **MISSING** — Cannot contrast with подобається when подобається is never taught.

**Section "Я хочу (I want)":**
- Конструкція «Хочу + інфінітив»: **COVERED** — Lines 77-79 show correct infinitive usage.
- Конструкція «Хочу + Знахідний»: **PARTIAL** — Examples use wrong case: 「Я хочу кава.」 (line 105) instead of "Я хочу каву."
- Контраст із подобається: **MISSING**

**Section "Порівняння (Comparing likes)":**
- Питання про уподобання інших: **COVERED** — Lines 115-119 demonstrate question forms.
- Культурний контекст: **PARTIAL** — Brief mention of gathering for meals (line 127) but no specific Ukrainian cultural details.

**Section "Практика (Practice)":**
- Вправи на вибір правильної конструкції: **PARTIAL** — Practice exists but only contrasts люблю vs хочу (not подобається).
- Діалогові завдання з пропусками: **COVERED** — Lines 158-161 show gap-fill dialogues.

**Required Vocabulary in Prose:**
- подобатися: **MISSING** from prose (only in H2 title)
- любити: COVERED
- хотіти: COVERED
- кава: COVERED
- музика: COVERED
- читати: COVERED
- їсти: COVERED
- піти: **MISSING** from prose entirely
- улюблений (recommended): **MISSING** from prose

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 5/10 | <7 ✘ | Section "Мені подобається (I like)" title promises one thing, teaches another. No warm welcome, no learning preview, abrupt ending. Learner would be confused by the content-title mismatch. |
| 2 | Language | 3/10 | <8 ✘ | 9+ sentences use Nominative where Accusative is required. 「В Україна」 (line 35) instead of "В Україні." This would actively teach wrong grammar. |
| 3 | Pedagogy | 3/10 | <7 ✘ | The primary grammar point (Dative подобається construction) is completely absent. The contrast подобається vs люблю vs хочу — the pedagogical core — cannot exist without подобається. |
| 4 | Activities | 6/10 | <7 ✘ | Activities correctly teach подобається with Dative pronouns (quiz items 1, 6, 7, 9; fill-in items 1, 5, 8), but the prose never teaches this — learners encounter untaught material in activities. 6 activity types is adequate. |
| 5 | Beginner Safety | 4/10 | <7 ✘ | "Would I Continue?" 1/5. Wrong case forms would confuse any learner who later encounters correct Ukrainian. No welcome, no preview, no encouragement, no celebration. |
| 6 | LLM Fingerprint | 6/10 | <7 ✘ | Sections 1 and 2 are nearly identical in structure and content — both teach люблю conjugation tables. 5 identical `[!tip] 💡🎬🌍` callouts with `**Цікаво знати!**` / `**Remember!**` / `**У кафе:**` format. Repetitive padding. |
| 7 | Linguistic Accuracy | 2/10 | <9 ✘ | CATASTROPHIC. At least 9 sentences teach wrong case (Nominative instead of Accusative after transitive verbs). "В Україна" is not a valid form. This module would actively harm learners. |

**Weighted Overall:** (5×1.5 + 3×1.1 + 3×1.2 + 6×1.3 + 4×1.3 + 6×1.0 + 2×1.5) / 8.9 = (7.5 + 3.3 + 3.6 + 7.8 + 5.2 + 6.0 + 3.0) / 8.9 = 36.4 / 8.9 = **4.1/10**

## Auto-Fail Checklist Results

- Russianisms: [CLEAN] — no Russianisms detected
- Calques: [CLEAN]
- Grammar scope: [FAIL] — The Dative construction is in-scope per plan but completely absent
- Activity errors: [FAIL] — Activities test подобається which is never taught in prose
- Beginner safety: 1/5
- Factual accuracy: [FAIL] — 「В Україна люди часто п'ють чай або кава разом. Це гарна традиція.」 (line 35) has grammatically impossible forms ("В Україна" is not Locative)
- Colonial framing: [CLEAN]

## Critical Issues Found

### Issue 1: CATASTROPHIC — Dative подобається construction completely missing from prose
- **Location**: Section "Мені подобається (I like)" (entire section, lines 1-36)
- **Problem**: The plan requires the Dative construction «Мені подобається + noun/infinitive» as the PRIMARY grammar point. The section is titled "Мені подобається" but the content teaches "Я люблю" instead. The word "подобається" appears zero times in the prose. The Dative pronoun paradigm (мені/тобі/йому/їй/нам/вам/їм) is never taught. This is the #1 learning objective and it is entirely absent.
- **Fix**: Complete rewrite of section "Мені подобається (I like)" to teach the Dative construction with examples like "Мені подобається кава", "Тобі подобається музика?", and the full Dative pronoun table. Move люблю content to section "Я люблю (I love)".

### Issue 2: CATASTROPHIC — Systematic wrong case (Nominative instead of Accusative) in 9+ sentences
- **Location**: Multiple sections, throughout the module
- **Original examples**:
  - Line 5: 「Я люблю́ ка́ва.」 → should be "Я люблю́ ка́ву."
  - Line 11: 「Я люблю́ му́зика і спорт.」 → should be "Я люблю́ му́зику і спорт."
  - Line 61: 「Я люблю́ ця кни́га.」 → should be "Я люблю́ цю кни́гу."
  - Line 68: 「Ми любимо музика.」 → should be "Ми любимо музику."
  - Line 100: 「Я люблю́ ка́ва.」 → should be "Я люблю́ ка́ву."
  - Line 105: 「Я хочу кава.」 → should be "Я хочу каву."
  - Line 117: 「Ти лю́биш му́зика?」 → should be "Ти лю́биш му́зику?"
  - Line 138: 「Я хочу вода.」 → should be "Я хочу воду."
- **Problem**: Люблю and хочу are transitive verbs that take the Accusative case. Feminine nouns (кава→каву, музика→музику, вода→воду, книга→книгу) must change form. VESUM confirms каву (v_zna), музику (v_zna), воду (v_zna) as correct Accusative forms. Teaching Nominative after transitive verbs is actively harmful — learners would internalize incorrect grammar.
- **Fix**: Replace all Nominative objects after люблю/хочу with correct Accusative forms. Note: some correct forms already exist in the conjugation table (line 19: 「Я люблю́ ка́ву.」, line 21: 「Він лю́бить му́зику.」) — the module contradicts itself.

### Issue 3: HIGH — "В Україна" (line 35) — invalid Locative form
- **Location**: Line 35, Section "Мені подобається (I like)", callout box
- **Original**: 「В Україна люди часто п'ють чай або кава разом. Це гарна традиція.」
- **Problem**: "В Україна" is Nominative. The Locative (Місцевий відмінок) required after "в" for location is "В Україні". VESUM confirms "Україні" as v_mis (Locative). Additionally, "кава" after "п'ють" should be "каву" (Accusative).
- **Fix**: "В Україні люди часто п'ють чай або каву разом. Це гарна традиція."

### Issue 4: HIGH — Sections 1 and 2 are nearly identical (both teach люблю)
- **Location**: Section "Мені подобається (I like)" (lines 1-36) and Section "Я люблю (I love)" (lines 38-69)
- **Problem**: Because section 1 teaches люблю instead of подобатися, both sections cover the same verb. Section 1 has a люблю conjugation table (lines 17-25), section 2 has another люблю conjugation table (lines 50-57). The content is redundant.
- **Fix**: Section 1 must be rewritten to teach подобатися. Section 2 should then properly contrast люблю with подобатися as the plan requires.

### Issue 5: HIGH — Required vocabulary words missing from prose
- **Location**: Entire module
- **Problem**: "подобатися" (required) never appears in prose. "піти" (required) never appears in prose. "улюблений" (recommended) never appears in prose. The vocabulary file lists all three, and the activities use подобатися extensively, but learners would never encounter these words before being tested on them.
- **Fix**: Full rewrite needed — подобатися will naturally appear when section 1 is fixed. піти needs an example like "Я хочу піти" in section "Я хочу (I want)". улюблений should appear in at least one example.

### Issue 6: MEDIUM — No welcome, no learning preview, no encouragement, no celebration
- **Location**: Module opening (line 1) and closing (lines 173-184)
- **Problem**: The module jumps straight into grammar with no warm greeting, no "Today you'll learn..." preview. The closing section "Підсумок" (line 173) says 「You can now confidently express your likes, loves, and desires.」 — but the learner was never taught подобатися, so this claim is false. No encouragement markers throughout.
- **Fix**: Add a warm opening before section 1. Add encouragement at section transitions. Fix the Підсумок to accurately reflect what was actually taught.

### Issue 7: MEDIUM — Callout boxes all use identical format
- **Location**: Lines 33-36, 66-69, 103-107, 134-139, 168-171
- **Problem**: All 5 callout boxes use `[!tip] 💡🎬🌍` with a bold title and Ukrainian examples followed by English translation in parentheses. No variety — no `[!did-you-know]`, `[!culture-note]`, or other types. This is repetitive LLM-pattern output.
- **Fix**: Vary callout types. Use `[!culture-note]` for the Ukraine tea/coffee tradition, `[!did-you-know]` for interesting facts, `[!tip]` only for actual tips.

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| 5 | 「Я люблю́ ка́ва.」 | Я люблю́ ка́ву. | Grammar (wrong case) |
| 11 | 「Я люблю́ му́зика і спорт.」 | Я люблю́ му́зику і спорт. | Grammar (wrong case) |
| 35 | 「В Україна люди часто п'ють чай або кава разом.」 | В Україні люди часто п'ють чай або каву разом. | Grammar (wrong Locative + wrong Accusative) |
| 61 | 「Я люблю́ ця кни́га.」 | Я люблю́ цю кни́гу. | Grammar (wrong case — both demonstrative and noun) |
| 68 | 「Ми любимо музика.」 | Ми любимо музику. | Grammar (wrong case) |
| 100 | 「Я люблю́ ка́ва.」 | Я люблю́ ка́ву. | Grammar (wrong case) |
| 105 | 「Я хочу кава.」 | Я хочу каву. | Grammar (wrong case) |
| 117 | 「Ти лю́биш му́зика?」 | Ти лю́биш му́зику? | Grammar (wrong case) |
| 138 | 「Я хочу вода.」 | Я хочу воду. | Grammar (wrong case) |

## Beginner Safety Audit

"Would I Continue?" Test: 1/5
- Overwhelmed? **Fail** — Two nearly identical sections on люблю with contradictory case usage (some examples Nominative, some Accusative) would confuse a beginner
- Instructions clear? **Fail** — Section 1 titled "Мені подобається" teaches люблю; the mismatch makes structure unintelligible
- Quick wins? **Fail** — No quick wins, no practice until section 5, no mini-exercises
- Ukrainian scary? **Pass** — Ukrainian is introduced gradually with English support
- Come back tomorrow? **Fail** — Contradictory grammar and repetitive structure would discourage continuation

## Strengths

- The **activities file** is well-constructed: 6 varied activity types (quiz, fill-in, match-up, unjumble, true-false, group-sort) that correctly use Accusative forms and properly teach the подобається Dative construction. The activities are better than the prose.
- The **conjugation tables** for люблю (lines 50-57) and хочу (lines 83-90) are correct and well-formatted.
- The **dialogue examples** (lines 10-13, 123-125, 153-154) are a good pedagogical approach for beginners.
- Some example sentences use correct Accusative forms (line 19: 「Я люблю́ ка́ву.」, line 21: 「Він лю́бить му́зику.」) — the correct forms exist, they're just inconsistently applied.

## Fix Plan to Reach 9/10 (REQUIRED — score is 4.1)

### This module requires a FULL REBUILD, not incremental fixes.

The issues are too fundamental for FIND/REPLACE patches:
1. Section "Мені подобається (I like)" must be entirely rewritten to teach the Dative construction
2. 9+ sentences have wrong case forms scattered throughout
3. The pedagogical core (three-way contrast: подобається vs люблю vs хочу) doesn't exist
4. Missing vocabulary items (подобатися, піти, улюблений) need organic integration
5. Module needs welcome/preview/encouragement/celebration scaffolding

**Recommended action**: Rebuild via pipeline with explicit instruction to teach подобатися Dative construction in section 1, use Accusative case consistently after люблю/хочу, and include all required vocabulary.

### Projected Overall After Rebuild
With correct grammar, proper подобатися teaching, and beginner scaffolding:
```
Experience: 5→9, Language: 3→9, Pedagogy: 3→9, Activities: 6→9 (already good, just needs prose alignment),
Beginner Safety: 4→9, LLM: 6→8, Linguistic Accuracy: 2→9
(9×1.5 + 9×1.1 + 9×1.2 + 9×1.3 + 9×1.3 + 8×1.0 + 9×1.5) / 8.9 = (13.5+9.9+10.8+11.7+11.7+8.0+13.5)/8.9 = 79.1/8.9 = 8.9/10
```

## Verification Summary

- Content lines read: 184
- Activity items checked: 56 (10 quiz + 8 fill-in + 10 match-up + 6 unjumble + 8 true-false + 1 group-sort with 12 items)
- Ukrainian sentences verified: 25+
- Citations in bank: 20
- Issues found: 7 (2 catastrophic, 3 high, 2 medium)

## Verdict

**FAIL**

This module has two catastrophic, blocking issues: (1) the primary grammar point — the Dative подобається construction — is completely absent from the prose despite being the #1 plan objective, the section title, and the focus of most activities; (2) at least 9 Ukrainian sentences systematically use Nominative case instead of Accusative after transitive verbs, which would actively teach learners wrong grammar. A full rebuild is required.