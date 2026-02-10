# Рецензія: In Order To

**Level:** A2 | **Module:** 31
**Overall Score:** 8.7/10
**Status:** FAIL
**Reviewed:** 2026-02-09

## Plan Verification

```
Plan-Content Alignment: [PASS]
- Sections: [PASS] (All main sections present; "Purpose with Nouns" covered under "Synonyms" via "Задля", though "Для" + Noun is less explicit)
- Vocabulary: [FAIL] (Vocabulary file contains hallucinations and ghost words not in text: 'комі', 'шиплячий')
- Grammar scope: [PASS] (Appropriate A2 level)
- Objectives: [PASS]
```

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 9/10 | <7 | Strong, engaging narrative ("Why we do what we do"). |
| 2 | Coherence | 10/10 | <7 | Logical flow from Same Subject -> Different Subject -> Formal. |
| 3 | Relevance | 10/10 | <7 | Highly relevant for A2 (expressing purpose is essential). |
| 4 | Educational | 10/10 | <7 | Clear distinction between Infinitive and Past Tense logic. |
| 5 | Language | 9/10 | <8 | Text is natural and accurate; error lies in metadata. |
| 6 | Pedagogy | 9/10 | <7 | PPP structure effectively used. |
| 7 | Immersion | 9/10 | <6 | Good balance of English explanation and Ukrainian examples. |
| 8 | Activities | 10/10 | <7 | Excellent variety; "The Project" cloze is particularly contextual. |
| 9 | Richness | 9/10 | <6 | Cultural note on toasts ("Щоб ти був здоровий!") is excellent. |
| 10 | Beginner Safety | 9/10 | <7 | Clear rules, "Mandatory Comma" tip is helpful. |
| 11 | LLM Fingerprint | 10/10 | <7 | Voice is warm and specific, not generic AI. |
| 12 | Linguistic Accuracy | 7/10 | <9 | **FAIL**: Vocabulary file contains hallucinated lemmas and bad translations. |

**Weighted Overall:** 8.7/10

## Auto-Fail Checklist Results

- Russianisms: [CLEAN]
- Calques: [CLEAN]
- Grammar scope: [CLEAN]
- Activity errors: [CLEAN]
- Beginner safety: 5/5

## Critical Issues Found

### Issue 1: Vocabulary Hallucinations (Metadata)
- **Location**: `vocabulary/31-in-order-to.yaml`
- **Problem**: The vocabulary extraction tool produced garbage lemmas that will confuse learners in flashcards.
    1. `lemma: комі` / `translation: Komi` -> The text mentions "Mandatory Comma" (**кома**). "Komi" is an ethnic group/region.
    2. `lemma: шиплячий` / `translation: sibilant` -> Word is **not in the text**. Likely hallucinated from the letter 'Щ' context.
    3. `lemma: бажай` / `translation: wish` / `pos: noun` -> `бажай` is the imperative verb "Wish!". The noun is **бажання** (which is also listed later).
    4. `lemma: бажальний` / `translation: desirable` -> Incorrect. `бажальний` is "optative" (grammar mood). "Desirable" is **бажаний**.
- **Fix**: Purge ghost words and fix lemmas.

### Issue 2: Plan Compliance (Minor)
- **Location**: Section "Synonyms for Purpose: Аби та Задля"
- **Original**: Mentions only `Задля` with nouns.
- **Problem**: Plan requested "Purpose with Nouns: Для + Genitive". While `Для того щоб` is covered, the simple `Для` + Noun (e.g., "Це для тебе") as a purpose marker is missing, despite being in the plan.
- **Fix**: Add a brief bullet point about `Для` + Genitive in the Synonyms section.

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| Vocab | комі | кома | Hallucination |
| Vocab | бажай | бажання | Bad Lemma |
| Vocab | бажальний | (remove) | Ghost Word |
| Vocab | шиплячий | (remove) | Ghost Word |

## Beginner Safety Audit

"Would I Continue?" Test: 5/5
- Overwhelmed? [No]
- Instructions clear? [Yes]
- Quick wins? [Yes - "I study to work"]
- Ukrainian scary? [No]
- Come back tomorrow? [Yes]

## Strengths
- The explanation of the "Past Tense Loophole" (Different Subjects) is intuitive and avoids overly complex terminology like "Subjunctive Mood".
- The cultural connection to toasts is a great hook for motivation.
- Activities are robust and context-heavy.

## Fix Plan to Reach 9/10

### Linguistic Accuracy: 7/10 → 10/10

**What to fix:**
1.  **File `vocabulary/31-in-order-to.yaml`**:
    *   Remove item: `lemma: комі`
    *   Add item: `lemma: кома`, `translation: comma`, `pos: noun`, `gender: f`
    *   Remove item: `lemma: шиплячий`
    *   Remove item: `lemma: бажай`
    *   Remove item: `lemma: бажальний`
    *   Ensure `lemma: бажання` is present (it is).

### Plan Compliance (Relevance): 9/10 → 10/10

**What to fix:**
1.  **File `31-in-order-to.md`**, Section "Synonyms for Purpose":
    *   Add a bullet point:
        ```markdown
        - **Для** — простий спосіб вказати мету, використовуючи іменник.
          - Я тут **для роботи**. (I am here **for work**.)
          - Це **для тебе**. (This is **for you**.)
        ```
    *   *Reason*: Explicitly satisfies the plan requirement "Purpose with Nouns: Для + Genitive".

### Projected Overall After Fixes

```
(9*1.5 + 10*1 + 10*1 + 10*1.2 + 9*1.1 + 9*1.2 + 9*1 + 10*1.3 + 9*0.9 + 10*1.3 + 10*1 + 10*1.5) / 14 = ~9.6
```

## Verification Summary

- Content lines read: ~140
- Activity items checked: ~40
- Ukrainian sentences verified: ~50
- IPA transcriptions checked: 0 (Not in text)
- Issues found: 4 (Vocab hallucinations)
- Naturalness score recommendation: 10/10

## Verdict

**FAIL**

The content is excellent, but the vocabulary metadata (which drives flashcards) contains severe hallucinations ("Komi" for "Comma", ghost words). These must be cleaned up before the module can be considered "safe" for learners.