<!-- content-hash: d81189348cf7 -->
# Рецензія: Being and Becoming

**Reviewed-By:** claude-opus-4-6

**Level:** A2 | **Module:** 6
**Overall Score:** 8.9/10
**Status:** PASS
**Reviewed:** 2026-03-14

## Plan Verification

```
Plan-Content Alignment: PASS
- Sections: 5/5 present (PASS)
- Vocabulary: 11/11 required present in prose, 5/5 recommended present
- Grammar scope: PASS — no scope creep detected
- Objectives: 4/4 PASS
- "став тестувальником": PRESENT in dialogue (line 291)
```

**Plan Adherence Checklist — content_outline.points:**

Section "Вступ":
- Concept of role vs identity (Nom vs Instr): **COVERED** — lines 18, 36-38
- Explicit English explanation of Identity vs Function logic: **COVERED** — lines 20, 38
- The 'Nominative Trap' warning: **COVERED** — lines 52-56

Section "Презентація: Дієслова та відмінювання":
- бути + instrumental (Past/Future): **COVERED** — lines 80-87
- стати/ставати + instrumental, хоче стати constructions, formal програмувальник: **COVERED** — lines 89-103, 157-161
- працювати + instrumental, "Work As" calque: **COVERED** — lines 105-122
- Primary profession vocabulary with instrumental forms: **COVERED** — lines 130-139

Section "Соціокультурний контекст: Фемінітиви та IT":
- 2020 Grammar Reform, femininitives: **COVERED** — lines 172-190
- IT Industry Prestige, програміст vs айтішник: **COVERED** — lines 192-206
- Consistent use of both masc/fem forms: **COVERED** throughout

Section "Практика та запобігання помилкам":
- Transformation drills (Nom → Instr): **COVERED** — lines 229-236
- Gender Mismatch drilling: **COVERED** — lines 237-255
- Correction of "як" calques: **COVERED** — lines 259-263

Section "Діалоги та кар'єрні плани":
- "What do you do?" conversations in IT/professional contexts: **COVERED** — lines 277-297
- "став тестувальником" example: **COVERED** — line 291 「Мій друг нещодавно став тестувальником у тій самій компанії.」
- Career history scenarios, "був офіціантом" and "мріє стати громадянкою": **COVERED** — "офіціанткою" appears (line 313), "громадянкою" covered (lines 299-305).
- Synthesis activity: **COVERED** — lines 307-309

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 9/10 | <7 | Warm tutor voice, excellent pacing, clear arc from intro to celebration. 「Вітаємо! Тепер ви можете розповідати українською мовою про свою кар'єру та плани!」 |
| 2 | Language | 9/10 | <8 | [D.2 FIX] Duplicate "перекласти" removed (line 113); "як" calque in reading passage fixed to instrumental 「не працювала журналісткою чи вчителькою」 (line 266); word order fixed to 「Раніше вона була студенткою.」 (line 82). No remaining language errors. |
| 3 | Pedagogy | 9/10 | <7 | Strong PPP structure, excellent error-correction approach. [D.2 FIX] "тестувальник" added to dialogue (line 291). Translation error fixed: line 101 now reads "I want to become a good lawyer." |
| 4 | Activities | 9/10 | <7 | 10 activities with good variety (fill-in, quiz, match-up, error-correction, true-false, group-sort, unjumble). [D.2 FIX] Content aligned to айтішник/айтішниця matching activities, vocab, and plan. |
| 5 | Beginner Safety | 9/10 | <7 | "Would I Continue?" 5/5. Warm welcome, clear preview, quick wins, gentle Ukrainian intro, encouraging ending. |
| 6 | LLM Fingerprint | 8/10 | <7 | "Давайте" opens 6 callouts (lines 60, 75, 126, 219, 245 + line 58 title). Repetitive but serves pedagogical purpose. One "не лише" instance (line 188). No stacked abstract nouns, no AI clichés. |
| 7 | Linguistic Accuracy | 9/10 | <9 | [D.2 FIX] Duplicate "перекласти" removed; "як" calque in reading passage fixed to instrumental; date corrected to 2019 (Cabinet Resolution No. 437, May 22, 2019). No remaining accuracy issues. |

