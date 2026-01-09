# Audit Report: 89-b1-grammar-integration.md
**Phase:** B1.8 | **Level:** B1 | **Pedagogy:** TTT | **Target:** 1000
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[SECTION_ORDER]** '## Самооцінка' should come after 'summary' section
  - FIX: Reorder sections to: Summary → Activities → Self-Assessment → External → Vocabulary
- **[YAML_SCHEMA_VIOLATION]** Schema error in 89-b1-grammar-integration.yaml: [складіть-складні-речення] unjumble: 'items.9' - Additional properties are not allowed ('scrambled' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 89-b1-grammar-integration.yaml: [переклад] translate: 'items.13' - 'source' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 89-b1-grammar-integration.yaml: [знайдіть-дієслова-доконаного-виду] mark-the-words: 'correct_words' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## TEMPLATE COMPLIANCE
- ❌ **[DUPLICATE_SYNONYMOUS_HEADERS]** Multiple aliases for 'Warm-up|Introduction|Objectives|Контекст|Вступ|Розминка|Тест' found: Тест 2: Дієслова руху, Тест 3: Складні речення, Тест 4: Дієприкметники, Тест 1: Вид дієслова
  - FIX: Keep only one version of the header (preferably the primary one or the one with more content).
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Presentation|Grammar|Focus|Презентація|Граматика|Теорія|Пояснення' per template 'b1-grammar-module-template'
  - FIX: Add '## Presentation' section as specified in docs/l2-uk-en/templates/b1-grammar-module-template.md
- ❌ **[EMPTY_REQUIRED_SECTION]** Required section '## Потрібно більше практики?' is empty
  - FIX: Populate the section with meaningful content or generate it if it's a mandatory placeholder.

## Recommendation
**📝 UPDATE** (severity 55/100)

- Revision recommended (severity 55/100)
- 7 violations (significant)
- Activity count below minimum
- Activity density below minimum

## Gates
- **Words:** ✅ 1557/1000
- **Activities:** ❌ 0/10
- **Density:** ❌ 0 < 12
- **Unique_types:** ❌ 0/4 types
- **Priority:** ❌ No priority types
- **Engagement:** ✅ 9/4
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 11 < 15 (soft target)
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 4 violations
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 99.8% (target 85-100% (B1.7-8 Ukraine))
- **Richness:** ✅ 100% (grammar)
- **Grammar:** ⏳ Pending validation

## Richness Details
**Score:** 100% (minimum: 95%)
**Module Type:** grammar

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| examples | 52 | 24 | 100% | 20% | 20.0% |
| engagement | 9 | 5 | 100% | 15% | 15.0% |
| dialogues | 4 | 4 | 100% | 15% | 15.0% |
| variety | 1.00 | - | 100% | 10% | 10.0% |
| cultural | 7 | 3 | 100% | 10% | 10.0% |
| realworld | 5 | 3 | 100% | 10% | 10.0% |
| visual | 7 | 3 | 100% | 5% | 5.0% |
| paragraph_var | 1.00 | - | 100% | 5% | 5.0% |
| questions | 18 | 5 | 100% | 5% | 5.0% |
| proverbs | 3 | 1 | 100% | 5% | 5.0% |
| **TOTAL** | | | | | **100.0%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 49 | Included in Core |
| **Діагностика** | ✅ | 205 | Included in Core |
| **Аналіз** | ✅ | 378 | Included in Core |
| **Поглиблення** | ⚪️ | 422 | Skipped |
| **Практика** | ⚪️ | 222 | Skipped |
| **Самооцінка** | ⚪️ | 130 | Skipped |
| **Наступний крок: Рівень B2** | ⚪️ | 68 | Skipped |
| **Підсумок** | ✅ | 83 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 0 | Skipped |