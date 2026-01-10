# Audit Report: 146-kolyskovi-ta-dumy.md
**Phase:** C1.5 | **Level:** C1 | **Pedagogy:** CBI | **Target:** 2000
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[YAML_SCHEMA_VIOLATION]** Schema error in 146-kolyskovi-ta-dumy.yaml: [146-act-01] quiz: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 146-kolyskovi-ta-dumy.yaml: [146-act-02] match-up: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 146-kolyskovi-ta-dumy.yaml: [146-act-03] fill-in: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 146-kolyskovi-ta-dumy.yaml: [146-act-04] critical-analysis: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 146-kolyskovi-ta-dumy.yaml: [146-act-06] essay-response: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 146-kolyskovi-ta-dumy.yaml: [146-act-08] true-false: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 146-kolyskovi-ta-dumy.yaml: [146-act-09] select: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 146-kolyskovi-ta-dumy.yaml: [146-act-10] error-correction: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 146-kolyskovi-ta-dumy.yaml: [146-act-11] group-sort: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 146-kolyskovi-ta-dumy.yaml: [146-act-12] unjumble: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## TEMPLATE COMPLIANCE
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Потрібно більше практики?' per template 'b2-history-module-template'
  - FIX: Add '## Потрібно більше практики?' section as specified in docs/l2-uk-en/templates/b2-history-module-template.md

## Recommendation
**📝 UPDATE** (severity 50/100)

- Revision recommended (severity 50/100)
- 11 violations (severe - consider revision)

## Gates
- **Words:** ✅ 2086/2000
- **Activities:** ✅ 12/12
- **Density:** ✅ All > 12
- **Unique_types:** ✅ 12/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 7/7
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 28/25
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 10 violations
- **Content_heavy:** ✅ Content-heavy OK (12 activities)
- **Immersion:** 🇺🇦 99.5% (target 98-100% (history))
- **Richness:** ✅ 99% (history)
- **Grammar:** ⏳ Pending validation

## Richness Details
**Score:** 99% (minimum: 95%)
**Module Type:** history

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| primary_sources | 6 | 3 | 100% | 24% | 23.8% |
| engagement | 7 | 6 | 100% | 14% | 14.3% |
| timeline_markers | 17 | 10 | 100% | 14% | 14.3% |
| decolonization | 15 | 2 | 100% | 14% | 14.3% |
| cultural | 7 | 4 | 100% | 10% | 9.5% |
| visual | 8 | 4 | 100% | 10% | 9.5% |
| variety | 0.96 | - | 96% | 5% | 4.6% |
| paragraph_var | 1.00 | - | 100% | 5% | 4.8% |
| questions | 9 | 3 | 100% | 5% | 4.8% |
| **TOTAL** | | | | | **99.8%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 75 | Included in Core |
| **Вступ: Код національної пам'яті** | ⚪️ | 165 | Skipped |
| **Колискова: Магія першого слова** | ⚪️ | 293 | Skipped |
| **Думи: Епос волі та туги** | ⚪️ | 240 | Skipped |
| **Кобзарство як духовна інституція** | ⚪️ | 186 | Skipped |
| **Читання: Дума про Марусю Богуславку** | ✅ | 138 | Included in Core |
| **Первинні джерела: Свідчення про кобзарів** | ⚪️ | 84 | Skipped |
| **Деколонізаційний погляд** | ⚪️ | 152 | Skipped |
| **Регіональні особливості: Різноголосся України** | ⚪️ | 106 | Skipped |
| **Сучасні інтерпретації: Від автентики до року** | ⚪️ | 204 | Skipped |
| **Аналіз образів: Козак-нетяга** | ✅ | 87 | Included in Core |
| **Хронологія кобзарської долі** | ⚪️ | 135 | Skipped |
| **Порівняльна стилістика: Інтимність vs Епічність** | ⚪️ | 0 | Skipped |
| **Need More Practice?** | ⚪️ | 100 | Skipped |
| **Підсумок** | ✅ | 121 | Included in Core |