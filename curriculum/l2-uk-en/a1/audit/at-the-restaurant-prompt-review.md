# Prompt Engineering Review: at-the-restaurant

**Track:** a1 | **Sequence:** 53
**Pipeline:** v4
**Validate attempts:** 2
**Friction reports:** 2 (content: NONE, activities: NONE)

## Prompt Clarity

| Issue | Severity | Template File | Details |
|-------|----------|---------------|---------|
| Dative case generated despite ban | HIGH | placeholders.yaml (LEVEL_CONSTRAINTS) | Model generated "вам" (3x) and "мові" (1x) -- all dative forms. "Вам" is explicitly listed in the ban but model still produced it. The constraint is in LEVEL_CONSTRAINTS but buried in a long list. |
| Instrumental case generated | HIGH | phase-2-output / validate-fix2 | "з офіціантом" uses Instrumental, explicitly banned. Model either ignored or missed the constraint in the long LEVEL_CONSTRAINTS block. |
| Subordinate clauses generated | HIGH | validate-fix2-prompt.md | 4 subordinate clause violations: "що о", "що в", "коли в", "Якщо в" (3x). These markers are all explicitly banned but the model used them extensively. |
| Sentence length violations (6 sentences) | HIGH | validate-fix2-prompt.md | 6 Ukrainian sentences exceeded 10-word limit (11-14 words). Same pattern as M51 and M52. |
| Russianisms in content | HIGH | validate-fix1-prompt.md | "давайте попрактикуємо" and "давайте подивимося" are Russian calques. SHARED_CONTENT_RULES has a Russianisms table but these specific forms are not listed. |
| Section balance: bloated section | MEDIUM | validate-fix2-prompt.md | "Презентація: Мова замовлення" has 997 words (51% of total) while "Підсумок та етикет" has only 107/250 words (-143). The content prompt provides word budgets per section but model significantly unbalanced them. |
| Robotic structure: 3x "if you..." | LOW | validate-fix2-prompt.md | Three sentences start with "if you" pattern. Anti-robotic rules exist but buried in SHARED_CONTENT_RULES. |

## Context Gaps

| Missing Context | Impact | Fix |
|-----------------|--------|-----|
| Russianisms table incomplete | HIGH | "давайте + perfective" is a common Russian calque pattern not listed in the Russianisms table. Add: "давайте попрактикуємо -> попрактикуймо; давайте подивимося -> подивімося" |
| Grammar constraints not prominent enough | HIGH | LEVEL_CONSTRAINTS is a wall of text in placeholders.yaml. The model misses individual rules. Break into numbered, short rules with examples. |
| Section balance not enforced at generation time | MEDIUM | Content prompt provides word budgets but no enforcement mechanism. Add: "CHECK: No section should exceed 40% of total words. If a section exceeds its budget by >50%, split it or move content to an adjacent section." |

## Friction Root Causes

| Friction Point | Root Cause Type | Details | Template Fix |
|----------------|-----------------|---------|--------------|
| Russianisms: давайте + perf | template_gap | These calques are not in the Russianisms table | Expand Russianisms table with "давайте" pattern |
| Dative/Instrumental/subordinate violations | template_gap + model_limitation | Constraints are clear but model ignores them in long text. Need more prominent placement and examples. | Break LEVEL_CONSTRAINTS into numbered rules with examples |
| Sentence length violations | template_gap | Same recurring issue as M51-M52 | Add sentence-counting enforcement (same fix) |
| Section bloat (51% in one section) | template_gap | No max-per-section constraint | Add 40% cap per section |
| PLAN_SECTION_MISSING false positive | schema_mismatch | Same heading matcher bug as M51-M52 | Fix audit tool |
| VESUM: "піцею", "сч", "єднує" | mixed | "піцею" is Instrumental of піца (could be VESUM gap); "сч" is a fragment (likely extraction error); "єднує" is part of "об'єднує" (extraction split on apostrophe) | Fix VESUM word extraction to handle apostrophes |

## Fix Loop Analysis

| Phase | Attempts | Root Cause | Preventable? |
|-------|----------|------------|--------------|
| validate | 2 | Fix1: Russianisms + section heading mismatch. Fix2: 17 pedagogical violations (dative 4x, instrumental 1x, subordinate 4x, sentence length 6x, robotic 1x, section balance 1x). | YES -- most violations are recurring patterns seen across M51-M53. Stronger constraint formatting and examples would prevent the majority. |

## VESUM Findings

- 362/365 (99.2%) verified
- Not found: "піцею" (Instrumental of піца -- VESUM may lack loanword declensions), "сч" (extraction artifact), "єднує" (apostrophe split from "об'єднує")
- The VESUM extraction pipeline should handle apostrophe-containing words better.

## Suggested Template Fixes

### Fix 1: Restructure LEVEL_CONSTRAINTS as numbered rules with examples (Priority: HIGH)
**Before:** A dense paragraph listing all grammar constraints together.
**After:**
```
HARD GRAMMAR RULES (numbered for enforcement):
1. Max 10 words per Ukrainian sentence. Example: "Я замовляю каву та тістечко." (5 words, OK)
2. ONE clause per sentence. BANNED: який, яка, що, коли, якщо, тому що, бо, щоб, поки.
3. Dative FORBIDDEN: мені, тобі, йому, їй, вам, їм, мові, AND all -ові/-еві dative endings.
4. Instrumental FORBIDDEN: з другом, з мамою, з офіціантом. No -ом/-ою/-ем/-ею endings.
5. Only imperfective verbs. WRONG: написав (perf) -> RIGHT: писав (impf).
6. No participles.
```
**Cross-module:** All A1 modules.

### Fix 2: Expand Russianisms table with "давайте + perfective" pattern (Priority: HIGH)
**Before:** Table does not include this common calque.
**After:** Add rows: "давайте попрактикуємо -> попрактикуймо (or use English instruction); давайте подивимося -> подивімося (or use English instruction)"
**Cross-module:** All A1+ modules.

### Fix 3: Add section balance cap (Priority: MEDIUM)
**Before:** Section word budgets provided but no maximum.
**After:** Add to content prompt: "BALANCE CHECK: No section may contain more than 40% of total words. If one section is significantly larger, redistribute content to maintain balance."
**Cross-module:** All modules.

### Fix 4: Fix VESUM apostrophe handling (Priority: LOW)
**Issue:** "об'єднує" splits into "об" + "єднує", causing VESUM miss.
**Fix:** Tooling fix -- word tokenizer should keep apostrophe-containing words intact.

## Summary

**Template health:** NEEDS WORK
**Top 3 fixes by leverage:**
1. Restructure LEVEL_CONSTRAINTS as numbered rules with examples (HIGH) -- addresses the root cause of most pedagogical violations across M51-M53
2. Expand Russianisms table with "давайте + perfective" pattern (HIGH) -- prevents a common calque
3. Add section balance cap to content prompt (MEDIUM) -- prevents bloated sections
