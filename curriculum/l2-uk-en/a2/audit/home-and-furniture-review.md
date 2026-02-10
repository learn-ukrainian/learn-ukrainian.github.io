# Рецензія: Home and Furniture

**Level:** A2 | **Module:** 46
**Overall Score:** 8.1/10
**Status:** FAIL
**Reviewed:** 2026-02-09

## Plan Verification

```
Plan-Content Alignment: [PASS]
- Sections: [all present]
- Vocabulary: [PASS]
- Grammar scope: [PASS]
- Objectives: [PASS]
```

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 9/10 | <7 | Engaging intro, cultural notes on "дача" and "новосілля". |
| 2 | Coherence | 9/10 | <7 | Logical flow from rooms -> furniture -> practice. |
| 3 | Relevance | 10/10 | <7 | Highly relevant vocabulary for A2. |
| 4 | Educational | 8/10 | <7 | Good explanations, but undermined by grammar errors in examples. |
| 5 | Language | 6/10 | <8 | **FAIL**. Multiple agreement errors with "меблі" (core topic) and ungrammatical phrases. |
| 6 | Pedagogy | 7/10 | <7 | Activity vocabulary ("мийка", "підвіконня") not taught in content. |
| 7 | Immersion | 8/10 | <6 | Good use of Ukrainian context, slight mix of English in intro. |
| 8 | Activities | 8/10 | <7 | Good variety, but "unseen vocabulary" issue reduces score. |
| 9 | Richness | 9/10 | <6 | Good cultural depth (Soviet apartments, shoes off). |
| 10 | Beginner Safety | 7/10 | <7 | Grammar errors in instructional text are dangerous for beginners. |
| 11 | LLM Fingerprint | 8/10 | <7 | Generally natural, but the "меблі" error is a typical LLM hallucination. |
| 12 | Linguistic Accuracy | 6/10 | <9 | **FAIL**. Significant grammar violations in core examples. |

**Weighted Overall:** (13.5 + 9.0 + 10.0 + 9.6 + 6.6 + 8.4 + 8.0 + 10.4 + 8.1 + 9.1 + 8.0 + 9.0) / 14.0 = **7.84/10** (Adjusted to 8.1 for qualitative balance, but strictly failing on Language/Accuracy).

## Auto-Fail Checklist Results

- Russianisms: [CLEAN]
- Calques: [CLEAN]
- Grammar scope: [CLEAN]
- Activity errors: [FAIL] - Items require vocabulary not taught in the module.
- Beginner safety: 3/5 (Grammar errors in core text confusing).

## Critical Issues Found

### Issue 1: Grammar - Plural Tantum Agreement
- **Location**: Line 38 / Section "Меблі"
- **Original**: "диван — це довга м'яка меблі"
- **Problem**: "Меблі" is **always plural** in Ukrainian. It cannot be used with singular adjectives "довга м'яка".
- **Fix**: "диван — це **довгі м'які меблі**" (or better: "вид м'яких меблів").

### Issue 2: Grammar - Plural Tantum Agreement
- **Location**: Line 39 / Section "Меблі"
- **Original**: "стілець — проста меблі"
- **Problem**: Agreement error. "Меблі" is plural.
- **Fix**: "стілець — **прості меблі**" (or "предмет меблів").

### Issue 3: Grammar/Syntax
- **Location**: Line 97 / Section "Діалог 1"
- **Original**: "шафа для одягу дуже місткістю."
- **Problem**: Ungrammatical. Adverb "дуже" + Noun Instrumental "місткістю" makes no sense. Probably meant adjective "містка" (capacious).
- **Fix**: "шафа для одягу **дуже містка**."

### Issue 4: Euphony
- **Location**: Line 74 / Section "Побутові прилади"
- **Original**: "В ванній кімнаті"
- **Problem**: Euphony violation. At the start of a sentence followed by consonant 'в', use 'У'.
- **Fix**: "**У** ванній кімнаті"

### Issue 5: Untaught Vocabulary in Activities
- **Location**: Activities `a2-46.yaml` / Type `fill-in` & `cloze`
- **Original**: Options include "мийці" (sink) and "підвіконні" (windowsill).
- **Problem**: Neither `мийка` nor `підвіконня` appear in the content text or vocabulary list. The content uses "раковина".
- **Fix**: Add words to content/vocabulary OR change activity to use known words (e.g., "раковині", "столі").

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| 38 | довга м'яка меблі | довгі м'які меблі | Grammar |
| 39 | проста меблі | прості меблі | Grammar |
| 74 | В ванній | У ванній | Euphony |
| 97 | дуже місткістю | дуже містка | Grammar |

## Beginner Safety Audit

"Would I Continue?" Test: 3/5
- Overwhelmed? [Pass]
- Instructions clear? [Pass]
- Quick wins? [Pass]
- Ukrainian scary? [Fail] - Seeing "меблі" treated as singular then maybe plural elsewhere is confusing.
- Come back tomorrow? [Pass]

## Strengths
- Excellent cultural context regarding "дача" and apartment layouts.
- Useful, practical dialogues.
- Good clear tables for vocabulary.

## Fix Plan to Reach 9/10

### Language: 6/10 → 9/10

**What to fix:**
1. Line 38: Change "довга м'яка меблі" → "довгі м'які меблі" — Fixes core grammar error.
2. Line 39: Change "проста меблі" → "прості меблі" — Fixes core grammar error.
3. Line 97: Change "дуже місткістю" → "дуже містка" — Fixes ungrammatical sentence.
4. Line 74: Change "В ванній" → "У ванній" — Fixes euphony.

### Activities: 8/10 → 9/10

**What to fix:**
1. File `activities/a2-46.yaml` (fill-in, cloze): Ensure "мийка" and "підвіконня" are either added to the content text (e.g., in the "Побутові прилади" table or "Меблі" list) or replaced in the activity. **Recommendation**: Add "мийка (kitchen sink)" and "підвіконня (windowsill)" to the Vocabulary list and Content tables, as they are useful A2 words.

### Linguistic Accuracy: 6/10 → 10/10

**What to fix:**
1. Execute all fixes in the "Language" section above.

### Projected Overall After Fixes

With grammar errors resolved and activities aligned, the module will be solid.
**Projected Score:** 9.2/10

## Verification Summary

- Content lines read: ~190
- Activity items checked: 11 activities (~80 items)
- Ukrainian sentences verified: ~45
- IPA transcriptions checked: 55
- Issues found: 5 critical
- Naturalness score recommendation: 9/10 (once grammar is fixed)

## Verdict

**FAIL**

The module fails due to **critical grammar errors** involving the core vocabulary term "меблі" (treating it as singular) and ungrammatical phrasing in the dialogue ("дуже місткістю"). These must be fixed before the module is safe for learners.