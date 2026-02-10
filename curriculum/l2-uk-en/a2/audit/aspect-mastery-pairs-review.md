# Рецензія: Aspect Mastery — Pairs

**Level:** A2 | **Module:** 16
**Overall Score:** 8.6/10
**Status:** FAIL
**Reviewed:** 2026-02-09

## Plan Verification

```
Plan-Content Alignment: [PASS]
- Sections: [all present]
- Vocabulary: [26/30 from plan used, 4 missing from text list: платити, губити, малювати, будувати]
- Grammar scope: [clean]
- Objectives: [all covered]
```

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 9/10 | <7 | Strong narrative and clear "Mental Switches". |
| 2 | Coherence | 9/10 | <7 | Logical flow from theory to practice. |
| 3 | Relevance | 9/10 | <7 | High-frequency "Core 30" focus. |
| 4 | Educational | 9/10 | <7 | Effective analogies (Dot vs Line). |
| 5 | Language | 9/10 | <8 | Natural Ukrainian, good explanations. |
| 6 | Pedagogy | 9/10 | <7 | PPP structure followed well. |
| 7 | Immersion | 8/10 | <6 | Good mix, could use slightly more Ukrainian in drill instructions. |
| 8 | Activities | 6/10 | <7 | Duplicate items, miscategorized sorting, grammar ambiguity in key. |
| 9 | Richness | 9/10 | <6 | Content is 153% of target, very detailed. |
| 10 | Beginner Safety | 9/10 | <7 | Encouraging tone, clear steps. |
| 11 | LLM Fingerprint | 9/10 | <7 | "Secret sauce" cliché in English summary, otherwise good. |
| 12 | Linguistic Accuracy | 8/10 | <9 | Minor case usage issue (`листа` vs `лист`) in activities. |

**Weighted Overall:** 8.64/10

## Auto-Fail Checklist Results

- Russianisms: [CLEAN]
- Calques: [CLEAN]
- Grammar scope: [CLEAN]
- Activity errors: [FAIL] (Duplicates, miscategorization)
- Beginner safety: 5/5

## Critical Issues Found

### Issue 1: Duplicate Activity Item
- **Location**: Line 8 / `activities/16-aspect-mastery-pairs.yaml`
- **Original**:
  ```yaml
  - left: читати
    right: прочитати
  ...
  - left: читати
    right: прочитати
  ```
- **Problem**: The pair `читати/прочитати` appears twice in the "Tier 1 Pairs" match-up activity.
- **Fix**: Remove the second instance (Lines 22-23).

### Issue 2: Incorrect Grouping in Sort Activity
- **Location**: Line 258 / `activities/16-aspect-mastery-pairs.yaml` (approx)
- **Original**: `класти → покласти` inside group "Suppletive / Variable"
- **Problem**: `класти` -> `покласти` is formed by adding the prefix `по-`. It belongs in the "Prefix" group, not "Suppletive / Variable".
- **Fix**: Move `класти → покласти` to the "Prefix" group.

### Issue 3: Confusing Distractors in Fill-in
- **Location**: Line 131 / `activities/16-aspect-mastery-pairs.yaml`
- **Original**: `options: [говорити, сказати, казати, переказати]`
- **Problem**: `казати` is a valid imperfective form often used interchangeably with `говорити` (or as the imperfective of `сказати` in some views). Using it as a distractor for `сказати` -> `говорити` is confusing.
- **Fix**: Replace `казати` with a clearly wrong option like `підказати` (perfective) or `розповідь` (noun).

### Issue 4: Case Usage in Unjumble
- **Location**: Line 186 / `activities/16-aspect-mastery-pairs.yaml`
- **Original**: `вона, написала, дуже, великого, листа, до, своєї, мами`
- **Problem**: `Лист` is an inanimate masculine noun. In standard A2 grammar, Accusative = Nominative (`великий лист`). `великого листа` treats it as animate (Genitive-Accusative), which is common in literature/spoken language but confuses the A2 rule "Inanimate Masc Acc = Nom".
- **Fix**: Change `великого` to `великий` and `листа` to `лист`.

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| 186 (Yaml) | написала ... великого листа | написала ... великий лист | Grammar (Level Appropriateness) |

## Beginner Safety Audit

"Would I Continue?" Test: 5/5
- Overwhelmed? Pass
- Instructions clear? Pass
- Quick wins? Pass
- Ukrainian scary? Pass
- Come back tomorrow? Pass

Emotional beats: 4 found
- Welcome: "Ласкаво просимо..."
- Curiosity: "Secret of Automaticity"
- Quick wins: "Rapid Fire Recall"
- Encouragement: "успіхів у вашому прагненні"

## Strengths
- Excellent conceptual explanations ("Dot vs Line", "Photo vs Movie").
- High-quality narrative in the "Context Story".
- Strong focus on the most useful high-frequency verbs.

## Fix Plan to Reach 9/10

### Activities: 6/10 → 9/10

**What to fix:**
1. `activities/16-aspect-mastery-pairs.yaml`: Remove lines 22-23 (duplicate `читати/прочитати`).
2. `activities/16-aspect-mastery-pairs.yaml`: In "Transform to Imperfective" (Line 131), change option `казати` to `підказати`.
3. `activities/16-aspect-mastery-pairs.yaml`: In "Aspect Sentences" (Line 186), change `великого` to `великий` and `листа` to `лист`. Update `answer` to match: `Вона написала дуже великий лист до своєї мами`.
4. `activities/16-aspect-mastery-pairs.yaml`: In "Formation Pattern", move `- класти → покласти` from `Suppletive / Variable` group to `Prefix` group.

**Expected score after fix:** 9/10

### Linguistic Accuracy: 8/10 → 9/10

**What to fix:**
1. The fix for `великого листа` -> `великий лист` addresses the main accuracy/level-appropriateness concern.

**Expected score after fix:** 9/10

### Projected Overall After Fixes

```
(9*1.5 + 9*1.0 + 9*1.0 + 9*1.2 + 9*1.1 + 9*1.2 + 8*1.0 + 9*1.3 + 9*0.9 + 9*1.3 + 9*1.0 + 9*1.5) / 14.0 = 8.95 -> 9.0
```

## Verification Summary

- Content lines read: 154
- Activity items checked: 10 types, ~50 items
- Ukrainian sentences verified: ~40
- IPA transcriptions checked: N/A (Vocab file checked separately)
- Issues found: 4
- Naturalness score recommendation: 9/10

## Verdict

**FAIL**

The module content is excellent, but the activities file contains critical errors (duplicates, miscategorization) and level-inappropriate grammar (`великого листа`) that must be fixed before release.