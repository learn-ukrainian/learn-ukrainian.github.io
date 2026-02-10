===REVIEW_START===
# Рецензія: Buying Tickets

**Level:** A1 | **Module:** 39
**Overall Score:** 8.8/10
**Status:** FAIL
**Reviewed:** 2026-02-09

## Plan Verification

```
Plan-Content Alignment: FAIL
- Sections: PASS
- Vocabulary: PASS (All required words present)
- Grammar scope: FAIL (Past tense in activities not taught)
- Objectives: PASS
- Note: Plan point "маршрутка" (Warm-up) missing from Content text but appears in Activities.
```

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 9/10 | <7 | Clear structure, helpful cultural context. |
| 2 | Coherence | 10/10 | <7 | Logical flow from vocab to dialogue. |
| 3 | Relevance | 9/10 | <7 | Highly practical for travelers. |
| 4 | Educational | 9/10 | <7 | Good explanations of usage. |
| 5 | Language | 10/10 | <8 | Natural Ukrainian phrasing. |
| 6 | Pedagogy | 7/10 | <7 | Scope creep in activities (undefined words). |
| 7 | Immersion | 9/10 | <6 | Good use of Ukrainian headers and examples. |
| 8 | Activities | 6/10 | <7 | Contains words explicitly marked "Out of Scope" in Research. |
| 9 | Richness | 9/10 | <6 | Good cultural details (tea, passport rule). |
| 10 | Beginner Safety | 8/10 | <7 | Mostly safe, but activity vocab is scary/undefined. |
| 11 | LLM Fingerprint | 10/10 | <7 | Feels handcrafted. |
| 12 | Linguistic Accuracy | 10/10 | <9 | No grammatical errors found. |

**Weighted Overall:** (13.5 + 10 + 9 + 10.8 + 11 + 8.4 + 9 + 7.8 + 8.1 + 10.4 + 10 + 15) / 14.0 = **8.78/10**

## Auto-Fail Checklist Results

- Russianisms: [CLEAN]
- Calques: [CLEAN]
- Grammar scope: Failed (Past tense in Activity)
- Activity errors: Failed (Undefined vocabulary)
- Beginner safety: 4/5 (Activity vocabulary issues)

## Critical Issues Found

### Issue 1: Research Scope Violation (Activity)
- **Location**: Activities / `group-sort` "Transport Types"
- **Original**: `items: ["вагон", "купе", "плацкарт", "провідник", "Інтерсіті", "електричка"]`
- **Problem**: The word "електричка" is explicitly listed as **OUT OF SCOPE** in the Research Notes ("Advanced Classifications... e.g., 'електричка'").
- **Fix**: Remove "електричка". Replace with known word like "експрес" or just remove.

### Issue 2: Undefined Vocabulary in Activities
- **Location**: Activities / `group-sort` "Transport Types"
- **Original**: `items: ["водій", "автовокзал", "маршрутка", "салон", "зупинка", "автостанція"]`
- **Problem**: "Салон" (cabin/salon), "зупинка" (stop), and "автостанція" (bus station - synonym) are not introduced in the text, nor are they A1 prerequisites. "Маршрутка" is in the Plan but missing from the Content text.
- **Fix**: Replace with known words (e.g., "квиток", "пасажир", "місце") or remove the complex items.

### Issue 3: Grammar Scope Creep (Past Tense)
- **Location**: Activities / `quiz` "Prepositions of Motion" / Item 6
- **Original**: `question: «Я приїхав сюди _____ (from Ukraine).»`
- **Problem**: "Приїхав" is Past Tense Perfective. A1 Module 39 typically focuses on Present Tense or simple Future. Past tense adds unnecessary cognitive load.
- **Fix**: Change to Present Tense: "Я їду сюди..." or "Я тут..."

### Issue 4: Grammar Scope Creep (Reflexive)
- **Location**: Activities / `quiz` "Prepositions of Motion" / Item 10
- **Original**: `question: «Я вже повертаюся додому _____ (back).»`
- **Problem**: "Повертаюся" (Reflexive verb) is complex for this stage.
- **Fix**: Simplify sentence: "Я їду додому..."

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| Act | "електричка" | [REMOVE] | Scope |
| Act | "Я приїхав" | "Я їду" | Scope |

## Beginner Safety Audit

"Would I Continue?" Test: 4/5
- Overwhelmed? Pass
- Instructions clear? Pass
- Quick wins? Pass
- Ukrainian scary? Fail (in the sorting activity with unknown words)
- Come back tomorrow? Pass

Emotional beats: 4 found
- Welcome: "Ukraine is a large country..."
- Curiosity: Myth-buster about trains.
- Quick wins: 3 scenarios with dialogue.
- Encouragement: "Тепер ви можете подорожувати!"

## Strengths
- Excellent practical dialogues.
- "Myth-buster" and "Cultural" notes are very engaging and high value.
- Clear distinction between "Туди" and "Туди й назад".

## Fix Plan to Reach 9/10

### Activities: 6/10 → 9/10

**What to fix:**
1. **Activity `group-sort`**:
   - Change `["вагон", "купе", "плацкарт", "провідник", "Інтерсіті", "електричка"]`
   - To `["вагон", "купе", "плацкарт", "провідник", "Інтерсіті", "квиток"]` (Replaces banned/unknown words).
   - Change `["водій", "автовокзал", "маршрутка", "салон", "зупинка", "автостанція"]`
   - To `["водій", "автовокзал", "автобус", "місце", "пасажир", "дорога"]` (Uses known/simple vocab).
2. **Activity `quiz` (Prepositions)**:
   - Item 6: Change `«Я приїхав сюди...»` → `«Я їду сюди...»` (Fixes past tense).
   - Item 10: Change `«Я вже повертаюся додому...»` → `«Я вже їду додому...»` (Removes reflexive).

### Pedagogy: 7/10 → 9/10

**What to fix:**
1. Implementation of the above Activity fixes resolves the pedagogical scope violations.

### Projected Overall After Fixes

Activities rises to 9/10. Pedagogy rises to 9/10. Beginner Safety rises to 9/10.
New Score: ~9.2/10

## Verification Summary

- Content lines read: ~140
- Activity items checked: 60+
- Ukrainian sentences verified: ~45
- IPA transcriptions checked: 17
- Issues found: 4 (Scope/Vocab in activities)
- Naturalness score recommendation: 10/10

## Verdict

**FAIL**

The module content is excellent, but the **Activities** file contains significant scope violations (banned words from Research, undefined vocabulary, and untaught grammar concepts like Past Tense). These must be cleaned up to ensure a safe beginner experience.

===REVIEW_END===
