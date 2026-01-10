# Audit Report: 86-ukrainski-sviata-ta-festyvali.md
**Phase:** B1.7 | **Level:** B1 | **Pedagogy:** cultural | **Target:** 1500
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[COMPLEXITY]** match-up 'Свята — лексика та визначення' has 15 pairs (target: 12-14)
  - FIX: Adjust number of pairs to 12-14.
- **[YAML_SCHEMA_VIOLATION]** Schema error in 86-ukrainski-sviata-ta-festyvali.yaml: [українські-свята--розуміння-тексту] quiz: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 86-ukrainski-sviata-ta-festyvali.yaml: [правда-чи-хибність-про-українські-свята] true-false: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 86-ukrainski-sviata-ta-festyvali.yaml: [свята--лексика-та-визначення] match-up: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 86-ukrainski-sviata-ta-festyvali.yaml: [святкові-вирази] cloze: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 86-ukrainski-sviata-ta-festyvali.yaml: [релігійні-свята-україни] cloze: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 86-ukrainski-sviata-ta-festyvali.yaml: [категорії-свят] group-sort: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 86-ukrainski-sviata-ta-festyvali.yaml: [що-пов'язано-з-різдвом?] select: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 86-ukrainski-sviata-ta-festyvali.yaml: [знайдіть-святкові-терміни] mark-the-words: 'correct_words' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 86-ukrainski-sviata-ta-festyvali.yaml: [складіть-речення-про-свята] unjumble: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 86-ukrainski-sviata-ta-festyvali.yaml: [виправте-помилки] error-correction: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 86-ukrainski-sviata-ta-festyvali.yaml: [перекладіть-святкові-фрази] translate: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[STATE_STANDARD_LOW_IMMERSION]** Module 86 has 97.5% immersion (target: 98.0%+)
  - FIX: Add more Ukrainian content to reach 98%+ immersion for full immersion modules

## TEMPLATE COMPLIANCE
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Пояснення|Граматика|Теорія' per template 'b1-grammar-module-template'
  - FIX: Add '## Пояснення' section as specified in docs/l2-uk-en/templates/b1-grammar-module-template.md

## Recommendation
**📝 UPDATE** (severity 50/100)

- Revision recommended (severity 50/100)
- 14 violations (severe - consider revision)

## Gates
- **Words:** ✅ 2015/1500
- **Activities:** ✅ 11/8
- **Density:** ✅ All > 12
- **Unique_types:** ✅ 10/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 12/5
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 49/25
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 12 violations
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 97.5% (target 85-100% (B1.7-8 Ukraine))
- **Richness:** ✅ 95% (cultural)
- **Grammar:** ⏳ Pending validation

## Richness Details
**Score:** 95% (minimum: 95%)
**Module Type:** cultural

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| cultural | 13 | 5 | 100% | 33% | 33.3% |
| engagement | 9 | 6 | 100% | 20% | 20.0% |
| visual | 3 | 4 | 75% | 13% | 10.0% |
| variety | 0.95 | - | 95% | 7% | 6.3% |
| paragraph_var | 0.87 | - | 87% | 7% | 5.8% |
| examples | 43 | - | 100% | 7% | 6.7% |
| realworld | 6 | - | 100% | 7% | 6.7% |
| questions | 30 | 4 | 100% | 7% | 6.7% |
| **TOTAL** | | | | | **95.5%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 136 | Included in Core |
| **Презентація** | ⚪️ | 0 | Skipped |
| **Релігійні свята України** | ⚪️ | 461 | Skipped |
| **Народні свята та обряди** | ⚪️ | 332 | Skipped |
| **Національні та сучасні свята** | ⚪️ | 265 | Skipped |
| **Практика** | ⚪️ | 177 | Skipped |
| **Продукція** | ⚪️ | 0 | Skipped |
| **Діалог 1: Запрошення на свято** | ✅ | 90 | Included in Core |
| **Діалог 2: Розмова про фестиваль** | ✅ | 90 | Included in Core |
| **Діалог 3: Привітання зі святом** | ✅ | 107 | Included in Core |
| **Діалог 4: Обговорення Івана Купала** | ✅ | 141 | Included in Core |
| **Підсумок** | ✅ | 106 | Included in Core |
| **Ресурси** | ⚪️ | 0 | Skipped |
| **Потрібно більше практики?** | ⚪️ | 110 | Skipped |