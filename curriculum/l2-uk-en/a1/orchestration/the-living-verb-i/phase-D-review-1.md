# Рецензія: The Living Verb I

**Level:** A1 | **Module:** 6
**Overall Score:** 9.6/10
**Status:** PASS
**Reviewed:** 2026-02-20

## Plan Verification

- Plan-Content Alignment: PASS
- Sections: PASS (All sections present)
- Vocabulary: PASS (All required words present; "recommended" words used effectively)
- Grammar scope: PASS (Strictly follows A1 constraints)
- Objectives: PASS (Objectives met)

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 10/10 | <7 | Excellent "Patient Tutor" persona; metaphors like "frozen world" vs "living world" are highly effective. |
| 2 | Coherence | 10/10 | <7 | Logical flow from concepts to examples to practice. |
| 3 | Relevance | 10/10 | <7 | Focuses on high-frequency daily actions; practical. |
| 4 | Educational | 10/10 | <7 | Clear explanations; "Master Key" concept empowers learners. |
| 5 | Language | 10/10 | <8 | Correct Ukrainian; natural examples; good use of IPA. |
| 6 | Pedagogy | 9/10 | <7 | Strong scaffolding. Deduction for missing stress markers on "писати" conjugation despite mentioning the shift. |
| 7 | Immersion | 10/10 | <6 | Appropriate for A1.1 (heavy English scaffolding). |
| 8 | Activities | 9/10 | <7 | Good variety. Deduction for using "книгу" (accusative) in an activity despite explicit text promise to avoid it. |
| 9 | Richness | 9/10 | <6 | Good cultural context (Ivan Fedorovych, proverbs). |
| 10 | Beginner Safety | 9/10 | <7 | Generally very safe. Warning about "Я читати" is great. "Would I continue?": 5/5. |
| 11 | LLM Fingerprint | 9/10 | <7 | Very low fingerprint; voice feels distinct and curated. |
| 12 | Linguistic Accuracy | 10/10 | <9 | No Russianisms or errors found. |

**Weighted Overall:** 9.6/10

## Auto-Fail Checklist Results

- Russianisms: CLEAN
- Calques: CLEAN
- Grammar scope: CLEAN
- Activity errors: 1 minor issue (Accusative leak)
- Beginner safety: 5/5

## Critical Issues Found

### Issue 1: Activity Content Leak (Beginner Safety)
- **Location**: `activities/the-living-verb-i.yaml` (True/False item)
- **Original**: `statement: «Ми читає книгу» — це правильне речення.`
- **Problem**: The content text explicitly states: *"If we used a feminine word like **книга** (book), it would change to **книгу**. But we aren't ready for that headache yet!"* Using `книгу` in the activity contradicts this promise and exposes the learner to unexplained grammar (Accusative case).
- **Fix**: Change `книгу` to a masculine inanimate noun like `журнал` or `текст` to maintain the "Safe Harbor".

### Issue 2: Missing Visual Scaffolding for Stress Shift
- **Location**: `content.md` / Section "Примітка про «Писати»"
- **Original**:
  ```markdown
  *   **Я пишу.** (I write.) — *Note the stress shift!*
  *   **Ти пишеш.**
  *   **Він пише.**
  ...
  ```
- **Problem**: The text correctly identifies the stress shift, but visually the learner cannot *see* it in the list because there are no stress marks on `пишеш`, `пише`, etc. A beginner might assume the stress returns to the first syllable or stays on the second.
- **Fix**: Add stress markers (bolding or accents) to the conjugated forms to guide pronunciation.

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| Act | «Ми читає книгу» | «Ми читає журнал» | Pedagogy/Scope |

## Beginner Safety Audit

"Would I Continue?" Test: 5/5
- Overwhelmed? No
- Instructions clear? Yes
- Quick wins? Yes
- Ukrainian scary? No
- Come back tomorrow? Yes

## Strengths
- **Metaphors**: The "sleeping tail" (-ти) and "Master Key" metaphors are excellent mnemonic devices.
- **Cultural Depth**: Connecting the verb "to read" to the 1574 "Apostol" is a fantastic touch that elevates the lesson.
- **Tone**: The "Patient Tutor" persona is perfectly executed—supportive, clear, and encouraging.

## Fix Plan to Reach 10/10

### Pedagogy: 9/10 → 10/10
**What to fix:**
1. Section "Примітка про «Писати»": Add bolding to stressed vowels in the conjugation list.

### Activities: 9/10 → 10/10
**What to fix:**
1. Activity `true-false`: Replace `книгу` with `журнал`.

## Verification Summary

- Content lines read: ~200
- Activity items checked: 82
- Ukrainian sentences verified: ~40
- IPA transcriptions checked: ~25
- Issues found: 2

## Verdict

**PASS**

The module is excellent. It is engaging, culturally rich, and linguistically accurate. The "Safe Harbor" strategy is largely successful, with only one minor leak in the activities regarding the accusative case. The fix is trivial. This is high-quality A1 content.