# Рецензія: Can, Must, Want - Modals

**Level:** A1 | **Module:** 24
**Overall Score:** 6.4/10
**Status:** FAIL
**Reviewed:** 2026-02-08

## Plan Verification

Plan-Content Alignment: [FAIL]
- Sections: [PASS]
- Vocabulary: [MISSING CRITICAL] 'хотіти' is required by plan but absent from teaching sections.
- Grammar scope: [FAIL] 'хотіти' missing; 'обіцяю' tested but not taught; heavy overload with Pres 5/6.
- Objectives: [FAIL] "Learner can express desire" is NOT covered.

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 6/10 | <7 | Module promises "Want" in title but fails to deliver it. |
| 2 | Coherence | 5/10 | <7 | Summary claims "You know how to say 'I want'", but the lesson never taught it. |
| 3 | Relevance | 5/10 | <7 | Prioritizes 'вдаватися/здатний' over the required high-frequency 'хотіти'. |
| 4 | Educational | 5/10 | <7 | Fails to teach a core learning objective defined in the plan. |
| 5 | Language | 9/10 | <8 | The Ukrainian that is present is correct. |
| 6 | Pedagogy | 5/10 | <7 | Major alignment failure: Title/Plan mismatch with Content. |
| 7 | Immersion | 8/10 | <6 | Good usage of examples and dialogues. |
| 8 | Activities | 7/10 | <7 | Mostly good, but tests untaught material ("I promise"). |
| 9 | Richness | 8/10 | <6 | Good tables and IPA usage. |
| 10 | Beginner Safety | 6/10 | <7 | Overwhelming lists in Pres 5/6; confusing to miss "Want". |
| 11 | LLM Fingerprint | 8/10 | <7 | Generally natural structure. |
| 12 | Linguistic Accuracy | 9/10 | <9 | No obvious grammatical errors in the text present. |

**Weighted Overall:** (6*1.5 + 5*1.0 + 5*1.0 + 5*1.2 + 9*1.1 + 5*1.2 + 8*1.0 + 7*1.3 + 8*0.9 + 6*1.3 + 8*1.0 + 9*1.5) / 14.0 = **6.81/10** (Adjusted manually to **6.4** due to critical missing content penalty)

## Auto-Fail Checklist Results

- Russianisms: [CLEAN]
- Calques: [CLEAN]
- Grammar scope: [FAIL] Missing `хотіти` (Required); Testing `обіцяю` (Untaught).
- Activity errors: [FAIL] Quiz tests untaught vocabulary.
- Beginner safety: 3/5

## Critical Issues Found

### Issue 1: Missing Core Concept 'Хотіти'
- **Location**: Entire file
- **Original**: (Missing)
- **Problem**: The module title is "Can, Must, Want". The Plan requires `хотіти`. The Summary says "Now you know how to say... I want". But the content **never teaches** `хотіти` (conjugation or usage).
- **Fix**: Add a dedicated "Presentation" section for `хотіти` (conjugation: хочу, хочеш...) and examples.

### Issue 2: Vocabulary Overload / Priorities
- **Location**: Presentation 5 & 6
- **Original**: Lists of `намагатися`, `старатися`, `пробувати`, `вдаватися`, `встигати`, `здатний`, `певний`, `згодний`.
- **Problem**: These are B1-level or late A2 synonyms/nuances. Dumping them in A1.24 while missing the basic `хотіти` is poor pedagogy. It overwhelms the beginner.
- **Fix**: Delete Presentation 5 and 6. Replace them with the missing `хотіти` section. Keep it simple.

### Issue 3: Testing Untaught Vocabulary
- **Location**: Activities file, `quiz` "Modal Meanings", Item 10
- **Original**: Question: "How do you say accurately 'I promise' in Ukrainian?" Option: "Я обіцяю" (Correct).
- **Problem**: `обіцяю` is not taught in the content, nor is it a modal.
- **Fix**: Remove this question or replace it with a question about `хотіти` once added.

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| - | (Missing хотіти) | (Add хотіти) | Scope |

## Beginner Safety Audit

"Would I Continue?" Test: 3/5
- Overwhelmed? [Fail] (Too many advanced synonyms in Pres 5/6)
- Instructions clear? [Pass]
- Quick wins? [Pass]
- Ukrainian scary? [Fail] (Lists of "modal adjectives" and "trying verbs" are intimidating)
- Come back tomorrow? [Pass] (If fixed)

## Fix Plan to Reach 9/10 (REQUIRED)

### Pedagogy & Relevance: 5/10 → 9/10

**What to fix:**
1.  **DELETE** "Presentation 5" (Trying and Succeeding) and "Presentation 6" (Modal Adjectives). These are out of scope for A1.24.
2.  **INSERT** a new "Presentation" section for **Бажання: хотіти (Desire: To Want)**.
    - Include full conjugation table (я хочу, ти хочеш...).
    - Highlight the `т` → `ч` sound change.
    - Add examples: "Я хочу їсти", "Я хочу спати".
3.  **UPDATE** `activities/24-can-must-want-modals.yaml`:
    - Remove Item 10 ("I promise") from the `quiz`.
    - Add a new `fill-in` or `match-up` activity specifically for `хотіти` forms.
    - Ensure `хотіти` is in the vocabulary list in `vocabulary/24-can-must-want-modals.yaml`.

### Coherence: 5/10 → 9/10

**What to fix:**
1.  Ensure the Content actually matches the Title ("Can, Must, Want").
2.  Ensure the Summary's claim ("You know how to say... I want") becomes true.

**Expected score after fix:** 9.5/10

### Projected Overall After Fixes

With `хотіти` added and the fluff removed, this module will be tight, relevant, and accurate.
Projected Score: **9.5/10**

## Verification Summary

- Content lines read: 250+
- Activity items checked: ~35
- Ukrainian sentences verified: ~40
- IPA transcriptions checked: ~20
- Issues found: 3 (1 Critical Missing, 1 Scope Creep, 1 Overload)
- Naturalness score recommendation: 9/10 (The text itself is natural, just poorly selected)

## Verdict

**FAIL**

Blocking issues:
1.  **Missing "Want" (`хотіти`)**: The lesson fails to teach one of its three title concepts.
2.  **Pedagogical Overload**: Includes advanced synonyms instead of the core required verb.
3.  **Activity Scope**: Tests untaught material.

Must be rebuilt to focus on **Can, Must, Want** as promised.