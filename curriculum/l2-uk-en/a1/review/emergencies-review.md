<!-- content-hash: a0cccb7b29d6 -->
# Рецензія: Emergencies

**Level:** A1 | **Module:** 42
**Overall Score:** 7.6/10
**Status:** FAIL
**Reviewed:** 2026-02-26
**Reviewed-By:** claude-opus-4-6

## Plan Verification

```
Plan-Content Alignment: PASS (with gaps)
- Sections: PASS — all 4 H2 sections present (Вступ, Презентація, Практика, Виробництво та підсумок)
- Vocabulary: 14/14 from plan (8 required + 6 recommended), plus 6 extra (лікар, офіцер, гаманець, метро, дзвонити, викликати)
- Grammar scope: PASS — Vocative, imperative, location expressions all within scope
- Objectives: PASS — all 4 objectives addressed (call for help, describe problems, give location, understand instructions)
- Activity plan divergence: Plan hints suggested 4 activities (match-up/20, fill-in/8, quiz/10, fill-in/5); actual has 10 activities across 5 types. More activities is fine but types diverge from plan.
```

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 8/10 | <7 | Solid WELCOME→PRESENT→PRACTICE→PRODUCE arc; dialogues are engaging. Section «Виробництво та підсумок» Дія subsection is thin/vague. Excessive English intensifiers create purple-prose feeling rather than warm tutor voice. |
| 2 | Language | 8/10 | <8 | Ukrainian prose is generally correct and natural. Culture callout (line 82) makes factually incorrect claim about Slavic languages. Line 68 overstatement about nominative sounding "дуже неприродно." No Russianisms detected in Ukrainian. |
| 3 | Pedagogy | 7/10 | <7 | Testing before teaching: "Офіцере!" tested twice in activities but never taught in content. Vocative case presented as bullets instead of a table — critical miss for beginner grammar. No comparison table for дзвонити/викликати. |
| 4 | Activities | 7/10 | <7 | Testing untaught content (Офіцере!). Unjumble answers omit commas around "будь ласка." Good variety (5 types). Quiz items are well-constructed. |
| 5 | Beginner Safety | 8/10 | <7 | "Would I Continue?" 4/5. Warm opening, clear learning path, good quick wins via vocabulary matching. Some English paragraphs dense with superlatives. |
| 6 | LLM Fingerprint | 7/10 | <7 | "highly" ×7, "extremely" ×3, "perfectly" ×2, "elegantly" ×1. Line 236 pure AI prose. Example format mostly uniform (bold Ukrainian + English in parentheses). |
| 7 | Linguistic Accuracy | 8/10 | <9 | **AUTO-FAIL.** False claim "р" is soft consonant (line 79). IPA error: ʍ in вкрасти (vocab). Missing stress in викликати IPA. False claim about vocative in Slavic languages (line 82). |

**Weighted Overall:** (8×1.5 + 8×1.1 + 7×1.2 + 7×1.3 + 8×1.3 + 7×1.0 + 8×1.5) / 8.9 = (12.0 + 8.8 + 8.4 + 9.1 + 10.4 + 7.0 + 12.0) / 8.9 = 67.7 / 8.9 = **7.6/10**

## Auto-Fail Checklist Results

- Russianisms: **CLEAN** — No Russianisms in content Ukrainian. Content correctly identifies and corrects «визивати» → «викликати».
- Calques: **CLEAN**
- Grammar scope: **CLEAN** — Vocative case and imperative mood appropriate for A1.4
- Activity errors: **ISSUES** — Офіцере! tested but never taught; unjumble answers missing commas
- Beginner safety: 4/5
- Factual accuracy: **ISSUES** — єДопомога mischaracterized; Slavic vocative claim incorrect; "soft consonant р" claim wrong

## Critical Issues Found

### Issue 1: Linguistic Accuracy — False claim about soft consonant "р"
- **Location**: Line 79 / Section «Презентація»
- **Original**: «Masculine nouns ending in a soft consonant like "р" often take the **-ю** ending in the Vocative.»
- **Problem**: The consonant р in лікар is HARD, not soft. The vocative ending -ю for лікар comes from the declension pattern of masculine nouns ending in -ар (лікар→лікарю, кобзар→кобзарю, аптекар→аптекарю), not from consonant softness. Meanwhile, the quiz tests офіцер→офіцере with the explanation "Чоловічі іменники на приголосний у кличному відмінку мають закінчення -е" — directly contradicting the content. A beginner following the content's rule would expect офіцер→офіцерю (wrong).
- **Fix**: Replace with accurate rule: "Masculine nouns ending in **-ар** take **-ю** in the Vocative (лікар → лікарю, кобзар → кобзарю). Most other masculine nouns ending in a hard consonant take **-е** (офіцер → офіцере, друг → друже)." Present this in a comparison TABLE.

