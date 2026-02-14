# Рецензія: Мова про дієслова

**Level:** B1 | **Module:** 2
**Overall Score:** 6.9/10
**Status:** FAIL
**Reviewed:** 2026-02-14

## Plan Verification

```
Plan-Content Alignment: [PASS]
- Sections: [10/10 sections present as H2/H3]
- Vocabulary: [25/25 items from plan present, enriched with IPA/Examples]
- Grammar scope: [Covers terminology for aspect, tense, negation, and forms as planned]
- Objectives: [All objectives addressed through detailed explanations and practice dialogues]
```

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 8/10 | <7 | Strong "Helpful Neighbor" voice; the transition to terminology is handled with empathy. |
| 2 | Coherence | 7/10 | <7 | Terminology inconsistency between `складна форма` and `складена форма` across files. |
| 3 | Relevance | 9/10 | <7 | High relevance for B1 learners transitioning to authentic Ukrainian resources. |
| 4 | Educational | 8/10 | <7 | Explanations of aspect (photo vs. video) are pedagogically sound. |
| 5 | Language | 5/10 | <8 | **AUTO-FAIL**: Presence of hybrid English/Ukrainian sentences like «Тепер we переходимо». |
| 6 | Pedagogy | 8/10 | <7 | Good use of comparison tables and guided analysis of real grammar texts. |
| 7 | Immersion | 9/10 | <6 | 94.1% immersion is excellent for a B1 bridge module, exceeding the 70% target. |
| 8 | Activities | 7/10 | <7 | Content is good, but carries the `складна/складена` terminology confusion into the items. |
| 9 | Richness | 9/10 | <6 | 11 engagement boxes provide high cultural and historical depth. |
| 10 | Beginner Safety | 8/10 | <7 | Clear instructions and supportive tone ("Would I Continue?" 4/5). |
| 11 | LLM Fingerprint | 5/10 | <7 | Excessive rhetoric patterns («не просто... а») and hybrid language glitches detected. |
| 12 | Linguistic Accuracy | 4/10 | <9 | **AUTO-FAIL**: Fatal errors in sentence construction (mixing English/Ukrainian verbs). |

**Weighted Overall:** (8×1.5 + 7×1.0 + 9×1.0 + 8×1.2 + 5×1.1 + 8×1.2 + 9×1.0 + 7×1.3 + 9×0.9 + 8×1.3 + 5×1.0 + 4×1.5) / 14.0 = **6.92/10**

## Auto-Fail Checklist Results

- Russianisms: [CLEAN]
- Calques: [CLEAN]
- Grammar scope: [CLEAN]
- Activity errors: [FAIL] - Inconsistency in `складна` vs `складена` form terminology.
- Beginner safety: 4/5

## Critical Issues Found

### Issue 1: Hybrid Language Glitch
- **Location**: Line 55 / Section "Вид дієслова: Доконаний та недоконаний"
- **Original**: «Тепер we переходимо до однієї з найважливіших категорій української мови.»
- **Problem**: Hybrid English/Ukrainian sentence construction ("we переходимо"). This is a serious generation error.
- **Fix**: Replace with «Тепер ми переходимо до однієї з найважливіших категорій української мови.»

### Issue 2: Hybrid Language Glitch
- **Location**: Line 83 / Section "Поняття дії: Процес та результат"
- **Original**: «Коли ми розглядаємо дієслово, we analyze три ключові терміни: **дія** (action), **процес** (process) та **результат** (result).»
- **Problem**: Hybrid English/Ukrainian sentence construction ("we analyze").
- **Fix**: Replace with «Коли ми розглядаємо дієслово, ми аналізуємо три ключові терміни...»

