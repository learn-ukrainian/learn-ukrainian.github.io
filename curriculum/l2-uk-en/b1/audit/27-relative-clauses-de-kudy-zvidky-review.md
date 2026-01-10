# Audit Report: 27-relative-clauses-de-kudy-zvidky.md
**Phase:** B1.3a | **Level:** B1 | **Pedagogy:** TTT | **Target:** 1500
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[YAML_SCHEMA_VIOLATION]** Schema error in 27-relative-clauses-de-kudy-zvidky.yaml: [де,-куди-чи-звідки?] quiz: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 27-relative-clauses-de-kudy-zvidky.yaml: [прислівники-та-їх-значення] match-up: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 27-relative-clauses-de-kudy-zvidky.yaml: [оберіть-правильний-прислівник] cloze: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 27-relative-clauses-de-kudy-zvidky.yaml: [правда-чи-неправда?] true-false: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 27-relative-clauses-de-kudy-zvidky.yaml: [типи-просторових-відносин] group-sort: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 27-relative-clauses-de-kudy-zvidky.yaml: [розставте-слова-в-правильному-порядку] unjumble: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 27-relative-clauses-de-kudy-zvidky.yaml: [виправте-помилки] error-correction: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 27-relative-clauses-de-kudy-zvidky.yaml: [де,-куди,-звідки-у-контексті] cloze: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 27-relative-clauses-de-kudy-zvidky.yaml: [знайдіть-прислівники-місця] mark-the-words: 'correct_words' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 27-relative-clauses-de-kudy-zvidky.yaml: [оберіть-усі-правильні-варіанти] select: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 27-relative-clauses-de-kudy-zvidky.yaml: [перекладіть-речення] translate: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[STATE_STANDARD_LOW_IMMERSION]** Module 27 has 97.9% immersion (target: 98.0%+)
  - FIX: Add more Ukrainian content to reach 98%+ immersion for full immersion modules

## TEMPLATE COMPLIANCE
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Вступ|Контекст|Розминка|Тест' per template 'b1-grammar-module-template'
  - FIX: Add '## Вступ' section as specified in docs/l2-uk-en/templates/b1-grammar-module-template.md
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Пояснення|Граматика|Теорія' per template 'b1-grammar-module-template'
  - FIX: Add '## Пояснення' section as specified in docs/l2-uk-en/templates/b1-grammar-module-template.md
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Практика|Вправи' per template 'b1-grammar-module-template'
  - FIX: Add '## Практика' section as specified in docs/l2-uk-en/templates/b1-grammar-module-template.md

## Recommendation
**🔄 REWRITE** (severity 75/100)

- 15 violations (severe - consider revision)
- Activity count below minimum
- Activity density below minimum

## Gates
- **Words:** ✅ 1727/1500
- **Activities:** ❌ 0/8
- **Density:** ❌ 0 < 12
- **Unique_types:** ❌ 0/4 types
- **Priority:** ❌ No priority types
- **Engagement:** ✅ 11/5
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 13 < 25 (soft target)
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 11 violations
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 97.9% (target 85-100% (B1.3-4 Complex))
- **Richness:** ✅ 98% (grammar)
- **Grammar:** ⏳ Pending validation

## Richness Details
**Score:** 98% (minimum: 95%)
**Module Type:** grammar

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| examples | 60 | 24 | 100% | 20% | 20.0% |
| engagement | 11 | 5 | 100% | 15% | 15.0% |
| dialogues | 11 | 4 | 100% | 15% | 15.0% |
| variety | 0.95 | - | 95% | 10% | 9.5% |
| cultural | 4 | 3 | 100% | 10% | 10.0% |
| realworld | 9 | 3 | 100% | 10% | 10.0% |
| visual | 5 | 3 | 100% | 5% | 5.0% |
| paragraph_var | 0.88 | - | 88% | 5% | 4.4% |
| questions | 28 | 5 | 100% | 5% | 5.0% |
| proverbs | 6 | 1 | 100% | 5% | 5.0% |
| **TOTAL** | | | | | **98.9%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 47 | Included in Core |
| **Діагностика** | ✅ | 146 | Included in Core |
| **Аналіз** | ✅ | 260 | Included in Core |
| **Поглиблення** | ⚪️ | 707 | Skipped |
| **Діалоги** | ✅ | 219 | Included in Core |
| **Українське прислів'я** | ⚪️ | 77 | Skipped |
| **Підсумок** | ✅ | 161 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 110 | Skipped |