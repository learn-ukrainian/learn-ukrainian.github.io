# Рецензія: The Locative: Where Things Are

**Level:** A1 | **Module:** 13
**Overall Score:** 8.5/10
**Status:** FAIL
**Reviewed:** 2026-02-08

## Plan Verification

```
Plan-Content Alignment: [PASS]
- Sections: [all present]
- Vocabulary: [Most vocab present; 'поріх' is a hallucinated word; 'кухня' used in activities but not intro]
- Grammar scope: [clean, mostly appropriate for A1]
- Objectives: [all covered]
```

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 9/10 | <7 | Strong cultural intro ("Майдан", "Шевченка"). |
| 2 | Coherence | 9/10 | <7 | Clear progression from concepts to practice. |
| 3 | Relevance | 10/10 | <7 | Highly relevant navigation skills. |
| 4 | Educational | 8/10 | <7 | "Secret Shifts" section uses obscure/wrong examples (`поріх`). |
| 5 | Language | 8/10 | <8 | Non-existent word `поріх`; Euphony contradictions in activities. |
| 6 | Pedagogy | 8/10 | <7 | Activity keys contradict the text's own euphony rules. |
| 7 | Immersion | 9/10 | <6 | Appropriate mix of English instruction and Ukrainian examples. |
| 8 | Activities | 7/10 | <7 | Euphony quiz items mark correct answers as false; Misleading "room" explanation. |
| 9 | Richness | 9/10 | <6 | Good cultural notes and context. |
| 10 | Beginner Safety | 8/10 | <7 | "Secret Shifts" might be slightly overwhelming, but manageable. |
| 11 | LLM Fingerprint | 9/10 | <7 | Reads naturally. |
| 12 | Linguistic Accuracy | 8/10 | <9 | `поріх` error; Activity euphony policing is incorrect. |

**Weighted Overall:** 8.5/10

## Auto-Fail Checklist Results

- Russianisms: [CLEAN]
- Calques: [CLEAN]
- Grammar scope: [CLEAN]
- Activity errors: [Activity 1: items 3, 6; Activity 3: item 7 (explanation)]
- Beginner safety: 5/5

## Critical Issues Found

### Issue 1: Non-existent Word / Typo
- **Location**: Section "Consonant Changes", bullet 3.
- **Original**: "порі**х** → на поро**с**і"
- **Problem**: `Поріх` is not a common standard Ukrainian word (archaic/dialect for dust?). The intended word was likely `поріг` (threshold), but `г` changes to `з` (`на порозі`), not `с`. Or the intended word was `вухо` (ear) -> `у вусі` or `птах` (bird) -> `на птасі`.
- **Fix**: Replace with a common A1 word like "вухо" (ear) or "птах" (bird). Example: `ву**х**о → у ву**с**і`.

### Issue 2: Euphony Contradiction (Activities vs Text)
- **Location**: Activity 1 (Quiz), Item 3 and Item 6.
- **Original**: Item 3: "Я живу ___ Києві" (Correct: у, False: в). Item 6: "I am in the city" (Correct: Я у місті, False: Я в місті).
- **Problem**: The text explicitly states: "Use **в** if the previous word ends in a vowel". `Я` and `живу` end in vowels. Therefore, `в` is the strictly correct form per the text's rule (and standard Ukrainian). The quiz marks the correct form as false.
- **Fix**: Accept both `в` and `у` as correct, or fix the key to `в` to match the text's rule. For "Я живу...", `в` is preferred.

### Issue 3: Misleading Grammar Explanation
- **Location**: Activity 3 (Fill-in), Item 7 Explanation.
- **Original**: "Room name uses на."
- **Problem**: This is false. `Кімната`, `спальня`, `вітальня` all use `в/у`. `Кухня` is an exception. Teaching "Room name uses на" creates a false rule that will confuse students later.
- **Fix**: Change explanation to "The word 'кухня' exceptionally takes 'на'."

### Issue 4: Advanced/Rare Vocabulary in Examples
- **Location**: Section "Consonant Changes".
- **Original**: "стрі**х**а → на стрісі"
- **Problem**: `Стріха` (thatched roof) is not high-frequency A1 vocabulary.
- **Fix**: Use `муха` (fly) or `кожух` (coat - purely for sound example, though maybe rare too). `Муха` is already there. Just keep `муха` and add `вухо`.

## Fix Plan to Reach 9/10

### Language: 8/10 → 9/10

**What to fix:**
1.  Section "Consonant Changes": Remove `поріх` example. Replace with `вухо → у вусі`.
2.  Section "Consonant Changes": Remove `стріха` example (optional, but recommended). Use `птах → на птасі` if needed, or just stick to `муха`.

### Activities: 7/10 → 9/10

**What to fix:**
1.  `activities/13-the-locative-where-things-are.yaml`:
    -   Item 3 ("Я живу..."): Change correct answer to `в` (matches text rule) or allow both. Ideally, change sentence to one where `у` is strictly required (e.g., "Він жив **у** Києві") or accept `в`. Recommendation: Change `correct: true` for `в`.
    -   Item 6 ("I am in the city"): Change `correct: true` for `Я в місті` (matches text rule).
    -   Item 7 ("She is at the stop"): `Вона на зупинці` is correct, but check distractors.
    -   Fill-in Item 7 Explanation: Change "Room name uses на" to "The word 'кухня' typically uses 'на'."

### Projected Overall After Fixes

With `Language` raised to 9 and `Activities` raised to 9, the weighted average will exceed 9.0.

## Verification Summary

- Content lines read: ~140
- Activity items checked: 45
- Ukrainian sentences verified: ~30
- IPA transcriptions checked: (present in vocab file, generally accurate)
- Issues found: 4
- Naturalness score recommendation: 10/10 (after fixes)

## Verdict

**FAIL**

The module fails primarily due to the inclusion of a non-existent/typo word (`поріх`) in a core grammar explanation and significant contradictions between the text's euphony rules and the activity answer keys. These issues confuse beginners and penalize correct answers.