### Issue 2: Factual Error — Vocative in Slavic languages
- **Location**: Line 82 / Section «Презентація» / `[!culture]` callout
- **Original**: «Using the Vocative case is a beautiful hallmark of the Ukrainian language, distinguishing it clearly from other Slavic languages that have lost this feature.»
- **Problem**: This is factually incorrect. Polish, Czech, Croatian, Serbian, and Bulgarian all retain productive vocative cases. Only Russian has largely lost the vocative. The statement implicitly defines Ukrainian against Russian without naming it, which also borders on colonial framing.
- **Fix**: Rewrite to: "The Vocative case is a proud grammatical feature shared across several Slavic languages including Polish and Czech. In Ukrainian, it remains highly productive and is expected in everyday speech — using «Лікарю!» instead of «Лікар!» immediately signals respect and natural fluency."

### Issue 3: IPA Error — вкрасти
- **Location**: Vocabulary YAML, line 47
- **Original**: `ipa: '[ˈʍkrɑstɪ]'`
- **Problem**: The symbol ʍ represents a voiceless labial-velar approximant (English "wh" in some dialects). This phoneme does not exist in Ukrainian. The initial в before к in вкрасти is realized as [u̯] (non-syllabic u) or is simply assimilated.
- **Fix**: Change to `'[ˈu̯krɑstɪ]'`

### Issue 4: IPA Error — викликати missing stress
- **Location**: Vocabulary YAML, line 77
- **Original**: `ipa: '[ʋɪklɪkɑtɪ]'`
- **Problem**: No stress mark present. The stress falls on the penultimate syllable: викликáти.
- **Fix**: Change to `'[ʋɪklɪˈkɑtɪ]'`

### Issue 5: Testing Before Teaching — Офіцере!
- **Location**: Activities YAML, lines 329-339 and 408-419 / Content section «Презентація»
- **Problem**: The quiz tests "Офіцере!" as the correct vocative of "офіцер" twice (two separate quiz activities). However, the content (lines 70-78) only teaches three vocative forms: Лікарю!, Поліціє!, Рятувальнику! The word "офіцер" and its vocative "офіцере" appear nowhere in the lesson text. This violates beginner safety — testing content that was never presented.
- **Fix**: Either (a) add офіцер→офіцере to the vocative presentation table in section «Презентація», or (b) replace quiz items testing Офіцере! with items testing taught forms (Лікарю!, Поліціє!, Рятувальнику!).

### Issue 6: Factual Error — єДопомога mischaracterized
- **Location**: Lines 244-245 / Section «Виробництво та підсумок»
- **Original**: «Також існує платформа **«єДопомога»**. Це платформа для соціальної солідарності. Люди можуть знайти волонтерів для допомоги.»
- **Problem**: єДопомога was a state cash assistance program distributing financial aid to internally displaced persons and war-affected citizens through the Дія app. It was NOT a volunteering platform for "social solidarity." This is a fabricated characterization.
- **Fix**: Rewrite to accurately describe єДопомога as a government cash assistance program, or replace with a genuine digital safety tool like the "Повітряна тривога" (Air Alert) app if the goal is to showcase digital resilience.

### Issue 7: Unjumble Missing Commas
- **Location**: Activities YAML, lines 222, 430, 437
- **Original**: «Скажіть будь ласка вашу адресу», «Дайте будь ласка цей документ», «Допоможіть будь ласка написати заяву»
- **Problem**: Standard Ukrainian orthography requires commas around the parenthetical "будь ласка": "Скажіть, будь ласка, вашу адресу." While unjumble activities sometimes omit punctuation, these particular sentences teach a key polite pattern where comma placement is integral to the structure. Beginners may internalize the missing commas.
- **Fix**: Add commas to answers: "Скажіть, будь ласка, вашу адресу" etc. Also add commas as separate "words" in the word lists.

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| 79 | «soft consonant like "р"» | р is a hard consonant; -ю ending is the -ар noun pattern | Grammar explanation error |
| 82 | «from other Slavic languages that have lost this feature» | Polish, Czech, Croatian etc. retain vocative; only Russian largely lost it | Factual error |
| 68 | «Це звучить дуже неприродно» | Overstatement — nominative shout is colloquial but functional | Register overstatement |
| 242 | «це приклад революції» | Vague; specify "цифрової трансформації державних послуг" | Vague claim |
| 244 | «єДопомога... Люди можуть знайти волонтерів» | єДопомога is a cash aid program, not a volunteering platform | Factual error |
| Vocab:47 | `[ˈʍkrɑstɪ]` | `[ˈu̯krɑstɪ]` | IPA error |
| Vocab:77 | `[ʋɪklɪkɑtɪ]` | `[ʋɪklɪˈkɑtɪ]` | Missing IPA stress |

## Beginner Safety Audit

"Would I Continue?" Test: 4/5
- Overwhelmed? **Pass** — Pacing is reasonable, Ukrainian introduced gradually with English scaffolding.
- Instructions clear? **Pass** — Each section has clear purpose and examples.
- Quick wins? **Pass** — Vocabulary matching and basic phrases provide early success.
- Ukrainian scary? **Pass** — Gentle introduction with extensive English support at 37.2% immersion.
- Come back tomorrow? **Soft Fail** — The English prose is dense with superlatives and adverbs ("remarkably natural, deeply respectful, and commands immediate attention") that feel more like marketing copy than a warm tutor. A nervous beginner might feel the instructor is performing rather than teaching.

