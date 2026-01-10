# Audit Report: 91-b1-capstone.md
**Phase:** B1.8 | **Level:** B1 | **Pedagogy:** TBL | **Target:** 1500
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[SECTION_ORDER]** '## Самооцінка' should come after 'summary' section
  - FIX: Reorder sections to: Summary → Activities → Self-Assessment → External → Vocabulary
- **[YAML_SCHEMA_VIOLATION]** Schema error in 91-b1-capstone.yaml: [index-1] fill-in: 'items.13.options' - ['приходитимеш', 'прийдеш'] is too short
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[YAML_SCHEMA_VIOLATION]** Schema error in 91-b1-capstone.yaml: [index-10] mark-the-words: 'correct_words' is a required property
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[STATE_STANDARD_LOW_IMMERSION]** Module 91 has 97.7% immersion (target: 98.0%+)
  - FIX: Add more Ukrainian content to reach 98%+ immersion for full immersion modules

## TEMPLATE COMPLIANCE
- ❌ **[DUPLICATE_SYNONYMOUS_HEADERS]** Multiple aliases for 'Пояснення|Граматика|Теорія' found: Граматика, Завдання 4: Граматика
  - FIX: Keep only one version of the header (preferably the primary one or the one with more content).
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Практика|Вправи' per template 'b1-grammar-module-template'
  - FIX: Add '## Практика' section as specified in docs/l2-uk-en/templates/b1-grammar-module-template.md

## Recommendation
**📝 UPDATE** (severity 25/100)

- 6 violations (moderate)
- Activity density below minimum

## Gates
- **Words:** ✅ 1579/1500
- **Activities:** ✅ 12/10
- **Density:** ❌ 1 < 12
- **Unique_types:** ✅ 11/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 9/4
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 10 < 15 (soft target)
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 3 violations
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 97.7% (target 85-100% (B1.7-8 Ukraine))
- **Richness:** ✅ 98% (grammar)
- **Grammar:** ⏳ Pending validation

## Richness Details
**Score:** 98% (minimum: 95%)
**Module Type:** grammar

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| examples | 63 | 24 | 100% | 20% | 20.0% |
| engagement | 9 | 5 | 100% | 15% | 15.0% |
| dialogues | 6 | 4 | 100% | 15% | 15.0% |
| variety | 0.98 | - | 98% | 10% | 9.8% |
| cultural | 3 | 3 | 100% | 10% | 10.0% |
| realworld | 6 | 3 | 100% | 10% | 10.0% |
| visual | 6 | 3 | 100% | 5% | 5.0% |
| paragraph_var | 0.67 | - | 67% | 5% | 3.4% |
| questions | 47 | 5 | 100% | 5% | 5.0% |
| proverbs | 6 | 1 | 100% | 5% | 5.0% |
| **TOTAL** | | | | | **98.1%** |

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
| **Потрібно більше практики?** | ⚪️ | 110 | Skipped |