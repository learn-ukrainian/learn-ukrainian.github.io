# Audit Report: 137-religion-in-ukraine.md
**Phase:** B2.4 | **Level:** B2 | **Pedagogy:** CBI | **Target:** 1750
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[COMPLEXITY_WORD_COUNT]** quiz 'Релігійне різноманіття України' Q2 prompt length 9 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Релігійне різноманіття України' Q3 prompt length 9 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Релігійне різноманіття України' Q4 prompt length 6 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Релігійне різноманіття України' Q5 prompt length 9 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Релігійне різноманіття України' Q6 prompt length 9 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Релігійне різноманіття України' Q8 prompt length 7 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Духовні концепції' item 1 has 8 words (target: 10-18)
  - FIX: Adjust sentence length to 10-18 words to match B2 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Духовні концепції' item 2 has 7 words (target: 10-18)
  - FIX: Adjust sentence length to 10-18 words to match B2 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Духовні концепції' item 3 has 8 words (target: 10-18)
  - FIX: Adjust sentence length to 10-18 words to match B2 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Духовні концепції' item 4 has 8 words (target: 10-18)
  - FIX: Adjust sentence length to 10-18 words to match B2 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Духовні концепції' item 5 has 8 words (target: 10-18)
  - FIX: Adjust sentence length to 10-18 words to match B2 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Духовні концепції' item 6 has 7 words (target: 10-18)
  - FIX: Adjust sentence length to 10-18 words to match B2 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Духовні концепції' item 7 has 8 words (target: 10-18)
  - FIX: Adjust sentence length to 10-18 words to match B2 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Духовні концепції' item 8 has 8 words (target: 10-18)
  - FIX: Adjust sentence length to 10-18 words to match B2 complexity.
- **[YAML_SCHEMA_VIOLATION]** Schema error in 137-religion-in-ukraine.yaml: Array validation: {'type': 'translate', 'title': 'Пасивні конструкції в духовному тексті', 'items': [{'options': [{'text': 'Русь було охрещено у 988 році.', 'correct': True}, {'text': 'Русь хрестила Володимира.'}, {'text': 'Володимир охрестив Русь.'}], 'source': 'Князь Володимир хрестив Русь у 988 році. (Пасив з -но/-то)'}, {'options': [{'text': 'Храм наповнюється віруючими.', 'correct': True}, {'text': 'Віруючі будуть наповнювати храм.'}, {'text': 'Храм наповнив віруючих.'}], 'source': 'Натовп віруючих наповнює храм. (Пасив на -ся)'}, {'options': [{'text': 'Цей проект був благословенний священиком.', 'correct': True}, {'text': 'Священик буде благословляти проект.'}, {'text': 'Проект благословив священика.'}], 'source': 'Священик благословив цей проект. (Пасив з -ний/-тий)'}, {'options': [{'text': 'Собор збудовано у центрі міста.', 'correct': True}, {'text': 'Ми будуємо собор.'}, {'text': 'Центр міста збудував собор.'}], 'source': 'Ми збудували собор у центрі міста. (Пасив з -но/-то)'}, {'options': [{'text': 'Допомога збирається громадою.', 'correct': True}, {'text': 'Громада буде збирати допомогу.'}, {'text': 'Допомога зібрала громаду.'}], 'source': 'Громада збирає допомогу. (Пасив на -ся)'}, {'options': [{'text': 'Ця мечеть була спроектована архітектором.', 'correct': True}, {'text': 'Архітектор спроектував мечеть.'}, {'text': 'Мечеть спроектувала архітектора.'}], 'source': 'Архітектор спроектував цю мечеть. (Пасив з -ний/-тий)'}, {'options': [{'text': 'Урядом ухвалено закон про свободу совісті.', 'correct': True}, {'text': 'Уряд ухвалює закон.'}, {'text': 'Закон ухвалив уряд.'}], 'source': 'Уряд ухвалив закон про свободу совісті. (Пасив з -но/-то)'}, {'options': [{'text': 'Наші серця об’єднуються любов’ю.', 'correct': True}, {'text': 'Любов буде об’єднувати серця.'}, {'text': 'Серця об’єднали любов.'}], 'source': 'Любов об’єднує наші серця. (Пасив на -ся)'}], 'instruction': 'Виберіть правильну пасивну форму для наведеного речення.'} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 137-religion-in-ukraine.yaml: [index-7] error-correction: 'items.7' - 'options' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 137-religion-in-ukraine.yaml: [index-8] translate: 'items.7.options.2' - 'correct' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 137-religion-in-ukraine.yaml: [index-11] translate: 'items.7.options.2' - 'correct' is a required property
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
- 22 violations (severe - consider revision)

## Gates
- **Words:** ✅ 3031/1750
- **Activities:** ✅ 14/10
- **Density:** ✅ All > 14
- **Unique_types:** ✅ 11/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 10/6
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 25/25
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 19 violations
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 99.4% (target 90-100% (skills))
- **Richness:** ✅ 95% (content)
- **Grammar:** ⏳ Pending validation

## Richness Details
**Score:** 95% (minimum: 95%)
**Module Type:** content

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| examples | 64 | 15 | 100% | 25% | 25.0% |
| engagement | 10 | 5 | 100% | 19% | 18.7% |
| variety | 0.99 | - | 99% | 12% | 12.4% |
| cultural | 8 | 4 | 100% | 12% | 12.5% |
| realworld | 2 | 3 | 67% | 12% | 8.4% |
| visual | 5 | 4 | 100% | 6% | 6.2% |
| paragraph_var | 1.00 | - | 100% | 6% | 6.2% |
| questions | 10 | 4 | 100% | 6% | 6.2% |
| **TOTAL** | | | | | **95.8%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 60 | Included in Core |
| **Багатоконфесійна мозаїка України** | ⚪️ | 700 | Skipped |
| **Релігія та боротьба за суб’єктність** | ⚪️ | 322 | Skipped |
| **Духовні центри та архітектурна спадщина** | ⚪️ | 779 | Skipped |
| **Міжконфесійний мир та Рада церков** | ⚪️ | 336 | Skipped |
| **Reading Practice: Духовний фундамент нації** | ✅ | 472 | Included in Core |
| **✍️ Аналіз тексту** | ✅ | 194 | Included in Core |
| **Summary** | ✅ | 58 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 110 | Skipped |