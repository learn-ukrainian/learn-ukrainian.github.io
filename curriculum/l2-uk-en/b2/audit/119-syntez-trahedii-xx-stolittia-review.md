# Audit Report: 119-syntez-trahedii-xx-stolittia.md
**Phase:** B2.3c | **Level:** B2 | **Pedagogy:** CBI | **Target:** 1400
**Overall Status:** ❌ FAIL

## LINT ERRORS
- ❌ Line 9: Use Ukrainian angular quotes («...») instead of ASCII quotes (").
- ❌ Line 15: Use Ukrainian angular quotes («...») instead of ASCII quotes (").
- ❌ Line 23: Use Ukrainian angular quotes («...») instead of ASCII quotes (").
- ❌ Line 41: Use Ukrainian angular quotes («...») instead of ASCII quotes (").
- ❌ Line 43: Use Ukrainian angular quotes («...») instead of ASCII quotes (").
- ❌ Line 52: Use Ukrainian angular quotes («...») instead of ASCII quotes (").
- ❌ Line 61: Use Ukrainian angular quotes («...») instead of ASCII quotes (").
- ❌ Line 69: Use Ukrainian angular quotes («...») instead of ASCII quotes (").
- ❌ Line 70: Use Ukrainian angular quotes («...») instead of ASCII quotes (").
- ❌ Line 72: Use Ukrainian angular quotes («...») instead of ASCII quotes (").
- ❌ Line 76: Use Ukrainian angular quotes («...») instead of ASCII quotes (").
- ❌ Line 80: Use Ukrainian angular quotes («...») instead of ASCII quotes (").
- ❌ Line 81: Use Ukrainian angular quotes («...») instead of ASCII quotes (").
- ❌ Line 82: Use Ukrainian angular quotes («...») instead of ASCII quotes (").
- ❌ Line 86: Use Ukrainian angular quotes («...») instead of ASCII quotes (").

## PEDAGOGICAL VIOLATIONS
- **[YAML_SCHEMA_VIOLATION]** Schema error in 119-syntez-trahedii-xx-stolittia.yaml: [письмове-завдання-(аналіз)] select: 'items.7' - 'question' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 119-syntez-trahedii-xx-stolittia.yaml: [порівняльний-аналіз-джерел] select: 'items.6' - 'question' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 119-syntez-trahedii-xx-stolittia.yaml: [синтез-міфів-та-реальності] true-false: 'items.7' - 'correct' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 119-syntez-trahedii-xx-stolittia.yaml: [методи-деколонізації] select: 'items.5' - 'question' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 119-syntez-trahedii-xx-stolittia.yaml: [патерни-нищення-та-спротиву] group-sort: 'groups.1' - 'name' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 119-syntez-trahedii-xx-stolittia.yaml: [професійний-переклад] translate: 'items.5' - 'source' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[MISSING_ADVANCED_ACTIVITY]** B2+ module (focus: history) missing advanced activity type: essay-response
  - FIX: Add a essay-response activity to meet advanced richness standards.
- **[MISSING_ADVANCED_ACTIVITY]** B2+ module (focus: history) missing advanced activity type: comparative-study
  - FIX: Add a comparative-study activity to meet advanced richness standards.

## Recommendation
**🔄 REWRITE** (severity 75/100)

- 8 violations (significant)
- 15 format errors (many)
- Activity count below minimum
- Activity density below minimum

## Gates
- **Words:** ✅ 1730/1400
- **Activities:** ❌ 0/10
- **Density:** ❌ 0 < 14
- **Unique_types:** ❌ 0/4 types
- **Priority:** ❌ No priority types
- **Engagement:** ✅ 8/5
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 25/20
- **Structure:** ✅ Valid Structure
- **Lint:** ❌ 15 Format Errors
- **Pedagogy:** ❌ 8 violations
- **Content_heavy:** ⚠️ Too few activities: 0 (target 10-14)
- **Immersion:** 🇺🇦 99.9% (target 98-100% (history))
- **Richness:** ✅ 95% (history)
- **Grammar:** ⏳ Pending validation

## Richness Details
**Score:** 95% (minimum: 95%)
**Module Type:** history

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| primary_sources | 3 | 3 | 100% | 24% | 23.8% |
| engagement | 7 | 6 | 100% | 14% | 14.3% |
| timeline_markers | 30 | 10 | 100% | 14% | 14.3% |
| decolonization | 15 | 2 | 100% | 14% | 14.3% |
| cultural | 2 | 4 | 50% | 10% | 4.8% |
| visual | 8 | 4 | 100% | 10% | 9.5% |
| variety | 1.00 | - | 100% | 5% | 4.8% |
| paragraph_var | 1.00 | - | 100% | 5% | 4.8% |
| questions | 6 | 3 | 100% | 5% | 4.8% |
| **TOTAL** | | | | | **95.2%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 109 | Included in Core |
| **Ключова тема: Травма як фундамент стійкості** | ⚪️ | 96 | Skipped |
| **Тематичний аналіз: Патерни нищення та виживання** | ✅ | 977 | Included in Core |
| **Деколонізаційний синтез: Повернення національної суб'єктності** | ⚪️ | 205 | Skipped |
| **Історіографічна рефлексія: Пам'ять як наша головна зброя** | ⚪️ | 240 | Skipped |
| **Summary** | ✅ | 103 | Included in Core |
| **Need More Practice?** | ⚪️ | 0 | Skipped |