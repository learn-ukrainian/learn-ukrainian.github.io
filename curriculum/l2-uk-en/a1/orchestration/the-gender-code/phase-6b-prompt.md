        # Phase 6b: Apply Prose Fixes

        Read the review below and fix the issues in the content file.

        ## Review

        # Рецензія: The Gender Code

**Level:** A1 | **Module:** 3
**Overall Score:** 8.6/10
**Status:** FAIL (Auto-fail on Linguistic Accuracy)
**Reviewed:** 2026-02-16

## Plan Verification

```
Plan-Content Alignment: [PASS]
- Sections: All present (Warm-up, Presentation, Classification, Application, Summary)
- Vocabulary: 24/24 from plan included, with additional thematic words (sun, heart, artifact).
- Grammar scope: Covered gender and declension families as planned.
- Objectives: All met, though a factual error exists in the declension section.
```

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 9/10 | <7 | Very warm, supportive "neighbor" persona is consistent. |
| 2 | Coherence | 9/10 | <7 | Logical progression from simple endings to complex exceptions. |
| 3 | Relevance | 10/10 | <7 | Directly addresses A1.1 core grammar needs. |
| 4 | Educational | 8/10 | <7 | Explanations are clear but the `тато` classification error is confusing. |
| 5 | Language | 9/10 | <8 | Natural, simple Ukrainian. No Russianisms found. |
| 6 | Pedagogy | 8/10 | <7 | The "families" metaphor is great, but the misclassification of `тато` hurts it. |
| 7 | Immersion | 9/10 | <6 | 11% immersion (target 10-25%). Perfect for A1.1 intro. |
| 8 | Activities | 9/10 | <7 | High variety (10 activities), well-aligned with theory. |
| 9 | Richness | 9/10 | <6 | Great use of S.T.A.L.K.E.R. and folklore (The Neuter Sun). |
| 10 | Beginner Safety | 10/10 | <7 | "Would I Continue?" 5/5. Extremely safe and encouraging. |
| 11 | LLM Fingerprint | 8/10 | <7 | Some repetitive phrasing ("Cracking the code", "meeting neighbors"). |
| 12 | Linguistic Accuracy | 7/10 | <9 | Major error: `тато` (Family 2) listed in Family 1. |

**Weighted Overall:** 
(9×1.5 + 9×1.0 + 10×1.0 + 8×1.2 + 9×1.1 + 8×1.2 + 9×1.0 + 9×1.3 + 9×0.9 + 10×1.3 + 8×1.0 + 7×1.5) / 14.0 = **120.8 / 14 = 8.63/10**

## Auto-Fail Checklist Results

- Russianisms: [CLEAN]
- Calques: [CLEAN]
- Grammar scope: [CLEAN]
- Activity errors: [CLEAN] (Activities correctly place `Микола` in Family 1, unlike the text).
- Beginner safety: 5/5

## Critical Issues Found

### Issue 1: Linguistic Accuracy (Declension Classification)
- **Location**: Line 266 / Section "Family 1: The «Open/A» Group"
- **Original**: «However, this family also welcomes a few «masculine guests»... For example, **тато** [ˈtɑtɔ] (father) and the name **Микола** [mɪˈkɔlɑ] (Mykola) live here because they share the same endings»
- **Problem**: `тато` belongs to the **2nd declension** (Family 2) because it ends in **-о**. Family 1 is strictly for nouns ending in **-а** or **-я**. Listing `тато` here is a factual grammar error.
- **Fix**: Remove `тато` from the Family 1 section. Keep `Микола` as the example of a masculine guest. Move `тато` to Family 2 as an example of a masculine noun ending in -о.

### Issue 2: IPA Inconsistency
- **Location**: Multiple locations (Lines 64, 190, 33)
- **O

        ## Files

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/the-gender-code.md`

        ## Instructions

        1. Fix issues from the review — word/sentence changes, grammar, clarity
        2. Skip major structural rewrites
        3. After fixing, run IPA lint: `.venv/bin/python scripts/lint_ipa.py /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/the-gender-code.md --fix`
        4. Regenerate MDX: `.venv/bin/python scripts/generate_mdx.py l2-uk-en a1 3`
