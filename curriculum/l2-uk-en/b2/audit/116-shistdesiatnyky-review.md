# Audit Report: 116-shistdesiatnyky.md
**Phase:** B2.3c | **Level:** B2 | **Pedagogy:** CBI | **Target:** 2000
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[COMPLEXITY_WORD_COUNT]** quiz 'Читання: Перевірка розуміння' Q1 prompt length 7 (target: 8-20)
  - FIX: Adjust prompt length to 8-20 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Читання: Перевірка розуміння' Q5 prompt length 5 (target: 8-20)
  - FIX: Adjust prompt length to 8-20 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Читання: Перевірка розуміння' Q6 prompt length 3 (target: 8-20)
  - FIX: Adjust prompt length to 8-20 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Читання: Перевірка розуміння' Q8 prompt length 6 (target: 8-20)
  - FIX: Adjust prompt length to 8-20 words.
- **[COMPLEXITY]** match-up 'Поєднайте видатних діячів шістдесятництва з їхньою діяльністю або долею.' has 8 pairs (target: 12-16)
  - FIX: Adjust number of pairs to 12-16.
- **[COMPLEXITY]** group-sort 'Розподіліть за групами' has 2 groups (target: 3-5)
  - FIX: Adjust number of sorting categories to 3-5.
- **[COMPLEXITY]** match-up 'Доберіть синоніми до слів.' has 8 pairs (target: 12-16)
  - FIX: Adjust number of pairs to 12-16.
- **[YAML_SCHEMA_VIOLATION]** Schema error in 116-shistdesiatnyky.yaml: Array validation: {'type': 'translate', 'items': [{'source': 'Thaw', 'options': [{'text': 'Відлига', 'correct': True}]}, {'source': 'Censorship', 'options': [{'text': 'Цензура', 'correct': True}]}, {'source': 'Dissident', 'options': [{'text': 'Дисидент', 'correct': True}]}, {'source': 'Persecution', 'options': [{'text': 'Переслідування', 'correct': True}]}, {'source': 'Exile', 'options': [{'text': 'Заслання', 'correct': True}]}, {'source': 'Self-publishing', 'options': [{'text': 'Самвидав', 'correct': True}]}, {'source': 'Human dignity', 'options': [{'text': 'Людська гідність', 'correct': True}]}, {'source': 'Conscience', 'options': [{'text': 'Совість', 'correct': True}]}], 'title': 'Перекладіть історичні терміни українською мовою.', 'instruction': 'Оберіть правильний переклад.'} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 116-shistdesiatnyky.yaml: [index-4] select: 'items.5' - 'options' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 116-shistdesiatnyky.yaml: [index-5] mark-the-words: 'title' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 116-shistdesiatnyky.yaml: [index-12] select: 'items.5' - 'options' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 116-shistdesiatnyky.yaml: [index-13] translate: 'items.7.options' - [{'text': 'Совість', 'correct': True}] is too short
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
- 15 violations (severe - consider revision)

## Gates
- **Words:** ✅ 2109/2000
- **Activities:** ✅ 14/10
- **Density:** ✅ All > 14
- **Unique_types:** ✅ 11/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 11/5
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 35/20
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 14 violations
- **Content_heavy:** ✅ Content-heavy OK (14 activities)
- **Immersion:** 🇺🇦 99.3% (target 90-100% (history))
- **Richness:** ✅ 99% (history)
- **Grammar:** ⏳ Pending validation

## Richness Details
**Score:** 99% (minimum: 95%)
**Module Type:** history

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| primary_sources | 9 | 3 | 100% | 24% | 23.8% |
| engagement | 11 | 6 | 100% | 14% | 14.3% |
| timeline_markers | 30 | 10 | 100% | 14% | 14.3% |
| decolonization | 15 | 2 | 100% | 14% | 14.3% |
| cultural | 5 | 4 | 100% | 10% | 9.5% |
| visual | 9 | 4 | 100% | 10% | 9.5% |
| variety | 0.99 | - | 99% | 5% | 4.7% |
| paragraph_var | 1.00 | - | 100% | 5% | 4.8% |
| questions | 9 | 3 | 100% | 5% | 4.8% |
| **TOTAL** | | | | | **100.0%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 104 | Included in Core |
| **Вступ** | ⚪️ | 395 | Skipped |
| **Історичний наратив: Від надії до спротиву** | ⚪️ | 912 | Skipped |
| **Первинні джерела** | ⚪️ | 274 | Skipped |
| **Деколонізаційний погляд** | ⚪️ | 256 | Skipped |
| **Підсумок** | ✅ | 58 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 110 | Skipped |