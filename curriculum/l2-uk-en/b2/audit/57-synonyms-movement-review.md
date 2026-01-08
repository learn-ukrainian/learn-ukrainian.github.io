# Audit Report: 57-synonyms-movement.md
**Phase:** B2.2 | **Level:** B2 | **Pedagogy:** CBI | **Target:** 1750
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[COMPLEXITY]** match-up 'Знайдіть манеру руху' has 8 pairs (target: 12-16)
  - FIX: Adjust number of pairs to 12-16.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Оберіть точний рух' Q1 prompt length 14 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Оберіть точний рух' Q2 prompt length 11 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Оберіть точний рух' Q3 prompt length 10 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Оберіть точний рух' Q4 prompt length 9 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Оберіть точний рух' Q5 prompt length 13 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Оберіть точний рух' Q6 prompt length 11 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Оберіть точний рух' Q7 prompt length 13 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Оберіть точний рух' Q8 prompt length 10 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY]** match-up 'Рух та Його Джерело' has 8 pairs (target: 12-16)
  - FIX: Adjust number of pairs to 12-16.
- **[COMPLEXITY]** match-up 'Антоніми за манерою' has 8 pairs (target: 12-16)
  - FIX: Adjust number of pairs to 12-16.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Метафоричний рух' Q1 prompt length 7 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Метафоричний рух' Q2 prompt length 9 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Метафоричний рух' Q3 prompt length 7 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Метафоричний рух' Q4 prompt length 6 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Метафоричний рух' Q5 prompt length 6 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Метафоричний рух' Q6 prompt length 7 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Метафоричний рух' Q7 prompt length 5 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Метафоричний рух' Q8 prompt length 5 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[YAML_SCHEMA_VIOLATION]** Schema error in 57-synonyms-movement.yaml: [перекладіть-дію] translate: 'items.7.options.3' - 'correct' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 57-synonyms-movement.yaml: [метафоричний-рух] quiz: 'items.7.options.3' - 'correct' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[MISSING_ADVANCED_ACTIVITY]** B2+ module (focus: vocab) missing advanced activity type: essay-response
  - FIX: Add a essay-response activity to meet advanced richness standards.
- **[VOCAB_PLAN_MISSING]** Missing vocabulary from plan (14 words): стрибати, ходити, обережно, незграбно, рухатися...
  - FIX: Add missing words from curriculum plan to module vocabulary section.

## Recommendation
**📝 UPDATE** (severity 50/100)

- Revision recommended (severity 50/100)
- 23 violations (severe - consider revision)

## Gates
- **Words:** ⚠️ 1658/1750 (92 short)
- **Activities:** ✅ 14/13
- **Density:** ✅ All > 16
- **Unique_types:** ✅ 10/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 6/6
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 136/35
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 22 violations
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 99.9% (target 98-100% (vocab))
- **Richness:** ✅ 99% (content)
- **Grammar:** ⏳ Pending validation

## Richness Details
**Score:** 99% (minimum: 95%)
**Module Type:** content

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| examples | 48 | 15 | 100% | 25% | 25.0% |
| engagement | 6 | 5 | 100% | 19% | 18.7% |
| variety | 0.95 | - | 95% | 12% | 11.9% |
| cultural | 7 | 4 | 100% | 12% | 12.5% |
| realworld | 8 | 3 | 100% | 12% | 12.5% |
| visual | 5 | 4 | 100% | 6% | 6.2% |
| paragraph_var | 0.97 | - | 97% | 6% | 6.1% |
| questions | 8 | 4 | 100% | 6% | 6.2% |
| **TOTAL** | | | | | **99.2%** |

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
| **Need More Practice?** | ⚪️ | 0 | Skipped |