# Audit Report: 148-rehionalni-tantsi.md
**Phase:** C1.5 | **Level:** C1 | **Pedagogy:** CBI | **Target:** 2000
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[YAML_SCHEMA_VIOLATION]** Schema error in 148-rehionalni-tantsi.yaml: [148-act-01] quiz: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 148-rehionalni-tantsi.yaml: [148-act-02] match-up: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 148-rehionalni-tantsi.yaml: [148-act-03] fill-in: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 148-rehionalni-tantsi.yaml: [148-act-04] critical-analysis: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 148-rehionalni-tantsi.yaml: [148-act-06] essay-response: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 148-rehionalni-tantsi.yaml: [148-act-08] true-false: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 148-rehionalni-tantsi.yaml: [148-act-09] select: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 148-rehionalni-tantsi.yaml: [148-act-10] error-correction: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 148-rehionalni-tantsi.yaml: [148-act-11] group-sort: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 148-rehionalni-tantsi.yaml: [148-act-12] unjumble: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## TEMPLATE COMPLIANCE
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Потрібно більше практики?' per template 'b2-history-module-template'
  - FIX: Add '## Потрібно більше практики?' section as specified in docs/l2-uk-en/templates/b2-history-module-template.md

## Recommendation
**📝 UPDATE** (severity 50/100)

- Revision recommended (severity 50/100)
- 11 violations (severe - consider revision)

## Gates
- **Words:** ⚠️ 1903/2000 (97 short)
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
- **Immersion:** 🇺🇦 99.7% (target 98-100% (history))
- **Richness:** ✅ 100% (history)
- **Grammar:** ⏳ Pending validation

## Richness Details
**Score:** 100% (minimum: 95%)
**Module Type:** history

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| primary_sources | 7 | 3 | 100% | 24% | 23.8% |
| engagement | 7 | 6 | 100% | 14% | 14.3% |
| timeline_markers | 13 | 10 | 100% | 14% | 14.3% |
| decolonization | 5 | 2 | 100% | 14% | 14.3% |
| cultural | 6 | 4 | 100% | 10% | 9.5% |
| visual | 9 | 4 | 100% | 10% | 9.5% |
| variety | 1.00 | - | 100% | 5% | 4.8% |
| paragraph_var | 1.00 | - | 100% | 5% | 4.8% |
| questions | 5 | 3 | 100% | 5% | 4.8% |
| **TOTAL** | | | | | **100.0%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 86 | Included in Core |
| **Вступ: Географія українського руху** | ⚪️ | 80 | Skipped |
| **Аркан: Священний танець чоловічої ініціації** | ⚪️ | 266 | Skipped |
| **Коломийка: Нескінченний вихор народної душі** | ⚪️ | 185 | Skipped |
| **Танці Центральної України: Метелиця та Голуб** | ⚪️ | 91 | Skipped |
| **Деколонізаційний погляд: Проти примітивізації культури** | ✅ | 91 | Included in Core |
| **Танці Півдня та Полісся: Між степом і лісом** | ⚪️ | 72 | Skipped |
| **Закарпатський Чардаш та Буковинська Полька: Гібридність краси** | ⚪️ | 78 | Skipped |
| **Спадщина: Від сільської площі до Карнеґі-холу** | ⚪️ | 77 | Skipped |
| **Аналіз руху: Бартка як продовження душі** | ✅ | 71 | Included in Core |
| **Хронологія наукової документації танцю** | ⚪️ | 103 | Skipped |
| **Читання: Екзистенційний опис коломийки** | ✅ | 103 | Included in Core |
| **Первинні джерела: Методологія Василя Верховинця** | ⚪️ | 84 | Skipped |
| **Порівняльна стилістика: Гірські vs Степові танці** | ⚪️ | 0 | Skipped |
| **Специфіка Буковини: Аристократизм та статус** | ⚪️ | 72 | Skipped |
| **Сучасний стан регіональних танців** | ⚪️ | 95 | Skipped |
| **Музична магія: Троїсті музики** | ⚪️ | 129 | Skipped |
| **Need More Practice?** | ⚪️ | 87 | Skipped |
| **Підсумок** | ✅ | 133 | Included in Core |