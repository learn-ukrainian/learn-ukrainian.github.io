# Audit Report: 122-pomarancheva-revoliutsiia.md
**Phase:** B2.3d | **Level:** B2 | **Pedagogy:** CBI | **Target:** 2000
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[COMPLEXITY_WORD_COUNT]** quiz 'Читання: Перевірка розуміння' Q2 prompt length 7 (target: 8-20)
  - FIX: Adjust prompt length to 8-20 words.
- **[COMPLEXITY]** match-up 'Поєднайте осіб та інституції з їхньою роллю у 2004 році.' has 8 pairs (target: 12-16)
  - FIX: Adjust number of pairs to 12-16.
- **[COMPLEXITY]** match-up 'Доберіть синоніми до термінів політичної боротьби.' has 8 pairs (target: 12-16)
  - FIX: Adjust number of pairs to 12-16.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Перевірте знання фактів про Помаранчеву революцію.' Q1 prompt length 7 (target: 8-20)
  - FIX: Adjust prompt length to 8-20 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Перевірте знання фактів про Помаранчеву революцію.' Q2 prompt length 4 (target: 8-20)
  - FIX: Adjust prompt length to 8-20 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Перевірте знання фактів про Помаранчеву революцію.' Q7 prompt length 7 (target: 8-20)
  - FIX: Adjust prompt length to 8-20 words.
- **[YAML_SCHEMA_VIOLATION]** Schema error in 122-pomarancheva-revoliutsiia.yaml: Array validation: {'type': 'select', 'items': [{'correct': True, 'question': 'Разом нас багато — нас не подолати!'}, {'correct': True, 'question': 'Ющенко — Так!'}, {'correct': False, 'question': 'Кіборги'}, {'correct': True, 'question': 'Схід і Захід разом'}, {'correct': False, 'question': 'Беркут'}, {'correct': True, 'question': 'Ці руки нічого не крали'}], 'title': 'Які слова та вирази стали знаковими для 2004 року?', 'instruction': 'Оберіть усі правильні відповіді.'} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 122-pomarancheva-revoliutsiia.yaml: [index-4] select: 'items.5' - 'options' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 122-pomarancheva-revoliutsiia.yaml: [index-5] mark-the-words: 'title' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 122-pomarancheva-revoliutsiia.yaml: [index-10] translate: 'items.7.options' - [{'text': 'Політична реформа', 'correct': True}] is too short
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 122-pomarancheva-revoliutsiia.yaml: [index-11] select: 'items.5' - 'options' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[MISSING_ADVANCED_ACTIVITY]** B2+ module (focus: history) missing advanced activity type: essay-response
  - FIX: Add a essay-response activity to meet advanced richness standards.
- **[MISSING_ADVANCED_ACTIVITY]** B2+ module (focus: history) missing advanced activity type: comparative-study
  - FIX: Add a comparative-study activity to meet advanced richness standards.

## TEMPLATE COMPLIANCE
- ❌ **[DUPLICATE_SYNONYMOUS_HEADERS]** Multiple aliases for 'Вступ|Контекст|Розминка' found: Вступ, Контекст: Кінець епохи Кучми та передісторія конфлікту
  - FIX: Keep only one version of the header (preferably the primary one or the one with more content).
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Читання' per template 'b2-history-module-template'
  - FIX: Add '## Читання' section as specified in docs/l2-uk-en/templates/b2-history-module-template.md
- ⚠️ **[MISSING_REQUIRED_CALLOUT]** Missing required callout '[!myth-buster]' per template 'b2-history-module-template'
  - FIX: Add a `> [!myth-buster]` box as specified in the template. This enhances module quality.
- ⚠️ **[MISSING_REQUIRED_CALLOUT]** Missing required callout '[!quote]' per template 'b2-history-module-template'
  - FIX: Add a `> [!quote]` box as specified in the template. This enhances module quality.

## Recommendation
**📝 UPDATE** (severity 50/100)

- Revision recommended (severity 50/100)
- 17 violations (severe - consider revision)

## Gates
- **Words:** ✅ 2058/2000
- **Activities:** ✅ 14/10
- **Density:** ✅ All > 14
- **Unique_types:** ✅ 11/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 8/5
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 35/20
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 13 violations
- **Content_heavy:** ✅ Content-heavy OK (14 activities)
- **Immersion:** 🇺🇦 99.4% (target 90-100% (history))
- **Richness:** ✅ 97% (history)
- **Grammar:** ⏳ Pending validation

## Richness Details
**Score:** 97% (minimum: 95%)
**Module Type:** history

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| primary_sources | 5 | 3 | 100% | 24% | 23.8% |
| engagement | 8 | 6 | 100% | 14% | 14.3% |
| timeline_markers | 28 | 10 | 100% | 14% | 14.3% |
| decolonization | 15 | 2 | 100% | 14% | 14.3% |
| cultural | 3 | 4 | 75% | 10% | 7.1% |
| visual | 4 | 4 | 100% | 10% | 9.5% |
| variety | 0.99 | - | 99% | 5% | 4.7% |
| paragraph_var | 1.00 | - | 100% | 5% | 4.8% |
| questions | 5 | 3 | 100% | 5% | 4.8% |
| **TOTAL** | | | | | **97.6%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 63 | Included in Core |
| **Вступ** | ⚪️ | 129 | Skipped |
| **Помаранчева революція: Шлях до демократичного прориву** | ⚪️ | 640 | Skipped |
| **Персоналії революції: Творці історії** | ⚪️ | 161 | Skipped |
| **Аналіз політичної стратегії** | ✅ | 530 | Included in Core |
| **Первинні джерела** | ⚪️ | 259 | Skipped |
| **Деколонізаційний погляд** | ⚪️ | 109 | Skipped |
| **Підсумок** | ✅ | 57 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 110 | Skipped |