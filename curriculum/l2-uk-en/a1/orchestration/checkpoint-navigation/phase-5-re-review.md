# Рецензія: Checkpoint - Navigation

**Level:** A1 | **Module:** 20
**Overall Score:** 9.6/10
**Status:** PASS
**Reviewed:** 2026-02-08

## Plan Verification

```
Plan-Content Alignment: [PASS]
- Sections: [all present]
- Vocabulary: [8/8 from plan used, clean scope]
- Grammar scope: [clean - strict adherence to A1.2 material]
- Objectives: [all covered]
```

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 10/10 | <7 | Excellent tone, "Gamer's Corner" adds personality. |
| 2 | Coherence | 10/10 | <7 | Logical progression from cases to practical application. |
| 3 | Relevance | 10/10 | <7 | Highly practical skills (café, directions). |
| 4 | Educational | 10/10 | <7 | Clear models and immediate practice. |
| 5 | Language | 9/10 | <8 | 2 euphony errors in Activity YAML keys. |
| 6 | Pedagogy | 10/10 | <7 | Strong scaffolding (TTT/PPP mix). |
| 7 | Immersion | 10/10 | <6 | Healthy mix of Ukrainian examples and context. |
| 8 | Activities | 8/10 | <7 | Euphony errors in answer keys need fixing. |
| 9 | Richness | 9/10 | <6 | Good variety, but explanation typo in YAML. |
| 10 | Beginner Safety | 10/10 | <7 | "Would I Continue?" 5/5. Very encouraging. |
| 11 | LLM Fingerprint | 10/10 | <7 | Feels handcrafted and authentic. |
| 12 | Linguistic Accuracy | 9/10 | <9 | Minor euphony and explanation typo. |

**Weighted Overall:** (15 + 10 + 10 + 12 + 9.9 + 12 + 10 + 10.4 + 8.1 + 13 + 10 + 13.5) / 14 = **9.56/10**

## Auto-Fail Checklist Results

- Russianisms: [CLEAN]
- Calques: [CLEAN]
- Grammar scope: [CLEAN]
- Activity errors: [Euphony errors in 2 items]
- Beginner safety: 5/5

## Critical Issues Found

### Issue 1: Euphony Violation (Activity YAML)
- **Location**: Activity YAML Line 207 (Case Mastery - Locative)
- **Original**: `sentence: Ми ___ ресторані.` / `answer: у`
- **Problem**: After a vowel ("Ми"), the preposition should be `в`, not `у`, to avoid hiatus.
- **Fix**: Change answer to `в`.

### Issue 2: Euphony Violation (Activity YAML)
- **Location**: Activity YAML Line 232 (Case Mastery - Locative)
- **Original**: `sentence: Кава ___ чашці.` / `answer: у`
- **Problem**: After a vowel ("Кава"), the preposition should be `в`, not `у`.
- **Fix**: Change answer to `в`.

### Issue 3: Typo in Explanation (Activity YAML)
- **Location**: Activity YAML Line 427 (Real Dialogues Order)
- **Original**: `explanation: 'Correct: Так, можна готівкою або картою.'`
- **Problem**: The option text uses `карткою` (correct for small card), but explanation uses `картою` (map/large card). Inconsistency.
- **Fix**: Change explanation to `...або карткою.'` to match the option.

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| YAML 207 | answer: у | answer: в | Euphony |
| YAML 232 | answer: у | answer: в | Euphony |

## Beginner Safety Audit

"Would I Continue?" Test: 5/5
- Overwhelmed? [Pass]
- Instructions clear? [Pass]
- Quick wins? [Pass]
- Ukrainian scary? [Pass]
- Come back tomorrow? [Pass]

Emotional beats: 5 found
- Welcome: Overview section.
- Curiosity: "Gamer's Corner" (Stalker reference).
- Quick wins: Short, clear drills for each skill.
- Encouragement: "Ready for A1.3?" section.
- Progress: Clear checklist at the end.

## Strengths
- **Cultural Touch**: The S.T.A.L.K.E.R. reference ("Я в Зоні" vs "на землі") is brilliant for engaging learners.
- **Clarity**: The summary table is excellent for revision.
- **Flow**: The transition from grammar rules to "At the Café" integration is very smooth.

## Fix Plan to Reach 10/10

### Activities: 8/10 → 10/10

**What to fix:**
1.  **YAML Line 207**: Change `answer: у` to `answer: в` (Euphony).
2.  **YAML Line 232**: Change `answer: у` to `answer: в` (Euphony).
3.  **YAML Line 427**: Change `картою` to `карткою` in the explanation string to match the option.

**Expected score after fix:** 10/10

### Projected Overall After Fixes

```
(15 + 10 + 10 + 12 + 11 + 12 + 10 + 13 + 9 + 13 + 10 + 15) / 14 = 10.0/10
```

## Verification Summary

- Content lines read: 215
- Activity items checked: 55
- Ukrainian sentences verified: ~40
- IPA transcriptions checked: 3
- Issues found: 3 (all in YAML)
- Naturalness score recommendation: 10/10

## Verdict

**PASS**

The content is excellent and safe for learners. The only issues are minor technical corrections in the Activity YAML file (euphony rules and one typo). These should be fixed, but the module is fundamentally sound and high quality.