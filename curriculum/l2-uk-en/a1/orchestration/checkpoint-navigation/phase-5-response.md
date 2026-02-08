# Рецензія: Checkpoint - Navigation

**Level:** A1 | **Module:** 20
**Overall Score:** 7.5/10
**Status:** FAIL
**Reviewed:** 2026-02-08

## Plan Verification

```
Plan-Content Alignment: [FAIL]
- Sections: [PASS]
- Vocabulary: [7/8 from plan, "направо" missing (used "праворуч")]
- Grammar scope: [FAIL - Major Past Tense usage]
- Objectives: [PASS]
```

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 8/10 | <7 | Clear explanations, friendly tone. |
| 2 | Coherence | 8/10 | <7 | Logical progression of skills. |
| 3 | Relevance | 6/10 | <7 | **FAIL**: Uses grammar (Past Tense) not yet taught. |
| 4 | Educational | 6/10 | <7 | **FAIL**: Tests untaught concepts in Integration Challenge. |
| 5 | Language | 9/10 | <8 | Natural Ukrainian, correct forms. |
| 6 | Pedagogy | 5/10 | <7 | **FAIL**: Integration Challenge requires A1.3 skills (Past Tense). |
| 7 | Immersion | 7/10 | <6 | Good use of dialogues and models. |
| 8 | Activities | 8/10 | <7 | Good variety, though some euphony issues. |
| 9 | Richness | 7/10 | <6 | Meets baseline. |
| 10 | Beginner Safety | 6/10 | <7 | **FAIL**: Sudden introduction of past tense is overwhelming. |
| 11 | LLM Fingerprint | 9/10 | <7 | Low, sounds natural. |
| 12 | Linguistic Accuracy | 9/10 | <9 | High accuracy. |

**Weighted Overall:** 105.1 / 14.0 = **7.51/10**

## Auto-Fail Checklist Results

- Russianisms: [CLEAN]
- Calques: [CLEAN]
- Grammar scope: **FAIL** (Past tense used extensively in Integration Challenge)
- Activity errors: [Euphony issues in Fill-in Locative]
- Beginner safety: 3/5 (Failed on "Did I get quick wins?" due to impossible text)

## Critical Issues Found

### Issue 1: Grammar Scope Violation (Past Tense)
- **Location**: Section "Integration Challenge"
- **Original**: "Вчора я була в кав'ярні... Я замовила каву... Кава коштувала... У мене не було готівки... я платила карткою."
- **Problem**: This module is A1.2 Checkpoint (Module 20). Past tense is introduced in the NEXT module (Module 21: "Yesterday - Past Tense"). Students have not learned past forms (була, замовила, коштувала, платила) yet.
- **Fix**: Rewrite the text in the Present Tense.
  - "Сьогодні я в кав'ярні..."
  - "Я замовляю каву..."
  - "Кава коштує..."
  - "У мене немає готівки..."
  - "я плачу карткою."

### Issue 2: Vocabulary Mismatch (Plan vs Content)
- **Location**: Content "Skill 5" vs Plan
- **Original**: "наліво / праворуч"
- **Problem**: Plan explicitly requires "направо". Content uses "праворуч". While synonyms, for A1 it's better to stick to the planned vocabulary or explicitly teach both.
- **Fix**: Change "праворуч" to "направо" or add "направо" as a synonym.

### Issue 3: Grammar Scope in Activities (Future Tense)
- **Location**: Activities `quiz` "Real Dialogues Order", Question 5
- **Original**: "Я візьму борщ і вареники."
- **Problem**: "візьму" is Future Perfective (A1.3/A2). A1 student knows "Я хочу".
- **Fix**: Change to "Я хочу борщ і вареники." or "Будь ласка, борщ і вареники."

### Issue 4: Euphony Violations
- **Location**: Activities `fill-in` "Locative", Item 3
- **Original**: "Студенти у бібліотеці."
- **Problem**: "Студенти" ends in vowel 'и'. Next word should start with 'в' for euphony (V-v-C).
- **Fix**: Change option/answer to "в". (Студенти в бібліотеці).

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| Text | "Вчора я була..." | "Сьогодні я..." | Scope (Past Tense) |
| Text | "Я замовила..." | "Я замовляю..." | Scope (Past Tense) |
| Text | "Кава коштувала..." | "Кава коштує..." | Scope (Past Tense) |
| Text | "У мене не було..." | "У мене немає..." | Scope (Past Tense) |
| Act | "Я візьму..." | "Я хочу..." | Scope (Future Tense) |

## Beginner Safety Audit

"Would I Continue?" Test: 3/5
- Overwhelmed? **Fail** (The final text is impossible to parse grammatically for a student who only knows Present Tense).
- Instructions clear? Pass
- Quick wins? Pass (until the end).
- Ukrainian scary? **Fail** (Sudden appearance of unknown verb endings -ла, -ло, -ли).
- Come back tomorrow? Maybe.

## Fix Plan to Reach 9/10

### Relevance & Pedagogy: 6/10 → 9/10

**What to fix:**
1.  **Section "Integration Challenge"**: REWRITE the entire text to **Present Tense**.
    *   Change: "Вчора я була в кав'ярні" → "Сьогодні я в кав'ярні".
    *   Change: "Я замовила каву" → "Я замовляю каву".
    *   Change: "Кава коштувала" → "Кава коштує".
    *   Change: "У мене не було готівки" → "У мене немає готівки".
    *   Change: "тому я платила карткою" → "тому я плачу карткою".
2.  **Activity "Real Dialogues Order"**:
    *   Change: "Я візьму борщ..." → "Я хочу борщ..." (Remove future tense).

### Beginner Safety: 6/10 → 9/10

**What to fix:**
1.  **Section "Skill 5"**: Ensure vocabulary matches exactly.
    *   Change: "наліво / праворуч" → "наліво / направо (або праворуч)". Add "направо" to match the Plan.

### Activities: 8/10 → 9/10

**What to fix:**
1.  **File `activities/20-checkpoint-navigation.yaml`**: Fix euphony in Locative fill-ins.
    *   Item 3: "Студенти ___ бібліотеці" → Answer "в" (not "у").
    *   Item 5: "Діти ___ парку" → Answer "в" (not "у").

### Projected Overall After Fixes

```
(8*1.5 + 9*1 + 10*1 + 10*1.2 + 9*1.1 + 10*1.2 + 8*1 + 9*1.3 + 7*0.9 + 9*1.3 + 9*1 + 9*1.5) / 14 = ~9.1
```

## Verification Summary

- Content lines read: All
- Activity items checked: 35
- Ukrainian sentences verified: ~40
- Issues found: 4 (Major Scope, Vocab, Euphony)
- Naturalness score recommendation: 10/10 (The Ukrainian itself is natural, just wrong level).

## Verdict

**FAIL**

The module fails due to a **Critical Grammar Scope Violation**. The Integration Challenge text is written entirely in the **Past Tense** ("була", "замовила", "платила"), but the Past Tense is not taught until the *next* module (Module 21). This makes the text incomprehensible to a student following the curriculum order. The text must be rewritten in the Present Tense.