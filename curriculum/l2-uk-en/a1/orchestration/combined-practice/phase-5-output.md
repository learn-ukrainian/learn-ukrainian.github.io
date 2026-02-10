===REVIEW_START===
# Рецензія: Combined Practice

**Level:** A1 | **Module:** 43
**Overall Score:** 7.5/10
**Status:** FAIL
**Reviewed:** 2026-02-09

## Plan Verification

```
Plan-Content Alignment: [FAIL]
- Sections: [FAIL] "Warm-up" section appears at the end of the module (post-Practice) instead of the beginning. It contains the Narrative ("Warm-up 2" in plan). The initial "Warm-up" from the plan is missing.
- Vocabulary: [FAIL] Vocabulary file is empty (contains only 1 word: "зв'язний"). Missing ALL required words from plan: спочатку, потім, нарешті, тому що, якщо, але, також, разом.
- Grammar scope: [FAIL] Activities require productive Dative Case (мамі, другу), which is explicitly marked as "OUT Scope" in the research notes/plan.
- Objectives: [PASS]
```

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 8/10 | <7 | Good practical scenarios, but the structure (Warm-up at the end) is confusing. |
| 2 | Coherence | 6/10 | <7 | Section labeled "Warm-up" is the last section before Summary. It should be "Narrative" or "Reading". |
| 3 | Relevance | 10/10 | <7 | Highly relevant survival scenarios. |
| 4 | Educational | 8/10 | <7 | Good content, but grammar scope violations in activities. |
| 5 | Language | 9/10 | <8 | Natural Ukrainian. "Збігаю" (run quickly) might be slightly colloquial for A1 but acceptable. |
| 6 | Pedagogy | 6/10 | <7 | Activities test Dative case production (changing noun endings), which is forbidden by the scope constraints for this level. |
| 7 | Immersion | 9/10 | <6 | Good usage of Ukrainian. |
| 8 | Activities | 6/10 | <7 | Violates grammar scope (Dative). "Fill-in" activity requires declining nouns into Dative. |
| 9 | Richness | 9/10 | <6 | Good detail in scenarios. |
| 10 | Beginner Safety | 7/10 | <7 | Dative case exercises will frustrate students who haven't learned the declension rules yet. |
| 11 | LLM Fingerprint | 8/10 | <7 | Minor meta-talk: "Use these exercises. This is good practice." |
| 12 | Linguistic Accuracy | 10/10 | <9 | No obvious errors in the Ukrainian text itself. |

**Weighted Overall:** (8*1.5 + 6*1.0 + 10*1.0 + 8*1.2 + 9*1.1 + 6*1.2 + 9*1.0 + 6*1.3 + 9*0.9 + 7*1.3 + 8*1.0 + 10*1.5) / 14.0 = **105.2 / 14.0 = 7.51/10**

## Auto-Fail Checklist Results

- Russianisms: [CLEAN]
- Calques: [CLEAN]
- Grammar scope: **[FAIL]** Dative case production in Activities.
- Activity errors: [CLEAN] (Mechanically correct, but scope violation).
- Beginner safety: 4/5 (Scope violation risks frustration).

## Critical Issues Found

### Issue 1: Structural Inconsistency (Coherence)
- **Location**: Final Section
- **Original**: `## Warm-up` (containing the Narrative)
- **Problem**: This section is placed at the very end of the module, after "Practice". A "Warm-up" belongs at the beginning. This corresponds to "Warm-up 2" in the plan but is mislabeled and oddly placed.
- **Fix**: Rename to `## Narrative Practice` or `## Reading: A Busy Saturday`. Ensure the module flow is logical.

### Issue 2: Grammar Scope Violation (Pedagogy/Activities)
- **Location**: `activities.yaml` (fill-in: Task List)
- **Original**: `sentence: «Я хочу говорити з мамою. Треба подзвонити _____.» answer: мамі`
- **Problem**: The plan/research notes explicitly state "OUT Scope (Avoid): Dative Case". This item requires the student to decline "мама" to "мамі" (Dative). This is productive grammar application of an untaught case.
- **Fix**: Replace with an Accusative or Locative task. E.g., "Я хочу бачити маму. Треба відвідати ____." (маму - Accusative) or use a different verb.

### Issue 3: Missing Vocabulary (Plan Alignment)
- **Location**: `vocabulary.yaml`
- **Original**: Only contains `зв'язний`.
- **Problem**: The plan lists required words: `спочатку`, `потім`, `нарешті`, `тому що`, `якщо`, `але`, `також`, `разом`. None are in the file.
- **Fix**: Populate the vocabulary file with the required items.

### Issue 4: Meta-Commentary (LLM Fingerprint)
- **Location**: End of Narrative section
- **Original**: "Використовуйте ці вправи. Це гарна практика. (Use these exercises. This is good practice.)"
- **Problem**: Unnecessary AI meta-talk.
- **Fix**: Delete these sentences.

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| Text | "Я зараз швидко збігаю" | "Я зараз швидко сходжу" | Stylistic (Colloquial "збігаю" implies running/popping out, "схожу" is more standard A1) |

## Beginner Safety Audit

"Would I Continue?" Test: 4/5
- Overwhelmed? No
- Instructions clear? Yes
- Quick wins? Yes
- Ukrainian scary? No
- Come back tomorrow? Yes, but might be confused by "Warm-up" at the end and Dative exercises.

## Fix Plan to Reach 9/10

### Coherence: 6/10 → 9/10
**What to fix:**
1. **Section "Warm-up"**: Rename to `## Narrative Practice` or `## Reading`.
2. **Move Section**: Ensure the Overview acts as the actual introduction. The current structure is okay if the final section is just renamed.

### Pedagogy & Activities: 6/10 → 9/10
**What to fix:**
1. **Activity "Task List"**: Replace Dative items.
   - Change `«Треба подзвонити _____.» (мамі)` → `«Треба провідати _____.» (маму)` (Accusative) OR `«Я чекаю _____.» (таксі)` (Accusative).
   - Change `«Я дзвоню _____.» (другу)` in "My Plans" → `«Я чекаю _____.» (друга)` (Genitive/Accusative - *Wait, Genitive is safer for "wait for person" in UA, but Accusative is often used by learners. Better: "Я бачу ____" (друга - Accusative).*
   - **Goal**: Ensure all fill-in answers use Nominative, Accusative, or Locative cases (or Genitive if strictly for quantity/possession).

### Plan Alignment (Vocabulary): Fail → Pass
**What to fix:**
1. **vocabulary.yaml**: Add the missing words from the Plan's `vocabulary_hints.required` list: `спочатку`, `потім`, `нарешті`, `тому що`, `якщо`, `але`, `також`, `разом`.

### Projected Overall After Fixes
With these fixes, Coherence -> 9, Pedagogy -> 9, Activities -> 9.
Projected Score: **9.2/10**

## Verification Summary
- Content lines read: 140
- Activity items checked: 45
- Ukrainian sentences verified: ~30
- Issues found: 4 (Structure, Vocabulary missing, Grammar Scope, Meta-talk)

## Verdict

**FAIL**

Blocking issues:
1.  **Grammar Scope**: Activities require Dative case production, which is explicitly forbidden in the plan/research notes.
2.  **Structure**: "Warm-up" section is misplaced at the end of the module.
3.  **Vocabulary**: The vocabulary file is effectively empty, missing all required terms.

===REVIEW_END===
