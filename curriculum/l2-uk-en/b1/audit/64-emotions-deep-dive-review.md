# Audit Report: 64-emotions-deep-dive.md
**Phase:** B1.6 | **Level:** B1 | **Pedagogy:** PPP | **Target:** 1500
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[COMPLEXITY_WORD_COUNT]** quiz 'Розуміння емоційної лексики' Q1 prompt length 9 (target: 10-18)
  - FIX: Adjust prompt length to 10-18 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Розуміння емоційної лексики' Q4 prompt length 9 (target: 10-18)
  - FIX: Adjust prompt length to 10-18 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Розуміння емоційної лексики' Q5 prompt length 9 (target: 10-18)
  - FIX: Adjust prompt length to 10-18 words.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення про емоції' item 1 has 6 words (target: 10-14)
  - FIX: Adjust sentence length to 10-14 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення про емоції' item 2 has 6 words (target: 10-14)
  - FIX: Adjust sentence length to 10-14 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення про емоції' item 3 has 5 words (target: 10-14)
  - FIX: Adjust sentence length to 10-14 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення про емоції' item 4 has 6 words (target: 10-14)
  - FIX: Adjust sentence length to 10-14 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення про емоції' item 5 has 4 words (target: 10-14)
  - FIX: Adjust sentence length to 10-14 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення про емоції' item 6 has 6 words (target: 10-14)
  - FIX: Adjust sentence length to 10-14 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення про емоції' item 7 has 7 words (target: 10-14)
  - FIX: Adjust sentence length to 10-14 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення про емоції' item 8 has 7 words (target: 10-14)
  - FIX: Adjust sentence length to 10-14 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення про емоції' item 9 has 6 words (target: 10-14)
  - FIX: Adjust sentence length to 10-14 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення про емоції' item 10 has 5 words (target: 10-14)
  - FIX: Adjust sentence length to 10-14 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення про емоції' item 11 has 7 words (target: 10-14)
  - FIX: Adjust sentence length to 10-14 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення про емоції' item 12 has 6 words (target: 10-14)
  - FIX: Adjust sentence length to 10-14 words to match B1 complexity.
- **[SECTION_ORDER]** '## Лексика' should come after 'summary' section
  - FIX: Reorder sections to: Summary → Activities → Self-Assessment → External → Vocabulary
- **[SECTION_ORDER]** Content section '## Діалоги' appears after end section '## Лексика'
  - FIX: Reorder sections to: Summary → Activities → Self-Assessment → External → Vocabulary
- **[YAML_SCHEMA_VIOLATION]** Schema error in 64-emotions-deep-dive.yaml: [складіть-речення-про-емоції] unjumble: 'items.11' - Additional properties are not allowed ('scrambled' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 64-emotions-deep-dive.yaml: [знайдіть-слова,-що-описують-емоції] mark-the-words: 'correct_words' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## TEMPLATE COMPLIANCE
- ❌ **[DUPLICATE_SYNONYMOUS_HEADERS]** Multiple aliases for 'Warm-up|Introduction|Objectives|Контекст|Вступ|Розминка|Тест' found: Українські культурні контексти, Вступ
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
- 23 violations (severe - consider revision)
- Activity density below minimum

## Gates
- **Words:** ✅ 1583/1500
- **Activities:** ✅ 13/12
- **Density:** ❌ 1 < 14
- **Unique_types:** ✅ 11/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 12/5
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 35/35
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 19 violations
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 99.9% (target 85-100% (B1.5-6 Vocab))
- **Richness:** ✅ 99% (vocabulary)
- **Grammar:** ⏳ Pending validation

## Richness Details
**Score:** 99% (minimum: 95%)
**Module Type:** vocabulary

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| collocations | 29 | 20 | 100% | 25% | 25.0% |
| usage_examples | 18 | 15 | 100% | 20% | 20.0% |
| engagement | 12 | 4 | 100% | 15% | 15.0% |
| cultural | 4 | 3 | 100% | 10% | 10.0% |
| visual | 5 | 3 | 100% | 10% | 10.0% |
| register_notes | 13 | 5 | 100% | 10% | 10.0% |
| variety | 0.99 | - | 99% | 5% | 5.0% |
| paragraph_var | 1.00 | - | 100% | 5% | 5.0% |
| **TOTAL** | | | | | **100.0%** |

## Low Density Activities
| Activity | Type | Items | Required | Fix |
|----------|------|-------|----------|-----|
| Вибір правильного слова для контексту | cloze | 12 | 14 | Add 2 more items |


## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 55 | Included in Core |
| **Вступ** | ⚪️ | 92 | Skipped |
| **Лексика** | ⚪️ | 382 | Skipped |
| **Використання** | ⚪️ | 275 | Skipped |
| **Читання** | ✅ | 288 | Included in Core |
| **Діалоги** | ✅ | 310 | Included in Core |
| **Підсумок** | ✅ | 181 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 0 | Skipped |