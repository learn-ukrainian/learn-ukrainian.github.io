# Рецензія: Prepositions III

**Level:** A1 | **Module:** 30
**Overall Score:** 8.8/10
**Status:** FAIL (Needs Minor Fixes)
**Reviewed:** 2026-02-08

## Plan Verification

Plan-Content Alignment: [FAIL]
- Sections: [Missing explicit headers "Presentation 2", "Presentation 3", "Practice 2" defined in plan, though content is largely present.]
- Vocabulary: [PASS]
- Grammar scope: [PASS]
- Objectives: [PASS]

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 9/10 | <7 | Clear, welcoming tone, good use of humor and encouragement. |
| 2 | Coherence | 9/10 | <7 | Logical progression from Де -> Куди -> Звідки. |
| 3 | Relevance | 10/10 | <7 | Highly relevant daily survival phrases. |
| 4 | Educational | 9/10 | <7 | Good explanation of the case logic linked to questions. |
| 5 | Language | 8/10 | <8 | Minor naturalness issues with "є" in unjumble activities; "з школи" phonetic error. |
| 6 | Pedagogy | 9/10 | <7 | Effective PPP structure. |
| 7 | Immersion | 8/10 | <6 | Appropriate English scaffolding for A1 grammar. |
| 8 | Activities | 8/10 | <7 | "з школи" error in quiz; unnatural "є" in unjumble. |
| 9 | Richness | 8/10 | <6 | Good examples, but could use more varied contexts. |
| 10 | Beginner Safety | 9/10 | <7 | 5/5 on Safety Test. |
| 11 | LLM Fingerprint | 9/10 | <7 | No obvious AI artifacts. |
| 12 | Linguistic Accuracy | 8/10 | <9 | Phonetic error "з школи" (should be "зі школи"). |

**Weighted Overall:** (13.5 + 9.0 + 10.0 + 10.8 + 8.8 + 10.8 + 8.0 + 10.4 + 7.2 + 11.7 + 9.0 + 12.0) / 14.0 = **8.66/10**

## Auto-Fail Checklist Results

- Russianisms: [CLEAN]
- Calques: [CLEAN]
- Grammar scope: [CLEAN]
- Activity errors: [Issue found: "з школи" vs "зі школи"]
- Beginner safety: 5/5

## Critical Issues Found

### Issue 1: Phonetic Error (Euphony)
- **Location**: Activity `Which Preposition?`, Item 6
- **Original**: "з школи"
- **Problem**: In Ukrainian, the preposition `з` becomes `зі` before consonant clusters like `шк-` to maintain euphony (милозвучність). `з школи` is difficult to pronounce and linguistically incorrect.
- **Fix**: Change option to `зі школи`.

### Issue 2: Naturalness in Unjumble
- **Location**: Activity `Preposition Sentences`, Item 1 and 8
- **Original**: "Де ти зараз є" / "Вона зараз є вдома"
- **Problem**: While not strictly grammatically wrong, using the explicit copula `є` in these simple present tense location sentences is unnatural and redundant in standard neutral Ukrainian. A1 students are taught to omit "to be". Including it confuses the rule.
- **Fix**: Remove `є` from the word list and answer key.
    - Item 1: `Де ти зараз?`
    - Item 8: `Вона зараз вдома.`

### Issue 3: Missing Structure Headers
- **Location**: Content File
- **Original**: Missing `## Presentation 2` and `## Presentation 3` headers.
- **Problem**: The plan explicitly calls for these sections. While the content is somewhat integrated into `Examples in Context`, adhering to the plan structure helps maintain modular consistency.
- **Fix**: Add explicit headers or map `Examples in Context` to these sections more clearly.

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| Act-7 | з школи | зі школи | Phonetic/Grammar |
| Act-9 | Де ти зараз є | Де ти зараз | Naturalness |

## Beginner Safety Audit

"Would I Continue?" Test: 5/5
- Overwhelmed? [Pass]
- Instructions clear? [Pass]
- Quick wins? [Pass]
- Ukrainian scary? [Pass]
- Come back tomorrow? [Pass]

## Strengths
- Excellent conceptual breakdown of the Де/Куди/Звідки triad.
- Clear "Myth vs Fact" section that demystifies cases.
- Practical "Location vs Direction" pairs table.

## Fix Plan to Reach 9/10

### Linguistic Accuracy: 8/10 → 9/10

**What to fix:**
1. **Activity `30-prepositions-iii.yaml`**:
   - In `type: quiz`, `title: Which Preposition?`, `question: How is «Coming FROM school» translated?`:
     - Change option `text: з школи` to `text: зі школи`.
     - Update phonetic logic.

### Language & Naturalness: 8/10 → 9/10

**What to fix:**
1. **Activity `30-prepositions-iii.yaml`**:
   - In `type: unjumble`, `title: Preposition Sentences`:
     - Item 1: Remove `є` from `words` list. Update `answer` to `Де ти зараз`.
     - Item 8: Remove `є` from `words` list. Update `answer` to `Вона зараз вдома`.

### Plan-Content Alignment: Fail → Pass

**What to fix:**
1. **Content `30-prepositions-iii.md`**:
   - Rename `### Location vs Direction Pairs` to `## Presentation 2: Common Pairs`.
   - Rename `## Examples in Context` to `## Presentation 3: In the City`.

### Projected Overall After Fixes

(13.5 + 9 + 10 + 10.8 + 9.9 + 10.8 + 8 + 11.7 + 7.2 + 11.7 + 9 + 13.5) / 14 = 9.1

## Verification Summary

- Content lines read: 215
- Activity items checked: 55
- Ukrainian sentences verified: ~40
- IPA transcriptions checked: 10
- Issues found: 3
- Naturalness score recommendation: 9/10

## Verdict

**FAIL**

Requires specific fixes to Activity file (phonetics, naturalness) and Content file (structure) to meet the 9/10 standard and strictly follow Ukrainian euphony rules.