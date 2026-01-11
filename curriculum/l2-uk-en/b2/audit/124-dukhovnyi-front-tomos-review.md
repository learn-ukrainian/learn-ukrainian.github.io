# Audit Report: 124-dukhovnyi-front-tomos.md
**Phase:** B2.3d | **Level:** B2 | **Pedagogy:** CBI | **Target:** 2000
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[COMPLEXITY_WORD_COUNT]** quiz 'Читання: Перевірка розуміння' Q1 prompt length 6 (target: 8-20)
  - FIX: Adjust prompt length to 8-20 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Читання: Перевірка розуміння' Q2 prompt length 5 (target: 8-20)
  - FIX: Adjust prompt length to 8-20 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Читання: Перевірка розуміння' Q6 prompt length 7 (target: 8-20)
  - FIX: Adjust prompt length to 8-20 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Читання: Перевірка розуміння' Q7 prompt length 3 (target: 8-20)
  - FIX: Adjust prompt length to 8-20 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Читання: Перевірка розуміння' Q8 prompt length 7 (target: 8-20)
  - FIX: Adjust prompt length to 8-20 words.
- **[COMPLEXITY]** match-up 'Встановіть відповідність між особами/термінами та їхньою роллю.' has 8 pairs (target: 12-16)
  - FIX: Adjust number of pairs to 12-16.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Перевірте свої знання про світове православ'я та місце України в ньому.' Q2 prompt length 6 (target: 8-20)
  - FIX: Adjust prompt length to 8-20 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Перевірте свої знання про світове православ'я та місце України в ньому.' Q3 prompt length 7 (target: 8-20)
  - FIX: Adjust prompt length to 8-20 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Перевірте свої знання про світове православ'я та місце України в ньому.' Q4 prompt length 7 (target: 8-20)
  - FIX: Adjust prompt length to 8-20 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Перевірте свої знання про світове православ'я та місце України в ньому.' Q5 prompt length 7 (target: 8-20)
  - FIX: Adjust prompt length to 8-20 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Перевірте свої знання про світове православ'я та місце України в ньому.' Q6 prompt length 3 (target: 8-20)
  - FIX: Adjust prompt length to 8-20 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Перевірте свої знання про світове православ'я та місце України в ньому.' Q7 prompt length 7 (target: 8-20)
  - FIX: Adjust prompt length to 8-20 words.
- **[COMPLEXITY]** match-up 'Доберіть синоніми до церковних та історичних термінів.' has 8 pairs (target: 12-16)
  - FIX: Adjust number of pairs to 12-16.
- **[YAML_SCHEMA_VIOLATION]** Schema error in 124-dukhovnyi-front-tomos.yaml: Array validation: {'type': 'select', 'items': [{'correct': True, 'question': 'Церква, що молиться мовою свого народу'}, {'correct': False, 'question': 'Інструмент російського впливу в Україні'}, {'correct': True, 'question': 'Активний учасник волонтерського руху'}, {'correct': True, 'question': 'Основа духовної деколонізації'}, {'correct': False, 'question': 'Закрита організація лише для обраних'}, {'correct': True, 'question': 'Символ відновленої історичної тяглості від Русі'}], 'title': 'Виберіть правильні відповіді', 'instruction': 'Оберіть усі правильні відповіді.'} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 124-dukhovnyi-front-tomos.yaml: [index-4] select: 'items.5' - 'options' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 124-dukhovnyi-front-tomos.yaml: [index-5] mark-the-words: 'title' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 124-dukhovnyi-front-tomos.yaml: [index-9] translate: 'items.7.options' - [{'text': 'Ідентичність', 'correct': True}] is too short
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 124-dukhovnyi-front-tomos.yaml: [index-10] select: 'items.5' - 'options' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[MISSING_ADVANCED_ACTIVITY]** B2+ module (focus: history) missing advanced activity type: essay-response
  - FIX: Add a essay-response activity to meet advanced richness standards.
- **[MISSING_ADVANCED_ACTIVITY]** B2+ module (focus: history) missing advanced activity type: comparative-study
  - FIX: Add a comparative-study activity to meet advanced richness standards.

## TEMPLATE COMPLIANCE
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Читання' per template 'b2-history-module-template'
  - FIX: Add '## Читання' section as specified in docs/l2-uk-en/templates/b2-history-module-template.md

## Recommendation
**📝 UPDATE** (severity 50/100)

- Revision recommended (severity 50/100)
- 21 violations (severe - consider revision)

## Gates
- **Words:** ⚠️ 1967/2000 (33 short)
- **Activities:** ✅ 14/10
- **Density:** ✅ All > 14
- **Unique_types:** ✅ 11/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 11/5
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 35/20
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 20 violations
- **Content_heavy:** ✅ Content-heavy OK (14 activities)
- **Immersion:** 🇺🇦 99.3% (target 90-100% (history))
- **Richness:** ✅ 95% (history)
- **Grammar:** ⏳ Pending validation

## Richness Details
**Score:** 95% (minimum: 95%)
**Module Type:** history

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| primary_sources | 12 | 3 | 100% | 24% | 23.8% |
| engagement | 11 | 6 | 100% | 14% | 14.3% |
| timeline_markers | 30 | 10 | 100% | 14% | 14.3% |
| decolonization | 15 | 2 | 100% | 14% | 14.3% |
| cultural | 2 | 4 | 50% | 10% | 4.8% |
| visual | 9 | 4 | 100% | 10% | 9.5% |
| variety | 1.00 | - | 100% | 5% | 4.8% |
| paragraph_var | 1.00 | - | 100% | 5% | 4.8% |
| questions | 9 | 3 | 100% | 5% | 4.8% |
| **TOTAL** | | | | | **95.2%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 114 | Included in Core |
| **Вступ** | ⚪️ | 224 | Skipped |
| **Історичний наратив: Від анексії до свободи** | ⚪️ | 959 | Skipped |
| **Первинні джерела** | ⚪️ | 254 | Skipped |
| **Деколонізаційний погляд** | ⚪️ | 251 | Skipped |
| **Підсумок** | ✅ | 55 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 110 | Skipped |