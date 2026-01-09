# Audit Report: 69-synonymy-speaking-verbs.md
**Phase:** B1.6 | **Level:** B1 | **Pedagogy:** PPP | **Target:** 1500
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[COMPLEXITY_WORD_COUNT]** quiz 'Розуміння дієслів мовлення' Q4 prompt length 6 (target: 10-18)
  - FIX: Adjust prompt length to 10-18 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Розуміння дієслів мовлення' Q5 prompt length 6 (target: 10-18)
  - FIX: Adjust prompt length to 10-18 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Розуміння дієслів мовлення' Q6 prompt length 9 (target: 10-18)
  - FIX: Adjust prompt length to 10-18 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Розуміння дієслів мовлення' Q7 prompt length 6 (target: 10-18)
  - FIX: Adjust prompt length to 10-18 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Розуміння дієслів мовлення' Q8 prompt length 8 (target: 10-18)
  - FIX: Adjust prompt length to 10-18 words.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення' item 1 has 5 words (target: 10-14)
  - FIX: Adjust sentence length to 10-14 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення' item 2 has 4 words (target: 10-14)
  - FIX: Adjust sentence length to 10-14 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення' item 3 has 4 words (target: 10-14)
  - FIX: Adjust sentence length to 10-14 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення' item 4 has 4 words (target: 10-14)
  - FIX: Adjust sentence length to 10-14 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення' item 5 has 5 words (target: 10-14)
  - FIX: Adjust sentence length to 10-14 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення' item 6 has 4 words (target: 10-14)
  - FIX: Adjust sentence length to 10-14 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення' item 7 has 4 words (target: 10-14)
  - FIX: Adjust sentence length to 10-14 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення' item 8 has 4 words (target: 10-14)
  - FIX: Adjust sentence length to 10-14 words to match B1 complexity.
- **[SECTION_ORDER]** '## Лексика' should come after 'summary' section
  - FIX: Reorder sections to: Summary → Activities → Self-Assessment → External → Vocabulary
- **[SECTION_ORDER]** Content section '## Діалоги' appears after end section '## Лексика'
  - FIX: Reorder sections to: Summary → Activities → Self-Assessment → External → Vocabulary
- **[YAML_SCHEMA_VIOLATION]** Schema error in 69-synonymy-speaking-verbs.yaml: [складіть-речення] unjumble: 'items.7' - Additional properties are not allowed ('scrambled' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 69-synonymy-speaking-verbs.yaml: [знайдіть-дієслова-мовлення] mark-the-words: 'correct_words' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## TEMPLATE COMPLIANCE
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Practice|Exercises|Activity|Практика|Вправи' per template 'b1-grammar-module-template'
  - FIX: Add '## Practice' section as specified in docs/l2-uk-en/templates/b1-grammar-module-template.md
- ❌ **[EMPTY_REQUIRED_SECTION]** Required section '## Потрібно більше практики?' is empty
  - FIX: Populate the section with meaningful content or generate it if it's a mandatory placeholder.

## Recommendation
**📝 UPDATE** (severity 60/100)

- Revision recommended (severity 60/100)
- 19 violations (severe - consider revision)
- Activity density below minimum

## Gates
- **Words:** ✅ 1635/1500
- **Activities:** ✅ 12/12
- **Density:** ❌ 1 < 14
- **Unique_types:** ✅ 10/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 16/5
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 18 < 35 (soft target)
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 17 violations
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 99.6% (target 85-100% (B1.7-8 Ukraine))
- **Richness:** ✅ 99% (vocabulary)
- **Grammar:** ⏳ Pending validation

## Richness Details
**Score:** 99% (minimum: 95%)
**Module Type:** vocabulary

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| collocations | 30 | 20 | 100% | 25% | 25.0% |
| usage_examples | 26 | 15 | 100% | 20% | 20.0% |
| engagement | 16 | 4 | 100% | 15% | 15.0% |
| cultural | 4 | 3 | 100% | 10% | 10.0% |
| visual | 8 | 3 | 100% | 10% | 10.0% |
| register_notes | 15 | 5 | 100% | 10% | 10.0% |
| variety | 0.96 | - | 96% | 5% | 4.8% |
| paragraph_var | 1.00 | - | 100% | 5% | 5.0% |
| **TOTAL** | | | | | **99.8%** |

## Low Density Activities
| Activity | Type | Items | Required | Fix |
|----------|------|-------|----------|-----|
| Вибір дієслова з контексту | cloze | 12 | 14 | Add 2 more items |


## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 38 | Included in Core |
| **Вступ** | ⚪️ | 66 | Skipped |
| **Лексика** | ⚪️ | 485 | Skipped |
| **Використання** | ⚪️ | 305 | Skipped |
| **Читання** | ✅ | 253 | Included in Core |
| **Діалоги** | ✅ | 317 | Included in Core |
| **Підсумок** | ✅ | 171 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 0 | Skipped |