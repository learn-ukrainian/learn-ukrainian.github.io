# Рецензія: Checkpoint: Word Formation

**Level:** A2 | **Module:** 44
**Overall Score:** 7.5/10
**Status:** FAIL
**Reviewed:** 2026-02-10

## Plan Verification

```
Plan-Content Alignment: [PASS]
- Sections: [all present]
- Vocabulary: [Plan hints used; Ukrainian terms appear in unjumble]
- Grammar scope: [clean]
- Objectives: [all covered]
```

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 8/10 | <7 | Clear structure, but marred by Latin typo and ambiguous activities. |
| 2 | Coherence | 9/10 | <7 | Logical flow from prefixes to suffixes to roots. |
| 3 | Relevance | 9/10 | <7 | Highly relevant for A2 expansion. |
| 4 | Educational | 8/10 | <7 | Good explanations, but "Mark the words" activity is pedagogically broken. |
| 5 | Language | 7/10 | <8 | Latin typo "napisав", clumsy tautology "словотвору слів", punctuation missing in unjumble. |
| 6 | Pedagogy | 6/10 | <7 | Activity count mismatches; Mark-the-words asks for morphemes but tool likely selects words. |
| 7 | Immersion | 8/10 | <6 | Good mix, though headings are English (standard for A2). |
| 8 | Activities | 6/10 | <7 | Technical failures (cloze typo, mark-words logic), count mismatches. |
| 9 | Richness | 9/10 | <6 | Content is dense and valuable. |
| 10 | Beginner Safety | 8/10 | <7 | Clear, not overwhelming despite the meta-topic. |
| 11 | LLM Fingerprint | 8/10 | <7 | Generally natural, but some robotic definitions in unjumble. |
| 12 | Linguistic Accuracy | 6/10 | <9 | "napisав", wrong POS/IPA for "читати". |

**Weighted Overall:** 7.5/10

## Auto-Fail Checklist Results

- Russianisms: [CLEAN]
- Calques: [CLEAN]
- Grammar scope: [CLEAN]
- Activity errors: [FAIL] (Typo "napisав", Cloze duplication, Mark-the-words logic)
- Beginner safety: 5/5

## Critical Issues Found

### Issue 1: Latin Script / Typo
- **Location**: Activities YAML / `mark-the-words` / `text`
- **Original**: "Український письменник napisав музичну п'єсу..."
- **Problem**: The word `napisав` mixes Latin `napis` with Cyrillic `ав` (or is fully Latin `napis` plus separate `ав`?). This is a critical text generation failure.
- **Fix**: Change to `написав`.

### Issue 2: Broken "Mark the Words" Logic
- **Location**: Activities YAML / `mark-the-words`
- **Original**: Answers: `при`, `ви`, `Читач`, `читання`, ... / Text: "Він прийшов..."
- **Problem**: The instruction asks to find "Word Parts" (prefixes/roots), but `mark-the-words` activities typically select **whole words**. You cannot click just the `при` in `прийшов` in most web interfaces. If the user clicks `прийшов` and the key is `при`, it will likely mark it wrong.
- **Fix**: Change activity type to `fill-in` or change instruction to "Click the **words** that contain prefixes/suffixes" and update answers to full words (`прийшов`, `вийшов`).

### Issue 3: Cloze Prefix Duplication
- **Location**: Activities YAML / `cloze` / Item "Зробити ще раз"
- **Original**: "Зробити ще раз = пере{переписати|написати|дописати}"
- **Problem**: The text before the brace is `пере`. If the correct answer is `переписати`, the result reads `перепереписати`.
- **Fix**: Change to "Зробити ще раз = {переписати|написати|дописати}" OR "Зробити ще раз = пере{писати|робити|читати}".

