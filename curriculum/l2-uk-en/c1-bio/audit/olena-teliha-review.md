# Audit Report: M92 — olena-teliha.md

**Level:** C1 | **Module:** M92 | **Phase:** C1 | **Pedagogy:** Not Specified | **Target:** 4000
**Naturalness:** 1/10 (PENDING)
**Overall Status:** ❌ FAIL
**Generated:** 2026-01-26 22:56:44

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
| 2 | fill-in | Лексика патріотичного спротиву | 6 | 6 | ✅ |
| 3 | error-correction | Граматика в історичному наративі | 5 | 5 | ✅ |
| 4 | match-up | Термінологія та ідеологеми | 8 | 6 | ✅ |
| 5 | select | Лінгвістичний та ідейний аналіз | 5 | 5 | ✅ |
| 6 | group-sort | Тематична класифікація лексики | 18 | 1 | ✅ |
| 7 | fill-in | Прислівники та характеристики вчинків | 6 | 6 | ✅ |
| 8 | error-correction | Складні синтаксичні структури | 5 | 5 | ✅ |
| 9 | quiz | Критичне мислення та аналіз | 5 | 5 | ✅ |
| 10 | true-false | Правда чи міф про Олену Телігу | 12 | 5 | ✅ |
| 11 | essay-response | Поезія і чин у моєму розумінні | 1 | 1 | ✅ |
| 12 | comparative-study | Жіночий героїзм: Теліга та Леся Українка | 1 | 1 | ✅ |

**Summary:**
- Total activities: 12 (target: 3-9) ❌
- Unique types: 9 (minimum: 3) ✅
- Priority types used: 3/6 (comparative-study, essay-response, quiz) ✅
- Required types used: 5/6 (essay-response, fill-in, group-sort, match-up, quiz) ❌
- Low density activities: 0

## PEDAGOGICAL VIOLATIONS

- **[YAML_SCHEMA_VIOLATION]** Schema error in olena-teliha.yaml: Schema validation error at key '7': {'type': 'error-correction', 'title': 'Складні синтаксичні структури', 'items': [{'sentence': 'Хоча друзі просили її поїхати, проте вона залишилася.', 'error': 'проте', 'answer': 'none', 'options': ['хоча', 'проте', 'залишилася', 'none'], 'explanation': 'Вживання «проте» після «хоча» є стилістично надлишковим у літературній мові.'}, {'sentence': 'Теліга була жінкою яка не знала страху.', 'error': 'жінкою яка', 'answer': 'жінкою, яка', 'options': ['жінкою яка', 'жінкою, яка', 'жінкою: яка', 'none'], 'explanation': 'Перед сполучним словом «яка» у підрядному реченні ставиться кома.'}, {'sentence': 'Вона знала що за нею прийдуть з Гестапо.', 'error': 'знала що', 'answer': 'знала, що', 'options': ['знала що', 'знала, що', 'знала: що', 'none'], 'explanation': 'Кома перед сполучником «що».'}, {'sentence': 'Читаючи її вірші, ми відчуваємо подих епохи.', 'error': 'none', 'answer': '✓', 'options': ['читаючи', 'її', 'відчуваємо', '✓'], 'explanation': 'Речення з дієприслівниковим зворотом побудоване правильно.'}, {'sentence': 'Вона хотіла щоб Україна була вільною та незалежною.', 'error': 'хотіла щоб', 'answer': 'хотіла, щоб', 'options': ['хотіла щоб', 'хотіла, щоб', 'хотіла: щоб', 'none'], 'explanation': 'Кома перед сполучником «щоб».'}]} is not valid under any of the given schemas
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

- **Words:** ❌ 2009/4000 (raw: 2273)
- **Activities:** ✅ 12/3
- **Density:** ✅ All > 1
- **Unique_types:** ✅ 9/3 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 6/5
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 0 < 24 (soft target)
- **Structure:** ❌ Missing '## Vocabulary' header OR vocabulary sidecar
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 1 violations
- **Content_heavy:** ⚠️ Too many activities: 12 (target 3-9)
- **Immersion:** 🇺🇦 100.0% (target 95-100% (biography))
- **Richness:** ✅ 99% (biography)
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ❌ 1/10 (PENDING) - Naturalness check required

## Richness Details

**Score:** 99% (minimum: 95%)
**Module Type:** biography

### Score Breakdown

| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| primary_sources | 8 | 4 | 100% | 19% | 19.0% |
| engagement | 6 | 6 | 100% | 14% | 14.3% |
| quotes | 9 | 3 | 100% | 14% | 14.3% |
| cultural | 4 | 4 | 100% | 10% | 9.5% |
| visual | 10 | 4 | 100% | 10% | 9.5% |
| timeline_markers | 27 | 8 | 100% | 10% | 9.5% |
| legacy | 15 | 2 | 100% | 10% | 9.5% |
| variety | 0.97 | - | 97% | 5% | 4.6% |
| paragraph_var | 1.00 | - | 100% | 5% | 4.8% |
| questions | 16 | 3 | 100% | 5% | 4.8% |
| **TOTAL** | | | | | **99.9%** |

## Section Audit

| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 69 | Included in Core |
| **Вступ** | ✅ | 194 | Included in Core |
| **Біографія** | ⚪️ | 646 | Skipped |
| **Історичний контекст** | ✅ | 296 | Included in Core |
| **Порівняльний аналіз** | ✅ | 139 | Included in Core |
| **Есе** | ⚪️ | 0 | Skipped |
| **Тема** | ⚪️ | 56 | Skipped |
| **Критерії оцінювання** | ⚪️ | 0 | Skipped |
| **Зразок відповіді** | ⚪️ | 318 | Skipped |
| **Підсумок** | ✅ | 47 | Included in Core |
| **Практикум рефлексії** | ⚪️ | 132 | Skipped |
| **Потрібно більше практики?** | ⚪️ | 112 | Skipped |
