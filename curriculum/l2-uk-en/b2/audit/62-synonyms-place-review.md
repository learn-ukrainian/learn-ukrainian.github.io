# Audit Report: 62-synonyms-place.md
**Phase:** B2.2 | **Level:** B2 | **Pedagogy:** CBI | **Target:** 1750
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[COMPLEXITY]** match-up 'Знайдіть місце' has 8 pairs (target: 12-16)
  - FIX: Adjust number of pairs to 12-16.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Орієнтування у просторі' Q3 prompt length 11 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Орієнтування у просторі' Q4 prompt length 13 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Орієнтування у просторі' Q5 prompt length 9 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Орієнтування у просторі' Q6 prompt length 14 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Орієнтування у просторі' Q7 prompt length 9 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Орієнтування у просторі' Q8 prompt length 14 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY]** group-sort 'Статика чи Напрямок?' has 2 groups (target: 3-5)
  - FIX: Adjust number of sorting categories to 3-5.
- **[COMPLEXITY]** match-up 'Простір та Об'єкти' has 8 pairs (target: 12-16)
  - FIX: Adjust number of pairs to 12-16.
- **[COMPLEXITY]** match-up 'Антоніми простору' has 8 pairs (target: 12-16)
  - FIX: Adjust number of pairs to 12-16.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Простір пам'яті' Q1 prompt length 8 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Простір пам'яті' Q2 prompt length 7 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Простір пам'яті' Q3 prompt length 5 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Простір пам'яті' Q4 prompt length 6 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Простір пам'яті' Q5 prompt length 3 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Простір пам'яті' Q6 prompt length 6 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Простір пам'яті' Q7 prompt length 5 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Простір пам'яті' Q8 prompt length 4 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[YAML_SCHEMA_VIOLATION]** Schema error in 62-synonyms-place.yaml: [орієнтування-у-просторі] quiz: 'items.7.options.3' - 'correct' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 62-synonyms-place.yaml: [переклад-простору] translate: 'items.7.options.3' - 'correct' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 62-synonyms-place.yaml: [простір-пам'яті] quiz: 'items.7.options.3' - 'correct' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[MISSING_ADVANCED_ACTIVITY]** B2+ module (focus: vocab) missing advanced activity type: essay-response
  - FIX: Add a essay-response activity to meet advanced richness standards.
- **[VOCAB_PLAN_MISSING]** Missing vocabulary from plan (15 words): район, туди, простір, близько, сюди...
  - FIX: Add missing words from curriculum plan to module vocabulary section.

## Recommendation
**📝 UPDATE** (severity 50/100)

- Revision recommended (severity 50/100)
- 23 violations (severe - consider revision)

## Gates
- **Words:** ⚠️ 1656/1750 (94 short)
- **Activities:** ✅ 14/13
- **Density:** ✅ All > 16
- **Unique_types:** ✅ 10/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 6/6
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 57/35
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 22 violations
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 99.9% (target 98-100% (vocab))
- **Richness:** ✅ 98% (content)
- **Grammar:** ⏳ Pending validation

## Richness Details
**Score:** 98% (minimum: 95%)
**Module Type:** content

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| examples | 32 | 15 | 100% | 25% | 25.0% |
| engagement | 7 | 5 | 100% | 19% | 18.7% |
| variety | 0.95 | - | 95% | 12% | 11.9% |
| cultural | 4 | 4 | 100% | 12% | 12.5% |
| realworld | 6 | 3 | 100% | 12% | 12.5% |
| visual | 6 | 4 | 100% | 6% | 6.2% |
| paragraph_var | 0.86 | - | 86% | 6% | 5.4% |
| questions | 12 | 4 | 100% | 6% | 6.2% |
| **TOTAL** | | | | | **98.5%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 87 | Included in Core |
| **Вступ: Карта українського простору** | ⚪️ | 97 | Skipped |
| **Частина 1: Тут і Там — Магія вказівки** | ✅ | 153 | Included in Core |
| **Частина 2: Відстань та Близькість** | ✅ | 79 | Included in Core |
| **Частина 3: Простір та Локації — Від точки до території** | ✅ | 106 | Included in Core |
| **Частина 4: Простір в українській культурі — Шацькі озера** | ✅ | 65 | Included in Core |
| **Частина 5: Практичний додаток — Навігація в розмові** | ✅ | 50 | Included in Core |
| **Частина 6: Напрямок руху — Від «сюди» до «кудись»** | ✅ | 63 | Included in Core |
| **Частина 7: Простір у цифрову епоху** | ✅ | 71 | Included in Core |
| **Частина 8: Концепція дому в українському світогляді** | ✅ | 100 | Included in Core |
| **Частина 9: Ландшафт як доля — Гори, Степ та Море** | ✅ | 91 | Included in Core |
| **Частина 10: Простір майбутнього — Урбаністика та Екологія** | ✅ | 98 | Included in Core |
| **Частина 11: Простір пам'яті та меморіальна лексика** | ✅ | 208 | Included in Core |
| **Частина 12: Простір у художній візії та мистецтві** | ✅ | 81 | Included in Core |
| **Частина 13: Геометрія українського міста: Від майдану до дворика** | ✅ | 81 | Included in Core |
| **Частина 14: Психологія рідного місця: Дім та Оселя** | ✅ | 96 | Included in Core |
| **Частина 15: Простір як виклик та можливість** | ✅ | 82 | Included in Core |
| **Підсумок** | ✅ | 48 | Included in Core |
| **Need More Practice?** | ⚪️ | 0 | Skipped |