### Issue 4: Vocabulary Metadata Errors
- **Location**: Vocabulary YAML / Item `читати`
- **Original**: `pos: noun`, `gender: f`, `ipa: /t͡ʃɪtˈa/`
- **Problem**: `читати` is a VERB (infinitive), not a noun. It has no gender. IPA is missing the final syllable `/t͡ʃɪtˈatɪ/`.
- **Fix**: `pos: verb`, remove `gender`, fix IPA to `/t͡ʃɪtˈatɪ/`.

### Issue 5: Missing Activity Items
- **Location**: Activities YAML
- **Problem**: Plan requires 12 items for `fill-in`, 8 for `error-correction`, 8 for `unjumble`.
- **Actual**: `fill-in` (8), `error-correction` (6), `unjumble` (6).
- **Fix**: Add missing items to meet the quota.

### Issue 6: Unjumble Grammar & Tautology
- **Location**: Activities YAML / `unjumble`
- **Original**: "Українська мова має дуже багату систему словотвору слів"
- **Problem**: "словотвору слів" is redundant (word-formation of words). Also missing punctuation in other items (`...слів щоб...`).
- **Fix**: Remove `слів` -> "...систему словотвору". Add commas: "...корені слів, щоб...".

### Issue 7: Ambiguous Fill-in
- **Location**: Activities YAML / `fill-in` / Item 1
- **Original**: "Він [___] до класу вчасно." (Options: прийшов, вийшов, увійшов...)
- **Problem**: Without the English cue "(arrived)" used in the content, `увійшов` (entered) is also semantically correct.
- **Fix**: Add English context to the sentence: "Він [___] до класу вчасно. (arrived)" or ensure the prompt explicitly asks for "arrival".

## Strengths
- Excellent conceptual breakdown of word formation (Theory-First).
- "Myth Buster" about prefixes is engaging and culturally relevant.
- Clear distinction between `при-`/`ви-` and root families.

## Fix Plan to Reach 9/10

### Linguistic Accuracy: 6/10 → 9/10
**What to fix:**
1. Activities YAML `mark-the-words`: Fix `napisав` → `написав`.
2. Vocabulary YAML: Fix `читати` POS to `verb`, remove gender, fix IPA.
3. Activities YAML `cloze`: Fix `пере{переписати}` → `пере{писати}` or `{переписати}`.

### Activities: 6/10 → 9/10
**What to fix:**
1. `fill-in`: Add 4 items (Total 12). Add English cues to existing items to resolve ambiguity.
2. `error-correction`: Add 2 items (Total 8).
3. `unjumble`: Add 2 items (Total 8). Fix punctuation in answers (add commas/periods).
4. `mark-the-words`: Change strategy. Either ask to click WHOLE words (`answers: [прийшов, вийшов...]`) or change to a different activity type (e.g., `drag-text` to drag prefixes to roots).

### Language: 7/10 → 9/10
**What to fix:**
1. Activities YAML `unjumble`: Change "систему словотвору слів" → "систему словотвору".
2. Ensure unjumble target sentences have proper punctuation (commas before `що`, `яка`).

### Projected Overall After Fixes
(8+9+9+8+9+9+8+9+9+8+8+9) / 12 ≈ **8.6/10** (Wait, let's re-calc: 7.5 base. Fixing Activity/Lang/Acc -> ~9.0).
Weighted: (8*1.5 + 9 + 9 + 8*1.2 + 9*1.1 + 9*1.2 + 8 + 9*1.3 + 9*0.9 + 8*1.3 + 8 + 9*1.5) / 14 = **8.85**.
Close enough to pass, as mostly technical errors.

## Verification Summary
- Content lines read: 180
- Activity items checked: 60+
- Ukrainian sentences verified: 30+
- IPA transcriptions checked: 5
- Issues found: 7 (3 Critical)
- Naturalness score recommendation: 8/10

## Verdict
**FAIL**

Blocking issues:
1.  **Latin script typo** in Ukrainian text (`napisав`).
2.  **Pedagogically broken activity** (`mark-the-words` asking for substrings).
3.  **Vocabulary metadata error** (verb labeled as noun).
4.  **Activity count mismatches** against plan.