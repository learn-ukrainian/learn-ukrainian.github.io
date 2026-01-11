# Audit Report: 119-syntez-trahedii-xx-stolittia.md
**Phase:** B2.3c | **Level:** B2 | **Pedagogy:** CBI | **Target:** 2000
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[COMPLEXITY]** group-sort 'Патерни нищення та спротиву' has 2 groups (target: 3-5)
  - FIX: Adjust number of sorting categories to 3-5.
- **[COMPLEXITY]** match-up 'Аналітичні колокації' has 8 pairs (target: 12-16)
  - FIX: Adjust number of pairs to 12-16.
- **[YAML_SCHEMA_VIOLATION]** Schema error in 119-syntez-trahedii-xx-stolittia.yaml: Array validation: {'type': 'select', 'title': 'Методи деколонізації', 'instruction': 'Виберіть усі дії, які є частиною справжньої деколонізації історії.', 'items': [{'correct': True, 'question': "Визнання українців суб'єктом, а не об'єктом історії"}, {'correct': False, 'question': 'Механічне видалення всіх дат з підручників історії'}, {'correct': True, 'question': 'Аналіз подій з точки зору національних інтересів'}, {'correct': True, 'question': 'Повернення справжніх імен замість радянських кліше'}, {'correct': False, 'question': 'Створення нових міфів замість пошуку історичної істини'}, {'correct': True, 'question': 'Критичний розбір колоніальних стереотипів Москви'}]} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 119-syntez-trahedii-xx-stolittia.yaml: [index-4] select: 'items.7' - 'options' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 119-syntez-trahedii-xx-stolittia.yaml: [index-5] select: 'items.6' - 'options' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 119-syntez-trahedii-xx-stolittia.yaml: [index-7] select: 'items.5' - 'options' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[MISSING_ADVANCED_ACTIVITY]** B2+ module (focus: history) missing advanced activity type: essay-response
  - FIX: Add a essay-response activity to meet advanced richness standards.
- **[MISSING_ADVANCED_ACTIVITY]** B2+ module (focus: history) missing advanced activity type: comparative-study
  - FIX: Add a comparative-study activity to meet advanced richness standards.

## TEMPLATE COMPLIANCE
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Вступ|Контекст|Розминка' per template 'b2-history-module-template'
  - FIX: Add '## Вступ' section as specified in docs/l2-uk-en/templates/b2-history-module-template.md
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Читання' per template 'b2-history-module-template'
  - FIX: Add '## Читання' section as specified in docs/l2-uk-en/templates/b2-history-module-template.md
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Первинні джерела' per template 'b2-history-module-template'
  - FIX: Add '## Первинні джерела' section as specified in docs/l2-uk-en/templates/b2-history-module-template.md
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Деколонізаційний погляд' per template 'b2-history-module-template'
  - FIX: Add '## Деколонізаційний погляд' section as specified in docs/l2-uk-en/templates/b2-history-module-template.md
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Підсумок' per template 'b2-history-module-template'
  - FIX: Add '## Підсумок' section as specified in docs/l2-uk-en/templates/b2-history-module-template.md
- ⚠️ **[MISSING_REQUIRED_CALLOUT]** Missing required callout '[!myth-buster]' per template 'b2-history-module-template'
  - FIX: Add a `> [!myth-buster]` box as specified in the template. This enhances module quality.

## Recommendation
**📝 UPDATE** (severity 50/100)

- Revision recommended (severity 50/100)
- 14 violations (severe - consider revision)

## Gates
- **Words:** ❌ 1840/2000
- **Activities:** ✅ 14/10
- **Density:** ✅ All > 14
- **Unique_types:** ✅ 11/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 9/5
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 25/20
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 8 violations
- **Content_heavy:** ✅ Content-heavy OK (14 activities)
- **Immersion:** 🇺🇦 99.2% (target 90-100% (history))
- **Richness:** ✅ 95% (history)
- **Grammar:** ⏳ Pending validation

## Richness Details
**Score:** 95% (minimum: 95%)
**Module Type:** history

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| primary_sources | 3 | 3 | 100% | 24% | 23.8% |
| engagement | 9 | 6 | 100% | 14% | 14.3% |
| timeline_markers | 30 | 10 | 100% | 14% | 14.3% |
| decolonization | 15 | 2 | 100% | 14% | 14.3% |
| cultural | 2 | 4 | 50% | 10% | 4.8% |
| visual | 8 | 4 | 100% | 10% | 9.5% |
| variety | 1.00 | - | 100% | 5% | 4.8% |
| paragraph_var | 1.00 | - | 100% | 5% | 4.8% |
| questions | 6 | 3 | 100% | 5% | 4.8% |
| **TOTAL** | | | | | **95.2%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 109 | Included in Core |
| **Ключова тема: Травма як фундамент стійкості** | ⚪️ | 96 | Skipped |
| **Тематичний аналіз: Патерни нищення та виживання** | ✅ | 977 | Included in Core |
| **Деколонізаційний синтез: Повернення національної суб'єктності** | ⚪️ | 205 | Skipped |
| **Історіографічна рефлексія: Пам'ять як наша головна зброя** | ⚪️ | 240 | Skipped |
| **Summary** | ✅ | 103 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 110 | Skipped |