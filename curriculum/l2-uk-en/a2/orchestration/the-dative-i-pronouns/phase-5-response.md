# Рецензія: Давальний відмінок I — Займенники

**Level:** A2 | **Module:** 01
**Overall Score:** 8.5/10
**Status:** FAIL
**Reviewed:** 2026-02-08

## Plan Verification

Plan-Content Alignment: [PASS]
- Sections: [all present]
- Vocabulary: [10/15 from plan, 8 extra found]
- Grammar scope: [clean]
- Objectives: [all covered]

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 9/10 | <7 | Clear flow, welcoming tone. |
| 2 | Coherence | 9/10 | <7 | Logical progression from pronouns to needs/likes. |
| 3 | Relevance | 10/10 | <7 | Essential topic for A2 (likes/needs). |
| 4 | Educational | 9/10 | <7 | Good examples and tables. |
| 5 | Language | 6/10 | <8 | **Contradiction**: Text says `потрібно` never changes, but Practice uses `потрібна`. |
| 6 | Pedagogy | 6/10 | <7 | Confusing grammar rule explanation for "потрібно". |
| 7 | Immersion | 7/10 | <6 | English-heavy (expected for A2.1 grammar), but could be higher. |
| 8 | Activities | 9/10 | <7 | Strong variety and volume (10 activities). |
| 9 | Richness | 9/10 | <6 | Cultural note on hospitality is excellent. |
| 10 | Beginner Safety | 10/10 | <7 | Very safe, reassuring tone. |
| 11 | LLM Fingerprint | 8/10 | <7 | "Welcome to the sixth Ukrainian case..." is slightly generic. |
| 12 | Linguistic Accuracy | 9/10 | <9 | Generally high, except the metalanguage error in activities. |

**Weighted Overall:** (13.5 + 9 + 10 + 10.8 + 6.6 + 7.2 + 7 + 11.7 + 8.1 + 13 + 8 + 13.5) / 14 = **8.45/10**

## Auto-Fail Checklist Results

- Russianisms: [CLEAN]
- Calques: [CLEAN]
- Grammar scope: [CLEAN]
- Activity errors: [Minor issue in match-up]
- Beginner safety: 5/5

## Critical Issues Found

### Issue 1: Grammar Contradiction (Потрібно)
- **Location**: Section "Presentation", Subsection "Конструкція "потрібно""
- **Original**: "These are impersonal words that never change their endings, making them very easy to use once you know your Dative pronouns."
- **Problem**: This is false when used with nouns. We say "Мені потріб**на** машина" (f), "Мені потріб**ен** час" (m). The Practice section actually uses "Їй потріб**на** нова машина", contradicting the explanation.
- **Fix**: Update the explanation to distinguish between `потрібно` (with verbs) and `потрібен/потрібна/потрібне/потрібні` (with nouns). Or simplify to just `треба` (invariant) vs `потрібен` (agreeing).

### Issue 2: Confusing Example
- **Location**: Section "Presentation", Subsection "Конструкція "потрібно""
- **Original**: "Мені потрібно кави."
- **Problem**: While `треба кави` (Genitive) is common, `потрібно кави` is less standard for A2 than `Мені потрібна кава` (Nominative). Given the Practice section uses Nominative agreement ("нова машина"), the examples should be consistent.
- **Fix**: Change to "Мені потрібна кава." and update explanation to cover gender agreement.

### Issue 3: Incorrect Question in Activity
- **Location**: Activities file, `match-up` "Nominative to Dative", Item 10
- **Original**: "left: подобатися (до кого?)"
- **Problem**: "До кого?" means "To whom?" (direction/motion). The Dative case question is simply "Кому?". "До кого" is grammatically incorrect for `подобатися`.
- **Fix**: Change to "подобатися (кому?)"

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| Act | подобатися (до кого?) | подобатися (кому?) | Grammar |

## Beginner Safety Audit

"Would I Continue?" Test: 5/5
- Overwhelmed? Pass
- Instructions clear? Pass
- Quick wins? Pass ("I like" is a big win)
- Ukrainian scary? Pass
- Come back tomorrow? Pass

Emotional beats: 4 found
- Welcome: Intro
- Curiosity: "Language of care and attention"
- Quick wins: "Мені подобається"
- Encouragement: Summary "Це дуже важливо..."

## Strengths
- The explanation of the "Experiencer" role is excellent and helps shift the mindset from English to Ukrainian logic.
- The cultural note about hospitality ("Вам ще борщу?") is fantastic contextual learning.

## Fix Plan to Reach 9/10

### Language: 6/10 → 9/10
### Pedagogy: 6/10 → 9/10

**What to fix:**
1.  **Section "Presentation"**: Rewrite the "Конструкція "потрібно"" section.
    *   **Delete**: "These are impersonal words that never change their endings..."
    *   **Insert**: "When you need to **do** something (action), use **потрібно** + infinitive. This form never changes."
    *   **Insert**: "When you need **something** (noun), the word changes to agree with the gender of the noun: **потрібен** (masculine), **потрібна** (feminine), **потрібне** (neuter), **потрібні** (plural)."
    *   **Change Example**: "Мені потрібно кави" → "Мені потрібна кава." (Matches gender rule).
    *   **Keep Example**: "Йому потрібно працювати." (Matches action rule).
    *   **Add Example**: "Мені потрібен час." (Masculine).

2.  **Activities File**:
    *   Find `match-up` activity "Nominative to Dative".
    *   Change `left: подобатися (до кого?)` → `left: подобатися (кому?)`.

### Expected Overall After Fixes
(9*1.5 + 9*1 + 10*1 + 9*1.2 + **9***1.1 + **9***1.2 + 7*1 + 9*1.3 + 9*0.9 + 10*1.3 + 8*1 + 9*1.5) / 14 = **9.05/10**

## Verification Summary

- Content lines read: 140
- Activity items checked: 55
- Ukrainian sentences verified: ~45
- IPA transcriptions checked: N/A (Vocab file read but content doesn't use inline IPA heavily)
- Issues found: 3 (1 Major Grammar, 1 Minor Content, 1 Minor Activity)
- Naturalness score recommendation: 9/10

## Verdict

**FAIL**

The module is excellent in tone and structure, but the explanation of `потрібно` is factually incorrect regarding gender agreement ("never change their endings"), which contradicts the practice exercises (`потрібна машина`). This confuses learners and must be fixed before release.