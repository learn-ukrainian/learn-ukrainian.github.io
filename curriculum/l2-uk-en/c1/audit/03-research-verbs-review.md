# Audit Report: M03 — 03-research-verbs.md
**Level:** C1 | **Module:** M03 | **Phase:** C1.1 | **Pedagogy:** Not Specified | **Target:** 3000
**Naturalness:** None/10 (PENDING)
**Overall Status:** ❌ FAIL
**Generated:** 2026-01-25 19:24:05

## Configuration
**Type:** C1-vocab
**Word Target:** 3000 words
**Activities:** 12-16 required
**Items per Activity:** ≥12 items
**Unique Types:** ≥4 types required
**Priority Types:** error-correction, fill-in, unjumble
**Required Types:** cloze, essay-response, fill-in, group-sort, match-up, quiz
**Engagement:** ≥7 callouts
**Immersion:** 90-100%
**Vocab Target:** ≥25 words
**Transliteration:** Not allowed

## Activity Breakdown
| # | Type | Title | Items | Min | Status |
|---|------|-------|-------|-----|--------|
| 1 | quiz | Розуміння Тексту 1 (Етапи) | 8 | 5 | ✅ |
| 2 | quiz | Розуміння Тексту 2 та 3 | 8 | 5 | ✅ |
| 3 | match-up | Визначення термінів | 14 | 6 | ✅ |
| 4 | match-up | Визначення термінів 2 | 14 | 6 | ✅ |
| 5 | match-up | Синоніми | 14 | 6 | ✅ |
| 6 | match-up | Антоніми | 14 | 6 | ✅ |
| 7 | group-sort | Етапи дослідження | 18 | 12 | ✅ |
| 8 | fill-in | Керування дієслів 1 | 8 | 6 | ✅ |
| 9 | fill-in | Керування дієслів 2 | 8 | 6 | ✅ |
| 10 | group-sort | Стилістичне сортування | 18 | 12 | ✅ |
| 11 | error-correction | Виправлення помилок | 8 | 5 | ✅ |
| 12 | fill-in | Пасивні конструкції | 8 | 6 | ✅ |
| 13 | quiz | Загальний тест | 8 | 5 | ✅ |
| 14 | quiz | Переклад речень | 8 | 5 | ✅ |
| 15 | match-up | Колокації: Іменник + Дієслово | 14 | 6 | ✅ |
| 16 | match-up | Словотвір (Дієслово -> Іменник) | 14 | 6 | ✅ |
| 17 | essay-response | Письмове завдання: Опис дослідження | 1 | 1 | ✅ |

**Summary:**
- Total activities: 17 (target: 12-16) ❌
- Unique types: 6 (minimum: 4) ✅
- Priority types used: 2/3 (error-correction, fill-in) ✅
- Required types used: 5/6 (essay-response, fill-in, group-sort, match-up, quiz) ❌
- Low density activities: 0

## PEDAGOGICAL VIOLATIONS
- **[YAML_SCHEMA_VIOLATION]** Schema error in 03-research-verbs.yaml: Schema validation error at key 'min_words': 100 is less than the minimum of 200
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## Recommendation
**📝 UPDATE** (severity 25/100)

- 1 violations (minor)
- Structure issue: Missing '## Vocabulary' header OR vocabulary sidecar

## Gates
- **Words:** ❌ 1929/3000 (raw: 2036)
- **Activities:** ✅ 17/12
- **Density:** ✅ All > 12
- **Unique_types:** ✅ 6/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 8/7
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 0 < 25 (soft target)
- **Structure:** ❌ Missing '## Vocabulary' header OR vocabulary sidecar
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 1 violations
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 99.2% (target 90-100% (vocab))
- **Richness:** ❌ 74% < 95% min (vocabulary)
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ❌ None/10 (PENDING) - Naturalness check required

## Richness Details
**Score:** 74% (minimum: 95%)
**Module Type:** vocabulary

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| collocations | 0 | 20 | 0% | 25% | 0.0% |
| usage_examples | 48 | 15 | 100% | 20% | 20.0% |
| engagement | 8 | 4 | 100% | 15% | 15.0% |
| cultural | 4 | 3 | 100% | 10% | 10.0% |
| visual | 9 | 3 | 100% | 10% | 10.0% |
| register_notes | 7 | 5 | 100% | 10% | 10.0% |
| variety | 0.98 | - | 98% | 5% | 4.9% |
| paragraph_var | 1.00 | - | 100% | 5% | 5.0% |
| **TOTAL** | | | | | **74.9%** |

### Dryness Flags & Fixes
- ❌ **NO_COLLOCATIONS**
  - FIX:
    Add 5+ collocations in format: **слово** + noun/verb (e.g., **важка** робота, **приймати** рішення)

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 66 | Included in Core |
| **Вступ: Етапи наукового пошуку** | ✅ | 235 | Included in Core |
| **Академічне письмо: Нюанси значень** | ⚪️ | 301 | Skipped |
| **Діалог: Консультація з науковим керівником** | ✅ | 186 | Included in Core |
| **Текст 2: Рецензія на наукову працю** | ✅ | 89 | Included in Core |
| **Текст 3: Еволюція тексту (До і Після)** | ✅ | 198 | Included in Core |
| **Порівняльний аналіз стилів** | ✅ | 124 | Included in Core |
| **Текст 4: Золотий вік та репресії української термінології** | ✅ | 264 | Included in Core |
| **Практика** | ⚪️ | 164 | Skipped |
| **Самоперевірка** | ⚪️ | 76 | Skipped |
| **Підсумок** | ✅ | 173 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 53 | Skipped |