# Audit Report: 64-synonyms-action.md
**Phase:** B2.2 | **Level:** B2 | **Pedagogy:** CBI | **Target:** 1750
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[COMPLEXITY]** match-up 'Знайдіть характер дії' has 8 pairs (target: 12-16)
  - FIX: Adjust number of pairs to 12-16.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Оберіть точну дію' Q1 prompt length 9 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Оберіть точну дію' Q2 prompt length 12 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Оберіть точну дію' Q3 prompt length 11 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Оберіть точну дію' Q4 prompt length 10 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Оберіть точну дію' Q5 prompt length 13 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Оберіть точну дію' Q6 prompt length 8 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Оберіть точну дію' Q7 prompt length 10 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Оберіть точну дію' Q8 prompt length 10 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY]** group-sort 'Дія чи Результат?' has 2 groups (target: 3-5)
  - FIX: Adjust number of sorting categories to 3-5.
- **[COMPLEXITY]** match-up 'Дія та Регістри' has 8 pairs (target: 12-16)
  - FIX: Adjust number of pairs to 12-16.
- **[COMPLEXITY]** match-up 'Дія та Її Об'єкт' has 8 pairs (target: 12-16)
  - FIX: Adjust number of pairs to 12-16.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Філософія чину' Q1 prompt length 9 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Філософія чину' Q2 prompt length 6 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Філософія чину' Q3 prompt length 6 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Філософія чину' Q4 prompt length 4 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Філософія чину' Q5 prompt length 5 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Філософія чину' Q6 prompt length 6 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Філософія чину' Q7 prompt length 4 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Філософія чину' Q8 prompt length 5 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[YAML_SCHEMA_VIOLATION]** Schema error in 64-synonyms-action.yaml: [оберіть-точну-дію] quiz: 'items.7.options.3' - 'correct' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 64-synonyms-action.yaml: [переклад-дії] translate: 'items.7.options.3' - 'correct' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 64-synonyms-action.yaml: [всі-форми-активності] select: 'items.0.options' - [{'text': 'чинити', 'correct': True}, {'text': 'діяти', 'correct': True}, {'text': 'виконувати', 'correct': True}, {'text': 'здійснювати', 'correct': True}, {'text': 'реалізовувати', 'correct': True}, {'text': 'втілювати', 'correct': True}, {'text': 'творити', 'correct': True}] is too long
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 64-synonyms-action.yaml: [філософія-чину] quiz: 'items.7.options.3' - 'correct' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[MISSING_ADVANCED_ACTIVITY]** B2+ module (focus: vocab) missing advanced activity type: essay-response
  - FIX: Add a essay-response activity to meet advanced richness standards.
- **[VOCAB_PLAN_MISSING]** Missing vocabulary from plan (18 words): діяти, зміна, вручати, віддавати, давати...
  - FIX: Add missing words from curriculum plan to module vocabulary section.

## Recommendation
**📝 UPDATE** (severity 50/100)

- Revision recommended (severity 50/100)
- 26 violations (severe - consider revision)

## Gates
- **Words:** ⚠️ 1720/1750 (30 short)
- **Activities:** ✅ 14/13
- **Density:** ✅ All > 16
- **Unique_types:** ✅ 10/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 6/6
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 67/35
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 25 violations
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 100.0% (target 98-100% (vocab))
- **Richness:** ✅ 95% (content)
- **Grammar:** ⏳ Pending validation

## Richness Details
**Score:** 95% (minimum: 95%)
**Module Type:** content

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| examples | 42 | 15 | 100% | 25% | 25.0% |
| engagement | 7 | 5 | 100% | 19% | 18.7% |
| variety | 0.96 | - | 96% | 12% | 12.0% |
| cultural | 3 | 4 | 75% | 12% | 9.4% |
| realworld | 8 | 3 | 100% | 12% | 12.5% |
| visual | 7 | 4 | 100% | 6% | 6.2% |
| paragraph_var | 0.88 | - | 88% | 6% | 5.5% |
| questions | 6 | 4 | 100% | 6% | 6.2% |
| **TOTAL** | | | | | **95.6%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 87 | Included in Core |
| **Вступ: Енергія українського чину та перетворення** | ⚪️ | 109 | Skipped |
| **Частина 1: Робити — Як ми змінюємо світ навколо себе** | ✅ | 286 | Included in Core |
| **Частина 2: Брати — Як ми взаємодіємо з ресурсами та об'єктами** | ✅ | 156 | Included in Core |
| **Частина 3: Категорії дії — Від вчинку до результату в аналізі** | ✅ | 144 | Included in Core |
| **Частина 4: Дія в українській культурі та філософії «чину»** | ✅ | 79 | Included in Core |
| **Частина 5: Практичний додаток — Контекст і Регістр мовлення** | ✅ | 13 | Included in Core |
| **Частина 6: Дія в епоху глобальних перетворень** | ✅ | 101 | Included in Core |
| **Частина 7: Відповідальність за кожен крок та результат** | ✅ | 65 | Included in Core |
| **Частина 8: Мистецтво вчинку та Моральна Дія** | ✅ | 93 | Included in Core |
| **Частина 9: Технологічна дія: Від алгоритму до результату** | ✅ | 79 | Included in Core |
| **Частина 10: Дія як головний інструмент соціальних змін** | ✅ | 171 | Included in Core |
| **Частина 11: Дія в контексті відновлення міст** | ✅ | 90 | Included in Core |
| **Частина 12: Дія як самореалізація в Дніпро** | ✅ | 76 | Included in Core |
| **Частина 13: Дія у сучасному мистецтві та медіа** | ✅ | 121 | Included in Core |
| **Підсумок** | ✅ | 50 | Included in Core |
| **Need More Practice?** | ⚪️ | 0 | Skipped |