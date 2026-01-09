# Audit Report: 74-regions-south.md
**Phase:** B1.7 | **Level:** B1 | **Pedagogy:** PPP | **Target:** 1500
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення про Південну Україну' item 1 has 5 words (target: 10-14)
  - FIX: Adjust sentence length to 10-14 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення про Південну Україну' item 2 has 7 words (target: 10-14)
  - FIX: Adjust sentence length to 10-14 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення про Південну Україну' item 3 has 4 words (target: 10-14)
  - FIX: Adjust sentence length to 10-14 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення про Південну Україну' item 4 has 4 words (target: 10-14)
  - FIX: Adjust sentence length to 10-14 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення про Південну Україну' item 5 has 5 words (target: 10-14)
  - FIX: Adjust sentence length to 10-14 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення про Південну Україну' item 6 has 6 words (target: 10-14)
  - FIX: Adjust sentence length to 10-14 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення про Південну Україну' item 7 has 6 words (target: 10-14)
  - FIX: Adjust sentence length to 10-14 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення про Південну Україну' item 8 has 5 words (target: 10-14)
  - FIX: Adjust sentence length to 10-14 words to match B1 complexity.
- **[YAML_SCHEMA_VIOLATION]** Schema error in 74-regions-south.yaml: [складіть-речення-про-південну-україну] unjumble: 'items.7' - Additional properties are not allowed ('scrambled' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 74-regions-south.yaml: [знайдіть-географічні-та-культурні-терміни] mark-the-words: 'correct_words' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## TEMPLATE COMPLIANCE
- ❌ **[EMPTY_REQUIRED_SECTION]** Required section '## Презентація' is empty
  - FIX: Populate the section with meaningful content or generate it if it's a mandatory placeholder.
- ❌ **[EMPTY_REQUIRED_SECTION]** Required section '## Потрібно більше практики?' is empty
  - FIX: Populate the section with meaningful content or generate it if it's a mandatory placeholder.

## Recommendation
**📝 UPDATE** (severity 60/100)

- Revision recommended (severity 60/100)
- 12 violations (severe - consider revision)
- Activity density below minimum

## Gates
- **Words:** ✅ 1599/1500
- **Activities:** ✅ 12/12
- **Density:** ❌ 1 < 14
- **Unique_types:** ✅ 10/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 8/5
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 56/25
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 10 violations
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 99.9% (target 85-100% (B1.7-8 Ukraine))
- **Richness:** ✅ 96% (cultural)
- **Grammar:** ⏳ Pending validation

## Richness Details
**Score:** 96% (minimum: 95%)
**Module Type:** cultural

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| cultural | 10 | 5 | 100% | 33% | 33.3% |
| engagement | 8 | 6 | 100% | 20% | 20.0% |
| visual | 4 | 4 | 100% | 13% | 13.3% |
| variety | 0.98 | - | 98% | 7% | 6.5% |
| paragraph_var | 0.56 | - | 56% | 7% | 3.7% |
| examples | 19 | - | 100% | 7% | 6.7% |
| realworld | 2 | - | 100% | 7% | 6.7% |
| questions | 25 | 4 | 100% | 7% | 6.7% |
| **TOTAL** | | | | | **96.9%** |

## Low Density Activities
| Activity | Type | Items | Required | Fix |
|----------|------|-------|----------|-----|
| Заповніть пропуски | cloze | 12 | 14 | Add 2 more items |


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
| **Потрібно більше практики?** | ⚪️ | 0 | Skipped |