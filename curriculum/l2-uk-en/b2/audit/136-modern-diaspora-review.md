# Audit Report: 136-modern-diaspora.md
**Phase:** B2.4 | **Level:** B2 | **Pedagogy:** CBI | **Target:** 1750
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Роль діаспори у світі' item 3 has 8 words (target: 10-18)
  - FIX: Adjust sentence length to 10-18 words to match B2 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Роль діаспори у світі' item 4 has 8 words (target: 10-18)
  - FIX: Adjust sentence length to 10-18 words to match B2 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Роль діаспори у світі' item 7 has 8 words (target: 10-18)
  - FIX: Adjust sentence length to 10-18 words to match B2 complexity.
- **[YAML_SCHEMA_VIOLATION]** Schema error in 136-modern-diaspora.yaml: Array validation: {'type': 'translate', 'title': 'Пасивні конструкції (B2 фокус)', 'items': [{'options': [{'text': 'Громадою побудовано нову церкву.', 'correct': True}, {'text': 'Громада збудувала церкву.'}, {'text': 'Церква побудувала громаду.'}], 'source': 'Громада збудувала нову церкву.'}, {'options': [{'text': 'Цей мітинг був організований діаспорою.', 'correct': True}, {'text': 'Мітинг організував діаспору.'}, {'text': 'Діаспора буде організовувати мітинг.'}], 'source': 'Діаспора організувала цей мітинг.'}, {'options': [{'text': 'Допомога доставляється волонтерами.', 'correct': True}, {'text': 'Волонтери будуть доставляти допомогу.'}, {'text': 'Допомога доставлена волонтерам.'}], 'source': 'Волонтери доставляють допомогу.'}, {'options': [{'text': 'Урядом ухвалено закон про громадянство.', 'correct': True}, {'text': 'Уряд ухвалить закон.'}, {'text': 'Закон ухвалив уряд.'}], 'source': 'Уряд ухвалив закон про громадянство.'}, {'options': [{'text': 'Зусилля громад координуються СКУ.', 'correct': True}, {'text': 'СКУ буде координувати зусилля.'}, {'text': 'Громади координують СКУ.'}], 'source': 'СКУ координує зусилля громад.'}, {'options': [{'text': 'Суботня школа була відкрита нами.', 'correct': True}, {'text': 'Ми відкриваємо школу.'}, {'text': 'Школа відкрила нас.'}], 'source': 'Ми відкрили суботню школу.'}, {'options': [{'text': 'Активістами проведено протест.', 'correct': True}, {'text': 'Активісти проводять протест.'}, {'text': 'Протест провели активістів.'}], 'source': 'Активісти провели протест.'}, {'options': [{'text': 'Ідентичність зберігається нею.', 'correct': True}, {'text': 'Вона буде зберігати ідентичність.'}, {'text': 'Ідентичність зберегла її.'}], 'source': 'Вона зберігає ідентичність.'}], 'instruction': 'Виберіть правильний пасивний варіант для активного речення.'} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 136-modern-diaspora.yaml: [index-7] error-correction: 'items.7' - 'options' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 136-modern-diaspora.yaml: [index-8] translate: 'items.7.options.2' - 'correct' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 136-modern-diaspora.yaml: [index-11] translate: 'items.7.options.2' - 'correct' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[MISSING_ADVANCED_ACTIVITY]** B2+ module (focus: skills) missing advanced activity type: essay-response
  - FIX: Add a essay-response activity to meet advanced richness standards.

## TEMPLATE COMPLIANCE
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Вступ|Контекст|Розминка' per template 'b2-module-template'
  - FIX: Add '## Вступ' section as specified in docs/l2-uk-en/templates/b2-module-template.md
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Пояснення|Граматика|Теорія' per template 'b2-module-template'
  - FIX: Add '## Пояснення' section as specified in docs/l2-uk-en/templates/b2-module-template.md
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Підсумок' per template 'b2-module-template'
  - FIX: Add '## Підсумок' section as specified in docs/l2-uk-en/templates/b2-module-template.md

## Recommendation
**📝 UPDATE** (severity 50/100)

- Revision recommended (severity 50/100)
- 11 violations (severe - consider revision)

## Gates
- **Words:** ✅ 2866/1750
- **Activities:** ✅ 14/10
- **Density:** ✅ All > 14
- **Unique_types:** ✅ 11/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 8/6
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 25/25
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 8 violations
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 98.5% (target 90-100% (skills))
- **Richness:** ✅ 98% (content)
- **Grammar:** ⏳ Pending validation

## Richness Details
**Score:** 98% (minimum: 95%)
**Module Type:** content

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| examples | 55 | 15 | 100% | 25% | 25.0% |
| engagement | 7 | 5 | 100% | 19% | 18.7% |
| variety | 0.99 | - | 99% | 12% | 12.4% |
| cultural | 4 | 4 | 100% | 12% | 12.5% |
| realworld | 3 | 3 | 100% | 12% | 12.5% |
| visual | 3 | 4 | 75% | 6% | 4.7% |
| paragraph_var | 1.00 | - | 100% | 6% | 6.2% |
| questions | 8 | 4 | 100% | 6% | 6.2% |
| **TOTAL** | | | | | **98.3%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 65 | Included in Core |
| **Глобальне українство: Понад кордонами** | ⚪️ | 752 | Skipped |
| **Культурна дипломатія та м’яка сила** | ✅ | 427 | Included in Core |
| **Лобізм та гуманітарний фронт** | ⚪️ | 278 | Skipped |
| **Аналіз та рефлексія: Ідентичність у вигнанні** | ✅ | 208 | Included in Core |
| **Майбутнє діаспори: Від еміграції до повернення** | ⚪️ | 266 | Skipped |
| **Reading Practice: Голос цифрової нації** | ✅ | 419 | Included in Core |
| **✍️ Написання есе** | ⚪️ | 275 | Skipped |
| **Summary** | ✅ | 66 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 110 | Skipped |