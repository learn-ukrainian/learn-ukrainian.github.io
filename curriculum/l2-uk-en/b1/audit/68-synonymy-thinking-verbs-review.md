# Audit Report: 68-synonymy-thinking-verbs.md
**Phase:** B1.6 | **Level:** B1 | **Pedagogy:** PPP | **Target:** 1500
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[COMPLEXITY_WORD_COUNT]** quiz 'Розуміння дієслів мислення' Q1 prompt length 8 (target: 12-20)
  - FIX: Adjust prompt length to 12-20 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Розуміння дієслів мислення' Q2 prompt length 9 (target: 12-20)
  - FIX: Adjust prompt length to 12-20 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Розуміння дієслів мислення' Q3 prompt length 9 (target: 12-20)
  - FIX: Adjust prompt length to 12-20 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Розуміння дієслів мислення' Q4 prompt length 8 (target: 12-20)
  - FIX: Adjust prompt length to 12-20 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Розуміння дієслів мислення' Q5 prompt length 9 (target: 12-20)
  - FIX: Adjust prompt length to 12-20 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Розуміння дієслів мислення' Q6 prompt length 11 (target: 12-20)
  - FIX: Adjust prompt length to 12-20 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Розуміння дієслів мислення' Q7 prompt length 7 (target: 12-20)
  - FIX: Adjust prompt length to 12-20 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Розуміння дієслів мислення' Q8 prompt length 10 (target: 12-20)
  - FIX: Adjust prompt length to 12-20 words.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення правильно' item 1 has 6 words (target: 12-16)
  - FIX: Adjust sentence length to 12-16 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення правильно' item 2 has 6 words (target: 12-16)
  - FIX: Adjust sentence length to 12-16 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення правильно' item 3 has 5 words (target: 12-16)
  - FIX: Adjust sentence length to 12-16 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення правильно' item 4 has 5 words (target: 12-16)
  - FIX: Adjust sentence length to 12-16 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення правильно' item 5 has 4 words (target: 12-16)
  - FIX: Adjust sentence length to 12-16 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення правильно' item 6 has 5 words (target: 12-16)
  - FIX: Adjust sentence length to 12-16 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення правильно' item 7 has 4 words (target: 12-16)
  - FIX: Adjust sentence length to 12-16 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення правильно' item 8 has 5 words (target: 12-16)
  - FIX: Adjust sentence length to 12-16 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення правильно' item 9 has 4 words (target: 12-16)
  - FIX: Adjust sentence length to 12-16 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення правильно' item 10 has 5 words (target: 12-16)
  - FIX: Adjust sentence length to 12-16 words to match B1 complexity.
- **[SECTION_ORDER]** '## Лексика' should come after 'summary' section
  - FIX: Reorder sections to: Summary → Activities → Self-Assessment → External → Vocabulary
- **[SECTION_ORDER]** Content section '## Діалоги' appears after end section '## Лексика'
  - FIX: Reorder sections to: Summary → Activities → Self-Assessment → External → Vocabulary
- **[YAML_SCHEMA_VIOLATION]** Schema error in 68-synonymy-thinking-verbs.yaml: [складіть-речення-правильно] unjumble: 'items.9' - Additional properties are not allowed ('scrambled' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 68-synonymy-thinking-verbs.yaml: [знайдіть-дієслова-мислення] mark-the-words: 'correct_words' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## TEMPLATE COMPLIANCE
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Presentation|Grammar|Focus|Презентація|Граматика|Теорія|Пояснення' per template 'b1-grammar-module-template'
  - FIX: Add '## Presentation' section as specified in docs/l2-uk-en/templates/b1-grammar-module-template.md
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Practice|Exercises|Activity|Практика|Вправи' per template 'b1-grammar-module-template'
  - FIX: Add '## Practice' section as specified in docs/l2-uk-en/templates/b1-grammar-module-template.md
- ❌ **[EMPTY_REQUIRED_SECTION]** Required section '## Потрібно більше практики?' is empty
  - FIX: Populate the section with meaningful content or generate it if it's a mandatory placeholder.

## Recommendation
**📝 UPDATE** (severity 60/100)

- Revision recommended (severity 60/100)
- 25 violations (severe - consider revision)
- Activity density below minimum

## Gates
- **Words:** ✅ 1655/1500
- **Activities:** ✅ 12/12
- **Density:** ❌ 1 < 14
- **Unique_types:** ✅ 10/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 12/5
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 17 < 25 (soft target)
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 22 violations
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 98.6% (target 85-100% (B1.7-8 Ukraine))
- **Richness:** ✅ 99% (grammar)
- **Grammar:** ⏳ Pending validation

## Richness Details
**Score:** 99% (minimum: 95%)
**Module Type:** grammar

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| examples | 30 | 24 | 100% | 20% | 20.0% |
| engagement | 12 | 5 | 100% | 15% | 15.0% |
| dialogues | 12 | 4 | 100% | 15% | 15.0% |
| variety | 0.96 | - | 96% | 10% | 9.6% |
| cultural | 3 | 3 | 100% | 10% | 10.0% |
| realworld | 6 | 3 | 100% | 10% | 10.0% |
| visual | 9 | 3 | 100% | 5% | 5.0% |
| paragraph_var | 1.00 | - | 100% | 5% | 5.0% |
| questions | 29 | 5 | 100% | 5% | 5.0% |
| proverbs | 5 | 1 | 100% | 5% | 5.0% |
| **TOTAL** | | | | | **99.6%** |

## Low Density Activities
| Activity | Type | Items | Required | Fix |
|----------|------|-------|----------|-----|
| Вибір правильного дієслова | cloze | 12 | 14 | Add 2 more items |


## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 55 | Included in Core |
| **Вступ** | ⚪️ | 97 | Skipped |
| **Лексика** | ⚪️ | 401 | Skipped |
| **Використання** | ⚪️ | 372 | Skipped |
| **Читання** | ✅ | 307 | Included in Core |
| **Діалоги** | ✅ | 246 | Included in Core |
| **Підсумок** | ✅ | 177 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 0 | Skipped |