# Audit Report: 57-synonyms-movement.md
**Phase:** B2.2 | **Level:** B2 | **Pedagogy:** CBI | **Target:** 1750
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[COMPLEXITY]** match-up 'Знайдіть манеру руху' has 8 pairs (target: 12-16)
  - FIX: Adjust number of pairs to 12-16.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Оберіть точний рух' Q4 prompt length 9 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY]** match-up 'Рух та Його Джерело' has 8 pairs (target: 12-16)
  - FIX: Adjust number of pairs to 12-16.
- **[COMPLEXITY]** match-up 'Антоніми за манерою' has 8 pairs (target: 12-16)
  - FIX: Adjust number of pairs to 12-16.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Метафоричний рух' Q1 prompt length 7 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Метафоричний рух' Q2 prompt length 9 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Метафоричний рух' Q3 prompt length 7 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Метафоричний рух' Q4 prompt length 6 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Метафоричний рух' Q5 prompt length 6 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Метафоричний рух' Q6 prompt length 7 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Метафоричний рух' Q7 prompt length 5 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Метафоричний рух' Q8 prompt length 5 (target: 10-25)
  - FIX: Adjust prompt length to 10-25 words.
- **[YAML_SCHEMA_VIOLATION]** Schema error in 57-synonyms-movement.yaml: Array validation: {'type': 'translate', 'title': 'Перекладіть дію', 'instruction': 'Оберіть правильний український синонім до англійського дієслова.', 'items': [{'source': 'to stride', 'options': [{'text': 'крокувати', 'correct': True}, {'text': 'брести', 'correct': False}, {'text': 'повзти', 'correct': False}, {'text': 'лізти', 'correct': False}], 'explanation': 'Найкращий відповідник для впевненої ходи.'}, {'source': 'to race', 'options': [{'text': 'мчати', 'correct': True}, {'text': 'йти', 'correct': False}, {'text': 'тупати', 'correct': False}, {'text': 'плавати', 'correct': False}], 'explanation': 'Передає високу швидкість руху.'}, {'source': 'to limp', 'options': [{'text': 'шкутильгати', 'correct': True}, {'text': 'бігати', 'correct': False}, {'text': 'летіти', 'correct': False}, {'text': 'стрибати', 'correct': False}], 'explanation': 'Описує рух травмованої людини.'}, {'source': 'to sneak', 'options': [{'text': 'крастися', 'correct': True}, {'text': 'нестися', 'correct': False}, {'text': 'спускатися', 'correct': False}, {'text': 'підніматися'}], 'explanation': 'Рух з метою залишитися непоміченим.'}, {'source': 'to trudge', 'options': [{'text': 'брести', 'correct': True}, {'text': 'мчати', 'correct': False}, {'text': 'летіти', 'correct': False}, {'text': 'плисти'}], 'explanation': 'Важкий, втомлений рух.'}, {'source': 'to scurry', 'options': [{'text': 'чимчикувати', 'correct': True}, {'text': 'стояти', 'correct': False}, {'text': 'лежати', 'correct': False}, {'text': 'сидіти'}], 'explanation': 'Швидкий рух маленькими кроками.'}, {'source': 'to stomp', 'options': [{'text': 'тупати', 'correct': True}, {'text': 'крастися', 'correct': False}, {'text': 'повзти', 'correct': False}, {'text': 'лізти'}], 'explanation': 'Йти, видаючи сильний шум ногами.'}, {'source': 'to zoom past', 'options': [{'text': 'проноситися', 'correct': True}, {'text': 'брести', 'correct': False}, {'text': 'йти', 'correct': False}, {'text': 'стояти'}], 'explanation': 'Дуже швидкий рух повз щось.'}]} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 57-synonyms-movement.yaml: [index-7] translate: 'items.7.options.3' - 'correct' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[MISSING_ADVANCED_ACTIVITY]** B2+ module (focus: vocab) missing advanced activity type: essay-response
  - FIX: Add a essay-response activity to meet advanced richness standards.

## TEMPLATE COMPLIANCE
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Фразеологізми' per template 'b2-phraseology-module-template'
  - FIX: Add '## Фразеологізми' section as specified in docs/l2-uk-en/templates/b2-phraseology-module-template.md
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Вживання у контексті' per template 'b2-phraseology-module-template'
  - FIX: Add '## Вживання у контексті' section as specified in docs/l2-uk-en/templates/b2-phraseology-module-template.md

## Recommendation
**📝 UPDATE** (severity 50/100)

- Revision recommended (severity 50/100)
- 17 violations (severe - consider revision)

## Gates
- **Words:** ✅ 1768/1750
- **Activities:** ✅ 14/10
- **Density:** ✅ All > 14
- **Unique_types:** ✅ 10/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 7/6
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 136/35
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 15 violations
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 99.1% (target 90-100% (vocab))
- **Richness:** ✅ 98% (phraseology)
- **Grammar:** ⏳ Pending validation

## Richness Details
**Score:** 98% (minimum: 95%)
**Module Type:** phraseology

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| engagement | 8 | 4 | 100% | 25% | 25.0% |
| variety | 0.95 | - | 95% | 17% | 15.8% |
| cultural | 7 | - | 100% | 17% | 16.7% |
| visual | 5 | 3 | 100% | 8% | 8.3% |
| paragraph_var | 0.95 | - | 95% | 8% | 7.9% |
| examples | 49 | - | 100% | 8% | 8.3% |
| realworld | 8 | - | 100% | 8% | 8.3% |
| questions | 8 | - | 100% | 8% | 8.3% |
| **TOTAL** | | | | | **98.7%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 71 | Included in Core |
| **Вступ: Ритм українських доріг** | ⚪️ | 96 | Skipped |
| **Частина 1: Мистецтво кроку — Від «йти» до «тупати»** | ✅ | 213 | Included in Core |
| **Частина 2: Швидкість та Енергія — Біг та його грані** | ✅ | 160 | Included in Core |
| **Частина 3: Специфічні способи пересування** | ✅ | 128 | Included in Core |
| **Частина 4: Психологія руху в літературі** | ✅ | 85 | Included in Core |
| **Частина 5: Практичний додаток — Ритм і Манера** | ✅ | 64 | Included in Core |
| **Частина 6: Географія руху в Україні** | ✅ | 335 | Included in Core |
| **Частина 7: Рух у просторі культури та історії** | ✅ | 447 | Included in Core |
| **Підсумок** | ✅ | 59 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 110 | Skipped |