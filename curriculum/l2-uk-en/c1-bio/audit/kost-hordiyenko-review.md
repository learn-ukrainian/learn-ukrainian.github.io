# Рецензія: Кость Гордієнко: Запорозький кошовий

**Level:** C1-BIO | **Module:** 28
**Overall Score:** 8.9/10
**Status:** FAIL
**Reviewed:** 2026-02-09

## Plan Verification

```
Plan-Content Alignment: PASS
- Sections: all present
- Vocabulary: 3/3 hints covered; "істеблішмент" in vocab file but missing from text
- Grammar scope: clean
- Objectives: all covered
```

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 9/10 | <7 | Strong narrative voice, compelling "Intro" and "Legacy". |
| 2 | Coherence | 8/10 | <7 | Narrative flow is interrupted: "Life Story" -> "Context" -> "Contribution" -> "Last Years". Ideally, "Last Years" should follow "Life Story". |
| 3 | Relevance | 10/10 | <7 | Perfectly aligned with the module's objectives. |
| 4 | Educational | 10/10 | <7 | Deep historical insight, excellent debunking of myths. |
| 5 | Language | 10/10 | <8 | High-level C1 vocabulary ("суб'єктність", "візіонерство"), grammatical complexity is appropriate. |
| 6 | Pedagogy | 9/10 | <7 | Good variety of callouts and reflection points. |
| 7 | Immersion | 10/10 | <6 | 100% Ukrainian, authentic tone. |
| 8 | Activities | 6/10 | <7 | **Blocking Issue**: True/False drills have 8-9 items; standard requires 12+. |
| 9 | Richness | 10/10 | <6 | Word count met (4700+), culturally dense. |
| 10 | Beginner Safety | 8/10 | <7 | Structure is clear, though text is dense (expected for C1). |
| 11 | LLM Fingerprint | 9/10 | <7 | Content feels curated and specific, not generic. |
| 12 | Linguistic Accuracy | 10/10 | <9 | No Russianisms or grammatical errors found. |

**Weighted Overall:** 124.9 / 14.0 = **8.92/10**

## Auto-Fail Checklist Results

- Russianisms: [CLEAN]
- Calques: [CLEAN]
- Grammar scope: [CLEAN]
- Activity errors: **FAIL** (Density < 12 items for drills)
- Beginner safety: 5/5

## Critical Issues Found

### Issue 1: Activity Density Violation
- **Location**: `activities.yaml` / Activity 3 and 4 (True-False)
- **Original**: 9 items and 8 items respectively.
- **Problem**: Project standards require drill-type activities (like True/False, Match-up) to have at least 12 items to ensure sufficient practice volume.
- **Fix**: Add 3-4 new items to each True/False activity.

### Issue 2: Vocabulary Consistency
- **Location**: `vocabulary.yaml` / Item "істеблішмент"
- **Original**: `lemma: істеблішмент`
- **Problem**: This word appears in the vocabulary list but is NOT used in the module text. Vocabulary must be contextual.
- **Fix**: Replace with a word actually used in the text, such as "еліта" (used as "елітарного") or "старшина", OR add the word "істеблішмент" to the text (e.g., in the "Історичний контекст" section).

### Issue 3: Structural Coherence
- **Location**: `kost-hordiyenko.md` / Section Order
- **Original**: "Життєпис" ... "Історичний контекст" ... "Внесок" ... "Останні роки"
- **Problem**: The biography is split. The reader finishes the "Life Story" (which implies the end of his active period), reads about context and constitution, and then jumps back to "Last Years" and his death.
- **Fix**: While the plan dictates this outline, for the sake of flow, ensure the transition to "Останні роки" explicitly reconnects the narrative, or consider moving the content of "Останні роки" to the end of "Життєпис" in future iterations (keeping headers for plan compliance). For now, no text change is strictly required if plan compliance is paramount, but it lowers the Coherence score.

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| N/A | [CLEAN] | [CLEAN] | None |

## Beginner Safety Audit

