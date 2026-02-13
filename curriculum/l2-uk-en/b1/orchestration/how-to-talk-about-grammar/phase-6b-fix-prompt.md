# Phase 6b: Post-Review Fixes

> **You are Gemini, applying fixes from an independent review.**
> **Your ONLY task: Fix the specific issues identified, return the full corrected content.**

## Current Content (READ FROM DISK)

```
curriculum/l2-uk-en/b1/how-to-talk-about-grammar.md
```

## Review (READ FROM DISK)

```
curriculum/l2-uk-en/b1/review/how-to-talk-about-grammar-review.md
```

## Required Fixes

### Fix 1: Russianism — "на то, що" → "на те, що"
**Location:** Near the Займенник section, sentence about "себе"
**Current:** «...яка вказує на **то**, що дія повертається до самого виконавця.»
**Fix:** «...яка вказує на **те**, що дія повертається до самого виконавця.»

### Fix 2: Agreement Error — neuter adjectives
**Location:** Дієслово section, usage note about зворотні дієслова
**Current:** «...які можуть змінювати значення дії з активного на **пасивний** або **зворотний**.»
**Fix:** «...які можуть змінювати значення дії з активного на **пасивне** або **зворотне**.» (agrees with "значення" — neuter)

### Fix 3: Calque — "відчуваєте себе" → "почуваєтеся"
**Location:** Introduction/psychology section
**Current:** «Ви **відчуваєте себе** не стороннім спостерігачем...»
**Fix:** «Ви **почуваєтеся** не стороннім спостерігачем...»

### Fix 4: Redundant preposition
**Location:** Mnemonic section
**Current:** «...на кожну першу літеру слова у фразі відповідає першій літері назви відмінка.»
**Fix:** «**Кожна** перша літера слова у фразі відповідає першій літері назви відмінка.»

### Fix 5: Immersion Rebalancing (65% target)

This is the MOST IMPORTANT fix. The module currently has 95% Ukrainian immersion, but as a B1 bridge module (M01), the plan requires 65% immersion. Students are transitioning from A2 (English-mediated) to B1 (Ukrainian-mediated). This module must BRIDGE that gap with:

**Rule: L1 scaffolding with L2 primacy for 65% immersion:**
- Ukrainian term FIRST, English equivalent in parentheses on FIRST introduction only
- English explanations woven through main sections for abstract concepts
- Full English scaffold in the introduction
- After a term is introduced with its English equivalent, use Ukrainian exclusively

**Specific changes needed:**

1. **Introduction section**: Keep the English paragraph. Add 2-3 more English sentences explaining what metalanguage is and why students need it.

2. **Section 2 (Самостійні частини мови)**: After the intro paragraph (Ukrainian), add a 2-sentence English bridging note: "In this section, you'll learn the names of the six content word types in Ukrainian. Pay attention to the Ukrainian terms — after this module, we'll use them exclusively."

3. **Section 3 (Службові слова)**: Add a brief English bridging note: "Service words (службові слова) work differently from content words. They connect ideas and add nuance to sentences."

4. **Section 4 (Відмінки)**: Add an English bridging note before the case list: "Ukrainian has seven grammatical cases. Each case changes the ending of a noun to show its role in a sentence. The system below will help you learn their names."

5. **Section 5 (Будова слова)**: Add an English bridging note: "Understanding word structure (morphemics) will help you decode unfamiliar words. Here are the building blocks of Ukrainian words."

6. **Section 6 (Практика)**: Keep mostly Ukrainian — by this section students should be comfortable with the terms.

7. **Section 7 (Підсумок)**: Can remain Ukrainian.

The total English content should bring immersion to approximately 65-75%. Do NOT replace existing Ukrainian content — ADD English scaffolding alongside it.

## Output Format

Return the COMPLETE fixed content:

```
===CONTENT_START===
{full corrected content with all 5 fixes applied}
===CONTENT_END===
```

```
===FRICTION_START===
**Phase**: Phase 6b: Post-Review Fixes
**Step**: {what}
**Friction Type**: NONE | ...
**Raw Error**: {or "None"}
**Self-Correction**: {or "N/A"}
**Proposed Tooling Fix**: {or "N/A"}
===FRICTION_END===
```

## Boundaries

- Apply ALL 5 fixes
- Do NOT remove existing Ukrainian content for the immersion fix — ADD English alongside
- Do NOT change activity or vocabulary files
- Do NOT change H2/H3 structure
