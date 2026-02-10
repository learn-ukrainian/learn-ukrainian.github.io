# Рецензія: Numbers & Money

**Level:** A1 | **Module:** 17
**Overall Score:** 8.7/10
**Status:** FAIL
**Reviewed:** 2026-02-08

## Plan Verification

```
Plan-Content Alignment: [PASS]
- Sections: [all present]
- Vocabulary: [8/8 required present; 'решта' used instead of 'здача' (better)]
- Grammar scope: [clean - introduces genitive plural contextually for numbers, appropriate for topic]
- Objectives: [all covered]
```

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 10/10 | <7 | Excellent pop culture reference (S.T.A.L.K.E.R.) and historical context. |
| 2 | Coherence | 10/10 | <7 | Logical flow from digits to tens to shopping. |
| 3 | Relevance | 10/10 | <7 | Highly practical shopping skills. |
| 4 | Educational | 10/10 | <7 | Clear explanation of the 1/2-4/5+ agreement rule. |
| 5 | Language | 9/10 | <8 | Ukrainian is natural; minor IPA inconsistency. |
| 6 | Pedagogy | 10/10 | <7 | Good mix of rote learning and practical application. |
| 7 | Immersion | 9/10 | <6 | Strong cultural integration (banknotes, history). |
| 8 | Activities | 6/10 | <7 | **FAIL**: Extensive "LLM Fingerprint" in question phrasing (broken English). |
| 9 | Richness | 10/10 | <6 | Word count met, engaging sidebars. |
| 10 | Beginner Safety | 10/10 | <7 | "Pattern discovery" boxes reduce overwhelm. |
| 11 | LLM Fingerprint | 6/10 | <7 | **FAIL**: Repetitive, unnatural use of "accurately" and "exactly" in quiz questions. |
| 12 | Linguistic Accuracy | 9/10 | <9 | Minor IPA variance. |

**Weighted Overall:** 8.7/10

## Auto-Fail Checklist Results

- Russianisms: [CLEAN]
- Calques: [CLEAN]
- Grammar scope: [CLEAN]
- Activity errors: [FAIL - Ungrammatical English questions]
- Beginner safety: 5/5

## Critical Issues Found

### Issue 1: Robotic/Broken English in Activities (LLM Fingerprint)
- **Location**: `activities/17-numbers-and-money.yaml` (Multiple lines)
- **Original**:
    - Line 98: "Which number has accurately a gender distinction?"
    - Line 125: "What does exactly the Ukrainian word «готівка» mean?"
    - Line 348: "What is the meaning of accurately «решта»?"
    - Line 88: "What does «Скільки коштує?» accurately mean in English?"
- **Problem**: The words "accurately" and "exactly" are inserted mechanically, often breaking English grammar or creating unnatural phrasing. This is a clear hallucination/pattern artifact.
- **Fix**: Remove these filler words. "What does «готівка» mean?" is sufficient.

### Issue 2: IPA Inconsistency
- **Location**: `17-numbers-and-money.md` Line 12 vs `vocabulary/17-numbers-and-money.yaml`
- **Original**: Content uses `/ˈɦrɪwnʲɑ/` (using [w]); Vocabulary uses `/ˈɦrɪʋnʲa/` (using [ʋ]).
- **Problem**: Inconsistent transcription of letter 'в'.
- **Fix**: Standardize to `/ˈɦrɪʋnʲa/` (using [ʋ]) across both files.

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| 12 | /ˈɦrɪwnʲɑ/ | /ˈɦrɪʋnʲa/ | IPA Consistency |

## Beginner Safety Audit

"Would I Continue?" Test: 5/5
- Overwhelmed? [No]
- Instructions clear? [Yes]
- Quick wins? [Yes - S.T.A.L.K.E.R. reference is a win]
- Ukrainian scary? [No - patterns explained well]
- Come back tomorrow? [Yes]

Emotional beats: 5 found
- Welcome: "You're at a market in Kyiv."
- Curiosity: "S.T.A.L.K.E.R." reference.
- Quick wins: "Pattern discovery" (11-19).
- Encouragement: "Ukrainian players know the real treasure..."
- Progress: "You can now count, ask prices, and shop confidently..."

## Strengths
- **Cultural Hook**: The S.T.A.L.K.E.R. reference (Line 72) is brilliant for the target audience.
- **Visuals**: The explanation of "Hryvnia Symbol" and banknotes adds great depth.
- **Clarity**: The 1/2-4/5+ rule is explained simply without overwhelming grammatical jargon.

## Fix Plan to Reach 9/10

### Activities & LLM Fingerprint: 6/10 → 9/10

**What to fix:**
1.  **Open `activities/17-numbers-and-money.yaml`**:
2.  **Bulk Remove**: Delete the words "accurately" and "exactly" from ALL `question` fields.
    -   Change "How do you accurately say exactly..." -> "How do you say..."
    -   Change "Which number has accurately a gender distinction?" -> "Which number has a gender distinction?"
    -   Change "What does exactly the Ukrainian word..." -> "What does the Ukrainian word..."
    -   Check lines: 61, 88, 98, 116, 125, 153, 162, 294, 303, 321, 348.

### Linguistic Accuracy: 9/10 → 10/10

**What to fix:**
1.  **Open `17-numbers-and-money.md`**:
2.  Line 12: Change `/ˈɦrɪwnʲɑ/` to `/ˈɦrɪʋnʲa/`.

### Projected Overall After Fixes

```
(10*1.5 + 10*1.0 + 10*1.0 + 10*1.2 + 10*1.1 + 10*1.2 + 9*1.0 + 9*1.3 + 10*0.9 + 10*1.3 + 10*1.0 + 10*1.5) / 14.0 = 9.8/10
```

## Verification Summary

- Content lines read: 236
- Activity items checked: 43
- Ukrainian sentences verified: ~25
- IPA transcriptions checked: 30+
- Issues found: 2 (1 systemic in activities, 1 minor IPA)
- Naturalness score recommendation: 10/10 (Content is natural, only English instruction in activities is flawed)

## Verdict

**FAIL**

The content is excellent, but the **Activities** file is plagued by a systemic "LLM Fingerprint" error where the words "accurately" and "exactly" are inserted into questions, often resulting in broken English syntax (e.g., "What does exactly the Ukrainian word..."). This makes the quiz feel robotic and unpolished. This must be scrubbed before passing.