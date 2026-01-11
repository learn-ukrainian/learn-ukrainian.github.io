# Audit Report: 27-law-justice-vocabulary.md
**Phase:** B2 | **Level:** B2 | **Pedagogy:** CLIL | **Target:** 1750
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[YAML_SCHEMA_VIOLATION]** Schema error in 27-law-justice-vocabulary.yaml: Array validation: '' should be non-empty
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 27-law-justice-vocabulary.yaml: [index-3] fill-in: 'items.15' - 'answer' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 27-law-justice-vocabulary.yaml: [index-4] fill-in: 'items.15' - 'answer' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 27-law-justice-vocabulary.yaml: [index-7] unjumble: 'items.15' - 'words' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 27-law-justice-vocabulary.yaml: [index-8] cloze: 'passage' - '' should be non-empty
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[MISSING_ADVANCED_ACTIVITY]** B2+ module (focus: grammar) missing advanced activity type: essay-response
  - FIX: Add a essay-response activity to meet advanced richness standards.

## TEMPLATE COMPLIANCE
- ❌ **[DUPLICATE_SYNONYMOUS_HEADERS]** Multiple aliases for 'Вступ|Контекст|Розминка' found: Історичний контекст: Судова реформа в Україні, Вступ: Судова система України
  - FIX: Keep only one version of the header (preferably the primary one or the one with more content).
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Пояснення|Граматика|Теорія' per template 'b2-grammar-module-template'
  - FIX: Add '## Пояснення' section as specified in docs/l2-uk-en/templates/b2-grammar-module-template.md
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Трансформації' per template 'b2-grammar-module-template'
  - FIX: Add '## Трансформації' section as specified in docs/l2-uk-en/templates/b2-grammar-module-template.md

## Recommendation
**📝 UPDATE** (severity 55/100)

- Revision recommended (severity 55/100)
- 9 violations (significant)
- Activity count below minimum
- Activity density below minimum

## Gates
- **Words:** ✅ 1848/1750
- **Activities:** ❌ 0/10
- **Density:** ❌ 0 < 14
- **Unique_types:** ❌ 0/4 types
- **Priority:** ❌ No priority types
- **Engagement:** ✅ 10/6
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 132/25
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 6 violations
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 99.1% (target 90-100% (grammar))
- **Richness:** ✅ 95% (grammar)
- **Grammar:** ⏳ Pending validation

## Richness Details
**Score:** 95% (minimum: 95%)
**Module Type:** grammar

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| examples | 51 | 24 | 100% | 20% | 20.0% |
| engagement | 13 | 5 | 100% | 15% | 15.0% |
| dialogues | 23 | 4 | 100% | 15% | 15.0% |
| variety | 0.96 | - | 96% | 10% | 9.6% |
| cultural | 3 | 3 | 100% | 10% | 10.0% |
| realworld | 2 | 3 | 67% | 10% | 6.7% |
| visual | 5 | 3 | 100% | 5% | 5.0% |
| paragraph_var | 0.89 | - | 89% | 5% | 4.5% |
| questions | 18 | 5 | 100% | 5% | 5.0% |
| proverbs | 3 | 1 | 100% | 5% | 5.0% |
| **TOTAL** | | | | | **95.8%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 52 | Included in Core |
| **Вступ: Судова система України** | ⚪️ | 253 | Skipped |
| **Історичний контекст: Судова реформа в Україні** | ✅ | 239 | Included in Core |
| **Наратив: Цивільна справа** | ⚪️ | 178 | Skipped |
| **Наратив: Кримінальна справа** | ⚪️ | 564 | Skipped |
| **Аналіз: Юридичний регістр** | ✅ | 311 | Included in Core |
| **Підсумок** | ✅ | 0 | Included in Core |
| **Що ми вивчили** | ⚪️ | 75 | Skipped |
| **Самоперевірка** | ⚪️ | 50 | Skipped |
| **Наступні кроки** | ⚪️ | 16 | Skipped |
| **Потрібно більше практики?** | ⚪️ | 110 | Skipped |