### Issue 3: Terminology Inconsistency
- **Location**: Vocabulary.yaml (Item 16) vs Content/Activities
- **Original**: Vocabulary: `складна форма`. Text: `складена форма`. Activity 3: `складена`.
- **Problem**: Conflicting terms for "compound form". In Ukrainian grammar, `складена` is the standard for forms consisting of two words (future tense). `Складна` implies complexity and is often used for synthetic forms in older traditions, causing confusion here.
- **Fix**: Unify to `складена форма` (composed/compound) in all files for the `буду читати` structure.

### Issue 4: Hybrid Language Glitch
- **Location**: Line 140 / Section "Заперечення та його вплив на вид"
- **Original**: «Коли we talk про **заперечення** (negation), ми найчастіше маємо на увазі...»
- **Problem**: Hybrid English/Ukrainian sentence construction ("we talk").
- **Fix**: Replace with «Коли ми говоримо про заперечення (negation)...»

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| 55 | «Тепер we переходимо» | «Тепер ми переходимо» | Hybrid Language |
| 83 | «we analyze» | «ми аналізуємо» | Hybrid Language |
| 140 | «Коли we talk про» | «Коли ми говоримо про» | Hybrid Language |
| 58 | «... розуміння різниці між фотографією (результат) та відео (процес).» | «... розуміння різниці між фотографією (результатом) та відео (процесом).» | Case agreement |

## Beginner Safety Audit

"Would I Continue?" Test: 4/5
- Overwhelmed? [Pass] - Concepts are broken down well.
- Instructions clear? [Pass] - Clear use of English equivalents in parentheses.
- Quick wins? [Pass] - Identifying aspect names is an immediate win.
- Ukrainian scary? [Fail] - The hybrid language glitches might confuse a learner about the target language's own grammar.
- Come back tomorrow? [Pass] - The friendly neighbor voice makes it inviting.

## Strengths
- **Authentic Pedagogy**: The comparison between "photo" (result) and "video" (process) for aspect is a world-class pedagogical tool for English speakers.
- **Teacher Voice**: The "Senior Specialist as Tutor" persona is very warm and reduces the anxiety of learning metalanguage.

## Fix Plan to Reach 9/10

### Language: 5/10 → 10/10
**What to fix:**
1. Line 55: Change «Тепер we переходимо» → «Тепер ми переходимо» — Remove English verb.
2. Line 83: Change «we analyze» → «ми аналізуємо» — Remove English verb.
3. Line 140: Change «Коли we talk» → «Коли ми говоримо» — Remove English verb.

### Coherence: 7/10 → 9/10
**What to fix:**
1. `vocabulary.yaml`: Change `складна форма` → `складена форма` for item 16.
2. `language-about-verbs.md`: Remove the parenthetical `(складена)` in "Визначення термінів: складна (складена) форма" and just use `складена форма`.
3. `activities.yaml`: Ensure `error-correction` item 2 uses the agreed term to test against.

### LLM Fingerprint: 5/10 → 9/10
**What to fix:**
1. Remove 50% of metaphors like "архітектура", "ключ", "двері" to sound more like a human teacher and less like an AI essay.
2. Rewrite sentences starting with «це не просто... а» (e.g., line 13, line 29, line 137) to vary rhetoric.

### Projected Overall After Fixes
```
(8.0×1.5 + 9.0×1.0 + 9.0×1.0 + 8.0×1.2 + 10.0×1.1 + 8.0×1.2 + 9.0×1.0 + 9.0×1.3 + 9.0×0.9 + 8.0×1.3 + 9.0×1.0 + 10.0×1.5) / 14.0 = 9.02/10
```

## Verification Summary

- Content lines read: 365
- Activity items checked: 36
- Ukrainian sentences verified: 184
- IPA transcriptions checked: 25
- Issues found: 4 critical, 3 stylistic

## Verdict

**FAIL**

The module suffers from critical "hybrid language" glitches where English verbs are used in Ukrainian sentence structures (e.g., "we переходимо"). This is an absolute blocker for a language curriculum. Additionally, terminology for "compound form" is inconsistent across files.
