===REVIEW_START===
# Рецензія: If I Were

**Level:** A2 | **Module:** 22
**Overall Score:** 8.3/10
**Status:** FAIL
**Reviewed:** 2026-02-09

## Plan Verification

```
Plan-Content Alignment: [PASS]
- Sections: [all present]
- Vocabulary: [Matches plan context, but YAML contains lemma errors]
- Grammar scope: [clean]
- Objectives: [all covered]
```

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 9/10 | <7 | Good flow, clear explanations, engaging topic. |
| 2 | Coherence | 9/10 | <7 | Concepts build logically from formation to usage. |
| 3 | Relevance | 9/10 | <7 | Highly relevant for A2 (dreams, polite requests). |
| 4 | Educational | 9/10 | <7 | Clear distinction between real/unreal conditions. |
| 5 | Language | 7/10 | <8 | Lemma error (`мріти`), neuter adj (`багате`), phonetic error in cloze. |
| 6 | Pedagogy | 9/10 | <7 | Good PPP structure. |
| 7 | Immersion | 8/10 | <6 | ~50% Ukrainian, well balanced. |
| 8 | Activities | 6/10 | <7 | Logic errors in Cloze (phonetic rules ignored), tautological Quiz question. |
| 9 | Richness | 9/10 | <6 | Good use of proverbs and cultural context. |
| 10 | Beginner Safety | 8/10 | <7 | 5/5 on "Would I Continue?". |
| 11 | LLM Fingerprint | 9/10 | <7 | Natural phrasing, low repetition. |
| 12 | Linguistic Accuracy | 7/10 | <9 | Wrong vocabulary lemma is a critical accuracy failure. |

**Weighted Overall:** (9*1.5 + 9*1 + 9*1 + 9*1.2 + 7*1.1 + 9*1.2 + 8*1 + 6*1.3 + 9*0.9 + 8*1.3 + 9*1 + 7*1.5) / 14.0 = **8.29/10**

## Auto-Fail Checklist Results

- Russianisms: [CLEAN] (Note: `білет` is acceptable in lottery context, though `квиток` is standard).
- Calques: [CLEAN]
- Grammar scope: [CLEAN]
- Activity errors: [FAIL] - Phonetic rule violation in Cloze; Redundant particle usage; Tautological question.
- Beginner safety: 5/5

## Critical Issues Found

### Issue 1: Vocabulary Lemma Error
- **Location**: `vocabulary/22-if-i-were.yaml` (Item: `мріти`)
- **Original**: `lemma: мріти` / translation: `to appear dimly`
- **Problem**: The module is about "Dreams" (`мріяти`). `мріти` is a different verb meaning "to loom/appear dimly". The IPA `/mrˈitɪ/` matches the wrong verb.
- **Fix**: Change to `lemma: мріяти`, `ipa: /mrˈijatɪ/`, `translation: to dream`.

### Issue 2: Incorrect Adjective Lemma
- **Location**: `vocabulary/22-if-i-were.yaml` (Item: `багате`)
- **Original**: `lemma: багате` / translation: `rich (neuter)`
- **Problem**: Adjectives should be listed in the masculine form unless specifically teaching the neuter noun (which "rich" is not here).
- **Fix**: Change to `lemma: багатий`, `ipa: /baˈɦatɪj/`, `translation: rich`.

### Issue 3: Phonetic Rule Violation in Cloze
- **Location**: `activities/22-if-i-were.yaml` (Cloze "Dreams and Wishes", line ~37)
- **Original**: `Я теж {б|би} хотів жити там`
- **Problem**: `теж` ends in a consonant (`ж`). The euphonic rule requires `би`. `теж б` is phonetically incorrect. If the first option `б` is the intended key, it teaches incorrect grammar.
- **Fix**: Change options to `{би|б}` or context to a vowel-ending word.

### Issue 4: Redundant Particle in Cloze
- **Location**: `activities/22-if-i-were.yaml` (Cloze "Dreams and Wishes", line ~40)
- **Original**: `Так, ми {б|би} могли б запрошувати`
- **Problem**: The sentence already has `могли б`. Adding another `{б|би}` creates a double particle `ми б могли б` which is clumsy and redundant.
- **Fix**: Remove the gap or the particle in text. Better: `Так, ми могли {б|би} запрошувати...` (remove `б` after `могли` if gap is kept).

### Issue 5: Tautological Quiz Question
- **Location**: `activities/22-if-i-were.yaml` (Quiz Item 5)
- **Original**: `Question: Що означає ввічливе прохання «Я б хотів замовити каву»...? Option: Я б хотів`
- **Problem**: The question asks what the phrase "Я б хотів..." means, and the correct answer is the phrase itself. This is confusing and tests nothing.
- **Fix**: Change question to `Як перекласти "I would like" українською?` or `Яка фраза є найбільш ввічливою?`.

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| Vocab | мріти | мріяти | Vocabulary Error |
| Vocab | багате | багатий | Morphology Error |
| Act | Я теж б хотів | Я теж би хотів | Euphony Rule |
| Act | ми б могли б | ми могли б | Stylistic/Redundancy |

## Beginner Safety Audit

"Would I Continue?" Test: 5/5
- Overwhelmed? [No]
- Instructions clear? [Yes]
- Quick wins? [Yes - transformation drills are easy and satisfying]
- Ukrainian scary? [No - grammar explained simply]
- Come back tomorrow? [Yes]

## Fix Plan to Reach 9/10

### Vocabulary: 7/10 → 10/10
1. `vocabulary/22-if-i-were.yaml`: Replace `lemma: мріти` block with `lemma: мріяти`, `ipa: /mrˈijatɪ/`, `translation: to dream`.
2. `vocabulary/22-if-i-were.yaml`: Replace `lemma: багате` block with `lemma: багатий`, `ipa: /baˈɦatɪj/`, `translation: rich`.
3. `vocabulary/22-if-i-were.yaml`: Change `lemma: білет` to `lemma: квиток` (translation: ticket), as it is the standard term used in the presentation examples (`я куплю квиток`).

### Activities: 6/10 → 9/10
1. `activities/22-if-i-were.yaml` (Cloze): Change `Я теж {б|би} хотів` to `Я теж {би|б} хотів` (making `би` the correct first option).
2. `activities/22-if-i-were.yaml` (Cloze): Change `ми {б|би} могли б запрошувати` to `ми {б|би} могли запрошувати` (remove the hardcoded `б` after `могли` to make the gap meaningful).
3. `activities/22-if-i-were.yaml` (Quiz): Replace Question 5 with `Question: Як найкраще перекласти "I would like"? Options: Я б хотів (True) / Я хочу (False)...`.

### Projected Overall After Fixes
(9*1.5 + 9*1 + 9*1 + 9*1.2 + 9*1.1 + 9*1.2 + 8*1 + 9*1.3 + 9*0.9 + 8*1.3 + 9*1 + 9*1.5) / 14.0 = **8.9** (approx 9.0)

## Verdict

**FAIL**

The module is well-written and pedagogically sound, but it fails on specific linguistic accuracy issues in the vocabulary list (wrong lemma for the core concept "to dream") and logical/phonetic errors in the activities. These must be fixed before release.

===REVIEW_END===
