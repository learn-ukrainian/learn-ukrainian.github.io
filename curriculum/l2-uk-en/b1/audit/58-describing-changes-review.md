# Audit Report: 58-describing-changes.md
**Phase:** B1.5 | **Level:** B1 | **Pedagogy:** PPP | **Target:** 1500
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[COMPLEXITY_WORD_COUNT]** quiz 'Розуміння лексики змін' Q3 prompt length 7 (target: 8-18)
  - FIX: Adjust prompt length to 8-18 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Розуміння лексики змін' Q4 prompt length 6 (target: 8-18)
  - FIX: Adjust prompt length to 8-18 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Розуміння лексики змін' Q5 prompt length 7 (target: 8-18)
  - FIX: Adjust prompt length to 8-18 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Розуміння лексики змін' Q8 prompt length 7 (target: 8-18)
  - FIX: Adjust prompt length to 8-18 words.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення про зміни' item 2 has 5 words (target: 8-14)
  - FIX: Adjust sentence length to 8-14 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення про зміни' item 4 has 5 words (target: 8-14)
  - FIX: Adjust sentence length to 8-14 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення про зміни' item 5 has 6 words (target: 8-14)
  - FIX: Adjust sentence length to 8-14 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення про зміни' item 8 has 5 words (target: 8-14)
  - FIX: Adjust sentence length to 8-14 words to match B1 complexity.
- **[SECTION_ORDER]** '## Лексика' should come after 'summary' section
  - FIX: Reorder sections to: Summary → Activities → Self-Assessment → External → Vocabulary
- **[SECTION_ORDER]** Content section '## Діалоги' appears after end section '## Лексика'
  - FIX: Reorder sections to: Summary → Activities → Self-Assessment → External → Vocabulary
- **[YAML_SCHEMA_VIOLATION]** Schema error in 58-describing-changes.yaml: [index-8] unjumble: 'items.7' - Additional properties are not allowed ('scrambled' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 58-describing-changes.yaml: [index-11] mark-the-words: 'correct_words' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## TEMPLATE COMPLIANCE
- ❌ **[DUPLICATE_SYNONYMOUS_HEADERS]** Multiple aliases for 'Вступ|Контекст|Розминка|Тест' found: Контексти використання, Вступ
  - FIX: Keep only one version of the header (preferably the primary one or the one with more content).
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Пояснення|Граматика|Теорія' per template 'b1-grammar-module-template'
  - FIX: Add '## Пояснення' section as specified in docs/l2-uk-en/templates/b1-grammar-module-template.md
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Практика|Вправи' per template 'b1-grammar-module-template'
  - FIX: Add '## Практика' section as specified in docs/l2-uk-en/templates/b1-grammar-module-template.md

## Recommendation
**📝 UPDATE** (severity 50/100)

- Revision recommended (severity 50/100)
- 15 violations (severe - consider revision)

## Gates
- **Words:** ✅ 1689/1500
- **Activities:** ✅ 12/8
- **Density:** ✅ All > 12
- **Unique_types:** ✅ 10/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 13/5
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 34 < 35 (soft target)
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 12 violations
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 99.1% (target 85-100% (B1.5-6 Vocab))
- **Richness:** ✅ 96% (vocabulary)
- **Grammar:** ⏳ Pending validation

## Richness Details
**Score:** 96% (minimum: 95%)
**Module Type:** vocabulary

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| collocations | 30 | 20 | 100% | 25% | 25.0% |
| usage_examples | 21 | 15 | 100% | 20% | 20.0% |
| engagement | 13 | 4 | 100% | 15% | 15.0% |
| cultural | 2 | 3 | 67% | 10% | 6.7% |
| visual | 11 | 3 | 100% | 10% | 10.0% |
| register_notes | 9 | 5 | 100% | 10% | 10.0% |
| variety | 0.96 | - | 96% | 5% | 4.8% |
| paragraph_var | 1.00 | - | 100% | 5% | 5.0% |
| **TOTAL** | | | | | **96.5%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 49 | Included in Core |
| **Вступ** | ⚪️ | 95 | Skipped |
| **Лексика** | ⚪️ | 378 | Skipped |
| **Використання** | ⚪️ | 346 | Skipped |
| **Читання** | ✅ | 287 | Included in Core |
| **Діалоги** | ✅ | 244 | Included in Core |
| **Підсумок** | ✅ | 180 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 110 | Skipped |