        # Phase 6b: Apply Prose Fixes

        Read the review below and fix the issues in the content file.

        ## Review

        # Рецензія: The Accusative II: People

**Level:** A1 | **Module:** 12
**Overall Score:** 8.5/10
**Status:** PASS
**Reviewed:** 2026-02-16

## Plan Verification

```
Plan-Content Alignment: [PASS]
- Sections: [PASS] All meta sections mapped to MD headers.
- Vocabulary: [15/8 from plan, 15 extra] Core family/animate vocab well-covered.
- Grammar scope: [PASS] Focuses strictly on Accusative Animate (Masculine/Feminine).
- Objectives: [PASS] All learning objectives addressed through theory and activities.
```

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 9/10 | <7 | Excellent "Heart Words" vs "Stone Words" metaphor. |
| 2 | Coherence | 9/10 | <7 | Logical flow from metaphor to specific gender rules. |
| 3 | Relevance | 9/10 | <7 | Highly relevant family and social contexts. |
| 4 | Educational | 9/10 | <7 | Clear explanation of the Genitive connection. |
| 5 | Language | 8/10 | <8 | Correct Ukrainian, but some minor accent/stress inconsistencies in IPA. |
| 6 | Pedagogy | 9/10 | <7 | Strong scaffolding; addresses the "Animate Trap" specifically. |
| 7 | Immersion | 7/10 | <6 | 25% immersion meets target, though slightly leaning on English. |
| 8 | Activities | 8/10 | <7 | Items match theory well; good variety of activity types. |
| 9 | Richness | 9/10 | <6 | 9 engagement boxes and high word count (300% of target). |
| 10 | Beginner Safety | 9/10 | <7 | "Would I Continue?" 5/5. Supportive tone. |
| 11 | LLM Fingerprint | 7/10 | <7 | Repetitive structure in some H3 sections; "це не просто" pattern found. |
| 12 | Linguistic Accuracy | 9/10 | <9 | High accuracy in case forms; animals correctly treated as animate. |

**Weighted Overall:** (9×1.5 + 9×1.0 + 9×1.0 + 9×1.2 + 8×1.1 + 9×1.2 + 7×1.0 + 8×1.3 + 9×0.9 + 9×1.3 + 7×1.0 + 9×1.5) / 14.0 = **8.46/10**

## Auto-Fail Checklist Results

- Russianisms: [CLEAN]
- Calques: [CLEAN]
- Grammar scope: [CLEAN]
- Activity errors: [CLEAN] One minor IPA stress check needed but grammar is solid.
- Beginner safety: 5/5

## Critical Issues Found

### Issue 1: LLM Fingerprint / Rhetoric Pattern
- **Location**: Section "My Family: Loving and Waiting"
- **Original**: «Think of the Accusative case as a spotlight.»
- **Problem**: Classic AI "X as Y" metaphor (Metaphor density test). While helpful, the module uses multiple high-level metaphors (Spotlight, Heart vs Stone, Outfit, Skeleton).
- **Fix**: Remove the spotlight metaphor or consolidate with the "Heart Word" theme to reduce abstract clutter.

### Issue 2: Linguistic Nuance / IPA Stress
- **Location**: Vocabulary YAML
- **Original**: «мама [mɑˈmɑ]»
- **Problem**: Stress in Ukrainian is on the first syllable for «мама» (usually [ˈmɑmɑ]), though vocative or emphatic might differ. In standard Nominative A1, [ˈmɑmɑ] is preferred.
- **Fix**: Change to [ˈmɑmɑ].

### Issue 3: LLM Fingerprint / Structure
- **Location**: Section "The Animate Trap"
- **Original**: «Це помилка! ... Це свід

        ## Files

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/the-accusative-ii-people.md`

        ## Instructions

        1. Fix issues from the review — word/sentence changes, grammar, clarity
        2. Skip major structural rewrites
        3. After fixing, run IPA lint: `.venv/bin/python scripts/lint_ipa.py /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/the-accusative-ii-people.md --fix`
        4. Regenerate MDX: `.venv/bin/python scripts/generate_mdx.py l2-uk-en a1 12`
