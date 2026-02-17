        # Phase 6b: Apply Prose Fixes

        Read the review below and fix the issues in the content file.

        ## Review

        # Рецензія: Tomorrow - Future Tense

**Level:** A1 | **Module:** 22
**Overall Score:** 6.7/10
**Status:** FAIL
**Reviewed:** 2026-02-16

## Plan Verification

```
Plan-Content Alignment: FAIL
- Sections: Mostly aligned, but Practice Dialogue 2 mismatches Plan (Work vs Vacation).
- Vocabulary: FAIL (Recommended vocabulary tested in activities but NOT taught in content).
- Grammar scope: PASS
- Objectives: PASS
```

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 6/10 | <7 | Activities test vocabulary that was never taught, leading to learner frustration. |
| 2 | Coherence | 8/10 | <7 | Logical flow is generally good. |
| 3 | Relevance | 9/10 | <7 | Topic is highly relevant. |
| 4 | Educational | 6/10 | <7 | Testing untaught material is a critical educational failure. |
| 5 | Language | 8/10 | <8 | Generally good, but "Я буду спати рано" is unnatural. |
| 6 | Pedagogy | 5/10 | <7 | Severe misalignment between taught content and tested content. |
| 7 | Immersion | 4/10 | <6 | 40% is way below the 60-80% target for A1.3. Too much English explanation. |
| 8 | Activities | 5/10 | <7 | Activities 4 and 6 test words not in the text (`обіцяти`, `мріяти`, `планувати`). |
| 9 | Richness | 7/10 | <6 | Good cultural notes (Odesa), but content is verbose in English. |
| 10 | Beginner Safety | 5/10 | <7 | "Would I Continue?" 2/5. Learners will feel set up to fail by the quiz. |
| 11 | LLM Fingerprint | 9/10 | <7 | Content feels relatively natural, avoiding worst AI tropes. |
| 12 | Linguistic Accuracy | 9/10 | <9 | Grammar explanations are accurate. |

**Weighted Overall:** (9.0 + 8.0 + 9.0 + 7.2 + 8.8 + 6.0 + 4.0 + 6.5 + 6.3 + 6.5 + 9.0 + 13.5) / 14.0 = **6.7/10**

## Auto-Fail Checklist Results

- Russianisms: [CLEAN]
- Calques: [CLEAN]
- Grammar scope: [CLEAN]
- Activity errors: [FAIL] (Untaught vocabulary in Quiz)
- Beginner safety: 2/5 (Fail due to unfair testing)

## Critical Issues Found

### Issue 1: Pedagogy / Beginner Safety
- **Location**: Activities 4 (Intentions and Plans) & 6 (Vocabulary Quiz)
- **Original**: Options include «обіцяти», «мріяти», «планувати», «сподіватися».
- **Problem**: These words are listed in the Plan as "Recommended" and in the Vocabulary file, but they are **NEVER TAUGHT** in the Content file (`tomorrow-future-tense.md`). A1 learners cannot answer these questions.
- **Fix**: Add a new section or expand the "Reading Practice" to explicitly use and define these verbs, OR remove them from the activities.

### Issue 2: Immersion Level (A1.3 Violation)
- **Location**: Whole Module
- **Original**: Immersion 40%
- **Problem**: This module is A1.3 (Phase Consolidation). The target immersion is **60-80%**. 40% is appropriate for A1.1, not A1.3. There is too much English "cheerleading" and explanation.
- **Fix**: Rewrite English explanations to be more concise. Convert simple "patter" into Ukrainian with glosses.

### Issue 3: Plan-Content Mismatch

        ## Files

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/tomorrow-future-tense.md`

        ## Instructions

        1. Fix issues from the review — word/sentence changes, grammar, clarity
        2. Skip major structural rewrites
        3. After fixing, run IPA lint: `.venv/bin/python scripts/lint_ipa.py /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/tomorrow-future-tense.md --fix`
