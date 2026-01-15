# Audit Report: 132-metaphor-simile.md
**Phase:** C1.4 | **Level:** C1 | **Pedagogy:** Immersion | **Target:** 2000
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[YAML_SCHEMA_VIOLATION]** Schema error in 132-metaphor-simile.yaml: Schema validation error at key '11': {'type': 'fill-in', 'title': 'Створення метафор', 'items': [{'sentence': 'Його ідеї були _____ для нашого проекту.', 'answer': 'фундаментом', 'options': ['фундаментом', 'стіною', 'дахом', 'вікном']}, {'sentence': 'Вона потонула в _____ своїх мрій.', 'answer': 'океані', 'options': ['океані', 'лісі', 'полі', 'небі']}, {'sentence': 'Ця новина вдарила його, як _____.', 'answer': 'блискавка', 'options': ['блискавка', 'дощ', 'вітер', 'сніг']}, {'sentence': 'Він побудував _____ стіну мовчання навколо себе.', 'answer': 'глуху', 'options': ['глуху', 'німу', 'сліпу', 'тиху']}, {'sentence': 'Її слова були бальзамом на _____.', 'answer': 'душу', 'options': ['душу', 'серце', 'розум', 'тіло']}, {'sentence': 'Він тримав свої емоції в _____ рукавицях.', 'answer': 'їжакових', 'options': ['їжакових', 'вовчих', 'лисячих', 'ведмежих']}]} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## TEMPLATE COMPLIANCE
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Вступ|Контекст|Розминка' per template 'c1-module-template.md'
  - FIX: Add '## Вступ' section as specified in docs/l2-uk-en/templates/c1-module-template.md.md

## Recommendation
**📝 UPDATE** (severity 5/100)

- 2 violations (minor)

## Gates
- **Words:** ⚠️ 1993/2000 (7 short)
- **Activities:** ✅ 12/12
- **Density:** ✅ All > 12
- **Unique_types:** ✅ 10/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 9/7
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 25/25
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 1 violations
- **Content_heavy:** ✅ Content-heavy OK (12 activities)
- **Immersion:** 🇺🇦 99.9% (target 90-100%)
- **Richness:** ✅ 99% (style)
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ❌ 0/10 (PENDING) - Naturalness check required

## Richness Details
**Score:** 99% (minimum: 95%)
**Module Type:** style

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| exemplar_texts | 15 | 2 | 100% | 25% | 25.0% |
| model_answers | 74 | 3 | 100% | 20% | 20.0% |
| engagement | 9 | 5 | 100% | 15% | 15.0% |
| register_analysis | 7 | 5 | 100% | 15% | 15.0% |
| visual | 9 | 4 | 100% | 10% | 10.0% |
| variety | 0.99 | - | 99% | 5% | 5.0% |
| cultural | 5 | - | 100% | 5% | 5.0% |
| paragraph_var | 1.00 | - | 100% | 5% | 5.0% |
| **TOTAL** | | | | | **100.0%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 72 | Included in Core |
| **Warm-up** | ✅ | 73 | Included in Core |
| **Теорія: Від прямого до переносного** | ⚪️ | 753 | Skipped |
| **Аналіз: Майстри слова** | ✅ | 227 | Included in Core |
| **Стиль та Регістр** | ⚪️ | 290 | Skipped |
| **Метафори цифрової ери** | ⚪️ | 141 | Skipped |
| **Деколонізація мови** | ⚪️ | 308 | Skipped |
| **Підсумок** | ✅ | 67 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 62 | Skipped |