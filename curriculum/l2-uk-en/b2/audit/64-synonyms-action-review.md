# Audit Report: 64-synonyms-action.md
**Phase:** B2.2 | **Level:** B2 | **Pedagogy:** CBI | **Target:** 1750
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[COMPLEXITY]** match-up 'Знайдіть характер дії' has 8 pairs (target: 12-16)
  - FIX: Adjust number of pairs to 12-16.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Оберіть точну дію' Q1 prompt length 9 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Оберіть точну дію' Q6 prompt length 8 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY]** group-sort 'Дія чи Результат?' has 2 groups (target: 3-5)
  - FIX: Adjust number of sorting categories to 3-5.
- **[COMPLEXITY]** match-up 'Дія та Регістри' has 8 pairs (target: 12-16)
  - FIX: Adjust number of pairs to 12-16.
- **[COMPLEXITY]** match-up 'Дія та Її Об'єкт' has 8 pairs (target: 12-16)
  - FIX: Adjust number of pairs to 12-16.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Філософія чину' Q1 prompt length 9 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Філософія чину' Q2 prompt length 6 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Філософія чину' Q3 prompt length 6 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Філософія чину' Q4 prompt length 4 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Філософія чину' Q5 prompt length 5 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Філософія чину' Q6 prompt length 6 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Філософія чину' Q7 prompt length 4 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Філософія чину' Q8 prompt length 5 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[YAML_SCHEMA_VIOLATION]** Schema error in 64-synonyms-action.yaml: [знайдіть-характер-дії] match-up: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 64-synonyms-action.yaml: [оберіть-точну-дію] quiz: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 64-synonyms-action.yaml: [дія-чи-результат?] group-sort: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 64-synonyms-action.yaml: [складіть-дієве-речення] unjumble: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 64-synonyms-action.yaml: [проєкт-перетворення] cloze: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 64-synonyms-action.yaml: [професійне-дієслово] fill-in: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 64-synonyms-action.yaml: [виправте-вчинок] error-correction: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 64-synonyms-action.yaml: [переклад-дії] translate: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 64-synonyms-action.yaml: [нюанси-чину] true-false: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 64-synonyms-action.yaml: [всі-форми-активності] select: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 64-synonyms-action.yaml: [дія-та-регістри] match-up: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 64-synonyms-action.yaml: [дія-та-її-об'єкт] match-up: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 64-synonyms-action.yaml: [філософія-чину] quiz: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 64-synonyms-action.yaml: [творча-та-технічна-дія] select: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[MISSING_ADVANCED_ACTIVITY]** B2+ module (focus: vocab) missing advanced activity type: essay-response
  - FIX: Add a essay-response activity to meet advanced richness standards.

## TEMPLATE COMPLIANCE
- ❌ **[DUPLICATE_SYNONYMOUS_HEADERS]** Multiple aliases for 'Вступ|Контекст|Розминка' found: Частина 5: Практичний додаток — Контекст і Регістр мовлення, Частина 11: Дія в контексті відновлення міст, Вступ: Енергія українського чину та перетворення
  - FIX: Keep only one version of the header (preferably the primary one or the one with more content).
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Пояснення|Граматика|Теорія' per template 'b2-module-template'
  - FIX: Add '## Пояснення' section as specified in docs/l2-uk-en/templates/b2-module-template.md

## Recommendation
**📝 UPDATE** (severity 50/100)

- Revision recommended (severity 50/100)
- 31 violations (severe - consider revision)

## Gates
- **Words:** ✅ 1830/1750
- **Activities:** ✅ 14/10
- **Density:** ✅ All > 14
- **Unique_types:** ✅ 10/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 7/6
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 67/35
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 29 violations
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 99.2% (target 98-100% (vocab))
- **Richness:** ✅ 95% (content)
- **Grammar:** ⏳ Pending validation

## Richness Details
**Score:** 95% (minimum: 95%)
**Module Type:** content

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| examples | 43 | 15 | 100% | 25% | 25.0% |
| engagement | 8 | 5 | 100% | 19% | 18.7% |
| variety | 0.96 | - | 96% | 12% | 12.0% |
| cultural | 3 | 4 | 75% | 12% | 9.4% |
| realworld | 8 | 3 | 100% | 12% | 12.5% |
| visual | 7 | 4 | 100% | 6% | 6.2% |
| paragraph_var | 0.86 | - | 86% | 6% | 5.4% |
| questions | 6 | 4 | 100% | 6% | 6.2% |
| **TOTAL** | | | | | **95.5%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 87 | Included in Core |
| **Вступ: Енергія українського чину та перетворення** | ⚪️ | 109 | Skipped |
| **Частина 1: Робити — Як ми змінюємо світ навколо себе** | ✅ | 286 | Included in Core |
| **Частина 2: Брати — Як ми взаємодіємо з ресурсами та об'єктами** | ✅ | 156 | Included in Core |
| **Частина 3: Категорії дії — Від вчинку до результату в аналізі** | ✅ | 144 | Included in Core |
| **Частина 4: Дія в українській культурі та філософії «чину»** | ✅ | 79 | Included in Core |
| **Частина 5: Практичний додаток — Контекст і Регістр мовлення** | ✅ | 13 | Included in Core |
| **Частина 6: Дія в епоху глобальних перетворень** | ✅ | 101 | Included in Core |
| **Частина 7: Відповідальність за кожен крок та результат** | ✅ | 65 | Included in Core |
| **Частина 8: Мистецтво вчинку та Моральна Дія** | ✅ | 93 | Included in Core |
| **Частина 9: Технологічна дія: Від алгоритму до результату** | ✅ | 79 | Included in Core |
| **Частина 10: Дія як головний інструмент соціальних змін** | ✅ | 171 | Included in Core |
| **Частина 11: Дія в контексті відновлення міст** | ✅ | 90 | Included in Core |
| **Частина 12: Дія як самореалізація в Дніпро** | ✅ | 76 | Included in Core |
| **Частина 13: Дія у сучасному мистецтві та медіа** | ✅ | 121 | Included in Core |
| **Підсумок** | ✅ | 50 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 110 | Skipped |