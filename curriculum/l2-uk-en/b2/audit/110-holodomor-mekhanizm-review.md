# Audit Report: 110-holodomor-mekhanizm.md
**Phase:** B2.3c | **Level:** B2 | **Pedagogy:** CBI | **Target:** 2000
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[YAML_SCHEMA_VIOLATION]** Schema error in 110-holodomor-mekhanizm.yaml: [розуміння-механізму-голодомору] quiz: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 110-holodomor-mekhanizm.yaml: [лексика-голодомору] fill-in: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 110-holodomor-mekhanizm.yaml: [елемент-голодомору-↔-функція] match-up: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 110-holodomor-mekhanizm.yaml: [перевірка-знань] true-false: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 110-holodomor-mekhanizm.yaml: [механізм-голодомору] cloze: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 110-holodomor-mekhanizm.yaml: [аналіз-первинних-джерел] select: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 110-holodomor-mekhanizm.yaml: [правда-vs-заперечення] group-sort: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 110-holodomor-mekhanizm.yaml: [граматика-в-історичних-реченнях] quiz: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 110-holodomor-mekhanizm.yaml: [історичні-факти:-виправлення-помилок] error-correction: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 110-holodomor-mekhanizm.yaml: [відновлення-речень] unjumble: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 110-holodomor-mekhanizm.yaml: [переклад-ключових-понять] translate: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 110-holodomor-mekhanizm.yaml: [хронологія-голодомору] cloze: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 110-holodomor-mekhanizm.yaml: [ключові-терміни-голодомору] mark-the-words: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 110-holodomor-mekhanizm.yaml: [дати-та-числа-голодомору] fill-in: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[MISSING_ADVANCED_ACTIVITY]** B2+ module (focus: history) missing advanced activity type: essay-response
  - FIX: Add a essay-response activity to meet advanced richness standards.
- **[MISSING_ADVANCED_ACTIVITY]** B2+ module (focus: history) missing advanced activity type: comparative-study
  - FIX: Add a comparative-study activity to meet advanced richness standards.

## TEMPLATE COMPLIANCE
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Огляд' per template 'b2-checkpoint-module-template'
  - FIX: Add '## Огляд' section as specified in docs/l2-uk-en/templates/b2-checkpoint-module-template.md
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Skill Sections' per template 'b2-checkpoint-module-template'
  - FIX: Add '## Skill Sections' section as specified in docs/l2-uk-en/templates/b2-checkpoint-module-template.md
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Інтеграційне завдання' per template 'b2-checkpoint-module-template'
  - FIX: Add '## Інтеграційне завдання' section as specified in docs/l2-uk-en/templates/b2-checkpoint-module-template.md

## Recommendation
**🔄 REWRITE** (severity 75/100)

- 19 violations (severe - consider revision)
- Activity count below minimum
- Activity density below minimum

## Gates
- **Words:** ⚠️ 1902/2000 (98 short)
- **Activities:** ❌ 0/10
- **Density:** ❌ 0 < 14
- **Unique_types:** ❌ 0/4 types
- **Priority:** ❌ No priority types
- **Engagement:** ✅ 10/5
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 68/20
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 16 violations
- **Content_heavy:** ⚠️ Too few activities: 0 (target 10-14)
- **Immersion:** 🇺🇦 99.1% (target 98-100% (history))
- **Richness:** ✅ 96% (content)
- **Grammar:** ⏳ Pending validation

## Richness Details
**Score:** 96% (minimum: 95%)
**Module Type:** content

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| examples | 43 | 15 | 100% | 25% | 25.0% |
| engagement | 10 | 5 | 100% | 19% | 18.7% |
| variety | 1.00 | - | 100% | 12% | 12.5% |
| cultural | 4 | 4 | 100% | 12% | 12.5% |
| realworld | 3 | 3 | 100% | 12% | 12.5% |
| visual | 3 | 4 | 75% | 6% | 4.7% |
| paragraph_var | 0.63 | - | 63% | 6% | 3.9% |
| questions | 15 | 4 | 100% | 6% | 6.2% |
| **TOTAL** | | | | | **96.1%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 48 | Included in Core |
| **Вступ: Голод як зброя** | ⚪️ | 159 | Skipped |
| **Частина 1: Колективізація — знищення селянства** | ✅ | 353 | Included in Core |
| **Частина 2: Хлібозаготівлі — конфіскація всього** | ✅ | 289 | Included in Core |
| **Частина 3: «Закон про п'ять колосків»** | ✅ | 210 | Included in Core |
| **Частина 4: Блокада сіл** | ✅ | 204 | Included in Core |
| **Частина 5: Заперечення і приховування** | ✅ | 249 | Included in Core |
| **Первинні джерела** | ⚪️ | 167 | Skipped |
| **Підсумок** | ✅ | 113 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 110 | Skipped |