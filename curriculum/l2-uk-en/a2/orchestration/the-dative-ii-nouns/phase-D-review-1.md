# Рецензія: The Dative II — Nouns

**Level:** A2 | **Module:** 2
**Overall Score:** 8.1/10
**Status:** FAIL
**Reviewed:** 2026-02-19

## Plan Verification

- Plan-Content Alignment: PASS
- Sections: All plan sections present (Introduction, Masculine/Neuter, Feminine, Plural, Verbs, Practice, Dialogues).
- Vocabulary: Covers required verbs (давати, дарувати, допомагати, телефонувати, etc.).
- Grammar scope: Correctly focuses on Dative Nouns (M/F/N/Pl) and consonant shifts.
- Objectives: All objectives addressed.

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 9/10 | <7 | Tone is warm, encouraging, and culturally rich ("Language of generosity"). |
| 2 | Coherence | 9/10 | <7 | Logical flow from concept -> endings -> verbs -> context. |
| 3 | Relevance | 10/10 | <7 | Highly relevant cultural context (gifts, name days). |
| 4 | Educational | 9/10 | <7 | Explanations of age and indirect object are clear. |
| 5 | Language | 8/10 | <8 | Main text is natural, but critical grammar errors in activities. |
| 6 | Pedagogy | 9/10 | <7 | Good scaffolding, clear examples. |
| 7 | Immersion | 8/10 | <6 | Meets Band 1 targets (English logic, Ukrainian examples). |
| 8 | Activities | 5/10 | <7 | **CRITICAL FAILURE**: Subject-Verb agreement errors in activity prompts ("Я даруємо"). |
| 9 | Richness | 9/10 | <6 | excellent cultural integration (odd numbers of flowers, taboo gifts). |
| 10 | Beginner Safety | 8/10 | <7 | Explanations are safe, but activity errors could confuse beginners. |
| 11 | LLM Fingerprint | 8/10 | <7 | Some repetition in activity sentence structures, otherwise good persona. |
| 12 | Linguistic Accuracy | 6/10 | <9 | "Я даруємо" is a basic A1 error that must not exist in A2 curriculum. |

**Weighted Overall:** (9*1.5 + 9 + 10 + 9*1.2 + 8*1.1 + 9*1.2 + 8 + 5*1.3 + 9*0.9 + 8*1.3 + 8 + 6*1.5) / 14.0 = **114.3 / 14.0 = 8.16/10**

## Auto-Fail Checklist Results

- Russianisms: [CLEAN]
- Calques: [CLEAN]
- Grammar scope: [CLEAN]
- Activity errors: **FAIL** (Subject-Verb agreement errors found)
- Beginner safety: 4/5 (Good, but errors in practice undermine trust)

## Critical Issues Found

### Issue 1: Grammar Error in Activity (Agreement)
- **Location**: `activities/the-dative-ii-nouns.yaml` / fill-in "Жіночий рід: магія чергування"
- **Original**: «sentence: "Я даруємо квіти (подруга)."»
- **Problem**: Subject "Я" (I) does not match Verb "даруємо" (we give).
- **Fix**: Change to "Я дарую" or "Ми даруємо". Given the context of "I", "дарую" is better, or change subject to "Ми".

### Issue 2: Grammar Error in Activity (Agreement)
- **Location**: `activities/the-dative-ii-nouns.yaml` / fill-in "Множина: щедрість для всіх"
- **Original**: «sentence: "Я даруємо радість (люди)."»
- **Problem**: Subject "Я" (I) does not match Verb "даруємо" (we give).
- **Fix**: Change to "Ми даруємо" (We give joy - general statement) or "Я дарую".

### Issue 3: Grammar Error in Cloze Activity
- **Location**: `activities/the-dative-ii-nouns.yaml` / cloze "День народження"
- **Original**: «passage: "...Я даруємо {{2}} книгу..."»
- **Problem**: Subject "Я" (I) does not match Verb "даруємо" (we give).
- **Fix**: Change to "Я дарую".

### Issue 4: Typo in Activity Instruction
- **Location**: `activities/the-dative-ii-nouns.yaml` / match-up
- **Original**: «left: "Читат казку"»
- **Problem**: Typo in verb infinitive.
- **Fix**: «Читати казку»

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| Act | «Я даруємо» | «Я дарую» | Grammar (Agreement) |
| Act | «Читат» | «Читати» | Typo |

## Beginner Safety Audit

"Would I Continue?" Test: 4/5
- Overwhelmed? No
- Instructions clear? Yes
- Quick wins? Yes
- Ukrainian scary? No
- Come back tomorrow? Yes, but might be confused by "Я даруємо" if they learned "Я даю" previously.

## Strengths
- **Cultural Depth**: The section on flower etiquette (odd/even numbers) and taboo gifts is excellent A2 content.
- **Voice**: The "Patient Tutor" persona is well-maintained in the main text.
- **Visuals**: The explanation of consonant shifts (G-Z, K-C, Kh-S) is vivid and memorable.

## Fix Plan to Reach 9/10

### Activities: 5/10 → 9/10
**What to fix:**
1. Fix all "Я даруємо" instances to correct agreement.
2. Fix typo "Читат".
3. Verify all other verb forms.

**Expected score after fix:** 9/10

### Projected Overall After Fixes
(9*1.5 + 9 + 10 + 9*1.2 + 9*1.1 + 9*1.2 + 8 + 9*1.3 + 9*0.9 + 9*1.3 + 8 + 9*1.5) / 14.0 = **124.6 / 14.0 = 8.9/10**

## Verification Summary

- Content lines read: ~200
- Activity items checked: 12 types, ~60 items
- Ukrainian sentences verified: All
- IPA transcriptions checked: 25
- Issues found: 4 (All in activities)

## Verdict

**FAIL**

Blocking issues: Critical grammar errors (Subject-Verb agreement) in 3 activity items. These must be fixed before release.