# Рецензія: Questions & Negation

**Level:** A1 | **Module:** 7
**Overall Score:** 8.2/10
**Status:** FAIL
**Reviewed:** 2026-02-15

## Plan Verification

```
Plan-Content Alignment: [FAIL]
- Sections: [PASS]
- Vocabulary: [FAIL] 6 words from plan missing in content (куди, чому, як, скільки, завжди, ніколи)
- Grammar scope: [PASS] Generally clean
- Objectives: [FAIL] Missing "frequency adverbs" and associated double negation rule
```

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 9/10 | <7 | Engaging tone, clear structure. |
| 2 | Coherence | 9/10 | <7 | Logical flow. |
| 3 | Relevance | 9/10 | <7 | Highly relevant content. |
| 4 | Educational | 6/10 | <7 | **FAIL**: Missed required learning objectives (frequency/double negation) and tested untaught vocab. |
| 5 | Language | 10/10 | <8 | Ukrainian examples are natural and correct. |
| 6 | Pedagogy | 6/10 | <7 | **FAIL**: Activities test concepts not taught in the lesson (assessment mismatch). |
| 7 | Immersion | 8/10 | <6 | Good usage of examples. |
| 8 | Activities | 7/10 | <7 | Good types, but marred by scope creep errors. |
| 9 | Richness | 9/10 | <6 | ALF cultural context is excellent. |
| 10 | Beginner Safety | 9/10 | <7 | Welcoming, "safe" explanation of grammar. |
| 11 | LLM Fingerprint | 9/10 | <7 | Minimal robotic feeling. |
| 12 | Linguistic Accuracy | 10/10 | <9 | No errors found in the text examples. |

**Weighted Overall:** 8.2/10

## Auto-Fail Checklist Results

- Russianisms: [CLEAN]
- Calques: [CLEAN]
- Grammar scope: [List] Activity uses future tense "буде".
- Activity errors: [List] Testing untaught vocabulary.
- Beginner safety: 5/5

## Critical Issues Found

### Issue 1: Missing Learning Objective (Double Negation)
- **Location**: Entire file
- **Original**: (Missing)
- **Problem**: The plan requires teaching "frequency adverbs (завжди, часто, іноді, ніколи)". In a "Negation" module, this implies teaching the Double Negation rule (e.g., "Я **ніколи не** сплю"). This is a critical Ukrainian grammar feature that is completely absent.
- **Fix**: Add a subsection "Double Negation: Never say Never alone" explaining that *ніколи* requires *не*.

### Issue 2: Assessment Mismatch (Untaught Vocab)
- **Location**: Activities `match-up` "Питальні слова" and `fill-in` "Оберіть правильне слово"
- **Original**: Tests words `чому`, `скільки`, `як`, `куди`.
- **Problem**: These words are listed in the vocabulary file but are NEVER introduced, defined, or explained in the content text. The learner has no way to know them.
- **Fix**: Either add a section introducing these "Advanced Question Words" or remove them from the activities.

### Issue 3: Grammar Scope Creep in Activity
- **Location**: `curriculum/l2-uk-en/a1/activities/questions-and-negation.yaml`, line 219 (approx)
- **Original**: "___ це буде?" -> Answer "Коли"
- **Problem**: "буде" is the Future tense of "бути". Future tense is not yet taught (Module 7).
- **Fix**: Change to present tense: "___ це?" (When is this?) or "___ цей урок?" (When is this lesson?).

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| Activity | "___ це буде?" | "Коли цей урок?" | Scope (Future tense) |

## Beginner Safety Audit

"Would I Continue?" Test: 5/5
- Overwhelmed? Pass
- Instructions clear? Pass
- Quick wins? Pass
- Ukrainian scary? Pass
- Come back tomorrow? Pass

Emotional beats:
- Welcome: Yes ("Imagine we are neighbors...")
- Curiosity: Yes ("ALF is a legend")
- Quick wins: Yes ("No 'Do' gymnastics")

## Strengths
- Excellent cultural integration with the ALF example.
- Very clear, comforting explanation of why "Do" is not needed.
- "The Politeness Scale" is a great mental model for learners.

## Fix Plan to Reach 9/10

### Educational: 6/10 → 9/10
**What to fix:**
1. **Section "Теорія"**: Add a new H3 subsection **"Ніколи не кажи ніколи" (Double Negation)**.
   - Explain that words like *ніколи* (never) require *не* (not).
   - Example: *Я ніколи не знаю* (I never know).
   - This covers the missing "frequency adverbs" objective and the "instructional gap" for negation.
2. **Section "Теорія"**: Add a brief list or table for the "Other Question Words" (`чому`, `скільки`, `як`, `куди`) under the "Question Words" section, so the activities are valid.

### Pedagogy: 6/10 → 9/10
**What to fix:**
1. **Activities**: Once the content above is added, the activities will be valid.
2. **Activity `fill-in`**: Replace "___ це буде?" with "___ цей урок?" to remove future tense.

### Projected Overall After Fixes
With these gaps closed, the Educational and Pedagogical scores will rise to 9/10, bringing the overall score above 9.0.

## Verification Summary
- Content lines read: ~160
- Activity items checked: 45
- Ukrainian sentences verified: ~40
- IPA transcriptions checked: ~40
- Issues found: 3 critical gaps

## Verdict
**FAIL**

The module fails to meet its own plan objectives (missing frequency adverbs/double negation) and tests students on vocabulary that was never taught. These are structural pedagogical failures that must be fixed before passing.
