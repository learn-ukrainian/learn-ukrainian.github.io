        # Phase 6b: Apply Prose Fixes

        Read the review below and fix the issues in the content file.

        ## Review

        # Рецензія: Mine and Yours

**Level:** A1 | **Module:** 14
**Overall Score:** 7.8/10
**Status:** FAIL
**Reviewed:** 2026-02-16

## Plan Verification

```
Plan-Content Alignment: [PASS]
- Sections: All 5 sections (Warm-up, Presentation, Practice, Production, Cultural Insight) present as defined.
- Vocabulary: All required (8/8) and recommended (4/4) items present.
- Grammar scope: [FAIL] Scope creep into Accusative case in activities.
- Objectives: Addressed, but activities exceed the grammar level specified.
```

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 8/10 | <7 | Helpful neighbor tone is consistent, but metaphors are slightly repetitive. |
| 2 | Coherence | 9/10 | <7 | Logical progression from questioning ownership to polite forms. |
| 3 | Relevance | 9/10 | <7 | High relevance for basic possession in A1. |
| 4 | Educational | 8/10 | <7 | PPP structure followed; grammar explanation is clear. |
| 5 | Language | 8/10 | <8 | Clear Ukrainian, but robotic structural patterns in some explanations. |
| 6 | Pedagogy | 8/10 | <7 | Good use of "Mirror" analogy (despite being an LLM cliché) for gender agreement. |
| 7 | Immersion | 7/10 | <6 | 26% immersion is within the 25-40% target for A1.2. |
| 8 | Activities | 6/10 | <7 | **AUTO-FAIL**: Activities 5 and 7 require Accusative case knowledge (свого, маму). |
| 9 | Richness | 8/10 | <6 | Good use of proverbs and community scenarios. |
| 10 | Beginner Safety | 7/10 | <7 | Beginner might be confused by Accusative forms not explained in text. |
| 11 | LLM Fingerprint | 6/10 | <7 | **AUTO-FAIL**: Clichés ("soul of language", "dance", "heartbeat") and structural monotony in examples. |
| 12 | Linguistic Accuracy | 9/10 | <9 | Ukrainian is grammatically correct, though scope creep is present. |

**Weighted Overall:** (8×1.5 + 9×1.0 + 9×1.0 + 8×1.2 + 8×1.1 + 8×1.2 + 7×1.0 + 6×1.3 + 8×0.9 + 7×1.3 + 6×1.0 + 9×1.5) / 14.0 = 108.6 / 14.0 = **7.76/10**

## Auto-Fail Checklist Results

- Russianisms: [CLEAN]
- Calques: [CLEAN]
- Grammar scope: [FAIL] Accusative case introduced in activities without explanation.
- Activity errors: [FAIL] Items in activities 5 and 7 use non-Nominative forms.
- Beginner safety: 3/5

## Critical Issues Found

### Issue 1: Grammar Scope Creep (Accusative Case)
- **Location**: Activities YAML / Activity 5 & 7
- **Original**: «Він бачить свого друга.», «Я бачу свого тата.», «Вона бачить свою маму.»
- **Problem**: The module focuses on possessive pronouns in Nominative (мій, твій, свій). However, several activity items use the Accusative case («свого», «свою», «тата», «маму», «друга»). A1.2 students haven't learned noun/pronoun endings for direct objects yet.
- **Fix**: Change sentences to Nominative: «Це його друг», «Ось мій тато», «Це моя мама».

### Issue 2: LLM Clichés and Metaphors
- **Location**: Lines 36, 95, 110, 169 / Various sections
- **Original**: «Вони схожі на дзеркала.», «Це як танец

        ## Files

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/mine-and-yours.md`

        ## Instructions

        1. Fix issues from the review — word/sentence changes, grammar, clarity
        2. Skip major structural rewrites
        3. After fixing, run IPA lint: `.venv/bin/python scripts/lint_ipa.py /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/mine-and-yours.md --fix`
