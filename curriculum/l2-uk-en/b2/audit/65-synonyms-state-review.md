# Audit Report: 65-synonyms-state.md
**Phase:** B2.2 | **Level:** B2 | **Pedagogy:** CBI | **Target:** 1750
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[COMPLEXITY]** match-up 'Знайдіть відтінок стану' has 8 pairs (target: 12-16)
  - FIX: Adjust number of pairs to 12-16.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Оберіть точний стан' Q5 prompt length 9 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY]** group-sort 'Об'єктивне чи Суб'єктивне?' has 2 groups (target: 3-5)
  - FIX: Adjust number of sorting categories to 3-5.
- **[COMPLEXITY]** match-up 'Стан та Регістри' has 8 pairs (target: 12-16)
  - FIX: Adjust number of pairs to 12-16.
- **[COMPLEXITY]** match-up 'Стан та Чинники' has 8 pairs (target: 12-16)
  - FIX: Adjust number of pairs to 12-16.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Філософія буття' Q1 prompt length 5 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Філософія буття' Q2 prompt length 5 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Філософія буття' Q3 prompt length 6 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Філософія буття' Q4 prompt length 6 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Філософія буття' Q5 prompt length 5 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Філософія буття' Q6 prompt length 3 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Філософія буття' Q7 prompt length 6 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Філософія буття' Q8 prompt length 5 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[YAML_SCHEMA_VIOLATION]** Schema error in 65-synonyms-state.yaml: [знайдіть-відтінок-стану] match-up: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 65-synonyms-state.yaml: [оберіть-точний-стан] quiz: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 65-synonyms-state.yaml: [об'єктивне-чи-суб'єктивне?] group-sort: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 65-synonyms-state.yaml: [складіть-речення-про-стан] unjumble: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 65-synonyms-state.yaml: [стан-речей] cloze: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 65-synonyms-state.yaml: [аналітичний-стан] fill-in: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 65-synonyms-state.yaml: [виправте-враження] error-correction: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 65-synonyms-state.yaml: [переклад-стану] translate: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 65-synonyms-state.yaml: [нюанси-буття] true-false: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 65-synonyms-state.yaml: [всі-форми-існування] select: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 65-synonyms-state.yaml: [стан-та-регістри] match-up: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 65-synonyms-state.yaml: [стан-та-чинники] match-up: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 65-synonyms-state.yaml: [філософія-буття] quiz: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 65-synonyms-state.yaml: [складні-стани] select: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[MISSING_ADVANCED_ACTIVITY]** B2+ module (focus: vocab) missing advanced activity type: essay-response
  - FIX: Add a essay-response activity to meet advanced richness standards.

## TEMPLATE COMPLIANCE
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Пояснення|Граматика|Теорія' per template 'b2-module-template'
  - FIX: Add '## Пояснення' section as specified in docs/l2-uk-en/templates/b2-module-template.md

## Recommendation
**📝 UPDATE** (severity 50/100)

- Revision recommended (severity 50/100)
- 29 violations (severe - consider revision)

## Gates
- **Words:** ✅ 1786/1750
- **Activities:** ✅ 14/10
- **Density:** ✅ All > 14
- **Unique_types:** ✅ 10/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 7/6
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 33 < 35 (soft target)
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 28 violations
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 99.1% (target 98-100% (vocab))
- **Richness:** ✅ 98% (content)
- **Grammar:** ⏳ Pending validation

## Richness Details
**Score:** 98% (minimum: 95%)
**Module Type:** content

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| examples | 42 | 15 | 100% | 25% | 25.0% |
| engagement | 8 | 5 | 100% | 19% | 18.7% |
| variety | 0.94 | - | 94% | 12% | 11.8% |
| cultural | 9 | 4 | 100% | 12% | 12.5% |
| realworld | 6 | 3 | 100% | 12% | 12.5% |
| visual | 7 | 4 | 100% | 6% | 6.2% |
| paragraph_var | 0.81 | - | 81% | 6% | 5.1% |
| questions | 7 | 4 | 100% | 6% | 6.2% |
| **TOTAL** | | | | | **98.1%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 80 | Included in Core |
| **Вступ: Глибина українського буття** | ⚪️ | 100 | Skipped |
| **Частина 1: Бути — Як ми фіксуємо існування** | ✅ | 159 | Included in Core |
| **Частина 2: Здаватися — Світ через призму сприйняття** | ✅ | 121 | Included in Core |
| **Частина 3: Категорії стану — Від умов до середовища** | ✅ | 116 | Included in Core |
| **Частина 4: Стан у дзеркалі української літератури та психології** | ✅ | 55 | Included in Core |
| **Частина 5: Практичний додаток — Тон та Аналіз** | ✅ | 9 | Included in Core |
| **Частина 6: Стан у сучасному світі: Стабільність та Криза** | ✅ | 93 | Included in Core |
| **Частина 7: Буття як цінність** | ✅ | 61 | Included in Core |
| **Частина 8: Стан довкілля та Екологічне Буття** | ✅ | 81 | Included in Core |
| **Частина 9: Історичний Стан: Між Минулим та Майбутнім** | ✅ | 84 | Included in Core |
| **Частина 10: Стан у цифровому просторі та Майбутнє Буття** | ✅ | 95 | Included in Core |
| **Частина 11: Стан спокою у містах Суми та Полтава** | ✅ | 79 | Included in Core |
| **Частина 12: Естетичне Буття в Ужгород** | ✅ | 146 | Included in Core |
| **Частина 13: Стан архітектури та Історичне Буття** | ✅ | 153 | Included in Core |
| **Частина 14: Стан в офіційному листуванні та Звітності** | ✅ | 97 | Included in Core |
| **Частина 15: Психологія стабільності в епоху змін** | ✅ | 99 | Included in Core |
| **Підсумок** | ✅ | 48 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 110 | Skipped |