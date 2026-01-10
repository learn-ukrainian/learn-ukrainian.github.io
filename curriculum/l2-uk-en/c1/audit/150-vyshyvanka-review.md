# Audit Report: 150-vyshyvanka.md
**Phase:** C1.5 | **Level:** C1 | **Pedagogy:** CBI | **Target:** 2000
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[YAML_SCHEMA_VIOLATION]** Schema error in 150-vyshyvanka.yaml: [150-act-01] quiz: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 150-vyshyvanka.yaml: [150-act-02] match-up: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 150-vyshyvanka.yaml: [150-act-03] fill-in: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 150-vyshyvanka.yaml: [150-act-04] critical-analysis: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 150-vyshyvanka.yaml: [150-act-06] essay-response: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 150-vyshyvanka.yaml: [150-act-08] true-false: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 150-vyshyvanka.yaml: [150-act-09] select: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 150-vyshyvanka.yaml: [150-act-10] error-correction: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 150-vyshyvanka.yaml: [150-act-11] group-sort: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 150-vyshyvanka.yaml: [150-act-12] unjumble: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## TEMPLATE COMPLIANCE
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Потрібно більше практики?' per template 'b2-history-module-template'
  - FIX: Add '## Потрібно більше практики?' section as specified in docs/l2-uk-en/templates/b2-history-module-template.md

## Recommendation
**📝 UPDATE** (severity 50/100)

- Revision recommended (severity 50/100)
- 11 violations (severe - consider revision)

## Gates
- **Words:** ⚠️ 1956/2000 (44 short)
- **Activities:** ✅ 12/12
- **Density:** ✅ All > 12
- **Unique_types:** ✅ 12/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 7/7
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 29/25
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
| timeline_markers | 12 | 10 | 100% | 14% | 14.3% |
| decolonization | 6 | 2 | 100% | 14% | 14.3% |
| cultural | 9 | 4 | 100% | 10% | 9.5% |
| visual | 8 | 4 | 100% | 10% | 9.5% |
| variety | 0.97 | - | 97% | 5% | 4.6% |
| paragraph_var | 1.00 | - | 100% | 5% | 4.8% |
| questions | 7 | 3 | 100% | 5% | 4.8% |
| **TOTAL** | | | | | **99.9%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 96 | Included in Core |
| **Вступ: Генетичний код нації у стібках** | ⚪️ | 138 | Skipped |
| **Семантика орнаменту: Геометрія духу та природи** | ⚪️ | 278 | Skipped |
| **Техніки вишивки: Крізь терни до візуальної досконалості** | ⚪️ | 233 | Skipped |
| **Символіка чоловічої vs жіночої сорочки** | ⚪️ | 102 | Skipped |
| **Регіональні стилі: Етнографічна карта України на полотні** | ⚪️ | 173 | Skipped |
| **Деколонізаційний погляд: Вишиванка як політичний маніфест** | ⚪️ | 126 | Skipped |
| **Хронологія нитки, голки та волі народу** | ⚪️ | 128 | Skipped |
| **Читання: Поезія вишитого рушника як метафора долі** | ✅ | 131 | Included in Core |
| **Первинні джерела: Інтелектуальна праця голки** | ⚪️ | 65 | Skipped |
| **Специфіка білого вишивання: Світло на світлі** | ⚪️ | 77 | Skipped |
| **Вишиванка як сучасна інтелектуальна зброя та дипломатія** | ⚪️ | 85 | Skipped |
| **Обрядова культура догляду** | ✅ | 150 | Included in Core |
| **Need More Practice?** | ⚪️ | 55 | Skipped |
| **Підсумок** | ✅ | 119 | Included in Core |