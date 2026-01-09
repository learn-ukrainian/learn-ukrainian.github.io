# Audit Report: 34-checkpoint-complex-sentences-1.md
**Phase:** B1.3a | **Level:** B1 | **Pedagogy:** TTT | **Target:** 800
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[COMPLEXITY]** mark-the-words 'Позначте сполучники й відносні слова' has 0 items (minimum: 6)
  - FIX: Add more items. B1 mark-the-words requires at least 6 items.
- **[MISSING_FIELD]** mark-the-words 'Позначте сполучники й відносні слова' is missing 'correct_words' array
  - FIX: Add 'correct_words' array with correct words
- **[YAML_SCHEMA_VIOLATION]** Schema error in 34-checkpoint-complex-sentences-1.yaml: [позначте-сполучники-й-відносні-слова] mark-the-words: 'correct_words' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## Recommendation
**📝 UPDATE** (severity 15/100)

- 3 violations (minor)
- Activity density below minimum

## Gates
- **Words:** ✅ 1063/800
- **Activities:** ✅ 12/10
- **Density:** ❌ 1 < 12
- **Unique_types:** ✅ 10/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 3/3
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 7 < 10 (soft target)
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 3 violations
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 99.8% (checkpoint - no gate)
- **Richness:** ✅ 88% (checkpoint)
- **Grammar:** ⏳ Pending validation

## Richness Details
**Score:** 88% (minimum: 85%)
**Module Type:** checkpoint

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| activity_types | 10 | 8 | 100% | 25% | 25.0% |
| review_sections | 17 | 3 | 100% | 20% | 20.0% |
| variety | 0.95 | - | 95% | 15% | 14.2% |
| engagement | 2 | 3 | 67% | 10% | 6.7% |
| cultural | 4 | - | 100% | 10% | 10.0% |
| visual | 1 | 3 | 33% | 10% | 3.3% |
| paragraph_var | 0.87 | - | 87% | 10% | 8.7% |
| **TOTAL** | | | | | **88.0%** |

## Low Density Activities
| Activity | Type | Items | Required | Fix |
|----------|------|-------|----------|-----|
| Позначте сполучники й відносні слова | mark-the-words | 0 | 6 | Add 6 more items |


## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 143 | Included in Core |
| **Skill 1: Відносні речення** | ⚪️ | 144 | Skipped |
| **Skill 2: Підрядні речення мети** | ⚪️ | 109 | Skipped |
| **Skill 3: Умовні речення** | ⚪️ | 148 | Skipped |
| **Integration Challenge** | ⚪️ | 124 | Skipped |
| **Практика** | ⚪️ | 230 | Skipped |
| **Підсумок** | ✅ | 165 | Included in Core |
| **Need More Practice?** | ⚪️ | 0 | Skipped |