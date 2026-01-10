# Audit Report: 29-surzhyk.md
**Phase:** C1.3 | **Level:** C1 | **Pedagogy:** Immersion | **Target:** 2000
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[COMPLEXITY_WORD_COUNT]** quiz 'Що таке суржик?' Q5 prompt length 11 (target: 12-30)
  - FIX: Adjust prompt length to 12-30 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Культурний феномен' Q5 prompt length 11 (target: 12-30)
  - FIX: Adjust prompt length to 12-30 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Лінгвістична теорія' Q2 prompt length 11 (target: 12-30)
  - FIX: Adjust prompt length to 12-30 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Лінгвістична теорія' Q3 prompt length 8 (target: 12-30)
  - FIX: Adjust prompt length to 12-30 words.
- **[YAML_SCHEMA_VIOLATION]** Schema error in 29-surzhyk.yaml: [29-quiz-1] quiz: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 29-surzhyk.yaml: [29-group-sort-1] group-sort: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 29-surzhyk.yaml: [29-match-1] match-up: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 29-surzhyk.yaml: [29-fill-in-1] fill-in: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 29-surzhyk.yaml: [29-group-sort-2] group-sort: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 29-surzhyk.yaml: [29-quiz-2] quiz: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 29-surzhyk.yaml: [29-match-2] match-up: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 29-surzhyk.yaml: [29-fill-in-2] fill-in: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 29-surzhyk.yaml: [29-unjumble-1] unjumble: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 29-surzhyk.yaml: [29-quiz-3] quiz: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 29-surzhyk.yaml: [29-essay-1] essay-response: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 29-surzhyk.yaml: [29-mark-1] mark-the-words: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## TEMPLATE COMPLIANCE
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Потрібно більше практики?' per template 'c1-module-template'
  - FIX: Add '## Потрібно більше практики?' section as specified in docs/l2-uk-en/templates/c1-module-template.md

## Recommendation
**📝 UPDATE** (severity 50/100)

- Revision recommended (severity 50/100)
- 17 violations (severe - consider revision)

## Gates
- **Words:** ❌ 1897/2000
- **Activities:** ✅ 12/12
- **Density:** ✅ All > 12
- **Unique_types:** ✅ 7/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 7/7
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 25/25
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 16 violations
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 99.0% (target 98-100%)
- **Richness:** ✅ 99% (content)
- **Grammar:** ⏳ Pending validation

## Richness Details
**Score:** 99% (minimum: 95%)
**Module Type:** content

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| examples | 20 | 15 | 100% | 25% | 25.0% |
| engagement | 7 | 5 | 100% | 19% | 18.7% |
| variety | 0.98 | - | 98% | 12% | 12.2% |
| cultural | 5 | 4 | 100% | 12% | 12.5% |
| realworld | 3 | 3 | 100% | 12% | 12.5% |
| visual | 13 | 4 | 100% | 6% | 6.2% |
| paragraph_var | 1.00 | - | 100% | 6% | 6.2% |
| questions | 14 | 4 | 100% | 6% | 6.2% |
| **TOTAL** | | | | | **99.8%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 31 | Included in Core |
| **1. Що таке суржик?** | ⚪️ | 154 | Skipped |
| **2. Аналіз: Анатомія Суржику** | ✅ | 183 | Included in Core |
| **3. Чому ми так говоримо? (Історичний контекст)** | ✅ | 157 | Included in Core |
| **4. Суржик у культурі: Від сорому до сміху** | ✅ | 175 | Included in Core |
| **5. Інтернет-суржик: Нова реальність** | ⚪️ | 120 | Skipped |
| **6. Читання: Суржик у діалозі** | ✅ | 230 | Included in Core |
| **7. Приклади вживання суржику** | ⚪️ | 158 | Skipped |
| **8. Мовна гігієна: Як перейти на чисту мову?** | ⚪️ | 174 | Skipped |
| **9. Приклади з життя: Діалоги** | ✅ | 193 | Included in Core |
| **10. Практикум редагування** | ⚪️ | 146 | Skipped |
| **Підсумок** | ✅ | 81 | Included in Core |
| **Need More Practice?** | ⚪️ | 95 | Skipped |