        # Phase 6b: Apply Prose Fixes

        Read the review below and fix the issues in the content file.

        ## Review

        # Рецензія: My Daily Routine

**Level:** A1 | **Module:** 25
**Overall Score:** 8.6/10
**Status:** PASS
**Reviewed:** 2026-02-16

## Plan Verification

```
Plan-Content Alignment: PASS
- Sections: PASS (Theory/Practice structure covers all plan points)
- Vocabulary: PASS (All required words present, plus recommended)
- Grammar scope: PASS (Reflexive verbs and adverbs covered correctly)
- Objectives: PASS (All learning objectives addressed)
```

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 8/10 | <7 | Tone is warm and excellent ("Привіт, сусіде!"), but word count (1865) is 2.5x target, risking overwhelm. |
| 2 | Coherence | 9/10 | <7 | Logical flow from verbs -> time -> sequence -> frequency. |
| 3 | Relevance | 10/10 | <7 | Daily routine is a core survival skill. |
| 4 | Educational | 9/10 | <7 | Explanation of "-ся" is clear, accessible, and accurate. |
| 5 | Language | 9/10 | <8 | Natural phrasing (e.g., "Заходь на каву"). |
| 6 | Pedagogy | 8/10 | <7 | Good PPP, but Presentation phase is very text-heavy for A1. |
| 7 | Immersion | 6/10 | <6 | 42% is low for A1.3 (Target 60-80%). English explanations are too verbose. |
| 8 | Activities | 10/10 | <7 | Excellent variety, 72+ items, culturally relevant contexts. |
| 9 | Richness | 8/10 | <6 | Good cultural notes (Lunch culture), but some missed opportunities for more Ukrainian text. |
| 10 | Beginner Safety | 8/10 | <7 | "Would I Continue?" 4/5. Safe tone, but length is daunting. |
| 11 | LLM Fingerprint | 9/10 | <7 | Very human voice, avoids "In this lesson we will..." clichés. |
| 12 | Linguistic Accuracy | 9/10 | <9 | Grammar is solid. One ambiguous phrase noted below. |

**Weighted Overall:** 120.4 / 14.0 = **8.6/10**

## Auto-Fail Checklist Results

- Russianisms: [CLEAN]
- Calques: [CLEAN]
- Grammar scope: [CLEAN]
- Activity errors: [CLEAN]
- Beginner Safety: 4/5

## Critical Issues Found

### Issue 1: Low Immersion (A1.3 Violation)
- **Location**: Entire module
- **Original**: (English conversational filler throughout)
- **Problem**: Immersion is at 42%, while the A1.3 target is 60-80%. The module relies too heavily on lengthy English setups for every section and dialogue.
- **Fix**: Trim English scaffolding. For example, change "Imagine you met a neighbor in the morning. You want to ask about his schedule. In Ukraine we often talk about work and time. Let's look at a typical conversation." to just "Read this dialogue about a morning routine."

### Issue 2: Ambiguous Phrasing
- **Location**: Section "Робочий день проти вихідного", Table row 3
- **Original**: «Я не одягаюся довго.»
- **Problem**: Ambiguous. It suggests "I don't dress for a long time" (duration/negation mix) rather than "I dress slowly" or "I take my time dressing". It's confusing for a beginner comparing "швидко" vs "довго/повільно".
- **Fix**: «Я одягаюся повільно.» (I dress slowly) — this creates a clear antonym pair with "швидко".



        ## Files

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/my-daily-routine.md`

        ## Instructions

        1. Fix issues from the review — word/sentence changes, grammar, clarity
        2. Skip major structural rewrites
        3. After fixing, run IPA lint: `.venv/bin/python scripts/lint_ipa.py /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/my-daily-routine.md --fix`
