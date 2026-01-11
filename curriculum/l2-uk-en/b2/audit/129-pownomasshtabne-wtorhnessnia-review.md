# Audit Report: 129-pownomasshtabne-wtorhnessnia.md
**Phase:** B2.3e | **Level:** B2 | **Pedagogy:** CBI | **Target:** 2000
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[COMPLEXITY]** match-up 'Встановіть відповідність між воєнним терміном та його значенням.' has 8 pairs (target: 12-16)
  - FIX: Adjust number of pairs to 12-16.
- **[COMPLEXITY]** match-up 'Доберіть синоніми до слів з теми модуля.' has 8 pairs (target: 12-16)
  - FIX: Adjust number of pairs to 12-16.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Перевірте розуміння стратегічних наслідків битви за Київ.' Q4 prompt length 7 (target: 8-20)
  - FIX: Adjust prompt length to 8-20 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Перевірте розуміння стратегічних наслідків битви за Київ.' Q7 prompt length 7 (target: 8-20)
  - FIX: Adjust prompt length to 8-20 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Перевірте розуміння стратегічних наслідків битви за Київ.' Q8 prompt length 7 (target: 8-20)
  - FIX: Adjust prompt length to 8-20 words.
- **[YAML_SCHEMA_VIOLATION]** Schema error in 129-pownomasshtabne-wtorhnessnia.yaml: Array validation: {'type': 'select', 'items': [{'correct': True, 'question': 'Поява нових термінів для позначення видів зброї (Джавеліни, Хаймарси).'}, {'correct': False, 'question': 'Використання виключно архаїзмів та застарілих слів.'}, {'correct': True, 'question': 'Переосмислення старих виразів у воєнному контексті (бандерівські смузі).'}, {'correct': True, 'question': 'Масове вживання скорочень та абревіатур (ЗСУ, ТрО, ВПО).'}, {'correct': False, 'question': 'Повна відмова від будь-яких іноземних запозичень.'}, {'correct': True, 'question': 'Використання мілітарного сленгу в щоденному спілкуванні.'}], 'title': 'Лексика: Виберіть правильні відповіді', 'instruction': 'Оберіть усі правильні відповіді.'} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 129-pownomasshtabne-wtorhnessnia.yaml: [index-2] error-correction: 'items.1.options' - ['Потрібна зброя', 'а не поїздка.', 'Потрібна зброю', 'а не поїздка.', 'Потрібна зброї', 'а не поїздка.', 'Потрібна зброєю', 'а не поїздка.'] is too long
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 129-pownomasshtabne-wtorhnessnia.yaml: [index-4] select: 'items.5' - 'options' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 129-pownomasshtabne-wtorhnessnia.yaml: [index-5] mark-the-words: 'title' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 129-pownomasshtabne-wtorhnessnia.yaml: [index-11] translate: 'items.7.options' - [{'text': 'Надзвичайна ситуація', 'correct': True}] is too short
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 129-pownomasshtabne-wtorhnessnia.yaml: [index-12] select: 'items.5' - 'options' is a required property
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
- 14 violations (severe - consider revision)

## Gates
- **Words:** ❌ 1812/2000
- **Activities:** ✅ 14/10
- **Density:** ✅ All > 14
- **Unique_types:** ✅ 11/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 12/5
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 35/20
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 13 violations
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
| primary_sources | 8 | 3 | 100% | 24% | 23.8% |
| engagement | 12 | 6 | 100% | 14% | 14.3% |
| timeline_markers | 16 | 10 | 100% | 14% | 14.3% |
| decolonization | 8 | 2 | 100% | 14% | 14.3% |
| cultural | 6 | 4 | 100% | 10% | 9.5% |
| visual | 10 | 4 | 100% | 10% | 9.5% |
| variety | 0.99 | - | 99% | 5% | 4.7% |
| paragraph_var | 1.00 | - | 100% | 5% | 4.8% |
| questions | 13 | 3 | 100% | 5% | 4.8% |
| **TOTAL** | | | | | **100.0%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 106 | Included in Core |
| **Вступ: Ранок, що триває** | ⚪️ | 225 | Skipped |
| **Історичний наратив: Крах бліцкригу** | ⚪️ | 743 | Skipped |
| **Первинні джерела** | ⚪️ | 294 | Skipped |
| **Деколонізаційний погляд** | ⚪️ | 252 | Skipped |
| **Підсумок** | ✅ | 82 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 110 | Skipped |