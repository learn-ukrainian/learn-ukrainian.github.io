# Audit Report: 87-novyny-yak-chytaty.md
**Phase:** B1.8 | **Level:** B1 | **Pedagogy:** PPP | **Target:** 1500
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення про читання новин' item 4 has 7 words (target: 9-16)
  - FIX: Adjust sentence length to 9-16 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення про читання новин' item 5 has 7 words (target: 9-16)
  - FIX: Adjust sentence length to 9-16 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення про читання новин' item 6 has 7 words (target: 9-16)
  - FIX: Adjust sentence length to 9-16 words to match B1 complexity.
- **[YAML_SCHEMA_VIOLATION]** Schema error in 87-novyny-yak-chytaty.yaml: [index-7] mark-the-words: 'correct_words' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 87-novyny-yak-chytaty.yaml: [index-8] unjumble: 'items.7' - Additional properties are not allowed ('scrambled' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## TEMPLATE COMPLIANCE
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Пояснення|Граматика|Теорія' per template 'b1-grammar-module-template'
  - FIX: Add '## Пояснення' section as specified in docs/l2-uk-en/templates/b1-grammar-module-template.md

## Recommendation
**📝 UPDATE** (severity 15/100)

- 6 violations (moderate)

## Gates
- **Words:** ✅ 1922/1500
- **Activities:** ✅ 11/10
- **Density:** ✅ All > 12
- **Unique_types:** ✅ 10/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 8/4
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 21/15
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 5 violations
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 99.0% (target 85-100% (B1.7-8 Ukraine))
- **Richness:** ✅ 97% (grammar)
- **Grammar:** ⏳ Pending validation

## Richness Details
**Score:** 97% (minimum: 95%)
**Module Type:** grammar

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| examples | 60 | 24 | 100% | 20% | 20.0% |
| engagement | 8 | 5 | 100% | 15% | 15.0% |
| dialogues | 8 | 4 | 100% | 15% | 15.0% |
| variety | 0.96 | - | 96% | 10% | 9.6% |
| cultural | 3 | 3 | 100% | 10% | 10.0% |
| realworld | 4 | 3 | 100% | 10% | 10.0% |
| visual | 5 | 3 | 100% | 5% | 5.0% |
| paragraph_var | 0.58 | - | 58% | 5% | 2.9% |
| questions | 49 | 5 | 100% | 5% | 5.0% |
| proverbs | 10 | 1 | 100% | 5% | 5.0% |
| **TOTAL** | | | | | **97.5%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 146 | Included in Core |
| **Презентація** | ⚪️ | 634 | Skipped |
| **Практика** | ⚪️ | 550 | Skipped |
| **Продукція** | ⚪️ | 372 | Skipped |
| **Підсумок** | ✅ | 110 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 110 | Skipped |