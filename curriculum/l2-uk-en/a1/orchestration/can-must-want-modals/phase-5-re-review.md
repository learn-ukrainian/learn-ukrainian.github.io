# Рецензія: Can, Must, Want - Modals

**Level:** A1 | **Module:** 24
**Overall Score:** 7.5/10
**Status:** FAIL
**Reviewed:** 2026-02-08

## Plan Verification

Plan-Content Alignment: [FAIL]
- Sections: [FAIL] Missing "Presentation" content for "хотіти" (to want) despite title and summary claims.
- Vocabulary: [FAIL] Core modals (могти, вміти, мусити, хотіти) missing from vocabulary.yaml.
- Grammar scope: [PASS] Appropriate for A1.
- Objectives: [FAIL] "Learner can express desire" (implied by "Want" in title) is not taught.

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 7/10 | <7 | Confusion caused by missing "Want" section promised in title. |
| 2 | Coherence | 5/10 | <7 | Title says "Want", Summary says "You learned 'I want'", but the section is missing. |
| 3 | Relevance | 9/10 | <7 | Modals are high-frequency and essential. |
| 4 | Educational | 7/10 | <7 | Explanations for ability/obligation are good, but incomplete module. |
| 5 | Language | 10/10 | <8 | Ukrainian examples are natural and correct. |
| 6 | Pedagogy | 6/10 | <7 | Fails to teach a core objective (хотіти) while testing/referencing it. |
| 7 | Immersion | 7/10 | <6 | ~20% Ukrainian. Acceptable for complex grammar explanation. |
| 8 | Activities | 9/10 | <7 | Strong variety, 8 activities, valid distractors. |
| 9 | Richness | 8/10 | <6 | Good use of "Myth" and cultural context (солов'їна мова). |
| 10 | Beginner Safety | 8/10 | <7 | Clear tables, IPA provided. |
| 11 | LLM Fingerprint | 7/10 | <7 | Lazy headers "Presentation 2", "Presentation 3". |
| 12 | Linguistic Accuracy | 9/10 | <9 | No errors found in Ukrainian text. |

**Weighted Overall:** (10.5 + 5.0 + 9.0 + 8.4 + 11.0 + 7.2 + 7.0 + 11.7 + 7.2 + 10.4 + 7.0 + 13.5) / 14.0 = **7.7/10** (Adjusted manually: The critical missing section drags it down significantly).

## Auto-Fail Checklist Results

- Russianisms: [CLEAN]
- Calques: [CLEAN]
- Grammar scope: [CLEAN]
- Activity errors: [CLEAN]
- Beginner safety: 5/5

## Critical Issues Found

### Issue 1: Missing "Want" (хотіти) Section
- **Location**: Entire file
- **Original**: Title "Can, Must, **Want**"; Summary "Ви знаєте, як сказати ... «я хочу»"
- **Problem**: The verb `хотіти` (to want) is completely absent from the teaching sections. There is no conjugation table, no usage examples, and no IPA for it.
- **Fix**: Add a new presentation section for `хотіти` before the Practice section.

### Issue 2: Lazy Headers
- **Location**: Presentation sections
- **Original**: "Presentation 2", "Presentation 3", "Presentation 4"...
- **Problem**: Headers should be descriptive for navigation and review.
- **Fix**: Rename to "Expressing Obligation", "Expressing Permission", "Recommendations", etc.

### Issue 3: Missing Core Vocabulary in YAML
- **Location**: `curriculum/l2-uk-en/a1/vocabulary/24-can-must-want-modals.yaml`
- **Original**: Only 8 items (project, piano, etc.)
- **Problem**: The core modal verbs (`могти`, `вміти`, `мусити`, `хотіти`, `треба`) are not in the vocabulary file, meaning they won't generate flashcards.
- **Fix**: Add all bolded modal verbs from the text to the vocabulary YAML.

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| - | - | - | CLEAN |

## Beginner Safety Audit

"Would I Continue?" Test: 4/5
- Overwhelmed? [Pass]
- Instructions clear? [Pass]
- Quick wins? [Pass]
- Ukrainian scary? [Pass]
- Come back tomorrow? [Fail] (I'd be confused why "Want" was missing)

Emotional beats: 4 found
- Welcome: Yes (Warm-up)
- Curiosity: Pattern Discovery boxes
- Quick wins: Clear tables
- Encouragement: "Це була гарна робота" in summary

## Strengths
- Clear distinction between `могти` (physical) and `вміти` (skill).
- Excellent use of `Pattern Discovery` callouts.
- Natural dialogues in the Practice section.

## Fix Plan to Reach 9/10

### Coherence & Pedagogy: 5-6/10 → 9/10

**What to fix:**
1.  **Add `хотіти` Section:** Insert a new section after "Presentation 2" or "Presentation 3":
        ## Expressing Desire: хотіти

    > [!observe] Pattern Discovery
    > - Я **хочу** пити. (I want to drink.)
    > - Він **хоче** спати. (He wants to sleep.)

    ### хотіти — To Want

    | Person | хотіти | IPA | Example |
    |---|---|---|---|
    | я | хочу | /ˈxɔtʃu/ | Я хочу їсти. |
    | ти | хочеш | /ˈxɔtʃɛʃ/ | Ти хочеш кави? |
    | ... | ... | ... | ... |
    2.  **Rename Headers:** Change "Presentation 2" to "Expressing Obligation", "Presentation 3" to "Permission", etc.

### Vocabulary: Fix Missing Items

**What to fix:**
1.  Update `vocabulary/24-can-must-want-modals.yaml` to include: `могти`, `вміти`, `хотіти`, `мусити`, `треба`, `потрібно`, `можна`, `не можна`, `варто`, `слід`.

### Expected Overall After Fixes
With the missing content restored and headers fixed, Coherence and Pedagogy will rise to 9/10.

## Verification Summary

- Content lines read: 250+
- Activity items checked: 45
- Ukrainian sentences verified: 60+
- IPA transcriptions checked: 25+
- Issues found: 3 (1 Critical)
- Naturalness score recommendation: 10/10 (The existing text is natural, just incomplete)

## Verdict

**FAIL**

The module is missing the entire "Want" (`хотіти`) section despite promising it in the title and summary. This is a critical content gap that must be filled before approval.