# Audit Report: 120-shliakh-do-nezalezhnosti.md
**Phase:** B2.3d | **Level:** B2 | **Pedagogy:** CBI | **Target:** 2000
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[COMPLEXITY_WORD_COUNT]** quiz 'Читання: Перевірка розуміння' Q4 prompt length 7 (target: 8-20)
  - FIX: Adjust prompt length to 8-20 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Читання: Перевірка розуміння' Q6 prompt length 7 (target: 8-20)
  - FIX: Adjust prompt length to 8-20 words.
- **[COMPLEXITY]** match-up 'Поєднайте терміни з їхніми визначеннями.' has 8 pairs (target: 12-16)
  - FIX: Adjust number of pairs to 12-16.
- **[COMPLEXITY]** match-up 'Встановіть відповідність між датами та подіями.' has 8 pairs (target: 12-16)
  - FIX: Adjust number of pairs to 12-16.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Перевірте знання про лідерів руху за незалежність.' Q3 prompt length 6 (target: 8-20)
  - FIX: Adjust prompt length to 8-20 words.
- **[YAML_SCHEMA_VIOLATION]** Schema error in 120-shliakh-do-nezalezhnosti.yaml: Array validation: {'type': 'select', 'items': [{'correct': True, 'question': 'Геть від Москви!'}, {'correct': True, 'question': 'Соціалізм з людським обличчям'}, {'correct': True, 'question': 'Україна — понад усе!'}, {'correct': False, 'question': 'Ми за єдиний і неподільний Союз'}, {'correct': True, 'question': "Свободу політв'язням!"}, {'correct': False, 'question': "П'ятирічку — за три дні!"}], 'title': 'Виберіть правильні відповіді', 'instruction': 'Оберіть усі правильні відповіді.'} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 120-shliakh-do-nezalezhnosti.yaml: [index-6] select: 'items.5' - 'options' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 120-shliakh-do-nezalezhnosti.yaml: [index-7] mark-the-words: 'title' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 120-shliakh-do-nezalezhnosti.yaml: [index-11] translate: 'items.7.options' - [{'text': 'Конституційна більшість', 'correct': True}] is too short
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 120-shliakh-do-nezalezhnosti.yaml: [index-12] select: 'items.5' - 'options' is a required property
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
- 13 violations (severe - consider revision)

## Gates
- **Words:** ⚠️ 1984/2000 (16 short)
- **Activities:** ✅ 14/10
- **Density:** ✅ All > 14
- **Unique_types:** ✅ 11/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 11/5
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 35/20
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 12 violations
- **Content_heavy:** ✅ Content-heavy OK (14 activities)
- **Immersion:** 🇺🇦 99.2% (target 90-100% (history))
- **Richness:** ✅ 99% (history)
- **Grammar:** ⏳ Pending validation

## Richness Details
**Score:** 99% (minimum: 95%)
**Module Type:** history

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| primary_sources | 12 | 3 | 100% | 24% | 23.8% |
| engagement | 11 | 6 | 100% | 14% | 14.3% |
| timeline_markers | 30 | 10 | 100% | 14% | 14.3% |
| decolonization | 15 | 2 | 100% | 14% | 14.3% |
| cultural | 8 | 4 | 100% | 10% | 9.5% |
| visual | 9 | 4 | 100% | 10% | 9.5% |
| variety | 0.97 | - | 97% | 5% | 4.6% |
| paragraph_var | 1.00 | - | 100% | 5% | 4.8% |
| questions | 11 | 3 | 100% | 5% | 4.8% |
| **TOTAL** | | | | | **99.9%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 90 | Included in Core |
| **Вступ** | ⚪️ | 427 | Skipped |
| **Історичний наратив: Лавина свободи** | ⚪️ | 789 | Skipped |
| **Первинні джерела** | ⚪️ | 244 | Skipped |
| **Деколонізаційний погляд** | ⚪️ | 254 | Skipped |
| **Підсумок** | ✅ | 70 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 110 | Skipped |