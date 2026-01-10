# Audit Report: 77-ukrainian-cinema-and-tv.md
**Phase:** B1.7 | **Level:** B1 | **Pedagogy:** cultural | **Target:** 1500
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Складіть речення про українське кіно' item 8 has 6 words (target: 8-14)
  - FIX: Adjust sentence length to 8-14 words to match B1 complexity.
- **[YAML_SCHEMA_VIOLATION]** Schema error in 77-ukrainian-cinema-and-tv.yaml: [українське-кіно--розуміння-тексту] quiz: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 77-ukrainian-cinema-and-tv.yaml: [правда-чи-хибність-про-українське-кіно] true-false: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 77-ukrainian-cinema-and-tv.yaml: [кіно-лексика--терміни-та-визначення] match-up: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 77-ukrainian-cinema-and-tv.yaml: [заповніть-пропуски-кінолексикою] cloze: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 77-ukrainian-cinema-and-tv.yaml: [заповніть-текст-про-українське-кіно] cloze: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 77-ukrainian-cinema-and-tv.yaml: [розподіліть-за-категоріями] group-sort: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 77-ukrainian-cinema-and-tv.yaml: [оберіть-усі-правильні-відповіді] select: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 77-ukrainian-cinema-and-tv.yaml: [знайдіть-слова,-пов'язані-з-кіно] mark-the-words: 'correct_words' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 77-ukrainian-cinema-and-tv.yaml: [складіть-речення-про-українське-кіно] unjumble: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 77-ukrainian-cinema-and-tv.yaml: [виправте-помилки-у-реченнях-про-кіно] error-correction: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 77-ukrainian-cinema-and-tv.yaml: [перекладіть-фрази-про-кіно] translate: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## TEMPLATE COMPLIANCE
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Пояснення|Граматика|Теорія' per template 'b1-grammar-module-template'
  - FIX: Add '## Пояснення' section as specified in docs/l2-uk-en/templates/b1-grammar-module-template.md

## Recommendation
**📝 UPDATE** (severity 50/100)

- Revision recommended (severity 50/100)
- 13 violations (severe - consider revision)

## Gates
- **Words:** ✅ 1702/1500
- **Activities:** ✅ 11/8
- **Density:** ✅ All > 12
- **Unique_types:** ✅ 10/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 9/5
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 50/25
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 12 violations
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 99.0% (target 85-100% (B1.7-8 Ukraine))
- **Richness:** ❌ 94% < 95% min (cultural)
- **Grammar:** ⏳ Pending validation

## Richness Details
**Score:** 94% (minimum: 95%)
**Module Type:** cultural

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| cultural | 5 | 5 | 100% | 33% | 33.3% |
| engagement | 9 | 6 | 100% | 20% | 20.0% |
| visual | 3 | 4 | 75% | 13% | 10.0% |
| variety | 0.97 | - | 97% | 7% | 6.5% |
| paragraph_var | 0.72 | - | 72% | 7% | 4.8% |
| examples | 23 | - | 100% | 7% | 6.7% |
| realworld | 3 | - | 100% | 7% | 6.7% |
| questions | 32 | 4 | 100% | 7% | 6.7% |
| **TOTAL** | | | | | **94.6%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 131 | Included in Core |
| **Презентація** | ⚪️ | 819 | Skipped |
| **Практика** | ⚪️ | 485 | Skipped |
| **Підсумок** | ✅ | 157 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 110 | Skipped |