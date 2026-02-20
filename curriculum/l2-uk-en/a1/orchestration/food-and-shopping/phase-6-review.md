# Рецензія: Food, Drinks & Shopping

**Level:** A1 | **Module:** 18
**Overall Score:** 8.3/10
**Status:** FAIL
**Reviewed:** 2026-02-18

## Plan Verification

```
Plan-Content Alignment: PASS
- Sections: Matches plan exactly (Warm-up, Presentation, Practice, Culture).
- Vocabulary: Required words present. Recommended words mostly present.
- Grammar scope: Accusative and Genitive covered as planned.
- Objectives: Met.
```

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 8/10 | <7 | Good pacing, warm tone, but activity disconnects reduce safety. |
| 2 | Coherence | 8/10 | <7 | Logical flow, though Accusative+Genitive in one lesson is heavy. |
| 3 | Relevance | 10/10 | <7 | Essential survival vocabulary. |
| 4 | Educational | 9/10 | <7 | Clear explanations of complex case rules (Gender vs Case). |
| 5 | Language | 10/10 | <8 | Natural Ukrainian, correct grammar. |
| 6 | Pedagogy | 7/10 | <7 | Activities test untaught vocabulary (Major "Safety" violation). |
| 7 | Immersion | 10/10 | <6 | 27% is appropriate for A1.2. |
| 8 | Activities | 6/10 | <7 | **FAIL**: Items contain words not taught in the lesson. |
| 9 | Richness | 9/10 | <6 | Strong cultural notes (Palianytsia, Bread/Salt). |
| 10 | Beginner Safety | 7/10 | <7 | Testing unknown words causes frustration. |
| 11 | LLM Fingerprint | 8/10 | <7 | Some cliché phrasing ("delicious world", "bustling kitchen"), but acceptable. |
| 12 | Linguistic Accuracy | 10/10 | <9 | No errors found in Ukrainian text. |

**Weighted Overall:** 8.3/10

## Auto-Fail Checklist Results

- Russianisms: [CLEAN]
- Calques: [CLEAN]
- Grammar scope: [CLEAN]
- Activity errors: **[FAILED]** (Untaught vocabulary in Fill-in/Match-up)
- Beginner Safety: 3/5 (Failed "Instructions clear?" due to unknown words)

## Critical Issues Found

### Issue 1: Activity Error (Untaught Vocabulary)
- **Location**: `activities/food-and-shopping.yaml`, Activity 6 (Match-up) & Activity 10 (Fill-in)
- **Original**: «тарілка» - «супу» (Act 6); «олії» (Act 10)
- **Problem**: The words **тарілка** (plate) and **олія** (oil) appear nowhere in the lesson content. A1 learners cannot answer this without guessing.
- **Fix**: Replace with taught vocabulary.
    - Act 6: Replace `тарілка/супу` with `кілограм/моркви` (taught).
    - Act 10: Replace `олії` with `соку` (taught).

### Issue 2: Incomplete Vocabulary YAML
- **Location**: `vocabulary/food-and-shopping.yaml`
- **Original**: Contains only 20 items.
- **Problem**: Missing ~12 core words explicitly taught in the lesson: **цибуля, морква, свинина, йогурт, булка, батон, пакет, склянка, чашка, пачка**.
- **Fix**: Add all missing bolded terms from the lesson to the vocabulary file. This is critical for flashcard generation.

### Issue 3: Missing Genitive Plural Explanation
- **Location**: `content` section "Одиниці виміру"
- **Original**: "Plural Genitive... For now, just memorize: Кілограм яблук"
- **Problem**: Activity 6 matches "кілограм" -> "яблук" (Plural) AND "кілограм" -> "картоплі" (Singular). The lesson explains Feminine Singular Genitive (-а -> -и), which covers "картоплі", but the distinction between why it's "kilo of potato (sg)" vs "kilo of apples (pl)" might confuse learners without a brief note that mass nouns stay singular.
- **Fix**: Add a small note: "Note: For mass items like potato or carrot, we use the singular form (like 'water'). For countable items like apples, we use plural."

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| N/A | N/A | N/A | None Found |

## Beginner Safety Audit

"Would I Continue?" Test: 3/5
- Overwhelmed? [Pass] - Explanations are clear.
- Instructions clear? [Fail] - Activities ask for unknown words.
- Quick wins? [Pass] - Good easy anagrams.
- Ukrainian scary? [Pass] - "I love pizza" is approachable.
- Come back tomorrow? [Pass] - If activities are fixed.

## Strengths
- **Cultural Depth**: The "Myth-buster" about *Palianytsia* and the "Bread and Salt" context are excellent for engagement.
- **Grammar Clarity**: The "Golden Rule" for Accusative (Masc/Neut don't change, Fem changes) is presented very clearly.

## Fix Plan to Reach 9/10

### Activities: 6/10 → 9/10
**What to fix:**
1. Activity 6: Remove/replace `тарілка`.
2. Activity 10: Remove/replace `олії`.
3. Verify all distractor options in quizzes are also known words.

### Pedagogy: 7/10 → 9/10
**What to fix:**
1. Ensure Vocabulary YAML matches Content 1:1. Add the missing ~12 words.
2. Add the brief "Mass vs Count" note for Genitive quantity to prevent confusion between `картоплі` (sg) and `яблук` (pl).

**Expected score after fix:** 9.2/10

## Verification Summary

- Content lines read: 230
- Activity items checked: 133
- Ukrainian sentences verified: ~50
- IPA transcriptions checked: 20
- Issues found: 3

## Verdict

**FAIL**

The module is linguistically sound and culturally rich, but fails on **Beginner Safety** and **Activity Quality**. It tests vocabulary (`тарілка`, `олія`) that was never taught, which causes frustration for A1 learners. Additionally, the **Vocabulary YAML** is significantly incomplete, missing over a dozen core words taught in the text, which will break the flashcard experience. These must be fixed before release.
