        # Phase 6b: Apply Prose Fixes

        Read the review below and fix the issues in the content file.

        ## Review

        # Рецензія: Prepositions III

**Level:** A1 | **Module:** 30
**Overall Score:** 9.0/10
**Status:** PASS
**Reviewed:** 2026-02-17

## Plan Verification

```
Plan-Content Alignment: PASS
- Sections: PASS (All plan points covered)
- Vocabulary: PASS (All required words present; "від" present in vocab list but under-explained in text)
- Grammar scope: PASS (Appropriate for A1.3)
- Objectives: PASS
```

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 10/10 | <7 | Excellent "Patient Tutor" persona; "GPS-navigator" and "Anchor" metaphors work well. |
| 2 | Coherence | 9/10 | <7 | Logical flow from static -> dynamic -> origin. |
| 3 | Relevance | 10/10 | <7 | Perfectly aligned with A1 need for basic navigation. |
| 4 | Educational | 8/10 | <7 | **Issue:** Explains "до" (to person) but misses "від" (from person) in body text. |
| 5 | Language | 9/10 | <8 | Natural Ukrainian, but one typo found ("спит" instead of "спить"). |
| 6 | Pedagogy | 9/10 | <7 | Strong PPP structure; clear distinction between йти/їхати. |
| 7 | Immersion | 10/10 | <6 | 38% is perfect for A1.3 (Target 35-55%); good English scaffolding. |
| 8 | Activities | 9/10 | <7 | Varied and well-structured; typo in one item. |
| 9 | Richness | 9/10 | <6 | "Slipper Culture" and "Glass Holder" callouts add great flavor. |
| 10 | Beginner Safety | 10/10 | <7 | "Would I Continue?" 5/5. Very encouraging tone. |
| 11 | LLM Fingerprint | 8/10 | <7 | Slightly repetitive "Ukrainian is logical" phrasing, but acceptable. |
| 12 | Linguistic Accuracy | 10/10 | <9 | Grammar rules are explained simply and correctly. |

**Weighted Overall:** 9.2/10 (Calculated) -> **9.0/10** (Rounding down due to educational gap)

## Auto-Fail Checklist Results

- Russianisms: [CLEAN] (One typo "спит" resembles Russian, but looks like typo)
- Calques: [CLEAN]
- Grammar scope: [CLEAN]
- Activity errors: [ISSUES FOUND] (Typo in item)
- Beginner safety: 5/5

## Critical Issues Found

### Issue 1: Missing Grammar Explanation (Educational)
- **Location**: Section "Питання «Звідки?»" vs Activity "Quiz"
- **Original**: Body text explains "з" (from place) but not "від" (from person).
- **Problem**: The quiz asks "___ цей лист? — Це від мами" (Item 7), but the student was never taught that "from a person" requires "від", unlike "from a place" (з).
- **Fix**: Add a brief note in the "Звідки" section: "Just like we go **до** a person, we come back **від** [vid] a person. *Я йду від мами.*"

### Issue 2: Typo / Russianism (Language)
- **Location**: Activity `fill-in` ("Прийменники місця"), Item 7
- **Original**: "Кіт спит ___ дивані."
- **Problem**: "Спит" is Russian or a typo. Ukrainian 3rd person singular is "спить".
- **Fix**: Change to "Кіт **спить** ___ дивані."

### Issue 3: Unnatural English Translation (Experience)
- **Location**: Section "Історія: Андрій у Києві"
- **Original**: "Він їде в метро. (He goes in the metro.)"
- **Problem**: "Goes 

        ## Files

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/prepositions-iii.md`

        ## Instructions

        1. Fix issues from the review — word/sentence changes, grammar, clarity
        2. Skip major structural rewrites
        3. After fixing, run IPA lint: `.venv/bin/python scripts/lint_ipa.py /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/prepositions-iii.md --fix`
