# Audit Report: 74-regions-south.md
**Phase:** B1.7 | **Level:** B1 | **Pedagogy:** PPP | **Target:** 1500
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення про Південну Україну' item 1 has 5 words (target: 8-14)
  - FIX: Adjust sentence length to 8-14 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення про Південну Україну' item 3 has 4 words (target: 8-14)
  - FIX: Adjust sentence length to 8-14 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення про Південну Україну' item 4 has 4 words (target: 8-14)
  - FIX: Adjust sentence length to 8-14 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення про Південну Україну' item 5 has 5 words (target: 8-14)
  - FIX: Adjust sentence length to 8-14 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення про Південну Україну' item 6 has 6 words (target: 8-14)
  - FIX: Adjust sentence length to 8-14 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення про Південну Україну' item 7 has 6 words (target: 8-14)
  - FIX: Adjust sentence length to 8-14 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення про Південну Україну' item 8 has 5 words (target: 8-14)
  - FIX: Adjust sentence length to 8-14 words to match B1 complexity.
- **[YAML_SCHEMA_VIOLATION]** Schema error in 74-regions-south.yaml: [index-7] unjumble: 'items.7' - Additional properties are not allowed ('scrambled' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 74-regions-south.yaml: [index-11] mark-the-words: 'correct_words' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## TEMPLATE COMPLIANCE
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Пояснення|Граматика|Теорія' per template 'b1-grammar-module-template'
  - FIX: Add '## Пояснення' section as specified in docs/l2-uk-en/templates/b1-grammar-module-template.md

## Recommendation
**📝 UPDATE** (severity 30/100)

- 10 violations (significant)

## Gates
- **Words:** ✅ 1709/1500
- **Activities:** ✅ 12/8
- **Density:** ✅ All > 12
- **Unique_types:** ✅ 10/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 9/5
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 56/25
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 9 violations
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 99.1% (target 85-100% (B1.7-8 Ukraine))
- **Richness:** ✅ 96% (cultural)
- **Grammar:** ⏳ Pending validation

## Richness Details
**Score:** 96% (minimum: 95%)
**Module Type:** cultural

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| cultural | 10 | 5 | 100% | 33% | 33.3% |
| engagement | 9 | 6 | 100% | 20% | 20.0% |
| visual | 4 | 4 | 100% | 13% | 13.3% |
| variety | 0.98 | - | 98% | 7% | 6.5% |
| paragraph_var | 0.55 | - | 55% | 7% | 3.7% |
| examples | 20 | - | 100% | 7% | 6.7% |
| realworld | 2 | - | 100% | 7% | 6.7% |
| questions | 25 | 4 | 100% | 7% | 6.7% |
| **TOTAL** | | | | | **96.9%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 184 | Included in Core |
| **Презентація** | ⚪️ | 0 | Skipped |
| **Південна Україна: географія та клімат** | ⚪️ | 208 | Skipped |
| **Одеса: перлина біля моря** | ⚪️ | 199 | Skipped |
| **Херсон, Миколаїв та узбережжя** | ⚪️ | 197 | Skipped |
| **Багатонаціональний південь** | ⚪️ | 215 | Skipped |
| **Практика** | ⚪️ | 145 | Skipped |
| **Продукція** | ⚪️ | 0 | Skipped |
| **Діалог 1: Планування відпустки на півдні** | ✅ | 76 | Included in Core |
| **Діалог 2: Розмова про одеський гумор** | ✅ | 68 | Included in Core |
| **Діалог 3: Обговорення сільського господарства** | ✅ | 67 | Included in Core |
| **Діалог 4: Туристи в Миколаєві** | ✅ | 63 | Included in Core |
| **Підсумок** | ✅ | 177 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 110 | Skipped |