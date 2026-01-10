# Audit Report: 03-research-verbs.md
**Phase:** C1.1 | **Level:** C1 | **Pedagogy:** grammar | **Target:** 2000
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[YAML_SCHEMA_VIOLATION]** Schema error in 03-research-verbs.yaml: [quiz-comprehension-text1] quiz: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 03-research-verbs.yaml: [quiz-comprehension-text23] quiz: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 03-research-verbs.yaml: [match-terms-def] match-up: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 03-research-verbs.yaml: [match-terms-def2] match-up: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 03-research-verbs.yaml: [match-synonyms] match-up: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 03-research-verbs.yaml: [match-antonyms] match-up: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 03-research-verbs.yaml: [group-sort-research-stages] group-sort: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 03-research-verbs.yaml: [fill-in-verb-gov1] fill-in: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 03-research-verbs.yaml: [fill-in-verb-gov2] fill-in: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 03-research-verbs.yaml: [group-sort-stylistic] group-sort: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 03-research-verbs.yaml: [error-correction] error-correction: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 03-research-verbs.yaml: [fill-in-passive] fill-in: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 03-research-verbs.yaml: [quiz-general-test] quiz: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 03-research-verbs.yaml: [quiz-translate-sentences] quiz: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 03-research-verbs.yaml: [match-collocations] match-up: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 03-research-verbs.yaml: [match-word-formation] match-up: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 03-research-verbs.yaml: [essay-research-description] essay-response: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## TEMPLATE COMPLIANCE
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Вступ|Контекст|Розминка' per template 'c1-module-template'
  - FIX: Add '## Вступ' section as specified in docs/l2-uk-en/templates/c1-module-template.md
- ❌ **[DUPLICATE_SYNONYMOUS_HEADERS]** Multiple aliases for 'Аналіз' found: Порівняльний аналіз стилів, Група 1: Вивчення та аналіз, Аналіз тексту
  - FIX: Keep only one version of the header (preferably the primary one or the one with more content).
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Підсумок' per template 'c1-module-template'
  - FIX: Add '## Підсумок' section as specified in docs/l2-uk-en/templates/c1-module-template.md
- ❌ **[EMPTY_REQUIRED_SECTION]** Required section '## Потрібно більше практики?' is empty
  - FIX: Populate the section with meaningful content or generate it if it's a mandatory placeholder.

## Recommendation
**📝 UPDATE** (severity 50/100)

- Revision recommended (severity 50/100)
- 21 violations (severe - consider revision)

## Gates
- **Words:** ❌ 1876/2000
- **Activities:** ✅ 17/12
- **Density:** ✅ All > 12
- **Unique_types:** ✅ 6/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 8/7
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 30/25
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 17 violations
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 99.6% (target 98-100% (grammar))
- **Richness:** ✅ 99% (grammar)
- **Grammar:** ⏳ Pending validation

## Richness Details
**Score:** 99% (minimum: 95%)
**Module Type:** grammar

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| examples | 47 | 24 | 100% | 20% | 20.0% |
| engagement | 8 | 5 | 100% | 15% | 15.0% |
| dialogues | 4 | 4 | 100% | 15% | 15.0% |
| variety | 1.00 | - | 100% | 10% | 10.0% |
| cultural | 4 | 3 | 100% | 10% | 10.0% |
| realworld | 5 | 3 | 100% | 10% | 10.0% |
| visual | 9 | 3 | 100% | 5% | 5.0% |
| paragraph_var | 1.00 | - | 100% | 5% | 5.0% |
| questions | 19 | 5 | 100% | 5% | 5.0% |
| proverbs | 10 | 1 | 100% | 5% | 5.0% |
| **TOTAL** | | | | | **100.0%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 66 | Included in Core |
| **Текст 1: Етапи наукового пошуку** | ✅ | 235 | Included in Core |
| **Академічне письмо: Нюанси значень** | ⚪️ | 301 | Skipped |
| **Діалог: Консультація з науковим керівником** | ✅ | 186 | Included in Core |
| **Текст 2: Рецензія на наукову працю** | ✅ | 89 | Included in Core |
| **Текст 3: Еволюція тексту (До і Після)** | ✅ | 198 | Included in Core |
| **Порівняльний аналіз стилів** | ✅ | 124 | Included in Core |
| **Текст 4: Золотий вік та репресії української термінології** | ✅ | 264 | Included in Core |
| **Практика** | ⚪️ | 164 | Skipped |
| **Самоперевірка** | ⚪️ | 76 | Skipped |
| **Summary** | ✅ | 173 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 0 | Skipped |