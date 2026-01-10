# Audit Report: 63-synonyms-quantity.md
**Phase:** B2.2 | **Level:** B2 | **Pedagogy:** CBI | **Target:** 1750
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[COMPLEXITY]** match-up 'Знайдіть точну міру' has 8 pairs (target: 12-16)
  - FIX: Adjust number of pairs to 12-16.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Оберіть масштаб' Q8 prompt length 9 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY]** group-sort 'Багато чи Мало?' has 2 groups (target: 3-5)
  - FIX: Adjust number of sorting categories to 3-5.
- **[COMPLEXITY]** match-up 'Регістри та Кількість' has 8 pairs (target: 12-16)
  - FIX: Adjust number of pairs to 12-16.
- **[COMPLEXITY]** match-up 'Кількість та Об'єкти' has 8 pairs (target: 12-16)
  - FIX: Adjust number of pairs to 12-16.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Кількість у житті' Q1 prompt length 6 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Кількість у житті' Q2 prompt length 6 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Кількість у житті' Q3 prompt length 5 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Кількість у житті' Q4 prompt length 5 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Кількість у житті' Q5 prompt length 6 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Кількість у житті' Q6 prompt length 4 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Кількість у житті' Q7 prompt length 4 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Кількість у житті' Q8 prompt length 6 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[YAML_SCHEMA_VIOLATION]** Schema error in 63-synonyms-quantity.yaml: [знайдіть-точну-міру] match-up: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 63-synonyms-quantity.yaml: [оберіть-масштаб] quiz: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 63-synonyms-quantity.yaml: [багато-чи-мало?] group-sort: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 63-synonyms-quantity.yaml: [складіть-кількісне-речення] unjumble: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 63-synonyms-quantity.yaml: [звіт-з-ярмарку] cloze: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 63-synonyms-quantity.yaml: [офіційна-міра] fill-in: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 63-synonyms-quantity.yaml: [виправте-кількість] error-correction: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 63-synonyms-quantity.yaml: [переклад-міри] translate: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 63-synonyms-quantity.yaml: [нюанси-кількості] true-false: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 63-synonyms-quantity.yaml: [всі-відтінки-багатоманітності] select: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 63-synonyms-quantity.yaml: [регістри-та-кількість] match-up: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 63-synonyms-quantity.yaml: [кількість-та-об'єкти] match-up: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 63-synonyms-quantity.yaml: [кількість-у-житті] quiz: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 63-synonyms-quantity.yaml: [кількісна-етика] select: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[MISSING_ADVANCED_ACTIVITY]** B2+ module (focus: vocab) missing advanced activity type: essay-response
  - FIX: Add a essay-response activity to meet advanced richness standards.

## TEMPLATE COMPLIANCE
- ❌ **[DUPLICATE_SYNONYMOUS_HEADERS]** Multiple aliases for 'Вступ|Контекст|Розминка' found: Вступ: Масштаби українського життя, Таблиця відповідності регістрам та контекстам
  - FIX: Keep only one version of the header (preferably the primary one or the one with more content).
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Пояснення|Граматика|Теорія' per template 'b2-module-template'
  - FIX: Add '## Пояснення' section as specified in docs/l2-uk-en/templates/b2-module-template.md

## Recommendation
**📝 UPDATE** (severity 50/100)

- Revision recommended (severity 50/100)
- 30 violations (severe - consider revision)

## Gates
- **Words:** ✅ 2392/1750
- **Activities:** ✅ 14/10
- **Density:** ✅ All > 14
- **Unique_types:** ✅ 10/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 7/6
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 60/35
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 28 violations
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 99.3% (target 98-100% (vocab))
- **Richness:** ✅ 95% (content)
- **Grammar:** ⏳ Pending validation

## Richness Details
**Score:** 95% (minimum: 95%)
**Module Type:** content

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| examples | 65 | 15 | 100% | 25% | 25.0% |
| engagement | 9 | 5 | 100% | 19% | 18.7% |
| variety | 0.71 | - | 71% | 12% | 8.9% |
| cultural | 5 | 4 | 100% | 12% | 12.5% |
| realworld | 9 | 3 | 100% | 12% | 12.5% |
| visual | 8 | 4 | 100% | 6% | 6.2% |
| paragraph_var | 0.85 | - | 85% | 6% | 5.3% |
| questions | 9 | 4 | 100% | 6% | 6.2% |
| **TOTAL** | | | | | **95.4%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 69 | Included in Core |
| **Вступ: Масштаби українського життя** | ⚪️ | 98 | Skipped |
| **Частина 1: Океан багатоманітності — Від «багато» до «безлічі»** | ✅ | 280 | Included in Core |
| **Частина 2: Острів недостатності — Від «мало» до «декількох»** | ✅ | 253 | Included in Core |
| **Частина 3: Параметри вимірювання та Аналіз обсягів** | ✅ | 111 | Included in Core |
| **Частина 4: Кількість у дзеркалі української історії та культури** | ✅ | 135 | Included in Core |
| **Частина 5: Практичний додаток — Регістри та Акценти** | ✅ | 16 | Included in Core |
| **Частина 6: Психологія сприйняття кількості** | ✅ | 116 | Included in Core |
| **Частина 7: Формування культури достатку** | ✅ | 133 | Included in Core |
| **Частина 8: Кількість у цифрову епоху** | ✅ | 95 | Included in Core |
| **Частина 9: Соціальний масштаб та Кількість можливостей** | ✅ | 80 | Included in Core |
| **Частина 3: Параметри вимірювання та Аналіз обсягів у професійній мові** | ✅ | 166 | Included in Core |
| **Частина 5: Практичний додаток — Регістри та Кількісні Акценти** | ✅ | 22 | Included in Core |
| **Частина 6: Психологія сприйняття кількості та баланс у житті** | ✅ | 138 | Included in Core |
| **Частина 7: Формування культури свідомого достатку** | ✅ | 96 | Included in Core |
| **Підсумок** | ✅ | 52 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 110 | Skipped |