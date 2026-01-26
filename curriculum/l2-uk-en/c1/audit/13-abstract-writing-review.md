# Audit Report: M13 — 13-abstract-writing.md
**Level:** C1 | **Module:** M13 | **Phase:** C1 | **Pedagogy:** Not Specified | **Target:** 3000
**Naturalness:** None/10 (PENDING)
**Overall Status:** ❌ FAIL
**Generated:** 2026-01-26 22:29:02

## Configuration
**Type:** C1-grammar
**Word Target:** 3000 words
**Activities:** 12-16 required
**Items per Activity:** ≥12 items
**Unique Types:** ≥4 types required
**Priority Types:** error-correction, fill-in, unjumble
**Required Types:** cloze, error-correction, essay-response, fill-in, match-up, quiz
**Engagement:** ≥7 callouts
**Immersion:** 90-100%
**Vocab Target:** ≥25 words
**Transliteration:** Not allowed

## Activity Breakdown
| # | Type | Title | Items | Min | Status |
|---|------|-------|-------|-----|--------|
| 1 | quiz | Анатомія анотації | 8 | 5 | ✅ |
| 2 | match-up | Об'єкт vs Предмет | 8 | 6 | ✅ |
| 3 | fill-in | Кліше анотації | 8 | 6 | ✅ |
| 4 | group-sort | Сортування: Описова vs Інформативна | 18 | 12 | ✅ |
| 5 | error-correction | Стислість: Редагування | 6 | 5 | ✅ |
| 6 | match-up | Академічні синоніми | 8 | 6 | ✅ |
| 7 | match-up | Компоненти анотації (English vs Ukrainian) | 8 | 6 | ✅ |
| 8 | unjumble | Складання речення: Номіналізація | 6 | 5 | ✅ |
| 9 | true-false | Логіка побудови | 8 | 5 | ✅ |
| 10 | match-up | Переклад термінів | 8 | 6 | ✅ |
| 11 | quiz | Вибір дієслова | 8 | 5 | ✅ |
| 12 | true-false | Пошук 'води' | 8 | 5 | ✅ |
| 13 | fill-in | Академічна пунктуація | 8 | 6 | ✅ |
| 14 | match-up | Сигнали переказу | 8 | 6 | ✅ |
| 15 | quiz | Регістр: Академічний ремонт | 8 | 5 | ✅ |
| 16 | essay-response | Письмове завдання: Написання анотації | 1 | 1 | ✅ |

**Summary:**
- Total activities: 16 (target: 12-16) ✅
- Unique types: 8 (minimum: 4) ✅
- Priority types used: 3/3 (error-correction, fill-in, unjumble) ✅
- Required types used: 5/6 (error-correction, essay-response, fill-in, match-up, quiz) ❌
- Low density activities: 0

## PEDAGOGICAL VIOLATIONS
- **[YAML_SCHEMA_VIOLATION]** Schema error in 13-abstract-writing.yaml: Schema validation error at key 'min_words': 100 is less than the minimum of 200
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## Recommendation
**📝 UPDATE** (severity 25/100)

- 1 violations (minor)
- Structure issue: Missing '## Vocabulary' header OR vocabulary sidecar

## Gates
- **Words:** ❌ 2230/3000 (raw: 2461)
- **Activities:** ✅ 16/12
- **Density:** ✅ All > 12
- **Unique_types:** ✅ 8/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 11/7
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 0 < 25 (soft target)
- **Structure:** ❌ Missing '## Vocabulary' header OR vocabulary sidecar
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 1 violations
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 99.6% (target 90-100% (grammar))
- **Richness:** ❌ 87% < 95% min (content)
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ❌ None/10 (PENDING) - Naturalness check required

## Richness Details
**Score:** 87% (minimum: 95%)
**Module Type:** content

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| examples | 26 | 15 | 100% | 25% | 25.0% |
| engagement | 11 | 5 | 100% | 19% | 18.7% |
| variety | 0.98 | - | 98% | 12% | 12.2% |
| cultural | 0 | 4 | 0% | 12% | 0.0% |
| realworld | 6 | 3 | 100% | 12% | 12.5% |
| visual | 15 | 4 | 100% | 6% | 6.2% |
| paragraph_var | 1.00 | - | 100% | 6% | 6.2% |
| questions | 15 | 4 | 100% | 6% | 6.2% |
| **TOTAL** | | | | | **87.2%** |

### Dryness Flags & Fixes
- ❌ **NO_CULTURAL_ANCHOR**
  - FIX:
    Add 3+ cultural references. Use this exact format:
    
    > 🇺🇦 **Культурний момент**
    >
    > [Reference to Ukrainian place (Київ, Львів, Одеса, Карпати), tradition, or custom]
    > [How it connects to the grammar/vocabulary being taught]
    > [Example sentence using the grammar with cultural context]

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 101 | Included in Core |
| **Вступ** | ✅ | 173 | Included in Core |
| **Розділ 1: Що таке анотація і навіщо вона потрібна** | ⚪️ | 335 | Skipped |
| **Розділ 2: Структура ідеальної анотації** | ⚪️ | 227 | Skipped |
| **Розділ 3: Об'єкт і Предмет дослідження — в чому різниця?** | ⚪️ | 298 | Skipped |
| **Розділ 4: Стратегії мовної економії** | ⚪️ | 232 | Skipped |
| **Розділ 5: Етика стислості та повага до читача** | ⚪️ | 158 | Skipped |
| **Розділ 6: Мистецтво вибору ключових слів** | ⚪️ | 180 | Skipped |
| **Розділ 7: Роль анотації в академічній репутації** | ⚪️ | 150 | Skipped |
| **Розділ 8: Ситуативний діалог про якість тексту** | ✅ | 172 | Included in Core |
| **Академічний текст: Кейс-стаді (Аналіз анотації)** | ✅ | 113 | Included in Core |
| **Підсумок** | ✅ | 77 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 14 | Skipped |