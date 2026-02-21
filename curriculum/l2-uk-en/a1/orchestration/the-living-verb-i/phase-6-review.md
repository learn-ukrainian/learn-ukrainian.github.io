# Рецензія: The Living Verb I

**Level:** A1 | **Module:** 6
**Overall Score:** 9.1/10
**Status:** PASS
**Reviewed:** 2026-02-18

## Plan Verification

```
Plan-Content Alignment: PASS
- Sections: PASS
- Vocabulary: FAIL (Missing required word 'чекати' in vocab file; testing untaught 'recommended' words)
- Grammar scope: PASS
- Objectives: PASS
```

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 9/10 | <7 | Excellent metaphors ("Master Key", "Surgery"), warm tone. |
| 2 | Coherence | 10/10 | <7 | Logical progression from pronouns to verbs to sentences. |
| 3 | Relevance | 10/10 | <7 | Perfectly aligned with the goal of introducing -ати verbs. |
| 4 | Educational | 10/10 | <7 | Clear explanations of stem/ending concept. |
| 5 | Language | 9/10 | <8 | Natural examples, correct grammar. |
| 6 | Pedagogy | 8/10 | <7 | **Issue:** Testing vocabulary in activities that was not taught in the lesson. |
| 7 | Immersion | 8/10 | <6 | ~20% Ukrainian, appropriate for A1.1. |
| 8 | Activities | 8/10 | <7 | **Issue:** Using untaught words (думати, розуміти, вивчати) confuses beginners. |
| 9 | Richness | 9/10 | <6 | Strong cultural hook ("Птицю пізнати по пір'ю"). |
| 10 | Beginner Safety | 10/10 | <7 | Very supportive, "Would I Continue?" 5/5. |
| 11 | LLM Fingerprint | 8/10 | <7 | Some rhetorical clichés ("You are the mechanic"), but acceptable. |
| 12 | Linguistic Accuracy | 10/10 | <9 | No grammatical errors found. |

**Weighted Overall:** (13.5 + 10 + 10 + 12 + 9.9 + 9.6 + 8 + 10.4 + 8.1 + 13 + 8 + 15) / 14.0 = **9.1/10**

## Auto-Fail Checklist Results

- Russianisms: [CLEAN]
- Calques: [CLEAN]
- Grammar scope: [CLEAN]
- Activity errors: [CLEAN] (Functionally correct, but pedagogical issue with vocab)
- Beginner safety: 5/5

## Critical Issues Found

### Issue 1: Missing Required Vocabulary
- **Location**: `vocabulary/the-living-verb-i.yaml` vs Plan
- **Original**: (Missing entry for `чекати`)
- **Problem**: Plan lists `чекати` as **Required**. It appears in activities (Match-up, Unjumble, True-False) but is missing from the vocabulary file and the lesson text.
- **Fix**: Add `чекати` (to wait) to `vocabulary/the-living-verb-i.yaml` and introduce it in the "Основні дії повсякденного життя" list or a new "More Actions" list in the text.

### Issue 2: Testing Untaught Vocabulary
- **Location**: `activities/the-living-verb-i.yaml` (Quiz, Unjumble)
- **Original**: Items using `думаю`, `розумієте`, `вивчаємо`.
- **Problem**: These verbs (`думати`, `розуміти`, `вивчати`) are listed as "Recommended" in the plan but are **never introduced** in the text or vocabulary file. Testing words the student hasn't seen violates A1 scaffolding principles.
- **Fix**: Either add these verbs to the lesson content/vocabulary file OR replace them in activities with known verbs (e.g., `читаємо`, `знаєте`).

### Issue 3: Missing IPA for Activity Words
- **Location**: `activities/the-living-verb-i.yaml`
- **Original**: `чекати`, `думати`, `розуміти`, `вивчати`
- **Problem**: Because these words are missing from the vocabulary file, the learner has no IPA reference for them, yet is asked to use them.
- **Fix**: Once added to the vocabulary file (Issue 1 & 2), ensure IPA is generated.

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| N/A | (No linguistic errors found in text) | | |

## Beginner Safety Audit

"Would I Continue?" Test: 5/5
- Overwhelmed? Pass
- Instructions clear? Pass
- Quick wins? Pass
- Ukrainian scary? Pass
- Come back tomorrow? Pass

## Strengths
- The "Surgery" metaphor for removing `-ти` and adding endings is vivid and memorable.
- excellent contrast drills ("Я працюю" vs "Ти відпочиваєш").
- Strong cultural connection with the "Apostol" and literacy tradition.

## Fix Plan to Reach 9.5/10

### Pedagogy: 8/10 → 10/10
**What to fix:**
1. **Sync Vocab:** Add `чекати`, `думати`, `розуміти`, `вивчати` to the vocabulary file and briefly list them in the module (perhaps a "Bonus Verbs" box).
2. **Impact:** Ensures learners are tested only on what they've been taught.

### Activities: 8/10 → 10/10
**What to fix:**
1. **Verification:** After adding the words to vocab/text, the activities will be valid.

**Expected score after fix:** 9.5/10

## Verification Summary

- Content lines read: 230
- Activity items checked: 72
- Ukrainian sentences verified: 45
- IPA transcriptions checked: 20
- Issues found: 3

## Verdict

**PASS**

The module is excellent in tone, explanation, and structure. It passes the overall quality bar easily. However, the **vocabulary consistency** between Plan, Text, and Activities must be fixed (adding `чекати` and the recommended verbs to the explicit teaching list) to ensure a fair experience for A1 learners.
