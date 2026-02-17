        # Phase 6b: Apply Prose Fixes

        Read the review below and fix the issues in the content file.

        ## Review

        # Рецензія: Food, Drinks & Shopping

**Level:** A1 | **Module:** 18
**Overall Score:** 8.1/10
**Status:** FAIL
**Reviewed:** 2026-02-16

## Plan Verification

```
Plan-Content Alignment: PASS
- Sections: PASS (Matches concept and Meta outline)
- Vocabulary: PASS (Required and Recommended words present)
- Grammar scope: PASS (Accusative and Genitive covered appropriately)
- Objectives: PASS
```

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 8/10 | <7 | Tone is good, but jarred by factual/grammar errors. |
| 2 | Coherence | 9/10 | <7 | Logical flow and progression. |
| 3 | Relevance | 10/10 | <7 | Highly practical vocabulary for daily life. |
| 4 | Educational | 7/10 | <7 | IPA polluted with Cyrillic characters; grammar mismatch. |
| 5 | Language | 8/10 | <8 | Some calques ("makes shopping easy"). |
| 6 | Pedagogy | 9/10 | <7 | Good scaffolding and clear tables. |
| 7 | Immersion | 10/10 | <6 | 39% (Target 25-40%). Excellent balance. |
| 8 | Activities | 6/10 | <7 | Logic error in "Vegetable or Fruit" (Chicken is neither). |
| 9 | Richness | 8/10 | <6 | Good cultural notes, but one contains a hallucination. |
| 10 | Beginner Safety | 9/10 | <7 | "Would I Continue?" 5/5. |
| 11 | LLM Fingerprint | 8/10 | <7 | Minor structural repetition, generally okay. |
| 12 | Linguistic Accuracy | 6/10 | <9 | Subject-verb mismatch, mixed Cyrillic in IPA. |

**Weighted Overall:** 112.7 / 14.0 = **8.05/10**

## Auto-Fail Checklist Results

- Russianisms: [CLEAN]
- Calques: [LIST] "Це робить покупки легкими", "Ми маємо"
- Grammar scope: [CLEAN]
- Activity errors: [LIST] Chicken in Veggie/Fruit quiz; Broken MD display for Group Sort.
- Beginner safety: 5/5

## Critical Issues Found

### Issue 1: Linguistic Accuracy (IPA)
- **Location**: Throughout the module (e.g., Lines 110, 126, 142)
- **Original**: «[prɔ.ˈduk.тɪ]», «[ˈkur.кa]», «[ba.ˈтɔn]»
- **Problem**: The IPA transcriptions use Cyrillic characters `т` and `к` instead of Latin `t` and `k`. This renders the IPA invalid and confusing for tools/learners.
- **Fix**: Replace all Cyrillic homoglyphs in IPA with Latin characters.

### Issue 2: Grammar (Subject-Verb Mismatch)
- **Location**: Line 124 / Section "М'ясо та молочні продукти"
- **Original**: «Тепер ми йдете у магазин.»
- **Problem**: Mismatch between subject «ми» (we) and verb «йдете» (you go - plural).
- **Fix**: Change to «Тепер ми йдемо у магазин.» (Now we go...) or «Тепер ви йдете...» (Now you go...). Given context "Now *we* go...", use «йдемо».

### Issue 3: Cultural/Factual Error
- **Location**: Line 223 / Section "Українські традиції"
- **Original**: «Булочки не мають часник.»
- **Problem**: This statement regarding pampushky is factually confusing or incorrect. Pampushky are famous specifically *for* their garlic sauce. Saying they "do not have garlic" (even if technically meaning "inside the dough") contradicts the primary cultural association. Also, «не мають 

        ## Files

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/food-and-shopping.md`

        ## Instructions

        1. Fix issues from the review — word/sentence changes, grammar, clarity
        2. Skip major structural rewrites
        3. After fixing, run IPA lint: `.venv/bin/python scripts/lint_ipa.py /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/food-and-shopping.md --fix`
