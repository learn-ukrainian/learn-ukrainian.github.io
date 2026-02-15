# Рецензія: The Living Verb I

**Level:** A1 | **Module:** 6
**Overall Score:** 8.2/10
**Status:** FAIL
**Reviewed:** 2026-02-15

## Plan Verification

```
Plan-Content Alignment: [FAIL]
- Sections: [PASS] All sections present.
- Vocabulary: [FAIL] Required word 'писати' (to write) is missing from the vocabulary file and explicit teaching (only mentioned in passing in intro).
- Grammar scope: [FAIL] Multiple violations of A1.1 scope (Feminine Accusative case used before Module 11).
- Objectives: [PASS] Core conjugation objectives met.
```

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 9/10 | <7 | Clear metaphors ("Master Key", "Sleeping Verb") make it engaging. |
| 2 | Coherence | 8/10 | <7 | Logical flow, but the omission of 'писати' (a core literacy verb) creates a gap. |
| 3 | Relevance | 6/10 | <7 | **FAIL**: Missing plan-required word 'писати'. Scope creep with untaught grammar cases. |
| 4 | Educational | 7/10 | <7 | Good explanations, but risks confusion by introducing case changes (`музика` → `музику`) without explanation. |
| 5 | Language | 9/10 | <8 | Natural Ukrainian. |
| 6 | Pedagogy | 6/10 | <7 | **FAIL**: Violated research note constraint: "Use 'Inanimate Masculine/Neuter' objects... because they look like Nominative". |
| 7 | Immersion | 10/10 | <6 | 15.1% (Target met). |
| 8 | Activities | 8/10 | <7 | Good variety, but 3 activities rely on out-of-scope grammar (Accusative). |
| 9 | Richness | 9/10 | <6 | Strong cultural context (Apostol 1574, Proverb). |
| 10 | Beginner Safety | 7/10 | <7 | Generally safe, but unexplained word changes (`мова` → `мову`) can induce anxiety. |
| 11 | LLM Fingerprint | 10/10 | <7 | No "AI-isms" detected. |
| 12 | Linguistic Accuracy | 9/10 | <9 | Grammatically correct (just advanced for this level). |

**Weighted Overall:** (9*1.5 + 8*1.0 + 6*1.0 + 7*1.2 + 9*1.1 + 6*1.2 + 10*1.0 + 8*1.3 + 9*0.9 + 7*1.3 + 10*1.0 + 9*1.5) / 14.0 = **8.15/10**

## Auto-Fail Checklist Results

- Russianisms: [CLEAN]
- Calques: [CLEAN]
- Grammar scope: [FAIL] Feminine Accusative case used repeatedly (Module 11 grammar).
- Activity errors: [CLEAN] Logic is sound, only grammar scope is an issue.
- Beginner safety: 4/5 (Risks confusion with unexplained endings).

## Critical Issues Found

### Issue 1: Scope Creep - Feminine Accusative Case
- **Location**: Multiple Lines (Content & Activities)
- **Original**: `музику`, `правду`, `адресу`, `маму`, `мову`, `погоду`, `ціну`.
- **Problem**: This module (A1-06) precedes the Accusative Case module (A1-11). The Research Notes explicitly instructed to use "Inanimate Masculine/Neuter objects" because they don't change form (look like Nominative). Learners will be confused why `музика` becomes `музику`.
- **Fix**: Replace all Feminine Accusative objects with Masculine/Neuter Inanimate objects.

### Issue 2: Missing Required Vocabulary
- **Location**: Plan `vocabulary_hints.required` vs Content
- **Original**: Missing `писати` (to write).
- **Problem**: The plan requires `писати`. It is mentioned in the Intro ("Reading, writing...") but never conjugated, never listed in "New Words", and missing from the Vocabulary file. It is a core verb for this level.
- **Fix**: Add `писати` to the Presentation/Model section and the Vocabulary file.

### Issue 3: Vocabulary File Inconsistency
- **Location**: `vocabulary/the-living-verb-i.yaml`
- **Original**: `[ˈrɑdʲijo]` vs Content `[ˈrɑdijo]`
- **Problem**: Inconsistent IPA transcription for 'радіо'.
- **Fix**: Standardize to `[ˈrɑdʲijo]` (more precise) or `[ˈrɑdijo]` in both places.

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| 152 | слухає музику | слухає джаз / рок | Scope (Accusative) |
| 153 | знаєте це | знаєте все / текст | Scope (Accusative) |
| 168 | знаємо правду | знаємо факт / результат | Scope (Accusative) |
| 188 | знаємо адресу | знаємо код / телефон | Scope (Accusative) |
| 196 | питаю про текст | питаю про текст | Clean (Masc Inanim) |
| 197 | питаєш про це | питаєш про це | Clean (Neut) |
| 205 | Чекаєш маму? | Чекаєш автобус? | Scope (Accusative) |
| Act | вивчають мову | вивчають алфавіт | Scope (Accusative) |
| Act | питаю про ціну | питаю про номер | Scope (Accusative) |

## Beginner Safety Audit

"Would I Continue?" Test: 4/5
- Overwhelmed? [Pass]
- Instructions clear? [Pass]
- Quick wins? [Pass]
- Ukrainian scary? [Fail] Unexplained changes like `мова` -> `мову` make the language seem unpredictable/scary at this stage.
- Come back tomorrow? [Pass]

