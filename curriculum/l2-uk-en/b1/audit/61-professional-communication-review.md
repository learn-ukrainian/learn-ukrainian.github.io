# Audit Report: 61-professional-communication.md
**Phase:** B1.5 | **Level:** B1 | **Pedagogy:** PPP | **Target:** 1500
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[COMPLEXITY_WORD_COUNT]** quiz 'Розуміння професійної лексики' Q1 prompt length 9 (target: 10-18)
  - FIX: Adjust prompt length to 10-18 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Розуміння професійної лексики' Q2 prompt length 8 (target: 10-18)
  - FIX: Adjust prompt length to 10-18 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Розуміння професійної лексики' Q3 prompt length 8 (target: 10-18)
  - FIX: Adjust prompt length to 10-18 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Розуміння професійної лексики' Q4 prompt length 7 (target: 10-18)
  - FIX: Adjust prompt length to 10-18 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Розуміння професійної лексики' Q5 prompt length 7 (target: 10-18)
  - FIX: Adjust prompt length to 10-18 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Розуміння професійної лексики' Q7 prompt length 6 (target: 10-18)
  - FIX: Adjust prompt length to 10-18 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Розуміння професійної лексики' Q8 prompt length 7 (target: 10-18)
  - FIX: Adjust prompt length to 10-18 words.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення' item 1 has 8 words (target: 10-14)
  - FIX: Adjust sentence length to 10-14 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення' item 2 has 7 words (target: 10-14)
  - FIX: Adjust sentence length to 10-14 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення' item 3 has 6 words (target: 10-14)
  - FIX: Adjust sentence length to 10-14 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення' item 4 has 5 words (target: 10-14)
  - FIX: Adjust sentence length to 10-14 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення' item 5 has 6 words (target: 10-14)
  - FIX: Adjust sentence length to 10-14 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення' item 6 has 7 words (target: 10-14)
  - FIX: Adjust sentence length to 10-14 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення' item 7 has 5 words (target: 10-14)
  - FIX: Adjust sentence length to 10-14 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення' item 8 has 7 words (target: 10-14)
  - FIX: Adjust sentence length to 10-14 words to match B1 complexity.
- **[SECTION_ORDER]** '## Лексика' should come after 'summary' section
  - FIX: Reorder sections to: Summary → Activities → Self-Assessment → External → Vocabulary
- **[SECTION_ORDER]** Content section '## Діалоги' appears after end section '## Лексика'
  - FIX: Reorder sections to: Summary → Activities → Self-Assessment → External → Vocabulary
- **[YAML_SCHEMA_VIOLATION]** Schema error in 61-professional-communication.yaml: [складіть-речення] unjumble: 'items.7' - Additional properties are not allowed ('scrambled' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 61-professional-communication.yaml: [знайдіть-професійну-лексику] mark-the-words: 'correct_words' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## TEMPLATE COMPLIANCE
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Presentation|Grammar|Focus|Презентація|Граматика|Теорія|Пояснення' per template 'b1-grammar-module-template'
  - FIX: Add '## Presentation' section as specified in docs/l2-uk-en/templates/b1-grammar-module-template.md
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Practice|Exercises|Activity|Практика|Вправи' per template 'b1-grammar-module-template'
  - FIX: Add '## Practice' section as specified in docs/l2-uk-en/templates/b1-grammar-module-template.md
- ❌ **[EMPTY_REQUIRED_SECTION]** Required section '## Потрібно більше практики?' is empty
  - FIX: Populate the section with meaningful content or generate it if it's a mandatory placeholder.

## Recommendation
**📝 UPDATE** (severity 50/100)

- Revision recommended (severity 50/100)
- 22 violations (severe - consider revision)

## Gates
- **Words:** ✅ 1641/1500
- **Activities:** ✅ 12/12
- **Density:** ✅ All > 14
- **Unique_types:** ✅ 10/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 12/5
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 15 < 35 (soft target)
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 19 violations
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 98.4% (target 85-100% (B1.5-6 Vocab))
- **Richness:** ✅ 99% (vocabulary)
- **Grammar:** ⏳ Pending validation

## Richness Details
**Score:** 99% (minimum: 95%)
**Module Type:** vocabulary

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| collocations | 30 | 20 | 100% | 25% | 25.0% |
| usage_examples | 24 | 15 | 100% | 20% | 20.0% |
| engagement | 12 | 4 | 100% | 15% | 15.0% |
| cultural | 5 | 3 | 100% | 10% | 10.0% |
| visual | 12 | 3 | 100% | 10% | 10.0% |
| register_notes | 15 | 5 | 100% | 10% | 10.0% |
| variety | 0.97 | - | 97% | 5% | 4.9% |
| paragraph_var | 1.00 | - | 100% | 5% | 5.0% |
| **TOTAL** | | | | | **99.8%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 53 | Included in Core |
| **Вступ** | ⚪️ | 75 | Skipped |
| **Лексика** | ⚪️ | 520 | Skipped |
| **Використання** | ⚪️ | 307 | Skipped |
| **Читання** | ✅ | 249 | Included in Core |
| **Діалоги** | ✅ | 273 | Included in Core |
| **Підсумок** | ✅ | 164 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 0 | Skipped |