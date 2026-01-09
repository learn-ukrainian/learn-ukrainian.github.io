# Audit Report: 26-relative-clauses-yakyi.md
**Phase:** B1.3a | **Level:** B1 | **Pedagogy:** TTT | **Target:** 1500
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[YAML_SCHEMA_VIOLATION]** Schema error in 26-relative-clauses-yakyi.yaml: [розставте-слова-в-правильному-порядку] unjumble: 'items.7' - Additional properties are not allowed ('scrambled' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 26-relative-clauses-yakyi.yaml: [знайдіть-форми-який] mark-the-words: 'correct_words' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 26-relative-clauses-yakyi.yaml: [перекладіть-речення] translate: 'items.7' - 'source' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## TEMPLATE COMPLIANCE
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Warm-up|Introduction|Objectives|Контекст|Вступ|Розминка|Тест' per template 'b1-grammar-module-template'
  - FIX: Add '## Warm-up' section as specified in docs/l2-uk-en/templates/b1-grammar-module-template.md
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Presentation|Grammar|Focus|Презентація|Граматика|Теорія|Пояснення' per template 'b1-grammar-module-template'
  - FIX: Add '## Presentation' section as specified in docs/l2-uk-en/templates/b1-grammar-module-template.md
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Practice|Exercises|Activity|Практика|Вправи' per template 'b1-grammar-module-template'
  - FIX: Add '## Practice' section as specified in docs/l2-uk-en/templates/b1-grammar-module-template.md
- ❌ **[EMPTY_REQUIRED_SECTION]** Required section '## Потрібно більше практики?' is empty
  - FIX: Populate the section with meaningful content or generate it if it's a mandatory placeholder.

## Recommendation
**📝 UPDATE** (severity 55/100)

- Revision recommended (severity 55/100)
- 7 violations (significant)
- Activity count below minimum
- Activity density below minimum

## Gates
- **Words:** ⚠️ 1491/1500 (9 short)
- **Activities:** ❌ 0/12
- **Density:** ❌ 0 < 14
- **Unique_types:** ❌ 0/4 types
- **Priority:** ❌ No priority types
- **Engagement:** ✅ 13/5
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 10 < 25 (soft target)
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 3 violations
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 98.6% (target 85-100% (B1.3-4 Complex))
- **Richness:** ✅ 95% (grammar)
- **Grammar:** ⏳ Pending validation

## Richness Details
**Score:** 95% (minimum: 95%)
**Module Type:** grammar

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| examples | 50 | 24 | 100% | 20% | 20.0% |
| engagement | 13 | 5 | 100% | 15% | 15.0% |
| dialogues | 11 | 4 | 100% | 15% | 15.0% |
| variety | 0.94 | - | 94% | 10% | 9.4% |
| cultural | 2 | 3 | 67% | 10% | 6.7% |
| realworld | 4 | 3 | 100% | 10% | 10.0% |
| visual | 6 | 3 | 100% | 5% | 5.0% |
| paragraph_var | 0.96 | - | 96% | 5% | 4.8% |
| questions | 40 | 5 | 100% | 5% | 5.0% |
| proverbs | 2 | 1 | 100% | 5% | 5.0% |
| **TOTAL** | | | | | **95.9%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 49 | Included in Core |
| **Діагностика** | ✅ | 166 | Included in Core |
| **Аналіз** | ✅ | 93 | Included in Core |
| **Поглиблення** | ⚪️ | 617 | Skipped |
| **Діалоги** | ✅ | 203 | Included in Core |
| **Підсумок** | ✅ | 363 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 0 | Skipped |