        # Phase 6b: Apply Prose Fixes

        Read the review below and fix the issues in the content file.

        ## Review

        # Рецензія: Can, Must, Want - Modals

**Level:** A1 | **Module:** 24
**Overall Score:** 6.4/10
**Status:** FAIL
**Reviewed:** 2026-02-16

## Plan Verification

```
Plan-Content Alignment: FAIL
- Sections: Matches roughly, but content is significantly denser than appropriate for A1.
- Vocabulary: 21 items in audit vs 8 required in plan. Massive scope creep.
- Grammar scope: Explodes beyond "Introduction to Modals" into complex bureaucratic nuances (необхідно, намагатися, заборонено).
- Objectives: Met, but at the cost of learner safety.
```

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 5/10 | <7 | Starts cold ("We distinguish..."). No warm welcome. Feels like reading a dictionary, not a lesson. |
| 2 | Coherence | 7/10 | <7 | Logical flow, but the density makes it hard to follow. |
| 3 | Relevance | 8/10 | <7 | The core modals are highly relevant, but the "official language" section is irrelevant for A1. |
| 4 | Educational | 6/10 | <7 | Explanations are clear, but the volume of information ensures low retention. |
| 5 | Language | 8/10 | <8 | Generally correct Ukrainian, but some stiff phrasing ("Зробити це сьогодні — можливо"). |
| 6 | Pedagogy | 5/10 | <7 | Classic "drinking from a firehose". Introduces ~16 modal variations in one lesson. |
| 7 | Immersion | 7/10 | <6 | 41% is acceptable for A1.3. |
| 8 | Activities | 7/10 | <7 | Functional drill-and-kill. |
| 9 | Richness | 6/10 | <6 | Pure grammar explanation. No cultural depth or engaging narrative elements. |
| 10 | Beginner Safety | 4/10 | <7 | "Would I Continue?" 2/5. Overwhelming amount of vocabulary/synonyms. |
| 11 | LLM Fingerprint | 7/10 | <7 | "Grammar is a tool. Desire is the engine." (Metaphor). "Today you received keys to freedom..." (Grandiosity). |
| 12 | Linguistic Accuracy | 7/10 | <9 | IPA errors found (mismatching forms). |

**Weighted Overall:** (5×1.5 + 7×1 + 8×1 + 6×1.2 + 8×1.1 + 5×1.2 + 7×1 + 7×1.3 + 6×0.9 + 4×1.3 + 7×1 + 7×1.5) / 14.0 = **6.4/10**

## Auto-Fail Checklist Results

- Russianisms: [CLEAN]
- Calques: [CLEAN]
- Grammar scope: [FAIL] - Includes "намагатися" (striving), "необхідно/обов'язково" (official registers) which are B1 concepts.
- Activity errors: [CLEAN]
- Beginner Safety: 2/5 (Fail - Overwhelming)

## Critical Issues Found

### Issue 1: IPA Error (Hallucination)
- **Location**: Section "Могти", Example 2
- **Original**: «[vɪ ˈmɔʒɛtɛ dɔpɔmhˈtɪ]»
- **Problem**: The IPA for `допомогти` is mangled. It misses the vowels and `ɦ`.
- **Fix**: «[vɪ ˈmɔʒɛtɛ dɔpɔmɔɦˈtɪ]»

### Issue 2: IPA Mismatch (Form)
- **Location**: Section "Спроби та зусилля"
- **Original**: «намагатися [nɑmɑˈɦɑjɛmɔsʲɑ]»
- **Problem**: The text gives the infinitive (`намагатися`), but the IPA provides the first person plural form (`ми намагаємося` - [nɑmɑˈɦɑjɛmɔsʲɑ]).
- **Fix**: «намагатися [nɑmɑˈɦɑtɪsʲɑ]» (or remove this advanced verb entirely).

### Issue 3: Cognitive Overload (Scope Creep)
- **Lo

        ## Files

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/can-must-want-modals.md`

        ## Instructions

        1. Fix issues from the review — word/sentence changes, grammar, clarity
        2. Skip major structural rewrites
        3. After fixing, run IPA lint: `.venv/bin/python scripts/lint_ipa.py /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/can-must-want-modals.md --fix`
