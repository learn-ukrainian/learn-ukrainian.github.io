# Audit Report: 91-b1-capstone.md
**Phase:** B1.8 | **Level:** B1 | **Pedagogy:** TBL | **Target:** 1000
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[SECTION_ORDER]** '## Самооцінка' should come after 'summary' section
  - FIX: Reorder sections to: Summary → Activities → Self-Assessment → External → Vocabulary
- **[YAML_SCHEMA_VIOLATION]** Schema error in 91-b1-capstone.yaml: [вид-дієслова-у-контексті] fill-in: 'items.13.options' - ['приходитимеш', 'прийдеш'] is too short
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 91-b1-capstone.yaml: [знайдіть-дієприкметники] mark-the-words: 'correct_words' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## TEMPLATE COMPLIANCE
- ❌ **[DUPLICATE_SYNONYMOUS_HEADERS]** Multiple aliases for 'Presentation|Grammar|Focus|Презентація|Граматика|Теорія|Пояснення' found: Завдання 4: Граматика, Граматика
  - FIX: Keep only one version of the header (preferably the primary one or the one with more content).
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Practice|Exercises|Activity|Практика|Вправи' per template 'b1-grammar-module-template'
  - FIX: Add '## Practice' section as specified in docs/l2-uk-en/templates/b1-grammar-module-template.md
- ❌ **[EMPTY_REQUIRED_SECTION]** Required section '## Потрібно більше практики?' is empty
  - FIX: Populate the section with meaningful content or generate it if it's a mandatory placeholder.

## Recommendation
**📝 UPDATE** (severity 25/100)

- 6 violations (moderate)
- Activity density below minimum

## Gates
- **Words:** ✅ 1469/1000
- **Activities:** ✅ 12/10
- **Density:** ❌ 1 < 12
- **Unique_types:** ✅ 11/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 8/4
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 10 < 15 (soft target)
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 3 violations
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 98.5% (target 85-100% (B1.7-8 Ukraine))
- **Richness:** ✅ 98% (grammar)
- **Grammar:** ⏳ Pending validation

## Richness Details
**Score:** 98% (minimum: 95%)
**Module Type:** grammar

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| examples | 62 | 24 | 100% | 20% | 20.0% |
| engagement | 8 | 5 | 100% | 15% | 15.0% |
| dialogues | 6 | 4 | 100% | 15% | 15.0% |
| variety | 0.98 | - | 98% | 10% | 9.8% |
| cultural | 3 | 3 | 100% | 10% | 10.0% |
| realworld | 6 | 3 | 100% | 10% | 10.0% |
| visual | 6 | 3 | 100% | 5% | 5.0% |
| paragraph_var | 0.68 | - | 68% | 5% | 3.4% |
| questions | 47 | 5 | 100% | 5% | 5.0% |
| proverbs | 6 | 1 | 100% | 5% | 5.0% |
| **TOTAL** | | | | | **98.2%** |

## Low Density Activities
| Activity | Type | Items | Required | Fix |
|----------|------|-------|----------|-----|
| Розмова про рівень B1 | cloze | 8 | 12 | Add 4 more items |


## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 59 | Included in Core |
| **Структура підсумкового модуля** | ⚪️ | 11 | Skipped |
| **Завдання 1: Читання** | ✅ | 301 | Included in Core |
| **Завдання 2: Письмо** | ⚪️ | 117 | Skipped |
| **Завдання 3: Аудіювання** | ⚪️ | 119 | Skipped |
| **Завдання 4: Граматика** | ⚪️ | 222 | Skipped |
| **Завдання 5: Лексика** | ⚪️ | 119 | Skipped |
| **Самооцінка** | ⚪️ | 186 | Skipped |
| **Діалог: Розмова про підсумки B1** | ✅ | 177 | Included in Core |
| **Підсумок** | ✅ | 0 | Included in Core |
| **Ваш шлях від A1 до B1** | ⚪️ | 5 | Skipped |
| **Ваші досягнення** | ⚪️ | 37 | Skipped |
| **Наступний крок: Рівень B2** | ⚪️ | 22 | Skipped |
| **Слова підтримки** | ⚪️ | 76 | Skipped |
| **Додаткові ресурси** | ⚪️ | 18 | Skipped |
| **Потрібно більше практики?** | ⚪️ | 0 | Skipped |