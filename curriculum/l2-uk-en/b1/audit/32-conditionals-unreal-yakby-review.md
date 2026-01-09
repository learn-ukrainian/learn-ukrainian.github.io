# Audit Report: 32-conditionals-unreal-yakby.md
**Phase:** B1.3a | **Level:** B1 | **Pedagogy:** TTT | **Target:** 1500
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[COMPLEXITY]** cloze 'Заповніть пропуски в тексті' has 0 items (minimum: 6)
  - FIX: Add more items. B1 cloze requires at least 6 items.
- **[YAML_SCHEMA_VIOLATION]** Schema error in 32-conditionals-unreal-yakby.yaml: [позначте-частку-«б»-або-«би»-та-сполучник-«якби»] mark-the-words: 'correct_words' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 32-conditionals-unreal-yakby.yaml: [виберіть-усі-граматично-правильні-речення] select: 'items.7' - 'question' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[STATE_STANDARD_LOW_IMMERSION]** Module 32 has 96.1% immersion (target: 98.0%+)
  - FIX: Add more Ukrainian content to reach 98%+ immersion for full immersion modules

## TEMPLATE COMPLIANCE
- ❌ **[EMPTY_REQUIRED_SECTION]** Required section '## Потрібно більше практики?' is empty
  - FIX: Populate the section with meaningful content or generate it if it's a mandatory placeholder.

## Recommendation
**📝 UPDATE** (severity 40/100)

- Revision recommended (severity 40/100)
- 5 violations (moderate)
- Activity count below minimum
- Activity density below minimum

## Gates
- **Words:** ✅ 1615/1500
- **Activities:** ❌ 11/12
- **Density:** ❌ 2 < 14
- **Unique_types:** ✅ 10/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 8/5
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 25/25
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 3 violations
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 96.1% (target 85-100% (B1.3-4 Complex))
- **Richness:** ✅ 95% (grammar)
- **Grammar:** ⏳ Pending validation

## Richness Details
**Score:** 95% (minimum: 95%)
**Module Type:** grammar

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| examples | 32 | 24 | 100% | 20% | 20.0% |
| engagement | 8 | 5 | 100% | 15% | 15.0% |
| dialogues | 16 | 4 | 100% | 15% | 15.0% |
| variety | 0.93 | - | 93% | 10% | 9.3% |
| cultural | 4 | 3 | 100% | 10% | 10.0% |
| realworld | 2 | 3 | 67% | 10% | 6.7% |
| visual | 9 | 3 | 100% | 5% | 5.0% |
| paragraph_var | 0.94 | - | 94% | 5% | 4.7% |
| questions | 23 | 5 | 100% | 5% | 5.0% |
| proverbs | 10 | 1 | 100% | 5% | 5.0% |
| **TOTAL** | | | | | **95.7%** |

## Low Density Activities
| Activity | Type | Items | Required | Fix |
|----------|------|-------|----------|-----|
| Доповніть речення правильною формою | cloze | 8 | 14 | Add 6 more items |
| Заповніть пропуски в тексті | cloze | 0 | 14 | Add 14 more items |


## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 48 | Included in Core |
| **Тест: Перевірте себе** | ⚪️ | 122 | Skipped |
| **Пояснення** | ⚪️ | 676 | Skipped |
| **Практика** | ⚪️ | 248 | Skipped |
| **Діалоги** | ✅ | 362 | Included in Core |
| **Підсумок** | ✅ | 159 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 0 | Skipped |