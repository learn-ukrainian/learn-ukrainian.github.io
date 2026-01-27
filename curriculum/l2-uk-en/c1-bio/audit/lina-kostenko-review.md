# Audit Report: M105 — lina-kostenko.md

**Level:** C1 | **Module:** M105 | **Phase:** C1 | **Pedagogy:** Not Specified | **Target:** 4000
**Naturalness:** 9/10 (PASS)
**Overall Status:** ❌ FAIL
**Generated:** 2026-01-26 22:56:49

## Configuration

**Type:** C1-biography
**Word Target:** 4000 words
**Activities:** 3-9 required
**Items per Activity:** ≥1 items
**Unique Types:** ≥3 types required
**Priority Types:** authorial-intent, comparative-study, critical-analysis, essay-response, quiz, reading
**Required Types:** essay-response, fill-in, group-sort, match-up, quiz, reading
**Engagement:** ≥5 callouts
**Immersion:** 95-100%
**Vocab Target:** ≥24 words
**Transliteration:** Not allowed

## Activity Breakdown

| # | Type | Title | Items | Min | Status |
|---|------|-------|-------|-----|--------|
| 1 | quiz | Розуміння біографії | 5 | 5 | ✅ |
| 2 | fill-in | Лексика поезії та моралі | 6 | 6 | ✅ |
| 3 | error-correction | Граматика в тексті про поетесу | 5 | 5 | ✅ |
| 4 | match-up | Поняття та асоціації | 8 | 6 | ✅ |
| 5 | select | Аналіз творчості та позиції | 5 | 5 | ✅ |
| 6 | group-sort | Твори та поняття | 15 | 1 | ✅ |
| 7 | fill-in | Прислівники та характеристики | 6 | 6 | ✅ |
| 8 | error-correction | Складні речення | 5 | 5 | ✅ |
| 9 | quiz | Критичне мислення | 5 | 5 | ✅ |
| 10 | true-false | Правда чи міф | 12 | 5 | ✅ |
| 11 | essay-response | Сила одного слова | 1 | 1 | ✅ |
| 12 | comparative-study | Дві поетеси: Костенко і Ахматова | 1 | 1 | ✅ |

**Summary:**
- Total activities: 12 (target: 3-9) ❌
- Unique types: 9 (minimum: 3) ✅
- Priority types used: 3/6 (comparative-study, essay-response, quiz) ✅
- Required types used: 5/6 (essay-response, fill-in, group-sort, match-up, quiz) ❌
- Low density activities: 0

## PEDAGOGICAL VIOLATIONS

- **[YAML_SCHEMA_VIOLATION]** Schema error in lina-kostenko.yaml: Schema validation error at key '7': {'type': 'error-correction', 'title': 'Складні речення', 'items': [{'sentence': 'Ліна яка не писала віршів мовчала.', 'error': 'Ліна яка', 'answer': 'Ліна, яка', 'options': ['Ліна яка', 'Ліна, яка', 'Ліна: яка', 'none'], 'explanation': 'Виділення підрядного речення комами.'}, {'sentence': 'Вона сказала що не носить біжутерії.', 'error': 'сказала що', 'answer': 'сказала, що', 'options': ['сказала що', 'сказала, що', 'сказала: що', 'none'], 'explanation': 'Кома перед «що».'}, {'sentence': 'Коли вийшов роман його розкупили.', 'error': 'роман його', 'answer': 'роман, його', 'options': ['роман його', 'роман, його', 'роман: його', 'none'], 'explanation': 'Кома між частинами складного речення.'}, {'sentence': 'Це була жінка, яку поважали всі.', 'error': 'none', 'answer': '✓', 'options': ['жінка', 'яку', 'поважали', '✓'], 'explanation': 'Речення побудоване правильно.'}, {'sentence': 'Вона знала, що правда переможе.', 'error': 'none', 'answer': '✓', 'options': ['знала', 'що', 'правда', '✓'], 'explanation': 'Речення побудоване правильно.'}]} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## Recommendation

**📝 UPDATE** (severity 25/100)

- 1 violations (minor)
- Structure issue: Missing '## Vocabulary' header OR vocabulary sidecar

## Gates

- **Words:** ❌ 2647/4000 (raw: 2958)
- **Activities:** ✅ 12/3
- **Density:** ✅ All > 1
- **Unique_types:** ✅ 9/3 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 14/5
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 0 < 24 (soft target)
- **Structure:** ❌ Missing '## Vocabulary' header OR vocabulary sidecar
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 1 violations
- **Content_heavy:** ⚠️ Too many activities: 12 (target 3-9)
- **Immersion:** 🇺🇦 99.9% (target 95-100% (biography))
- **Richness:** ❌ 92% < 95% min (biography)
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ✅ 9/10 (High)

## Richness Details

**Score:** 92% (minimum: 95%)
**Module Type:** biography

### Score Breakdown

| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| primary_sources | 15 | 4 | 100% | 19% | 19.0% |
| engagement | 14 | 6 | 100% | 14% | 14.3% |
| quotes | 15 | 3 | 100% | 14% | 14.3% |
| cultural | 1 | 4 | 25% | 10% | 2.4% |
| visual | 17 | 4 | 100% | 10% | 9.5% |
| timeline_markers | 30 | 8 | 100% | 10% | 9.5% |
| legacy | 15 | 2 | 100% | 10% | 9.5% |
| variety | 0.98 | - | 98% | 5% | 4.7% |
| paragraph_var | 1.00 | - | 100% | 5% | 4.8% |
| questions | 22 | 3 | 100% | 5% | 4.8% |
| **TOTAL** | | | | | **92.8%** |

## Section Audit

| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 85 | Included in Core |
| **Вступ** | ✅ | 231 | Included in Core |
| **Життєпис** | ⚪️ | 590 | Skipped |
| **Внесок** | ⚪️ | 55 | Skipped |
| **Сучасний етап** | ⚪️ | 228 | Skipped |
| **Історичний контекст** | ✅ | 318 | Included in Core |
| **Вплив** | ⚪️ | 204 | Skipped |
| **Порівняльний аналіз** | ✅ | 164 | Included in Core |
| **Есе** | ⚪️ | 0 | Skipped |
| **Тема** | ⚪️ | 57 | Skipped |
| **Критерії оцінювання** | ⚪️ | 0 | Skipped |
| **Зразок відповіді** | ⚪️ | 356 | Skipped |
| **Підсумок** | ✅ | 53 | Included in Core |
| **Практикум рефлексії** | ⚪️ | 173 | Skipped |
| **Потрібно більше практики?** | ⚪️ | 133 | Skipped |
