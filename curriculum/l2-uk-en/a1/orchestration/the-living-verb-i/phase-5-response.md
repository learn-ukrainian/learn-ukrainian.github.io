# Рецензія: The Living Verb I

**Level:** A1 | **Module:** 06
**Overall Score:** 8.6/10
**Status:** FAIL (Requires Fixes)
**Reviewed:** 2026-02-08

## Plan Verification

```
Plan-Content Alignment: FAIL
- Sections: PASS (All sections present)
- Vocabulary: FAIL (YAML vocabulary list contains only 10 items, while content teaches ~20+ verbs. Missing core verbs: читати, писати, працювати, гуляти, грати, думати, слухати, розуміти, знати)
- Grammar scope: FAIL (Dialogue uses Second Conjugation verb 'любити' in a First Conjugation module; Activity tests 'робити' which text explicitly delays to M08)
- Objectives: PASS
```

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 9/10 | <7 | Strong cultural hooks (Hermione, Barista) and engaging tone. |
| 2 | Coherence | 9/10 | <7 | Logical flow from pronouns to verbs to practice. |
| 3 | Relevance | 8/10 | <7 | High-frequency verbs, but 'робити' usage in activity contradicts text advice. |
| 4 | Educational | 8/10 | <7 | Clear explanations of conjugation, but 'Aspect' note might be too early/abstract (minor). |
| 5 | Language | 9/10 | <8 | Natural phrasing, good examples. |
| 6 | Pedagogy | 7/10 | <7 | **Major Issue**: Introduces II conjugation 'любити' in dialogue without explanation; tests 'робити' after saying "wait for M08". |
| 7 | Immersion | 10/10 | <6 | High immersion level (68%), good use of Ukrainian examples. |
| 8 | Activities | 8/10 | <7 | Good variety, but match-up contains the 'робити' consistency error. |
| 9 | Richness | 8/10 | <6 | Good cultural insight and "Did You Know" boxes. |
| 10 | Beginner Safety | 9/10 | <7 | Friendly tone, reassuring ("Ukrainian comes alive"). |
| 11 | LLM Fingerprint | 9/10 | <7 | Voice feels curated and specific, not generic. |
| 12 | Linguistic Accuracy | 9/10 | <9 | IPA and grammar generally correct. |

**Weighted Overall:** (9*1.5 + 9*1.0 + 8*1.0 + 8*1.2 + 9*1.1 + 7*1.2 + 10*1.0 + 8*1.3 + 8*0.9 + 9*1.3 + 9*1.0 + 9*1.5) / 14.0 = **8.58/10**

## Auto-Fail Checklist Results

- Russianisms: [CLEAN]
- Calques: [CLEAN]
- Grammar scope: **FAIL** (Use of 'любити' - II conjugation; Use of 'робити' in activity)
- Activity errors: **FAIL** (Match-up includes 'робити' which text says to avoid)
- Beginner safety: 5/5

## Critical Issues Found

### Issue 1: Pedagogy/Scope Violation (Dialogue)
- **Location**: Section "Mini-Dialogue 2: Вдома"
- **Original**: "Я теж **люблю** парк."
- **Problem**: The verb `любити` (to love) is a **Second Conjugation** verb (любить). This module explicitly teaches **First Conjugation** (-ати/-яти) only. Using a different conjugation pattern in the example text confuses the learner and breaks the "logical pattern" promise made in the intro.
- **Fix**: Change to a First Conjugation verb or a nominal phrase. Suggested: "Я **знаю** цей парк." (I know this park) or "Я теж **гуляю** там." (I also walk there).

### Issue 2: Internal Consistency (Activity)
- **Location**: Activity `match-up` (Infinitive to English)
- **Original**: `left: робити / right: to do/make`
- **Problem**: The "Pro Tip" in the text explicitly says: "The verb робити... is tricky! ... We learn that in Module 08. For now, use читаю, граю...". Testing `робити` immediately after this instruction creates cognitive dissonance and sets the student up for failure/confusion regarding the conjugation pattern.
- **Fix**: Replace `робити` with a First Conjugation verb taught in the lesson, e.g., `снідати` (to have breakfast) or `чекати` (to wait).

