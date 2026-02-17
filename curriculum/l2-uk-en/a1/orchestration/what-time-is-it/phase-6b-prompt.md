        # Phase 6b: Apply Prose Fixes

        Read the review below and fix the issues in the content file.

        ## Review

        # Рецензія: What Time Is It?

**Level:** A1 | **Module:** 23
**Overall Score:** 8.4/10
**Status:** FAIL
**Reviewed:** 2026-02-16

## Plan Verification

```
Plan-Content Alignment: PASS
- Sections: PASS (Matches Meta and Plan)
- Vocabulary: WARNING (Word "рік" required but missing from text)
- Grammar scope: PASS
- Objectives: PASS
```

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 9/10 | <7 | Friendly tone, excellent pacing for A1. |
| 2 | Coherence | 9/10 | <7 | Logical progression from hours to days/months. |
| 3 | Relevance | 10/10 | <7 | Essential daily skill. |
| 4 | Educational | 9/10 | <7 | Clear explanations of "digital style" vs traditional. |
| 5 | Language | 7/10 | <8 | Several calques and unnatural lexical choices (сезони, імена). |
| 6 | Pedagogy | 9/10 | <7 | Good scaffolding, "Myth-buster" is helpful. |
| 7 | Immersion | 6/10 | <6 | 37% is low for A1.3 (Target 60-80% per guide, though audit allowed 35%). |
| 8 | Activities | 10/10 | <7 | Massive volume (120+ items), excellent variety. |
| 9 | Richness | 8/10 | <6 | Good Ukrzaliznytsia context, slightly English-heavy. |
| 10 | Beginner Safety | 9/10 | <7 | "Would I Continue?" 5/5. Very safe. |
| 11 | LLM Fingerprint | 9/10 | <7 | Natural variation, no obvious AI patterns. |
| 12 | Linguistic Accuracy | 8/10 | <9 | Minor stress/IPA issues, mostly good. |

**Weighted Overall:** (13.5 + 9 + 10 + 10.8 + 7.7 + 10.8 + 6 + 13 + 7.2 + 11.7 + 9 + 12) / 14.0 = **8.62/10** (Adjusted manually: Language failure drags it down).

## Auto-Fail Checklist Results

- Russianisms: CLEAN
- Calques: DETECTED ("Україна має сезони", "Імена природи")
- Grammar scope: CLEAN
- Activity errors: CLEAN
- Beginner Safety: 5/5

## Critical Issues Found

### Issue 1: Lexical Error (Calque/Anglicism)
- **Location**: Section "Чотири сезони"
- **Original**: «Україна має чотири сезони.»
- **Problem**: "Сезони" usually refers to tourist/hunting/TV seasons. The standard term for winter/spring/summer/autumn is "пори року". Also "Україна має" is a clunky calque of "Ukraine has".
- **Fix**: «В Україні є чотири пори року.»

### Issue 2: Lexical Error (Wrong noun)
- **Location**: Section "Місяці та пори року"
- **Original**: «Імена природи»
- **Problem**: "Ім'я" (Name) is used for people or pets. For inanimate objects/concepts, we use "Назва" (Name/Title).
- **Fix**: «Назви в природі» or «Природні назви»

### Issue 3: Contextual Semantics
- **Location**: Section "Прийменники часу"
- **Original**: «Магазин тут з ранку до вечора.»
- **Problem**: "Магазин тут" means "The shop is located here". It does not communicate opening hours.
- **Fix**: «Магазин працює з ранку до вечора.»

### Issue 4: Missing Vocabulary
- **Location**: Entire Text
- **Original**: (Missing)
- **Problem**: The word "рік" (year) is in the required vocabulary list and essential for the "Months/Seasons" section, but never appears in the text.
- **Fix**: Add a sentence lik

        ## Files

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/what-time-is-it.md`

        ## Instructions

        1. Fix issues from the review — word/sentence changes, grammar, clarity
        2. Skip major structural rewrites
        3. After fixing, run IPA lint: `.venv/bin/python scripts/lint_ipa.py /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/what-time-is-it.md --fix`
