# Audit Report: 24-motion-practice-integration.md
**Phase:** B1.2 | **Level:** B1 | **Pedagogy:** TTT | **Target:** 1500
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[MALFORMED_ERROR_CORRECTION]** Error-correction activity 'Типові помилки' uses placeholder syntax instead of real errors
  - FIX: Convert to proper error-correction format with real error words in sentences, or change to fill-in activity. Found 5/6 items with placeholders/missing errors.
- **[YAML_SCHEMA_VIOLATION]** Schema error in 24-motion-practice-integration.yaml: [деталі-навігації] quiz: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 24-motion-practice-integration.yaml: [префікс-та-прийменник] match-up: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 24-motion-practice-integration.yaml: [культурні-нюанси-та-логіка] true-false: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 24-motion-practice-integration.yaml: [життя-в-русі] cloze: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 24-motion-practice-integration.yaml: [складіть-маршрут] unjumble: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 24-motion-practice-integration.yaml: [вставте-прийменник] group-sort: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 24-motion-practice-integration.yaml: [лист-із-відпустки] cloze: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 24-motion-practice-integration.yaml: [типові-помилки] error-correction: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 24-motion-practice-integration.yaml: [ідіоми-в-тексті] mark-the-words: 'correct_words' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 24-motion-practice-integration.yaml: [синоніми-руху] select: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 24-motion-practice-integration.yaml: [навігація-в-місті] translate: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[STATE_STANDARD_LOW_IMMERSION]** Module 24 has 93.9% immersion (target: 98.0%+)
  - FIX: Add more Ukrainian content to reach 98%+ immersion for full immersion modules

## TEMPLATE COMPLIANCE
- ❌ **[DUPLICATE_SYNONYMOUS_HEADERS]** Multiple aliases for 'Практика|Вправи' found: Дієслова руху: практика та інтеграція, Практика
  - FIX: Keep only one version of the header (preferably the primary one or the one with more content).

## Recommendation
**📝 UPDATE** (severity 60/100)

- Revision recommended (severity 60/100)
- 14 violations (severe - consider revision)
- Activity density below minimum

## Gates
- **Words:** ✅ 1569/1500
- **Activities:** ✅ 11/8
- **Density:** ❌ 1 < 12
- **Unique_types:** ✅ 10/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 8/5
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 46/25
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 12 violations
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 93.9% (target 85-100% (B1.3-4 Complex))
- **Richness:** ✅ 99% (grammar)
- **Grammar:** ⏳ Pending validation

## Richness Details
**Score:** 99% (minimum: 95%)
**Module Type:** grammar

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| examples | 43 | 24 | 100% | 20% | 20.0% |
| engagement | 8 | 5 | 100% | 15% | 15.0% |
| dialogues | 9 | 4 | 100% | 15% | 15.0% |
| variety | 0.96 | - | 96% | 10% | 9.6% |
| cultural | 5 | 3 | 100% | 10% | 10.0% |
| realworld | 4 | 3 | 100% | 10% | 10.0% |
| visual | 6 | 3 | 100% | 5% | 5.0% |
| paragraph_var | 1.00 | - | 100% | 5% | 5.0% |
| questions | 21 | 5 | 100% | 5% | 5.0% |
| proverbs | 1 | 1 | 100% | 5% | 5.0% |
| **TOTAL** | | | | | **99.6%** |

## Low Density Activities
| Activity | Type | Items | Required | Fix |
|----------|------|-------|----------|-----|
| Життя в русі | cloze | 9 | 12 | Add 3 more items |


## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 70 | Included in Core |
| **Тест** | ⚪️ | 127 | Skipped |
| **Пояснення** | ⚪️ | 929 | Skipped |
| **Практика** | ⚪️ | 92 | Skipped |
| **Діалоги** | ✅ | 168 | Included in Core |
| **Підсумок** | ✅ | 73 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 110 | Skipped |