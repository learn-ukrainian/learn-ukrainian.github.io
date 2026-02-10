# Рецензія: At the Restaurant

**Level:** A1 | **Module:** 36
**Overall Score:** 8.4/10
**Status:** FAIL
**Reviewed:** 2026-02-09

## Plan Verification

```
Plan-Content Alignment: [FAIL]
- Sections: [PASS] All sections present.
- Vocabulary: [FAIL] 0/8 required words from plan found in vocabulary file.
- Grammar scope: [FAIL] Instrumental Plural ("з друзями") is out of scope.
- Objectives: [PASS] All objectives covered.
```

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 9/10 | <7 | Clear, practical, and culturally relevant. |
| 2 | Coherence | 9/10 | <7 | Logical flow from booking to paying. |
| 3 | Relevance | 10/10 | <7 | Highly relevant survival skills. |
| 4 | Educational | 9/10 | <7 | Good explanation of cultural norms (soup as first course). |
| 5 | Language | 9/10 | <8 | Natural phrasing ("Я буду...", "На коли?"). |
| 6 | Pedagogy | 6/10 | <7 | **FAIL**: Severe mismatch between Plan vocabulary and Vocabulary file. Scope creep. |
| 7 | Immersion | 8/10 | <6 | Good use of Ukrainian headers and context. |
| 8 | Activities | 10/10 | <7 | Excellent variety and relevance in `activities/36-at-the-restaurant.yaml`. |
| 9 | Richness | 9/10 | <6 | informative "History Bite" and "Myth Buster". |
| 10 | Beginner Safety | 8/10 | <7 | Slightly dense, but manageable. |
| 11 | LLM Fingerprint | 9/10 | <7 | Low. Feels handcrafted. |
| 12 | Linguistic Accuracy | 9/10 | <9 | Minor scope issue, but grammatically correct. |

**Weighted Overall:** (13.5 + 9 + 10 + 10.8 + 9.9 + 7.2 + 8 + 13 + 8.1 + 10.4 + 9 + 13.5) / 14.0 = **122.4 / 14.0 = 8.74/10** (Adjusted down to **8.4** due to auto-fail in Pedagogy).

## Auto-Fail Checklist Results

- Russianisms: [CLEAN]
- Calques: [CLEAN]
- Grammar scope: [FAIL] Instrumental Plural used.
- Activity errors: [CLEAN]
- Beginner safety: 4/5 (Slightly dense).

## Critical Issues Found

### Issue 1: Vocabulary File Mismatch
- **Location**: `vocabulary/36-at-the-restaurant.yaml`
- **Original**: Contains only `алергія`, `бронювання`, `вегетаріанець`, `вегетаріанка`, `горіх`.
- **Problem**: Missing ALL "Required" words from Plan: `столик`, `замовити`, `офіціант`, `меню`, `страва`, `рахунок`, `перше`, `друге`. The vocabulary file must explicitly define the core lexicon taught in the module.
- **Fix**: Add missing items to the vocabulary YAML.

### Issue 2: Grammar Scope Creep (Instrumental Plural)
- **Location**: Line 100 / Section "Scenario 2" header ("Narrative" header in file content actually says "Dinner with Friends")
- **Original**: "Вечеря з друзями" (Header in Narrative section)
- **Problem**: "з друзями" is Instrumental Plural (друг -> друзі -> друзями). This is A2 grammar. A1 students only know Singular Instrumental (maybe).
- **Fix**: Change to "Вечеря з другом" (Dinner with a friend - Instr. Sing.) or "Вечеря у ресторані".

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| 100 | "Вечеря з друзями" | "Вечеря з другом" | Scope (Instr. Plural) |

## Beginner Safety Audit

"Would I Continue?" Test: 4/5
- Overwhelmed? [No]
- Instructions clear? [Yes]
- Quick wins? [Yes] (Ordering borsch)
- Ukrainian scary? [No]
- Come back tomorrow? [Yes]

Emotional beats:
- Welcome: Yes ("Don't worry if you make mistakes!")
- Curiosity: Yes (Borsch War)
- Quick wins: Dialogue scenarios.

## Strengths
- Excellent "History Bite" about Borsch culture.
- Very practical dialogues that match real life.
- Activities are perfectly aligned with the content.

## Fix Plan to Reach 9/10

### Pedagogy: 6/10 → 9/10

**What to fix:**
1.  **File `vocabulary/36-at-the-restaurant.yaml`**: Add the following items from the Plan:
    *   `столик` (table)
    *   `замовити` (to order)
    *   `офіціант` (waiter)
    *   `меню` (menu)
    *   `страва` (dish)
    *   `рахунок` (bill)
    *   `перше` (first course)
    *   `друге` (main course)
2.  **File `36-at-the-restaurant.md` (Line 100)**: Change "Вечеря з друзями" → "Вечеря з другом" (or "Вечеря удвох" - Dinner for two).

**Expected score after fix:** 9/10

### Projected Overall After Fixes

**9.0/10**

## Verification Summary

- Content lines read: 162
- Activity items checked: 42
- Ukrainian sentences verified: ~30
- IPA transcriptions checked: 7
- Issues found: 2
- Naturalness score recommendation: 10/10

## Verdict

**FAIL**

The module is excellent in content and activities but fails on **Pedagogy** due to a severe mismatch between the Plan's vocabulary requirements and the actual Vocabulary file, plus a minor grammar scope violation (Instrumental Plural). These must be fixed to pass.