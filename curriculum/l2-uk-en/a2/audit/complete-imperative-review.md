# Рецензія: Complete Imperative

**Level:** A2 | **Module:** 23
**Overall Score:** 6.9/10
**Status:** FAIL
**Reviewed:** 2026-02-09

## Plan Verification

```
Plan-Content Alignment: [PASS]
- Sections: [all present]
- Vocabulary: [Mixed - core imperatives present, but weird hallucinated words in yaml]
- Grammar scope: [Standard A2 imperative]
- Objectives: [Met]
```

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 6/10 | <7 | Internal editing monologue left in student-facing text ("Wait, no: ...") |
| 2 | Coherence | 6/10 | <7 | Algorithm Step 1 says "Singular" but Examples use "Plural" endings (-уть/-ять) |
| 3 | Relevance | 9/10 | <7 | Imperative is highly relevant for A2. |
| 4 | Educational | 7/10 | <7 | Explanation of formation rules is confusing due to Singular/Plural mix-up. |
| 5 | Language | 6/10 | <8 | "Wait, no..." artifact; Vocabulary file contains `хаяти` (to criticize) instead of `хай` (let). |
| 6 | Pedagogy | 6/10 | <7 | Teaching explicit grammar algorithm that contradicts its own examples. |
| 7 | Immersion | 8/10 | <6 | Good mix of Ukrainian/English. |
| 8 | Activities | 9/10 | <7 | Activities are generally well-structured and relevant. |
| 9 | Richness | 9/10 | <6 | Good word count (1855 words) and cultural context (toasts). |
| 10 | Beginner Safety | 6/10 | <7 | The editing artifact destroys trust; confused grammar rules cause frustration. |
| 11 | LLM Fingerprint | 5/10 | <7 | "Wait, no..." is a classic LLM "thinking out loud" artifact printed to output. |
| 12 | Linguistic Accuracy | 8/10 | <9 | Mostly correct, except for the `хаяти`/`часть` vocab hallucinations. |

**Weighted Overall:** (6*1.5 + 6*1.0 + 9*1.0 + 7*1.2 + 6*1.1 + 6*1.2 + 8*1.0 + 9*1.3 + 9*0.9 + 6*1.3 + 5*1.0 + 8*1.5) / 14.0 = **6.9/10**

## Auto-Fail Checklist Results

- Russianisms: [List] `часть` (vocab file) - should be `частина`.
- Calques: [CLEAN]
- Grammar scope: [CLEAN]
- Activity errors: [CLEAN]
- Beginner safety: 2/5 (Overwhelmed by contradictory rules, confused by artifacts)

## Critical Issues Found

### Issue 1: Editing Artifact (Severity: Critical)
- **Location**: Line 191 / Section "Practice"
- **Original**: "5. дати (хай + він) -> **хай дасть** (Wait, no: **хай дасть** / **хай дає** depending on aspect). Correct: **Хай дає!**"
- **Problem**: The AI's internal reasoning ("Wait, no...") was printed into the final lesson. This is confusing and unprofessional.
- **Fix**: "5. дати (хай + він) -> **хай дає!**"

### Issue 2: Logical Contradiction in Grammar Rule (Severity: High)
- **Location**: Line 63 / Section "Step-by-Step"
- **Original**: "Крок 1: Візьміть дієслово та поставте його в 3-ю особу однини (він/вона/воно)."
- **Problem**: The instructions say "3rd Singular" (e.g., *говорить*), but the examples in Type 1 (Line 80) explicitly use "3rd Plural" endings (*говор**ять***, *пиш**уть***). The standard rule uses the 3rd person plural stem.
- **Fix**: Change "3-ю особу однини (він/вона/воно)" to "3-ю особу множини (вони)".

### Issue 3: Vocabulary Hallucinations (Severity: Medium)
- **Location**: `vocabulary/23-complete-imperative.yaml`
- **Items**:
    - `хаяти` ("to criticize") - The text teaches the particle `хай`. `Хаяти` is a different, colloquial/low-register verb not used in the text.
    - `часть` ("part") - Russianism. Should be `частина`.
    - `калька` ("tracing paper") - Not used in text.
- **Fix**: Remove these items. Ensure `хай` (particle) is properly listed (it is currently listed twice, once as `part` and once as `particle`).

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| 191 | (Wait, no: ... ) | [REMOVE] | Artifact |
| Vocab | хаяти | [REMOVE] | Hallucination |
| Vocab | часть | частина | Russianism |

## Beginner Safety Audit

"Would I Continue?" Test: 2/5
- Overwhelmed? **Pass** (Content length is fine)
- Instructions clear? **Fail** (Grammar rule contradicts examples)
- Quick wins? **Pass** (Simple commands are easy)
- Ukrainian scary? **Pass**
- Come back tomorrow? **Fail** (The "Wait, no" artifact makes the course look broken/untrusted)

Emotional beats: 4 found
- Welcome: "Ласкаво просимо..." (Intro)
- Curiosity: "Це не лише про 'накази'..." (Intro)
- Quick wins: 5 irregulars memorized (Section 4)
- Encouragement: "Ви вже знаєте..." (Summary)

## Strengths
- **Flowchart**: The Mermaid diagram is a great visual aid (once the text rule is fixed to match it).
- **Cultural Context**: The section on toasts ("Хай щастить") and the "Давай" vs "-мо" nuance is excellent.
- **Activity Volume**: 10 activities is a strong practice set.

## Fix Plan to Reach 9/10

### Experience & Language: 6/10 → 9/10

**What to fix:**
1.  **Line 191**: Delete the parenthetical "(Wait, no: **хай дасть** / **хай дає** depending on aspect). Correct: **Хай дає!**" and replace with just "**хай дає**".
2.  **Vocabulary File**: Delete `хаяти`, `часть`, `калька`, `вибачення`. Deduplicate `хай`.

### Pedagogy & Coherence: 6/10 → 9/10

**What to fix:**
1.  **Line 63**: Change "3-ю особу однини (він/вона/воно)" to "3-ю особу множини (вони)".
2.  **Line 81-83**: The examples `говорять`, `пишуть` will now align correctly with the "Step 1" instruction.

### Projected Overall After Fixes

With artifacts removed and grammar rules aligned, Language rises to 9/10, Pedagogy to 9/10, and Beginner Safety to 9/10.
Projected Score: **9.2/10**

## Verification Summary

- Content lines read: ~230
- Activity items checked: 10 types
- Ukrainian sentences verified: ~40
- IPA transcriptions checked: Vocabulary file scanned
- Issues found: 3 major (Artifact, Grammar Logic, Vocab Garbage)
- Naturalness score recommendation: 7/10 (until artifact fixed)

## Verdict

**FAIL**

The module contains a critical LLM artifact ("Wait, no...") visible to students and a fundamental pedagogical error where the grammar rule contradicts its own examples. The vocabulary file also contains hallucinations/Russianisms (`хаяти`, `часть`). These must be fixed before release.