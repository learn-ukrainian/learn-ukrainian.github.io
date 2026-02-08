# Рецензія: The Living Verb II

**Level:** A1 | **Module:** 08
**Overall Score:** 7.9/10
**Status:** FAIL
**Reviewed:** 2026-02-08

## Plan Verification

```
Plan-Content Alignment: FAIL
- Sections: PASS (All key grammar points covered)
- Vocabulary: FAIL (YAML file contains only 2 words; content teaches ~15 verbs)
- Grammar scope: PASS
- Objectives: PASS
```

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 7/10 | <7 | Quiz asks questions about untaught forms (reflexives), causing frustration. |
| 2 | Coherence | 9/10 | <7 | Logic flows well, distinct sections. |
| 3 | Relevance | 10/10 | <7 | Highly relevant verbs for daily communication. |
| 4 | Educational | 7/10 | <7 | Testing untaught material undermines the learning path. |
| 5 | Language | 10/10 | <8 | Ukrainian examples are natural and grammatically correct. |
| 6 | Pedagogy | 6/10 | <7 | Explicitly says "reflexives in Module 09" then tests them in Module 08 activities. |
| 7 | Immersion | 8/10 | <6 | Good balance of examples. |
| 8 | Activities | 6/10 | <7 | "Fill-in" and "Complete Dialogue" require conjugating `дивитися` (untaught). |
| 9 | Richness | 5/10 | <6 | Vocabulary YAML is virtually empty (2 words). |
| 10 | Beginner Safety | 6/10 | <7 | Unfair activity questions (reflexives) create a "trap" for beginners. |
| 11 | LLM Fingerprint | 10/10 | <7 | Content feels human-curated and specific. |
| 12 | Linguistic Accuracy | 10/10 | <9 | No grammar errors found in content. |

**Weighted Overall:** (10.5 + 9 + 10 + 8.4 + 11 + 7.2 + 8 + 7.8 + 4.5 + 7.8 + 10 + 15) / 14 = **7.80/10**

## Auto-Fail Checklist Results

- Russianisms: [CLEAN]
- Calques: [CLEAN]
- Grammar scope: [FAIL] - Activities require conjugating reflexive verbs (`дивитися`) which are not taught.
- Activity errors: [FAIL] - Multiple items require untaught knowledge.
- Beginner safety: 3/5 (Overwhelmed by unfair questions).

## Critical Issues Found

### Issue 1: Pedagogy/Scope Trap (Reflexive Verbs)
- **Location**: Activities file, `fill-in` (Conjugate the Verb) and `fill-in` (Complete the Dialogue).
- **Original**: `sentence: Ви ___ фільм? answer: дивитеся`, `sentence: Він ___ фільм. answer: дивиться`, `sentence: Ти ___ фільм сьогодні? answer: дивишся`.
- **Problem**: The lesson text explicitly states: *"You'll learn the full pattern in Module 09, but for now, just notice them when they appear!"*. The student has only seen the form `ми дивимося`. They have NOT been taught how to conjugate `-ся` verbs for `ти`, `він`, `ви`, `я`. Testing this is unfair and guarantees failure.
- **Fix**: Replace all instances of `дивитися` in exercises that require conjugation with verbs taught in this module (e.g., `бачити`, `любити`, `хотіти`).

### Issue 2: Missing Vocabulary Metadata
- **Location**: `vocabulary/08-the-living-verb-ii.yaml`
- **Original**: File contains only `Катя` and `іти`.
- **Problem**: The module introduces core vocabulary: `говорити`, `робити`, `бачити`, `любити`, `хотіти`, `їсти`, `пити`, `ходити`, `спати`, `стояти`, `сидіти`, `вчити`, `просити`. These must be in the vocabulary file to be tracked by the system and generated in flashcards.
- **Fix**: Populate the YAML with all 13+ new verbs.

### Issue 3: Conjugation Gap (спати)
- **Location**: Activities file, `fill-in` (Conjugate the Verb).
- **Original**: `sentence: Вони ___. answer: сплять`
- **Problem**: The lesson teaches `спати` as an example `Вона спить` (singular). It does not show the plural `сплять`. While it follows the `-ять` rule, `спати` is slightly irregular (appearing to be First Conjugation `-ати`).
- **Fix**: Add the full conjugation of `спати` to the "Irregular Verbs" or "Key Examples" section, OR change the activity item to `Вона ___` (spyt) which is explicitly taught.

## Beginner Safety Audit

"Would I Continue?" Test: 3/5
- Overwhelmed? **Fail** (When hit with `дивишся/дивитеся` questions I couldn't answer).
- Instructions clear? **Pass**
- Quick wins? **Pass** (Conjugation table is clear).
- Ukrainian scary? **Fail** (Sudden appearance of untaught grammar in quiz).
- Come back tomorrow? **Pass** (If quiz is fixed).

## Fix Plan to Reach 9/10

### Pedagogy & Activities: 6/10 → 9/10

**What to fix:**
1.  **Activity `fill-in` (Conjugate the Verb)**:
    -   Item 5: Replace `Ви ___ фільм? (дивитеся)` with `Ви ___ каву? (п'єте)`.
    -   Item 7: Replace `Він ___ фільм. (дивиться)` with `Він ___ книгу. (читає)` or `Він ___ маму. (бачить)`.
2.  **Activity `fill-in` (Complete the Dialogue)**:
    -   Item 12: Replace `Ти ___ фільм сьогодні? (дивишся)` with `Ти ___ цей фільм? (бачиш)` or `Ти ___ спати? (хочеш)`.
    -   Item 13: Replace `Так, я ___ фільм! (дивлюся)` with matching verb.

### Richness: 5/10 → 10/10

**What to fix:**
1.  **File `vocabulary/08-the-living-verb-ii.yaml`**: Add the following entries with IPA and translations:
    -   говорити
    -   робити
    -   бачити
    -   любити
    -   хотіти
    -   їсти
    -   пити
    -   ходити
    -   спати
    -   стояти
    -   сидіти
    -   вчити
    -   просити
    -   дякувати (mentioned in text)

### Projected Overall After Fixes

Recalculating with Pedagogy=9, Activities=9, Richness=10, Beginner Safety=9:
Weighted Overall: **9.2/10**

## Verdict

**FAIL**

The module content is linguistically excellent, but the activities are broken because they aggressively test grammar (reflexive conjugation) that the lesson explicitly defers to Module 09. This creates a "trap" for learners. Additionally, the vocabulary metadata is missing, which breaks the system's flashcard generation. These are quick but blocking fixes.
