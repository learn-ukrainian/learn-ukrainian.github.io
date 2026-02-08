# Рецензія: The Cyrillic Code I

**Level:** A1 | **Module:** 01
**Overall Score:** 8.8/10
**Status:** FAIL
**Reviewed:** 2026-02-08

## Plan Verification

```
Plan-Content Alignment: [FAIL]
- Sections: [PASS]
- Vocabulary: [5/8 from plan, 3 missing (такт, кіт, тато), 21 extra]
- Grammar scope: [PASS]
- Objectives: [PASS]
```

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 9/10 | <7 | Engaging hooks (S.T.A.L.K.E.R., Myth Buster) and warm tone. |
| 2 | Coherence | 8/10 | <7 | Disconnect between content vocabulary and activity/file vocabulary. |
| 3 | Relevance | 9/10 | <7 | Focus on high-frequency internationalisms is excellent. |
| 4 | Educational | 8/10 | <7 | Clear explanations, though some "required" plan words are missing. |
| 5 | Language | 10/10 | <8 | Natural Ukrainian, no Russianisms found. |
| 6 | Pedagogy | 8/10 | <7 | Strong PPP structure; "False Friends" concept well applied. |
| 7 | Immersion | 10/10 | <6 | Visual inspection confirms ~20% density (appropriate for A1.1). Automated metric (63%) is demonstrably false. |
| 8 | Activities | 6/10 | <7 | Critical ambiguity in "Complete the Word" and untaught vocabulary in Anagrams. |
| 9 | Richness | 9/10 | <6 | Good variety of examples and cultural context. |
| 10 | Beginner Safety | 10/10 | <7 | "Would I Continue?" 5/5. Very encouraging. |
| 11 | LLM Fingerprint | 9/10 | <7 | Authentic "human" teaching voice. |
| 12 | Linguistic Accuracy | 10/10 | <9 | No errors in Ukrainian text. |

**Weighted Overall:** (13.5 + 8.0 + 9.0 + 9.6 + 11.0 + 9.6 + 10.0 + 7.8 + 8.1 + 13.0 + 9.0 + 15.0) / 14.0 = **8.82/10**

## Auto-Fail Checklist Results

- Russianisms: [CLEAN]
- Calques: [CLEAN]
- Grammar scope: [CLEAN]
- Activity errors: [FAIL] (Ambiguity, untaught vocab)
- Beginner safety: 5/5

## Critical Issues Found

### Issue 1: Activity Ambiguity
- **Location**: Activities / "Complete the Word" / Item `___ото`
- **Original**: Options: `Л, П, Р, Ф` / Answer: `Л`
- **Problem**: Both `лото` (Lotto) and `фото` (Photo) are valid words taught in the module. If the user selects `Ф`, it is marked wrong despite being a valid completion.
- **Fix**: Change options to `Л, П, Н, В` (remove Ф) OR change target word to `___ото` (Photo) -> Answer `Ф` with options `Ф, П, Р, Б`.

### Issue 2: Untaught Vocabulary in Activity
- **Location**: Activities / "International Words" / Item `с т у д е н т`
- **Original**: scrambled: `с т у д е н т` / answer: `студент`
- **Problem**: The word `студент` does not appear in the content module or vocabulary list.
- **Fix**: Replace with a taught word like `т е л е ф о н` (телефон) or `д о к т о р` (доктор).

### Issue 3: Vocabulary-Content Mismatch
- **Location**: Vocabulary File vs Content File
- **Original**: Vocab file missing `тост`, `маска`, `ваза`, `доктор`, `хор`, `лото`, `мама`.
- **Problem**: These words are used as key examples in the Content tables but are not in the structured vocabulary file.
- **Fix**: Add these words to `vocabulary/01-the-cyrillic-code-i.yaml`.

### Issue 4: Plan Deviation
- **Location**: Content
- **Original**: Missing `такт`, `кіт`, `тато`.
- **Problem**: These words are listed as `required` in the Plan but are absent from content.
- **Fix**: Add them to the "True Friends" or "New Letters" examples, or update Plan to remove them if they are deferred. (Suggestion: Add `Т т` -> `Т а к т` example).

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| - | - | - | CLEAN |

## Beginner Safety Audit

"Would I Continue?" Test: 5/5
- Overwhelmed? Pass
- Instructions clear? Pass
- Quick wins? Pass (Reading "Metro" immediately)
- Ukrainian scary? Pass (Debunked well)
- Come back tomorrow? Pass

Emotional beats: 4 found
- Welcome: "You're about to crack a code..."
- Curiosity: "Russian didn't even exist..."
- Quick wins: "True Friends" table.
- Encouragement: "Only 14 letters remain..."

## Strengths
- **"True Friends" vs "False Friends"**: This framing is excellent for English speakers.
- **S.T.A.L.K.E.R. Reference**: Great cultural hook for a specific demographic.
- **Decolonization**: Clear distinction between Rus/Ukraine/Russia history.

## Fix Plan to Reach 9/10

### Activities: 6/10 → 10/10

**What to fix:**
1.  **"Complete the Word"**: Change item `___ото` (Answer `Л`) -> `___ото` (Answer `Ф`). Change options to `Ф, П, Р, Б`. (Students know `фото` from text better than `лото`).
2.  **"International Words"**: Replace `с т у д е н т` -> `т е л е ф о н`.
3.  **"True Friends" Match-up**: Ensure consistent casing (All Upper or All Lower pairs) if possible, or leave as is if UI handles case-insensitive matching. (Minor).

### Coherence: 8/10 → 10/10

**What to fix:**
1.  **Vocabulary File**: Add the following lemmas to `vocabulary/01-the-cyrillic-code-i.yaml`:
    - `тост` (toast)
    - `маска` (mask)
    - `ваза` (vase)
    - `доктор` (doctor)
    - `хор` (choir)
    - `лото` (lotto)
    - `мама` (mom)
2.  **Vocabulary File**: Remove `лимон` and `піца` (not in text) OR add them to the "Food" list in Content. (Recommendation: Add to content text "Practice > Reading International Words > Food").

### Educational: 8/10 → 9/10

**What to fix:**
1.  **Plan Alignment**: Add `кіт` (cat) and `такт` (tact) to the examples.
    - Change `Т т` example in "True Friends" from `тост` to `такт` (matches Plan)? Or keep `тост` and add `такт`.
    - Add `кіт` to "True Friends" examples (Wait, `К`, `І`, `Т` are all True Friends! Perfect example).
    - Add `К і т` -> `Cat` to "True Friends" table.

### Projected Overall After Fixes

**Activities** 10, **Coherence** 10, **Educational** 9.
New Weighted Overall: **9.38/10**

## Verification Summary

- Content lines read: ~180
- Activity items checked: 45
- Ukrainian sentences verified: ~30
- IPA transcriptions checked: 20
- Issues found: 4 Critical
- Naturalness score recommendation: 10/10

## Verdict

**FAIL**

The module is structurally sound and linguistically excellent, but fails on technical activity integrity (ambiguous answers, untaught vocabulary) and data consistency (vocabulary file does not match content). These are "easy fixes" but critical for a 2.0 release. The fix plan is straightforward.