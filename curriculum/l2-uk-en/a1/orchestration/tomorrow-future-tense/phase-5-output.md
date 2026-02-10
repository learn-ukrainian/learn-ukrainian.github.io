I will locate and read the required files for the "Tomorrow - Future Tense" module (A1-22) to perform the critical deep review.
I will use `glob` to verify the file paths and checking for the existence of the research file, then I will read all the required files.
I will list the contents of `curriculum/l2-uk-en/a1` to identify the correct file names and paths.
I will list the `curriculum/l2-uk-en/a1/research` directory to check for the research file, and then I will read the content, activities, vocabulary, plan, and meta files for the module.
I will read the content, activities, vocabulary, plan, meta, and research files for the "Tomorrow - Future Tense" module in parallel.
I will write the review for the "Tomorrow - Future Tense" module, identifying the issues with undeclared vocabulary in the activities and content, and providing a specific fix plan to remove these items and improve the module's coherence and beginner safety.

```
===REVIEW_START===
# Рецензія: Tomorrow - Future Tense

**Level:** A1 | **Module:** 22
**Overall Score:** 8.8/10
**Status:** PASS
**Reviewed:** 2026-02-09

## Plan Verification

```
Plan-Content Alignment: [PASS]
- Sections: [all present]
- Vocabulary: [8/8 required, 6/6 recommended present]
- Grammar scope: [clean]
- Objectives: [all covered]
```

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 9/10 | <7 | Clear, logical flow; warm tone. |
| 2 | Coherence | 9/10 | <7 | Connects well to Past Tense (M21). |
| 3 | Relevance | 10/10 | <7 | Future plans are essential for communication. |
| 4 | Educational | 10/10 | <7 | Explanation of `буду` + infinitive is crystal clear. |
| 5 | Language | 9/10 | <8 | Natural examples. |
| 6 | Pedagogy | 8/10 | <7 | Introduction of `маю намір` without vocabulary support adds unnecessary load. |
| 7 | Immersion | 9/10 | <6 | Good usage of Ukrainian in examples and dialogues. |
| 8 | Activities | 7/10 | <7 | `group-sort` activity contains 4 undeclared/unknown words. |
| 9 | Richness | 9/10 | <6 | Cultural notes (songs, appointments) are excellent. |
| 10 | Beginner Safety | 8/10 | <7 | Safe generally, but "Levels of Certainty" activity risks confusion with unknown words. |
| 11 | LLM Fingerprint | 9/10 | <7 | Very little fluff; structured well. |
| 12 | Linguistic Accuracy | 9/10 | <9 | No major errors found. |

**Weighted Overall:** (13.5 + 9.0 + 10.0 + 12.0 + 9.9 + 9.6 + 9.0 + 9.1 + 8.1 + 10.4 + 9.0 + 13.5) / 14.0 = **8.8/10**

## Auto-Fail Checklist Results

- Russianisms: [CLEAN]
- Calques: [CLEAN]
- Grammar scope: [CLEAN]
- Activity errors: [Undeclared vocabulary in group-sort]
- Beginner safety: 4/5 (Confusion in one activity)

## Critical Issues Found

### Issue 1: Undeclared Vocabulary in Activities
- **Location**: `activities/22-tomorrow-future-tense.yaml` / `group-sort`
- **Original**: `гарантую`, `мабуть`, `можливо`
- **Problem**: These words appear in the sorting activity but are NOT taught in the module, NOT in the vocabulary list, and NOT in the plan.
- **Fix**: Remove them to strictly test taught concepts.

### Issue 2: Vocabulary Bloat (Content)
- **Location**: `content` / Presentation: Plans and Intentions
- **Original**: `Я маю намір почати завтра.`
- **Problem**: `маю намір` (have an intention) is a specific phrase not listed in the plan or vocabulary. `планую` and `збираюся` are sufficient for A1.
- **Fix**: Remove to streamline learning.

### Issue 3: Unused Vocabulary Lemma
- **Location**: `vocabulary/22-tomorrow-future-tense.yaml`
- **Original**: `lemma: дієслово`
- **Problem**: The word `дієслово` appears in the YAML but is never used in the Ukrainian text of the module.
- **Fix**: Remove from vocabulary file.

## Fix Plan to Reach 9/10 (REQUIRED)

### Activities: 7/10 → 9/10

**What to fix:**
1. File `activities/22-tomorrow-future-tense.yaml`, Activity `Levels of Certainty` (`group-sort`):
   - Remove `гарантую` from "Very Certain".
   - Remove `мабуть` and `можливо` from "Less Certain".
   - Remove `маю намір` from "Very Certain" (see Pedagogy fix).
   - **Why**: Ensures students are tested ONLY on what they learned.
2. File `activities/22-tomorrow-future-tense.yaml`, Activity `Planning Expressions` (`fill-in`):
   - Remove item: `sentence: Я ___ вивчити три мови. (I intend...)`
   - **Why**: Removes the `маю намір` phrase which is being cut.

**Expected score after fix:** 9/10

### Pedagogy: 8/10 → 9/10

**What to fix:**
1. File `22-tomorrow-future-tense.md`, Section "Presentation: Plans and Intentions":
   - Remove line: `- **маю намір** — I intend to`
   - Remove line: `- Я **маю намір** почати завтра. (I intend to start tomorrow.)`
2. File `22-tomorrow-future-tense.md`, Section "Examples in Context":
   - Remove line: `- Вона **має намір** вивчити три мови. (She intends to learn three languages.)`
   - **Why**: Reduces cognitive load by focusing on high-frequency synonyms (`планую`, `збираюся`) required by the plan.

**Expected score after fix:** 9/10

### Vocabulary Cleanup

**What to fix:**
1. File `vocabulary/22-tomorrow-future-tense.yaml`:
   - Remove item `lemma: дієслово`.
   - **Why**: Unused in content.

### Projected Overall After Fixes

```
(13.5 + 9.0 + 10.0 + 12.0 + 9.9 + 10.8 + 9.0 + 11.7 + 8.1 + 10.4 + 9.0 + 13.5) / 14.0 = 9.06/10
```

## Verification Summary

- Content lines read: 188
- Activity items checked: 35
- Ukrainian sentences verified: ~45
- IPA transcriptions checked: 20
- Issues found: 3 (Vocabulary related)
- Naturalness score recommendation: 10/10

## Verdict

**PASS**

The module is structurally sound, culturally rich, and pedagogically strong. The only issues are related to vocabulary hygiene (undeclared words in activities and one phrase `маю намір` that adds unnecessary complexity). Implementing the fix plan will bring this to a polished 9/10 state.

===REVIEW_END===
```
