# Рецензія: Dative Verbs

**Level:** A2 | **Module:** 3
**Overall Score:** 7.9/10
**Status:** FAIL
**Reviewed:** 2026-02-20

## Plan Verification

Plan-Content Alignment: FAIL
- Sections: PASS (All planned sections present)
- Vocabulary: FAIL (Missing 9 required items: `вибачати`, `пробачати`, `заздрити`, `симпатизувати`, `співчувати`, `личити`, `підходити`, `вистачати`, `бракувати`)
- Grammar scope: PASS
- Objectives: PASS

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 10/10 | <7 | Excellent analogy ("bossy driver"), warm tone throughout. |
| 2 | Coherence | 10/10 | <7 | Logical flow: concept -> presentation -> drills -> synthesis. |
| 3 | Relevance | 10/10 | <7 | Highly relevant examples (Volunteering, Toloka). |
| 4 | Educational | 9/10 | <7 | Clear explanations of "invisible to". |
| 5 | Language | 10/10 | <8 | Natural Ukrainian, correct forms used. |
| 6 | Pedagogy | 6/10 | <7 | Critical failure: Uses untaught vocabulary in activities (`личити`, `співчувати`). |
| 7 | Immersion | 8/10 | <6 | ~50-60% range appropriate for A2.1. |
| 8 | Activities | 6/10 | <7 | Critical typo in item text; missing vocabulary practice. |
| 9 | Richness | 8/10 | <6 | Good cultural callouts, but missing required emotional vocabulary. |
| 10 | Beginner Safety | 10/10 | <7 | "Would I Continue?" 5/5. Very supportive. |
| 11 | LLM Fingerprint | 9/10 | <7 | Unique voice, avoids standard AI clichés. |
| 12 | Linguistic Accuracy | 9/10 | <9 | One agreement error in activity text. |

**Weighted Overall:** 7.9/10

## Auto-Fail Checklist Results

- Russianisms: CLEAN
- Calques: CLEAN
- Grammar scope: CLEAN
- Activity errors: **FAIL** (Typo in item text, untaught concepts)
- Beginner safety: 5/5

## Critical Issues Found

### Issue 1: Missing Required Vocabulary
- **Location**: Entire Module
- **Problem**: The plan explicitly lists `вибачати`, `пробачати`, `заздрити`, `симпатизувати`, `співчувати`, `личити`, `підходити`, `вистачати`, `бракувати` in `vocabulary_hints.required`. None of these are taught in the text or listed in the vocabulary file.
- **Fix**: Add a "Group 4: Emotional & State Verbs" section to the text and update the vocabulary YAML. (Requires full rebuild).

### Issue 2: Concept Before Use Violation
- **Location**: `activities/dative-verbs.yaml` (Items: "Ця сукня дуже личить подрузі", sorting item "співчувати")
- **Problem**: The verb `личити` is used in a quiz, but never introduced or defined in the lesson. This violates the "Concept Before Use" rule.
- **Fix**: Remove these items until the vocabulary is added to the lesson.

### Issue 3: Grammatical Error in Activity
- **Location**: `activities/dative-verbs.yaml`, "error-correction", Item 1
- **Original**: `sentence: 'Я дуже дякують тебе за подарунок.'`
- **Problem**: Subject `Я` (I) does not agree with verb `дякують` (they thank). The intended error was `тебе` vs `тобі`, but the verb error distracts.
- **Fix**: Change to `дякую`.

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| Act. | «Я дуже дякують тебе» | «Я дуже дякую тебе» | Grammar (Agreement) |

## Beginner Safety Audit

"Would I Continue?" Test: 5/5
- Overwhelmed? Pass
- Instructions clear? Pass
- Quick wins? Pass
- Ukrainian scary? Pass
- Come back tomorrow? Pass

## Strengths
- **Tone:** The "bossy driver" analogy for verb government is brilliant A2 pedagogy.
- **Culture:** The inclusion of "Toloka" and volunteering context makes the grammar feel alive and relevant.
- **Style:** Strong recommendation of `-ові/-еві` endings promotes high-quality Ukrainian.

## Fix Plan to Reach 9/10

### Activities: 6/10 → 9/10
**What to fix:**
1. Fix the agreement error in the error-correction activity.
2. (Requires Rebuild) Add missing vocabulary practice.

### Pedagogy: 6/10 → 10/10
**What to fix:**
1. (Requires Rebuild) Ensure all vocabulary used in activities is taught in the text.

## Verification Summary

- Content lines read: ~200
- Activity items checked: 62
- Ukrainian sentences verified: 100%
- IPA transcriptions checked: 35
- Issues found: 3

## Verdict

**FAIL**

The module is tonally excellent and safe for beginners, but it fails on **Completeness**. It misses nearly 50% of the required vocabulary listed in the plan (9 verbs), and subsequently violates the "Concept Before Use" rule by testing untaught words in the activities. It requires a content expansion to include these missing verbs.