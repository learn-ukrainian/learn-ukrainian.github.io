# Audit Report: 140-intimate-register.md
**Phase:** C1.4 | **Level:** C1 | **Pedagogy:** Sociolinguistics | **Target:** 2000
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[YAML_SCHEMA_VIOLATION]** Schema error in 140-intimate-register.yaml: Schema validation error at key '9': {'type': 'error-correction', 'title': 'Стилістичні помилки в інтимній розмові', 'instruction': 'Знайдіть недоречні офіційні фрази в розмові закоханих і замініть їх на інтимні.', 'items': [{'sentence': 'Кохана, я хочу [[здійснити акт дарування]] тобі квітів.', 'error': 'здійснити акт дарування', 'answer': 'подарувати', 'options': ['podaruvaty', 'vruchyty', 'nadaty', 'peredaty'], 'explanation': "Офіційна фраза 'здійснити акт дарування' звучить комічно в інтимній розмові. Краще просто 'подарувати'."}, {'sentence': 'Згідно з нашою домовленістю, я [[прибув]] на побачення вчасно.', 'error': 'прибув', 'answer': 'прийшов', 'options': ['pryyshov', "z'yavyvsya", 'pryletiv', 'prybig'], 'explanation': "'Прибув' — це канцеляризм. У розмові з коханою людиною краще сказати 'прийшов'."}, {'sentence': 'Шановна Олено, ти [[виглядаєш]] задовільно.', 'error': 'виглядаєш', 'answer': 'маєш вигляд', 'options': ['mayesh vyhlyad', 'dyvyshysya', 'bachysh', 'zdayeshsya'], 'explanation': "Краще сказати 'Ти маєш чудовий вигляд' або 'Ти красуня'. 'Виглядаєш' — калька, а 'задовільно' — це оцінка '3', а не комплімент."}, {'sentence': 'Я відчуваю до тебе [[симпатію і повагу]].', 'error': 'симпатію і повагу', 'answer': 'кохання', 'options': ['kokhannya', 'lyubov', 'interes', 'druzhbu'], 'explanation': "Для близьких стосунків це занадто сухо. Краще: 'Я тебе кохаю' або 'Я тебе обожнюю'."}, {'sentence': 'Прошу [[надати дозвіл]] поцілувати тебе.', 'error': 'надати дозвіл', 'answer': 'дозволити', 'options': ['dozvolyty', 'daty pravo', 'pidpysaty paperu', 'skazaty tak'], 'explanation': "'Надати дозвіл' — це мова заяв. В інтимній розмові краще: 'Можна тебе поцілувати?' або 'Дозволь тебе поцілувати'."}]} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## Recommendation
**📝 UPDATE** (severity 5/100)

- 1 violations (minor)

## Gates
- **Words:** ✅ 2041/2000
- **Activities:** ✅ 12/12
- **Density:** ✅ All > 12
- **Unique_types:** ✅ 10/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 7/7
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 35/25
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 1 violations
- **Content_heavy:** ✅ Content-heavy OK (12 activities)
- **Immersion:** 🇺🇦 99.4% (target 90-100%)
- **Richness:** ✅ 97% (style)
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ❌ 0/10 (PENDING) - Naturalness check required

## Richness Details
**Score:** 97% (minimum: 95%)
**Module Type:** style

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| exemplar_texts | 15 | 2 | 100% | 25% | 25.0% |
| model_answers | 57 | 3 | 100% | 20% | 20.0% |
| engagement | 7 | 5 | 100% | 15% | 15.0% |
| register_analysis | 15 | 5 | 100% | 15% | 15.0% |
| visual | 3 | 4 | 75% | 10% | 7.5% |
| variety | 1.00 | - | 100% | 5% | 5.0% |
| cultural | 4 | - | 100% | 5% | 5.0% |
| paragraph_var | 1.00 | - | 100% | 5% | 5.0% |
| **TOTAL** | | | | | **97.5%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 82 | Included in Core |
| **Вступ: Мова серця** | ⚪️ | 221 | Skipped |
| **Презентація первинних текстів** | ✅ | 222 | Included in Core |
| **Порівняльний аналіз** | ✅ | 188 | Included in Core |
| **Граматика ніжності** | ⚪️ | 288 | Skipped |
| **Психологія мови: Від конфлікту до любові** | ⚪️ | 158 | Skipped |
| **Соціокультурний аспект** | ✅ | 472 | Included in Core |
| **Фразеологія кохання** | ⚪️ | 70 | Skipped |
| **Письмо: Лист коханій людині** | ⚪️ | 204 | Skipped |
| **Потрібно більше практики?** | ⚪️ | 55 | Skipped |
| **Підсумок** | ✅ | 81 | Included in Core |