**Weighted Overall:** (9×1.5 + 9×1.1 + 9×1.2 + 9×1.3 + 9×1.3 + 8×1.0 + 9×1.5) / 8.9 = (13.5 + 9.9 + 10.8 + 11.7 + 11.7 + 8.0 + 13.5) / 8.9 = 79.1 / 8.9 = **8.9/10**

## Auto-Fail Checklist Results

- Russianisms: CLEAN
- Calques: CLEAN [D.2 FIX] — line 266 corrected to instrumental 「не працювала журналісткою чи вчителькою」
- Grammar scope: CLEAN — no grammar from later modules
- Activity errors: CLEAN [D.2 FIX] — content aligned to айтішник/айтішниця matching activities/vocab/plan
- Colonial framing: CLEAN — line 174 mentions Russian influence on grammar rules in historical context (legitimate)
- Beginner safety: 5/5
- Factual accuracy: CLEAN [D.2 FIX] — date corrected to 2019 (Cabinet Resolution No. 437)

## Critical Issues Found (All resolved in D.2)

### Issue 1: Terminology Mismatch — айтівець/айтівка vs айтішник/айтішниця [RESOLVED]
- **Location**: Content lines 194, 196, 200, 205, 206, 210, 290, 313, 319 vs Vocabulary YAML and Activities YAML throughout
- **Original (content)**: 「Але в повсякденній розмові майже всі використовують слова **айтівець** (для чоловіків) та **айтівка** (для жінок).」
- **Problem**: The content teaches "айтівець/айтівка" as the colloquial IT terms, but the vocabulary YAML lists "айтішник/айтішниця" and ALL activities use "айтішник/айтішниця/айтішником/айтішницею". Both are valid VESUM words, but a learner doing activities will encounter different words than what the prose taught them. The plan specifies "айтішник / айтішниця."
- **Fix**: Align content to use айтішник/айтішниця (matching plan, vocab, and activities), or update vocab+activities to match content. Since the plan says "айтішник", content should be updated.

### Issue 2: Duplicate Word — "перекласти" appears twice [RESOLVED]
- **Location**: Line 113, Section "Презентація: Дієслова та відмінювання"
- **Original**: 「Англомовні студенти часто хочуть перекласти слово "as" перекласти словом **як**.」
- **Problem**: The word "перекласти" is duplicated, creating a broken Ukrainian sentence.
- **Fix**: Remove the first "перекласти": "Англомовні студенти часто хочуть слово "as" перекласти словом **як**." or "часто хочуть перекласти слово "as" словом **як**."

### Issue 3: "як" Calque in Reading Passage Contradicts Teaching [RESOLVED]
- **Location**: Line 266, Section "Практика та запобігання помилкам"
- **Original**: 「Вона ніколи не працювала як журналістка чи вчителька.」
- **Problem**: This reading passage uses "працювала як журналістка" — the EXACT calque the module explicitly teaches is wrong (lines 111-115, 259-262). Reading passages should model correct usage. Immediately after, line 266 correctly uses 「Вона завжди працювала економісткою в банку.」 — the contrast is confusing without any correction marker.
- **Fix**: Change to instrumental: "Вона ніколи не працювала журналісткою чи вчителькою."

### Issue 4: Translation Error [RESOLVED]
- **Location**: Line 101, Section "Презентація: Дієслова та відмінювання"
- **Original**: 「Я хочу стати хорошим юристом.」 — I will become a good lawyer.
- **Problem**: "Я хочу" means "I want", not "I will". The English gloss should be "I want to become a good lawyer."
- **Fix**: Change English translation to "I want to become a good lawyer."

### Issue 5: Missing Plan Point — "тестувальник" [RESOLVED]
- **Location**: Section "Діалоги та кар'єрні плани"
- **Problem**: The plan specifies modeling "став тестувальником" in the dialogues section, but this word does not appear anywhere in the module.
- **Fix**: Add "тестувальник" to one of the dialogues or career examples.