### Issue 3: Vocabulary File Incompleteness
- **Location**: `vocabulary/06-the-living-verb-i.yaml`
- **Original**: List contains only 10 items (`вечеряти`, `вільний`, etc.).
- **Problem**: The content teaches core verbs like `читати`, `писати`, `працювати`, `гуляти`, `грати`, `думати`, `слухати`, `розуміти`, `знати`. These are MISSING from the vocabulary file.
- **Fix**: Populate the YAML file with all verbs taught in the module. (This is a meta-fix, but critical for the project structure).

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| Dialogue 2 | Я теж люблю парк. | Я теж гуляю там. | Scope (II Conjugation) |

## Beginner Safety Audit

"Would I Continue?" Test: 5/5
- Overwhelmed? Pass
- Instructions clear? Pass
- Quick wins? Pass (Conjugation pattern is easy to grasp)
- Ukrainian scary? Pass (Reassuring tone)
- Come back tomorrow? Pass

Emotional beats: 5 found
- Welcome: "Today you unlock your first set of Ukrainian action verbs..."
- Curiosity: "Did You Know? ... master key to Ukrainian action."
- Quick wins: "One verb — працюєш — and they know your whole vibe."
- Encouragement: "Ukrainian verb conjugations are incredibly logical."
- Progress: "You've unlocked First Conjugation verbs!"

## Strengths
- **Cultural Hooks**: The "Barista" example explains *why* the language works the way it does (efficiency/context), which is excellent for adult learners.
- **Phonetic Focus**: Good attention to the rhythm and melody of the verbs.
- **Clarity**: The explanation of the -ва- drop (`працювати`) is handled with a good mnemonic ("shy syllable").

## Fix Plan to Reach 9/10

### Pedagogy: 7/10 → 9/10

**What to fix:**
1.  **Section "Mini-Dialogue 2: Вдома"**:
    - Change: "Я теж **люблю** парк." → "Я теж **гуляю** там." (or "Я теж **знаю** цей парк.")
    - *Why*: Removes the confusing Second Conjugation verb, reinforcing the module's First Conjugation focus.
2.  **Activity `match-up`**:
    - Change: Pair `робити` / `to do/make` → `снідати` / `to have breakfast`
    - *Why*: Aligns activity with the text's advice to wait on `робити` (Module 08).
3.  **Vocabulary YAML**:
    - Action: Add missing core verbs (`читати`, `писати`, `працювати`, `грати`, `думати`, `слухати`, `розуміти`, `знати`, `чекати`) to `vocabulary/06-the-living-verb-i.yaml`.

**Expected score after fix:** 9/10

### Relevance: 8/10 → 9/10

**What to fix:**
1.  **Activity `match-up`**: (See above). Removing the contradiction improves relevance and trust in the guide.

**Expected score after fix:** 9/10

### Projected Overall After Fixes

`(9*1.5 + 9*1.0 + 9*1.0 + 8*1.2 + 9*1.1 + 9*1.2 + 10*1.0 + 9*1.3 + 8*0.9 + 9*1.3 + 9*1.0 + 9*1.5) / 14.0`
= `(13.5 + 9 + 9 + 9.6 + 9.9 + 10.8 + 10 + 11.7 + 7.2 + 11.7 + 9 + 13.5) / 14`
= `124.9 / 14`
= **8.92/10** (Rounds to 9.0)

## Verification Summary

- Content lines read: ~140
- Activity items checked: 43
- Ukrainian sentences verified: ~30
- IPA transcriptions checked: ~20
- Issues found: 3 (1 Scope, 1 Activity, 1 Meta)
- Naturalness score recommendation: 10/10

## Verdict

**FAIL**

The module is excellent in tone and explanation but fails on strict pedagogical scope consistency. Introducing a Second Conjugation verb (`любити`) in a First Conjugation lesson and testing a verb (`робити`) explicitly marked as "learn later" confuses the learner and breaks the promise of logical structure. These must be fixed to pass.
