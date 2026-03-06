# Batch Review Summary: A1 M11-M14

**Date:** 2026-03-06
**Modules reviewed:** 4 | **Skipped:** 0

## Results Table

| # | Slug | Prompt Health | Content Grade | Critical | High | Key Issues |
|---|------|--------------|---------------|----------|------|------------|
| 11 | describing-things-adjectives | NEEDS_WORK | B | 0 | 1 | 1 surviving imperative, Latin transliteration |
| 12 | colors-and-clothing | BROKEN | C | 1 | 3 | Russianisms (красивий/красива), 6 imperatives + 10 conjugated verbs, choppy prose, 6 wasted validation rounds |
| 13 | plurals-and-alternation | NEEDS_WORK | C | 2 | 3 | ніж/ножі mislabeled (і-to-о not і-to-е), unjumble schema wrong, forbidden verb conjugation, missing vocab |
| 14 | checkpoint-first-contact | NEEDS_WORK | B | 0 | 2 | Stale plan (verb objectives forbidden by sequence constraints), true-false activity И/Н confusion |

**Template fixes proposed:** 6
**Modules needing rebuild:** 2 (M12, M13)

---

## Cross-Module Pattern Analysis

### Pattern 1: Verb-Free Ukrainian Constraint Violation (ALL 4 modules)

**Occurrences:** 4/4 modules | **Priority:** HIGH

The pre-M15 constraint forbids conjugated verbs and imperatives in Ukrainian examples, but the template demands 25-40% Ukrainian immersion. Without a verb-free pattern bank, Gemini inevitably introduces verbs. This caused:
- M11: 5 validation rounds, 1 surviving imperative
- M12: 6 validation rounds exhausted, 6+ imperatives + 10+ verbs still present
- M13: Conjugated verbs (грають, сидять) in examples
- M14: Plan itself contradicts constraint (verb conjugation objective)

**Root cause:** Template gap — no positive examples of verb-free Ukrainian patterns.

**Auto-fix target:** `scripts/pipeline_lib.py` (PEDAGOGICAL_CONSTRAINTS) + content prompt templates

### Pattern 2: Duplicate/Identical Fix Prompts (M12 confirmed, likely others)

**Occurrences:** 1 confirmed (M12: fix3 = fix5 = fix6) | **Priority:** MEDIUM

The pipeline sends identical fix prompts on repeated validation failures. This wastes API budget with zero chance of improvement.

**Root cause:** Pipeline gap — no deduplication check before sending fix prompts.

**Auto-fix target:** `scripts/pipeline_v5.py` or `scripts/pipeline_lib.py` — add fix prompt hash comparison

### Pattern 3: Plan/Constraint Conflicts (M12, M14)

**Occurrences:** 2 | **Priority:** HIGH

Plans written before sequence constraints were finalized contain objectives that violate those constraints:
- M12: Plan demands "Мені подобається" (dative) but constraints forbid dative pre-M15
- M14: Plan lists "Conjugate First Conjugation verbs" but M14 is pre-M15

**Root cause:** Stale plans — no pre-build validation of plan objectives against sequence constraints.

**Auto-fix target:** `scripts/build_module.py` — add plan-constraint validation gate before content generation

### Pattern 4: Missing Activity Schema Examples (M13)

**Occurrences:** 1 (unjumble type) | **Priority:** MEDIUM

The activities prompt (phase-C-prompt.md) lacks schema examples for the `unjumble` activity type. Gemini generated wrong fields (`sentence` instead of `words` + `answer`).

**Auto-fix target:** `claude_extensions/phases/gemini/` activity prompt templates — add unjumble schema example

### Pattern 5: Russianisms Passing Pipeline (M12)

**Occurrences:** 1 module, 2 instances | **Priority:** HIGH

красивий/красива passed all validation including VESUM screening. These are technically valid Ukrainian words (VESUM contains them) but are Russianisms in the context of "beautiful" — the Ukrainian equivalent is гарний/гарна.

