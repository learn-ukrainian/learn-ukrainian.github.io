# Audit Report: 59-media-news.md
**Phase:** B1.5 | **Level:** B1 | **Pedagogy:** PPP | **Target:** 1500
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[COMPLEXITY_WORD_COUNT]** quiz 'Розуміння медіа-лексики' Q2 prompt length 9 (target: 10-18)
  - FIX: Adjust prompt length to 10-18 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Розуміння медіа-лексики' Q3 prompt length 7 (target: 10-18)
  - FIX: Adjust prompt length to 10-18 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Розуміння медіа-лексики' Q4 prompt length 8 (target: 10-18)
  - FIX: Adjust prompt length to 10-18 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Розуміння медіа-лексики' Q5 prompt length 6 (target: 10-18)
  - FIX: Adjust prompt length to 10-18 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Розуміння медіа-лексики' Q6 prompt length 5 (target: 10-18)
  - FIX: Adjust prompt length to 10-18 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Розуміння медіа-лексики' Q7 prompt length 8 (target: 10-18)
  - FIX: Adjust prompt length to 10-18 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Розуміння медіа-лексики' Q8 prompt length 9 (target: 10-18)
  - FIX: Adjust prompt length to 10-18 words.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення про медіа' item 1 has 7 words (target: 10-14)
  - FIX: Adjust sentence length to 10-14 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення про медіа' item 2 has 7 words (target: 10-14)
  - FIX: Adjust sentence length to 10-14 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення про медіа' item 3 has 8 words (target: 10-14)
  - FIX: Adjust sentence length to 10-14 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення про медіа' item 4 has 7 words (target: 10-14)
  - FIX: Adjust sentence length to 10-14 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення про медіа' item 5 has 5 words (target: 10-14)
  - FIX: Adjust sentence length to 10-14 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення про медіа' item 6 has 7 words (target: 10-14)
  - FIX: Adjust sentence length to 10-14 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення про медіа' item 7 has 6 words (target: 10-14)
  - FIX: Adjust sentence length to 10-14 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення про медіа' item 8 has 6 words (target: 10-14)
  - FIX: Adjust sentence length to 10-14 words to match B1 complexity.
- **[COMPLEXITY]** mark-the-words 'Знайдіть медіа-лексику' has 0 items (minimum: 6)
  - FIX: Add more items. B1 mark-the-words requires at least 6 items.
- **[SECTION_ORDER]** '## Лексика' should come after 'summary' section
  - FIX: Reorder sections to: Summary → Activities → Self-Assessment → External → Vocabulary
- **[SECTION_ORDER]** Content section '## Діалоги' appears after end section '## Лексика'
  - FIX: Reorder sections to: Summary → Activities → Self-Assessment → External → Vocabulary
- **[MISSING_FIELD]** mark-the-words 'Знайдіть медіа-лексику' is missing 'correct_words' array
  - FIX: Add 'correct_words' array with correct words
- **[YAML_SCHEMA_VIOLATION]** Schema error in 59-media-news.yaml: [mark-media-vocabulary] mark-the-words: 'correct_words' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## TEMPLATE COMPLIANCE
- ❌ **[DUPLICATE_SYNONYMOUS_HEADERS]** Multiple aliases for 'Warm-up|Introduction|Objectives|Контекст|Вступ|Розминка|Тест' found: Приклади в контексті, Вступ
  - FIX: Keep only one version of the header (preferably the primary one or the one with more content).
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Presentation|Grammar|Focus|Презентація|Граматика|Теорія|Пояснення' per template 'b1-grammar-module-template'
  - FIX: Add '## Presentation' section as specified in docs/l2-uk-en/templates/b1-grammar-module-template.md
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Practice|Exercises|Activity|Практика|Вправи' per template 'b1-grammar-module-template'
  - FIX: Add '## Practice' section as specified in docs/l2-uk-en/templates/b1-grammar-module-template.md
- ❌ **[EMPTY_REQUIRED_SECTION]** Required section '## Потрібно більше практики?' is empty
  - FIX: Populate the section with meaningful content or generate it if it's a mandatory placeholder.

## Recommendation
**📝 UPDATE** (severity 60/100)

- Revision recommended (severity 60/100)
- 24 violations (severe - consider revision)
- Activity density below minimum

## Gates
- **Words:** ✅ 1525/1500
- **Activities:** ✅ 12/12
- **Density:** ❌ 1 < 14
- **Unique_types:** ✅ 11/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 10/5
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 19 < 35 (soft target)
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 20 violations
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 99.6% (target 85-100% (B1.5-6 Vocab))
- **Richness:** ✅ 96% (vocabulary)
- **Grammar:** ⏳ Pending validation

## Richness Details
**Score:** 96% (minimum: 95%)
**Module Type:** vocabulary

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| collocations | 30 | 20 | 100% | 25% | 25.0% |
| usage_examples | 25 | 15 | 100% | 20% | 20.0% |
| engagement | 10 | 4 | 100% | 15% | 15.0% |
| cultural | 2 | 3 | 67% | 10% | 6.7% |
| visual | 8 | 3 | 100% | 10% | 10.0% |
| register_notes | 15 | 5 | 100% | 10% | 10.0% |
| variety | 0.96 | - | 96% | 5% | 4.8% |
| paragraph_var | 1.00 | - | 100% | 5% | 5.0% |
| **TOTAL** | | | | | **96.5%** |

## Low Density Activities
| Activity | Type | Items | Required | Fix |
|----------|------|-------|----------|-----|
| Знайдіть медіа-лексику | mark-the-words | 0 | 6 | Add 6 more items |


## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 49 | Included in Core |
| **Вступ** | ⚪️ | 85 | Skipped |
| **Лексика** | ⚪️ | 316 | Skipped |
| **Використання** | ⚪️ | 354 | Skipped |
| **Читання** | ✅ | 268 | Included in Core |
| **Діалоги** | ✅ | 281 | Included in Core |
| **Підсумок** | ✅ | 172 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 0 | Skipped |