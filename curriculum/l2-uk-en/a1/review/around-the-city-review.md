# Рецензія: Around the City

**Level:** A1 | **Module:** 15
**Overall Score:** 6.9/10
**Status:** FAIL
**Reviewed:** February 8, 2026

## Plan Verification

```
Plan-Content Alignment: [FAIL]
- Sections: [PASS]
- Vocabulary: [FAIL] Plan requires "наліво/направо", content uses "ліворуч/праворуч". Content includes significantly more vocab than plan (e.g., "світлофор" is recommended but used).
- Grammar scope: [FAIL] Major scope creep. Genitive (M16) and Instrumental (A2/late A1) cases used extensively in prepositions (`біля`, `навпроти`, `за`, `між`) before they are taught.
- Objectives: [PASS]
```

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 7/10 | <7 | Good cultural context, but confusing grammar demands reduce quality. |
| 2 | Coherence | 6/10 | <7 | Relies on "just memorize these phrases" for complex case logic (Genitive/Instrumental), creating structural confusion. |
| 3 | Relevance | 9/10 | <7 | High utility vocabulary for navigation. |
| 4 | Educational | 5/10 | <7 | Tests students on untaught grammar in activities (matching prepositions to case endings they haven't learned). |
| 5 | Language | 8/10 | <8 | Generally natural, but contains a grammatical error in activities. |
| 6 | Pedagogy | 5/10 | <7 | Severe scope creep: Genitive and Instrumental prepositions used and tested before introduction. |
| 7 | Immersion | 8/10 | <6 | Good use of dialogue and scenarios. |
| 8 | Activities | 4/10 | <7 | Contains a grammatically incorrect answer key (wrong case government). |
| 9 | Richness | 8/10 | <6 | Good cultural insights (Metro, Coffee, Lviv). |
| 10 | Beginner Safety | 6/10 | <7 | Overwhelming due to unexplained case endings (-у, -а, -ом) in activities. |
| 11 | LLM Fingerprint | 8/10 | <7 | Generally feels authored, though the scope slip is typical of LLMs. |
| 12 | Linguistic Accuracy | 8/10 | <9 | Error in activity file (wrong case for preposition). |

**Weighted Overall:** (10.5 + 6.0 + 9.0 + 6.0 + 8.8 + 6.0 + 8.0 + 5.2 + 7.2 + 7.8 + 8.0 + 12.0) / 14.0 = **6.75/10**

## Auto-Fail Checklist Results

- Russianisms: [CLEAN]
- Calques: [CLEAN]
- Grammar scope: [FAIL] Heavy use of Genitive prepositions (біля, навпроти, до, від, вздовж) and Instrumental prepositions (за, між, перед) before M16/A2.
- Activity errors: [FAIL] Grammatically incorrect answer in Fill-in activity.
- Beginner safety: 3/5

## Critical Issues Found

### Issue 1: Grammatically Incorrect Activity Item
- **Location**: Activities File, `fill-in` "Complete the Directions", Item 10
- **Original**: `sentence: Театр ___ парку. answer: перед`
- **Problem**: The noun `парку` is in the Genitive case. The preposition `перед` requires the Instrumental case (`перед парком`). Using `перед` with `парку` is grammatically wrong. `біля` or `навпроти` would be correct for this case ending.
- **Fix**: Change sentence to `Театр перед парком.` OR change answer to `біля` (if `парку` is kept).

### Issue 2: Testing Untaught Grammar (Instrumental Case)
- **Location**: Activities File, `fill-in` "Complete the Directions", Item 6 & 8
- **Original**: `Станція метро ___ мостом` (answer: `за`), `Книгарня ___ кафе і банком` (answer: `між`)
- **Problem**: These items require the student to recognize the Instrumental endings (`-ом`) to select the correct prepositions (`за`, `між`). Instrumental case has not been taught.
- **Fix**: Remove these items or change the activity to not rely on case matching (e.g., provide the full phrase).

### Issue 3: Vocabulary Mismatch with Plan
- **Location**: Content vs Plan
- **Original**: Plan asks for `наліво/направо`. Content uses `ліворуч/праворуч`.
- **Problem**: Inconsistency. While `ліворуч/праворуч` is better/more formal, the plan should ideally match.
- **Fix**: Update Plan to `ліворуч/праворуч` OR add `наліво/направо` as synonyms in content.

### Issue 4: Future Tense Usage
- **Location**: Content, Scenario 2
- **Original**: `Вийдете на станції «Майдан Незалежності.»`
- **Problem**: `Вийдете` is Future Perfective (You will exit/get off). M15 A1 students only know Present Imperfective.
- **Fix**: Change to `Виходьте` (Imperative) or `Треба вийти` (Need to exit) or keep as a set phrase but gloss it.

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| Act #10 | Театр перед парку | Театр перед парком | Grammar |

## Beginner Safety Audit

"Would I Continue?" Test: 3/5
- Overwhelmed? **Fail** (Too many unexplained case endings in activities)
- Instructions clear? **Pass**
- Quick wins? **Pass**
- Ukrainian scary? **Fail** (Genitive/Instrumental appearing out of nowhere)
- Come back tomorrow? **Pass** (Content is interesting)

## Fix Plan to Reach 9/10

### Activities: 4/10 → 9/10
**What to fix:**
1. **Activity "Complete the Directions"**: Remove or rewrite items requiring Instrumental case (`за мостом`, `між...`, `перед...`).
2. **Activity "Complete the Directions"**: FIX the grammar error `Театр перед парку`. Change to `Театр біля парку` (answer: `біля`) to match the Genitive ending `парку`.
3. **Activity "Complete the Directions"**: Ensure all distractors in multiple choice don't create accidental correct answers with the given case ending.

### Pedagogy & Coherence: 5-6/10 → 8/10
**What to fix:**
1. **Content**: Explicitly label the directional phrases using Genitive/Instrumental as **"Fixed Phrases"** and add a note: "You will see word endings change (like *парк* → *парку*). This is the Genitive case, which we will learn in the next module. For now, treat the whole phrase as a vocabulary item."
2. **Content**: Reduce reliance on Instrumental examples (`за`, `перед`, `між`) since M16 covers Genitive, but Instrumental is far off. Focus more on `біля`, `навпроти` (Genitive) which connects to M16.

### Plan Compliance
**What to fix:**
1. Update Plan `vocabulary_hints` to replace `наліво/направо` with `ліворуч/праворуч`.

### Projected Overall After Fixes
(10.5 + 8.0 + 9.0 + 8.4 + 9.9 + 8.4 + 8.0 + 11.7 + 7.2 + 9.1 + 8.0 + 13.5) / 14.0 = **9.4/10**

## Verdict

**FAIL**

The module fails primarily due to a blatant grammatical error in the activities (`Театр перед парку`) and severe scope creep where the activities test students on untaught grammar (Instrumental case endings) rather than just the vocabulary.