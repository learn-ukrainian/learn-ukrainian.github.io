# Рецензія: Questions & Negation

**Level:** A1 | **Module:** 07
**Overall Score:** 6.9/10
**Status:** FAIL
**Reviewed:** 2026-02-08

## Plan Verification

```
Plan-Content Alignment: [FAIL]
- Sections: [PASS] All sections present.
- Vocabulary: [FAIL] Core words present in text, but activity contains 7+ untaught words (сьогодні, завтра, щодня, etc.).
- Grammar scope: [FAIL] Genitive case (чаю, Львова) and irregular verbs (їмо, п'ю) used before introduction.
- Objectives: [PASS] Objectives covered.
```

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 7/10 | <7 | Activities use untaught vocabulary, frustrating the user. |
| 2 | Coherence | 8/10 | <7 | Lesson flow is logical. |
| 3 | Relevance | 7/10 | <7 | Uses "звичайно" for "usually", which is arguably archaic/Russian-influenced vs modern "зазвичай". |
| 4 | Educational | 6/10 | <7 | Scope creep in examples hinders focused learning. |
| 5 | Language | 7/10 | <8 | Stylistic error with "звичайно"; otherwise correct. |
| 6 | Pedagogy | 6/10 | <7 | Testing untaught concepts (activities). |
| 7 | Immersion | 8/10 | <6 | Good use of dialogue, though metric says 69% (likely high due to activities). |
| 8 | Activities | 5/10 | <7 | Multiple items test words/grammar not taught in this or previous modules. |
| 9 | Richness | 7/10 | <6 | Good dialogues, but vocabulary selection in examples is inconsistent with level. |
| 10 | Beginner Safety | 6/10 | <7 | High frustration risk due to unfair activities ("Would I Continue?" 2/5). |
| 11 | LLM Fingerprint | 8/10 | <7 | "Звичайно" is a common LLM mistranslation of "usually". |
| 12 | Linguistic Accuracy | 8/10 | <9 | Grammar is correct, but register/lexical choice is off. |

**Weighted Overall:** 6.87 = **6.9/10**

## Auto-Fail Checklist Results

