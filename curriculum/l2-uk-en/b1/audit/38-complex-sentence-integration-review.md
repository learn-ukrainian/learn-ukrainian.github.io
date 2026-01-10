# Audit Report: 38-complex-sentence-integration.md
**Phase:** B1.3b | **Level:** B1 | **Pedagogy:** TTT | **Target:** 1500
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[COMPLEXITY]** mark-the-words 'Позначте підрядні сполучники' has 0 items (minimum: 6)
  - FIX: Add more items. B1 mark-the-words requires at least 6 items.
- **[MISSING_FIELD]** mark-the-words 'Позначте підрядні сполучники' is missing 'correct_words' array
  - FIX: Add 'correct_words' array with correct words
- **[YAML_SCHEMA_VIOLATION]** Schema error in 38-complex-sentence-integration.yaml: [index-8] mark-the-words: 'correct_words' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## TEMPLATE COMPLIANCE
- ❌ **[DUPLICATE_SYNONYMOUS_HEADERS]** Multiple aliases for 'Пояснення|Граматика|Теорія' found: Пояснення, Діалог 1: Пояснення ситуації
  - FIX: Keep only one version of the header (preferably the primary one or the one with more content).

## Recommendation
**📝 UPDATE** (severity 25/100)

- 4 violations (moderate)
- Activity density below minimum

## Gates
- **Words:** ✅ 1577/1500
- **Activities:** ✅ 11/8
- **Density:** ❌ 1 < 12
- **Unique_types:** ✅ 11/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 8/5
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 9 < 25 (soft target)
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 3 violations
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 99.0% (target 85-100% (B1.3-4 Complex))
- **Richness:** ✅ 96% (grammar)
- **Grammar:** ⏳ Pending validation

## Richness Details
**Score:** 96% (minimum: 95%)
**Module Type:** grammar

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| examples | 40 | 24 | 100% | 20% | 20.0% |
| engagement | 7 | 5 | 100% | 15% | 15.0% |
| dialogues | 13 | 4 | 100% | 15% | 15.0% |
| variety | 0.99 | - | 99% | 10% | 9.9% |
| cultural | 4 | 3 | 100% | 10% | 10.0% |
| realworld | 2 | 3 | 67% | 10% | 6.7% |
| visual | 3 | 3 | 100% | 5% | 5.0% |
| paragraph_var | 0.91 | - | 91% | 5% | 4.6% |
| questions | 28 | 5 | 100% | 5% | 5.0% |
| proverbs | 10 | 1 | 100% | 5% | 5.0% |
| **TOTAL** | | | | | **96.2%** |

## Low Density Activities
| Activity | Type | Items | Required | Fix |
|----------|------|-------|----------|-----|
| Позначте підрядні сполучники | mark-the-words | 0 | 6 | Add 6 more items |


## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 58 | Included in Core |
| **Тест** | ⚪️ | 188 | Skipped |
| **Пояснення** | ⚪️ | 641 | Skipped |
| **Практика** | ⚪️ | 183 | Skipped |
| **Діалоги** | ✅ | 240 | Included in Core |
| **Підсумок** | ✅ | 157 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 110 | Skipped |