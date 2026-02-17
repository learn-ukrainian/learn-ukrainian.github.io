        # Phase 6b: Apply Prose Fixes

        Read the review below and fix the issues in the content file.

        ## Review

        # Рецензія: Colors & Clothing

**Level:** A1 | **Module:** 27
**Overall Score:** 8.1/10
**Status:** PASS
**Reviewed:** 2026-02-16

## Plan Verification

```
Plan-Content Alignment: PASS
- Sections: Matches content coverage (Colors, Gender, Clothes, Nosyty, Shopping).
- Vocabulary: 23/25 from plan. Missing: "коричневий", "взуття".
- Grammar scope: PASS. Covers adjectives, nosyty, accusative, pluralia tantum.
- Objectives: PASS. All met.
```

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 8/10 | <7 | Generally warm, but some metaphors are too abstract for A1 ("canvas for the soul"). |
| 2 | Coherence | 8/10 | <7 | Inconsistent terminology (плаття vs сукня). |
| 3 | Relevance | 10/10 | <7 | Very practical shopping skills. |
| 4 | Educational | 8/10 | <7 | Explanations are clear, but some activity items are untaught. |
| 5 | Language | 9/10 | <8 | "Плаття" is acceptable but "Сукня" is preferred standard. |
| 6 | Pedagogy | 7/10 | <7 | Testing untaught verb forms (plural "wear", "I buy"). |
| 7 | Immersion | 10/10 | <6 | 40% is appropriate for A1.3 transition. |
| 8 | Activities | 7/10 | <7 | "Phrase Building" includes untaught conjugation. |
| 9 | Richness | 9/10 | <6 | Good cultural notes (Vyshyvanka, symbolism). |
| 10 | Beginner Safety | 8/10 | <7 | Good pacing, but "Znahidnyi vidminok" terminology is borderline (though explained well). |
| 11 | LLM Fingerprint | 7/10 | <7 | "Painting a picture", "Music of words", "Canvas for the soul" - high metaphor density. |
| 12 | Linguistic Accuracy | 10/10 | <9 | No grammatical errors found. |

**Weighted Overall:** 8.1/10

## Auto-Fail Checklist Results

- Russianisms: [CLEAN]
- Calques: [CLEAN]
- Grammar scope: [List] - Testing "Ми/Ви/Вони" forms of "носити" without teaching.
- Activity errors: [List] - "Phrase Building" requires untaught knowledge.
- Beginner Safety: 4/5

## Critical Issues Found

### Issue 1: Pedagogy / Scope Violation
- **Location**: Activities / "Phrase Building" & Content Section "The Art of Wearing"
- **Original**: Activity pairs: `left: "Ми носимо" right: "We wear"`, `left: "Ви носите" right: "You (pl) wear"`, `left: "Вони носять" right: "They wear"`.
- **Problem**: The content only teaches the singular forms ("Я ношу", "Ти носиш", "Він/Вона носить"). The plural forms are NOT introduced in the grammar table or text (except one example of "Ми носимо"). The learner cannot answer this activity based on the lesson.
- **Fix**: Add the plural forms to the grammar section or remove them from the activity.

### Issue 2: Vocabulary Inconsistency
- **Location**: Content / Various lines
- **Original**: «Чи є у вас зелене **плаття**?», «Вона носить біле **плаття**», «Я люблю чорне **плаття**».
- **Problem**: The Vocabulary YAML and the definitions list use **«сукня»**. The text mixes both. "Сукня" is the preferred standard term in this curriculum.
- **Fix**: Replace all instances of «плаття» with «сукня».


        ## Files

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/colors-and-clothing.md`

        ## Instructions

        1. Fix issues from the review — word/sentence changes, grammar, clarity
        2. Skip major structural rewrites
        3. After fixing, run IPA lint: `.venv/bin/python scripts/lint_ipa.py /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/colors-and-clothing.md --fix`
