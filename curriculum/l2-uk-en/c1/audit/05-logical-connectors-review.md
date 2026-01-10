# Audit Report: 05-logical-connectors.md
**Phase:** C1.1 | **Level:** C1 | **Pedagogy:** CTT | **Target:** 2000
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[YAML_SCHEMA_VIOLATION]** Schema error in 05-logical-connectors.yaml: [group-sort-connectors-1] group-sort: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 05-logical-connectors.yaml: [group-sort-connectors-2] group-sort: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 05-logical-connectors.yaml: [quiz-causal-logic] quiz: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 05-logical-connectors.yaml: [quiz-consequence-logic] quiz: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 05-logical-connectors.yaml: [quiz-contrast-logic] quiz: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 05-logical-connectors.yaml: [match-synonyms] match-up: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 05-logical-connectors.yaml: [match-english-equivalents] match-up: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 05-logical-connectors.yaml: [match-register-pairs] match-up: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 05-logical-connectors.yaml: [fill-in-ecology] fill-in: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 05-logical-connectors.yaml: [fill-in-politics] fill-in: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 05-logical-connectors.yaml: [fill-in-academic-discussion] fill-in: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 05-logical-connectors.yaml: [true-false-grammar] true-false: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 05-logical-connectors.yaml: [error-correction-style] error-correction: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 05-logical-connectors.yaml: [unjumble-syntax-1] unjumble: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 05-logical-connectors.yaml: [unjumble-syntax-2] unjumble: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 05-logical-connectors.yaml: [fill-in-argument-constructor] fill-in: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 05-logical-connectors.yaml: [essay-argumentation] essay-response: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## TEMPLATE COMPLIANCE
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Вступ|Контекст|Розминка' per template 'c1-module-template'
  - FIX: Add '## Вступ' section as specified in docs/l2-uk-en/templates/c1-module-template.md
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Підсумок' per template 'c1-module-template'
  - FIX: Add '## Підсумок' section as specified in docs/l2-uk-en/templates/c1-module-template.md
- ❌ **[EMPTY_REQUIRED_SECTION]** Required section '## Потрібно більше практики?' is empty
  - FIX: Populate the section with meaningful content or generate it if it's a mandatory placeholder.

## Recommendation
**📝 UPDATE** (severity 50/100)

- Revision recommended (severity 50/100)
- 20 violations (severe - consider revision)

## Gates
- **Words:** ✅ 2288/2000
- **Activities:** ✅ 17/12
- **Density:** ✅ All > 12
- **Unique_types:** ✅ 8/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 7/7
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 37/25
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 17 violations
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 99.5% (target 98-100% (grammar))
- **Richness:** ✅ 96% (grammar)
- **Grammar:** ⏳ Pending validation

## Richness Details
**Score:** 96% (minimum: 95%)
**Module Type:** grammar

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| examples | 50 | 24 | 100% | 20% | 20.0% |
| engagement | 7 | 5 | 100% | 15% | 15.0% |
| dialogues | 3 | 4 | 75% | 15% | 11.2% |
| variety | 0.98 | - | 98% | 10% | 9.8% |
| cultural | 5 | 3 | 100% | 10% | 10.0% |
| realworld | 7 | 3 | 100% | 10% | 10.0% |
| visual | 13 | 3 | 100% | 5% | 5.0% |
| paragraph_var | 1.00 | - | 100% | 5% | 5.0% |
| questions | 9 | 5 | 100% | 5% | 5.0% |
| proverbs | 10 | 1 | 100% | 5% | 5.0% |
| **TOTAL** | | | | | **96.0%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 0 | Included in Core |
| **Summary** | ✅ | 41 | Included in Core |
| **Логіка причини** | ⚪️ | 290 | Skipped |
| **Логіка наслідку** | ⚪️ | 197 | Skipped |
| **Логіка протиставлення** | ⚪️ | 437 | Skipped |
| **Текст 2: Ідентичність та глобалізація** | ✅ | 214 | Included in Core |
| **Діалог: Академічна дискусія** | ✅ | 379 | Included in Core |
| **Текст 3: Цифрова приватність** | ✅ | 80 | Included in Core |
| **Текст 4: Мова та політика** | ✅ | 120 | Included in Core |
| **Детальний аналіз аргументації** | ✅ | 116 | Included in Core |
| **Додаткові засоби аргументації** | ⚪️ | 414 | Skipped |
| **Потрібно більше практики?** | ⚪️ | 0 | Skipped |