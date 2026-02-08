# Рецензія: Checkpoint - First Contact

**Level:** A1 | **Module:** 10
**Overall Score:** 7.2/10
**Status:** FAIL
**Reviewed:** 2026-02-08

## Plan Verification

```
Plan-Content Alignment: [FAIL] (No plan file provided)
- Sections: [PASS - Structure is logical for a checkpoint]
- Vocabulary: [PASS - Basic vocab seems aligned, but "Скільки/Куди" missing from intro]
- Grammar scope: [FAIL - Accusative case usage overlaps with "future" content; Irregular verbs in practice without explanation]
- Objectives: [PASS - Review objectives met, but execution has flaws]
```

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 7/10 | <7 | Good explanations, but pedagogical traps (irregular verbs) undermine confidence. |
| 2 | Coherence | 7/10 | <7 | Contradiction: Claims Accusative is next (M11-20), but uses Fem Accusative (-у) in examples. |
| 3 | Relevance | 8/10 | <7 | Content is highly relevant (survival phrases, food). |
| 4 | Educational | 6/10 | <7 | **FAIL**. Tests untaught irregular verb mutations ("писати", "робити") in practice drills. |
| 5 | Language | 9/10 | <8 | Ukrainian is natural and correct. |
| 6 | Pedagogy | 6/10 | <7 | **FAIL**. Introduces concepts (mutations) in testing phase rather than teaching phase. |
| 7 | Immersion | 8/10 | <6 | Good use of "Model" sections and Ukrainian examples. |
| 8 | Activities | 6/10 | <7 | **FAIL**. YAML Quiz tests "Скільки" and "Куди" which are not taught in the module content. |
| 9 | Richness | 7/10 | <6 | Standard checkpoint depth. |
| 10 | Beginner Safety | 6/10 | <7 | **FAIL**. A student following the rules will fail the "писати/робити" and "Скільки" questions. |
| 11 | LLM Fingerprint | 8/10 | <7 | Good structure, minimal robotic phrasing. |
| 12 | Linguistic Accuracy | 9/10 | <9 | No errors in the Ukrainian text itself. |

**Weighted Overall:** 101.2 / 14.0 = **7.2/10**

## Auto-Fail Checklist Results

- Russianisms: [CLEAN]
- Calques: [CLEAN]
- Grammar scope: [FAIL - Accusative usage (contradicts summary), Irregular mutations (untaught)]
- Activity errors: [FAIL - Testing untaught vocabulary "Скільки" and "Куди"]
- Beginner safety: 6/5 (Wait, X/5? 2/5 - "Did I get quick wins? No (failed practice)", "Was Ukrainian scary? Yes (hidden rules)")

## Critical Issues Found

### Issue 1: Hidden Grammar Traps (Irregular Verbs)
- **Location**: Section "Skill 3: Дієвідміна", Practice: Fill the Gaps
- **Original**: "Ми ___ (писати) листа." / "Вони ___ (робити) домашнє завдання."
- **Problem**: The student was just taught regular patterns (читати -> -ємо, говорити -> -ять). "Писати" has a consonant mutation (с -> ш: пишемо), and "робити" has an epenthetic l in 3pl (роблять) compared to the model "говорять" (no L). These irregularities are NOT explained. A student will guess "писаємо" or "робять" and fail.
- **Fix**: Replace with fully regular verbs for this level (e.g., "снідати", "слухати") OR explicitly teach the mutation in the Model section.

### Issue 2: Scope Creep / Contradiction (Accusative Case)
- **Location**: Section "Skill 3: Дієвідміна" examples and "Summary"
- **Original**: Examples use "Я читаю книгу" (Fem Acc -у), "Ти читаєш газету" (Fem Acc -у). Summary says: "Ready for Modules 11-20: the accusative case".
- **Problem**: The summary implies Accusative is new content for the next phase, but the examples use feminine accusative forms which change the ending (-а -> -у). This confuses the learner: have we learned this or not?
- **Fix**: Change examples to Masculine Inanimate or Neuter nouns which do not change in Accusative (e.g., "Я читаю журнал", "Ти читаєш текст"), preserving the "Nominative-like" look appropriate for A1.1.

### Issue 3: Testing Untaught Vocabulary
- **Location**: Activities File (Quiz: Question Words) vs Content File (Skill 4)
- **Original**: Quiz asks about "Скільки" (How much) and "Куди" (Where to).
- **Problem**: These words are NOT listed in the "Skill 4: Питальні речення" section (which lists only Що, Хто, Де, Як, Коли, Чому).
- **Fix**: Add "Скільки" and "Куди" to the Skill 4 list in the Content file.

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| Skill 3 | "Я читаю книгу" | "Я читаю журнал" | Scope (Avoid Fem Accusative) |
| Skill 3 | "Ти читаєш газету" | "Ти читаєш лист" | Scope (Avoid Fem Accusative) |
| Integration | "українську каву" | "український борщ" | Scope (Avoid Fem Accusative) |

## Beginner Safety Audit

"Would I Continue?" Test: 2/5
- Overwhelmed? **Fail** (Unexpected verb mutations)
- Instructions clear? **Pass**
- Quick wins? **Fail** (Practice exercises act as traps)
- Ukrainian scary? **Fail** (Rules seem to have hidden exceptions immediately)
- Come back tomorrow? **Pass** (Maybe, if resilient)

## Fix Plan to Reach 9/10

### Educational / Pedagogy / Beginner Safety: 6/10 → 9/10

**What to fix:**
1.  **Section "Skill 3: Дієвідміна"**: Change examples to avoid Feminine Accusative.
    *   Change "Я читаю книгу" → "Я читаю журнал" (Masculine Inanimate = Nominative).
    *   Change "Ти читаєш газету" → "Ти читаєш текст" (Masculine Inanimate).
    *   Change "Він читає журнал" → Keep (already ok).
2.  **Section "Skill 3: Дієвідміна"**: Replace irregular/mutating verbs in "Practice" with regular ones.
    *   Change "Ми ___ (писати) листа." → "Ми ___ (слухати) музику." (Regular: слухаємо).
    *   Change "Вони ___ (робити) домашнє завдання." → "Вони ___ (знати) це." (Regular: знають).
    *   *Alternative*: Use "снідати" (to breakfast) -> "Ми снідаємо".
3.  **Section "Skill 4: Питальні речення"**: Add missing question words to the list.
    *   Add: "**Куди** /kuˈdɪ/ = where to"
    *   Add: "**Скільки** /ˈskilʲkɪ/ = how much/many"
4.  **Integration Task**: Change "Я люблю українську каву" → "Я люблю український борщ" (Masc Inan) to avoid Accusative ending confusion before it's taught.

### Activities: 6/10 → 9/10

**What to fix:**
1.  **YAML `fill-in` (Verb Conjugation)**: Ensure the "fill-in" items match the new regular verbs in the content if intended to mirror them. (Current YAML uses "читати/говорити" which are safe, but if we change content practice, we should ensure alignment).
2.  **YAML `quiz` (Question Words)**: The fix in Content (adding Скільки/Куди) resolves the Activity error.

### Projected Overall After Fixes

Scores: Educational 9, Pedagogy 9, Activities 9, Beginner Safety 9.
Weighted Overall: ~9.2/10.

## Verdict

**FAIL**

The module fails on **Beginner Safety** and **Pedagogical Fairness**. It sets clear rules for verb conjugation and then immediately tests students on exceptions (mutations) that were not taught. It also claims Accusative case is "future content" while using it in examples. These must be fixed to pass.
