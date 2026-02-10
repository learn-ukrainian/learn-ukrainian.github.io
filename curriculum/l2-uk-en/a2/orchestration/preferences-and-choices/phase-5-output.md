===REVIEW_START===
# Рецензія: Preferences and Choices

**Level:** A2 | **Module:** 20
**Overall Score:** 8.3/10
**Status:** FAIL
**Reviewed:** 2026-02-09

## Plan Verification

```
Plan-Content Alignment: [PASS]
- Sections: [all present]
- Vocabulary: [70+ items, mostly aligned, 1 archaic found]
- Grammar scope: [clean]
- Objectives: [all covered]
```

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 9/10 | <7 | Clear explanations, good cultural "social dance" metaphor. |
| 2 | Coherence | 9/10 | <7 | Logical progression from casual to formal to hypothetical. |
| 3 | Relevance | 10/10 | <7 | Core A2 topic, highly relevant for daily life. |
| 4 | Educational | 9/10 | <7 | Strong contrastive analysis (English Subject vs Ukrainian Dative). |
| 5 | Language | 8/10 | <8 | Grammar error in activity answer key (`Що` vs `Чому`). |
| 6 | Pedagogy | 8/10 | <7 | Subjective error correction (marking male form as error without context). |
| 7 | Immersion | 8/10 | <6 | Good balance, Ukrainian headers used. |
| 8 | Activities | 5/10 | <7 | **FAIL**: Grammar error in correct answer, ambiguous multiple correct answers, subjective "false error". |
| 9 | Richness | 9/10 | <6 | Cultural context about hospitality and Lviv coffee culture implies depth. |
| 10 | Beginner Safety | 8/10 | <7 | Good, but "false errors" in activities would frustrate a learner. |
| 11 | LLM Fingerprint | 9/10 | <7 | Content feels curated and specific. |
| 12 | Linguistic Accuracy | 8/10 | <9 | **FAIL**: Grammatical case error in activity key. |

**Weighted Overall:** 115.7 / 14.0 = **8.26/10**

## Auto-Fail Checklist Results

- Russianisms: [CLEAN]
- Calques: [CLEAN]
- Grammar scope: [CLEAN]
- Activity errors: **[FAIL]** (Lines 117, 137, 240)
- Beginner safety: 4/5 (Frustration risk in activities)

## Critical Issues Found

### Issue 1: Grammar Error in Activity Key
- **Location**: Line 240 / Activity `translate`
- **Original**: `question: What do you prefer? ... text: Що ти віддаєш перевагу? correct: true`
- **Problem**: `Віддавати перевагу` requires the Dative case. `Що` is Nominative/Accusative. The correct form is `Чому`.
- **Fix**: Change option to `Чому ти віддаєш перевагу?` or replace with `Що ти вибираєш?`.

### Issue 2: False Error (Subjective Gender)
- **Location**: Line 137 / Activity `error-correction`
- **Original**: `sentence: Я б вибрав каву. error: вибрав answer: вибрала explanation: Feminine past: вибрала.`
- **Problem**: `Я б вибрав` is grammatically correct for a male speaker. Marking it as an error without context (e.g., "Oksana says...") confuses male learners.
- **Fix**: Change sentence to clearly imply a female subject, e.g., `Вона б вибрав каву.` or `Марія сказала: "Я б вибрав..."`.

### Issue 3: Ambiguous Multiple Correct Answers
- **Location**: Line 227 / Activity `translate`
- **Original**: `source: Coffee is better than tea. ... text: Кава краща за чай. correct: true ... text: Кава краща ніж чай. correct: true`
- **Problem**: Both options are correct and marked true. In a single-choice UI, this is broken or confusing.
- **Fix**: Keep `Кава краща за чай` as true. Change the second option to a distractor, e.g., `Кава краще чай` (incorrect syntax).

### Issue 4: Archaic Vocabulary
- **Location**: Vocabulary YAML & Activity `group-sort`
- **Original**: `lemma: волити ... translation: to prefer`
- **Problem**: `Волити` is archaic/literary and very rare in modern spoken Ukrainian compared to `віддавати перевагу` or `хотіти`.
- **Fix**: Remove `волити` from vocabulary and activities.

### Issue 5: Unnatural Phrasing
- **Location**: Line 195 / Activity `unjumble`
- **Original**: `Я зазвичай віддаю повну перевагу тільки міцній чорній каві`
- **Problem**: `Віддаю повну перевагу` is not a standard collocation. It sounds like a calque of "give full preference".
- **Fix**: Simplify to `Я зазвичай віддаю перевагу тільки міцній чорній каві`.

## Fix Plan to Reach 9/10

### Activities: 5/10 → 9/10

**What to fix:**
1.  **Line 240 (`translate`):** Change `Що ти віддаєш перевагу?` to `Чому ти віддаєш перевагу?`. (Fixes grammar error).
2.  **Line 137 (`error-correction`):** Change sentence to `Вона б вибрав каву.` -> Error `вибрав` -> Answer `вибрала`. (Fixes subjective error).
3.  **Line 227 (`translate`):** Change option `Кава краща ніж чай` (correct) to `Кава краще чай` (incorrect). (Fixes ambiguity).
4.  **Line 117 (`group-sort`):** Remove `Я волію` item. Add `Мені до вподоби` (neutral) or remove item entirely.
5.  **Line 195 (`unjumble`):** Remove word `повну` from the list and answer.
6.  **Line 206 (`unjumble`):** Change `робити важку справу` (tautology) to `виконувати важку роботу` or simplify sentence.

### Language: 8/10 → 10/10

**What to fix:**
1.  **Vocabulary YAML:** Remove `волити`.
2.  **Activity corrections:** (See above).

**Expected score after fix:** 9.5/10

### Projected Overall After Fixes

```
Activities -> 9, Language -> 10, Pedagogy -> 9, Linguistic Accuracy -> 10.
Overall = ~9.4/10
```

## Verification Summary

- Content lines read: ~140
- Activity items checked: 10 types, ~50 items
- Ukrainian sentences verified: ~40
- IPA transcriptions checked: N/A (Vocab file read separately)
- Issues found: 5
- Naturalness score recommendation: 9/10

## Verdict

**FAIL**

Blocking issues in Activities file: grammar error in answer key (`Що` vs `Чому`), subjective error correction confusing for male learners, and ambiguous multiple correct answers.

===REVIEW_END===