- Russianisms: [list] "звичайно" used for "usually" (better: "зазвичай").
- Calques: [CLEAN]
- Grammar scope: [list] Irregular verbs (їмо, п'ю, хочу), Genitive case (чаю).
- Activity errors: [list] Untaught vocabulary (сьогодні, завтра, вчора, щодня, щоранку, питання, відповідь).
- Beginner safety: 2/5

## Critical Issues Found

### Issue 1: Lexical Choice ("Звичайно")
- **Location**: Line 108 (Table), Line 113, Line 192, Activities (Group Sort, Anagram)
- **Original**: "звичайно" / "usually"
- **Problem**: While "звичайно" can mean "usually", it primarily means "of course/certainly". In modern Ukrainian, "зазвичай" is the standard word for "usually". Using "звичайно" confuses learners and sounds unnatural/Russian-calqued ("конечно" vs "обычно").
- **Fix**: Replace all instances of "звичайно" with "зазвичай".

### Issue 2: Activity Scope Creep (Vocabulary)
- **Location**: Activities (Group-sort "Frequency Adverbs", Anagram "Frequency Words", Anagram "Question Words")
- **Original**: "щодня", "щоранку", "сьогодні", "завтра", "вчора", "питання", "відповідь"
- **Problem**: None of these words are taught in the module or prerequisite modules. Testing them is unfair.
- **Fix**: Remove these items or replace with known words (e.g., "завжди", "часто", "ніколи").

### Issue 3: Grammar Scope Creep (Verbs)
- **Location**: Activities (Fill-in "Add Negation", Quiz "Negative Sentence Order"), Content (Line 111, 113)
- **Original**: "Ми ніколи не їмо м'ясо", "Я ніколи не п'ю каву", "Я не хочу чаю", "снідаю"
- **Problem**: Verbs "їсти" (їмо), "пити" (п'ю), "хотіти" (хочу) are irregular or Conjugation 2/stem-changing, not yet taught (Module 06 covered basic Conj 1). "Снідати" is Conj 1 but new vocab.
- **Fix**: Change examples to use known Conj 1 verbs like "читати", "знати", "працювати", "слухати", "думати".
    - "Ми ніколи не їмо м'ясо" → "Ми ніколи не слухаємо рок" (We never listen to rock).
    - "Я ніколи не п'ю каву" → "Я ніколи не працюю вдома" (I never work at home).

### Issue 4: Grammar Scope Creep (Cases)
- **Location**: Activity Quiz "Negative Sentence Order"
- **Original**: "Я не хочу чаю"
- **Problem**: "Чаю" is Genitive/Partitive case. Cases are introduced in A1-10.
- **Fix**: "Я не читаю книгу" (Accusative/Direct Object usually matches Nom for inanimate, or just intransitive: "Я не читаю"). Or "Я не знаю" (I don't know).

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| 108 | звичайно | зазвичай | Lexical / Naturalness |
| 113 | снідаю | читаю | Vocabulary Scope |
| 111 | п'ю | працюю | Grammar Scope (Irregular Verb) |
| Act | їмо | слухаємо | Grammar Scope (Irregular Verb) |
| Act | чаю | (change sentence) | Grammar Scope (Case) |

## Beginner Safety Audit

"Would I Continue?" Test: 2/5
- Overwhelmed? **Fail** (Activities ask for words I don't know)
- Instructions clear? **Pass**
- Quick wins? **Fail** (Getting answers wrong because I wasn't taught the words)
- Ukrainian scary? **Fail** (Irregular verbs appear without explanation)
- Come back tomorrow? **Fail** (Unfair testing is demotivating)

Emotional beats: 2 found
- Welcome: Line 3 "You've learned to make statements..."
- Curiosity: Line 11 "Did You Know?"
- Quick wins: None in activities due to scope creep.
- Encouragement: Line 160 "Нічого! Це нормально."
- Progress: Missing clear milestone check.

## Strengths
- Clear explanation of the "Чи" particle.
- Good contrast with English "do/does".
- "Cultural Insight" regarding directness is valuable.

## Fix Plan to Reach 9/10 (REQUIRED)

### Vocabulary & Language: 7/10 → 9/10

**What to fix:**
1.  **Global Replace**: Change "звичайно" to "зазвичай" in `07-questions-and-negation.md` (Lines 108, 113, 192) and `activities/07-questions-and-negation.yaml` (Items: "звичайно").
2.  **Content Line 113**: Change "Я звичайно снідаю вдома" → "Я зазвичай читаю вдома". (Avoids untaught "снідати").
3.  **Content Line 111**: Change "Я ніколи п'ю каву" (and the correct version "Я ніколи не п'ю каву") → "Я ніколи не працюю вдома" (Positive: "Я ніколи працюю..."). Avoids irregular "пити".

### Activities: 5/10 → 9/10

**What to fix:**
1.  **Group-sort "Frequency Adverbs"**: Remove items "щодня", "щоранку". Keep only "завжди", "зазвичай" (was звичайно), "часто", "іноді", "рідко", "ніколи".
2.  **Anagram "Frequency Words"**: Remove "сьогодні", "завтра", "вчора", "щоранку", "щодня", "правда". Add "рідко", "часто", "ніколи".
3.  **Anagram "Question Words"**: Remove "питання", "відповідь".
4.  **Fill-in "Add Negation"**:
    - Change "Ми ___ ___ їмо м'ясо" → "Ми ___ ___ слухаємо рок" (answer: ніколи не).
    - Change "Я ___ ___ п'ю каву" → "Я ___ ___ працюю тут" (answer: ніколи не).
    - Change "Я ___ хочу чаю" → "Я ___ читаю газету" (answer: не).
5.  **Quiz "Negative Sentence Order"**:
    - Change "Ми ніколи не їмо м'ясо" → "Ми ніколи не граємо" (We never play).
    - Change "Я ніколи не п'ю каву" → "Я ніколи не співаю" (I never sing).
    - Change "Я не хочу чаю" → "Я не знаю це" (I don't know this).

### Pedagogy: 6/10 → 8/10

**What to fix:**
1.  **Content Line 78/80**: Add a small note or just accept phrases "Я з Києва", "Я з Америки" as fixed expressions, but ensure no activities test the Genitive case formation yet. (Current activities don't test this, so just fixing the verbs/vocab above is sufficient).
2.  **Content Line 129**: "Куди ти йдеш?" (Where are you going?). "Йдеш" is irregular/motion. Replace with "Куди ти?" (Where are you [going]?) - very common colloquial ellipsis, avoids verb conjugation issues. Or "Де ти працюєш?" (Where do you work?).
    - Recommendation: Change example "Куди ти йдеш?" → "Куди ми йдемо?" (Where are we going?) or just keep "Куди ти?" if ellipsis is acceptable. Actually, "Куди ти йдеш?" is very high frequency. Add a gloss: "(йдеш = are going)".

### Projected Overall After Fixes

(9.0 Experience + 9.0 Coherence + 9.0 Relevance + 9.0 Educational + 9.0 Language + 9.0 Pedagogy + 9.0 Immersion + 9.0 Activities + 8.0 Richness + 9.0 Safety + 9.0 LLM + 9.0 Accuracy) / 14 ≈ **8.9 - 9.0**

## Verification Summary

- Content lines read: 218
- Activity items checked: 75+
- Ukrainian sentences verified: ~40
- IPA transcriptions checked: 15
- Issues found: 15+ (mostly scope creep and one lexical choice)
- Naturalness score recommendation: 7/10 (current), 10/10 (after "зазвичай" fix)

## Verdict

**FAIL**

Blocking issues:
1.  Use of "звичайно" (naturalness/style).
2.  Significant scope creep in activities (untaught vocabulary and grammar).
3.  Irregular verbs and cases used in examples without explanation.
