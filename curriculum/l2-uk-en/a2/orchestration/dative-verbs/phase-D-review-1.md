# Рецензія: Dative Verbs

**Level:** A2 | **Module:** 3
**Overall Score:** 8.6/10
**Status:** FAIL
**Reviewed:** 21 February 2026

## Plan Verification

Plan-Content Alignment: FAIL
- Sections: PASS (all sections from outline are present)
- Vocabulary: FAIL (7/15 required words from plan; 8 missing: вибачати, пробачати, заздрити, симпатизувати, співчувати, підходити, вистачати, бракувати)
- Grammar scope: PASS
- Objectives: PASS

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 9/10 | <7 | Good progression from theory to practice; supportive and structured tone. |
| 2 | Coherence | 9/10 | <7 | Concepts are logically grouped (Pure Dative, Double Object, Impersonal). |
| 3 | Relevance | 8/10 | <7 | Missed 8 required vocabulary words from the module plan. |
| 4 | Educational | 8/10 | <7 | Incomplete vocabulary coverage limits the educational scope. |
| 5 | Language | 8/10 | <8 | Minor Russian calques ("нема за що", "один одному") and clunky phrasing ("зробити толоку"). |
| 6 | Pedagogy | 8/10 | <7 | Internal contradiction: teaches "-еві" is preferred for men, but corrects "вчителя" to "вчителю" in a table. |
| 7 | Immersion | 9/10 | <6 | Meets target. Scaffolded English used effectively for grammar theory. |
| 8 | Activities | 8/10 | <7 | Activity 4 tests stylistic preference (-ові vs -у) by presenting a grammatically valid distractor, which is unfair in a multiple-choice format. |
| 9 | Richness | 9/10 | <6 | Good cultural context (Толока) and realistic dialogues. |
| 10 | Beginner Safety | 10/10 | <7 | "Would I Continue?" test passed 5/5. Excellent supportive pacing. |
| 11 | LLM Fingerprint | 9/10 | <7 | Natural voice, no repetitive structural markers found. |
| 12 | Linguistic Accuracy | 8/10 | <9 | Calques and stylistic inconsistencies with standard Ukrainian norms. |

**Weighted Overall:** (13.5 + 9.0 + 8.0 + 9.6 + 8.8 + 9.6 + 9.0 + 10.4 + 8.1 + 13.0 + 9.0 + 12.0) / 14.0 = **8.57/10**

## Auto-Fail Checklist Results

- Russianisms: CLEAN
- Calques: FAIL («Нема за що», «один одному», «зробити толоку»)
- Grammar scope: CLEAN
- Activity errors: FAIL (Grammatically valid distractor used in quiz)
- Beginner safety: 5/5

## Critical Issues Found

### Issue 1: Calques & Russian Interference
- **Location**: Line 403 / Section "Діалог 1: Толока (The Cleanup)"
- **Original**: «**Петро:** Нема за що. Ми повинні допомагати **один одному**.»
- **Problem**: «Нема за що» and «один одному» are literal translations (calques) from Russian.
- **Fix**: Replace with «**Петро:** Прошу. Ми повинні допомагати **одне одному**.»

### Issue 2: Poor Stylistic Phrasing
- **Location**: Line 400 / Section "Діалог 1: Толока (The Cleanup)"
- **Original**: «**Оксана:** Ми хочемо зробити толоку в суботу.»
- **Problem**: «Зробити толоку» is a poor, unnatural collocation. In Ukrainian, one should «влаштувати толоку» or «провести толоку».
- **Fix**: Replace with «**Оксана:** Ми хочемо влаштувати толоку в суботу.»

### Issue 3: Internal Pedagogical Contradiction
- **Location**: Line 290 / Section "Drill 2: The "Dyakuyu" Fix"
- **Original**: «| Ми дякуємо *вчителя*. | Ми дякуємо **вчителю**. | *Дякувати (кому?)* — Dative. |»
- **Problem**: The module previously taught that male animate nouns prefer the long ending "-еві/-ові" to sound more "Ukrainian", but here it explicitly corrects to the short ending "-у".
- **Fix**: Replace «вчителю» with «вчителеві».

### Issue 4: Valid Distractor in Quiz
- **Location**: Line 168 / `activities/dative-verbs.yaml`
- **Original**: `options: ['клієнтові', 'клієнта', 'клієнту', 'клієнтом']`
- **Problem**: Both "клієнтові" and "клієнту" are grammatically valid Dative endings. A multiple-choice question should not penalize a grammatically correct option unless explicitly testing stylistic nuance (which the instruction doesn't specify).
- **Fix**: Change the distractor `клієнту` to `клієнті`.

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| 403 | «Нема за що. Ми повинні допомагати один одному.» | «Прошу. Ми повинні допомагати одне одному.» | Calque |
| 400 | «Ми хочемо зробити толоку в суботу.» | «Ми хочемо влаштувати толоку в суботу.» | Calque |
| 290 | «Ми дякуємо вчителю.» | «Ми дякуємо вчителеві.» | Grammar (Stylistics) |

## Beginner Safety Audit

"Would I Continue?" Test: 5/5
- Overwhelmed? Pass
- Instructions clear? Pass
- Quick wins? Pass
- Ukrainian scary? Pass
- Come back tomorrow? Pass

## Strengths
- Excellent use of the "Толока" cultural concept to explain the deeper meaning of the word "допомагати". The breakdown of "Подобатися" (impersonal vs active logic) is also exceptionally clear for beginners.

## Fix Plan to Reach 9/10

### Language: 8/10 → 9/10
**What to fix:**
1. Line 403: Change «Нема за що. Ми повинні допомагати один одному.» → «Прошу. Ми повинні допомагати одне одному.» — Removes Russian calques.
2. Line 400: Change «Ми хочемо зробити толоку в суботу.» → «Ми хочемо влаштувати толоку в суботу.» — Improves natural collocation.

### Pedagogy: 8/10 → 9/10
**What to fix:**
1. Line 290: Change «Ми дякуємо вчителю.» to «Ми дякуємо вчителеві.» — Resolves internal rule contradiction.

### Activities: 8/10 → 9/10
**What to fix:**
1. `activities/dative-verbs.yaml`: Change option `клієнту` to `клієнті` — Removes the ambiguity of having two valid case endings in a single-choice question.

**Expected score after fix:** 9.2/10

### Projected Overall After Fixes
(13.5 + 9.0 + 8.0 + 9.6 + 9.9 + 10.8 + 9.0 + 11.7 + 8.1 + 13.0 + 9.0 + 12.0) / 14.0 = **8.82/10**

## Verification Summary

- Content lines read: 418
- Activity items checked: 45
- Ukrainian sentences verified: 52
- IPA transcriptions checked: 38
- Issues found: 4

## Verdict

**FAIL**

While the pedagogical tone and structure are excellent, the module contains several Russian calques ("нема за що", "один одному") and an internal contradiction regarding the Dative "-ові/-еві" rule. Furthermore, it completely misses 8 mandatory vocabulary words from the curriculum plan. Inline fixes can repair the grammar, but the vocabulary scope gap remains blocking.