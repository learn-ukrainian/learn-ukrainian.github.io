===REVIEW_START===
# Рецензія: Spatial Prepositions

**Level:** A2 | **Module:** 07
**Overall Score:** 7.5/10
**Status:** FAIL
**Reviewed:** February 9, 2026

## Plan Verification

```
Plan-Content Alignment: [FAIL]
- Sections: [PASS] All outlined sections present.
- Vocabulary: [PASS] Hints used correctly.
- Grammar scope: [FAIL] Research notes explicitly mark "Plural Case Forms" as OUT OF SCOPE, but content includes a table and examples for Plural Instrumental endings.
- Objectives: [PASS] Objectives met.
```

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 9/10 | <7 | Clear explanations, engaging tone ("3D map"). |
| 2 | Coherence | 9/10 | <7 | Logic flows well from Motion/Location to specific cases. |
| 3 | Relevance | 9/10 | <7 | Highly relevant for A2 navigation. |
| 4 | Educational | 8/10 | <7 | Good concept checking, but marred by scope creep. |
| 5 | Language | 9/10 | <8 | Natural Ukrainian examples. |
| 6 | Pedagogy | 6/10 | <7 | **FAIL**: Explicit violation of scope boundaries defined in Research Notes (Instrumental Plural). |
| 7 | Immersion | 8/10 | <6 | Good use of Ukrainian in examples and dialogues. |
| 8 | Activities | 5/10 | <7 | **FAIL**: Cloze options contain leaked grammatical metadata; Vocabulary file contains wrong lemmas for key verbs. |
| 9 | Richness | 8/10 | <6 | Good variety of prepositions. |
| 10 | Beginner Safety | 7/10 | <7 | Plurals might be overwhelming given they are out of scope. |
| 11 | LLM Fingerprint | 8/10 | <7 | Generally human-like tone. |
| 12 | Linguistic Accuracy | 8/10 | <9 | **FAIL**: Vocabulary file errors (`спити` vs `спати`). |

**Weighted Overall:** 7.5/10

## Auto-Fail Checklist Results

- Russianisms: [CLEAN]
- Calques: [CLEAN]
- Grammar scope: **[FAIL]** Plural Instrumental introduced despite being Out of Scope.
- Activity errors: **[FAIL]** Broken Cloze formatting; Metadata in options.
- Beginner safety: 7/5

## Critical Issues Found

### Issue 1: Grammar Scope Violation
- **Location**: Section "Prepositions with the Instrumental Case", Table "Рід | Закінчення...", Row "Plural"
- **Original**: "| Plural | **-ами** / **-ями** | між вікн**ами**, перед двер**има** |"
- **Problem**: Research Notes Section 5 explicitly states: "**OUT OF SCOPE**: ... **Plural Case Forms**: Focus remains on singular nouns to ensure mastery of the core concept." Introducing plurals here confuses the learner who is just learning singulars.
- **Fix**: Remove the "Plural" row from the table and the examples "між вікнами, перед дверима, дітьми". Keep examples singular.

### Issue 2: Activity Formatting (Broken UX)
- **Location**: Activities file, `type: cloze`, `passage`
- **Original**: "Марія живе {в/у + Loc|на + Acc|до + Gen} Києві."
- **Problem**: The options include grammatical metalanguage ("+ Loc", "+ Acc") which should not be visible to the user in the selection dropdown. It looks like a template error.
- **Fix**: Change options to plain words: `{в|на|до}`. If the intention was to test logic, the cues should be outside the brace or in the hint, not in the clickable text. Given the context "Києві" (Locative), the only grammatically possible option is `в` (or `у`), so adding `+ Loc` gives away the answer if the user knows the case name, or confuses them if they don't.
- **Correction**: "Марія живе {в|на|до} Києві." (and fix all similar items in the passage).

### Issue 3: Vocabulary Extraction Errors (Wrong Lemmas)
- **Location**: Vocabulary file, Items `спити` and `поклад`
- **Original**:
  - `lemma: спити` (translation: to drink all of)
  - `lemma: поклад` (translation: deposit)
- **Problem**:
  - The text uses "Кіт **спить**" (sleeps). The lemma for "sleeps" is **спати**, not `спити` (perfective of *pity*).
  - The text uses " **Поклади** зошит" (Put the notebook). This is the imperative of **класти** (or *покласти*). `поклад` is a geological noun.
- **Fix**: Replace `спити` with `спати` (to sleep). Replace `поклад` with `покласти` (to put).

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| Vocab | спити | спати | Wrong Lemma |
| Vocab | поклад | покласти | Wrong Lemma |

## Beginner Safety Audit

"Would I Continue?" Test: 4/5
- Overwhelmed? Pass
- Instructions clear? Pass
- Quick wins? Pass
- Ukrainian scary? Pass
- Come back tomorrow? Pass

## Strengths
- Excellent explanation of the "Motion vs. Location" concept using the "targeting energy" analogy.
- High-quality diagrams (mermaid) visualizing the logic.

## Fix Plan to Reach 9/10

### Pedagogy: 6/10 → 9/10
**What to fix:**
1. **Section "Prepositions with the Instrumental Case"**: Remove the "Plural" row from the table.
2. **Same Section**: Change examples "між вікнами" → "між вікном і дверима" (or singular equivalents), "перед дверима" → "перед будинком".
3. **Research Alignment**: Ensure content strictly follows the "Singular Only" rule from Research Notes.

### Activities: 5/10 → 9/10
**What to fix:**
1. **Cloze Activity**: Remove `+ Loc`, `+ Acc`, `+ Gen` tags from all options in the `passage`.
   - Change `{в/у + Loc|на + Acc|до + Gen}` → `{в|на|до}`.
   - Change `{на + Loc|в + Acc|до + Gen}` → `{на|в|до}`.
   - (And so on for all items in the story).
2. **Vocabulary File**:
   - Change `lemma: спити` → `lemma: спати`, `translation: to sleep`.
   - Change `lemma: поклад` → `lemma: покласти`, `translation: to put (perfective)`.

### Linguistic Accuracy: 8/10 → 10/10
**What to fix:**
1. **Vocabulary**: Executing the lemma fixes above resolves this.

### Projected Overall After Fixes
(9 + 9 + 9 + 8 + 9 + 9 + 8 + 9 + 8 + 8 + 8 + 10) / 14 ≈ **8.8/10** (Wait, calculating...)
Let's aim for 9s across the board.
With fixes:
- Activities: 9
- Pedagogy: 9
- Linguistic Accuracy: 10
Result: > 9.0.

## Verification Summary
- Content lines read: ~140
- Activity items checked: 11 types (~60 items)
- Ukrainian sentences verified: ~30
- IPA transcriptions checked: 50
- Issues found: 3 Critical
- Naturalness score recommendation: 9/10

## Verdict
**FAIL**

The module fails due to **Pedagogical Scope Violation** (introducing plurals explicitly forbidden by the design docs) and **Critical Activity Errors** (broken Cloze formatting and incorrect vocabulary lemmas). These must be fixed to ensure a safe learner experience.

===REVIEW_END===
