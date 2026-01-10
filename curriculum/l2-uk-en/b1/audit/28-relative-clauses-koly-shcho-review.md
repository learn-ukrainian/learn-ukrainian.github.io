# Audit Report: 28-relative-clauses-koly-shcho.md
**Phase:** B1.3a | **Level:** B1 | **Pedagogy:** TTT | **Target:** 1500
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[YAML_SCHEMA_VIOLATION]** Schema error in 28-relative-clauses-koly-shcho.yaml: [index-5] unjumble: 'items.7' - Additional properties are not allowed ('scrambled' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 28-relative-clauses-koly-shcho.yaml: [index-8] mark-the-words: 'correct_words' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 28-relative-clauses-koly-shcho.yaml: [index-10] translate: 'items.7' - 'source' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## TEMPLATE COMPLIANCE
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Вступ|Контекст|Розминка|Тест' per template 'b1-grammar-module-template'
  - FIX: Add '## Вступ' section as specified in docs/l2-uk-en/templates/b1-grammar-module-template.md
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Пояснення|Граматика|Теорія' per template 'b1-grammar-module-template'
  - FIX: Add '## Пояснення' section as specified in docs/l2-uk-en/templates/b1-grammar-module-template.md
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Практика|Вправи' per template 'b1-grammar-module-template'
  - FIX: Add '## Практика' section as specified in docs/l2-uk-en/templates/b1-grammar-module-template.md

## Recommendation
**📝 UPDATE** (severity 40/100)

- Revision recommended (severity 40/100)
- 6 violations (moderate)
- Activity count below minimum
- Activity density below minimum

## Gates
- **Words:** ✅ 1999/1500
- **Activities:** ❌ 0/8
- **Density:** ❌ 0 < 12
- **Unique_types:** ❌ 0/4 types
- **Priority:** ❌ No priority types
- **Engagement:** ✅ 16/5
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 18 < 25 (soft target)
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 3 violations
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 98.7% (target 85-100% (B1.3-4 Complex))
- **Richness:** ✅ 99% (grammar)
- **Grammar:** ⏳ Pending validation

## Richness Details
**Score:** 99% (minimum: 95%)
**Module Type:** grammar

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| examples | 31 | 24 | 100% | 20% | 20.0% |
| engagement | 12 | 5 | 100% | 15% | 15.0% |
| dialogues | 11 | 4 | 100% | 15% | 15.0% |
| variety | 0.96 | - | 96% | 10% | 9.6% |
| cultural | 3 | 3 | 100% | 10% | 10.0% |
| realworld | 6 | 3 | 100% | 10% | 10.0% |
| visual | 8 | 3 | 100% | 5% | 5.0% |
| paragraph_var | 1.00 | - | 100% | 5% | 5.0% |
| questions | 19 | 5 | 100% | 5% | 5.0% |
| proverbs | 2 | 1 | 100% | 5% | 5.0% |
| **TOTAL** | | | | | **99.6%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 50 | Included in Core |
| **Діагностика** | ✅ | 197 | Included in Core |
| **Аналіз** | ✅ | 293 | Included in Core |
| **Поглиблення** | ⚪️ | 896 | Skipped |
| **Діалоги** | ✅ | 214 | Included in Core |
| **Підсумок** | ✅ | 239 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 110 | Skipped |