Emotional beats: 4 found
- Welcome: "Вітаю! You already know..."
- Curiosity: "The Master Key" metaphor.
- Quick wins: Conjugation table is clear.
- Encouragement: "Це ваш Майстер-ключ."
- Progress: "You have moved from naming objects to describing actions."

## Strengths
- Excellent use of metaphors ("Sleeping Verb", "Master Key") to demystify grammar.
- Strong cultural integration regarding literacy and the "Apostol".
- Very natural, authentic examples (e.g., "Чекаємо" vs "Ми чекаємо").

## Fix Plan to Reach 9/10

### Relevance: 6/10 → 10/10

**What to fix:**
1.  **Section "Нові слова" (Line 144):** Add `писати` to the list.
    *   Change: Add bullet: `* **писати** [pɪˈtɑtɪ] (to write) → **Я пишу** [jɑ pɪˈʃu]...` WAIT. **CRITICAL STOP.**
    *   **Self-Correction**: `писати` is a Type 1 verb (-ати), BUT it has a consonant mutation (`с` -> `ш`) in the present tense (`писати` -> `пишу`, `пишеш`).
    *   **Investigation**: The module teaches the standard `-аю`, `-аєш` pattern ("The Master Key"). `писати` breaks this simple pattern (it's First Conjugation but with mutation).
    *   **Decision**: This explains why it might have been omitted despite being in the plan. Including it *confuses* the "simple pattern" narrative.
    *   **Revised Fix**: Check if `писати` is strictly required as a *regular* verb here. The plan lists it under "First Conjugation pattern (-ати -> -аю)". This is technically incorrect for `писати`. `писати` is First Conjugation (`-е` endings) but not the `-аю` sub-type.
    *   **Strategy**: If I introduce `писати` (`пишу`, `пишеш`), I break the "Master Key" promise ("Stem stays strong... It does not change").
    *   **Recommendation**: **REMOVE** `писати` from the required list in the Plan (update the Plan) OR add a "Note on irregularities" (risky for A1.1). Given "Beginner Safety", it is better to **Replace** `писати` in the Plan with a regular regular verb like `мати` (irregular but common) or just stick to regular ones. actually `мати` is also special. Better regular verb: `співати` (to sing).
    *   **Alternative**: The user Plan is "Immutable" source of truth? "Plan (source of truth for scope)". If the plan is wrong (asking for `писати` in a regular `-аю` module), I should flag it.
    *   **Refined Fix**: I cannot edit the plan. I must flag this as a **Plan Error**. `писати` should NOT be here if the goal is the `-аю` pattern. I will NOT add it to the content, but I will critique the Plan Alignment.
    *   **Correction to Review**: I will downgrade Plan Alignment but NOT demand `писати` be added to content, as it would break Pedagogy.

**REVISED SCORES & FIX PLAN:**

### Pedagogy: 6/10 → 9/10

**What to fix:**
1.  **Global Replace:** Eliminate Feminine Accusative objects.
    *   `музику` → `джаз` (jazz) or `радіо` (radio).
    *   `правду` → `все` (everything) or `факт` (fact).
    *   `адресу` → `телефон` (phone number) or `код` (code).
    *   `маму` → `автобус` (bus) or `поїзд` (train).
    *   `мову` → `текст` (text) or `діалог` (dialogue).
    *   `погоду` → `прогноз` (forecast).
    *   `ціну` → `номер` (number).
    *   **Why**: Ensures all objects look like Nominative (A1.1 friendly), strictly following Research Notes.

### Activity Check: 8/10 → 10/10

**What to fix:**
1.  **Activity `fill-in` Item 2**: `Ти _____ це місто?` (`місто` is neuter, ok).
2.  **Activity `quiz` Item 6**: `Вони вивчають мову` → `Вони вивчають алфавіт` (alphabet) or `Вони вивчають текст` (text).
3.  **Activity `match-up`**: `Я вивчаю мову` → `Я вивчаю текст`.
4.  **Activity `match-up`**: `Я знаю адресу` → `Я знаю телефон`.
5.  **Activity `match-up`**: `Я питаю про ціну` → `Я питаю про номер`.

### Projected Overall After Fixes

Relevance rises to 9 (Plan conflict resolved by acknowledging mutation issue), Pedagogy to 9, Beginner Safety to 9.
Projected Score: ~9.2/10.

## Verification Summary

- Content lines read: ~230
- Activity items checked: 30+
- Ukrainian sentences verified: ~35
- IPA transcriptions checked: 20+
- Issues found: 2 Major (Scope Creep, Plan Conflict)
- Naturalness score recommendation: 9/10

## Verdict

**FAIL**

The module is well-written and engaging but fails on two critical pedagogical constraints:
1.  **Scope Creep**: It uses Feminine Accusative endings (`-у`) extensively, which have not been taught yet and violate the explicit Research Note instruction to use only Inanimate Masculine/Neuter objects (which look like Nominative).
2.  **Plan Conflict**: The Plan requires `писати`, but `писати` has a consonant mutation (`пишу`, `пишеш`) which contradicts the "Master Key" rule taught in this module ("Stem does not change"). The content correctly omits it to preserve the rule, but this causes a Plan Alignment failure.

**Action**: Remove Accusative forms and update the Plan to replace `писати` with a regular verb like `співати` (to sing) or `гуляти` (to walk).
