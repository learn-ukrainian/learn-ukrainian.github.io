# Audit Report: 67-travel-geography.md
**Phase:** B1.6 | **Level:** B1 | **Pedagogy:** PPP | **Target:** 1500
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[COMPLEXITY_WORD_COUNT]** quiz 'Розуміння лексики подорожей' Q3 prompt length 7 (target: 8-18)
  - FIX: Adjust prompt length to 8-18 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Розуміння лексики подорожей' Q4 prompt length 6 (target: 8-18)
  - FIX: Adjust prompt length to 8-18 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Розуміння лексики подорожей' Q5 prompt length 7 (target: 8-18)
  - FIX: Adjust prompt length to 8-18 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Розуміння лексики подорожей' Q6 prompt length 6 (target: 8-18)
  - FIX: Adjust prompt length to 8-18 words.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення' item 1 has 6 words (target: 8-14)
  - FIX: Adjust sentence length to 8-14 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення' item 2 has 4 words (target: 8-14)
  - FIX: Adjust sentence length to 8-14 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення' item 4 has 6 words (target: 8-14)
  - FIX: Adjust sentence length to 8-14 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення' item 5 has 5 words (target: 8-14)
  - FIX: Adjust sentence length to 8-14 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення' item 6 has 5 words (target: 8-14)
  - FIX: Adjust sentence length to 8-14 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення' item 7 has 4 words (target: 8-14)
  - FIX: Adjust sentence length to 8-14 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення' item 8 has 6 words (target: 8-14)
  - FIX: Adjust sentence length to 8-14 words to match B1 complexity.
- **[SECTION_ORDER]** '## Лексика' should come after 'summary' section
  - FIX: Reorder sections to: Summary → Activities → Self-Assessment → External → Vocabulary
- **[SECTION_ORDER]** Content section '## Діалоги' appears after end section '## Лексика'
  - FIX: Reorder sections to: Summary → Activities → Self-Assessment → External → Vocabulary
- **[YAML_SCHEMA_VIOLATION]** Schema error in 67-travel-geography.yaml: [index-8] unjumble: 'items.7' - Additional properties are not allowed ('scrambled' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 67-travel-geography.yaml: [index-11] mark-the-words: 'correct_words' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## TEMPLATE COMPLIANCE
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Пояснення|Граматика|Теорія' per template 'b1-grammar-module-template'
  - FIX: Add '## Пояснення' section as specified in docs/l2-uk-en/templates/b1-grammar-module-template.md
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Практика|Вправи' per template 'b1-grammar-module-template'
  - FIX: Add '## Практика' section as specified in docs/l2-uk-en/templates/b1-grammar-module-template.md

## Recommendation
**📝 UPDATE** (severity 50/100)

- Revision recommended (severity 50/100)
- 17 violations (severe - consider revision)

## Gates
- **Words:** ✅ 1660/1500
- **Activities:** ✅ 12/8
- **Density:** ✅ All > 12
- **Unique_types:** ✅ 10/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 13/5
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 38/35
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 15 violations
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 98.8% (target 85-100% (B1.7-8 Ukraine))
- **Richness:** ✅ 99% (vocabulary)
- **Grammar:** ⏳ Pending validation

## Richness Details
**Score:** 99% (minimum: 95%)
**Module Type:** vocabulary

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| collocations | 30 | 20 | 100% | 25% | 25.0% |
| usage_examples | 15 | 15 | 100% | 20% | 20.0% |
| engagement | 13 | 4 | 100% | 15% | 15.0% |
| cultural | 12 | 3 | 100% | 10% | 10.0% |
| visual | 6 | 3 | 100% | 10% | 10.0% |
| register_notes | 14 | 5 | 100% | 10% | 10.0% |
| variety | 0.98 | - | 98% | 5% | 4.9% |
| paragraph_var | 1.00 | - | 100% | 5% | 5.0% |
| **TOTAL** | | | | | **99.9%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 56 | Included in Core |
| **Вступ** | ⚪️ | 107 | Skipped |
| **Лексика** | ⚪️ | 440 | Skipped |
| **Використання** | ⚪️ | 141 | Skipped |
| **Читання** | ✅ | 445 | Included in Core |
| **Діалоги** | ✅ | 200 | Included in Core |
| **Підсумок** | ✅ | 161 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 110 | Skipped |