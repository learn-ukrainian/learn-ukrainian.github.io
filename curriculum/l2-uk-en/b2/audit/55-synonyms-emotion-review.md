# Audit Report: 55-synonyms-emotion.md
**Phase:** B2.2 | **Level:** B2 | **Pedagogy:** CBI | **Target:** 1750
**Overall Status:** ❌ FAIL

## LINT ERRORS
- ❌ Line 124: Use Ukrainian angular quotes («...») instead of ASCII quotes (").
- ❌ Line 130: Use Ukrainian angular quotes («...») instead of ASCII quotes (").

## PEDAGOGICAL VIOLATIONS
- **[COMPLEXITY]** match-up 'Знайдіть значення' has 8 pairs (target: 12-16)
  - FIX: Adjust number of pairs to 12-16.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Оберіть точне слово' Q1 prompt length 13 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Оберіть точне слово' Q2 prompt length 14 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Оберіть точне слово' Q3 prompt length 10 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Оберіть точне слово' Q4 prompt length 13 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Оберіть точне слово' Q5 prompt length 12 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Оберіть точне слово' Q6 prompt length 12 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Оберіть точне слово' Q7 prompt length 14 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Оберіть точне слово' Q8 prompt length 13 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Емоційні речення' item 1 has 6 words (target: 14-18)
  - FIX: Adjust sentence length to 14-18 words to match B2 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Емоційні речення' item 2 has 5 words (target: 14-18)
  - FIX: Adjust sentence length to 14-18 words to match B2 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Емоційні речення' item 3 has 5 words (target: 14-18)
  - FIX: Adjust sentence length to 14-18 words to match B2 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Емоційні речення' item 4 has 5 words (target: 14-18)
  - FIX: Adjust sentence length to 14-18 words to match B2 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Емоційні речення' item 5 has 5 words (target: 14-18)
  - FIX: Adjust sentence length to 14-18 words to match B2 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Емоційні речення' item 6 has 6 words (target: 14-18)
  - FIX: Adjust sentence length to 14-18 words to match B2 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Емоційні речення' item 7 has 6 words (target: 14-18)
  - FIX: Adjust sentence length to 14-18 words to match B2 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Емоційні речення' item 8 has 5 words (target: 14-18)
  - FIX: Adjust sentence length to 14-18 words to match B2 complexity.
- **[COMPLEXITY]** group-sort 'Позитивні чи Негативні?' has 2 groups (target: 3-5)
  - FIX: Adjust number of sorting categories to 3-5.
- **[COMPLEXITY]** match-up 'Контексти вживання (Емоції)' has 8 pairs (target: 12-16)
  - FIX: Adjust number of pairs to 12-16.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Психологічні нюанси' Q1 prompt length 11 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Психологічні нюанси' Q2 prompt length 5 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Психологічні нюанси' Q3 prompt length 10 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Психологічні нюанси' Q4 prompt length 6 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Психологічні нюанси' Q5 prompt length 13 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Психологічні нюанси' Q6 prompt length 11 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Психологічні нюанси' Q7 prompt length 11 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Психологічні нюанси' Q8 prompt length 9 (target: 15-25)
  - FIX: Adjust prompt length to 15-25 words.
- **[YAML_SCHEMA_VIOLATION]** Schema error in 55-synonyms-emotion.yaml: [переклад-почуттів] translate: 'items.7.options.3' - 'correct' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 55-synonyms-emotion.yaml: [психологічні-нюанси] quiz: 'items.7.options.3' - 'correct' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[MISSING_ADVANCED_ACTIVITY]** B2+ module (focus: vocab) missing advanced activity type: essay-response
  - FIX: Add a essay-response activity to meet advanced richness standards.
- **[VOCAB_PLAN_MISSING]** Missing vocabulary from plan (16 words): щастя, задоволення, сум, радість, тривога...
  - FIX: Add missing words from curriculum plan to module vocabulary section.

## Recommendation
**📝 UPDATE** (severity 52/100)

- Revision recommended (severity 52/100)
- 31 violations (severe - consider revision)

## Gates
- **Words:** ✅ 1773/1750
- **Activities:** ✅ 13/13
- **Density:** ✅ All > 16
- **Unique_types:** ✅ 10/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 7/6
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 104/35
- **Structure:** ✅ Valid Structure
- **Lint:** ❌ 2 Format Errors
- **Pedagogy:** ❌ 30 violations
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 99.8% (target 98-100% (vocab))
- **Richness:** ✅ 99% (content)
- **Grammar:** ⏳ Pending validation

## Richness Details
**Score:** 99% (minimum: 95%)
**Module Type:** content

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| examples | 52 | 15 | 100% | 25% | 25.0% |
| engagement | 8 | 5 | 100% | 19% | 18.7% |
| variety | 1.00 | - | 100% | 12% | 12.5% |
| cultural | 4 | 4 | 100% | 12% | 12.5% |
| realworld | 6 | 3 | 100% | 12% | 12.5% |
| visual | 4 | 4 | 100% | 6% | 6.2% |
| paragraph_var | 1.00 | - | 100% | 6% | 6.2% |
| questions | 10 | 4 | 100% | 6% | 6.2% |
| **TOTAL** | | | | | **100.0%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 87 | Included in Core |
| **Вступ: Мова як інструмент душі та дзеркало серця** | ⚪️ | 220 | Skipped |
| **Частина 1: Світло радості — Від задоволення до екстазу** | ✅ | 238 | Included in Core |
| **Частина 2: Сутінки суму — Від печалі до повного розпачу** | ✅ | 237 | Included in Core |
| **Частина 3: Вогонь гніву та Тінь паралізуючого страху** | ✅ | 286 | Included in Core |
| **Культурний код: Емоції в українській ментальності та філософії** | ✅ | 423 | Included in Core |
| **Емоції та почуття в українській класичній літературі** | ⚪️ | 124 | Skipped |
| **Практичний додаток: Таблиця інтенсивності та Регістрів** | ⚪️ | 68 | Skipped |
| **Підсумок** | ✅ | 90 | Included in Core |
| **Need More Practice?** | ⚪️ | 0 | Skipped |