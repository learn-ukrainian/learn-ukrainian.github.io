# Audit Report: 63-synonyms-quantity.md
**Phase:** B2.2 | **Level:** B2 | **Pedagogy:** CBI | **Target:** 1750
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[COMPLEXITY]** match-up 'Знайдіть точну міру' has 8 pairs (target: 12-16)
  - FIX: Adjust number of pairs to 12-16.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Оберіть масштаб' Q1 prompt length 12 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Оберіть масштаб' Q2 prompt length 12 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Оберіть масштаб' Q3 prompt length 10 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Оберіть масштаб' Q4 prompt length 12 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Оберіть масштаб' Q5 prompt length 12 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Оберіть масштаб' Q6 prompt length 12 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Оберіть масштаб' Q7 prompt length 11 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Оберіть масштаб' Q8 prompt length 9 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY]** group-sort 'Багато чи Мало?' has 2 groups (target: 3-5)
  - FIX: Adjust number of sorting categories to 3-5.
- **[COMPLEXITY]** match-up 'Регістри та Кількість' has 8 pairs (target: 12-16)
  - FIX: Adjust number of pairs to 12-16.
- **[COMPLEXITY]** match-up 'Кількість та Об'єкти' has 8 pairs (target: 12-16)
  - FIX: Adjust number of pairs to 12-16.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Кількість у житті' Q1 prompt length 6 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Кількість у житті' Q2 prompt length 6 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Кількість у житті' Q3 prompt length 5 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Кількість у житті' Q4 prompt length 5 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Кількість у житті' Q5 prompt length 6 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Кількість у житті' Q6 prompt length 4 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Кількість у житті' Q7 prompt length 4 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Кількість у житті' Q8 prompt length 6 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[YAML_SCHEMA_VIOLATION]** Schema error in 63-synonyms-quantity.yaml: [оберіть-масштаб] quiz: 'items.7.options.3' - 'correct' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 63-synonyms-quantity.yaml: [переклад-міри] translate: 'items.7.options.3' - 'correct' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 63-synonyms-quantity.yaml: [всі-відтінки-багатоманітності] select: 'items.0.options' - [{'text': 'чимало', 'correct': True}, {'text': 'безліч', 'correct': True}, {'text': 'сила-силенна', 'correct': True}, {'text': 'маса', 'correct': True}, {'text': 'купа', 'correct': True}, {'text': 'повно', 'correct': True}, {'text': 'хоч греблю гати', 'correct': True}, {'text': 'мізер', 'correct': False}] is too long
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 63-synonyms-quantity.yaml: [кількість-у-житті] quiz: 'items.7.options.3' - 'correct' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[MISSING_ADVANCED_ACTIVITY]** B2+ module (focus: vocab) missing advanced activity type: essay-response
  - FIX: Add a essay-response activity to meet advanced richness standards.
- **[VOCAB_PLAN_MISSING]** Missing vocabulary from plan (17 words): обсяг, число, недостатньо, сила, ніякий...
  - FIX: Add missing words from curriculum plan to module vocabulary section.

## Recommendation
**📝 UPDATE** (severity 50/100)

- Revision recommended (severity 50/100)
- 26 violations (severe - consider revision)

## Gates
- **Words:** ✅ 2282/1750
- **Activities:** ✅ 14/13
- **Density:** ✅ All > 16
- **Unique_types:** ✅ 10/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 6/6
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 60/35
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 25 violations
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 99.8% (target 98-100% (vocab))
- **Richness:** ✅ 95% (content)
- **Grammar:** ⏳ Pending validation

## Richness Details
**Score:** 95% (minimum: 95%)
**Module Type:** content

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| examples | 64 | 15 | 100% | 25% | 25.0% |
| engagement | 8 | 5 | 100% | 19% | 18.7% |
| variety | 0.70 | - | 70% | 12% | 8.8% |
| cultural | 5 | 4 | 100% | 12% | 12.5% |
| realworld | 9 | 3 | 100% | 12% | 12.5% |
| visual | 8 | 4 | 100% | 6% | 6.2% |
| paragraph_var | 0.86 | - | 86% | 6% | 5.4% |
| questions | 9 | 4 | 100% | 6% | 6.2% |
| **TOTAL** | | | | | **95.4%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 69 | Included in Core |
| **Вступ: Масштаби українського життя** | ⚪️ | 98 | Skipped |
| **Частина 1: Океан багатоманітності — Від «багато» до «безлічі»** | ✅ | 280 | Included in Core |
| **Частина 2: Острів недостатності — Від «мало» до «декількох»** | ✅ | 253 | Included in Core |
| **Частина 3: Параметри вимірювання та Аналіз обсягів** | ✅ | 111 | Included in Core |
| **Частина 4: Кількість у дзеркалі української історії та культури** | ✅ | 135 | Included in Core |
| **Частина 5: Практичний додаток — Регістри та Акценти** | ✅ | 16 | Included in Core |
| **Частина 6: Психологія сприйняття кількості** | ✅ | 116 | Included in Core |
| **Частина 7: Формування культури достатку** | ✅ | 133 | Included in Core |
| **Частина 8: Кількість у цифрову епоху** | ✅ | 95 | Included in Core |
| **Частина 9: Соціальний масштаб та Кількість можливостей** | ✅ | 80 | Included in Core |
| **Частина 3: Параметри вимірювання та Аналіз обсягів у професійній мові** | ✅ | 166 | Included in Core |
| **Частина 5: Практичний додаток — Регістри та Кількісні Акценти** | ✅ | 22 | Included in Core |
| **Частина 6: Психологія сприйняття кількості та баланс у житті** | ✅ | 138 | Included in Core |
| **Частина 7: Формування культури свідомого достатку** | ✅ | 96 | Included in Core |
| **Підсумок** | ✅ | 52 | Included in Core |
| **Need More Practice?** | ⚪️ | 0 | Skipped |