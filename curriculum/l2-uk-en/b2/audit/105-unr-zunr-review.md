# Audit Report: 105-unr-zunr.md
**Phase:** B2 | **Level:** B2 | **Pedagogy:** CBI | **Target:** 2000
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[YAML_SCHEMA_VIOLATION]** Schema error in 105-unr-zunr.yaml: [revolution-facts] quiz: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 105-unr-zunr.yaml: [universals-match] match-up: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 105-unr-zunr.yaml: [zluky-text] cloze: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 105-unr-zunr.yaml: [chronology-1917] match-up: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 105-unr-zunr.yaml: [myths-unr] true-false: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 105-unr-zunr.yaml: [leaders-sort] group-sort: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 105-unr-zunr.yaml: [synonyms] select: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 105-unr-zunr.yaml: [find-politics] mark-the-words: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 105-unr-zunr.yaml: [grammar-passive] cloze: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 105-unr-zunr.yaml: [vocab-defs-2] match-up: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 105-unr-zunr.yaml: [final-test] quiz: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 105-unr-zunr.yaml: [geography-match] match-up: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 105-unr-zunr.yaml: [unr-lessons] essay-response: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## TEMPLATE COMPLIANCE
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Вступ|Контекст|Розминка' per template 'b2-history-module-template'
  - FIX: Add '## Вступ' section as specified in docs/l2-uk-en/templates/b2-history-module-template.md
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Читання' per template 'b2-history-module-template'
  - FIX: Add '## Читання' section as specified in docs/l2-uk-en/templates/b2-history-module-template.md
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Первинні джерела' per template 'b2-history-module-template'
  - FIX: Add '## Первинні джерела' section as specified in docs/l2-uk-en/templates/b2-history-module-template.md
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Деколонізаційний погляд' per template 'b2-history-module-template'
  - FIX: Add '## Деколонізаційний погляд' section as specified in docs/l2-uk-en/templates/b2-history-module-template.md
- ⚠️ **[MISSING_REQUIRED_CALLOUT]** Missing required callout '[!myth-buster]' per template 'b2-history-module-template'
  - FIX: Add a `> [!myth-buster]` box as specified in the template. This enhances module quality.
- ⚠️ **[MISSING_REQUIRED_CALLOUT]** Missing required callout '[!history-bite]' per template 'b2-history-module-template'
  - FIX: Add a `> [!history-bite]` box as specified in the template. This enhances module quality.

## Recommendation
**📝 UPDATE** (severity 50/100)

- Revision recommended (severity 50/100)
- 19 violations (severe - consider revision)

## Gates
- **Words:** ✅ 2111/2000
- **Activities:** ✅ 14/10
- **Density:** ✅ All > 14
- **Unique_types:** ✅ 9/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 10/5
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 90/20
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 13 violations
- **Content_heavy:** ⚠️ 1 cloze with year blanks
- **Immersion:** 🇺🇦 99.0% (target 98-100% (history))
- **Richness:** ✅ 99% (history)
- **Grammar:** ⏳ Pending validation

## Richness Details
**Score:** 99% (minimum: 95%)
**Module Type:** history

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| primary_sources | 14 | 3 | 100% | 24% | 23.8% |
| engagement | 10 | 6 | 100% | 14% | 14.3% |
| timeline_markers | 30 | 10 | 100% | 14% | 14.3% |
| decolonization | 15 | 2 | 100% | 14% | 14.3% |
| cultural | 10 | 4 | 100% | 10% | 9.5% |
| visual | 12 | 4 | 100% | 10% | 9.5% |
| variety | 1.00 | - | 100% | 5% | 4.8% |
| paragraph_var | 1.00 | - | 100% | 5% | 4.8% |
| questions | 7 | 3 | 100% | 5% | 4.8% |
| **TOTAL** | | | | | **100.0%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 0 | Included in Core |
| **1917: Весна народів** | ⚪️ | 90 | Skipped |
| **Чотири Універсали: шлях до свободи** | ⚪️ | 98 | Skipped |
| **Крути: бій за майбутнє** | ⚪️ | 297 | Skipped |
| **Гетьманат і Директорія** | ⚪️ | 137 | Skipped |
| **Культурний фронт: Гроші, Тризуб і Щедрик** | ✅ | 195 | Included in Core |
| **Символи держави: Тризуб і Прапор** | ⚪️ | 156 | Skipped |
| **Махновщина: Третя сила** | ⚪️ | 89 | Skipped |
| **Холодний Яр: Фортеця волі** | ⚪️ | 76 | Skipped |
| **Зимові походи: Лицарі абсурду** | ⚪️ | 91 | Skipped |
| **Акт Злуки: об'єднання земель** | ⚪️ | 121 | Skipped |
| **Трагедія «Трикутника смерті»** | ⚪️ | 111 | Skipped |
| **Еміграція: Збереження Держави** | ⚪️ | 189 | Skipped |
| **Жінки в Революції: Невидимі герої** | ⚪️ | 153 | Skipped |
| **Культура опору: Поезія в окопах** | ✅ | 118 | Included in Core |
| **Підсумок** | ✅ | 80 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 110 | Skipped |