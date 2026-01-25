# Audit Report: M04 — 04-analysis-vocabulary.md
**Level:** C1 | **Module:** M04 | **Phase:** C1.1 | **Pedagogy:** Not Specified | **Target:** 3000
**Naturalness:** None/10 (PENDING)
**Overall Status:** ❌ FAIL
**Generated:** 2026-01-25 19:24:06

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
| 1 | match-up | Ключові терміни аналізу | 8 | 6 | ✅ |
| 2 | quiz | Розуміння академічного тексту | 8 | 5 | ✅ |
| 3 | fill-in | Вибір прикметника | 8 | 6 | ✅ |
| 4 | group-sort | Етапи дослідження | 12 | 12 | ✅ |
| 5 | match-up | Словотвір: Іменник -> Прикметник | 8 | 6 | ✅ |
| 6 | fill-in | Академічні колокації | 8 | 6 | ✅ |
| 7 | match-up | Синоніми в академічному стилі | 8 | 6 | ✅ |
| 8 | quiz | Визначення регістру | 8 | 5 | ✅ |
| 9 | error-correction | Виправлення лексичних помилок | 8 | 5 | ✅ |
| 10 | unjumble | Побудова академічних речень | 8 | 5 | ✅ |
| 11 | mark-the-words | Пошук слів аналізу | 10 | 5 | ✅ |
| 12 | fill-in | Структура анотації | 8 | 6 | ✅ |
| 13 | match-up | Антоніми в аналізі | 8 | 6 | ✅ |
| 14 | quiz | Логіка та аргументація | 8 | 5 | ✅ |
| 15 | group-sort | Суб'єктивність vs Об'єктивність | 12 | 12 | ✅ |
| 16 | essay-response | Есе: Роль критичного мислення | 1 | 1 | ✅ |
| 17 | fill-in | Прийменники в колокаціях | 8 | 6 | ✅ |
| 18 | match-up | Академічні вирази | 8 | 6 | ✅ |

**Summary:**
- Total activities: 18 (target: 12-16) ❌
- Unique types: 8 (minimum: 4) ✅
- Priority types used: 3/3 (error-correction, fill-in, unjumble) ✅
- Required types used: 5/6 (essay-response, fill-in, group-sort, match-up, quiz) ❌
- Low density activities: 0

## PEDAGOGICAL VIOLATIONS
- **[YAML_SCHEMA_VIOLATION]** Schema error in 04-analysis-vocabulary.yaml: Schema validation error at key 'words': ['Глибокий', 'аналіз', 'зібраних', 'даних', 'дозволив', 'вченим', 'виявити', 'приховані', 'закономірності', 'розвитку', 'системи'] is too short
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## Recommendation
**📝 UPDATE** (severity 25/100)

- 1 violations (minor)
- Structure issue: Missing '## Vocabulary' header OR vocabulary sidecar

## Gates
- **Words:** ❌ 2546/3000 (raw: 2890)
- **Activities:** ✅ 18/12
- **Density:** ✅ All > 12
- **Unique_types:** ✅ 8/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 12/7
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 0 < 25 (soft target)
- **Structure:** ❌ Missing '## Vocabulary' header OR vocabulary sidecar
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 1 violations
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 96.9% (target 90-100% (vocab))
- **Richness:** ✅ 97% (vocabulary)
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ❌ None/10 (PENDING) - Naturalness check required

## Richness Details
**Score:** 97% (minimum: 95%)
**Module Type:** vocabulary

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| collocations | 18 | 20 | 90% | 25% | 22.5% |
| usage_examples | 62 | 15 | 100% | 20% | 20.0% |
| engagement | 12 | 4 | 100% | 15% | 15.0% |
| cultural | 4 | 3 | 100% | 10% | 10.0% |
| visual | 15 | 3 | 100% | 10% | 10.0% |
| register_notes | 8 | 5 | 100% | 10% | 10.0% |
| variety | 0.98 | - | 98% | 5% | 4.9% |
| paragraph_var | 1.00 | - | 100% | 5% | 5.0% |
| **TOTAL** | | | | | **97.4%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 116 | Included in Core |
| **Лексика для критики** | ⚪️ | 135 | Skipped |
| **Вступ: Презентація - Мистецтво наукового сумніву** | ✅ | 991 | Included in Core |
| **Академічне письмо: Побудова аргументації** | ⚪️ | 350 | Skipped |
| **Порівняльний аналіз** | ✅ | 331 | Included in Core |
| **Типові помилки в аналітичних текстах** | ✅ | 157 | Included in Core |
| **Чек-лист: Самоперевірка** | ⚪️ | 150 | Skipped |
| **Практика письма: Рецензія** | ⚪️ | 134 | Skipped |
| **Підсумок** | ✅ | 134 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 48 | Skipped |