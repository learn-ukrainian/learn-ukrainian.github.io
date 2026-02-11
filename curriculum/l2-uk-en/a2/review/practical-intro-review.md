# Рецензія: Practical Intro

**Level:** A2 | **Module:** 57
**Overall Score:** 8.1/10
**Status:** FAIL
**Reviewed:** 2026-02-10

## Plan Verification

Plan-Content Alignment: FAIL
- Sections: all present.
- Vocabulary: Required words (речення, слово, граматика, правило, помилка, правильно, неправильно, контекст) are used in content but MISSING from the vocabulary YAML file.
- Grammar scope: clean review of A2 topics.
- Objectives: all covered (Identify 7 cases, aspect choice, error correction, complex sentences).

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 8/10 | <7 | Good bridge content; integration task is excellent. Shortfall in activity density. |
| 2 | Coherence | 9/10 | <7 | Logical progression from theoretical review to error analysis. |
| 3 | Relevance | 10/10 | <7 | Vital transition module; addresses real student struggles with Case vs. Motion. |
| 4 | Educational | 9/10 | <7 | Strong review with clear model boxes and self-checks. |
| 5 | Language | 7/10 | <8 | Punctuation in unjumble activities is missing required commas taught in the text. |
| 6 | Pedagogy | 6/10 | <7 | Pedagogical inconsistency: teaches punctuation rules but ignores them in drill answers. Missing required vocab in YAML. |
| 7 | Immersion | 8/10 | <6 | Appropriate bilingual balance for A2 review. |
| 8 | Activities | 6/10 | <7 | Significant shortfall in item counts (Fill-in: 8/20; Error-correction: 13/20). Punctuation errors in unjumble. |
| 9 | Richness | 9/10 | <6 | 1335 words (target 1000); 4 engagement boxes; high-quality integration story. |
| 10 | Beginner Safety | 9/10 | <7 | "Would I Continue?" 5/5. Encouraging tone and clear instructions. |
| 11 | LLM Fingerprint | 9/10 | <7 | Structure matches project conventions; tone is tutor-like. |
| 12 | Linguistic Accuracy | 8/10 | <9 | Commas missing in multiple activity answers. "писати лист" is acceptable but less idiomatic than "листа". |

**Weighted Overall:** (8*1.5 + 9*1.0 + 10*1.0 + 9*1.2 + 7*1.1 + 6*1.2 + 8*1.0 + 6*1.3 + 9*0.9 + 9*1.3 + 9*1.0 + 8*1.5) / 14.0 = **8.1/10**

## Auto-Fail Checklist Results

- Russianisms: [CLEAN]
- Calques: [CLEAN]
- Grammar scope: [CLEAN]
- Activity errors: [Punctuation missing in 12 unjumble items; Ambiguous error in Item 12 of error-correction]
- Beginner safety: 5/5

## Critical Issues Found

### Issue 1: Pedagogical/Linguistic Punctuation Inconsistency
- **Location**: Activity `unjumble` (Sentence Builder)
- **Original**: "Я не пішов у кіно тому що працював"
- **Problem**: Skill 3 explicitly teaches: "Майже завжди перед ним [що] потрібна кома" and "Do you remember to put a comma before these connectors?". However, all 12 answers in the unjumble activity omit these mandatory commas.
- **Fix**: Add commas to all unjumble answers where required (e.g., "Я не пішов у кіно, тому що працював").

### Issue 2: Vocabulary YAML Mismatch
- **Location**: `vocabulary/57-practical-intro.yaml`
- **Problem**: The vocabulary file omits ALL 8 required words from the plan (речення, слово, граматика, правило, помилка, правильно, неправильно, контекст).
- **Fix**: Update the YAML to include the plan's required vocabulary items with IPA and translations.

### Issue 3: Activity Item Count Shortfall
- **Location**: Activities `fill-in`, `error-correction`, `unjumble`, `quiz`
- **Problem**: Significant shortfall vs. plan hints: Fill-in (8 vs 20), Error-correction (13 vs 20), Unjumble (12 vs 15), Quiz (12 vs 15).
- **Fix**: Expand item counts to match plan targets.

### Issue 4: Ambiguous Error Correction
- **Location**: Activity `error-correction`, Item 12
- **Original**: "Я чекаю автобус. (error: автобус, answer: автобуса)"
- **Problem**: The explanation states "Both are used." Marking a commonly used and acceptable form ("чекаю автобус") as an error is confusing for A2 learners.
- **Fix**: Replace with a clear error (e.g., "дякую тебе" -> "дякую тобі") or an unambiguous case error.

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| 132 | "Я писав лист вчора дві години." | "Я писав листа вчора дві години." | Naturalness (Genitive preferred for specific letter) |
| YAML | "тому що працював" (unjumble ans 1) | ", тому що працював" | Punctuation |
| YAML | "додому він вже" (unjumble ans 2) | "додому, він вже" | Punctuation |
| YAML | "хочу щоб ти" (unjumble ans 3) | "хочу, щоб ти" | Punctuation |

## Beginner Safety Audit

"Would I Continue?" Test: 5/5
- Overwhelmed? Pass
- Instructions clear? Pass
- Quick wins? Pass
- Ukrainian scary? Pass
- Come back tomorrow? Pass

Emotional beats: 6 found
- Welcome: Section "Огляд"
- Curiosity: Skill headers "Чи можете ви..."
- Quick wins: 3 items in Skill 1 "Практика"
- Encouragement: "Остання порада" Box (Important)
- Progress: "Підсумок" table and "Наступні кроки"

## Strengths
- Excellent "Integration Task" that combines multiple skills into a single narrative context.
- High word count provides depth and meaningful context for the review.

## Fix Plan to Reach 9/10 (REQUIRED if score < 9.0)

### Pedagogy: 6/10 → 9/10
**What to fix:**
1. `vocabulary/57-practical-intro.yaml`: Add required words: речення, слово, граматика, правило, помилка, правильно, неправильно, контекст.
2. Section "Skill 4": Ensure the examples used in text perfectly match the corrected activity logic.

### Activities: 6/10 → 9/10
**What to fix:**
1. `fill-in`: Add 12 more items to reach the target of 20.
2. `error-correction`: Add 7 more items to reach 20; remove ambiguous item 12.
3. `unjumble`: Add 3 more items to reach 15.
4. `quiz`: Add 3 more items to reach 15.
5. All activities: Audit every Ukrainian sentence for mandatory commas before connectors (що, щоб, тому що, бо, який) to ensure pedagogical consistency.

### Language/Accuracy: 7.5/10 → 9.5/10
**What to fix:**
1. Fix punctuation in all 12 `unjumble` answer strings.
2. Change "писав лист" to "писав листа" in Skill 2 Model for better naturalness.

### Projected Overall After Fixes
(8*1.5 + 9*1.0 + 10*1.0 + 9*1.2 + 9*1.1 + 9*1.2 + 8*1.0 + 9*1.3 + 9*0.9 + 9*1.3 + 9*1.0 + 9.5*1.5) / 14.0 = **9.1/10**

## Verification Summary

- Content lines read: 250
- Activity items checked: 114
- Ukrainian sentences verified: 65
- IPA transcriptions checked: 6
- Issues found: 4 Critical categories
- Naturalness score recommendation: 9/10 (Content is natural; activities need polish)

## Verdict

**FAIL**

Blocking issues: 1) Pedagogical inconsistency in punctuation between lesson and activities. 2) Significant shortfall in activity item counts vs. plan hints. 3) Required vocabulary missing from YAML.