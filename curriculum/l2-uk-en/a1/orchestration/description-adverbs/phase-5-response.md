# Рецензія: Description: Adverbs

**Level:** A1 | **Module:** 28
**Overall Score:** 8.9/10
**Status:** FAIL
**Reviewed:** 2026-02-08

## Plan Verification

Plan-Content Alignment: [PASS]
- Sections: [all present]
- Vocabulary: [8/8 required present; Recommended "легко/важко" only in activities; Extra vocab: постійно, деколи, час від часу (in activities)]
- Grammar scope: [FAIL: Past tense "втомилась" found]
- Objectives: [all covered]

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 9/10 | <7 | Clear progression, friendly tone ("It is very simple and logical!"). |
| 2 | Coherence | 9/10 | <7 | Logical flow from Adjective -> Adverb -> Frequency. |
| 3 | Relevance | 9/10 | <7 | Very useful for daily conversation ("How are things?", Habits). |
| 4 | Educational | 9/10 | <7 | Good explanations of the derivation rule. |
| 5 | Language | 8/10 | <8 | **FAIL**: Scope creep (Past tense "втомилась"). |
| 6 | Pedagogy | 8/10 | <7 | **FAIL**: Activities test vocabulary NOT taught in the lesson (`постійно`, `деколи`, `час від часу`). |
| 7 | Immersion | 8/10 | <6 | Good mix of examples. |
| 8 | Activities | 7/10 | <7 | Ambiguous distractors in Fill-in; Missing punctuation in Unjumble answer key. |
| 9 | Richness | 9/10 | <6 | Good cultural notes (Myth vs Fact, Songs). |
| 10 | Beginner Safety | 10/10 | <7 | clear instructions, not overwhelming. |
| 11 | LLM Fingerprint | 10/10 | <7 | Feels curated. |
| 12 | Linguistic Accuracy | 9/10 | <9 | Minor stress preference for "завжди". |

**Weighted Overall:** (9*1.5 + 9*1.0 + 9*1.0 + 9*1.2 + 8*1.1 + 8*1.2 + 8*1.0 + 7*1.3 + 9*0.9 + 10*1.3 + 10*1.0 + 9*1.5) / 14.0 = **124.7 / 14.0 = 8.90/10**

## Auto-Fail Checklist Results

- Russianisms: [CLEAN]
- Calques: [CLEAN]
- Grammar scope: [FAIL] Past tense "втомилась" (A1.28 vs Past Tense A1.38).
- Activity errors: [FAIL] Ambiguous questions; Unjumble answer key punctuation; Testing untaught vocabulary.
- Beginner safety: 5/5

## Critical Issues Found

### Issue 1: Grammar Scope Creep (Past Tense)
- **Location**: Line 89 / Section "Degree Adverbs"
- **Original**: "Вона трохи **втомилась**."
- **Problem**: "Втомилась" is Past Tense (she got tired). Past tense is not taught until Module 38. Students at Module 28 do not know this form.
- **Fix**: Change to an adjective or present tense structure known to students. Suggestion: "Вона трохи **сумна**." (She is a little sad) or "Це трохи **дорого**." (It is a little expensive) - using the adverb/predicative structure.

### Issue 2: Vocabulary Scope Creep in Activities
- **Location**: `activities/28-description-adverbs.yaml` / Activity 2 "Frequency Scale"
- **Original**: Items include `постійно`, `деколи`, `час від часу`, `майже ніколи`, `зовсім не часто`.
- **Problem**: These words are NOT introduced in the lesson content (Markdown). The lesson only teaches `завжди`, `часто`, `зазвичай`, `іноді`, `рідко`, `ніколи`. Students cannot sort words they haven't seen.
- **Fix**: Remove untaught words from the sorting activity. Stick to the frequency adverbs explicitly taught in the "Frequency Adverbs" section.

### Issue 3: Ambiguous Distractors
- **Location**: `activities/28-description-adverbs.yaml` / Activity 5 "How Often?", Item 2
- **Original**: "Вона ___ читає книжки." (Answer: `часто`. Options: `часто`, `ніколи`, `швидко`, `добре`)
- **Problem**: `швидко` and `добре` are grammatically and semantically valid completions ("She reads books quickly", "She reads books well"). Multiple valid answers.
- **Fix**: Change distractors to be invalid. E.g., Adjectives (`швидка`, `добра`) or non-fitting words.