### Issue 6: Factual Date — 2020 vs 2019 [RESOLVED]
- **Location**: Line 174, Section "Соціокультурний контекст: Фемінітиви та IT"
- **Original**: 「Український уряд у 2020 році прийняв важливу граматичну реформу.」
- **Problem**: The new Ukrainian orthography (which codified femininitives) was approved by the Cabinet of Ministers on May 22, 2019 (Resolution No. 437). The content says 2020.
- **Fix**: Change "2020 році" to "2019 році".

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| 113 | 「хочуть перекласти слово "as" перекласти словом」 | 「хочуть слово "as" перекласти словом」 | Grammar (duplicate word) |
| 266 | 「не працювала як журналістка чи вчителька」 | 「не працювала журналісткою чи вчителькою」 | Calque (як + працювати) |
| 82 | 「Вона була раніше студенткою.」 | 「Раніше вона була студенткою.」 | Word order (minor) |

## Beginner Safety Audit

"Would I Continue?" Test: 5/5
- Overwhelmed? **Pass** — comfortable pacing, small chunks
- Instructions clear? **Pass** — always clear what to do, English scaffolding present
- Quick wins? **Pass** — simple examples from line 23 onwards
- Ukrainian scary? **Pass** — introduced gently with English translations
- Come back tomorrow? **Pass** — encouraging tone, progress celebration at end

## Strengths
- Excellent PPP structure with natural progression from identity → verbs → culture → practice → dialogues
- Very strong error prevention pedagogy — the "Nominative Trap" (line 52) and "Work As Calque" (line 111) callouts anticipate real learner errors
- Rich reading passages that tell engaging personal stories (lines 65-68, 313-315, 317-333)
- Good gender parity — feminine forms consistently modeled alongside masculine throughout
- Activities cover all key error patterns (error-correction type directly targets the taught calques)

## Fix Plan to Reach 9/10 (REQUIRED if score < 9.0)

### Language: 7/10 → 9/10
**What to fix:**
1. Line 113: Remove duplicate "перекласти" — fixes broken Ukrainian sentence
2. Line 266: Change "як журналістка чи вчителька" to "журналісткою чи вчителькою" — eliminates calque contradiction
3. Line 82: Reorder to "Раніше вона була студенткою." — more natural word order

**Expected score after fix:** 9/10

### Pedagogy: 8/10 → 9/10
**What to fix:**
1. Line 101: Fix English translation to "I want to become a good lawyer"
2. Add "тестувальник" example to one dialogue in Section "Діалоги та кар'єрні плани"

**Expected score after fix:** 9/10

### Activities: 8/10 → 9/10
**What to fix:**
1. Align айтівець/айтівка in content to айтішник/айтішниця (matching plan, vocab, activities)

**Expected score after fix:** 9/10

### Linguistic Accuracy: 7/10 → 9/10
**What to fix:**
1. Fix duplicate "перекласти" (line 113)
2. Fix "як" calque in reading passage (line 266)
3. Verify and correct "2020 році" to "2019 році" (line 174)

**Expected score after fix:** 9/10

### Projected Overall After Fixes
```
(9×1.5 + 9×1.1 + 9×1.2 + 9×1.3 + 9×1.3 + 8×1.0 + 9×1.5) / 8.9
= (13.5 + 9.9 + 10.8 + 11.7 + 11.7 + 8.0 + 13.5) / 8.9
= 79.1 / 8.9 = 8.9/10
```

## Verification Summary

- Content lines read: 363
- Activity items checked: 79 (across 10 activity blocks)
- Ukrainian sentences verified: 45+
- Citations in bank: 17
- Issues found: 6

## Verdict

**PASS**

All blocking issues resolved in Phase D.2: (1) "як" calque in reading passage (line 266) corrected to instrumental; (2) content aligned to айтішник/айтішниця matching vocabulary, activities, and plan; (3) duplicate "перекласти" removed from line 113; (4) date corrected to 2019; (5) translation error fixed; (6) "тестувальник" added to dialogue.