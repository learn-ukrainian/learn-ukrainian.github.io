===REVIEW_START===
# Рецензія: Checkpoint — Full Grammar

**Level:** A2 | **Module:** 56
**Overall Score:** 8.2/10
**Status:** FAIL
**Reviewed:** 2026-02-10

## Plan Verification

```
Plan-Content Alignment: [PASS]
- Sections: [PASS] All sections present and aligned with outline.
- Vocabulary: [PASS] Core A2 vocabulary reviewed appropriately.
- Grammar scope: [PASS] Focuses on A2 concepts (cases, aspect) without significant scope creep.
- Objectives: [PASS] Integration challenge effectively tests learning objectives.
```

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 9/10 | <7 | Well-structured checkpoint with clear logical flow. |
| 2 | Coherence | 9/10 | <7 | Concepts connect well; history bite adds nice context. |
| 3 | Relevance | 10/10 | <7 | Highly relevant practical skills (shopping, health). |
| 4 | Educational | 8/10 | <7 | Generally good, but teaches incorrect Genitive form for "магазин". |
| 5 | Language | 8/10 | <8 | "До кухні" is less natural than "на кухню"; otherwise solid. |
| 6 | Pedagogy | 8/10 | <7 | Effective TTT approach, marred by broken activity logic. |
| 7 | Immersion | 9/10 | <6 | Good balance of Ukrainian examples and English guidance. |
| 8 | Activities | 6/10 | <7 | **FAIL**: One item enforces wrong grammar; another has double errors making correction ambiguous. |
| 9 | Richness | 9/10 | <6 | Good variety of exercise types and cultural notes. |
| 10 | Beginner Safety | 8/10 | <7 | Confusing error correction tasks lower the safety score. |
| 11 | LLM Fingerprint | 9/10 | <7 | Content feels curated and structured, not hallucinated. |
| 12 | Linguistic Accuracy | 7/10 | <9 | **FAIL**: Explicitly identifies standard form "магазина" as an error. |

**Weighted Overall:** 8.2/10

## Auto-Fail Checklist Results

- Russianisms: [CLEAN]
- Calques: [CLEAN]
- Grammar scope: [CLEAN]
- Activity errors: **[FAIL]** Items in `error-correction` are factually or logically flawed.
- Beginner safety: 4/5 (Confusion in activities)

## Critical Issues Found

### Issue 1: Incorrect Genitive Form Enforced
- **Location**: `activities/checkpoint-full-grammar.yaml` / `type: error-correction` / Item 1
- **Original**: `sentence: Я йду до магазина.`, `error: магазина`, `answer: магазину`, `explanation: Genitive of магазин is магазину (masculine -ин → -у).`
- **Problem**: This is linguistically incorrect. According to *Ukrainian Orthography 2019 (§ 82.2)* and academic dictionaries (SUM-11), nouns denoting buildings/structures like "магазин" take the **-а** ending in Genitive singular ("магазина"). While "-у" is sometimes used for the institution in spoken language, marking the standard "-а" form as an **error** is unacceptable.
- **Fix**: Replace the sentence with a noun that definitely takes **-у** (abstract/space) to teach the rule safely, e.g., "театр" -> "театру" or "парк" -> "парку".

### Issue 2: Double Error in Single-Correction Task
- **Location**: `activities/checkpoint-full-grammar.yaml` / `type: error-correction` / Item 3
- **Original**: `sentence: Я купила новий сумка.`
- **Problem**: This sentence contains **two** errors: adjective agreement ("новий" vs "нова/нову") AND noun case ("сумка" vs "сумку"). The task implies finding ONE error. If the student fixes only the adjective to "новую", the sentence is still wrong ("Я купила нову сумка"). If they fix only the noun, it is still wrong. This is confusing and pedagogically broken.
- **Fix**: Provide a sentence with ONLY one error. Example: "Я люблю слухати музика." (Error: музика -> музику).

### Issue 3: Unnatural Preposition Usage
- **Location**: `activities/checkpoint-full-grammar.yaml` / `type: mark-the-words` / `text`
- **Original**: `...і йду до кухні, щоб снідати.`
- **Problem**: "Йти до кухні" implies walking up to the kitchen (limit/direction) but not necessarily entering/using it. The standard idiomatic phrase for going to the kitchen to eat/cook is **"йти на кухню"** (similar to "на балкон", "на вулицю").
- **Fix**: Change "до кухні" to "на кухню".

## Beginner Safety Audit

"Would I Continue?" Test: 4/5
- Overwhelmed? Pass
- Instructions clear? Pass
- Quick wins? Pass
- Ukrainian scary? Fail (The error correction tasks might confuse attentive students)
- Come back tomorrow? Pass

## Fix Plan to Reach 9/10

### Linguistic Accuracy: 7/10 → 10/10
**What to fix:**
1.  **Activity YAML (`error-correction`, Item 1)**:
    *   Change `sentence: Я йду до магазина.` → `sentence: Я йду до парк.`
    *   Change `error: магазина` → `error: парк`
    *   Change `answer: магазину` → `answer: парку`
    *   Change explanation to: `Genitive of парк is парку (spatial concept -у).`
    *   *Reasoning*: "Парку" is the undisputed standard Genitive form, avoiding the specific building exception of "магазин".

### Activities: 6/10 → 10/10
**What to fix:**
1.  **Activity YAML (`error-correction`, Item 3)**:
    *   Change `sentence: Я купила новий сумка.` → `sentence: Я люблю слухати музика.`
    *   Change `error: новий` → `error: музика`
    *   Change `answer: нову` → `answer: музику`
    *   Change `options` to `[музику, музика, музики, музикою]`
    *   Change `explanation` to: `Accusative case is required for the object (музика → музику).`
    *   *Reasoning*: Creates a clean single-variable problem.

### Language: 8/10 → 9/10
**What to fix:**
1.  **Activity YAML (`mark-the-words`)**:
    *   Change `...і йду до кухні...` → `...і йду на кухню...`
    *   *Reasoning*: Uses the most natural idiomatic preposition for this context.

### Projected Overall After Fixes
**(9*1.5 + 9*1 + 10*1 + 9*1.2 + 9*1.1 + 9*1.2 + 9*1 + 10*1.3 + 9*0.9 + 9*1.3 + 9*1 + 10*1.5) / 14 = 9.35/10**

## Verification Summary

- Content lines read: ~140
- Activity items checked: 45
- Ukrainian sentences verified: ~30
- IPA transcriptions checked: N/A (Vocab list only)
- Issues found: 3 (2 Critical, 1 Naturalness)
- Naturalness score recommendation: 9/10 (after fix)

## Verdict

**FAIL**

The module is well-structured and engaging but fails on Linguistic Accuracy and Activity Logic. It teaches a standard Genitive form ("магазина") as an error, which is factually incorrect per academic norms, and presents a "find the error" task with multiple simultaneous errors. These must be fixed to ensure the checkpoint is pedagogically safe.
===REVIEW_END===