# Audit Report: 110-holodomor-mekhanizm.md
**Phase:** B2.3c | **Level:** B2 | **Pedagogy:** CBI | **Target:** 2000
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[YAML_SCHEMA_VIOLATION]** Schema error in 110-holodomor-mekhanizm.yaml: Array validation: {'type': 'translate', 'title': 'Переклад ключових понять', 'instruction': 'Оберіть правильний переклад.', 'items': [{'sentence': 'Голодомор — це геноцид.', 'options': [{'text': 'Holodomor is genocide.', 'correct': True}, {'text': 'Holodomor is famine.', 'correct': False}, {'text': 'Holodomor is revolution.', 'correct': False}, {'text': 'Holodomor is liberation.', 'correct': False}]}, {'sentence': 'Селяни не мали паспортів.', 'options': [{'text': "Peasants didn't have passports.", 'correct': True}, {'text': 'Peasants had many passports.', 'correct': False}, {'text': 'Peasants bought passports.', 'correct': False}, {'text': 'Peasants sold passports.', 'correct': False}]}, {'sentence': 'Куркулів депортували до Сибіру.', 'options': [{'text': 'Kulaks were deported to Siberia.', 'correct': True}, {'text': 'Kulaks moved to Siberia.', 'correct': False}, {'text': 'Kulaks traveled to Siberia.', 'correct': False}, {'text': 'Kulaks returned from Siberia.', 'correct': False}]}, {'sentence': 'Закон криміналізував виживання.', 'options': [{'text': 'The law criminalized survival.', 'correct': True}, {'text': 'The law protected survival.', 'correct': False}, {'text': 'The law promoted survival.', 'correct': False}, {'text': 'The law ignored survival.', 'correct': False}]}, {'sentence': 'Влада фальсифікувала статистику.', 'options': [{'text': 'The authorities falsified statistics.', 'correct': True}, {'text': 'The authorities published statistics.', 'correct': False}, {'text': 'The authorities studied statistics.', 'correct': False}, {'text': 'The authorities shared statistics.', 'correct': False}]}, {'sentence': 'Перепис був засекречений.', 'options': [{'text': 'The census was classified.', 'correct': True}, {'text': 'The census was published.', 'correct': False}, {'text': 'The census was accurate.', 'correct': False}, {'text': 'The census was celebrated.', 'correct': False}]}, {'sentence': "Україну перетворили на в'язницю.", 'options': [{'text': 'Ukraine was turned into a prison.', 'correct': True}, {'text': 'Ukraine was turned into paradise.', 'correct': False}, {'text': 'Ukraine was set free.', 'correct': False}, {'text': 'Ukraine was modernized.', 'correct': False}]}, {'sentence': 'Понад 30 країн визнали Голодомор геноцидом.', 'options': [{'text': 'Over 30 countries recognized Holodomor as genocide.', 'correct': True}, {'text': '30 countries denied Holodomor.', 'correct': False}, {'text': 'All countries recognized Holodomor.', 'correct': False}, {'text': 'No country recognized Holodomor.', 'correct': False}]}]} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 110-holodomor-mekhanizm.yaml: [index-10] translate: 'items.7' - 'source' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[MISSING_ADVANCED_ACTIVITY]** B2+ module (focus: history) missing advanced activity type: essay-response
  - FIX: Add a essay-response activity to meet advanced richness standards.
- **[MISSING_ADVANCED_ACTIVITY]** B2+ module (focus: history) missing advanced activity type: comparative-study
  - FIX: Add a comparative-study activity to meet advanced richness standards.

## TEMPLATE COMPLIANCE
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Читання' per template 'b2-history-module-template'
  - FIX: Add '## Читання' section as specified in docs/l2-uk-en/templates/b2-history-module-template.md
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Деколонізаційний погляд' per template 'b2-history-module-template'
  - FIX: Add '## Деколонізаційний погляд' section as specified in docs/l2-uk-en/templates/b2-history-module-template.md
- ⚠️ **[MISSING_REQUIRED_CALLOUT]** Missing required callout '[!myth-buster]' per template 'b2-history-module-template'
  - FIX: Add a `> [!myth-buster]` box as specified in the template. This enhances module quality.
- ⚠️ **[MISSING_REQUIRED_CALLOUT]** Missing required callout '[!history-bite]' per template 'b2-history-module-template'
  - FIX: Add a `> [!history-bite]` box as specified in the template. This enhances module quality.

## Recommendation
**📝 UPDATE** (severity 55/100)

- Revision recommended (severity 55/100)
- 8 violations (significant)
- Activity count below minimum
- Activity density below minimum

## Gates
- **Words:** ⚠️ 1902/2000 (98 short)
- **Activities:** ❌ 0/10
- **Density:** ❌ 0 < 14
- **Unique_types:** ❌ 0/4 types
- **Priority:** ❌ No priority types
- **Engagement:** ✅ 10/5
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 68/20
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 4 violations
- **Content_heavy:** ⚠️ Too few activities: 0 (target 10-14)
- **Immersion:** 🇺🇦 99.1% (target 90-100% (history))
- **Richness:** ✅ 95% (history)
- **Grammar:** ⏳ Pending validation

## Richness Details
**Score:** 95% (minimum: 95%)
**Module Type:** history

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| primary_sources | 15 | 3 | 100% | 24% | 23.8% |
| engagement | 10 | 6 | 100% | 14% | 14.3% |
| timeline_markers | 29 | 10 | 100% | 14% | 14.3% |
| decolonization | 9 | 2 | 100% | 14% | 14.3% |
| cultural | 4 | 4 | 100% | 10% | 9.5% |
| visual | 3 | 4 | 75% | 10% | 7.1% |
| variety | 1.00 | - | 100% | 5% | 4.8% |
| paragraph_var | 0.63 | - | 63% | 5% | 3.0% |
| questions | 15 | 3 | 100% | 5% | 4.8% |
| **TOTAL** | | | | | **95.9%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 48 | Included in Core |
| **Вступ: Голод як зброя** | ⚪️ | 159 | Skipped |
| **Частина 1: Колективізація — знищення селянства** | ✅ | 353 | Included in Core |
| **Частина 2: Хлібозаготівлі — конфіскація всього** | ✅ | 289 | Included in Core |
| **Частина 3: «Закон про п'ять колосків»** | ✅ | 210 | Included in Core |
| **Частина 4: Блокада сіл** | ✅ | 204 | Included in Core |
| **Частина 5: Заперечення і приховування** | ✅ | 249 | Included in Core |
| **Первинні джерела** | ⚪️ | 167 | Skipped |
| **Підсумок** | ✅ | 113 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 110 | Skipped |