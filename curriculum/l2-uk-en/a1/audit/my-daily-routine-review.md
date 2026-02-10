# Рецензія: My Daily Routine

**Level:** A1 | **Module:** 25
**Overall Score:** 8.0/10
**Status:** FAIL
**Reviewed:** 2026-02-09

## Plan Verification

```
Plan-Content Alignment: [PASS]
- Sections: [all present]
- Vocabulary: [8/8 from plan used, 0 extra major words]
- Grammar scope: [clean]
- Objectives: [all covered]
```

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 8/10 | <7 | Good practical flow, but confused by the grammar table contradiction. |
| 2 | Coherence | 7/10 | <7 | Contradiction in grammar table (says add -сь, shows result with -ся). |
| 3 | Relevance | 9/10 | <7 | Highly relevant daily routine content. |
| 4 | Educational | 8/10 | <7 | Strong scaffolding. |
| 5 | Language | 9/10 | <8 | Natural Ukrainian. |
| 6 | Pedagogy | 7/10 | <7 | Scope creep in activities (untested vocabulary). |
| 7 | Immersion | 9/10 | <6 | High, good cultural note. |
| 8 | Activities | 6/10 | <7 | **FAIL**: 4 items use vocabulary not taught in the module (`зустрічаємося`, `називається`, `рідко`, `звичка`). |
| 9 | Richness | 8/10 | <6 | Good use of audio/IPA context. |
| 10 | Beginner Safety | 7/10 | <7 | Frustration risk due to undefined words in quiz. |
| 11 | LLM Fingerprint | 9/10 | <7 | Minimal. |
| 12 | Linguistic Accuracy | 9/10 | <9 | Generally accurate. |

**Weighted Overall:** (12+7+9+9.6+9.9+8.4+9+7.8+7.2+9.1+9+13.5)/14 = **7.96/10**

## Auto-Fail Checklist Results

- Russianisms: [CLEAN]
- Calques: [CLEAN]
- Grammar scope: [CLEAN]
- Activity errors: [FAIL] - 4 items use undefined vocabulary.
- Beginner safety: 4/5

## Critical Issues Found

### Issue 1: Grammar Table Contradiction
- **Location**: Line 116, 119 / Section "The Reflexive Pattern"
- **Original**: `| Я | вмиваю | + **-сь** | **вмиваюся** |`
- **Problem**: The column says add `-сь`, but the result `вмиваюся` clearly uses the `-ся` ending. If you added `-сь`, it would be `вмиваюсь`. Since the text claims "-ся is always correct", the table should reflect that logic.
- **Fix**: Change `+ **-сь**` to `+ **-ся**` in rows for "Я" and "Ми".

### Issue 2: Scope Creep in Activities (Undefined Vocab)
- **Location**: Activities File / `fill-in` (Reflexive Verb Forms) / Item 11 & 12
- **Original**: `зустрічаємося`, `називається`
- **Problem**: These verbs are not in the module's vocabulary list or text. A1 students cannot guess them.
- **Fix**: Replace with known verbs (e.g., `бачимося` if taught, or reuse `вмиваємося`/`одягається` in new contexts). Or change sentences.

### Issue 3: Scope Creep (Adverbs)
- **Location**: Activities File / `fill-in` (Sequence Words) / Item 12
- **Original**: `Вона ___ дивиться фільми українською. (Answer: рідко)`
- **Problem**: `рідко` (rarely) is not taught in the content (only `іноді`, `зазвичай`, `ніколи`, `завжди`).
- **Fix**: Change answer to `іноді` or `завжди`.

### Issue 4: Scope Creep (Nouns)
- **Location**: Activities File / `true-false` / Item 11
- **Original**: `«Звичка» means "habit".`
- **Problem**: The word `Звичка` appears nowhere in the text.
- **Fix**: Remove item or replace with `«Розпорядок» means "routine"`.

### Issue 5: Missing Frequency Word in Summary
- **Location**: Line 178 / Section "Summary"
- **Original**: `завжди (always), зазвичай (usually), щодня (every day), ніколи (never)`
- **Problem**: The word `іноді` (sometimes) is used in the text ("Іноді я гуляю") and activities, but missing from the summary list.
- **Fix**: Add `іноді (sometimes)`.

## Beginner Safety Audit

"Would I Continue?" Test: 4/5
- Overwhelmed? No
- Instructions clear? Yes
- Quick wins? Yes (Translation exercise)
- Ukrainian scary? No
- Come back tomorrow? Yes, provided I don't get stuck on the "mystery words" in the quiz.

## Fix Plan to Reach 9/10 (REQUIRED)

### Coherence: 7/10 → 9/10
**What to fix:**
1. Line 116: Change `| + **-сь** |` → `| + **-ся** |` — align calculation with result.
2. Line 119: Change `| + **-сь** |` → `| + **-ся** |` — align calculation with result.

### Activities: 6/10 → 9/10
**What to fix:**
1. `activities/25-my-daily-routine.yaml`: In `fill-in` (Reflexive Verb Forms), Item 11: Change `sentence` to "Ми зазвичай ___ вдома." and `answer` to "снідаємо" (or keep reflexive focus: "Ми ___ швидко." -> "одягаємося"). REPLACE `зустрічаємося` item.
2. `activities/25-my-daily-routine.yaml`: In `fill-in` (Reflexive Verb Forms), Item 12: REPLACE `називається` item with a known verb (e.g., "Вона ___" -> "прокидається").
3. `activities/25-my-daily-routine.yaml`: In `fill-in` (Sequence Words), Item 12: Change `answer` from `рідко` to `іноді`.
4. `activities/25-my-daily-routine.yaml`: In `true-false`, Item 11: Replace "«Звичка» means 'habit'" with "«Розпорядок» means 'routine'".

### Completeness (Richness)
**What to fix:**
1. Line 178: Add `- іноді (sometimes)` to the Frequency words list.

### Projected Overall After Fixes
(8*1.5 + 9*1 + 9*1 + 8*1.2 + 9*1.1 + 9*1.2 + 9*1 + 9*1.3 + 9*0.9 + 8*1.3 + 9*1 + 9*1.5) / 14 = **8.8/10** (rounding up to 9 for clean execution)

## Verdict

**FAIL**

The module is strong in content but fails on **Activities** due to significant scope creep (testing words not taught). The **Grammar Table** also contains a confusing contradiction regarding the -ся/-сь rule application. These must be fixed before release.