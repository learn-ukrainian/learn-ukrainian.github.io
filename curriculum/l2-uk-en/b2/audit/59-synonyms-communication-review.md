# Audit Report: 59-synonyms-communication.md
**Phase:** B2.2 | **Level:** B2 | **Pedagogy:** CBI | **Target:** 1750
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[COMPLEXITY]** match-up 'Знайдіть контекст мовлення' has 8 pairs (target: 12-16)
  - FIX: Adjust number of pairs to 12-16.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Оберіть точне дієслово' Q1 prompt length 12 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Оберіть точне дієслово' Q2 prompt length 11 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Оберіть точне дієслово' Q3 prompt length 10 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Оберіть точне дієслово' Q4 prompt length 11 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Оберіть точне дієслово' Q5 prompt length 9 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Оберіть точне дієслово' Q6 prompt length 12 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Оберіть точне дієслово' Q7 prompt length 9 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Оберіть точне дієслово' Q8 prompt length 10 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY]** group-sort 'Рівень офіційності' has 2 groups (target: 3-5)
  - FIX: Adjust number of sorting categories to 3-5.
- **[COMPLEXITY]** match-up 'Спілкування та Регістри' has 8 pairs (target: 12-16)
  - FIX: Adjust number of pairs to 12-16.
- **[COMPLEXITY]** match-up 'Антоніми спілкування' has 8 pairs (target: 12-16)
  - FIX: Adjust number of pairs to 12-16.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Метафоричне слово' Q1 prompt length 7 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Метафоричне слово' Q2 prompt length 6 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Метафоричне слово' Q3 prompt length 4 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Метафоричне слово' Q4 prompt length 7 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Метафоричне слово' Q5 prompt length 5 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Метафоричне слово' Q6 prompt length 4 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Метафоричне слово' Q7 prompt length 7 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Метафоричне слово' Q8 prompt length 7 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[YAML_SCHEMA_VIOLATION]** Schema error in 59-synonyms-communication.yaml: [переклад-спілкування] translate: 'items.7.options.3' - 'correct' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 59-synonyms-communication.yaml: [метафоричне-слово] quiz: 'items.7.options.3' - 'correct' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 59-synonyms-communication.yaml: [професійна-комунікація] select: 'items.0.options' - [{'text': 'пропонувати', 'correct': True}, {'text': 'узгоджувати', 'correct': True}, {'text': 'базікати', 'correct': False}, {'text': 'підтверджувати', 'correct': True}, {'text': 'теревенити', 'correct': False}, {'text': 'резюмувати', 'correct': True}, {'text': 'обговорювати', 'correct': True}, {'text': 'уточнювати', 'correct': True}] is too long
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[MISSING_ADVANCED_ACTIVITY]** B2+ module (focus: vocab) missing advanced activity type: essay-response
  - FIX: Add a essay-response activity to meet advanced richness standards.
- **[VOCAB_PLAN_MISSING]** Missing vocabulary from plan (20 words): запитувати, монолог, сперечатися, пояснювати, бесіда...
  - FIX: Add missing words from curriculum plan to module vocabulary section.

## Recommendation
**📝 UPDATE** (severity 50/100)

- Revision recommended (severity 50/100)
- 25 violations (severe - consider revision)

## Gates
- **Words:** ⚠️ 1699/1750 (51 short)
- **Activities:** ✅ 14/13
- **Density:** ✅ All > 16
- **Unique_types:** ✅ 10/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 7/6
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 58/35
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 24 violations
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 100.0% (target 98-100% (vocab))
- **Richness:** ✅ 98% (content)
- **Grammar:** ⏳ Pending validation

## Richness Details
**Score:** 98% (minimum: 95%)
**Module Type:** content

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| examples | 39 | 15 | 100% | 25% | 25.0% |
| engagement | 8 | 5 | 100% | 19% | 18.7% |
| variety | 0.97 | - | 97% | 12% | 12.1% |
| cultural | 7 | 4 | 100% | 12% | 12.5% |
| realworld | 10 | 3 | 100% | 12% | 12.5% |
| visual | 8 | 4 | 100% | 6% | 6.2% |
| paragraph_var | 0.84 | - | 84% | 6% | 5.2% |
| questions | 8 | 4 | 100% | 6% | 6.2% |
| **TOTAL** | | | | | **98.6%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 70 | Included in Core |
| **Вступ: Мистецтво висловлення думки** | ⚪️ | 115 | Skipped |
| **Частина 1: Сказати — Як передати інформацію** | ✅ | 190 | Included in Core |
| **Частина 2: Питати — Як дізнатися істину** | ✅ | 144 | Included in Core |
| **Частина 3: Форми комунікації — Від монологу до переговорів** | ✅ | 205 | Included in Core |
| **Частина 4: Мовлення в українській літературі та фольклорі** | ✅ | 108 | Included in Core |
| **Частина 5: Практичний додаток — Тон та Контекст** | ✅ | 41 | Included in Core |
| **Частина 6: Комунікація в сучасному світі** | ✅ | 106 | Included in Core |
| **Частина 7: Дискусія як інструмент розвитку** | ✅ | 335 | Included in Core |
| **Частина 7: Рух у просторі культури через діалог** | ✅ | 337 | Included in Core |
| **Підсумок** | ✅ | 48 | Included in Core |
| **Need More Practice?** | ⚪️ | 0 | Skipped |