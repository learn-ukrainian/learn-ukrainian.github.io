# Audit Report: 14-aspect-integration-practice.md
**Phase:** B1.1 | **Level:** B1 | **Pedagogy:** TTT | **Target:** 1500
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[YAML_SCHEMA_VIOLATION]** Schema error in 14-aspect-integration-practice.yaml: [визначення-виду-в-тексті] mark-the-words: 'correct_words' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## TEMPLATE COMPLIANCE
- ❌ **[DUPLICATE_SYNONYMOUS_HEADERS]** Multiple aliases for 'Practice|Exercises|Activity|Практика|Вправи' found: Інтеграція виду: практика, Практика
  - FIX: Keep only one version of the header (preferably the primary one or the one with more content).
- ❌ **[EMPTY_REQUIRED_SECTION]** Required section '## Потрібно більше практики?' is empty
  - FIX: Populate the section with meaningful content or generate it if it's a mandatory placeholder.

## Recommendation
**📝 UPDATE** (severity 30/100)

- 3 violations (minor)
- Activity count below minimum
- Activity density below minimum

## Gates
- **Words:** ✅ 1690/1500
- **Activities:** ❌ 11/12
- **Density:** ❌ 1 < 14
- **Unique_types:** ✅ 10/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 6/5
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 28/25
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 1 violations
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 100.0% (target 85-100% (B1.2 Motion))
- **Richness:** ✅ 96% (grammar)
- **Grammar:** ⏳ Pending validation

## Richness Details
**Score:** 96% (minimum: 95%)
**Module Type:** grammar

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| examples | 49 | 24 | 100% | 20% | 20.0% |
| engagement | 6 | 5 | 100% | 15% | 15.0% |
| dialogues | 14 | 4 | 100% | 15% | 15.0% |
| variety | 0.94 | - | 94% | 10% | 9.4% |
| cultural | 2 | 3 | 67% | 10% | 6.7% |
| realworld | 8 | 3 | 100% | 10% | 10.0% |
| visual | 3 | 3 | 100% | 5% | 5.0% |
| paragraph_var | 1.00 | - | 100% | 5% | 5.0% |
| questions | 34 | 5 | 100% | 5% | 5.0% |
| proverbs | 1 | 1 | 100% | 5% | 5.0% |
| **TOTAL** | | | | | **96.1%** |

## Low Density Activities
| Activity | Type | Items | Required | Fix |
|----------|------|-------|----------|-----|
| Вибір виду в оповіданні | cloze | 8 | 14 | Add 6 more items |


## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 74 | Included in Core |
| **Тест** | ⚪️ | 134 | Skipped |
| **Пояснення** | ⚪️ | 795 | Skipped |
| **Практика** | ⚪️ | 165 | Skipped |
| **Діалоги** | ✅ | 292 | Included in Core |
| **Підсумок** | ✅ | 230 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 0 | Skipped |