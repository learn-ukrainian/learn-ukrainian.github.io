# Audit Report: 18-essay-writing-practice.md
**Phase:** C1.1 | **Level:** C1 | **Pedagogy:** Task-Based | **Target:** 2000
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[COMPLEXITY_WORD_COUNT]** quiz 'Критерії оцінювання: Checklist' Q3 prompt length 11 (target: 12-30)
  - FIX: Adjust prompt length to 12-30 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Критерії оцінювання: Checklist' Q5 prompt length 11 (target: 12-30)
  - FIX: Adjust prompt length to 12-30 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Перевірка розуміння' Q3 prompt length 11 (target: 12-30)
  - FIX: Adjust prompt length to 12-30 words.
- **[YAML_SCHEMA_VIOLATION]** Schema error in 18-essay-writing-practice.yaml: [анатомія-тексту:-структура] match-up: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 18-essay-writing-practice.yaml: [детектор-тези] group-sort: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 18-essay-writing-practice.yaml: [академічний-стиль:-трансформація] match-up: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 18-essay-writing-practice.yaml: [логічні-зв'язки-(конектори)] fill-in: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 18-essay-writing-practice.yaml: [редагування:-емоційна-лексика] error-correction: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 18-essay-writing-practice.yaml: [розробка-аргументу] cloze: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 18-essay-writing-practice.yaml: [критерії-оцінювання:-checklist] quiz: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 18-essay-writing-practice.yaml: [типи-вступу] match-up: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 18-essay-writing-practice.yaml: [синтез-висновку] unjumble: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 18-essay-writing-practice.yaml: [есе:-практичне-завдання] essay-response: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 18-essay-writing-practice.yaml: [перевірка-розуміння] quiz: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 18-essay-writing-practice.yaml: [тематична-лексика] fill-in: Additional properties are not allowed ('id' was unexpected)
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## Recommendation
**📝 UPDATE** (severity 50/100)

- Revision recommended (severity 50/100)
- 15 violations (severe - consider revision)

## Gates
- **Words:** ⚠️ 1907/2000 (93 short)
- **Activities:** ✅ 12/12
- **Density:** ✅ All > 12
- **Unique_types:** ✅ 8/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 8/7
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 18 < 25 (soft target)
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 15 violations
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 99.5% (target 98-100%)
- **Richness:** ✅ 99% (style)
- **Grammar:** ⏳ Pending validation

## Richness Details
**Score:** 99% (minimum: 95%)
**Module Type:** style

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| exemplar_texts | 15 | 2 | 100% | 25% | 25.0% |
| model_answers | 45 | 3 | 100% | 20% | 20.0% |
| engagement | 8 | 5 | 100% | 15% | 15.0% |
| register_analysis | 8 | 5 | 100% | 15% | 15.0% |
| visual | 8 | 4 | 100% | 10% | 10.0% |
| variety | 1.00 | - | 100% | 5% | 5.0% |
| cultural | 2 | - | 100% | 5% | 5.0% |
| paragraph_var | 1.00 | - | 100% | 5% | 5.0% |
| **TOTAL** | | | | | **100.0%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 0 | Included in Core |
| **Вступ** | ⚪️ | 83 | Skipped |
| **Аналіз: Етос академічного письма** | ✅ | 268 | Included in Core |
| **Анатомія переконливого тексту** | ✅ | 453 | Included in Core |
| **Конектори: Тканина тексту** | ✅ | 207 | Included in Core |
| **Практичний розбір: Від чернетки до шедевру** | ⚪️ | 184 | Skipped |
| **Типові помилки студентів** | ✅ | 210 | Included in Core |
| **Робота з джерелами та цитування** | ⚪️ | 210 | Skipped |
| **Етап планування** | ⚪️ | 228 | Skipped |
| **Підсумок** | ✅ | 43 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 21 | Skipped |