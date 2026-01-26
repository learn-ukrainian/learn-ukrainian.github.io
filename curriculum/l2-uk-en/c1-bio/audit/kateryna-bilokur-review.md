# Audit Report: M90 — kateryna-bilokur.md
**Level:** C1 | **Module:** M90 | **Phase:** C1 | **Pedagogy:** Not Specified | **Target:** 4000
**Naturalness:** 1/10 (PENDING)
**Overall Status:** ❌ FAIL
**Generated:** 2026-01-26 22:56:43

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
| 2 | fill-in | Мистецтвознавча лексика | 6 | 6 | ✅ |
| 3 | error-correction | Граматика в описі мистецтва | 5 | 5 | ✅ |
| 4 | match-up | Кольори та барви | 8 | 6 | ✅ |
| 5 | select | Аналіз стилю Білокур | 5 | 5 | ✅ |
| 6 | reading | Епістолярна спадщина Білокур | 3 | 1 | ✅ |
| 7 | group-sort | Жанри та інструменти | 16 | 1 | ✅ |
| 8 | fill-in | Прислівники та обставини | 6 | 6 | ✅ |
| 9 | error-correction | Складні речення | 5 | 5 | ✅ |
| 10 | quiz | Мистецький контекст | 5 | 5 | ✅ |
| 11 | true-false | Правда чи міф про Білокур | 12 | 5 | ✅ |
| 12 | essay-response | Творчий шлях Катерини Білокур | 1 | 1 | ✅ |
| 13 | comparative-study | Порівняння світів: Білокур та Примаченко | 1 | 1 | ✅ |

**Summary:**
- Total activities: 13 (target: 3-9) ❌
- Unique types: 10 (minimum: 3) ✅
- Priority types used: 4/6 (comparative-study, essay-response, quiz, reading) ✅
- Required types used: 6/6 (essay-response, fill-in, group-sort, match-up, quiz, reading) ✅
- Low density activities: 0

## PEDAGOGICAL VIOLATIONS
- **[YAML_SCHEMA_VIOLATION]** Schema error in kateryna-bilokur.yaml: Schema validation error at key '8': {'type': 'error-correction', 'title': 'Складні речення', 'items': [{'sentence': 'Хоча вона не мала офіційного диплома, але її талант визнали в усьому світі.', 'error': 'але', 'answer': 'none', 'options': ['хоча', 'але', 'визнали', 'none'], 'explanation': 'Для літературної мови краще уникати дублювання «хоча» та «але».'}, {'sentence': 'Вона малювала так старанно, що кожна квітка здавалася справді живою.', 'error': 'none', 'answer': '✓', 'options': ['що', 'старанно', 'здавалася', '✓'], 'explanation': 'Правильне вживання сполучника «що» у підрядному реченні.'}, {'sentence': 'Катерина знала, який колір краще пасує для пелюстки троянди.', 'error': 'none', 'answer': '✓', 'options': ['який', 'пасує', 'пелюстки', '✓'], 'explanation': 'Речення побудоване правильно.'}, {'sentence': 'Батьки не розуміли, чому їхня донька витрачає час на малювання.', 'error': 'none', 'answer': '✓', 'options': ['чому', 'витрачає', 'час', '✓'], 'explanation': 'Речення побудоване правильно.'}, {'sentence': 'Коли вона отримала визнання, її життя трохи полегшилося.', 'error': 'none', 'answer': '✓', 'options': ['коли', 'отримала', 'визнання', '✓'], 'explanation': 'Речення побудоване правильно.'}]} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## TEMPLATE COMPLIANCE
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Життєпис' per template 'c1-biography-module-template.md'
  - FIX: Add '## Життєпис' section as specified in docs/l2-uk-en/templates/c1-biography-module-template.md.md
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Внесок' per template 'c1-biography-module-template.md'
  - FIX: Add '## Внесок' section as specified in docs/l2-uk-en/templates/c1-biography-module-template.md.md

## Recommendation
**📝 UPDATE** (severity 25/100)

- 3 violations (minor)
- Structure issue: Missing '## Vocabulary' header OR vocabulary sidecar

## Gates
- **Words:** ❌ 2401/4000 (raw: 2718)
- **Activities:** ✅ 13/3
- **Density:** ✅ All > 1
- **Unique_types:** ✅ 10/3 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 6/5
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 0 < 24 (soft target)
- **Structure:** ❌ Missing '## Vocabulary' header OR vocabulary sidecar
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 1 violations
- **Content_heavy:** ⚠️ Too many activities: 13 (target 3-9)
- **Immersion:** 🇺🇦 99.8% (target 95-100% (biography))
- **Richness:** ✅ 97% (biography)
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ❌ 1/10 (PENDING) - Naturalness check required

## Richness Details
**Score:** 97% (minimum: 95%)
**Module Type:** biography

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| primary_sources | 10 | 4 | 100% | 19% | 19.0% |
| engagement | 6 | 6 | 100% | 14% | 14.3% |
| quotes | 14 | 3 | 100% | 14% | 14.3% |
| cultural | 3 | 4 | 75% | 10% | 7.1% |
| visual | 10 | 4 | 100% | 10% | 9.5% |
| timeline_markers | 30 | 8 | 100% | 10% | 9.5% |
| legacy | 10 | 2 | 100% | 10% | 9.5% |
| variety | 0.99 | - | 99% | 5% | 4.7% |
| paragraph_var | 1.00 | - | 100% | 5% | 4.8% |
| questions | 17 | 3 | 100% | 5% | 4.8% |
| **TOTAL** | | | | | **97.6%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 84 | Included in Core |
| **Вступ** | ✅ | 236 | Included in Core |
| **Біографія** | ⚪️ | 884 | Skipped |
| **Історичний контекст** | ✅ | 315 | Included in Core |
| **Порівняльний аналіз** | ✅ | 170 | Included in Core |
| **Есе** | ⚪️ | 0 | Skipped |
| **Тема** | ⚪️ | 55 | Skipped |
| **Критерії оцінювання** | ⚪️ | 0 | Skipped |
| **Зразок відповіді** | ⚪️ | 334 | Skipped |
| **Підсумок** | ✅ | 57 | Included in Core |
| **Практикум рефлексії** | ⚪️ | 131 | Skipped |
| **Потрібно більше практики?** | ⚪️ | 135 | Skipped |