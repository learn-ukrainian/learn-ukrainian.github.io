# Audit Report: 136-rhetorical-questions.md
**Phase:** C1.4 | **Level:** C1 | **Pedagogy:** Immersion | **Target:** 2000
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[YAML_SCHEMA_VIOLATION]** Schema error in 136-rhetorical-questions.yaml: Schema validation error at key '10': {'type': 'fill-in', 'title': 'Контекстуальна риторика', 'items': [{'sentence': "Коли хтось робить очевидну дурницю, ми питаємо: 'Де були твої _____?'", 'answer': 'очі', 'options': ['очі', 'руки', 'ноги', 'вуха']}, {'sentence': "Коли ми не віримо своїм вухам, ми кажем: 'Та _____?'", 'answer': 'невже', 'options': ['невже', 'коли', 'хто', 'де']}, {'sentence': "Коли ми хочемо присоромити когось, ми кажемо: 'Як тобі не _____?'", 'answer': 'соромно', 'options': ['соромно', 'сумно', 'весело', 'боляче']}, {'sentence': "Коли ми наголошуємо на очевидності, ми кажемо: 'Хіба це не _____?'", 'answer': 'зрозуміло', 'options': ['зрозуміло', 'темно', 'тихо', 'далеко']}, {'sentence': "Коли ми втрачаємо терпіння, ми питаємо: 'Скільки можна _____?'", 'answer': 'терпіти', 'options': ['терпіти', 'спати', 'їсти', 'гуляти']}, {'sentence': "Коли ми бачимо безлад, ми питаємо: 'Що тут _____?'", 'answer': 'відбувається', 'options': ['відбувається', 'лежить', 'стоїть', 'росте']}]} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## TEMPLATE COMPLIANCE
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Вступ|Контекст|Розминка' per template 'c1-module-template.md'
  - FIX: Add '## Вступ' section as specified in docs/l2-uk-en/templates/c1-module-template.md.md

## Recommendation
**📝 UPDATE** (severity 5/100)

- 2 violations (minor)

## Gates
- **Words:** ✅ 2011/2000
- **Activities:** ✅ 12/12
- **Density:** ✅ All > 12
- **Unique_types:** ✅ 10/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 8/7
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 25/25
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 1 violations
- **Content_heavy:** ✅ Content-heavy OK (12 activities)
- **Immersion:** 🇺🇦 99.1% (target 90-100%)
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
| model_answers | 76 | 3 | 100% | 20% | 20.0% |
| engagement | 8 | 5 | 100% | 15% | 15.0% |
| register_analysis | 5 | 5 | 100% | 15% | 15.0% |
| visual | 7 | 4 | 100% | 10% | 10.0% |
| variety | 0.99 | - | 99% | 5% | 5.0% |
| cultural | 3 | - | 100% | 5% | 5.0% |
| paragraph_var | 0.97 | - | 97% | 5% | 4.9% |
| **TOTAL** | | | | | **99.8%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 63 | Included in Core |
| **Warm-up** | ✅ | 61 | Included in Core |
| **Теорія: Питання, що є Відповіддю** | ⚪️ | 218 | Skipped |
| **Аналіз: Риторика в літературі** | ✅ | 177 | Included in Core |
| **Психологія переконання** | ⚪️ | 92 | Skipped |
| **Риторика в політиці та медіа** | ⚪️ | 219 | Skipped |
| **Філософські питання** | ⚪️ | 123 | Skipped |
| **Агресія під маскою питання** | ⚪️ | 109 | Skipped |
| **Риторика Шевченка: Питання до Бога** | ⚪️ | 99 | Skipped |
| **Психологічний захист: "Чому?"** | ⚪️ | 0 | Skipped |
| **Риторика в побуті та конфліктах** | ⚪️ | 138 | Skipped |
| **Регістр: Коли НЕ варто використовувати риторичні питання** | ⚪️ | 325 | Skipped |
| **Складна гра з запереченням** | ⚪️ | 122 | Skipped |
| **Як будувати промову** | ⚪️ | 118 | Skipped |
| **Підсумок** | ✅ | 99 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 48 | Skipped |