### Issue 4: Unjumble Punctuation
- **Location**: `activities/28-description-adverbs.yaml` / Activity 8 "Describing Actions", Item 9
- **Original**: `answer: Як справи Добре`
- **Problem**: Missing punctuation makes the sentence run-on.
- **Fix**: `answer: Як справи? Добре.` (Or just "Добре" if it's a response, but the words list includes "Як", "справи").

### Issue 5: IPA Stress for "Завжди"
- **Location**: Line 60 / Table "Frequency Adverbs"
- **Original**: `завжди` /ˈzɑvʒdɪ/
- **Problem**: While `/ˈzɑvʒdɪ/` (first syllable stress) exists, the standard literary stress is usually `/zɑvˈʒdɪ/` (second syllable).
- **Fix**: Update IPA to `/zɑvˈʒdɪ/` for standard pronunciation, or keep if specifically aiming for a common spoken variant, but consistency with standard dictionaries is preferred for learners.

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| 89 | Вона трохи втомилась. | Вона трохи сумна. / Це трохи дорого. | Scope (Past Tense) |
| Activity | постійно, деколи, час від часу | [REMOVE] | Scope (Untaught Vocab) |

## Beginner Safety Audit

"Would I Continue?" Test: 5/5
- Overwhelmed? Pass
- Instructions clear? Pass
- Quick wins? Pass (Adjective -> Adverb rule is simple)
- Ukrainian scary? Pass
- Come back tomorrow? Pass

Emotional beats:
- Welcome: Yes ("Привіт! Сьогодні ми вивчаємо прислівники...")
- Curiosity: Yes ("How Does He Do It?")
- Quick wins: Yes ("It is very simple... Formula...")
- Encouragement: Yes ("Simple and beautiful!", "Молодець!")
- Progress: Yes ("Now you can describe how you do something.")

## Strengths
- Excellent explanation of the Adjective → Adverb transformation.
- "Myth vs Fact" section effectively builds confidence.
- Dialogue examples are natural and useful for A1 level.

## Fix Plan to Reach 9/10

### Language: 8/10 → 9/10
**What to fix:**
1. **Line 89**: Change "Вона трохи втомилась." → "Вона трохи **сумна**." (She is a little sad). This removes the past tense verb `втомилась`.

### Activities: 7/10 → 9/10
**What to fix:**
1. **Activity 2 (Group Sort)**: Remove `постійно`, `деколи`, `час від часу`, `майже ніколи`, `зовсім не часто`. Use only taught words: `завжди`, `часто`, `зазвичай`, `іноді`, `рідко`, `ніколи`. If 10 items are needed, repeat common ones or add "дуже часто", "дуже рідко" (combinations of taught words).
2. **Activity 5 (Fill-in)**: Item 2 "Вона ___ читає книжки". Change distractors from `швидко`, `добре` to adjectives like `швидка`, `добра` or noun `радіо`.
3. **Activity 8 (Unjumble)**: Item 9. Change answer "Як справи Добре" → "Як справи? Добре."

### Pedagogy: 8/10 → 9/10
**What to fix:**
1. Removing the untaught vocabulary from activities (see above) resolves the pedagogical disconnect.

### Projected Overall After Fixes
(9*1.5 + 9*1.0 + 9*1.0 + 9*1.2 + **9**+1.1 + **9**+1.2 + 8*1.0 + **9**+1.3 + 9*0.9 + 10*1.3 + 10*1.0 + 9*1.5) / 14.0 = **130.8 / 14.0 = 9.34/10**

## Verification Summary
- Content lines read: 172
- Activity items checked: 9 activities (~60 items)
- Ukrainian sentences verified: ~25
- IPA transcriptions checked: 11
- Issues found: 5 (1 Scope Creep in Content, 1 Scope Creep in Activity, 1 Ambiguity, 1 Punctuation, 1 IPA preference)
- Naturalness score recommendation: 10/10 (The Ukrainian itself is natural, just one verb was too advanced grammatically).

## Verdict

**FAIL**

The module is well-written and engaging but fails on **Grammar Scope** (using Past Tense before it is taught) and **Pedagogical Fairness** (testing vocabulary in activities that was never taught in the lesson). These must be fixed to protect the learner's progression path.