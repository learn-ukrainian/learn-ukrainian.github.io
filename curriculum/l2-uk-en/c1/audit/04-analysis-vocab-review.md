# Audit Report: 04-analysis-vocab.md
**Phase:** C1.1 | **Level:** C1 | **Pedagogy:** Lexical Approach | **Target:** 1750
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[YAML_SCHEMA_VIOLATION]** Schema error in 04-analysis-vocab.yaml: [fill-in-text1] fill-in: 'items.7' - 'sentence' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 04-analysis-vocab.yaml: [fill-in-text2] fill-in: 'items.7' - 'sentence' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 04-analysis-vocab.yaml: [fill-in-prepositions] fill-in: 'items.7' - 'sentence' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 04-analysis-vocab.yaml: [essay-problem-analysis] essay-response: 'min_words' - 60 is less than the minimum of 100
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## TEMPLATE COMPLIANCE
- ❌ **[DUPLICATE_SYNONYMOUS_HEADERS]** Multiple aliases for 'Аналіз' found: Наукова об'єктивність: Глибина аналізу, Лексика аналізу: Аспекти, Фактори, Тенденції, Скелет аналізу: Абстрактні іменники
  - FIX: Keep only one version of the header (preferably the primary one or the one with more content).
- ❌ **[EMPTY_REQUIRED_SECTION]** Required section '## Потрібно більше практики?' is empty
  - FIX: Populate the section with meaningful content or generate it if it's a mandatory placeholder.

## Recommendation
**📝 UPDATE** (severity 15/100)

- 6 violations (moderate)

## Gates
- **Words:** ✅ 1984/1750
- **Activities:** ✅ 17/12
- **Density:** ✅ All > 12
- **Unique_types:** ✅ 6/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 11/7
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 30/25
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 4 violations
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 98.8% (target 98-100% (vocab))
- **Richness:** ✅ 98% (vocabulary)
- **Grammar:** ⏳ Pending validation

## Richness Details
**Score:** 98% (minimum: 95%)
**Module Type:** vocabulary

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| collocations | 28 | 20 | 100% | 25% | 25.0% |
| usage_examples | 40 | 15 | 100% | 20% | 20.0% |
| engagement | 11 | 4 | 100% | 15% | 15.0% |
| cultural | 3 | 3 | 100% | 10% | 10.0% |
| visual | 17 | 3 | 100% | 10% | 10.0% |
| register_notes | 5 | 5 | 100% | 10% | 10.0% |
| variety | 0.93 | - | 93% | 5% | 4.7% |
| paragraph_var | 0.69 | - | 69% | 5% | 3.4% |
| **TOTAL** | | | | | **98.1%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 46 | Included in Core |
| **Скелет аналізу: Абстрактні іменники** | ✅ | 362 | Included in Core |
| **Текст 1: Анатомія кризи** | ✅ | 146 | Included in Core |
| **Оцінні прикметники: Вага слів** | ⚪️ | 316 | Skipped |
| **Текст 2: Зміна парадигм** | ✅ | 87 | Included in Core |
| **Синтаксис: Ланцюжки іменників** | ⚪️ | 105 | Skipped |
| **Текст 3: Есе "Критерії успіху"** | ✅ | 124 | Included in Core |
| **Культурний контекст: Українська думка** | ✅ | 122 | Included in Core |
| **Текст 4: Олександр Потебня і філософія мови** | ✅ | 183 | Included in Core |
| **Наукова об'єктивність: Глибина аналізу** | ✅ | 140 | Included in Core |
| **Діалог: Наукова дискусія** | ✅ | 60 | Included in Core |
| **Стилістичний практикум** | ⚪️ | 126 | Skipped |
| **Практика** | ⚪️ | 37 | Skipped |
| **Самоперевірка** | ⚪️ | 37 | Skipped |
| **Summary** | ✅ | 93 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 0 | Skipped |