        # Phase 6b: Apply Prose Fixes

        Read the review below and fix the issues in the content file.

        ## Review

        # Рецензія: Body & Health

**Level:** A1 | **Module:** 31
**Overall Score:** 6.9/10
**Status:** FAIL
**Reviewed:** 2026-02-17

## Plan Verification

```
Plan-Content Alignment: FAIL
- Sections: PASS (All sections present)
- Vocabulary: PASS (Required words present)
- Grammar scope: FAIL (Missing explicit "Треба + Infinitive" instruction required by plan)
- Objectives: PASS
```

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 6/10 | <7 | Module is 2112 words (257% of target), overwhelming for A1 learners. Robotic tone. |
| 2 | Coherence | 8/10 | <7 | Logical flow is good, sections connect well. |
| 3 | Relevance | 9/10 | <7 | Topic is highly relevant and useful. |
| 4 | Educational | 8/10 | <7 | Good explanations, but missing the "Треба" grammar point from plan. |
| 5 | Language | 9/10 | <8 | Ukrainian is generally correct and natural. |
| 6 | Pedagogy | 7/10 | <7 | PPP structure used, but Presentation phase is text-heavy and repetitive. |
| 7 | Immersion | 5/10 | <6 | 38% is far below the A1.3 target of 60-80% (per Review Guidance). Too much English. |
| 8 | Activities | 8/10 | <7 | Good variety and relevance. |
| 9 | Richness | 7/10 | <6 | Cultural notes are good, but text style is repetitive and robotic. |
| 10 | Beginner Safety | 5/10 | <7 | "Would I Continue?" 2/5. Massive text volume (2.5x target) causes cognitive overload. |
| 11 | LLM Fingerprint | 4/10 | <7 | Extreme structural monotony: "Imagine...", "You are...", "Ukrainians are...". |
| 12 | Linguistic Accuracy | 9/10 | <9 | No major errors found. |

**Weighted Overall:** 6.9/10

## Auto-Fail Checklist Results

- Russianisms: [CLEAN]
- Calques: [CLEAN]
- Grammar scope: [FAIL] - Missing "Треба + Infinitive"
- Activity errors: [CLEAN]
- Beginner Safety: 2/5 (Overwhelming length)

## Critical Issues Found

### Issue 1: LLM Fingerprint / Structural Monotony
- **Location**: Throughout the module (Intro, Pharmacy, Doctor sections)
- **Original**:
    - Line 8: «Уявіть: ви хворі. Ви у лікаря. Треба знати слова.»
    - Line 67: «Уявіть: ви гуляєте. Ви бачите знак. Ви йдете всередину.»
    - Line 95: «Отже, ви знаєте симптоми. Час діяти. Українці хворіють.»
    - Line 146: «Ви знаєте симптоми. У вас є ліки. А як щодо роботи?»
- **Problem**: Extremely repetitive, staccato sentence structure (Short sentence. Short sentence. Short sentence.). It sounds like a robotic tutor and creates a monotonous reading experience.
- **Fix**: Rewrite these introductions to be more natural and varied. Use connecting words and varied sentence lengths. E.g., "When you get sick in Ukraine, you will likely need to visit a pharmacy."

### Issue 2: Plan Deviation (Missing Grammar)
- **Location**: Section "В аптеці та у лікаря: Лікування"
- **Original**: «Лікар каже: ми відпочиваємо.» / «Advice: Лежіть. Пийте багато води.»
- **Problem**: The Plan explicitly required: "Grammar connection: Using 'треба' (need) + infinitive for advice (

        ## Files

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/body-and-health.md`

        ## Instructions

        1. Fix issues from the review — word/sentence changes, grammar, clarity
        2. Skip major structural rewrites
        3. After fixing, run IPA lint: `.venv/bin/python scripts/lint_ipa.py /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/body-and-health.md --fix`
