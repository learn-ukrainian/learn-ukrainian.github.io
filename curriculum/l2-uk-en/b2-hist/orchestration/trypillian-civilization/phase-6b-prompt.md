        # Phase 6b: Apply Prose Fixes

        Read the review below and fix the issues in the content file.

        ## Review

        # Рецензія: Трипільська цивілізація

**Level:** B2_HIST | **Module:** 1
**Overall Score:** 9.2/10
**Status:** PASS
**Reviewed:** 2026-02-17

## Plan Verification

```
Plan-Content Alignment: PASS
- Sections: All plan sections present and correctly structured.
- Vocabulary: 18/18 required items present; 10/10 recommended items present.
- Grammar scope: Historical narrative and passive constructions used correctly.
- Objectives: All learning objectives addressed thoroughly.
```

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 10/10 | <7 | Compelling narrative voice, excellent use of hooks ("Але як ми про це дізналися?", "естетичний шок"). |
| 2 | Coherence | 10/10 | <7 | Logical flow from discovery to analysis to modern reflection. |
| 3 | Relevance | 10/10 | <7 | Strong connection to Ukrainian identity and modern decolonization. |
| 4 | Educational | 10/10 | <7 | Deep dive into "proto-cities" and "burnt house horizon" provides high value. |
| 5 | Language | 9/10 | <8 | High literary standard, though slightly repetitive with transition words ("Але", "Важливо розуміти"). |
| 6 | Pedagogy | 9/10 | <7 | Strong scaffolding, though the reading activity text is a placeholder. |
| 7 | Immersion | 10/10 | <6 | 100% Ukrainian context, strong cultural immersion. |
| 8 | Activities | 8/10 | <7 | Reading activity text is a stub; other activities are well-structured. |
| 9 | Richness | 10/10 | <6 | Packed with specific data (dates, sizes, names) and rich callouts. |
| 10 | Beginner Safety | 8/10 | <7 | Content is very long (134% of target), potentially overwhelming, but broken up well. |
| 11 | LLM Fingerprint | 8/10 | <7 | Some repetitive "Imagine" (Уявіть) and "It is important to understand" patterns. |
| 12 | Linguistic Accuracy | 9/10 | <9 | Almost flawless, minor stylistic polish needed. |

**Weighted Overall:** (15 + 10 + 10 + 12 + 9.9 + 10.8 + 10 + 10.4 + 9 + 10.4 + 8 + 13.5) / 14.0 = **9.2/10**

## Auto-Fail Checklist Results

- Russianisms: [CLEAN]
- Calques: [CLEAN]
- Grammar scope: [CLEAN]
- Activity errors: [Activity text stub detected]
- Beginner Safety: 4/5 (Length is the main risk)

## Critical Issues Found

### Issue 1: AI Filler Phrases
- **Location**: Line 38 / Section "Вступ"
- **Original**: «Важливо розуміти, що термін «енеоліт» позначає перехідний час...»
- **Problem**: "Важливо розуміти, що" is a classic AI filler that delays the point.
- **Fix**: «Термін «енеоліт» позначає перехідний час...» (Cut the filler).

### Issue 2: Repetitive Transitions
- **Location**: Lines 81, 156, 351, 621 / Various Sections
- **Original**: «Але як ми про це дізналися?» ... «Але повернімося до тексту...» ... «Але навіть сміливі гіпотези...» ... «Але форма була лише полотном.»
- **Problem**: Overuse of "Але" (But) to start paragraphs/sections makes the transition formulaic.
- **Fix**: Vary the transitions: «Як ми про це дізналися?», «Повернімося до тексту...», «Утім, навіть 

        ## Files

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b2-hist/trypillian-civilization.md`

        ## Instructions

        1. Fix issues from the review — word/sentence changes, grammar, clarity
        2. Skip major structural rewrites
        3. After fixing, run IPA lint: `.venv/bin/python scripts/lint_ipa.py /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b2-hist/trypillian-civilization.md --fix`
