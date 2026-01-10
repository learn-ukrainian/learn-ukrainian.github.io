# Audit Report: 78-technology-and-startups.md
**Phase:** B1.7 | **Level:** B1 | **Pedagogy:** PPP | **Target:** 1500
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[YAML_SCHEMA_VIOLATION]** Schema error in 78-technology-and-startups.yaml: [index-6] unjumble: 'items.7' - Additional properties are not allowed ('scrambled' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 78-technology-and-startups.yaml: [index-8] mark-the-words: 'correct_words' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[STATE_STANDARD_LOW_IMMERSION]** Module 78 has 96.1% immersion (target: 98.0%+)
  - FIX: Add more Ukrainian content to reach 98%+ immersion for full immersion modules

## TEMPLATE COMPLIANCE
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Пояснення|Граматика|Теорія' per template 'b1-grammar-module-template'
  - FIX: Add '## Пояснення' section as specified in docs/l2-uk-en/templates/b1-grammar-module-template.md

## Recommendation
**📝 UPDATE** (severity 15/100)

- 4 violations (moderate)

## Gates
- **Words:** ✅ 1621/1500
- **Activities:** ✅ 11/8
- **Density:** ✅ All > 12
- **Unique_types:** ✅ 10/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 7/5
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 23 < 25 (soft target)
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 2 violations
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 96.1% (target 85-100% (B1.7-8 Ukraine))
- **Richness:** ✅ 98% (cultural)
- **Grammar:** ⏳ Pending validation

## Richness Details
**Score:** 98% (minimum: 95%)
**Module Type:** cultural

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| cultural | 8 | 5 | 100% | 33% | 33.3% |
| engagement | 7 | 6 | 100% | 20% | 20.0% |
| visual | 4 | 4 | 100% | 13% | 13.3% |
| variety | 0.96 | - | 96% | 7% | 6.4% |
| paragraph_var | 0.76 | - | 76% | 7% | 5.1% |
| examples | 17 | - | 100% | 7% | 6.7% |
| realworld | 3 | - | 100% | 7% | 6.7% |
| questions | 25 | 4 | 100% | 7% | 6.7% |
| **TOTAL** | | | | | **98.1%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 113 | Included in Core |
| **Презентація** | ⚪️ | 740 | Skipped |
| **Практика** | ⚪️ | 122 | Skipped |
| **Продукція** | ⚪️ | 354 | Skipped |
| **Підсумок** | ✅ | 182 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 110 | Skipped |