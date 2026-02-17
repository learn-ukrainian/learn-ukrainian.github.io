        # Phase 6b: Apply Prose Fixes

        Read the review below and fix the issues in the content file.

        ## Review

        # Рецензія: Description: Adverbs

**Level:** A1 | **Module:** 28
**Overall Score:** 8.4/10
**Status:** PASS
**Reviewed:** 2026-02-16

## Plan Verification

```
Plan-Content Alignment: PASS
- Sections: PASS (Consolidated in Meta/Content but covers all Plan points)
- Vocabulary: PASS (All required words present: добре, погано, швидко, etc.)
- Grammar scope: PASS (Adverbs of manner, frequency, intensity covered)
- Objectives: PASS
```

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 8/10 | <7 | Encouraging tone, but word count (2080 vs 750) is overwhelming for A1. |
| 2 | Coherence | 9/10 | <7 | Logical flow from formation to usage to practice. |
| 3 | Relevance | 10/10 | <7 | Highly relevant topic (How?, How often?). |
| 4 | Educational | 9/10 | <7 | Clear explanations of -ий -> -о transformation. |
| 5 | Language | 8/10 | <8 | Good simple Ukrainian, but IPA stress marks are inconsistent in the second half. |
| 6 | Pedagogy | 9/10 | <7 | Strong scaffolding, good use of "double negation" myth-buster. |
| 7 | Immersion | 7/10 | <6 | 36% is acceptable for A1.3, but heavily English-reliant. |
| 8 | Activities | 10/10 | <7 | Excellent variety (Sort, Match, Quiz, Unjumble). |
| 9 | Richness | 9/10 | <6 | Cultural notes on Lviv coffee and "Добре" are excellent. |
| 10 | Beginner Safety | 8/10 | <7 | "Would I Continue?" 4/5. Supportive, but the length is daunting. |
| 11 | LLM Fingerprint | 7/10 | <7 | Repetitive "Imagine" (Уявіть...) hooks (3 times). |
| 12 | Linguistic Accuracy | 9/10 | <9 | No Russianisms found; grammar is correct. |

**Weighted Overall:** (12 + 9 + 10 + 10.8 + 8.8 + 10.8 + 7 + 13 + 8.1 + 10.4 + 7 + 13.5) / 14.0 = **8.53/10**

## Auto-Fail Checklist Results

- Russianisms: [CLEAN]
- Calques: [CLEAN]
- Grammar scope: [CLEAN]
- Activity errors: [CLEAN]
- Beginner Safety: 4/5

## Critical Issues Found

### Issue 1: Inconsistent IPA Stress Marks
- **Location**: Lines 158, 164, 166, 183-185
- **Original**: `[ja zaʋʒdɪ sɲidaju ʃʋɪdkɔ]`, `[tut ɦarnɔ]`
- **Problem**: The IPA transcriptions in the "Practice" sections suddenly stop using stress marks (ˈ), unlike the earlier sections (`[ˈdɔ.bre]`). This is critical for A1 learners.
- **Fix**: Add stress marks. E.g., `[jɑ zɐu̯ˈʒdɪ ˈsɲidɑju ˈʃʋɪdko]`.

### Issue 2: Repetitive LLM "Hook" Pattern
- **Location**: Lines 7 ("Уявіть: ми п’ємо..."), 82 ("Уявіть ваш тиждень"), 142 ("Уявіть: ви критик")
- **Original**: Multiple sections start with "Imagine..." (Уявіть...).
- **Problem**: Structural monotony/LLM fingerprint.
- **Fix**: Vary the openings. E.g., Change Line 82 to direct address: "Let's look at your schedule." (Подивімося на ваш графік.).

### Issue 3: Content Bloat
- **Location**: Entire Module
- **Original**: 2080 words
- **Problem**: The word count is 277% of the 750-word target. While extra explanation is good, this is excessive and risks cognitive overload.
- **Fix**: Tighten the English explanations. Fo

        ## Files

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/description-adverbs.md`

        ## Instructions

        1. Fix issues from the review — word/sentence changes, grammar, clarity
        2. Skip major structural rewrites
        3. After fixing, run IPA lint: `.venv/bin/python scripts/lint_ipa.py /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/description-adverbs.md --fix`