## Strengths
- **Decolonization**: The Russicism correction (визивати → викликати) section is excellent — direct, clear, with a well-placed myth-buster callout.
- **Practical dialogues**: The three scenarios (112 call, police interaction, embassy) form a coherent progression from emergency → follow-up → resolution.
- **Verb pair distinction**: The дзвонити/викликати differentiation with the learner error warning is pedagogically strong and addresses a genuine A1 error.
- **Activity variety**: 5 different activity types (match-up, fill-in, quiz, unjumble, group-sort) keep practice engaging.
- **Comprehensive scope**: Content covers all plan objectives and provides realistic emergency vocabulary.

## Fix Plan to Reach 9/10 (REQUIRED)

### Linguistic Accuracy: 8/10 → 9/10
**What to fix:**
1. Line 79: Replace "soft consonant like 'р'" with correct rule: -ар nouns take -ю (лікар→лікарю), hard-consonant nouns take -е (офіцер→офіцере). Present as a TABLE.
2. Line 82: Rewrite culture callout to remove false claim about Slavic languages. State vocative is shared with Polish, Czech, etc.
3. Vocab line 47: Fix `вкрасти` IPA from `[ˈʍkrɑstɪ]` to `[ˈu̯krɑstɪ]`.
4. Vocab line 77: Fix `викликати` IPA from `[ʋɪklɪkɑtɪ]` to `[ʋɪklɪˈkɑtɪ]`.

**Expected score after fix:** 9/10

### Pedagogy: 7/10 → 9/10
**What to fix:**
1. Section «Презентація»: Add a markdown TABLE for vocative case forms (Nominative → Vocative, with pattern explanation). Include офіцер→офіцере alongside existing examples.
2. Section «Презентація» subsection «Дієслово «Викликати» та «Дзвонити»»: Add a 2-column comparison TABLE (дзвонити: process/phone vs викликати: summon/dispatch) with example sentences.
3. Lines 240-246 in section «Виробництво та підсумок»: Fix єДопомога description to accurately reflect the cash aid program, or replace with a more relevant digital safety tool.

**Expected score after fix:** 9/10

### Activities: 7/10 → 9/10
**What to fix:**
1. Either add офіцер→офіцере to section «Презентація» content, OR replace quiz items testing Офіцере! with taught forms.
2. Fix unjumble answers to include commas: "Скажіть, будь ласка, вашу адресу" etc.

**Expected score after fix:** 9/10

### LLM Fingerprint: 7/10 → 8/10
**What to fix:**
1. Line 236: Rewrite «This comprehensive role-play elegantly demonstrates how all the disparate elements...come perfectly together» — replace with a direct statement like "This role-play brings together everything from the module: reporting, location, and documentation."
2. Reduce intensifiers throughout English prose: cut ~50% of "highly", "extremely", "remarkably", "immense" instances. Replace with specific, concrete descriptions.
3. Line 134: «brings immense peace of mind» → cut or replace with a teaching point.
4. Line 191: «This dialogue perfectly highlights the crucial, legal difference between two extremely important verbs» → "This dialogue shows the difference between two key verbs:"

**Expected score after fix:** 8/10

### Projected Overall After Fixes
```
Experience: 8→8, Language: 8→9, Pedagogy: 7→9, Activities: 7→9,
Beginner Safety: 8→8, LLM: 7→8, Linguistic Accuracy: 8→9

(8×1.5 + 9×1.1 + 9×1.2 + 9×1.3 + 8×1.3 + 8×1.0 + 9×1.5) / 8.9
= (12.0 + 9.9 + 10.8 + 11.7 + 10.4 + 8.0 + 13.5) / 8.9
= 76.3 / 8.9 = 8.6/10
```

## Factual Verification

- Research notes consulted: YES
- Key Facts Ledger present: NO (not applicable — A1 core track)
- Dates checked: 1 — "У 2023 році" for 112 launch matches research ("July 2023") ✓
- Named figures verified: N/A
- Primary quotes cross-referenced: N/A
- Chronological sequence: CONSISTENT
- Claims without research grounding: 2 found:
  - Line 39: «Оператори 112 також говорять англійською мовою» — not in research notes. Plausible for some operators but broad claim is unverifiable.
  - Lines 244-245: єДопомога characterization as "volunteering platform" — contradicts public knowledge of the program as cash assistance.

## Verification Summary

- Content lines read: 278
- Activity items checked: 67 (across 10 activities)
- Ukrainian sentences verified: 42
- IPA transcriptions checked: 20 (all vocabulary items)
- Factual claims verified: 6
- Issues found: 7

## Verdict

**FAIL**

The module fails on **Linguistic Accuracy** (8/10, auto-fail threshold <9). Three blocking issues must be resolved: (1) the false grammar explanation claiming р is a "soft consonant" in лікар, which directly contradicts quiz items; (2) the fabricated claim about vocative in Slavic languages; (3) two IPA errors in the vocabulary sidecar. Secondary issues include testing Офіцере! without teaching it, and mischaracterizing єДопомога. The module's core content structure and emergency vocabulary are strong — targeted fixes to the linguistic claims, IPA, and activity alignment would bring it to passing threshold.