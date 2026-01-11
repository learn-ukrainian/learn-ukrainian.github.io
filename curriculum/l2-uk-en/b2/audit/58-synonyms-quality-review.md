# Audit Report: 58-synonyms-quality.md
**Phase:** B2.2 | **Level:** B2 | **Pedagogy:** CBI | **Target:** 1750
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[COMPLEXITY]** match-up 'Знайдіть відповідність (Якість)' has 8 pairs (target: 12-16)
  - FIX: Adjust number of pairs to 12-16.
- **[COMPLEXITY]** match-up 'Регістри та Оцінки' has 8 pairs (target: 12-16)
  - FIX: Adjust number of pairs to 12-16.
- **[COMPLEXITY]** match-up 'Антоніми якості' has 8 pairs (target: 12-16)
  - FIX: Adjust number of pairs to 12-16.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Метафорична якість' Q1 prompt length 5 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Метафорична якість' Q3 prompt length 7 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Метафорична якість' Q4 prompt length 8 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Метафорична якість' Q5 prompt length 7 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Метафорична якість' Q6 prompt length 7 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Метафорична якість' Q7 prompt length 4 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Метафорична якість' Q8 prompt length 4 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[YAML_SCHEMA_VIOLATION]** Schema error in 58-synonyms-quality.yaml: Array validation: {'type': 'translate', 'title': 'Переклад якості', 'instruction': 'Оберіть правильний український синонім до англійського слова.', 'items': [{'source': 'flawless', 'options': [{'text': 'бездоганний', 'correct': True}, {'text': 'кепський', 'correct': False}, {'text': 'злий', 'correct': False}, {'text': 'гіркий', 'correct': False}], 'explanation': 'Найкращий відповідник для flawless.'}, {'source': 'disgusting', 'options': [{'text': 'огидний', 'correct': True}, {'text': 'чудовий', 'correct': False}, {'text': 'хороший', 'correct': False}, {'text': 'сучасний'}], 'explanation': 'Найкращий відповідник для disgusting.'}, {'source': 'lousy', 'options': [{'text': 'кепський', 'correct': True}, {'text': 'прекрасний', 'correct': False}, {'text': 'відмінний', 'correct': False}, {'text': 'ідеальний'}], 'explanation': 'Розмовне слово для позначення поганої якості.'}, {'source': 'splendid', 'options': [{'text': 'прекрасний', 'correct': True}, {'text': 'поганий', 'correct': False}, {'text': 'жахливий', 'correct': False}, {'text': 'дрібний'}], 'explanation': 'Високий стиль для позначення краси та якості.'}, {'source': 'harmful', 'options': [{'text': 'шкідливий', 'correct': True}, {'text': 'добрий', 'correct': False}, {'text': 'гарний', 'correct': False}, {'text': 'чудовий'}], 'explanation': 'Той, що завдає шкоди.'}, {'source': 'miraculous', 'options': [{'text': 'чудесний', 'correct': True}, {'text': 'страшний', 'correct': False}, {'text': 'кепський', 'correct': False}, {'text': 'звичайний'}], 'explanation': 'Той, що подібний до дива.'}, {'source': 'insufficient', 'options': [{'text': 'незадовільний', 'correct': True}, {'text': 'відмінний', 'correct': False}, {'text': 'бездоганний', 'correct': False}, {'text': 'ідеальний'}], 'explanation': 'Який не відповідає вимогам.'}, {'source': 'crucial', 'options': [{'text': 'вирішальний', 'correct': True}, {'text': 'незначний', 'correct': False}, {'text': 'дрібний', 'correct': False}, {'text': 'мізерний'}], 'explanation': 'Найважливіший у ситуації.'}]} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 58-synonyms-quality.yaml: [index-7] translate: 'items.7.options.3' - 'correct' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[MISSING_ADVANCED_ACTIVITY]** B2+ module (focus: vocab) missing advanced activity type: essay-response
  - FIX: Add a essay-response activity to meet advanced richness standards.

## TEMPLATE COMPLIANCE
- ❌ **[DUPLICATE_SYNONYMOUS_HEADERS]** Multiple aliases for 'Вступ|Контекст|Розминка' found: Частина 6: Психологія оцінки та емоційний інтелект в українському контексті, Вступ: Світ у відтінках якості
  - FIX: Keep only one version of the header (preferably the primary one or the one with more content).
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Фразеологізми' per template 'b2-phraseology-module-template'
  - FIX: Add '## Фразеологізми' section as specified in docs/l2-uk-en/templates/b2-phraseology-module-template.md
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Вживання у контексті' per template 'b2-phraseology-module-template'
  - FIX: Add '## Вживання у контексті' section as specified in docs/l2-uk-en/templates/b2-phraseology-module-template.md

## Recommendation
**📝 UPDATE** (severity 50/100)

- Revision recommended (severity 50/100)
- 16 violations (severe - consider revision)

## Gates
- **Words:** ✅ 1777/1750
- **Activities:** ✅ 14/10
- **Density:** ✅ All > 14
- **Unique_types:** ✅ 10/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 8/6
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 65/35
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 13 violations
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 99.2% (target 90-100% (vocab))
- **Richness:** ✅ 98% (phraseology)
- **Grammar:** ⏳ Pending validation

## Richness Details
**Score:** 98% (minimum: 95%)
**Module Type:** phraseology

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| engagement | 9 | 4 | 100% | 25% | 25.0% |
| variety | 0.99 | - | 99% | 17% | 16.5% |
| cultural | 9 | - | 100% | 17% | 16.7% |
| visual | 4 | 3 | 100% | 8% | 8.3% |
| paragraph_var | 0.88 | - | 88% | 8% | 7.3% |
| examples | 53 | - | 100% | 8% | 8.3% |
| realworld | 10 | - | 100% | 8% | 8.3% |
| questions | 5 | - | 100% | 8% | 8.3% |
| **TOTAL** | | | | | **98.8%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 71 | Included in Core |
| **Вступ: Світ у відтінках якості** | ⚪️ | 126 | Skipped |
| **Частина 1: Світло позитиву — Від «доброго» до «ідеального»** | ✅ | 254 | Included in Core |
| **Частина 2: Тіні негативу — Від «поганого» до «жахливого»** | ✅ | 219 | Included in Core |
| **Частина 3: Критерії та Стандарти оцінки** | ✅ | 98 | Included in Core |
| **Частина 4: Якість у дзеркалі української літератури** | ✅ | 102 | Included in Core |
| **Частина 5: Практичний додаток — Регістр оцінки** | ✅ | 109 | Included in Core |
| **Частина 6: Психологія оцінки та емоційний інтелект в українському контексті** | ✅ | 333 | Included in Core |
| **Частина 7: Динаміка змінної якості у глобальному світі** | ✅ | 129 | Included in Core |
| **Частина 8: Репутація та соціальна оцінка** | ✅ | 96 | Included in Core |
| **Частина 9: Самооцінка та внутрішній стандарт** | ✅ | 78 | Included in Core |
| **Підсумок** | ✅ | 52 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 110 | Skipped |