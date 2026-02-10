# Рецензія: Богдан Хмельницький: Гетьман-державотворець

**Level:** C1-BIO | **Module:** 22
**Overall Score:** 8.8/10
**Status:** FAIL
**Reviewed:** 2026-02-09

## Plan Verification

```
Plan-Content Alignment: FAIL
- Sections: PASS (All outline points covered)
- Vocabulary: 2/3 required words found. MISSING: "Гетьманщина" (Critical term required by plan).
- Grammar scope: PASS
- Objectives: PASS
```

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 10/10 | <7 | Powerful narrative, excellent rhetorical flow. |
| 2 | Coherence | 10/10 | <7 | Logical progression from biography to analysis. |
| 3 | Relevance | 10/10 | <7 | Central figure of Ukrainian history, crucial for C1. |
| 4 | Educational | 10/10 | <7 | Deep insights into state-building and diplomacy. |
| 5 | Language | 8/10 | <8 | Several euphony violations ("у унікальній", "у 1664"). |
| 6 | Pedagogy | 9/10 | <7 | Strong seminar approach, good activities. |
| 7 | Immersion | 10/10 | <6 | 100% Ukrainian, authentic feel. |
| 8 | Activities | 10/10 | <7 | Excellent C1-level tasks (comparative, critical analysis). |
| 9 | Richness | 10/10 | <6 | 5000+ words, dense with history. |
| 10 | Beginner Safety | 8/10 | <7 | Dense text, but appropriate for C1. |
| 11 | LLM Fingerprint | 9/10 | <7 | Feels curated and specific. |
| 12 | Linguistic Accuracy | 8/10 | <9 | IPA stress error in vocabulary. |

**Weighted Overall:** (15 + 10 + 10 + 12 + 8.8 + 10.8 + 10 + 13 + 9 + 10.4 + 9 + 12) / 14.0 = **9.28/10**
*Correction*: Despite high weighted score, the **Plan Alignment Failure** and **Linguistic Accuracy** issues (<9) require a mandatory fix loop. I am overriding the status to FAIL to ensure these technical fixes are applied.

## Auto-Fail Checklist Results

- Russianisms: [CLEAN]
- Calques: [CLEAN]
- Grammar scope: [CLEAN]
- Activity errors: [CLEAN]
- Beginner safety: 5/5

## Critical Issues Found

### Issue 1: Missing Required Vocabulary
- **Location**: `vocabulary/bohdan-khmelnytskyy.yaml`
- **Original**: (Missing)
- **Problem**: Plan explicitly requires `Гетьманщина` (Hetmanate) as a vocabulary item.
- **Fix**: Add entry for `Гетьманщина`.

### Issue 2: Euphony Violation (U/V rule)
- **Location**: Paragraph 1 (Intro) / Line ~5
- **Original**: "полягав у унікальній здатності"
- **Problem**: Hiatus "у у..." is hard to pronounce and violates euphony rules (after consonant `в`, before vowel `у`, use `в`).
- **Fix**: "полягав в унікальній здатності"

### Issue 3: Euphony Violation (Prepositions with dates)
- **Location**: Section "Останні роки" / Paragraph 3
- **Original**: "за легендою, у 1664 році"
- **Problem**: After vowel `ю`, before number starting with consonant `1` (тисяча), use `в`.
- **Fix**: "за легендою, в 1664 році"

### Issue 4: IPA Stress Error
- **Location**: Vocabulary item `суб'єктність`
- **Original**: `/subjekˈtnʲisʲtʲ/`
- **Problem**: Stress is placed incorrectly on the suffix `-ність`. Stress should be on the root/suffix boundary `є`. Also missing palatalization marker or syllable break nuance.
- **Fix**: `/subˈjɛktnʲisʲtʲ/`

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| Intro | "полягав у унікальній" | "полягав в унікальній" | Euphony |
| Late Yrs | "за легендою, у 1664" | "за легендою, в 1664" | Euphony |
| Vocab | `/subjekˈtnʲisʲtʲ/` | `/subˈjɛktnʲisʲtʲ/` | IPA Error |

## Beginner Safety Audit

"Would I Continue?" Test: 5/5
- Overwhelmed? No (C1 expectation met)
- Instructions clear? Yes
- Quick wins? Yes (Reading activities are segmented)
- Ukrainian scary? No (Appropriate density)
- Come back tomorrow? Yes

Emotional beats: 4 found
- Welcome: Strong patriotic intro.
- Curiosity: "History bite" about coffee.
- Quick wins: "History bite" box.
- Progress: Detailed timeline.

## Strengths
- **Narrative Power**: The text effectively positions Khmelnytskyy not just as a warrior, but as a sophisticated politician ("Machiavellian mind").
- **Vocabulary**: Rich, academic lexicon ("деміург", "суб'єктність", "легітимність").
- **Activities**: The comparison with Cromwell is a brilliant C1-level analytical task.

## Fix Plan to Reach 9/10 (REQUIRED)

### Language & Accuracy: 8/10 → 10/10

**What to fix:**
1.  **Vocabulary**: Add the missing item:
    ```yaml
    - lemma: Гетьманщина
      ipa: /ɦetʲˈmɑnʃt͡ʃɪnɐ/
      translation: Hetmanate
      pos: noun
      gender: f
      note: козацька держава
    ```
2.  **Vocabulary**: Fix IPA for `суб'єктність` -> `/subˈjɛktnʲisʲtʲ/`.
3.  **Content (Intro)**: Change "полягав у унікальній" to "полягав в унікальній".
4.  **Content (Late Years)**: Change "за легендою, у 1664" to "за легендою, в 1664".
5.  **Content (Late Years)**: Change "Коли у 1656" to "Коли в 1656" (Euphony: after vowel `и`).

### Projected Overall After Fixes

9.5/10

## Verification Summary

- Content lines read: ~200
- Activity items checked: 6
- Ukrainian sentences verified: ~80
- IPA transcriptions checked: 25
- Issues found: 4
- Naturalness score recommendation: 10/10

## Verdict

**FAIL**

Excellent content quality marred by minor but strict euphony violations and a missing required vocabulary item from the plan. Fix the euphony issues and add "Гетьманщина" to the vocabulary to pass.