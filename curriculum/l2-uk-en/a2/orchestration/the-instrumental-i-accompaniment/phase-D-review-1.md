# Рецензія: The Instrumental I — Accompaniment

**Level:** A2 | **Module:** 4
**Overall Score:** 7.5/10
**Status:** FAIL
**Reviewed:** 21 лютого 2026 р.

## Plan Verification

Plan-Content Alignment: FAIL
- Sections: PASS (all H2/H3 match outline)
- Vocabulary: PASS (covers required terms)
- Grammar scope: FAIL (Activities include Spatial and Route Instrumental cases which are explicitly excluded by the plan)
- Objectives: PASS

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 8/10 | <7 | Good explanations, but some English transitions are extremely robotic. |
| 2 | Coherence | 8/10 | <7 | Logical flow from endings to euphony to verbs. |
| 3 | Relevance | 6/10 | <7 | Activities violate scope (include 'над морем', 'під Львовом', 'пляжем' which are not Accompaniment). |
| 4 | Educational | 8/10 | <7 | Solid grammatical breakdown. |
| 5 | Language | 9/10 | <8 | Clear Ukrainian examples. |
| 6 | Pedagogy | 8/10 | <7 | Good use of contrast and error highlighting. |
| 7 | Immersion | 8/10 | <6 | English scaffolding is appropriate for A2, ~55% immersion. |
| 8 | Activities | 4/10 | <7 | CRITICAL: AI left its internal thought process in the YAML output (`Trick question! Living *under* Lviv? No, wait...`). Duplicate `explanation` keys violate schema. |
| 9 | Richness | 8/10 | <6 | Good cultural hook about bread and salt. |
| 10 | Beginner Safety | 9/10 | <7 | 5/5 "Would I Continue?". Very supportive tone. |
| 11 | LLM Fingerprint | 6/10 | <7 | Repetitive paragraph starters in English ("In Ukrainian grammar...", "Soft stems are...", "Feminine nouns ending in...", "The Ukrainian language loves..."). |
| 12 | Linguistic Accuracy | 8/10 | <9 | The euphony rule for `зі` is slightly inaccurate (says "especially sibilants" but applies it too broadly, though acceptable for A2). |

**Weighted Overall:** (8×1.5 + 8×1.0 + 6×1.0 + 8×1.2 + 9×1.1 + 8×1.2 + 8×1.0 + 4×1.3 + 8×0.9 + 9×1.3 + 6×1.0 + 8×1.5) / 14.0 = **7.5/10**

## Auto-Fail Checklist Results

- Russianisms: CLEAN
- Calques: CLEAN
- Grammar scope: FAIL (Included Spatial/Route Instrumental in activities, violating `Not covered: Spatial Prepositions (under/behind/above) → a2-07` from plan).
- Activity errors: FAIL (Duplicate YAML keys, AI prompt leak in output).
- Beginner safety: 5/5

## Critical Issues Found

### Issue 1: AI Prompt Leak & Schema Violation
- **Location**: Line 86 / Activities YAML `the-instrumental-i-accompaniment.yaml`
- **Original**: `explanation: 'Trick question! Living *under* Lviv? No, wait. Let us stick to accompaniment. Re-doing this item to be clearer about accompaniment.'`
- **Problem**: The AI printed its internal monologue into the final YAML output. It also created two `explanation` keys for the same item, causing a YAML schema violation.
- **Fix**: Replace the entire quiz item with a correct accompaniment question.

### Issue 2: Scope Violation (Spatial Instrumental)
- **Location**: Line 233 / Activities YAML `the-instrumental-i-accompaniment.yaml`
- **Original**: `Ми жили в готелі {{2}} (море). Щовечора ми гуляли {{3}} (пляж).` -> Answers `над морем`, `пляжем`.
- **Problem**: The plan explicitly forbids Spatial Prepositions (`над`) and the Route Instrumental (`пляжем`) as they belong in a2-07 and other modules. This module is STRICTLY Accompaniment (`з кимось`).
- **Fix**: Rewrite the cloze sentences to use `з колегою` and `із собакою`.

### Issue 3: LLM Fingerprint (Robotic English Transitions)
- **Location**: Line 213 / Content `the-instrumental-i-accompaniment.md`
- **Original**: `The word order in the Ukrainian language is notoriously flexible, allowing you to move words around for emphasis or artistic effect. However, the standard grammatical structure preserves logic and clarity, especially for beginners.`
- **Problem**: Classic overly verbose, robotic AI transition that breaks the "friendly tutor" persona. Used repeatedly across sections.
- **Fix**: Simplify and humanize the English transition.

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| 85 | `зі зіркою` | `із зіркою` | Phonetics (while `зі` is technically possible, `із зіркою` is far more natural to avoid the z-z repetition) |

## Beginner Safety Audit

"Would I Continue?" Test: 5/5
- Overwhelmed? Pass
- Instructions clear? Pass
- Quick wins? Pass
- Ukrainian scary? Pass
- Come back tomorrow? Pass

## Strengths
- Excellent explanation of the difference between "знайомий", "приятель", and "друг".
- The "Bread and Salt" cultural hook beautifully ties into the grammatical concept of accompaniment.

## Fix Plan to Reach 9/10 

### Activities: 4/10 → 9/10
**What to fix:**
1. Line 86: Remove the AI monologue and duplicate key in the `quiz` activity. Change the question to a valid euphony test for accompaniment.
2. Line 233: Rewrite the first three blanks of the `cloze` passage to remove spatial instrumental cases (`над морем`, `пляжем`) and replace them with accompaniment (`з колегою`, `із собакою`).

**Expected score after fix:** 9/10

### Relevance: 6/10 → 9/10
**What to fix:**
1. Removing the spatial instrumental from activities aligns the module perfectly with the plan's scope.

**Expected score after fix:** 9/10

### LLM Fingerprint: 6/10 → 8/10
**What to fix:**
1. Simplify the robotic English introductions under H3 headers to sound more like a human tutor.

**Expected score after fix:** 8/10

### Projected Overall After Fixes
(8×1.5 + 8×1.0 + 9×1.0 + 8×1.2 + 9×1.1 + 8×1.2 + 8×1.0 + 9×1.3 + 8×0.9 + 9×1.3 + 8×1.0 + 8×1.5) / 14.0 = **8.3/10**

## Verification Summary

- Content lines read: 320
- Activity items checked: 55
- Ukrainian sentences verified: 60
- IPA transcriptions checked: 0 (None present, which is a minor gap but acceptable for A2 grammar focus)
- Issues found: 3

## Verdict

**FAIL**

The module contains severe activity schema violations, including the AI leaking its internal thought process into the final YAML. Furthermore, the activities violate the strict scope boundary by introducing Spatial and Route Instrumental forms, which are explicitly banned in the plan for this module. Fixes provided below.