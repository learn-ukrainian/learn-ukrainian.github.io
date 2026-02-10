# Рецензія: The Locative: Where Things Are

**Level:** A1 | **Module:** 13
**Overall Score:** 9.6/10
**Status:** PASS
**Reviewed:** 2026-02-08

## Plan Verification

Plan-Content Alignment: [PASS]
- Sections: [all present]
- Vocabulary: [8/8 required from plan used, many useful contextual words added]
- Grammar scope: [clean - "Зустрінемося" is a minor advanced phrase but acceptable as lexical chunk]
- Objectives: [all covered]

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 10/10 | <7 | Clear, welcoming, culturally rich. |
| 2 | Coherence | 9/10 | <7 | Euphony rules explained well, but slightly contradicted in one activity item. |
| 3 | Relevance | 10/10 | <7 | Highly relevant navigation skills. |
| 4 | Educational | 10/10 | <7 | Great breakdown of "Secret Shifts" and "Deep Logic" of prepositions. |
| 5 | Language | 10/10 | <8 | Natural examples, good use of idiomatic "на". |
| 6 | Pedagogy | 10/10 | <7 | Good progression from forms to prepositions to production. |
| 7 | Immersion | 10/10 | <6 | Examples are well-contextualized (Kyiv, Shevchenko St). |
| 8 | Activities | 8/10 | <7 | One item contradicts the euphony rule taught in the lesson. |
| 9 | Richness | 10/10 | <6 | Cultural notes on street names and "на роботі". |
| 10 | Beginner Safety | 10/10 | <7 | "Would I Continue?" 5/5. Encouraging tone. |
| 11 | LLM Fingerprint | 10/10 | <7 | No obvious AI-isms. |
| 12 | Linguistic Accuracy | 9/10 | <9 | Minor euphony strictness issue. |

**Weighted Overall:** (15 + 9 + 10 + 12 + 11 + 12 + 10 + 10.4 + 9 + 13 + 10 + 13.5) / 14.0 = **9.63/10**

## Auto-Fail Checklist Results

- Russianisms: [CLEAN]
- Calques: [CLEAN]
- Grammar scope: [CLEAN]
- Activity errors: [Minor contradiction found in Preposition Choice]
- Beginner safety: 5/5

## Critical Issues Found

### Issue 1: Euphony Rule Contradiction
- **Location**: Activities file, `type: fill-in`, title `Preposition Choice`, items "Діти ___ школі" and "Ми ___ Львові".
- **Original**: Answer is `у`, but options include `в`.
- **Problem**: The lesson explicitly teaches: "Use **в** if the previous word ends in a vowel". "Діти" ends in a vowel, so the rule dictates "Діти **в** школі". The activity marks `в` as incorrect and `у` as correct. While `у` is possible in spoken language for rhythm, it contradicts the simplified rule given to the A1 learner. Similarly for "Ми в/у Львові".
- **Fix**: Remove `в` from the options for these specific items to avoid confusion, OR change the subject to end in a consonant (e.g., "Брат ___ школі") to make `у` the unambiguous correct choice per the taught rule.

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| Act | Діти **у** школі (key) | Діти **в** школі | Euphony Consistency |

## Beginner Safety Audit

"Would I Continue?" Test: 5/5
- Overwhelmed? [No]
- Instructions clear? [Yes]
- Quick wins? [Yes - "Where is dad?" simple dialogues]
- Ukrainian scary? [No - "Secret shifts" explained gently]
- Come back tomorrow? [Yes]

Emotional beats: 5 found
- Welcome: "Imagine you are in the heart of Kyiv..."
- Curiosity: "Did you know that the most common street name..."
- Quick wins: Transformation practice (simple logical steps).
- Encouragement: "Don't worry about memorizing these all at once!"
- Progress: "Місцевий відмінок — як світло в темній кімнаті."

## Strengths
- **Cultural Context**: The explanation of why we say "на пошті" vs "в офісі" (public sphere vs enclosed) is excellent and much better than rote memorization.
- **Phonetics**: The explanation of vowel alternation ("linguistic memory") makes a dry grammar point feel poetic and logical.
- **Realism**: Dialogues use "вулиця Шевченка" and "Майдан", grounding the learner in Ukrainian reality.

## Fix Plan to Reach 9/10

*Current score is >9.0, but the activity fix is highly recommended for consistency.*

### Activities: 8/10 → 10/10

**What to fix:**
1. **File**: `curriculum/l2-uk-en/a1/activities/13-the-locative-where-things-are.yaml`
2. **Item**: Under `Preposition Choice` (fill-in), locate `sentence: Діти ___ школі.`
3. **Action**: Change `options` to exclude `в` OR change sentence to `Учень ___ школі.` (starts with vowel, previous ends in consonant).
   - *Recommendation*: Change sentence to **"Брат ___ школі."** (Ends in consonant 'т', so 'у' is strictly correct per rule).
4. **Item**: Under `Preposition Choice`, locate `sentence: Ми ___ Львові.`
5. **Action**: Change sentence to **"Він ___ Львові."** (Ends in consonant 'н', so 'у' is strictly correct per rule).

## Verification Summary

- Content lines read: ~160
- Activity items checked: ~55
- Ukrainian sentences verified: ~40
- IPA transcriptions checked: 23 (Vocabulary file)
- Issues found: 2 (Euphony consistency in activities)
- Naturalness score recommendation: 10/10

## Verdict

**PASS**

The module is excellent—engaging, culturally rich, and linguistically sound. The content explains complex changes (palatalization, alternation) in a friendly way. The only issue is a minor inconsistency between the strict euphony rules taught in the text and the flexibility expected in two activity items. Fixing these two activity items to perfectly align with the "Consonant → У, Vowel → В" rule will make this module perfect.