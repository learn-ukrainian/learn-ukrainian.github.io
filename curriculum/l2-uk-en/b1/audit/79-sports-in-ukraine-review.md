# Audit Report: 79-sports-in-ukraine.md
**Phase:** B1.7 | **Level:** B1 | **Pedagogy:** PPP | **Target:** 1500
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[YAML_SCHEMA_VIOLATION]** Schema error in 79-sports-in-ukraine.yaml: [index-6] unjumble: 'items.7' - Additional properties are not allowed ('scrambled' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 79-sports-in-ukraine.yaml: [index-8] mark-the-words: 'correct_words' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## TEMPLATE COMPLIANCE
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Пояснення|Граматика|Теорія' per template 'b1-grammar-module-template'
  - FIX: Add '## Пояснення' section as specified in docs/l2-uk-en/templates/b1-grammar-module-template.md

## Recommendation
**📝 UPDATE** (severity 5/100)

- 3 violations (minor)

## Gates
- **Words:** ✅ 1751/1500
- **Activities:** ✅ 11/8
- **Density:** ✅ All > 12
- **Unique_types:** ✅ 10/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 8/5
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 69/25
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 2 violations
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 98.9% (target 85-100% (B1.7-8 Ukraine))
- **Richness:** ✅ 99% (cultural)
- **Grammar:** ⏳ Pending validation

## Richness Details
**Score:** 99% (minimum: 95%)
**Module Type:** cultural

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| cultural | 7 | 5 | 100% | 33% | 33.3% |
| engagement | 8 | 6 | 100% | 20% | 20.0% |
| visual | 7 | 4 | 100% | 13% | 13.3% |
| variety | 0.98 | - | 98% | 7% | 6.5% |
| paragraph_var | 1.00 | - | 100% | 7% | 6.7% |
| examples | 38 | - | 100% | 7% | 6.7% |
| realworld | 1 | - | 100% | 7% | 6.7% |
| questions | 21 | 4 | 100% | 7% | 6.7% |
| **TOTAL** | | | | | **99.9%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 110 | Included in Core |
| **Презентація** | ⚪️ | 843 | Skipped |
| **Практика** | ⚪️ | 123 | Skipped |
| **Продукція** | ⚪️ | 354 | Skipped |
| **Підсумок** | ✅ | 211 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 110 | Skipped |