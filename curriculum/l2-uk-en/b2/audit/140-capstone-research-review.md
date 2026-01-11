# Audit Report: 140-capstone-research.md
**Phase:** B2.4 | **Level:** B2 | **Pedagogy:** integration | **Target:** 1750
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[COMPLEXITY_WORD_COUNT]** quiz 'Фази підготовчої роботи' Q2 prompt length 9 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Фази підготовчої роботи' Q6 prompt length 9 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Фази підготовчої роботи' Q7 prompt length 8 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Фази підготовчої роботи' Q8 prompt length 9 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Об'єкт та предмет дослідження' Q2 prompt length 8 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Об'єкт та предмет дослідження' Q3 prompt length 5 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Об'єкт та предмет дослідження' Q4 prompt length 9 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Об'єкт та предмет дослідження' Q5 prompt length 7 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Об'єкт та предмет дослідження' Q6 prompt length 8 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Об'єкт та предмет дослідження' Q7 prompt length 7 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[YAML_SCHEMA_VIOLATION]** Schema error in 140-capstone-research.yaml: Array validation: {'type': 'translate', 'title': 'Ключові фрази дослідження', 'items': [{'options': [{'text': 'Актуальність теми обґрунтована...', 'correct': True}, {'text': 'Тема є гарною через...'}, {'text': 'Ми вибрали цю тему, бо...'}], 'source': 'The relevance of the topic is grounded in...'}, {'options': [{'text': 'На основі опрацьованих джерел...', 'correct': True}, {'text': 'Згідно з книжками, які я читав...'}, {'text': 'Виходячи з тексту...'}], 'source': 'Based on the analyzed sources...'}, {'options': [{'text': 'Об’єктом дослідження є...', 'correct': True}, {'text': 'Предмет праці — це...'}, {'text': 'Ми дивимося на...'}], 'source': 'The object of the study is...'}, {'options': [{'text': 'Результати вказують на те, що...', 'correct': True}, {'text': 'Ми бачимо, що...'}, {'text': 'Зрештою сталося так, що...'}], 'source': 'The results indicate that...'}, {'options': [{'text': 'Згідно з обраною методологією...', 'correct': True}, {'text': 'Дивлячись на правила...'}, {'text': 'Через наш метод...'}], 'source': 'According to the methodology...'}, {'options': [{'text': 'На завершення варто зауважити...', 'correct': True}, {'text': 'Короче, ми хочемо сказати...'}, {'text': 'В самому кінці ми пишемо...'}], 'source': 'In conclusion, it should be noted...'}], 'instruction': 'Оберіть правильний український переклад для академічної фрази.'} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 140-capstone-research.yaml: [index-7] error-correction: 'items.7' - 'options' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 140-capstone-research.yaml: [index-8] translate: 'items.7.options.2' - 'correct' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 140-capstone-research.yaml: [index-11] translate: 'items.7.options.2' - 'correct' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 140-capstone-research.yaml: [index-14] translate: 'items.5.options.2' - 'correct' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## TEMPLATE COMPLIANCE
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Огляд' per template 'b2-checkpoint-module-template'
  - FIX: Add '## Огляд' section as specified in docs/l2-uk-en/templates/b2-checkpoint-module-template.md
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Навички' per template 'b2-checkpoint-module-template'
  - FIX: Add '## Навички' section as specified in docs/l2-uk-en/templates/b2-checkpoint-module-template.md
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Інтеграційне завдання' per template 'b2-checkpoint-module-template'
  - FIX: Add '## Інтеграційне завдання' section as specified in docs/l2-uk-en/templates/b2-checkpoint-module-template.md
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Підсумок' per template 'b2-checkpoint-module-template'
  - FIX: Add '## Підсумок' section as specified in docs/l2-uk-en/templates/b2-checkpoint-module-template.md

## Recommendation
**📝 UPDATE** (severity 50/100)

- Revision recommended (severity 50/100)
- 19 violations (severe - consider revision)

## Gates
- **Words:** ❌ 1056/1750
- **Activities:** ✅ 15/15
- **Density:** ✅ All > 14
- **Unique_types:** ✅ 11/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 5/4
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 25/10
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 15 violations
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 98.4% (checkpoint - no gate)
- **Richness:** ✅ 98% (checkpoint)
- **Grammar:** ⏳ Pending validation

## Richness Details
**Score:** 98% (minimum: 85%)
**Module Type:** checkpoint

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| activity_types | 11 | 8 | 100% | 25% | 25.0% |
| review_sections | 22 | 3 | 100% | 20% | 20.0% |
| variety | 0.93 | - | 93% | 15% | 14.0% |
| engagement | 5 | 3 | 100% | 10% | 10.0% |
| cultural | 1 | - | 100% | 10% | 10.0% |
| visual | 11 | 3 | 100% | 10% | 10.0% |
| paragraph_var | 1.00 | - | 100% | 10% | 10.0% |
| **TOTAL** | | | | | **99.0%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 0 | Included in Core |
| **Overview** | ⚪️ | 114 | Skipped |
| **Навичка 1: Вибір теми та обґрунтування** | ⚪️ | 152 | Skipped |
| **Навичка 2: Пошук та опрацювання джерел** | ⚪️ | 107 | Skipped |
| **Навичка 3: Складання анотованої бібліографії** | ⚪️ | 135 | Skipped |
| **Навичка 4: План-проспект та тези дослідження** | ⚪️ | 106 | Skipped |
| **Integration Challenge** | ⚪️ | 332 | Skipped |
| **Summary** | ✅ | 0 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 110 | Skipped |