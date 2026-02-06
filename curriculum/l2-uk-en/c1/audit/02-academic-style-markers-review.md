# Audit Report: M02 — 02-academic-style-markers.md
**Level:** C1 | **Module:** M02 | **Phase:** C1.1 | **Pedagogy:** Not Specified | **Target:** 4000
**Naturalness:** None/10 (PENDING)
**Overall Status:** ❌ FAIL
**Generated:** 2026-02-06 20:12:42

## Configuration
**Type:** C1-grammar
**Word Target:** 4000 words
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
| 1 | quiz | Розуміння Тексту 1 | 8 | 5 | ✅ |
| 2 | match-up | Маркери академічного стилю | 14 | 6 | ✅ |
| 3 | group-sort | Сортування за стилем | 18 | 12 | ✅ |
| 4 | fill-in | Трансформація: Номіналізація | 8 | 6 | ✅ |
| 5 | select | Хеджинг: Вибір слова | 6 | 5 | ✅ |
| 6 | fill-in | Безособові конструкції | 8 | 6 | ✅ |
| 7 | match-up | Академічна лексика: Синоніми | 14 | 6 | ✅ |
| 8 | fill-in | Логічні конектори | 18 | 6 | ✅ |
| 9 | quiz | Пошук помилок регістру | 8 | 5 | ✅ |
| 10 | unjumble | Складання речень: Хеджинг | 6 | 5 | ✅ |
| 11 | true-false | Ідентифікація пасиву | 8 | 5 | ✅ |
| 12 | fill-in | Академічні дієслова | 8 | 6 | ✅ |
| 13 | quiz | Коректність посилань | 8 | 5 | ✅ |
| 14 | quiz | Аналітичне читання | 8 | 5 | ✅ |
| 15 | fill-in | Завершіть речення | 18 | 6 | ✅ |
| 16 | fill-in | Словниковий диктант | 8 | 6 | ✅ |
| 17 | quiz | Підсумковий тест | 8 | 5 | ✅ |
| 18 | essay-response | Письмове завдання: Редагування | 1 | 1 | ✅ |

**Summary:**
- Total activities: 18 (target: 12-16) ❌
- Unique types: 8 (minimum: 4) ✅
- Priority types used: 2/3 (fill-in, unjumble) ✅
- Required types used: 4/6 (essay-response, fill-in, match-up, quiz) ❌
- Low density activities: 0

## PEDAGOGICAL VIOLATIONS
- **[CONTENT_REDUNDANCY]** Redundant information detected in lesson (100% overlap): "У Мюнхені діяв Український вільний університет, у США — Наукове товариство імені Шевченка та Гарвард...". Shares significant keywords with sentence at index 56.
  - FIX: Remove redundant paragraphs. Ensure each section adds new unique value.
- **[CONTENT_REDUNDANCY]** Redundant information detected in lesson (100% overlap): "Такі вчені, як Юрій Шевельов та Омелян Пріцак, зберігали високі стандарти українського академічного ...". Shares significant keywords with sentence at index 57.
  - FIX: Remove redundant paragraphs. Ensure each section adds new unique value.
- **[YAML_SCHEMA_VIOLATION]** Schema error in 02-academic-style-markers.yaml: Schema validation error at key 'min_words': 100 is less than the minimum of 200
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## Recommendation
**📝 UPDATE** (severity 25/100)

- 3 violations (minor)
- Structure issue: Missing '## Vocabulary' header OR vocabulary sidecar

## Gates
- **Words:** ❌ 2487/4000 (raw: 2821)
- **Activities:** ✅ 18/12
- **Density:** ✅ All > 12
- **Unique_types:** ✅ 8/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 15/7
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 0 < 25 (soft target)
- **Structure:** ❌ Missing '## Vocabulary' header OR vocabulary sidecar
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 3 violations
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 98.2% (target 90-100% (grammar))
- **Richness:** ✅ 99% (grammar)
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ℹ️ PENDING — awaiting review

## Richness Details
**Score:** 99% (minimum: 95%)
**Module Type:** grammar

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| examples | 47 | 24 | 100% | 20% | 20.0% |
| engagement | 10 | 5 | 100% | 15% | 15.0% |
| dialogues | 6 | 4 | 100% | 15% | 15.0% |
| variety | 0.97 | - | 97% | 10% | 9.7% |
| cultural | 3 | 3 | 100% | 10% | 10.0% |
| realworld | 5 | 3 | 100% | 10% | 10.0% |
| visual | 21 | 3 | 100% | 5% | 5.0% |
| paragraph_var | 1.00 | - | 100% | 5% | 5.0% |
| questions | 17 | 5 | 100% | 5% | 5.0% |
| proverbs | 10 | 1 | 100% | 5% | 5.0% |
| **TOTAL** | | | | | **99.7%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 86 | Included in Core |
| **Вступ: Науковий дискурс** | ✅ | 739 | Included in Core |
| **Академічне письмо: Теорія та Практика** | ⚪️ | 590 | Skipped |
| **Порівняльний аналіз** | ✅ | 443 | Included in Core |
| **Практика** | ⚪️ | 395 | Skipped |
| **Підсумок** | ✅ | 175 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 59 | Skipped |