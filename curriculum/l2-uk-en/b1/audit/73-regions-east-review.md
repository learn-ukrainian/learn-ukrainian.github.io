# Audit Report: 73-regions-east.md
**Phase:** B1.7 | **Level:** B1 | **Pedagogy:** PPP | **Target:** 1500
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення' item 4 has 6 words (target: 8-14)
  - FIX: Adjust sentence length to 8-14 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення' item 6 has 6 words (target: 8-14)
  - FIX: Adjust sentence length to 8-14 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення' item 7 has 6 words (target: 8-14)
  - FIX: Adjust sentence length to 8-14 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення' item 8 has 6 words (target: 8-14)
  - FIX: Adjust sentence length to 8-14 words to match B1 complexity.
- **[YAML_SCHEMA_VIOLATION]** Schema error in 73-regions-east.yaml: [index-6] unjumble: 'items.7' - Additional properties are not allowed ('scrambled' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 73-regions-east.yaml: [index-9] mark-the-words: 'correct_words' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## TEMPLATE COMPLIANCE
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Пояснення|Граматика|Теорія' per template 'b1-grammar-module-template'
  - FIX: Add '## Пояснення' section as specified in docs/l2-uk-en/templates/b1-grammar-module-template.md

## Recommendation
**📝 UPDATE** (severity 30/100)

- 7 violations (significant)

## Gates
- **Words:** ✅ 1883/1500
- **Activities:** ✅ 12/8
- **Density:** ✅ All > 12
- **Unique_types:** ✅ 10/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 12/5
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 47/25
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 6 violations
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 98.9% (target 85-100% (B1.7-8 Ukraine))
- **Richness:** ✅ 98% (cultural)
- **Grammar:** ⏳ Pending validation

## Richness Details
**Score:** 98% (minimum: 95%)
**Module Type:** cultural

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| cultural | 8 | 5 | 100% | 33% | 33.3% |
| engagement | 14 | 6 | 100% | 20% | 20.0% |
| visual | 4 | 4 | 100% | 13% | 13.3% |
| variety | 0.97 | - | 97% | 7% | 6.5% |
| paragraph_var | 0.78 | - | 78% | 7% | 5.2% |
| examples | 22 | - | 100% | 7% | 6.7% |
| realworld | 3 | - | 100% | 7% | 6.7% |
| questions | 37 | 4 | 100% | 7% | 6.7% |
| **TOTAL** | | | | | **98.3%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 67 | Included in Core |
| **Вступ** | ⚪️ | 127 | Skipped |
| **Презентація** | ⚪️ | 857 | Skipped |
| **Практика** | ⚪️ | 188 | Skipped |
| **Продукція** | ⚪️ | 362 | Skipped |
| **Підсумок** | ✅ | 0 | Included in Core |
| **Що ви дізналися** | ⚪️ | 172 | Skipped |
| **Потрібно більше практики?** | ⚪️ | 110 | Skipped |