**Root cause:** VESUM verifies word existence, not semantic appropriateness. No Russicism filter in the pipeline.

**Auto-fix target:** `scripts/rag_batch_verify.py` — add R2U Russicism cross-check for flagged words

---

## Suggested Template Fixes (by leverage)

### Fix 1: Verb-Free Ukrainian Pattern Bank (Priority: HIGH)
**Prevents:** 80%+ of validation loops in M1-M14
**Scope:** All A1 modules M1-M14
**Template file:** Content prompt templates (beginner-content.md or equivalent)

Add a section like:
```
## Verb-Free Ukrainian Patterns (Modules 1-14)
Use these patterns for Ukrainian immersion WITHOUT conjugated verbs:
- Це + noun: "Це кіт" (This is a cat)
- Noun + adjective: "великий дім" (big house)
- Noun + noun (genitive): "центр Києва" (center of Kyiv)
- Question particles: "Хто це?" "Що це?" "Який?"
- Demonstratives: "Цей, ця, це, ці"
- Possessives: "мій, моя, моє, мої"
- Preposition + noun: "у місті", "на столі"
DO NOT use: conjugated verbs, imperatives, infinitives
```

### Fix 2: Plan-Constraint Validation Gate (Priority: HIGH)
**Prevents:** Plan/constraint conflicts causing rewrites and orphaned vocab
**Scope:** All modules with sequence constraints
**Target:** `scripts/build_module.py`

Add pre-build check: parse plan objectives and vocabulary_hints, compare against sequence constraints for the module number. Flag conflicts before content generation starts.

### Fix 3: Fix Prompt Deduplication (Priority: MEDIUM)
**Prevents:** Wasted API budget on identical repeated fixes
**Scope:** All modules
**Target:** `scripts/pipeline_v5.py`

Before sending a fix prompt, hash it and compare against previous fix prompts for this build. If identical, escalate immediately instead of retrying.

### Fix 4: Unjumble Schema Example in Activity Prompt (Priority: MEDIUM)
**Prevents:** Wrong field names in unjumble activities
**Scope:** All modules using unjumble activity type
**Target:** Activity prompt templates

### Fix 5: R2U Russicism Cross-Check (Priority: MEDIUM)
**Prevents:** Semantically inappropriate words that pass VESUM
**Scope:** All modules
**Target:** `scripts/rag_batch_verify.py`

### Fix 6: Stale Plan Updates (Priority: LOW — requires user approval)
**Prevents:** Contradictory objectives
**Modules affected:** M12 (colors-and-clothing), M14 (checkpoint-first-contact)
**Action:** Propose new plan versions removing verb/dative objectives that conflict with sequence constraints

---

## Modules Needing Rebuild

| Module | Reason | Severity |
|--------|--------|----------|
| M12 colors-and-clothing | Russianisms, 16+ verb violations, choppy prose — too many issues for patch fix | Must rebuild after template fixes |
| M13 plurals-and-alternation | Critical factual error (ніж/ножі alternation mislabeled), unjumble schema broken | Must rebuild after template + schema fixes |

## Modules Fixable Without Rebuild

| Module | Fixes Needed |
|--------|-------------|
| M11 describing-things-adjectives | Remove 1 imperative (Подивімося), fix Latin transliteration, remove metalanguage from vocab YAML |
| M14 checkpoint-first-contact | Fix true-false activity (И/Н confusion), update plan to remove verb objectives |

---

## Template Health Scores

| Template | Score | Notes |
|----------|-------|-------|
| Content prompt (beginner) | 5/10 | Verb-free constraint impossible to meet without pattern bank |
| Activities prompt | 6/10 | Missing unjumble schema, otherwise functional |
| Validation prompt | 4/10 | Duplicate fix prompts, no deduplication |
| Fix prompts | 4/10 | Identical prompts sent repeatedly |
