# Audit Report: 83-cycling-water.md
**Phase:** B1.7 | **Level:** B1 | **Pedagogy:** PPP | **Target:** 1500
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[COMPLEXITY_WORD_COUNT]** quiz 'Розуміння тексту про велоспорт' Q1 prompt length 0 (target: 8-18)
  - FIX: Adjust prompt length to 8-18 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Розуміння тексту про велоспорт' Q2 prompt length 0 (target: 8-18)
  - FIX: Adjust prompt length to 8-18 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Розуміння тексту про велоспорт' Q3 prompt length 0 (target: 8-18)
  - FIX: Adjust prompt length to 8-18 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Розуміння тексту про велоспорт' Q4 prompt length 0 (target: 8-18)
  - FIX: Adjust prompt length to 8-18 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Розуміння тексту про велоспорт' Q5 prompt length 0 (target: 8-18)
  - FIX: Adjust prompt length to 8-18 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Розуміння тексту про велоспорт' Q6 prompt length 0 (target: 8-18)
  - FIX: Adjust prompt length to 8-18 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Розуміння тексту про велоспорт' Q7 prompt length 0 (target: 8-18)
  - FIX: Adjust prompt length to 8-18 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Розуміння тексту про велоспорт' Q8 prompt length 0 (target: 8-18)
  - FIX: Adjust prompt length to 8-18 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Розуміння тексту про велоспорт' Q9 prompt length 0 (target: 8-18)
  - FIX: Adjust prompt length to 8-18 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Розуміння тексту про велоспорт' Q10 prompt length 0 (target: 8-18)
  - FIX: Adjust prompt length to 8-18 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Розуміння тексту про велоспорт' Q11 prompt length 0 (target: 8-18)
  - FIX: Adjust prompt length to 8-18 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Розуміння тексту про велоспорт' Q12 prompt length 0 (target: 8-18)
  - FIX: Adjust prompt length to 8-18 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Розуміння тексту про велоспорт' Q13 prompt length 0 (target: 8-18)
  - FIX: Adjust prompt length to 8-18 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Розуміння тексту про велоспорт' Q14 prompt length 0 (target: 8-18)
  - FIX: Adjust prompt length to 8-18 words.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Відновіть порядок слів' item 5 has 18 words (target: 8-14)
  - FIX: Adjust sentence length to 8-14 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Відновіть порядок слів' item 7 has 17 words (target: 8-14)
  - FIX: Adjust sentence length to 8-14 words to match B1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Відновіть порядок слів' item 8 has 17 words (target: 8-14)
  - FIX: Adjust sentence length to 8-14 words to match B1 complexity.
- **[YAML_SCHEMA_VIOLATION]** Schema error in 83-cycling-water.yaml: [index-0] quiz: 'items.13' - 'question' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 83-cycling-water.yaml: [index-6] select: 'items.5' - 'question' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 83-cycling-water.yaml: [index-9] translate: 'items.7.options.3' - 'correct' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[STATE_STANDARD_LOW_IMMERSION]** Module 83 has 97.9% immersion (target: 98.0%+)
  - FIX: Add more Ukrainian content to reach 98%+ immersion for full immersion modules

## TEMPLATE COMPLIANCE
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Пояснення|Граматика|Теорія' per template 'b1-grammar-module-template'
  - FIX: Add '## Пояснення' section as specified in docs/l2-uk-en/templates/b1-grammar-module-template.md

## Recommendation
**📝 UPDATE** (severity 50/100)

- Revision recommended (severity 50/100)
- 22 violations (severe - consider revision)

## Gates
- **Words:** ✅ 1749/1500
- **Activities:** ✅ 11/8
- **Density:** ✅ All > 12
- **Unique_types:** ✅ 11/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 7/5
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 30/25
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 20 violations
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 97.9% (target 85-100% (B1.7-8 Ukraine))
- **Richness:** ✅ 99% (cultural)
- **Grammar:** ⏳ Pending validation

## Richness Details
**Score:** 99% (minimum: 95%)
**Module Type:** cultural

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| cultural | 6 | 5 | 100% | 33% | 33.3% |
| engagement | 7 | 6 | 100% | 20% | 20.0% |
| visual | 6 | 4 | 100% | 13% | 13.3% |
| variety | 0.98 | - | 98% | 7% | 6.5% |
| paragraph_var | 1.00 | - | 100% | 7% | 6.7% |
| examples | 14 | - | 100% | 7% | 6.7% |
| realworld | 5 | - | 100% | 7% | 6.7% |
| questions | 24 | 4 | 100% | 7% | 6.7% |
| **TOTAL** | | | | | **99.9%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 0 | Included in Core |
| **Вступ** | ⚪️ | 237 | Skipped |
| **Презентація** | ⚪️ | 735 | Skipped |
| **Практика** | ⚪️ | 112 | Skipped |
| **Продукція** | ⚪️ | 435 | Skipped |
| **Підсумок** | ✅ | 120 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 110 | Skipped |