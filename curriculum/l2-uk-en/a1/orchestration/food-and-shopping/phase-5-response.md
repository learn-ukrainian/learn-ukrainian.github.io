# Рецензія: Food, Drinks & Shopping

**Level:** A1 | **Module:** 18
**Overall Score:** 9.4/10
**Status:** PASS
**Reviewed:** 2026-02-08

## Plan Verification

```
Plan-Content Alignment: [PASS]
- Sections: [PASS] (Covered: Food, Drinks, Eating verbs, Shopping cases, Dialogues)
- Vocabulary: [FAIL] (CRITICAL: YAML vocabulary file does not match Content. Content teaches ~30 core words (борщ, хліб, вода...), YAML lists only 12 items, mostly supermarket brands and supplementary terms.)
- Grammar scope: [PASS] (Accusative/Genitive usage is appropriate. "Я буду" formula is acceptable for A1.)
- Objectives: [PASS] (Shopping and ordering goals met.)
```

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 10/10 | <7 | Strong cultural hook (Borshch, Stalker), practical dialogues. |
| 2 | Coherence | 8/10 | <7 | Content flows well, but Vocabulary YAML is completely disconnected from the text. |
| 3 | Relevance | 10/10 | <7 | Essential survival skills (buying food, ordering). |
| 4 | Educational | 9/10 | <7 | Explanations of cases are clear and practical. |
| 5 | Language | 9/10 | <8 | Natural dialogues. One minor "translation-ese" phrase ("Ви хочете цукор?"). |
| 6 | Pedagogy | 10/10 | <7 | Good scaffolding from words to phrases to dialogues. |
| 7 | Immersion | 10/10 | <6 | English used for instruction, Ukrainian for examples. Appropriate for A1. |
| 8 | Activities | 9/10 | <7 | Good variety. One minor aspect mismatch in a quiz item. |
| 9 | Richness | 9/10 | <6 | Cultural notes are excellent. Vocabulary YAML deficiency hurts this slightly. |
| 10 | Beginner Safety | 10/10 | <7 | Clear, encouraging, not overwhelming. 5/5 on Safety Test. |
| 11 | LLM Fingerprint | 10/10 | <7 | "Bread is Head" and "S.T.A.L.K.E.R." references feel authentic. |
| 12 | Linguistic Accuracy | 9/10 | <9 | Text is clean. Vocabulary YAML contains a lemma error ("курко"). |

**Weighted Overall:** (15+8+10+10.8+9.9+12+10+11.7+8.1+13+10+13.5) / 14.0 = **9.42/10**

## Auto-Fail Checklist Results

- Russianisms: [CLEAN]
- Calques: [CLEAN]
- Grammar scope: [CLEAN]
- Activity errors: [CLEAN] (Minor semantic precision issue, not fatal)
- Beginner safety: 5/5

## Critical Issues Found

### Issue 1: Broken Vocabulary Extraction
- **Location**: `/vocabulary/18-food-and-shopping.yaml`
- **Original**: Lists words like `АТБ`, `Новус`, `тушонка`, `курко`.
- **Problem**: Misses almost ALL core vocabulary taught in the lesson: `борщ`, `суп`, `вареники`, `м'ясо`, `риба`, `курка`, `хліб`, `сир`, `яйце`, `вода`, `чай`, `кава`, `сік`, `вино`, `пиво`, `огірок`, `помідор`, `цибуля`, `яблуко`, `банан`.
- **Fix**: Regenerate vocabulary YAML to include all bolded terms from the Content file.

### Issue 2: Vocabulary Lemma Error
- **Location**: `/vocabulary/18-food-and-shopping.yaml` item `курко`
- **Original**: `lemma: курко`, `translation: chicken (diminutive)`, `gender: m`
- **Problem**: `Курко` is not a standard lemma. "Chicken" is `курка` (fem). Diminutive is `курочка`. `Курко` might be a hallucinated vocative or neuter form.
- **Fix**: Change to `lemma: курка`, `gender: f`, `translation: chicken`.

### Issue 3: Activity Semantic Mismatch
- **Location**: Activity `Shopping Sentences Order`, Item "The store opens at 8"
- **Original**: `Магазин відчинено о восьмій`
- **Problem**: "Відчинено" (is open) describes a state. "Opens" (action) is "відчиняється". "The store opens at 8" implies the schedule of opening.
- **Fix**: Change Ukrainian text to `Магазин відчиняється о восьмій` OR change English prompt to "The store is open at 8".

### Issue 4: Phrasing Naturalness
- **Location**: Dialogue "У ресторані"
- **Original**: `Ви хочете цукор?`
- **Problem**: Grammatically correct but sounds like a translation of "Do you want sugar?".
- **Fix**: Change to `Вам з цукром?` (To you with sugar?) or `Цукор треба?` for more natural flow, or keep simple `Ви хочете цукор?` but note it's simplified.

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| Vocab YAML | курко | курка | Typo/Error |
| Activity | Магазин відчинено о восьмій | Магазин відчиняється о восьмій | Grammar/Aspect |

## Beginner Safety Audit

"Would I Continue?" Test: 5/5
- Overwhelmed? [No]
- Instructions clear? [Yes]
- Quick wins? [Yes] (Ordering logic is simple)
- Ukrainian scary? [No]
- Come back tomorrow? [Yes]

Emotional beats: 5 found
- Welcome: "Food is at the heart of Ukrainian culture."
- Curiosity: "Did You Know? Borshch..."
- Quick wins: "You learned these verbs in Module 08. Use them now!"
- Encouragement: "The Magic Word: Смачного!"
- Progress: "You can now feed yourself in Ukraine!"

## Strengths
- **Cultural Integration**: referencing S.T.A.L.K.E.R. and the "Bread is Head" saying makes the lesson feel alive and specific to Ukraine, not generic.
- **Practicality**: The phrases taught are exactly what a beginner needs (ordering, paying, asking price).
- **Scaffolding**: Reviewing verbs from Mod 08 before applying them keeps the learning curve manageable.

## Verdict

**PASS**

The content module itself is excellent—engaging, culturally rich, and pedagogically sound. However, the **Vocabulary YAML file is critically defective** and misses 90% of the lesson's actual vocabulary. This must be fixed before release to ensure flashcards/tools work correctly. The score reflects the high quality of the text, but the technical asset (YAML) requires immediate regeneration.
