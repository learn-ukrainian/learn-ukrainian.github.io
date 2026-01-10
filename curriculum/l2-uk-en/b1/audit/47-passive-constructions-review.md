# Audit Report: 47-passive-constructions.md
**Phase:** B1.4 | **Level:** B1 | **Pedagogy:** TTT | **Target:** 1500
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[YAML_SCHEMA_VIOLATION]** Schema error in 47-passive-constructions.yaml: [index-5] unjumble: 'items.5' - Additional properties are not allowed ('scrambled' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 47-passive-constructions.yaml: [index-8] mark-the-words: 'correct_words' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 47-passive-constructions.yaml: [index-10] translate: 'items.5' - 'source' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## Recommendation
**📝 UPDATE** (severity 30/100)

- 3 violations (minor)
- Activity count below minimum
- Activity density below minimum

## Gates
- **Words:** ✅ 1673/1500
- **Activities:** ❌ 0/8
- **Density:** ❌ 0 < 12
- **Unique_types:** ❌ 0/4 types
- **Priority:** ❌ No priority types
- **Engagement:** ✅ 14/5
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 30/25
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 3 violations
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 99.1% (target 85-100% (B1.5-6 Vocab))
- **Richness:** ✅ 95% (grammar)
- **Grammar:** ⏳ Pending validation

## Richness Details
**Score:** 95% (minimum: 95%)
**Module Type:** grammar

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| examples | 69 | 24 | 100% | 20% | 20.0% |
| engagement | 11 | 5 | 100% | 15% | 15.0% |
| dialogues | 15 | 4 | 100% | 15% | 15.0% |
| variety | 0.91 | - | 91% | 10% | 9.1% |
| cultural | 2 | 3 | 67% | 10% | 6.7% |
| realworld | 14 | 3 | 100% | 10% | 10.0% |
| visual | 11 | 3 | 100% | 5% | 5.0% |
| paragraph_var | 1.00 | - | 100% | 5% | 5.0% |
| questions | 34 | 5 | 100% | 5% | 5.0% |
| proverbs | 10 | 1 | 100% | 5% | 5.0% |
| **TOTAL** | | | | | **95.8%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 85 | Included in Core |
| **Тест** | ⚪️ | 147 | Skipped |
| **Пояснення** | ⚪️ | 430 | Skipped |
| **Практика** | ⚪️ | 470 | Skipped |
| **Діалоги** | ✅ | 269 | Included in Core |
| **Підсумок** | ✅ | 162 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 110 | Skipped |