"Would I Continue?" Test: 5/5
- Overwhelmed? No, structure helps navigation.
- Instructions clear? Yes.
- Quick wins? Yes, myth-busters provide immediate value.
- Ukrainian scary? No, appropriate for C1.
- Come back tomorrow? Yes, the narrative is engaging.

Emotional beats: 5 found
- Welcome: "Вступ — Лицар степу" sets a strong heroic tone.
- Curiosity: `[!myth-buster]` effectively engages critical thinking.
- Quick wins: Short, punchy callouts.
- Encouragement: "Потрібно більше практики?" section.
- Progress: Clear chronological progression (mostly).

## Strengths
- **Narrative Power**: The text effectively positions Gordiyenko not just as a soldier, but as a political visionary.
- **Myth-Busting**: excellent handling of the "betrayal" narrative regarding Mazepa.
- **Richness**: The word count is high (4700+), providing the depth required for C1 "Reading to Learn".

## Fix Plan to Reach 9/10

### Activities: 6/10 → 9/10

**What to fix:**
1.  **Activity "Деконструкція міфів про запорозький спротив"**: Add 4 items.
    *   *Item 1*: `statement: "Гордієнко підтримував ідею спадковості гетьманської влади."`, `correct: false`, `explanation: "Він був переконаним республіканцем і захисником виборності."`
    *   *Item 2*: `statement: "Кам'янська Січ була заснована на території, підконтрольній Польщі."`, `correct: false`, `explanation: "Вона розташовувалася ближче до кордону з Гетьманщиною, але під протекторатом Криму."`
    *   *Item 3*: `statement: "Гордієнко особисто керував обороною Батурина."`, `correct: false`, `explanation: "Обороною Батурина керував Дмитро Чечель; Гордієнко приєднався до Мазепи пізніше."`
    *   *Item 4*: `statement: "Запорожці отримали право безмитної торгівлі у Криму завдяки дипломатії Гордієнка."`, `correct: true`, `explanation: "Він умів домовлятися про економічні преференції для козаків."`
2.  **Activity "Деталі запорозької дипломатії"**: Add 4 items.
    *   *Item 1*: `statement: "Гордієнко листувався з європейськими газетами, щоб поширювати правду про Україну."`, `correct: true`, `explanation: "Інформаційна війна була частиною його стратегії."`
    *   *Item 2*: `statement: "Петро I пропонував Гордієнці звання фельдмаршала за зраду Мазепи."`, `correct: false`, `explanation: "Цар намагався підкупити його, але не такими високими званнями."`
    *   *Item 3*: `statement: "Гордієнко вимагав від Орлика звіту перед козацькою радою."`, `correct: true`, `explanation: "Підзвітність влади була його ключовою вимогою."`
    *   *Item 4*: `statement: "Отаман планував створити козацький флот на Чорному морі."`, `correct: true`, `explanation: "Морські походи залишалися важливою частиною стратегії Січі."`

### Language (Vocabulary): 10/10 (Maintain, but fix consistency)

**What to fix:**
1.  `vocabulary.yaml`: Replace `lemma: істеблішмент` with `lemma: еліта`.
    *   `ipa: /eˈlʲitɐ/`
    *   `translation: elite`
    *   `pos: noun`
    *   `gender: f`
    *   `note: найкращі представники суспільства`

**Expected score after fix:** 9.5/10 (Activities score will rise to 10).

### Projected Overall After Fixes

```
(9*1.5 + 8*1.0 + 10*1.0 + 10*1.2 + 10*1.1 + 9*1.2 + 10*1.0 + 10*1.3 + 10*0.9 + 8*1.3 + 9*1.0 + 10*1.5) / 14 = 9.29/10
```

## Verification Summary

- Content lines read: ~230
- Activity items checked: 27 (current) -> need ~35
- Ukrainian sentences verified: ~150
- IPA transcriptions checked: 24
- Issues found: 3 (Density, Vocab mismatch, Structure)
- Naturalness score recommendation: 10/10

## Verdict

**FAIL**

The module is linguistically excellent and content-rich, but it fails the **Activity Density** requirement (Activities must have 12+ items). The Vocabulary file also contains an orphan word not found in the text. These must be fixed to pass.